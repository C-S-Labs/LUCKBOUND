--!strict
-- Global announcements and live events. Build spec §4.1.
--
-- THE LATE-JOINER RULE, restated because it is the easy thing to get wrong:
-- FireAllClients only reaches people who are already here. Every broadcast in
-- this module is therefore a side effect of mutating EventCore state, and
-- every joining player is handed a snapshot of that state. A player who joins
-- a server four minutes into a five-minute Starfall sees the Starfall, with
-- one minute left on the clock.
--
-- Cross-server (Master Spec §12: "reality has been altered" everywhere) runs
-- over MessagingService. Each server applies the event to its own state, so a
-- player joining ANY server mid-Fatebreak still gets the correct picture.

local MessagingService = game:GetService("MessagingService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local EventCore = require(Root.Core.EventCore)
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)

local EventSystem = {}

local state = EventCore.newState()
local serverId = game.JobId ~= "" and game.JobId or "studio"

--- Sends the full live-event picture to one player. Called on join.
function EventSystem.syncTo(player: Player): ()
	Net.get("Event_StateSync"):FireClient(player, EventCore.snapshot(state, os.time(), GameConfig))
end

--- Records an announcement in state, then broadcasts it. Order matters: state
--- first, so a player joining between the two still sees it.
function EventSystem.announce(announcement: any): ()
	local now = os.time()
	EventCore.pushAnnouncement(state, {
		Kind = announcement.Kind,
		Text = announcement.Text,
		Rarity = announcement.Rarity,
		PlayerName = announcement.PlayerName,
		At = now,
	}, now, GameConfig)

	Net.get("Announce_Global"):FireAllClients({
		Kind = announcement.Kind,
		Text = announcement.Text,
		Rarity = announcement.Rarity,
		PlayerName = announcement.PlayerName,
		AgeSeconds = 0,
	})
end

--- Starts a live event on THIS server and tells everyone currently here.
--- Late joiners pick it up through syncTo.
function EventSystem.startLocal(event: any): ()
	local now = os.time()
	local live = EventCore.startEvent(state, {
		Id = event.Id,
		Kind = event.Kind,
		Name = event.Name,
		StartedAt = event.StartedAt or now,
		EndsAt = (event.StartedAt or now) + (event.Duration or GameConfig.Events.FatebreakDurationSeconds),
		TriggeredBy = event.TriggeredBy,
		DiscoveryId = event.DiscoveryId,
	})

	EventSystem.announce({
		Kind = "FATEBREAK",
		Text = `FATEBREAK! {live.TriggeredBy or "Someone"} has discovered {live.Name}. Reality has been altered.`,
		Rarity = event.Rarity or "UNKNOWN",
		PlayerName = live.TriggeredBy or "",
	})

	for _, player in Players:GetPlayers() do
		EventSystem.syncTo(player)
	end
end

--- Triggers a Fatebreak across every server. Master Spec §12.
function EventSystem.triggerFatebreak(event: any): ()
	local payload = {
		Origin = serverId,
		Id = event.Id,
		Kind = "FATEBREAK",
		Name = event.Name,
		Rarity = event.Rarity,
		TriggeredBy = event.TriggeredBy,
		DiscoveryId = event.DiscoveryId,
		StartedAt = os.time(),
		Duration = event.Duration or GameConfig.Events.FatebreakDurationSeconds,
	}

	EventSystem.startLocal(payload)

	local ok, err = pcall(function()
		MessagingService:PublishAsync(GameConfig.Events.CrossServerTopic, payload)
	end)
	if not ok then
		warn(`[EventSystem] cross-server publish failed: {err}`)
	end
end

function EventSystem.init(): ()
	local ok, err = pcall(function()
		MessagingService:SubscribeAsync(GameConfig.Events.CrossServerTopic, function(message)
			local payload = message.Data
			if type(payload) ~= "table" or payload.Origin == serverId then
				return -- we already applied our own
			end
			-- StartedAt is preserved, so every server counts down to the same
			-- wall-clock end and a late joiner anywhere sees the same clock.
			EventSystem.startLocal(payload)
		end)
	end)
	if not ok then
		warn(`[EventSystem] cross-server subscribe failed (expected in Studio without API access): {err}`)
	end

	-- Sweep expired events so snapshots stay accurate and clients are told
	-- when something ends.
	task.spawn(function()
		while true do
			task.wait(5)
			local ended = EventCore.expire(state, os.time())
			if #ended > 0 then
				for _, player in Players:GetPlayers() do
					EventSystem.syncTo(player)
				end
			end
		end
	end)
end

--- Exposed for tests and for the bootstrap's join handler.
function EventSystem._state()
	return state
end

return EventSystem
