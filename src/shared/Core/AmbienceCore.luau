--!strict
-- The pure half of a world's ambience: how much of it to draw on this device,
-- where the cloud sea's puffs sit, and whether a world's ambience data is sane.
-- AmbienceController is the Roblox half; it draws what this decides.
--
-- PURE. No Roblox globals, no Instances -- so the cloud sea's layout and the
-- quality scaling are testable headlessly, exactly like ChunkCore.

local AmbienceCore = {}

--- How much of the ambience to draw, 0..1, from Roblox's saved graphics level.
---
--- savedLevel is UserGameSettings.SavedQualityLevel as a number: 0 means
--- "Automatic" (the engine decides and does not say what it chose), 1..10 are
--- the player's own slider. Automatic gets a middling scale rather than full,
--- because the devices that leave it on Automatic are disproportionately the
--- phones this exists to protect.
function AmbienceCore.qualityScale(savedLevel: number, cfg: any): number
	if savedLevel <= 0 then
		return cfg.AutomaticQuality
	end
	return math.clamp(savedLevel / 10, cfg.QualityFloor, 1)
end

--- A count scaled by quality, never below one: a layer that exists at all
--- should draw at least something, or it reads as a bug rather than a setting.
function AmbienceCore.scaledCount(base: number, scale: number): number
	return math.max(1, math.floor(base * scale + 0.5))
end

--- Wraps an offset into [-half, half). This is the whole "infinite" trick: a
--- puff that drifts off one side of the square around the camera reappears on
--- the other, so a few dozen puffs pave an endless sea.
function AmbienceCore.wrap(offset: number, half: number): number
	local span = half * 2
	return ((offset + half) % span + span) % span - half
end

-- Finishes a cloud layer may use. Matte ones exist to be tried against the
-- default in Studio; Glass and Neon are deliberately absent -- a cloud that is
-- see-through or self-lit reads as a bubble or a lamp, not a cloud.
AmbienceCore.CLOUD_MATERIALS = {
	SmoothPlastic = true,
	Plastic = true,
	Sand = true,
	Fabric = true,
	Snow = true,
}

-- The mix a layer uses when it declares none: mostly heaped cumulus, some flat
-- stratus banks, a few thin wisps.
local DEFAULT_MIX = { Cumulus = 0.55, Stratus = 0.3, Wisp = 0.15 }

local function pickStyle(mix: any, roll: number): string
	local total = 0
	for _, w in mix do
		total += w
	end
	local acc = 0
	for _, name in { "Cumulus", "Stratus", "Wisp" } do
		acc += (mix[name] or 0) / total
		if roll <= acc then
			return name
		end
	end
	return "Cumulus"
end

