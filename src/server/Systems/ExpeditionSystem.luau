--!strict
-- Expedition entry, generation and return. Build spec §7.1, and §7.2 for
-- parties and expeditions as their own server.
--
-- WHAT THIS DELIBERATELY IS NOT: there is no combat, no enemies and no boss
-- here; build spec §7 still excludes them. Loot, chests, the vault and its key
-- (§7.5) are LootSystem's: this file hands it each map as it is built, and
-- otherwise answers one question -- can a player (or a party) roll a world,
-- walk through the portal, and arrive in a map that was generated for them?
--
-- ExpeditionCore owns every decision; this file owns remotes, geometry,
-- teleports and timers. If you find yourself writing an `if worldId ==` in
-- here, the schema is wrong -- stop and amend the spec (CLAUDE.md, prime
-- directive).
--
-- THE THREE WAYS THIS FILE RUNS (§7.2):
--
--   HUB, TELEPORT  -- a live hub server. Entering the portal reserves a new
--                     server, writes a manifest (world, seed, duration,
--                     members) to MemoryStore under that server's id, and
--                     teleports the player -- or the leader's whole party --
--                     into it together.
--   HUB, IN_PLACE  -- Studio, where TeleportService cannot run. The map is
--                     built high above the hub in this server, exactly as
--                     the §7.1 prototype did, and a party is placed on it
--                     together. Same decision, same seed, same map.
--   HOST           -- this server IS the reserved expedition server. It reads
--                     its manifest, builds the one map, places each member as
--                     they arrive, runs the timer, and teleports everyone
--                     home to the hub server they came from.
--
-- Whichever it is, the players are a GROUP: one map, one timer, one seed --
-- the leader's. Each player's own profile (Fate, level, history) follows
-- them through SaveSystem and is never shared.

local Lighting = game:GetService("Lighting")
local MemoryStoreService = game:GetService("MemoryStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TeleportService = game:GetService("TeleportService")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local ChunkCore = require(Root.Util.ChunkCore)
local ChunkLoader = require(Root.Util.ChunkLoader)
local Chunks = require(Root.Content.Chunks)

-- Fresh entropy per expedition. Random.new() with no argument seeds itself
-- from the engine's entropy source, so no two sessions share a sequence --
-- which the roll-count seed alone could not promise: in Studio, with no
-- persistence, TotalRolls starts at the same value every session and roll
-- #1 always built seed 1704274940. The seed is still logged on entry, so
-- any map can still be rebuilt exactly from its log line.
local seedSource = Random.new()
local ScenarioCore = require(Root.Util.ScenarioCore)
local Scenarios = require(Root.Content.Scenarios)
local Constants = require(Root.Core.Constants)
local ExpeditionCore = require(Root.Core.ExpeditionCore)
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)
local PortalRig = require(Root.Util.PortalRig)
local PrebuiltLoader = require(Root.Util.PrebuiltLoader)
local Worlds = require(Root.Content.Worlds)

local ExpeditionSystem = {}

local SaveSystem
local ProgressionSystem
local PartySystem
local LootSystem

-- One map and everyone on it.
type Group = {
	WorldId: string,
	Seed: number,
	Slot: number?, -- IN_PLACE only; a host has the whole server
	Stage: Model,
	FloorY: number, -- the map's walk plane; the client's cloud sea hangs below it
	EntryPosition: Vector3,
	Summary: string,
	Duration: number,
	-- Set when the first member arrives, so a slow teleport does not eat
	-- into the expedition. In place, that is the moment of entry.
	StartedAt: number?,
	LeaderUserId: number,
	PartySize: number,
	Members: { [number]: boolean },
	Arrivals: number,
}

type Active = {
	Group: Group,
	Died: RBXScriptConnection?,
}

local active: { [number]: Active } = {}
local groups: { Group } = {}
local occupiedSlots: { [number]: boolean } = {}
local lastEntryAt: { [number]: number } = {}
-- Players between "teleport requested" and "left the server". They are not
-- on an expedition yet, but they must not be sent on a second one.
local launching: { [number]: boolean } = {}
-- Set only for the duration of one forceEnter call, so the distance check is
-- skipped for that call and nothing else. A flag rather than a parameter keeps
-- requestEnter's signature honest: it is still "the client sends nothing".
local forcedEntry: { [number]: boolean } = {}

-- HOST mode only.
local hosting = false
local manifest: any = nil
local manifestFailed = false
local hostGroup: Group? = nil

