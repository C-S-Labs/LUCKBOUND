--!strict
-- THE GLOBAL LEDGER: the only thing in the game that knows how many of a
-- unique item have ever existed, on any server, since launch.
--
-- ONE RULE, AND IT IS THE WHOLE SYSTEM:
--
--     CLAIM FIRST. ANNOUNCE SECOND.
--
-- A roll that announces a one-of-ten and then records it will, on a busy day,
-- announce eleven. UpdateAsync is serialised per key by the platform, so a
-- claim that comes back with a number is the only proof that the number is
-- yours. Everything else -- the banner, the sky, the item -- hangs off that.
--
-- AND IT FAILS CLOSED. SaveSystem, faced with an unreachable DataStore, runs
-- the game without persistence: the worst case is a lost session. This system
-- faced with the same outage must REFUSE, because the worst case here is a
-- unique item that was never counted, announced to every server in the game,
-- with no way to take it back. Two DataStore wrappers, opposite instincts,
-- and the difference is deliberate (GameConfig.Ledger.GrantWhenUnavailable).

local DataStoreService = game:GetService("DataStoreService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local LedgerCore = require(Root.Core.LedgerCore)
local Result = require(Root.Core.Result)

local LedgerSystem = {}

local store: DataStore? = nil
local available = false

local function keyFor(id: string): string
	return Constants.DATASTORE.LEDGER_PREFIX .. id
end

--- CLAIMS THE NEXT NUMBER, or refuses. Yields.
---
--- Returns Result.ok{ Number, Cap, Remaining } on success. On failure the
--- error is one of:
---   EXHAUSTED   -- all of them are already out there. This is not an error
---                  condition so much as the system working.
---   UNAVAILABLE -- the ledger could not be reached. Refused on purpose.
---   DISABLED    -- GameConfig.Ledger.Enabled is false.
---
--- The caller must treat anything other than ok as "this did not happen":
--- no announcement, no event, no item.
function LedgerSystem.claim(id: string, cap: number, player: Player): any
	if not GameConfig.Ledger.Enabled then
		return Result.err("DISABLED")
	end

	if not available or not store then
		if GameConfig.Ledger.GrantWhenUnavailable then
			-- Deliberately reachable and deliberately loud: somebody has to
			-- have decided this, and the log is the evidence they did.
			warn(`[Ledger] granting '{id}' UNCOUNTED -- GrantWhenUnavailable is true`)
			return Result.ok({ Number = 0, Cap = cap, Remaining = cap, Uncounted = true })
		end
		warn(`[Ledger] refusing '{id}': ledger unavailable`)
		return Result.err("UNAVAILABLE")
	end

	local claimant = { UserId = player.UserId, Name = player.Name }
	local claimed: any = nil
	local outcome: string? = nil

	for attempt = 1, GameConfig.Ledger.MaxRetries do
		local ok, err = pcall(function()
			(store :: DataStore):UpdateAsync(keyFor(id), function(stored)
				local decision = LedgerCore.claim(stored, cap, claimant, os.time())
				if not decision.ok then
					outcome = decision.err
					-- Returning nil aborts the write: nothing is stored, and
					-- the value on the key is left exactly as it was.
					return nil
				end
				outcome = nil
				claimed = decision.value.Claim
				return decision.value.Ledger
			end)
		end)

		if ok then
			if outcome ~= nil then
				return Result.err(outcome :: string)
			end
			if claimed then
				local number = claimed.Number
				print(`[Ledger] '{id}' #{number} of {cap} claimed by {player.Name}`)
				return Result.ok({
					Number = number,
					Cap = cap,
					Remaining = math.max(0, cap - number),
				})
			end
			-- Wrote nothing and refused nothing: treat as unavailable rather
			-- than guessing.
			return Result.err("UNAVAILABLE")
		end

		warn(`[Ledger] claim '{id}' attempt {attempt} failed: {err}`)
		if attempt < GameConfig.Ledger.MaxRetries then
			task.wait(GameConfig.Ledger.RetryBackoffSeconds * attempt)
		end
	end

	return Result.err("UNAVAILABLE")
end

--- Reads the public summary without claiming anything: how many are out
--- there, and who has them. Scarcity nobody can see is a rumour rather than a
--- feature -- this is what the Hall of Legends displays.
function LedgerSystem.summary(id: string, cap: number): any
	if not available or not store then
		return Result.err("UNAVAILABLE")
	end

	local ok, value = pcall(function()
		return (store :: DataStore):GetAsync(keyFor(id))
	end)

	if not ok then
		warn(`[Ledger] summary '{id}' failed: {value}`)
		return Result.err("UNAVAILABLE")
	end

	return Result.ok(LedgerCore.summary(value, cap))
end

function LedgerSystem.isAvailable(): boolean
	return available
end

function LedgerSystem.init(): ()
	if not GameConfig.Ledger.Enabled then
		print("[Ledger] disabled (GameConfig.Ledger.Enabled)")
		return
	end

	-- Same expected failure SaveSystem handles: GetDataStore raises on an
	-- unpublished place. It must not take the server down -- it must make
	-- every claim refuse, which is what `available` staying false does.
	local ok, result = pcall(function()
		return DataStoreService:GetDataStore(Constants.DATASTORE.LEDGER_STORE)
	end)

	if ok then
		store = result
		available = true
	else
		warn("[Ledger] DataStores unavailable -- NO unique item can be granted on this server.")
		warn("[Ledger] Reason: " .. tostring(result))
	end
end

return LedgerSystem
