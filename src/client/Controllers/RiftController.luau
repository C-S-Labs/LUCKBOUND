--!strict
-- The client half of the expedition rifts (build spec §7.8): how they MOVE.
-- RiftRig builds them on the server and RiftCore says what every curve is;
-- this file poses every part, every frame, from those curves.
--
-- The server sets two facts and nothing else: the rift's kind, and (for the
-- exit) OpenedAt in SERVER time. The client derives the rest, so a player who
-- streams in mid-sequence sees exactly the frame everyone else sees, and one
-- who arrives late sees an open door already open.
--
-- THE TWO RULES (RiftCore keeps them; this file must not break them)
--   * Nothing enters the lane in front of the tear: fragments only move
--     outward from home, and fly in from their own side.
--   * The tear's tip stays on the deck: the loop breathes width and
--     thickness only.
--
-- Every part is looked up by NAME and may be absent (a blockout rift has no
-- fragments or lips). Nothing here may assume the prefab is complete.

local CollectionService = game:GetService("CollectionService")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local RiftCore = require(Root.Core.RiftCore)

local RiftController = {}

type PartInfo = {
	Part: BasePart,
	Home: CFrame,
	Size: Vector3,
	Rest: number, -- resting transparency, from RiftRig
	Side: number, -- +1 / -1: which side of the tear the part's home is on
	Index: number, -- N in Edge<N> / FragRock<N> / FragGem<N>
}

type Tracked = {
	Model: Model,
	Kind: string,
	Centre: CFrame, -- the tear's centre, in world space
	Shells: { PartInfo }, -- RiftCore / RiftMid / RiftHalo
	Edges: { PartInfo },
	Rocks: { PartInfo },
	Gems: { PartInfo },
	Ground: { PartInfo }, -- Scar / Debris
	Glow: { PartInfo }, -- ScarGlow
	Light: PointLight?,
	Motes: ParticleEmitter?,
	Burst: ParticleEmitter?,
	Ribbons: {
		{
			Beam: Beam,
			A0: Attachment,
			A1: Attachment,
			P0: Vector3,
			P1: Vector3,
			Phase: number,
		}
	},
	Phase: number, -- de-syncs this rift from the other one
	Burned: boolean, -- the bloom burst has fired
	LastPhase: string,
}

local tracked: { [Model]: Tracked } = {}
local count = 0

local function indexOf(name: string): number
	return tonumber(string.match(name, "(%d+)$")) or 0
end

local function info(part: BasePart, centre: CFrame): PartInfo
	local rest = part:GetAttribute("RestTransparency")
	local local_ = centre:PointToObjectSpace(part.Position)
	return {
		Part = part,
		Home = part.CFrame,
		Size = part.Size,
		Rest = if type(rest) == "number" then rest else 0,
		Side = if local_.X >= 0 then 1 else -1,
		Index = indexOf(part.Name),
	}
end