--- Seeded clouds for one layer. A cloud is a CLUSTER -- a wide shaded base
--- with rounder, lit billows heaped on top -- which is what makes a sea read
--- as cloud rather than as a field of discs. Three kinds, so no two stretches
--- of sea look alike:
---
---   Cumulus  a base and several billows; the tall, heaped kind
---   Stratus  a broad, flat bank with one or two low swells
---   Wisp     a thin, pale streak with nothing heaped on it
---
--- Each cloud is turned to its own heading, so the ellipsoids do not all line
--- up with the world axes. Part offsets are returned already rotated, relative
--- to the cloud's centre, so the whole cluster wraps round the camera as one
--- and never splits across the seam.
---
--- billowScale (0..1, from graphics quality) trims billows before it trims
--- clouds: a low-end device keeps the same sea, less heaped.
---
--- ceiling is how far below the walk plane no cloud may rise -- the kit's
--- deepest keel plus a margin. Any cloud whose tallest billow would cross it
--- is lowered until it does not. Without it a heaped cumulus in the near layer
--- climbed up through the islands.
function AmbienceCore.layoutClouds(
	layer: any,
	count: number,
	billowScale: number,
	nextNumber: () -> number,
	ceiling: number?
): { any }
	local clouds = {}
	local half = layer.Radius
	local mix = layer.Mix or DEFAULT_MIX
	local maxBillows = math.max(0, math.floor((layer.Billows or 0) * billowScale + 0.5))
	-- Tufts are the finest detail, so they thin first: below full quality a
	-- billow carries fewer, and on low graphics none.
	local maxTufts = math.max(0, math.floor((layer.Tufts or 0) * billowScale * billowScale + 0.5))
	for _ = 1, count do
		local size = layer.SizeMin + (layer.SizeMax - layer.SizeMin) * nextNumber()
		local style = pickStyle(mix, nextNumber())
		local yaw = nextNumber() * math.pi * 2
		local c, sn = math.cos(yaw), math.sin(yaw)
		local parts = {}
		local function add(dx: number, dy: number, dz: number, w: number, h: number, l: number, shade: number, fade: number)
			-- Rotate the offset about Y by the cloud's heading, the same way
			-- CFrame.Angles(0, yaw, 0) will turn the part itself.
			table.insert(parts, {
				DX = dx * c + dz * sn,
				DY = dy,
				DZ = -dx * sn + dz * c,
				Width = w,
				Height = h,
				Length = l,
				-- 0 = fully lit top colour, 1 = the underside shade. Jittered a
				-- little so no two pieces of one cloud are quite the same tone.
				Shade = math.clamp(shade + (nextNumber() - 0.5) * 0.16, 0, 1),
				Fade = fade, -- extra transparency on top of the layer's
			})
		end

		local baseH = size * layer.Thickness
		if style == "Wisp" then
			-- Several thin streaks laid slightly across one another: a wisp is
			-- the one cloud that should read as brushed rather than heaped.
			local streaks = 2 + math.floor(nextNumber() * 3)
			for i = 1, streaks do
				local along = (i - (streaks + 1) / 2) * size * 0.35
				add(
					along,
					(nextNumber() - 0.5) * baseH * 0.3,
					(nextNumber() - 0.5) * size * 0.25,
					size * (1.1 + 0.6 * nextNumber()),
					baseH * (0.2 + 0.15 * nextNumber()),
					size * (0.2 + 0.15 * nextNumber()),
					0.25,
					0.3 + 0.2 * nextNumber()
				)
			end
		else
			local flat = style == "Stratus"
			local baseW = size * (if flat then 1.4 else 1)
			local baseL = size * (if flat then 0.9 else 0.7 + 0.5 * nextNumber())
			-- Cumulus sit on a FLAT, squashed base and heap upward; a round base
			-- hanging below the billows is what made them read as bubbles.
			local baseTall = if flat then baseH * 0.5 else baseH * 0.6
			-- A LOBED base -- two or three overlapping ellipsoids -- so the
			-- outline seen from above is irregular instead of one clean oval.
			local lobes = 2 + math.floor(nextNumber() * 2)
			for i = 1, lobes do
				local t = (i - (lobes + 1) / 2) / lobes
				add(
					t * baseW * 0.45,
					(nextNumber() - 0.5) * baseTall * 0.15,
					(nextNumber() - 0.5) * baseL * 0.3,
					baseW * (0.62 + 0.2 * nextNumber()),
					baseTall * (0.85 + 0.2 * nextNumber()),
					baseL * (0.7 + 0.25 * nextNumber()),
					1,
					0
				)
			end
			local n = if flat
				then math.min(maxBillows, 1 + math.floor(nextNumber() * 2))
				else math.max(if maxBillows > 0 then 1 else 0, math.floor(maxBillows * (0.5 + 0.5 * nextNumber()) + 0.5))
			for _ = 1, n do
				local w = size * (if flat then 0.3 + 0.2 * nextNumber() else 0.3 + 0.3 * nextNumber())
				-- Squashed, not spherical: a billow is wider than it is tall.
				local h = w * (if flat then 0.3 else 0.5 + 0.2 * nextNumber())
				local bx = (nextNumber() * 2 - 1) * baseW * 0.32
				local by = baseTall * 0.25 + h * (if flat then 0.1 else 0.2 + 0.2 * nextNumber())
				local bz = (nextNumber() * 2 - 1) * baseL * 0.28
				add(bx, by, bz, w, h, w * (0.8 + 0.4 * nextNumber()), 0.15 * nextNumber(), 0)
				-- TUFTS: small round puffs on the billow's upper surface. This
				-- is the cauliflower texture that separates a cumulus from a
				-- pile of balls.
				if not flat then
					local tufts = math.floor(maxTufts * (0.4 + 0.6 * nextNumber()) + 0.5)
					for _ = 1, tufts do
						local tw = w * (0.28 + 0.22 * nextNumber())
						local ang = nextNumber() * math.pi * 2
						local reach = w * 0.3 * nextNumber()
						add(
							bx + math.cos(ang) * reach,
							by + h * (0.25 + 0.15 * nextNumber()),
							bz + math.sin(ang) * reach,
							tw,
							tw * (0.55 + 0.2 * nextNumber()),
							tw * (0.85 + 0.3 * nextNumber()),
							0.05 * nextNumber(),
							0
						)
					end
				end
			end
		end

		-- A little vertical scatter, so the sea has a surface, not a floor --
		-- then held under the ceiling. Y is relative to the layer's plane
		-- (Depth below the walk plane), so the cloud's top sits at
		-- Y + top - Depth relative to the walk plane.
		local y = (nextNumber() * 2 - 1) * baseH * 0.5
		if ceiling then
			local top = 0
			for _, piece in parts do
				top = math.max(top, piece.DY + piece.Height / 2)
			end
			y = math.min(y, layer.Depth - ceiling - top)
		end
		table.insert(clouds, {
			X = (nextNumber() * 2 - 1) * half,
			Z = (nextNumber() * 2 - 1) * half,
			Y = y,
			Yaw = yaw,
			Style = style,
			Parts = parts,
		})
	end
	return clouds
