--!strict
-- LightningController: LIVE lightning between anchor Bones on a rigged model (a boss's weapon web, arcs...).
--
-- A model opts in with two attributes:
--   LightningRig : key into Content/LightningRigs (which anchor Bones each strand joins, per phase)
--   Phase        : 1 or 2 (which strand set is live; default 1)
-- Every strand is a short chain of thin Neon segments, re-formed with a fresh random zig-zag ~12 times a second
-- with a little flicker, so no two frames match. Bones ARE Attachments in Roblox, so strands follow the animation.
-- Client-only and cheap: rigs farther than MAX_DIST from the camera are paused and hidden.

local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local LightningRigs = require(Root.Content.LightningRigs)

local LightningController = {}

local SEGMENTS = 5 -- per strand
local RATE = 1 / 12 -- seconds between re-forms
local JITTER = 0.18 -- zig-zag size, as a fraction of the strand length
local WIDTH = 0.035 -- fraction of the strand length, clamped below
local MAX_DIST = 250

type Strand = { a: Bone, b: Bone, parts: { BasePart } }
type Rig = {
	model: Model,
	def: any,
	folder: Folder,
	strands: { [number]: { Strand } },
	phase: number,
}

local rigs: { [Model]: Rig } = {}

local function findBones(model: Model): { [string]: Bone }
	local out = {}
	for _, d in model:GetDescendants() do
		if d:IsA("Bone") then
			out[d.Name] = d
		end
	end
	return out
end

local function makeStrands(rig: Rig, list: { any }, bones: { [string]: Bone }): { Strand }
	local strands = {}
	for _, pair in list do
		local a, b = bones[pair[1]], bones[pair[2]]
		if a and b then
			local parts = {}
			for _ = 1, SEGMENTS do
				local p = Instance.new("Part")
				p.Anchored = true
				p.CanCollide = false
				p.CanQuery = false
				p.CanTouch = false
				p.CastShadow = false
				p.Material = Enum.Material.Neon
				p.Color = rig.def.Color
				p.Transparency = 1
				p.Parent = rig.folder
				table.insert(parts, p)
			end
			table.insert(strands, { a = a, b = b, parts = parts })
		end
	end
	return strands
end

local function attach(model: Model)
	if rigs[model] then
		return
	end
	local key = model:GetAttribute("LightningRig")
	local def = type(key) == "string" and (LightningRigs :: any)[key]
	if not def then
		return
	end
	local folder = Instance.new("Folder")
	folder.Name = "LiveLightning"
	folder.Parent = workspace
	local rig: Rig = { model = model, def = def, folder = folder, strands = {}, phase = 1 }
	local bones = findBones(model)
	rig.strands[1] = makeStrands(rig, def.Phase1 or {}, bones)
	rig.strands[2] = makeStrands(rig, def.Phase2 or {}, bones)
	rigs[model] = rig
	model.AncestryChanged:Connect(function(_, parent)
		if parent == nil then
			folder:Destroy()
			rigs[model] = nil
		end
	end)
end

local function hide(strands: { Strand })
	for _, s in strands do
		for _, p in s.parts do
			p.Transparency = 1
		end
	end
end

local rng = Random.new()
local function reform(s: Strand)
	local a, b = s.a.WorldPosition, s.b.WorldPosition
	local d = b - a
	local len = d.Magnitude
	if len < 1e-3 then
		return
	end
	local dir = d.Unit
	local side = dir:Cross(if math.abs(dir.Y) < 0.9 then Vector3.yAxis else Vector3.xAxis).Unit
	local up = dir:Cross(side).Unit
	local pts = { a }
	for i = 1, SEGMENTS - 1 do
		local t = i / SEGMENTS
		local off = (side * rng:NextNumber(-1, 1) + up * rng:NextNumber(-1, 1)) * len * JITTER
		table.insert(pts, a + d * t + off)
	end
	table.insert(pts, b)
	local w = math.clamp(len * WIDTH, 0.04, 0.35) * rng:NextNumber(0.7, 1.3)
	local flick = rng:NextNumber(0, 0.35)
	for i, p in s.parts do
		local p0, p1 = pts[i], pts[i + 1]
		local seg = p1 - p0
		p.Size = Vector3.new(w, w, seg.Magnitude + w * 0.5)
		p.CFrame = CFrame.lookAt((p0 + p1) / 2, p1)
		p.Transparency = flick
	end
end

function LightningController.init(): ()
	for _, d in workspace:GetDescendants() do
		if d:IsA("Model") and d:GetAttribute("LightningRig") then
			attach(d)
		end
	end
	workspace.DescendantAdded:Connect(function(d)
		if d:IsA("Model") then
			task.defer(function()
				if d:GetAttribute("LightningRig") then
					attach(d)
				end
			end)
		end
	end)
	local acc = 0
	RunService.RenderStepped:Connect(function(dt)
		acc += dt
		if acc < RATE then
			return
		end
		acc = 0
		local cam = workspace.CurrentCamera
		for model, rig in rigs do
			local phase = (model:GetAttribute("Phase") :: number?) or 1
			local near = cam ~= nil
				and (model:GetPivot().Position - cam.CFrame.Position).Magnitude <= MAX_DIST
			for p, strands in rig.strands do
				if p == phase and near then
					for _, s in strands do
						reform(s)
					end
				else
					hide(strands)
				end
			end
		end
	end)
end

return LightningController