local manifestMap: MemoryStoreHashMap? = nil
local function manifestStore(): MemoryStoreHashMap?
	if manifestMap then
		return manifestMap
	end
	local ok, map = pcall(function()
		return MemoryStoreService:GetHashMap(Constants.DATASTORE.EXPEDITION_MANIFESTS)
	end)
	if ok then
		manifestMap = map
		return map
	end
	warn(`[ExpeditionSystem] MemoryStore unavailable: {map}`)
	return nil
end

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

--- The Gate's entry anchor -- the same seam the Fate Engine's RollAnchor is.
--- Distance is measured from here rather than from the portal art, so the rig
--- can be rebuilt in Blender at any size without moving the goalposts.
---
--- Absent on a place with no hub, in which case the distance check is skipped
--- rather than failing -- same handling FateSystem gives a missing RollAnchor.
--- WHEREVER ENTRY LIVES. It was under Zones/EXPEDITION_GATE; it is now on the
--- Fate Engine, and it moves again when the portal grows its staircase.
--- Searching the hub by NAME rather than by path makes that a placement
--- decision in HubBuilder instead of an edit here every time.
local function gatePart(): BasePart?
	local hub = Workspace:FindFirstChild(Constants.NAMES.CROSSROADS)
	if not hub then
		return nil
	end
	local anchor = hub:FindFirstChild(Constants.NAMES.GATE_ANCHOR, true)
	return if anchor and anchor:IsA("BasePart") then anchor else nil
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

--- Tells one player something about the door without starting anything.
--- ABORTED is what ExpeditionController already reads as "a refusal at the
--- door": no lighting change, just the message.
local function tell(player: Player, worldId: string?, message: string)
	Net.get("Expedition_Ended"):FireClient(player, {
		WorldId = worldId,
		Reason = "ABORTED",
		FateAwarded = 0,
		Message = message,
	})
end

--- Fired on entry and then on a timer. RemainingSeconds, never an absolute end
--- time -- build spec §4.1 rule 4.
local function syncTimer(player: Player, group: Group)
	Net.get("Expedition_TimerSync"):FireClient(player, {
		RemainingSeconds = ExpeditionCore.remaining(
			group.StartedAt or os.clock(),
			group.Duration,
			os.clock()
		),
		ServerNow = os.time(),
	})
end

-- === the map ==========================================================

