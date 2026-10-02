--!strict
-- Opt-in asset experiment; production and A-F never call this module.
local AssetService = game:GetService("AssetService")
local ServerStorage = game:GetService("ServerStorage")
local Profile = require(script.Parent.GenerationProfile)
local GameConfig = require(script.Parent.Parent.Core.GameConfig)
local AssetPreparation = {}

function AssetPreparation.new(manifest: any, policy: any, createMesh: any?): any
	local resolver: any = {
		Manifest = manifest,
		Policy = policy,
		Templates = {},
		Flights = {},
		Local = {},
		Loads = {},
	}
	local started = os.clock()
	if policy.LocalTemplates then
		local kits = ServerStorage:FindFirstChild("LuckboundChunkKits")
		if kits then
			for _, instance in kits:GetDescendants() do
				if instance:IsA("MeshPart") then
					-- Match the canonical mesh id, never a guessed part name.
					local id = string.match(instance.MeshId, "%d+")
					if id then
						resolver.Local[id] = instance
					end
				end
			end
		end
	end
	resolver.ResolveSeconds = os.clock() - started

	function resolver:load(key: string, visualOnly: boolean, profile: any): MeshPart?
		local id = self.Manifest.assetId(key)
		if not id then
			return nil
		end
		local fidelity = if self.Policy.VisualFidelity and visualOnly
			then Enum.CollisionFidelity.Box
			else Enum.CollisionFidelity.PreciseConvexDecomposition
		-- A key requested for gameplay collision must never reuse a visual-only cook.
		local cacheKey = key .. ":" .. fidelity.Name
		if self.Policy.Cache and self.Templates[cacheKey] then
			Profile.count(profile, "TemplateCacheHits")
			return self.Templates[cacheKey]
		end
		if self.Policy.Cache and self.Flights[cacheKey] then
			Profile.count(profile, "InFlightDeduplications")
			local flight = self.Flights[cacheKey]
			flight.Event:Wait()
			return self.Templates[cacheKey]
		end
		Profile.count(
			profile,
			if self.Policy.Cache then "TemplateCacheMisses" else "UncachedPreparations"
		)
		local flight = Instance.new("BindableEvent")
		if self.Policy.Cache then
			self.Flights[cacheKey] = flight
		end
		local template: MeshPart? = nil
		local resolveStarted = os.clock()
		local authored = self.Local[string.match(id, "%d+") or ""]
		-- Authoritative visual collision remains on the production precise route.
		if authored and visualOnly then
			template = authored
			Profile.count(profile, "LocalTemplateResolutions")
		end
		Profile.time(profile, "TemplateResolution", resolveStarted)
		if not template then
			Profile.count(profile, "CreateMeshPartAsyncCalls")
			Profile.count(
				profile,
				"PreciseRequests",
				if fidelity == Enum.CollisionFidelity.PreciseConvexDecomposition then 1 else 0
			)
			if visualOnly and fidelity == Enum.CollisionFidelity.PreciseConvexDecomposition then
				Profile.count(profile, "VisualOnlyPreciseRequests")
			end
			self.Loads[key] = (self.Loads[key] or 0) + 1
			profile.CreatedAssets = profile.CreatedAssets or {}
			profile.CreatedAssets[key] = (profile.CreatedAssets[key] or 0) + 1
			local loadStarted = os.clock()
			local ok, result = pcall(function()
				if createMesh then
					return createMesh(id, fidelity)
				end
				return AssetService:CreateMeshPartAsync(id, { CollisionFidelity = fidelity })
			end)
			local elapsed = os.clock() - loadStarted
			profile.AssetCreations = profile.AssetCreations or {}
			table.insert(profile.AssetCreations, {
				AssetKey = key,
				Seconds = elapsed,
				Fidelity = fidelity.Name,
				Success = ok and result ~= nil,
			})
			local observedMemory = game:GetService("Stats"):GetTotalMemoryUsageMb()
			profile.MemoryPeakObservedMb =
				math.max(profile.MemoryPeakObservedMb or 0, observedMemory)
			Profile.time(profile, "CreateMeshPartAsync", loadStarted)
			profile.MaximumCreationSeconds = math.max(profile.MaximumCreationSeconds or 0, elapsed)
			if ok and result then
				template = result
			else
				Profile.count(profile, "AssetCreationErrors")
			end
		end
		if self.Policy.Cache and template then
			self.Templates[cacheKey] = template
		end
		self.Flights[cacheKey] = nil
		flight:Fire()
		task.defer(function()
			flight:Destroy()
		end)
		return template
	end

	function resolver:place(
		key: string,
		size: Vector3,
		frame: CFrame,
		parent: Instance,
		visualOnly: boolean,
		profile: any
	): MeshPart?
		local template = self:load(key, visualOnly, profile)
		if not template then
			return nil
		end
		local startedClone = os.clock()
		local mesh: MeshPart
		if self.Policy.Cache or template.Parent ~= nil then
			mesh = template:Clone()
			Profile.count(profile, "TemplateClones")
			if template.Parent ~= nil then
				Profile.count(profile, "LocalTemplateClones")
			end
		else
			mesh = template
		end
		Profile.time(profile, "TemplateClone", startedClone)
		mesh.Name = "Mesh"
		mesh.Anchored = true
		-- Preserve loader calibration/query order; caller disables visual collision
		-- only after its authored proxy has been attached successfully.
		mesh.CanCollide = true
		mesh.CanQuery = true
		mesh.CanTouch = true
		mesh.Size = size
		mesh.CFrame = frame
		mesh.Parent = parent
		return mesh
	end

	function resolver:prepare(requests: { any }, workers: number, profile: any)
		assert(self.Policy.Cache, "preparation requires cache")
		assert(
			table.find(GameConfig.GenerationBenchmark.AssetWorkers, workers),
			"unsupported asset worker count"
		)
		local nextIndex, remaining = 1, math.min(workers, #requests)
		local failure: any = nil
		local startedPrepare = os.clock()
		for _ = 1, remaining do
			task.spawn(function()
				local ok, err = pcall(function()
					while nextIndex <= #requests do
						local index = nextIndex
						nextIndex += 1
						local request = requests[index]
						self:load(request.Key, request.VisualOnly, profile)
					end
				end)
				if not ok then
					failure = err
				end
				remaining -= 1
			end)
		end
		while remaining > 0 do
			task.wait()
		end
		Profile.time(profile, "AssetPreparation", startedPrepare)
		if failure then
			error(failure)
		end
	end

	function resolver:destroy()
		for _, template in self.Templates do
			if template.Parent == nil then
				template:Destroy()
			end
		end
		table.clear(self.Templates)
	end
	return resolver
end

return AssetPreparation
