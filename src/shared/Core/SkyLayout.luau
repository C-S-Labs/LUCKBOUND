--!strict
-- WHERE THE ISLANDS ROUND THE HUB GO: the pure layout behind HubV2.buildSky's
-- backdrop (no Roblox types, so it runs headless and the tests fly creatures
-- through the very same world the server builds).
--
-- docs/design/SKY_ECOSYSTEM_CONTRACT.md 7, item 3: the islands grow with their
-- distance from the hub (the creatures are enormous), are spread out with real
-- gaps, are staggered in height, and leave LANES: radial corridors with no island
-- in them, along which a colossal can reach the hub and pass under or over it.
-- Every number is GameConfig.HubLayout.V2.Backdrop.

local SkyLayout = {}

export type Rng = any

--- One placed island. X/Y/Z are relative to the hub origin; R and H are the
--- bounding cylinder (radius, half height) the planner treats as the obstacle.
export type Island = {
	Chunk: number,
	Scale: number,
	Angle: number,
	Radius: number,
	X: number,
	Y: number,
	Z: number,
	R: number,
	H: number,
	Yaw: number,
}

local TWO_PI = math.pi * 2

local function clamp(v: number, lo: number, hi: number): number
	return math.max(lo, math.min(hi, v))
end

--- The size factor of an island centred `radius` from the hub axis (before jitter).
function SkyLayout.scaleAt(b: any, radius: number): number
	local t = clamp((radius - b.RadiusMin) / math.max(b.RadiusMax - b.RadiusMin, 1), 0, 1)
	return b.ScaleNear + (b.ScaleFar - b.ScaleNear) * t ^ b.ScaleCurve
end

--- The bounding cylinder of a chunk of size `shape` ({x, y, z}) drawn at `scale`.
function SkyLayout.cylinder(b: any, shape: { number }, scale: number): (number, number)
	local r = math.sqrt(shape[1] ^ 2 + shape[3] ^ 2) * 0.5 * scale * b.Shape
	local h = shape[2] * 0.5 * scale * b.Shape
	return r, h
end

--- Distance from a point (polar: angle `a`, radius `r`) to the ray leaving the hub
--- axis at angle `lane`.
local function laneDistance(a: number, r: number, lane: number): number
	local diff = a - lane
	local along = r * math.cos(diff)
	if along <= 0 then
		return r
	end
	return r * math.abs(math.sin(diff))
end

--- The bearings of the open lanes. LaneCount DIAMETERS cross the hub, evenly spread from
--- a random start, so each lane has another straight opposite it: a creature can
--- come in along one, pass under or over the hub and leave along the other.
function SkyLayout.lanes(b: any, rng: Rng): { number }
	local out = {}
	local base = rng:NextNumber(0, math.pi)
	for i = 1, b.LaneCount do
		local a = base + math.pi * (i - 1) / b.LaneCount
		table.insert(out, a % TWO_PI)
		table.insert(out, (a + math.pi) % TWO_PI)
	end
	return out
end

--- Lay the backdrop out. `shapes` are the chunk sizes ({x, y, z} each). Islands
--- that cannot be fitted (after shrinking) are left out, so the result may be
--- shorter than Count. Returns the islands and the lane bearings.
function SkyLayout.backdrop(b: any, shapes: { { number } }, rng: Rng): ({ Island }, { number })
	local lanes = SkyLayout.lanes(b, rng)
	local placed: { Island } = {}
	if #shapes == 0 then
		return placed, lanes
	end
	for i = 1, b.Count do
		local frac = (i * 0.6180339887 + rng:NextNumber(-0.15, 0.15)) % 1 -- spreads heights evenly
		local y = b.HeightMin + frac * (b.HeightMax - b.HeightMin)
		local shrink = 1.0
		for try = 1, b.Tries do
			if try > 1 and (try - 1) % b.ShrinkEvery == 0 then
				shrink *= b.Shrink
			end
			local a = rng:NextNumber(0, TWO_PI)
			local r = rng:NextNumber(b.RadiusMin, b.RadiusMax)
			local chunk = rng:NextInteger(1, #shapes)
			local k = SkyLayout.scaleAt(b, r) * (1 + rng:NextNumber(-b.ScaleJitter, b.ScaleJitter))
			k *= shrink
			local cr, ch = SkyLayout.cylinder(b, shapes[chunk], k)
			local x, z = math.cos(a) * r, math.sin(a) * r
			local ok = r - cr >= b.HubClear
			if ok then
				for _, lane in lanes do
					if laneDistance(a, r, lane) < cr + b.LaneWidth * 0.5 then
						ok = false
						break
					end
				end
			end
			if ok then
				for _, o in placed do
					local dh = math.sqrt((o.X - x) ^ 2 + (o.Z - z) ^ 2) - o.R - cr
					local dv = math.abs(o.Y - y) - o.H - ch
					if dh < b.MinGap and dv < b.VGap then
						ok = false
						break
					end
				end
			end
			if ok then
				table.insert(placed, {
					Chunk = chunk,
					Scale = k,
					Angle = a,
					Radius = r,
					X = x,
					Y = y,
					Z = z,
					R = cr,
					H = ch,
					Yaw = rng:NextNumber(0, TWO_PI),
				})
				break
			end
		end
	end
	return placed, lanes
end

return SkyLayout
