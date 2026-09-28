--!strict
-- THE DEVELOPER COMMAND REGISTRY. Testing tooling, not a feature.
--
-- One list, read by everything that runs a command:
--   * chat       -- Controllers/DebugCommands registers every entry as a
--                   TextChatCommand, so Roblox's chat autocompletes /names
--   * dev panel  -- UI/DevPanel draws a card per entry: clickable pickers for
--                   every argument, one-click presets, and a command bar that
--                   autocompletes names AND argument values (Core/DevCore)
--   * server     -- Systems/DebugSystem checks at boot that every SERVER entry
--                   has a handler and every handler has an entry
--
-- ADDING A COMMAND is one entry here plus its handler:
--   Side = "CLIENT"  -> a function in DebugCommands.CLIENT (things the client
--                       already owns: its camera, its character's movement,
--                       what it draws)
--   Side = "SERVER"  -> a function in DebugSystem's COMMANDS (anything a client
--                       must not be trusted with: rolls, entry, loot, health)
-- The tests (tests/cases.luau, "dev registry") fail on a malformed entry, an
-- unknown category or source, or a duplicate name.
--
-- ARGUMENTS. Each is { Name, Type, Optional?, ... }:
--   Type = "choice"  pick one of Options (a literal list) or Source (a named
--                    list the client resolves live -- see DevCore.SOURCES)
--   Type = "number"  typed; Min/Max are advisory, Suggest lists quick values
--   Type = "text"    free text
-- Presets are whole argument lists run in one click ({ Label, Args }).

export type Arg = {
	Name: string,
	Type: string,
	Optional: boolean?,
	Options: { string }?,
	Source: string?,
	Min: number?,
	Max: number?,
	Suggest: { string }?,
}

export type Command = {
	Name: string,
	Category: string,
	Side: string,
	Summary: string,
	Args: { Arg }?,
	Presets: { { Label: string, Args: { string } } }?,
	Danger: boolean?, -- drawn with the DANGER button style
}

-- Tab order in the panel. Id is what a command's Category names.
local CATEGORIES = {
	{ Id = "WORLD", Label = "World & Map" },
	{ Id = "CHUNKS", Label = "Chunks" },
	{ Id = "PLAYER", Label = "Player" },
	{ Id = "LOOT", Label = "Fate & Loot" },
	{ Id = "EVENTS", Label = "Events" },
	{ Id = "AMBIENCE", Label = "Ambience" },
	{ Id = "BOSSES", Label = "Bosses" },
	{ Id = "DIAG", Label = "Diagnostics" },
	{ Id = "GENERAL", Label = "General" },
}

local CHANCE = { "0", "0.1", "0.25", "0.5", "1", "reset" }

