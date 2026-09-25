--!strict
-- Procedurally generates The Crossroads into Workspace at runtime.
-- Biome Blueprint §2. Build spec T-112.
--
-- Contains NO art direction. Every colour, dimension and material comes from
-- Content/Hub/Crossroads; every position comes from GameConfig.HubLayout.
-- If you find yourself editing this file to change how something LOOKS, the
-- schema is missing a field and that is the bug.
--
-- Zone geometry is dispatched by `Kind`, so adding a sixth zone means adding a
-- data entry and (only if it is a genuinely new shape) one builder function.

local AssetService = game:GetService("AssetService")
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local Layout = require(Root.Content.Hub.Crossroads)
local PortalRig = require(Root.Util.PortalRig)
local PrefabLoader = require(Root.Util.PrefabLoader)
local HubV2 = require(script.Parent.HubV2)
local V2Layout = require(Root.Content.Hub.CrossroadsV2)

local HubBuilder = {}

local Anchors = GameConfig.HubLayout.Anchors

-- Which v2 district mesh stands at each compass zone.
local V2_PIECE = {
	HALL_OF_LEGENDS = "HUB_HALL_OF_CHAMPIONS",
	DISCOVERY_ARCHIVE = "HUB_ARCHIVES",
	EXPEDITION_GATE = "HUB_SHOP",
	TRAINING_GROUNDS = "HUB_TRAINING_GROUNDS",
}

local function part(props: { [string]: any }, parent: Instance): Part
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = props.CanCollide ~= false
	p.Material = props.Material or Layout.Theme.StoneMaterial
	p.Color = props.Color or Layout.Theme.Marble
	p.Size = props.Size or Vector3.one
	p.CFrame = props.CFrame or CFrame.new(props.Position or Vector3.zero)
	p.Name = props.Name or "Part"
	p.Transparency = props.Transparency or 0
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	if props.Shape then
		p.Shape = props.Shape
	end
	p.Parent = parent
	return p
end

--- A TRUE cylinder -- `Part.Shape = Cylinder`, never a Part wearing a
--- `CylinderMesh`. Both halves of that distinction cost a playtest:
---
--- 1. **A CylinderMesh is VISUAL ONLY.** The part keeps its block collision
---    hull, so an invisible square corner juts out past every visible round
---    edge and the player is stopped by nothing they can see.
--- 2. **CylinderMesh's axis is Y; PartType.Cylinder's axis is X.** Every
---    caller here passes `(thickness, diameter, diameter)` -- the X
---    convention -- so the mesh version built a diameter-TALL column where a
---    thin disc was wanted. At the old 120-stud scale that was a 120-stud
---    wall; after the 10x rescale the plaza became a 1200-stud wall and the
---    hub had no floor at all. The player spawned on top of it.
---
--- Size keeps the `(thickness, diameter, diameter)` convention; the part is
--- rolled a quarter turn about Z so its local X axis points up.
local function cylinder(props: { [string]: any }, parent: Instance): Part
	local p = part(props, parent)
	p.Shape = Enum.PartType.Cylinder
	p.CFrame = p.CFrame * CFrame.Angles(0, 0, math.pi / 2)
	return p
end

--- Uses an authored mesh when the data supplies one. Returns nil so callers
--- fall through to primitives when it is absent or fails to load.
---
--- THIS USED TO BE BROKEN, SILENTLY, AND THAT IS THE INTERESTING PART.
--- The original set `MeshPart.MeshId` directly, which Roblox does not permit at
--- runtime -- MeshId is assignable only by the importer. The assignment was
--- wrapped in a `pcall`, so it failed, warned, and fell back to a primitive.
--- Every `MeshId` seam in `Content/Hub/Crossroads` would therefore have done
--- nothing at all, and the symptom would have been "we uploaded the mesh and
--- the game ignored it" with no error to chase.
---
--- `AssetService:CreateMeshPartAsync` is the supported runtime path, and it is
--- what `Util/ChunkLoader` already used -- the two seams had drifted apart.
--- Note it YIELDS: it fetches from Roblox's CDN. That is fine here because
--- HubBuilder runs during bootstrap, before any player is bound (build spec
--- §1.2 step 9 of 11), but it is the reason this must not be called per-frame.
local function meshOrNil(meshId: string?, size: Vector3, cframe: CFrame, name: string, parent: Instance): BasePart?
	if not meshId or meshId == "" then
		return nil
	end

	local ok, result = pcall(function()
		return AssetService:CreateMeshPartAsync(meshId)
	end)
	if not ok or not result then
		warn(`[HubBuilder] mesh {meshId} failed for {name}: {result}; using primitive`)
		return nil
	end

	local p = result :: MeshPart
	p.Name = name
	p.Anchored = true
	p.Size = size
	p.CFrame = cframe
	p.Parent = parent
	print(`[HubBuilder] {name}: using authored mesh {meshId}`)
	return p
end

local function label(text: string, color: Color3, size: UDim2, parent: BasePart, maxDistance: number)
	local gui = Instance.new("BillboardGui")
	gui.Size = size
	gui.AlwaysOnTop = false
	gui.MaxDistance = maxDistance
	gui.Parent = parent

	local textLabel = Instance.new("TextLabel")
	textLabel.Size = UDim2.fromScale(1, 1)
	textLabel.BackgroundTransparency = 1
	textLabel.Text = text
	textLabel.TextColor3 = color
	textLabel.TextScaled = true
	textLabel.Font = Enum.Font.GothamBold
	textLabel.TextStrokeTransparency = 0.4
	textLabel.Parent = gui
	return gui
end

-- === lighting ========================================================

local function applyLighting()
	local theme = Layout.Theme

	-- Technology is a place setting and is read-only at runtime in a live
	-- server. Attempted here so a fresh Studio place picks it up; set it in
	-- Studio (Lighting.Technology = Future) if this warns.
	pcall(function()
		Lighting.Technology = Enum.Technology.Future
	end)

	Lighting.GlobalShadows = true
	Lighting.Brightness = theme.Brightness
	Lighting.ExposureCompensation = theme.ExposureCompensation
	Lighting.Ambient = theme.Ambient
	Lighting.OutdoorAmbient = theme.OutdoorAmbient
	Lighting.ColorShift_Top = theme.ColorShiftTop
	Lighting.ColorShift_Bottom = theme.ColorShiftBottom
	Lighting.FogColor = theme.FogColor
	Lighting.FogStart = theme.FogStart
	Lighting.FogEnd = theme.FogEnd
	Lighting.ClockTime = theme.ClockTime
	Lighting.EnvironmentDiffuseScale = 1
	Lighting.EnvironmentSpecularScale = 1

	local sky = Lighting:FindFirstChildOfClass("Sky") or Instance.new("Sky")
	sky.StarCount = theme.StarCount or 3000
	sky.SunAngularSize = theme.SunAngularSize or 21
	sky.Parent = Lighting

	local atmosphere = Lighting:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere")
	atmosphere.Density = theme.AtmosphereDensity or 0.3
	atmosphere.Offset = theme.AtmosphereOffset or 0
	atmosphere.Haze = theme.AtmosphereHaze or 2
	atmosphere.Glare = theme.AtmosphereGlare or 0
	atmosphere.Color = theme.AtmosphereColor or theme.ColorShiftTop
	atmosphere.Decay = theme.AtmosphereDecay or theme.FogColor
	atmosphere.Parent = Lighting

	local bloom = Lighting:FindFirstChildOfClass("BloomEffect") or Instance.new("BloomEffect")
	bloom.Intensity = 0.7
	bloom.Size = 24
	bloom.Threshold = 0.9
	bloom.Parent = Lighting

	if theme.SunRays then
		local rays = Lighting:FindFirstChildOfClass("SunRaysEffect") or Instance.new("SunRaysEffect")
		rays.Intensity = theme.SunRays.Intensity
		rays.Spread = theme.SunRays.Spread
		rays.Parent = Lighting
	end
	if theme.Grade then
		local grade = Lighting:FindFirstChildOfClass("ColorCorrectionEffect") or Instance.new("ColorCorrectionEffect")
		grade.Brightness = theme.Grade.Brightness
		grade.Contrast = theme.Grade.Contrast
		grade.Saturation = theme.Grade.Saturation
		grade.TintColor = theme.Grade.Tint
		grade.Parent = Lighting
	end
