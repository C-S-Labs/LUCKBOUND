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
local GameConfig = require(Root.Core.GameConfig)
local Layout = require(Root.Content.Hub.Crossroads)
local PortalRig = require(Root.Util.PortalRig)

local HubEffects = {}

local engineRig: Model? = nil
local gateRig: Model? = nil
local featuredIndex = 0

--- A stable 0-1 value from a name. See the note at its call site for why the
--- trailing multiply matters -- without it, names that differ only in their
--- last character hash to neighbouring values and every "variation" collapses.
local function hashName(name: string): number
	local h = 0
	for i = 1, #name do
		h = (h * 131 + string.byte(name, i)) % 1000003
	end
	return (h * 2654435761) % 1000003 / 1000003
end

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

--- Ends the reveal. The Engine KEEPS the rolled rarity rather than reverting
--- to UNKNOWN: it is the portal to the world you just rolled, and a player
--- looking at it should be able to see where they are going. Reverting made
--- the Engine disagree with the Gate, which holds the destination colour --
--- reported from the third authored playtest.
function HubEffects.settle(rarityKey: string?): ()
	if engineRig then
		PortalRig.setIdle(engineRig)
		PortalRig.setRarity(
			engineRig,
			rarityKey or Constants.RARITY.UNKNOWN.Key,
			GameConfig.Portal.RarityTweenSeconds
		)
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

	-- A WAVE, not a switch. Every shard taking the same colour at the same
	-- instant is what made six floating crystals read as one machine --
	-- reported from the third authored playtest. Each shard takes the NEXT
	-- rarity along and starts a little after the one before, so the group
	-- always shows a spread and the change travels around the ring.
	for index, shard in shards do
		local key = keys[(featuredIndex + index - 2) % #keys + 1]
		local color = Constants.RARITY[key].Color
		task.delay(0.18 * (index - 1), function()
			if shard.Parent then
				TweenService:Create(shard, TweenInfo.new(1.6), { Color = color }):Play()
			end
		end)
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

		-- ...and then wait for the parts themselves. Ready says the SERVER has
		-- finished; it says nothing about what has reached this client yet.
		-- Without this the scan runs against a half-replicated hub and finds
		-- an EngineRig with no rings inside it.
		local expected = hub:GetAttribute("PartCount") :: number?
		if expected then
			local waited = 0
			while waited < 20 do
				local seen = 0
				for _, d in hub:GetDescendants() do
					if d:IsA("BasePart") then
						seen += 1
					end
				end
				if seen >= expected then
					break
				end
				waited += task.wait(0.1)
			end
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
			local wobble = part:GetAttribute("WobbleDegrees") :: number?
			local colorA = part:GetAttribute("ColorA") :: Color3?
			if not (spin or bob or pulse or alphaMin or wobble or colorA) then
				return
			end

			-- A deterministic per-part phase, so six shards do not bob in
			-- lockstep like a machine. Derived from the name rather than
			-- random, so it is the same every join.
			--
			-- THE SCRAMBLE IS NOT DECORATION. The obvious rolling hash gives
			-- adjacent names adjacent values -- Shard1..Shard6 came out 147,
			-- 148, 149, 150, 151, 152 out of 1000, half a percent apart, so
			-- every crystal got the same phase and the variation code did
			-- nothing for two playtests. The final multiply is what pulls
			-- neighbours apart: the same six now land at .50 .92 .35 .78 .21
			-- .64.
			-- A WavePhase makes a set pulse IN ORDER rather than at random --
			-- eight glyphs lighting one after another around the plinth reads
			-- as the machine thinking, where eight random phases just reads as
			-- flicker. Set from the trailing number in the part's name.
			local phase = (part:GetAttribute("WavePhase") :: number?) or hashName(part.Name)

			table.insert(animated, {
				Part = part,
				-- The rotation is accumulated as an ANGLE and the CFrame is
				-- rebuilt from a captured base each frame. Multiplying into
				-- the live CFrame instead would let the bob offset compound
				-- and walk the part away from where the artist put it.
				Base = part.CFrame,
				BaseSize = part.Size,
				Angle = 0,
				Active = true,
				Spin = spin,
				Axis = AXES[(part:GetAttribute("SpinAxis") :: string?) or "Y"] or Vector3.yAxis,
				Bob = bob,
				BobSeconds = (part:GetAttribute("BobSeconds") :: number?) or 4,
				-- A small oscillating tilt across the spin axis. A ring
				-- turning at a perfectly constant rate on a perfectly fixed
				-- axis is the definition of robotic; a degree or two of sway
				-- is what makes it read as suspended rather than bolted on.
				Wobble = (part:GetAttribute("WobbleDegrees") :: number?),
				WobbleSeconds = (part:GetAttribute("WobbleSeconds") :: number?) or 7,
				-- Varies the spin rate itself, so it is never metronomic.
				Jitter = (part:GetAttribute("SpinJitter") :: number?) or 0,
				Pulse = pulse,
				PulseSeconds = (part:GetAttribute("PulseSeconds") :: number?) or 3.5,
				AlphaMin = alphaMin,
				AlphaMax = (part:GetAttribute("PulseAlphaMax") :: number?) or 0.7,
				-- Drifts between two colours. One mesh cannot be painted two
				-- tones, but it can be both in turn.
				ColorA = colorA,
				ColorB = (part:GetAttribute("ColorB") :: Color3?) or colorA,
				ColorSeconds = (part:GetAttribute("ColorSeconds") :: number?) or 6,
				Phase = phase * math.pi * 2,
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

		-- PERFORMANCE. This loop runs every frame on every player's machine,
		-- including the low-end phones the §6 checklist budgets for, so it is
		-- built around doing as little as possible:
		--
		--   1. Parts further than Effects.AnimationDistance from the camera do
		--      not animate at all. The hub is 1150 studs across; most of what
		--      is tagged is off screen or a speck for most of the session.
		--   2. The distance check itself is throttled -- per part per frame it
		--      would cost more than the animation it protects.
		--   3. Size and Transparency are written at Effects.SlowUpdateSeconds,
		--      not every frame. A Size change on a MeshPart re-scales the
		--      mesh, which is far more expensive than a CFrame write, and at
		--      20 Hz a slow breath is indistinguishable from 60.
		--
		-- Only CFrame runs at full rate, because motion is what the eye
		-- catches stuttering.
		local fx = GameConfig.Effects
		local elapsed = 0
		local sinceCull = math.huge
		local sinceSlow = 0

		RunService.Heartbeat:Connect(function(dt)
			elapsed += dt
			sinceCull += dt
			sinceSlow += dt

			local recull = sinceCull >= fx.CullIntervalSeconds
			if recull then
				sinceCull = 0
			end
			local slow = sinceSlow >= fx.SlowUpdateSeconds
			if slow then
				sinceSlow = 0
			end

			local eye = Workspace.CurrentCamera and Workspace.CurrentCamera.CFrame.Position

			for _, a in animated do
				local part = a.Part

				if recull and eye then
					a.Active = (part.Position - eye).Magnitude <= fx.AnimationDistance
				end
				if not a.Active then
					continue
				end

				local moved = false
				local cf = a.Base

				if a.Spin then
					-- Breathe the rate a little rather than holding it exact.
					local rate = a.Spin
					if a.Jitter > 0 then
						rate *= 1 + math.sin(elapsed / 3.1 + a.Phase) * a.Jitter
					end
					a.Angle += rate * dt
					cf = cf * CFrame.fromAxisAngle(a.Axis, a.Angle)
					moved = true
				end
				if a.Wobble then
					-- Tilt across the spin axis on two slightly different
					-- periods, so the sway never repeats on a beat.
					local w = math.rad(a.Wobble)
					cf = cf
						* CFrame.Angles(
							math.sin(elapsed / a.WobbleSeconds * math.pi * 2 + a.Phase) * w,
							math.sin(elapsed / (a.WobbleSeconds * 1.37) * math.pi * 2 + a.Phase) * w,
							0
						)
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

				if slow then
					if a.Pulse then
						local t = (math.sin(elapsed / a.PulseSeconds * math.pi * 2 + a.Phase) + 1) / 2
						part.Size = a.BaseSize * (1 - a.Pulse + a.Pulse * 2 * t)
					end
					if a.AlphaMin then
						local t = (math.sin(elapsed / a.PulseSeconds * math.pi * 2 + a.Phase) + 1) / 2
						part.Transparency = a.AlphaMin + (a.AlphaMax - a.AlphaMin) * t
					end
					if a.ColorA then
						local t = (math.sin(elapsed / a.ColorSeconds * math.pi * 2 + a.Phase) + 1) / 2
						part.Color = a.ColorA:Lerp(a.ColorB, t)
					end
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

		-- Runs regardless of what the scan found. Gated on "are there shards
		-- YET" each pass rather than "were there shards then", so a crystal
		-- that replicates late still joins the cycle instead of the whole
		-- rotation never starting.
		task.spawn(function()
			while true do
				if #shards > 0 then
					cycleFeaturedRarity(shards)
				end
				task.wait(Layout.FateEngine.FeaturedCycleSeconds)
			end
		end)
	end)
end

return HubEffects
