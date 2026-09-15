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
