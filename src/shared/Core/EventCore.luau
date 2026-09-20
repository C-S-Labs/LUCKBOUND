--!strict
-- Pure live-event state. Build spec §4.1.
--
-- THE LATE-JOINER RULE
-- A RemoteEvent fired before a player joined is gone forever. So server state
-- is never "what I broadcast" -- it is a table held here, and every broadcast
-- is a side effect of changing that table. A player joining a server that is
-- already three minutes into a Starfall gets the same picture as everyone who
-- was there when it started, with the correct remaining time.
--
-- Anything a late joiner must see goes in this state. If you find yourself
-- firing a remote to "everyone" without touching this table, you have just
-- made something invisible to the next person through the door.

local EventCore = {}

export type LiveEvent = {
	Id: string,
	Kind: string, -- "FATEBREAK" | "STARFALL" | ...
	Name: string,
	-- HOW FAR THIS EVENT REACHES. "GLOBAL" is every server in the game,
	-- "SERVER" is this one, "BIOME" is everyone inside one world.
	--
	-- Scope is a FIELD rather than a flavour of Kind because the reach and the
	-- thing that happened are independent: the same aurora can be a one-server
	-- curiosity or a game-wide announcement, and content should be able to say
	-- so without a second Kind.
	Scope: string,
	WorldId: string?, -- BIOME scope only; which world it is confined to
	-- Ranking within a scope. The sky can only be one sky, so when two events
	-- overlap, EventCore.dominant decides which one owns it.
	Priority: number?,
	StartedAt: number,
	EndsAt: number,
	TriggeredBy: string?, -- player name, for the banner
	DiscoveryId: string?,
}

export type Announcement = {
	Kind: string, -- "ROLL" | "FATEBREAK" | "WORLD_FIRST"
	Text: string,
	Rarity: string,
	PlayerName: string,
	At: number,
}

export type State = {
	ActiveEvents: { [string]: LiveEvent },
	Announcements: { Announcement },
}

-- THE COMPLETE SET OF LIGHTING PROPERTIES ANYTHING MAY TOUCH, and the
-- content field name that maps to each. Stated once, here, because three
-- places depend on agreeing about it: the client that applies an event's
-- lighting, the client that snapshots and restores the hub's own, and the
-- validator that refuses an event declaring a property nobody restores.
--
-- The failure this prevents is specific and nasty: an event that sets a
-- property outside the restore list leaves it changed forever -- an aurora
-- that ends and leaves the fog green until the player rejoins.
EventCore.LIGHTING_PROPERTIES = table.freeze({
	Ambient = "Ambient",
	OutdoorAmbient = "OutdoorAmbient",
	ColorShiftTop = "ColorShift_Top",
	FogColor = "FogColor",
	FogStart = "FogStart",
	FogEnd = "FogEnd",
	Brightness = "Brightness",
	ClockTime = "ClockTime",
})

--- The same set as an array of Roblox property names, for snapshot/restore.
function EventCore.trackedLighting(): { string }
	local names = {}
	for _, property in EventCore.LIGHTING_PROPERTIES do
		table.insert(names, property)
	end
	table.sort(names)
	return names
end

--- Fills {player}, {event} and {remaining} into an announcement. Kept tiny on
--- purpose: an announcement can only reference things the server always has.
function EventCore.formatAnnouncement(template: string, values: any): string
	local text = string.gsub(template, "{player}", tostring(values.Player or "Someone"))
	text = string.gsub(text, "{event}", tostring(values.Event or ""))
	text = string.gsub(text, "{remaining}", tostring(values.Remaining or 0))
	return text
end

function EventCore.newState(): State
	return { ActiveEvents = {}, Announcements = {} }
end

--- Drops finished events. Call before every snapshot and on a timer.
--- Returns the ids that expired, so the caller can broadcast the end.
function EventCore.expire(state: State, now: number): { string }
	local ended = {}
	for id, event in state.ActiveEvents do
		if now >= event.EndsAt then
			table.insert(ended, id)
		end
	end
	for _, id in ended do
		state.ActiveEvents[id] = nil
	end
	table.sort(ended)
	return ended
end

function EventCore.startEvent(state: State, event: LiveEvent): LiveEvent
	state.ActiveEvents[event.Id] = event
	return event
end

