--!strict
-- LightningController: makes WeaponFX crackle Beams (tag "CrackleBeam") re-shape now and then by bending their curves
-- a little at random, so strands look alive rather than only scrolling. Purely cosmetic and cheap: only Beams
-- within MAX_DIST of the camera are touched, ~8 times a second. The weapon looks complete without it (the web is
-- real geometry; the Beams still scroll and glow on their own).

local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local WeaponFX = require(ReplicatedStorage:WaitForChild("Luckbound").Util.WeaponFX)

local LightningController = {}

local RATE = 1 / 8
local BEND = 0.35 -- curve size as a fraction of the strand's length
local MAX_DIST = 250

function LightningController.init(): ()
	local rng = Random.new()
	local acc = 0
	-- charged weapons: re-open the blade halves every frame, after the Animator has written its pose
	RunService.PreRender:Connect(function()
		for _, model in CollectionService:GetTagged("WeaponFXModel") do
			if model:IsA("Model") and model:GetAttribute("Charged") == true then
				WeaponFX.applySlide(model)
			end
		end
	end)
	RunService.RenderStepped:Connect(function(dt)
		acc += dt
		if acc < RATE then
			return
		end
		acc = 0
		local cam = workspace.CurrentCamera
		if not cam then
			return
		end
		for _, beam in CollectionService:GetTagged("CrackleBeam") do
			if beam:IsA("Beam") and beam.Enabled and beam.Attachment0 then
				local p = (beam.Attachment0 :: Attachment).WorldPosition
				if (p - cam.CFrame.Position).Magnitude <= MAX_DIST then
					local span = (beam:GetAttribute("Span") :: number?) or 1
					beam.CurveSize0 = rng:NextNumber(-BEND, BEND) * span
					beam.CurveSize1 = rng:NextNumber(-BEND, BEND) * span
				end
			end
		end
	end)
end

return LightningController
