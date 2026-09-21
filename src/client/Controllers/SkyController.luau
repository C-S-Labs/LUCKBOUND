--!strict
-- THE SKY, WHEN SOMETHING IS HAPPENING TO THE WORLD.
--
-- An event's lighting and its sky layer, applied on the client that sees them
-- and taken away again exactly. Per client, never server-side, for the same
-- reason biome lighting is (Biome Blueprint §6): Lighting is a shared service,
-- so a server that painted a Starfall would paint it on the player standing
-- in Verdant Valley too.
--
-- THE RULE THIS MODULE EXISTS TO KEEP: whatever it changes, it changes back.
-- The properties it may write are exactly EventCore.LIGHTING_PROPERTIES, which
-- is also the list ExpeditionController snapshots and the list the content
-- validator checks an event against. Three things agreeing about one list is
-- not tidiness -- an event that writes a property nobody restores is an aurora
-- that leaves the fog green until the player rejoins.
--
-- ON SHARING LIGHTING WITH EXPEDITIONS. A biome owns the sky while you are in
-- one. So this releases the hub's sky the moment an expedition starts and
-- takes it back when you return -- otherwise ExpeditionController would
-- snapshot an event-altered hub as "the hub" and restore that forever.

local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local Events = require(Root.Content.Events)
local EventCore = require(Root.Core.EventCore)
local GameConfig = require(Root.Core.GameConfig)
local UITheme = require(Root.Core.UITheme)

local EventController = require(script.Parent.EventController)
local ExpeditionController = require(script.Parent.ExpeditionController)
local StateController = require(script.Parent.StateController)

local SkyController = {}

local player = Players.LocalPlayer

local baseline: { [string]: any } = {}
local haveBaseline = false
local appliedKind: string? = nil
local effectFolder: Folder? = nil

--- An event's definition, found by the Kind the live event carries. Live ids
--- are unique per firing (`STARFALL_1726800000`), so Kind is the stable thing
--- to match on -- and it is also what the menu palette matches, so the sky and
--- the menu cannot disagree about which event is running.
local function definitionFor(kind: string?): any?
	if kind == nil then
		return nil
	end
	for _, definition in Events do
		if definition.Kind == kind then
			return definition
		end
	end
	return nil
end

--- The hub's own lighting, captured once, after HubBuilder has applied it.
--- Everything this module does is measured from here.
local function captureBaseline()
	for _, property in EventCore.trackedLighting() do
		baseline[property] = (Lighting :: any)[property]
	end
	haveBaseline = true
end

local function tweenLighting(target: { [string]: any }, seconds: number)
	local info = TweenInfo.new(seconds, UITheme.Motion.EaseStyle, UITheme.Motion.EaseDirection)
	-- Lighting is not a GuiObject but it is an Instance with tweenable
	-- properties, so one tween carries the whole palette rather than eight
	-- hand-rolled lerps on Heartbeat.
	TweenService:Create(Lighting, info, target):Play()
end

--- The sky layer: motes over the plaza and a colour-correction pass. Both are
--- created here and destroyed here, so an event cannot leave anything behind
--- in Lighting or Workspace.
local function buildEffects(sky: any)
	local folder = Instance.new("Folder")
	folder.Name = "LuckboundEventSky"
	folder.Parent = Workspace

	-- THE EMITTER IS THE SIZE OF THE WEATHER. A ParticleEmitter emits across
	-- its part, so a one-stud part makes a column and a plaza-sized one makes
	-- weather. It was a column, which is why the effect only ever appeared
	-- over the Fate Engine.
	local span = GameConfig.HubLayout.HubDiameter * GameConfig.Events.SkySpanFactor
	local height = GameConfig.Events.SkyHeight * GameConfig.HubLayout.WorldScale

	local anchor = Instance.new("Part")
	anchor.Name = "SkyAnchor"
	anchor.Anchored = true
	anchor.CanCollide = false
	anchor.CanQuery = false
	anchor.CanTouch = false
	anchor.Transparency = 1
	anchor.Size = Vector3.new(span, 1, span)
	anchor.Position = GameConfig.HubLayout.Anchors.FATE_ENGINE + Vector3.new(0, height, 0)
	anchor.Parent = folder

	local emitter = Instance.new("ParticleEmitter")
	emitter.Texture = "rbxasset://textures/particles/sparkles_main.dds"
	emitter.Color = ColorSequence.new(sky.ParticleColor)
	-- Long enough to fall the whole way from SkyHeight, or the weather stops
	-- in mid-air above head height.
	emitter.Lifetime = NumberRange.new(10, 18)
	-- Content states a rate as a FEEL -- a Starfall is heavier than a Veil --
	-- and the area multiplier keeps that meaning now that the same rate has a
	-- whole plaza to cover instead of one dais.
	emitter.Rate = (sky.ParticleRate or 20) * GameConfig.Events.SkyRateScale
	emitter.Speed = NumberRange.new(4, 12)
	emitter.SpreadAngle = Vector2.new(180, 180)
	emitter.Size = NumberSequence.new(3)
	emitter.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(0.3, 0.45),
		NumberSequenceKeypoint.new(1, 1),
	})
	-- Emit across the whole plaza, not from a point.
	emitter.EmissionDirection = Enum.NormalId.Bottom
	emitter.Acceleration = Vector3.new(0, -2, 0)
	emitter.Parent = anchor

	local shape = Instance.new("Attachment")
	shape.Parent = anchor

	if sky.Tint then
		local correction = Instance.new("ColorCorrectionEffect")
		correction.Name = "LuckboundEventGrade"
		correction.TintColor = sky.Tint
		correction.Saturation = sky.Saturation or 0
		correction.Contrast = sky.Contrast or 0
		correction.Brightness = 0
		correction.Parent = Lighting
		-- Parented to the folder's lifetime by hand, since it must live in
		-- Lighting to have any effect.
		folder.Destroying:Connect(function()
			correction:Destroy()
		end)
	end

	effectFolder = folder
