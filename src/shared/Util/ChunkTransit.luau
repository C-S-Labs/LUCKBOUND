--!strict
-- Server-authoritative walk-through transit inside one expedition (§7.7).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Root = ReplicatedStorage:WaitForChild("Luckbound")
local GameConfig = require(Root.Core.GameConfig)
local Chunks = require(Root.Content.Chunks)
local ChunkRuntimeCore = require(Root.Core.ChunkRuntimeCore)
local ChunkCore = require(Root.Util.ChunkCore)
local ChunkTransit = {}

function ChunkTransit.attach(stage: Instance, members: { [number]: boolean })
	assert(RunService:IsServer(), "ChunkTransit is server-only")
	local cfg = GameConfig.ChunkRuntime
	local cooldown: { [number]: number } = {}
	for _, object in stage:GetDescendants() do
		if object:IsA("BasePart") and object.Name == "RoomPortalTrigger" then
			object.Touched:Connect(function(hit)
				local character = hit:FindFirstAncestorOfClass("Model")
				local player = character and Players:GetPlayerFromCharacter(character)
				local humanoid = character and character:FindFirstChildOfClass("Humanoid")
				local root = character and character:FindFirstChild("HumanoidRootPart")
				if
					not player
					or not members[player.UserId]
					or not humanoid
					or humanoid.Health <= 0
					or not root
					or not root:IsA("BasePart")
					or not stage.Parent
				then
					return
				end
				local now = os.clock()
				if cooldown[player.UserId] and now < cooldown[player.UserId] then
					return
				end
				local localPosition = object.CFrame:PointToObjectSpace(root.Position)
				local half = object.Size / 2
				local slack = cfg.TriggerSlackStuds
				if
					math.abs(localPosition.X) > half.X + slack
					or math.abs(localPosition.Y) > half.Y + slack
					or math.abs(localPosition.Z) > half.Z + slack
				then
					return
				end
				local arrival = object:GetAttribute("Arrival")
				if typeof(arrival) ~= "CFrame" then
					return
				end
				cooldown[player.UserId] = math.huge
				local streamed, streamError = pcall(function()
					player:RequestStreamAroundAsync(arrival.Position, cfg.StreamTimeoutSeconds)
				end)
				cooldown[player.UserId] = os.clock() + cfg.PortalCooldownSeconds
				if not streamed then
					warn("[ChunkTransit] destination streaming failed: " .. tostring(streamError))
					return
				end
				if
					player.Character ~= character
					or not members[player.UserId]
					or not stage.Parent
					or humanoid.Health <= 0
				then
					return
				end
				localPosition = object.CFrame:PointToObjectSpace(root.Position)
				if
					math.abs(localPosition.X) > half.X + slack
					or math.abs(localPosition.Y) > half.Y + slack
					or math.abs(localPosition.Z) > half.Z + slack
				then
					return
				end
				root.AssemblyLinearVelocity = Vector3.zero
				root.AssemblyAngularVelocity = Vector3.zero
				character:PivotTo(arrival)
			end)
		end
	end
	local library = ReplicatedStorage:FindFirstChild("LuckboundProps")
	for _, folder in stage:GetChildren() do
		local id = folder:GetAttribute("ChunkId")
		local definition = id and ChunkRuntimeCore.lookup(Chunks, id)
		local gate = definition and definition.Gate
		if gate and library then
			local source = library:FindFirstChild(gate.Mesh, true)
			if source and source:IsA("BasePart") then
				local part = source:Clone()
				part.Name = "EncounterGate"
				part.Anchored = true
				part.CanCollide = true
				part.Size = Vector3.new(table.unpack(gate.S))
				local frame = CFrame.new(folder:GetAttribute("Centre"))
					* CFrame.Angles(0, ChunkCore.yawRadians(folder:GetAttribute("Yaw")), 0)
				local rest = frame
					* CFrame.new(table.unpack(gate.P))
					* CFrame.Angles(0, ChunkCore.yawRadians(definition.MeshYawOffset or 0), 0)
				part.CFrame = rest
				part.Parent = folder
				local opened = false
				local function open()
					if opened or stage:GetAttribute(gate.RequiredStageState) ~= true then
						return
					end
					opened = true
					TweenService:Create(
						part,
						TweenInfo.new(cfg.GateOpenSeconds),
						{ CFrame = rest + Vector3.new(0, gate.TravelY, 0) }
					):Play()
				end
				stage:GetAttributeChangedSignal(gate.RequiredStageState):Connect(open)
				open()
			else
				warn("[ChunkTransit] missing encounter gate mesh " .. gate.Mesh)
			end
		end
	end
end

return ChunkTransit
