--!strict
-- Pure expedition logic. No Roblox globals, no Instances, no side effects --
-- so every rule below runs in CI and there is exactly one place that answers
-- "may this player enter, where are they going, and how long do they have?"
--
-- ExpeditionSystem (server) owns the plumbing: remotes, geometry, teleports,
-- timers. This file owns the decisions. Same split as FateCore/FateSystem, and
-- for the same reason: the decisions are what break, and plumbing cannot be
-- tested without Roblox.

local ExpeditionCore = {}

export type EntryRefusal =
	"DISABLED" -- GameConfig.Expedition.Enabled is false
	| "NO_DESTINATION" -- the player has not rolled yet
	| "UNKNOWN_WORLD" -- their last roll names a world that no longer exists
	| "NO_KIT" -- the world has no chunk kit, so no map can be built
	| "ALREADY_IN_EXPEDITION"
	| "COOLDOWN"
	| "TOO_FAR"
	| "SERVER_FULL" -- every stage slot is occupied

export type EntryDecision = {
	Allowed: boolean,
	WorldId: string?,
	Refusal: EntryRefusal?,
}

--- The player's pending destination is simply THEIR LAST ROLL.
---
--- No new state, no schema bump, and it survives a rejoin for free because
--- RollHistory is already persisted. It is also the game's own fiction: you
--- roll, and then you go. Rolling again replaces where you are going, which
--- is exactly what a player would expect.
function ExpeditionCore.destinationFrom(profile: any): string?
	local history = profile and profile.RollHistory
	if type(history) ~= "table" or #history == 0 then
		return nil
	end
	local last = history[#history]
	return if type(last) == "table" and type(last.WorldId) == "string"
		then last.WorldId
		else nil
end

--- True when `worldId` has at least one chunk, i.e. a map can be assembled.
--- A world with no kit is not a bug -- Sky Citadel has none by design today --
--- but it must be refused at the door rather than crashing the assembler.
function ExpeditionCore.hasKit(chunks: { [string]: any }, worldId: string): boolean
	for _, chunk in chunks do
		if chunk.WorldId == worldId then
			return true
		end
	end
	return false
end

--- Every world a player can currently roll that has no chunk kit.
---
--- This is the Sky Citadel debt made visible: it is printed at boot, so the
--- gap between "rollable" and "enterable" can never quietly grow. Sorted, so
--- the boot log is stable across restarts.
function ExpeditionCore.worldsWithoutKits(
	worlds: { [string]: any },
	chunks: { [string]: any },
	currentPhase: number
): { string }
	local missing = {}
	for id, world in worlds do
		if world.EnabledInPhase <= currentPhase and not ExpeditionCore.hasKit(chunks, id) then
			table.insert(missing, id)
		end
	end
	table.sort(missing)
	return missing
end

--- How many connective chunks this world's map should have. Content wins over
--- config: a world with a short expedition needs a short map, or the whole
--- expedition is the walk.
function ExpeditionCore.pathLengthFor(world: any, config: any): number
	return world.MapPathLength or config.Expedition.PathLength
end

function ExpeditionCore.durationFor(world: any, config: any): number
	return world.DurationSeconds or config.Expedition.DefaultDurationSeconds
end

--- Per-expedition seed. Deterministic from facts already recorded server-side,
--- so any expedition can be rebuilt exactly from its log line -- which is what
--- addendum §A4 asks for, and the same argument as §3.4.6 makes for rolls:
--- "the map was rigged" needs a verifiable answer.
---
--- Kept inside 2^31 so it survives being carried through a float without
--- losing precision.
function ExpeditionCore.seedFor(userId: number, rollNumber: number, worldId: string): number
	local hash = 0
	for i = 1, #worldId do
		hash = (hash * 31 + string.byte(worldId, i)) % 2147483647
	end
	local mixed = (userId % 2147483647) * 1000003 + rollNumber * 7919 + hash
	return mixed % 2147483647
end

--- One random stream per assembly attempt, derived from the expedition seed.
--- Attempt N must not reproduce attempt N-1's failure, but the whole sequence
--- must still be reproducible from the one seed.
function ExpeditionCore.streamFor(seed: number, attempt: number): () -> number
	local state = (seed + attempt * 2654435761) % 2147483647
	if state <= 0 then
		state += 2147483646
	end
	return function(): number
		state = (state * 16807) % 2147483647
		return (state - 1) / 2147483646
	end
end

--- Seconds left. Clamped at zero, and derived from elapsed time rather than a
--- stored end time so a client with a skewed clock still counts down correctly
--- (build spec §4.1 rule 4).
function ExpeditionCore.remaining(startedAt: number, duration: number, now: number): number
	return math.max(0, duration - (now - startedAt))
end

--- The first free stage slot, or nil when the server is full. Slots are reused
--- as expeditions end, so a long-running server does not drift off into space.
function ExpeditionCore.freeSlot(occupied: { [number]: boolean }, maxConcurrent: number): number?
	for slot = 1, maxConcurrent do
		if not occupied[slot] then
			return slot
		end
	end
	return nil
end

--- Where stage `slot` is built. Plain numbers, so the offset maths is testable
--- without Vector3.
function ExpeditionCore.stageOffset(slot: number, spacing: number): (number, number, number)
	return (slot - 1) * spacing, 0, 0
end

--- The ENTRY chunk of a layout -- where the player arrives and where the
--- return portal goes.
function ExpeditionCore.entryChunk(layout: any): any?
	for _, chunk in layout.Chunks do
		if chunk.Role == "ENTRY" then
			return chunk
		end
	end
	return nil
end

--- The whole entry decision, in one place and in a fixed order.
---
--- Order matters: cheap and non-revealing checks first. Cooldown and distance
--- are the anti-spam guards (build spec §3.4) and come before anything that
--- reads content, so a spamming client costs the server almost nothing.
function ExpeditionCore.evaluateEntry(opts: {
	Profile: any,
	Worlds: { [string]: any },
	Chunks: { [string]: any },
	Config: any,
	Now: number,
	LastEntryAt: number?,
	AlreadyActive: boolean,
	DistanceToGate: number?,
	FreeSlot: number?,
}): EntryDecision
	local config = opts.Config

	if not config.Expedition.Enabled then
		return { Allowed = false, Refusal = "DISABLED" }
	end

	if opts.AlreadyActive then
		return { Allowed = false, Refusal = "ALREADY_IN_EXPEDITION" }
	end

	local last = opts.LastEntryAt
	if last and opts.Now - last < config.Expedition.EntryCooldownSeconds then
		return { Allowed = false, Refusal = "COOLDOWN" }
	end

	-- nil distance means the Gate is not in the Workspace at all (a place
	-- without a built hub). Treat that as "cannot check" rather than "too
	-- far", exactly as FateSystem does for the roll anchor.
	local distance = opts.DistanceToGate
	if distance ~= nil and distance > config.Expedition.MaxEntryDistance then
		return { Allowed = false, Refusal = "TOO_FAR" }
	end

	local worldId = ExpeditionCore.destinationFrom(opts.Profile)
	if not worldId then
		return { Allowed = false, Refusal = "NO_DESTINATION" }
	end

	local world = opts.Worlds[worldId]
	if not world then
		return { Allowed = false, Refusal = "UNKNOWN_WORLD" }
	end

	if not ExpeditionCore.hasKit(opts.Chunks, worldId) then
		return { Allowed = false, WorldId = worldId, Refusal = "NO_KIT" }
	end

	if opts.FreeSlot == nil then
		return { Allowed = false, WorldId = worldId, Refusal = "SERVER_FULL" }
	end

	return { Allowed = true, WorldId = worldId }
end

--- Player-facing text for a refusal. Only two of these are ever shown: the
--- rest are exploit guards and stay silent, on the same reasoning as build
--- spec §3.4.3 -- telling a client where the boundary is tells an exploiter
--- where the boundary is.
function ExpeditionCore.refusalMessage(refusal: EntryRefusal): string?
	if refusal == "NO_DESTINATION" then
		return "Roll at the Fate Engine first."
	elseif refusal == "NO_KIT" then
		return "That world has no map yet."
	end
	return nil
end

return ExpeditionCore
