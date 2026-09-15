--!strict
-- The single client-side mirror of server state. Build spec T-114.
-- UI modules read from here and never hold their own copy, so there is one
-- answer to "what is my Fate level?" on the client.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Net = require(Root.Core.Net)

local StateController = {}

local state = {
	FatePoints = 0,
	FateLevel = 1,
	TotalRolls = 0,
	Progress = 0,
	Stats = nil :: any,
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

function StateController.init(): ()
	Net.get("Profile_Loaded").OnClientEvent:Connect(function(snapshot)
		state.FatePoints = snapshot.FatePoints
		state.FateLevel = snapshot.FateLevel
		state.TotalRolls = snapshot.TotalRolls
		state.Progress = snapshot.Progress
		state.Stats = snapshot.Stats
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
