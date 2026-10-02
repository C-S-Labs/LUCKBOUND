--!strict
-- Client-only real-instance invariant: anchors must not destroy moving scenery.
local effects = require(script.Parent.AtmosphereEffects)
local props = game.ReplicatedStorage:FindFirstChild("LuckboundProps")
assert(props, "prop library missing")
local fixtures = {}
local fixtureFolder = Instance.new("Folder")
fixtureFolder.Name = "GenerationAtmosphereFixture"
fixtureFolder.Parent = props
for _, name in { "atm_security_probe", "atm_alarm_beacon" } do
	if not props:FindFirstChild(name, true) then
		local part = Instance.new("Part")
		part.Name = name
		part.Size = Vector3.new(2, 2, 2)
		part.Parent = fixtureFolder
		table.insert(fixtures, part)
	end
end
assert(
	not workspace:FindFirstChild("LuckboundAtmosphere"),
	"existing atmosphere must remain untouched"
)
local stage = Instance.new("Model")
stage.Name = "AtmosphereLateUpdateFixture"
stage.Parent = workspace
local anchors = {
	Min = Vector3.new(-128, 20000, -128),
	Max = Vector3.new(128, 20256, 128),
	Tips = {},
	Path = {},
	Pending = true,
}
effects.enter({}, Vector3.new(0, 20000, 0), stage.Name, "LOCKDOWN", anchors)
local folder = workspace:FindFirstChild("LuckboundAtmosphere")
assert(folder, "initial effects absent")
local probe = folder:FindFirstChild("atm_security_probe", true)
assert(probe and probe:IsA("BasePart"), "moving actor absent")
local initial = probe.CFrame
local updated = {
	Min = anchors.Min,
	Max = anchors.Max,
	Tips = { Vector3.new(0, 20160, 0) },
	Path = { Vector3.new(0, 20000, 0), Vector3.new(0, 20000, 64) },
}
assert(effects.updateAnchors(updated), "late anchors rejected")
assert(
	workspace:FindFirstChild("LuckboundAtmosphere") == folder,
	"late update replaced effect root"
)
assert(probe.Parent and probe.CFrame == initial, "late update reset/destroyed flyer")
assert(folder:FindFirstChild("atm_alarm_beacon", true), "late lights not initialized")
local count = #folder:GetDescendants()
assert(
	effects.updateAnchors(updated) and #folder:GetDescendants() == count,
	"duplicate packet duplicated lights"
)
effects.leave()
assert(not folder.Parent, "leave retained effects")
assert(not effects.updateAnchors(updated), "late packet resurrected departed effects")
stage:Destroy()
for _, part in fixtures do
	part:Destroy()
end
fixtureFolder:Destroy()
return { Passed = 9 }
