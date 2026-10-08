--!strict
-- Run as a Server command after the opt-in Batch2 review reports READY.
local RS = game:GetService("ReplicatedStorage")
local data: any = require(RS.EmberfallBatch2ReviewData)
local world = workspace.ExpeditionStage.EmberfallBatch2Review
assert(world:GetAttribute("TerrainReady"), "Review not ready")
local origin = world:GetAttribute("Origin") :: Vector3
local folders = {}
for _, f in world:GetChildren() do
	local id = f:GetAttribute("ChunkId")
	if id then
		folders[id] = f
	end
end
local centres, sizes, sockets, seamError, misses, rays = 0, 0, 0, 0, 0, 0
local presentationSizeError, presentationCount = 0, 0
for _, record in data.assets do
	if record.role ~= "collision" and record.role ~= "terrain" then
		local part = world.AssemblyPresentation:FindFirstChild(record.key) :: MeshPart
		assert(part and part.MeshId == data.ids[record.key], "Missing presentation mapping")
		presentationSizeError = math.max(
			presentationSizeError,
			(part.Size - Vector3.new(unpack(record.size))).Magnitude
		)
		presentationCount += 1
	end
end
local sourceMappingCount = 0
for _, record in data.sourceVisuals do
	local template =
		game.ServerStorage:FindFirstChild(record.key .. "_VISUAL_ONLY", true) :: MeshPart
	assert(
		template and template.MeshId == data.sourceIds[record.key],
		"Source/variant mapping unavailable"
	)
	sourceMappingCount += 1
end
local checks = {}
local function frame(row: any): CFrame
	return CFrame.new(origin + Vector3.new(row.x, row.y, row.z))
		* CFrame.Angles(0, -math.rad(row.yaw), 0)
end
local function socketPoint(row: any, socket: any): Vector3
	return frame(row):PointToWorldSpace(Vector3.new(socket.OffsetX, socket.OffsetY, socket.OffsetZ))
end
local function cast(folder: Instance, point: Vector3): RaycastResult?
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { folder }
	params.RespectCanCollide = true
	rays += 1
	local hit = workspace:Raycast(point + Vector3.new(0, 60, 0), Vector3.new(0, -120, 0), params)
	if not hit then
		misses += 1
	end
	return hit
end
for i, row in data.rows do
	local folder = folders[row.id]
	assert(folder and folder.WalkCollision, "Missing placement collision")
	local mesh = folder.Mesh
	local definition = data.kit[row.id]
	local record
	for _, r in data.assets do
		if r.key == definition.AssetKey then
			record = r
			break
		end
	end
	assert(record and mesh:IsA("MeshPart"), "Missing authored terrain record")
	centres = math.max(
		centres,
		(mesh.Position - frame(row):PointToWorldSpace(Vector3.new(unpack(record.center)))).Magnitude
	)
	sizes = math.max(sizes, (mesh.Size - Vector3.new(unpack(record.size))).Magnitude)
	assert(
		not mesh.CanCollide and mesh.MeshId == data.ids[record.key],
		"Terrain mapping/collision role mismatch"
	)
	local routeHit = cast(folder.WalkCollision, frame(row):PointToWorldSpace(Vector3.new(0, 0, 0)))
	table.insert(checks, {
		placement = i,
		source = row.source_id,
		yaw = row.yaw,
		colliderCount = folder:GetAttribute("WalkCollisionPieces"),
		centreGroundHit = routeHit ~= nil,
	})
	if i == #data.rows then
		continue
	end
	local nextRow = data.rows[i + 1]
	local a, b
	for _, sa in definition.Sockets do
		for _, sb in data.kit[nextRow.id].Sockets do
			if (socketPoint(row, sa) - socketPoint(nextRow, sb)).Magnitude < 0.005 then
				a, b = sa, sb
			end
		end
	end
	assert(
		a and b and a.Kind == b.Kind and a.Width == 24 and b.Width == 24,
		"Socket compatibility lost"
	)
	sockets = math.max(sockets, (socketPoint(row, a) - socketPoint(nextRow, b)).Magnitude)
	local localPoint = Vector3.new(a.OffsetX, a.OffsetY, a.OffsetZ)
	local inward = Vector3.new(-a.OffsetX, 0, -a.OffsetZ).Unit
	local tangent = Vector3.new(inward.Z, 0, -inward.X)
	local seam = 0
	for _, shoulder in { -12, 0, 12 } do
		local point = frame(row):PointToWorldSpace(localPoint + tangent * shoulder)
		local step = frame(row):VectorToWorldSpace(inward) * 0.02
		local ha = cast(folder.WalkCollision, point + step)
		local hb = cast(folders[nextRow.id].WalkCollision, point - step)
		if ha and hb then
			seam = math.max(seam, math.abs(ha.Position.Y - hb.Position.Y))
		end
	end
	seamError = math.max(seamError, seam)
	checks[#checks].exitSeam = seam
end
local result = {
	placements = #data.rows,
	centreError = centres,
	sizeError = sizes,
	socketError = sockets,
	seamHeightDifference = seamError,
	rays = rays,
	misses = misses,
	presentationSizeError = presentationSizeError,
	presentationParts = presentationCount,
	sourceMappingCount = sourceMappingCount,
	checks = checks,
	attributes = world:GetAttributes(),
	sourceVisualsResolved = workspace:GetAttribute("EmberfallBatch2SourceVisualsResolved"),
}
world:SetAttribute("ImportedValidation", game:GetService("HttpService"):JSONEncode(result))
assert(
	misses == 0
		and centres < 0.01
		and sizes < 0.01
		and sockets < 0.005
		and seamError < 0.05
		and presentationSizeError < 0.01,
	"Imported geometry probe failed"
)
return result
