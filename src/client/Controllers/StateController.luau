--!strict
-- The single client-side mirror of server state. Build spec T-114.
-- UI modules read from here and never hold their own copy, so there is one
-- answer to "what is my Fate level?" on the client.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Net = require(Root.Core.Net)
local SettingsCore = require(Root.Core.SettingsCore)

local StateController = {}

local state = {
	FatePoints = 0,
	FateLevel = 1,
	TotalRolls = 0,
	Progress = 0,
	Stats = nil :: any,
	-- Settings are held sanitised from the moment the client starts, so the
	-- UI never has to cope with a nil setting or a value from an older build.
	-- The server's copy is still the authority; this is the mirror the panels
	-- read while a write is in flight.
	Settings = SettingsCore.defaults(),
	RedeemedCodes = {} :: { [string]: any },
	Loaded = false,
}

local listeners: { (any) -> () } = {}

local function notify()
	for _, fn in listeners do
		task.spawn(fn, state)
	end
end

function StateController.get()
	return state
end

function StateController.onChanged(fn: (any) -> ()): () -> ()
	table.insert(listeners, fn)
	if state.Loaded then
		task.spawn(fn, state)
	end
	return function()
		local index = table.find(listeners, fn)
		if index then
			table.remove(listeners, index)
		end
	end
end

--- One setting's current value, always valid.
function StateController.setting(id: string): any
	local value = state.Settings[id]
	if value == nil then
		local entry = SettingsCore.specById(id)
		return entry and entry.Default
	end
	return value
end

--- Changes a setting: applied locally at once so the UI is never waiting on a
--- round trip, and sent to the server, which validates it again and is the
--- one that persists it. A rejected value is simply never saved -- the client
--- is a mirror, not a source (AGENTS.md rule 5).
function StateController.applySetting(id: string, value: any): boolean
	local decision = SettingsCore.validate(id, value)
	if not decision.ok then
		return false
	end
	state.Settings[id] = decision.value
	Net.get("Settings_Update"):FireServer({ Id = id, Value = decision.value })
	notify()
	return true
end

function StateController.init(): ()
	Net.get("Profile_Loaded").OnClientEvent:Connect(function(snapshot)
		state.FatePoints = snapshot.FatePoints
		state.FateLevel = snapshot.FateLevel
		state.TotalRolls = snapshot.TotalRolls
		state.Progress = snapshot.Progress
		state.Stats = snapshot.Stats
		state.Settings = SettingsCore.sanitise(snapshot.Settings)
		state.RedeemedCodes = snapshot.RedeemedCodes or {}
		state.Loaded = true
		notify()
	end)

	Net.get("Progression_FateChanged").OnClientEvent:Connect(function(payload)
		state.FatePoints = payload.FatePoints
		state.FateLevel = payload.FateLevel
		state.Progress = payload.Progress
		notify()
	end)

	Net.get("Fate_RollResult").OnClientEvent:Connect(function()
		state.TotalRolls += 1
		notify()
	end)
end

return StateController
