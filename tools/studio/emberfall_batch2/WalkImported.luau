--!strict
-- Explicit Client command, never automatically executed by the review place.
-- Normal ControllerManager input; one entry placement, no further translation.
local data: any = require(game.ReplicatedStorage.EmberfallBatch2ReviewData)
local world = workspace.ExpeditionStage.EmberfallBatch2Review
local player = game.Players.LocalPlayer
local character = player.Character
assert(
	character and character:FindFirstChildOfClass("ControllerManager"),
	"Normal controller not ready"
)
local humanoid = character:FindFirstChildOfClass("Humanoid") :: Humanoid
local root = character:FindFirstChild("HumanoidRootPart") :: BasePart
local origin = world:GetAttribute("Origin") :: Vector3
local route = data.route
local run = game:GetService("RunService")
workspace:SetAttribute("EmberfallBatch2ImportedWalkStatus", "Running")
task.spawn(function()
	local index = 14
	local initial = origin + Vector3.new(unpack(route[index], 1, 3))
	character:PivotTo(CFrame.new(initial + Vector3.new(0, 3.2, 0)))
	root.AssemblyLinearVelocity = Vector3.zero
	task.wait(0.7)
	local started, lastProgress, prior = os.clock(), os.clock(), index
	local lowest, maximumCrossTrack = humanoid.Health, 0
	local crossed = {}
	run:BindToRenderStep(
		"EmberfallBatch2ImportedWalkInput",
		Enum.RenderPriority.Input.Value + 1,
		function()
			local destination = origin + Vector3.new(unpack(route[index], 1, 3))
			local delta = destination - root.Position
			local flat = Vector3.new(delta.X, 0, delta.Z)
			if flat.Magnitude < 3 and index < #route - 2 then
				index += 1
			end
			humanoid:Move(if flat.Magnitude > 0.01 then flat.Unit else Vector3.zero, false)
		end
	)
	while os.clock() - started < 420 and index < #route - 2 and humanoid.Health > 0 do
		task.wait(0.2)
		lowest = math.min(lowest, humanoid.Health)
		if index ~= prior then
			lastProgress, prior = os.clock(), index
		end
		if os.clock() - lastProgress > 15 then
			break
		end
		local nearestDistance, nearest
		for i, row in data.rows do
			local position = origin + Vector3.new(row.x, row.y, row.z)
			local distance = (Vector3.new(root.Position.X, 0, root.Position.Z) - Vector3.new(
				position.X,
				0,
				position.Z
			)).Magnitude
			if not nearestDistance or distance < nearestDistance then
				nearestDistance, nearest = distance, i
			end
		end
		if nearest then
			crossed[tostring(nearest)] = true
		end
		workspace:SetAttribute("EmberfallBatch2ImportedWalkProgress", index)
		local target = origin + Vector3.new(unpack(route[index], 1, 3))
		maximumCrossTrack = math.max(
			maximumCrossTrack,
			(Vector3.new(target.X, 0, target.Z) - Vector3.new(root.Position.X, 0, root.Position.Z)).Magnitude
		)
	end
	run:UnbindFromRenderStep("EmberfallBatch2ImportedWalkInput")
	humanoid:Move(Vector3.zero, false)
	local result = {
		completed = index >= #route - 2,
		waypoint = index,
		total = #route,
		seconds = os.clock() - started,
		health = lowest,
		visitedPlacements = crossed,
		maximumWaypointDistance = maximumCrossTrack,
		position = { root.Position.X, root.Position.Y, root.Position.Z },
		controller = "ControllerManager",
		translationAfterEntry = false,
	}
	workspace:SetAttribute(
		"EmberfallBatch2ImportedWalkResult",
		game:GetService("HttpService"):JSONEncode(result)
	)
	workspace:SetAttribute("EmberfallBatch2ImportedWalkStatus", "Finished")
end)
return "Full repeated-source route queued using normal movement input"