end

-- === the contract ====================================================
-- The three things other systems look up by name. They live here, alone,
-- because BOTH paths through HubBuilder need them: the generated hub builds
-- them inline, and an authored hub has them added by ensureContract when the
-- artist did not supply them. Duplicating any of these would let an authored
-- hub drift from a generated one.

--- What FateSystem measures roll distance from. Invisible, non-colliding.
local function buildRollAnchor(parent: Instance): BasePart
	local cfg = Layout.FateEngine
	local anchor = part({
		Name = Constants.NAMES.ROLL_ANCHOR,
		Size = cfg.AnchorSize,
		Position = Anchors.FATE_ENGINE + Vector3.new(0, cfg.AnchorHeight, 0),
		Transparency = 1,
		CanCollide = false,
	}, parent)
	anchor:SetAttribute("IsRollAnchor", true)

	-- ProximityPrompt over a bespoke keybind: blueprint §2.2 calls it the
	-- clearer mobile affordance, and it handles keyboard, gamepad and touch
	-- natively. The client listens for Triggered; the server still validates
	-- distance and cooldown independently (build spec §3.4).
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "RollPrompt"
	prompt.ActionText = "ROLL"
	prompt.ObjectText = "Fate Engine"
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = GameConfig.UI.PromptActivationDistance
	prompt.RequiresLineOfSight = false
	prompt.Parent = anchor

	return anchor
end

--- THE WAY INTO A BIOME, ON THE ENGINE ITSELF.
---
--- Owner-directed 2026-09-21. The staircase up to the portal is not modelled
--- yet, but the teleport and the biome scripts need testing now -- so the
--- portal is enterable from the dais, and the stairs become art rather than a
--- blocker.
---
--- It carries the GATE_ANCHOR name deliberately: ExpeditionSystem finds entry
--- by that name wherever it sits, so moving entry from the market to the
--- Engine (and later to the top of a staircase) is a placement decision here
--- rather than a change to a system.
local function buildEngineEntryAnchor(parent: Instance): BasePart?
	if not GameConfig.Expedition.Enabled or not GameConfig.Expedition.EntryAtEngine then
		return nil
	end

	local cfg = Layout.FateEngine
	local anchor = part({
		Name = Constants.NAMES.GATE_ANCHOR,
		Size = cfg.AnchorSize,
		-- Above the roll anchor rather than beside it: the two prompts share
		-- one dais, and stacking keeps both inside their own reach from
		-- anywhere a player can stand on it.
		Position = Anchors.FATE_ENGINE + Vector3.new(0, cfg.AnchorHeight + cfg.EntryPromptLift, 0),
		Transparency = 1,
		CanCollide = false,
	}, parent)
	anchor:SetAttribute("IsGateAnchor", true)

	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "EnterPrompt"
	prompt.ActionText = "ENTER"
	prompt.ObjectText = "The Portal"
	prompt.HoldDuration = 0.5
	prompt.MaxActivationDistance = GameConfig.UI.PromptActivationDistance
	prompt.RequiresLineOfSight = false
	prompt.Enabled = true

	-- A DIFFERENT KEY FROM ROLL. Every ProximityPrompt defaults to E, and two
	-- of them on one dais would fight over it. Resolved through the same
	-- allow-list every other key in content uses, so a typo warns here rather
	-- than throwing on every keystroke somewhere else.
	local keyName = GameConfig.Expedition.EntryPromptKey
	if Constants.HOTKEY_NAMES[keyName] then
		local ok, keyCode = pcall(function()
			return (Enum.KeyCode :: any)[keyName]
		end)
		if ok then
			prompt.KeyboardKeyCode = keyCode
		end
	else
		warn(`[HubBuilder] entry prompt key '{tostring(keyName)}' is not in Constants.HOTKEY_NAMES`)
	end

	prompt.Parent = anchor
	return anchor
end

--- What ExpeditionSystem measures entry distance from, and where the ENTER
--- prompt lives. Decoupled from the portal art on purpose: a ProximityPrompt
--- measures from its part's origin, and a plinth wider than the prompt's reach
--- locks the player out while standing on it. That shipped once.
local function buildGateAnchor(zone: any, top: Vector3, parent: Instance): BasePart
	local anchor = part({
		Name = Constants.NAMES.GATE_ANCHOR,
		Size = Vector3.new(
			zone.PortalScale * GameConfig.HubLayout.GateAnchorSpan,
			1,
			zone.PortalScale * GameConfig.HubLayout.GateAnchorSpan
		),
		Position = top
			+ Vector3.new(0, GameConfig.Portal.MaxPlinthHeight + GameConfig.HubLayout.GateAnchorLift, 0),
		Transparency = 1,
		CanCollide = false,
	}, parent)
	anchor:SetAttribute("IsGateAnchor", true)

	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "EnterPrompt"
	prompt.ActionText = "ENTER"
	prompt.ObjectText = "Expedition Gate"
	prompt.HoldDuration = 0.5
	prompt.MaxActivationDistance = GameConfig.UI.PromptActivationDistance
	prompt.RequiresLineOfSight = false
	prompt.Enabled = GameConfig.Expedition.Enabled
	prompt.Parent = anchor

	return anchor
end