--- THE ONE BRANCH. It reads a data field, never a world id -- add an authored
--- world and this function does not change. See ExpeditionCore.hasPrebuiltMap
--- for why the two routes exist at all. Returns nil on a content failure,
--- which is loud here and silent to the player.
local function buildStage(worldId: string, seed: number, origin: Vector3, stageName: string)
	local world = Worlds[worldId]

	if ExpeditionCore.hasPrebuiltMap(world) then
		local built = PrebuiltLoader.build(world, origin, stageFolder(), stageName)
		if not built then
			-- The scene is not in ServerStorage: Rojo is not running, or the
			-- file is not in assets/rbxm/maps/. A CONTENT problem.
			warn(
				string.format(
					"[ExpeditionSystem] prebuilt map '%s' for %s is not in ServerStorage.%s",
					tostring(world.PrebuiltMap.AssetKey),
					worldId,
					Constants.NAMES.MAPS_FOLDER
				)
			)
			return nil
		end
		return {
			Stage = built.Model,
			FloorY = origin.Y,
			EntryPosition = built.EntryPosition,
			ReturnPosition = built.ReturnPosition,
			Summary = string.format(
				"prebuilt %s  %d parts at %.2f scale  %s arrival",
				world.PrebuiltMap.AssetKey,
				built.PartCount,
				world.PrebuiltMap.Scale,
				if built.Authored then "authored" else "derived"
			),
		}
	end

	local ok, layout, attempts = ChunkCore.assembleWithRetry(Chunks, {
		WorldId = worldId,
		PathLength = ExpeditionCore.pathLengthFor(world, GameConfig),
		-- Was never passed, so GameConfig.Expedition.IncludeSide did nothing:
		-- ChunkCore treats nil as "on", which happened to match the config's
		-- value, so a designer turning it off would have been ignored in
		-- silence. A dial that is read nowhere is not a dial.
		IncludeSide = GameConfig.Expedition.IncludeSide,
		BranchLength = GameConfig.Expedition.BranchLength,
		MaxRepeats = GameConfig.Expedition.MaxRepeats,
	}, function(attempt)
		return ExpeditionCore.streamFor(seed, attempt)
	end, GameConfig.Expedition.AssemblyAttempts)

	if not ok then
		-- A kit that cannot assemble is a CONTENT bug, not a player problem.
		warn(
			string.format(
				"[ExpeditionSystem] assembly failed for %s seed %d after %d attempts -- %s",
				worldId,
				seed,
				attempts,
				tostring(layout)
			)
		)
		return nil
	end

	layout.Seed = seed

	-- SCENARIO SELECTION -- build spec §7.3, the layer above the geometry.
	--
	-- ChunkCore decided WHERE the pieces go; this decides WHAT HAPPENS in
	-- them. It spawns nothing: the plan is recorded on the layout and written
	-- onto each chunk folder as an attribute, so a generated map is
	-- verifiable by eye in Studio exactly like Role and Yaw already are.
	-- Encounter and reward configuration remain behind the §7 exclusions.
	--
	-- Its own stream, offset well past the assembly attempts, so adding or
	-- removing a scenario can never shift which CHUNKS a seed picks. The two
	-- layers stay independently reproducible, which is the whole point of the
	-- seam between them.
	local planOk, plan = ScenarioCore.assign(layout, Chunks, Scenarios, {
		FateInterventionChance = GameConfig.Expedition.FateInterventionChance,
		RecentMemory = GameConfig.Expedition.ScenarioRecentMemory,
		EscalateFrom = GameConfig.Expedition.ScenarioEscalateFrom,
	}, ExpeditionCore.streamFor(seed, GameConfig.Expedition.ScenarioStreamOffset))

	if planOk then
		layout.ScenarioPlan = plan
	else
		-- A kit that cannot be populated is a CONTENT bug, and it is not worth
		-- refusing a walkable expedition over: nothing reads the plan yet.
		-- Loud server-side, invisible to the player -- the same posture the
		-- loader takes when a mesh fails and it falls back to blockout.
		warn(
			string.format(
				"[ExpeditionSystem] scenario assignment failed for %s seed %d -- %s",
				worldId,
				seed,
				tostring(plan)
			)
		)
	end

	local result = ChunkLoader.build(layout, Chunks, origin, stageFolder(), stageName)

	local scenarioSummary = "no plan"
	if planOk then
		local bands = ScenarioCore.bandCounts(plan)
		scenarioSummary = string.format(
			"%d ordinary/%d uncommon/%d rare",
			bands.ORDINARY,
			bands.UNCOMMON,
			bands.RARE
		)
	end

	return {
		Stage = result.Model,
		-- The layout plane: every chunk's walk surface sits at origin.Y. The
		-- client hangs its cloud sea below this.
		FloorY = origin.Y,
		EntryPosition = result.EntryPosition,
		ReturnPosition = result.ReturnPosition,
		ScenarioPlan = if planOk then plan else nil,
		Summary = string.format(
			"%d chunks (%d mesh, %d blockout)  scenarios %s  attempt %d",
			#layout.Chunks,
			result.UsedMeshes,
			result.FloorCount,
			scenarioSummary,
			attempts
		),
	}
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
	prompt.MaxActivationDistance = GameConfig.Expedition.ReturnPromptDistance
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

local function newGroup(
	worldId: string,
	seed: number,
	built: any,
	slot: number?,
	leaderUserId: number,
	partySize: number
): Group
	local world = Worlds[worldId]
	buildReturnPortal(built.Stage, built.ReturnPosition, world.Rarity)
	local group: Group = {
		WorldId = worldId,
		Seed = seed,
		Slot = slot,
		Stage = built.Stage,
		FloorY = built.FloorY,
		EntryPosition = built.EntryPosition,
		Summary = built.Summary,
		Duration = ExpeditionCore.durationFor(world, GameConfig),
		StartedAt = nil,
		LeaderUserId = leaderUserId,
		PartySize = partySize,
		Members = {},
		Arrivals = 0,
	}
	table.insert(groups, group)
	-- Chests, the vault, the forcefield, and the boss stand-in (§7.5). Handed
	-- the group's own Members table, so whoever is on the map when something
	-- opens is who shares it.
	if LootSystem then
		LootSystem.attach(built.Stage, worldId, group.Members)
	end
	return group
end

local function dropGroup(group: Group)
	local index = table.find(groups, group)
	if index then
		table.remove(groups, index)
	end
	if group.Slot then
		occupiedSlots[group.Slot] = nil
	end
	group.Stage:Destroy()
end

