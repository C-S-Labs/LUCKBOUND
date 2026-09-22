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
function ChunkCore.placeAgainst(chunk: any, openSocket: any, index: number): (any?, any?)
	local wanted = norm(openSocket.Facing + 180)

	for _, s in chunk.Sockets do
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
				}, s
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
	WorldId: string,
	PathLength: number, -- chunks between entry and boss
	IncludeSide: boolean?,
	-- Seal every socket the layout leaves open with a CAP chunk (build spec
	-- §7.4). No effect in a world that declares no CAP pieces.
	SealOpenSockets: boolean?,
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
--- CAPS (SealOpenSockets). Last of all, every socket still unjoined is closed
--- with a CAP chunk, so the map ends in authored art rather than at a raw
--- opening. Worlds with no CAP pieces are unaffected.
---
--- Returns ok, layout-or-error. Failure is a normal outcome, not an error:
--- a kit whose sockets cannot reach the boss is a content bug, and the caller
--- should reject the seed rather than ship a broken expedition.
function ChunkCore.assemble(
	chunks: { [string]: any },
	options: AssembleOptions,
	nextNumber: () -> number
): (boolean, any)
	local byRole = ChunkCore.libraryFor(chunks, options.WorldId)

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
	-- Per placed piece: which of its sockets are already joined to something.
	-- The critical path spends at most two per piece -- one to arrive, one to
	-- leave -- and whatever is left over is where an optional pocket hangs and
	-- where a cap goes. Without this the spare sockets are unknowable after
	-- the fact, which is why IncludeSide sat unimplemented for so long.
	--
	-- ONE record of what is spent, not two. A parallel `spent` table indexed
	-- by placement order used to sit beside this one; nothing ever read it,
	-- and two answers to "is this socket free" is how a cap ends up sealing a
	-- doorway the path walks through.
	local consumedBy: { [any]: { [string]: boolean } } = {}

	local function record(p: any, chunk: any)
		table.insert(placed, p)
		used[chunk.Id] = (used[chunk.Id] or 0) + 1
		consumedBy[p] = {}
	end

	local function allowed(chunk: any): boolean
		local cap = chunk.MaxPerLayout
		return cap == nil or (used[chunk.Id] or 0) < cap
	end

	local function collides(p: any, chunk: any): boolean
		for _, other in placed do
			if ChunkCore.overlaps(p, chunk, other, chunks[other.ChunkId]) then
				return true
			end
		end
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
			if allowed(c) and plausible then
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
			local c = WeightedRandom.pick(candidates, function(x)
				return x.Weight
			end, nextNumber)
			if c then
				local p, consumed = ChunkCore.placeAgainst(c, open, i)
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
	local bossPlacement = ChunkCore.placeAgainst(boss, open, options.PathLength + 1)
	if not bossPlacement then
		return false,
			`boss chunk '{boss.Id}' cannot attach to a '{open.Kind}' socket -- the path must end on a socket the arena accepts`
	end
	if collides(bossPlacement, boss) then
		return false, "boss arena collides with the path"
	end
	record(bossPlacement, boss)

	if options.IncludeSide and byRole.SIDE and #byRole.SIDE > 0 then
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
				local p, consumed = ChunkCore.placeAgainst(side, at, options.PathLength + 2)
				if p and not collides(p, side) then
					record(p, side)
					-- BOTH ends of the join, or the sealing pass below reads
					-- the branch the pocket is standing on as still open and
					-- caps a doorway that already has a room behind it.
					consumedBy[spare.Placement][spare.Socket.Id] = true
					consumedBy[p][(consumed :: any).Id] = true
					break
				end
			end
		end
	end

	-- SEALING THE LEFTOVERS (build spec §7.4). Every socket still unjoined is
	-- an opening onto nothing -- in Sky Citadel, a skyway mouth that stops at
	-- the edge of a floating island. A CAP chunk closes it with authored art.
	--
	-- Runs LAST, on purpose: the path and the pocket decide what the map is,
	-- and capping only dresses what they left. Placed in a fixed order
	-- (placement order, then socket declaration order) rather than a shuffled
	-- one, because every open socket gets a cap -- there is nothing to choose
	-- between, and a shuffle would burn stream numbers for no variety.
	--
	-- A cap that does not fit is skipped, not an error: the layout was already
	-- complete and walkable before any of this.
	if options.SealOpenSockets and byRole.CAP and #byRole.CAP > 0 then
		local nextIndex = options.PathLength + 3
		-- Snapshot: caps are appended to `placed` as they are made, and a cap
		-- has one socket which its own join consumes, so it can never need
		-- capping itself.
		local openings = {}
		for _, p in placed do
			for _, s in chunks[p.ChunkId].Sockets do
				if not consumedBy[p][s.Id] then
					table.insert(openings, { Placement = p, Chunk = chunks[p.ChunkId], Socket = s })
				end
			end
		end

		for _, opening in openings do
			local at = ChunkCore.worldSocket(opening.Placement, opening.Chunk, opening.Socket)
			-- Several attempts: which cap is drawn is seeded, so the three
			-- Sky Citadel endings vary across the map, and a cap that
			-- collides gives way to another draw rather than to a hole.
			for _ = 1, 8 do
				local cap = WeightedRandom.pick(byRole.CAP, function(c)
					return c.Weight
				end, nextNumber)
				if cap then
					local p, consumed = ChunkCore.placeAgainst(cap, at, nextIndex)
					if p and not collides(p, cap) then
						record(p, cap)
						consumedBy[opening.Placement][opening.Socket.Id] = true
						consumedBy[p][(consumed :: any).Id] = true
						nextIndex += 1
						break
					end
				end
			end
		end
	end

	return true,
		{
			WorldId = options.WorldId,
			Chunks = placed,
		}
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

--- Every socket in a finished layout that is not joined to another one.
---
--- Computed from GEOMETRY, not from the assembler's own bookkeeping: two
--- sockets are joined when they sit at the same point facing opposite ways.
--- Asking the assembler whether it sealed everything would only ever confirm
--- that it believes it did -- the same class of self-agreement that let a
--- faked Vector3 pass 152 tests. This measures the map instead.
function ChunkCore.openSockets(layout: any, chunks: { [string]: any }): { any }
	local TOL = 1
	local all = {}
	for _, placed in layout.Chunks do
		local chunk = chunks[placed.ChunkId]
		for _, socket in chunk.Sockets do
			local world = ChunkCore.worldSocket(placed, chunk, socket)
			table.insert(all, { Placed = placed, World = world, Joined = false })
		end
	end

	for i = 1, #all do
		for j = i + 1, #all do
			local a, b = all[i], all[j]
			if
				not a.Joined
				and not b.Joined
				and math.abs(a.World.X - b.World.X) < TOL
				and math.abs(a.World.Y - b.World.Y) < TOL
				and math.abs(a.World.Z - b.World.Z) < TOL
				and norm(a.World.Facing + 180) == b.World.Facing
			then
				a.Joined, b.Joined = true, true
			end
		end
	end

	local open = {}
	for _, entry in all do
		if not entry.Joined then
			table.insert(open, { ChunkId = entry.Placed.ChunkId, Socket = entry.World })
		end
	end
	return open
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
	if (roles.SIDE or 0) > 1 then
		table.insert(errors, `layout has {roles.SIDE} SIDE pockets, expected at most 1`)
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