end

local function checkRange(errors: { string }, label: string, value: any, lo: number, hi: number)
	if type(value) ~= "number" or value < lo or value > hi then
		table.insert(errors, `{label} must be a number in {lo}..{hi} (got {tostring(value)})`)
	end
end

--- Validates the optional ambience blocks of one world's Environment. Every
--- block is optional -- a world with none keeps plain Lighting -- but a block
--- that is present must be complete, because a half-declared cloud layer
--- fails on a player's device, not at boot.
function AmbienceCore.validate(environment: any, label: string): { string }
	local errors = {}
	if type(environment) ~= "table" then
		return errors
	end

	local atmosphere = environment.Atmosphere
	if atmosphere ~= nil then
		checkRange(errors, `{label}.Atmosphere.Density`, atmosphere.Density, 0, 1)
		checkRange(errors, `{label}.Atmosphere.Haze`, atmosphere.Haze, 0, 10)
		checkRange(errors, `{label}.Atmosphere.Glare`, atmosphere.Glare, 0, 10)
	end

	local sea = environment.CloudSea
	if sea ~= nil then
		-- A sea needs a ceiling: without one nothing stops a cloud rising
		-- through the map.
		checkRange(errors, `{label}.CloudCeiling`, environment.CloudCeiling, 0, 5000)
		if type(sea) ~= "table" or #sea == 0 then
			table.insert(errors, `{label}.CloudSea must be a non-empty list of layers`)
		else
			for i, layer in sea do
				local l = `{label}.CloudSea[{i}]`
				checkRange(errors, `{l}.Depth`, layer.Depth, 1, 5000)
				if type(layer.Depth) == "number" and type(environment.CloudCeiling) == "number"
					and layer.Depth <= environment.CloudCeiling then
					table.insert(errors, `{l}.Depth must be below CloudCeiling ({environment.CloudCeiling})`)
				end
				checkRange(errors, `{l}.Count`, layer.Count, 1, 400)
				checkRange(errors, `{l}.Radius`, layer.Radius, 64, 10000)
				checkRange(errors, `{l}.Speed`, layer.Speed, 0, 200)
				checkRange(errors, `{l}.SizeMin`, layer.SizeMin, 1, 2000)
				checkRange(errors, `{l}.SizeMax`, layer.SizeMax, 1, 2000)
				checkRange(errors, `{l}.Thickness`, layer.Thickness, 0.01, 1)
				checkRange(errors, `{l}.Transparency`, layer.Transparency, 0, 1)
				if layer.Billows ~= nil then
					checkRange(errors, `{l}.Billows`, layer.Billows, 0, 12)
				end
				if layer.Tufts ~= nil then
					checkRange(errors, `{l}.Tufts`, layer.Tufts, 0, 6)
				end
				if layer.Material ~= nil and not AmbienceCore.CLOUD_MATERIALS[layer.Material] then
					table.insert(errors, `{l}.Material '{tostring(layer.Material)}' is not an allowed cloud material`)
				end
				if layer.Mix ~= nil then
					local sum = 0
					for key, w in layer.Mix do
						if key ~= "Cumulus" and key ~= "Stratus" and key ~= "Wisp" then
							table.insert(errors, `{l}.Mix: unknown cloud kind '{tostring(key)}'`)
						end
						sum += if type(w) == "number" then w else 0
					end
					if sum <= 0 then
						table.insert(errors, `{l}.Mix must give at least one kind a positive weight`)
					end
				end
				if type(layer.SizeMin) == "number" and type(layer.SizeMax) == "number"
					and layer.SizeMin > layer.SizeMax then
					table.insert(errors, `{l}: SizeMin is larger than SizeMax`)
				end
			end
		end
	end

	local motes = environment.Motes
	if motes ~= nil then
		checkRange(errors, `{label}.Motes.Rate`, motes.Rate, 0, 200)
		checkRange(errors, `{label}.Motes.Lifetime`, motes.Lifetime, 0.1, 60)
	end
	return errors
end

return AmbienceCore
