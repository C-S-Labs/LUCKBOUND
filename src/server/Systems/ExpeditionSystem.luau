--!strict
-- Expedition entry, generation and return. Build spec §7.1 (the Phase 2 slice).
--
-- WHAT THIS DELIBERATELY IS NOT: there is no combat, no loot, no enemies and
-- no boss here. Build spec §7 excludes all of those and they stay excluded.
-- This system answers one question and no others -- can a player roll a world,
-- walk through the Gate, and arrive in a map that was generated for them?
-- Everything past that is still Phase 2 proper.
--
-- ExpeditionCore owns every decision; this file owns remotes, geometry,
-- teleports and timers. If you find yourself writing an `if worldId ==` in
-- here, the schema is wrong -- stop and amend the spec (CLAUDE.md, prime
-- directive).

local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local ChunkCore = require(Root.Util.ChunkCore)
local ChunkLoader = require(Root.Util.ChunkLoader)
local Chunks = require(Root.Content.Chunks)
local Constants = require(Root.Core.Constants)
local ExpeditionCore = require(Root.Core.ExpeditionCore)
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)
local PortalRig = require(Root.Util.PortalRig)
local Worlds = require(Root.Content.Worlds)

local ExpeditionSystem = {}

local SaveSystem
local ProgressionSystem

type Active = {
	WorldId: string,
	Slot: number,
	Seed: number,
	StartedAt: number,
	Duration: number,
	Stage: Model,
	Died: RBXScriptConnection?,
}

local active: { [number]: Active } = {}
local occupiedSlots: { [number]: boolean } = {}
local lastEntryAt: { [number]: number } = {}

local function stageFolder(): Folder
	local existing = Workspace:FindFirstChild(Constants.NAMES.EXPEDITION_STAGE)
	if existing and existing:IsA("Folder") then
		return existing
	end
	local folder = Instance.new("Folder")
	folder.Name = Constants.NAMES.EXPEDITION_STAGE
	folder.Parent = Workspace
	return folder
end

--- The Gate's portal, which is what "walk into the portal" measures against.
--- Absent on a place with no hub, in which case the distance check is skipped
--- rather than failing -- same handling FateSystem gives a missing RollAnchor.
local function gatePart(): BasePart?
	local hub = Workspace:FindFirstChild(Constants.NAMES.CROSSROADS)
	local zones = hub and hub:FindFirstChild("Zones")
	local gate = zones and zones:FindFirstChild("EXPEDITION_GATE")
	local rig = gate and gate:FindFirstChild("GateRig")
	local plane = rig and rig:FindFirstChild("PortalPlane")
	return if plane and plane:IsA("BasePart") then plane else nil
end

local function distanceToGate(player: Player): number?
	local target = gatePart()
	if not target then
		return nil
	end
	local character = player.Character
	local hrp = character and character:FindFirstChild("HumanoidRootPart")
	if not hrp or not hrp:IsA("BasePart") then
		return math.huge
	end
	return (hrp.Position - target.Position).Magnitude
end

local function moveCharacter(player: Player, position: Vector3): boolean
	local character = player.Character
	local hrp = character and character:FindFirstChild("HumanoidRootPart")
	if not hrp or not hrp:IsA("BasePart") then
		return false
	end
	-- PivotTo moves the whole rig, not just the root part, which is what stops
	-- limbs being left behind at the old location for a frame.
	;(character :: Model):PivotTo(CFrame.new(position))
	return true
end

--- The way home, on the arrival chunk. Small on purpose (GameConfig.Expedition
--- .ReturnPortalScale): it is a door, and it must not read as more important
--- than whatever the world put at the far end.
local function buildReturnPortal(stage: Model, position: Vector3, rarityKey: string)
	local rig = PortalRig.build({
		Name = "ReturnPortal",
		Position = position,
		Scale = GameConfig.Expedition.ReturnPortalScale,
		Rarity = rarityKey,
		PlinthMaterial = Enum.Material.Marble,
		OuterMaterial = Enum.Material.CorrodedMetal,
	}, stage)

	local plinth = rig.PrimaryPart
	if not plinth then
		return
	end

	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "ReturnPrompt"
	prompt.ActionText = "RETURN"
	prompt.ObjectText = "The Crossroads"
	prompt.HoldDuration = 0.4
	prompt.MaxActivationDistance = 40
	prompt.RequiresLineOfSight = false
	prompt.Parent = plinth

	-- ProximityPrompt.Triggered fires on the SERVER with the triggering player,
	-- so this path needs no remote and cannot be spoofed.
	prompt.Triggered:Connect(function(player)
		if active[player.UserId] then
			ExpeditionSystem.finish(player, "RETURNED")
		end
	end)
end

