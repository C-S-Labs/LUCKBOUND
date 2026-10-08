--!strict
-- Opt-in bounded Studio client fixture; NOT included in the Rojo project.
-- Parent a temporary copy to StarterPlayerScripts, Play, then remove it.
local RunService = game:GetService("RunService")
assert(RunService:IsStudio(), "Diagnostic fixture is Studio-only")
local data: any = require(game.ReplicatedStorage.EmberfallWalkthroughData)
local service = game:GetService("AssetService")
local groups = { terrain = {}, grass = {} }
for _, record in data.assets do
	if groups[record.role] then
		table.insert(groups[record.role], record.key)
	end
end
local function measure(name: string, keys: { string })
	local retained = {}
	local samples = {}
	local start = os.clock()
	for _, key in keys do
		local allocationStart = os.clock()
		local ok, mesh = pcall(function()
			return service:CreateEditableMeshAsync(
				Content.fromUri(data.ids[key]),
				{ FixedSize = true }
			)
		end)
		local sample: any =
			{ key = key, seconds = os.clock() - allocationStart, ok = ok and mesh ~= nil }
		if ok and mesh then
			sample.vertices, sample.faces, sample.colors =
				#mesh:GetVertices(), #mesh:GetFaces(), #mesh:GetColors()
			table.insert(retained, mesh)
		else
			sample.failure = ok and "nil allocation" or tostring(mesh)
		end
		table.insert(samples, sample)
		if not sample.ok then
			break
		end
		task.wait()
	end
	local result =
		{ name = name, samples = samples, retained = #retained, seconds = os.clock() - start }
	for _, mesh in retained do
		mesh:Destroy()
	end
	task.wait(1)
	return result
end
local combined = table.clone(groups.terrain)
for _, key in groups.grass do
	table.insert(combined, key)
end
local result = {
	measure("terrain", groups.terrain),
	measure("grass", groups.grass),
	measure("terrain+grass", combined),
}
script:SetAttribute("Results", game:GetService("HttpService"):JSONEncode(result))
print("[SceneryAllocationProbe]", script:GetAttribute("Results"))
