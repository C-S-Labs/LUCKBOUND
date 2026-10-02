--!strict
-- Full VV catalogue parity with an injected production-baseline loader.
local Root = game.ReplicatedStorage.Luckbound
local Loader = require(Root.Util.ChunkLoader)
local Preparation = require(Root.Util.AssetPreparation)
local Core = require(Root.Util.ChunkCore)
local Chunks = require(Root.Content.Chunks)
local Manifest = require(Root.Content.AssetManifest)
local Config = require(Root.Core.GameConfig)
local Geometry = require(Root.Util.ProductionGeometryVerification)
local Check = {}

function Check.run(control: any): any
	local ok, layout = Core.assembleTest(Chunks, "VERDANT_VALLEY", Config.Debug.TestChunkGap)
	assert(ok, layout)
	local owner = Preparation.new(Manifest, Config.Expedition)
	local holder = Instance.new("Folder")
	holder.Name = "ProductionLoaderFixture"
	holder.Parent = workspace
	local prepared = Loader.prepare(layout, Chunks, owner)
	assert(prepared.ok, prepared.err)
	local baseline = control.build(layout, Chunks, Vector3.new(0, 35000, 0), holder, "Control")
	local optimized =
		Loader.build(layout, Chunks, Vector3.new(0, 37000, 0), holder, "Prepared", owner)
	game:GetService("RunService").Heartbeat:Wait()
	local yawMatches, proxyFlags = 0, 0
	for _, folder in optimized.Model:GetChildren() do
		local prior = baseline.Model:FindFirstChild(folder.Name)
		local mesh = folder:FindFirstChild("Mesh") :: MeshPart
		local priorMesh = prior and prior:FindFirstChild("Mesh") :: MeshPart
		assert(mesh and priorMesh and not folder:GetAttribute("Blockout"), "missing visual")
		assert(
			(mesh.CFrame.LookVector - priorMesh.CFrame.LookVector).Magnitude < 0.0001,
			folder.Name
		)
		yawMatches += 1
		assert(
			not mesh.CanCollide and not mesh.CanQuery and not mesh.CanTouch,
			"proxy visual flags"
		)
		local collision = folder:FindFirstChild("WalkCollision")
		assert(collision, "missing authored collision")
		for _, part in collision:GetDescendants() do
			if part:IsA("BasePart") then
				assert(
					part.CanCollide
						and part.CanQuery
						and not part.CanTouch
						and part.Transparency == 1,
					"authored proxy flags"
				)
				proxyFlags += 1
			end
		end
	end
	local result = {
		Chunks = yawMatches,
		ProxyParts = proxyFlags,
		Cache = owner:stats(),
		Control = Geometry.sample(baseline.Model, layout, Chunks, 35000),
		Prepared = Geometry.sample(optimized.Model, layout, Chunks, 37000),
	}
	assert(yawMatches == 30, "incomplete VV catalogue")
	assert(owner:stats().TemplateClones == 30, "catalogue did not exercise prepared templates")
	holder:Destroy()
	owner:destroy()
	return result
end

return Check
