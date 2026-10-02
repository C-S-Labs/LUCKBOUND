--!strict
-- Experimental world views over existing direct-key manifest access. No content migration.
local Runtime = require(script.Parent.Parent.Core.ChunkRuntimeCore)
local ServerStorage = game:GetService("ServerStorage")
local AssetRegistry = {}

local function proxyValid(chunk: any): boolean
	local kits = ServerStorage:FindFirstChild("LuckboundChunkKits")
	local proxy = chunk.CollisionTemplate
		and kits
		and kits:FindFirstChild(chunk.CollisionTemplate, true)
	return proxy ~= nil
		and proxy:IsA("Model")
		and proxy:FindFirstChildWhichIsA("BasePart", true) ~= nil
end

function AssetRegistry.requests(layout: any, chunks: any, manifest: any): { any }
	local rows, definitions = Runtime.expand(layout, chunks)
	local unique = {}
	for _, row in rows do
		local chunk = definitions[row.ChunkId]
		local parts = chunk.MeshParts
			or { { AssetKey = chunk.AssetKey, CanCollide = not proxyValid(chunk) } }
		for _, definition in parts do
			local key = definition.AssetKey
			if
				not chunk.MeshParts
				and layout.Atmosphere
				and manifest.isUploaded(key .. "__" .. layout.Atmosphere)
			then
				key ..= "__" .. layout.Atmosphere
			end
			-- If any occurrence needs collision, preparation must use precise.
			if not unique[key] then
				unique[key] = { Key = key, VisualOnly = true }
			end
			if definition.CanCollide ~= false then
				unique[key].VisualOnly = false
			end
		end
	end
	local result = {}
	for _, request in unique do
		table.insert(result, request)
	end
	table.sort(result, function(a, b)
		return a.Key < b.Key
	end)
	return result
end

function AssetRegistry.new(manifest: any, chunks: any): any
	local registry: any = { Cache = {} }
	function registry:GetWorld(worldId: string): any
		if self.Cache[worldId] then
			return self.Cache[worldId]
		end
		local rows = {}
		for _, chunk in chunks do
			if chunk.WorldId == worldId then
				table.insert(
					rows,
					{ ChunkId = chunk.Id, Index = #rows + 1, X = 0, Y = 0, Z = 0, Yaw = 0 }
				)
			end
		end
		local requests = AssetRegistry.requests({ Chunks = rows }, chunks, manifest)
		local view = {}
		for _, request in requests do
			view[request.Key] =
				{ AssetId = manifest.assetId(request.Key), VisualOnly = request.VisualOnly }
		end
		self.Cache[worldId] = view
		return view
	end
	return registry
end

return AssetRegistry
