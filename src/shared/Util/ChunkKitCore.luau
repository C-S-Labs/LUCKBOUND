--!strict
-- Drop-in chunk kits: turns what the server MEASURED on a world's meshes into
-- ChunkDefinitions. The Roblox half -- loading each mesh and ray-probing it --
-- is server/Systems/ChunkAutoKit; this half is pure so it runs in CI.
--
-- WHY THIS EXISTS. A hand-written kit (Content/Chunks/SkyCitadel.luau) needs
-- every piece's size, openings and asset id typed in, and a new art drop that
-- skips that step silently keeps the OLD kit. The delivered .rbxmx already
-- carries the ids and the sizes, and the openings can be measured, so for a
-- world with no hand-written kit the file IS the kit: drop it in
-- assets/rbxm/chunks/<world>/ and the server builds the rest at boot.
-- docs/CHUNK_DROP_IN.md is the artist-facing version of this comment.
--
-- WHAT THE NAME DECIDES. The mesh's Name (with any "chunk_" prefix dropped):
--   contains "entry"              -> ENTRY
--   contains "boss" or "arena"    -> BOSS
--   starts "side_"                -> SIDE
--   starts "cap_"                 -> CAP
--   starts "path_"                -> PATH
--   anything else                 -> COMBAT
-- A Role attribute on the MeshPart overrides the name.
--
-- WHAT THE SOCKET KINDS ARE, and why there are two. ChunkCore reserves every
-- Kind the arena accepts for the final step (see isBossKind there), so a kit
-- where every opening is the same Kind can never leave its first piece. Every
-- measured opening is PATH; the arena's opening is GATE; and a few ordinary
-- pieces get one GATE opening, which makes them the approach to the arena.
-- Those are the pieces named "*gate*" when there are any, and otherwise half
-- of the two-opening COMBAT pieces (falling back to PATH). A two-opening gate
-- piece can ONLY be the last step -- it is never stranded mid-path or on a
-- branch, because ChunkCore already refuses both.

local ChunkKitCore = {}

ChunkKitCore.KIND = "PATH"
ChunkKitCore.GATE_KIND = "GATE"

-- Facing -> socket id and the unit offset of that edge's midpoint. Facing is
-- ChunkCore's: 0 = -Z (north), 90 = +X, 180 = +Z (south), 270 = -X.
local EDGES = {
	[0] = { Id = "N", X = 0, Z = -1 },
	[90] = { Id = "E", X = 1, Z = 0 },
	[180] = { Id = "S", X = 0, Z = 1 },
	[270] = { Id = "W", X = -1, Z = 0 },
}
local LETTER_FACING = { N = 0, E = 90, S = 180, W = 270 }

-- What can HAPPEN in an auto piece when it does not say (a Supports attribute
-- overrides). Generous on purpose: a measured kit has no designer telling the
-- scenario layer what a room is for, and a piece that supports nothing is
-- walked through empty.
local DEFAULT_SUPPORTS: { [string]: { string } } = {
	PATH = { "Combat", "Traversal", "Ambush", "Event" },
	COMBAT = { "Combat", "MiniBoss", "Ambush", "Treasure", "Puzzle", "Shrine", "Secret", "Event" },
	SIDE = { "Treasure", "Secret", "Shrine", "Puzzle" },
}

export type Opening = {
	Facing: number,
	OffsetY: number, -- studs above the piece's walk plane
}

-- One mesh as ChunkAutoKit measured it.
export type Piece = {
	Name: string,
	SizeX: number,
	SizeY: number,
	SizeZ: number,
	-- Studs from the bottom of the bounding box up to the walk plane.
	GroundOffsetY: number,
	Openings: { Opening },
	-- The MeshPart's attributes, as authored in Studio. All optional.
	Attributes: { [string]: any },
}

--- "sky_citadel" / "Sky Citadel" -> "SKY_CITADEL": a kit folder's name as a
--- world id.
function ChunkKitCore.worldIdFor(folderName: string): string
	local id = string.upper(folderName)
	id = string.gsub(id, "[^%w]+", "_")
	id = string.gsub(id, "^_+", "")
	id = string.gsub(id, "_+$", "")
	return id
end

--- A recoloured copy ("chunk_archive__aether_surge") is a variant of a piece
--- the loader swaps in by name, never a piece of its own.
function ChunkKitCore.isVariant(name: string): boolean
	return string.find(name, "__", 1, true) ~= nil
end

