--!strict
-- The client half of fixtures (build spec §7.5, CHUNK_AUTHORING.md
-- convention 7): how they MOVE. LootSystem places them on the server and
-- decides everything -- whether a chest is open, who gets what.
--
-- A CHEST is the party's: this file watches the Opened attribute the server
-- sets and animates from the moment it did (OpenedAt, server time), so a
-- player arriving late sees an open chest already open, not opening.
--
-- A VAULT is each player's own (owner, 2026-09-23): it opens only on the
-- screen of the player who used their key. The server says so to that player
-- alone, in their Loot_Result (Fixture = the vault), and this file swings the
-- door and hides the prompt locally. Everyone else still sees it shut.
--
-- Also the forcefield's slow breath, which is purely a look: the field keeps
-- colliding on the server whatever its transparency here.

local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Root = ReplicatedStorage:WaitForChild("Luckbound")
local FixtureCore = require(Root.Core.FixtureCore)
local GameConfig = require(Root.Core.GameConfig)
local PropCore = require(Root.Core.PropCore)

local Net = require(Root.Core.Net)

local FixtureController = {}

-- Vaults this player opened, and when (server time).
local openedHere: { [Instance]: number } = {}

type Tracked = {
	Model: Model,
	Kind: string,
	Phase: number,
}

local tracked: { [Model]: Tracked } = {}
local count = 0

local function partPose(part: BasePart, local_: CFrame): CFrame?
	local base = part:GetAttribute("Base")
	local fix = part:GetAttribute("Fix")
	if typeof(base) ~= "CFrame" or typeof(fix) ~= "CFrame" then
		return nil
	end
	return base * local_ * fix
end

local function animate(t: Tracked, now: number)
	local cfg = GameConfig.Loot.Fixture
	local model = t.Model
	if t.Kind == "FORCEFIELD" then
		local field = model:FindFirstChild("Field")
		if field and field:IsA("BasePart") then
			field.Transparency = FixtureCore.fieldTransparency(now, t.Phase, cfg)
		end
		return
	end
	local openedAt: any = if t.Kind == "VAULT"
		then openedHere[model]
		else model:GetAttribute("OpenedAt")
	if openedAt == nil or (t.Kind ~= "VAULT" and not model:GetAttribute("Opened")) then
		return
	end
	local elapsed = now - (if type(openedAt) == "number" then openedAt else now)
	if t.Kind == "CHEST" then
		local lid = model:FindFirstChild("Lid")
		local hinge = lid and lid:GetAttribute("Hinge")
		if lid and lid:IsA("BasePart") and typeof(hinge) == "Vector3" then
			local swing = CFrame.new(hinge)
				* CFrame.Angles(FixtureCore.lidAngle(elapsed, cfg), 0, 0)
				* CFrame.new(-hinge)
			local cf = partPose(lid, swing)
			if cf then
				lid.CFrame = cf
			end
		end
	elseif t.Kind == "VAULT" then
		local door = model:FindFirstChild("Door")
		if door and door:IsA("BasePart") then
			-- Spin about its own axis, then sink back into the wall (its -Z;
			-- the door's face looks out along +Z).
			local cf = partPose(
				door,
				CFrame.new(0, 0, -FixtureCore.doorRecess(elapsed, cfg))
					* CFrame.Angles(0, 0, FixtureCore.doorSpin(elapsed, cfg))
			)
			if cf then
				door.CFrame = cf
			end
		end
	end
end

local function track(model: Instance)
	if not model:IsA("Model") or tracked[model] then
		return
	end
	local kind = model:GetAttribute("FixtureKind")
	if type(kind) ~= "string" then
		return
	end
	count += 1
	tracked[model] = { Model = model, Kind = kind, Phase = PropCore.phase(count) }
	model.AncestryChanged:Connect(function(_, parent)
		if parent == nil then
			tracked[model] = nil
			openedHere[model] = nil
		end
	end)
end

function FixtureController.init(): ()
	-- Fixtures replicate as part of an expedition's map. Descendant watching
	-- is cheap here: maps arrive rarely, and only Models with the attribute
	-- are kept.
	for _, d in Workspace:GetDescendants() do
		track(d)
	end
	Workspace.DescendantAdded:Connect(function(d)
		if d:IsA("Model") then
			-- Attributes arrive with the instance, but give replication a beat.
			task.defer(track, d)
		end
	end)
	Net.get("Loot_Result").OnClientEvent:Connect(function(payload)
		local vault = payload.Fixture
		if payload.Source == "VAULT" and payload.KeySpent and typeof(vault) == "Instance" then
			openedHere[vault] = Workspace:GetServerTimeNow()
			-- The prompt is the server's and everyone's; hiding it here hides
			-- it for this player only.
			for _, d in vault:GetDescendants() do
				if d:IsA("ProximityPrompt") then
					d.Enabled = false
				end
			end
		end
	end)
	RunService.RenderStepped:Connect(function()
		if next(tracked) == nil then
			return
		end
		local now = Workspace:GetServerTimeNow()
		for _, t in tracked do
			animate(t, now)
		end
	end)
end

return FixtureController