--- Where a player arrives. Non-colliding, so it cannot become a lip on the
--- walkway it sits over.
--- A RING OF INVISIBLE PADS AROUND THE ENGINE'S DAIS, not one visible pad.
---
--- Owner-directed after the first authored walk. Invisible because the
--- authored plaza already has a floor worth looking at and a glowing disc on
--- it is set dressing nobody asked for; a ring because several players
--- arriving at once must not stack inside each other.
---
--- Every pad faces the Engine. A new player's first frame must contain the
--- thing the game is about -- that rule survives the move, it just no longer
--- costs a 250-stud walk to honour.
local function buildSpawn(parent: Instance): SpawnLocation
	local ring = GameConfig.HubLayout.SpawnRing

	local folder = Instance.new("Folder")
	folder.Name = "SpawnPads"
	folder.Parent = parent

	local first: SpawnLocation? = nil
	for i = 1, ring.Count do
		local angle = (i - 1) / ring.Count * math.pi * 2
		local position = Vector3.new(
			math.sin(angle) * ring.Radius,
			ring.Height,
			math.cos(angle) * ring.Radius
		)

		local spawn = Instance.new("SpawnLocation")
		spawn.Name = `SpawnPad{i}`
		spawn.Anchored = true
		-- Non-colliding, so a pad can never become a lip on the deck it sits
		-- over. The player drops the last couple of studs onto the floor.
		spawn.CanCollide = false
		spawn.Size = Vector3.new(12, 1, 12)
		spawn.Transparency = 1
		spawn.Neutral = true
		spawn.TopSurface = Enum.SurfaceType.Smooth
		spawn.CFrame = CFrame.lookAt(position, Vector3.new(0, position.Y, 0))
		spawn.Parent = folder

		first = first or spawn
	end

	return first :: SpawnLocation
end

--- Removes what a fresh Roblox place ships with. The default Baseplate sits at
--- Y 0 -- exactly where the authored plaza's top surface is -- so it z-fights
--- the floor and extends past it; the default SpawnLocation drops players onto
--- the Baseplate instead of into the ring above.
---
--- Deliberately conservative: it takes the Baseplate by name and SpawnLocations
--- that are direct children of Workspace, which is where Roblox puts its own
--- and where ours never are (they live under the Crossroads). Anything an
--- author has deliberately placed elsewhere is left alone.
local function clearPlaceDefaults(): ()
	local removed = {}
	for _, child in Workspace:GetChildren() do
		if child.Name == "Baseplate" and child:IsA("BasePart") then
			table.insert(removed, child.Name)
			child:Destroy()
		elseif child:IsA("SpawnLocation") then
			table.insert(removed, `SpawnLocation '{child.Name}'`)
			child:Destroy()
		end
	end
	if #removed > 0 then
		print(`[HubBuilder] removed place defaults: ` .. table.concat(removed, ", "))
	end
end

-- === centre: Fate Engine =============================================

-- Every part an authored Engine must supply, because something in code drives
-- it by this exact name: PortalRig spins and reskins the portal, HubEffects
-- turns the shards. A delivery missing one of these still builds -- the rest
-- of the Engine is fine -- but it warns rather than going quietly dead, which
-- is the failure the MeshId seam taught us to shout about.
local ENGINE_CONTRACT = { "Platform", "Plinth", "OuterRing", "InnerRing", "PortalPlane", "SpotAnchor" }
do
	for i = 1, 8 do
		table.insert(ENGINE_CONTRACT, `Rune{i}`)
		table.insert(ENGINE_CONTRACT, `Glyph{i}`)
	end
	for i = 1, 6 do
		table.insert(ENGINE_CONTRACT, `Shard{i}`)
	end
	for i = 1, 16 do
		table.insert(ENGINE_CONTRACT, `Inlay{i}`)
	end
end

local function buildFateEngine(parent: Instance): Model
	local cfg = Layout.FateEngine
	local base = Anchors.FATE_ENGINE

	local engine = Instance.new("Model")
	engine.Name = Constants.NAMES.FATE_ENGINE
	engine.Parent = parent

	-- THE AUTHORED ENGINE, when there is one. Whole-rig replacement: the
	-- prefab carries the dais, the plinth, the rune ring, the portal and the
	-- shards, so none of the blockout below runs. The spotlight and the
	-- RollAnchor are still ours -- they are behaviour, not art.
	--
	-- The blockout path underneath stays live and untouched. A place without
	-- Rojo, or with the file missing, builds exactly what it built before.
	if cfg.Prefab then
		local built = PrefabLoader.build(
			{ AssetKey = cfg.Prefab.AssetKey, Scale = cfg.Prefab.Scale, Styles = cfg.PrefabStyles },
			ENGINE_CONTRACT,
			-- Offset lands the dais flush with the walkways that meet it, so
			-- a player walks on rather than steps up. Content derives it; see
			-- FateEngine.Prefab.Offset.
			CFrame.new(base + (cfg.Prefab.Offset or Vector3.zero)),
			engine,
			"Authored"
		)
		if built then
			if #built.Missing > 0 then
				warn(
					`[HubBuilder] {cfg.Prefab.AssetKey} is missing {#built.Missing} contract part(s): `
						.. table.concat(built.Missing, ", ")
						.. " -- those will not animate or reskin"
				)
			end
			print(
				string.format(
					"[HubBuilder] Fate Engine: authored prefab, %d parts at %.3f scale",
					built.PartCount,
					cfg.Prefab.Scale
				)
			)

			local rig = built.Model:FindFirstChild("EngineRig")
			if rig and rig:IsA("Model") then
				-- Reparent to the Engine so HubEffects finds it at the path
				-- it has always looked at: FateEngine/EngineRig.
				rig.Parent = engine
				rig:SetAttribute("Rarity", cfg.IdleRarity)
				rig:SetAttribute("State", "Idle")
				rig:SetAttribute("Scale", cfg.Prefab.Scale)
				PortalRig.attachEffects(rig, cfg.IdleRarity)
				PortalRig.setRarity(rig, cfg.IdleRarity)
			end

			local spotAnchor = built.Model:FindFirstChild("SpotAnchor", true)
			if spotAnchor and spotAnchor:IsA("BasePart") then
				local spot = Instance.new("SpotLight")
				spot.Color = cfg.SpotLight.Color
				spot.Brightness = cfg.SpotLight.Brightness
				spot.Range = cfg.SpotLight.Range
				spot.Angle = cfg.SpotLight.Angle
				spot.Face = Enum.NormalId.Bottom
				spot.Parent = spotAnchor
			end

			local authoredAnchor = buildRollAnchor(engine)
			buildEngineEntryAnchor(engine)
			engine.PrimaryPart = authoredAnchor
			return engine
		end

		warn(
			`[HubBuilder] prefab '{cfg.Prefab.AssetKey}' not found in ServerStorage.`
				.. `{Constants.NAMES.PREFABS_FOLDER} -- drawing the blockout Engine instead`
		)
	end

	-- Raised marble platform with a radial rune inlay.
	cylinder({
		Name = "Platform",
		Size = Vector3.new(cfg.PlatformRaise, cfg.PlatformRadius * 2, cfg.PlatformRadius * 2),
		Position = base + Vector3.new(0, cfg.PlatformRaise / 2, 0),
		Color = cfg.PlatformColor,
		Material = cfg.PlatformMaterial,
	}, engine)

	local inlay = Instance.new("Folder")
	inlay.Name = "RuneInlay"
	inlay.Parent = engine
	for i = 1, cfg.RuneInlayCount do
		local angle = (i - 1) / cfg.RuneInlayCount * math.pi * 2
		part({
			Name = `Inlay{i}`,
			Size = Vector3.new(0.6, 0.12, cfg.PlatformRadius * 0.85),
			CFrame = CFrame.new(base + Vector3.new(0, cfg.PlatformRaise + 0.02, 0))
				* CFrame.Angles(0, angle, 0)
				* CFrame.new(0, 0, -cfg.PlatformRadius * 0.45),
			Color = cfg.RuneInlayColor,
			Material = Enum.Material.Neon,
			CanCollide = false,
		}, inlay)
	end

	-- The Engine is the shared PortalRig at 1.5x. Blueprint §2.2.
	if not meshOrNil(
		cfg.MeshId,
		Vector3.new(cfg.PlatformRadius, 40, cfg.PlatformRadius),
		CFrame.new(base + Vector3.new(0, 20, 0)),
		"EngineMesh",
		engine
	) then
		PortalRig.build({
			Name = "EngineRig",
			Position = base + Vector3.new(0, cfg.PlatformRaise, 0),
			Scale = cfg.PortalScale,
			Rarity = cfg.IdleRarity,
			PlinthMaterial = Enum.Material.SmoothPlastic,
			OuterMaterial = Enum.Material.SmoothPlastic,
		}, engine)
	end

	-- Six free-floating crystal shards, slow independent rotation.
	local shardCfg = cfg.CrystalShards
	local shards = Instance.new("Folder")
	shards.Name = "CrystalShards"
	shards.Parent = engine

	local shardRng = Random.new(Layout.FloatingIslands.Seed)
	for i = 1, shardCfg.Count do
		local angle = (i - 1) / shardCfg.Count * math.pi * 2
		local height = shardRng:NextNumber(shardCfg.MinHeight, shardCfg.MaxHeight)
		local shard = part({
			Name = `Shard{i}`,
			Size = Vector3.new(shardCfg.Size, shardCfg.Size * 2.4, shardCfg.Size),
			CFrame = CFrame.new(base + Vector3.new(
				math.cos(angle) * shardCfg.OrbitRadius,
				height,
				math.sin(angle) * shardCfg.OrbitRadius
			)) * CFrame.Angles(
				shardRng:NextNumber(-0.4, 0.4),
				shardRng:NextNumber(0, math.pi * 2),
				shardRng:NextNumber(-0.4, 0.4)
			),
			Color = Constants.RARITY[cfg.IdleRarity].Color,
			Material = shardCfg.Material,
			CanCollide = false,
			Transparency = 0.35,
		}, shards)
		shard:SetAttribute("SpinSpeed", shardRng:NextNumber(shardCfg.SpinSpeedMin, shardCfg.SpinSpeedMax))
		shard:SetAttribute("IsFeaturedShard", true)
	end

	-- Warm gold spotlight from above. Blueprint §2.2.
	local spotAnchor = part({
		Name = "SpotAnchor",
		Size = Vector3.new(2, 2, 2),
		Position = base + Vector3.new(0, cfg.SpotLight.Height, 0),
		Transparency = 1,
		CanCollide = false,
	}, engine)

	local spot = Instance.new("SpotLight")
	spot.Color = cfg.SpotLight.Color
	spot.Brightness = cfg.SpotLight.Brightness
	spot.Range = cfg.SpotLight.Range
	spot.Angle = cfg.SpotLight.Angle
	spot.Face = Enum.NormalId.Bottom
	spot.Parent = spotAnchor

	local anchor = buildRollAnchor(engine)
	buildEngineEntryAnchor(engine)
	engine.PrimaryPart = anchor
	return engine
