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

--- Seeded puff positions and sizes for one cloud layer, in the layer's own
--- square around the camera. nextNumber is any 0..1 stream, so the caller owns
--- the Random and the layout is reproducible.
function AmbienceCore.layoutPuffs(layer: any, count: number, nextNumber: () -> number): { any }
	local puffs = {}
	local half = layer.Radius
	for _ = 1, count do
		local width = layer.SizeMin + (layer.SizeMax - layer.SizeMin) * nextNumber()
		table.insert(puffs, {
			X = (nextNumber() * 2 - 1) * half,
			Z = (nextNumber() * 2 - 1) * half,
			-- A little vertical scatter, so the sea has a surface and not a floor.
			Y = (nextNumber() * 2 - 1) * layer.Thickness * width * 0.5,
			Width = width,
			Length = width * (0.6 + 0.8 * nextNumber()),
			Height = width * layer.Thickness,
		})
	end
	return puffs
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