end

local function clearEffects()
	if effectFolder then
		effectFolder:Destroy()
		effectFolder = nil
	end
end

--- Back to the hub's own sky.
local function revert(seconds: number)
	if not haveBaseline or appliedKind == nil then
		return
	end
	appliedKind = nil
	clearEffects()
	tweenLighting(baseline, seconds)
end

local function apply(definition: any, seconds: number)
	if not haveBaseline then
		return
	end

	local target: { [string]: any } = {}
	for field, property in EventCore.LIGHTING_PROPERTIES do
		local value = definition.Lighting and definition.Lighting[field]
		-- A property the event does not mention returns to the hub's value
		-- rather than keeping whatever the last event left there. Without
		-- this, two events in a row compose into a sky neither one authored.
		target[property] = if value ~= nil then value else baseline[property]
	end

	clearEffects()
	tweenLighting(target, seconds)

	if definition.Sky and definition.Sky.Enabled then
		buildEffects(definition.Sky)
	end

	appliedKind = definition.Kind
end

local function evaluate()
	if not haveBaseline then
		return
	end

	-- Reduce Motion shortens the crossfade; it does not cancel the event.
	-- Someone who has asked for less movement has not asked to be the only
	-- player who cannot see that the sky changed.
	local seconds = if StateController.setting("ReduceMotion") == true
		then UITheme.Motion.Quick
		else GameConfig.Loading.ShotCrossfadeSeconds

	-- A biome owns the sky while you are inside it.
	if ExpeditionController.get() ~= nil then
		if appliedKind ~= nil then
			appliedKind = nil
			clearEffects()
			-- No lighting tween: ExpeditionController is mid-apply and owns
			-- Lighting now. Touching it here would fight the biome.
		end
		return
	end

	local dominant = EventController.dominant(nil)
	local definition = definitionFor(if dominant then dominant.Kind else nil)

	if definition == nil then
		revert(seconds)
		return
	end

	if definition.Kind == appliedKind then
		return
	end

	apply(definition, seconds)
end

--- What the sky is currently showing, or nil for the hub's own. For the
--- debug overlay and for anything that needs to know without asking Lighting.
function SkyController.current(): string?
	return appliedKind
end

function SkyController.init(): ()
	-- Capture AFTER the hub's lighting has been applied by HubBuilder, not
	-- before: snapshotting Studio's defaults would "restore" the wrong world.
	-- Same wait, and the same reason, as ExpeditionController's.
	task.spawn(function()
		if Workspace:WaitForChild(Constants.NAMES.CROSSROADS, 30) then
			task.wait(1)
		end
		captureBaseline()
		evaluate()
	end)

	EventController.onChanged(function()
		evaluate()
	end)

	ExpeditionController.onChanged(function()
		-- Returning from a biome hands the sky back: re-apply whatever is
		-- still running, or the hub's own if nothing is.
		task.defer(evaluate)
	end)

	player.CharacterAdded:Connect(function()
		task.defer(evaluate)
	end)
end

return SkyController
