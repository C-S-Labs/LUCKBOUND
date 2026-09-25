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
	| "NO_MAP" -- the world has neither a chunk kit nor a prebuilt map
	| "ALREADY_IN_EXPEDITION"
	| "COOLDOWN"
	| "TOO_FAR"
	| "SERVER_FULL" -- every stage slot is occupied
	| "NOT_PARTY_LEADER" -- in a party, and only the leader opens the portal

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
	return if type(last) == "table" and type(last.WorldId) == "string" then last.WorldId else nil
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

--- True when the world ships a hand-authored map instead of a chunk kit.
---
--- THE TWO WAYS A WORLD GETS A MAP. Generated worlds declare a kit and the
--- assembler lays it out; authored worlds declare one composed scene and the
--- loader clones it. Ethereal Scape is the first of the second kind, because
--- its art is a composed traverse -- see the comment on its PrebuiltMap.
---
--- Which kind a world is, is DATA. Nothing downstream branches on a world id.
function ExpeditionCore.hasPrebuiltMap(world: any): boolean
	return type(world) == "table" and type(world.PrebuiltMap) == "table"
end

--- True when the world can produce a map at all, by either route. This is the
--- question the door actually asks; `hasKit` answers the narrower one.
function ExpeditionCore.hasMap(world: any, chunks: { [string]: any }, worldId: string): boolean
	return ExpeditionCore.hasPrebuiltMap(world) or ExpeditionCore.hasKit(chunks, worldId)
end

--- Every world a player can currently roll that has no map by either route.
---
--- This is the Sky Citadel debt made visible: it is printed at boot, so the
--- gap between "rollable" and "enterable" can never quietly grow. Sorted, so
--- the boot log is stable across restarts.
function ExpeditionCore.worldsWithoutMaps(
	worlds: { [string]: any },
	chunks: { [string]: any },
	currentPhase: number
): { string }
	local missing = {}
	for id, world in worlds do
		if
			world.EnabledInPhase <= currentPhase and not ExpeditionCore.hasMap(world, chunks, id)
		then
			table.insert(missing, id)
		end
	end
	table.sort(missing)
	return missing
end

--- How many connective chunks this world's map should have. Content wins over
--- config: a world with a short expedition needs a short map, or the whole
--- expedition is the walk. Meaningless for a prebuilt world, which is why
--- those declare no MapPathLength and never reach the assembler.
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
function ExpeditionCore.evaluateEntry(
	opts: {
		Profile: any,
		Worlds: { [string]: any },
		Chunks: { [string]: any },
		Config: any,
		Now: number,
		LastEntryAt: number?,
		AlreadyActive: boolean,
		DistanceToGate: number?,
		FreeSlot: number?,
		-- From PartyCore.expeditionGroup. nil and "SOLO" mean the same thing.
		PartyRole: string?,
	}
): EntryDecision
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

	-- A member walking into the portal would either split the party or drag
	-- it somewhere the leader did not choose. Neither is theirs to decide.
	if opts.PartyRole == "MEMBER" then
		return { Allowed = false, Refusal = "NOT_PARTY_LEADER" }
	end

	local worldId = ExpeditionCore.destinationFrom(opts.Profile)
	if not worldId then
		return { Allowed = false, Refusal = "NO_DESTINATION" }
	end

	local world = opts.Worlds[worldId]
	if not world then
		return { Allowed = false, Refusal = "UNKNOWN_WORLD" }
	end

	if not ExpeditionCore.hasMap(world, opts.Chunks, worldId) then
		return { Allowed = false, WorldId = worldId, Refusal = "NO_MAP" }
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
	elseif refusal == "NO_MAP" then
		return "That world has no map yet."
	elseif refusal == "NOT_PARTY_LEADER" then
		return "Your party leader opens the portal."
	end
	return nil
end

-- === EXPEDITIONS AS THEIR OWN SERVER (build spec §7.2) ================

--- "TELEPORT" or "IN_PLACE". AUTO teleports everywhere except Studio, where
--- TeleportService cannot run -- so a Studio session still walks the whole
--- loop, parties included, and a live server always gets its own instance.
function ExpeditionCore.instanceMode(config: any, isStudio: boolean): string
	local mode = config.Expedition.InstanceMode
	if mode == "TELEPORT" or mode == "IN_PLACE" then
		return mode
	end
	return if isStudio then "IN_PLACE" else "TELEPORT"
