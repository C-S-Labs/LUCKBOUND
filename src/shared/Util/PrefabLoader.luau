--!strict
-- Drops an authored .rbxmx into a hub slot. The hub's counterpart to
-- Util/PrebuiltLoader, which does the same job for whole expedition maps.
--
-- WHY THIS EXISTS. The hub's original art seam took ONE uploaded mesh per slot
-- (HubBuilder.meshOrNil). A Fate Engine is 78 MeshParts that must stay separate
-- so they can be animated independently, so it needs the other kind of seam:
-- a Model synced into ServerStorage by Rojo and cloned on demand.
--
-- WHAT IT FIXES ON THE WAY IN, and why each one is not the artist's problem:
--
--   SCALE     An FBX round trip through Studio's importer rarely lands at
--             1 metre = 1 stud. The Fate Engine arrived at 0.42x. One number
--             in content corrects it; the alternative is re-exporting 78
--             meshes, which is how a pipeline gets abandoned.
--   HIERARCHY Empties do NOT survive FBX -> Studio. The authored model comes
--             back flat, but PortalRig and HubEffects walk a tree
--             (EngineRig/RuneRing/CrystalShards). So the loader rebuilds that
--             tree by name rather than asking the artist to hand-group 78
--             parts in Studio after every delivery.
--   COLOUR    Roblox imports untextured meshes grey. Colour lives in content
--             as a name -> style table, so recolouring the Engine is a data
--             edit, never a re-export.
--
-- The contract with the artist stays exactly two things: the part NAMES, and
-- keeping animated parts separate. Everything else is this file's job.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)

local PrefabLoader = {}

export type Style = {
	Color: Color3?,
	Material: Enum.Material?,
	Transparency: number?,
	CanCollide: boolean?,
	Attributes: { [string]: any }?,
}

--- The Rojo-synced source model for a key, or nil when it is not there --
--- which means Rojo is not running or the file is missing, not that the
--- caller did something wrong. Callers fall back to blockout.
function PrefabLoader.source(assetKey: string): Model?
	local folder = ServerStorage:FindFirstChild(Constants.NAMES.PREFABS_FOLDER)
	local model = folder and folder:FindFirstChild(assetKey)
	return if model and model:IsA("Model") then model else nil
end

--- Longest matching prefix wins, so `Plinth_SideBand` can be gold while
--- `Plinth` stays marble. Exact names are just the longest prefix of all.
local function styleFor(name: string, styles: { [string]: Style }): Style?
	local best, bestLength = nil, -1
	for prefix, style in styles do
		if #prefix > bestLength and string.sub(name, 1, #prefix) == prefix then
			best, bestLength = style, #prefix
		end
	end
	return best
end

--- Rebuilds the group a flat import lost. Parts are matched by name and moved
--- under `container`, which is created only if something actually matches --
--- an empty EngineRig would be worse than none, because the code that looks
--- for it would find it and then find nothing inside.
local function regroup(
	root: Instance,
	containerName: string,
	className: string,
	matches: (string) -> boolean
): Instance?
	local found = {}
	for _, child in root:GetChildren() do
		if child:IsA("BasePart") and matches(child.Name) then
			table.insert(found, child)
		end
	end
	if #found == 0 then
		return nil
	end

	local container = Instance.new(className)
	container.Name = containerName
	container.Parent = root
	for _, part in found do
		part.Parent = container
	end
	return container
end

export type LoadResult = {
	Model: Model,
	PartCount: number,
	Missing: { string },
}

--- Clones `spec.AssetKey` to `cframe` under `parent`.
---
--- Order matters and is not arbitrary: anchor, then scale, then pivot, then
--- regroup, then paint. Scaling before the pivot move keeps ScaleTo working
--- about the model's own centre; regrouping before painting means the paint
--- pass walks the finished tree exactly as the game will.
function PrefabLoader.build(
	spec: { AssetKey: string, Scale: number, Styles: { [string]: Style }? },
	required: { string },
	cframe: CFrame,
	parent: Instance,
	name: string
): LoadResult?
	local source = PrefabLoader.source(spec.AssetKey)
	if not source then
		return nil
	end

	local model = source:Clone()
	model.Name = name
	model:SetAttribute("AssetKey", spec.AssetKey)
	model:SetAttribute("Scale", spec.Scale)

	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true
		end
	end

	model:ScaleTo(spec.Scale)
	model:PivotTo(cframe)
	model.Parent = parent

	-- The tree PortalRig and HubEffects expect. Rune and Glyph share one
	-- folder because setRarity looks for Glyph* among RuneRing's children.
	regroup(model, "RuneInlay", "Folder", function(n)
		return string.match(n, "^Inlay%d+$") ~= nil
	end)
	regroup(model, "CrystalShards", "Folder", function(n)
		return string.match(n, "^Shard%d+$") ~= nil
	end)

	local rig = regroup(model, "EngineRig", "Model", function(n)
		return n == "Plinth"
			or n == "OuterRing"
			or n == "InnerRing"
			or n == "PortalPlane"
			or string.match(n, "^Rune%d+$") ~= nil
			or string.match(n, "^Glyph%d+$") ~= nil
			or string.match(n, "^RingFoot") ~= nil
	end)
	if rig then
		regroup(rig, "RuneRing", "Folder", function(n)
			return string.match(n, "^Rune%d+$") ~= nil or string.match(n, "^Glyph%d+$") ~= nil
		end)
		local plinth = rig:FindFirstChild("Plinth")
		if plinth and plinth:IsA("BasePart") then
			(rig :: Model).PrimaryPart = plinth
		end
	end

	local partCount = 0
	local styles = spec.Styles
	for _, d in model:GetDescendants() do
		if not d:IsA("BasePart") then
			continue
		end
		partCount += 1
		-- Authored meshes import untextured and grey. Everything visible is
		-- painted here, from content.
		d.CanCollide = false
		if styles then
			local style = styleFor(d.Name, styles)
			if style then
				if style.Color then
					d.Color = style.Color
				end
				if style.Material then
					d.Material = style.Material
				end
				if style.Transparency then
					d.Transparency = style.Transparency
				end
				if style.CanCollide ~= nil then
					d.CanCollide = style.CanCollide
				end
				for key, value in style.Attributes or {} do
					d:SetAttribute(key, value)
				end
			end
		end
	end

	-- A missing name is not fatal -- the rest of the Engine still stands --
	-- but it is silent otherwise, and silence is how the MeshId seam went
	-- unnoticed for four sessions.
	local missing = {}
	for _, partName in required do
		if not model:FindFirstChild(partName, true) then
			table.insert(missing, partName)
		end
	end

	return { Model = model, PartCount = partCount, Missing = missing }
end

return PrefabLoader
