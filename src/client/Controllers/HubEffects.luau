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

		-- Wait for the server to say the hub is FINISHED, not merely present.
		-- WaitForChild returns as soon as the Crossroads model itself
		-- replicates, which with an authored Fate Engine is well before its
		-- ~80 MeshParts have arrived. Scanning at that moment finds no
		-- EngineRig and no shards, so nothing animates for the whole session
		-- and the cause looks like the animation code rather than timing.
		if not hub:GetAttribute("Ready") then
			hub:GetAttributeChangedSignal("Ready"):Wait()
		end

		findRigs()
		if engineRig then
			PortalRig.animate(engineRig)
		end
		if gateRig then
			PortalRig.animate(gateRig)
		end

		-- ONE DATA-DRIVEN ANIMATOR for everything in the hub that moves.
		--
		-- It used to be two paths: this loop, which only ever looked for
		-- IsFeaturedShard, and PortalRig.animate, which found the rings by
		-- name through the EngineRig lookup. The shards moved and the rings
		-- did not, across two playtests -- and because the two paths fail
		-- differently, the symptom looked like an anchoring or replication
		-- problem rather than "the rings were never in the list".
		--
		-- Now anything carrying a SpinSpeed, BobStuds, PulseScale or
		-- PulseAlphaMin attribute animates, wherever it sits in the hub and
		-- whoever put it there. Adding motion to an authored part is a line in
		-- the content paint table, not a code change.
		local animated: { any } = {}
		local shards: { BasePart } = {}
		local orbiters: { BasePart } = {}

		local AXES: { [string]: Vector3 } = {
			X = Vector3.xAxis,
			Y = Vector3.yAxis,
			Z = Vector3.zAxis,
		}

		local function consider(part: BasePart)
			if part:GetAttribute("IsFeaturedShard") then
				table.insert(shards, part)
			end
			if part:GetAttribute("OrbitRadius") then
				table.insert(orbiters, part)
				return
			end

			local spin = part:GetAttribute("SpinSpeed") :: number?
			local bob = part:GetAttribute("BobStuds") :: number?
			local pulse = part:GetAttribute("PulseScale") :: number?
			local alphaMin = part:GetAttribute("PulseAlphaMin") :: number?
			if not (spin or bob or pulse or alphaMin) then
				return
			end

			-- A deterministic per-part phase, so six shards do not bob in
			-- lockstep like a machine. Derived from the name rather than
			-- random, so it is the same every join.
			local phase = 0
			for k = 1, #part.Name do
				phase = (phase * 31 + string.byte(part.Name, k)) % 1000
			end

			table.insert(animated, {
				Part = part,
				-- The rotation is accumulated as an ANGLE and the CFrame is
				-- rebuilt from a captured base each frame. Multiplying into
				-- the live CFrame instead would let the bob offset compound
				-- and walk the part away from where the artist put it.
				Base = part.CFrame,
				BaseSize = part.Size,
				Angle = 0,
				Spin = spin,
				Axis = AXES[(part:GetAttribute("SpinAxis") :: string?) or "Y"] or Vector3.yAxis,
				Bob = bob,
				BobSeconds = (part:GetAttribute("BobSeconds") :: number?) or 4,
				Pulse = pulse,
				PulseSeconds = (part:GetAttribute("PulseSeconds") :: number?) or 3.5,
				AlphaMin = alphaMin,
				AlphaMax = (part:GetAttribute("PulseAlphaMax") :: number?) or 0.7,
				Phase = phase / 1000 * math.pi * 2,
			})
		end

		for _, descendant in hub:GetDescendants() do
			if descendant:IsA("BasePart") then
				consider(descendant)
			end
		end

		print(
			string.format(
				"[HubEffects] animating %d part(s), %d shard(s), %d orbiter(s); engineRig %s",
				#animated,
				#shards,
				#orbiters,
				if engineRig then "found" else "MISSING"
			)
		)

		-- Belt and braces: anything tagged that arrives after the scan still
		-- animates. Streaming, or a part added by a later system, would
		-- otherwise sit still with no way to tell why.
		hub.DescendantAdded:Connect(function(descendant)
			if descendant:IsA("BasePart") then
				consider(descendant)
			end
		end)

		local elapsed = 0
		RunService.Heartbeat:Connect(function(dt)
			elapsed += dt

			for _, a in animated do
				local part = a.Part
				local moved = false
				local cf = a.Base

				if a.Spin then
					a.Angle += a.Spin * dt
					cf = cf * CFrame.fromAxisAngle(a.Axis, a.Angle)
					moved = true
				end
				if a.Bob then
					local t = math.sin(elapsed / a.BobSeconds * math.pi * 2 + a.Phase)
					cf = cf + Vector3.new(0, t * a.Bob, 0)
					moved = true
				end
				if moved then
					part.CFrame = cf
				end

				if a.Pulse then
					local t = (math.sin(elapsed / a.PulseSeconds * math.pi * 2 + a.Phase) + 1) / 2
					part.Size = a.BaseSize * (1 - a.Pulse + a.Pulse * 2 * t)
				end
				if a.AlphaMin then
					local t = (math.sin(elapsed / a.PulseSeconds * math.pi * 2 + a.Phase) + 1) / 2
					part.Transparency = a.AlphaMin + (a.AlphaMax - a.AlphaMin) * t
				end
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