-- How far an event reaches, ranked. A game-wide event is by definition the
-- biggest news on the screen, so scope outranks priority rather than
-- competing with it -- otherwise a high-priority local event could shout over
-- something happening to every player in the game.
local SCOPE_RANK: { [string]: number } = {
	GLOBAL = 3,
	SERVER = 2,
	BIOME = 1,
}

EventCore.SCOPE_RANK = SCOPE_RANK

function EventCore.isValidScope(scope: any): boolean
	return type(scope) == "string" and SCOPE_RANK[scope] ~= nil
end

--- WHICH EVENT OWNS THE SKY? Pure, total and deterministic.
---
--- There is one sky, one set of lighting properties and one menu tint, so
--- overlapping events cannot all have them. Exactly one event is dominant and
--- the rest contribute additive effects only -- which keeps "what colour is
--- the world right now" a function of state rather than of whichever
--- broadcast happened to land last.
---
--- The order is scope, then Priority, then the event that has been running
--- LONGEST, then Id. Longest-running rather than newest is deliberate: a tie
--- broken by recency would make the sky flip every time an equal event
--- started somewhere, and a sky that changes for no visible reason reads as a
--- bug. Id is the final tiebreak so the answer is identical on every client.
---
--- `context` is optional and filters by reach: { WorldId = <world the viewer
--- is inside, or nil for the hub> }. A BIOME event is invisible to anyone who
--- is not in that biome.
function EventCore.dominant(events: { LiveEvent }, context: any?): LiveEvent?
	local viewerWorld = if context then context.WorldId else nil
	local best: LiveEvent? = nil

	for _, event in events do
		local rank = SCOPE_RANK[event.Scope]
		if rank == nil then
			continue -- an unknown scope never owns the sky
		end
		if event.Scope == "BIOME" and event.WorldId ~= viewerWorld then
			continue
		end

		if best == nil then
			best = event
		else
			local current = best :: LiveEvent
			local bestRank = SCOPE_RANK[current.Scope]
			local bestPriority = current.Priority or 0
			local priority = event.Priority or 0

			local wins = false
			if rank ~= bestRank then
				wins = rank > bestRank
			elseif priority ~= bestPriority then
				wins = priority > bestPriority
			elseif event.StartedAt ~= current.StartedAt then
				wins = event.StartedAt < current.StartedAt
			else
				wins = event.Id < current.Id
			end

			if wins then
				best = event
			end
		end
	end

	return best
end

--- Appends an announcement and trims the buffer by size and age.
function EventCore.pushAnnouncement(
	state: State,
	announcement: Announcement,
	now: number,
	config: any
): ()
	table.insert(state.Announcements, announcement)

	local maxAge = config.Events.AnnouncementBufferMaxAgeSeconds
	local maxSize = config.Events.AnnouncementBufferSize

	local kept = {}
	for _, entry in state.Announcements do
		if now - entry.At <= maxAge then
			table.insert(kept, entry)
		end
	end

	while #kept > maxSize do
		table.remove(kept, 1)
	end

	state.Announcements = kept
end

--- Everything a joining client needs to render the current world state.
--- Remaining time is sent rather than EndsAt so a client with a skewed clock
--- still counts down correctly.
function EventCore.snapshot(state: State, now: number, config: any): any
	EventCore.expire(state, now)

	local events = {}
	for _, event in state.ActiveEvents do
		table.insert(events, {
			Id = event.Id,
			Kind = event.Kind,
			Name = event.Name,
			Scope = event.Scope,
			WorldId = event.WorldId,
			Priority = event.Priority,
			TriggeredBy = event.TriggeredBy,
			DiscoveryId = event.DiscoveryId,
			RemainingSeconds = math.max(0, event.EndsAt - now),
			ElapsedSeconds = math.max(0, now - event.StartedAt),
		})
	end
	table.sort(events, function(a, b)
		return a.Id < b.Id
	end)

	local announcements = {}
	for _, entry in state.Announcements do
		if now - entry.At <= config.Events.AnnouncementBufferMaxAgeSeconds then
			table.insert(announcements, {
				Kind = entry.Kind,
				Text = entry.Text,
				Rarity = entry.Rarity,
				PlayerName = entry.PlayerName,
				AgeSeconds = now - entry.At,
			})
		end
	end

	return { ActiveEvents = events, Announcements = announcements, ServerNow = now }
end

return EventCore
