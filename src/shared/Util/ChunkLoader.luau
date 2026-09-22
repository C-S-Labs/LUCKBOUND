--!strict
-- Turns a ChunkCore Layout into Roblox geometry. Addendum §A4, step 5.
--
-- ChunkCore decides WHAT goes WHERE and stays pure so it can run in CI. This
-- file is the other half: it knows about Instances and CFrames and nothing
-- about layout rules. The seam between them is a list of plain numbers.
--
-- THE MESH SEAM, same as HubBuilder's: every chunk names an AssetKey. If the
-- manifest has an uploaded id, the loader streams that mesh in. If it does not
-- -- which is every chunk today -- it draws a labelled blockout platform
-- instead. Both paths produce a walkable map at the same coordinates, so a kit
-- can be designed, generated and WALKED before a single mesh exists, and art
-- arrives one piece at a time with no flag day.
--
-- The blockout is deliberately informative rather than pretty: each piece
-- carries its own ChunkId, its Role and a coloured marker at every socket. A
-- generated map is meant to be verifiable by eye -- if the Waystone Ring is
-- not the piece before the temple, you can see that from the ground.

local AssetService = game:GetService("AssetService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local AssetManifest = require(Root.Content.AssetManifest)
local ChunkCore = require(Root.Util.ChunkCore)
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)

local ChunkLoader = {}

-- Blockout colours by Role. Not art direction -- these exist so a tester can
-- read the shape of a generated map at a glance and say "entry, two paths, a
-- combat space, the gate, the arena".
local ROLE_COLOR: { [string]: Color3 } = {
	ENTRY = Color3.fromRGB(122, 200, 140),
	PATH = Color3.fromRGB(120, 126, 148),
	COMBAT = Color3.fromRGB(156, 140, 190),
	SIDE = Color3.fromRGB(196, 176, 110),
	BOSS = Color3.fromRGB(198, 104, 104),
}

local function part(props: { [string]: any }, parent: Instance): Part
	local p = Instance.new("Part")
	p.Anchored = true
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	for key, value in props do
		(p :: any)[key] = value
	end
	p.Parent = parent
	return p
end

local function billboard(text: string, color: Color3, adornee: BasePart, studs: number)
	local gui = Instance.new("BillboardGui")
	gui.Name = "ChunkLabel"
	gui.Size = UDim2.fromScale(studs, studs * 0.22)
	-- Adorned to the floor, whose centre is INSIDE the slab, so the label has
	-- to be lifted clear or it renders half-buried in its own platform.
	gui.StudsOffset = Vector3.new(0, 60, 0)
	gui.AlwaysOnTop = false
	gui.MaxDistance = 2500
	gui.Adornee = adornee
	gui.Parent = adornee

	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.GothamBold
	label.TextScaled = true
	label.TextColor3 = color
	label.TextStrokeTransparency = 0.4
	label.Text = text
	label.Parent = gui
end

--- Tries the authored mesh. Returns nil when the asset is a PLACEHOLDER, when
--- the id fails to load, or when the engine refuses it -- every one of which
--- must fall back to blockout rather than leaving a hole in the map.
local function tryMesh(assetKey: string, size: Vector3, cframe: CFrame, parent: Instance): BasePart?
	local id = AssetManifest.assetId(assetKey)
	if not id then
		return nil
	end

	local ok, meshPart = pcall(function()
		return AssetService:CreateMeshPartAsync(id)
	end)
	if not ok or not meshPart then
		warn(`[ChunkLoader] asset '{assetKey}' ({id}) failed to load; using blockout`)
		return nil
	end

	local mesh = meshPart :: MeshPart
	mesh.Name = "Mesh"
	mesh.Anchored = true
	mesh.CanCollide = true
	mesh.Size = size
	mesh.CFrame = cframe
	mesh.Parent = parent
	return mesh
end

