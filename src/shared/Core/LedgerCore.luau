--!strict
-- GLOBAL SCARCITY, DECIDED. Pure, so the one rule that can never be wrong is
-- the one rule that is fully testable.
--
-- THE PROBLEM THIS EXISTS FOR. "Only ten Catalyst Stars will ever exist" is a
-- promise about every server in the game at once, and the game's existing
-- cross-server channel cannot keep it: MessagingService is fire-and-forget,
-- lossy, rate-limited and reaches only the servers that happen to be running.
-- Two players on two servers can roll the tenth star in the same second and
-- both announcements are true.
--
-- The only atomic cross-server primitive Roblox offers is a DataStore
-- UpdateAsync transform, which the platform serialises per key. So the rule
-- is: the roll CLAIMS a number, and only a successful claim is a Catalyst
-- Star. Announce-then-claim gets you eleven of ten, publicly, and there is no
-- taking it back.
--
-- This module is the transform. LedgerSystem is the DataStore around it.

local Result = require(script.Parent.Result)

local LedgerCore = {}

export type Claim = {
	Number: number, -- 1..Cap, the nth ever issued
	UserId: number,
	Name: string,
	At: number,
}

export type Ledger = {
	Claims: { Claim },
}

--- An empty ledger. Also what a key that has never been written reads as.
function LedgerCore.newLedger(): Ledger
	return { Claims = {} }
end

--- Takes whatever came back from the DataStore -- nil, a table, or something
--- from an older build -- and returns a ledger. A malformed ledger is treated
--- as EMPTY only when it is unreadable in a way that cannot lose claims;
--- anything with a Claims array keeps it verbatim, because silently dropping
--- a claim would re-issue a unique item.
function LedgerCore.sanitise(stored: any): Ledger
	if type(stored) ~= "table" or type(stored.Claims) ~= "table" then
		return LedgerCore.newLedger()
	end

	local claims: { Claim } = {}
	for _, entry in stored.Claims do
		if type(entry) == "table" and type(entry.Number) == "number" then
			table.insert(claims, {
				Number = entry.Number,
				UserId = if type(entry.UserId) == "number" then entry.UserId else 0,
				Name = if type(entry.Name) == "string" then entry.Name else "?",
				At = if type(entry.At) == "number" then entry.At else 0,
			})
		end
	end

	table.sort(claims, function(a, b)
		return a.Number < b.Number
	end)

	return { Claims = claims }
end

function LedgerCore.issued(ledger: Ledger): number
	return #ledger.Claims
end

function LedgerCore.remaining(ledger: Ledger, cap: number): number
	return math.max(0, cap - LedgerCore.issued(ledger))
end

--- THE TRANSFORM. Returns Result.ok{ Ledger, Claim } or an error.
---
--- It must be pure and it must be idempotent-safe: UpdateAsync can call the
--- transform more than once for a single claim when it retries against a
--- newer version of the value, and the answer has to be right every time.
--- That is why the decision reads the ledger it was handed and never any
--- state of its own.
---
--- `claimant` = { UserId, Name }.
function LedgerCore.claim(stored: any, cap: number, claimant: any, now: number): any
	if type(cap) ~= "number" or cap < 1 then
		return Result.err("INVALID_CAP")
	end
	if type(claimant) ~= "table" or type(claimant.UserId) ~= "number" then
		return Result.err("INVALID_CLAIMANT")
	end

	local ledger = LedgerCore.sanitise(stored)

	if LedgerCore.issued(ledger) >= cap then
		-- The whole point. When the last one is gone it is gone, on every
		-- server, forever.
		return Result.err("EXHAUSTED")
	end

	local claim: Claim = {
		Number = LedgerCore.issued(ledger) + 1,
		UserId = claimant.UserId,
		Name = if type(claimant.Name) == "string" then claimant.Name else "?",
		At = now,
	}

	local claims = table.clone(ledger.Claims)
	table.insert(claims, claim)

	return Result.ok({
		Ledger = { Claims = claims },
		Claim = claim,
	})
end

--- A public summary: "3 of 10 found", and who found them. Scarcity that
--- nobody can see is a rumour rather than a feature -- this is what the Hall
--- of Legends displays.
function LedgerCore.summary(stored: any, cap: number): any
	local ledger = LedgerCore.sanitise(stored)
	return {
		Issued = LedgerCore.issued(ledger),
		Cap = cap,
		Remaining = LedgerCore.remaining(ledger, cap),
		Claims = ledger.Claims,
	}
end

return LedgerCore
