--!strict
-- Owner-authorized Layout1 snapshot. Production EditableMesh allocation remains open.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then
	return
end
local Players = game:GetService("Players")
local Lighting = game:GetService("Lighting")
local RS = game:GetService("ReplicatedStorage")
local data: any = require(RS.EmberfallWalkthroughData)
assert(data.appearanceMode == "Layout1Snapshot", "Unexpected appearance backend")
local player = Players.LocalPlayer
local gui = Instance.new("ScreenGui")
gui.Name = "EmberfallWalkthroughStatus"
gui.ResetOnSpawn = false
gui.Parent = player:WaitForChild("PlayerGui")
local label = Instance.new("TextLabel")
label.Size = UDim2.fromOffset(650, 28)
label.Position = UDim2.new(0.5, -325, 0, 60)
label.BackgroundColor3 = Color3.fromRGB(25, 28, 22)
label.BackgroundTransparency = 0.2
label.TextColor3 = Color3.new(1, 1, 1)
label.TextSize = 16
label.Parent = gui
local function updateStatus()
	label.Text = workspace:GetAttribute("EmberfallWalkthroughStatus") or "Loading Burned Plains"
end
workspace:GetAttributeChangedSignal("EmberfallWalkthroughStatus"):Connect(updateStatus)
updateStatus()
local stages = workspace:WaitForChild("ExpeditionStage", 600)
local world = stages:WaitForChild("EmberfallOwnerWalkthrough", 600)
while not world:GetAttribute("TerrainReady") or not player:GetAttribute("EmberfallWalkthrough") do
	task.wait(0.25)
end
local Loader = require(RS.Luckbound.Util.ChunkLoader)
Loader.applyEnvironment(Lighting, {
	AmbientColor = Color3.fromRGB(90, 90, 80),
	OutdoorAmbientColor = Color3.fromRGB(130, 130, 120),
	ColorShiftTop = Color3.new(0, 0, 0),
	FogColor = Color3.fromRGB(165, 176, 174),
	FogStart = 4000,
	FogEnd = 8000,
	Brightness = 2,
	ClockTime = 14,
})
for _, effect in Lighting:GetChildren() do
	if effect:IsA("Atmosphere") then
		effect.Density = 0.15
		effect.Haze = 0
		effect.Glare = 0
		effect.Color = Color3.fromRGB(190, 199, 185)
		effect.Decay = Color3.fromRGB(125, 130, 119)
	elseif effect:IsA("ColorCorrectionEffect") then
		effect.TintColor = Color3.new(1, 1, 1)
		effect.Contrast = 0
		effect.Saturation = 0
	end
end
workspace:SetAttribute(
	"EmberfallWalkthroughStatus",
	"READY — Layout1 • scenery continuity candidate"
)
world:SetAttribute("AppearanceMode", data.appearanceMode)
print(
	"[EmberfallWalkthrough] Ready: frozen playable snapshot plus baked scenery; zero client EditableMesh copies"
)