--- Fired on entry and then on a timer. RemainingSeconds, never an absolute end
--- time -- build spec §4.1 rule 4.
local function syncTimer(player: Player, state: Active)
	Net.get("Expedition_TimerSync"):FireClient(player, {
		RemainingSeconds = ExpeditionCore.remaining(state.StartedAt, state.Duration, os.clock()),
		ServerNow = os.time(),
	})
end

function ExpeditionSystem.isActive(player: Player): boolean
	return active[player.UserId] ~= nil
end

--- Ends an expedition and brings the player home. Safe to call for a player
--- who is not on one.
function ExpeditionSystem.finish(player: Player, reason: string): ()
	local state = active[player.UserId]
	if not state then
		return
	end
	active[player.UserId] = nil
	occupiedSlots[state.Slot] = nil

	if state.Died then
		state.Died:Disconnect()
	end

	local awarded = 0
	-- Dying is not completing. Fate is awarded for finishing an expedition,
	-- and "finishing" has to mean something or the reward means nothing.
	if reason == "COMPLETED" or reason == "RETURNED" then
		local profile = SaveSystem.get(player)
		if profile then
			profile.Stats.ExpeditionsCompleted += 1
			ProgressionSystem.award(player, "ExpeditionCompleted")
			awarded = GameConfig.Progression.Rewards.ExpeditionCompleted
		end
	end

	-- Bring the player home BEFORE destroying the ground under them, or they
	-- fall for a frame and Roblox's FallenPartsDestroyHeight takes over.
	moveCharacter(player, GameConfig.HubLayout.SpawnAnchor)
	state.Stage:Destroy()

	Net.get("Expedition_Ended"):FireClient(player, {
		WorldId = state.WorldId,
		Reason = reason,
		FateAwarded = awarded,
	})

	print(
		string.format(
			"[Expedition] %s left %s after %.0fs (%s)",
			player.Name,
			state.WorldId,
			os.clock() - state.StartedAt,
			reason
		)
	)
end

--- The whole entry path. Every refusal is decided by ExpeditionCore and most
--- are silent, for the reason build spec §3.4.3 gives about the roll cooldown:
--- an error that names the boundary tells an exploiter where the boundary is.
function ExpeditionSystem.requestEnter(player: Player, ...: any): ()
	-- The client sends nothing. A payload means a tampered client.
	if select("#", ...) > 0 then
		warn(`[ExpeditionSystem] {player.Name} sent arguments with Expedition_RequestEnter; discarded`)
		return
	end

	local profile = SaveSystem.get(player)
	if not profile then
		return
	end

	local decision = ExpeditionCore.evaluateEntry({
		Profile = profile,
		Worlds = Worlds,
		Chunks = Chunks,
		Config = GameConfig,
		Now = os.clock(),
		LastEntryAt = lastEntryAt[player.UserId],
		AlreadyActive = active[player.UserId] ~= nil,
		DistanceToGate = distanceToGate(player),
		FreeSlot = ExpeditionCore.freeSlot(occupiedSlots, GameConfig.Expedition.MaxConcurrent),
	})

	if not decision.Allowed then
		local message = ExpeditionCore.refusalMessage(decision.Refusal :: any)
		if message then
			-- Only the two refusals a legitimate player can actually hit are
			-- spoken aloud. The rest are exploit guards and stay silent.
			Net.get("Expedition_Ended"):FireClient(player, {
				WorldId = decision.WorldId,
				Reason = "ABORTED",
				FateAwarded = 0,
				Message = message,
			})
		end
		return
	end

	lastEntryAt[player.UserId] = os.clock()

	local worldId = decision.WorldId :: string
	local world = Worlds[worldId]
	local seed = ExpeditionCore.seedFor(player.UserId, profile.TotalRolls, worldId)

	local ok, layout, attempts = ChunkCore.assembleWithRetry(Chunks, {
		WorldId = worldId,
		PathLength = ExpeditionCore.pathLengthFor(world, GameConfig),
	}, function(attempt)
		return ExpeditionCore.streamFor(seed, attempt)
	end, GameConfig.Expedition.AssemblyAttempts)

	if not ok then
		-- A kit that cannot assemble is a CONTENT bug, not a player problem.
		-- Say so loudly server-side and refuse quietly client-side.
		warn(
			string.format(
				"[ExpeditionSystem] %s: assembly failed for %s after %d attempts -- %s",
				player.Name,
				worldId,
				attempts,
				tostring(layout)
			)
		)
		return
	end

	layout.Seed = seed

	local slot = ExpeditionCore.freeSlot(occupiedSlots, GameConfig.Expedition.MaxConcurrent) :: number
	occupiedSlots[slot] = true

	local dx, dy, dz = ExpeditionCore.stageOffset(slot, GameConfig.Expedition.StageSpacing)
	local origin = GameConfig.Expedition.StageOrigin + Vector3.new(dx, dy, dz)

	local result = ChunkLoader.build(
		layout,
		Chunks,
		origin,
		stageFolder(),
		`{worldId}_{player.UserId}`
	)

	-- Reskinned to the rolled world's rarity, like every other portal in the
	-- game: the way home from an Uncommon world is an Uncommon-green ring.
	buildReturnPortal(result.Model, result.ReturnPosition, world.Rarity)

	if not moveCharacter(player, result.EntryPosition) then
		-- No character to move: tear the stage down rather than leaking it.
		result.Model:Destroy()
		occupiedSlots[slot] = nil
		return
	end

	local duration = ExpeditionCore.durationFor(world, GameConfig)
	local state: Active = {
		WorldId = worldId,
		Slot = slot,
		Seed = seed,
		StartedAt = os.clock(),
		Duration = duration,
		Stage = result.Model,
	}

	-- Falling off a floating island is a real outcome in Ethereal Scape. End
	-- the expedition rather than respawning the player at the hub with an
	-- expedition still notionally running above their head.
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if humanoid then
		state.Died = humanoid.Died:Connect(function()
			ExpeditionSystem.finish(player, "DIED")
		end)
	end

	active[player.UserId] = state

	Net.get("Expedition_Started"):FireClient(player, {
		WorldId = worldId,
		Name = world.Name,
		Rarity = world.Rarity,
		Flavor = world.Flavor,
		Environment = world.Environment,
		DurationSeconds = duration,
		RemainingSeconds = duration,
		ServerNow = os.time(),
		Seed = seed,
		ChunkCount = #layout.Chunks,
	})

	print(
		string.format(
			"[Expedition] %s -> %s  seed %d  %d chunks (%d mesh, %d blockout)  attempt %d  %ds",
			player.Name,
			worldId,
			seed,
			#layout.Chunks,
			result.UsedMeshes,
			result.FloorCount,
			attempts,
			duration
		)
	)
