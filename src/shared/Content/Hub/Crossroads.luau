--!strict
-- The Crossroads, described as DATA. Biome Blueprint §2.
--
-- THIS FILE IS THE ART-DIRECTION DIAL. HubBuilder reads it and builds
-- geometry; it holds no art direction of its own. Changing how the hub looks
-- means editing numbers and colours here.
--
-- Positions come from GameConfig.HubLayout.Anchors, not from this file, per
-- blueprint §7.3: the axis mapping is confirmed once in Studio and locked in
-- one place rather than re-derived per script.
--
-- THE MESH SEAM: every swappable piece carries an optional MeshId. While nil
-- the builder generates primitives; set it to an asset id and the builder uses
-- the mesh at the same position, scale and pivot. Authored art replaces
-- blockout one piece at a time, with no flag day.

local GameConfig = require(script.Parent.Parent.Parent.Core.GameConfig)

local Layout = GameConfig.HubLayout

local Theme = {
	-- Blueprint §2.3, with the brightness deviation recorded below and in
	-- docs/BLUEPRINT_RECONCILIATION.md. Palette is unchanged; only the key
	-- light and the ambient fill moved.
	--
	-- BRIGHTNESS PASS, 2026-09-16. "Hub is very dark" has been open since the
	-- first Studio session. The blueprint's §2.3 values were authored against
	-- Roblox's default lighting; at ClockTime 22 with Future lighting and a
	-- 1150-stud footprint they left the plaza close to unreadable.
	--
	-- The fix is mostly ClockTime, not Brightness. Raising Brightness alone
	-- blows out the neon and the portal glow while leaving the stone flat,
	-- because at ClockTime 22 the sun is below the horizon and there is no key
	-- light to raise. Moving to 4.5 puts the sun just above it -- a low, raking
	-- pre-dawn light that still reads as night, keeps the purple sky, and gives
	-- the marble something to catch.
	Ambient = Color3.fromRGB(72, 66, 96),
	OutdoorAmbient = Color3.fromRGB(96, 88, 128),
	ColorShiftTop = Color3.fromRGB(90, 70, 140),
	ColorShiftBottom = Color3.fromRGB(30, 25, 50),
	FogColor = Color3.fromRGB(30, 25, 50),
	-- Fog must reach past the distant islands or the world looks boxed in --
	-- the blueprint's 150/500 was sized to a 120-stud hub.
	FogStart = 700,
	FogEnd = 4400,
	Brightness = 2.6,
	ExposureCompensation = 0.15,
	ClockTime = 4.5,

	-- Hub materials and accents.
	Marble = Color3.fromRGB(226, 221, 234),
	MarbleTrim = Color3.fromRGB(230, 178, 74), -- AccentGold, matches UITheme
	Plaza = Color3.fromRGB(58, 52, 76),
	Walkway = Color3.fromRGB(78, 70, 98),
	TorchLight = Color3.fromRGB(255, 176, 92),
	EngineSpot = Color3.fromRGB(255, 200, 120), -- blueprint §2.2

	StoneMaterial = Enum.Material.Marble,
	PlazaMaterial = Enum.Material.Slate,
}

