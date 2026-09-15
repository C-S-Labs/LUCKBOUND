--!strict
-- Profile persistence with session locking. Build spec T-109.
--
-- Session locking matters more than it looks: without it, two servers holding
-- the same player (rejoin during a shutdown, or a teleport) both write, and
-- the loser's progress vanishes. Losing a tester's Fate is how you lose the
-- tester.

local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local ProfileSchema = require(Root.Core.ProfileSchema)

local SaveSystem = {}

local store: DataStore?
-- True when DataStores are unreachable -- an unpublished local place, or the
-- API-services toggle left off. The game runs normally; nothing persists.
local volatileMode = false
local cache: { [number]: any } = {}
local dirty: { [number]: boolean } = {}
local lockId = game.JobId ~= "" and game.JobId or `studio-{os.time()}`

local function keyFor(userId: number): string
	return Constants.DATASTORE.KEY_PREFIX .. userId
end

local function retry<T>(label: string, fn: () -> T): T?
	for attempt = 1, GameConfig.Save.MaxRetries do
		local ok, result = pcall(fn)
		if ok then
			return result
		end
		warn(`[SaveSystem] {label} attempt {attempt} failed: {result}`)
		if attempt < GameConfig.Save.MaxRetries then
			task.wait(GameConfig.Save.RetryBackoffSeconds * attempt)
		end
	end
	return nil
end

--- Loads (or creates) a profile and takes the session lock.
function SaveSystem.load(player: Player): any
	local now = os.time()

	-- No store: hand out a temporary profile immediately rather than spending
	-- 20 seconds retrying a call that cannot succeed.
	if volatileMode or not store then
		local profile = ProfileSchema.default(now)
		profile.__volatile = true
		cache[player.UserId] = profile
		print(`[SaveSystem] {player.Name} given a temporary profile (no persistence this session)`)
		return profile
	end

	local loaded = retry(`load {player.UserId}`, function()
		return (store :: DataStore):UpdateAsync(keyFor(player.UserId), function(stored)
			stored = stored or {}

			-- Respect a live lock held by another server, unless it is stale.
			local lock = stored.__lock
			if lock and lock.owner ~= lockId then
				if now - (lock.at or 0) < GameConfig.Save.SessionLockTimeoutSeconds then
					return nil -- abort; another server still owns this profile
				end
			end

			stored.__lock = { owner = lockId, at = now }
			return stored
		end)
	end)

	local profile
	if loaded == nil then
		-- Locked elsewhere or the store is unreachable. Serve a non-persisting
		-- session rather than kicking: a tester losing a session beats a
		-- tester who cannot play. Marked so autosave skips it.
		warn(`[SaveSystem] could not acquire profile for {player.Name}; session will not persist`)
		profile = ProfileSchema.default(now)
		profile.__volatile = true
	else
		local hadData = loaded.SchemaVersion ~= nil
		local migrated, applied = ProfileSchema.migrate(loaded, now)
		if applied > 0 then
			print(`[SaveSystem] migrated {player.Name} through {applied} schema step(s)`)
		end
		if not hadData then
			print(`[SaveSystem] created new profile for {player.Name}`)
		end
		migrated.LastSeenAt = now
		profile = migrated
	end

	cache[player.UserId] = profile
	return profile
end

function SaveSystem.get(player: Player): any?
	return cache[player.UserId]
end

function SaveSystem.markDirty(player: Player): ()
	dirty[player.UserId] = true
end

--- Writes the profile back and optionally releases the lock.
function SaveSystem.save(player: Player, releaseLock: boolean?): boolean
	if volatileMode or not store then
		return false
	end
	local profile = cache[player.UserId]
	if not profile or profile.__volatile then
		return false
	end
	if not dirty[player.UserId] and not releaseLock then
		return true
	end

	ProfileSchema.prune(profile, GameConfig)
	profile.LastSeenAt = os.time()

	local payload = table.clone(profile)
	payload.__volatile = nil

	local result = retry(`save {player.UserId}`, function()
		return (store :: DataStore):UpdateAsync(keyFor(player.UserId), function(stored)
			local lock = stored and stored.__lock
			if lock and lock.owner ~= lockId then
				-- Another server took over mid-session. Its data is newer.
				return nil
			end
			payload.__lock = if releaseLock then nil else { owner = lockId, at = os.time() }
			return payload
		end)
	end)

	if result ~= nil then
		dirty[player.UserId] = false
		return true
	end
	return false
end

function SaveSystem.release(player: Player): ()
	if not volatileMode then
		SaveSystem.save(player, true)
	end
	cache[player.UserId] = nil
	dirty[player.UserId] = nil
end

--- True if profiles cannot persist this session. Read by anything that wants
--- to surface it to the player.
function SaveSystem.isVolatile(): boolean
	return volatileMode
end

function SaveSystem.init(): ()
	-- GetDataStore raises on an unpublished place ("You must publish this
	-- place to the web to access DataStore"). That is an expected condition
	-- while developing locally, not a programmer error, so it must not take
	-- the whole server down -- the bootstrap has not built the hub yet.
	local ok, result = pcall(function()
		return DataStoreService:GetDataStore(Constants.DATASTORE.PROFILE_STORE)
	end)

	if ok then
		store = result
	else
		volatileMode = true
		warn("[SaveSystem] DataStores unavailable; running WITHOUT persistence.")
		warn("[SaveSystem] Reason: " .. tostring(result))
		warn("[SaveSystem] Publish the place and enable Studio Access to API Services to save progress.")
		return -- no autosave loop, no BindToClose: there is nothing to write
	end

	task.spawn(function()
		while true do
			task.wait(GameConfig.Save.AutosaveIntervalSeconds)
			for _, player in Players:GetPlayers() do
				if dirty[player.UserId] then
					SaveSystem.save(player)
				end
			end
		end
	end)

	-- BindToClose is the difference between a clean shutdown and a lost
	-- session. Studio gives roughly 30s; live servers similar.
	game:BindToClose(function()
		if RunService:IsStudio() then
			task.wait(0.5)
		end
		for _, player in Players:GetPlayers() do
			task.spawn(SaveSystem.release, player)
		end
		task.wait(2)
	end)
end

return SaveSystem
