--!strict
-- The client's picture of its party. Build spec §7.2.
--
-- Holds the last Party_Sync, tells anyone listening when it changes, and
-- sends requests. It decides nothing: whether an invite is allowed, who
-- leads, and who goes through the portal are all PartyCore, on the server.
-- The panel draws what this holds, and a button that the server would refuse
-- is refused there, with the reason sent back in the next sync.
--
-- INVITES ARRIVE WHEREVER THE PLAYER IS LOOKING. An invite that only showed
-- up inside a closed panel would be an invite nobody sees, so a new one also
-- raises Roblox's own notification with Accept and Decline on it.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterGui = game:GetService("StarterGui")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Net = require(Root.Core.Net)

local PartyController = {}

local EMPTY = table.freeze({
	PartyId = nil,
	LeaderUserId = nil,
	Members = {},
	IsLeader = false,
	Invites = {},
	MaxSize = 0,
	Names = {},
	Others = {},
})

local snapshot: any = EMPTY
local listeners: { (any) -> () } = {}
-- Invites already announced, so a re-sync does not raise the same one twice.
local announced: { [number]: boolean } = {}

function PartyController.get(): any
	return snapshot
end

--- Subscribe to changes. Fires immediately with the current picture, like
--- every other controller here, so a panel built late is never stale.
function PartyController.onChanged(fn: (any) -> ()): () -> ()
	table.insert(listeners, fn)
	task.spawn(fn, snapshot)
	return function()
		local index = table.find(listeners, fn)
		if index then
			table.remove(listeners, index)
		end
	end
end

function PartyController.nameOf(userId: number): string
	local names = snapshot.Names or {}
	return names[tostring(userId)] or `Player {userId}`
end

--- The only thing the client ever sends: an action name and, where needed,
--- the UserId it is about.
function PartyController.request(action: string, targetUserId: number?): ()
	Net.get("Party_Request"):FireServer({ Action = action, TargetUserId = targetUserId })
end

local function announceInvite(fromUserId: number, name: string)
	-- SendNotification's buttons report back through a BindableFunction.
	local callback = Instance.new("BindableFunction")
	callback.OnInvoke = function(choice: string)
		if choice == "Accept" then
			PartyController.request("ACCEPT", fromUserId)
		elseif choice == "Decline" then
			PartyController.request("DECLINE", fromUserId)
		end
		callback:Destroy()
		return nil
	end

	-- SetCore can refuse early in a session, before the core scripts have
	-- registered it; a few retries cover that without a busy loop.
	task.spawn(function()
		for _ = 1, 5 do
			local ok = pcall(function()
				StarterGui:SetCore("SendNotification", {
					Title = "Party invite",
					Text = `{name} invited you to their party.`,
					Duration = 20,
					Button1 = "Accept",
					Button2 = "Decline",
					Callback = callback,
				})
			end)
			if ok then
				return
			end
			task.wait(1)
		end
	end)
end

function PartyController.init(): ()
	Net.get("Party_Sync").OnClientEvent:Connect(function(payload)
		if type(payload) ~= "table" then
			return
		end
		snapshot = payload

		local live: { [number]: boolean } = {}
		for _, invite in payload.Invites or {} do
			live[invite.FromUserId] = true
			if not announced[invite.FromUserId] then
				announced[invite.FromUserId] = true
				announceInvite(invite.FromUserId, PartyController.nameOf(invite.FromUserId))
			end
		end
		-- Forget answered or lapsed invites, so the same player inviting
		-- again later is announced again.
		for fromUserId in announced do
			if not live[fromUserId] then
				announced[fromUserId] = nil
			end
		end

		for _, fn in listeners do
			task.spawn(fn, snapshot)
		end
	end)

	-- Named for the log only: a party survives this player's own respawns
	-- because it lives on the server.
	assert(Players.LocalPlayer, "PartyController needs a LocalPlayer")
end

return PartyController