local Crossroads = {
	Theme = Theme,
	SpawnOffset = Layout.SpawnAnchor,

	-- Lower plaza ring the raised walkways sit above. Blueprint §2.1.
	Plaza = {
		Diameter = Layout.HubDiameter,
		Thickness = 14,
		Color = Theme.Plaza,
		Material = Theme.PlazaMaterial,
		MeshId = nil,
	},

	-- Centre — Fate Engine. Blueprint §2.2.
	FateEngine = {
		Name = "FateEngine",
		-- 140 -> 120 with the world de-scale, then 120 -> 23 when the authored
		-- Engine arrived and the owner's verdict was "way too big".
		--
		-- THIS IS NOW DERIVED, not chosen: it is half the authored Platform's
		-- width at Prefab.Scale (101.0 * 0.464 / 2). The dais IS this radius,
		-- so the two cannot drift -- walkways are cut to meet this number and
		-- would otherwise stop short in mid-air. Asserted by test.
		PlatformRadius = 23,
		-- 10 -> 2, to match the authored dais (4.21 raw at Prefab.Scale). The
		-- blockout stands in for the real thing, so a player stepping onto it
		-- has to step the same distance in either build.
		PlatformRaise = 2,
		PlatformColor = Theme.Marble,
		PlatformMaterial = Enum.Material.Marble,
		RuneInlayCount = 16, -- radial groove pattern
		RuneInlayColor = Color3.fromRGB(124, 245, 224),

		PortalScale = GameConfig.Portal.FateEngineScale,
		-- The Engine cycles a "featured" rarity cosmetically; it is NOT the
		-- roll result and must never be read as a prediction.
		IdleRarity = "UNKNOWN",
		FeaturedCycleSeconds = 14,

		CrystalShards = {
			Count = 6,
			OrbitRadius = 100,
			MinHeight = 50,
			MaxHeight = 140,
			Size = 20,
			Material = Enum.Material.Glass,
			SpinSpeedMin = 0.2,
			SpinSpeedMax = 0.7,
		},

		SpotLight = {
			Color = Theme.EngineSpot,
			Brightness = 8,
			Range = 400,
			Angle = 80,
			Height = 300,
		},

		-- The roll pad, and it has to FIT the dais. At 90 it was wider than
		-- the whole re-tuned Engine, so the prompt would have floated out
		-- over open plaza.
		AnchorSize = Vector3.new(30, 1, 30),
		AnchorHeight = 6,
		MeshId = nil, -- superseded by Prefab below; kept for the blockout path

		-- THE AUTHORED ENGINE. Delivered 2026-09-18, 78 MeshParts.
		--
		-- Whole-rig replacement: when this loads, HubBuilder draws no portal
		-- primitives at all and PortalRig DRIVES these parts instead of
		-- building its own. Absent (no Rojo, missing file), the blockout runs
		-- exactly as before -- there is no flag day either way.
		Prefab = {
			AssetKey = "HUB_FATE_ENGINE",
			-- Studio's FBX importer landed the model at 0.42x. Measured
			-- against the spec on arrival, every part by the same factor:
			-- Platform 101.0 -> 240, Plinth 35.35 -> 84, OuterRing
			-- 48.48 -> 115.2, SpotAnchor y 126.29 -> 300. One number fixes
			-- all of it; re-exporting 78 meshes to fix it is how a pipeline
			-- gets abandoned.
			-- 2.3762 put the ring 115 studs tall -- 23x a player -- and the
			-- owner's verdict on walking it was "way too big". Retuned to
			-- put the PORTAL at ~4.5x player height, which was the ask:
			--
			--   OuterRing   48.48 raw -> 22.5 studs  (4.5x a 5-stud player)
			--   InnerRing   34.34 raw -> 15.9 studs  (the opening, walkable)
			--   Platform   101.0  raw -> 46.9 studs  (the dais)
			--   Crown      126.29 raw -> 58.6 studs  (SpotAnchor height)
			--
			-- Everything else in this file that describes the dais is derived
			-- from this number rather than set beside it, so one edit re-tunes
			-- the Engine and a test catches it if they disagree.
			Scale = 0.464,
		},

		-- PAINT, BY PART NAME. Authored meshes import untextured and grey,
		-- and that is the intended pipeline here: the house style is flat
		-- colour with no textures, so colour is data rather than something
		-- baked into an upload. Changing the Engine's palette is an edit here
		-- and a rejoin.
		--
		-- Longest matching prefix wins, so Plinth_SideBand is gold while
		-- Plinth stays marble.
		--
		-- NEVER give a rarity-tinted part a SurfaceAppearance: it overrides
		-- Color, and Color is how the rarity reskin works.
		PrefabStyles = {
			-- Ceremonial architecture ------------------------------------
			Platform = {
				Color = Theme.Marble,
				Material = Enum.Material.Marble,
				CanCollide = true,
			},
			Platform_RadialPanels = { Color = Color3.fromRGB(88, 82, 104), Material = Enum.Material.Slate },
			Platform_ConcentricInlays = { Color = Theme.MarbleTrim, Material = Enum.Material.Metal },
			Platform_EdgeAccents = { Color = Theme.MarbleTrim, Material = Enum.Material.Metal },
			Plinth = {
				Color = Color3.fromRGB(196, 190, 208),
				Material = Enum.Material.Marble,
				CanCollide = true,
			},
			Plinth_SideBand = { Color = Theme.MarbleTrim, Material = Enum.Material.Metal },
			Plinth_TopFiligree = { Color = Theme.MarbleTrim, Material = Enum.Material.Metal },
			Plinth_CornerButtresses = { Color = Color3.fromRGB(64, 58, 78), Material = Enum.Material.Basalt },
			-- Dimmed from the palette's 124,245,224 by Portal.NeonTint. Neon emits at
			-- full Color and bloom amplifies it; at full value these spokes bled a
			-- halo across the dais.
			Inlay = { Color = Color3.fromRGB(68, 135, 123), Material = Enum.Material.Neon },

			-- Rune ring ---------------------------------------------------
			Rune = { Color = Color3.fromRGB(88, 82, 104), Material = Enum.Material.Slate },
			Rune_GoldFrames = { Color = Theme.MarbleTrim, Material = Enum.Material.Metal },
			-- Rarity-tinted. The colour set here is only the idle look.
			Glyph = { Color = Color3.fromRGB(68, 135, 123), Material = Enum.Material.Neon },

			-- The portal --------------------------------------------------
			OuterRing = {
				Color = Color3.fromRGB(64, 58, 78),
				Material = Enum.Material.Basalt,
				-- Drives the spin. Negative on the inner ring so the two
				-- counter-rotate, which is what makes the portal read as a
				-- mechanism rather than a wheel.
				-- SpinAxis Z because the ring is thin along its own Z, so Z is
				-- the axle. Driven by HubEffects, not PortalRig -- see the
				-- comment on the animator there.
				Attributes = { SpinSpeed = 1.0, SpinAxis = "Z" },
			},
			RingFoot_Clamps = { Color = Theme.MarbleTrim, Material = Enum.Material.Metal },
			InnerRing = {
				Color = Color3.fromRGB(68, 135, 123),
				Material = Enum.Material.Neon,
				Attributes = { SpinSpeed = -1.4, SpinAxis = "Z" },
			},
			PortalPlane = {
				Color = Color3.fromRGB(40, 70, 150), -- Portal_Veil: deep blue
				Material = Enum.Material.ForceField,
				Transparency = 0.45,
				-- The veil breathes. Slower than the rings so the two do not
				-- beat against each other.
				Attributes = { PulseAlphaMin = 0.3, PulseAlphaMax = 0.6, PulseSeconds = 3.2 },
			},

			-- The levitation stack, added by the artist on top of the spec.
			-- Static geometry: it sells the floating portal and nothing in
			-- code needs to move it.
			LevitationGenerator = { Color = Color3.fromRGB(88, 82, 104), Material = Enum.Material.Slate, CanCollide = true },
			GeneratorVents = { Color = Color3.fromRGB(64, 58, 78), Material = Enum.Material.Basalt },
			GeneratorPanelTrim = { Color = Theme.MarbleTrim, Material = Enum.Material.Metal },
			GeneratorEmitter = { Color = Color3.fromRGB(68, 135, 123), Material = Enum.Material.Neon },
			-- The core's second colour. Cyan core over violet coils gives the
			-- energy stack two tones instead of one flat glow, and both are
			-- hub palette rather than invented.
			LevitationCoils = {
				Color = Color3.fromRGB(96, 70, 140),
				Material = Enum.Material.Neon,
				Attributes = { PulseScale = 0.08, PulseSeconds = 3.6 },
			},
			-- Static. The artist's design note is explicit that the
			-- generator, core and coils are decorative unless the game adds
			-- behaviour, and a rotating core would also get caught by the
			-- shard rarity cycle and tinted away from its cyan-violet.
			LevitationCore = {
				Color = Color3.fromRGB(78, 150, 140),
				Material = Enum.Material.Neon,
				-- Breathes in and out, +/-12%, as a regulator under load.
				Attributes = { PulseScale = 0.12, PulseSeconds = 3.6 },
			},

			-- Floating crystals. Rarity-tinted, and each spins in place.
			Shard = {
				Color = Color3.fromRGB(68, 135, 123),
				Material = Enum.Material.Glass,
				Transparency = 0.35,
				-- Spin, plus a slow vertical drift so they read as floating
				-- rather than mounted. Each shard gets a different phase from
				-- its name, so the six never bob in lockstep.
				Attributes = {
					IsFeaturedShard = true,
					SpinSpeed = 0.9,
					BobStuds = 1.6,
					BobSeconds = 5.5,
				},
			},

			-- Invisible: the spotlight's mount point, nothing to look at.
			SpotAnchor = { Transparency = 1 },
		},
	},

	-- Zones. Angle is degrees clockwise from north, kept for validation and
	-- for bridge maths; the authoritative position is GameConfig anchors.
	Districts = {
		{
			Id = "HALL_OF_LEGENDS",
			Name = "Hall of Legends",
			Angle = 0,
			Radius = Layout.ZoneRingRadius,
			Kind = "AMPHITHEATRE",
			PlatformSize = Vector3.new(320, 14, 250),
			Height = 8,
			Color = Theme.Marble,
			Accent = Theme.MarbleTrim,
			Pillars = 0,
			PillarHeight = 0,
			-- Blueprint §2.2: 5 initial obelisk slots, TUNABLE, grows over time.
			ObeliskSlots = 5,
			ObeliskHeight = 56,
			TierCount = 5,
			SpotColor = Color3.fromRGB(226, 236, 255), -- cool white, museum-lit
			MeshId = nil,
		},
		{
			Id = "DISCOVERY_ARCHIVE",
			Name = "Discovery Archive",
			Angle = 90,
			Radius = Layout.ZoneRingRadius,
			Kind = "ROTUNDA",
			PlatformSize = Vector3.new(210, 14, 210),
			Height = 8,
			Color = Color3.fromRGB(27, 75, 74), -- #1B4B4A deep teal
			Accent = Color3.fromRGB(124, 245, 224), -- #7CF5E0 cosmic trim
			Pillars = 8,
			PillarHeight = 95,
			InteriorDiameter = 155,
			DomeSegments = 7,
			ShelfRings = 4,
			ShelvesPerRing = 10,
			MeshId = nil,
		},
		{
			Id = "EXPEDITION_GATE",
			Name = "Expedition Gate",
			Angle = 180,
			Radius = Layout.ZoneRingRadius,
			Kind = "GATE",
			PlatformSize = Vector3.new(290, 14, 240),
			Height = 0,
			Color = Color3.fromRGB(48, 43, 64),
			Accent = Color3.fromRGB(158, 158, 158),
			Pillars = 6, -- torch pillars flanking the processional
			PillarHeight = 110,
			PortalScale = GameConfig.Portal.ExpeditionGateScale,
			MeshId = nil,
		},
		{
			Id = "TRAINING_GROUNDS",
			Name = "Training Grounds",
			Angle = 270,
			Radius = Layout.ZoneRingRadius,
			Kind = "YARD",
			PlatformSize = Vector3.new(235, 14, 235), -- blueprint §2.2: 30x30
			Height = 8,
			Color = Color3.fromRGB(107, 104, 98), -- #6B6862 neutral stone grey
			Accent = Theme.TorchLight,
			Pillars = 0,
			PillarHeight = 0,
			FenceHeight = 14,
			DummyCount = 3,
			HasBossDummy = true,
			TorchCount = 8,
			MeshId = nil,
		},
	},

	-- Decorative depth. Deterministic so every server shows one skyline.
	-- Non-walkable scenery. These extend to GameConfig.HubLayout.VisualExtent,
	-- far beyond the 1200-stud playable footprint: the world reads as several
	-- thousand studs across while every walk stays short.
	FloatingIslands = {
		Count = 40,
		MinRadius = 900,
		MaxRadius = 4000,
		MinHeight = -700,
		MaxHeight = 900,
		MinSize = 90,
		MaxSize = 420,
		Seed = 20260915,
		Color = Color3.fromRGB(42, 37, 58),
		MeshId = nil,
	},

	Bridges = {
		Width = Layout.WalkwayWidth,
		ProcessionalWidth = Layout.ProcessionalWidth,
		Thickness = 8,
		Raise = Layout.WalkwayRaise,
		-- Walkways run a little INTO the surfaces they join at both ends.
		-- Butting them edge to edge leaves a hairline seam that a character
		-- can catch on, and any float error turns it into a hole.
		-- 10 -> 3. A 10-stud bite into a 23-radius dais swallowed most of its
		-- visible edge. Enough to hide the seam, not enough to hide the dais.
		Overlap = 3,
		Color = Theme.Walkway,
		Material = Theme.StoneMaterial,
	},
}

return Crossroads