end

-- === zone builders, dispatched by Kind ===============================

local function buildPlatform(zone: any, centre: Vector3, parent: Instance)
	if meshOrNil(zone.MeshId, zone.PlatformSize, CFrame.new(centre), "ZoneMesh", parent) then
		return
	end

	-- A ROUND zone gets a disc, not a box. Shape is declared in the data
	-- rather than implied by which builder happens to run -- a district that
	-- got both a box from here and a disc from its own builder, one buried
	-- inside the other, is what taught that lesson.
	if zone.PlatformShape == "ROUND" then
		cylinder({
			Name = "Platform",
			Size = Vector3.new(
				zone.PlatformSize.Y,
				zone.PlatformRadius * 2,
				zone.PlatformRadius * 2
			),
			Position = centre,
			Color = zone.Color,
			Material = zone.PlatformMaterial,
		}, parent)
		return
	end

	part({
		Name = "Platform",
		Size = zone.PlatformSize,
		Position = centre,
		Color = zone.Color,
	}, parent)
end

local function buildAmphitheatre(zone: any, centre: Vector3, parent: Instance)
	-- Semicircular tiered seating facing a row of obelisks. Blueprint §2.2.
	for tier = 1, zone.TierCount do
		local radius = 16 + tier * 6
		local segments = 14
		for i = 0, segments do
			-- Half-circle only: seating faces the obelisk row.
			local angle = math.pi + (i / segments) * math.pi
			part({
				Name = `Tier{tier}_Seat{i}`,
				Size = Vector3.new(5, 1.6, 4),
				CFrame = CFrame.new(centre + Vector3.new(
					math.cos(angle) * radius,
					zone.PlatformSize.Y / 2 + tier * 1.6,
					math.sin(angle) * radius
				)) * CFrame.Angles(0, -angle, 0),
				Color = zone.Color,
				Material = Enum.Material.SmoothPlastic,
			}, parent)
		end
	end

	local obelisks = Instance.new("Folder")
	obelisks.Name = "Obelisks"
	obelisks.Parent = parent

	for slot = 1, zone.ObeliskSlots do
		local offset = (slot - (zone.ObeliskSlots + 1) / 2) * 9
		local obelisk = part({
			Name = `Obelisk{slot}`,
			Size = Vector3.new(3, zone.ObeliskHeight, 3),
			Position = centre + Vector3.new(offset, zone.PlatformSize.Y / 2 + zone.ObeliskHeight / 2, -6),
			Color = zone.Color,
			Material = Enum.Material.SmoothPlastic,
		}, obelisks)
		obelisk:SetAttribute("WorldFirstSlot", slot)

		part({
			Name = `ObeliskCap{slot}`,
			Size = Vector3.new(3.4, 0.6, 3.4),
			Position = obelisk.Position + Vector3.new(0, zone.ObeliskHeight / 2, 0),
			Color = zone.Accent,
			Material = Enum.Material.Neon,
			CanCollide = false,
		}, obelisks)

		-- Empty until a World First is claimed (Master Spec §13).
		label("—", zone.Accent, UDim2.fromScale(6, 2), obelisk, 180)

		-- Cool white, so legends read as museum pieces against warm ambient.
		local spot = Instance.new("SpotLight")
		spot.Color = zone.SpotColor
		spot.Brightness = 3
		spot.Range = 28
		spot.Angle = 45
		spot.Face = Enum.NormalId.Top
		spot.Parent = obelisk
	end