--- The mesh name with its conventional prefix dropped, lower case.
function ChunkKitCore.baseName(name: string): string
	local base = string.lower(name)
	base = string.gsub(base, "^chunk_", "")
	return base
end

function ChunkKitCore.roleFor(name: string, override: any?): string
	if type(override) == "string" and override ~= "" then
		return string.upper(override)
	end
	local base = ChunkKitCore.baseName(name)
	if string.find(base, "entry", 1, true) then
		return "ENTRY"
	elseif string.find(base, "boss", 1, true) or string.find(base, "arena", 1, true) then
		return "BOSS"
	elseif string.sub(base, 1, 5) == "side_" then
		return "SIDE"
	elseif string.sub(base, 1, 4) == "cap_" then
		return "CAP"
	elseif string.sub(base, 1, 5) == "path_" then
		return "PATH"
	end
	return "COMBAT"
end

function ChunkKitCore.chunkId(worldId: string, name: string): string
	local base = string.upper(ChunkKitCore.baseName(name))
	base = string.gsub(base, "[^%w]+", "_")
	return `{worldId}_{base}`
end

--- AssetKey for an auto piece. Prefixed so it can never collide with a
--- hand-written manifest entry.
function ChunkKitCore.assetKey(chunkId: string): string
	return `AUTO_{chunkId}`
end

--- "N, S" -> { 0, 180 }. Unknown letters are dropped.
function ChunkKitCore.parseFacings(text: string): { number }
	local out = {}
	for letter in string.gmatch(string.upper(text), "[NESW]") do
		local facing = LETTER_FACING[letter]
		if not table.find(out, facing) then
			table.insert(out, facing)
		end
	end
	return out
end

local function parseList(text: string): { [string]: boolean }
	local out = {}
	for word in string.gmatch(text, "[%w_]+") do
		out[word] = true
	end
	return out
end

local function socketFor(piece: Piece, opening: Opening, kind: string)
	local edge = EDGES[opening.Facing]
	return {
		Id = edge.Id,
		Kind = kind,
		OffsetX = edge.X * piece.SizeX / 2,
		OffsetY = opening.OffsetY,
		OffsetZ = edge.Z * piece.SizeZ / 2,
		Facing = opening.Facing,
	}
end

-- The opening a piece's gate goes on: the GateSide attribute, else the one
-- opposite the first opening (so the approach reads as straight through),
-- else the last.
local function gateOpening(piece: Piece, openings: { Opening }, prefer: number?): number
	local side = piece.Attributes.GateSide
	if type(side) == "string" then
		local facing = ChunkKitCore.parseFacings(side)[1]
		for i, o in openings do
			if o.Facing == facing then
				return i
			end
		end
	end
	if prefer then
		for i, o in openings do
			if o.Facing == prefer then
				return i
			end
		end
	end
	local opposite = (openings[1].Facing + 180) % 360
	for i, o in openings do
		if o.Facing == opposite then
			return i
		end
	end
	return #openings
end

