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

-- THE WORLD SCALE, from the one place that owns it. The authored meshes and
-- the layout numbers that position things on them must agree, and the test
-- suite checks the agreement from the mesh's own measurements -- so both
-- sides derive from GameConfig.HubLayout.WorldScale rather than carrying two
-- numbers that happen to match today.
local S = Layout.WorldScale

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
	-- The other three of the seven the Crossroads brief named. They were
	-- already in use as literals on the Fate Engine's paint table; the
	-- authored hub needs them by name, so they are hoisted here rather than
	-- typed out a hundred more times.
	Basalt = Color3.fromRGB(64, 58, 78), -- heavy structure, roofs, pillars
	Slate = Color3.fromRGB(88, 82, 104), -- carved detail, shelving, posts
	-- Dimmed from the palette's cosmic 124,245,224 by Portal.NeonTint, for the
	-- same reason the Engine's inlays are: Neon emits at full Color and bloom
	-- amplifies it, so a bright value bleeds a halo across everything near it.
	Inlay = Color3.fromRGB(68, 135, 123),
	Cosmic = Color3.fromRGB(124, 245, 224), -- the undimmed trim, used sparingly
	DeepTeal = Color3.fromRGB(27, 75, 74), -- the Archive's own colour
	Sand = Color3.fromRGB(107, 104, 98), -- the Training yard floor
	MarbleDim = Color3.fromRGB(196, 190, 208), -- marble in shadow: balustrades
	TorchLight = Color3.fromRGB(255, 176, 92),
	EngineSpot = Color3.fromRGB(255, 200, 120), -- blueprint §2.2

	-- NO BUILT-IN ROBLOX MATERIALS ANYWHERE IN THE HUB. Owner-directed
	-- 2026-09-18: their grain fights flat-shaded low-poly geometry, and the
	-- palette is meant to carry the look on its own. SmoothPlastic takes the
	-- colour and nothing else. Neon and ForceField stay, because those are
	-- light rather than surface.
	--
	-- It is also cheaper: Glass in particular is expensive on the phones the
	-- §6 checklist budgets for, and six floating crystals were using it.
	StoneMaterial = Enum.Material.SmoothPlastic,
	PlazaMaterial = Enum.Material.SmoothPlastic,
}

