--!strict
-- Drop-in chunk kits, the Roblox half. At boot, every world folder under
-- ServerStorage.LuckboundChunkKits (assets/rbxm/chunks/<world>/ in the repo)
-- that has NO hand-written kit in Content/Chunks becomes a kit:
--
--   1. every MeshPart in the folder's .rbxmx files is a piece -- its MeshId is
--      the asset, its Size the footprint, its Name the Role;
--   2. each is loaded once with precise collision, off in a corner of the
--      world, and ray-probed: deck at the middle of an edge, at the piece's
--      walk height, with nothing standing in the way, is an opening;
--   3. ChunkKitCore turns the measurements into ChunkDefinitions, which go
--      into the chunk registry and the asset manifest beside the hand-written
--      ones -- before boot validation, so a broken drop fails loudly there.
--
-- Hand-written kits always win: a world with even one chunk in Content/Chunks
-- is left exactly as it is, and its folder here is only provenance. To move a
-- world onto its drop-in file, delete its Content/Chunks module.
--
-- This runs on every server start (servers do not outlive a deploy, so there
-- is nothing to remember between them). It costs one mesh load per piece, in
-- parallel, and only for drop-in worlds. docs/CHUNK_DROP_IN.md.

local AssetService = game:GetService("AssetService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local ChunkKitCore = require(Root.Util.ChunkKitCore)
local Constants = require(Root.Core.Constants)
local ExpeditionCore = require(Root.Core.ExpeditionCore)
local GameConfig = require(Root.Core.GameConfig)

local ChunkAutoKit = {}

-- Far from anything a player will ever see. Every probe ray is filtered to
-- its own mesh, so the pieces can all sit on the same spot at once.
local PROBE_ORIGIN = Vector3.new(40000, 4000, 40000)
-- An opening must have this much headroom above the deck, clear of the mesh,
-- from this far in to the edge: that is what tells a walkway from a railed or
-- walled edge whose top happens to sit near walk height.
local CLEAR_HEIGHT = 3
local CLEAR_DEPTH = 16
-- How far in from the centre the walk-height samples sit, as a fraction of
-- the footprint. Off-centre, so a statue in the middle does not set the floor.
local CENTRE_SPREAD = 0.2

local function median(values: { number }): number?
	if #values == 0 then
		return nil
	end
	table.sort(values)
	return values[math.ceil(#values / 2)]
end

local EDGE_DIR = {
	[0] = Vector3.new(0, 0, -1),
	[90] = Vector3.new(1, 0, 0),
	[180] = Vector3.new(0, 0, 1),
	[270] = Vector3.new(-1, 0, 0),
}

--- Loads one piece and measures it. Returns nil when the mesh will not load.
local function probe(source: MeshPart, name: string): ChunkKitCore.Piece?
	local ok, loaded = pcall(function()
		return AssetService:CreateMeshPartAsync(source.MeshId, {
			CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
		})
	end)
	if not ok or not loaded then
		warn(`[ChunkAutoKit] {name}: mesh {source.MeshId} failed to load -- {tostring(loaded)}`)
		return nil
	end
	local mesh = loaded :: MeshPart
	local size = source.Size
	mesh.Anchored = true
	mesh.Size = size
	mesh.CFrame = CFrame.new(PROBE_ORIGIN)
	mesh.Transparency = 1
	mesh.CanTouch = false
	mesh.Parent = Workspace
	-- A freshly cooked precise hull is not queryable until physics steps.
	RunService.Heartbeat:Wait()

	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { mesh }
	local top = PROBE_ORIGIN.Y + size.Y / 2
	local bottom = PROBE_ORIGIN.Y - size.Y / 2
	local function deckAt(x: number, z: number): number?
		local hit =
			Workspace:Raycast(Vector3.new(x, top + 5, z), Vector3.new(0, -(size.Y + 10), 0), params)
		return if hit then hit.Position.Y else nil
	end

	local centreHits = {}
	for i = -1, 1 do
		for j = -1, 1 do
			local y = deckAt(
				PROBE_ORIGIN.X + i * size.X * CENTRE_SPREAD,
				PROBE_ORIGIN.Z + j * size.Z * CENTRE_SPREAD
			)
			if y then
				table.insert(centreHits, y)
			end
		end
	end

	local cfg = GameConfig.Expedition.SocketProbe
	local edgeHits: { [number]: number } = {}
	for facing, dir in EDGE_DIR do
		local half = if facing == 0 or facing == 180 then size.Z / 2 else size.X / 2
		local at = PROBE_ORIGIN + dir * (half - cfg.Inset)
		edgeHits[facing] = deckAt(at.X, at.Z)
	end

	-- Walk height: the middle of the piece, or failing that (a ring, a
	-- pit) the most typical edge.
	local walk0 = median(centreHits)
	if not walk0 then
		local all = {}
		for _, y in edgeHits do
			table.insert(all, y)
		end
		walk0 = median(all)
	end

	local openings = {}
	local openingYs = {}
	if walk0 then
		for facing, y in edgeHits do
			if math.abs(y - walk0) <= cfg.Tolerance then
				local dir = EDGE_DIR[facing]
				local half = if facing == 0 or facing == 180 then size.Z / 2 else size.X / 2
				local from = PROBE_ORIGIN + dir * (half - CLEAR_DEPTH)
				local blocked = Workspace:Raycast(
					Vector3.new(from.X, y + CLEAR_HEIGHT, from.Z),
					dir * (CLEAR_DEPTH + 1),
					params
				)
				if not blocked then
					table.insert(openings, { Facing = facing, Y = y })
					table.insert(openingYs, y)
				end
			end
		end
	end
	mesh:Destroy()

	-- The walk plane is where the openings are: that is the height pieces
	-- join at, and a sunken or raised middle is the piece's own business.
	local walk = median(openingYs) or walk0 or (bottom + size.Y / 2)
	local out = {}
	for _, o in openings do
		table.insert(out, { Facing = o.Facing, OffsetY = math.round((o.Y - walk) * 10) / 10 })
	end

	return {
		Name = name,
		SizeX = size.X,
		SizeY = size.Y,
		SizeZ = size.Z,
		GroundOffsetY = math.round((walk - bottom) * 10) / 10,
		Openings = out,
		Attributes = source:GetAttributes(),
	}
end

-- A MeshPart named generically takes its wrapping Model's name, so a file
-- exported as one Model around one "MeshPart" still names its piece.
local function pieceName(mesh: MeshPart): string
	if (mesh.Name == "MeshPart" or mesh.Name == "Mesh") and mesh.Parent then
		return mesh.Parent.Name
	end
	return mesh.Name
end

--- Builds every drop-in kit into `chunks` and `manifest`. Yields while the
--- meshes load; call it before content validation.
function ChunkAutoKit.load(chunks: { [string]: any }, worlds: { [string]: any }, manifest: any)
	local root = ServerStorage:FindFirstChild(Constants.NAMES.CHUNK_KITS_FOLDER)
	if not root then
		return
	end

	for _, folder in root:GetChildren() do
		local worldId = ChunkKitCore.worldIdFor(folder.Name)
		local world = worlds[worldId]
		if not world then
			warn(
				`[ChunkAutoKit] folder '{folder.Name}' names no world ('{worldId}' is not in Content/Worlds); skipped`
			)
			continue
		end
		if ExpeditionCore.hasKit(chunks, worldId) then
			-- The hand-written kit is the kit. Say so, so a new drop into a
			-- hand-written world does not look like it was silently ignored.
			print(
				`[ChunkAutoKit] {worldId}: has a hand-written kit in Content/Chunks, so its drop-in file is not used`
			)
			continue
		end
		if ExpeditionCore.hasPrebuiltMap(world) then
			warn(`[ChunkAutoKit] {worldId}: declares a PrebuiltMap, so its chunk file is not used`)
			continue
		end

		local sources: { MeshPart } = {}
		for _, d in folder:GetDescendants() do
			if d:IsA("MeshPart") and not ChunkKitCore.isVariant(pieceName(d)) then
				table.insert(sources, d)
			end
		end
		if #sources == 0 then
			warn(`[ChunkAutoKit] {worldId}: folder has no MeshParts`)
			continue
		end

		-- All pieces in parallel: each probe is one mesh load and a physics
		-- step, and they do not see each other.
		local pieces: { ChunkKitCore.Piece } = {}
		local fileOf: { [string]: string } = {}
		local idOf: { [string]: string } = {}
		local pending = #sources
		for _, source in sources do
			task.spawn(function()
				local name = pieceName(source)
				local piece = probe(source, name)
				if piece then
					table.insert(pieces, piece)
					idOf[name] = source.MeshId
					local file = source:FindFirstAncestorWhichIsA("Model")
					while file and file.Parent ~= folder and file.Parent do
						file = file.Parent :: any
					end
					fileOf[name] = if file then file.Name else folder.Name
				end
				pending -= 1
			end)
		end
		while pending > 0 do
			task.wait()
		end

		local defs, report, problems = ChunkKitCore.build(worldId, pieces)
		for _, def in defs do
			if chunks[def.Id] then
				table.insert(problems, `duplicate piece {def.Id}; the second one is skipped`)
				continue
			end
			local name = ""
			for n in idOf do
				if ChunkKitCore.chunkId(worldId, n) == def.Id then
					name = n
				end
			end
			manifest.register(def.AssetKey, {
				AssetId = idOf[name],
				Status = "UPLOADED",
				Source = `assets/rbxm/chunks/{folder.Name}/{fileOf[name]}.rbxmx`,
				Notes = "Drop-in chunk kit, registered at boot by ChunkAutoKit.",
			})
			chunks[def.Id] = def
		end

		print(`[ChunkAutoKit] {table.concat(report, "\n    ")}`)
		for _, problem in problems do
			warn(`[ChunkAutoKit] {worldId}: {problem}`)
		end
	end
end

return ChunkAutoKit
