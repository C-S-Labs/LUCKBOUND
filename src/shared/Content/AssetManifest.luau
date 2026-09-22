--!strict
-- Logical asset name → Roblox asset id. Addendum §A1.
--
-- WHY THIS FILE EXISTS
-- Roblox cannot load .blend/.fbx/.obj at runtime. Every mesh must be uploaded
-- to Roblox's servers first and referenced by rbxassetid://. So the repo holds
-- the SOURCE (assets/source/*.blend) and this MANIFEST; Roblox's CDN holds the
-- geometry. Nothing in the game ever names a raw asset id directly -- code and
-- content name a logical key here, so re-uploading a mesh is a one-line change
-- in this file rather than a hunt through the codebase.
--
-- ADDING AN ASSET
--   1. Author it in Blender, save under assets/source/...
--   2. Export FBX to assets/export/... (same relative path)
--   3. Upload via Studio's 3D Importer or the Open Cloud Assets API
--   4. Add an entry here with the returned id and Status = "UPLOADED"
--
-- Status = "PLACEHOLDER" means the entry is reserved but not yet uploaded.
-- Placeholders are legal and validate fine -- the loader falls back to
-- primitive geometry for them, exactly like the MeshId seam in the hub. This
-- lets chunk layouts be designed and tested before any art exists.

local AssetManifest = {}

export type AssetEntry = {
	AssetId: string, -- "rbxassetid://123..." or "" while PLACEHOLDER
	Status: "PLACEHOLDER" | "UPLOADED",
	Source: string, -- repo path of the .blend, for traceability
	Notes: string?,
}

-- Keyed by logical name. UPPER_SNAKE, matching every other content Id.
local ENTRIES: { [string]: AssetEntry } = {
	-- === Verdant Valley chunk kit ================================
	-- Placeholder entries so the chunk library below is complete and
	-- testable before a single mesh exists.
	-- === Verdant Valley chunk kit ================================
	-- DELIVERED AND UPLOADED 2026-09-22. The modeller returned .rbxmx models,
	-- each one Model wrapping a single MeshPart that already carries a real
	-- rbxassetid -- so the meshes were uploaded on their side and these ids
	-- are all the integration needs. ChunkLoader calls CreateMeshPartAsync on
	-- them directly; the .rbxmx files are kept in assets/rbxm/chunks/ as
	-- provenance and a re-import path, NOT as the load route.
	--
	-- Every piece measures 256 x 256. Heights differ per piece and are
	-- recorded as SizeY in Content/Chunks/VerdantValley.luau.
	--
	-- VV_CHUNK_GROVE IS MISSING from this delivery -- 11 pieces, not 12. It
	-- was the only WIDE provider, so its absence would have made the kit
	-- unassemblable; WIDE now sits on Ruins, Waterfall and Ridge Overlook
	-- instead, which is the variety fix that was owed anyway.
	VV_CHUNK_ENTRY = {
		AssetId = "rbxassetid://109348763234820",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/entry.rbxmx",
		Notes = "Arrival. One opening, south. 60.4 studs tall.",
	},
	VV_CHUNK_PATH_STRAIGHT = {
		AssetId = "rbxassetid://120564645668062",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/path_straight.rbxmx",
		Notes = "Connective forest path, north-south.",
	},
	VV_CHUNK_MEADOW_A = {
		AssetId = "rbxassetid://129906508861393",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/meadow_a.rbxmx",
		Notes = "Open ground, north-south. Long sightlines.",
	},
	VV_CHUNK_MEADOW_B = {
		AssetId = "rbxassetid://126497104831594",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/meadow_b.rbxmx",
		Notes = "Open ground, east-west.",
	},
	VV_CHUNK_STREAM_CROSSING = {
		AssetId = "rbxassetid://100033248306049",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/stream_crossing.rbxmx",
		Notes = "Water and a crossing, north-south.",
	},
	VV_CHUNK_FERN_HOLLOW = {
		AssetId = "rbxassetid://70675226143466",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/fern_hollow.rbxmx",
		Notes = "Sunken and overgrown. East + north. 6-stud skirt, not 4.",
	},
	VV_CHUNK_MUSHROOM_GLEN = {
		AssetId = "rbxassetid://137378616554385",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/mushroom_glen.rbxmx",
		Notes = "Bright and strange. A bend, west + south.",
	},
	VV_CHUNK_RUINS = {
		AssetId = "rbxassetid://94180951428623",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ruins.rbxmx",
		Notes = "Something was here before you. West + north(WIDE).",
	},
	VV_CHUNK_WATERFALL = {
		AssetId = "rbxassetid://134351347864323",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/waterfall.rbxmx",
		Notes = "Landmark. East(WIDE) + south.",
	},
	VV_CHUNK_RIDGE_OVERLOOK = {
		AssetId = "rbxassetid://89335064445927",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ridge_overlook.rbxmx",
		Notes = "High ground and a view. West + east(WIDE).",
	},
	VV_CHUNK_BOSS_CLEARING = {
		AssetId = "rbxassetid://94890260474505",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/boss_clearing.rbxmx",
		Notes = "The arena. One opening, south, WIDE only.",
	},

	-- === Sky Citadel chunk kit ===================================
	-- DELIVERED AND UPLOADED 2026-09-23. 22 pieces, each a .rbxmx holding one
	-- Model around one MeshPart that already carries a real rbxassetid -- the
	-- same shape Verdant Valley arrived in, so these ids are the whole
	-- integration and there is no upload step on our side. The .rbxmx files
	-- live in assets/rbxm/chunks/sky_citadel/ as provenance and a re-import
	-- path, NOT as the load route: ChunkLoader calls CreateMeshPartAsync on
	-- the id.
	--
	-- Generated by assets/source/worlds/sky_citadel/build_sky_citadel_kit.py.
	-- EVERY PIECE MEASURES EXACTLY 256 x 256 x 256 -- read off the delivered
	-- MeshPart Size, not assumed -- with the walk plane 32 studs below the
	-- box centre. The delivered PivotOffset of Y = -32 on all 22 confirms it
	-- independently, which is what GroundOffsetY = 96 encodes.
	--
	-- Untextured: TextureID is null on every piece and the look is the mesh's
	-- own vertex colour plus Color3. docs/biomes/SKY_CITADEL.md.
	SC_CHUNK_ENTRY = {
		AssetId = "rbxassetid://102401700089040",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_entry.rbxmx",
		Notes = "Octagonal arrival plaza under the Beacon.",
	},
	SC_CHUNK_PATH_STRAIGHT = {
		AssetId = "rbxassetid://71690059615130",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_path_straight.rbxmx",
		Notes = "The gatehouse pier: a skyway under an arch between two turrets.",
	},
	SC_CHUNK_PATH_SKYPORT = {
		AssetId = "rbxassetid://112923431493429",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_path_skyport.rbxmx",
		Notes = "A plank pier with a dock islet off it: hazard pad, crane, a moored skiff.",
	},
	SC_CHUNK_PATH_HOOPS = {
		AssetId = "rbxassetid://119074308293684",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_path_hoops.rbxmx",
		Notes = "A bare glass-floored span through three floating rings, between two satellites.",
	},
	SC_CHUNK_PATH_SHATTERED = {
		AssetId = "rbxassetid://129859552462672",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_path_shattered.rbxmx",
		Notes = "The span is broken: eight floating plates, a stride apart, and the Sundered Spire whose crown hangs over its stump.",
	},
	SC_CHUNK_PATH_AVIARY = {
		AssetId = "rbxassetid://105695988662713",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_path_aviary.rbxmx",
		Notes = "The path runs through a gilded birdcage dome, birds in and around it.",
	},
	SC_CHUNK_CROSSROADS = {
		AssetId = "rbxassetid://77637559845243",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_crossroads.rbxmx",
		Notes = "THE INTERSECTION.",
	},
	SC_CHUNK_PATH_BEND = {
		AssetId = "rbxassetid://133368936241819",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_path_bend.rbxmx",
		Notes = "Turns right round the Spired Keep.",
	},
	SC_CHUNK_PATH_BEND_WEST = {
		AssetId = "rbxassetid://73698519651660",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_path_bend_west.rbxmx",
		Notes = "Turns left on a dark engine-deck, the lighthouse on its own islet.",
	},
	SC_CHUNK_VAULT_TURN = {
		AssetId = "rbxassetid://89567819132048",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_vault_turn.rbxmx",
		Notes = "The treasury, passed THROUGH on a right turn.",
	},
	SC_CHUNK_AETHER_SPRINGS = {
		AssetId = "rbxassetid://94743639922681",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_aether_springs.rbxmx",
		Notes = "Terraced pools and the Cascade Tower, water falling off the east rim; turns left.",
	},
	SC_CHUNK_GARDEN_TERRACE = {
		AssetId = "rbxassetid://78944402967747",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_garden_terrace.rbxmx",
		Notes = "The hanging gardens: three islets, the Sky Tree, a pool, a gazebo.",
	},
	SC_CHUNK_OBSERVATORY = {
		AssetId = "rbxassetid://82885736517401",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_observatory.rbxmx",
		Notes = "A night-dark deck of stars: dome and mast, an orrery, dishes on a raised deck.",
	},
	SC_CHUNK_ARMORY = {
		AssetId = "rbxassetid://76151384662039",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_armory.rbxmx",
		Notes = "A slate training yard and a barracks islet, under the banner mast.",
	},
	SC_CHUNK_ARCHIVE = {
		AssetId = "rbxassetid://122698470750875",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_archive.rbxmx",
		Notes = "A roofed hall of shelves and ribbed vaults, floating tomes, the clock tower.",
	},
	SC_CHUNK_SPIRE_COURT = {
		AssetId = "rbxassetid://95480891312919",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_spire_court.rbxmx",
		Notes = "Gate-court: the Sky Fountain and the Ascent Gate.",
	},
	SC_CHUNK_SPIRE_COURT_B = {
		AssetId = "rbxassetid://124418098058619",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_spire_court_b.rbxmx",
		Notes = "Gate-court, rare: the Hall of Winds and its Moon Gate.",
	},
	SC_CHUNK_SIDE_LOOKOUT = {
		AssetId = "rbxassetid://104009041715767",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_side_lookout.rbxmx",
		Notes = "The world's SIDE pocket: a lookout and a loot cache, hung off a spare socket (a crossroads branch, typically) when IncludeSide is on.",
	},
	SC_CHUNK_BOSS_CLEARING = {
		AssetId = "rbxassetid://112186543847771",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_boss_clearing.rbxmx",
		Notes = "The Crown Spire arena.",
	},

	-- The three CAPs (build spec §7.4). A cap seals a socket the layout left
	-- open, so unlike every other piece it is placed MANY times in one
	-- layout -- hence no MaxPerLayout on any of them.
	SC_CHUNK_CAP_OVERLOOK = {
		AssetId = "rbxassetid://71950983482489",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_cap_overlook.rbxmx",
		Notes = "Cap: a railed overlook. The skyway arrives somewhere worth standing.",
	},
	SC_CHUNK_CAP_CRUMBLING = {
		AssetId = "rbxassetid://88594616695898",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_cap_crumbling.rbxmx",
		Notes = "Cap: the span breaks off. The skyway ends because it fell.",
	},
	SC_CHUNK_CAP_SEALED_GATE = {
		AssetId = "rbxassetid://92822941612076",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/chunk_cap_sealed_gate.rbxmx",
		Notes = "Cap: a gate that stays shut. The skyway ends because someone closed it.",
	},

	-- === Hub prefabs =============================================
	-- Authored pieces of the Crossroads, synced to ServerStorage by Rojo and
	-- cloned by Util/PrefabLoader. Like the map entries below, AssetId stays
	-- empty forever: a prefab is a Model of many MeshParts, so the loader
	-- reads the NAME, not an uploaded mesh id.
	HUB_FATE_ENGINE = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/rbxm/prefabs/HUB_FATE_ENGINE.rbxmx",
		Notes = "The Fate Engine, delivered 2026-09-18: 78 MeshParts, flat "
			.. "shaded, untextured. A generator at ground level, a levitation "
			.. "core above it, the portal floating at the crown.",
	},

	HUB_CROSSROADS = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/rbxm/prefabs/HUB_CROSSROADS.rbxmx",
		Notes = "The hub shell, delivered 2026-09-18: 225 MeshParts, flat "
			.. "shaded, untextured. Plaza, four walkways, four districts and "
			.. "their dressing, plus the ground it stands on. Reserves the "
			.. "Fate Engine's footprint and models nothing inside it.",
	},
	HUB_BACKDROP = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/rbxm/prefabs/HUB_BACKDROP.rbxm",
		Notes = "The mountain horizon, delivered 2026-09-18: 4 MeshParts, "
			.. "4096 studs across at Scale. Authored in the same Blender "
			.. "scene as HUB_CROSSROADS, so it shares its scale and yaw. "
			.. "Pure decoration -- nothing looks it up.",
	},

	-- === Ethereal Scape ==========================================
	-- ONE ENTRY, not a kit. The delivered scene is a composed traverse -- its
	-- islands climb, its six bridges are each cut to their own gap, and the
	-- islands grow toward the temple -- so it ships whole and the chunk
	-- assembler never sees it. The eight ES_CHUNK_* placeholders that used to
	-- sit here were retired with the kit; they described a modular version of
	-- this scene that was never built.
	--
	-- This one is not a mesh id either. A prebuilt map is a Model of many
	-- MeshParts, synced into ServerStorage by Rojo and named for this key --
	-- so `assetId` stays empty forever and PrebuiltLoader reads the NAME.
	-- The manifest entry still earns its place: it is what Schema checks a
	-- world's PrebuiltMap.AssetKey against.
	ES_ENVIRONMENT_FULL = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/rbxm/maps/ES_ENVIRONMENT_FULL.rbxmx",
		Notes = "The whole Ethereal Scape scene, v2 (2026-09-17): 925 MeshParts "
			.. "with PBR SurfaceAppearances, 8 islands + 16 satellites, six "
			.. "railed golden bridges, one sky temple. Delivered anchored and "
			.. "at play scale. Cloned per expedition.",
	},
}

AssetManifest.ENTRIES = ENTRIES

--- Returns the asset id for a logical key, or nil when it is still a
--- placeholder. Callers fall back to primitive geometry on nil -- the same
--- seam HubBuilder uses for MeshId.
function AssetManifest.assetId(key: string): string?
	local entry = ENTRIES[key]
	if not entry or entry.Status ~= "UPLOADED" or entry.AssetId == "" then
		return nil
	end
	return entry.AssetId
end

function AssetManifest.exists(key: string): boolean
	return ENTRIES[key] ~= nil
end

function AssetManifest.isUploaded(key: string): boolean
	return AssetManifest.assetId(key) ~= nil
end

--- Counts by status. Printed at boot so it is obvious how much of the kit is
--- still placeholder geometry.
function AssetManifest.summary(): (number, number)
	local uploaded, placeholder = 0, 0
	for key in ENTRIES do
		if AssetManifest.isUploaded(key) then
			uploaded += 1
		else
			placeholder += 1
		end
	end
	return uploaded, placeholder
end

return AssetManifest