-- === THE AUTHORED CROSSROADS ========================================
--
-- Delivered 2026-09-18 as assets/rbxm/prefabs/HUB_CROSSROADS.rbxmx: 225
-- MeshParts in one flat Model, built from docs/CROSSROADS_BLENDER_PROMPT.md.
-- Wired exactly like the Fate Engine -- a Prefab field and a paint table --
-- because that seam was built to take a second piece without new code.
--
-- MEASURED, NOT ASSUMED. Every number below came out of the delivered file
-- before a line of this was written. The derivations are recorded in
-- assets/rbxm/prefabs/README.md and asserted by test.
--
-- Roblox imports untextured meshes grey, so this table is the entire look of
-- the hub. Longest matching prefix wins, which is why every dressing group
-- also carries a `District_X_` catch-all: without it a part this table forgot
-- would inherit the PLATFORM's entry, and the platform's entry is the one
-- that turns collision ON. A decorative banner you cannot walk through is a
-- worse bug than a grey one.
--
-- WHY SO LITTLE OF THIS COLLIDES, and it is deliberate rather than lazy.
--
-- MEASURED: all 225 delivered parts ship with an EMPTY PhysicsData and no
-- CollisionFidelity, so Roblox generates a hull for each at `Default`
-- fidelity when it loads. Default is coarse, and coarse means it FILLS small
-- openings -- and a great many of these meshes are several separate objects
-- merged into one: eight columns in a ring, four archways, a pair of flanking
-- guardians, a parapet that circles the whole plaza.
--
-- A filled hull on any of those is an invisible wall exactly where players
-- walk. `Walkways_Gateways` would seal all four walkway mouths;
-- `Processional_South_Guardians` would seal the spawn approach;
-- `Plaza_RimParapet` would lay a 5.8-stud slab across the entire floor. That
-- is the same class of bug as the CylinderMesh that gave the hub no floor,
-- and it is invisible in exactly the same way.
--
-- So collision is granted ONLY to things that are a single solid volume and
-- are meant to be one: the floor, the four decks, the walkways, the stairs,
-- the yard, and freestanding props like pillars, rocks and tree trunks.
-- Everything else -- railings, colonnades, arches, walls, stalls, seating --
-- is scenery you can walk through. Walking through a balustrade is a small
-- oddity; being unable to reach the market is not.
--
-- NONE OF THIS IS VERIFIED IN STUDIO. It is the safe half of a choice that
-- cannot be checked headlessly. If a walk shows a railing that should stop
-- you, the fix is one `CollisionFidelity` line on that entry, not a re-export.
local ShellStyles: { [string]: any } = {
	-- The floor ------------------------------------------------------
	-- The only large collidable surface in the hub. Everything else that
	-- collides is a platform, a step or a column.
	Plaza = { Color = Theme.Marble, Material = Theme.StoneMaterial, CanCollide = true },
	-- Covers the whole plaza as a thin proud disc, so it must NOT collide:
	-- 0.6 studs of lip across 1300 studs of floor is a trip hazard with no
	-- visible cause.
	PlazaRim = { Color = Theme.Plaza, Material = Theme.StoneMaterial },
	Plaza_ = { Color = Theme.Slate, Material = Theme.StoneMaterial },
	Plaza_RimParapet = {
		Color = Theme.Basalt,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	Plaza_RimParapetCaps = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	Plaza_RimLampPosts = { Color = Theme.Slate, Material = Theme.StoneMaterial },
	-- === LIGHT SOURCES DO NOT MOVE ===
	-- Owner-directed 2026-09-21, after seeing the market: the glow on these is
	-- right, the drifting is not. A lamp that spins, bobs or wobbles reads as
	-- a floating object rather than as a fixture bolted to a post.
	--
	-- So every lamp, lantern, finial and gateway crystal keeps its PulseAlpha
	-- (colour and brightness animation, which is what makes them feel lit)
	-- and has lost every attribute that changed its position.
	--
	-- The Fate Engine's CrystalShards are deliberately NOT in this group:
	-- they orbit because they are part of a machine, not because they are a
	-- light fitting.
	Plaza_RimLampCrystals = {
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Attributes = {
			PulseAlphaMin = 0.15,
			PulseAlphaMax = 0.5,
			PulseSeconds = 5.2,
		},
	},
	Plaza_Braziers = { Color = Theme.Basalt, Material = Theme.StoneMaterial },
	Plaza_BrazierFlames = {
		Color = Theme.TorchLight,
		Material = Enum.Material.Neon,
		Attributes = { PulseAlphaMin = 0.05, PulseAlphaMax = 0.35, PulseSeconds = 1.9 },
	},
	Plaza_Obelisks = {
		Color = Theme.Slate,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	Plaza_ObeliskCaps = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	-- The ring of light the Engine stands inside. Slow, because it is 780
	-- studs across and a fast pulse on something that large reads as a fault.
	Plaza_InlayRing = {
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Attributes = { PulseAlphaMin = 0.2, PulseAlphaMax = 0.6, PulseSeconds = 6.5 },
	},
	Plaza_GoldNodes = {
		Attributes = { PulseAlphaMin = 0.25, PulseAlphaMax = 0.55, PulseSeconds = 7.5 },
		Color = Theme.MarbleTrim,
		Material = Enum.Material.Neon,
		Transparency = 0.15,
	},
	Plaza_PromenadeRing = { Color = Theme.Walkway, Material = Theme.StoneMaterial },
	Plaza_PromenadeInlay = {
		Attributes = { PulseAlphaMin = 0.15, PulseAlphaMax = 0.45, PulseSeconds = 6.8 },
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Transparency = 0.25,
	},
	Plaza_Shards = {
		Color = Theme.Inlay,
		Material = Theme.StoneMaterial,
		Transparency = 0.35,
		Attributes = { SpinSpeed = 0.18, BobStuds = 2.2, BobSeconds = 7.0 },
	},

	-- The Engine's reserved footprint. A marker, not scenery: the authored
	-- Fate Engine's own Platform lands on top of it and carries the collision.
	EngineReserve = { Transparency = 1, CanCollide = false },

	-- Ceremonial gateways where the walkways leave the centre ---------
	Walkways_ = { Color = Theme.Slate, Material = Theme.StoneMaterial },
	-- WAS Basalt, AND READ AS BLACK. These are the four ceremonial arches over
	-- the walkway mouths, and at 64,58,78 under a pre-dawn key they were
	-- indistinguishable from the night sky behind them -- reported as
	-- "flags and pillars remain uncolored". Pale stone, like the colonnades
	-- they stand beside.
	Walkways_Gateways = {
		Color = Theme.MarbleDim,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	Walkways_GatewayTrim = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	Walkways_GatewayCrystals = {
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Attributes = {
			PulseAlphaMin = 0.18,
			PulseAlphaMax = 0.55,
			PulseSeconds = 4.4,
		},
	},
	Walkways_GoldThresholds = {
		Attributes = { PulseAlphaMin = 0.1, PulseAlphaMax = 0.4, PulseSeconds = 5.4 },
		Color = Theme.MarbleTrim,
		Material = Enum.Material.Neon,
		Transparency = 0.2,
	},
	Walkways_RuneBands = {
		Attributes = { PulseAlphaMin = 0.2, PulseAlphaMax = 0.5, PulseSeconds = 6.2 },
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Transparency = 0.3,
	},
	-- THE FLAGS, ON THEIR THIRD COLOUR. Basalt read as black; gold read as
	-- wrong. Owner-directed: match the crystal-and-pedestal objects the rest
	-- of the hub is dressed with -- so the cloth is the same dimmed teal the
	-- shrine crystals and lamp crystals use, and the poles are pale stone
	-- like the pedestals under them.
	Walkways_Banners = {
		Attributes = { WobbleDegrees = 1.8, WobbleSeconds = 7 },
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Transparency = 0.3,
	},

	-- The spawn approach ---------------------------------------------
	-- The first thing anybody sees, so it gets the guardians and the gold.
	Processional_South = { Color = Theme.Marble, Material = Theme.StoneMaterial, CanCollide = true },
	Processional_South_Guardians = {
		Color = Theme.MarbleDim,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	Processional_South_GuardianCrests = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	Processional_South_Threshold = {
		Attributes = { PulseAlphaMin = 0.1, PulseAlphaMax = 0.45, PulseSeconds = 4.6 },
		Color = Theme.MarbleTrim,
		Material = Enum.Material.Neon,
		Transparency = 0.2,
	},

	-- Scenery ---------------------------------------------------------
	-- The same value the blockout skyline uses (FloatingIslands.Color below),
	-- so swapping between authored and generated scenery does not change the
	-- colour of the horizon.
	FloatingIsland = { Color = Color3.fromRGB(42, 37, 58), Material = Theme.StoneMaterial },
	-- Solid: a broken column you can walk through stops reading as stone.
	Pillar_ = { Color = Theme.Basalt, Material = Theme.StoneMaterial, CanCollide = true },

	-- The ground the plaza sits on, which reaches past its rim and falls
	-- away. Never walked on -- the Plaza is the floor.
	Backdrop_GroundIslets = { Color = Theme.Basalt, Material = Theme.StoneMaterial },
	Backdrop_Rocks = { Color = Theme.Plaza, Material = Theme.StoneMaterial },
	Backdrop_TreeTrunks = { Color = Theme.Basalt, Material = Theme.StoneMaterial },
	Backdrop_TreeCanopies = { Color = Theme.DeepTeal, Material = Theme.StoneMaterial },
	Backdrop_Crystals = {
		Attributes = { PulseAlphaMin = 0.3, PulseAlphaMax = 0.55, PulseSeconds = 11.0 },
		Color = Theme.Inlay,
		Material = Theme.StoneMaterial,
		Transparency = 0.4,
	},

	-- District 1: the Leaderboard (HALL_OF_LEGENDS) -------------------
	-- Marble and gold, museum-lit. Reads as the ceremonial one.
	District_Leaderboard = {
		Color = Theme.Marble,
		Material = Theme.StoneMaterial,
		CanCollide = true,
	},
	District_Leaderboard_ = { Color = Theme.Slate, Material = Theme.StoneMaterial },
	District_Leaderboard_Skirt = {
		Color = Theme.Basalt,
		Material = Theme.StoneMaterial,
		CanCollide = true,
	},
	District_Leaderboard_EdgeBand = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Leaderboard_Balustrade = {
		Color = Theme.MarbleDim,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Leaderboard_BalustradeCaps = {
		Color = Theme.MarbleTrim,
		Material = Theme.StoneMaterial,
	},
	District_Leaderboard_Seating = {
		Color = Theme.Slate,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Leaderboard_SeatLights = {
		Attributes = { PulseAlphaMin = 0.2, PulseAlphaMax = 0.5, PulseSeconds = 5.1 },
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Transparency = 0.35,
	},
	District_Leaderboard_Podiums = {
		Color = Theme.Slate,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Leaderboard_PodiumTops = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Leaderboard_Rails = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Leaderboard_MonumentPlinth = {
		Color = Theme.Slate,
		Material = Theme.StoneMaterial,
		CanCollide = true,
	},
	District_Leaderboard_Monument = {
		Color = Theme.Marble,
		Material = Theme.StoneMaterial,
		CanCollide = true,
	},
	District_Leaderboard_Capital = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Leaderboard_CrownSegments = {
		Color = Theme.MarbleTrim,
		Material = Enum.Material.Neon,
		Transparency = 0.25,
		Attributes = { PulseAlphaMin = 0.2, PulseAlphaMax = 0.55, PulseSeconds = 4.8 },
	},
	District_Leaderboard_NamePanelFrames = {
		Color = Theme.MarbleTrim,
		Material = Theme.StoneMaterial,
	},
	District_Leaderboard_NamePanelInlays = {
		Attributes = { PulseAlphaMin = 0.25, PulseAlphaMax = 0.6, PulseSeconds = 4.4 },
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Transparency = 0.4,
	},
	District_Leaderboard_Runes = {
		Attributes = { PulseAlphaMin = 0.2, PulseAlphaMax = 0.55, PulseSeconds = 3.9 },
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Transparency = 0.3,
	},
	District_Leaderboard_Buttresses = {
		Color = Theme.Basalt,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Leaderboard_FinialPylons = { Color = Theme.Slate, Material = Theme.StoneMaterial },
	District_Leaderboard_CrystalFinials = {
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Attributes = {
			PulseAlphaMin = 0.15,
			PulseAlphaMax = 0.5,
			PulseSeconds = 5.6,
		},
	},
	District_Leaderboard_BannerMasts = { Color = Theme.MarbleDim, Material = Theme.StoneMaterial },
	District_Leaderboard_BannerCloth = {
		Attributes = { WobbleDegrees = 2.0, WobbleSeconds = 6.4 },
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Transparency = 0.3,
	},

	-- District 2: the Discovery Archive -------------------------------
	-- The only district with its own hue. Deep teal and cosmic trim, which
	-- are already DISCOVERY_ARCHIVE's colours in the blockout district table.
	District_Archive = { Color = Theme.Marble, Material = Theme.StoneMaterial, CanCollide = true },
	District_Archive_ = { Color = Theme.Slate, Material = Theme.StoneMaterial },
	District_Archive_Skirt = {
		Color = Theme.Basalt,
		Material = Theme.StoneMaterial,
		CanCollide = true,
	},
	District_Archive_EdgeBand = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Archive_Balustrade = {
		Color = Theme.MarbleDim,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Archive_BalustradeCaps = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Archive_Columns = {
		Color = Theme.Marble,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Archive_ColumnCapitals = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Archive_Dome = { Color = Theme.DeepTeal, Material = Theme.StoneMaterial },
	District_Archive_DomeRibs = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Archive_DomeTrim = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Archive_Oculus = {
		Color = Theme.Cosmic,
		Material = Enum.Material.Neon,
		Transparency = 0.3,
		Attributes = { PulseAlphaMin = 0.2, PulseAlphaMax = 0.6, PulseSeconds = 7.2 },
	},
	District_Archive_Shelves = {
		Color = Theme.Slate,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Archive_ShelfBands = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Archive_ReadingPlinths = {
		Color = Theme.Slate,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Archive_PlinthTrim = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Archive_RuneFloor = {
		Attributes = { PulseAlphaMin = 0.2, PulseAlphaMax = 0.55, PulseSeconds = 6.6 },
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Transparency = 0.35,
	},
	District_Archive_LampBases = { Color = Theme.Slate, Material = Theme.StoneMaterial },
	District_Archive_LampCrystals = {
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Attributes = {
			PulseAlphaMin = 0.15,
			PulseAlphaMax = 0.5,
			PulseSeconds = 4.9,
		},
	},
	District_Archive_Braziers = { Color = Theme.Basalt, Material = Theme.StoneMaterial },
	District_Archive_BrazierFlames = {
		Color = Theme.TorchLight,
		Material = Enum.Material.Neon,
		Attributes = { PulseAlphaMin = 0.05, PulseAlphaMax = 0.35, PulseSeconds = 2.1 },
	},
	-- The books that hang in the air under the dome. The one piece of the
	-- Archive that moves, and the reason the room reads as arcane rather
	-- than as a library.
	District_Archive_FloatingTomes = {
		Color = Theme.Marble,
		Material = Theme.StoneMaterial,
		Attributes = { SpinSpeed = 0.12, BobStuds = 1.4, BobSeconds = 6.4 },
	},
	District_Archive_TomeGlow = {
		Color = Theme.Cosmic,
		Material = Enum.Material.Neon,
		Transparency = 0.45,
		Attributes = { PulseAlphaMin = 0.35, PulseAlphaMax = 0.7, PulseSeconds = 3.8 },
	},
	District_Archive_EntranceThreshold = {
		Color = Theme.MarbleTrim,
		Material = Enum.Material.Neon,
		Transparency = 0.2,
	},

	-- District 3: the Shop --------------------------------------------
	-- NOTE: this is the district the brief renamed. In Content it is still
	-- EXPEDITION_GATE, and the swap is gated on the portal-as-entry spec
	-- amendment -- see STATUS.md. The ART is a market, because that is what
	-- the finished hub wants; the ID catches up when the amendment lands.
	District_Shop = { Color = Theme.Marble, Material = Theme.StoneMaterial, CanCollide = true },
	District_Shop_ = { Color = Theme.Slate, Material = Theme.StoneMaterial },
	District_Shop_Skirt = {
		Color = Theme.Basalt,
		Material = Theme.StoneMaterial,
		CanCollide = true,
	},
	District_Shop_EdgeBand = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Shop_Balustrade = {
		Color = Theme.MarbleDim,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Shop_BalustradeCaps = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Shop_EntrancePylons = {
		Color = Theme.Slate,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Shop_EntranceCrystals = {
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Attributes = { PulseAlphaMin = 0.18, PulseAlphaMax = 0.55, PulseSeconds = 4.2 },
	},
	District_Shop_Columns = {
		Color = Theme.Marble,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Shop_StallStructures = {
		Color = Theme.Slate,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Shop_HippedRoofs = { Color = Theme.Basalt, Material = Theme.StoneMaterial },
	District_Shop_RoofTiles = { Color = Theme.Plaza, Material = Theme.StoneMaterial },
	District_Shop_GoldTrim = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Shop_Counters = {
		Color = Theme.Slate,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Shop_DisplayGoods = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Shop_Crates = {
		Color = Theme.Slate,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Shop_CrateBands = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Shop_Signs = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Shop_LanternBases = { Color = Theme.Slate, Material = Theme.StoneMaterial },
	-- WARM, not cyan. The market is the one place in a cold hub that should
	-- feel lit from inside, and torchlight is already in the palette.
	District_Shop_LanternCrystals = {
		Color = Theme.TorchLight,
		Material = Enum.Material.Neon,
		Attributes = {
			PulseAlphaMin = 0.1,
			PulseAlphaMax = 0.45,
			PulseSeconds = 3.3,
		},
	},
	District_Shop_AisleRunes = {
		Attributes = { PulseAlphaMin = 0.2, PulseAlphaMax = 0.5, PulseSeconds = 4.2 },
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Transparency = 0.35,
	},
	District_Shop_Fountain = {
		Color = Theme.Marble,
		Material = Theme.StoneMaterial,
		CanCollide = true,
	},
	District_Shop_FountainGlow = {
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Transparency = 0.4,
		Attributes = { PulseAlphaMin = 0.3, PulseAlphaMax = 0.65, PulseSeconds = 4.6 },
	},
	District_Shop_RuneRing = {
		Attributes = { PulseAlphaMin = 0.25, PulseAlphaMax = 0.6, PulseSeconds = 5.3 },
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Transparency = 0.3,
	},

	-- District 4: the Training Grounds --------------------------------
	-- Neutral stone and torchlight. Deliberately the least magical of the
	-- four: it is the practical one, and Phase 2 is where it gets a purpose.
	District_Training = { Color = Theme.Marble, Material = Theme.StoneMaterial, CanCollide = true },
	District_Training_ = { Color = Theme.Slate, Material = Theme.StoneMaterial },
	District_Training_Skirt = {
		Color = Theme.Basalt,
		Material = Theme.StoneMaterial,
		CanCollide = true,
	},
	District_Training_EdgeBand = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Training_Wall = {
		Color = Theme.Slate,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Training_WallCaps = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Training_YardFloor = {
		Color = Theme.Sand,
		Material = Theme.StoneMaterial,
		CanCollide = true,
	},
	District_Training_RuneRing = {
		Attributes = { PulseAlphaMin = 0.2, PulseAlphaMax = 0.55, PulseSeconds = 4.8 },
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Transparency = 0.35,
	},
	District_Training_ArenaMarkers = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Training_DummyPosts = {
		Color = Theme.Slate,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Training_DummyHeads = {
		Color = Theme.MarbleDim,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Training_WeaponRacks = {
		Color = Theme.MarbleDim,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Training_Targets = { Color = Theme.Marble, Material = Theme.StoneMaterial },
	District_Training_TargetStands = {
		Color = Theme.Slate,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Training_TargetRings = { Color = Theme.MarbleTrim, Material = Theme.StoneMaterial },
	District_Training_Bleachers = {
		Color = Theme.MarbleDim,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Training_Buttresses = {
		Color = Theme.Slate,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
	},
	District_Training_Gate = { Color = Theme.MarbleDim, Material = Theme.StoneMaterial },
	District_Training_Banners = { Color = Theme.MarbleDim, Material = Theme.StoneMaterial },
	District_Training_BannerCloth = {
		Attributes = { WobbleDegrees = 2.0, WobbleSeconds = 6.4 },
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Transparency = 0.3,
	},
	District_Training_Braziers = { Color = Theme.Slate, Material = Theme.StoneMaterial },
	District_Training_BrazierFlames = {
		Color = Theme.TorchLight,
		Material = Enum.Material.Neon,
		Attributes = { PulseAlphaMin = 0.05, PulseAlphaMax = 0.35, PulseSeconds = 2.3 },
	},
}

-- The three radial walkways are identical in every respect but their compass
-- letter, and so are the four plaza corners and the four district stairs.
-- Written as loops rather than as forty near-identical entries: a copied
-- table is a table that drifts, and the last thing this file needs is three
-- walkways that are subtly different colours.
do
	for _, compass in { "North", "East", "West" } do
		ShellStyles[`Walkway_{compass}`] =
			{ Color = Theme.Marble, Material = Theme.StoneMaterial, CanCollide = true }
		-- Kerbs. Collidable on purpose -- they are the lip that stops a
		-- player walking off a deck raised above the plaza without noticing,
		-- and at 0.36 studs they are far too low to be a wall.
		-- ExtendInwardTo: the kerbs were authored from radius 60 while their
		-- walkway runs from 20, so each path had 40 studs of bare deck and
		-- the edging stopped in mid-air short of the Engine. 20 matches the
		-- walkway exactly, which tucks both under the dais by the same amount.
		ShellStyles[`Walkway_{compass}_Edge`] = {
			Color = Theme.Walkway,
			Material = Theme.StoneMaterial,
			CanCollide = true,
			ExtendInwardTo = 20 * S,
		}
	end
	ShellStyles.Processional_South_Edge = {
		Color = Theme.Walkway,
		Material = Theme.StoneMaterial,
		CanCollide = true,
		ExtendInwardTo = 20 * S,
	}
	ShellStyles.Processional_South_Inlay = {
		Attributes = { PulseAlphaMin = 0.2, PulseAlphaMax = 0.5, PulseSeconds = 5.8 },
		Color = Theme.Inlay,
		Material = Enum.Material.Neon,
		Transparency = 0.3,
	}

	-- Every district is reached by a flight of steps, and all three parts of
	-- one (treads, cheeks, rails) must be solid or the climb fails halfway.
	for _, district in { "Leaderboard", "Archive", "Shop", "Training" } do
		ShellStyles[`District_{district}_Stair`] =
			{ Color = Theme.Walkway, Material = Theme.StoneMaterial, CanCollide = true }
		ShellStyles[`District_{district}_StairRails`] =
			{ Color = Theme.MarbleTrim, Material = Theme.StoneMaterial, CanCollide = true }
	end

	-- The four outcrops on the plaza's diagonals, and the smaller pair inside
	-- the promenade ring.
	for _, corner in { "NE", "NW", "SE", "SW" } do
		ShellStyles[`PlazaInner_{corner}_Rocks`] =
			{ Color = Theme.Basalt, Material = Theme.StoneMaterial, CanCollide = true }
		ShellStyles[`PlazaInner_{corner}_Crystal`] = {
			Color = Theme.Inlay,
			Material = Enum.Material.Neon,
			Attributes = {
				PulseAlphaMin = 0.2,
				PulseAlphaMax = 0.6,
				PulseSeconds = 5.0,
				SpinSpeed = 0.28,
				BobStuds = 0.6,
				BobSeconds = 7.2,
			},
		}

		ShellStyles[`PlazaOuter_{corner}_RockBase`] =
			{ Color = Theme.Basalt, Material = Theme.StoneMaterial, CanCollide = true }
		ShellStyles[`PlazaOuter_{corner}_SharpRocks`] =
			{ Color = Theme.Plaza, Material = Theme.StoneMaterial, CanCollide = true }
		ShellStyles[`PlazaOuter_{corner}_Crystals`] = {
			Color = Theme.Inlay,
			Material = Enum.Material.Neon,
			Attributes = {
				PulseAlphaMin = 0.2,
				PulseAlphaMax = 0.58,
				PulseSeconds = 5.8,
				SpinSpeed = 0.24,
				BobStuds = 0.5,
				BobSeconds = 8.4,
			},
		}
		ShellStyles[`PlazaOuter_{corner}_Shrine`] =
			{ Color = Theme.Slate, Material = Theme.StoneMaterial, CanCollide = true }
		ShellStyles[`PlazaOuter_{corner}_ShrineTrim`] =
			{ Color = Theme.MarbleTrim, Material = Theme.StoneMaterial }
		ShellStyles[`PlazaOuter_{corner}_ShrineCrystal`] = {
			Color = Theme.Cosmic,
			Material = Enum.Material.Neon,
			Attributes = {
				PulseAlphaMin = 0.25,
				PulseAlphaMax = 0.7,
				PulseSeconds = 3.6,
				SpinSpeed = 0.35,
				BobStuds = 0.8,
				BobSeconds = 6.5,
			},
		}
		ShellStyles[`PlazaOuter_{corner}_TreeTrunk`] =
			{ Color = Theme.Basalt, Material = Theme.StoneMaterial, CanCollide = true }
		ShellStyles[`PlazaOuter_{corner}_TreeCanopy`] = {
			Color = Theme.DeepTeal,
			Material = Theme.StoneMaterial,
			-- A degree or two on a long period. Anything more and low-poly
			-- foliage reads as rubber rather than as leaves.
			Attributes = { WobbleDegrees = 1.4, WobbleSeconds = 9 },
		}
	end
end

-- The mountain ring, delivered separately as HUB_BACKDROP.rbxm: four
-- MeshParts, 4096 studs across at Scale, which is what
-- GameConfig.HubLayout.VisualExtent has always claimed the world reaches.
--
-- Flat and dark on purpose. It is a horizon, and a horizon that competes for
-- attention is a mistake -- it stands 4000 studs from the portal the whole
-- hub exists to frame.
local BackdropStyles: { [string]: any } = {
	Backdrop_Foothills = { Color = Color3.fromRGB(46, 41, 62), Material = Theme.StoneMaterial },
	Backdrop_Mountain = { Color = Color3.fromRGB(38, 34, 52), Material = Theme.StoneMaterial },
	-- The caps catch the same low pre-dawn key light the plaza does, which is
	-- the one thing that stops the ring reading as a painted wall.
	Backdrop_MountainCap = { Color = Color3.fromRGB(78, 70, 104), Material = Theme.StoneMaterial },
	Backdrop_Spires = { Color = Color3.fromRGB(52, 46, 70), Material = Theme.StoneMaterial },
}
local Crossroads = {
	Theme = Theme,

	-- THE AUTHORED HUB SHELL. Delivered 2026-09-18, 225 MeshParts.
	--
	-- Whole-shell replacement, exactly like FateEngine.Prefab above: when this
	-- loads, HubBuilder draws no plaza, no district platforms, no walkways and
	-- no skyline. Absent (no Rojo, missing file), the blockout below runs
	-- unchanged. There is no flag day either way.
	--
	-- The Fate Engine is NOT part of this. The brief reserved its footprint
	-- and asked for nothing inside it, so the Engine still loads from its own
	-- prefab, at the origin, on top of `EngineReserve`.
	Shell = {
		Prefab = {
			AssetKey = "HUB_CROSSROADS",

			-- SCALE 2.0, AND IT IS EXACT. Studio's FBX importer halved it.
			-- Measured against docs/CROSSROADS_BLENDER_PROMPT.md on arrival,
			-- on six independent dimensions that all agreed to four figures:
			--
			--   EngineReserve width   23.000 -> 46      (2.000)
			--   Walkway width         22.000 -> 44      (2.000)
			--   Walkway thickness      0.750 -> 1.5     (2.000)
			--   Walkway length       190.000 -> 380     (2.000)
			--   District deck          7.000 -> 14      (2.000)
			--   District ring radius 200.000 -> 400     (2.000)
			--
			-- Six agreeing measurements is what makes ONE number the right
			-- correction. Re-exporting 225 meshes to fix an importer setting
			-- is how a pipeline gets abandoned.
			-- 2.0 * WorldScale. The delivery measured 2.0 against the brief
			-- and that was internally consistent; what was wrong was the
			-- brief's stud assumption, which made the counters 6 studs tall
			-- for a 5-stud player. See docs/ART_DIRECTION.md.
			Scale = 2.0 * S,

			-- THE COMPASS WAS 180 DEGREES OUT, and that is the export's axis
			-- convention rather than anybody's mistake. The brief put north at
			-- Blender +Y; the FBX round trip landed north at Roblox +Z; and
			-- GameConfig.HubLayout.Anchors has always put north at -Z.
			--
			-- Confirmed as a pure ROTATION, not a mirror: all four districts
			-- are exactly negated in both X and Z, and every part in the file
			-- arrived with an identity rotation. A mirrored delivery would
			-- have needed a re-export; this one needs a number.
			YawDegrees = 180,

			-- REGISTERED FROM THE ENGINE'S OWN MARKER, not from the model
			-- pivot. The artist set the pivot correctly -- it landed on the
			-- hub centre at floor level, to four decimal places -- but a
			-- pivot is invisible metadata and the next delivery's might not.
			-- `EngineReserve` is a named part in the contract, it is visible
			-- in the file, and it is the one object in the scene whose whole
			-- purpose is to mark this point.
			--
			-- Its centre sits half its own height above the plaza deck
			-- (23.000 x 1.000 x 23.000, bottom flush with the floor), so the
			-- registration point is half a source unit below its centre.
			AnchorPart = "EngineReserve",
			AnchorOffset = Vector3.new(0, -0.5 * S, 0),
		},
		Styles = ShellStyles,

		-- The top face of an authored district platform, in studs above the
		-- plaza. The brief asked for 14 and the delivery measured 13.99, so
		-- this is the DELIVERED number rounded, not the requested one.
		--
		-- It is here because behaviour has to sit on top of art: the ENTER
		-- prompt and the district labels are placed from it, and the blockout
		-- district heights no longer describe the floor anyone stands on.
		DeckHeight = 14 * S,

		-- Where a district's name floats, above its deck.
		SignLift = 46,

		-- NO EXPEDITION GATE. Owner-directed after the first authored walk: the
		-- "Verdant Valley / ENTER" prompt standing in the middle of the market
		-- is not where a biome is entered, and the Fate Engine's portal takes
		-- that job. So the authored hub builds no gate anchor and no gate
		-- prompt at all.
		--
		-- WHAT THIS COSTS, STATED PLAINLY: until the Engine carries entry,
		-- there is no in-world way into an expedition. ExpeditionSystem
		-- already handles a missing anchor -- it warns that entry is
		-- remote-only and keeps running -- so /enter still works for testing
		-- and nothing else breaks. This is a deliberate gap, not an
		-- oversight, and it closes with the portal-as-entry amendment.
	},

	-- THE HORIZON, BUILT RATHER THAN PLACED.
	--
	-- The delivered `HUB_BACKDROP` is one ring-shaped model, and placing it
	-- whole failed three times: at Scale 2.0 it read as far too large, at 1.0
	-- it clipped through the plaza, and at 3.0 it was still clipping. The
	-- reason is that the distance from the hub to its nearest peak is a
	-- property of the MESH, which lives in a Roblox asset we cannot measure --
	-- so every scale was a guess, and scaling moves size and distance
	-- together anyway.
	--
	-- Owner-directed after the third attempt: take ONE chunk of mountain,
	-- stand it a set distance beyond the crossroads, and clone it round a
	-- circle. Distance stops being emergent and becomes a number we choose.
	--
	-- It is decoration with no contract: nothing looks it up, nothing drives
	-- it, and a place without the file simply has no mountains.
	Backdrop = {
		-- The model is now only the SOURCE of a mesh. It is never placed
		-- whole, so it has no Scale, yaw or anchor of its own.
		AssetKey = "HUB_BACKDROP",
		Styles = BackdropStyles,

		Ring = {
			-- Which mesh gets cloned. One name, so trying a different massif
			-- is a one-line edit. The others in the file are
			-- Backdrop_Foothills, Backdrop_MountainCap and Backdrop_Spires.
			Part = "Backdrop_Mountain",

			-- Studs from the hub centre to each chunk's CENTRE. Every number
			-- here is chosen against measured hub geometry rather than eyed:
			--
			--   plaza edge          653
			--   hub ground skirt   1097
			--   chunk half-width   1024  (Backdrop_Mountain, at Scale 1.0)
			--
			-- so the band spans 1376 .. 3424 studs. Its NEAR FACE lands 723
			-- studs beyond the plaza edge -- inside the 500-1000 the owner
			-- asked for -- and its far face stays inside FogEnd (4400) so the
			-- range fades rather than ending in a hard line.
			Radius = 2400 * S,

			-- 14 chunks of 2048 across a 15080-stud circumference is ~1.9x
			-- coverage. They are MEANT to overlap: a single chunk is itself a
			-- ragged mass, and overlapping rotated copies is what turns a
			-- repeated mesh into a continuous range instead of a ring of
			-- identical lumps.
			Count = 14,
			-- Scales with the world: a full-size massif standing in a
			-- half-size ring would march across the plaza.
			Scale = 1.0 * S,

			-- The hub's own ground plane, which every chunk stands on. Equal
			-- to -(34.7237511 + Shell.Prefab.AnchorOffset.Y) * Shell scale --
			-- the shell's source Y 0 in world studs. A test asserts the two
			-- agree, because a horizon floating above its own ground is the
			-- first thing anyone would notice.
			BaseY = -68.4475 * S,

			-- Deterministic, like FloatingIslands: one skyline per server,
			-- never a different one per boot. Jitter is what stops 14 copies
			-- of one mesh reading as 14 copies of one mesh.
			Seed = 20260918,
			YawJitterDegrees = 30,
			ScaleJitter = 0.25,
		},
	},

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
		PlatformRadius = 23 * S,
		-- 10 -> 2, to match the authored dais (4.21 raw at Prefab.Scale). The
		-- blockout stands in for the real thing, so a player stepping onto it
		-- has to step the same distance in either build.
		PlatformRaise = 2,
		PlatformColor = Theme.Marble,
		PlatformMaterial = Enum.Material.SmoothPlastic,
		RuneInlayCount = 16, -- radial groove pattern
		RuneInlayColor = Color3.fromRGB(124, 245, 224),

		PortalScale = GameConfig.Portal.FateEngineScale,
		-- The Engine cycles a "featured" rarity cosmetically; it is NOT the
		-- roll result and must never be read as a prediction.
		IdleRarity = "UNKNOWN",
		FeaturedCycleSeconds = 14,

		CrystalShards = {
			Count = 6,
			-- Every one of these is a distance around the Engine, so they
			-- scale with it. Left alone they were shards the size of the
			-- machine they orbit.
			OrbitRadius = 100 * S,
			MinHeight = 50 * S,
			MaxHeight = 140 * S,
			Size = 20 * S,
			Material = Enum.Material.SmoothPlastic,
			SpinSpeedMin = 0.2,
			SpinSpeedMax = 0.7,
		},

		SpotLight = {
			Color = Theme.EngineSpot,
			-- 8 -> 3 -> 1.1, across two walks. Range and Height are distances
			-- and scale with the world, but BRIGHTNESS does not work that
			-- way: the same light hung half as high over a half-size dais is
			-- four times the illuminance by inverse square, so halving the
			-- world QUADRUPLED this. 3 was still a white pool over the plaza.
			--
			-- There is no ratio to derive this from -- it is a look, and the
			-- only instrument is a walk. If it is still too hot, this is the
			-- number, and the Angle below is the other one.
			Brightness = 1.1,
			Range = 400 * S,
			-- 80 -> 50. A wide cone washes the whole plaza; a narrow one pools
			-- on the dais, which is the thing the light is for.
			Angle = 50,
			Height = 300 * S,
		},

		-- The roll pad, and it has to FIT the dais. At 90 it was wider than
		-- the whole re-tuned Engine, so the prompt would have floated out
		-- over open plaza.
		AnchorSize = Vector3.new(30 * S, 1, 30 * S),
		AnchorHeight = 6 * S,
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
			Scale = 0.464 * S,

			-- WALK ON, DO NOT STEP UP -- AND FROM ANY DIRECTION.
			--
			-- Measured from the delivered Engine: Platform's top face sits
			-- 1.934 studs above the model pivot at this Scale, and the
			-- concentric inlays sit ON that face at 1.933, which is how we
			-- know it is the walkable deck rather than a rim.
			--
			-- The first attempt lowered it to WalkwayRaise, flush with the
			-- four paths. That still left a step for anyone crossing the open
			-- plaza, which is most of the approach angles, and the second
			-- walk said so. It now sits on the PLAZA -- dais top at Y 0 --
			-- so it can be walked onto from anywhere.
			--
			-- The walkways still run 1.5 studs above it and overlap its rim
			-- by 3.4, so arriving along a path is a step DOWN onto the dais.
			-- That is free in Roblox; stepping UP is the thing that catches.
			Offset = Vector3.new(0, -1.934 * S, 0),
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
				Material = Enum.Material.SmoothPlastic,
				CanCollide = true,
			},
			Platform_RadialPanels = { Color = Color3.fromRGB(88, 82, 104), Material = Enum.Material.SmoothPlastic },
			Platform_ConcentricInlays = { Color = Theme.MarbleTrim, Material = Enum.Material.SmoothPlastic },
			Platform_EdgeAccents = { Color = Theme.MarbleTrim, Material = Enum.Material.SmoothPlastic },
			Plinth = {
				Color = Color3.fromRGB(196, 190, 208),
				Material = Enum.Material.SmoothPlastic,
				CanCollide = true,
			},
			Plinth_SideBand = { Color = Theme.MarbleTrim, Material = Enum.Material.SmoothPlastic },
			Plinth_TopFiligree = { Color = Theme.MarbleTrim, Material = Enum.Material.SmoothPlastic },
			Plinth_CornerButtresses = { Color = Color3.fromRGB(64, 58, 78), Material = Enum.Material.SmoothPlastic },
			-- Dimmed from the palette's 124,245,224 by Portal.NeonTint. Neon emits at
			-- full Color and bloom amplifies it; at full value these spokes bled a
			-- halo across the dais.
			Inlay = {
				Color = Color3.fromRGB(68, 135, 123),
				Material = Enum.Material.Neon,
				-- The same ripple, one ring further out. Sixteen spokes on a
				-- slower period than the glyphs, so the dais breathes under
				-- the plinth rather than with it.
				WaveCount = 16,
				Attributes = { PulseAlphaMin = 0.1, PulseAlphaMax = 0.6, PulseSeconds = 3.4 },
			},

			-- Rune ring ---------------------------------------------------
			Rune = { Color = Color3.fromRGB(88, 82, 104), Material = Enum.Material.SmoothPlastic },
			Rune_GoldFrames = { Color = Theme.MarbleTrim, Material = Enum.Material.SmoothPlastic },
			-- Rarity-tinted. The colour set here is only the idle look.
			-- Eight glyphs lighting one after another around the plinth. A
			-- travelling ripple reads as the machine thinking; eight random
			-- phases would just read as flicker.
			Glyph = {
				Color = Color3.fromRGB(68, 135, 123),
				Material = Enum.Material.Neon,
				WaveCount = 8,
				Attributes = { PulseAlphaMin = 0.05, PulseAlphaMax = 0.55, PulseSeconds = 2.6 },
			},

			-- The portal --------------------------------------------------
			-- POLISHED, NOT RUSTIC. Basalt's heavy grain read as corroded
			-- bronze against pale marble and cool energy -- a third material
			-- language in a palette that only has two. Slate keeps the mass
			-- and the dark value without the rust, so the frame reads as
			-- machined stone. One line to put back if the weathered look is
			-- wanted after all.
			OuterRing = {
				-- Turns with the portal assembly. See GameConfig.Portal.YawIdleSpeed.
				YawFollow = true,
				Color = Color3.fromRGB(58, 53, 72),
				Material = Enum.Material.SmoothPlastic,
				-- Drives the spin. Negative on the inner ring so the two
				-- counter-rotate, which is what makes the portal read as a
				-- mechanism rather than a wheel.
				-- SpinAxis Z because the ring is thin along its own Z, so Z is
				-- the axle. Driven by HubEffects, not PortalRig -- see the
				-- comment on the animator there.
				-- Wobble and jitter are what stop a constant spin on a fixed
				-- axis reading as machinery. A degree and a half of sway on
				-- two uneven periods, and a rate that breathes +/-25%.
				Attributes = {
					-- 0.32 -> 0.22. Still reading as "rigid" rather than
					-- drifting; a 28-second revolution with a rate that
					-- breathes +/-32% over a long wobble is a ring that is
					-- floating, not one that is driven.
					SpinSpeed = 0.22,
					SpinAxis = "Z",
					SpinJitter = 0.32,
					-- THE RINGS SHARE ONE SWAY. Giving them different wobble
					-- periods made them tilt independently, and with ~1 stud
					-- of clearance the inner assembly swung straight out
					-- through the outer aperture. Identical degrees and
					-- period means the whole rig leans as one object -- still
					-- alive, never diverging. Only the SPIN differs.
					WobbleDegrees = 1.6,
					WobbleSeconds = 8,
					-- NO PulseScale here. Swelling the outer ring shrinks the
					-- hole the inner ring sits in, which is the one thing
					-- guaranteed to clip. Its emphasis comes from the spin,
					-- the jitter and the gold clamps instead.
				},
			},
			RingFoot_Clamps = {
				-- Turns with the portal assembly. See GameConfig.Portal.YawIdleSpeed.
				YawFollow = true,
				Color = Theme.MarbleTrim,
				Material = Enum.Material.Neon,
				-- Four gold catches around the frame, breathing against the
				-- ring's swell rather than with it, so the eye has something
				-- warm to land on in a cool palette.
				WaveCount = 4,
				Attributes = { PulseAlphaMin = 0.25, PulseAlphaMax = 0.72, PulseSeconds = 4.1 },
			},
			-- MATTE, deliberately. With the ring and the veil both emissive in
			-- the same hue they merged into one bright disc and the teeth
			-- stopped reading. Metal takes the rarity colour but catches light
			-- instead of emitting it, so the frame is machined and the
			-- aperture inside it glows -- which is the way round it should be.
			InnerRing = {
				-- Turns with the portal assembly. See GameConfig.Portal.YawIdleSpeed.
				YawFollow = true,
				Color = Color3.fromRGB(68, 135, 123),
				Material = Enum.Material.SmoothPlastic,
				-- The delivered inner ring is 15.92 studs across inside an
				-- 18.0 aperture -- about a stud a side, which anything that
				-- moves can eat. At 0.88 it sits ~2 studs clear, so the
				-- assembly reads as nested rather than jammed.
				SizeScale = 0.88,
				Attributes = {
					SpinSpeed = -0.31,
					SpinAxis = "Z",
					SpinJitter = 0.38,
					-- Matched to the outer ring on purpose. See the note there.
					WobbleDegrees = 1.6,
					WobbleSeconds = 8,
				},
			},
			-- THE VEIL. This is the surface a player walks through, so it is
			-- the one piece that has to read as the point of the whole
			-- machine. At deep blue and 0.45 transparent it was nearly
			-- invisible against the dark hub -- reported from the third
			-- authored playtest as "you can't even see it hardly".
			--
			-- Brighter, more opaque, rarity-tinted, and given its own slow
			-- breath so it is the only part of the Engine that changes SIZE.
			-- Explicitly non-colliding: you walk through a portal.
			PortalPlane = {
				-- Turns with the portal assembly. See GameConfig.Portal.YawIdleSpeed.
				YawFollow = true,
				Color = Color3.fromRGB(96, 170, 235),
				-- Neon, not ForceField. ForceField's shimmer is too subtle to
				-- read against a dark hub -- the aperture looked like a hole
				-- rather than the thing you step into, across two playtests.
				-- Neon glows; the transparency pulse keeps the bloom in check
				-- and lets the ring's teeth stay readable through it.
				Material = Enum.Material.Neon,
				Transparency = 0.45,
				CanCollide = false,
				-- Set INTO the ring, not flush with it. The mesh arrived
				-- 15.22 studs across inside a 15.92 ring -- 0.35 a side -- so
				-- anything that moved it clipped. At 0.9 it sits ~1.1 studs
				-- clear all round, which reads as an aperture in a frame
				-- rather than a disc jammed in a hole.
				SizeScale = 0.82,
				Attributes = {
					-- TWO RINGS, NOT THREE. Owner-directed 2026-09-21: the
					-- inner ring so nearly encases the portal that the two
					-- read as one object, so they are treated as one --
					-- ring 1 is the outer frame, ring 2 is the inner ring and
					-- the aperture it holds, turning together against it.
					--
					-- EXACTLY InnerRing's speed, not merely a similar one. A
					-- near-match is worse than either extreme: two nested
					-- discs at -0.31 and -0.14 slowly slide against each
					-- other, which reads as one of them slipping rather than
					-- as a mechanism. Identical is what makes them one ring.
					SpinSpeed = -0.31,
					-- AND ABOUT THE SAME AXIS. This is what was still wrong
					-- after the speeds matched: SpinAxis defaults to "Y", so
					-- the aperture was turning about the VERTICAL while the
					-- rings turned about their own Z. Same number, different
					-- axle -- which looks exactly like "still not connected".
					SpinAxis = "Z",
					-- NO PulseScale. The veil is 15.22 studs across inside a
					-- 15.92 ring: 0.35 studs of clearance a side. A 6% breath
					-- grew it to 16.13 and it pulsed straight through its own
					-- frame. The breath is carried entirely by transparency,
					-- which cannot clip.
					PulseAlphaMin = 0.35,
					PulseAlphaMax = 0.62,
					PulseSeconds = 2.8,
				},
			},

			-- The levitation stack, added by the artist on top of the spec.
			-- Static geometry: it sells the floating portal and nothing in
			-- code needs to move it.
			LevitationGenerator = { Color = Color3.fromRGB(88, 82, 104), Material = Enum.Material.SmoothPlastic, CanCollide = true },
			GeneratorVents = { Color = Color3.fromRGB(64, 58, 78), Material = Enum.Material.SmoothPlastic },
			GeneratorPanelTrim = { Color = Theme.MarbleTrim, Material = Enum.Material.SmoothPlastic },
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
			-- The core is a SINGLE mesh, so it cannot be painted two tones --
			-- but it can be both in turn. It drifts cyan to violet over six
			-- seconds while breathing on a different period, so the two never
			-- line up and it never looks like a loop.
			LevitationCore = {
				-- Turns with the portal assembly. See GameConfig.Portal.YawIdleSpeed.
				YawFollow = true,
				Color = Color3.fromRGB(78, 150, 140),
				Material = Enum.Material.Neon,
				Attributes = {
					PulseScale = 0.12,
					PulseSeconds = 3.6,
					ColorA = Color3.fromRGB(78, 150, 140),
					ColorB = Color3.fromRGB(112, 78, 164),
					ColorSeconds = 6,
				},
			},

			-- Floating crystals. Rarity-tinted, and each spins in place.
			Shard = {
				Color = Color3.fromRGB(68, 135, 123),
				Material = Enum.Material.SmoothPlastic,
				Transparency = 0.35,
				-- Spin, plus a slow vertical drift so they read as floating
				-- rather than mounted. Each shard gets a different phase from
				-- its name, so the six never bob in lockstep.
				Attributes = {
					IsFeaturedShard = true,
					SpinSpeed = 0.5,
					BobStuds = 1.6,
					BobSeconds = 5.5,
					WobbleDegrees = 4,
					WobbleSeconds = 6,
				},
				-- Six crystals sharing one entry animated in lockstep, which
				-- read as machinery rather than as things adrift. Each now
				-- gets its own speed, drift and period from its name.
				-- Now that the hash actually separates Shard1..Shard6, these
				-- spreads do what they always claimed to. Wobble is varied
				-- too, so no two crystals tumble the same way.
				Vary = {
					SpinSpeed = 0.55,
					BobStuds = 0.45,
					BobSeconds = 0.4,
					WobbleDegrees = 0.5,
					WobbleSeconds = 0.4,
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
			PlatformSize = Vector3.new(320 * S, 14 * S, 250 * S),
			Height = 8 * S,
			Color = Theme.Marble,
			Accent = Theme.MarbleTrim,
			Pillars = 0,
			PillarHeight = 0,
			-- Blueprint §2.2: 5 initial obelisk slots, TUNABLE, grows over time.
			ObeliskSlots = 5,
			ObeliskHeight = 56 * S,
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
			PlatformSize = Vector3.new(210 * S, 14 * S, 210 * S),
			Height = 8 * S,
			Color = Color3.fromRGB(27, 75, 74), -- #1B4B4A deep teal
			Accent = Color3.fromRGB(124, 245, 224), -- #7CF5E0 cosmic trim
			Pillars = 8,
			PillarHeight = 95 * S,
			InteriorDiameter = 155 * S,
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
			PlatformSize = Vector3.new(290 * S, 14 * S, 240 * S),
			Height = 0,
			Color = Color3.fromRGB(48, 43, 64),
			Accent = Color3.fromRGB(158, 158, 158),
			Pillars = 6, -- torch pillars flanking the processional
			PillarHeight = 110 * S,
			PortalScale = GameConfig.Portal.ExpeditionGateScale,
			MeshId = nil,
		},
		{
			Id = "TRAINING_GROUNDS",
			Name = "Training Grounds",
			Angle = 270,
			Radius = Layout.ZoneRingRadius,
			Kind = "YARD",
			PlatformSize = Vector3.new(235 * S, 14 * S, 235 * S), -- blueprint §2.2: 30x30
			Height = 8 * S,
			Color = Color3.fromRGB(107, 104, 98), -- #6B6862 neutral stone grey
			Accent = Theme.TorchLight,
			Pillars = 0,
			PillarHeight = 0,
			FenceHeight = 14 * S,
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
		MinRadius = 900 * S,
		MaxRadius = 4000 * S,
		MinHeight = -700 * S,
		MaxHeight = 900 * S,
		MinSize = 90 * S,
		MaxSize = 420 * S,
		Seed = 20260915,
		Color = Color3.fromRGB(42, 37, 58),
		MeshId = nil,
	},

	Bridges = {
		Width = Layout.WalkwayWidth,
		ProcessionalWidth = Layout.ProcessionalWidth,
		Thickness = 8 * S,
		Raise = Layout.WalkwayRaise,
		-- Walkways run a little INTO the surfaces they join at both ends.
		-- Butting them edge to edge leaves a hairline seam that a character
		-- can catch on, and any float error turns it into a hole.
		-- 10 -> 3. A 10-stud bite into a 23-radius dais swallowed most of its
		-- visible edge. Enough to hide the seam, not enough to hide the dais.
		Overlap = 3 * S,
		Color = Theme.Walkway,
		Material = Theme.StoneMaterial,
	},
}

return Crossroads
