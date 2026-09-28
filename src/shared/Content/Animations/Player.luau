--!strict
-- THE PLAYER'S ANIMATION SET: one slot per thing a character's body does.
--
-- Content, not code. Paste an uploaded animation's id into a slot
-- ("rbxassetid://123...") and CharacterAnimator plays it; leave it "" and the
-- slot falls back to the stock Roblox asset with our procedural layer on top
-- (docs/PLAYER_ABILITIES.md §2.7). A slot never needs a code change.
--
-- The directional slots are only used as a SET: all four of a gait
-- (Forward, Backward, Left, Right) must be filled before that gait switches
-- from the procedural fallback to blended clips, so a half-filled set never
-- plays three real clips and one fake one.
--
-- Animation ids are account/group-scoped (docs/PARTNER_SETUP.md): upload to
-- the group that owns the place.

return {
	-- Standing still.
	Idle = "",

	-- Walking (slow: a half-pushed stick, a weapon lock's crawl).
	WalkForward = "",
	WalkBackward = "",
	WalkLeft = "",
	WalkRight = "",

	-- Running: the normal on-foot speed in the hub and in an expedition.
	RunForward = "",
	RunBackward = "",
	RunLeft = "",
	RunRight = "",

	-- Sprinting. Forward only: sprint always faces the way it runs.
	Sprint = "",

	-- Airborne: the take-off (one-shot), the rise and fall (loops).
	JumpStart = "",
	Rise = "",
	Fall = "",

	-- Landing, one-shot, chosen by how fast the character came down.
	LandSoft = "",
	LandHard = "",

	-- The roll, one per direction RELATIVE TO FACING (owner, 2026-09-28): with
	-- the shoulder camera or a lock-on the character keeps facing forward and
	-- rolls whichever way was pressed. One-shot, timed to
	-- GameConfig.Locomotion.RollDurationSeconds. Unlike walk/run, each
	-- direction falls back on its own, so they can be filled one at a time.
	RollForward = "",
	RollBackward = "",
	RollLeft = "",
	RollRight = "",
	-- The backstep (roll pressed with no direction), one-shot.
	Backstep = "",

	-- Turning on the spot, one-shot, played when standing and turning fast.
	TurnLeft = "",
	TurnRight = "",
}