local COMMANDS: { Command } = {
	-- === WORLD & MAP ===================================================
	{
		Name = "roll",
		Category = "WORLD",
		Side = "SERVER",
		Summary = "Force your next destination. 'test' lays out every chunk of the kit once.",
		Args = {
			{ Name = "world", Type = "choice", Source = "WORLDS" },
			{ Name = "mode", Type = "choice", Options = { "test" }, Optional = true },
		},
	},
	{
		Name = "enter",
		Category = "WORLD",
		Side = "SERVER",
		Summary = "Enter your destination from anywhere. A seed replays that exact map.",
		Args = { { Name = "seed", Type = "number", Optional = true } },
		Presets = { { Label = "New map", Args = {} } },
	},
	{
		Name = "leave",
		Category = "WORLD",
		Side = "SERVER",
		Summary = "End the expedition and return to the Crossroads (counts as RETURNED).",
	},
	{
		Name = "seed",
		Category = "WORLD",
		Side = "CLIENT",
		Summary = "The world and seed of the map you are on (/enter <seed> replays it).",
	},
	{
		Name = "worlds",
		Category = "WORLD",
		Side = "CLIENT",
		Summary = "List the rollable world ids.",
	},

	-- === CHUNKS ========================================================
	{
		Name = "chunks",
		Category = "CHUNKS",
		Side = "CLIENT",
		Summary = "Overlay every chunk's bounds and a label (index, id, role, mesh or BLOCKOUT).",
		Args = { { Name = "state", Type = "choice", Options = { "on", "off" }, Optional = true } },
		Presets = { { Label = "On", Args = { "on" } }, { Label = "Off", Args = { "off" } } },
	},
	{
		Name = "chunklist",
		Category = "CHUNKS",
		Side = "CLIENT",
		Summary = "Print the map's chunks in placement order.",
	},
	{
		Name = "chunktp",
		Category = "CHUNKS",
		Side = "CLIENT",
		Summary = "Teleport to a chunk of the current map (by index or id).",
		Args = { { Name = "chunk", Type = "choice", Source = "CHUNKS" } },
	},

	-- === PLAYER ========================================================
	{
		Name = "fly",
		Category = "PLAYER",
		Side = "CLIENT",
		Summary = "Toggle flight: WASD, Space up, Shift down.",
	},
	{
		Name = "noclip",
		Category = "PLAYER",
		Side = "CLIENT",
		Summary = "Toggle walking through geometry (pairs well with /fly).",
	},
	{
		Name = "moveprofile",
		Category = "PLAYER",
		Side = "CLIENT",
		Summary = "Force the hub or expedition movement feel (auto = normal).",
		Args = {
			{
				Name = "profile",
				Type = "choice",
				Options = { "hub", "expedition", "auto" },
				Optional = true,
			},
		},
	},
	{
		Name = "stamina",
		Category = "PLAYER",
		Side = "CLIENT",
		Summary = "Set stamina to a percent (no value prints it).",
		Args = {
			{
				Name = "percent",
				Type = "number",
				Optional = true,
				Min = 0,
				Max = 100,
				Suggest = { "0", "10", "50", "100" },
			},
		},
		Presets = {
			{ Label = "Empty", Args = { "0" } },
			{ Label = "Sliver", Args = { "5" } },
			{ Label = "Full", Args = { "100" } },
		},
	},
	{
		Name = "animslot",
		Category = "PLAYER",
		Side = "CLIENT",
		Summary = 'Try an animation id in a player slot live (no args lists slots; id "" clears).',
		Args = {
			{
				Name = "slot",
				Type = "choice",
				Optional = true,
				Options = {
					"Idle",
					"WalkForward",
					"WalkBackward",
					"WalkLeft",
					"WalkRight",
					"RunForward",
					"RunBackward",
					"RunLeft",
					"RunRight",
					"Sprint",
					"JumpStart",
					"Rise",
					"Fall",
					"LandSoft",
					"LandHard",
					"RollForward",
					"RollBackward",
					"RollLeft",
					"RollRight",
					"Backstep",
					"TurnLeft",
					"TurnRight",
				},
			},
			{ Name = "id", Type = "text", Optional = true },
		},
	},
	{
		Name = "speed",
		Category = "PLAYER",
		Side = "CLIENT",
		Summary = "Set walk speed (no value prints it).",
		Args = {
			{
				Name = "studs/s",
				Type = "number",
				Optional = true,
				Min = 4,
				Max = 300,
				Suggest = { "16", "32", "64", "120" },
			},
		},
		Presets = {
			{ Label = "Default", Args = { "16" } },
			{ Label = "x2", Args = { "32" } },
			{ Label = "x4", Args = { "64" } },
			{ Label = "Sprint", Args = { "120" } },
		},
	},
	{
		Name = "tp",
		Category = "PLAYER",
		Side = "CLIENT",
		Summary = "Jump to a hub anchor.",
		Args = { { Name = "place", Type = "choice", Source = "DESTINATIONS" } },
	},
	{
		Name = "where",
		Category = "PLAYER",
		Side = "CLIENT",
		Summary = "Print your position.",
	},
	{
		Name = "god",
		Category = "PLAYER",
		Side = "SERVER",
		Summary = "Toggle invulnerability.",
	},
	{
		Name = "heal",
		Category = "PLAYER",
		Side = "SERVER",
		Summary = "Restore full health.",
	},
	{
		Name = "respawn",
		Category = "PLAYER",
		Side = "SERVER",
		Summary = "Respawn your character where the game would put you.",
		Danger = true,
	},

	-- === FATE & LOOT ===================================================
	{
		Name = "boss",
		Category = "LOOT",
		Side = "SERVER",
		Summary = "Act as if you just defeated this map's boss (repeatable).",
	},
	{
		Name = "givekey",
		Category = "LOOT",
		Side = "SERVER",
		Summary = "Give yourself a vault key.",
		Args = { { Name = "key", Type = "choice", Source = "KEYS", Optional = true } },
	},
	{
		Name = "takekey",
		Category = "LOOT",
		Side = "SERVER",
		Summary = "Remove every key you hold.",
		Danger = true,
	},
	{
		Name = "keys",
		Category = "LOOT",
		Side = "SERVER",
		Summary = "Your keys and any testing overrides in force.",
	},
	{
		Name = "keychance",
		Category = "LOOT",
		Side = "SERVER",
		Summary = "Vault key drop chance for this session (0-1, or reset).",
		Args = { { Name = "chance", Type = "choice", Options = CHANCE } },
	},
	{
		Name = "vaultchance",
		Category = "LOOT",
		Side = "SERVER",
		Summary = "How often the treasury spawns, next map on (0-1, or reset).",
		Args = { { Name = "chance", Type = "choice", Options = CHANCE } },
	},
	{
		Name = "ledger",
		Category = "LOOT",
		Side = "SERVER",
		Summary = "How many of a unique have been claimed, and by whom.",
		Args = { { Name = "unique", Type = "choice", Source = "LEDGERS" } },
	},

	-- === EVENTS ========================================================
	{
		Name = "event",
		Category = "EVENTS",
		Side = "SERVER",
		Summary = "Start a live event. Uniques still claim from the ledger.",
		Args = { { Name = "event", Type = "choice", Source = "EVENTS" } },
	},
	{
		Name = "endevents",
		Category = "EVENTS",
		Side = "SERVER",
		Summary = "Stop every live event on this server.",
		Danger = true,
	},

	-- === AMBIENCE ======================================================
	{
		Name = "atmosphere",
		Category = "AMBIENCE",
		Side = "SERVER",
		Summary = "Force a scenario atmosphere now and on the next map. RANDOM goes back to the seed.",
		Args = { { Name = "atmosphere", Type = "choice", Source = "ATMOSPHERES" } },
	},
	{
		Name = "tint",
		Category = "AMBIENCE",
		Side = "CLIENT",
		Summary = "Tint the map's meshes by the atmosphere.",
		Args = { { Name = "state", Type = "choice", Options = { "on", "off" } } },
	},
	{
		Name = "props",
		Category = "AMBIENCE",
		Side = "CLIENT",
		Summary = "Show or hide the ambient props (clouds, skyrays, lanterns...).",
		Args = { { Name = "state", Type = "choice", Options = { "on", "off" } } },
	},
	{
		Name = "clock",
		Category = "AMBIENCE",
		Side = "CLIENT",
		Summary = "Set the local time of day, 0-24 (a sky system may take it back).",
		Args = {
			{
				Name = "hour",
				Type = "number",
				Min = 0,
				Max = 24,
				Suggest = { "0", "6", "12", "18" },
			},
		},
		Presets = {
			{ Label = "Dawn", Args = { "6" } },
			{ Label = "Noon", Args = { "12" } },
			{ Label = "Dusk", Args = { "18" } },
			{ Label = "Night", Args = { "0" } },
		},
	},

	-- === BOSSES ========================================================
	{
		Name = "showboss",
		Category = "BOSSES",
		Side = "SERVER",
		Summary = "Preview a boss in the nearest boss arena, idling (no AI).",
		Args = {
			{ Name = "boss", Type = "choice", Source = "BOSSES" },
			{ Name = "height", Type = "number", Optional = true, Suggest = { "30", "60", "90" } },
		},
	},
	{
		Name = "bossphase",
		Category = "BOSSES",
		Side = "SERVER",
		Summary = "Switch the preview between phase 1 and 2.",
		Args = { { Name = "phase", Type = "choice", Options = { "1", "2" } } },
	},
	{
		Name = "clearboss",
		Category = "BOSSES",
		Side = "SERVER",
		Summary = "Remove the boss preview.",
	},
	{
		Name = "dummies",
		Category = "BOSSES",
		Side = "SERVER",
		Summary = "Spawn lock-on dummies in front of you (0 clears them).",
		Args = { { Name = "count", Type = "number", Optional = true, Suggest = { "0", "3", "6" } } },
	},

	-- === DIAGNOSTICS ===================================================
	{
		Name = "stats",
		Category = "DIAG",
		Side = "CLIENT",
		Summary = "Overlay FPS, ping, memory and instance counts.",
		Args = { { Name = "state", Type = "choice", Options = { "on", "off" }, Optional = true } },
	},
	{
		Name = "assets",
		Category = "DIAG",
		Side = "CLIENT",
		Summary = "Which chunks of this map drew as BLOCKOUT (no uploaded mesh id).",
	},

	-- === GENERAL =======================================================
	{
		Name = "panel",
		Category = "GENERAL",
		Side = "CLIENT",
		Summary = "Open or close this panel (also F4, or the DEV button).",
	},
	{
		Name = "help",
		Category = "GENERAL",
		Side = "CLIENT",
		Summary = "List every command.",
	},
	{
		Name = "clear",
		Category = "GENERAL",
		Side = "CLIENT",
		Summary = "Clear the panel's output log.",
	},
}

return {
	Categories = CATEGORIES,
	Commands = COMMANDS,
}