end

local function buildRotunda(zone: any, centre: Vector3, parent: Instance)
	local radius = zone.InteriorDiameter / 2
	local top = centre.Y + zone.PlatformSize.Y / 2

	for i = 1, zone.Pillars do
		local angle = (i - 1) / zone.Pillars * math.pi * 2
		part({
			Name = `Column{i}`,
			Size = Vector3.new(2.4, zone.PillarHeight, 2.4),
			Position = Vector3.new(
				centre.X + math.cos(angle) * radius,
				top + zone.PillarHeight / 2,
				centre.Z + math.sin(angle) * radius
			),
			Color = zone.Color,
		}, parent)
	end

	-- Stepped dome: each ring narrower and higher than the last.
	for segment = 1, zone.DomeSegments do
		local t = segment / zone.DomeSegments
		cylinder({
			Name = `Dome{segment}`,
			Size = Vector3.new(1.4, radius * 2 * (1 - t * 0.85), radius * 2 * (1 - t * 0.85)),
			Position = Vector3.new(centre.X, top + zone.PillarHeight + segment * 1.6, centre.Z),
			Color = zone.Color,
			CanCollide = false,
		}, parent)
	end

	-- Floating bookshelves: rings orbiting at different heights, cosmetic.
	local shelves = Instance.new("Folder")
	shelves.Name = "FloatingShelves"
	shelves.Parent = parent

	for ring = 1, zone.ShelfRings do
		local ringRadius = radius * (0.35 + ring * 0.18)
		local height = top + 3 + ring * 3.5
		for i = 1, zone.ShelvesPerRing do
			local angle = (i - 1) / zone.ShelvesPerRing * math.pi * 2
			local shelf = part({
				Name = `Shelf_R{ring}_{i}`,
				Size = Vector3.new(3.6, 0.5, 1.4),
				CFrame = CFrame.new(
					centre.X + math.cos(angle) * ringRadius,
					height,
					centre.Z + math.sin(angle) * ringRadius
				) * CFrame.Angles(0, -angle, 0),
				Color = zone.Accent,
				Material = Enum.Material.Neon,
				CanCollide = false,
				Transparency = 0.25,
			}, shelves)
			shelf:SetAttribute("OrbitRadius", ringRadius)
			shelf:SetAttribute("OrbitSpeed", 0.08 + ring * 0.04)
			shelf:SetAttribute("OrbitHeight", height)
			-- The client orbits these; it must not have to re-derive the
			-- zone centre from the layout.
			shelf:SetAttribute("OrbitCentre", Vector3.new(centre.X, height, centre.Z))
		end
	end

	local podium = part({
		Name = "Podium",
		Size = Vector3.new(3, 4, 3),
		Position = Vector3.new(centre.X, top + 2, centre.Z),
		Color = zone.Accent,
		Material = Enum.Material.Neon,
	}, parent)

	-- Phase 2 opens the Discovery Book here; the affordance exists now so the
	-- zone reads as interactive rather than decorative.
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "ArchivePrompt"
	prompt.ActionText = "Open Discovery Book"
	prompt.ObjectText = "Discovery Archive"
	prompt.MaxActivationDistance = 10
	prompt.RequiresLineOfSight = false
	prompt.Enabled = false -- Phase 2
	prompt.Parent = podium
end

local function buildGate(zone: any, centre: Vector3, parent: Instance)
	local top = centre + Vector3.new(0, zone.PlatformSize.Y / 2, 0)

	-- The largest portal in the hub. Blueprint §2.2.
	PortalRig.build({
		Name = "GateRig",
		Position = top,
		Scale = zone.PortalScale,
		Rarity = "COMMON",
		PlinthMaterial = Enum.Material.SmoothPlastic,
		OuterMaterial = Enum.Material.CorrodedMetal,
	}, parent)

	-- The part the ENTER prompt lives on, and the part the server measures
	-- entry distance from. Exactly the RollAnchor pattern from the Fate
	-- Engine, and for the same two reasons.
	--
	-- A ProximityPrompt measures from its parent part's ORIGIN. Hanging the
	-- prompt on the plinth meant measuring from the plinth's centre, and the
	-- plinth is wider than the prompt's reach -- so a player standing on it
	-- was already out of range. An anchor decouples "where the prompt is"
	-- from "how big the art is", which is what lets the rig be rebuilt in
	-- Blender at any size without breaking entry.
	buildGateAnchor(zone, top, parent)

	-- Processional walkway with flanking torch pillars: deliberately the most
	-- dramatic sightline in the hub, visible from the Fate Engine.
	local torches = Instance.new("Folder")
	torches.Name = "TorchPillars"
	torches.Parent = parent

	local perSide = math.max(1, math.floor(zone.Pillars / 2))
	for side = -1, 1, 2 do
		for i = 1, perSide do
			local z = centre.Z - i * 11
			local pillar = part({
				Name = `Torch_{side}_{i}`,
				Size = Vector3.new(2.4, zone.PillarHeight, 2.4),
				Position = Vector3.new(
					centre.X + side * (GameConfig.HubLayout.ProcessionalWidth / 2 + 3),
					centre.Y + zone.PillarHeight / 2,
					z
				),
				Color = zone.Color,
			}, torches)

			local flame = part({
				Name = "Flame",
				Size = Vector3.new(1.6, 1.6, 1.6),
				Position = pillar.Position + Vector3.new(0, zone.PillarHeight / 2 + 0.8, 0),
				Color = Layout.Theme.TorchLight,
				Material = Enum.Material.Neon,
				CanCollide = false,
			}, torches)

			local flameLight = Instance.new("PointLight")
			flameLight.Color = Layout.Theme.TorchLight
			flameLight.Brightness = 2
			flameLight.Range = 22
			flameLight.Parent = flame
		end
	end
end

