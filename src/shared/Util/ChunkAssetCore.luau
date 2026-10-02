--!strict
-- Seed-only mesh dependencies. Layout/content selection remain unchanged.
local Runtime = require(script.Parent.Parent.Core.ChunkRuntimeCore)
local ChunkAssetCore = {}

export type Role = "VISUAL_ONLY" | "AUTHORITATIVE_MESH_COLLISION"
export type Request = { Key: string, Role: Role }

function ChunkAssetCore.role(component: any?, hasProxy: boolean): Role
	return if (component and component.CanCollide == false) or (not component and hasProxy)
		then "VISUAL_ONLY"
		else "AUTHORITATIVE_MESH_COLLISION"
end

function ChunkAssetCore.key(chunk: any, atmosphere: string?, manifest: any): string
	local key = chunk.AssetKey
	return if atmosphere and manifest.isUploaded(key .. "__" .. atmosphere)
		then key .. "__" .. atmosphere
		else key
end

function ChunkAssetCore.requests(
	layout: any,
	chunks: any,
	manifest: any,
	hasProxy: (any) -> boolean
): { Request }
	local rows, definitions = Runtime.expand(layout, chunks)
	local unique: { [string]: Request } = {}
	for _, row in rows do
		local chunk = definitions[row.ChunkId]
		if not chunk then
			continue
		end
		local parts = chunk.MeshParts
			or { { AssetKey = ChunkAssetCore.key(chunk, layout.Atmosphere, manifest) } }
		for _, component in parts do
			local role =
				ChunkAssetCore.role(if chunk.MeshParts then component else nil, hasProxy(chunk))
			-- Preserve distinct visual/authoritative requirements even if an asset is reused across roles.
			local identity = component.AssetKey .. ":" .. role
			unique[identity] = { Key = component.AssetKey, Role = role }
		end
	end
	local requests = {}
	for _, request in unique do
		table.insert(requests, request)
	end
	table.sort(requests, function(a, b)
		return a.Key .. a.Role < b.Key .. b.Role
	end)
	return requests
end

return ChunkAssetCore
