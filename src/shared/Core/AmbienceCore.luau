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
function AmbienceCore.layoutClouds(layer: any, count: number, billowScale: number, nextNumber: () -> number): { any }
	local clouds = {}
	local half = layer.Radius
	local mix = layer.Mix or DEFAULT_MIX
	local maxBillows = math.max(0, math.floor((layer.Billows or 0) * billowScale + 0.5))
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
				Shade = shade, -- 0 = fully lit top colour, 1 = the underside shade
				Fade = fade, -- extra transparency on top of the layer's
			})
		end

		local baseH = size * layer.Thickness
		if style == "Wisp" then
			add(0, 0, 0, size * 1.6, baseH * 0.35, size * (0.3 + 0.2 * nextNumber()), 0.3, 0.35)
			if nextNumber() < 0.5 then
				add(size * 0.4, baseH * 0.1, size * 0.12, size * 1.1, baseH * 0.25, size * 0.25, 0.2, 0.45)
			end
		else
			local flat = style == "Stratus"
			local baseW = size * (if flat then 1.4 else 1)
			local baseL = size * (if flat then 0.9 else 0.7 + 0.5 * nextNumber())
			local baseTall = if flat then baseH * 0.6 else baseH
			add(0, 0, 0, baseW, baseTall, baseL, 1, 0)
			local n = if flat
				then math.min(maxBillows, 1 + math.floor(nextNumber() * 2))
				else math.max(if maxBillows > 0 then 1 else 0, math.floor(maxBillows * (0.5 + 0.5 * nextNumber()) + 0.5))
			for _ = 1, n do
				local w = size * (if flat then 0.3 + 0.2 * nextNumber() else 0.3 + 0.3 * nextNumber())
				local h = w * (if flat then 0.35 else 0.6 + 0.3 * nextNumber())
				add(
					(nextNumber() * 2 - 1) * baseW * 0.32,
					baseTall * 0.25 + h * (if flat then 0.1 else 0.2 + 0.2 * nextNumber()),
					(nextNumber() * 2 - 1) * baseL * 0.28,
					w,
					h,
					w * (0.8 + 0.4 * nextNumber()),
					0.15 * nextNumber(),
					0
				)
			end
		end

		table.insert(clouds, {
			X = (nextNumber() * 2 - 1) * half,
			Z = (nextNumber() * 2 - 1) * half,
			-- A little vertical scatter, so the sea has a surface, not a floor.
			Y = (nextNumber() * 2 - 1) * baseH * 0.5,
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
		if type(sea) ~= "table" or #sea == 0 then
			table.insert(errors, `{label}.CloudSea must be a non-empty list of layers`)
		else
			for i, layer in sea do
				local l = `{label}.CloudSea[{i}]`
				checkRange(errors, `{l}.Depth`, layer.Depth, 1, 5000)
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
