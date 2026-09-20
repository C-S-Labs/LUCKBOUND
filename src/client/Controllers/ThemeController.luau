--!strict
-- THE LIVE PALETTE, APPLIED.
--
-- `ThemeCore` decides what colour the menu should be; this is the half that
-- knows about Instances. It watches two inputs -- where the player is standing
-- and what is happening to the world -- resolves a palette when either
-- changes, and tweens every painted surface to it.
--
-- WHY A PAINT REGISTRY RATHER THAN A REBUILD. UITheme is deep-frozen and every
-- screen reads it once, at build time, so there is no way to "change the
-- theme" after the fact short of destroying and rebuilding the UI -- which
-- would close whatever panel the player had open. Instead a widget declares
-- which token paints which property (UIKit.paint) and this repaints exactly
-- those. The cost is one table of a few dozen entries; the alternative is a
-- menu that flickers every time someone walks into the Archive.
--
-- IT IS NOT PER FRAME. The district check runs on a timer
-- (GameConfig.HubMenu.DistrictPollSeconds) and a repaint happens only when
-- the resolved palette actually differs.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local GameConfig = require(Root.Core.GameConfig)
local Menu = require(Root.Content.Hub.Menu)
local Palettes = require(Root.Content.Hub.Palettes)
local ThemeCore = require(Root.Core.ThemeCore)
local UITheme = require(Root.Core.UITheme)

local EventController = require(script.Parent.EventController)
local ExpeditionController = require(script.Parent.ExpeditionController)
local StateController = require(script.Parent.StateController)

local ThemeController = {}

local player = Players.LocalPlayer

type Painted = { Instance: Instance, Property: string, Token: string }

local painted: { Painted } = {}
local palette = ThemeCore.base()
local currentDistrict: string? = nil
local listeners: { ({ [string]: any }) -> () } = {}

--- Registers an instance property to be repainted from a palette token.
--- Called by UIKit as widgets are built; nothing else should call it.
function ThemeController.register(instance: Instance, property: string, token: string): ()
	table.insert(painted, { Instance = instance, Property = property, Token = token })
	-- Paint immediately, so a widget built during an event does not wear the
	-- base colour until the next change.
	if palette[token] ~= nil then
		(instance :: any)[property] = palette[token]
	end
end

function ThemeController.palette(): { [string]: any }
	return palette
end

function ThemeController.onChanged(fn: ({ [string]: any }) -> ()): () -> ()
	table.insert(listeners, fn)
	task.spawn(fn, palette)
	return function()
		local index = table.find(listeners, fn)
		if index then
			table.remove(listeners, index)
		end
	end
end

local function differs(a: { [string]: any }, b: { [string]: any }): boolean
	for _, token in ThemeCore.TINTABLE do
		if a[token] ~= b[token] then
			return true
		end
	end
	return false
end

local function repaint(reduceMotion: boolean)
	local seconds = if reduceMotion then 0 else GameConfig.HubMenu.TintTweenSeconds
	local info = TweenInfo.new(seconds, UITheme.Motion.EaseStyle, UITheme.Motion.EaseDirection)

	local alive: { Painted } = {}
	for _, entry in painted do
		-- Destroyed widgets fall out of the registry here rather than being
		-- tracked with a connection each. A panel is rebuilt every time it
		-- opens, so without this the list would grow all session.
		if entry.Instance.Parent ~= nil then
			table.insert(alive, entry)
			local value = palette[entry.Token]
			if value ~= nil then
				if seconds <= 0 then
					(entry.Instance :: any)[entry.Property] = value
				else
					TweenService:Create(entry.Instance, info, { [entry.Property] = value }):Play()
				end
			end
		end
	end
	painted = alive

	for _, fn in listeners do
		task.spawn(fn, palette)
	end
end

local function evaluate()
	if not GameConfig.HubMenu.LiveTintEnabled then
		return
	end

	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	local expedition = ExpeditionController.get()
	local worldId = if expedition then expedition.WorldId else nil

	local districtId: string? = nil
	if root and root:IsA("BasePart") and expedition == nil then
		-- District only means anything in the hub. Inside a biome the sky is
		-- that biome's, and the menu is not on screen anyway.
		districtId = ThemeCore.districtAt(root.Position, Menu, GameConfig.HubMenu.DistrictTintRadius)
	end

	local dominant = EventController.dominant(worldId)
	local resolved = ThemeCore.resolve(Palettes, {
		DistrictId = districtId,
		Event = dominant,
	})

	if not differs(resolved, palette) then
		palette = resolved -- keep Source/DistrictId fresh without repainting
		currentDistrict = districtId
		return
	end

	palette = resolved
	currentDistrict = districtId

	-- ReduceMotion is read at the moment of the change rather than cached, so
	-- a player who turns it on mid-session does not have to rejoin.
	repaint(StateController.setting("ReduceMotion") == true)
end

--- Which district the player is being treated as standing in, or nil on the
--- open plaza. Exposed for the debug overlay and for tests of the caller.
function ThemeController.district(): string?
	return currentDistrict
end

function ThemeController.init(): ()
	-- An event starting is news; do not wait up to half a second for the
	-- poll to notice it.
	EventController.onChanged(function()
		evaluate()
	end)
	ExpeditionController.onChanged(function()
		evaluate()
	end)

	local accumulated = 0
	RunService.Heartbeat:Connect(function(dt)
		accumulated += dt
		if accumulated < GameConfig.HubMenu.DistrictPollSeconds then
			return
		end
		accumulated = 0
		evaluate()
	end)

	evaluate()
end

return ThemeController