--- Every piece of one world -> ChunkDefinitions, plus a report to print and
--- the problems that will stop the kit assembling. Deterministic: pieces are
--- handled in name order, so the same file always makes the same kit.
function ChunkKitCore.build(worldId: string, pieces: { Piece }): ({ any }, { string }, { string })
	local report, problems = {}, {}
	local sorted = table.clone(pieces)
	table.sort(sorted, function(a, b)
		return a.Name < b.Name
	end)

	type Work = { Piece: Piece, Role: string, Openings: { Opening }, Gate: number? }
	local work: { Work } = {}
	for _, piece in sorted do
		if ChunkKitCore.isVariant(piece.Name) then
			continue
		end
		local role = ChunkKitCore.roleFor(piece.Name, piece.Attributes.Role)
		local openings = table.clone(piece.Openings)
		-- An Openings attribute is the author overruling the probe.
		if type(piece.Attributes.Openings) == "string" then
			openings = {}
			for _, facing in ChunkKitCore.parseFacings(piece.Attributes.Openings) do
				local measured = 0
				for _, o in piece.Openings do
					if o.Facing == facing then
						measured = o.OffsetY
					end
				end
				table.insert(openings, { Facing = facing, OffsetY = measured })
			end
		end
		table.sort(openings, function(a, b)
			return a.Facing < b.Facing
		end)
		if #openings == 0 then
			table.insert(
				problems,
				`{piece.Name}: no opening found on any edge -- skipped (set an Openings attribute, e.g. "N,S")`
			)
			continue
		end
		table.insert(work, { Piece = piece, Role = role, Openings = openings })
	end

	-- One opening, not several, on the pieces the assembler treats as ends:
	-- ChunkCore never caps an arena mouth and fails a capped layout on any
	-- mouth left open, so a second opening on either would fail every seed.
	for _, w in work do
		if (w.Role == "BOSS" or w.Role == "CAP") and #w.Openings > 1 then
			local keep = if w.Role == "BOSS" then gateOpening(w.Piece, w.Openings, 180) else 1
			table.insert(
				report,
				`{w.Piece.Name}: {w.Role} with {#w.Openings} openings -- using only the {EDGES[w.Openings[keep].Facing].Id} one`
			)
			w.Openings = { w.Openings[keep] }
		end
	end

	-- The approach to the arena.
	local named, pairsCombat, pairsPath = {}, {}, {}
	for _, w in work do
		if w.Role == "PATH" or w.Role == "COMBAT" then
			local base = ChunkKitCore.baseName(w.Piece.Name)
			if w.Piece.Attributes.GateSide ~= nil or string.find(base, "gate", 1, true) then
				table.insert(named, w)
			elseif #w.Openings == 2 then
				table.insert(if w.Role == "COMBAT" then pairsCombat else pairsPath, w)
			end
		end
	end
	local gates = named
	if #gates == 0 then
		local pool = if #pairsCombat > 0 then pairsCombat else pairsPath
		for i = 1, math.ceil(#pool / 2) do
			table.insert(gates, pool[i])
		end
	end
	for _, w in gates do
		if #w.Openings >= 2 then
			w.Gate = gateOpening(w.Piece, w.Openings, nil)
		end
	end

	local defs = {}
	local counts: { [string]: number } = {}
	local hasGate = false
	for _, w in work do
		local piece = w.Piece
		local sockets = {}
		for i, o in w.Openings do
			local kind = if w.Role == "BOSS" or i == w.Gate
				then ChunkKitCore.GATE_KIND
				else ChunkKitCore.KIND
			table.insert(sockets, socketFor(piece, o, kind))
		end
		if w.Gate then
			hasGate = true
		end

		local id = ChunkKitCore.chunkId(worldId, piece.Name)
		local def: any = {
			Id = id,
			WorldId = worldId,
			Role = w.Role,
			AssetKey = ChunkKitCore.assetKey(id),
			SizeX = piece.SizeX,
			SizeY = piece.SizeY,
			SizeZ = piece.SizeZ,
			GroundOffsetY = piece.GroundOffsetY,
			-- Measured in the orientation the mesh arrived in, so the art
			-- already agrees with its sockets.
			MeshYawOffset = 0,
			Sockets = sockets,
			Weight = if type(piece.Attributes.Weight) == "number"
					and piece.Attributes.Weight > 0
				then piece.Attributes.Weight
				else 1,
			Tags = { "auto" },
		}
		local supports = DEFAULT_SUPPORTS[w.Role]
		if type(piece.Attributes.Supports) == "string" then
			def.Supports = parseList(piece.Attributes.Supports)
		elseif supports then
			def.Supports = {}
			for _, key in supports do
				def.Supports[key] = true
			end
		end
		table.insert(defs, def)
		counts[w.Role] = (counts[w.Role] or 0) + 1

		local names = {}
		for _, s in sockets do
			table.insert(names, if s.Kind == ChunkKitCore.GATE_KIND then `{s.Id}(gate)` else s.Id)
		end
		table.insert(report, `{id}  {w.Role}  {table.concat(names, "+")}`)
	end

	if (counts.ENTRY or 0) == 0 then
		table.insert(problems, `no ENTRY piece -- name one "chunk_entry"`)
	end
	if (counts.BOSS or 0) == 0 then
		table.insert(problems, `no BOSS piece -- name one "chunk_boss_..." or "..._arena"`)
	end
	if (counts.PATH or 0) + (counts.COMBAT or 0) == 0 then
		table.insert(problems, "no PATH or COMBAT pieces")
	elseif not hasGate then
		table.insert(
			problems,
			`no piece can lead into the arena -- give one PATH/COMBAT piece two openings, or name it "..._gate..."`
		)
	end

	table.insert(
		report,
		1,
		string.format(
			"%s: %d pieces -- %d entry, %d path, %d combat, %d side, %d cap, %d boss",
			worldId,
			#defs,
			counts.ENTRY or 0,
			counts.PATH or 0,
			counts.COMBAT or 0,
			counts.SIDE or 0,
			counts.CAP or 0,
			counts.BOSS or 0
		)
	)
	return defs, report, problems
end

return ChunkKitCore
