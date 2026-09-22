--!strict
-- PARTY RULES. Pure: no Roblox globals, no Instances, no remotes -- so every
-- rule below runs in CI, and there is exactly one place that answers "who is
-- in whose party, and who may do what to it?"
--
-- PartySystem (server) owns the plumbing: the remote, the rate limit, names,
-- and telling clients. This file owns the decisions. Same split as
-- ExpeditionCore/ExpeditionSystem.
--
-- THE SHAPE OF IT, owner-directed 2026-09-22:
--   * Up to GameConfig.Party.MaxSize players. One leader.
--   * Only the leader invites, kicks and promotes. Anyone may leave.
--   * An invite does not create a party; ACCEPTING one does. A declined
--     invite therefore leaves nothing behind -- no party of one lingering.
--   * A party that drops to one member disbands. A party of one is just a
--     player.
--   * The leader leaving hands leadership to the longest-standing member.
--   * The roll stays personal. A party travels on its LEADER's roll
--     (`expeditionGroup`), so everyone enters the same world and seed.
--
-- State is mutated in place and every operation returns a Result whose `err`
-- is a sentence a player can read. Nothing here is secret: unlike the roll
-- and entry guards, a party refusal is always the player's own business.

local Result = require(script.Parent.Result)

local PartyCore = {}

export type Party = {
	Id: number,
	LeaderUserId: number,
	-- Join order. The leader is not necessarily first; `Members[1]` after
	-- the leader is who inherits leadership.
	Members: { number },
}

export type Invite = {
	FromUserId: number,
	ToUserId: number,
	ExpiresAt: number,
}

export type State = {
	Parties: { [number]: Party },
	MemberOf: { [number]: number },
	-- Invites[toUserId][fromUserId]. One invite per pair; re-inviting
	-- refreshes the expiry rather than stacking.
	Invites: { [number]: { [number]: Invite } },
	NextId: number,
}

-- The complete set of things a client may ask for. Anything else is dropped.
local ACTIONS: { [string]: boolean } = {
	INVITE = true,
	ACCEPT = true,
	DECLINE = true,
	LEAVE = true,
	KICK = true,
	PROMOTE = true,
}
PartyCore.ACTIONS = table.freeze(ACTIONS)

-- Actions that name another player. LEAVE names nobody.
local NEEDS_TARGET: { [string]: boolean } =
	{ INVITE = true, ACCEPT = true, DECLINE = true, KICK = true, PROMOTE = true }

function PartyCore.newState(): State
	return { Parties = {}, MemberOf = {}, Invites = {}, NextId = 1 }
end

function PartyCore.partyOf(state: State, userId: number): Party?
	local id = state.MemberOf[userId]
	return if id then state.Parties[id] else nil
end

function PartyCore.isLeader(state: State, userId: number): boolean
	local party = PartyCore.partyOf(state, userId)
	return party ~= nil and party.LeaderUserId == userId
end

local function disband(state: State, party: Party)
	for _, member in party.Members do
		state.MemberOf[member] = nil
	end
	state.Parties[party.Id] = nil
end

local function removeMember(party: Party, userId: number)
	local index = table.find(party.Members, userId)
	if index then
		table.remove(party.Members, index)
	end
end

--- Validates a Party_Request payload. The client names an action and, for
--- most actions, a UserId. The UserId is only an IDENTIFIER: the server still
--- checks that player is actually in this server before anything happens.
function PartyCore.parseRequest(payload: any)
	if type(payload) ~= "table" then
		return Result.err("Malformed request.")
	end
	local action = payload.Action
	if type(action) ~= "string" or not PartyCore.ACTIONS[action] then
		return Result.err("Unknown party action.")
	end
	local target = payload.TargetUserId
	if NEEDS_TARGET[action] then
		-- An integer UserId in range. NaN fails the floor comparison and
		-- infinity fails the bound, so neither reaches a table lookup.
		if
			type(target) ~= "number"
			or target ~= math.floor(target)
			or target <= 0
			or target >= 2 ^ 53
		then
			return Result.err("No player named.")
		end
	else
		target = nil
	end
	return Result.ok({ Action = action, TargetUserId = target })
end

function PartyCore.invite(
	state: State,
	fromUserId: number,
	toUserId: number,
	now: number,
	config: any
)
	if fromUserId == toUserId then
		return Result.err("You cannot invite yourself.")
	end

	local mine = PartyCore.partyOf(state, fromUserId)
	if mine and mine.LeaderUserId ~= fromUserId then
		return Result.err("Only the party leader can invite.")
	end

	local theirs = PartyCore.partyOf(state, toUserId)
	if theirs then
		if mine and theirs.Id == mine.Id then
			return Result.err("They are already in your party.")
		end
		return Result.err("That player is already in a party.")
	end

	if mine and #mine.Members >= config.Party.MaxSize then
		return Result.err("Your party is full.")
	end

	local inbox = state.Invites[toUserId]
	if not inbox then
		inbox = {}
		state.Invites[toUserId] = inbox
	end
	inbox[fromUserId] = {
		FromUserId = fromUserId,
		ToUserId = toUserId,
		ExpiresAt = now + config.Party.InviteExpirySeconds,
	}
	return Result.ok(inbox[fromUserId])