local function buildYard(zone: any, centre: Vector3, parent: Instance)
	local half = zone.PlatformSize.X / 2
	local top = centre.Y + zone.PlatformSize.Y / 2

	-- Low fencing, no roof: visibly the practical zone, not a mystical one.
	for side = 1, 4 do
		local angle = (side - 1) * math.pi / 2
		part({
			Name = `Fence{side}`,
			Size = Vector3.new(zone.PlatformSize.X, zone.FenceHeight, 0.6),
			CFrame = CFrame.new(centre + Vector3.new(0, top - centre.Y + zone.FenceHeight / 2, 0))
				* CFrame.Angles(0, angle, 0)
				* CFrame.new(0, 0, -half),
			Color = zone.Color,
		}, parent)
	end

	-- Static dummy rigs only. Blueprint §2.2 wants them to respond to attack
	-- input, but combat is explicitly excluded from Phase 1 (build spec §7),
	-- so these are geometry and an attribute for Phase 2 to find. No combat
	-- behaviour is attached here.
	local dummies = Instance.new("Folder")
	dummies.Name = "TargetDummies"
	dummies.Parent = parent

	for i = 1, zone.DummyCount do
		local offset = (i - (zone.DummyCount + 1) / 2) * 7
		local dummy = part({
			Name = `TargetDummy{i}`,
			Size = Vector3.new(2.4, 6, 2.4),
			Position = centre + Vector3.new(offset, top - centre.Y + 3, -half + 6),
			Color = Color3.fromRGB(150, 128, 96),
			Material = Enum.Material.WoodPlanks,
		}, dummies)
		dummy:SetAttribute("IsTrainingDummy", true)
		dummy:SetAttribute("Phase", 2)
	end

	if zone.HasBossDummy then
		local boss = part({
			Name = "BossDummy",
			Size = Vector3.new(5, 10, 5),
			Position = centre + Vector3.new(0, top - centre.Y + 5, half - 7),
			Color = Color3.fromRGB(96, 84, 70),
			Material = Enum.Material.WoodPlanks,
		}, dummies)
		boss:SetAttribute("IsTrainingDummy", true)
		boss:SetAttribute("IsBossDummy", true)
		boss:SetAttribute("Phase", 2)
		label("Practice Target", zone.Accent, UDim2.fromScale(10, 2), boss, 140)
	end

	for i = 1, zone.TorchCount do
		local angle = (i - 1) / zone.TorchCount * math.pi * 2
		local torch = part({
			Name = `PracticeTorch{i}`,
			Size = Vector3.new(1, 4, 1),
			Position = centre + Vector3.new(
				math.cos(angle) * (half - 2),
				top - centre.Y + 2,
				math.sin(angle) * (half - 2)
			),
			Color = zone.Color,
		}, parent)

		local light = Instance.new("PointLight")
		light.Color = Layout.Theme.TorchLight
		light.Brightness = 1.6
		light.Range = 18
		light.Parent = torch
	end
end

local ZONE_BUILDERS: { [string]: (any, Vector3, Instance) -> () } = {
	AMPHITHEATRE = buildAmphitheatre,
	ROTUNDA = buildRotunda,
	GATE = buildGate,
	YARD = buildYard,
}

-- === assembly ========================================================

local function buildWalkway(zone: any, centre: Vector3, parent: Instance)
	local bridges = Layout.Bridges
	local flat = Vector3.new(centre.X, 0, centre.Z)
	if flat.Magnitude < 1 then
		return -- a district at the hub's centre needs no radial walkway
	end

	local dir = flat.Unit

	-- HALF-EXTENT ALONG THE APPROACH, not always X. Hall of Legends is
	-- 360x280 and is approached down -Z, so its near edge is 140 studs out,
	-- not 180 -- using X left a 40-stud hole in the floor between the walkway
	-- and the platform. The Expedition Gate had a 30-stud one for the same
	-- reason. Projecting the platform's extents onto the approach direction
	-- gets it right for every zone, including any future diagonal.
	local half = math.abs(dir.X) * zone.PlatformSize.X / 2
		+ math.abs(dir.Z) * zone.PlatformSize.Z / 2

	-- Walkway tops must MEET the surfaces they join, or every trip ends in a
	-- step the player has to jump. Both ends are computed from the top face of
	-- what they land on, and the deck is sloped between them.
	local engineTop = Layout.FateEngine.PlatformRaise
	local zoneTop = centre.Y + zone.PlatformSize.Y / 2
	local deck = bridges.Thickness / 2

	-- Overlap both ends slightly so there is no hairline seam to catch on.
	local inner = dir * (Layout.FateEngine.PlatformRadius - bridges.Overlap)
	local outer = flat - dir * (half - bridges.Overlap)
	inner = Vector3.new(inner.X, engineTop - deck, inner.Z)
	outer = Vector3.new(outer.X, zoneTop - deck, outer.Z)

	local delta = outer - inner
	local length = delta.Magnitude
	if length < 1 then
		return
	end

	local width = if zone.Kind == "GATE" then bridges.ProcessionalWidth else bridges.Width

	part({
		Name = `Walkway_{zone.Id}`,
		Size = Vector3.new(width, bridges.Thickness, length),
		CFrame = CFrame.lookAt(inner + delta / 2, outer),
		Color = bridges.Color,
		Material = bridges.Material,
	}, parent)
end

local function buildFloatingIslands(parent: Instance)
	local cfg = Layout.FloatingIslands
	local rng = Random.new(cfg.Seed) -- deterministic: one skyline per server
	local folder = Instance.new("Folder")
	folder.Name = "FloatingIslands"
	folder.Parent = parent

	for i = 1, cfg.Count do
		local angle = rng:NextNumber() * math.pi * 2
		local radius = rng:NextNumber(cfg.MinRadius, cfg.MaxRadius)
		local size = rng:NextNumber(cfg.MinSize, cfg.MaxSize)
		part({
			Name = `Island{i}`,
			Size = Vector3.new(size, size * 0.4, size * rng:NextNumber(0.7, 1.3)),
			Position = Vector3.new(
				math.cos(angle) * radius,
				rng:NextNumber(cfg.MinHeight, cfg.MaxHeight),
				math.sin(angle) * radius
			),
			Color = cfg.Color,
			CanCollide = false,
		}, folder)
	end
end

-- === the authored hub shell ==========================================

-- Every part of the authored Crossroads that something outside the art
-- depends on: the floor players stand on, the marker the whole model is
-- registered from, the four walkways that join the centre to the districts,
-- and the four district decks. A delivery missing one of these still builds --
-- the rest of the hub is fine -- but it says so, rather than going quietly
-- wrong in a place nobody looks. Same contract-or-warn rule as ENGINE_CONTRACT.
local SHELL_CONTRACT = {
	"Plaza",
	"EngineReserve",
	"Walkway_North",
	"Walkway_East",
	"Walkway_West",
	"Processional_South",
	"District_Leaderboard",
	"District_Archive",
	"District_Shop",
	"District_Training",
}

--- Clones a hub-scale prefab in, or returns nil so the caller falls through
--- to the blockout. Exactly the shape buildFateEngine's prefab branch has --
--- the seam was built to take a second and a third piece without new code,
--- and this is that turning out to be true.
local function buildHubPrefab(
	cfg: any,
	contract: { string },
	name: string,
	parent: Instance
): Model?
	if not cfg or not cfg.Prefab then
		return nil
	end

	local built = PrefabLoader.build({
		AssetKey = cfg.Prefab.AssetKey,
		Scale = cfg.Prefab.Scale,
		YawDegrees = cfg.Prefab.YawDegrees,
		AnchorPart = cfg.Prefab.AnchorPart,
		AnchorOffset = cfg.Prefab.AnchorOffset,
		Styles = cfg.Styles,
	}, contract, CFrame.new(Anchors.FATE_ENGINE), parent, name)

	if not built then
		print(
			`[HubBuilder] prefab '{cfg.Prefab.AssetKey}' not found in ServerStorage.`
				.. `{Constants.NAMES.PREFABS_FOLDER} -- using the blockout instead`
		)
		return nil
	end

	if #built.Missing > 0 then
		warn(
			`[HubBuilder] {cfg.Prefab.AssetKey} is missing {#built.Missing} contract part(s): `
				.. table.concat(built.Missing, ", ")
		)
	end

	print(
		`[HubBuilder] {name}: authored {cfg.Prefab.AssetKey}, `
			.. `{built.PartCount} part(s) at scale {cfg.Prefab.Scale}`
	)
	return built.Model
