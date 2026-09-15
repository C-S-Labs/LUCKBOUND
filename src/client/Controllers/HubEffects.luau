--!strict
-- Drives every animated element in the Crossroads. Biome Blueprint §2.2.
--
-- All of it runs client-side: these are cosmetic, and animating them on the
-- server would replicate a CFrame change per part per frame to every player
-- for no gameplay benefit. Parts carry their own speed as attributes, set by
-- HubBuilder, so this controller reads data rather than knowing the layout.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local Layout = require(Root.Content.Hub.Crossroads)
local PortalRig = require(Root.Util.PortalRig)

local HubEffects = {}

local engineRig: Model? = nil
local gateRig: Model? = nil
local featuredIndex = 0

local function findRigs()
	local hub = Workspace:FindFirstChild(Constants.NAMES.CROSSROADS)
	if not hub then
		return
	end

	local engine = hub:FindFirstChild(Constants.NAMES.FATE_ENGINE)
	engineRig = engine and engine:FindFirstChild("EngineRig") :: Model?

	local zones = hub:FindFirstChild("Zones")
	local gate = zones and zones:FindFirstChild("EXPEDITION_GATE")
	gateRig = gate and gate:FindFirstChild("GateRig") :: Model?
end

--- Plays the 2.5s spin-up on both rigs, coloured to the rolled rarity.
--- Blueprint §1.3: this beat happens BEFORE the destination banner.
function HubEffects.spinUpForRoll(rarityKey: string): ()
	if engineRig then
		PortalRig.playSpinUp(engineRig, rarityKey)
	end
	if gateRig then
		PortalRig.playSpinUp(gateRig, rarityKey)
	end
end

function HubEffects.settle(): ()
	if engineRig then
		PortalRig.setIdle(engineRig)
		PortalRig.setRarity(engineRig, Constants.RARITY.UNKNOWN.Key)
	end
	if gateRig then
		PortalRig.setIdle(gateRig)
	end
end

--- Cosmetic rarity cycle on the Engine's crystal shards. Explicitly NOT a
--- prediction of the next roll -- the roll is true RNG and nothing in the hub
--- may imply otherwise.
local function cycleFeaturedRarity(shards: { BasePart })
	local keys = {}
	for key in Constants.RARITY do
		table.insert(keys, key)
	end
	table.sort(keys)

	featuredIndex = featuredIndex % #keys + 1
	local color = Constants.RARITY[keys[featuredIndex]].Color

	for _, shard in shards do
		TweenService:Create(shard, TweenInfo.new(1.6), { Color = color }):Play()
	end
end

function HubEffects.init(): ()
	task.spawn(function()
		-- The hub is built during server bootstrap; wait for it rather than
		-- assuming it exists when the client starts.
		local hub = Workspace:WaitForChild(Constants.NAMES.CROSSROADS, 30)
		if not hub then
			warn("[HubEffects] Crossroads never appeared; hub animation disabled")
			return
		end

		findRigs()
		if engineRig then
			PortalRig.animate(engineRig)
		end
		if gateRig then
			PortalRig.animate(gateRig)
		end

		local shards: { BasePart } = {}
		local orbiters: { BasePart } = {}
		local spinners: { BasePart } = {}

		for _, descendant in hub:GetDescendants() do
			if not descendant:IsA("BasePart") then
				continue
			end
			if descendant:GetAttribute("IsFeaturedShard") then
				table.insert(shards, descendant)
				table.insert(spinners, descendant)
			elseif descendant:GetAttribute("IsOrrery") then
				table.insert(spinners, descendant)
			elseif descendant:GetAttribute("OrbitRadius") then
				table.insert(orbiters, descendant)
			end
		end

		local elapsed = 0
		RunService.Heartbeat:Connect(function(dt)
			elapsed += dt

			for _, spinner in spinners do
				local speed = spinner:GetAttribute("SpinSpeed") or 0.2
				spinner.CFrame = spinner.CFrame * CFrame.Angles(0, speed * dt, 0)
			end

			-- Shelves orbit the Archive's centre at their own radius and speed.
			for _, shelf in orbiters do
				local radius = shelf:GetAttribute("OrbitRadius") :: number
				local speed = shelf:GetAttribute("OrbitSpeed") :: number
				local height = shelf:GetAttribute("OrbitHeight") :: number
				local centre = shelf:GetAttribute("OrbitCentre") :: Vector3?
				if centre then
					local angle = elapsed * speed
					shelf.CFrame = CFrame.new(
						centre.X + math.cos(angle) * radius,
						height,
						centre.Z + math.sin(angle) * radius
					) * CFrame.Angles(0, -angle, 0)
				end
			end
		end)

		if #shards > 0 then
			task.spawn(function()
				while true do
					cycleFeaturedRarity(shards)
					task.wait(Layout.FateEngine.FeaturedCycleSeconds)
				end
			end)
		end
	end)
end

return HubEffects
