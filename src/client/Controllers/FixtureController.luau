--!strict
-- The client half of fixtures (build spec §7.5, CHUNK_AUTHORING.md
-- convention 7): how they MOVE. LootSystem places them on the server and
-- decides everything -- whether a chest is open, who gets what. This file only
-- watches the Opened attribute the server sets and animates from the moment
-- it did (OpenedAt, server time), so a player arriving late sees an open chest
-- already open, not opening.
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

local FixtureController = {}

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
	if not model:GetAttribute("Opened") then
		return
	end
	local openedAt = model:GetAttribute("OpenedAt")
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
