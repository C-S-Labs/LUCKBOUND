--!strict
-- THE HUB MENU, AS DATA. Build spec §2.2 -- Systems are reusable, content is
-- data. `HubMenuCore` decides what a menu does; this file decides what is in
-- one, and the client draws whatever it finds here.
--
-- Adding a panel is one row in `Panels`. Adding a destination is one row in
-- `Destinations`. Neither requires touching the rail, the panel builder, the
-- teleport system or the server -- and if one ever seems to, the schema is
-- wrong and wants amending rather than special-casing (CLAUDE.md, the prime
-- directive).
--
-- STATUS is the honest field. "LIVE" means the panel does something today;
-- "PREVIEW" means it draws its real design over placeholder data and says so
-- on screen. The owner's direction is that the stat tree, shop, parties and
-- rebirth are designed now and implemented after testing, so they ship as
-- PREVIEW rather than as buttons that lie.

local GameConfig = require(script.Parent.Parent.Parent.Core.GameConfig)

local Anchors = GameConfig.HubLayout.Anchors

local Menu = {
	-- The key that hides and shows the whole rail, by Enum.KeyCode NAME. A
	-- name rather than the enum itself so this file stays a data file -- the
	-- client resolves it, and an unknown name degrades to "no shortcut"
	-- rather than to an error at require time.
	CollapseHotkey = "Backslash",

	-- === THE SIDE RAIL ================================================
	-- Order is the vertical order on the rail, top to bottom, and it is a
	-- design statement: Travel first because it is the thing a player in a
	-- 1150-stud hub reaches for most, Rebirth last because it is the thing
	-- they reach for once.
	--
	-- Glyphs are text, not images. A rail built from asset ids cannot be read
	-- in a diff, cannot be changed without an upload, and renders as a grey
	-- box the moment an id is wrong. These are placeholders in the same sense
	-- the blockout chunks are: correct shape, art later.
	Panels = {
		{
			Id = "TRAVEL",
			Label = "Travel",
			Glyph = "◈",
			Order = 1,
			Status = "LIVE",
			Summary = "Cross the Crossroads without walking it.",
			-- Keyboard shortcut. Touch devices get the rail button only.
			Hotkey = "T",
		},
		{
			Id = "SHOP",
			Label = "Shop",
			Glyph = "❖",
			Order = 2,
			Status = "PREVIEW",
			Summary = "Spend Fate on what the market has today.",
			Hotkey = "B",
		},
		{
			Id = "CODES",
			Label = "Codes",
			Glyph = "⌘",
			Order = 3,
			Status = "LIVE",
			Summary = "Redeem a code.",
			Hotkey = "C",
		},
		{
			Id = "SKILLS",
			Label = "Fate Tree",
			Glyph = "✦",
			Order = 4,
			Status = "PREVIEW",
			Summary = "Spend Fate levels on lasting upgrades.",
			Hotkey = "K",
		},
		{
			Id = "PARTY",
			Label = "Party",
			Glyph = "◎",
			Order = 5,
			Status = "PREVIEW",
			Summary = "Roll and expedition together.",
			Hotkey = "P",
		},
		{
			Id = "REBIRTH",
			Label = "Rebirth",
			Glyph = "⟲",
			Order = 6,
			Status = "PREVIEW",
			Summary = "Trade everything for a permanent edge.",
			Hotkey = "R",
		},
		{
			Id = "SETTINGS",
			Label = "Settings",
			Glyph = "⚙",
			Order = 7,
			Status = "LIVE",
			Summary = "Sound, motion and display.",
			Hotkey = "O",
		},
	},

	-- === THE TRAVEL NETWORK ===========================================
	-- Five destinations: the Fate Engine at the centre and the four compass
	-- districts around it. Positions are NOT repeated here -- they are read
	-- from GameConfig.HubLayout.Anchors, which build spec §7.3 makes the one
	-- place the hub's geometry is stated. `Landing` is an offset from that
	-- anchor, and the server drops a ray onto the deck from above it
	-- (GameConfig.HubMenu.TeleportProbeHeight) rather than trusting the Y.
	--
	-- `Facing` is the compass bearing the player is turned to on arrival, in
	-- degrees clockwise from north. Every district faces the Engine, because
	-- arriving with your back to the only interactive thing in the game is
	-- the kind of small wrongness nobody can name but everybody feels.
	Destinations = {
		{
			Id = "FATE_ENGINE",
			Label = "The Fate Engine",
			Subtitle = "Roll your next world",
			AnchorId = "FATE_ENGINE",
			Anchor = Anchors.FATE_ENGINE,
			-- Off the dais rim rather than on it: the same reasoning as the
			-- spawn ring (GameConfig.HubLayout.SpawnRing) -- you arrive facing
			-- the Engine with it already filling the frame, not standing
			-- inside its geometry.
			Landing = Vector3.new(0, 8, 58),
			Facing = 0,
			Order = 1,
		},
		{
			Id = "HALL_OF_LEGENDS",
			Label = "Hall of Legends",
			Subtitle = "The server's rarest rolls",
			AnchorId = "HALL_OF_LEGENDS",
			Anchor = Anchors.HALL_OF_LEGENDS,
			Landing = Vector3.new(0, 22, 80),
			Facing = 180,
			Order = 2,
		},
		{
			Id = "DISCOVERY_ARCHIVE",
			Label = "Discovery Archive",
			Subtitle = "What you have found",
			AnchorId = "DISCOVERY_ARCHIVE",
			Anchor = Anchors.DISCOVERY_ARCHIVE,
			Landing = Vector3.new(-72, 22, 0),
			Facing = 270,
			Order = 3,
		},
		{
			Id = "EXPEDITION_GATE",
			Label = "The Market",
			-- The district is still called EXPEDITION_GATE in Content while
			-- the authored art makes it a shop (STATUS §4). The Id is the
			-- contract with the geometry and must not drift; the LABEL is what
			-- the player reads, and it tells the truth about what is there.
			Subtitle = "Stalls, traders and the shop",
			AnchorId = "EXPEDITION_GATE",
			Anchor = Anchors.EXPEDITION_GATE,
			Landing = Vector3.new(0, 14, -88),
			Facing = 0,
			Order = 4,
		},
		{
			Id = "TRAINING_GROUNDS",
			Label = "Training Grounds",
			Subtitle = "Try a weapon out",
			AnchorId = "TRAINING_GROUNDS",
			Anchor = Anchors.TRAINING_GROUNDS,
			Landing = Vector3.new(72, 22, 0),
			Facing = 90,
			Order = 5,
		},
	},
}

return Menu
