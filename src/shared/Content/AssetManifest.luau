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
	VV_CHUNK_ENTRY = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/source/worlds/verdant_valley/chunk_entry.blend",
		Notes = "Entry clearing. One exit socket, wide, gentle.",
	},
	VV_CHUNK_PATH_STRAIGHT = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/source/worlds/verdant_valley/chunk_path_straight.blend",
	},
	VV_CHUNK_PATH_BEND = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/source/worlds/verdant_valley/chunk_path_bend.blend",
	},
	VV_CHUNK_MEADOW = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/source/worlds/verdant_valley/chunk_meadow.blend",
		Notes = "Widest sightlines. Forest Wolf pack encounters.",
	},
	VV_CHUNK_STREAM = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/source/worlds/verdant_valley/chunk_stream.blend",
		Notes = "Stream crossing. Thorn Goblin camps on both banks.",
	},
	VV_CHUNK_GROVE = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/source/worlds/verdant_valley/chunk_grove.blend",
		Notes = "Dense cover, narrow sightlines. Elder Treants.",
	},
	VV_CHUNK_HOLLOW = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/source/worlds/verdant_valley/chunk_hollow.blend",
		Notes = "Optional side pocket -- the §6 checklist item for this world.",
	},
	VV_CHUNK_BOSS_CLEARING = {
		AssetId = "",
		Status = "PLACEHOLDER",
		Source = "assets/source/worlds/verdant_valley/chunk_boss_clearing.blend",
		Notes = "60-stud circular arena ringed by 6 oversized trees.",
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
		Notes = "The whole Ethereal Scape scene: 699 MeshParts, 14 landmasses, "
			.. "six bridges, one sky temple. Cloned per expedition and scaled "
			.. "by WorldDefinition.PrebuiltMap.Scale.",
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
