--!strict
-- Optional authored boundaries and conditional rooms, build spec §7.7.
-- Rooms are dependencies of a placed chunk, never candidates in the assembler.
local ChunkRuntimeCore = {}

function ChunkRuntimeCore.lookup(chunks: any, id: string): any
	if chunks[id] then
		return chunks[id]
	end
	for _, chunk in chunks do
		for _, room in chunk.AttachedRooms or {} do
			if room.Id == id then
				return room
			end
		end
	end
	return nil
end

function ChunkRuntimeCore.expand(layout: any, chunks: any): (any, any)
	local rows = table.clone(layout.Chunks)
	local definitions = table.clone(chunks)
	local nextIndex = 0
	for _, placed in rows do
		nextIndex = math.max(nextIndex, placed.Index)
	end
	for _, placed in layout.Chunks do
		local chunk = chunks[placed.ChunkId]
		for _, room in (chunk and chunk.AttachedRooms) or {} do
			nextIndex += 1
			local angle = -math.rad(placed.Yaw)
			local c, s = math.cos(angle), math.sin(angle)
			local p = room.Offset
			definitions[room.Id] = room
			table.insert(rows, {
				Index = nextIndex,
				ChunkId = room.Id,
				Role = room.Role,
				Yaw = placed.Yaw,
				X = placed.X + c * p[1] + s * p[3],
				Y = placed.Y + p[2],
				Z = placed.Z - s * p[1] + c * p[3],
				ParentIndex = placed.Index,
				ParentChunkId = placed.ChunkId,
				Portal = room.Portal,
			})
		end
	end
	return rows, definitions
end

function ChunkRuntimeCore.vector(value: any, positive: boolean?): boolean
	if type(value) ~= "table" or #value ~= 3 then
		return false
	end
	for _, n in value do
		if type(n) ~= "number" or n ~= n or math.abs(n) == math.huge or (positive and n <= 0) then
			return false
		end
	end
	return true
end

function ChunkRuntimeCore.validate(chunks: any, manifest: any): { string }
	local errors = {}
	local roomIds = {}
	local function boundary(data: any, label: string)
		if data == nil then
			return
		end
		if type(data) ~= "table" or type(data.Segments) ~= "table" then
			table.insert(errors, label .. ": Boundary needs Segments")
			return
		end
		for _, dim in { "Height", "Thickness" } do
			local n = data[dim]
			if type(n) ~= "number" or n ~= n or n <= 0 or n == math.huge then
				table.insert(errors, label .. ": invalid boundary " .. dim)
			end
		end
		for _, segment in data.Segments do
			if not ChunkRuntimeCore.vector(segment.A) or not ChunkRuntimeCore.vector(segment.B) then
				table.insert(errors, label .. ": invalid boundary endpoints")
			elseif segment.A[1] == segment.B[1] and segment.A[3] == segment.B[3] then
				table.insert(errors, label .. ": zero boundary length")
			end
		end
	end
	for id, chunk in chunks do
		boundary(chunk.Boundary, id)
		for _, room in chunk.AttachedRooms or {} do
			local label = id .. " attached room"
			if type(room.Id) ~= "string" or chunks[room.Id] or roomIds[room.Id] then
				table.insert(errors, label .. ": duplicate or invalid Id")
			else
				roomIds[room.Id] = true
			end
			if room.WorldId ~= chunk.WorldId or room.Role ~= "MINIBOSS" or room.AttachedRooms then
				table.insert(errors, label .. ": invalid world, role or nested rooms")
			end
			if not ChunkRuntimeCore.vector(room.Offset) then
				table.insert(errors, label .. ": invalid Offset")
			end
			for _, key in { "SizeX", "SizeY", "SizeZ", "GroundOffsetY" } do
				local n = room[key]
				if
					type(n) ~= "number"
					or n ~= n
					or n < 0
					or n == math.huge
					or (key ~= "GroundOffsetY" and n == 0)
				then
					table.insert(errors, label .. ": invalid " .. key)
				end
			end
			if type(room.MeshParts) ~= "table" or #room.MeshParts == 0 then
				table.insert(errors, label .. ": missing MeshParts")
			else
				for _, part in room.MeshParts do
					if type(part.AssetKey) ~= "string" or not manifest.exists(part.AssetKey) then
						table.insert(errors, label .. ": unknown asset")
					end
					if
						not ChunkRuntimeCore.vector({ part.SizeX, part.SizeY, part.SizeZ }, true)
						or not ChunkRuntimeCore.vector({ part.OffsetX, part.OffsetY, part.OffsetZ })
					then
						table.insert(errors, label .. ": invalid mesh bounds")
					end
				end
			end
			local portal = room.Portal
			if type(portal) ~= "table" then
				table.insert(errors, label .. ": missing Portal")
			else
				for _, key in { "SourceP", "SourceArrival", "RoomP", "RoomArrival" } do
					if not ChunkRuntimeCore.vector(portal[key]) then
						table.insert(errors, label .. ": invalid portal " .. key)
					end
				end
				for _, key in { "SourceS", "RoomS" } do
					if not ChunkRuntimeCore.vector(portal[key], true) then
						table.insert(errors, label .. ": invalid portal " .. key)
					end
				end
			end
			boundary(room.Boundary, label)
			local gate = room.Gate
			if gate ~= nil then
				if
					type(gate) ~= "table"
					or type(gate.Mesh) ~= "string"
					or not ChunkRuntimeCore.vector(gate.P)
					or not ChunkRuntimeCore.vector(gate.S, true)
					or type(gate.TravelY) ~= "number"
					or gate.TravelY ~= gate.TravelY
					or gate.TravelY <= 0
					or gate.TravelY == math.huge
					or gate.RequiredStageState ~= "BossDefeated"
				then
					table.insert(errors, label .. ": invalid biome-boss gate")
				end
			end
		end
	end
	return errors
end

return ChunkRuntimeCore