--- Blockout for one chunk: a floor, a rim so the edge reads at distance, and
--- a label naming the piece.
local function buildBlockout(chunk: any, placed: any, centre: Vector3, parent: Instance): BasePart
	local cfg = GameConfig.Expedition
	local color = ROLE_COLOR[placed.Role] or ROLE_COLOR.PATH

	-- A quarter turn swaps the piece's X and Z extents, exactly as
	-- ChunkCore.overlaps assumes. Getting this wrong would draw a footprint
	-- that does not match the one collision was checked against.
	local sizeX, sizeZ = chunk.SizeX, chunk.SizeZ
	if placed.Yaw == 90 or placed.Yaw == 270 then
		sizeX, sizeZ = sizeZ, sizeX
	end

	local floor = part({
		Name = "Floor",
		Size = Vector3.new(sizeX, cfg.FloorThickness, sizeZ),
		CFrame = CFrame.new(centre),
		Color = color,
		Material = Enum.Material.SmoothPlastic,
	}, parent)

	-- Rim on all four edges. Non-colliding: it is a visual boundary, not a
	-- wall, and a wall would change how the map plays.
	local halfX, halfZ = sizeX / 2, sizeZ / 2
	local edges = {
		{ Vector3.new(0, 0, -halfZ), Vector3.new(sizeX, cfg.RimHeight, cfg.RimThickness) },
		{ Vector3.new(0, 0, halfZ), Vector3.new(sizeX, cfg.RimHeight, cfg.RimThickness) },
		{ Vector3.new(-halfX, 0, 0), Vector3.new(cfg.RimThickness, cfg.RimHeight, sizeZ) },
		{ Vector3.new(halfX, 0, 0), Vector3.new(cfg.RimThickness, cfg.RimHeight, sizeZ) },
	}
	for index, edge in edges do
		part({
			Name = `Rim{index}`,
			Size = edge[2],
			CFrame = CFrame.new(centre + edge[1] + Vector3.new(0, cfg.FloorThickness / 2, 0)),
			Color = color:Lerp(Color3.new(1, 1, 1), 0.35),
			Material = Enum.Material.SmoothPlastic,
			CanCollide = false,
			Transparency = 0.25,
		}, parent)
	end

	billboard(
		`{placed.ChunkId}\n{placed.Role} · #{placed.Index}`,
		color:Lerp(Color3.new(1, 1, 1), 0.5),
		floor,
		math.min(sizeX, sizeZ) * 0.5
	)

	return floor
end

-- Kind -> a stable, well-separated hue. A lookup table would have to grow
-- every time a world invents a vocabulary, so this derives the colour instead.
--
-- The obvious `sum of bytes % 360` does NOT work here: "SPAN" and "RITE" land
-- six degrees apart and render as the same orange, which would make two
-- different socket Kinds look like a legal join. A polynomial hash spread by
-- the golden-ratio conjugate puts them at opposite ends of the wheel, which is
-- the whole reason the markers are coloured at all.
local function kindColor(kind: string): Color3
	local hash = 0
	for i = 1, #kind do
		hash = (hash * 31 + string.byte(kind, i)) % 65536
	end
	return Color3.fromHSV((hash * 0.6180339887) % 1, 0.7, 1)
end

--- A marker post at every socket, coloured by Kind. These are the whole point
--- of the blockout: two posts of the same colour touching is a join the
--- grammar allowed, and you can see it from the ground.
local function buildSocketMarkers(chunk: any, placed: any, origin: Vector3, parent: Instance)
	local cfg = GameConfig.Expedition
	for _, socket in chunk.Sockets do
		local world = ChunkCore.worldSocket(placed, chunk, socket)
		local markerColor = kindColor(socket.Kind)

		part({
			Name = `Socket_{socket.Id}_{socket.Kind}`,
			Size = Vector3.new(5, cfg.SocketMarkerHeight, 5),
			CFrame = CFrame.new(
				origin + Vector3.new(world.X, world.Y + cfg.SocketMarkerHeight / 2, world.Z)
			),
			Color = markerColor,
			Material = Enum.Material.Neon,
			CanCollide = false,
			Transparency = 0.35,
		}, parent)
	end
end

export type LoadResult = {
	Model: Model,
	EntryPosition: Vector3,
	-- Where the way home goes. Offset toward the back of the arrival chunk so
	-- the player does not materialise standing inside the portal that would
	-- send them straight back out again.
	ReturnPosition: Vector3,
	FloorCount: number,
	UsedMeshes: number,
}