--- Puts one player on the group's map and starts their expedition. Party
--- members stand on a small ring around the entry point.
local function placeMember(player: Player, group: Group): boolean
	group.Arrivals += 1
	local dx, dz =
		ExpeditionCore.arrivalOffset(group.Arrivals, GameConfig.Expedition.ArrivalSpreadStuds)
	if not moveCharacter(player, group.EntryPosition + Vector3.new(dx, 0, dz)) then
		return false
	end

	if group.StartedAt == nil then
		group.StartedAt = os.clock()
	end

	local state: Active = { Group = group }
	-- Falling off a floating island is a real outcome in Ethereal Scape. End
	-- the expedition rather than respawning the player at the hub with an
	-- expedition still notionally running above their head.
	local humanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
	if humanoid then
		state.Died = humanoid.Died:Connect(function()
			ExpeditionSystem.finish(player, "DIED")
		end)
	end
	active[player.UserId] = state
	group.Members[player.UserId] = true

	local world = Worlds[group.WorldId]
	local remaining =
		ExpeditionCore.remaining(group.StartedAt :: number, group.Duration, os.clock())
	Net.get("Expedition_Started"):FireClient(player, {
		WorldId = group.WorldId,
		Name = world.Name,
		Rarity = world.Rarity,
		Flavor = world.Flavor,
		Environment = world.Environment,
		DurationSeconds = group.Duration,
		RemainingSeconds = remaining,
		ServerNow = os.time(),
		Seed = group.Seed,
		MapSummary = group.Summary,
		PartySize = group.PartySize,
		FloorY = group.FloorY,
		-- The map's model, by name, so the client can find its own pieces
		-- among several groups' maps in one Studio server.
		StageName = group.Stage.Name,
	})

	print(
		string.format(
			"[Expedition] %s -> %s  seed %d  %s  %ds  (party of %d)",
			player.Name,
			group.WorldId,
			group.Seed,
			group.Summary,
			math.floor(remaining),
			group.PartySize
		)
	)
	return true
end

-- === teleports ========================================================

--- TeleportAsync with retries. Returns true once Roblox accepts the request;
--- an individual failure after that arrives through TeleportInitFailed.
local function teleport(placeId: number, players: { Player }, options: TeleportOptions): boolean
	for attempt = 1, GameConfig.Expedition.TeleportAttempts do
		local ok, err = pcall(function()
			TeleportService:TeleportAsync(placeId, players, options)
		end)
		if ok then
			return true
		end
		warn(`[ExpeditionSystem] teleport attempt {attempt} failed: {err}`)
		if attempt < GameConfig.Expedition.TeleportAttempts then
			task.wait(GameConfig.Expedition.TeleportRetrySeconds)
		end
	end
	return false
end

