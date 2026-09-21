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

-- EVERY NUMBER HERE IS A DISTANCE, so every one scales with the world.
--
-- They did not, when the world was halved, and the result was a loading
-- screen with no Crossroads in it: the cameras stayed where they were while
-- the hub shrank to half the size underneath them, so the shots framed a lot
-- of empty sky with something small in the middle of it. Reported from the
-- fourth walk as "the background is not working".
local S = GameConfig.HubLayout.WorldScale

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
			Radius = 190 * S,
			Height = 96 * S,
			LookOffset = Vector3.new(0, 26 * S, 0),
			WorldId = nil,
		},
		{
			Id = "HALL_APPROACH",
			Caption = "Hall of Legends",
			Subject = Anchors.HALL_OF_LEGENDS,
			Radius = 240 * S,
			Height = 120 * S,
			LookOffset = Vector3.new(0, 34 * S, 0),
			WorldId = nil,
		},
		{
			Id = "ARCHIVE_ROTUNDA",
			Caption = "Discovery Archive",
			Subject = Anchors.DISCOVERY_ARCHIVE,
			Radius = 215 * S,
			Height = 108 * S,
			LookOffset = Vector3.new(0, 40 * S, 0),
			WorldId = nil,
		},
		{
			Id = "MARKET_STALLS",
			Caption = "The Market",
			Subject = Anchors.EXPEDITION_GATE,
			Radius = 230 * S,
			Height = 90 * S,
			LookOffset = Vector3.new(0, 24 * S, 0),
			WorldId = nil,
		},
		{
			Id = "TRAINING_YARD",
			Caption = "Training Grounds",
			Subject = Anchors.TRAINING_GROUNDS,
			Radius = 205 * S,
			Height = 86 * S,
			LookOffset = Vector3.new(0, 20 * S, 0),
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
			Radius = 1400 * S,
			Height = 620 * S,
			LookOffset = Vector3.new(0, -120 * S, 0),
			WorldId = nil,
		},
	},
}

return Cinematics
