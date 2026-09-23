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
	-- RE-IMPORTED 2026-09-23 with the ambient scenery split out (CHUNK_AUTHORING
	-- convention 6): the structure is now one FBX, one Model of 22 MeshParts,
	-- saved as SC_STRUCTURE.rbxmx; the floating props it used to carry are
	-- drawn client-side from assets/rbxm/props/SC_PROP_LIBRARY.rbxmx. The ids
	-- below are the structure-only meshes. The .rbxmx is provenance and a
	-- re-import path, NOT the load route: ChunkLoader calls
	-- CreateMeshPartAsync on the id.
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
		AssetId = "rbxassetid://94049257887544",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Octagonal arrival plaza under the Beacon.",
	},
	SC_CHUNK_PATH_STRAIGHT = {
		AssetId = "rbxassetid://78997875423445",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The gatehouse pier: a skyway under an arch between two turrets.",
	},
	SC_CHUNK_PATH_SKYPORT = {
		AssetId = "rbxassetid://72947286029946",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A plank pier with a dock islet off it: hazard pad, crane, a moored skiff.",
	},
	SC_CHUNK_PATH_HOOPS = {
		AssetId = "rbxassetid://127172600693241",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A bare glass-floored span through three floating rings, between two satellites.",
	},
	SC_CHUNK_PATH_SHATTERED = {
		AssetId = "rbxassetid://123495491942683",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The span is broken: eight floating plates, a stride apart, and the Sundered Spire whose crown hangs over its stump.",
	},
	SC_CHUNK_PATH_AVIARY = {
		AssetId = "rbxassetid://124455396728578",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The path runs through a gilded birdcage dome, birds in and around it.",
	},
	SC_CHUNK_CROSSROADS = {
		AssetId = "rbxassetid://102111942010566",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "THE INTERSECTION.",
	},
	SC_CHUNK_PATH_BEND = {
		AssetId = "rbxassetid://86529991861853",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Turns right round the Spired Keep.",
	},
	SC_CHUNK_PATH_BEND_WEST = {
		AssetId = "rbxassetid://73498702356852",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Turns left on a dark engine-deck, the lighthouse on its own islet.",
	},
	SC_CHUNK_VAULT_TURN = {
		AssetId = "rbxassetid://103360172438903",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The treasury, passed THROUGH on a right turn.",
	},
	SC_CHUNK_AETHER_SPRINGS = {
		AssetId = "rbxassetid://133993272884462",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Terraced pools and the Cascade Tower, water falling off the east rim; turns left.",
	},
	SC_CHUNK_GARDEN_TERRACE = {
		AssetId = "rbxassetid://80559202889312",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The hanging gardens: three islets, the Sky Tree, a pool, a gazebo.",
	},
	SC_CHUNK_OBSERVATORY = {
		AssetId = "rbxassetid://99367467929253",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A night-dark deck of stars: dome and mast, an orrery, dishes on a raised deck.",
	},
	SC_CHUNK_ARMORY = {
		AssetId = "rbxassetid://98167757653076",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A slate training yard and a barracks islet, under the banner mast.",
	},
	SC_CHUNK_ARCHIVE = {
		AssetId = "rbxassetid://105600917024638",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A roofed hall of shelves and ribbed vaults, floating tomes, the clock tower.",
	},
	SC_CHUNK_SPIRE_COURT = {
		AssetId = "rbxassetid://112340084496568",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Gate-court: the Sky Fountain and the Ascent Gate.",
	},
	SC_CHUNK_SPIRE_COURT_B = {
		AssetId = "rbxassetid://125770373844244",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Gate-court, rare: the Hall of Winds and its Moon Gate.",
	},
	SC_CHUNK_SIDE_LOOKOUT = {
		AssetId = "rbxassetid://136095255275027",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The world's SIDE pocket: a lookout and a loot cache, hung off a spare socket (a crossroads branch, typically) when IncludeSide is on.",
	},
	SC_CHUNK_BOSS_CLEARING = {
		AssetId = "rbxassetid://102538331648323",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The Crown Spire arena.",
	},
	SC_CHUNK_CAP_CRUMBLING = {
		AssetId = "rbxassetid://95272297315947",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A CAP: the skyway breaks off, its far half falling away, the Fallen Tower leaning over the gap.",
	},
	SC_CHUNK_CAP_OVERLOOK = {
		AssetId = "rbxassetid://131155400187787",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A CAP: the skyway ends at a railed round overlook with a light obelisk and telescopes.",
	},
	SC_CHUNK_CAP_SEALED_GATE = {
		AssetId = "rbxassetid://123385393207558",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A CAP: a citadel gate that stays shut.",
	},
	SC_CHUNK_PATH_COLONNADE = {
		AssetId = "rbxassetid://109271913099646",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The colonnade walk.",
	},
	SC_CHUNK_PATH_LONG_SPAN = {
		AssetId = "rbxassetid://119934137413101",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A long bare span over the drop.",
	},
	SC_CHUNK_PATH_LANTERN_ROW = {
		AssetId = "rbxassetid://82555863479592",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The lantern row.",
	},
	SC_CHUNK_PATH_TOWER_BEND = {
		AssetId = "rbxassetid://115687023110260",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Turns left round the watchtower.",
	},
	SC_CHUNK_PATH_TEE = {
		AssetId = "rbxassetid://138819351669775",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The tee junction.",
	},
	SC_CHUNK_PARADE_GROUND = {
		AssetId = "rbxassetid://112058013004730",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The parade ground.",
	},
	SC_CHUNK_TURBINE_HALL = {
		AssetId = "rbxassetid://106800163286808",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The turbine hall.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT = {
		AssetId = "rbxassetid://105159690917279",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Lighthouse point.",
	},
	SC_CHUNK_SKY_TREE_GROVE = {
		AssetId = "rbxassetid://72639705966751",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The sky tree grove.",
	},
	SC_CHUNK_DOCKSIDE = {
		AssetId = "rbxassetid://84529014375658",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The dockside yard.",
	},
	SC_CHUNK_SIDE_CHAPEL = {
		AssetId = "rbxassetid://71882175994823",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The chapel of winds.",
	},
	SC_CHUNK_SIDE_GARDEN = {
		AssetId = "rbxassetid://79173929695135",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A hanging garden.",
	},
	SC_CHUNK_SIDE_RELIQUARY = {
		AssetId = "rbxassetid://76898127982909",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The reliquary.",
	},
	SC_CHUNK_PRISM_ARENA = {
		AssetId = "rbxassetid://112610584864125",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The Prism Arena.",
	},
	-- Per-atmosphere recolours (same geometry): ChunkLoader swaps one in when the run's atmosphere matches.
	SC_CHUNK_AETHER_SPRINGS__AETHER_SURGE = {
		AssetId = "rbxassetid://137206629498345",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_AETHER_SPRINGS.",
	},
	SC_CHUNK_AETHER_SPRINGS__LOCKDOWN = {
		AssetId = "rbxassetid://78515248336647",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_AETHER_SPRINGS.",
	},
	SC_CHUNK_AETHER_SPRINGS__RECLAIMED = {
		AssetId = "rbxassetid://106184687471483",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_AETHER_SPRINGS.",
	},
	SC_CHUNK_AETHER_SPRINGS__RIME = {
		AssetId = "rbxassetid://102023034823193",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_AETHER_SPRINGS.",
	},
	SC_CHUNK_AETHER_SPRINGS__SIEGE = {
		AssetId = "rbxassetid://81861555141160",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_AETHER_SPRINGS.",
	},
	SC_CHUNK_AETHER_SPRINGS__STORMHAWK = {
		AssetId = "rbxassetid://119811137310821",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_AETHER_SPRINGS.",
	},
	SC_CHUNK_AETHER_SPRINGS__UNMOORING = {
		AssetId = "rbxassetid://97023130794785",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_AETHER_SPRINGS.",
	},
	SC_CHUNK_ARCHIVE__AETHER_SURGE = {
		AssetId = "rbxassetid://112908295576464",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_ARCHIVE.",
	},
	SC_CHUNK_ARCHIVE__LOCKDOWN = {
		AssetId = "rbxassetid://74195541066107",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_ARCHIVE.",
	},
	SC_CHUNK_ARCHIVE__RECLAIMED = {
		AssetId = "rbxassetid://139473046634644",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_ARCHIVE.",
	},
	SC_CHUNK_ARCHIVE__RIME = {
		AssetId = "rbxassetid://110324769970149",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_ARCHIVE.",
	},
	SC_CHUNK_ARCHIVE__SIEGE = {
		AssetId = "rbxassetid://90480893147936",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_ARCHIVE.",
	},
	SC_CHUNK_ARCHIVE__STORMHAWK = {
		AssetId = "rbxassetid://110039671215328",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_ARCHIVE.",
	},
	SC_CHUNK_ARCHIVE__UNMOORING = {
		AssetId = "rbxassetid://124675185369039",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_ARCHIVE.",
	},
	SC_CHUNK_ARMORY__AETHER_SURGE = {
		AssetId = "rbxassetid://91200336526370",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_ARMORY.",
	},
	SC_CHUNK_ARMORY__LOCKDOWN = {
		AssetId = "rbxassetid://87462537371489",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_ARMORY.",
	},
	SC_CHUNK_ARMORY__RECLAIMED = {
		AssetId = "rbxassetid://101987662460062",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_ARMORY.",
	},
	SC_CHUNK_ARMORY__RIME = {
		AssetId = "rbxassetid://112721384829697",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_ARMORY.",
	},
	SC_CHUNK_ARMORY__SIEGE = {
		AssetId = "rbxassetid://79667456174284",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_ARMORY.",
	},
	SC_CHUNK_ARMORY__STORMHAWK = {
		AssetId = "rbxassetid://95351078246643",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_ARMORY.",
	},
	SC_CHUNK_ARMORY__UNMOORING = {
		AssetId = "rbxassetid://134791363305663",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_ARMORY.",
	},
	SC_CHUNK_BOSS_CLEARING__AETHER_SURGE = {
		AssetId = "rbxassetid://84169297581505",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_BOSS_CLEARING.",
	},
	SC_CHUNK_BOSS_CLEARING__LOCKDOWN = {
		AssetId = "rbxassetid://83526673394804",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_BOSS_CLEARING.",
	},
	SC_CHUNK_BOSS_CLEARING__RECLAIMED = {
		AssetId = "rbxassetid://82019870852546",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_BOSS_CLEARING.",
	},
	SC_CHUNK_BOSS_CLEARING__RIME = {
		AssetId = "rbxassetid://93674089233437",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_BOSS_CLEARING.",
	},
	SC_CHUNK_BOSS_CLEARING__SIEGE = {
		AssetId = "rbxassetid://105602164875863",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_BOSS_CLEARING.",
	},
	SC_CHUNK_BOSS_CLEARING__STORMHAWK = {
		AssetId = "rbxassetid://71788089421427",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_BOSS_CLEARING.",
	},
	SC_CHUNK_BOSS_CLEARING__UNMOORING = {
		AssetId = "rbxassetid://97228286384237",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_BOSS_CLEARING.",
	},
	SC_CHUNK_CAP_CRUMBLING__AETHER_SURGE = {
		AssetId = "rbxassetid://94326173867057",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_CAP_CRUMBLING.",
	},
	SC_CHUNK_CAP_CRUMBLING__LOCKDOWN = {
		AssetId = "rbxassetid://121102818882248",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_CAP_CRUMBLING.",
	},
	SC_CHUNK_CAP_CRUMBLING__RECLAIMED = {
		AssetId = "rbxassetid://80478662959982",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_CAP_CRUMBLING.",
	},
	SC_CHUNK_CAP_CRUMBLING__RIME = {
		AssetId = "rbxassetid://132179510717185",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_CAP_CRUMBLING.",
	},
	SC_CHUNK_CAP_CRUMBLING__SIEGE = {
		AssetId = "rbxassetid://72848597198970",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_CAP_CRUMBLING.",
	},
	SC_CHUNK_CAP_CRUMBLING__STORMHAWK = {
		AssetId = "rbxassetid://119074664314080",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_CAP_CRUMBLING.",
	},
	SC_CHUNK_CAP_CRUMBLING__UNMOORING = {
		AssetId = "rbxassetid://89869401142915",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_CAP_CRUMBLING.",
	},
	SC_CHUNK_CAP_OVERLOOK__AETHER_SURGE = {
		AssetId = "rbxassetid://104234217243491",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_CAP_OVERLOOK.",
	},
	SC_CHUNK_CAP_OVERLOOK__LOCKDOWN = {
		AssetId = "rbxassetid://76993614739741",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_CAP_OVERLOOK.",
	},
	SC_CHUNK_CAP_OVERLOOK__RECLAIMED = {
		AssetId = "rbxassetid://78234132277539",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_CAP_OVERLOOK.",
	},
	SC_CHUNK_CAP_OVERLOOK__RIME = {
		AssetId = "rbxassetid://79619712981398",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_CAP_OVERLOOK.",
	},
	SC_CHUNK_CAP_OVERLOOK__SIEGE = {
		AssetId = "rbxassetid://108542017650954",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_CAP_OVERLOOK.",
	},
	SC_CHUNK_CAP_OVERLOOK__STORMHAWK = {
		AssetId = "rbxassetid://84927669227887",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_CAP_OVERLOOK.",
	},
	SC_CHUNK_CAP_OVERLOOK__UNMOORING = {
		AssetId = "rbxassetid://115341364233142",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_CAP_OVERLOOK.",
	},
	SC_CHUNK_CAP_SEALED_GATE__AETHER_SURGE = {
		AssetId = "rbxassetid://111300328030613",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_CAP_SEALED_GATE.",
	},
	SC_CHUNK_CAP_SEALED_GATE__LOCKDOWN = {
		AssetId = "rbxassetid://100477472347783",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_CAP_SEALED_GATE.",
	},
	SC_CHUNK_CAP_SEALED_GATE__RECLAIMED = {
		AssetId = "rbxassetid://82187729770963",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_CAP_SEALED_GATE.",
	},
	SC_CHUNK_CAP_SEALED_GATE__RIME = {
		AssetId = "rbxassetid://112432812038520",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_CAP_SEALED_GATE.",
	},
	SC_CHUNK_CAP_SEALED_GATE__SIEGE = {
		AssetId = "rbxassetid://117355247195629",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_CAP_SEALED_GATE.",
	},
	SC_CHUNK_CAP_SEALED_GATE__STORMHAWK = {
		AssetId = "rbxassetid://98769823033919",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_CAP_SEALED_GATE.",
	},
	SC_CHUNK_CAP_SEALED_GATE__UNMOORING = {
		AssetId = "rbxassetid://97129120044273",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_CAP_SEALED_GATE.",
	},
	SC_CHUNK_CROSSROADS__AETHER_SURGE = {
		AssetId = "rbxassetid://134289724073130",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_CROSSROADS.",
	},
	SC_CHUNK_CROSSROADS__LOCKDOWN = {
		AssetId = "rbxassetid://80452401136170",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_CROSSROADS.",
	},
	SC_CHUNK_CROSSROADS__RECLAIMED = {
		AssetId = "rbxassetid://98553092071839",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_CROSSROADS.",
	},
	SC_CHUNK_CROSSROADS__RIME = {
		AssetId = "rbxassetid://107373813724842",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_CROSSROADS.",
	},
	SC_CHUNK_CROSSROADS__SIEGE = {
		AssetId = "rbxassetid://94473788141557",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_CROSSROADS.",
	},
	SC_CHUNK_CROSSROADS__STORMHAWK = {
		AssetId = "rbxassetid://90693800040281",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_CROSSROADS.",
	},
	SC_CHUNK_CROSSROADS__UNMOORING = {
		AssetId = "rbxassetid://99076009271187",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_CROSSROADS.",
	},
	SC_CHUNK_DOCKSIDE__AETHER_SURGE = {
		AssetId = "rbxassetid://70616407130164",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_DOCKSIDE.",
	},
	SC_CHUNK_DOCKSIDE__LOCKDOWN = {
		AssetId = "rbxassetid://81129366520429",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_DOCKSIDE.",
	},
	SC_CHUNK_DOCKSIDE__RECLAIMED = {
		AssetId = "rbxassetid://70670858185264",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_DOCKSIDE.",
	},
	SC_CHUNK_DOCKSIDE__RIME = {
		AssetId = "rbxassetid://123731523023551",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_DOCKSIDE.",
	},
	SC_CHUNK_DOCKSIDE__SIEGE = {
		AssetId = "rbxassetid://131394256189799",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_DOCKSIDE.",
	},
	SC_CHUNK_DOCKSIDE__STORMHAWK = {
		AssetId = "rbxassetid://110548590076216",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_DOCKSIDE.",
	},
	SC_CHUNK_DOCKSIDE__UNMOORING = {
		AssetId = "rbxassetid://121633300876108",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_DOCKSIDE.",
	},
	SC_CHUNK_ENTRY__AETHER_SURGE = {
		AssetId = "rbxassetid://117448788938691",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_ENTRY.",
	},
	SC_CHUNK_ENTRY__LOCKDOWN = {
		AssetId = "rbxassetid://96483341954994",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_ENTRY.",
	},
	SC_CHUNK_ENTRY__RECLAIMED = {
		AssetId = "rbxassetid://76813362028258",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_ENTRY.",
	},
	SC_CHUNK_ENTRY__RIME = {
		AssetId = "rbxassetid://100007888298247",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_ENTRY.",
	},
	SC_CHUNK_ENTRY__SIEGE = {
		AssetId = "rbxassetid://109725231836832",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_ENTRY.",
	},
	SC_CHUNK_ENTRY__STORMHAWK = {
		AssetId = "rbxassetid://106343246323307",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_ENTRY.",
	},
	SC_CHUNK_ENTRY__UNMOORING = {
		AssetId = "rbxassetid://99008664614126",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_ENTRY.",
	},
	SC_CHUNK_GARDEN_TERRACE__AETHER_SURGE = {
		AssetId = "rbxassetid://130357271651062",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_GARDEN_TERRACE.",
	},
	SC_CHUNK_GARDEN_TERRACE__LOCKDOWN = {
		AssetId = "rbxassetid://77540428150406",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_GARDEN_TERRACE.",
	},
	SC_CHUNK_GARDEN_TERRACE__RECLAIMED = {
		AssetId = "rbxassetid://139130723646665",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_GARDEN_TERRACE.",
	},
	SC_CHUNK_GARDEN_TERRACE__RIME = {
		AssetId = "rbxassetid://77965777419823",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_GARDEN_TERRACE.",
	},
	SC_CHUNK_GARDEN_TERRACE__SIEGE = {
		AssetId = "rbxassetid://101147706870368",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_GARDEN_TERRACE.",
	},
	SC_CHUNK_GARDEN_TERRACE__STORMHAWK = {
		AssetId = "rbxassetid://109947034331851",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_GARDEN_TERRACE.",
	},
	SC_CHUNK_GARDEN_TERRACE__UNMOORING = {
		AssetId = "rbxassetid://116922486937158",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_GARDEN_TERRACE.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT__AETHER_SURGE = {
		AssetId = "rbxassetid://125445827199676",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_LIGHTHOUSE_POINT.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT__LOCKDOWN = {
		AssetId = "rbxassetid://101059084923630",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_LIGHTHOUSE_POINT.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT__RECLAIMED = {
		AssetId = "rbxassetid://140301886697913",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_LIGHTHOUSE_POINT.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT__RIME = {
		AssetId = "rbxassetid://91320986767954",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_LIGHTHOUSE_POINT.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT__SIEGE = {
		AssetId = "rbxassetid://140686940149178",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_LIGHTHOUSE_POINT.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT__STORMHAWK = {
		AssetId = "rbxassetid://128349868553548",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_LIGHTHOUSE_POINT.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT__UNMOORING = {
		AssetId = "rbxassetid://79523172391800",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_LIGHTHOUSE_POINT.",
	},
	SC_CHUNK_OBSERVATORY__AETHER_SURGE = {
		AssetId = "rbxassetid://123511635634227",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_OBSERVATORY.",
	},
	SC_CHUNK_OBSERVATORY__LOCKDOWN = {
		AssetId = "rbxassetid://106984947422527",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_OBSERVATORY.",
	},
	SC_CHUNK_OBSERVATORY__RECLAIMED = {
		AssetId = "rbxassetid://98085924954705",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_OBSERVATORY.",
	},
	SC_CHUNK_OBSERVATORY__RIME = {
		AssetId = "rbxassetid://108896116240517",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_OBSERVATORY.",
	},
	SC_CHUNK_OBSERVATORY__SIEGE = {
		AssetId = "rbxassetid://122393337738581",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_OBSERVATORY.",
	},
	SC_CHUNK_OBSERVATORY__STORMHAWK = {
		AssetId = "rbxassetid://129651827475021",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_OBSERVATORY.",
	},
	SC_CHUNK_OBSERVATORY__UNMOORING = {
		AssetId = "rbxassetid://130074465759891",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_OBSERVATORY.",
	},
	SC_CHUNK_PARADE_GROUND__AETHER_SURGE = {
		AssetId = "rbxassetid://114593493077437",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PARADE_GROUND.",
	},
	SC_CHUNK_PARADE_GROUND__LOCKDOWN = {
		AssetId = "rbxassetid://114362557757768",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PARADE_GROUND.",
	},
	SC_CHUNK_PARADE_GROUND__RECLAIMED = {
		AssetId = "rbxassetid://118807032768976",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PARADE_GROUND.",
	},
	SC_CHUNK_PARADE_GROUND__RIME = {
		AssetId = "rbxassetid://121930437903085",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PARADE_GROUND.",
	},
	SC_CHUNK_PARADE_GROUND__SIEGE = {
		AssetId = "rbxassetid://125173875522470",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PARADE_GROUND.",
	},
	SC_CHUNK_PARADE_GROUND__STORMHAWK = {
		AssetId = "rbxassetid://78311622648802",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PARADE_GROUND.",
	},
	SC_CHUNK_PARADE_GROUND__UNMOORING = {
		AssetId = "rbxassetid://136722058804489",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PARADE_GROUND.",
	},
	SC_CHUNK_PATH_AVIARY__AETHER_SURGE = {
		AssetId = "rbxassetid://121686945662559",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_AVIARY.",
	},
	SC_CHUNK_PATH_AVIARY__LOCKDOWN = {
		AssetId = "rbxassetid://125688973459079",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_AVIARY.",
	},
	SC_CHUNK_PATH_AVIARY__RECLAIMED = {
		AssetId = "rbxassetid://91369286113042",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_AVIARY.",
	},
	SC_CHUNK_PATH_AVIARY__RIME = {
		AssetId = "rbxassetid://124012141028514",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_AVIARY.",
	},
	SC_CHUNK_PATH_AVIARY__SIEGE = {
		AssetId = "rbxassetid://136243947848877",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_AVIARY.",
	},
	SC_CHUNK_PATH_AVIARY__STORMHAWK = {
		AssetId = "rbxassetid://139311648283096",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_AVIARY.",
	},
	SC_CHUNK_PATH_AVIARY__UNMOORING = {
		AssetId = "rbxassetid://75681314260480",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_AVIARY.",
	},
	SC_CHUNK_PATH_BEND__AETHER_SURGE = {
		AssetId = "rbxassetid://140320646632179",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_BEND.",
	},
	SC_CHUNK_PATH_BEND__LOCKDOWN = {
		AssetId = "rbxassetid://91287432136191",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_BEND.",
	},
	SC_CHUNK_PATH_BEND__RECLAIMED = {
		AssetId = "rbxassetid://135824914356303",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_BEND.",
	},
	SC_CHUNK_PATH_BEND__RIME = {
		AssetId = "rbxassetid://123075961401577",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_BEND.",
	},
	SC_CHUNK_PATH_BEND__SIEGE = {
		AssetId = "rbxassetid://134088348801815",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_BEND.",
	},
	SC_CHUNK_PATH_BEND__STORMHAWK = {
		AssetId = "rbxassetid://102340526513846",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_BEND.",
	},
	SC_CHUNK_PATH_BEND__UNMOORING = {
		AssetId = "rbxassetid://128360435486134",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_BEND.",
	},
	SC_CHUNK_PATH_BEND_WEST__AETHER_SURGE = {
		AssetId = "rbxassetid://88903871658548",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_BEND_WEST.",
	},
	SC_CHUNK_PATH_BEND_WEST__LOCKDOWN = {
		AssetId = "rbxassetid://118251731606633",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_BEND_WEST.",
	},
	SC_CHUNK_PATH_BEND_WEST__RECLAIMED = {
		AssetId = "rbxassetid://88981040171007",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_BEND_WEST.",
	},
	SC_CHUNK_PATH_BEND_WEST__RIME = {
		AssetId = "rbxassetid://84550435127719",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_BEND_WEST.",
	},
	SC_CHUNK_PATH_BEND_WEST__SIEGE = {
		AssetId = "rbxassetid://96469512235719",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_BEND_WEST.",
	},
	SC_CHUNK_PATH_BEND_WEST__STORMHAWK = {
		AssetId = "rbxassetid://82193652798092",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_BEND_WEST.",
	},
	SC_CHUNK_PATH_BEND_WEST__UNMOORING = {
		AssetId = "rbxassetid://88280522953605",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_BEND_WEST.",
	},
	SC_CHUNK_PATH_COLONNADE__AETHER_SURGE = {
		AssetId = "rbxassetid://99128090557904",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_COLONNADE.",
	},
	SC_CHUNK_PATH_COLONNADE__LOCKDOWN = {
		AssetId = "rbxassetid://79433511821625",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_COLONNADE.",
	},
	SC_CHUNK_PATH_COLONNADE__RECLAIMED = {
		AssetId = "rbxassetid://104323062717675",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_COLONNADE.",
	},
	SC_CHUNK_PATH_COLONNADE__RIME = {
		AssetId = "rbxassetid://91596285167650",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_COLONNADE.",
	},
	SC_CHUNK_PATH_COLONNADE__SIEGE = {
		AssetId = "rbxassetid://105701283630575",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_COLONNADE.",
	},
	SC_CHUNK_PATH_COLONNADE__STORMHAWK = {
		AssetId = "rbxassetid://81177532652805",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_COLONNADE.",
	},
	SC_CHUNK_PATH_COLONNADE__UNMOORING = {
		AssetId = "rbxassetid://103128733462497",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_COLONNADE.",
	},
	SC_CHUNK_PATH_HOOPS__AETHER_SURGE = {
		AssetId = "rbxassetid://74503252419035",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_HOOPS.",
	},
	SC_CHUNK_PATH_HOOPS__LOCKDOWN = {
		AssetId = "rbxassetid://123110085887872",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_HOOPS.",
	},
	SC_CHUNK_PATH_HOOPS__RECLAIMED = {
		AssetId = "rbxassetid://74107047034244",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_HOOPS.",
	},
	SC_CHUNK_PATH_HOOPS__RIME = {
		AssetId = "rbxassetid://82070927044202",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_HOOPS.",
	},
	SC_CHUNK_PATH_HOOPS__SIEGE = {
		AssetId = "rbxassetid://84076707580242",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_HOOPS.",
	},
	SC_CHUNK_PATH_HOOPS__STORMHAWK = {
		AssetId = "rbxassetid://128831176637366",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_HOOPS.",
	},
	SC_CHUNK_PATH_HOOPS__UNMOORING = {
		AssetId = "rbxassetid://87313616580861",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_HOOPS.",
	},
	SC_CHUNK_PATH_LANTERN_ROW__AETHER_SURGE = {
		AssetId = "rbxassetid://99179718890088",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_LANTERN_ROW.",
	},
	SC_CHUNK_PATH_LANTERN_ROW__LOCKDOWN = {
		AssetId = "rbxassetid://84841374574248",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_LANTERN_ROW.",
	},
	SC_CHUNK_PATH_LANTERN_ROW__RECLAIMED = {
		AssetId = "rbxassetid://90174005501015",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_LANTERN_ROW.",
	},
	SC_CHUNK_PATH_LANTERN_ROW__RIME = {
		AssetId = "rbxassetid://138464470196598",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_LANTERN_ROW.",
	},
	SC_CHUNK_PATH_LANTERN_ROW__SIEGE = {
		AssetId = "rbxassetid://82918980354869",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_LANTERN_ROW.",
	},
	SC_CHUNK_PATH_LANTERN_ROW__STORMHAWK = {
		AssetId = "rbxassetid://79377088129841",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_LANTERN_ROW.",
	},
	SC_CHUNK_PATH_LANTERN_ROW__UNMOORING = {
		AssetId = "rbxassetid://116171936632611",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_LANTERN_ROW.",
	},
	SC_CHUNK_PATH_LONG_SPAN__AETHER_SURGE = {
		AssetId = "rbxassetid://77191749201349",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_LONG_SPAN.",
	},
	SC_CHUNK_PATH_LONG_SPAN__LOCKDOWN = {
		AssetId = "rbxassetid://133308433756656",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_LONG_SPAN.",
	},
	SC_CHUNK_PATH_LONG_SPAN__RECLAIMED = {
		AssetId = "rbxassetid://130422093977838",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_LONG_SPAN.",
	},
	SC_CHUNK_PATH_LONG_SPAN__RIME = {
		AssetId = "rbxassetid://112867166599406",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_LONG_SPAN.",
	},
	SC_CHUNK_PATH_LONG_SPAN__SIEGE = {
		AssetId = "rbxassetid://85931854683101",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_LONG_SPAN.",
	},
	SC_CHUNK_PATH_LONG_SPAN__STORMHAWK = {
		AssetId = "rbxassetid://134524133827956",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_LONG_SPAN.",
	},
	SC_CHUNK_PATH_LONG_SPAN__UNMOORING = {
		AssetId = "rbxassetid://92933065124133",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_LONG_SPAN.",
	},
	SC_CHUNK_PATH_SHATTERED__AETHER_SURGE = {
		AssetId = "rbxassetid://81750293789130",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_SHATTERED.",
	},
	SC_CHUNK_PATH_SHATTERED__LOCKDOWN = {
		AssetId = "rbxassetid://86536669155032",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_SHATTERED.",
	},
	SC_CHUNK_PATH_SHATTERED__RECLAIMED = {
		AssetId = "rbxassetid://116686808577771",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_SHATTERED.",
	},
	SC_CHUNK_PATH_SHATTERED__RIME = {
		AssetId = "rbxassetid://95831173497594",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_SHATTERED.",
	},
	SC_CHUNK_PATH_SHATTERED__SIEGE = {
		AssetId = "rbxassetid://124238449477933",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_SHATTERED.",
	},
	SC_CHUNK_PATH_SHATTERED__STORMHAWK = {
		AssetId = "rbxassetid://120435410040999",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_SHATTERED.",
	},
	SC_CHUNK_PATH_SHATTERED__UNMOORING = {
		AssetId = "rbxassetid://107837372986748",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_SHATTERED.",
	},
	SC_CHUNK_PATH_SKYPORT__AETHER_SURGE = {
		AssetId = "rbxassetid://128484716566177",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_SKYPORT.",
	},
	SC_CHUNK_PATH_SKYPORT__LOCKDOWN = {
		AssetId = "rbxassetid://70853171160892",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_SKYPORT.",
	},
	SC_CHUNK_PATH_SKYPORT__RECLAIMED = {
		AssetId = "rbxassetid://127356189984363",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_SKYPORT.",
	},
	SC_CHUNK_PATH_SKYPORT__RIME = {
		AssetId = "rbxassetid://90135555163438",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_SKYPORT.",
	},
	SC_CHUNK_PATH_SKYPORT__SIEGE = {
		AssetId = "rbxassetid://94357023909668",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_SKYPORT.",
	},
	SC_CHUNK_PATH_SKYPORT__STORMHAWK = {
		AssetId = "rbxassetid://85023069368388",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_SKYPORT.",
	},
	SC_CHUNK_PATH_SKYPORT__UNMOORING = {
		AssetId = "rbxassetid://113927219875059",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_SKYPORT.",
	},
	SC_CHUNK_PATH_STRAIGHT__AETHER_SURGE = {
		AssetId = "rbxassetid://124057969418837",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_STRAIGHT.",
	},
	SC_CHUNK_PATH_STRAIGHT__LOCKDOWN = {
		AssetId = "rbxassetid://84260467775016",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_STRAIGHT.",
	},
	SC_CHUNK_PATH_STRAIGHT__RECLAIMED = {
		AssetId = "rbxassetid://128757076070470",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_STRAIGHT.",
	},
	SC_CHUNK_PATH_STRAIGHT__RIME = {
		AssetId = "rbxassetid://127298351032765",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_STRAIGHT.",
	},
	SC_CHUNK_PATH_STRAIGHT__SIEGE = {
		AssetId = "rbxassetid://128855118962453",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_STRAIGHT.",
	},
	SC_CHUNK_PATH_STRAIGHT__STORMHAWK = {
		AssetId = "rbxassetid://104104392571603",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_STRAIGHT.",
	},
	SC_CHUNK_PATH_STRAIGHT__UNMOORING = {
		AssetId = "rbxassetid://73478379671870",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_STRAIGHT.",
	},
	SC_CHUNK_PATH_TEE__AETHER_SURGE = {
		AssetId = "rbxassetid://94330760788735",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_TEE.",
	},
	SC_CHUNK_PATH_TEE__LOCKDOWN = {
		AssetId = "rbxassetid://74387273981888",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_TEE.",
	},
	SC_CHUNK_PATH_TEE__RECLAIMED = {
		AssetId = "rbxassetid://127268080409257",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_TEE.",
	},
	SC_CHUNK_PATH_TEE__RIME = {
		AssetId = "rbxassetid://103984094032811",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_TEE.",
	},
	SC_CHUNK_PATH_TEE__SIEGE = {
		AssetId = "rbxassetid://92267139938311",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_TEE.",
	},
	SC_CHUNK_PATH_TEE__STORMHAWK = {
		AssetId = "rbxassetid://115479075432983",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_TEE.",
	},
	SC_CHUNK_PATH_TEE__UNMOORING = {
		AssetId = "rbxassetid://121377806741512",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_TEE.",
	},
	SC_CHUNK_PATH_TOWER_BEND__AETHER_SURGE = {
		AssetId = "rbxassetid://133771697021826",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_TOWER_BEND.",
	},
	SC_CHUNK_PATH_TOWER_BEND__LOCKDOWN = {
		AssetId = "rbxassetid://91671933813743",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_TOWER_BEND.",
	},
	SC_CHUNK_PATH_TOWER_BEND__RECLAIMED = {
		AssetId = "rbxassetid://140131186387652",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_TOWER_BEND.",
	},
	SC_CHUNK_PATH_TOWER_BEND__RIME = {
		AssetId = "rbxassetid://82481636982829",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_TOWER_BEND.",
	},
	SC_CHUNK_PATH_TOWER_BEND__SIEGE = {
		AssetId = "rbxassetid://103197058189184",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_TOWER_BEND.",
	},
	SC_CHUNK_PATH_TOWER_BEND__STORMHAWK = {
		AssetId = "rbxassetid://95867924002099",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_TOWER_BEND.",
	},
	SC_CHUNK_PATH_TOWER_BEND__UNMOORING = {
		AssetId = "rbxassetid://126791801964360",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_TOWER_BEND.",
	},
	SC_CHUNK_PRISM_ARENA__AETHER_SURGE = {
		AssetId = "rbxassetid://74691536360339",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PRISM_ARENA.",
	},
	SC_CHUNK_PRISM_ARENA__LOCKDOWN = {
		AssetId = "rbxassetid://104691976951628",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PRISM_ARENA.",
	},
	SC_CHUNK_PRISM_ARENA__RECLAIMED = {
		AssetId = "rbxassetid://94008436254825",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PRISM_ARENA.",
	},
	SC_CHUNK_PRISM_ARENA__RIME = {
		AssetId = "rbxassetid://83702171385034",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PRISM_ARENA.",
	},
	SC_CHUNK_PRISM_ARENA__SIEGE = {
		AssetId = "rbxassetid://130884665115700",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PRISM_ARENA.",
	},
	SC_CHUNK_PRISM_ARENA__STORMHAWK = {
		AssetId = "rbxassetid://83067243238479",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PRISM_ARENA.",
	},
	SC_CHUNK_PRISM_ARENA__UNMOORING = {
		AssetId = "rbxassetid://106448839556521",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PRISM_ARENA.",
	},
	SC_CHUNK_SIDE_CHAPEL__AETHER_SURGE = {
		AssetId = "rbxassetid://139450200505450",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_SIDE_CHAPEL.",
	},
	SC_CHUNK_SIDE_CHAPEL__LOCKDOWN = {
		AssetId = "rbxassetid://109272124409250",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_SIDE_CHAPEL.",
	},
	SC_CHUNK_SIDE_CHAPEL__RECLAIMED = {
		AssetId = "rbxassetid://137713812751529",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_SIDE_CHAPEL.",
	},
	SC_CHUNK_SIDE_CHAPEL__RIME = {
		AssetId = "rbxassetid://70792018285406",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_SIDE_CHAPEL.",
	},
	SC_CHUNK_SIDE_CHAPEL__SIEGE = {
		AssetId = "rbxassetid://123517961246893",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_SIDE_CHAPEL.",
	},
	SC_CHUNK_SIDE_CHAPEL__STORMHAWK = {
		AssetId = "rbxassetid://132353895889058",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_SIDE_CHAPEL.",
	},
	SC_CHUNK_SIDE_CHAPEL__UNMOORING = {
		AssetId = "rbxassetid://79186147172743",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_SIDE_CHAPEL.",
	},
	SC_CHUNK_SIDE_GARDEN__AETHER_SURGE = {
		AssetId = "rbxassetid://133640312510726",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_SIDE_GARDEN.",
	},
	SC_CHUNK_SIDE_GARDEN__LOCKDOWN = {
		AssetId = "rbxassetid://75864315397875",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_SIDE_GARDEN.",
	},
	SC_CHUNK_SIDE_GARDEN__RECLAIMED = {
		AssetId = "rbxassetid://123959028445165",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_SIDE_GARDEN.",
	},
	SC_CHUNK_SIDE_GARDEN__RIME = {
		AssetId = "rbxassetid://89425291564378",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_SIDE_GARDEN.",
	},
	SC_CHUNK_SIDE_GARDEN__SIEGE = {
		AssetId = "rbxassetid://117036525121166",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_SIDE_GARDEN.",
	},
	SC_CHUNK_SIDE_GARDEN__STORMHAWK = {
		AssetId = "rbxassetid://110644487065673",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_SIDE_GARDEN.",
	},
	SC_CHUNK_SIDE_GARDEN__UNMOORING = {
		AssetId = "rbxassetid://113727639869430",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_SIDE_GARDEN.",
	},
	SC_CHUNK_SIDE_LOOKOUT__AETHER_SURGE = {
		AssetId = "rbxassetid://118659903543380",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_SIDE_LOOKOUT.",
	},
	SC_CHUNK_SIDE_LOOKOUT__LOCKDOWN = {
		AssetId = "rbxassetid://123891889835775",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_SIDE_LOOKOUT.",
	},
	SC_CHUNK_SIDE_LOOKOUT__RECLAIMED = {
		AssetId = "rbxassetid://125469508672011",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_SIDE_LOOKOUT.",
	},
	SC_CHUNK_SIDE_LOOKOUT__RIME = {
		AssetId = "rbxassetid://85560707818316",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_SIDE_LOOKOUT.",
	},
	SC_CHUNK_SIDE_LOOKOUT__SIEGE = {
		AssetId = "rbxassetid://91666311737019",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_SIDE_LOOKOUT.",
	},
	SC_CHUNK_SIDE_LOOKOUT__STORMHAWK = {
		AssetId = "rbxassetid://85861684956022",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_SIDE_LOOKOUT.",
	},
	SC_CHUNK_SIDE_LOOKOUT__UNMOORING = {
		AssetId = "rbxassetid://110588770561997",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_SIDE_LOOKOUT.",
	},
	SC_CHUNK_SIDE_RELIQUARY__AETHER_SURGE = {
		AssetId = "rbxassetid://77614195188009",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_SIDE_RELIQUARY.",
	},
	SC_CHUNK_SIDE_RELIQUARY__LOCKDOWN = {
		AssetId = "rbxassetid://90449683943007",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_SIDE_RELIQUARY.",
	},
	SC_CHUNK_SIDE_RELIQUARY__RECLAIMED = {
		AssetId = "rbxassetid://101018739817053",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_SIDE_RELIQUARY.",
	},
	SC_CHUNK_SIDE_RELIQUARY__RIME = {
		AssetId = "rbxassetid://122875461284136",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_SIDE_RELIQUARY.",
	},
	SC_CHUNK_SIDE_RELIQUARY__SIEGE = {
		AssetId = "rbxassetid://98322744331201",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_SIDE_RELIQUARY.",
	},
	SC_CHUNK_SIDE_RELIQUARY__STORMHAWK = {
		AssetId = "rbxassetid://120643359857422",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_SIDE_RELIQUARY.",
	},
	SC_CHUNK_SIDE_RELIQUARY__UNMOORING = {
		AssetId = "rbxassetid://125100100725830",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_SIDE_RELIQUARY.",
	},
	SC_CHUNK_SKY_TREE_GROVE__AETHER_SURGE = {
		AssetId = "rbxassetid://112638454716432",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_SKY_TREE_GROVE.",
	},
	SC_CHUNK_SKY_TREE_GROVE__LOCKDOWN = {
		AssetId = "rbxassetid://100636993423666",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_SKY_TREE_GROVE.",
	},
	SC_CHUNK_SKY_TREE_GROVE__RECLAIMED = {
		AssetId = "rbxassetid://104240641264009",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_SKY_TREE_GROVE.",
	},
	SC_CHUNK_SKY_TREE_GROVE__RIME = {
		AssetId = "rbxassetid://134988125939152",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_SKY_TREE_GROVE.",
	},
	SC_CHUNK_SKY_TREE_GROVE__SIEGE = {
		AssetId = "rbxassetid://138020776802541",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_SKY_TREE_GROVE.",
	},
	SC_CHUNK_SKY_TREE_GROVE__STORMHAWK = {
		AssetId = "rbxassetid://127835801142631",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_SKY_TREE_GROVE.",
	},
	SC_CHUNK_SKY_TREE_GROVE__UNMOORING = {
		AssetId = "rbxassetid://135303029364364",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_SKY_TREE_GROVE.",
	},
	SC_CHUNK_SPIRE_COURT__AETHER_SURGE = {
		AssetId = "rbxassetid://89265334582154",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_SPIRE_COURT.",
	},
	SC_CHUNK_SPIRE_COURT__LOCKDOWN = {
		AssetId = "rbxassetid://82892054248402",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_SPIRE_COURT.",
	},
	SC_CHUNK_SPIRE_COURT__RECLAIMED = {
		AssetId = "rbxassetid://140665278712026",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_SPIRE_COURT.",
	},
	SC_CHUNK_SPIRE_COURT__RIME = {
		AssetId = "rbxassetid://94437565042747",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_SPIRE_COURT.",
	},
	SC_CHUNK_SPIRE_COURT__SIEGE = {
		AssetId = "rbxassetid://125345138435771",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_SPIRE_COURT.",
	},
	SC_CHUNK_SPIRE_COURT__STORMHAWK = {
		AssetId = "rbxassetid://117561876397405",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_SPIRE_COURT.",
	},
	SC_CHUNK_SPIRE_COURT__UNMOORING = {
		AssetId = "rbxassetid://74790753021375",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_SPIRE_COURT.",
	},
	SC_CHUNK_SPIRE_COURT_B__AETHER_SURGE = {
		AssetId = "rbxassetid://90478200617352",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_SPIRE_COURT_B.",
	},
	SC_CHUNK_SPIRE_COURT_B__LOCKDOWN = {
		AssetId = "rbxassetid://112458057882031",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_SPIRE_COURT_B.",
	},
	SC_CHUNK_SPIRE_COURT_B__RECLAIMED = {
		AssetId = "rbxassetid://70536257060843",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_SPIRE_COURT_B.",
	},
	SC_CHUNK_SPIRE_COURT_B__RIME = {
		AssetId = "rbxassetid://130738906989597",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_SPIRE_COURT_B.",
	},
	SC_CHUNK_SPIRE_COURT_B__SIEGE = {
		AssetId = "rbxassetid://108960083333561",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_SPIRE_COURT_B.",
	},
	SC_CHUNK_SPIRE_COURT_B__STORMHAWK = {
		AssetId = "rbxassetid://110361958428962",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_SPIRE_COURT_B.",
	},
	SC_CHUNK_SPIRE_COURT_B__UNMOORING = {
		AssetId = "rbxassetid://82196381299312",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_SPIRE_COURT_B.",
	},
	SC_CHUNK_TURBINE_HALL__AETHER_SURGE = {
		AssetId = "rbxassetid://78837441306875",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_TURBINE_HALL.",
	},
	SC_CHUNK_TURBINE_HALL__LOCKDOWN = {
		AssetId = "rbxassetid://83732994702325",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_TURBINE_HALL.",
	},
	SC_CHUNK_TURBINE_HALL__RECLAIMED = {
		AssetId = "rbxassetid://137570926986741",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_TURBINE_HALL.",
	},
	SC_CHUNK_TURBINE_HALL__RIME = {
		AssetId = "rbxassetid://115273396577042",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_TURBINE_HALL.",
	},
	SC_CHUNK_TURBINE_HALL__SIEGE = {
		AssetId = "rbxassetid://80294534881116",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_TURBINE_HALL.",
	},
	SC_CHUNK_TURBINE_HALL__STORMHAWK = {
		AssetId = "rbxassetid://75810266658885",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_TURBINE_HALL.",
	},
	SC_CHUNK_TURBINE_HALL__UNMOORING = {
		AssetId = "rbxassetid://117768069605318",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_TURBINE_HALL.",
	},
	SC_CHUNK_VAULT_TURN__AETHER_SURGE = {
		AssetId = "rbxassetid://95293931515413",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_VAULT_TURN.",
	},
	SC_CHUNK_VAULT_TURN__LOCKDOWN = {
		AssetId = "rbxassetid://99221823643505",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_VAULT_TURN.",
	},
	SC_CHUNK_VAULT_TURN__RECLAIMED = {
		AssetId = "rbxassetid://90475224464701",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_VAULT_TURN.",
	},
	SC_CHUNK_VAULT_TURN__RIME = {
		AssetId = "rbxassetid://125746049145778",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_VAULT_TURN.",
	},
	SC_CHUNK_VAULT_TURN__SIEGE = {
		AssetId = "rbxassetid://128282719807075",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_VAULT_TURN.",
	},
	SC_CHUNK_VAULT_TURN__STORMHAWK = {
		AssetId = "rbxassetid://73127846632431",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_VAULT_TURN.",
	},
	SC_CHUNK_VAULT_TURN__UNMOORING = {
		AssetId = "rbxassetid://92521933338528",
		Status = "UPLOADED",
		Source = "assets/rbxm/maps/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_VAULT_TURN.",
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