end

function PartyCore.accept(
	state: State,
	toUserId: number,
	fromUserId: number,
	now: number,
	config: any
)
	local inbox = state.Invites[toUserId]
	local invite = inbox and inbox[fromUserId]
	if not invite or invite.ExpiresAt <= now then
		if inbox then
			inbox[fromUserId] = nil
		end
		return Result.err("That invite has expired.")
	end

	if PartyCore.partyOf(state, toUserId) then
		return Result.err("Leave your party first.")
	end

	local party = PartyCore.partyOf(state, fromUserId)
	if party and party.LeaderUserId ~= fromUserId then
		-- The inviter joined someone else's party (or lost the lead) since
		-- sending it. The invite was for a party that no longer exists.
		inbox[fromUserId] = nil
		return Result.err("That invite is no longer valid.")
	end
	if party and #party.Members >= config.Party.MaxSize then
		return Result.err("That party is full.")
	end

	if not party then
		local created: Party =
			{ Id = state.NextId, LeaderUserId = fromUserId, Members = { fromUserId } }
		state.NextId += 1
		state.Parties[created.Id] = created
		state.MemberOf[fromUserId] = created.Id
		-- The inviter is in a party now; anything addressed to them would
		-- pull them out of it, so it goes.
		state.Invites[fromUserId] = nil
		party = created
	end

	local joined = party :: Party
	table.insert(joined.Members, toUserId)
	state.MemberOf[toUserId] = joined.Id
	-- Every other invite this player held is moot: they are in a party.
	state.Invites[toUserId] = nil
	return Result.ok(joined)
end

function PartyCore.decline(state: State, toUserId: number, fromUserId: number)
	local inbox = state.Invites[toUserId]
	if inbox then
		inbox[fromUserId] = nil
	end
	return Result.ok(true)
end

--- Leaves the party. Returns what happened, so the system knows whom to
--- tell: `Disbanded` when the party fell to one, `NewLeaderUserId` when the
--- lead passed on.
function PartyCore.leave(state: State, userId: number)
	local party = PartyCore.partyOf(state, userId)
	if not party then
		return Result.err("You are not in a party.")
	end

	local affected = table.clone(party.Members)
	removeMember(party, userId)
	state.MemberOf[userId] = nil

	if #party.Members <= 1 then
		disband(state, party)
		return Result.ok({
			PartyId = party.Id,
			Disbanded = true,
			NewLeaderUserId = nil,
			Affected = affected,
		})
	end

	local newLeader = nil
	if party.LeaderUserId == userId then
		party.LeaderUserId = party.Members[1]
		newLeader = party.LeaderUserId
	end
	return Result.ok({
		PartyId = party.Id,
		Disbanded = false,
		NewLeaderUserId = newLeader,
		Affected = affected,
	})
end

function PartyCore.kick(state: State, leaderUserId: number, targetUserId: number)
	local party = PartyCore.partyOf(state, leaderUserId)
	if not party or party.LeaderUserId ~= leaderUserId then
		return Result.err("Only the party leader can remove players.")
	end
	if targetUserId == leaderUserId then
		return Result.err("Use Leave to leave your own party.")
	end
	if state.MemberOf[targetUserId] ~= party.Id then
		return Result.err("They are not in your party.")
	end
	return PartyCore.leave(state, targetUserId)
end

function PartyCore.promote(state: State, leaderUserId: number, targetUserId: number)
	local party = PartyCore.partyOf(state, leaderUserId)
	if not party or party.LeaderUserId ~= leaderUserId then
		return Result.err("Only the party leader can hand over the lead.")
	end
	if targetUserId == leaderUserId then
		return Result.err("You already lead this party.")
	end
	if state.MemberOf[targetUserId] ~= party.Id then
		return Result.err("They are not in your party.")
	end
	party.LeaderUserId = targetUserId
	return Result.ok(party)
end

--- A player left the server. Out of their party, and every invite to or from
--- them is gone. Returns the UserIds whose view of the world changed.
function PartyCore.removePlayer(state: State, userId: number): { number }
	local affected = {}
	local left = PartyCore.leave(state, userId)
	if left.ok then
		for _, member in left.value.Affected do
			if member ~= userId then
				table.insert(affected, member)
			end
		end
	end

	state.Invites[userId] = nil
	for toUserId, inbox in state.Invites do
		if inbox[userId] then
			inbox[userId] = nil
			table.insert(affected, toUserId)
		end
	end
	return affected
end

--- Drops expired invites. Returns the invitees whose list changed.
function PartyCore.pruneInvites(state: State, now: number): { number }
	local changed = {}
	for toUserId, inbox in state.Invites do
		local any = false
		for fromUserId, invite in inbox do
			if invite.ExpiresAt <= now then
				inbox[fromUserId] = nil
				any = true
			end
		end
		if any then
			table.insert(changed, toUserId)
		end
		if next(inbox) == nil then
			state.Invites[toUserId] = nil
		end
	end
	return changed