end

--- THE AUTHORED CROSSROADS. When this loads, none of the blockout plaza,
--- district or walkway geometry below runs: the art supplies all of it, and
--- only BEHAVIOUR is built on top -- the Fate Engine, the roll and gate
--- anchors, the district labels and the spawn.
---
--- It is placed at the hub centre at floor level, and the authored plaza's
--- top surface lands on Y 0 -- which is exactly where the blockout plaza's
--- top is. That is not a coincidence to be grateful for, it is the whole
--- reason the Engine, the spawn and every anchor need no adjustment in either
--- build.
local function buildShell(parent: Instance): Model?
	return buildHubPrefab(Layout.Shell, SHELL_CONTRACT, "Shell", parent)
end

--- THE MOUNTAIN HORIZON, BUILT RATHER THAN PLACED.
---
--- The delivered backdrop is one ring-shaped model, and placing it whole
--- failed three times over: the distance from the hub to its nearest peak is a
--- property of the MESH, which lives in a Roblox asset nothing here can
--- measure, so every scale was a guess -- and scaling moves size and distance
--- together anyway, so a smaller ring is also a closer one.
---
--- Cloning one chunk around a circle makes distance a number we choose instead
--- of one we discover. Same shape as buildFloatingIslands, and for the same
--- reason: a seeded Random so every server shows one skyline.
---
--- Decoration with no contract. A place without the file simply has no
--- mountains, and nothing else changes.
local function buildBackdrop(parent: Instance): Folder?
	local cfg = Layout.Backdrop
	local ring = cfg and cfg.Ring
	if not ring then
		return nil
	end

	local source = PrefabLoader.source(cfg.AssetKey)
	if not source then
		print(
			`[HubBuilder] prefab '{cfg.AssetKey}' not found in ServerStorage.`
				.. `{Constants.NAMES.PREFABS_FOLDER} -- the hub has no horizon`
		)
		return nil
	end

	local template = source:FindFirstChild(ring.Part, true)
	if not template or not template:IsA("BasePart") then
		warn(`[HubBuilder] {cfg.AssetKey} has no BasePart named '{ring.Part}'; no horizon built`)
		return nil
	end

	local folder = Instance.new("Folder")
	folder.Name = "Backdrop"
	folder.Parent = parent

	local style = cfg.Styles and cfg.Styles[ring.Part]
	local rng = Random.new(ring.Seed)

	for i = 1, ring.Count do
		local chunk = (template :: BasePart):Clone()
		chunk.Name = `Massif{i}`
		chunk.Anchored = true
		-- Never. It is 4000 studs of scenery no player can reach, and hulls
		-- for it would be pure cost.
		chunk.CanCollide = false
		chunk.CastShadow = false
		local jitter = 1 + rng:NextNumber(-ring.ScaleJitter, ring.ScaleJitter)
		chunk.Size = template.Size * (ring.Scale * jitter)

		if style then
			if style.Color then
				chunk.Color = style.Color
			end
			if style.Material then
				chunk.Material = style.Material
			end
			if style.Transparency then
				chunk.Transparency = style.Transparency
			end
		end

		-- Placed on the ring, then turned to face the centre, then jittered.
		-- The yaw is what keeps fourteen copies of one mesh from reading as
		-- fourteen copies of one mesh.
		local angle = (i - 1) / ring.Count * math.pi * 2
		local yaw = angle + math.rad(rng:NextNumber(-ring.YawJitterDegrees, ring.YawJitterDegrees))
		chunk.CFrame = CFrame.new(
			math.sin(angle) * ring.Radius,
			-- Standing ON the hub's ground plane, not floating over it.
			ring.BaseY + chunk.Size.Y / 2,
			math.cos(angle) * ring.Radius
		) * CFrame.Angles(0, yaw, 0)

		chunk.Parent = folder
	end

	print(`[HubBuilder] Backdrop: {ring.Count} massif(s) of '{ring.Part}' at radius {ring.Radius}`)
	return folder
end

--- Builds the hub if absent. Idempotent: a place that already contains a
--- hand-built Crossroads is left alone, so authored geometry always wins.
--- THE CONTRACT: the parts other systems look up by name.
---
--- `HubBuilder.build` hands the hub over to an authored Crossroads whenever one
--- is present -- authored art wins, which is the intent. But "authored art
--- wins" silently took the CONTRACT with it: `FateSystem` needs a `RollAnchor`
--- to measure roll distance from, `ExpeditionSystem` needs a `GateAnchor` and
--- its prompt, and players need somewhere to spawn. An artist who models a
--- beautiful Crossroads and names it `Crossroads` would switch off rolling and
--- expedition entry, with no error anywhere.
---
--- So the contract is checked separately from the geometry. A hand-built hub
--- that supplies these keeps them; one that does not gets them added, loudly.
--- Nothing here draws anything visible -- the anchors are invisible and
--- non-colliding, so adding them to authored art changes only behaviour.
local function ensureContract(hub: Instance): ()
	local added = {}

	local engine = hub:FindFirstChild(Constants.NAMES.FATE_ENGINE)
	if not engine then
		engine = Instance.new("Model")
		;(engine :: Model).Name = Constants.NAMES.FATE_ENGINE
		;(engine :: Model).Parent = hub
		table.insert(added, Constants.NAMES.FATE_ENGINE)
	end

	if not engine:FindFirstChild(Constants.NAMES.ROLL_ANCHOR) then
		buildRollAnchor(engine)
		table.insert(added, Constants.NAMES.ROLL_ANCHOR)
	end

	local zones = hub:FindFirstChild("Zones")
	if not zones then
		zones = Instance.new("Folder")
		;(zones :: Folder).Name = "Zones"
		;(zones :: Folder).Parent = hub
		table.insert(added, "Zones")
	end

	local gate = zones:FindFirstChild("EXPEDITION_GATE")
	if not gate then
		gate = Instance.new("Model")
		;(gate :: Model).Name = "EXPEDITION_GATE"
		;(gate :: Model).Parent = zones
		table.insert(added, "EXPEDITION_GATE")
	end

	-- NO GATE ANCHOR IS ADDED HERE ANY MORE. It used to be, on the reasoning
	-- that an artist who models a hub and names it Crossroads must not
	-- silently switch expedition entry off. That reasoning is now obsolete:
	-- entry is moving to the Fate Engine's portal, and the ENTER prompt in
	-- the middle of the market was the thing the first authored walk asked to
	-- be rid of. Putting it back here would resurrect it the moment anyone
	-- saved the built hub into the place.
	--
	-- ExpeditionSystem already tolerates a missing anchor -- it warns that
	-- entry is remote-only and carries on -- so nothing here can break. When
	-- the Engine carries entry, whatever it needs gets ensured in this spot.

	-- Looks for the FOLDER, not for a SpawnLocation. The pads live inside
	-- `SpawnPads`, and FindFirstChildOfClass does not recurse -- so checking
	-- for the class here would never find them and would stack a fresh ring
	-- on top of the existing one on every boot.
	if not hub:FindFirstChild("SpawnPads") then
		buildSpawn(hub)
		table.insert(added, "SpawnPads")
	end

	if #added > 0 then
		warn(
			`[HubBuilder] authored Crossroads was missing {#added} contract part(s); added: `
				.. table.concat(added, ", ")
				.. " -- see HubBuilder.ensureContract"
		)
	end
