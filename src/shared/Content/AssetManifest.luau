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

	ES_CHUNK_BACKDROP_DRIFT_ISLES_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://135765585748925",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_BACKDROP_DRIFT_ISLES_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://70528313904460",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_CAP_BROKEN_BRIDGE_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://88146335649478",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_CAP_BROKEN_BRIDGE_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://111613558925277",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_CAP_FALLS_LEDGE_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://118708650395810",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_CAP_FALLS_LEDGE_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://121607192897792",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_CAP_FALLS_LEDGE_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://111939748711578",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_CAP_OVERLOOK_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://137997136606440",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_CAP_OVERLOOK_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://92811690182374",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_CAP_SEALED_SHRINE_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://83425914375613",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_CAP_SEALED_SHRINE_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://130734588259026",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_CONVERGENCE_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://105133942007707",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_CONVERGENCE_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://102123413309127",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_CONVERGENCE_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://70490058234248",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_CRYSTAL_HOLLOW_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://99064241274688",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_CRYSTAL_HOLLOW_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://93643291030109",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://71236066007435",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_DEBRIS = {
		AssetId = "rbxassetid://112421974698712",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_EDGE1 = {
		AssetId = "rbxassetid://138418501825117",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_EDGE10 = {
		AssetId = "rbxassetid://125095426966308",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_EDGE11 = {
		AssetId = "rbxassetid://124471561003789",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_EDGE12 = {
		AssetId = "rbxassetid://123547321459190",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_EDGE2 = {
		AssetId = "rbxassetid://73702041523046",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_EDGE3 = {
		AssetId = "rbxassetid://85412737368025",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_EDGE4 = {
		AssetId = "rbxassetid://87977338740616",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_EDGE5 = {
		AssetId = "rbxassetid://116056592838193",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_EDGE6 = {
		AssetId = "rbxassetid://103070043628056",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_EDGE7 = {
		AssetId = "rbxassetid://79316903501075",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_EDGE8 = {
		AssetId = "rbxassetid://130806143853897",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_EDGE9 = {
		AssetId = "rbxassetid://125988454454713",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_FRAGGEM1 = {
		AssetId = "rbxassetid://78087733612290",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_FRAGGEM2 = {
		AssetId = "rbxassetid://76356483886485",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_FRAGGEM3 = {
		AssetId = "rbxassetid://81891788273647",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_FRAGGEM4 = {
		AssetId = "rbxassetid://110258257660631",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_FRAGGEM5 = {
		AssetId = "rbxassetid://116099551627224",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_FRAGGEM6 = {
		AssetId = "rbxassetid://101194904108863",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_FRAGGEM7 = {
		AssetId = "rbxassetid://135967946227512",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_FRAGROCK1 = {
		AssetId = "rbxassetid://86986100640607",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_FRAGROCK2 = {
		AssetId = "rbxassetid://100142242307333",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_FRAGROCK3 = {
		AssetId = "rbxassetid://130046064191098",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_FRAGROCK4 = {
		AssetId = "rbxassetid://134198349280397",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_FRAGROCK5 = {
		AssetId = "rbxassetid://139334608346397",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_FRAGROCK6 = {
		AssetId = "rbxassetid://116249036385222",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_FRAGROCK7 = {
		AssetId = "rbxassetid://140415515643318",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_LIGHTANCHOR = {
		AssetId = "rbxassetid://137797232883452",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_RIFTCORE = {
		AssetId = "rbxassetid://99184151286072",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_RIFTHALO = {
		AssetId = "rbxassetid://106914177008914",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_RIFTMID = {
		AssetId = "rbxassetid://99751927353297",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_SCAR = {
		AssetId = "rbxassetid://129887104874350",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_PORTAL_SCARGLOW = {
		AssetId = "rbxassetid://135753272666710",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ENTRY_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://91506910101176",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_FALLEN_COLONNADE_ARCH_DETAIL_01 = {
		AssetId = "rbxassetid://117065110635586",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_FALLEN_COLONNADE_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://97704501136009",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_FALLEN_COLONNADE_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://112348808402597",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_FALLEN_COLONNADE_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://82194363076862",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_FORK_THREE_TREES_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://102515812326768",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_FORK_THREE_TREES_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://102407492997906",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_FORK_TWIN_SPAN_ARCH_DETAIL_01 = {
		AssetId = "rbxassetid://82348241131188",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_FORK_TWIN_SPAN_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://121268796061541",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_FORK_TWIN_SPAN_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://131273761834567",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_FORK_TWIN_SPAN_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://97957097686443",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_FORK_WAYSHRINE_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://75528169550214",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_FORK_WAYSHRINE_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://85106320708640",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_MEADOW_OF_BLOOMS_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://139951938287103",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_MEADOW_OF_BLOOMS_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://96276251147540",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_MINIBOSS_RELIQUARY_COURT_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://85324500940780",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_MINIBOSS_RELIQUARY_COURT_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://77057204200027",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_MINIBOSS_RELIQUARY_COURT_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://103976518453128",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_MINIBOSS_WAYSTONE_RING_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://140556000569139",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_MINIBOSS_WAYSTONE_RING_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://116246937594731",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_MINIBOSS_WAYSTONE_RING_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://131291335599059",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_MIRROR_POOL_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://117007917643367",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_MIRROR_POOL_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://89311451407922",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_MIRROR_POOL_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://112206204948726",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_BEND_EAST_ASCENT_ARCH_DETAIL_01 = {
		AssetId = "rbxassetid://111029464411144",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_BEND_EAST_ASCENT_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://125770326693045",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_BEND_EAST_ASCENT_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://81565237285947",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_BEND_EAST_ASCENT_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://123736481094927",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_BEND_EAST_GROVE_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://84884193559761",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_BEND_EAST_GROVE_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://98969172655638",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_BEND_WEST_FALLS_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://128348537979325",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_BEND_WEST_FALLS_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://86661060068524",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_BEND_WEST_FALLS_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://84394409716959",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_BEND_WEST_SHRINE_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://85410397961157",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_BEND_WEST_SHRINE_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://103820631855542",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_BEND_WEST_SHRINE_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://115081192513201",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_GROVE_ISLE_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://90261454552124",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_GROVE_ISLE_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://72981229059282",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_PLANK_CROSSING_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://77867256272375",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_PLANK_CROSSING_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://138247471014401",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_PLANK_CROSSING_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://99873674508530",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_SKYSTAIR_DOWN_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://116033224291796",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_SKYSTAIR_DOWN_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://128312742251011",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_SKYSTAIR_UP_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://135961117707912",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_PATH_SKYSTAIR_UP_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://130370103198507",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ROOTED_HOLLOW_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://73332860711344",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_ROOTED_HOLLOW_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://75056362085552",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SANCTUM_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://101323333838519",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SANCTUM_CURVED_CHAIR_01 = {
		AssetId = "rbxassetid://95637268102368",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SANCTUM_DOOR_DETAIL_01 = {
		AssetId = "rbxassetid://79763764039627",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SANCTUM_ENTRY_WALL_DETAIL_01 = {
		AssetId = "rbxassetid://131094276769902",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SANCTUM_FACADE_DETAIL_01 = {
		AssetId = "rbxassetid://96478082913008",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SANCTUM_FLOOR_DETAIL_01 = {
		AssetId = "rbxassetid://140424867922619",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SANCTUM_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://130242443891834",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SANCTUM_TEMPLE_01_ARCH_DETAIL_01 = {
		AssetId = "rbxassetid://105734946818196",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SANCTUM_TEMPLE_01_PART_02 = {
		AssetId = "rbxassetid://120875703428291",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SANCTUM_TEMPLE_01_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://99454221912085",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SANCTUM_TEMPLE_01_STRUCTURE_TRIM_01_PART_02 = {
		AssetId = "rbxassetid://77177827353032",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SANCTUM_THRONE_DETAIL_01 = {
		AssetId = "rbxassetid://101377721829884",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SANCTUM_THRONE_INLAY_01 = {
		AssetId = "rbxassetid://115400878334296",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SANCTUM_WINDOW_DETAIL_01 = {
		AssetId = "rbxassetid://71596693256562",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_MINIBOSS_ROOM_CEILING_MURALS_01 = {
		AssetId = "rbxassetid://81037785391467",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_MINIBOSS_ROOM_DETAIL_01 = {
		AssetId = "rbxassetid://103998190342515",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_MINIBOSS_ROOM_FLOOR_DETAIL_01 = {
		AssetId = "rbxassetid://123118618486359",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_MINIBOSS_ROOM_ROOF_01 = {
		AssetId = "rbxassetid://95296323659590",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_MINIBOSS_ROOM_SHELL_01 = {
		AssetId = "rbxassetid://119744497269567",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_MINIBOSS_ROOM_SUPPORTS_01 = {
		AssetId = "rbxassetid://70644894512649",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_OF_WINDS_ARCH_DETAIL_01 = {
		AssetId = "rbxassetid://137767525821592",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_OF_WINDS_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://104378833434421",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_OF_WINDS_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://114208656415475",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_OF_WINDS_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://105804432642424",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_RETURN_DARK_BACKING_01 = {
		AssetId = "rbxassetid://128948623375697",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_RETURN_WALL_MASK_01 = {
		AssetId = "rbxassetid://138911488721326",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_VAULT_ALCOVE_01 = {
		AssetId = "rbxassetid://136755771778544",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_VAULT_ALCOVE_DETAIL_01 = {
		AssetId = "rbxassetid://131490639499142",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_VAULT_CHEST_DETAIL_01 = {
		AssetId = "rbxassetid://119586283859227",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SHRINE_VAULT_THRESHOLD_TRIM_01 = {
		AssetId = "rbxassetid://70935599253764",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SIDE_CRYSTAL_GROTTO_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://81255498634833",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SIDE_CRYSTAL_GROTTO_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://78520232637174",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SIDE_HERMIT_GROVE_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://112649258180361",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SIDE_HERMIT_GROVE_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://89928114413238",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SIDE_RELIC_ALTAR_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://127597653481088",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SIDE_RELIC_ALTAR_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://104654943521341",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SKY_AQUEDUCT_ARCH_DETAIL_01 = {
		AssetId = "rbxassetid://85786331762309",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SKY_AQUEDUCT_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://135116308951740",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SKY_AQUEDUCT_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://138825166725088",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SKY_AQUEDUCT_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://112845237041140",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SKY_OBSERVATORY_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://84003027497050",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SKY_OBSERVATORY_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://75263646034022",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SKY_OBSERVATORY_PART_02 = {
		AssetId = "rbxassetid://81869172401514",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SKY_OBSERVATORY_PART_03 = {
		AssetId = "rbxassetid://95436518628917",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SKY_OBSERVATORY_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://76602139270544",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_SKY_OBSERVATORY_STRUCTURE_TRIM_01_PART_02 = {
		AssetId = "rbxassetid://71751480626787",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_TEMPLE_GATE_A_ARCH_DETAIL_01 = {
		AssetId = "rbxassetid://109151153210791",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_TEMPLE_GATE_A_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://128961464510721",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_TEMPLE_GATE_A_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://114526065238133",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_TEMPLE_GATE_A_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://78945201738119",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_TEMPLE_GATE_B_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://104335787501439",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_TEMPLE_GATE_B_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://113470406856739",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_TEMPLE_GATE_B_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://115604297843358",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_TERRACED_GARDENS_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://95503489621824",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_TERRACED_GARDENS_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://127645157535460",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_TERRACED_GARDENS_STAIR_DETAIL_01 = {
		AssetId = "rbxassetid://131604699736134",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_TWIN_ISLES_CONNECTOR_KEEL_01 = {
		AssetId = "rbxassetid://115101779700791",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_TWIN_ISLES_FLOOR_TRIM_01 = {
		AssetId = "rbxassetid://131574176811278",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},
	ES_CHUNK_TWIN_ISLES_STRUCTURE_TRIM_01 = {
		AssetId = "rbxassetid://120407150858391",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
	},

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
	-- Verdant Valley base kit, 30 pieces. GENERATED by export_verdant_valley_kit.py;
	-- PLACEHOLDER draws the blockout until the piece is uploaded (re-run with --ids).
	VV_CHUNK_PATH_SUNWASH_FORK = {
		AssetId = "rbxassetid://124731754576795",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Sunwash Fork. PATH, opens N+E+S. 76.3 studs tall.",
	},
	VV_CHUNK_CUTBANK_FORD = {
		AssetId = "rbxassetid://123576031253680",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Cutbank Ford. COMBAT, opens N+S. 76.2 studs tall.",
	},
	VV_CHUNK_WINDWARD_RIDGE_GATE = {
		AssetId = "rbxassetid://75952327047107",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Windward Ridge. COMBAT, opens E+W. 106.2 studs tall.",
	},
	VV_CHUNK_FORGOTTEN_ORCHARD_GATE = {
		AssetId = "rbxassetid://102899400517887",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Forgotten Orchard. COMBAT, opens S+W. 70.7 studs tall.",
	},
	VV_CHUNK_LONGGRASS_MEADOW = {
		AssetId = "rbxassetid://71382604371128",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Longgrass Meadow. COMBAT, opens N+S. 68.4 studs tall.",
	},
	VV_CHUNK_SHADED_GROVE = {
		AssetId = "rbxassetid://116737947844320",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Shaded Grove. COMBAT, opens E+W. 77.2 studs tall.",
	},
	VV_CHUNK_FERN_HOLLOW = {
		AssetId = "rbxassetid://74601037115647",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Fern Hollow. COMBAT, opens N+S. 74.6 studs tall.",
	},
	VV_CHUNK_PATH_CLIFF_PASSAGE = {
		AssetId = "rbxassetid://115541060237984",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Cliff Passage. PATH, opens E+W. 99.4 studs tall.",
	},
	VV_CHUNK_STONE_SENTINELS = {
		AssetId = "rbxassetid://120954720998658",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Stone Sentinels. COMBAT, opens N+S. 76.5 studs tall.",
	},
	VV_CHUNK_MOSSBOUND_RUINS = {
		AssetId = "rbxassetid://116035874670415",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Mossbound Ruins. COMBAT, opens E+W. 68.4 studs tall.",
	},
	VV_CHUNK_ANCIENT_OAK = {
		AssetId = "rbxassetid://96205112804955",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Ancient Oak. COMBAT, opens N+S. 93.0 studs tall.",
	},
	VV_CHUNK_WETLAND_POOLS = {
		AssetId = "rbxassetid://104729256567910",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Wetland Pools. COMBAT, opens E+W. 72.2 studs tall.",
	},
	VV_CHUNK_PATH_NARROW_PASS = {
		AssetId = "rbxassetid://94804911449317",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Narrow Pass. PATH, opens N+S. 77.3 studs tall.",
	},
	VV_CHUNK_BLOSSOM_TERRACE = {
		AssetId = "rbxassetid://138655111463512",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Blossom Terrace. COMBAT, opens E+W. 80.4 studs tall.",
	},
	VV_CHUNK_ROCK_GARDEN = {
		AssetId = "rbxassetid://113509390452178",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Rock Garden. COMBAT, opens N+S. 65.4 studs tall.",
	},
	VV_CHUNK_CRYSTAL_SPRING_GATE = {
		AssetId = "rbxassetid://135569709710447",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Crystal Spring. COMBAT, opens E+W. 69.4 studs tall.",
	},
	VV_CHUNK_OVERGROWN_CAUSEWAY_GATE = {
		AssetId = "rbxassetid://83945520781147",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Overgrown Causeway. COMBAT, opens N+S. 72.3 studs tall.",
	},
	VV_CHUNK_HIGH_LEDGE_GATE = {
		AssetId = "rbxassetid://89731913709365",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "High Ledge. COMBAT, opens E+W. 82.3 studs tall.",
	},
	VV_CHUNK_CLIFF_OVERLOOK_GATE = {
		AssetId = "rbxassetid://80817874099038",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Cliff Overlook. COMBAT, opens N+S. 84.1 studs tall.",
	},
	VV_CHUNK_DEEP_CLEARING = {
		AssetId = "rbxassetid://124773291201766",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Deep Clearing. COMBAT, opens N+E+S. 67.5 studs tall.",
	},
	VV_CHUNK_PATH_SPLIT_MEADOW = {
		AssetId = "rbxassetid://104117597912146",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Split Meadow. PATH, opens N+E+W. 70.6 studs tall.",
	},
	VV_CHUNK_MUSHROOM_GLEN = {
		AssetId = "rbxassetid://131086208688466",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Mushroom Glen. COMBAT, opens N+E+S. 72.6 studs tall.",
	},
	VV_CHUNK_PATH_CROSSROADS_COPSE = {
		AssetId = "rbxassetid://126913858532095",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Crossroads Copse. PATH, opens N+E+S+W. 73.0 studs tall.",
	},
	VV_CHUNK_CAP_CAVE_MOUTH = {
		AssetId = "rbxassetid://78030030202123",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Cave Mouth. CAP, opens N. 81.0 studs tall.",
	},
	VV_CHUNK_ENTRY_DAWN_MEADOW = {
		AssetId = "rbxassetid://125747744370561",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Dawn Meadow. ENTRY, opens N. 63.8 studs tall.",
	},
	VV_CHUNK_ENTRY_WOODLAND_REFUGE = {
		AssetId = "rbxassetid://124136837229471",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Woodland Refuge. ENTRY, opens N. 68.8 studs tall.",
	},
	VV_CHUNK_BOSS_SANCTUARY = {
		AssetId = "rbxassetid://122401029379266",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Verdant Valley BOSS Sanctuary. BOSS, opens N. 113.7 studs tall.",
	},
	VV_CHUNK_CAP_TREASURE_HOLLOW = {
		AssetId = "rbxassetid://108998754327688",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Treasure Hollow. CAP, opens N. 69.0 studs tall.",
	},
	VV_CHUNK_CAP_WARDENS_CLEARING = {
		AssetId = "rbxassetid://91428635426624",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Warden's Clearing. CAP, opens N. 72.1 studs tall.",
	},
	VV_CHUNK_SIDE_FORGOTTEN_TRIAL = {
		AssetId = "rbxassetid://82807125317458",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/verdant_valley/VV_STRUCTURE.rbxmx",
		Notes = "Forgotten Trial. SIDE, opens N. 59.0 studs tall.",
	},
	VV_CHUNK_ENTRY = {
		AssetId = "rbxassetid://109348763234820",
		Status = "UPLOADED",
		Source = "legacy first-pass VV entry (file removed 2026-09-25); key kept as a test fixture",
		Notes = "Arrival. One opening, south. 60.4 studs tall.",
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
		AssetId = "rbxassetid://88026123779214",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Octagonal arrival plaza under the Beacon.",
	},
	SC_CHUNK_PATH_STRAIGHT = {
		AssetId = "rbxassetid://129089925999266",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The gatehouse pier: a skyway under an arch between two turrets.",
	},
	SC_CHUNK_PATH_SKYPORT = {
		AssetId = "rbxassetid://94483045189423",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A plank pier with a dock islet off it: hazard pad, crane, a moored skiff.",
	},
	SC_CHUNK_PATH_HOOPS = {
		AssetId = "rbxassetid://110348035119895",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A bare glass-floored span through three floating rings, between two satellites.",
	},
	SC_CHUNK_PATH_SHATTERED = {
		AssetId = "rbxassetid://135502845057517",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The span is broken: eight floating plates, a stride apart, and the Sundered Spire whose crown hangs over its stump.",
	},
	SC_CHUNK_PATH_AVIARY = {
		AssetId = "rbxassetid://137981780730267",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The path runs through a gilded birdcage dome, birds in and around it.",
	},
	SC_CHUNK_CROSSROADS = {
		AssetId = "rbxassetid://125660529173543",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "THE INTERSECTION.",
	},
	SC_CHUNK_PATH_BEND = {
		AssetId = "rbxassetid://117961282087994",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Turns right round the Spired Keep.",
	},
	SC_CHUNK_PATH_BEND_WEST = {
		AssetId = "rbxassetid://76613732448064",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Turns left on a dark engine-deck, the lighthouse on its own islet.",
	},
	SC_CHUNK_VAULT_TURN = {
		AssetId = "rbxassetid://89917125807653",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The treasury, passed THROUGH on a right turn.",
	},
	SC_CHUNK_AETHER_SPRINGS = {
		AssetId = "rbxassetid://126072084633109",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Terraced pools and the Cascade Tower, water falling off the east rim; turns left.",
	},
	SC_CHUNK_GARDEN_TERRACE = {
		AssetId = "rbxassetid://82489694760900",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The hanging gardens: three islets, the Sky Tree, a pool, a gazebo.",
	},
	SC_CHUNK_OBSERVATORY = {
		AssetId = "rbxassetid://129391704093522",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A night-dark deck of stars: dome and mast, an orrery, dishes on a raised deck.",
	},
	SC_CHUNK_ARMORY = {
		AssetId = "rbxassetid://112478409531568",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A slate training yard and a barracks islet, under the banner mast.",
	},
	SC_CHUNK_ARCHIVE = {
		AssetId = "rbxassetid://140031125559328",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A roofed hall of shelves and ribbed vaults, floating tomes, the clock tower.",
	},
	SC_CHUNK_SPIRE_COURT = {
		AssetId = "rbxassetid://92301933968079",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Gate-court: the Sky Fountain and the Ascent Gate.",
	},
	SC_CHUNK_SPIRE_COURT_B = {
		AssetId = "rbxassetid://129951400055967",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Gate-court, rare: the Hall of Winds and its Moon Gate.",
	},
	SC_CHUNK_SIDE_LOOKOUT = {
		AssetId = "rbxassetid://80071796065848",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The world's SIDE pocket: a lookout and a loot cache, hung off a spare socket (a crossroads branch, typically) when IncludeSide is on.",
	},
	SC_CHUNK_BOSS_CLEARING = {
		AssetId = "rbxassetid://109965904727909",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The Crown Spire arena.",
	},
	SC_CHUNK_CAP_CRUMBLING = {
		AssetId = "rbxassetid://117766670542193",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A CAP: the skyway breaks off, its far half falling away, the Fallen Tower leaning over the gap.",
	},
	SC_CHUNK_CAP_OVERLOOK = {
		AssetId = "rbxassetid://78182513014315",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A CAP: the skyway ends at a railed round overlook with a light obelisk and telescopes.",
	},
	SC_CHUNK_CAP_SEALED_GATE = {
		AssetId = "rbxassetid://116297783045278",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A CAP: a citadel gate that stays shut.",
	},
	SC_CHUNK_PATH_COLONNADE = {
		AssetId = "rbxassetid://82969550619674",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The colonnade walk.",
	},
	SC_CHUNK_PATH_LONG_SPAN = {
		AssetId = "rbxassetid://111164295397853",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A long bare span over the drop.",
	},
	SC_CHUNK_PATH_LANTERN_ROW = {
		AssetId = "rbxassetid://128410235010256",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The lantern row.",
	},
	SC_CHUNK_PATH_TOWER_BEND = {
		AssetId = "rbxassetid://132459811428668",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Turns left round the watchtower.",
	},
	SC_CHUNK_PATH_TEE = {
		AssetId = "rbxassetid://82848937468291",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The tee junction.",
	},
	SC_CHUNK_PARADE_GROUND = {
		AssetId = "rbxassetid://130221894470618",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The parade ground.",
	},
	SC_CHUNK_TURBINE_HALL = {
		AssetId = "rbxassetid://92367216899210",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The turbine hall.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT = {
		AssetId = "rbxassetid://128031908839397",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "Lighthouse point.",
	},
	SC_CHUNK_SKY_TREE_GROVE = {
		AssetId = "rbxassetid://116496516286575",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The sky tree grove.",
	},
	SC_CHUNK_DOCKSIDE = {
		AssetId = "rbxassetid://116550456955440",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The dockside yard.",
	},
	SC_CHUNK_SIDE_CHAPEL = {
		AssetId = "rbxassetid://87806779307836",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The chapel of winds.",
	},
	SC_CHUNK_SIDE_GARDEN = {
		AssetId = "rbxassetid://110451357110362",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "A hanging garden.",
	},
	SC_CHUNK_SIDE_RELIQUARY = {
		AssetId = "rbxassetid://123020266926627",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The reliquary.",
	},
	SC_CHUNK_PRISM_ARENA = {
		AssetId = "rbxassetid://94560926909219",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_STRUCTURE.rbxmx",
		Notes = "The Prism Arena.",
	},
	-- Per-atmosphere recolours (same geometry): ChunkLoader swaps one in when the run's atmosphere matches.
	SC_CHUNK_AETHER_SPRINGS__AETHER_SURGE = {
		AssetId = "rbxassetid://85256347634952",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_AETHER_SPRINGS.",
	},
	SC_CHUNK_AETHER_SPRINGS__LOCKDOWN = {
		AssetId = "rbxassetid://79490379106751",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_AETHER_SPRINGS.",
	},
	SC_CHUNK_AETHER_SPRINGS__RECLAIMED = {
		AssetId = "rbxassetid://84896067723282",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_AETHER_SPRINGS.",
	},
	SC_CHUNK_AETHER_SPRINGS__RIME = {
		AssetId = "rbxassetid://84986497916679",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_AETHER_SPRINGS.",
	},
	SC_CHUNK_AETHER_SPRINGS__SIEGE = {
		AssetId = "rbxassetid://96859726487613",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_AETHER_SPRINGS.",
	},
	SC_CHUNK_AETHER_SPRINGS__STORMHAWK = {
		AssetId = "rbxassetid://84859272794416",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_AETHER_SPRINGS.",
	},
	SC_CHUNK_AETHER_SPRINGS__UNMOORING = {
		AssetId = "rbxassetid://117556244923312",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_AETHER_SPRINGS.",
	},
	SC_CHUNK_ARCHIVE__AETHER_SURGE = {
		AssetId = "rbxassetid://126008114148568",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_ARCHIVE.",
	},
	SC_CHUNK_ARCHIVE__LOCKDOWN = {
		AssetId = "rbxassetid://71062693141403",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_ARCHIVE.",
	},
	SC_CHUNK_ARCHIVE__RECLAIMED = {
		AssetId = "rbxassetid://140231235520352",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_ARCHIVE.",
	},
	SC_CHUNK_ARCHIVE__RIME = {
		AssetId = "rbxassetid://122125045409097",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_ARCHIVE.",
	},
	SC_CHUNK_ARCHIVE__SIEGE = {
		AssetId = "rbxassetid://96773066771606",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_ARCHIVE.",
	},
	SC_CHUNK_ARCHIVE__STORMHAWK = {
		AssetId = "rbxassetid://100929137900939",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_ARCHIVE.",
	},
	SC_CHUNK_ARCHIVE__UNMOORING = {
		AssetId = "rbxassetid://98955632905246",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_ARCHIVE.",
	},
	SC_CHUNK_ARMORY__AETHER_SURGE = {
		AssetId = "rbxassetid://105058331340493",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_ARMORY.",
	},
	SC_CHUNK_ARMORY__LOCKDOWN = {
		AssetId = "rbxassetid://99644176793503",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_ARMORY.",
	},
	SC_CHUNK_ARMORY__RECLAIMED = {
		AssetId = "rbxassetid://109950196365218",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_ARMORY.",
	},
	SC_CHUNK_ARMORY__RIME = {
		AssetId = "rbxassetid://101240207210958",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_ARMORY.",
	},
	SC_CHUNK_ARMORY__SIEGE = {
		AssetId = "rbxassetid://107126475968660",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_ARMORY.",
	},
	SC_CHUNK_ARMORY__STORMHAWK = {
		AssetId = "rbxassetid://110765238552346",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_ARMORY.",
	},
	SC_CHUNK_ARMORY__UNMOORING = {
		AssetId = "rbxassetid://129282978400761",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_ARMORY.",
	},
	SC_CHUNK_BOSS_CLEARING__AETHER_SURGE = {
		AssetId = "rbxassetid://80024888161853",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_BOSS_CLEARING.",
	},
	SC_CHUNK_BOSS_CLEARING__LOCKDOWN = {
		AssetId = "rbxassetid://101586425102506",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_BOSS_CLEARING.",
	},
	SC_CHUNK_BOSS_CLEARING__RECLAIMED = {
		AssetId = "rbxassetid://115983076345655",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_BOSS_CLEARING.",
	},
	SC_CHUNK_BOSS_CLEARING__RIME = {
		AssetId = "rbxassetid://90704163974544",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_BOSS_CLEARING.",
	},
	SC_CHUNK_BOSS_CLEARING__SIEGE = {
		AssetId = "rbxassetid://107615028437128",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_BOSS_CLEARING.",
	},
	SC_CHUNK_BOSS_CLEARING__STORMHAWK = {
		AssetId = "rbxassetid://115451678854397",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_BOSS_CLEARING.",
	},
	SC_CHUNK_BOSS_CLEARING__UNMOORING = {
		AssetId = "rbxassetid://118445198026263",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_BOSS_CLEARING.",
	},
	SC_CHUNK_CAP_CRUMBLING__AETHER_SURGE = {
		AssetId = "rbxassetid://131701777057973",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_CAP_CRUMBLING.",
	},
	SC_CHUNK_CAP_CRUMBLING__LOCKDOWN = {
		AssetId = "rbxassetid://96211561532910",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_CAP_CRUMBLING.",
	},
	SC_CHUNK_CAP_CRUMBLING__RECLAIMED = {
		AssetId = "rbxassetid://114280628481696",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_CAP_CRUMBLING.",
	},
	SC_CHUNK_CAP_CRUMBLING__RIME = {
		AssetId = "rbxassetid://89709486629450",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_CAP_CRUMBLING.",
	},
	SC_CHUNK_CAP_CRUMBLING__SIEGE = {
		AssetId = "rbxassetid://76801669132938",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_CAP_CRUMBLING.",
	},
	SC_CHUNK_CAP_CRUMBLING__STORMHAWK = {
		AssetId = "rbxassetid://108404039634127",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_CAP_CRUMBLING.",
	},
	SC_CHUNK_CAP_CRUMBLING__UNMOORING = {
		AssetId = "rbxassetid://88128254984446",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_CAP_CRUMBLING.",
	},
	SC_CHUNK_CAP_OVERLOOK__AETHER_SURGE = {
		AssetId = "rbxassetid://124324692262001",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_CAP_OVERLOOK.",
	},
	SC_CHUNK_CAP_OVERLOOK__LOCKDOWN = {
		AssetId = "rbxassetid://100166919128256",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_CAP_OVERLOOK.",
	},
	SC_CHUNK_CAP_OVERLOOK__RECLAIMED = {
		AssetId = "rbxassetid://91777705770382",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_CAP_OVERLOOK.",
	},
	SC_CHUNK_CAP_OVERLOOK__RIME = {
		AssetId = "rbxassetid://125597742476623",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_CAP_OVERLOOK.",
	},
	SC_CHUNK_CAP_OVERLOOK__SIEGE = {
		AssetId = "rbxassetid://138796752330199",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_CAP_OVERLOOK.",
	},
	SC_CHUNK_CAP_OVERLOOK__STORMHAWK = {
		AssetId = "rbxassetid://113319551372059",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_CAP_OVERLOOK.",
	},
	SC_CHUNK_CAP_OVERLOOK__UNMOORING = {
		AssetId = "rbxassetid://116080474248216",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_CAP_OVERLOOK.",
	},
	SC_CHUNK_CAP_SEALED_GATE__AETHER_SURGE = {
		AssetId = "rbxassetid://126447279466013",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_CAP_SEALED_GATE.",
	},
	SC_CHUNK_CAP_SEALED_GATE__LOCKDOWN = {
		AssetId = "rbxassetid://106963532636428",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_CAP_SEALED_GATE.",
	},
	SC_CHUNK_CAP_SEALED_GATE__RECLAIMED = {
		AssetId = "rbxassetid://73976749295498",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_CAP_SEALED_GATE.",
	},
	SC_CHUNK_CAP_SEALED_GATE__RIME = {
		AssetId = "rbxassetid://96536051559808",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_CAP_SEALED_GATE.",
	},
	SC_CHUNK_CAP_SEALED_GATE__SIEGE = {
		AssetId = "rbxassetid://111992536585766",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_CAP_SEALED_GATE.",
	},
	SC_CHUNK_CAP_SEALED_GATE__STORMHAWK = {
		AssetId = "rbxassetid://93166628851646",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_CAP_SEALED_GATE.",
	},
	SC_CHUNK_CAP_SEALED_GATE__UNMOORING = {
		AssetId = "rbxassetid://125490415550637",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_CAP_SEALED_GATE.",
	},
	SC_CHUNK_CROSSROADS__AETHER_SURGE = {
		AssetId = "rbxassetid://113766136352146",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_CROSSROADS.",
	},
	SC_CHUNK_CROSSROADS__LOCKDOWN = {
		AssetId = "rbxassetid://71432022437918",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_CROSSROADS.",
	},
	SC_CHUNK_CROSSROADS__RECLAIMED = {
		AssetId = "rbxassetid://72725048187819",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_CROSSROADS.",
	},
	SC_CHUNK_CROSSROADS__RIME = {
		AssetId = "rbxassetid://76185210837668",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_CROSSROADS.",
	},
	SC_CHUNK_CROSSROADS__SIEGE = {
		AssetId = "rbxassetid://136757889921792",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_CROSSROADS.",
	},
	SC_CHUNK_CROSSROADS__STORMHAWK = {
		AssetId = "rbxassetid://87431596636623",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_CROSSROADS.",
	},
	SC_CHUNK_CROSSROADS__UNMOORING = {
		AssetId = "rbxassetid://138034338210373",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_CROSSROADS.",
	},
	SC_CHUNK_DOCKSIDE__AETHER_SURGE = {
		AssetId = "rbxassetid://93719693090559",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_DOCKSIDE.",
	},
	SC_CHUNK_DOCKSIDE__LOCKDOWN = {
		AssetId = "rbxassetid://105719386381864",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_DOCKSIDE.",
	},
	SC_CHUNK_DOCKSIDE__RECLAIMED = {
		AssetId = "rbxassetid://87311791291710",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_DOCKSIDE.",
	},
	SC_CHUNK_DOCKSIDE__RIME = {
		AssetId = "rbxassetid://133480414332247",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_DOCKSIDE.",
	},
	SC_CHUNK_DOCKSIDE__SIEGE = {
		AssetId = "rbxassetid://102077356220860",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_DOCKSIDE.",
	},
	SC_CHUNK_DOCKSIDE__STORMHAWK = {
		AssetId = "rbxassetid://102215105447597",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_DOCKSIDE.",
	},
	SC_CHUNK_DOCKSIDE__UNMOORING = {
		AssetId = "rbxassetid://100321680487018",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_DOCKSIDE.",
	},
	SC_CHUNK_ENTRY__AETHER_SURGE = {
		AssetId = "rbxassetid://101566827889964",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_ENTRY.",
	},
	SC_CHUNK_ENTRY__LOCKDOWN = {
		AssetId = "rbxassetid://81524862501266",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_ENTRY.",
	},
	SC_CHUNK_ENTRY__RECLAIMED = {
		AssetId = "rbxassetid://91268210909599",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_ENTRY.",
	},
	SC_CHUNK_ENTRY__RIME = {
		AssetId = "rbxassetid://83621043509483",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_ENTRY.",
	},
	SC_CHUNK_ENTRY__SIEGE = {
		AssetId = "rbxassetid://136163840685170",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_ENTRY.",
	},
	SC_CHUNK_ENTRY__STORMHAWK = {
		AssetId = "rbxassetid://87497585914759",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_ENTRY.",
	},
	SC_CHUNK_ENTRY__UNMOORING = {
		AssetId = "rbxassetid://133380290785530",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_ENTRY.",
	},
	SC_CHUNK_GARDEN_TERRACE__AETHER_SURGE = {
		AssetId = "rbxassetid://94327121815531",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_GARDEN_TERRACE.",
	},
	SC_CHUNK_GARDEN_TERRACE__LOCKDOWN = {
		AssetId = "rbxassetid://123604873756823",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_GARDEN_TERRACE.",
	},
	SC_CHUNK_GARDEN_TERRACE__RECLAIMED = {
		AssetId = "rbxassetid://133451889567745",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_GARDEN_TERRACE.",
	},
	SC_CHUNK_GARDEN_TERRACE__RIME = {
		AssetId = "rbxassetid://117754056988614",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_GARDEN_TERRACE.",
	},
	SC_CHUNK_GARDEN_TERRACE__SIEGE = {
		AssetId = "rbxassetid://112894304043033",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_GARDEN_TERRACE.",
	},
	SC_CHUNK_GARDEN_TERRACE__STORMHAWK = {
		AssetId = "rbxassetid://105360416916209",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_GARDEN_TERRACE.",
	},
	SC_CHUNK_GARDEN_TERRACE__UNMOORING = {
		AssetId = "rbxassetid://113104471013464",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_GARDEN_TERRACE.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT__AETHER_SURGE = {
		AssetId = "rbxassetid://98733100523409",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_LIGHTHOUSE_POINT.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT__LOCKDOWN = {
		AssetId = "rbxassetid://120288147741221",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_LIGHTHOUSE_POINT.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT__RECLAIMED = {
		AssetId = "rbxassetid://87507318384663",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_LIGHTHOUSE_POINT.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT__RIME = {
		AssetId = "rbxassetid://86958357930093",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_LIGHTHOUSE_POINT.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT__SIEGE = {
		AssetId = "rbxassetid://119114110565956",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_LIGHTHOUSE_POINT.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT__STORMHAWK = {
		AssetId = "rbxassetid://123584191090457",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_LIGHTHOUSE_POINT.",
	},
	SC_CHUNK_LIGHTHOUSE_POINT__UNMOORING = {
		AssetId = "rbxassetid://107978290934977",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_LIGHTHOUSE_POINT.",
	},
	SC_CHUNK_OBSERVATORY__AETHER_SURGE = {
		AssetId = "rbxassetid://117665068462873",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_OBSERVATORY.",
	},
	SC_CHUNK_OBSERVATORY__LOCKDOWN = {
		AssetId = "rbxassetid://73053319330415",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_OBSERVATORY.",
	},
	SC_CHUNK_OBSERVATORY__RECLAIMED = {
		AssetId = "rbxassetid://82437433680015",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_OBSERVATORY.",
	},
	SC_CHUNK_OBSERVATORY__RIME = {
		AssetId = "rbxassetid://94341732376690",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_OBSERVATORY.",
	},
	SC_CHUNK_OBSERVATORY__SIEGE = {
		AssetId = "rbxassetid://78063603398854",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_OBSERVATORY.",
	},
	SC_CHUNK_OBSERVATORY__STORMHAWK = {
		AssetId = "rbxassetid://79632123187147",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_OBSERVATORY.",
	},
	SC_CHUNK_OBSERVATORY__UNMOORING = {
		AssetId = "rbxassetid://86176285276887",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_OBSERVATORY.",
	},
	SC_CHUNK_PARADE_GROUND__AETHER_SURGE = {
		AssetId = "rbxassetid://82960177814724",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PARADE_GROUND.",
	},
	SC_CHUNK_PARADE_GROUND__LOCKDOWN = {
		AssetId = "rbxassetid://114734596066889",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PARADE_GROUND.",
	},
	SC_CHUNK_PARADE_GROUND__RECLAIMED = {
		AssetId = "rbxassetid://108554603462683",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PARADE_GROUND.",
	},
	SC_CHUNK_PARADE_GROUND__RIME = {
		AssetId = "rbxassetid://136858588861294",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PARADE_GROUND.",
	},
	SC_CHUNK_PARADE_GROUND__SIEGE = {
		AssetId = "rbxassetid://131432199040234",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PARADE_GROUND.",
	},
	SC_CHUNK_PARADE_GROUND__STORMHAWK = {
		AssetId = "rbxassetid://126569158656112",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PARADE_GROUND.",
	},
	SC_CHUNK_PARADE_GROUND__UNMOORING = {
		AssetId = "rbxassetid://82003712435359",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PARADE_GROUND.",
	},
	SC_CHUNK_PATH_AVIARY__AETHER_SURGE = {
		AssetId = "rbxassetid://134646634784304",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_AVIARY.",
	},
	SC_CHUNK_PATH_AVIARY__LOCKDOWN = {
		AssetId = "rbxassetid://82675484044085",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_AVIARY.",
	},
	SC_CHUNK_PATH_AVIARY__RECLAIMED = {
		AssetId = "rbxassetid://101213771934916",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_AVIARY.",
	},
	SC_CHUNK_PATH_AVIARY__RIME = {
		AssetId = "rbxassetid://105582358624373",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_AVIARY.",
	},
	SC_CHUNK_PATH_AVIARY__SIEGE = {
		AssetId = "rbxassetid://125802192615753",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_AVIARY.",
	},
	SC_CHUNK_PATH_AVIARY__STORMHAWK = {
		AssetId = "rbxassetid://83241051315081",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_AVIARY.",
	},
	SC_CHUNK_PATH_AVIARY__UNMOORING = {
		AssetId = "rbxassetid://128726688319733",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_AVIARY.",
	},
	SC_CHUNK_PATH_BEND__AETHER_SURGE = {
		AssetId = "rbxassetid://97587633861324",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_BEND.",
	},
	SC_CHUNK_PATH_BEND__LOCKDOWN = {
		AssetId = "rbxassetid://88920373615137",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_BEND.",
	},
	SC_CHUNK_PATH_BEND__RECLAIMED = {
		AssetId = "rbxassetid://119541346587314",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_BEND.",
	},
	SC_CHUNK_PATH_BEND__RIME = {
		AssetId = "rbxassetid://86607058565034",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_BEND.",
	},
	SC_CHUNK_PATH_BEND__SIEGE = {
		AssetId = "rbxassetid://112783348807994",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_BEND.",
	},
	SC_CHUNK_PATH_BEND__STORMHAWK = {
		AssetId = "rbxassetid://121388332380139",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_BEND.",
	},
	SC_CHUNK_PATH_BEND__UNMOORING = {
		AssetId = "rbxassetid://119459184709468",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_BEND.",
	},
	SC_CHUNK_PATH_BEND_WEST__AETHER_SURGE = {
		AssetId = "rbxassetid://74836537497312",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_BEND_WEST.",
	},
	SC_CHUNK_PATH_BEND_WEST__LOCKDOWN = {
		AssetId = "rbxassetid://114291134716970",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_BEND_WEST.",
	},
	SC_CHUNK_PATH_BEND_WEST__RECLAIMED = {
		AssetId = "rbxassetid://108908718573182",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_BEND_WEST.",
	},
	SC_CHUNK_PATH_BEND_WEST__RIME = {
		AssetId = "rbxassetid://100221343583293",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_BEND_WEST.",
	},
	SC_CHUNK_PATH_BEND_WEST__SIEGE = {
		AssetId = "rbxassetid://113240017860394",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_BEND_WEST.",
	},
	SC_CHUNK_PATH_BEND_WEST__STORMHAWK = {
		AssetId = "rbxassetid://86416147540531",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_BEND_WEST.",
	},
	SC_CHUNK_PATH_BEND_WEST__UNMOORING = {
		AssetId = "rbxassetid://87989024082106",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_BEND_WEST.",
	},
	SC_CHUNK_PATH_COLONNADE__AETHER_SURGE = {
		AssetId = "rbxassetid://80753409947649",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_COLONNADE.",
	},
	SC_CHUNK_PATH_COLONNADE__LOCKDOWN = {
		AssetId = "rbxassetid://94436148408411",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_COLONNADE.",
	},
	SC_CHUNK_PATH_COLONNADE__RECLAIMED = {
		AssetId = "rbxassetid://94862634621836",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_COLONNADE.",
	},
	SC_CHUNK_PATH_COLONNADE__RIME = {
		AssetId = "rbxassetid://78552779288538",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_COLONNADE.",
	},
	SC_CHUNK_PATH_COLONNADE__SIEGE = {
		AssetId = "rbxassetid://80450988647240",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_COLONNADE.",
	},
	SC_CHUNK_PATH_COLONNADE__STORMHAWK = {
		AssetId = "rbxassetid://84089668376702",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_COLONNADE.",
	},
	SC_CHUNK_PATH_COLONNADE__UNMOORING = {
		AssetId = "rbxassetid://86482423024152",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_COLONNADE.",
	},
	SC_CHUNK_PATH_HOOPS__AETHER_SURGE = {
		AssetId = "rbxassetid://123036951171125",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_HOOPS.",
	},
	SC_CHUNK_PATH_HOOPS__LOCKDOWN = {
		AssetId = "rbxassetid://75761630501057",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_HOOPS.",
	},
	SC_CHUNK_PATH_HOOPS__RECLAIMED = {
		AssetId = "rbxassetid://114757600638954",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_HOOPS.",
	},
	SC_CHUNK_PATH_HOOPS__RIME = {
		AssetId = "rbxassetid://133630149550773",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_HOOPS.",
	},
	SC_CHUNK_PATH_HOOPS__SIEGE = {
		AssetId = "rbxassetid://111592383622543",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_HOOPS.",
	},
	SC_CHUNK_PATH_HOOPS__STORMHAWK = {
		AssetId = "rbxassetid://76589211915317",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_HOOPS.",
	},
	SC_CHUNK_PATH_HOOPS__UNMOORING = {
		AssetId = "rbxassetid://126105797902637",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_HOOPS.",
	},
	SC_CHUNK_PATH_LANTERN_ROW__AETHER_SURGE = {
		AssetId = "rbxassetid://73664622313601",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_LANTERN_ROW.",
	},
	SC_CHUNK_PATH_LANTERN_ROW__LOCKDOWN = {
		AssetId = "rbxassetid://131898685613260",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_LANTERN_ROW.",
	},
	SC_CHUNK_PATH_LANTERN_ROW__RECLAIMED = {
		AssetId = "rbxassetid://113092773691237",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_LANTERN_ROW.",
	},
	SC_CHUNK_PATH_LANTERN_ROW__RIME = {
		AssetId = "rbxassetid://87262872823572",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_LANTERN_ROW.",
	},
	SC_CHUNK_PATH_LANTERN_ROW__SIEGE = {
		AssetId = "rbxassetid://114250143604975",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_LANTERN_ROW.",
	},
	SC_CHUNK_PATH_LANTERN_ROW__STORMHAWK = {
		AssetId = "rbxassetid://71658745305913",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_LANTERN_ROW.",
	},
	SC_CHUNK_PATH_LANTERN_ROW__UNMOORING = {
		AssetId = "rbxassetid://129218042947835",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_LANTERN_ROW.",
	},
	SC_CHUNK_PATH_LONG_SPAN__AETHER_SURGE = {
		AssetId = "rbxassetid://133042277838125",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_LONG_SPAN.",
	},
	SC_CHUNK_PATH_LONG_SPAN__LOCKDOWN = {
		AssetId = "rbxassetid://94643886522645",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_LONG_SPAN.",
	},
	SC_CHUNK_PATH_LONG_SPAN__RECLAIMED = {
		AssetId = "rbxassetid://129199697130114",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_LONG_SPAN.",
	},
	SC_CHUNK_PATH_LONG_SPAN__RIME = {
		AssetId = "rbxassetid://99795256583287",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_LONG_SPAN.",
	},
	SC_CHUNK_PATH_LONG_SPAN__SIEGE = {
		AssetId = "rbxassetid://75904592741204",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_LONG_SPAN.",
	},
	SC_CHUNK_PATH_LONG_SPAN__STORMHAWK = {
		AssetId = "rbxassetid://123631860526665",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_LONG_SPAN.",
	},
	SC_CHUNK_PATH_LONG_SPAN__UNMOORING = {
		AssetId = "rbxassetid://76844532666007",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_LONG_SPAN.",
	},
	SC_CHUNK_PATH_SHATTERED__AETHER_SURGE = {
		AssetId = "rbxassetid://112342488382328",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_SHATTERED.",
	},
	SC_CHUNK_PATH_SHATTERED__LOCKDOWN = {
		AssetId = "rbxassetid://116074383292811",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_SHATTERED.",
	},
	SC_CHUNK_PATH_SHATTERED__RECLAIMED = {
		AssetId = "rbxassetid://72222801976615",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_SHATTERED.",
	},
	SC_CHUNK_PATH_SHATTERED__RIME = {
		AssetId = "rbxassetid://115784237910331",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_SHATTERED.",
	},
	SC_CHUNK_PATH_SHATTERED__SIEGE = {
		AssetId = "rbxassetid://76637892907111",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_SHATTERED.",
	},
	SC_CHUNK_PATH_SHATTERED__STORMHAWK = {
		AssetId = "rbxassetid://86913039385546",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_SHATTERED.",
	},
	SC_CHUNK_PATH_SHATTERED__UNMOORING = {
		AssetId = "rbxassetid://101541943338026",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_SHATTERED.",
	},
	SC_CHUNK_PATH_SKYPORT__AETHER_SURGE = {
		AssetId = "rbxassetid://96464088919831",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_SKYPORT.",
	},
	SC_CHUNK_PATH_SKYPORT__LOCKDOWN = {
		AssetId = "rbxassetid://113248998587919",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_SKYPORT.",
	},
	SC_CHUNK_PATH_SKYPORT__RECLAIMED = {
		AssetId = "rbxassetid://114276253469572",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_SKYPORT.",
	},
	SC_CHUNK_PATH_SKYPORT__RIME = {
		AssetId = "rbxassetid://97987025234679",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_SKYPORT.",
	},
	SC_CHUNK_PATH_SKYPORT__SIEGE = {
		AssetId = "rbxassetid://77140556917898",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_SKYPORT.",
	},
	SC_CHUNK_PATH_SKYPORT__STORMHAWK = {
		AssetId = "rbxassetid://124686133101582",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_SKYPORT.",
	},
	SC_CHUNK_PATH_SKYPORT__UNMOORING = {
		AssetId = "rbxassetid://116485374518813",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_SKYPORT.",
	},
	SC_CHUNK_PATH_STRAIGHT__AETHER_SURGE = {
		AssetId = "rbxassetid://94008419939346",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_STRAIGHT.",
	},
	SC_CHUNK_PATH_STRAIGHT__LOCKDOWN = {
		AssetId = "rbxassetid://108887327128885",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_STRAIGHT.",
	},
	SC_CHUNK_PATH_STRAIGHT__RECLAIMED = {
		AssetId = "rbxassetid://125080580721218",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_STRAIGHT.",
	},
	SC_CHUNK_PATH_STRAIGHT__RIME = {
		AssetId = "rbxassetid://107050514609408",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_STRAIGHT.",
	},
	SC_CHUNK_PATH_STRAIGHT__SIEGE = {
		AssetId = "rbxassetid://84552220286568",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_STRAIGHT.",
	},
	SC_CHUNK_PATH_STRAIGHT__STORMHAWK = {
		AssetId = "rbxassetid://80781473572426",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_STRAIGHT.",
	},
	SC_CHUNK_PATH_STRAIGHT__UNMOORING = {
		AssetId = "rbxassetid://104395822823219",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_STRAIGHT.",
	},
	SC_CHUNK_PATH_TEE__AETHER_SURGE = {
		AssetId = "rbxassetid://100753407247624",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_TEE.",
	},
	SC_CHUNK_PATH_TEE__LOCKDOWN = {
		AssetId = "rbxassetid://107324564773854",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_TEE.",
	},
	SC_CHUNK_PATH_TEE__RECLAIMED = {
		AssetId = "rbxassetid://81537684298716",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_TEE.",
	},
	SC_CHUNK_PATH_TEE__RIME = {
		AssetId = "rbxassetid://139881752879469",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_TEE.",
	},
	SC_CHUNK_PATH_TEE__SIEGE = {
		AssetId = "rbxassetid://113641214827333",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_TEE.",
	},
	SC_CHUNK_PATH_TEE__STORMHAWK = {
		AssetId = "rbxassetid://85589804433749",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_TEE.",
	},
	SC_CHUNK_PATH_TEE__UNMOORING = {
		AssetId = "rbxassetid://136376236042152",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_TEE.",
	},
	SC_CHUNK_PATH_TOWER_BEND__AETHER_SURGE = {
		AssetId = "rbxassetid://122294351136130",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PATH_TOWER_BEND.",
	},
	SC_CHUNK_PATH_TOWER_BEND__LOCKDOWN = {
		AssetId = "rbxassetid://74530207342149",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PATH_TOWER_BEND.",
	},
	SC_CHUNK_PATH_TOWER_BEND__RECLAIMED = {
		AssetId = "rbxassetid://83016465964269",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PATH_TOWER_BEND.",
	},
	SC_CHUNK_PATH_TOWER_BEND__RIME = {
		AssetId = "rbxassetid://93622616937361",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PATH_TOWER_BEND.",
	},
	SC_CHUNK_PATH_TOWER_BEND__SIEGE = {
		AssetId = "rbxassetid://81394267338439",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PATH_TOWER_BEND.",
	},
	SC_CHUNK_PATH_TOWER_BEND__STORMHAWK = {
		AssetId = "rbxassetid://136911842474210",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PATH_TOWER_BEND.",
	},
	SC_CHUNK_PATH_TOWER_BEND__UNMOORING = {
		AssetId = "rbxassetid://100829300638407",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PATH_TOWER_BEND.",
	},
	SC_CHUNK_PRISM_ARENA__AETHER_SURGE = {
		AssetId = "rbxassetid://127323891051588",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_PRISM_ARENA.",
	},
	SC_CHUNK_PRISM_ARENA__LOCKDOWN = {
		AssetId = "rbxassetid://138674700795944",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_PRISM_ARENA.",
	},
	SC_CHUNK_PRISM_ARENA__RECLAIMED = {
		AssetId = "rbxassetid://94925757914870",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_PRISM_ARENA.",
	},
	SC_CHUNK_PRISM_ARENA__RIME = {
		AssetId = "rbxassetid://109978837629001",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_PRISM_ARENA.",
	},
	SC_CHUNK_PRISM_ARENA__SIEGE = {
		AssetId = "rbxassetid://79385853649843",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_PRISM_ARENA.",
	},
	SC_CHUNK_PRISM_ARENA__STORMHAWK = {
		AssetId = "rbxassetid://113001153646774",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_PRISM_ARENA.",
	},
	SC_CHUNK_PRISM_ARENA__UNMOORING = {
		AssetId = "rbxassetid://93678175307634",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_PRISM_ARENA.",
	},
	SC_CHUNK_SIDE_CHAPEL__AETHER_SURGE = {
		AssetId = "rbxassetid://110719734550665",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_SIDE_CHAPEL.",
	},
	SC_CHUNK_SIDE_CHAPEL__LOCKDOWN = {
		AssetId = "rbxassetid://87354655299067",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_SIDE_CHAPEL.",
	},
	SC_CHUNK_SIDE_CHAPEL__RECLAIMED = {
		AssetId = "rbxassetid://100707225493072",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_SIDE_CHAPEL.",
	},
	SC_CHUNK_SIDE_CHAPEL__RIME = {
		AssetId = "rbxassetid://129544952910152",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_SIDE_CHAPEL.",
	},
	SC_CHUNK_SIDE_CHAPEL__SIEGE = {
		AssetId = "rbxassetid://93205711025226",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_SIDE_CHAPEL.",
	},
	SC_CHUNK_SIDE_CHAPEL__STORMHAWK = {
		AssetId = "rbxassetid://139827290943387",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_SIDE_CHAPEL.",
	},
	SC_CHUNK_SIDE_CHAPEL__UNMOORING = {
		AssetId = "rbxassetid://107738834486807",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_SIDE_CHAPEL.",
	},
	SC_CHUNK_SIDE_GARDEN__AETHER_SURGE = {
		AssetId = "rbxassetid://129086110757380",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_SIDE_GARDEN.",
	},
	SC_CHUNK_SIDE_GARDEN__LOCKDOWN = {
		AssetId = "rbxassetid://115932424194805",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_SIDE_GARDEN.",
	},
	SC_CHUNK_SIDE_GARDEN__RECLAIMED = {
		AssetId = "rbxassetid://89597896028587",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_SIDE_GARDEN.",
	},
	SC_CHUNK_SIDE_GARDEN__RIME = {
		AssetId = "rbxassetid://88557371897503",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_SIDE_GARDEN.",
	},
	SC_CHUNK_SIDE_GARDEN__SIEGE = {
		AssetId = "rbxassetid://86643913630660",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_SIDE_GARDEN.",
	},
	SC_CHUNK_SIDE_GARDEN__STORMHAWK = {
		AssetId = "rbxassetid://118253004119432",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_SIDE_GARDEN.",
	},
	SC_CHUNK_SIDE_GARDEN__UNMOORING = {
		AssetId = "rbxassetid://83636741664426",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_SIDE_GARDEN.",
	},
	SC_CHUNK_SIDE_LOOKOUT__AETHER_SURGE = {
		AssetId = "rbxassetid://73982885696348",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_SIDE_LOOKOUT.",
	},
	SC_CHUNK_SIDE_LOOKOUT__LOCKDOWN = {
		AssetId = "rbxassetid://110120417421911",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_SIDE_LOOKOUT.",
	},
	SC_CHUNK_SIDE_LOOKOUT__RECLAIMED = {
		AssetId = "rbxassetid://91418849274622",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_SIDE_LOOKOUT.",
	},
	SC_CHUNK_SIDE_LOOKOUT__RIME = {
		AssetId = "rbxassetid://139183853482314",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_SIDE_LOOKOUT.",
	},
	SC_CHUNK_SIDE_LOOKOUT__SIEGE = {
		AssetId = "rbxassetid://90034711919543",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_SIDE_LOOKOUT.",
	},
	SC_CHUNK_SIDE_LOOKOUT__STORMHAWK = {
		AssetId = "rbxassetid://137902047720007",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_SIDE_LOOKOUT.",
	},
	SC_CHUNK_SIDE_LOOKOUT__UNMOORING = {
		AssetId = "rbxassetid://92612716564578",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_SIDE_LOOKOUT.",
	},
	SC_CHUNK_SIDE_RELIQUARY__AETHER_SURGE = {
		AssetId = "rbxassetid://121034935458568",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_SIDE_RELIQUARY.",
	},
	SC_CHUNK_SIDE_RELIQUARY__LOCKDOWN = {
		AssetId = "rbxassetid://112172165188832",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_SIDE_RELIQUARY.",
	},
	SC_CHUNK_SIDE_RELIQUARY__RECLAIMED = {
		AssetId = "rbxassetid://94430071523963",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_SIDE_RELIQUARY.",
	},
	SC_CHUNK_SIDE_RELIQUARY__RIME = {
		AssetId = "rbxassetid://111934395027265",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_SIDE_RELIQUARY.",
	},
	SC_CHUNK_SIDE_RELIQUARY__SIEGE = {
		AssetId = "rbxassetid://111475539195237",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_SIDE_RELIQUARY.",
	},
	SC_CHUNK_SIDE_RELIQUARY__STORMHAWK = {
		AssetId = "rbxassetid://131695915215167",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_SIDE_RELIQUARY.",
	},
	SC_CHUNK_SIDE_RELIQUARY__UNMOORING = {
		AssetId = "rbxassetid://99999220408438",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_SIDE_RELIQUARY.",
	},
	SC_CHUNK_SKY_TREE_GROVE__AETHER_SURGE = {
		AssetId = "rbxassetid://72952932540856",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_SKY_TREE_GROVE.",
	},
	SC_CHUNK_SKY_TREE_GROVE__LOCKDOWN = {
		AssetId = "rbxassetid://121368511205534",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_SKY_TREE_GROVE.",
	},
	SC_CHUNK_SKY_TREE_GROVE__RECLAIMED = {
		AssetId = "rbxassetid://113870019255628",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_SKY_TREE_GROVE.",
	},
	SC_CHUNK_SKY_TREE_GROVE__RIME = {
		AssetId = "rbxassetid://101512744461019",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_SKY_TREE_GROVE.",
	},
	SC_CHUNK_SKY_TREE_GROVE__SIEGE = {
		AssetId = "rbxassetid://89350127347356",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_SKY_TREE_GROVE.",
	},
	SC_CHUNK_SKY_TREE_GROVE__STORMHAWK = {
		AssetId = "rbxassetid://103321762472299",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_SKY_TREE_GROVE.",
	},
	SC_CHUNK_SKY_TREE_GROVE__UNMOORING = {
		AssetId = "rbxassetid://84893017256198",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_SKY_TREE_GROVE.",
	},
	SC_CHUNK_SPIRE_COURT__AETHER_SURGE = {
		AssetId = "rbxassetid://128318748386193",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_SPIRE_COURT.",
	},
	SC_CHUNK_SPIRE_COURT__LOCKDOWN = {
		AssetId = "rbxassetid://135040715981403",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_SPIRE_COURT.",
	},
	SC_CHUNK_SPIRE_COURT__RECLAIMED = {
		AssetId = "rbxassetid://82058345302577",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_SPIRE_COURT.",
	},
	SC_CHUNK_SPIRE_COURT__RIME = {
		AssetId = "rbxassetid://133639755186285",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_SPIRE_COURT.",
	},
	SC_CHUNK_SPIRE_COURT__SIEGE = {
		AssetId = "rbxassetid://81901669159611",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_SPIRE_COURT.",
	},
	SC_CHUNK_SPIRE_COURT__STORMHAWK = {
		AssetId = "rbxassetid://116211204325483",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_SPIRE_COURT.",
	},
	SC_CHUNK_SPIRE_COURT__UNMOORING = {
		AssetId = "rbxassetid://105593995949960",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_SPIRE_COURT.",
	},
	SC_CHUNK_SPIRE_COURT_B__AETHER_SURGE = {
		AssetId = "rbxassetid://104308592746507",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_SPIRE_COURT_B.",
	},
	SC_CHUNK_SPIRE_COURT_B__LOCKDOWN = {
		AssetId = "rbxassetid://102104397796472",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_SPIRE_COURT_B.",
	},
	SC_CHUNK_SPIRE_COURT_B__RECLAIMED = {
		AssetId = "rbxassetid://126140398020857",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_SPIRE_COURT_B.",
	},
	SC_CHUNK_SPIRE_COURT_B__RIME = {
		AssetId = "rbxassetid://98826396335161",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_SPIRE_COURT_B.",
	},
	SC_CHUNK_SPIRE_COURT_B__SIEGE = {
		AssetId = "rbxassetid://119613008914150",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_SPIRE_COURT_B.",
	},
	SC_CHUNK_SPIRE_COURT_B__STORMHAWK = {
		AssetId = "rbxassetid://107316213439679",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_SPIRE_COURT_B.",
	},
	SC_CHUNK_SPIRE_COURT_B__UNMOORING = {
		AssetId = "rbxassetid://86544784398597",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_SPIRE_COURT_B.",
	},
	SC_CHUNK_TURBINE_HALL__AETHER_SURGE = {
		AssetId = "rbxassetid://117298256652828",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_TURBINE_HALL.",
	},
	SC_CHUNK_TURBINE_HALL__LOCKDOWN = {
		AssetId = "rbxassetid://82397537311801",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_TURBINE_HALL.",
	},
	SC_CHUNK_TURBINE_HALL__RECLAIMED = {
		AssetId = "rbxassetid://71210595649989",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_TURBINE_HALL.",
	},
	SC_CHUNK_TURBINE_HALL__RIME = {
		AssetId = "rbxassetid://139667289226462",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_TURBINE_HALL.",
	},
	SC_CHUNK_TURBINE_HALL__SIEGE = {
		AssetId = "rbxassetid://93164531403907",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_TURBINE_HALL.",
	},
	SC_CHUNK_TURBINE_HALL__STORMHAWK = {
		AssetId = "rbxassetid://137340478706534",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_TURBINE_HALL.",
	},
	SC_CHUNK_TURBINE_HALL__UNMOORING = {
		AssetId = "rbxassetid://115275795024674",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_TURBINE_HALL.",
	},
	SC_CHUNK_VAULT_TURN__AETHER_SURGE = {
		AssetId = "rbxassetid://96228655099390",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "AETHER_SURGE recolour of SC_CHUNK_VAULT_TURN.",
	},
	SC_CHUNK_VAULT_TURN__LOCKDOWN = {
		AssetId = "rbxassetid://120016813061084",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "LOCKDOWN recolour of SC_CHUNK_VAULT_TURN.",
	},
	SC_CHUNK_VAULT_TURN__RECLAIMED = {
		AssetId = "rbxassetid://106693451409899",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RECLAIMED recolour of SC_CHUNK_VAULT_TURN.",
	},
	SC_CHUNK_VAULT_TURN__RIME = {
		AssetId = "rbxassetid://73444685748051",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "RIME recolour of SC_CHUNK_VAULT_TURN.",
	},
	SC_CHUNK_VAULT_TURN__SIEGE = {
		AssetId = "rbxassetid://138228710171837",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "SIEGE recolour of SC_CHUNK_VAULT_TURN.",
	},
	SC_CHUNK_VAULT_TURN__STORMHAWK = {
		AssetId = "rbxassetid://113116526723857",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "STORMHAWK recolour of SC_CHUNK_VAULT_TURN.",
	},
	SC_CHUNK_VAULT_TURN__UNMOORING = {
		AssetId = "rbxassetid://109777367648233",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/sky_citadel/SC_RECOLORS.rbxmx",
		Notes = "UNMOORING recolour of SC_CHUNK_VAULT_TURN.",
	},

	-- === Hub prefabs =============================================
	-- Expedition models are loaded by name; MeshIds live in the saved prefab.
	EXPEDITION_ENTRANCE = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/rbxm/prefabs/EXPEDITION_ENTRANCE.rbxmx",
		Notes = "Delivered entrance rift: 33 MeshParts, 15-stud tear, Stud / 1.0 import. Loaded as a local prefab.",
	},
	EXPEDITION_EXIT = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/rbxm/prefabs/EXPEDITION_EXIT.rbxmx",
		Notes = "Delivered exit rift: 45 MeshParts, 21-stud tear, Stud / 1.0 import. Loaded as a local prefab.",
	},
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

	-- === Ethereal Scape ===========================================
	-- HYBRID KIT 2026-09-27 (owner pick): floating isles + temple architecture + meadow
	-- dressing, 41 pieces incl. 2 landmarks, 2 MINIBOSS arenas and 6 BACKDROP surround pieces (build spec
	-- §7.7). Generated by assets/source/worlds/ethereal_scape/build_ethereal_scape_kit.py and
	-- exported as ONE structure FBX (one object per piece) plus a prop-library FBX. See
	-- docs/biomes/ETHEREAL_SCAPE.md. Placeholders until uploaded: the loader draws blockout.
	ES_CHUNK_ENTRY = {
		AssetId = "rbxassetid://87558612556793",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Arrival Isle: gold mosaic landing, crystal-topped spawn columns, a shrine terrace, the great sky tree, two perches.",
	},
	ES_CHUNK_PATH_PLANK_CROSSING = {
		AssetId = "rbxassetid://124478778946275",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Three isles strung on plank bridges, the middle one raised under a pavilion; a spire on a low perch.",
	},
	ES_CHUNK_PATH_GROVE_ISLE = {
		AssetId = "rbxassetid://129611787409916",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "One broad meadow isle: a great tree, a fairy ring, aether falls pouring off its east rim.",
	},
	ES_CHUNK_PATH_SKYSTAIR_UP = {
		AssetId = "rbxassetid://131946345833449",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A full storey UP (+24): three isles climbing past ruined columns and a great tree to a shrine arch.",
	},
	ES_CHUNK_PATH_SKYSTAIR_DOWN = {
		AssetId = "rbxassetid://125532048392306",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A full storey DOWN (-24): three isles stepping into the cloud past a crystal colossus.",
	},
	ES_CHUNK_SKY_AQUEDUCT = {
		AssetId = "rbxassetid://85694555382529",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Landmark (384): a stone aqueduct carries the road across open sky on three piers and arcades.",
	},
	ES_CHUNK_PATH_BEND_EAST_GROVE = {
		AssetId = "rbxassetid://115844789877272",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A bend on a grove isle, a mushroom ring, a great tree on a raised perch.",
	},
	ES_CHUNK_PATH_BEND_EAST_ASCENT = {
		AssetId = "rbxassetid://137240008429733",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Bend and climb (+16): a ruin isle, a bell-tower isle over the east mouth, a hermit's hut perch.",
	},
	ES_CHUNK_PATH_BEND_WEST_FALLS = {
		AssetId = "rbxassetid://111178239629221",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Bend and descend (-16): aether falls, a spire, a pavilion perch, a pool isle.",
	},
	ES_CHUNK_PATH_BEND_WEST_SHRINE = {
		AssetId = "rbxassetid://134586974797825",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A bend past a small shrine hall and a waystone arc, a spire over the corner.",
	},
	ES_CHUNK_FORK_WAYSHRINE = {
		AssetId = "rbxassetid://124503022970236",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A three-way fork round a waystone circle and a signpost, a great tree on a perch behind.",
	},
	ES_CHUNK_FORK_THREE_TREES = {
		AssetId = "rbxassetid://98453345147690",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A three-way fork under three ancient trees and a mushroom ring; a crag isle below.",
	},
	ES_CHUNK_FORK_TWIN_SPAN = {
		AssetId = "rbxassetid://87703031364900",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A fork on two isles: the lower sends a road west, the upper (+10) carries a bell tower and the north mouth.",
	},
	ES_CHUNK_CONVERGENCE = {
		AssetId = "rbxassetid://103952806164300",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "The crossroads isle: a compass court with a fountain, eight lanterns, four golden roads.",
	},
	ES_CHUNK_MEADOW_OF_BLOOMS = {
		AssetId = "rbxassetid://98463990559919",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "An open meadow isle drifted with blossoms under a great tree, a pool and a tree mesa.",
	},
	ES_CHUNK_TERRACED_GARDENS = {
		AssetId = "rbxassetid://97444880877364",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Garden isles terraced +10 and +20, soil rows and mushrooms, a crag on the highest.",
	},
	ES_CHUNK_CRYSTAL_HOLLOW = {
		AssetId = "rbxassetid://80581921546433",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "An aether pool ringed by crystal clusters under a crystal colossus; a shard isle below.",
	},
	ES_CHUNK_FALLEN_COLONNADE = {
		AssetId = "rbxassetid://87641653489098",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A temple-floor isle, its colonnade half fallen, statues, a bell tower still standing.",
	},
	ES_CHUNK_MIRROR_POOL = {
		AssetId = "rbxassetid://70669629361027",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A balustraded mirror pool watched by four statues, a spire beyond, a lantern perch below.",
	},
	ES_CHUNK_SHRINE_OF_WINDS = {
		AssetId = "rbxassetid://88978705457186",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A temple court: twin pavilions round an orb altar, a bell tower, a lantern avenue.",
	},
	ES_CHUNK_ROOTED_HOLLOW = {
		AssetId = "rbxassetid://86553856257597",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A great tree whose roots arch down across the isle, mushrooms in its shade.",
	},
	ES_CHUNK_TWIN_ISLES = {
		AssetId = "rbxassetid://87318428957815",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Two isles joined by a climbing bridge (+12): a spire on the low one, a pavilion on the high.",
	},
	ES_CHUNK_SKY_OBSERVATORY = {
		AssetId = "rbxassetid://116034293966913",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Landmark (384): a domed colonnade on a podium, an armillary sphere at its crown, the great telescope.",
	},
	ES_CHUNK_TEMPLE_GATE_A = {
		AssetId = "rbxassetid://110756468513680",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Gate-court: bell towers flank the great arch over the COMMUNION road; waystones line it.",
	},
	ES_CHUNK_TEMPLE_GATE_B = {
		AssetId = "rbxassetid://131070519404017",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Gate-court, rare: a roofed colonnade the road passes through, crystal colossi either side.",
	},
	ES_CHUNK_MINIBOSS_WAYSTONE_RING = {
		AssetId = "rbxassetid://88614179949141",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "The Waystone Sentinel's arena: eight waystones round a gold ring, twin spires, a gallery perch.",
	},
	ES_CHUNK_MINIBOSS_RELIQUARY_COURT = {
		AssetId = "rbxassetid://125091853621852",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "The Reliquary Keeper's court: a balustraded temple court before the reliquary hall.",
	},
	ES_CHUNK_SIDE_HERMIT_GROVE = {
		AssetId = "rbxassetid://137762813755555",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A hermit's hut and garden under a great tree, a lantern perch.",
	},
	ES_CHUNK_SIDE_CRYSTAL_GROTTO = {
		AssetId = "rbxassetid://129748468913737",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A crag with crystal clusters crowding its foot, an aether pool.",
	},
	ES_CHUNK_SIDE_RELIC_ALTAR = {
		AssetId = "rbxassetid://77672087844440",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A pavilion altar holding a relic, a crystal colossus on a raised isle behind.",
	},
	ES_CHUNK_CAP_BROKEN_BRIDGE = {
		AssetId = "rbxassetid://124569736618905",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A plank bridge that snaps over the void; a lone crag rises from the depths beyond.",
	},
	ES_CHUNK_CAP_OVERLOOK = {
		AssetId = "rbxassetid://87554917978823",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A balustraded lookout isle with a sky seat under a great tree.",
	},
	ES_CHUNK_CAP_SEALED_SHRINE = {
		AssetId = "rbxassetid://116404859001295",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A shrine door sealed in a crag's face, its seal still glowing.",
	},
	ES_CHUNK_CAP_FALLS_LEDGE = {
		AssetId = "rbxassetid://112295566391985",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "A ledge where aether falls pour off the isle's rim, a spire over it.",
	},
	ES_CHUNK_SANCTUM = {
		AssetId = "rbxassetid://117090521335311",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "The Sanctum: the grand temple that houses the boss, on the greatest isle in the sky.",
	},
	ES_CHUNK_BACKDROP_CLOUDBANK = {
		AssetId = "rbxassetid://135103035982907",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Surround: towering cumulus over a low shelf, puffs round their feet (drifting props).",
	},
	ES_CHUNK_BACKDROP_CLOUD_SHELF = {
		AssetId = "rbxassetid://103622548173409",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Surround: a long layered shelf of cloud, wisps trailing above (drifting props).",
	},
	ES_CHUNK_BACKDROP_CLOUD_DRIFT = {
		AssetId = "rbxassetid://121715778696491",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Surround: open sky, a loose drift of small clouds at every height (drifting props).",
	},
	ES_CHUNK_BACKDROP_STORM_ANVIL = {
		AssetId = "rbxassetid://74427436240497",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Surround: one great anvil cloud with hovering crystal shards in its shadow (props).",
	},
	ES_CHUNK_BACKDROP_DRIFT_ISLES = {
		AssetId = "rbxassetid://84528239803966",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Surround: small isles drifting at their own heights, one carrying a spire.",
	},
	ES_CHUNK_BACKDROP_CRYSTAL_SPIRE = {
		AssetId = "rbxassetid://127274358220179",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Surround: a crystal-ringed crag spire on a sunken isle.",
	},

	-- Retained as palette/art reference ONLY -- no longer what the world
	-- loads (Content/Worlds/EtherealScape.luau no longer declares
	-- PrebuiltMap). Nothing looks this key up any more.
	ES_ENVIRONMENT_FULL = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/rbxm/maps/ES_ENVIRONMENT_FULL.rbxmx",
		Notes = "RETIRED 2026-09-26 as the load route (superseded by the ES_CHUNK_* "
			.. "kit above); kept for provenance. The whole original Ethereal Scape "
			.. "scene, v2 (2026-09-17): 925 MeshParts with PBR SurfaceAppearances, "
			.. "8 islands + 16 satellites, six railed golden bridges, one sky "
			.. "temple. Its materials are this world's palette source of truth -- "
			.. "see assets/source/worlds/ethereal_scape/aether_environment_refined.blend.",
	},
	ES_CHUNK_SANCTUM_TEMPLE_01 = {
		AssetId = "rbxassetid://139700336182963",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_ENTRY_FOLIAGE_01 = {
		AssetId = "rbxassetid://75475813254783",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_PATH_PLANK_CROSSING_FOLIAGE_01 = {
		AssetId = "rbxassetid://129583278560780",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_PATH_GROVE_ISLE_FOLIAGE_01 = {
		AssetId = "rbxassetid://83990827632555",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_PATH_SKYSTAIR_UP_FOLIAGE_01 = {
		AssetId = "rbxassetid://70818004608886",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_PATH_SKYSTAIR_DOWN_FOLIAGE_01 = {
		AssetId = "rbxassetid://132194707595697",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_SKY_AQUEDUCT_FOLIAGE_01 = {
		AssetId = "rbxassetid://112153670212288",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_PATH_BEND_EAST_GROVE_FOLIAGE_01 = {
		AssetId = "rbxassetid://86690840527421",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_PATH_BEND_EAST_ASCENT_FOLIAGE_01 = {
		AssetId = "rbxassetid://72649209303892",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_PATH_BEND_WEST_FALLS_FOLIAGE_01 = {
		AssetId = "rbxassetid://119566840919086",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_PATH_BEND_WEST_SHRINE_FOLIAGE_01 = {
		AssetId = "rbxassetid://118738370323179",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_FORK_WAYSHRINE_FOLIAGE_01 = {
		AssetId = "rbxassetid://72023045108631",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_FORK_THREE_TREES_FOLIAGE_01 = {
		AssetId = "rbxassetid://139215632232195",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_FORK_TWIN_SPAN_FOLIAGE_01 = {
		AssetId = "rbxassetid://102065470737856",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_CONVERGENCE_FOLIAGE_01 = {
		AssetId = "rbxassetid://98758876638144",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_MEADOW_OF_BLOOMS_FOLIAGE_01 = {
		AssetId = "rbxassetid://87728641940355",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_TERRACED_GARDENS_FOLIAGE_01 = {
		AssetId = "rbxassetid://126711481348285",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_CRYSTAL_HOLLOW_FOLIAGE_01 = {
		AssetId = "rbxassetid://86716489662970",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_MIRROR_POOL_FOLIAGE_01 = {
		AssetId = "rbxassetid://139637263327033",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_ROOTED_HOLLOW_FOLIAGE_01 = {
		AssetId = "rbxassetid://87425400393324",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_TWIN_ISLES_FOLIAGE_01 = {
		AssetId = "rbxassetid://99467920339198",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_SKY_OBSERVATORY_TERRAIN_02 = {
		AssetId = "rbxassetid://91330367623995",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_SKY_OBSERVATORY_FOLIAGE_01 = {
		AssetId = "rbxassetid://77612374538855",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_SIDE_HERMIT_GROVE_FOLIAGE_01 = {
		AssetId = "rbxassetid://106251143761866",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_SIDE_CRYSTAL_GROTTO_FOLIAGE_01 = {
		AssetId = "rbxassetid://103657211261040",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_SIDE_RELIC_ALTAR_FOLIAGE_01 = {
		AssetId = "rbxassetid://104049568175509",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_CAP_BROKEN_BRIDGE_FOLIAGE_01 = {
		AssetId = "rbxassetid://108002360271894",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_CAP_OVERLOOK_FOLIAGE_01 = {
		AssetId = "rbxassetid://76478646989809",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_CAP_FALLS_LEDGE_FOLIAGE_01 = {
		AssetId = "rbxassetid://120657733288909",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
	},
	ES_CHUNK_SANCTUM_FOLIAGE_01 = {
		AssetId = "rbxassetid://79451633651966",
		Status = "UPLOADED",
		Source = "assets/rbxm/chunks/ethereal_scape/ES_STRUCTURE.rbxmx",
		Notes = "Multipart Ethereal Scape chunk mesh; generated geometry metadata in Content/Chunks.",
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

--- Adds an entry at runtime. Only for drop-in chunk kits (server/Systems/
--- ChunkAutoKit), whose ids come from the delivered .rbxmx rather than from
--- this file. Refuses to overwrite a hand-written entry.
function AssetManifest.register(key: string, entry: AssetEntry)
	assert(ENTRIES[key] == nil, `asset key '{key}' is already in the manifest`)
	ENTRIES[key] = entry
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
