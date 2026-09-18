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
	-- DECLARED HERE, BUT SET IN THE ASSET FILE. An imported MeshPart carries
	-- no baked PhysicsData, so Roblox generates its hull at `Default`
	-- fidelity, which is coarse enough to fill an archway or the gaps in a
	-- colonnade. The pieces where those openings are the point need
	-- PreciseConvexDecomposition.
	--
	-- `CollisionFidelity` CANNOT BE ASSIGNED AT RUNTIME. It is plugin
	-- security, exactly like MeshId, and writing it throws
	-- "lacking capability Plugin" -- which killed an entire hub build at boot
	-- once. It is a SERIALIZED property, so the value lives in the .rbxmx and
	-- this field is the declaration of what that value must be. The loader
	-- checks the two agree and says so when they do not.
	CollisionFidelity: Enum.CollisionFidelity?,
	Attributes: { [string]: any }?,
	-- Attribute name -> fraction to vary it by, per part. See the paint loop.
	-- Multiplies the part's size on load, for setting a piece into the frame
	-- around it without re-exporting the mesh.
	SizeScale: number?,
	Vary: { [string]: number }?,
	-- How many parts are in this set, for ordered wave phasing.
	WaveCount: number?,
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

export type PrefabSpec = {
	AssetKey: string,
	Scale: number,
	Styles: { [string]: Style }?,
	-- COMPASS CORRECTION. An FBX round trip carries the exporter's axis
	-- convention, not the game's: the Crossroads arrived with its north at +Z
	-- while GameConfig.HubLayout.Anchors put north at -Z, so every district was
	-- exactly 180 degrees out. That is a property of the DELIVERY, in the same
	-- family as Scale, and it belongs beside it rather than re-derived by every
	-- caller. Degrees about Y, applied before placement.
	YawDegrees: number?,
	-- WHERE THE MODEL IS REGISTERED FROM. Without this the model is placed by
	-- its pivot, which is what the Fate Engine does and is fine when the pivot
	-- survived the round trip intact.
	--
	-- A pivot is invisible metadata, and invisible metadata is exactly what a
	-- Blender -> FBX -> Studio -> rbxm chain mangles quietly. A PART NAME does
	-- not get mangled -- it is already the contract with the artist, and it is
	-- readable in the file. So a prefab may instead name the part it is
	-- registered from, plus the offset from that part's CENTRE to the point
	-- that should land on `cframe`, in SOURCE units (pre-scale, pre-yaw).
	AnchorPart: string?,
	AnchorOffset: Vector3?,
}

--- Clones `spec.AssetKey` to `cframe` under `parent`.
---
--- Order matters and is not arbitrary: anchor, then scale, then place, then
--- regroup, then paint. Scaling before the placement keeps ScaleTo working
--- about the model's own centre; regrouping before painting means the paint
--- pass walks the finished tree exactly as the game will.
function PrefabLoader.build(
	spec: PrefabSpec,
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

	-- PLACEMENT. The yaw is part of the delivery, so it composes onto whatever
	-- orientation the caller asked for rather than replacing it.
	local placement = cframe * CFrame.Angles(0, math.rad(spec.YawDegrees or 0), 0)
	model:PivotTo(placement)

	-- ...then, if the prefab is registered from a named part rather than its
	-- pivot, slide the whole model so that part's registration point lands
	-- exactly on `cframe`. The offset is rotated by the PLACEMENT rather than
	-- by the part's own CFrame, so a part that arrived with baked rotation
	-- cannot skew the correction.
	if spec.AnchorPart then
		local anchorPart = model:FindFirstChild(spec.AnchorPart, true)
		if anchorPart and anchorPart:IsA("BasePart") then
			local offset = (spec.AnchorOffset or Vector3.zero) * spec.Scale
			local registration = anchorPart.Position + placement:VectorToWorldSpace(offset)
			model:PivotTo(placement + (cframe.Position - registration))
		else
			-- Loud, because the symptom otherwise is a hub sitting a few hundred
			-- studs off to one side with nothing in the log to explain it.
			warn(
				`[PrefabLoader] {spec.AssetKey} names AnchorPart '{spec.AnchorPart}' `
					.. "but no such BasePart is in the model; placed by pivot instead"
			)
		end
	end

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
	local wrongFidelity = {}
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
				if style.SizeScale then
					d.Size *= style.SizeScale
				end
				if style.CanCollide ~= nil then
					d.CanCollide = style.CanCollide
				end
				-- VERIFIED, NEVER WRITTEN -- see the note on the field. A
				-- mismatch means the .rbxmx was not baked, and the symptom is
				-- a railing you walk through or an arch you cannot, with
				-- nothing in the log. Collected and reported once below
				-- rather than warned per part, because a fresh delivery would
				-- otherwise print thirty lines.
				if style.CollisionFidelity and d:IsA("MeshPart") then
					if d.CollisionFidelity ~= style.CollisionFidelity then
						table.insert(wrongFidelity, d.Name)
					end
				end
				for key, value in style.Attributes or {} do
					d:SetAttribute(key, value)
				end
				-- PER-PART VARIATION. Six shards sharing one style entry all
				-- animated identically, which made floating crystals read as
				-- one machine. `Vary` scales a numeric attribute by up to
				-- +/- its fraction, from a hash of the part NAME -- so the
				-- spread is different per part, identical every run, and
				-- still a single line of content rather than six.
				-- Ordered phase for a set that should pulse as a wave. Inlay7
				-- of 16 sits 7/16 of the way round the loop, so the ripple
				-- travels instead of flickering.
				if style.WaveCount then
					local index = tonumber(string.match(d.Name, "(%d+)$"))
					if index then
						d:SetAttribute("WavePhase", (index - 1) / style.WaveCount)
					end
				end
				for key, spread in style.Vary or {} do
					local base = d:GetAttribute(key)
					if type(base) == "number" then
						-- Keyed on name AND attribute, so a part's speed and
						-- its drift are not varied by the same amount. The
						-- trailing multiply is what separates Shard1 from
						-- Shard2 -- without it adjacent names hash to adjacent
						-- values and nothing actually varies.
						local h = 0
						for k = 1, #d.Name do
							h = (h * 131 + string.byte(d.Name, k)) % 1000003
						end
						for k = 1, #key do
							h = (h * 131 + string.byte(key, k)) % 1000003
						end
						local unit = (h * 2654435761) % 1000003 / 1000003
						d:SetAttribute(key, base * (1 + (unit * 2 - 1) * spread))
					end
				end
			end
		end
	end

	if #wrongFidelity > 0 then
		warn(
			`[PrefabLoader] {spec.AssetKey}: {#wrongFidelity} part(s) do not carry the `
				.. "CollisionFidelity content declares, so their hulls will be wrong: "
				.. table.concat(wrongFidelity, ", ")
				.. " -- CollisionFidelity is set in the .rbxmx, not at runtime"
		)
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