end

--- Live invites addressed to `userId`, soonest to expire first.
function PartyCore.invitesFor(
	state: State,
	userId: number,
	now: number
): { { FromUserId: number, RemainingSeconds: number } }
	type Entry = { FromUserId: number, RemainingSeconds: number }
	local list: { Entry } = {}
	for fromUserId, invite in state.Invites[userId] or {} do
		if invite.ExpiresAt > now then
			table.insert(
				list,
				{ FromUserId = fromUserId, RemainingSeconds = invite.ExpiresAt - now }
			)
		end
	end
	table.sort(list, function(a: Entry, b: Entry)
		if a.RemainingSeconds ~= b.RemainingSeconds then
			return a.RemainingSeconds < b.RemainingSeconds
		end
		return a.FromUserId < b.FromUserId
	end)
	return list
end

--- Who goes through the portal when `userId` walks into it.
---
---   SOLO    -- not in a party. Just them.
---   LEADER  -- the whole party, leader first. Everyone travels on the
---              leader's roll.
---   MEMBER  -- nobody. A member cannot take the party anywhere, and going
---              alone would split it without anyone deciding to.
function PartyCore.expeditionGroup(
	state: State,
	userId: number
): { Role: string, Members: { number } }
	local party = PartyCore.partyOf(state, userId)
	if not party then
		return { Role = "SOLO", Members = { userId } }
	end
	if party.LeaderUserId ~= userId then
		return { Role = "MEMBER", Members = {} }
	end
	local members = { userId }
	for _, member in party.Members do
		if member ~= userId then
			table.insert(members, member)
		end
	end
	return { Role = "LEADER", Members = members }
end

--- REBUILDING A PARTY AFTER AN EXPEDITION.
---
--- Parties live in a hub server's memory, and an expedition happens on a
--- different server. So the expedition server writes, for each member, "you
--- were in LeaderUserId's party", and the hub server they land on calls this
--- as each one arrives.
---
--- `pending[userId] = { LeaderUserId, ExpiresAt }`. `present[userId]` is true
--- for everyone in this server. A member is placed once their leader is here;
--- until then they wait, and after ExpiresAt they stop waiting. The leader's
--- own entry is kept until it expires, so a member landing after the party
--- has formed still finds it.
---
--- Returns the UserIds whose party changed, so the system can re-sync them.
function PartyCore.reunite(
	state: State,
	pending: { [number]: { LeaderUserId: number, ExpiresAt: number } },
	present: { [number]: boolean },
	now: number,
	config: any
): { number }
	local changed = {}

	for userId, entry in pending do
		if entry.ExpiresAt <= now then
			pending[userId] = nil
		end
	end

	-- Sorted so the outcome does not depend on table iteration order: the
	-- same arrivals always build the same party.
	local waiting = {}
	for userId, entry in pending do
		if userId ~= entry.LeaderUserId and present[userId] then
			table.insert(waiting, userId)
		end
	end
	table.sort(waiting)

	for _, userId in waiting do
		local leaderId = pending[userId].LeaderUserId
		if not present[leaderId] then
			continue -- not home yet; try again when they land
		end
		if PartyCore.partyOf(state, userId) then
			pending[userId] = nil -- joined something else meanwhile
			continue
		end

		local party = PartyCore.partyOf(state, leaderId)
		if party and party.LeaderUserId ~= leaderId then
			pending[userId] = nil -- the leader is following someone else now
			continue
		end
		if party and #party.Members >= config.Party.MaxSize then
			pending[userId] = nil
			continue
		end

		if not party then
			local created: Party =
				{ Id = state.NextId, LeaderUserId = leaderId, Members = { leaderId } }
			state.NextId += 1
			state.Parties[created.Id] = created
			state.MemberOf[leaderId] = created.Id
			state.Invites[leaderId] = nil
			table.insert(changed, leaderId)
			party = created
		end

		local joined = party :: Party
		table.insert(joined.Members, userId)
		state.MemberOf[userId] = joined.Id
		state.Invites[userId] = nil
		pending[userId] = nil
		table.insert(changed, userId)
		for _, member in joined.Members do
			if not table.find(changed, member) then
				table.insert(changed, member)
			end
		end
	end

	return changed
end

--- What one client is shown. UserIds only; the system adds display names,
--- because names come from Players and this file cannot see it.
function PartyCore.snapshotFor(state: State, userId: number, now: number, config: any)
	local party = PartyCore.partyOf(state, userId)
	return {
		PartyId = if party then party.Id else nil,
		LeaderUserId = if party then party.LeaderUserId else nil,
		Members = if party then table.clone(party.Members) else {},
		IsLeader = party ~= nil and party.LeaderUserId == userId,
		Invites = PartyCore.invitesFor(state, userId, now),
		MaxSize = config.Party.MaxSize,
	}
end

return PartyCore