end

function HubBuilder.build(): Model
	-- Lighting is applied either way. It is a property of the PLACE, not of the
	-- geometry, and an authored hub in the dark is not an improvement.
	applyLighting()

	local existing = Workspace:FindFirstChild(Constants.NAMES.CROSSROADS)
	if existing then
		print("[HubBuilder] Crossroads already in Workspace; leaving its geometry alone")
		ensureContract(existing)
		existing:SetAttribute("Ready", true)
		return existing :: Model
	end

	local hub = Instance.new("Model")
	hub.Name = Constants.NAMES.CROSSROADS

	-- A fresh place ships with a Baseplate at Y 0 and a SpawnLocation on it.
	-- The authored plaza's top surface is also Y 0, so the two fight; and the
	-- default spawn lands players on the Baseplate rather than in the ring
	-- around the Engine. Both go before anything is built.
	clearPlaceDefaults()

	-- AUTHORED ART WINS, one piece at a time. With a shell present the plaza,
	-- the districts, the walkways and the skyline all come from it; without
	-- one, every line below builds exactly what it built before.
	-- THE CROSSROADS v2 when its art is in the place; else the old shell;
	-- else the blockout.
	local v2 = if GameConfig.HubLayout.V2.Enabled then HubV2.build(hub, Anchors.FATE_ENGINE) else nil
	local shell = v2 or buildShell(hub)

	if not shell then
		-- Lower plaza ring the raised walkways sit above.
		cylinder({
			Name = "Plaza",
			Size = Vector3.new(
				Layout.Plaza.Thickness,
				Layout.Plaza.Diameter,
				Layout.Plaza.Diameter
			),
			Position = Vector3.new(0, -Layout.Plaza.Thickness / 2, 0),
			Color = Layout.Plaza.Color,
			Material = Layout.Plaza.Material,
		}, hub)
	end

	-- The Engine is its own prefab and is built either way. The shell reserves
	-- its footprint and deliberately models nothing inside it.
	buildFateEngine(hub)

	local zones = Instance.new("Folder")
	zones.Name = "Zones"
	zones.Parent = hub

	for _, zone in Layout.Districts do
		local anchor = Anchors[zone.Id]
		assert(anchor, `HubLayout.Anchors is missing an entry for zone '{zone.Id}'`)
		local centre = anchor + Vector3.new(0, zone.Height, 0)

		local model = Instance.new("Model")
		model.Name = zone.Id
		model.Parent = zones

		-- WITH A SHELL, the platform, its dressing and its walkway are all in
		-- the art, and only behaviour is built here. The one thing that still
		-- has to be placed is the Expedition Gate's prompt -- see below.
		local deckTop
		if shell then
			deckTop = if v2 then GameConfig.HubLayout.V2.DeckHeight else Layout.Shell.DeckHeight

			-- NO GATE ANCHOR, AND NO ENTER PROMPT. Owner-directed after the
			-- first authored walk: a "Verdant Valley / ENTER" prompt standing
			-- in the middle of the market is not where a biome gets entered,
			-- and the Fate Engine's portal takes that job. See the note on
			-- Layout.Shell -- this leaves expedition entry remote-only until
			-- the Engine carries it, which is a deliberate gap.
		else
			deckTop = centre.Y + zone.PlatformSize.Y / 2

			buildPlatform(zone, centre, model)

			local builder = ZONE_BUILDERS[zone.Kind]
			assert(builder, `no builder for zone Kind '{zone.Kind}' (zone {zone.Id})`)
			builder(zone, centre, model)

			buildWalkway(zone, centre, hub)
		end

		local lift = if v2 then GameConfig.HubLayout.V2.SignLift elseif shell then Layout.Shell.SignLift else 12
		-- v2: the label floats over the district's own centre, 218 out.
		local at = if v2 then Anchors.FATE_ENGINE + (V2Layout.Pieces[V2_PIECE[zone.Id]] or { Centre = anchor }).Centre * Vector3.new(1, 0, 1) else anchor
		local sign = part({
			Name = "Sign",
			Size = Vector3.new(4, 1, 1),
			Position = Vector3.new(at.X, deckTop + lift, at.Z),
			Transparency = 1,
			CanCollide = false,
		}, model)
		-- Every zone is labelled so a tester can name where they are without
		-- being told. Master Spec §20's success criterion depends on it.
		label(if v2 then GameConfig.HubLayout.V2.Names[zone.Id] or zone.Name else zone.Name, zone.Accent,
			UDim2.fromScale(24, 5), sign, 320)
	end

	if not shell then
		buildFloatingIslands(hub)
	end

	-- The horizon is independent of the shell: it is the one piece that can
	-- stand behind either build without looking wrong.
	if v2 then
		HubV2.buildSky(hub, Anchors.FATE_ENGINE)
	else
		buildBackdrop(hub)
	end

	buildSpawn(hub)

	hub.Parent = Workspace
	-- THE DONE SIGNAL. A Model does not replicate atomically: the client can
	-- see the Crossroads before its descendants arrive, and with an authored
	-- Engine that is ~80 MeshParts of mesh data rather than a dozen
	-- primitives. A client that scans too early finds no rig and no shards,
	-- animates nothing, and never retries -- which looks exactly like broken
	-- animation code. Set last, so waiting on it means waiting for all of it.
	-- HOW MANY PARTS THE CLIENT SHOULD WAIT FOR.
	--
	-- `Ready` alone was not a barrier. An attribute replicates with the model
	-- it sits on, while that model's descendants stream in afterwards -- so a
	-- client saw Ready, scanned immediately, found the Crossroads and the
	-- EngineRig but NOT the OuterRing inside it, and animated nothing. The
	-- playtest log said exactly that: "engineRig found" next to "driving 0
	-- ring(s) -- NONE FOUND".
	--
	-- A count is a barrier an attribute cannot be: the client waits until it
	-- can actually see this many parts.
	do
		local parts = 0
		for _, d in hub:GetDescendants() do
			if d:IsA("BasePart") then
				parts += 1
			end
		end
		hub:SetAttribute("PartCount", parts)
	end
	hub:SetAttribute("Ready", true)
	print(`[HubBuilder] built Crossroads: {#Layout.Districts} zones, {#hub:GetDescendants()} instances`)
	return hub
end

return HubBuilder
