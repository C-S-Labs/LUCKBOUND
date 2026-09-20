--!strict
-- The client's mirror of what is happening to the world. Build spec §4.1.
--
-- WHY THE CLIENT EXPIRES EVENTS ITSELF. The server tells you an event is
-- running and how many seconds are left; it does NOT promise to tell you when
-- it ends. Cross-server messages are lossy, a server can die mid-event, and a
-- dropped "it's over" leaves the sky cracked until the player rejoins. So the
-- deadline arrives with the event and this module counts it down locally: the
-- world heals itself without anyone having to say so.
--
-- The snapshot sends RemainingSeconds rather than an absolute time, precisely
-- so a client with a skewed clock still counts down correctly (EventCore
-- .snapshot). That is why the deadline below is built from os.clock() at the
-- moment of arrival rather than from anything the server said about "now".

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local EventCore = require(Root.Core.EventCore)
local Net = require(Root.Core.Net)

local EventController = {}

type LocalEvent = {
	Id: string,
	Kind: string,
	Name: string,
	Scope: string,
	WorldId: string?,
	Priority: number?,
	TriggeredBy: string?,
	StartedAt: number, -- local clock, for the precedence tiebreak
	ExpiresAt: number, -- local clock
}

local active: { [string]: LocalEvent } = {}
local listeners: { ({ LocalEvent }) -> () } = {}

local function list(): { LocalEvent }
	local out = {}
	for _, event in active do
		table.insert(out, event)
	end
	table.sort(out, function(a, b)
		return a.Id < b.Id
	end)
	return out
end

local function notify()
	local snapshot = list()
	for _, fn in listeners do
		task.spawn(fn, snapshot)
	end
end

--- Everything running right now, oldest-first by Id for determinism.
function EventController.active(): { LocalEvent }
	return list()
end

--- The one event that owns the sky and the menu's tint, or nil.
--- `worldId` is the biome the viewer is inside, or nil in the hub -- a BIOME
--- event is invisible to anyone outside it.
function EventController.dominant(worldId: string?): any
	return EventCore.dominant(list() :: any, { WorldId = worldId })
end

function EventController.onChanged(fn: ({ LocalEvent }) -> ()): () -> ()
	table.insert(listeners, fn)
	task.spawn(fn, list())
	return function()
		local index = table.find(listeners, fn)
		if index then
			table.remove(listeners, index)
		end
	end
end

local function apply(payload: any)
	if type(payload) ~= "table" then
		return
	end

	local now = os.clock()
	local seen: { [string]: boolean } = {}
	local changed = false

	for _, event in payload.ActiveEvents or {} do
		if type(event.Id) ~= "string" then
			continue
		end
		seen[event.Id] = true
		local existing = active[event.Id]
		local deadline = now + math.max(0, event.RemainingSeconds or 0)

		if not existing then
			changed = true
		end

		active[event.Id] = {
			Id = event.Id,
			Kind = event.Kind,
			Name = event.Name,
			-- An event from an older server build carries no Scope. Treating
			-- it as SERVER keeps it visible without letting it claim the
			-- whole game, which is the same default the server applies.
			Scope = if EventCore.isValidScope(event.Scope) then event.Scope else "SERVER",
			WorldId = event.WorldId,
			Priority = event.Priority,
			TriggeredBy = event.TriggeredBy,
			StartedAt = now - math.max(0, event.ElapsedSeconds or 0),
			ExpiresAt = deadline,
		}
	end

	-- A full snapshot is authoritative: anything it does not mention has
	-- ended. Without this, an event that ends while the player is loading
	-- would never clear.
	if payload.IsSnapshot then
		for id in active do
			if not seen[id] then
				active[id] = nil
				changed = true
			end
		end
	end

	if changed or next(seen) ~= nil then
		notify()
	end
end

function EventController.init(): ()
	Net.get("Event_StateSync").OnClientEvent:Connect(function(snapshot)
		if type(snapshot) == "table" then
			snapshot.IsSnapshot = true
		end
		apply(snapshot)
	end)

	-- THE SELF-HEAL. One pass a second, not per frame: the only thing it can
	-- change is whether a deadline has passed.
	local accumulated = 0
	RunService.Heartbeat:Connect(function(dt)
		accumulated += dt
		if accumulated < 1 then
			return
		end
		accumulated = 0

		local now = os.clock()
		local expired = false
		for id, event in active do
			if now >= event.ExpiresAt then
				active[id] = nil
				expired = true
			end
		end
		if expired then
			notify()
		end
	end)
end

return EventController
