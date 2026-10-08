--!strict
-- Manually invoked isolated Play-server check. No production content or imports.
local Probe = {}

function Probe.run(): any
	assert(workspace:FindFirstChild("EmberfallEdgeProfileProbe"), "Missing isolated colliders")
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { workspace.EmberfallEdgeProfileProbe }
	local results = {}
	for _, test in
		{
			{
				name = "A_B2",
				start = Vector3.new(10000, 103, -124),
				finish = Vector3.new(10000, 103, -132),
			},
			{
				name = "B2_C_rotated",
				start = Vector3.new(10124, 127, -256),
				finish = Vector3.new(10132, 127, -256),
			},
		}
	do
		local description = Instance.new("HumanoidDescription")
		local rig = game:GetService("Players")
			:CreateHumanoidModelFromDescriptionAsync(description, Enum.HumanoidRigType.R15)
		description:Destroy()
		rig.Name = "EmberfallEdgeProbeCharacter"
		rig.Parent = workspace
		local root = rig:FindFirstChild("HumanoidRootPart") :: BasePart
		local humanoid = rig:FindFirstChildOfClass("Humanoid") :: Humanoid
		local floor = workspace:Raycast(
			Vector3.new(test.start.X, 250, test.start.Z),
			Vector3.new(0, -220, 0),
			params
		)
		assert(floor, "Missing seam approach floor")
		local start = Vector3.new(test.start.X, floor.Position.Y + 3, test.start.Z)
		local finish = Vector3.new(test.finish.X, start.Y, test.finish.Z)
		rig:PivotTo(CFrame.new(start) * root.CFrame:Inverse() * rig:GetPivot())
		root:SetNetworkOwner(nil)
		humanoid.WalkSpeed = 8
		task.wait(0.35)
		humanoid:MoveTo(finish)
		local started = os.clock()
		local minimumY = root.Position.Y
		while os.clock() - started < 2.5 do
			minimumY = math.min(minimumY, root.Position.Y)
			if
				(Vector3.new(root.Position.X, 0, root.Position.Z) - Vector3.new(
					test.finish.X,
					0,
					test.finish.Z
				)).Magnitude < 1
			then
				break
			end
			task.wait(0.1)
		end
		local distance = (Vector3.new(root.Position.X, 0, root.Position.Z) - Vector3.new(
			test.finish.X,
			0,
			test.finish.Z
		)).Magnitude
		table.insert(
			results,
			{
				name = test.name,
				pass = distance < 1 and minimumY > start.Y - 1,
				distanceToTarget = distance,
				minimumRootY = minimumY,
				seconds = os.clock() - started,
				floorMaterial = humanoid.FloorMaterial.Name,
			}
		)
		rig:Destroy()
	end
	return results
end

return Probe