end

--- True when this server is an expedition instance rather than a hub.
---
--- A reserved server has a PrivateServerId and NO owner. A VIP server has
--- both, and is a hub someone paid for; a public server has neither. So the
--- owner check is what stops a private server being mistaken for an
--- expedition and sending its players home.
function ExpeditionCore.isExpeditionServer(
	privateServerId: string,
	privateServerOwnerId: number
): boolean
	return privateServerId ~= "" and privateServerOwnerId == 0
end

--- The place a teleport targets: the configured one, or this place when the
--- config says 0.
function ExpeditionCore.placeFor(configuredId: number, currentPlaceId: number): number
	return if configuredId and configuredId > 0 then configuredId else currentPlaceId
end

--- EVERYTHING AN EXPEDITION SERVER NEEDS TO BUILD THE SAME MAP.
---
--- Written by the hub to MemoryStore under the reserved server's id, read by
--- that server on boot. The seed and world are the leader's, which is what
--- makes a party's map identical for everyone in it. Each member's OWN
--- profile -- level, Fate, history -- follows them through SaveSystem and is
--- never in here.
---
--- `HubJobId` is the hub server they left, so they can be sent back to the
--- same one and find their party where they left it.
function ExpeditionCore.buildManifest(opts: {
	WorldId: string,
	Seed: number,
	DurationSeconds: number,
	LeaderUserId: number,
	Members: { number },
	HubPlaceId: number,
	HubJobId: string,
	CreatedAt: number,
})
	return {
		Version = 1,
		WorldId = opts.WorldId,
		Seed = opts.Seed,
		DurationSeconds = opts.DurationSeconds,
		LeaderUserId = opts.LeaderUserId,
		Members = table.clone(opts.Members),
		HubPlaceId = opts.HubPlaceId,
		HubJobId = opts.HubJobId,
		CreatedAt = opts.CreatedAt,
	}
end

--- Checks a manifest read back from MemoryStore before any of it is used.
--- It came from our own server, but through a store, and a half-written or
--- stale entry must fail here rather than as a nil index halfway through a
--- map build.
function ExpeditionCore.validateManifest(
	manifest: any,
	worlds: { [string]: any },
	chunks: { [string]: any }
)
	if type(manifest) ~= "table" then
		return false, "manifest missing"
	end
	if manifest.Version ~= 1 then
		return false, `unknown manifest version {tostring(manifest.Version)}`
	end
	local worldId = manifest.WorldId
	if type(worldId) ~= "string" or not worlds[worldId] then
		return false, `unknown world {tostring(worldId)}`
	end
	if not ExpeditionCore.hasMap(worlds[worldId], chunks, worldId) then
		return false, `{worldId} has no map`
	end
	if
		type(manifest.Seed) ~= "number"
		or type(manifest.DurationSeconds) ~= "number"
		or manifest.DurationSeconds <= 0
	then
		return false, "bad seed or duration"
	end
	if
		type(manifest.LeaderUserId) ~= "number"
		or type(manifest.Members) ~= "table"
		or #manifest.Members == 0
	then
		return false, "no members"
	end
	if not table.find(manifest.Members, manifest.LeaderUserId) then
		return false, "leader is not a member"
	end
	return true, nil
end

--- Only the players the hub sent may stay. Anyone else who reaches a
--- reserved server is sent home.
function ExpeditionCore.isManifestMember(manifest: any, userId: number): boolean
	return type(manifest) == "table"
		and type(manifest.Members) == "table"
		and table.find(manifest.Members, userId) ~= nil
end

--- Where the Nth arrival stands: a small ring around the entry point, so a
--- party does not spawn inside itself. Index 1 is the centre.
function ExpeditionCore.arrivalOffset(index: number, radius: number): (number, number)
	if index <= 1 then
		return 0, 0
	end
	local angle = (index - 2) * (math.pi / 3)
	return math.cos(angle) * radius, math.sin(angle) * radius
end

return ExpeditionCore
