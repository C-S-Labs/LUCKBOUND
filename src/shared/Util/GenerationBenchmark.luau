--!strict
-- Explicit scratch-server experiment runner. Never invoked by production boot.
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")
local Stats = game:GetService("Stats")
local Root = script.Parent.Parent
local ChunkCore = require(Root.Util.ChunkCore)
local ChunkLoader = require(Root.Util.ChunkLoader)
local ChunkDefinitionCache = require(Root.Util.ChunkDefinitionCache)
local GenerationProfile = require(Root.Util.GenerationProfile)
local GenerationAnchors = require(Root.Util.GenerationAnchors)
local PropRegistry = require(Root.Util.PropRegistry)
local ExpeditionCore = require(Root.Core.ExpeditionCore)
local ScenarioCore = require(Root.Util.ScenarioCore)
local Scenarios = require(Root.Content.Scenarios)
local Worlds = require(Root.Content.Worlds)
local Chunks = require(Root.Content.Chunks)
local GameConfig = require(Root.Core.GameConfig)
local GenerationBenchmark = {}
local records = {}
local running = false

local function memory(): number
	return Stats:GetTotalMemoryUsageMb()
end

function GenerationBenchmark.records(): any
	return { Running = running, Records = records }
end

function GenerationBenchmark.run(
	stage: string,
	dependencies: any,
	repeats: number?,
	seeds: { number }?
)
	assert(RunService:IsServer(), "server only")
	assert(not running, "benchmark already running")
	running = true
	local config = GameConfig.GenerationBenchmark
	GenerationAnchors.clear()
	ChunkDefinitionCache.clear()
	local worldProps = if stage >= "D" then PropRegistry.new(Root.Content.Props) else nil
	local assetResolver: any = nil
	local scopedAssets: any = nil
	for repeatIndex = 1, repeats or config.Repeats do
		for _, worldId in config.Worlds do
			for _, seed in seeds or config.Seeds do
				local profile = GenerationProfile.new(stage)
				profile.RequestEpochMs = DateTime.now().UnixTimestampMillis
				profile.MemoryBeforeMb = memory()
				profile.LuaHeapBeforeKb = collectgarbage("count")
				if dependencies.AssetPolicy then
					if not assetResolver then
						assetResolver = require(Root.Util.AssetPreparation).new(
							require(Root.Content.AssetManifest),
							dependencies.AssetPolicy
						)
						scopedAssets = require(Root.Util.AssetRegistry).new(
							require(Root.Content.AssetManifest),
							Chunks
						)
						profile.Times.TemplateIndex = assetResolver.ResolveSeconds
					end
					profile.AssetResolver = assetResolver
					profile.AssetExperiment = dependencies.AssetPolicy.Id
					profile.AssetPolicy = dependencies.AssetPolicy
					profile.ReferenceYaws = dependencies.ReferenceYaws
				end
				profile.RayBudget = config.RayBudget
				profile.WorldId, profile.Seed, profile.Repeat = worldId, seed, repeatIndex
				local world = Worlds[worldId]
				local propsStarted = os.clock()
				if stage >= "D" then
					profile.PropResolver = worldProps
					profile.PropResolver:GetForWorld(worldId)
				else
					local eager = require(Root.Content.Props)
					profile.PropResolver = { Stats = { ModulesRequired = 0, Hits = 0, Misses = 0 } }
					for _ in eager do
						profile.PropResolver.Stats.ModulesRequired += 1
					end
					function profile.PropResolver:GetForWorld(id: string): any
						return eager[id]
					end
				end
				GenerationProfile.time(profile, "PropRegistry", propsStarted)
				local started = os.clock()
				local ok, layout, attempts = ChunkCore.assembleWithRetry(Chunks, {
					WorldId = worldId,
					PathLength = ExpeditionCore.pathLengthFor(world, GameConfig),
					IncludeSide = GameConfig.Expedition.IncludeSide,
					BranchLength = GameConfig.Expedition.BranchLength,
					MaxRepeats = GameConfig.Expedition.MaxRepeats,
					Generation = world.Generation,
					Profile = profile,
				}, function(attempt)
					return ExpeditionCore.streamFor(seed, attempt)
				end, GameConfig.Expedition.AssemblyAttempts)
				GenerationProfile.time(profile, "Assembly", started)
				profile.LayoutSolvedSeconds = os.clock() - profile.Started
				profile.AssemblyAttempts = attempts
				if not ok then
					profile.Failure = tostring(layout)
				else
					local valid, errors = ChunkCore.validateLayout(layout, Chunks)
					profile.LayoutErrors = errors
					profile.StructuralValid = valid
					layout.Seed = seed
					local planOk, plan = ScenarioCore.assign(layout, Chunks, Scenarios, {
						FateInterventionChance = GameConfig.Expedition.FateInterventionChance,
						RecentMemory = GameConfig.Expedition.ScenarioRecentMemory,
						EscalateFrom = GameConfig.Expedition.ScenarioEscalateFrom,
					}, ExpeditionCore.streamFor(
						seed,
						GameConfig.Expedition.ScenarioStreamOffset
					))
					if planOk then
						layout.ScenarioPlan = plan
					end
					layout.Atmosphere = dependencies.atmosphereFor(worldId, seed)
					profile.Atmosphere = layout.Atmosphere
					if assetResolver then
						local startedSet = os.clock()
						local registry = require(Root.Util.AssetRegistry)
						local manifest = require(Root.Content.AssetManifest)
						local requests = registry.requests(layout, Chunks, manifest)
						profile.WorkingSetAssets = #requests
						if dependencies.AssetPolicy.WorldRegistry then
							local startedRegistry = os.clock()
							local view = scopedAssets:GetWorld(worldId)
							for _, request in requests do
								if not view[request.Key] then
									view[request.Key] = {
										AssetId = manifest.assetId(request.Key),
										VisualOnly = request.VisualOnly,
									}
								end
							end
							assetResolver.Manifest = {
								assetId = function(key)
									return view[key] and view[key].AssetId
								end,
							}
							local count = 0
							for _ in view do
								count += 1
							end
							profile.WorldRegistryAssets = count
							GenerationProfile.time(profile, "WorldAssetRegistry", startedRegistry)
						end
						if dependencies.AssetPolicy.Prepare == "World" then
							local view = scopedAssets:GetWorld(worldId)
							requests = {}
							for key, entry in view do
								table.insert(requests, { Key = key, VisualOnly = entry.VisualOnly })
							end
							table.sort(requests, function(a, b)
								return a.Key < b.Key
							end)
						end
						GenerationProfile.time(profile, "WorkingSet", startedSet)
						if dependencies.AssetPolicy.Prepare then
							assetResolver:prepare(
								requests,
								dependencies.AssetPolicy.Workers or 1,
								profile
							)
						end
						profile.AssetsPreparedSeconds = os.clock() - profile.Started
					end
					local built = ChunkLoader.build(
						layout,
						Chunks,
						Vector3.new(0, dependencies.FloorY, 0),
						Workspace,
						"GenerationBenchmark",
						profile
					)
					profile.BlockoutCount = built.FloorCount
					profile.MaterializationReadySeconds = os.clock() - profile.Started
					profile.CollisionReadySeconds = profile.MaterializationReadySeconds
					profile.PlayerPlacementMeasured = false
					if dependencies.player then
						local entryId = layout.Chunks[1].ChunkId
						local entry = built.Model:FindFirstChild(
							tostring(layout.Chunks[1].Index) .. "_" .. entryId
						)
						local meshes, collision = 0, 0
						for _, part in entry:GetDescendants() do
							if part:IsA("MeshPart") and part.Transparency < 1 then
								meshes += 1
							end
							if part:IsA("BasePart") and part.CanCollide then
								collision += 1
							end
						end
						built.Model:SetAttribute("ExpectedEntryMeshes", meshes)
						built.Model:SetAttribute("ExpectedEntryCollision", collision)
						built.Model:SetAttribute("EntryFolder", entry.Name)
						built.Model:SetAttribute("RequestEpochMs", profile.RequestEpochMs)
						built.Model:SetAttribute(
							"MaterializationReadyEpochMs",
							DateTime.now().UnixTimestampMillis
						)
					end
					if assetResolver then
						profile.VisualSignatures = {}
						for _, descendant in built.Model:GetDescendants() do
							if descendant:IsA("MeshPart") and descendant.Transparency < 1 then
								local folder = descendant.Parent
								while folder and folder.Parent ~= built.Model do
									folder = folder.Parent
								end
								if folder then
									local id = folder:GetAttribute("ChunkId")
									local key = (id or "") .. ":" .. descendant.Name
									profile.VisualSignatures[key] = {
										MeshId = descendant.MeshId,
										TextureID = descendant.TextureID,
										Material = descendant.Material.Name,
										Color = {
											descendant.Color.R,
											descendant.Color.G,
											descendant.Color.B,
										},
										Size = {
											descendant.Size.X,
											descendant.Size.Y,
											descendant.Size.Z,
										},
									}
								end
							end
						end
					end
					profile.ArtYaws = {}
					for _, folder in built.Model:GetChildren() do
						local id = folder:GetAttribute("ChunkId")
						if id then
							profile.ArtYaws[id] = folder:GetAttribute("ArtYawOffset")
						end
					end
					local members = {}
					dependencies.prepare(built, worldId, members)
					profile.StructureSeconds = os.clock() - profile.Started
					if assetResolver then
						profile.UniqueAssetLoads, profile.DuplicateAssetLoads = 0, 0
						for _, count in profile.CreatedAssets or {} do
							profile.UniqueAssetLoads += 1
							profile.DuplicateAssetLoads += count - 1
						end
						profile.TemplateCacheEntries = 0
						profile.RuntimeTemplateInstances = 0
						profile.CumulativeUniqueAssetLoads = 0
						for _ in assetResolver.Loads do
							profile.CumulativeUniqueAssetLoads += 1
						end
						for _, template in assetResolver.Templates do
							profile.TemplateCacheEntries += 1
							if template.Parent == nil then
								profile.RuntimeTemplateInstances += 1
							end
						end
					end
					local done = false
					local restorePlacement: any = nil
					local anchors
					local function atmosphere()
						local success, value =
							pcall(GenerationAnchors.scan, built.Model, dependencies.FloorY, profile)
						if success then
							anchors = value
						else
							profile.AtmosphereError = tostring(value)
						end
						profile.CompletionSeconds = os.clock() - profile.Started
						profile.ServerPresentationReadySeconds = profile.CompletionSeconds
						done = true
					end
					if stage >= "E" then
						task.defer(atmosphere)
						if dependencies.player then
							restorePlacement =
								dependencies.placePlayer(dependencies.player, built, profile)
						end
						profile.PlayableSeconds = profile.SafePlayerReadySeconds
							or profile.StructureSeconds
					else
						atmosphere()
						if dependencies.player then
							restorePlacement =
								dependencies.placePlayer(dependencies.player, built, profile)
						end
						profile.PlayableSeconds = profile.SafePlayerReadySeconds
							or profile.CompletionSeconds
					end
					while not done do
						RunService.Heartbeat:Wait()
					end
					profile.CompletionSeconds =
						math.max(profile.CompletionSeconds, profile.SafePlayerReadySeconds or 0)
					if dependencies.verify then
						dependencies.verify(built, layout, profile)
					end
					profile.TipCount = if anchors then #anchors.Tips else 0
					profile.PathCount = if anchors then #anchors.Path else 0
					profile.MemoryAfterMb = memory()
					if assetResolver then
						profile.MemoryPeakObservedMb =
							math.max(profile.MemoryPeakObservedMb or 0, profile.MemoryAfterMb)
					end
					profile.MemoryDeltaMb = profile.MemoryAfterMb - profile.MemoryBeforeMb
					profile.LuaHeapAfterKb = collectgarbage("count")
					profile.AnchorCache = GenerationAnchors.stats()
					profile.TotalRaycasts = (profile.Counters.PlacementRaycasts or 0)
						+ (profile.Counters.AtmosphereRaycasts or 0)
					if dependencies.player then
						local observationStarted = os.clock()
						while
							os.clock() - observationStarted
							< GameConfig.ChunkRuntime.StreamTimeoutSeconds
						do
							RunService.Heartbeat:Wait()
						end
					end
					if restorePlacement then
						restorePlacement()
					end
					built.Model:Destroy()
				end
				profile.PropResolver = nil
				profile.AssetResolver = nil
				profile.ReferenceYaws = nil
				table.insert(records, profile)
				print(
					string.format(
						"[GenerationBenchmark] %s %s seed %d repeat %d: playable %.3f complete %.3f rays %d",
						stage,
						worldId,
						seed,
						repeatIndex,
						profile.PlayableSeconds or -1,
						profile.CompletionSeconds or -1,
						profile.TotalRaycasts or 0
					)
				)
				RunService.Heartbeat:Wait()
			end
		end
	end
	if assetResolver then
		local retained = records[#records]
		retained.CacheRetentionBeforeDestroyMb = memory()
		retained.CacheInstancesBeforeDestroyMb =
			Stats:GetMemoryUsageMbForTag(Enum.DeveloperMemoryTag.Instances)
		assetResolver:destroy()
		RunService.Heartbeat:Wait()
		retained.CacheRetentionAfterDestroyMb = memory()
		retained.CacheInstancesAfterDestroyMb =
			Stats:GetMemoryUsageMbForTag(Enum.DeveloperMemoryTag.Instances)
	end
	running = false
end

return GenerationBenchmark
