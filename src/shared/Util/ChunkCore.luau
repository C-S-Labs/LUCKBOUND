--!strict
-- Seeded assembly of a map from a chunk library. Addendum §A4.
--
-- Procedural COMPOSITION, not procedural terrain: variety comes from arranging
-- a bounded library of authored, pre-validated pieces. That avoids the failure
-- modes §A4 flags for noise-generated landscape -- unreachable bosses, voxel
-- micro-gaps, and unpredictable mobile performance.
--
-- PURE. No Roblox globals, no Instances. Positions are plain numbers and yaw
-- is degrees, so a whole expedition layout can be generated and checked in CI
-- before any mesh exists. The loader turns a Layout into CFrames; this decides
-- what goes where.

local WeightedRandom = require(script.Parent.WeightedRandom)

local GenerationProfile = require(script.Parent.GenerationProfile)
local ChunkDefinitionCache = require(script.Parent.ChunkDefinitionCache)

local ChunkCore = {}

local QUARTER = { [0] = true, [90] = true, [180] = true, [270] = true }

--- Rotates a local offset about Y by an exact quarter turn.
local function rotate(x: number, z: number, yaw: number): (number, number)
	if yaw == 0 then
		return x, z
	elseif yaw == 90 then
		return -z, x
	elseif yaw == 180 then
		return -x, -z
	else
		return z, -x
	end
end

--- A layout yaw as the angle Roblox's CFrame.Angles(0, angle, 0) needs.
---
--- THE TWO TURN OPPOSITE WAYS. `rotate` above turns north into EAST at yaw 90
--- (clockwise seen from above), which is where every socket is placed.
--- CFrame.Angles(0, +90deg, 0) turns north into WEST. Feeding it the layout
--- yaw directly turned every mesh at yaw 90 or 270 half a turn away from its
--- own sockets -- right at 0 and 180, wrong at 90 and 270, so whether a piece
--- came out wrong depended on the seed. Every mesh CFrame goes through here.
function ChunkCore.yawRadians(yaw: number): number
	return -math.rad(yaw)
end

local function norm(deg: number): number
	return ((deg % 360) + 360) % 360
end

--- Every chunk of a world, grouped by Role.
function ChunkCore.libraryFor(chunks: { [string]: any }, worldId: string): { [string]: { any } }
	local byRole: { [string]: { any } } = {}
	local ordered = {}
	for _, chunk in chunks do
		if chunk.WorldId == worldId then
			table.insert(ordered, chunk)
		end
	end
	-- Stable order: hash iteration must not change what a seed produces.
	table.sort(ordered, function(a, b)
		return a.Id < b.Id
	end)
	for _, chunk in ordered do
		byRole[chunk.Role] = byRole[chunk.Role] or {}
		table.insert(byRole[chunk.Role], chunk)
	end
	return byRole
end

local function socketById(chunk: any, id: string): any?
	for _, s in chunk.Sockets do
		if s.Id == id then
			return s
		end
	end
	return nil
end

--- The world-space position and facing of a socket on a placed chunk.
function ChunkCore.worldSocket(placed: any, chunk: any, socket: any)
	local ox, oz = rotate(socket.OffsetX, socket.OffsetZ, placed.Yaw)
	return {
		Id = socket.Id,
		Kind = socket.Kind, -- carried through: matching is by Kind
		X = placed.X + ox,
		Y = placed.Y + socket.OffsetY,
		Z = placed.Z + oz,
		Facing = norm(socket.Facing + placed.Yaw),
	}
end

--- Places `chunk` so that one of its sockets meets `openSocket` head-on.
--- Returns the placement and the socket consumed, or nil if the chunk has no
--- socket of a matching Kind.
function ChunkCore.placeAgainst(
	chunk: any,
	openSocket: any,
	index: number,
	definition: any?
): (any?, any?)
	local wanted = norm(openSocket.Facing + 180)

	local sockets = if definition
		then definition.SocketsByKind[openSocket.Kind] or {}
		else chunk.Sockets
	for _, s in sockets do
		if s.Kind == openSocket.Kind then
			-- Yaw that turns this socket to face back down the corridor.
			local yaw = norm(wanted - s.Facing)
			if QUARTER[yaw] then
				local ox, oz = rotate(s.OffsetX, s.OffsetZ, yaw)
				return {
					ChunkId = chunk.Id,
					Role = chunk.Role,
					X = openSocket.X - ox,
					Y = openSocket.Y - s.OffsetY,
					Z = openSocket.Z - oz,
					Yaw = yaw,
					Index = index,
				},
					s
			end
		end
	end
	return nil, nil
end

--- The socket placeAgainst would arrive through: the first of a matching
--- Kind. Kept beside placeAgainst so the two cannot disagree.
function ChunkCore.arrivalSocket(chunk: any, openSocket: any): any?
	local wanted = norm(openSocket.Facing + 180)
	for _, s in chunk.Sockets do
		if s.Kind == openSocket.Kind and QUARTER[norm(wanted - s.Facing)] then
			return s
		end
	end
	return nil