end

function ExpeditionSystem.init(saveSystem: any, progressionSystem: any): ()
	SaveSystem = saveSystem
	ProgressionSystem = progressionSystem

	-- Lighting is a shared service. The server never touches it -- each client
	-- dresses its own screen from the Environment in Expedition_Started, which
	-- is what makes "biome lighting never bleeds" (Biome Blueprint §6) true
	-- for more than one player at a time.
	assert(Lighting, "Lighting service missing")

	stageFolder()

	Net.get("Expedition_RequestEnter").OnServerEvent:Connect(function(player, ...)
		ExpeditionSystem.requestEnter(player, ...)
	end)

	-- Timer sweep. One loop for every expedition rather than a task per
	-- player: the cost is fixed regardless of how many are running.
	task.spawn(function()
		while true do
			task.wait(GameConfig.Expedition.TimerSyncSeconds)
			local now = os.clock()
			for userId, state in active do
				local player = Players:GetPlayerByUserId(userId)
				if not player then
					continue
				end
				if ExpeditionCore.remaining(state.StartedAt, state.Duration, now) <= 0 then
					ExpeditionSystem.finish(player, "COMPLETED")
				else
					syncTimer(player, state)
				end
			end
		end
	end)

	Players.PlayerRemoving:Connect(function(player)
		local state = active[player.UserId]
		if state then
			-- Leaving mid-expedition must not leak a stage or a slot.
			occupiedSlots[state.Slot] = nil
			if state.Died then
				state.Died:Disconnect()
			end
			state.Stage:Destroy()
			active[player.UserId] = nil
		end
		lastEntryAt[player.UserId] = nil
	end)
end

--- Binds the Gate's ProximityPrompt once the hub exists. Triggered fires on
--- the server with the triggering player, so this path carries no client data
--- at all -- the strongest version of build spec §3.4's "the client sends
--- nothing".
function ExpeditionSystem.bindGatePrompt(): ()
	local target = gatePart()
	local rig = target and target.Parent
	local plinth = rig and rig:FindFirstChild("Plinth")
	if not plinth or not plinth:IsA("BasePart") then
		warn("[ExpeditionSystem] no Gate plinth found; entry is remote-only")
		return
	end

	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "EnterPrompt"
	prompt.ActionText = "ENTER"
	prompt.ObjectText = "Expedition Gate"
	prompt.HoldDuration = 0.5
	prompt.MaxActivationDistance = GameConfig.UI.PromptActivationDistance
	prompt.RequiresLineOfSight = false
	prompt.Enabled = GameConfig.Expedition.Enabled
	prompt.Parent = plinth

	prompt.Triggered:Connect(function(player)
		ExpeditionSystem.requestEnter(player)
	end)
end

return ExpeditionSystem