--- HOST: sends players back to the Crossroads -- to the very hub server they
--- left if it is still running, so they land among the people they left;
--- any hub server if not. One call for everyone going together, so a party
--- coming home at the timer lands in the same server.
local function sendHome(players: { Player })
	if #players == 0 then
		return
	end
	local hubPlaceId = ExpeditionCore.placeFor(
		if manifest then manifest.HubPlaceId else GameConfig.Expedition.HubPlaceId,
		game.PlaceId
	)

	local userIds = {}
	for _, player in players do
		table.insert(userIds, player.UserId)
		SaveSystem.handOff(player)
	end
	if manifest and PartySystem then
		PartySystem.recordForReunite(manifest.LeaderUserId, userIds, #manifest.Members)
	end

	-- Marks the arrival for the loading screen, which skips its title card
	-- for someone coming back. It is only a cosmetic hint, so it may travel
	-- through the client.
	local function options(toSameServer: boolean): TeleportOptions
		local opts = Instance.new("TeleportOptions")
		if
			toSameServer
			and manifest
			and type(manifest.HubJobId) == "string"
			and manifest.HubJobId ~= ""
		then
			opts.ServerInstanceId = manifest.HubJobId
		end
		opts:SetTeleportData({ Kind = "RETURN" })
		return opts
	end

	task.spawn(function()
		if teleport(hubPlaceId, players, options(true)) then
			return
		end
		-- The hub they came from has closed or filled. Any hub will do.
		if not teleport(hubPlaceId, players, options(false)) then
			for _, player in players do
				if player.Parent then
					player:Kick("Could not return you to the Crossroads. Please rejoin.")
				end
			end
		end
	end)
end

--- HUB: reserves a server, writes its manifest, and teleports the group in.
--- Returns false if anything fails BEFORE players have been sent, so the
--- caller can fall back to building in place.
local function launchInstance(
	leader: Player,
	members: { Player },
	worldId: string,
	seed: number
): boolean
	local map = manifestStore()
	if not map then
		return false
	end

	local placeId = ExpeditionCore.placeFor(GameConfig.Expedition.InstancePlaceId, game.PlaceId)
	local okReserve, accessCode, privateServerId = pcall(function()
		return TeleportService:ReserveServer(placeId)
	end)
	if not okReserve or type(accessCode) ~= "string" or type(privateServerId) ~= "string" then
		warn(`[ExpeditionSystem] ReserveServer failed: {accessCode}`)
		return false
	end

	local memberIds = {}
	for _, member in members do
		table.insert(memberIds, member.UserId)
	end
	local world = Worlds[worldId]
	local record = ExpeditionCore.buildManifest({
		WorldId = worldId,
		Seed = seed,
		DurationSeconds = ExpeditionCore.durationFor(world, GameConfig),
		LeaderUserId = leader.UserId,
		Members = memberIds,
		HubPlaceId = ExpeditionCore.placeFor(GameConfig.Expedition.HubPlaceId, game.PlaceId),
		HubJobId = game.JobId,
		CreatedAt = os.time(),
	})

	-- Keyed by the destination's own PrivateServerId: that server can read
	-- this about itself, and no client ever carries it.
	local okWrite, writeErr = pcall(function()
		(map :: MemoryStoreHashMap):SetAsync(
			privateServerId,
			record,
			GameConfig.Expedition.ManifestTtlSeconds
		)
	end)
	if not okWrite then
		warn(`[ExpeditionSystem] could not write manifest: {writeErr}`)
		return false
	end

	for _, member in members do
		launching[member.UserId] = true
		SaveSystem.handOff(member)
	end

	local options = Instance.new("TeleportOptions")
	options.ReservedServerAccessCode = accessCode
	options:SetTeleportData({ Kind = "EXPEDITION" })

	print(
		string.format(
			"[Expedition] %s opens %s for %d  seed %d  -> reserved server %s",
			leader.Name,
			worldId,
			#members,
			seed,
			privateServerId
		)
	)

	task.spawn(function()
		if not teleport(placeId, members, options) then
			for _, member in members do
				launching[member.UserId] = nil
				if member.Parent then
					tell(member, worldId, "The portal flickered. Try again.")
				end
			end
		end
	end)
	return true
end

-- === the public surface ================================================

function ExpeditionSystem.isActive(player: Player): boolean
	return active[player.UserId] ~= nil or launching[player.UserId] == true
end

function ExpeditionSystem.isHosting(): boolean
	return hosting
end

--- Ends one player's expedition and brings them home. Safe to call for a
--- player who is not on one. The map goes when its last player does.
function ExpeditionSystem.finish(player: Player, reason: string): ()
	local state = active[player.UserId]
	if not state then
		return
	end
	active[player.UserId] = nil
	local group = state.Group
	group.Members[player.UserId] = nil

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

	Net.get("Expedition_Ended"):FireClient(player, {
		WorldId = group.WorldId,
		Reason = reason,
		FateAwarded = awarded,
	})

	print(
		string.format(
			"[Expedition] %s left %s after %.0fs (%s)",
			player.Name,
			group.WorldId,
			os.clock() - (group.StartedAt or os.clock()),
			reason
		)
	)

	if hosting then
		-- Home is another server. The map stays for anyone still on it;
		-- the server closes itself once the last player has gone.
		sendHome({ player })
		return
	end

	-- Bring the player home BEFORE destroying the ground under them, or they
	-- fall for a frame and Roblox's FallenPartsDestroyHeight takes over.
	-- Home is the spawn ring's southern pad. Any pad would do; picking one
	-- keeps a return deterministic rather than dropping players at random.
	moveCharacter(
		player,
		Vector3.new(0, GameConfig.HubLayout.SpawnRing.Height, GameConfig.HubLayout.SpawnRing.Radius)
	)
	if next(group.Members) == nil then
		dropGroup(group)
	end
end

--- The timer ran out for the whole group. On a host, everyone goes home in
--- ONE teleport so a party lands in the same hub server together.
local function completeGroup(group: Group)
	local leaving = {}
	for userId in group.Members do
		local player = Players:GetPlayerByUserId(userId)
		if player then
			table.insert(leaving, player)
		end
	end

	if not hosting then
		for _, player in leaving do
			ExpeditionSystem.finish(player, "COMPLETED")
		end
		return
	end

	-- Award and notify each, but hold the teleport so it can be one call.
	-- The group leaves the sweep now, or the next tick would complete it
	-- again with nobody in it.
	local index = table.find(groups, group)
	if index then
		table.remove(groups, index)
	end
	for _, player in leaving do
		local state = active[player.UserId]
		if state then
			active[player.UserId] = nil
			group.Members[player.UserId] = nil
			if state.Died then
				state.Died:Disconnect()
			end
			local profile = SaveSystem.get(player)
			local awarded = 0
			if profile then
				profile.Stats.ExpeditionsCompleted += 1
				ProgressionSystem.award(player, "ExpeditionCompleted")
				awarded = GameConfig.Progression.Rewards.ExpeditionCompleted
			end
			Net.get("Expedition_Ended"):FireClient(player, {
				WorldId = group.WorldId,
				Reason = "COMPLETED",
				FateAwarded = awarded,
			})
		end
	end
	print(`[Expedition] {group.WorldId} completed; sending {#leaving} home together`)
	sendHome(leaving)
end

--- The whole entry path. Every refusal is decided by ExpeditionCore and most
--- are silent, for the reason build spec §3.4.3 gives about the roll cooldown:
--- an error that names the boundary tells an exploiter where the boundary is.
---
--- `player` is whoever walked into the portal. If they lead a party, the
--- party comes too, on this player's roll; if they are a member, nobody goes.
function ExpeditionSystem.requestEnter(player: Player, ...: any): ()
	-- The client sends nothing. A payload means a tampered client.
	if select("#", ...) > 0 then
		warn(
			`[ExpeditionSystem] {player.Name} sent arguments with Expedition_RequestEnter; discarded`
		)
		return
	end
	if hosting then
		return -- there is no portal onward from an expedition
	end

	local profile = SaveSystem.get(player)
	if not profile then
		return
	end

	local group = if PartySystem
		then PartySystem.groupFor(player)
		else { Role = "SOLO", Members = { player.UserId } }
	local mode = ExpeditionCore.instanceMode(GameConfig, RunService:IsStudio())

	local decision = ExpeditionCore.evaluateEntry({
		Profile = profile,
		Worlds = Worlds,
		Chunks = Chunks,
		Config = GameConfig,
		Now = os.clock(),
		LastEntryAt = lastEntryAt[player.UserId],
		AlreadyActive = ExpeditionSystem.isActive(player),
		DistanceToGate = if forcedEntry[player.UserId] then nil else distanceToGate(player),
		-- A teleport needs no stage slot here; the new server is the slot.
		FreeSlot = if mode == "TELEPORT"
			then 1
			else ExpeditionCore.freeSlot(occupiedSlots, GameConfig.Expedition.MaxConcurrent),
		PartyRole = group.Role,
	})

	if not decision.Allowed then
		local message = ExpeditionCore.refusalMessage(decision.Refusal :: any)
		if message then
			-- Only the refusals a legitimate player can actually hit are
			-- spoken aloud. The rest are exploit guards and stay silent.
			tell(player, decision.WorldId, message)
		end
		return
	end

	lastEntryAt[player.UserId] = os.clock()

	local worldId = decision.WorldId :: string
	-- THE LEADER'S SEED, for everyone. That is what "the same instance with
	-- the same parameters" means: one world, one map, one timer.
	-- Mixed with fresh entropy (seedSource above): every entry, every
	-- session, every player gets a new map.
	local seed = (ExpeditionCore.seedFor(player.UserId, profile.TotalRolls, worldId) + seedSource:NextInteger(
		1,
		2147483646
	)) % 2147483647

	-- Who actually goes. The leader always; each member only if they are
	-- still here, not already somewhere, and -- in place -- has a body to
	-- move. Anyone left behind is told why rather than wondering.
	local travellers: { Player } = { player }
	for _, userId in group.Members do
		if userId == player.UserId then
			continue
		end
		local member = Players:GetPlayerByUserId(userId)
		if not member then
			continue
		end
		local busy = ExpeditionSystem.isActive(member)
		local noBody = mode == "IN_PLACE" and member.Character == nil
		if busy or noBody or not SaveSystem.get(member) then
			tell(member, worldId, "Your party went through the portal without you.")
		else
			table.insert(travellers, member)
		end
	end

	if mode == "TELEPORT" then
		if launchInstance(player, travellers, worldId, seed) then
			return
		end
		-- Nothing has left yet: reserving or recording failed. Building here
		-- is better than a portal that does nothing, and it is the same map.
		warn("[ExpeditionSystem] could not open an instance; building in place instead")
	end

	local slot = ExpeditionCore.freeSlot(occupiedSlots, GameConfig.Expedition.MaxConcurrent)
	if not slot then
		return -- SERVER_FULL, silently, as before
	end
	local dx, dy, dz = ExpeditionCore.stageOffset(slot, GameConfig.Expedition.StageSpacing)
	local origin = GameConfig.Expedition.StageOrigin + Vector3.new(dx, dy, dz)

	local built = buildStage(worldId, seed, origin, `{worldId}_{player.UserId}`)
	if not built then
		return
	end
	-- Claimed only once the stage actually exists, so a refused build above
	-- does not leak a slot for the life of the server.
	occupiedSlots[slot] = true
	local stageGroup = newGroup(worldId, seed, built, slot, player.UserId, #travellers)

	for _, traveller in travellers do
		if not placeMember(traveller, stageGroup) and traveller ~= player then
			tell(traveller, worldId, "Your party went through the portal without you.")
		end
	end

	if next(stageGroup.Members) == nil then
		-- Nobody could be moved: tear the stage down rather than leaking it.
		dropGroup(stageGroup)
	end
end

--- DEVELOPER TOOL, behind DebugSystem's permission check.
---
--- Bypasses the DISTANCE check only. Everything else -- a destination, a kit
--- for it, not already running, a free stage slot -- still applies, because
--- skipping those would exercise a path the game does not actually have and
--- would prove nothing. Returns ok plus a line to print back.
function ExpeditionSystem.forceEnter(player: Player): (boolean, string)
	if ExpeditionSystem.isActive(player) then
		return false, "already on an expedition"
	end

	local profile = SaveSystem.get(player)
	if not profile then
		return false, "no profile loaded yet"
	end

	local worldId = ExpeditionCore.destinationFrom(profile)
	if not worldId then
		return false, "roll first -- you have no destination"
	end
	if not ExpeditionCore.hasMap(Worlds[worldId], Chunks, worldId) then
		return false, `{worldId} has neither a chunk kit nor a prebuilt map`
	end

	-- Clear the entry cooldown too: a developer re-entering repeatedly is the
	-- point of the command, not something to rate limit.
	lastEntryAt[player.UserId] = nil
	forcedEntry[player.UserId] = true
	ExpeditionSystem.requestEnter(player)
	forcedEntry[player.UserId] = nil

	return ExpeditionSystem.isActive(player),
		if ExpeditionSystem.isActive(player)
			then `entered {worldId}`
			else `entry failed -- see the server log`
end

-- === HOST mode ==========================================================

--- One arrival on the expedition server. Called once their character exists.
local function hostArrive(player: Player)
	if active[player.UserId] then
		return
	end

	-- The manifest may still be on its way from MemoryStore.
	local deadline = os.clock() + GameConfig.Expedition.ManifestWaitSeconds
	while not hostGroup and not manifestFailed and os.clock() < deadline and player.Parent do
		task.wait(0.25)
	end
	if not player.Parent then
		return
	end

	if not hostGroup or not manifest then
		warn(`[ExpeditionSystem] no expedition here for {player.Name}; sending them home`)
		tell(player, nil, "The way closed behind you. Returning to the Crossroads.")
		sendHome({ player })
		return
	end

	if not ExpeditionCore.isManifestMember(manifest, player.UserId) then
		warn(
			`[ExpeditionSystem] {player.Name} is not on this expedition's manifest; sending them home`
		)
		sendHome({ player })
		return
	end

	if not placeMember(player, hostGroup) then
		sendHome({ player })
	end
end

--- Turns this server into an expedition host. Called from bootstrap in
--- place of bindGatePrompt when ExpeditionCore.isExpeditionServer is true.
function ExpeditionSystem.startHost(): ()
	hosting = true
	print(`[ExpeditionSystem] this is an expedition server ({game.PrivateServerId})`)

	-- Characters are placed as they spawn. The client skips its title card
	-- here and asks to spawn immediately (LoadingScreen), and the character
	-- is moved onto the map the moment it exists.
	local function bind(player: Player)
		player.CharacterAdded:Connect(function()
			task.defer(hostArrive, player)
		end)
		if player.Character then
			task.defer(hostArrive, player)
		end
	end
	Players.PlayerAdded:Connect(bind)
	for _, player in Players:GetPlayers() do
		bind(player)
	end

	task.spawn(function()
		local map = manifestStore()
		local deadline = os.clock() + GameConfig.Expedition.ManifestWaitSeconds
		local record = nil
		while map and os.clock() < deadline do
			local ok, value = pcall(function()
				return (map :: MemoryStoreHashMap):GetAsync(game.PrivateServerId)
			end)
			if ok and value ~= nil then
				record = value
				break
			end
			task.wait(GameConfig.Expedition.ManifestPollSeconds)
		end

		local valid, reason = ExpeditionCore.validateManifest(record, Worlds, Chunks)
		if not valid then
			warn(
				`[ExpeditionSystem] expedition server has no usable manifest ({reason}); everyone goes home`
			)
			manifestFailed = true
			sendHome(Players:GetPlayers())
			return
		end
		manifest = record

		local built = buildStage(
			record.WorldId,
			record.Seed,
			GameConfig.Expedition.StageOrigin,
			record.WorldId
		)
		if not built then
			manifestFailed = true
			sendHome(Players:GetPlayers())
			return
		end
		local group =
			newGroup(record.WorldId, record.Seed, built, nil, record.LeaderUserId, #record.Members)
		-- The duration was decided by the hub from the same world; the
		-- manifest's copy wins so both ends agree even across a content
		-- update mid-flight.
		group.Duration = record.DurationSeconds
		hostGroup = group
		print(
			string.format(
				"[ExpeditionSystem] hosting %s  seed %d  %s  for %d player(s)",
				record.WorldId,
				record.Seed,
				built.Summary,
				#record.Members
			)
		)
	end)
end

function ExpeditionSystem.init(
	saveSystem: any,
	progressionSystem: any,
	partySystem: any?,
	lootSystem: any?
): ()
	SaveSystem = saveSystem
	ProgressionSystem = progressionSystem
	PartySystem = partySystem
	LootSystem = lootSystem

	-- Lighting is a shared service. The server never touches it -- each client
	-- dresses its own screen from the Environment in Expedition_Started, which
	-- is what makes "biome lighting never bleeds" (Biome Blueprint §6) true
	-- for more than one player at a time.
	assert(Lighting, "Lighting service missing")

	stageFolder()

	Net.get("Expedition_RequestEnter").OnServerEvent:Connect(function(player, ...)
		ExpeditionSystem.requestEnter(player, ...)
	end)

	-- A teleport Roblox accepted can still fail for one player. They are
	-- still here, so they are simply no longer on their way anywhere; the
	-- next autosave re-takes the save lock handOff released.
	TeleportService.TeleportInitFailed:Connect(function(player, result, message)
		if launching[player.UserId] then
			launching[player.UserId] = nil
			warn(`[ExpeditionSystem] teleport failed for {player.Name}: {result} {message}`)
			tell(player, nil, "The portal flickered. Try again.")
		end
	end)

	-- Timer sweep. One loop for every group rather than a task per player:
	-- the cost is fixed regardless of how many are running.
	task.spawn(function()
		while true do
			task.wait(GameConfig.Expedition.TimerSyncSeconds)
			local now = os.clock()
			for _, group in table.clone(groups) do
				if group.StartedAt == nil then
					continue
				end
				if ExpeditionCore.remaining(group.StartedAt, group.Duration, now) <= 0 then
					completeGroup(group)
				else
					for userId in group.Members do
						local player = Players:GetPlayerByUserId(userId)
						if player then
							syncTimer(player, group)
						end
					end
				end
			end
		end
	end)

	Players.PlayerRemoving:Connect(function(player)
		local state = active[player.UserId]
		if state then
			-- Leaving mid-expedition must not leak a stage or a slot.
			active[player.UserId] = nil
			state.Group.Members[player.UserId] = nil
			if state.Died then
				state.Died:Disconnect()
			end
			if not hosting and next(state.Group.Members) == nil then
				dropGroup(state.Group)
			end
		end
		lastEntryAt[player.UserId] = nil
		launching[player.UserId] = nil
	end)
end

--- Binds the Gate's ProximityPrompt once the hub exists. HubBuilder creates
--- the prompt (it owns geometry); this only attaches behaviour to it.
---
--- Triggered fires on the SERVER with the triggering player, so this path
--- carries no client data at all -- the strongest version of build spec
--- §3.4's "the client sends nothing".
function ExpeditionSystem.bindGatePrompt(): ()
	local anchor = gatePart()
	local prompt = anchor and anchor:FindFirstChild("EnterPrompt")
	if not prompt or not prompt:IsA("ProximityPrompt") then
		warn("[ExpeditionSystem] no GateAnchor prompt found; entry is remote-only")
		return
	end

	prompt.Triggered:Connect(function(player)
		ExpeditionSystem.requestEnter(player)
	end)
end

return ExpeditionSystem
