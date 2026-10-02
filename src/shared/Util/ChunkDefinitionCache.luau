--!strict
-- Lightweight derived definitions. Never owns instantiated geometry.
local ChunkDefinitionCache = {}
local cache: { [any]: any } = setmetatable({}, { __mode = "k" }) :: any

function ChunkDefinitionCache.get(chunk: any): (any, boolean)
	local existing = cache[chunk]
	if existing then
		return existing, true
	end
	local sockets = {}
	for _, socket in chunk.Sockets do
		sockets[socket.Kind] = sockets[socket.Kind] or {}
		table.insert(sockets[socket.Kind], socket)
	end
	local definition = {
		SocketsByKind = sockets,
		HalfX = chunk.SizeX / 2,
		HalfZ = chunk.SizeZ / 2,
	}
	cache[chunk] = definition
	return definition, false
end

function ChunkDefinitionCache.clear()
	table.clear(cache)
end

return ChunkDefinitionCache