local function track(model: Instance)
	if not model:IsA("Model") or tracked[model] then
		return
	end
	local kind = model:GetAttribute("RiftKind")
	if type(kind) ~= "string" then
		return
	end
	local core = model:FindFirstChild("RiftCore")
	-- The tear's centre, oriented by the MODEL's frame rather than the core
	-- mesh's own (an imported MeshPart can carry a baked turn of its own).
	local pivot = model:GetPivot()
	local centre = CFrame.new(
		if core and core:IsA("BasePart") then core.Position else pivot.Position
	) * (pivot - pivot.Position)

	local t: Tracked = {
		Model = model,
		Kind = kind,
		Centre = centre,
		Shells = {},
		Edges = {},
		Rocks = {},
		Gems = {},
		Ground = {},
		Glow = {},
		Light = nil,
		Motes = nil,
		Burst = nil,
		Ribbons = {},
		Phase = 0,
		Burned = false,
		LastPhase = "",
	}
	count += 1
	t.Phase = count * 2.1

	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") then
			local n = d.Name
			if n == "RiftCore" or n == "RiftMid" or n == "RiftHalo" then
				table.insert(t.Shells, info(d, centre))
			elseif string.sub(n, 1, 4) == "Edge" then
				table.insert(t.Edges, info(d, centre))
			elseif string.sub(n, 1, 8) == "FragRock" then
				table.insert(t.Rocks, info(d, centre))
			elseif string.sub(n, 1, 7) == "FragGem" then
				table.insert(t.Gems, info(d, centre))
			elseif n == "Scar" or n == "Debris" then
				table.insert(t.Ground, info(d, centre))
			elseif n == "ScarGlow" then
				table.insert(t.Glow, info(d, centre))
			end
		elseif d:IsA("PointLight") and d.Name == "RiftLight" then
			t.Light = d
		elseif d:IsA("ParticleEmitter") then
			if d.Name == "RiftMotes" then
				t.Motes = d
			elseif d.Name == "RiftBurst" then
				t.Burst = d
			end
		elseif d:IsA("Beam") then
			local a0, a1 = d.Attachment0, d.Attachment1
			if a0 and a1 then
				table.insert(t.Ribbons, {
					Beam = d,
					A0 = a0,
					A1 = a1,
					P0 = a0.Position,
					P1 = a1.Position,
					Phase = indexOf(d.Name) * 1.3,
				})
			end
		end
	end

	tracked[model] = t
	model.AncestryChanged:Connect(function(_, parent)
		if parent == nil then
			tracked[model] = nil
		end
	end)
end

local function setTransparency(list: { PartInfo }, value: (PartInfo) -> number)
	for _, p in list do
		p.Part.Transparency = value(p)
	end
end

--- A part moved by (across, up) in the rift's own frame: local X is across
--- the tear, local Y is up, local Z is the walk-through lane (never touched).
local function shifted(t: Tracked, p: PartInfo, across: number, up: number): CFrame
	return p.Home + t.Centre:VectorToWorldSpace(Vector3.new(across, up, 0))
end

