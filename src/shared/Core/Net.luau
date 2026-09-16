--!strict
-- The ONLY place RemoteEvents are created or looked up. Build spec §4.
-- Creating a remote anywhere else is a spec violation.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Constants = require(script.Parent.Constants)

-- The complete live remote list. Adding an entry here requires adding the
-- corresponding row to build spec §4 in the same change.
--
-- The four Expedition_* remotes were RESERVED by build spec §4 from the
-- beginning -- declared but unbuilt, precisely so that whoever implemented
-- expedition entry would promote them rather than invent CombatHit2-style
-- names. They are promoted here, with §4's table updated in the same change.
local REMOTES = {
	"Fate_RequestRoll", -- C->S, no payload
	"Fate_RollResult", -- S->C, RollPayload
	"Profile_Loaded", -- S->C, full snapshot, once on join
	"Profile_Updated", -- S->C, partial snapshot
	"Progression_FateChanged", -- S->C
	"Announce_Global", -- S->C
	"Event_StateSync", -- S->C, full live-event snapshot; fires on join (§4.1)
	"UI_Acknowledge", -- C->S
	"Expedition_RequestEnter", -- C->S, no payload; cooldown + distance guarded
	"Expedition_Started", -- S->C, ExpeditionPayload
	"Expedition_Ended", -- S->C, ExpeditionEndPayload
	"Expedition_TimerSync", -- S->C, { RemainingSeconds, ServerNow }
}

local Net = {}

local folder: Folder? = nil

local function root(): Folder
	local r = ReplicatedStorage:FindFirstChild(Constants.NAMES.ROOT)
	assert(r and r:IsA("Folder"), "Luckbound root folder missing from ReplicatedStorage")
	return r
end

--- Server-only. Creates every Phase 1 remote. Called once, from bootstrap.
function Net.buildRemotes(): Folder
	assert(RunService:IsServer(), "Net.buildRemotes may only be called on the server")

	local existing = root():FindFirstChild(Constants.NAMES.NET_FOLDER)
	if existing then
		existing:Destroy()
	end

	local f = Instance.new("Folder")
	f.Name = Constants.NAMES.NET_FOLDER

	for _, name in REMOTES do
		local remote = Instance.new("RemoteEvent")
		remote.Name = name
		remote.Parent = f
	end

	f.Parent = root()
	folder = f
	return f
end

--- Returns a remote by name. Yields on the client until the folder replicates.
function Net.get(name: string): RemoteEvent
	if not folder then
		local f = root():WaitForChild(Constants.NAMES.NET_FOLDER, 30)
		assert(f and f:IsA("Folder"), "Net folder never replicated")
		folder = f
	end

	local remote = (folder :: Folder):WaitForChild(name, 10)
	assert(
		remote and remote:IsA("RemoteEvent"),
		string.format("Unknown remote %q -- add it to Net.REMOTES and build spec §4", name)
	)
	return remote
end

Net.REMOTES = table.freeze(REMOTES)

return Net
