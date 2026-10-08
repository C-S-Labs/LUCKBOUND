--!strict
-- NON-PRODUCTION: bounded Studio client observations; no production content registration.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then
	return
end
local ContentProvider = game:GetService("ContentProvider")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local Stats = game:GetService("Stats")
local WAIT_TIMEOUT_SECONDS = 600
local VIEW_SETTLE_SECONDS = 1
local VIEW_SAMPLE_SECONDS = 5
local CAMERA_BINDING = "EmberfallBenchmarkCamera"
local MEMORY_TAGS = {
	"Instances",
	"LuaHeap",
	"PhysicsParts",
	"PhysicsCollision",
	"GraphicsMeshParts",
	"GraphicsTexture",
	"GraphicsParts",
	"GraphicsParticles",
	"Signals",
	"HttpCache",
}
local function memorySnapshot(): any
	local result: any = { categoriesMb = {}, unavailable = {} }
	local ok, total = pcall(function()
		return Stats:GetTotalMemoryUsageMb()
	end)
	if ok then
		result.totalMb = total
	end
	for _, name in MEMORY_TAGS do
		local tagOk, amount = pcall(function()
			return Stats:GetMemoryUsageMbForTag((Enum.DeveloperMemoryTag :: any)[name])
		end)
		if tagOk then
			result.categoriesMb[name] = amount
		else
			table.insert(result.unavailable, name)
		end
	end
	return result
end
local report: any = {
	schemaVersion = 1,
	clientStartedAt = workspace:GetServerTimeNow(),
	startupMemory = memorySnapshot(),
	streamingEnabled = workspace.StreamingEnabled,
	streamingMinRadius = "server-only property; see server report",
	streamingTargetRadius = "server-only property; see server report",
	views = {},
	limitations = {
		"Startup memory is a client-script-start snapshot, not an empty-process baseline.",
		"ServerTimeNow timestamps share a synchronized clock with synchronization uncertainty.",
		"Preload plus two rendered frames is a readiness proxy, not GPU residency or visual completeness proof.",
		"RenderStepped delta measures frame cadence including waits and frame caps, not isolated CPU or GPU time.",
		"Desktop Studio observations do not establish published-client or low-end-device safety.",
	},
}
local function waitUntil(predicate: () -> boolean, description: string)
	local deadline = os.clock() + WAIT_TIMEOUT_SECONDS
	while not predicate() do
		if os.clock() > deadline then
			error("Benchmark timed out waiting for " .. description)
		end
		task.wait(0.05)
	end
end
local function frameSummary(samples: { number }): any
	table.sort(samples)
	local count = #samples
	if count == 0 then
		return { frames = 0 }
	end
	local sum, over33, over50 = 0, 0, 0
	for _, seconds in samples do
		sum += seconds
		if seconds > 1 / 30 then
			over33 += 1
		end
		if seconds > 0.05 then
			over50 += 1
		end
	end
	local function percentile(fraction: number): number
		return samples[math.clamp(math.ceil(count * fraction), 1, count)] * 1000
	end
	return {
		frames = count,
		elapsedSampleSeconds = sum,
		meanMs = sum / count * 1000,
		meanFps = count / sum,
		medianMs = percentile(0.5),
		p95Ms = percentile(0.95),
		p99Ms = percentile(0.99),
		maxMs = samples[count] * 1000,
		framesOver33Ms = over33,
		framesOver50Ms = over50,
	}
end
local function performanceSnapshot(): any
	local result = {}
	for _, rootName in { "PerformanceStats", "RenderBreakdown" } do
		local root = Stats:FindFirstChild(rootName)
		if root then
			local rows = {}
			for _, item in root:GetChildren() do
				local ok, value = pcall(function()
					return item:GetValueString()
				end)
				if ok then
					rows[item.Name] = value
				end
			end
			result[rootName] = rows
		end
	end
	return result
