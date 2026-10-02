--!strict
-- Explicit server-owned canonical mesh templates; never parent into Workspace.
local AssetService = game:GetService("AssetService")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")
local AssetPreparation = {}

local function meshId(value: string): string?
	return string.match(value, "%d+")
end

function AssetPreparation.new(manifest: any, config: any, dependencies: any?): any
	assert(RunService:IsServer(), "asset preparation is server-only")
	assert(
		config.AssetPreparationWorkers >= 1 and config.AssetPreparationWorkers % 1 == 0,
		"invalid worker count"
	)
	local deps = dependencies or {}
	local parent = deps.Parent or ServerStorage
	assert(
		parent == ServerStorage or parent:IsDescendantOf(ServerStorage),
		"canonical storage must be server-only"
	)
	local storage = Instance.new("Folder")
	storage.Name = "PreparedChunkAssets"
	storage.Parent = parent
	local owner: any = {
		Storage = storage,
		Templates = {},
		Flights = {},
		Local = {},
		Active = 0,
		Destroyed = false,
		Workers = config.AssetPreparationWorkers,
		Counters = {},
		Loads = {},
		Diagnostics = config.AssetPreparationDiagnostics == true,
	}
	local kits = deps.Kits or ServerStorage:FindFirstChild("LuckboundChunkKits")
	local candidates = if kits then kits:GetDescendants() else {}
	table.sort(candidates, function(a, b)
		return a:GetFullName() < b:GetFullName()
	end)
	for _, candidate in candidates do
		if candidate:IsA("MeshPart") and candidate.Archivable then
			local id = meshId(candidate.MeshId)
			if id then
				local prior = owner.Local[id]
				-- Ambiguous render configurations require the AssetService fallback.
				if prior == false then
					continue
				end
				if
					prior
					and (
						prior.TextureID ~= candidate.TextureID
						or prior.Color ~= candidate.Color
						or prior.Material ~= candidate.Material
					)
				then
					owner.Local[id] = false
				else
					owner.Local[id] = candidate
				end
			end
		end
	end
	local function count(name: string, amount: number?)
		if owner.Diagnostics then
			owner.Counters[name] = (owner.Counters[name] or 0) + (amount or 1)
		end
	end
	local function identity(key: string, role: string): string
		assert(role == "VISUAL_ONLY" or role == "AUTHORITATIVE_MESH_COLLISION", "invalid mesh role")
		return key .. ":" .. role .. ":" .. tostring(manifest.assetId(key))
	end
	function owner:proxy(chunk: any): Model?
		local source = chunk.CollisionTemplate
			and kits
			and kits:FindFirstChild(chunk.CollisionTemplate, true)
		return if source
				and source:IsA("Model")
				and source.Archivable
				and source:FindFirstChildWhichIsA("BasePart", true)
			then source
			else nil
	end
	function owner:hasProxy(chunk: any): boolean
		return self:proxy(chunk) ~= nil
	end
	function owner:get(key: string, role: string): MeshPart?
		return self.Templates[identity(key, role)]
	end
	function owner:prepare(key: string, role: string): any
		if self.Destroyed then
			return { ok = false, err = "asset owner destroyed" }
		end
		local cacheKey = identity(key, role)
		local cached = self.Templates[cacheKey]
		if cached then
			count("CacheHits")
			return { ok = true, value = cached }
		end
		local pending = self.Flights[cacheKey]
		if pending then
			count("InFlightDeduplications")
			while not pending.Done do
				pending.Signal.Event:Wait()
			end
			return pending.Result
		end
		count("CacheMisses")
		local flight = { Signal = Instance.new("BindableEvent"), Done = false, Result = nil }
		self.Flights[cacheKey] = flight
		local entered = false
		local ok, value = pcall(function()
			local id = manifest.assetId(key)
			if not id then
				return nil
			end
			local localTemplate = self.Local[meshId(id) or ""]
			local template
			if role == "VISUAL_ONLY" and localTemplate and localTemplate.Parent then
				local cloned, clone = pcall(function()
					return localTemplate:Clone()
				end)
				if cloned and clone then
					template = clone
					count("AuthoredTemplateResolutions")
				end
			end
			if not template then
				while self.Active >= self.Workers and not self.Destroyed do
					task.wait()
				end
				if self.Destroyed then
					return nil
				end
				self.Active += 1
				entered = true
				if self.Diagnostics then
					self.Counters.MaximumActiveWorkers =
						math.max(self.Counters.MaximumActiveWorkers or 0, self.Active)
				end
				count("CreateMeshPartAsyncCalls")
				if self.Diagnostics then
					self.Loads[cacheKey] = (self.Loads[cacheKey] or 0) + 1
				end
				local fidelity = if role == "VISUAL_ONLY"
					then Enum.CollisionFidelity.Box
					else Enum.CollisionFidelity.PreciseConvexDecomposition
				if fidelity == Enum.CollisionFidelity.PreciseConvexDecomposition then
					count("PreciseRequests")
					if role == "VISUAL_ONLY" then
						count("VisualOnlyPreciseRequests")
					end
				end
				template = if deps.CreateMesh
					then deps.CreateMesh(id, fidelity)
					else AssetService:CreateMeshPartAsync(id, { CollisionFidelity = fidelity })
				self.Active -= 1
				entered = false
			end
			if template and template:IsA("MeshPart") then
				if self.Destroyed then
					template:Destroy()
					return nil
				end
				template.Name = key .. "_" .. role
				template.Archivable = true
				template.Anchored = true
				template.CanCollide = false
				template.CanQuery = false
				template.CanTouch = false
				template.Parent = storage
				self.Templates[cacheKey] = template
				return template
			end
			return nil
		end)
		if entered then
			self.Active -= 1
		end
		local result = if ok and value
			then { ok = true, value = value }
			else {
				ok = false,
				err = if ok then "asset unavailable: " .. key else tostring(value),
			}
		if not result.ok then
			count("PreparationFailures")
		end
		flight.Result, flight.Done = result, true
		self.Flights[cacheKey] = nil
		flight.Signal:Fire()
		task.defer(function()
			flight.Signal:Destroy()
		end)
		return result
	end
	function owner:clone(key: string, role: string): any
		local result = self:prepare(key, role)
		if not result.ok then
			return result
		end
		local ok, clone = pcall(function()
			return result.value:Clone()
		end)
		if not ok or not clone then
			return { ok = false, err = "template clone failed: " .. key }
		end
		count("TemplateClones")
		return { ok = true, value = clone }
	end
	function owner:prepareMany(requests: { any }): any
		local unique, queue = {}, {}
		for _, request in requests do
			local cacheKey = identity(request.Key, request.Role)
			if not unique[cacheKey] then
				unique[cacheKey] = true
				table.insert(queue, request)
			end
		end
		local nextIndex, remaining = 1, math.min(self.Workers, #queue)
		local errors = {}
		for _ = 1, remaining do
			task.spawn(function()
				local ok, err = pcall(function()
					while nextIndex <= #queue do
						local index = nextIndex
						nextIndex += 1
						local request = queue[index]
						local result = self:prepare(request.Key, request.Role)
						if not result.ok then
							table.insert(errors, result.err)
						end
					end
				end)
				if not ok then
					table.insert(errors, tostring(err))
				end
				remaining -= 1
			end)
		end
		while remaining > 0 do
			task.wait()
		end
		return if #errors == 0
			then { ok = true, value = #queue }
			else { ok = false, err = table.concat(errors, "; ") }
	end
	function owner:stats(): any
		local snapshot = table.clone(self.Counters)
		local entries = 0
		for _ in self.Templates do
			entries += 1
		end
		snapshot.Entries, snapshot.ActiveWorkers, snapshot.ConfiguredWorkers =
			entries, self.Active, self.Workers
		snapshot.VisualOnlyPreciseRequests = snapshot.VisualOnlyPreciseRequests or 0
		local unique = 0
		for _ in self.Loads do
			unique += 1
		end
		snapshot.UniqueAssetPreparations = unique
		snapshot.DuplicatePreparations =
			math.max(0, (snapshot.CreateMeshPartAsyncCalls or 0) - unique)
		return snapshot
	end
	function owner:destroy()
		self.Destroyed = true
		storage:Destroy()
		table.clear(self.Templates)
		table.clear(self.Local)
	end
	return owner
end

return AssetPreparation
