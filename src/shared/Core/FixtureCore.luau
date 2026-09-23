--!strict
-- The pure half of fixtures (CHUNK_AUTHORING.md convention 7, build spec
-- §7.5): the interactive things in a map -- chests, the vault door, a sealed
-- gate's forcefield. Unlike props they are placed by the SERVER, collide,
-- and change state; this module says what kinds exist, which parts each
-- needs, and how an opened one moves.
--
-- PURE: no Roblox types, so the motion is testable headlessly.

local FixtureCore = {}

-- Every fixture kind, and the part roles it is built from. Adding a kind
-- means writing what it does (LootSystem) and how it moves (below).
FixtureCore.KINDS = {
	CHEST = { Body = true, Lid = true }, -- opened once per party; loot for each
	VAULT = { Door = true }, -- opened once per party with a key; loot for each
	FORCEFIELD = { Field = true }, -- never opens; shimmers and blocks
}

-- Which kinds a player can use, and so get a prompt.
FixtureCore.OPENABLE = { CHEST = true, VAULT = true }

local function smooth(x: number): number
	local c = math.clamp(x, 0, 1)
	return c * c * (3 - 2 * c)
end

--- A chest lid's turn about its hinge (radians about its own X; negative
--- lifts the front), `elapsed` seconds after opening. Eases to cfg.LidAngle
--- over cfg.LidSeconds and stays there.
function FixtureCore.lidAngle(elapsed: number, cfg: any): number
	return -cfg.LidAngle * smooth(elapsed / cfg.LidSeconds)
end

--- A vault door's turn about its own axis (radians about its Z), `elapsed`
--- seconds after opening: DoorTurns full turns, easing in and out over
--- DoorSeconds, then still -- a combination dial being spun home.
function FixtureCore.doorSpin(elapsed: number, cfg: any): number
	return math.pi * 2 * cfg.DoorTurns * smooth(elapsed / cfg.DoorSeconds)
end

--- How far a vault door has slid back into the tunnel behind it once the
--- spin is done (studs along its axis), so an open vault reads as open.
function FixtureCore.doorRecess(elapsed: number, cfg: any): number
	return cfg.DoorRecess * smooth((elapsed - cfg.DoorSeconds) / cfg.DoorRecessSeconds)
end

--- A forcefield's transparency at time t: a slow breath between Min and Max.
--- Never fully clear -- it must read as a wall -- and never opaque.
function FixtureCore.fieldTransparency(t: number, phase: number, cfg: any): number
	local wave = 0.5 + 0.5 * math.sin(math.pi * 2 * (t / cfg.PulsePeriod + phase))
	return cfg.MinTransparency + (cfg.MaxTransparency - cfg.MinTransparency) * wave
end

return FixtureCore