--- Builds `layout` under `parent`, offset to `origin`. Returns where the
--- player should arrive.
function ChunkLoader.build(
	layout: any,
	chunks: { [string]: any },
	origin: Vector3,
	parent: Instance,
	name: string
): LoadResult
	local cfg = GameConfig.Expedition

	local model = Instance.new("Model")
	model.Name = name
	model:SetAttribute("WorldId", layout.WorldId)
	model:SetAttribute("Seed", layout.Seed)

	local entryPosition = origin
	local returnPosition = origin
	local usedMeshes = 0
	local floorCount = 0

	for _, placed in layout.Chunks do
		local chunk = chunks[placed.ChunkId]
		if not chunk then
			warn(`[ChunkLoader] layout names unknown chunk '{placed.ChunkId}'; skipped`)
			continue
		end

		local folder = Instance.new("Folder")
		folder.Name = `{placed.Index}_{placed.ChunkId}`
		folder:SetAttribute("Role", placed.Role)
		folder:SetAttribute("Yaw", placed.Yaw)
		folder.Parent = model

		-- THE ORIGIN CONTRACT WITH THE BLENDER FILE.
		--
		-- placed.X/Y/Z is the chunk's CENTRE, and the yaw rotates ABOUT that
		-- point. So an authored mesh must have its origin at the centre of its
		-- own footprint. A corner or edge origin lands the art half a chunk
		-- out -- by a DIFFERENT amount for each of the four yaws, so it is not
		-- an offset anything can correct for -- while ChunkCore.overlaps still
		-- certifies the layout as collision-free, because it only ever sees
		-- centre +/- half-size.
		--
		-- VERTICALLY THE TWO SIDES DISAGREE TODAY. Setting mesh.Size and
		-- CFrame puts the BOUNDING BOX CENTRE at placed.Y, while
		-- docs/CHUNK_AUTHORING.md asks the modeller for a GROUND-LEVEL origin
		-- -- which is the intuitive thing to author and the thing the blockout
		-- already assumes. A GroundOffsetY on the chunk schema is what closes
		-- that, and it is owed before the first mesh is uploaded. STATUS.md.
		--
		-- Nothing here can detect a wrong origin: it is invisible metadata in
		-- an FBX, the same class of failure that produced the "register a
		-- prefab from a NAMED PART, not from its pivot" rule for the hub.
		local centre = origin + Vector3.new(placed.X, placed.Y, placed.Z)
		local cframe = CFrame.new(centre) * CFrame.Angles(0, math.rad(placed.Yaw), 0)

		local mesh = tryMesh(
			chunk.AssetKey,
			Vector3.new(chunk.SizeX, chunk.SizeY, chunk.SizeZ),
			cframe,
			folder
		)

		local surface: BasePart
		if mesh then
			usedMeshes += 1
			surface = mesh
		else
			surface = buildBlockout(chunk, placed, centre, folder)
			floorCount += 1
		end

		buildSocketMarkers(chunk, placed, origin, folder)

		if placed.Role == "ENTRY" then
			local top = surface.Position + Vector3.new(0, surface.Size.Y / 2, 0)
			entryPosition = top + Vector3.new(0, cfg.SpawnHeight, 0)
			-- Every kit's entry socket faces away from the arrival point, and
			-- ChunkCore always places ENTRY unrotated at the layout origin, so
			-- +Z is reliably "behind the player". A quarter of the chunk back
			-- is far enough to be a destination, near enough to be obvious.
			returnPosition = top + Vector3.new(0, 0, surface.Size.Z * 0.25)
		end
	end

	model.Parent = parent
	return {
		Model = model,
		EntryPosition = entryPosition,
		ReturnPosition = returnPosition,
		FloorCount = floorCount,
		UsedMeshes = usedMeshes,
	}
end

--- Applies a world's Environment to Lighting. SERVER MUST NOT CALL THIS.
---
--- Lighting is a shared service, so a server-side apply would paint every
--- player's screen with whichever world was entered last. Called from the
--- client instead, which is what makes "lighting never bleeds between
--- expeditions" (Biome Blueprint §6 checklist) true rather than aspirational.
function ChunkLoader.applyEnvironment(lighting: Lighting, environment: any)
	lighting.Ambient = environment.AmbientColor
	if environment.OutdoorAmbientColor then
		lighting.OutdoorAmbient = environment.OutdoorAmbientColor
	end
	if environment.ColorShiftTop then
		lighting.ColorShift_Top = environment.ColorShiftTop
	end
	lighting.FogColor = environment.FogColor
	lighting.FogStart = environment.FogStart
	lighting.FogEnd = environment.FogEnd
	lighting.Brightness = environment.Brightness
	lighting.ClockTime = environment.ClockTime
end

ChunkLoader.kindColor = kindColor
ChunkLoader.ROLE_COLOR = ROLE_COLOR
ChunkLoader.STAGE_NAME = Constants.NAMES.EXPEDITION_STAGE

return ChunkLoader
