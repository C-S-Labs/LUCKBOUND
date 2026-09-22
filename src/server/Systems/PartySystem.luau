--!strict
-- PARTIES: the server half. Build spec §7.2.
--
-- PartyCore owns every rule; this file owns the remote, the rate limit,
-- display names, MemoryStore, and telling clients. If a rule appears in here
-- it is in the wrong file.
--
-- WHAT A CLIENT MAY SAY: an action name and, for most actions, a UserId. The
-- UserId is only an identifier -- it must name a player who is in THIS server
-- right now, or the request is refused before PartyCore sees it. Nothing
-- else crosses the wire (CLAUDE.md rule 5).
--
-- WHERE A PARTY LIVES. In this server's memory, and nowhere else. An
-- expedition happens on a different server (ExpeditionSystem, §7.2), so the
-- party cannot simply wait here for its members to come back; instead the
-- expedition server writes "you were in X's party" to MemoryStore for each
-- member as it sends them home, and whichever hub server they land on reads
-- it and rebuilds the party with PartyCore.reunite.

local MemoryStoreService = game:GetService("MemoryStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local Net = require(Root.Core.Net)
local PartyCore = require(Root.Core.PartyCore)

local PartySystem = {}

local state = PartyCore.newState()
-- Members on their way home from an expedition, waiting for their leader.
-- Times are os.time(), because the entries are written by another server.
local pending: { [number]: { LeaderUserId: number, ExpiresAt: number } } = {}

type Limiter = { Count: number, WindowStartedAt: number }
local limiter: { [number]: Limiter } = {}

-- Same fixed-window limiter HubUISystem uses for travel: it makes spam
-- pointless without ever being felt by someone clicking buttons.
local function allow(userId: number): boolean
	local now = os.clock()
	local entry = limiter[userId]
	if not entry or now - entry.WindowStartedAt >= 60 then
		limiter[userId] = { Count = 1, WindowStartedAt = now }
		return true
	end
	if entry.Count >= GameConfig.Party.RequestsPerMinute then
		return false
	end
	entry.Count += 1
	return true
end

local reuniteMap: MemoryStoreHashMap? = nil
local function reuniteStore(): MemoryStoreHashMap?
	if reuniteMap then
		return reuniteMap
	end
	local ok, map = pcall(function()
		return MemoryStoreService:GetHashMap(Constants.DATASTORE.PARTY_REUNITE)
	end)
	if ok then
		reuniteMap = map
		return map
	end
	return nil
end

local function nameOf(userId: number): string
	local player = Players:GetPlayerByUserId(userId)
	return if player then player.DisplayName else `Player {userId}`
end

--- Sends one player their whole party picture. `message` is an optional
--- sentence for the panel's toast -- the answer to whatever they just asked.
function PartySystem.sync(player: Player, message: string?, good: boolean?): ()
	local snapshot: any = PartyCore.snapshotFor(state, player.UserId, os.clock(), GameConfig)

	-- Names ride along with the ids so the client never has to look anybody
	-- up. Everyone in the server is listed, because the panel's "Players
	-- here" section is where invites are sent from.
	local names: { [string]: string } = {}
	local others = {}
	for _, other in Players:GetPlayers() do
		names[tostring(other.UserId)] = other.DisplayName
		if other ~= player then
			table.insert(others, {
				UserId = other.UserId,
				Name = other.DisplayName,
				InParty = PartyCore.partyOf(state, other.UserId) ~= nil,
			})
		end
	end
	for _, member in snapshot.Members do
		names[tostring(member)] = nameOf(member)
	end
	for _, invite in snapshot.Invites do
		names[tostring(invite.FromUserId)] = nameOf(invite.FromUserId)
	end
	table.sort(others, function(a, b)
		return a.Name < b.Name
	end)

	snapshot.Names = names
	snapshot.Others = others
	snapshot.Message = message
	snapshot.Good = good == true
	Net.get("Party_Sync"):FireClient(player, snapshot)
end

local function syncIds(userIds: { number })
	local seen = {}
	for _, userId in userIds do
		if not seen[userId] then
			seen[userId] = true
			local player = Players:GetPlayerByUserId(userId)
			if player then
				PartySystem.sync(player)
			end
		end
	end
end

--- Everyone's "Players here" list goes stale whenever somebody joins, leaves
--- or changes party. Cheap: one small table per player, on events a human
--- causes, never on a timer.
local function syncEveryone(except: Player?)
	for _, player in Players:GetPlayers() do
		if player ~= except then
			PartySystem.sync(player)
		end
	end
end

local function partyMemberIds(userId: number): { number }
	local party = PartyCore.partyOf(state, userId)
	return if party then table.clone(party.Members) else {}
end

function PartySystem.handle(player: Player, payload: any): ()
	if not GameConfig.Party.Enabled then
		return
	end
	if not allow(player.UserId) then
		return -- silent: a refused spammer is told nothing
	end

	local parsed = PartyCore.parseRequest(payload)
	if not parsed.ok then
		PartySystem.sync(player, parsed.err, false)
		return
	end
	local action = parsed.value.Action
	local targetId = parsed.value.TargetUserId

	-- The UserId must be somebody actually here. DECLINE is the exception:
	-- declining an invite from someone who has since left is still a tidy
	-- thing to let a player do.
	local target = if targetId then Players:GetPlayerByUserId(targetId) else nil
	if targetId and not target and action ~= "DECLINE" then
		PartySystem.sync(player, "That player is not in this server.", false)
		return
	end

	local me = player.UserId
	local result
	local message
	-- Who needs a fresh picture afterwards. The actor always does.
	local touched = { me }

	if action == "INVITE" then
		result = PartyCore.invite(state, me, targetId :: number, os.clock(), GameConfig)
		message = if result.ok then `Invited {nameOf(targetId :: number)}.` else nil
		table.insert(touched, targetId :: number)
	elseif action == "ACCEPT" then
		result = PartyCore.accept(state, me, targetId :: number, os.clock(), GameConfig)
		message = if result.ok then `You joined {nameOf(targetId :: number)}'s party.` else nil
		if result.ok then
			for _, member in result.value.Members do
				table.insert(touched, member)
			end
		end
	elseif action == "DECLINE" then
		result = PartyCore.decline(state, me, targetId :: number)
		message = "Invite declined."
	elseif action == "LEAVE" then
		local before = partyMemberIds(me)
		result = PartyCore.leave(state, me)
		message = if result.ok then "You left the party." else nil
		for _, member in before do
			table.insert(touched, member)
		end
	elseif action == "KICK" then
		local before = partyMemberIds(me)
		result = PartyCore.kick(state, me, targetId :: number)
		message = if result.ok then `Removed {nameOf(targetId :: number)}.` else nil
		for _, member in before do
			table.insert(touched, member)
		end
	elseif action == "PROMOTE" then
		result = PartyCore.promote(state, me, targetId :: number)
		message = if result.ok then `{nameOf(targetId :: number)} now leads the party.` else nil
		for _, member in partyMemberIds(me) do
			table.insert(touched, member)
		end
	end

	if not result or not result.ok then
		PartySystem.sync(player, if result then result.err else "Unknown party action.", false)
		return
	end

	PartySystem.sync(player, message, true)
	local others = {}
	for _, userId in touched do
		if userId ~= me then
			table.insert(others, userId)
		end
	end
	syncIds(others)
	-- A party forming or breaking changes the InParty flag everyone else sees.
	if action ~= "INVITE" and action ~= "DECLINE" and action ~= "PROMOTE" then
		syncEveryone(player)
	end
end

--- Who walks through the portal with `player`. ExpeditionSystem asks this
--- and nothing else -- it never reaches into party state.
function PartySystem.groupFor(player: Player): { Role: string, Members: { number } }
	return PartyCore.expeditionGroup(state, player.UserId)
end

--- Called by an expedition server as it sends players home: remember, for a
--- short while, whose party each of them was in. Solo expeditions write
--- nothing. Failure is logged and shrugged off -- the worst case is a party
--- that has to re-invite, which is not worth failing a trip home over.
function PartySystem.recordForReunite(
	leaderUserId: number,
	userIds: { number },
	partySize: number
): ()
	if partySize < 2 then
		return
	end
	local map = reuniteStore()
	if not map then
		return
	end
	local ttl = GameConfig.Party.ReuniteWindowSeconds
	for _, userId in userIds do
		local ok, err = pcall(function()
			(map :: MemoryStoreHashMap):SetAsync(tostring(userId), {
				LeaderUserId = leaderUserId,
				ExpiresAt = os.time() + ttl,
			}, ttl)
		end)
		if not ok then
			warn(`[PartySystem] could not record reunite for {userId}: {err}`)
		end
	end
end

local function runReunite()
	local present = {}
	for _, player in Players:GetPlayers() do
		present[player.UserId] = true
	end
	local changed = PartyCore.reunite(state, pending, present, os.time(), GameConfig)
	if #changed > 0 then
		syncEveryone()
	end
end

local function onPlayerAdded(player: Player)
	-- Were they on their way home in somebody's party?
	local map = reuniteStore()
	if map then
		local ok, entry = pcall(function()
			return (map :: MemoryStoreHashMap):GetAsync(tostring(player.UserId))
		end)
		if
			ok
			and type(entry) == "table"
			and type(entry.LeaderUserId) == "number"
			and type(entry.ExpiresAt) == "number"
		then
			pending[player.UserId] =
				{ LeaderUserId = entry.LeaderUserId, ExpiresAt = entry.ExpiresAt }
			pcall(function()
				(map :: MemoryStoreHashMap):RemoveAsync(tostring(player.UserId))
			end)
		end
	end

	if player.Parent == nil then
		return -- left while MemoryStore answered
	end
	runReunite()
	-- The newcomer needs their own picture, and everyone else has a new name
	-- in their list.
	syncEveryone()
end

function PartySystem.init(): ()
	Net.get("Party_Request").OnServerEvent:Connect(function(player, payload)
		PartySystem.handle(player, payload)
	end)

	Players.PlayerAdded:Connect(function(player)
		task.spawn(onPlayerAdded, player)
	end)
	for _, player in Players:GetPlayers() do
		task.spawn(onPlayerAdded, player)
	end

	Players.PlayerRemoving:Connect(function(player)
		limiter[player.UserId] = nil
		pending[player.UserId] = nil
		PartyCore.removePlayer(state, player.UserId)
		syncEveryone(player)
	end)

	-- Invites lapse on their own; the invitee's list has to notice. Also the
	-- reunite pass, so a member whose leader never arrives stops waiting.
	task.spawn(function()
		while true do
			task.wait(5)
			syncIds(PartyCore.pruneInvites(state, os.clock()))
			if next(pending) then
				runReunite()
			end
		end
	end)
end

return PartySystem
