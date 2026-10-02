--!strict
-- Studio test observer: local spawn geometry replication/preload, no new remotes.
local Workspace = game:GetService("Workspace")
local ContentProvider = game:GetService("ContentProvider")
local RunService = game:GetService("RunService")
local rows = {}
local connection
local function observe(model: Instance)
	if model.Name ~= "GenerationBenchmark" then
		return
	end
	task.spawn(function()
		local deadline = os.clock() + 60
		while
			model.Parent
			and model:GetAttribute("MaterializationReadyEpochMs") == nil
			and os.clock() < deadline
		do
			RunService.Heartbeat:Wait()
		end
		if not model.Parent then
			return
		end
		local request = model:GetAttribute("RequestEpochMs")
		if not request then
			return
		end
		local entry = model:WaitForChild(model:GetAttribute("EntryFolder"), 10)
		if not entry then
			table.insert(rows, { RequestEpochMs = request, Error = "entry not replicated" })
			return
		end
		local meshes = {}
		local collision = 0
		deadline = os.clock() + 10
		repeat
			table.clear(meshes)
			collision = 0
			for _, part in entry:GetDescendants() do
				if part:IsA("MeshPart") and part.Transparency < 1 then
					table.insert(meshes, part)
				end
				if part:IsA("BasePart") and part.CanCollide then
					collision += 1
				end
			end
			if
				#meshes >= model:GetAttribute("ExpectedEntryMeshes")
				and collision >= model:GetAttribute("ExpectedEntryCollision")
			then
				break
			end
			RunService.Heartbeat:Wait()
		until os.clock() > deadline or not model.Parent
		local started = os.clock()
		local failed = {}
		local ok, err = pcall(function()
			ContentProvider:PreloadAsync(meshes, function(id, status)
				if status ~= Enum.AssetFetchStatus.Success then
					table.insert(failed, { Id = id, Status = status.Name })
				end
			end)
		end)
		RunService.RenderStepped:Wait()
		table.insert(rows, {
			RequestEpochMs = request,
			ReadyEpochMs = DateTime.now().UnixTimestampMillis,
			PreloadSeconds = os.clock() - started,
			Meshes = #meshes,
			CollisionParts = collision,
			ExpectedMeshes = model:GetAttribute("ExpectedEntryMeshes"),
			ExpectedCollision = model:GetAttribute("ExpectedEntryCollision"),
			Error = if ok then nil else tostring(err),
			FailedAssets = failed,
			ModelStillPresent = model.Parent ~= nil,
		})
	end)
end
connection = Workspace.ChildAdded:Connect(observe)
return {
	records = function()
		return rows
	end,
	stop = function()
		connection:Disconnect()
	end,
}