local function animate(t: Tracked, now: number)
	local cfg = GameConfig.Rift
	local openedAt = t.Model:GetAttribute("OpenedAt")
	local phase, elapsed =
		RiftCore.phaseFor(t.Kind, if type(openedAt) == "number" then openedAt else nil, now, cfg)

	if phase == "SEALED" then
		if t.LastPhase ~= "SEALED" then
			t.LastPhase = "SEALED"
			for _, list in { t.Shells, t.Edges, t.Rocks, t.Gems, t.Ground, t.Glow } do
				setTransparency(list, function()
					return 1
				end)
			end
			if t.Light then
				t.Light.Enabled = false
			end
			if t.Motes then
				t.Motes.Enabled = false
			end
			for _, r in t.Ribbons do
				r.Beam.Enabled = false
			end
		end
		return
	end

	-- 0..1 for every strand of the sequence; an open rift is simply all 1.
	local m: RiftCore.Materialise = if phase == "OPEN"
		then { Seeds = 1, Gather = 1, Height = 1, Width = 1, Alpha = 1, Bloom = 0 }
		else RiftCore.materialise(elapsed, cfg)
	t.LastPhase = phase

	local loop = now + t.Phase

	-- The tear: three shells, each breathing on its own phase. Height belongs
	-- to the materialise alone, so the tip never leaves the deck.
	for i, p in t.Shells do
		local swell = RiftCore.breath(loop, i * 1.1, cfg)
		p.Part.Size = Vector3.new(
			math.max(0.02, p.Size.X * m.Width * swell),
			math.max(0.02, p.Size.Y * m.Height),
			math.max(0.02, p.Size.Z * swell)
		)
		p.Part.Transparency = RiftCore.shellTransparency(p.Rest, m.Alpha)
	end

	-- The lips ride the edge of the tear as it opens: pulled in toward the
	-- centre by its width and height, back out as it opens.
	for _, p in t.Edges do
		local d = t.Centre:PointToObjectSpace(p.Home.Position)
		local target = t.Centre:PointToWorldSpace(Vector3.new(d.X * m.Width, d.Y * m.Height, d.Z))
		p.Part.CFrame = p.Home - p.Home.Position + target
		local shimmer = cfg.EdgeShimmer * math.sin(loop * 2.3 + p.Index * 0.9)
		p.Part.Transparency =
			RiftCore.shellTransparency(math.clamp(p.Rest + shimmer, 0, 1), m.Alpha)
	end

	-- Fragments: fly in from their own side, then drift outward and back.
	for _, p in t.Rocks do
		local gx, gy = RiftCore.gatherOffset(m.Gather, p.Side, cfg)
		local dx, dy = RiftCore.fragmentOffset(loop, p.Index, p.Side, cfg)
		p.Part.CFrame = shifted(t, p, gx + dx * m.Gather, gy + dy * m.Gather)
		p.Part.Transparency = RiftCore.shellTransparency(0, m.Gather)
	end
	for _, p in t.Gems do
		local gx, gy = RiftCore.gatherOffset(m.Gather, p.Side, cfg)
		local dx, dy = RiftCore.fragmentOffset(loop, p.Index, p.Side, cfg)
		p.Part.CFrame = shifted(t, p, gx + dx * m.Gather, gy + dy * m.Gather)
		p.Part.Transparency = RiftCore.shellTransparency(p.Rest, m.Gather)
	end

	-- The ground: the scar appears first, and its cracks pulse.
	setTransparency(t.Ground, function()
		return RiftCore.shellTransparency(0, m.Seeds)
	end)
	setTransparency(t.Glow, function(p)
		local pulse = cfg.ScarGlowPulse * (0.5 + 0.5 * math.sin(loop * 1.6 + p.Index))
		return RiftCore.shellTransparency(math.clamp(p.Rest + pulse, 0, 1), m.Seeds)
	end)

	if t.Light then
		t.Light.Enabled = true
		t.Light.Brightness = RiftCore.lightBrightness(m.Bloom, cfg) * math.max(0.15, m.Alpha)
	end
	if t.Motes then
		t.Motes.Enabled = true
		-- Gathering motes are thick while the rift is forming.
		t.Motes.Rate = cfg.MoteRate * (1 + 2.5 * m.Seeds * (1 - m.Alpha))
	end
	for _, r in t.Ribbons do
		r.Beam.Enabled = m.Alpha > 0.6
		local sway = math.sin(loop * 0.9 + r.Phase)
		r.A0.Position = r.P0 + Vector3.new(sway * 0.6, 0, 0)
		r.A1.Position = r.P1 + Vector3.new(-sway * 0.6, 0, 0)
	end

	-- One burst of light-motes at the bloom, only if the player watched it.
	if
		phase == "MATERIALISING"
		and not t.Burned
		and elapsed >= cfg.Phases.Bloom[1] * cfg.MaterialiseSeconds
	then
		t.Burned = true
		if t.Burst then
			t.Burst:Emit(cfg.BloomBurst)
		end
	elseif phase == "OPEN" then
		t.Burned = true
	end
end

function RiftController.init(): ()
	for _, model in CollectionService:GetTagged(Constants.NAMES.RIFT_TAG) do
		track(model)
	end
	-- Rifts stream in and out with their chunk. Attributes arrive with the
	-- instance, but its children can trail it by a beat.
	CollectionService:GetInstanceAddedSignal(Constants.NAMES.RIFT_TAG):Connect(function(model)
		task.defer(track, model)
	end)

	RunService.RenderStepped:Connect(function()
		if next(tracked) == nil then
			return
		end
		local now = Workspace:GetServerTimeNow()
		for _, t in tracked do
			animate(t, now)
		end
	end)
end

return RiftController