end

--- Axis-aligned overlap between two placed chunks, with a small tolerance so
--- pieces that merely touch at a socket are not counted as colliding.
function ChunkCore.overlaps(a: any, chunkA: any, b: any, chunkB: any): boolean
	local TOL = 1
	local function extent(placed: any, chunk: any)
		-- A quarter turn swaps X and Z extents.
		local sx, sz = chunk.SizeX, chunk.SizeZ
		if placed.Yaw == 90 or placed.Yaw == 270 then
			sx, sz = sz, sx
		end
		return sx / 2, sz / 2
	end
	local ax, az = extent(a, chunkA)
	local bx, bz = extent(b, chunkB)
	return math.abs(a.X - b.X) < (ax + bx - TOL) and math.abs(a.Z - b.Z) < (az + bz - TOL)
end

export type AssembleOptions = {
	Profile: any?, -- explicit experiment context; nil preserves production
	WorldId: string,
	PathLength: number, -- chunks between entry and boss
	IncludeSide: boolean?,
	-- How many pieces a branch off a spare mouth may grow before it is capped.
	-- 0 or nil caps the mouth where it stands, which is what every layout did
	-- before 2026-09-23.
	BranchLength: number?,
	-- Cap on placements of any one non-CAP piece, on top of its MaxPerLayout.
	MaxRepeats: number?,
	-- Chunk Id -> a SpawnChance to use instead of the chunk's own. Developer
	-- testing only (/vaultchance); nil in play.
	SpawnOverrides: { [string]: number }?,
	-- Build spec §7.7 universal generation blueprint (WorldDefinition.Generation).
	-- nil runs the legacy passes below byte-for-byte, so a world that has not
	-- opted in assembles exactly the layouts it always did.
	Generation: {
		BranchLength: number?,
		Minibosses: number?,
		MaxSides: number?,
		Backdrop: number?,
		-- Target share of COMBAT pieces among the ordinary (PATH + COMBAT)
		-- pieces placed. While the map is below it, COMBAT pieces are favoured
		-- (CombatBoost x) on every pick, so the fight count scales with the
		-- map's size instead of being left to the raw weights.
		CombatShare: number?,
	}?,
}