end
local savedCamera: any = nil
local function runBenchmark()
	waitUntil(function()
		local stage = workspace:FindFirstChild("ExpeditionStage")
		return stage ~= nil and stage:FindFirstChild("EmberfallScaleBenchmark") ~= nil
	end, "benchmark model")
	local world = workspace.ExpeditionStage.EmberfallScaleBenchmark
	report.modelArrivedAt = workspace:GetServerTimeNow()
	waitUntil(function()
		return world:GetAttribute("ServerReady") == true
	end, "server instantiation readiness")
	report.serverReadyObservedAt = workspace:GetServerTimeNow()
	local expectedMeshParts = world:GetAttribute("ExpectedMeshParts")
	report.replicationCountVerified = typeof(expectedMeshParts) == "number"
	if typeof(expectedMeshParts) == "number" then
		waitUntil(function()
			local count = 0
			for _, descendant in world:GetDescendants() do
				if descendant:IsA("MeshPart") then
					count += 1
				end
			end
			return count >= expectedMeshParts
		end, "replicated benchmark MeshPart count")
		report.expectedMeshParts = expectedMeshParts
	else
		table.insert(
			report.limitations,
			"No ExpectedMeshParts attribute: full replication completeness was not verified."
		)
	end
	report.instancesReadyObservedAt = workspace:GetServerTimeNow()
	report.benchmarkStartedAt = world:GetAttribute("BenchmarkStartedAt")
	report.origin = tostring(world:GetAttribute("Origin"))
	report.viewport = tostring(workspace.CurrentCamera and workspace.CurrentCamera.ViewportSize)
	report.modelStreamingMode = tostring((world :: Model).ModelStreamingMode)
	local meshes: { Instance } = {}
	local uniqueIds: { [string]: boolean } = {}
	for _, descendant in world:GetDescendants() do
		if descendant:IsA("MeshPart") then
			table.insert(meshes, descendant)
			uniqueIds[descendant.MeshId] = true
		end
	end
	local uniqueCount = 0
	for _ in uniqueIds do
		uniqueCount += 1
	end
	report.meshParts, report.uniqueMeshIds = #meshes, uniqueCount
	report.beforePreloadMemory = memorySnapshot()
	local preload: any = { statusCounts = {}, failures = {}, callbackCount = 0 }
	report.preload = preload
	report.preloadStartedAt = workspace:GetServerTimeNow()
	local preloadStart = os.clock()
	local preloadOk, preloadError = pcall(function()
		ContentProvider:PreloadAsync(
			meshes,
			function(contentId: string, status: Enum.AssetFetchStatus)
				local statusName = tostring(status)
				preload.callbackCount += 1
				preload.statusCounts[statusName] = (preload.statusCounts[statusName] or 0) + 1
				if status ~= Enum.AssetFetchStatus.Success and #preload.failures < 16 then
					table.insert(preload.failures, { contentId = contentId, status = statusName })
				end
			end
		)
	end)
	preload.seconds, preload.ok = os.clock() - preloadStart, preloadOk
	if not preloadOk then
		preload.error = tostring(preloadError)
	end
	report.preloadCompletedAt = workspace:GetServerTimeNow()
	RunService.RenderStepped:Wait()
	RunService.RenderStepped:Wait()
	report.visibleReadyProxyAt = workspace:GetServerTimeNow()
	report.afterPreloadMemory = memorySnapshot()
	local Lighting = game:GetService("Lighting")
	local Loader = require(game.ReplicatedStorage.Luckbound.Util.ChunkLoader)
	Loader.applyEnvironment(Lighting, {
		AmbientColor = Color3.fromRGB(90, 90, 80),
		OutdoorAmbientColor = Color3.fromRGB(130, 130, 120),
		ColorShiftTop = Color3.new(0, 0, 0),
		FogColor = Color3.fromRGB(165, 176, 174),
		FogStart = 4000,
		FogEnd = 8000,
		Brightness = 2,
		ClockTime = 14,
	})
	for _, effect in Lighting:GetChildren() do
		if effect:IsA("Atmosphere") then
			effect.Density = 0.15
			effect.Haze = 0
			effect.Glare = 0
			effect.Color = Color3.fromRGB(190, 199, 185)
			effect.Decay = Color3.fromRGB(125, 130, 119)
		elseif effect:IsA("ColorCorrectionEffect") then
			effect.TintColor = Color3.new(1, 1, 1)
			effect.Contrast = 0
			effect.Saturation = 0
		end
	end
	local player = Players.LocalPlayer
	waitUntil(function()
		return typeof(world:GetAttribute("PlayerReadyAt")) == "number"
			or typeof(player:GetAttribute("PlayerReadyAt")) == "number"
	end, "server player teleport readiness")
	report.playerReadyAt = world:GetAttribute("PlayerReadyAt")
		or player:GetAttribute("PlayerReadyAt")
	report.playerReadyObservedAt = workspace:GetServerTimeNow()
	waitUntil(function()
		return workspace.CurrentCamera ~= nil
	end, "camera")
	local camera = workspace.CurrentCamera :: Camera
	savedCamera = {
		camera = camera,
		cameraType = camera.CameraType,
		cameraSubject = camera.CameraSubject,
		cframe = camera.CFrame,
		focus = camera.Focus,
		fieldOfView = camera.FieldOfView,
	}
	local originAttribute = world:GetAttribute("Origin")
	assert(typeof(originAttribute) == "Vector3", "Benchmark Origin must be a Vector3")
	local origin = originAttribute :: Vector3
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	local eye = if root and root:IsA("BasePart")
		then root.Position + Vector3.new(0, 2, 0)
		else origin + Vector3.new(0, 6, 0)
	local groups = world:GetAttribute("Groups") or 1
	local viewpoints = {
		{ name = "playerEye", eye = eye, target = eye + Vector3.new(0, 0, 140) },
		{
			name = "elevated",
			eye = origin + Vector3.new(120, 160, -180),
			target = origin + Vector3.new(0, 0, 350),
		},
		{
			name = "overview",
			eye = origin + Vector3.new(1000, 1250, -650),
			target = origin + Vector3.new(0, 0, 500),
		},
	}
	if typeof(groups) == "number" and groups > 1 then
		viewpoints[3].eye = origin + Vector3.new(1100, 2600, -1900)
		viewpoints[3].target = origin + Vector3.new(750, 0, 1300)
		local lastIndex = groups - 1
		local offset = Vector3.new((lastIndex % 2) * 2048, 0, math.floor(lastIndex / 2) * 2048)
		local remoteEye = origin + offset + Vector3.new(256, 21, 768)
		table.insert(viewpoints, {
			name = "laterHalfPlayerEye",
			eye = remoteEye,
			target = remoteEye + Vector3.new(0, 0, 140),
		})
		table.insert(
			report.limitations,
			"Proxy groups are disconnected grounds in a cost fixture, not an authored continuous route."
		)
	end
	for _, view in viewpoints do
		camera.CameraType = Enum.CameraType.Scriptable
		workspace:SetAttribute("EmberfallBenchmarkView", view.name)
		local fixedFrame = CFrame.lookAt(view.eye, view.target)
		RunService:BindToRenderStep(
			CAMERA_BINDING,
			Enum.RenderPriority.Camera.Value + 10,
			function()
				camera.CFrame = fixedFrame
				camera.Focus = CFrame.new(view.target)
			end
		)
		task.wait(VIEW_SETTLE_SECONDS)
		local samples: { number } = {}
		local connection = RunService.RenderStepped:Connect(function(delta)
			table.insert(samples, delta)
		end)
		task.wait(VIEW_SAMPLE_SECONDS)
		connection:Disconnect()
		RunService:UnbindFromRenderStep(CAMERA_BINDING)
		local result = frameSummary(samples)
		result.name, result.eye, result.target =
			view.name,
			{ view.eye.X, view.eye.Y, view.eye.Z },
			{ view.target.X, view.target.Y, view.target.Z }
		result.memory = memorySnapshot()
		result.performance = performanceSnapshot()
		result.performanceAccess =
			"LocalScript counters may be unavailable; privileged Studio samples recorded separately"
		table.insert(report.views, result)
	end
	if typeof(report.benchmarkStartedAt) == "number" then
		report.modelArrivalSeconds = report.modelArrivedAt - report.benchmarkStartedAt
		report.serverReadyObservedSeconds = report.serverReadyObservedAt - report.benchmarkStartedAt
		report.playerReadySeconds = report.playerReadyAt - report.benchmarkStartedAt
		report.visibleReadyProxySeconds = report.visibleReadyProxyAt - report.benchmarkStartedAt
	end
end
local ok, problem = xpcall(runBenchmark, debug.traceback)
RunService:UnbindFromRenderStep(CAMERA_BINDING)
if savedCamera then
	local camera = savedCamera.camera
	camera.CameraType, camera.CameraSubject = savedCamera.cameraType, savedCamera.cameraSubject
	camera.CFrame, camera.Focus, camera.FieldOfView =
		savedCamera.cframe, savedCamera.focus, savedCamera.fieldOfView
end
report.ok = ok
if not ok then
	report.error = tostring(problem)
end
report.completedAt = workspace:GetServerTimeNow()
report.finalMemory = memorySnapshot()
local encoded = HttpService:JSONEncode(report)
workspace:SetAttribute("EmberfallBenchmarkClientReport", encoded)
print("[EmberfallBenchmarkClient] " .. encoded)
