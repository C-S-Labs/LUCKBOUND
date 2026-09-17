--!strict
-- Clones a hand-authored map into an expedition stage. The other half of
-- ChunkLoader: same output, opposite input.
--
-- ChunkLoader turns a generated layout into geometry. This turns ONE AUTHORED
-- SCENE into geometry. A world declares which it is (WorldDefinition
-- .PrebuiltMap) and nothing downstream branches on a world id -- CLAUDE.md's
-- prime directive holds either way, because "generated or authored" is data.
--
-- WHY A WORLD WOULD BE AUTHORED
-- Chunk kits buy variety, and they cost modularity: every piece has to join
-- to every other piece, so gaps, heights and rims must all be interchangeable.
-- Art that was composed -- a traverse that climbs, bridges cut to their own
-- gaps, a crescendo toward the boss -- cannot supply that without being
-- re-authored. Ethereal Scape is that case. Verdant Valley is not.
--
-- THE CONTRACT WITH THE MODELLER is two named parts and nothing else:
--   EntryAnchor   where the player arrives
--   ReturnAnchor  where the way home is built
-- Both optional. Missing either, the loader derives it from the model's own
-- bounding box and says so, so an unprepared scene still loads and walks --
-- art arrives before its anchors do, and a hard failure there would mean the
-- map could not be looked at until it was finished.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)

local PrebuiltLoader = {}

--- The Rojo-synced source model for an asset key, or nil. Nil is a content
--- problem (the file is not in assets/rbxm/maps/, or Rojo is not running), so
--- callers refuse the entry rather than building an empty stage.
function PrebuiltLoader.source(assetKey: string): Model?
	local folder = ServerStorage:FindFirstChild(Constants.NAMES.MAPS_FOLDER)
	if not folder then
		return nil
	end
	local model = folder:FindFirstChild(assetKey)
	return if model and model:IsA("Model") then model else nil
end

--- Anchors every part and reports how many needed it.
---
--- An FBX import leaves everything unanchored, so a scene that has not been
--- prepared falls on its first frame -- and it falls SILENTLY, because nothing
--- errors. Doing it here rather than trusting the file means the same result
--- whichever delivery is dropped in.
local function anchorAll(model: Model): number
	local loosened = 0
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") and not d.Anchored then
			d.Anchored = true
			loosened += 1
		end
	end
	return loosened
end

--- A named anchor part, or nil. Searched by name anywhere in the model, so the
--- modeller can keep it wherever it makes sense to them.
local function anchorPart(model: Model, name: string): BasePart?
	local found = model:FindFirstChild(name, true)
	return if found and found:IsA("BasePart") then found else nil
end

export type PrebuiltResult = {
	Model: Model,
	EntryPosition: Vector3,
	ReturnPosition: Vector3,
	PartCount: number,
	-- True when the scene carried its own EntryAnchor, i.e. the arrival point
	-- is the modeller's choice rather than the loader's guess.
	Authored: boolean,
}

--- Clones `world.PrebuiltMap`'s scene to `origin` under `parent`.
---
--- Returns nil when the source model is missing. Scaling happens BEFORE the
--- pivot move, because Model:ScaleTo scales about the pivot and a scaled-then-
--- placed model is the only order that puts the anchors where they look.
function PrebuiltLoader.build(
	world: any,
	origin: Vector3,
	parent: Instance,
	name: string
): PrebuiltResult?
	local spec = world.PrebuiltMap
	local source = PrebuiltLoader.source(spec.AssetKey)
	if not source then
		return nil
	end

	local model = source:Clone()
	model.Name = name
	model:SetAttribute("WorldId", world.Id)
	model:SetAttribute("AssetKey", spec.AssetKey)
	model:SetAttribute("Scale", spec.Scale)

	local loosened = anchorAll(model)
	if loosened > 0 then
		warn(
			string.format(
				"[PrebuiltLoader] %s: anchored %d loose parts on clone -- "
					.. "the source model should ship anchored",
				spec.AssetKey,
				loosened
			)
		)
	end

	model:ScaleTo(spec.Scale)
	model:PivotTo(CFrame.new(origin))
	model.Parent = parent

	local partCount = 0
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") then
			partCount += 1
		end
	end

	local entryAnchor = anchorPart(model, Constants.NAMES.MAP_ENTRY_ANCHOR)
	local returnAnchor = anchorPart(model, Constants.NAMES.MAP_RETURN_ANCHOR)

	local entryPosition: Vector3
	if entryAnchor then
		entryPosition = entryAnchor.Position
			+ Vector3.new(0, entryAnchor.Size.Y / 2 + GameConfig.Expedition.SpawnHeight, 0)
	else
		-- No anchor: stand the player on top of the scene's bounding box at
		-- its pivot. Not where the modeller would have put them, but on solid
		-- ground rather than inside the geometry or under it.
		local _, size = model:GetBoundingBox()
		entryPosition = origin + Vector3.new(0, size.Y / 2 + GameConfig.Expedition.SpawnHeight, 0)
		warn(
			string.format(
				"[PrebuiltLoader] %s has no %s; arriving on top of the bounding box instead",
				spec.AssetKey,
				Constants.NAMES.MAP_ENTRY_ANCHOR
			)
		)
	end

	-- The way home defaults to the arrival point. Standing on your own return
	-- portal is survivable -- it is a hold prompt, not a trigger -- whereas a
	-- portal at the origin of an unprepared scene could be inside a mountain.
	local returnPosition = if returnAnchor
		then returnAnchor.Position + Vector3.new(0, returnAnchor.Size.Y / 2, 0)
		else entryPosition

	return {
		Model = model,
		EntryPosition = entryPosition,
		ReturnPosition = returnPosition,
		PartCount = partCount,
		Authored = entryAnchor ~= nil,
	}
end

return PrebuiltLoader
