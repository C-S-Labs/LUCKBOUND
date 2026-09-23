--!strict
-- Dresses a generated map with its world's ambient scenery (CHUNK_AUTHORING.md
-- convention 6): floating crystals, beacons, birds, tomes and the rest, which
-- ship apart from the pieces so they can move and be thinned on low graphics.
--
-- Client-only by design. Props carry no gameplay, so the server never builds
-- or replicates them; each device places its own at its own detail tier.
--
-- Where things come from:
--   ReplicatedStorage.LuckboundProps   the imported prop libraries (Rojo,
--                                      assets/rbxm/props), searched by NAME
--   Content/Props/<World>.luau         generated placements per chunk id
--   each chunk folder's attributes     ChunkId, Centre, Yaw (ChunkLoader)

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local AmbienceCore = require(Root.Core.AmbienceCore)
local ChunkCore = require(Root.Util.ChunkCore)
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local PropCore = require(Root.Core.PropCore)
local Chunks = require(Root.Content.Chunks)
local Props = require(Root.Content.Props)

local PropController = {}

type Placed = {
	Part: BasePart,
	Base: CFrame, -- the prop's placement frame, before motion
	Fix: CFrame, -- the importer's turn, applied after motion (see enter)
	Anim: string,
	Phase: number,
}

local folder: Folder? = nil
local placed: { Placed } = {}
local stepper: RBXScriptConnection? = nil
local startedAt = 0

local function quality(): number
	local ok, level = pcall(function()
		return (UserSettings():GetService("UserGameSettings") :: any).SavedQualityLevel.Value
	end)
	return AmbienceCore.qualityScale(if ok then level else 0, GameConfig.Ambience)
end

local function library(): Instance?
	return ReplicatedStorage:FindFirstChild("LuckboundProps")
end

local function step()
	local camera = Workspace.CurrentCamera
	if not camera then
		return
	end
	local cfg = GameConfig.Ambience.Props
	local focus = camera.CFrame.Position
	local radius2 = cfg.AnimateRadius * cfg.AnimateRadius
	local t = os.clock() - startedAt
	local parts, cframes = {}, {}
	for _, p in placed do
		if p.Anim ~= "Static" then
			local d = p.Base.Position - focus
			if d:Dot(d) <= radius2 then
				local m = PropCore.motion(p.Anim, t, p.Phase, cfg)
				table.insert(parts, p.Part)
				table.insert(
					cframes,
					p.Base
						* CFrame.Angles(0, m.orbitAngle, 0)
						* CFrame.new(0, m.dy, m.orbitRadius)
						* CFrame.Angles(m.pitch, m.yaw, m.roll)
						* p.Fix
				)
			end
		end
	end
	if #parts > 0 then
		Workspace:BulkMoveTo(parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)
	end
end

--- Places the props for the map named stageName. Safe to call when props are
--- off, when the world has none, or when the library has not been imported:
--- each of those draws nothing, and says why once.
function PropController.enter(worldId: string, stageName: string?)
	PropController.leave()
	local cfg = GameConfig.Ambience.Props
	local set = Props[worldId]
	if not cfg.Enabled or not set or not stageName then
		return
	end
	local lib = library()
	if not lib then
		warn(
			`[PropController] no prop library in ReplicatedStorage.LuckboundProps; {worldId} drawn without props`
		)
		return
	end
	local stages = Workspace:WaitForChild(Constants.NAMES.EXPEDITION_STAGE, 10)
	local stage = stages and stages:WaitForChild(stageName, 10)
	if not stage then
		return
	end

	local scale = quality()
	local holder = Instance.new("Folder")
	holder.Name = "LuckboundProps"
	holder.Parent = Workspace
	folder = holder
	startedAt = os.clock()
	local missing: { [string]: boolean } = {}
	local index = 0

	for _, chunkFolder in stage:GetChildren() do
		local chunkId = chunkFolder:GetAttribute("ChunkId")
		local centre = chunkFolder:GetAttribute("Centre")
		local yaw = chunkFolder:GetAttribute("Yaw")
		local rows = chunkId and set.Placements[chunkId]
		if rows and typeof(centre) == "Vector3" and type(yaw) == "number" then
			local chunk = Chunks[chunkId]
			-- The piece's layout frame: where the generator put it and which
			-- way it turned it. Placements are authored in exactly this frame.
			local layout = CFrame.new(centre) * CFrame.Angles(0, ChunkCore.yawRadians(yaw), 0)
			-- The importer turns every mesh relative to the Blender axes the
			-- placements use -- the same turn the kit's MeshYawOffset corrects
			-- for the structure -- so a prop gets it too, applied last, in its
			-- own frame.
			local fix =
				CFrame.Angles(0, ChunkCore.yawRadians((chunk and chunk.MeshYawOffset) or 0), 0)
			for _, row in rows do
				index += 1
				if PropCore.tierShown(row.Tier, scale, cfg) then
					local source = lib:FindFirstChild(row.Prop, true)
					if source and source:IsA("BasePart") then
						local part = source:Clone()
						part.Anchored = true
						part.CanCollide = false
						part.CanQuery = false
						part.CanTouch = false
						part.Size = Vector3.new(row.S[1], row.S[2], row.S[3])
						local r = row.R
						local base = layout
							* CFrame.new(
								row.P[1],
								row.P[2],
								row.P[3],
								r[1],
								r[2],
								r[3],
								r[4],
								r[5],
								r[6],
								r[7],
								r[8],
								r[9]
							)
						part.CFrame = base * fix
						part.Parent = holder
						table.insert(placed, {
							Part = part,
							Base = base,
							Fix = fix,
							Anim = row.Anim,
							Phase = PropCore.phase(index),
						})
					else
						missing[row.Prop] = true
					end
				end
			end
		end
	end

	if next(missing) then
		local names = {}
		for name in missing do
			table.insert(names, name)
		end
		table.sort(names)
		warn(`[PropController] prop library is missing: {table.concat(names, ", ")}`)
	end
	if #placed > 0 then
		stepper = RunService.RenderStepped:Connect(step)
	end
end

function PropController.leave()
	if stepper then
		stepper:Disconnect()
		stepper = nil
	end
	table.clear(placed)
	if folder then
		folder:Destroy()
		folder = nil
	end
end

return PropController
