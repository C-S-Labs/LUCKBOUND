--!strict
-- Loot, fixtures and vault keys on an expedition map. Build spec §7.5.
--
-- Owner-directed 2026-09-23:
--   * Chests open ONCE PER PARTY, and every member present gets their OWN
--     randomised loot. The same goes for the boss.
--   * Each world's vault needs THAT world's key (Loot.VaultKey), which drops
--     only from that world's boss (for now, on first reaching the arena --
--     bosses are still §7-excluded) at its DropChance, once per party, in any
--     map of that world, treasury or not. If it drops, every member present
--     gets one.
--   * The vault is PER PLAYER: whoever uses their key opens it for
--     themselves -- only their key is spent, only they get its loot, and
--     only their screen shows the door open. Chests stay once per party.
--   * Keys are saved to the profile and carried home, one of each kind at
--     most. Using one takes it back to zero.
--
-- WHAT DROPS IS NOT DECIDED. Every pool ships empty (Content/LootPools), so
-- an opening rolls each member's share and today that share is nothing. What
-- a drop BECOMES -- an inventory item, currency -- is the open seam; see
-- grantDrops below and docs/RESERVED.md.
--
-- Trust: nothing here reads a client value. Opening is a ProximityPrompt,
-- whose Triggered fires on the server with the player; distance and party
-- membership are re-checked here anyway, and every roll is server-side on
-- this system's own Random (CLAUDE.md rules 5 and 6).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local ChunkCore = require(Root.Util.ChunkCore)
local Chunks = require(Root.Content.Chunks)
local Fixtures = require(Root.Content.Fixtures)
local FixtureCore = require(Root.Core.FixtureCore)
local GameConfig = require(Root.Core.GameConfig)
local KeyCore = require(Root.Core.KeyCore)
local LootCore = require(Root.Core.LootCore)
local LootPools = require(Root.Content.LootPools)
local Net = require(Root.Core.Net)
local Worlds = require(Root.Content.Worlds)

local LootSystem = {}

local SaveSystem

-- The one stream every roll here draws from.
local rng = Random.new()
-- Refused vault attempts, so holding E on a locked door does not flood toasts.
local lastRefusal: { [number]: number } = {}

-- DEVELOPER TESTING ONLY (/keychance, /boss). Remove with the debug commands.
local keyChanceOverride: number? = nil
-- Every furnished map, so /boss can find the one a player is on.
local maps: { { Stage: Instance, WorldId: string, Members: { [number]: boolean }, Boss: () -> () } } =
	{}

local function library(): Instance?
	return ReplicatedStorage:FindFirstChild("LuckboundProps")
end

local function presentMembers(members: { [number]: boolean }): { Player }
	local out = {}
	for userId in members do
		local player = Players:GetPlayerByUserId(userId)
		if player then
			table.insert(out, player)
		end
	end
	return out
end

--- THE SEAM. A drop is rolled and reported, and will be STORED once what an
--- ItemId is has been decided (docs/RESERVED.md). Until then every pool is
--- empty, so there is nothing to store; a non-empty drop is logged loudly
--- rather than silently lost.
local function grantDrops(player: Player, drops: { LootCore.Drop }, source: string)
	if #drops > 0 then
		warn(
			string.format(
				"[LootSystem] %s rolled %d drop(s) from %s, but item storage is not built yet (build spec §7.5)",
				player.Name,
				#drops,
				source
			)
		)
	end
end

local function tell(player: Player, payload: any)
	Net.get("Loot_Result"):FireClient(player, payload)
end

--- Rolls a pool once for every member present, each on their own draws.
--- `extra` adds fields to one player's result (a key they just spent), so
--- each player gets ONE message per opening.
local function rollFor(
	players: { Player },
	poolId: string?,
	source: string,
	extra: { [Player]: any }?
)
	local pool = poolId and LootPools[poolId]
	for _, player in players do
		local drops = if pool
			then LootCore.roll(pool, function()
				return rng:NextNumber()
			end)
			else {}
		grantDrops(player, drops, source)
		local payload = { Source = source, Drops = drops }
		for k, v in (extra and extra[player]) or {} do
			payload[k] = v
		end
		tell(player, payload)
	end
end

