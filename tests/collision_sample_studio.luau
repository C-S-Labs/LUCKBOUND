--!strict
-- Two complex SC chunks, four rotations, three repeated paired samples.
local root = game.ReplicatedStorage.LuckboundAssetExperiment
local Loader = require(root.Util.ChunkLoader)
local Profile = require(root.Util.GenerationProfile)
local Preparation = require(root.Util.AssetPreparation)
local Proxy = require(root.Util.CollisionProxySample)
local Check = require(root.Util.AssetGeometryCheck)
local samples = require(root.Content.CollisionSamples)
local chunks = require(root.Content.Chunks)
local manifest = require(root.Content.AssetManifest)
local stats = game:GetService("Stats")
local kits = game.ServerStorage.LuckboundChunkKits
local folder = Instance.new("Folder")
folder.Name = "LuckboundCollisionExperiment"
folder.Parent = kits
local ids = {}
for id in samples do
	table.insert(ids, id)
end
table.sort(ids)
local models = {}
for _, id in ids do
	models[id] = Proxy.build("EXPERIMENT_" .. id, samples[id], folder)
end
local records = {}
root:SetAttribute("CollisionSampleRunning", true)
task.spawn(function()
	local ok, err = pcall(function()
		for repeatIndex = 1, 3 do
			for _, id in ids do
				for _, yaw in { 0, 90, 180, 270 } do
					local reference
					for _, mode in { "CONTROL", "PROXY" } do
						local definitions = table.clone(chunks)
						local chunk = table.clone(chunks[id])
						definitions[id] = chunk
						if mode == "PROXY" then
							chunk.CollisionTemplate = models[id].Name
						end
						local profile = Profile.new("A")
						profile.WorldId = "SKY_CITADEL"
						profile.SampleId = id
						profile.Yaw = yaw
						profile.Repeat = repeatIndex
						profile.Mode = mode
						profile.CollisionDense = true
						profile.ToleranceStuds =
							require(root.Core.GameConfig).GenerationBenchmark.CollisionSampleToleranceStuds
						profile.MemoryBeforeMb = stats:GetTotalMemoryUsageMb()
						profile.AssetResolver = Preparation.new(
							manifest,
							{ LocalTemplates = mode == "PROXY", VisualFidelity = mode == "PROXY" }
						)
						if reference ~= nil then
							profile.ReferenceYaws = { [id .. ":"] = reference }
						end
						local layout = {
							WorldId = "SKY_CITADEL",
							Chunks = {
								{
									ChunkId = id,
									Index = 1,
									Role = "PATH",
									Yaw = yaw,
									X = 0,
									Y = 0,
									Z = 0,
								},
							},
						}
						local built = Loader.build(
							layout,
							definitions,
							Vector3.new(0, 20000, 0),
							workspace,
							"CollisionSample",
							profile
						)
						profile.MaterializationSeconds = os.clock() - profile.Started
						local placed = built.Model:GetChildren()[1]
						if mode == "CONTROL" then
							reference = placed:GetAttribute("ArtYawOffset")
						end
						profile.ArtYaw = placed:GetAttribute("ArtYawOffset")
						profile.ProxyPieces = placed:GetAttribute("WalkCollisionPieces")
						Check.sample(built, layout, profile)
						profile.MemoryAfterMb = stats:GetTotalMemoryUsageMb()
						profile.MemoryDeltaMb = profile.MemoryAfterMb - profile.MemoryBeforeMb
						built.Model:Destroy()
						profile.AssetResolver:destroy()
						profile.AssetResolver = nil
						profile.ReferenceYaws = nil
						table.insert(records, profile)
					end
				end
			end
		end
	end)
	if not ok then
		root:SetAttribute("CollisionSampleError", tostring(err))
	end
	root:SetAttribute("CollisionSampleRunning", false)
	folder:Destroy()
end)
return {
	records = function()
		return records
	end,
}
