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
	Layout: CFrame, -- the piece's layout frame (centre, turned by its yaw)
	Offset: Vector3, -- the prop's position in that frame
	Rot: CFrame, -- the prop's own rotation, no translation
	Fix: CFrame, -- the importer's turn, applied last (see enter)
	Anim: string,
	Phase: number,
	Heading: number, -- birds only: PropCore.birdHeading
	Radius: number, -- birds only: distance from the piece's axis (turn rate = Speed / Radius)
	Position: Vector3, -- where it rests, for the animate-radius test
	-- Wings only: the bird this rides on, and the root it flaps about.
	Body: Placed?,
	Hinge: Vector3?,
	-- This frame's pose before the importer's turn, so a wing can ride on it.
	Pose: CFrame?,
}

-- The one place motion becomes a CFrame; PropCore.motion documents the order.
-- Returns the pose BEFORE the importer's turn (Fix), which is applied last.
local function rawPose(p: Placed, m: any): CFrame
	if p.Anim == "Wing" then
		-- On its bird's pose this frame, turned about its root. Both wings take
		-- the body's phase, so they beat together (see enter).
		local body = (p.Body :: Placed).Pose :: CFrame
		local h = p.Hinge :: Vector3
		return body
			* CFrame.new(p.Offset)
			* CFrame.new(h)
			* CFrame.Angles(PropCore.wingAngle(m.flap, p.Offset.Z), 0, 0)
			* CFrame.new(-h)
	end
	if p.Anim == "Bird" then
		-- The flock circles the piece's own vertical axis. A bird's authored
		-- rotation was only a random yaw, so it is replaced by its heading,
		-- banked into the turn (its inside is its -Z; see birdHeading).
		return p.Layout
			* CFrame.Angles(0, m.orbit, 0)
			* CFrame.new(p.Offset + Vector3.new(0, m.lift, 0))
			* CFrame.Angles(0, p.Heading, 0)
			* CFrame.Angles(-m.bank, 0, 0)
	end
	return p.Layout
		* CFrame.new(p.Offset + Vector3.new(0, m.lift, 0))
		* CFrame.Angles(0, m.turn, 0)
		* p.Rot
		* CFrame.Angles(m.tiltX, 0, m.tiltZ)
end

local function pose(p: Placed, m: any): CFrame
	local raw = rawPose(p, m)
	p.Pose = raw
	return raw * p.Fix
end

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
			local d = p.Position - focus
			-- A wing moves only when its bird did this frame.
			local near = if p.Body
				then (p.Body :: Placed).Pose ~= nil and d:Dot(d) <= radius2
				else d:Dot(d) <= radius2
			if near then
				table.insert(parts, p.Part)
				table.insert(cframes, pose(p, PropCore.motion(p.Anim, t, p.Phase, cfg, p.Radius)))
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
			-- This piece's placed entries by row, so a wing can find its bird.
			local byRow: { [number]: Placed } = {}
			for rowIndex, row in rows do
				index += 1
				-- A wing needs its bird drawn; a wing whose bird was not (tier,
				-- or a missing mesh) is simply not drawn either.
				local body = if row.Attach then byRow[row.Attach] else nil
				if row.Attach and not body then
					continue
				end
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
						local entry: Placed = {
							Part = part,
							Layout = layout,
							Offset = Vector3.new(row.P[1], row.P[2], row.P[3]),
							Rot = CFrame.new(
								0,
								0,
								0,
								r[1],
								r[2],
								r[3],
								r[4],
								r[5],
								r[6],
								r[7],
								r[8],
								r[9]
							),
							Fix = fix,
							Anim = row.Anim,
							-- A wing beats in time with its own bird.
							Phase = if body then body.Phase else PropCore.phase(index),
							Heading = PropCore.birdHeading(row.P[1], row.P[3]),
							Radius = math.sqrt(row.P[1] * row.P[1] + row.P[3] * row.P[3]),
							Position = if body
								then body.Position
								else layout * Vector3.new(row.P[1], row.P[2], row.P[3]),
							Body = body,
							Hinge = if row.Hinge
								then Vector3.new(row.Hinge[1], row.Hinge[2], row.Hinge[3])
								else nil,
						}
						-- At rest is motion at t = 0 for a bird (its heading, not
						-- its authored yaw) and its wings, and the authored pose
						-- for the rest.
						local restAnim = if row.Anim == "Bird" or row.Anim == "Wing"
							then row.Anim
							else "Static"
						part.CFrame = pose(entry, PropCore.motion(restAnim, 0, 0, cfg))
						part.Parent = holder
						table.insert(placed, entry)
						byRow[rowIndex] = entry
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