local function keysOf(player: Player): { [string]: number }?
	local profile = SaveSystem.get(player)
	if not profile then
		return nil
	end
	profile.Keys = profile.Keys or {}
	return profile.Keys
end

-- === placing fixtures ================================================

local function buildFixture(
	row: any,
	layout: CFrame,
	fix: CFrame,
	lib: Instance,
	missing: { [string]: boolean },
	parent: Instance
): Model?
	local r = row.R
	local frame = layout
		* CFrame.new(
			row.P[1],
			row.P[2],
			row.P[3],
			r[1],
			r[2],
			r[3],
			r[4],
			r[5],
			r[6],
			r[7],
			r[8],
			r[9]
		)
	local model = Instance.new("Model")
	model.Name = "Fixture_" .. row.Kind
	model:SetAttribute("FixtureKind", row.Kind)
	model:SetAttribute("Opened", false)
	local primary: BasePart? = nil
	for _, part in row.Parts do
		local source = lib:FindFirstChild(part.Mesh, true)
		if not (source and source:IsA("BasePart")) then
			missing[part.Mesh] = true
			model:Destroy()
			return nil
		end
		local mesh = source:Clone()
		mesh.Name = part.Role
		mesh.Anchored = true
		mesh.Size = Vector3.new(part.S[1], part.S[2], part.S[3])
		-- What stands still collides; what moves (a lid, the vault's dial)
		-- is animated on each client, so it must not collide on the server.
		mesh.CanCollide = part.Role == "Body" or part.Role == "Field"
		mesh.CanTouch = false
		mesh.CanQuery = mesh.CanCollide
		local base = frame * CFrame.new(part.P[1], part.P[2], part.P[3])
		mesh.CFrame = base * fix
		-- The client animates from these; the server never moves a part.
		mesh:SetAttribute("Base", base)
		mesh:SetAttribute("Fix", fix)
		if part.Hinge then
			mesh:SetAttribute("Hinge", Vector3.new(part.Hinge[1], part.Hinge[2], part.Hinge[3]))
		end
		mesh.Parent = model
		if part.Role == "Body" or part.Role == "Door" or part.Role == "Field" then
			primary = mesh
		end
	end
	model.PrimaryPart = primary
	model.Parent = parent
	return model
end

-- === opening =========================================================

local function standingNear(player: Player, part: BasePart): boolean
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not (root and root:IsA("BasePart")) then
		return false
	end
	-- The prompt already enforces this; checked again because the prompt's
	-- distance is a client-visible property, and slack for lag.
	return (root.Position - part.Position).Magnitude
		<= GameConfig.Loot.PromptDistance + GameConfig.Loot.PromptSlackStuds
end

local function markOpened(model: Model)
	model:SetAttribute("Opened", true)
	model:SetAttribute("OpenedAt", Workspace:GetServerTimeNow())
	local body = model.PrimaryPart
	local prompt = body and body:FindFirstChildOfClass("ProximityPrompt")
	if prompt then
		prompt:Destroy()
	end
end

local function openChest(model: Model, world: any, members: { [number]: boolean })
	markOpened(model)
	rollFor(presentMembers(members), world.Loot and world.Loot.Chest, "CHEST")
end

-- Who has opened which vault. A vault is PER PLAYER (owner, 2026-09-23):
-- each player who uses their own key opens it for themselves -- their key,
-- their loot, their door swinging open on their screen -- and a party member
-- who keeps their key sees it shut. Weak keys, so a destroyed map lets go.
local vaultOpenedBy: { [Model]: { [number]: boolean } } = setmetatable({}, { __mode = "k" }) :: any

local function openVault(player: Player, model: Model, world: any)
	local key = world.Loot and world.Loot.VaultKey
	if not key then
		return
	end
	local opened = vaultOpenedBy[model] or {}
	vaultOpenedBy[model] = opened
	if opened[player.UserId] then
		return
	end
	local keys = keysOf(player)
	if not keys or not KeyCore.spend(keys, key.Id) then
		local now = os.clock()
		if now - (lastRefusal[player.UserId] or 0) >= GameConfig.Loot.RefusalCooldownSeconds then
			lastRefusal[player.UserId] = now
			tell(
				player,
				{ Source = "VAULT", Drops = {}, Message = `Locked. It needs a {key.Name}.` }
			)
		end
		return
	end

	opened[player.UserId] = true
	SaveSystem.markDirty(player)
	-- Only this player's roll, and the vault named so their client -- and only
	-- theirs -- swings the door open and drops its prompt.
	rollFor({ player }, world.Loot.Vault, "VAULT", {
		[player] = { KeySpent = { Id = key.Id, Name = key.Name }, Fixture = model },
	})
end

-- === the boss (stand-in) =============================================

local function bossDefeated(worldId: string, members: { [number]: boolean })
	local world = Worlds[worldId]
	local present = presentMembers(members)
	rollFor(present, world.Loot and world.Loot.Boss, "BOSS")

	local key = world.Loot and world.Loot.VaultKey
	-- A world's key drops only from THAT world's boss (it is that world's
	-- Loot.VaultKey), but in every map of it, treasury or not (owner,
	-- 2026-09-23): the key is kept for the vault you meet later.
	if not key then
		return
	end
	-- World modifiers are still §7-excluded; the list they will fill is here
	-- so they can move the chance without touching this file.
	local modifiers = {}
	local chance = keyChanceOverride or KeyCore.dropChance(key.DropChance, modifiers)
	-- ONE roll for the party.
	if rng:NextNumber() >= chance then
		return
	end
	for _, member in present do
		local keys = keysOf(member)
		if keys then
			local gained = KeyCore.grant(keys, key.Id, GameConfig.Loot.MaxKeysPerKind)
			if gained then
				SaveSystem.markDirty(member)
			end
			tell(member, {
				Source = "BOSS",
				Drops = {},
				KeyGained = { Id = key.Id, Name = key.Name },
				Message = if gained then nil else `You already carry a {key.Name}.`,
			})
		end
	end
end

local function watchArena(
	stage: Instance,
	arena: Instance,
	onReached: () -> (),
	members: { [number]: boolean }
)
	local chunk = Chunks[arena:GetAttribute("ChunkId") :: string]
	local centre = arena:GetAttribute("Centre")
	if not chunk or typeof(centre) ~= "Vector3" then
		return
	end
	local radius = math.min(chunk.SizeX, chunk.SizeZ) * GameConfig.Loot.ArenaRadiusFraction
	task.spawn(function()
		while stage.Parent do
			for _, player in presentMembers(members) do
				local character = player.Character
				local root = character and character:FindFirstChild("HumanoidRootPart")
				if root and root:IsA("BasePart") then
					local d = root.Position - centre
					if
						Vector2.new(d.X, d.Z).Magnitude <= radius
						and d.Y > -GameConfig.Loot.ArenaBelowStuds
					then
						onReached()
						return
					end
				end
			end
			task.wait(GameConfig.Loot.ArenaCheckSeconds)
		end
	end)
end

-- === the one entry point =============================================

--- Furnishes one expedition map: places its fixtures, wires their prompts,
--- and (while bosses do not exist) watches the arena for the boss stand-in.
--- `members` is the group's own member table, read live, so whoever is on
--- the map when something opens is who shares it.
function LootSystem.attach(stage: Instance, worldId: string, members: { [number]: boolean })
	local world = Worlds[worldId]
	local set = Fixtures[worldId]
	local cfg = GameConfig.Loot
	local arena: Instance? = nil
	local lib = library()
	local missing: { [string]: boolean } = {}
	local folder = Instance.new("Folder")
	folder.Name = "Fixtures"
	folder.Parent = stage

	for _, chunkFolder in stage:GetChildren() do
		local chunkId = chunkFolder:GetAttribute("ChunkId")
		if type(chunkId) ~= "string" then
			continue
		end
		if chunkFolder:GetAttribute("Role") == "BOSS" then
			arena = chunkFolder
		end
		local rows = set and set.Placements[chunkId]
		local centre = chunkFolder:GetAttribute("Centre")
		local yaw = chunkFolder:GetAttribute("Yaw")
		if not rows or typeof(centre) ~= "Vector3" or type(yaw) ~= "number" or not lib then
			continue
		end
		local layout = CFrame.new(centre) * CFrame.Angles(0, ChunkCore.yawRadians(yaw), 0)
		local chunk = Chunks[chunkId]
		local fix = CFrame.Angles(0, ChunkCore.yawRadians((chunk and chunk.MeshYawOffset) or 0), 0)
		for _, row in rows do
			local model = buildFixture(row, layout, fix, lib :: Instance, missing, folder)
			if model and FixtureCore.OPENABLE[row.Kind] and model.PrimaryPart then
				local prompt = Instance.new("ProximityPrompt")
				prompt.ActionText = if row.Kind == "VAULT" then "UNLOCK" else "OPEN"
				prompt.ObjectText = if row.Kind == "VAULT"
						and world.Loot
						and world.Loot.VaultKey
					then world.Loot.VaultKey.Name
					else "Chest"
				prompt.HoldDuration = cfg.PromptHoldSeconds
				prompt.MaxActivationDistance = cfg.PromptDistance
				prompt.RequiresLineOfSight = false
				prompt.Parent = model.PrimaryPart
				prompt.Triggered:Connect(function(player)
					-- A chest's Opened is the party's; a vault's is per player
					-- (openVault keeps it).
					if model:GetAttribute("Opened") or not members[player.UserId] then
						return
					end
					if not standingNear(player, model.PrimaryPart :: BasePart) then
						return
					end
					if row.Kind == "CHEST" then
						openChest(model, world, members)
					else
						openVault(player, model, world)
					end
				end)
			end
		end
	end

	if set and not lib then
		warn(
			`[LootSystem] no prop library in ReplicatedStorage.LuckboundProps; {worldId} has no fixtures`
		)
	elseif next(missing) then
		local names = {}
		for name in missing do
			table.insert(names, name)
		end
		table.sort(names)
		warn(`[LootSystem] fixture meshes missing from the library: {table.concat(names, ", ")}`)
	end

	table.insert(maps, {
		Stage = stage,
		WorldId = worldId,
		Members = members,
		Boss = function()
			bossDefeated(worldId, members)
		end,
	})
	for i = #maps, 1, -1 do
		if maps[i].Stage.Parent == nil then
			table.remove(maps, i)
		end
	end

	if cfg.BossDefeatStandIn and arena then
		local done = false
		watchArena(stage, arena :: Instance, function()
			if not done then
				done = true
				bossDefeated(worldId, members)
			end
		end, members)
	end
end

-- === developer testing only (DebugSystem) ============================
-- Everything below exists for the /keychance, /boss, /givekey, /takekey and
-- /keys commands, and goes when they do.

function LootSystem.setKeyChanceOverride(chance: number?): ()
	keyChanceOverride = chance
end

function LootSystem.keyChanceOverride(): number?
	return keyChanceOverride
end

--- Fires the boss stand-in for the map this player is on, as if the boss had
--- just been defeated. Repeatable, unlike the real one.
function LootSystem.triggerBoss(player: Player): (boolean, string)
	for _, map in maps do
		if map.Stage.Parent and map.Members[player.UserId] then
			map.Boss()
			return true, `boss stand-in fired on {map.WorldId}`
		end
	end
	return false, "you are not on an expedition map"
end

--- Every world's vault key, by Id.
function LootSystem.keyDefinitions(): { [string]: any }
	local out = {}
	for _, world in Worlds do
		local key = world.Loot and world.Loot.VaultKey
		if key then
			out[key.Id] = key
		end
	end
	return out
end

function LootSystem.giveKey(player: Player, keyId: string): (boolean, string)
	local key = LootSystem.keyDefinitions()[keyId]
	local keys = keysOf(player)
	if not key or not keys then
		return false, `no key '{keyId}', or your profile is not loaded`
	end
	if not KeyCore.grant(keys, key.Id, GameConfig.Loot.MaxKeysPerKind) then
		return false, `you already hold the maximum {key.Name}`
	end
	SaveSystem.markDirty(player)
	return true, `gave you a {key.Name}`
end

function LootSystem.takeKeys(player: Player): (boolean, string)
	local profile = SaveSystem.get(player)
	if not profile then
		return false, "your profile is not loaded"
	end
	profile.Keys = {}
	SaveSystem.markDirty(player)
	return true, "removed all your keys"
end

function LootSystem.keysOf(player: Player): { [string]: number }
	return keysOf(player) or {}
end

function LootSystem.init(saveSystem: any): ()
	SaveSystem = saveSystem
	Players.PlayerRemoving:Connect(function(player)
		lastRefusal[player.UserId] = nil
	end)
end

return LootSystem
