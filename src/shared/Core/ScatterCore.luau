--!strict
-- The prop scatter: which scenery props a run stands on each chunk, and where.
--
-- A chunk ships no dressing (owner direction, 2026-09-23). It ships SPAWN
-- POINTS -- places a prop could stand, ray-cast onto the real deck by the kit,
-- never in the walking line between openings -- and when a map is generated
-- every client scatters props from its world's pools, seeded by the run. So no
-- two runs dress a chunk alike, nothing is placed twice, and every client in a
-- party draws the same scene without the server sending a single prop.
--
-- TWIN: assets/source/worlds/_framework/scatter_core.py is this algorithm in
-- the kit, which previews a seed in Blender. KEEP THEM IN STEP. Every decision
-- is integer maths on the same 32-bit generator (mulberry32), so a seed gives
-- the same scatter in both; floats appear only in what is output.
--
-- PURE: no Roblox types. PropController turns rows into MeshParts.

local ScatterCore = {}

local TWO32 = 4294967296
local ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
local INDEX: { [number]: number } = {}
for i = 1, #ALPHABET do
	INDEX[string.byte(ALPHABET, i)] = i - 1
end

local bxor, bor, rshift = bit32.bxor, bit32.bor, bit32.rshift

--- 32-bit multiply, exact (a double cannot hold the full 64-bit product).
local function imul(a: number, b: number): number
	local al, ah = a % 65536, a // 65536
	local bl, bh = b % 65536, b // 65536
	return (al * bl + ((ah * bl + al * bh) % 65536) * 65536) % TWO32
end
ScatterCore.imul = imul

--- FNV-1a over a string's bytes.
function ScatterCore.hash(text: string): number
	local h = 2166136261
	for i = 1, #text do
		h = bxor(h, string.byte(text, i))
		h = imul(h, 16777619)
	end
	return h
end

export type Rng = { a: number }

function ScatterCore.rng(seed: number): Rng
	return { a = seed % TWO32 }
end

--- mulberry32.
function ScatterCore.next(r: Rng): number
	r.a = (r.a + 0x6D2B79F5) % TWO32
	local t = r.a
	t = imul(bxor(t, rshift(t, 15)), bor(t, 1))
	t = bxor(t, (t + imul(bxor(t, rshift(t, 7)), bor(t, 61))) % TWO32)
	return bxor(t, rshift(t, 14))
end

local function below(r: Rng, n: number): number
	return ScatterCore.next(r) % n
end

local function range(r: Rng, lo: number, hi: number): number
	return lo + below(r, hi - lo + 1)
end

export type Point = {
	gx: number,
	gz: number,
	yq: number,
	r: number,
	wall: number,
	dir: number,
	tower: number,
	head: number,
}

local cache: { [string]: { Point } } = {}

