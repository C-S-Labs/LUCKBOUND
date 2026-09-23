--!strict
-- Client side of an expedition: lighting, the local countdown, and the Gate's
-- per-player label.
--
-- WHY LIGHTING LIVES HERE. Lighting is a shared service, so a server that
-- applied a biome's Environment would paint it on every player's screen --
-- including people still standing in the hub. Applying it on the entering
-- client instead is what makes Biome Blueprint §6's "lighting applied and
-- reverted by the expedition, never bleeding" actually true with more than one
-- player on the server. The hub's own lighting is snapshotted at join and
-- restored verbatim on exit.

local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local ChunkLoader = require(Root.Util.ChunkLoader)
local Constants = require(Root.Core.Constants)
local EventCore = require(Root.Core.EventCore)
local Net = require(Root.Core.Net)
local Worlds = require(Root.Content.Worlds)
local AmbienceController = require(script.Parent.AmbienceController)

local ExpeditionController = {}

-- Every Lighting property ChunkLoader.applyEnvironment writes. Restoring means
-- writing exactly this set back -- anything missing here would leak a biome's
-- look into the hub, which is the bug this whole arrangement exists to avoid.
-- Derived from EventCore rather than typed out, because a live event writes
-- the same properties and both lists have to be the same list. They were two
-- copies for about an hour, which is exactly long enough for them to diverge.
local TRACKED = EventCore.trackedLighting()

local hubLighting: { [string]: any } = {}
local active: any = nil
local startedAtClock = 0
local listeners: { (any) -> () } = {}

local function snapshotHubLighting()
	for _, property in TRACKED do
		hubLighting[property] = (Lighting :: any)[property]
	end
end

local function restoreHubLighting()
	for _, property in TRACKED do
		if hubLighting[property] ~= nil then
			(Lighting :: any)[property] = hubLighting[property]
		end
	end
end

local function notify()
	for _, fn in listeners do
		task.spawn(fn, active)
	end
end

--- Subscribe to expedition state. `nil` means "in the hub". Fires immediately
--- with the current state so a UI built later is never out of date.
function ExpeditionController.onChanged(fn: (any) -> ()): () -> ()
	table.insert(listeners, fn)
	task.spawn(fn, active)
	return function()
		local index = table.find(listeners, fn)
		if index then
			table.remove(listeners, index)
		end
	end
end

function ExpeditionController.get(): any
	return active
end

--- Seconds left, counted locally between server syncs so the number ticks
--- every frame instead of jumping every TimerSyncSeconds.
function ExpeditionController.remaining(): number
	if not active then
		return 0
	end
	return math.max(0, active.RemainingSeconds - (os.clock() - startedAtClock))
end

--- The Gate prompt tells THIS player where THIS player is going. Prompt
--- properties changed on a client are local-only, so one shared prompt can
--- carry a different destination for everyone standing at it.
local function labelGateFor(worldId: string?)
	local hub = Workspace:FindFirstChild(Constants.NAMES.CROSSROADS)
	local zones = hub and hub:FindFirstChild("Zones")
	local gate = zones and zones:FindFirstChild("EXPEDITION_GATE")
	local anchor = gate and gate:FindFirstChild(Constants.NAMES.GATE_ANCHOR)
	local prompt = anchor and anchor:FindFirstChild("EnterPrompt")
	if not prompt or not prompt:IsA("ProximityPrompt") then
		return
	end

	local world = worldId and Worlds[worldId]
	prompt.ObjectText = if world then world.Name else "Roll at the Fate Engine"
	prompt.ActionText = if world then "ENTER" else "NO DESTINATION"
end

function ExpeditionController.init(): ()
	-- Snapshot after the hub's own lighting has been applied by HubBuilder,
	-- not before: capturing Studio's defaults would restore the wrong world.
	task.spawn(function()
		if Workspace:WaitForChild(Constants.NAMES.CROSSROADS, 30) then
			task.wait(1)
		end
		snapshotHubLighting()
		labelGateFor(nil)
	end)

	Net.get("Fate_RollResult").OnClientEvent:Connect(function(payload)
		labelGateFor(payload.WorldId)
	end)

	Net.get("Expedition_Started").OnClientEvent:Connect(function(payload)
		if not next(hubLighting) then
			snapshotHubLighting()
		end
		ChunkLoader.applyEnvironment(Lighting, payload.Environment)
		-- Sky, atmosphere, grade, cloud sea, motes: the rest of the world's look.
		AmbienceController.enter(payload.Environment, payload.FloorY or 0)
		active = payload
		startedAtClock = os.clock()
		notify()
		print(
			string.format(
				"[Expedition] entered %s -- seed %d, %s, %ds",
				payload.Name,
				payload.Seed,
				payload.MapSummary,
				payload.DurationSeconds
			)
		)
	end)

	Net.get("Expedition_TimerSync").OnClientEvent:Connect(function(payload)
		if active then
			active.RemainingSeconds = payload.RemainingSeconds
			startedAtClock = os.clock()
		end
	end)

	Net.get("Expedition_Ended").OnClientEvent:Connect(function(payload)
		-- An ABORTED payload is a refusal at the door, not the end of an
		-- expedition: there is no lighting to restore and no state to clear.
		if payload.Reason ~= "ABORTED" then
			AmbienceController.leave()
			restoreHubLighting()
			active = nil
			notify()
		end
		ExpeditionController.onEnded(payload)
	end)

	-- Belt and braces: if a client somehow holds expedition state while its
	-- character is back in the hub, the countdown reaching zero clears it
	-- rather than leaving a stuck banner on screen.
	RunService.Heartbeat:Connect(function()
		if active and ExpeditionController.remaining() <= 0 then
			active = nil
			AmbienceController.leave()
			restoreHubLighting()
			notify()
		end
	end)
end

--- Overridden by the HUD so refusal messages and the end-of-run summary have
--- somewhere to go. A no-op by default, so the controller works headless.
function ExpeditionController.onEnded(_payload: any): () end

return ExpeditionController
