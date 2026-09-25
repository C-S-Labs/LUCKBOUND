--!strict
-- WeaponFX: live lightning + charge state for rigged weapons (first user: the Aether Lance - the Winged Sentinel's
-- weapon and an obtainable Legendary). Works the same whoever holds the weapon: a boss, a player, a display.
--
-- The web itself is REAL MESH GEOMETRY (always visible - inventory, icons, other players). On top of it, apply()
-- adds Roblox Beams between the rig's anchor Bones (Bones are Attachments) listed in Content/LightningRigs:
--   Phase1 strands: the web crackle - always on.
--   Phase2 strands: arcs between the plasma blade and the opened halves - only while CHARGED.
-- setCharged(model, on): the charge-up switch combat code calls (player charge meter full / boss phase 2):
--   shows the plasma blade mesh (*Beam*), slides the blade halves open, enables the Phase2 arcs.
-- The engine animates Beams itself (texture scroll + flicker); the client's LightningController only bends their
-- curves now and then so strands visibly re-shape. Everything here is safe to call on server or client.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CollectionService = game:GetService("CollectionService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local LightningRigs = require(Root.Content.LightningRigs)

local WeaponFX = {}

WeaponFX.BEAM_TAG = "CrackleBeam"
-- each half slides out sideways: direction = from the plasma blade's far edge to its near edge. Both anchors ride
-- the (static) lance body, so the direction never flips as the half moves, whatever the importer did to bone axes.
local SLIDE_BONES = { LanceBladeL = { "ArcBR1", "ArcBL1" }, LanceBladeR = { "ArcBL1", "ArcBR1" } }

local function bones(model: Instance): { [string]: Bone }
	local out = {}
	for _, d in model:GetDescendants() do
		if d:IsA("Bone") then
			out[d.Name] = d
		end
	end
	return out
end

-- Studs per rig metre, measured from two anchors whose metre distance the rig declares (works at any model scale).
local function studsPerMetre(def: any, b: { [string]: Bone }): number
	local ref = def.ScaleRef
	local a, c = ref and b[ref[1]], ref and b[ref[2]]
	if a and c and ref[3] > 0 then
		return (a.WorldPosition - c.WorldPosition).Magnitude / ref[3]
	end
	return 1
end

local function makeBeam(
	a: Bone,
	c: Bone,
	def: any,
	phase: number,
	parent: Instance,
	spm: number
): Beam
	local beam = Instance.new("Beam")
	beam.Attachment0 = a
	beam.Attachment1 = c
	beam.Color = ColorSequence.new(def.Color)
	beam.LightEmission = 1
	beam.LightInfluence = 0
	beam.FaceCamera = true
	beam.Segments = 8
	local w = (def.Width or 0.012) * spm
	beam.Width0 = w
	beam.Width1 = w
	beam.Texture = def.Texture or ""
	beam.TextureMode = Enum.TextureMode.Stretch
	beam.TextureSpeed = def.TextureSpeed or 2.5
	beam.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.1),
		NumberSequenceKeypoint.new(0.5, 0),
		NumberSequenceKeypoint.new(1, 0.1),
	})
	beam.Enabled = phase == 1
	beam:SetAttribute("Phase", phase)
	beam:SetAttribute("Span", (a.WorldPosition - c.WorldPosition).Magnitude)
	beam.Name = `Crackle{phase}`
	beam.Parent = parent
	CollectionService:AddTag(beam, WeaponFX.BEAM_TAG)
	return beam
end

--- Add the crackle Beams to a rigged weapon model (idempotent). rigKey = the LightningRigs entry.
function WeaponFX.apply(model: Model, rigKey: string): boolean
	local def = (LightningRigs :: any)[rigKey]
	if not def or model:FindFirstChild("WeaponFX") then
		return def ~= nil
	end
	local folder = Instance.new("Folder")
	folder.Name = "WeaponFX"
	folder.Parent = model
	local b = bones(model)
	local spm = studsPerMetre(def, b)
	model:SetAttribute("StudsPerMetre", spm)
	for phase, key in { "Phase1", "Phase2" } do
		for _, pair in def[key] or {} do
			local a, c = b[pair[1]], b[pair[2]]
			if a and c then
				makeBeam(a, c, def, phase, folder, spm)
			end
		end
	end
	model:SetAttribute("Charged", false)
	WeaponFX.setCharged(model, false)
	return true
end

local applied: { [Bone]: { set: CFrame, offset: CFrame } } = setmetatable({}, { __mode = "k" }) :: any

--- Open (or close) the blade halves. A playing animation rewrites bone transforms every frame, so the client's
--- LightningController calls this every frame for charged weapons (after the Animator). It remembers what it last
--- wrote, so with no animation playing the offset is swapped, never stacked.
function WeaponFX.applySlide(model: Model, b: { [string]: Bone }?, slide: number?, on: boolean?): ()
	local bb = b or bones(model)
	local isOn = if on == nil then model:GetAttribute("Charged") == true else on
	local rigKey = model:GetAttribute("LightningRig")
	local def = type(rigKey) == "string" and (LightningRigs :: any)[rigKey] or nil
	local spm = (model:GetAttribute("StudsPerMetre") :: number?) or 1
	local amount = slide or ((def and def.SlideMetres) or 0) * spm
	for name, pair in SLIDE_BONES do
		local bone, inner, edge = bb[name], bb[pair[1]], bb[pair[2]]
		if bone and inner and edge then
			local last = applied[bone]
			-- base pose: ours minus our offset if nothing rewrote the bone since, else whatever the animation set
			local base = if last and bone.Transform == last.set
				then last.set * last.offset:Inverse()
				else bone.Transform
			local offset = CFrame.new()
			if isOn then
				local out = edge.WorldPosition - inner.WorldPosition
				if out.Magnitude > 1e-4 then
					offset = CFrame.new(bone.WorldCFrame:VectorToObjectSpace(out.Unit) * amount)
				end
			end
			bone.Transform = base * offset
			applied[bone] = { set = bone.Transform, offset = offset }
		end
	end
end

--- The charge switch: plasma blade visible + halves open + blade arcs on (true), or the resting lance (false).
function WeaponFX.setCharged(model: Model, on: boolean): ()
	model:SetAttribute("Charged", on)
	local rigKey = model:GetAttribute("LightningRig")
	local def = type(rigKey) == "string" and (LightningRigs :: any)[rigKey] or nil
	local spm = (model:GetAttribute("StudsPerMetre") :: number?) or 1
	local slide = ((def and def.SlideMetres) or 0) * spm
	local b = bones(model)
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") and string.find(d.Name, "Beam") then
			d.Transparency = if on then 0 else 1
		elseif d:IsA("Beam") and d:GetAttribute("Phase") == 2 then
			d.Enabled = on
		end
	end
	WeaponFX.applySlide(model, b, slide, on)
	CollectionService:AddTag(model, "WeaponFXModel")
end

return WeaponFX
