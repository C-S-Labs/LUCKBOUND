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
local Events = require(Root.Content.Events)
local EventCore = require(Root.Core.EventCore)
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)
local Result = require(Root.Core.Result)

local EventSystem = {}

local state = EventCore.newState()
local serverId = game.JobId ~= "" and game.JobId or "studio"
local LedgerSystem: any = nil

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
		-- An event with no stated reach is a SERVER event: the narrowest
		-- honest answer. Defaulting to GLOBAL would let a missing field
		-- announce itself to the whole game.
		Scope = event.Scope or "SERVER",
		WorldId = event.WorldId,
		Priority = event.Priority,
		StartedAt = event.StartedAt or now,
		EndsAt = (event.StartedAt or now)
			+ (event.Duration or GameConfig.Events.FatebreakDurationSeconds),
		TriggeredBy = event.TriggeredBy,
		DiscoveryId = event.DiscoveryId,
	})

	EventSystem.announce({
		Kind = live.Kind,
		-- Content writes the line when it has one (EventSystem.trigger fills
		-- the placeholders). The fallback is for the older callers that
		-- predate events being content.
		Text = event.Text
			or `FATEBREAK! {live.TriggeredBy or "Someone"} has discovered {live.Name}. Reality has been altered.`,
		Rarity = event.Rarity or "UNKNOWN",
		PlayerName = live.TriggeredBy or "",
	})

	for _, player in Players:GetPlayers() do
		EventSystem.syncTo(player)
	end
end

--- Starts an event HERE and on every other server. Master Spec §12.
---
--- Cross-server delivery is best-effort by nature: MessagingService is lossy,
--- rate-limited, and reaches only servers that are running and subscribed. It
--- is the right tool for spectacle and the wrong one for anything that has to
--- be counted -- which is why a unique is claimed from the ledger BEFORE this
--- is ever called.
function EventSystem.publish(event: any): ()
	local payload = {
		Origin = serverId,
		Id = event.Id,
		Kind = event.Kind or "FATEBREAK",
		Name = event.Name,
		Text = event.Text,
		-- A Fatebreak is game-wide by definition (Master Spec §12: reality has
		-- been altered EVERYWHERE), so it is the one caller that overrides the
		-- SERVER default.
		Scope = event.Scope or "GLOBAL",
		WorldId = event.WorldId,
		Priority = event.Priority,
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

--- STARTS AN AUTHORED EVENT, BY ITS CONTENT ID. The one entry point content
--- should use; `startLocal` and `triggerFatebreak` are the plumbing under it.
---
--- THE ORDER IS THE WHOLE POINT for an event that grants a unique:
---
---     CLAIM FIRST. ANNOUNCE SECOND.
---
--- A Catalyst Star that announces and then records will, on a busy day,
--- announce eleven of ten -- to every server, with no way to take it back.
--- So the ledger is asked first, and a refusal means nothing happened at all:
--- no event, no sky, no announcement. A player whose claim lost the race
--- simply did not find one (docs/EVENTS.md §5.5).
---
--- Returns Result.ok(live event) or Result.err(reason).
function EventSystem.trigger(definitionId: string, player: Player?): any
	local definition = Events[definitionId]
	if not definition then
		return Result.err(`unknown event '{definitionId}'`)
	end

	local remaining: number? = nil

	if definition.Unique then
		if not LedgerSystem then
			return Result.err("UNAVAILABLE")
		end
		if not player then
			return Result.err("a unique event needs a claimant")
		end

		local claim = LedgerSystem.claim(definition.Unique.LedgerId, definition.Unique.Cap, player)
		if not claim.ok then
			return Result.err(claim.err)
		end
		remaining = claim.value.Remaining
	end

	local payload = {
		Id = `{definition.Id}_{os.time()}`,
		Kind = definition.Kind,
		Name = definition.Name,
		Scope = definition.Scope,
		WorldId = definition.WorldId,
		Priority = definition.Priority,
		Duration = definition.DurationSeconds,
		TriggeredBy = if player then player.Name else nil,
		Rarity = definition.Announcement and definition.Announcement.Rarity or "UNKNOWN",
		Text = EventCore.formatAnnouncement(
			definition.Announcement and definition.Announcement.Text or "{event}",
			{
				Player = if player then player.Name else "Someone",
				Event = definition.Name,
				Remaining = remaining or 0,
			}
		),
		StartedAt = os.time(),
	}

	if definition.Scope == "GLOBAL" then
		EventSystem.publish(payload)
	else
		EventSystem.startLocal(payload)
	end

	return Result.ok(payload)
end

--- Ends every live event on this server. Developer tooling only -- the game
--- itself ends an event by letting its EndsAt arrive, which is what clients
--- count down to locally (EventController). Returns how many were stopped.
function EventSystem.endAll(): number
	local count = 0
	for id in state.ActiveEvents do
		state.ActiveEvents[id] = nil
		count += 1
	end
	if count > 0 then
		for _, player in Players:GetPlayers() do
			EventSystem.syncTo(player)
		end
	end
	return count
end

--- Kept as the name Master Spec §12 and FateSystem already use. A Fatebreak
--- is one global event among several now, rather than the only one.
function EventSystem.triggerFatebreak(event: any): ()
	EventSystem.publish(event)
end

function EventSystem.init(ledgerSystem: any?): ()
	LedgerSystem = ledgerSystem
	-- SubscribeAsync YIELDS. pcall catches its errors but does nothing about it
	-- hanging, and on an unpublished place it never returns -- which blocked
	-- the whole bootstrap before the hub was ever built. Cross-server delivery
	-- is a nice-to-have; world creation is not. So it runs on its own thread
	-- and the bootstrap moves on immediately.
	task.spawn(function()
		local ok, err = pcall(function()
			MessagingService:SubscribeAsync(GameConfig.Events.CrossServerTopic, function(message)
				local payload = message.Data
				if type(payload) ~= "table" or payload.Origin == serverId then
					return -- we already applied our own
				end
				-- StartedAt is preserved, so every server counts down to the
				-- same wall-clock end and a late joiner anywhere sees the
				-- same clock.
				EventSystem.startLocal(payload)
			end)
		end)
		if ok then
			print("[EventSystem] cross-server Fatebreaks active")
		else
			warn(
				`[EventSystem] cross-server subscribe unavailable (expected on an unpublished place): {err}`
			)
		end
	end)

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
