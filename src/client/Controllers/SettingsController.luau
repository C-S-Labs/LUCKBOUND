--!strict
-- SETTINGS, APPLIED. The half that makes the Settings panel mean something.
--
-- `SettingsCore` declares what a setting is and validates it;
-- `StateController` holds the player's values and syncs them; this turns
-- those values into things the player can actually see and hear.
--
-- WHAT EACH SETTING DRIVES, honestly:
--
--   Music / Effects volume  -> two SoundGroups. Every sound the game ever
--                              plays should be parented to one of them, and
--                              then these sliders work for free. No sound
--                              exists yet, which is exactly why the groups
--                              are created now rather than later: a sound
--                              added to a game with no routing is a sound
--                              that ships ignoring the volume slider.
--   Interface size          -> a UIScale on every Luckbound ScreenGui.
--   Others' rolls           -> whether another player's roll banner is shown.
--   Reduce motion           -> read by UIKit.tween and ThemeController.
--   Start with menu hidden  -> read by HubMenu at load.
--   Screen shake            -> NOTHING SHAKES YET. The setting is stored and
--                              readable (SettingsController.screenShake) so
--                              that whoever builds a shake honours it from
--                              its first frame instead of adding it after.
--
-- That list is the whole contract. If a setting is not in it, it is stored
-- and inert, and saying so plainly is better than a panel that pretends.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)

local StateController = require(script.Parent.StateController)

local SettingsController = {}

local player = Players.LocalPlayer

local musicGroup: SoundGroup
local effectsGroup: SoundGroup
local scales: { [ScreenGui]: UIScale } = {}

--- The group every piece of music must be parented to for the Music slider to
--- reach it.
function SettingsController.musicGroup(): SoundGroup
	return musicGroup
end

--- ...and the one for every other sound.
function SettingsController.effectsGroup(): SoundGroup
	return effectsGroup
end

--- For whoever builds camera shake. Read it; do not shake without it.
function SettingsController.screenShake(): boolean
	return StateController.setting("ScreenShake") == true
end

--- Whether another player's roll should be shown to this one.
function SettingsController.showsOthersRolls(): boolean
	return StateController.setting("ShowGlobalAnnouncements") == true
end

local function buildSoundGroups()
	local existing = SoundService:FindFirstChild("LuckboundMusic")
	if existing and existing:IsA("SoundGroup") then
		musicGroup = existing
	else
		musicGroup = Instance.new("SoundGroup")
		musicGroup.Name = "LuckboundMusic"
		musicGroup.Parent = SoundService
	end

	local effects = SoundService:FindFirstChild("LuckboundEffects")
	if effects and effects:IsA("SoundGroup") then
		effectsGroup = effects
	else
		effectsGroup = Instance.new("SoundGroup")
		effectsGroup.Name = "LuckboundEffects"
		effectsGroup.Parent = SoundService
	end
end

--- Only this game's screens are scaled. The Roblox chat and topbar are not
--- ours to resize, and a UIScale on someone else's ScreenGui is the kind of
--- thing that breaks in an update.
local function isOurs(gui: Instance): boolean
	return gui:IsA("ScreenGui") and string.sub(gui.Name, 1, #Constants.NAMES.ROOT) == Constants.NAMES.ROOT
end

local function scaleFor(gui: ScreenGui): UIScale
	local existing = scales[gui]
	if existing and existing.Parent == gui then
		return existing
	end
	local scale = Instance.new("UIScale")
	scale.Name = "LuckboundUiScale"
	scale.Parent = gui
	scales[gui] = scale
	return scale
end

local function applyScale()
	local value = StateController.setting("UiScale") or 1
	for gui, scale in scales do
		if gui.Parent == nil or scale.Parent == nil then
			scales[gui] = nil
		else
			scale.Scale = value
		end
	end
end

local function adopt(gui: Instance)
	if not isOurs(gui) then
		return
	end
	local screen = gui :: ScreenGui
	scaleFor(screen).Scale = StateController.setting("UiScale") or 1
	screen.Destroying:Connect(function()
		scales[screen] = nil
	end)
end

local function applyVolumes()
	-- Volume is the setting as-is: the sliders are 0..1 and so is a
	-- SoundGroup's volume, so there is deliberately no curve here to argue
	-- with later.
	musicGroup.Volume = StateController.setting("MusicVolume") or 0
	effectsGroup.Volume = StateController.setting("SfxVolume") or 0
end

function SettingsController.init(): ()
	buildSoundGroups()

	local playerGui = player:WaitForChild("PlayerGui")
	for _, child in playerGui:GetChildren() do
		adopt(child)
	end
	playerGui.ChildAdded:Connect(adopt)

	-- Applied on every state change rather than on a settings-only signal,
	-- because a profile arriving IS a settings change -- and it is the one
	-- that matters, since it carries what the player chose last session.
	StateController.onChanged(function()
		applyVolumes()
		applyScale()
	end)

	applyVolumes()
	applyScale()
end

return SettingsController