--- Builds a layout: ENTRY → PathLength connective/combat chunks → BOSS,
--- optionally hanging one SIDE pocket off a spare socket.
---
--- EXITS ARE CHOSEN, NOT DEFAULTED. A piece with several valid exits leaves
--- through a seeded random one, so a crossroads can go straight, left or
--- right. Until 2026-09-22 this took the first valid socket, and a piece with
--- four openings left the same way on every seed.
---
--- SIDE POCKETS (IncludeSide). After the arena is placed, one SIDE chunk is
--- hung off a spare socket -- one the path neither arrived through nor left
--- through -- on any placed piece, tried in seeded order until one fits
--- without colliding. No fit is not a failure: the map is complete without
--- it. This is what makes an intersection mean something: the path takes one
--- branch, the pocket can sit on another.
---
--- CAPS (owner-directed 2026-09-22: "I don't want any paths to lead to
--- nothing"). If the world has CAP chunks -- one-socket dead ends authored as
--- dead ends: a crumbling bridge, an overlook, a sealed gate -- then every
--- socket still open after the path, arena and pocket gets one. A socket that
--- no cap can fill fails the attempt, and assembleWithRetry tries the next
--- seed: in a capped world a layout never ships an opening onto nothing. A
--- world with no CAP chunks keeps the old behaviour.
---
--- Returns ok, layout-or-error. Failure is a normal outcome, not an error:
--- a kit whose sockets cannot reach the boss is a content bug, and the caller
--- should reject the seed rather than ship a broken expedition.
function ChunkCore.assemble(
	chunks: { [string]: any },
	options: AssembleOptions,
	nextNumber: () -> number
): (boolean, any)
	local profile = options.Profile
	local byRole = ChunkCore.libraryFor(chunks, options.WorldId)
	local definitions = {}
	if profile and profile.Stage >= "C" then
		for _, list in byRole do
			for _, chunk in list do
				local definition, hit = ChunkDefinitionCache.get(chunk)
				definitions[chunk.Id] = definition
				GenerationProfile.count(
					profile,
					if hit then "DefinitionHits" else "DefinitionMisses"
				)
			end
		end
	end
	local function placeAgainst(chunk: any, openSocket: any, index: number): (any?, any?)
		GenerationProfile.count(profile, "CandidateAttempts")
		local placement, socket =
			ChunkCore.placeAgainst(chunk, openSocket, index, definitions[chunk.Id])
		if not placement then
			GenerationProfile.count(profile, "CompatibilityFailures")
		end
		return placement, socket
	end

	-- SPAWN CHANCE (build spec §7.5). A piece with SpawnChance is in this
	-- layout's library only if one seeded draw says so -- the treasury is in
	-- about one map in five. Drawn once per such piece, in Id order, BEFORE
	-- anything else, and only when a world has one: a kit without the field
	-- consumes no numbers, so its seeds build exactly what they always did.
	-- A piece that wins its draw is then strongly preferred wherever it fits,
	-- so "in one map in five" means placed, not merely eligible.
	local won: { [string]: boolean } = {}
	local chancy = {}
	local overrides = options.SpawnOverrides or {}
	local function chanceOf(c: any): number?
		local o = overrides[c.Id]
		return if o ~= nil then o else c.SpawnChance
	end
	for _, list in byRole do
		for _, c in list do
			local chance = chanceOf(c)
			if chance ~= nil and chance >= 1 and c.SpawnChance ~= nil then
				-- Forced in by an override: preferred, and no draw spent.
				won[c.Id] = true
			elseif chance ~= nil and chance < 1 then
				table.insert(chancy, c)
			end
		end
	end
	if #chancy > 0 then
		table.sort(chancy, function(a, b)
			return a.Id < b.Id
		end)
		local absent = {}
		for _, c in chancy do
			if nextNumber() >= (chanceOf(c) :: number) then
				absent[c.Id] = true
			else
				won[c.Id] = true
			end
		end
		for role, list in byRole do
			local kept = {}
			for _, c in list do
				if not absent[c.Id] then
					table.insert(kept, c)
				end
			end
			byRole[role] = kept
		end
	end

	-- Ordinary pieces placed so far, and how many of them are COMBAT (for the
	-- blueprint's CombatShare; see weightOf).
	local ordinaryPlaced, combatPlaced = 0, 0
	local combatShare = options.Generation and options.Generation.CombatShare
	local COMBAT_BOOST = 6

	local function weightOf(c: any): number
		local w = if won[c.Id] then c.Weight * 1000 else c.Weight
		if
			combatShare
			and c.Role == "COMBAT"
			and combatPlaced < combatShare * math.max(ordinaryPlaced + 1, 1)
		then
			w *= COMBAT_BOOST
		end
		return w
	end

	local entries = byRole.ENTRY
	local bosses = byRole.BOSS
	if not entries or #entries == 0 then
		return false, `world '{options.WorldId}' has no ENTRY chunk`
	end
	if not bosses or #bosses == 0 then
		return false, `world '{options.WorldId}' has no BOSS chunk`
	end

	local middle = {}
	for _, role in { "PATH", "COMBAT" } do
		for _, c in byRole[role] or {} do
			table.insert(middle, c)
		end
	end
	if #middle == 0 then
		return false, `world '{options.WorldId}' has no PATH or COMBAT chunks`
	end

	local placed: { any } = {}
	local used: { [string]: number } = {}
	-- Per placed piece: which of its sockets the path consumed. The rest are
	-- spare, and a SIDE pocket may hang off one.
	local consumedBy: { [any]: { [string]: boolean } } = {}

	-- Which sockets each placement has already spent, keyed by its index in
	-- `placed`. The critical path spends at most two per piece -- one to
	-- arrive, one to leave -- and whatever is left over is where an optional
	-- pocket can hang. Without this the spare sockets are unknowable after the
	-- fact, which is why IncludeSide sat unimplemented for so long.
	local spent: { [number]: { [string]: boolean } } = {}

	local function record(p: any, chunk: any)
		table.insert(placed, p)
		spent[#placed] = {}
		used[chunk.Id] = (used[chunk.Id] or 0) + 1
		consumedBy[p] = {}
		if chunk.Role == "PATH" or chunk.Role == "COMBAT" then
			ordinaryPlaced += 1
			if chunk.Role == "COMBAT" then
				combatPlaced += 1
			end
		end
	end

	local function spend(socketId: string?)
		if socketId and spent[#placed] then
			spent[#placed][socketId] = true
		end
	end

	local function allowed(chunk: any): boolean
		local n = used[chunk.Id] or 0
		local cap = chunk.MaxPerLayout
		if cap ~= nil and n >= cap then
			return false
		end
		-- Variety: no piece more than MaxRepeats times. Caps are exempt --
		-- a map needs as many as it has loose ends.
		local repeats = options.MaxRepeats
		return repeats == nil or chunk.Role == "CAP" or n < repeats
	end

	local occupancy = {}
	local function bounds(p: any, definition: any): any
		local x, z = definition.HalfX, definition.HalfZ
		if p.Yaw == 90 or p.Yaw == 270 then
			x, z = z, x
		end
		return { X = p.X, Z = p.Z, HalfX = x, HalfZ = z }
	end
	local function collides(p: any, chunk: any): boolean
		local started = os.clock()
		local candidate = if definitions[chunk.Id] then bounds(p, definitions[chunk.Id]) else nil
		for _, other in placed do
			GenerationProfile.count(profile, "OverlapComparisons")
			local collision
			if candidate then
				local existing = occupancy[other]
				if not existing then
					existing = bounds(other, definitions[other.ChunkId])
					occupancy[other] = existing
				end
				collision = math.abs(candidate.X - existing.X)
						< candidate.HalfX + existing.HalfX - 1
					and math.abs(candidate.Z - existing.Z)
						< candidate.HalfZ + existing.HalfZ - 1
			else
				collision = ChunkCore.overlaps(p, chunk, other, chunks[other.ChunkId])
			end
			if collision then
				GenerationProfile.count(profile, "PlacementFailures")
				GenerationProfile.time(profile, "Overlap", started)
				return true
			end
		end
		GenerationProfile.time(profile, "Overlap", started)
		return false
	end

	-- Entry sits at the origin, unrotated.
	local entry = WeightedRandom.pick(entries, function(c)
		return c.Weight
	end, nextNumber)
	assert(entry, "no entry chunk could be picked")
	local entryPlacement =
		{ ChunkId = entry.Id, Role = "ENTRY", X = 0, Y = 0, Z = 0, Yaw = 0, Index = 0 }
	record(entryPlacement, entry)

	-- The socket the next piece attaches to.
	local openChunk, openPlacement = entry, entryPlacement
	local openSocketDef = entry.Sockets[1]
	if not openSocketDef then
		return false, `entry chunk '{entry.Id}' has no sockets`
	end
	consumedBy[entryPlacement][openSocketDef.Id] = true
	local open = ChunkCore.worldSocket(openPlacement, openChunk, openSocketDef)
	spend(openSocketDef.Id)

	-- Which socket kinds the boss arena will accept. The final path chunk has
	-- to offer one of them, or the layout dead-ends at the arena door.
	local bossKinds: { [string]: boolean } = {}
	for _, b in bosses do
		for _, sk in b.Sockets do
			bossKinds[sk.Kind] = true
		end
	end

	-- A socket Kind the arena accepts is RESERVED for the arena. Using such a
	-- piece mid-path strands the layout on a socket only the boss can take,
	-- which was the dominant assembly failure before this rule existed.
	--
	--   non-final step -> must exit on a Kind the boss does NOT accept
	--   final step     -> must exit on a Kind the boss DOES accept
	--
	-- That makes "gate to the boss" an emergent property of socket Kinds
	-- rather than something the generator hard-codes. In Verdant Valley the
	-- Grove is the only WIDE provider, so it always becomes the arena
	-- approach -- exactly what Biome Blueprint §3.2 describes.
	-- A missing key reads as nil, not false, so compare against an explicit
	-- boolean -- `nil == false` is false and silently rejects everything.
	local function isBossKind(kind: string): boolean
		return bossKinds[kind] == true
	end

	local function exitFor(chunk: any, consumedId: string, isFinal: boolean): any?
		local valid = {}
		for _, sock in chunk.Sockets do
			if sock.Id ~= consumedId and isBossKind(sock.Kind) == isFinal then
				table.insert(valid, sock)
			end
		end
		if #valid <= 1 then
			return valid[1]
		end
		-- A seeded pick, so a many-exit piece varies by seed. Only drawn when
		-- there is a real choice, so single-exit kits consume no extra numbers.
		return valid[math.clamp(math.floor(nextNumber() * #valid) + 1, 1, #valid)]
	end

	-- §7.7: a blueprint that requires miniboss arenas needs somewhere to hang
	-- them -- a spare mouth. A critical path of two-mouth pieces has none, so
	-- until a junction is placed junctions are favoured, and the last ordinary
	-- step must be one. Only with a blueprint: legacy layouts draw as before.
	local needJunction = options.Generation ~= nil and (options.Generation.Minibosses or 0) > 0
	local function isJunction(c: any): boolean
		local spare = 0
		for _, sock in c.Sockets do
			if not isBossKind(sock.Kind) then
				spare += 1
			end
		end
		return spare >= 3
	end
	local function pathWeight(c: any): number
		return if needJunction and isJunction(c) then weightOf(c) * 4 else weightOf(c)
	end

	-- Walk the critical path.
	for i = 1, options.PathLength do
		local isFinalStep = i == options.PathLength
		local candidates = {}
		for _, c in middle do
			-- Cheap pre-filter; exitFor does the authoritative check once the
			-- entry socket is known.
			local plausible = false
			for _, sock in c.Sockets do
				if isBossKind(sock.Kind) == isFinalStep then
					plausible = true
				end
			end
			-- Never the same piece twice in a row.
			local forced = needJunction and i == options.PathLength - 1
			if
				allowed(c)
				and plausible
				and c.Id ~= openChunk.Id
				and (not forced or isJunction(c))
			then
				table.insert(candidates, c)
			end
		end
		if #candidates == 0 then
			if isFinalStep then
				return false,
					`no chunk can bridge the path to the boss arena -- at least one PATH or COMBAT piece needs an exit socket the arena accepts`
			end
			return false, `ran out of usable chunks at step {i}`
		end

		local chosen, placement, nextSocket, arrivedOn
		-- Several attempts: a piece may not match the open socket's Kind, may
		-- have no usable exit, or may collide with something already placed.
		for _ = 1, 24 do
			local c = WeightedRandom.pick(candidates, pathWeight, nextNumber)
			if c then
				local p, consumed = placeAgainst(c, open, i)
				if p and not collides(p, c) then
					local exit = exitFor(c, consumed.Id, isFinalStep)
					if exit then
						chosen, placement, nextSocket, arrivedOn = c, p, exit, consumed
						break
					end
				end
			end
		end

		if not chosen then
			-- Three distinct causes share this outcome: no piece takes a
			-- socket of this Kind, no piece has a usable exit, or every
			-- candidate collided with something already placed. Collision is
			-- the common one and is seed-dependent, so a retry usually clears
			-- it -- see assembleWithRetry.
			local where = if isFinalStep then "bridging to the arena" else "continuing the path"
			return false,
				`no chunk could be placed at step {i} while {where} (open socket Kind '{open.Kind}'): nothing matched, or every candidate collided`
		end
		record(placement, chosen)
		if isJunction(chosen) then
			needJunction = false
		end
		consumedBy[placement][nextSocket.Id] = true
		consumedBy[placement][(ChunkCore.arrivalSocket(chosen, open) :: any).Id] = true

		openChunk, openPlacement = chosen, placement
		open = ChunkCore.worldSocket(openPlacement, openChunk, nextSocket)
	end

	-- Boss must attach to whatever socket the path ended on.
	local boss = WeightedRandom.pick(bosses, function(c)
		return c.Weight
	end, nextNumber)
	assert(boss, "no boss chunk could be picked")
	local bossPlacement, bossArrived = placeAgainst(boss, open, options.PathLength + 1)
	if not bossPlacement then
		return false,
			`boss chunk '{boss.Id}' cannot attach to a '{open.Kind}' socket -- the path must end on a socket the arena accepts`
	end
	if collides(bossPlacement, boss) then
		return false, "boss arena collides with the path"
	end
	record(bossPlacement, boss)
	consumedBy[bossPlacement][(bossArrived :: any).Id] = true

	local gen = options.Generation
	if not gen and options.IncludeSide and byRole.SIDE and #byRole.SIDE > 0 then
		local spares = {}
		for _, p in placed do
			local chunk = chunks[p.ChunkId]
			if p.Role ~= "BOSS" then
				for _, s in chunk.Sockets do
					if not consumedBy[p][s.Id] and not isBossKind(s.Kind) then
						table.insert(spares, { Placement = p, Chunk = chunk, Socket = s })
					end
				end
			end
		end
		-- Seeded shuffle, so which branch carries the pocket varies by seed.
		for i = #spares, 2, -1 do
			local j = math.clamp(math.floor(nextNumber() * i) + 1, 1, i)
			spares[i], spares[j] = spares[j], spares[i]
		end
		for _, spare in spares do
			local side = WeightedRandom.pick(byRole.SIDE, function(c)
				return c.Weight
			end, nextNumber)
			if side and allowed(side) then
				local at = ChunkCore.worldSocket(spare.Placement, spare.Chunk, spare.Socket)
				local p, arrived = placeAgainst(side, at, options.PathLength + 2)
				if p and not collides(p, side) then
					record(p, side)
					consumedBy[p][arrived.Id] = true
					consumedBy[spare.Placement][spare.Socket.Id] = true
					break
				end
			end
		end
	end

	-- BRANCHES (build spec §7.4, extended 2026-09-23). Owner-directed after the
	-- first two walks came back a single straight shot: *"when paths branch
	-- off, ensure that all paths are filled to either a dead end or lead to
	-- the boss."*
	--
	-- A spare mouth used to take a cap where it stood, so an intersection was
	-- an intersection in name only -- three ways in, two of them a wall you
	-- could see from the junction. Now each one grows a short spur of ordinary
	-- pieces first, and the cap pass below closes whatever the spur leaves. A
	-- branch is therefore somewhere to go and a reason to choose.
	--
	-- Bounded on purpose: the frontier is SNAPSHOT before any spur is grown,
	-- so a spur's own leftovers are capped rather than grown again. Without
	-- that a kit whose pieces have spare sockets grows until it collides with
	-- itself, and every seed fails.
	--
	-- A spur never takes a socket Kind the arena accepts -- that Kind is
	-- reserved for the approach, and spending it here would strand the boss.
	--
	-- Nor may a spur take a PIECE with such a socket (a gate court): entered
	-- from the side, its arena mouth is left facing the sky, and the cap pass
	-- rightly never caps an arena Kind. That shipped once (Spire Court B on a
	-- branch, 2026-09-23).
	local function hasBossKind(chunk: any): boolean
		for _, s in chunk.Sockets do
			if isBossKind(s.Kind) then
				return true
			end
		end
		return false
	end
	local branchLength = options.BranchLength or 0
	if not gen and branchLength > 0 and #middle > 0 then
		local frontier = {}
		for _, p in placed do
			local chunk = chunks[p.ChunkId]
			for _, s in chunk.Sockets do
				if not consumedBy[p][s.Id] and not isBossKind(s.Kind) then
					table.insert(frontier, { Placement = p, Chunk = chunk, Socket = s })
				end
			end
		end

		local branchIndex = options.PathLength + 100
		for _, start in frontier do
			local steps = math.clamp(math.floor(nextNumber() * branchLength) + 1, 1, branchLength)
			local fromP, fromC, fromS = start.Placement, start.Chunk, start.Socket
			for _ = 1, steps do
				if fromS == nil or consumedBy[fromP][fromS.Id] then
					break
				end
				local at = ChunkCore.worldSocket(fromP, fromC, fromS)
				local grown = false
				for _ = 1, 12 do
					local c = WeightedRandom.pick(middle, weightOf, nextNumber)
					if c and allowed(c) and c.Id ~= fromC.Id and not hasBossKind(c) then
						local p, arrived = placeAgainst(c, at, branchIndex)
						if p and not collides(p, c) then
							record(p, c)
							branchIndex += 1
							consumedBy[p][(arrived :: any).Id] = true
							consumedBy[fromP][fromS.Id] = true
							-- Carry on out of one of its other mouths, if it
							-- has one the arena does not want.
							local onward = nil
							for _, s in c.Sockets do
								if s.Id ~= (arrived :: any).Id and not isBossKind(s.Kind) then
									onward = s
									break
								end
							end
							fromP, fromC, fromS = p, c, onward
							grown = true
							break
						end
					end
				end
				-- Nothing fitted: stop here and let the cap pass close it.
				if not grown then
					break
				end
			end
		end
	end

	-- UNIVERSAL GENERATION (build spec §7.7, owner-directed 2026-09-27:
	-- "intersections should always be filled. deadends should always end every
	-- path that doesnt lead to the boss, or miniboss areas").
	--
	-- Breadth-first from EVERY spare mouth of every placed piece -- not just the
	-- first, as the legacy spur did -- so a crossroads is filled on all sides.
	-- A branch grows ordinary pieces up to BranchLength deep, and then MUST end
	-- in a MINIBOSS arena (until the blueprint's quota is met), a SIDE pocket
	-- (up to MaxSides), or -- in the cap pass below -- a CAP. Every mouth a
	-- grown piece adds joins the queue one level deeper, so depth bounds the
	-- whole tree and the pass always terminates.
	if gen then
		local maxDepth = gen.BranchLength or 0
		local wantMini = gen.Minibosses or 0
		local maxSides = gen.MaxSides or 0
		local minis, sides = 0, 0
		local index = options.PathLength + 100
		local queue = {}
		local function enqueue(p: any, chunk: any, depth: number)
			for _, s in chunk.Sockets do
				if not consumedBy[p][s.Id] and not isBossKind(s.Kind) then
					table.insert(queue, { Placement = p, Chunk = chunk, Socket = s, Depth = depth })
				end
			end
		end
		for _, p in table.clone(placed) do
			if p.Role ~= "BOSS" then
				enqueue(p, chunks[p.ChunkId], 0)
			end
		end
		-- Every piece of `pool` tried once, in seeded weighted order.
		local function attach(pool: { any }?, from: any): (any?, any?)
			if not pool or #pool == 0 then
				return nil, nil
			end
			local at = ChunkCore.worldSocket(from.Placement, from.Chunk, from.Socket)
			local list = table.clone(pool)
			while #list > 0 do
				local c = WeightedRandom.pick(list, weightOf, nextNumber)
				if not c then
					break
				end
				table.remove(list, table.find(list, c) :: number)
				if allowed(c) and c.Id ~= from.Chunk.Id and not hasBossKind(c) then
					local p, arrived = placeAgainst(c, at, index)
					if p and not collides(p, c) then
						record(p, c)
						index += 1
						consumedBy[p][(arrived :: any).Id] = true
						consumedBy[from.Placement][from.Socket.Id] = true
						return p, c
					end
				end
			end
			return nil, nil
		end
		local head = 1
		while head <= #queue do
			local item = queue[head]
			head += 1
			if not consumedBy[item.Placement][item.Socket.Id] then
				local grown, grownChunk = nil, nil
				if item.Depth < maxDepth then
					grown, grownChunk = attach(middle, item)
				end
				if grown then
					enqueue(grown, grownChunk, item.Depth + 1)
				else
					-- The branch ends here: an arena, a pocket, or (below) a cap.
					local ended = nil
					if minis < wantMini then
						ended = attach(byRole.MINIBOSS, item)
						if ended then
							minis += 1
						end
					end
					if not ended and sides < maxSides and nextNumber() < 0.5 then
						ended = attach(byRole.SIDE, item)
						if ended then
							sides += 1
						end
					end
				end
			end
		end
		if minis < wantMini then
			return false, `placed {minis} of {wantMini} MINIBOSS arenas the blueprint requires`
		end
	end

	local caps = byRole.CAP
	if caps and #caps > 0 then
		-- Snapshot: caps are one-socket pieces, so they never add openings.
		local open = {}
		for _, p in placed do
			local chunk = chunks[p.ChunkId]
			for _, s in chunk.Sockets do
				if not consumedBy[p][s.Id] and not isBossKind(s.Kind) then
					table.insert(open, { Placement = p, Chunk = chunk, Socket = s })
				end
			end
		end
		for n, spare in open do
			-- Try every cap once, in a seeded order weighted by Weight.
			local pool = table.clone(caps)
			local capped = false
			while #pool > 0 and not capped do
				local cap = WeightedRandom.pick(pool, function(c)
					return c.Weight
				end, nextNumber)
				if not cap then
					break
				end
				table.remove(pool, table.find(pool, cap) :: number)
				if allowed(cap) then
					local at = ChunkCore.worldSocket(spare.Placement, spare.Chunk, spare.Socket)
					local p, arrived = placeAgainst(cap, at, options.PathLength + 2 + n)
					if p and not collides(p, cap) then
						record(p, cap)
						consumedBy[p][arrived.Id] = true
						consumedBy[spare.Placement][spare.Socket.Id] = true
						capped = true
					end
				end
			end
			if not capped then
				return false,
					`socket '{spare.Socket.Id}' on '{spare.Chunk.Id}' opens onto nothing and no CAP chunk fits there`
			end
		end
	end

	-- The promise, checked rather than assumed: in a capped world, no mouth of
	-- any placed piece is left open. Failing here costs one retry on another
	-- seed; passing it silently cost a walkway into the abyss.
	if caps and #caps > 0 then
		for _, p in placed do
			for _, s in chunks[p.ChunkId].Sockets do
				if not consumedBy[p][s.Id] then
					return false, `socket '{s.Id}' on '{p.ChunkId}' was left open onto nothing`
				end
			end
		end
	end

	-- BACKDROP (§7.7). Socketless surround scenery -- cloud banks, distant
	-- isles -- ringed round the finished layout so the playable map never
	-- ends at a bare horizon. Every free neighbour cell of every walkable
	-- piece, in placement order, until the blueprint's allowance is spent.
	-- Drawn AFTER every walkable piece and the open-mouth check, so it can
	-- never take room a branch needed nor change what a seed builds above.
	local backdrops = byRole.BACKDROP
	if gen and (gen.Backdrop or 0) > 0 and backdrops and #backdrops > 0 then
		local budget = gen.Backdrop :: number
		local walkable = table.clone(placed)
		for _, host in walkable do
			if budget <= 0 then
				break
			end
			local hostChunk = chunks[host.ChunkId]
			local hx, hz = hostChunk.SizeX / 2, hostChunk.SizeZ / 2
			if host.Yaw == 90 or host.Yaw == 270 then
				hx, hz = hz, hx
			end
			for _, d in
				{
					{ 1, 0 },
					{ -1, 0 },
					{ 0, 1 },
					{ 0, -1 },
					{ 1, 1 },
					{ -1, 1 },
					{ 1, -1 },
					{ -1, -1 },
				}
			do
				if budget <= 0 then
					break
				end
				local b = WeightedRandom.pick(backdrops, function(c)
					return c.Weight
				end, nextNumber)
				if b then
					local yaw = math.clamp(math.floor(nextNumber() * 4), 0, 3) * 90
					local bx, bz = b.SizeX / 2, b.SizeZ / 2
					if yaw == 90 or yaw == 270 then
						bx, bz = bz, bx
					end
					local p = {
						ChunkId = b.Id,
						Role = "BACKDROP",
						X = host.X + d[1] * (hx + bx),
						Y = host.Y,
						Z = host.Z + d[2] * (hz + bz),
						Yaw = yaw,
						Index = #placed + 1000,
					}
					if not collides(p, b) then
						record(p, b)
						budget -= 1
					end
				end
			end
		end
	end

	return true, {
		WorldId = options.WorldId,
		Chunks = placed,
		Generation = gen,
	}
end

--- Developer catalogue: every definition once, on the X axis. Socket joins
--- are preferred, but coverage never depends on the kit's connection grammar.
function ChunkCore.assembleTest(
	chunks: { [string]: any },
	worldId: string,
	gap: number
): (boolean, any)
	local remaining = {}
	for _, chunk in chunks do
		if chunk.WorldId == worldId then
			table.insert(remaining, chunk)
		end
	end
	table.sort(remaining, function(a, b)
		if (a.Role == "ENTRY") ~= (b.Role == "ENTRY") then
			return a.Role == "ENTRY"
		end
		return a.Id < b.Id
	end)
	if #remaining == 0 then
		return false, `{worldId} has no chunk kit`
	end
	local placed = {}
	local rightEdge = 0
	local previous: any = nil
	local function halfWidth(p: any, chunk: any): number
		return (if p.Yaw == 90 or p.Yaw == 270 then chunk.SizeZ else chunk.SizeX) / 2
	end
	local function rowYaw(chunk: any): number
		local bestYaw, bestScore = 0, -1
		for yaw = 0, 270, 90 do
			local score = 0
			for _, socket in chunk.Sockets do
				local facing = norm(socket.Facing + yaw)
				if facing == 90 or facing == 270 then
					score += 2
				end
				if facing == 90 then
					score += 1
				end
			end
			if score > bestScore then
				bestYaw, bestScore = yaw, score
			end
		end
		return bestYaw
	end
	while #remaining > 0 do
		local chosen = 1
		local candidate: any = nil
		if previous then
			local prior = chunks[previous.ChunkId]
			for i, chunk in remaining do
				for _, exit in prior.Sockets do
					local at = ChunkCore.worldSocket(previous, prior, exit)
					if at.Facing ~= 90 then
						continue
					end
					for _, arrival in chunk.Sockets do
						local probe = table.clone(chunk)
						probe.Sockets = { arrival }
						local p = ChunkCore.placeAgainst(probe, at, #placed + 1)
						if
							p
							and p.Z == 0
							and p.Y == 0
							and p.X - halfWidth(p, chunk) >= rightEdge
						then
							candidate, chosen = p, i
							break
						end
					end
					if candidate then
						break
					end
				end
				if candidate then
					break
				end
			end
		end
		local chunk = table.remove(remaining, chosen)
		local yaw = rowYaw(chunk)
		local width = halfWidth({ Yaw = yaw }, chunk)
		local p = candidate
			or {
				ChunkId = chunk.Id,
				Role = chunk.Role,
				Index = #placed + 1,
				X = if #placed == 0 then 0 else rightEdge + gap + width,
				Y = 0,
				Z = 0,
				Yaw = yaw,
			}
		table.insert(placed, p)
		rightEdge = p.X + halfWidth(p, chunk)
		previous = p
	end
	return true, { WorldId = worldId, Chunks = placed, TestMode = true }
end

--- Retries assembly across several seeds. A layout can legitimately fail when
--- the path folds back and collides with itself, which is seed-dependent, so
--- the caller should try a few rather than reject the expedition. Returns the
--- first success, or the last failure reason.
function ChunkCore.assembleWithRetry(
	chunks: { [string]: any },
	options: AssembleOptions,
	makeStream: (attempt: number) -> () -> number,
	attempts: number
): (boolean, any, number)
	local lastErr: any = "no attempts made"
	for attempt = 1, attempts do
		local ok, result = ChunkCore.assemble(chunks, options, makeStream(attempt))
		if ok then
			return true, result, attempt
		end
		lastErr = result
	end
	return false, lastErr, attempts
end

--- Bounding footprint of a layout, and how long it takes to walk end to end.
--- The relationship that matters: traverse time must stay a modest fraction of
--- the expedition duration, or the expedition is a corridor simulator. Raise
--- or lower PathLength to tune it.
function ChunkCore.footprint(layout: any): (number, number)
	local minX, maxX = math.huge, -math.huge
	local minZ, maxZ = math.huge, -math.huge
	for _, c in layout.Chunks do
		minX, maxX = math.min(minX, c.X), math.max(maxX, c.X)
		minZ, maxZ = math.min(minZ, c.Z), math.max(maxZ, c.Z)
	end
	if minX == math.huge then
		return 0, 0
	end
	return maxX - minX, maxZ - minZ
end

--- Post-assembly check: no two chunks overlap. Assembly rejects collisions as
--- it goes, so this is a belt-and-braces assertion for tests and for content
--- authors adding new pieces.
function ChunkCore.validateLayout(layout: any, chunks: { [string]: any }): (boolean, { string })
	local errors = {}
	local roles = {}
	for _, p in layout.Chunks do
		roles[p.Role] = (roles[p.Role] or 0) + 1
	end
	if roles.ENTRY ~= 1 then
		table.insert(errors, `layout has {roles.ENTRY or 0} ENTRY chunks, expected exactly 1`)
	end
	if roles.BOSS ~= 1 then
		table.insert(errors, `layout has {roles.BOSS or 0} BOSS chunks, expected exactly 1`)
	end
	-- A §7.7 blueprint sets its own pocket allowance; legacy layouts keep 1.
	local maxSides = if layout.Generation then layout.Generation.MaxSides or 0 else 1
	if (roles.SIDE or 0) > maxSides then
		table.insert(errors, `layout has {roles.SIDE} SIDE pockets, expected at most {maxSides}`)
	end
	if layout.Generation and (roles.MINIBOSS or 0) < (layout.Generation.Minibosses or 0) then
		table.insert(
			errors,
			`layout has {roles.MINIBOSS or 0} MINIBOSS arenas, blueprint requires {layout.Generation.Minibosses}`
		)
	end

	for i = 1, #layout.Chunks do
		for j = i + 1, #layout.Chunks do
			local a, b = layout.Chunks[i], layout.Chunks[j]
			if ChunkCore.overlaps(a, chunks[a.ChunkId], b, chunks[b.ChunkId]) then
				table.insert(errors, `chunks '{a.ChunkId}' and '{b.ChunkId}' overlap`)
			end
		end
	end

	return #errors == 0, errors
end

return ChunkCore
