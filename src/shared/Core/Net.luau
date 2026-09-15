--!strict
-- The ONLY place RemoteEvents are created or looked up. Build spec §4.
-- Creating a remote anywhere else is a spec violation.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Constants = require(script.Parent.Constants)

-- The complete Phase 1 remote list. Adding an entry here requires adding the
-- corresponding row to build spec §4 in the same change.
local PHASE_1_REMOTES = {
	"Fate_RequestRoll", -- C->S, no payload
	"Fate_RollResult", -- S->C, RollPayload
	"Profile_Loaded", -- S->C, full snapshot, once on join
	"Profile_Updated", -- S->C, partial snapshot
	"Progression_FateChanged", -- S->C
	"Announce_Global", -- S->C
	"UI_Acknowledge", -- C->S
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

	for _, name in PHASE_1_REMOTES do
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
		string.format("Unknown remote %q -- add it to Net.PHASE_1_REMOTES and build spec §4", name)
	)
	return remote
end

Net.REMOTES = table.freeze(PHASE_1_REMOTES)

return Net
