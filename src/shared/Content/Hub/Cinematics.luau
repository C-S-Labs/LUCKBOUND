--!strict
-- THE LOADING SCREEN'S CAMERA TOUR, AS DATA.
--
-- Each shot is a slow arc: the camera sits `Radius` studs from `Subject` at
-- `Height`, looks at `Subject + LookOffset`, and sweeps
-- GameConfig.Loading.ShotArcDegrees over GameConfig.Loading.ShotSeconds. That
-- is the entire vocabulary, and it is deliberately one shape -- a tour made of
-- one slow move reads as a single held breath, while a tour of pans, dollies
-- and cuts reads as a showreel and fights the title on top of it.
--
-- WHAT IS AND IS NOT IN HERE. Every shot below frames hub geometry, because
-- the hub is the only thing standing in the place while a player loads. A
-- biome is built 20000 studs up and only while someone is inside it
-- (GameConfig.Expedition.StageOrigin), so a shot of Ethereal Scape would be a
-- shot of empty sky. `WorldId` is declared on the schema now so that the shot
-- list can grow into the biomes the moment expeditions move to their own
-- place (STATUS §4) -- the client skips any shot whose world is not loaded,
-- so a shot added early degrades to being absent rather than to a black
-- screen.

local GameConfig = require(script.Parent.Parent.Parent.Core.GameConfig)

local Anchors = GameConfig.HubLayout.Anchors

local Cinematics = {
	-- Order is the order they play. The first shot is the one a player sees
	-- on a warm client that loads in three seconds, so it is the hero shot:
	-- the Fate Engine, the thing the game is about.
	Shots = {
		{
			Id = "ENGINE_ORBIT",
			Caption = "The Crossroads",
			Subject = Anchors.FATE_ENGINE,
			-- Outside the dais and above head height, looking slightly down.
			-- Close enough that the rings read, far enough that the four
			-- walkways are in frame leading away.
			Radius = 190,
			Height = 96,
			LookOffset = Vector3.new(0, 26, 0),
			WorldId = nil,
		},
		{
			Id = "HALL_APPROACH",
			Caption = "Hall of Legends",
			Subject = Anchors.HALL_OF_LEGENDS,
			Radius = 240,
			Height = 120,
			LookOffset = Vector3.new(0, 34, 0),
			WorldId = nil,
		},
		{
			Id = "ARCHIVE_ROTUNDA",
			Caption = "Discovery Archive",
			Subject = Anchors.DISCOVERY_ARCHIVE,
			Radius = 215,
			Height = 108,
			LookOffset = Vector3.new(0, 40, 0),
			WorldId = nil,
		},
		{
			Id = "MARKET_STALLS",
			Caption = "The Market",
			Subject = Anchors.EXPEDITION_GATE,
			Radius = 230,
			Height = 90,
			LookOffset = Vector3.new(0, 24, 0),
			WorldId = nil,
		},
		{
			Id = "TRAINING_YARD",
			Caption = "Training Grounds",
			Subject = Anchors.TRAINING_GROUNDS,
			Radius = 205,
			Height = 86,
			LookOffset = Vector3.new(0, 20, 0),
			WorldId = nil,
		},
		{
			Id = "HORIZON",
			Caption = "…and everywhere the roll can send you",
			-- High and far, framing the floating islands and the mountain
			-- ring rather than any one building. The last shot before the
			-- player presses Play should be the one that says the world is
			-- bigger than the plaza.
			Subject = Anchors.FATE_ENGINE,
			Radius = 1400,
			Height = 620,
			LookOffset = Vector3.new(0, -120, 0),
			WorldId = nil,
		},
	},
}

return Cinematics