--- Six characters per point; see scatter_core.py for the layout.
function ScatterCore.decodePoints(s: string): { Point }
	local hit = cache[s]
	if hit then
		return hit
	end
	local out = {}
	for i = 1, #s, 6 do
		local c0 = INDEX[string.byte(s, i)]
		local c1 = INDEX[string.byte(s, i + 1)]
		local c2 = INDEX[string.byte(s, i + 2)]
		local c3 = INDEX[string.byte(s, i + 3)]
		local c4 = INDEX[string.byte(s, i + 4)]
		local c5 = INDEX[string.byte(s, i + 5)]
		table.insert(out, {
			gx = c0,
			gz = c1,
			yq = c2 * 4 + c3 // 16,
			r = c3 % 16,
			wall = c4 // 32,
			dir = (c4 // 4) % 8,
			tower = (c4 // 2) % 2,
			head = c5,
		})
	end
	cache[s] = out
	return out
end

export type AirPoint = { gx: number, gz: number, z0: number, span: number }

function ScatterCore.decodeAir(s: string): { AirPoint }
	local out = {}
	for i = 1, #s, 4 do
		table.insert(out, {
			gx = INDEX[string.byte(s, i)],
			gz = INDEX[string.byte(s, i + 1)],
			z0 = INDEX[string.byte(s, i + 2)] - 32,
			span = INDEX[string.byte(s, i + 3)],
		})
	end
	return out
end

local function ruleOk(rule: string, p: Point, wind: number): boolean
	if rule == "Any" then
		return true
	elseif rule == "Wall" then
		return p.wall == 1
	elseif rule == "Open" then
		return p.wall == 0
	elseif rule == "Base" then
		return p.tower == 1
	elseif rule == "Lee" then
		local d = (p.dir - wind) % 8
		return p.wall == 1 and (d == 0 or d == 1 or d == 7)
	end
	return false
end

export type Placement = {
	kind: string,
	x: number, -- kit (Blender) axes: x east, y north, z up
	y: number,
	z: number,
	yaw: number, -- degrees about vertical
	scale: number,
	gx: number,
	gz: number,
	air: boolean,
}

--- One chunk's scatter for one run. `set` is a world's Scatter content;
--- `points` its entry for this chunk ({ Pool, Ground, Air }); `key` tells two
--- copies of one chunk in a run apart.
function ScatterCore.scatter(set: any, points: any, seed: number, key: string): { Placement }
	local grid, origin, airGrid, gap = set.Grid, set.Origin, set.AirGrid, set.Gap
	local pool = set.Pools[points.Pool]
	local kinds = set.Kinds
	local out: { Placement } = {}
	if not pool then
		return out
	end
	local rng = ScatterCore.rng(ScatterCore.hash(string.format("%d|%s", seed, key)))
	local pts = ScatterCore.decodePoints(points.Ground)
	local air: { AirPoint } = if points.Air ~= "" then ScatterCore.decodeAir(points.Air) else {}
	local n = #pts
	if n == 0 then
		return out
	end
	local byCell: { [number]: Point } = {}
	for _, p in pts do
		byCell[p.gx * 64 + p.gz] = p
	end
	local dens = range(rng, pool.Density[1], pool.Density[2])
	local target = (n * dens) // (pool.PointsPer * 1000)
	target = math.max(pool.Min, math.min(pool.Max, target))
	local wind = below(rng, 8)
	local taken: { { number } } = {}

	local function fits(p: Point, rad: number): boolean
		for _, t in taken do
			local dx = (p.gx - t[1]) * grid
			local dz = (p.gz - t[2]) * grid
			local lim = t[3] + rad + gap
			if dx * dx + dz * dz < lim * lim then
				return false
			end
		end
		return true
	end

	local function tryPlace(entry: any, pick: () -> Point?, tries: number): Point?
		local names = entry.Kinds
		local name = names[below(rng, #names) + 1]
		local k = kinds[name]
		local sc = range(rng, entry.Scale[1], entry.Scale[2])
		local rad = k.R * sc / 1000
		local hgt = k.H * sc / 1000
		for _ = 1, tries do
			local p = pick()
			if
				p
				and ruleOk(entry.Rule, p, wind)
				and p.r >= rad
				and not (p.head < 15 and p.head * 2 < hgt)
				and fits(p, rad)
			then
				local yaw
				if entry.Align == "Wall" and p.wall == 1 then
					yaw = p.dir * 45 + 90 + below(rng, 2) * 180
				else
					yaw = below(rng, 360)
				end
				local slack = math.min(2, p.r - rad)
				local jx = (below(rng, 2001) - 1000) / 1000 * slack
				local jz = (below(rng, 2001) - 1000) / 1000 * slack
				table.insert(taken, { p.gx, p.gz, rad })
				table.insert(out, {
					kind = name,
					x = origin + grid * p.gx + jx,
					y = origin + grid * p.gz + jz,
					z = p.yq / 4 - 8,
					yaw = yaw,
					scale = sc / 1000,
					gx = p.gx,
					gz = p.gz,
					air = false,
				})
				return p
			end
		end
		return nil
	end

	local function anywhere(): Point?
		return pts[below(rng, n) + 1]
	end

	for _, g in pool.Groups do
		if #out >= target then
			break
		end
		if below(rng, 100) < g.Chance then
			local core = tryPlace(g.Core, anywhere, 24)
			if core then
				for _, m in g.Members do
					local lo = (m.Ring[1] + grid - 1) // grid
					local hi = m.Ring[2] // grid
					local c = core :: Point
					local function ring(): Point?
						local dx = range(rng, -hi, hi)
						local dz = range(rng, -hi, hi)
						local d2 = dx * dx + dz * dz
						if d2 < lo * lo or d2 > hi * hi then
							return nil
						end
						return byCell[(c.gx + dx) * 64 + (c.gz + dz)]
					end
					for _ = 1, range(rng, m.Count[1], m.Count[2]) do
						tryPlace(m, ring, 10)
					end
				end
			end
		end
	end

	local singles = pool.Singles
	local total = 0
	for _, s in singles do
		total += s.Weight
	end
	local attempts = 0
	while #singles > 0 and #out < target and attempts < target * 8 + 20 do
		attempts += 1
		local roll = below(rng, total)
		local chosen = singles[#singles]
		for _, s in singles do
			roll -= s.Weight
			if roll < 0 then
				chosen = s
				break
			end
		end
		tryPlace(chosen, anywhere, 2)
	end

	-- floats, apart from the ground props: they only keep clear of each other
	local floating: { { number } } = {}
	for _, a in pool.Air do
		if #air == 0 then
			break
		end
		local names = a.Kinds
		for _ = 1, range(rng, a.Count[1], a.Count[2]) do
			local name = names[below(rng, #names) + 1]
			for _ = 1, 6 do
				local ap = air[below(rng, #air) + 1]
				local clash = false
				for _, f in floating do
					local dx, dz = ap.gx - f[1], ap.gz - f[2]
					if dx * dx + dz * dz < 1 then
						clash = true
						break
					end
				end
				if not clash then
					local z = ap.z0 + below(rng, ap.span + 1)
					table.insert(floating, { ap.gx, ap.gz })
					table.insert(out, {
						kind = name,
						x = origin + airGrid * ap.gx,
						y = origin + airGrid * ap.gz,
						z = z,
						yaw = below(rng, 360),
						scale = 1,
						gx = ap.gx,
						gz = ap.gz,
						air = true,
					})
					break
				end
			end
		end
	end
	return out
end

--- A placement as a PropController row, in the chunk's layout frame (game
--- axes: x east, y up, z south). The library mesh pivots on its box centre,
--- so the kind's Offset (anchor -> centre) is turned and scaled with it.
function ScatterCore.toRow(set: any, p: Placement): any
	local k = set.Kinds[p.kind]
	local a = math.rad(p.yaw)
	local c, s = math.cos(a), math.sin(a)
	local o = k.Offset
	local ox, oy, oz = o[1] * p.scale, o[2] * p.scale, o[3] * p.scale
	return {
		Prop = p.kind,
		Anim = k.Anim,
		Tier = k.Tier,
		Interact = k.Interact,
		P = { p.x + ox * c + oz * s, p.z + oy, -p.y - ox * s + oz * c },
		R = { c, 0, s, 0, 1, 0, -s, 0, c },
		S = { k.Size[1] * p.scale, k.Size[2] * p.scale, k.Size[3] * p.scale },
	}
end

--- Every scattered row for a chunk copy, or {} when the world scatters
--- nothing there.
function ScatterCore.rowsFor(set: any, chunkId: string, seed: number, key: string): { any }
	local points = set and set.Points[chunkId]
	if not points then
		return {}
	end
	local rows = {}
	for _, p in ScatterCore.scatter(set, points, seed, key) do
		table.insert(rows, ScatterCore.toRow(set, p))
	end
	return rows
end

--- Which of n versions of a fixed prop this run draws (0 = the row's own,
--- k = its Alt[k]): the same on every client, different run to run and
--- berth to berth. A moored raider ship is one of five this way.
function ScatterCore.pick(seed: number, key: string, row: number, n: number): number
	if n <= 1 then
		return 0
	end
	return ScatterCore.hash(string.format("%d|%s|%d", seed, key, row)) % n
end

--- The key that tells two copies of a chunk in one run apart: where it sits.
function ScatterCore.keyFor(chunkId: string, x: number, z: number): string
	return string.format("%s@%d,%d", chunkId, math.floor(x), math.floor(z))
end

return ScatterCore
