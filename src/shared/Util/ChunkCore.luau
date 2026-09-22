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
}

--- Builds a layout: ENTRY → PathLength connective/combat chunks → BOSS,
--- optionally hanging one SIDE pocket off a spare socket.
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
	end

	local function spend(socketId: string?)
		if socketId and spent[#placed] then
			spent[#placed][socketId] = true
		end
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
		for _, sock in chunk.Sockets do
			if sock.Id ~= consumedId and isBossKind(sock.Kind) == isFinal then
				return sock
			end
		end
		return nil
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
		spend(arrivedOn and arrivedOn.Id)
		spend(nextSocket.Id)

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

	-- === The optional side pocket ================================
	-- Hung off a socket the critical path did not spend. This is what
	-- IncludeSide has always promised and never done -- the field was declared
	-- and nothing read it, so every SIDE piece in every kit validated, passed
	-- its tests and was never once placed.
	--
	-- It is deliberately best-effort: a pocket that will not fit is a pocket
	-- this seed does not get, never a failed expedition. The critical path is
	-- already complete and valid by the time we get here, and refusing the
	-- whole layout because an OPTIONAL branch collided would trade something
	-- that matters for something that does not.
	if options.IncludeSide ~= false then
		local sides = byRole.SIDE or {}
		if #sides > 0 then
			-- Every unspent socket on every placed piece, as a flat list so
			-- one pick chooses both the host and the socket.
			local spare = {}
			for index, p in placed do
				local hostChunk = chunks[p.ChunkId]
				for _, sock in hostChunk.Sockets do
					if not (spent[index] and spent[index][sock.Id]) then
						table.insert(spare, { Placement = p, Chunk = hostChunk, Socket = sock })
					end
				end
			end

			-- Shuffled by the same seeded stream, so which pocket a seed gets
			-- is reproducible like everything else here.
			for i = #spare, 2, -1 do
				local j = math.floor(nextNumber() * i) + 1
				spare[i], spare[j] = spare[j], spare[i]
			end

			local pocketPlaced = false
			for _, slot in spare do
				if pocketPlaced then
					break
				end
				local openSide = ChunkCore.worldSocket(slot.Placement, slot.Chunk, slot.Socket)
				for _, side in sides do
					if allowed(side) then
						local p = ChunkCore.placeAgainst(side, openSide, #placed)
						if p and not collides(p, side) then
							p.Index = #placed
							record(p, side)
							pocketPlaced = true
							break
						end
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
