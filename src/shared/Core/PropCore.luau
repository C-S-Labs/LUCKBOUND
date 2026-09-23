--!strict
-- The pure half of a world's ambient scenery (CHUNK_AUTHORING.md convention
-- 6): which props a device draws, and how each kind of prop moves. The
-- client's PropController turns this into MeshParts and CFrames.
--
-- PURE: no Roblox types, so the motion is testable headlessly.
--
-- THE RULES EVERY MOTION KEEPS:
--   * Nothing ever changes size. A prop's Size is set once, at placement.
--   * Bobbing is along true vertical and spinning is about true vertical,
--     whatever the prop's own tilt -- a tilted crystal must not wander.
--   * Tilting (rock, roll) is about the prop's OWN axes, so a ring rolls in
--     its own plane and a skiff rocks along its keel.
--   * Every motion is small, slow and periodic: scenery, not spectacle.

local PropCore = {}

-- Every animation class a placement may name. Kept here, not in content,
-- because each is behaviour -- adding one means writing its motion below.
PropCore.ANIMS = {
	Static = true, -- never moves
	Float = true, -- a slow bob up and down (beacons, a drifting lintel)
	Hover = true, -- a gentle bob while turning slowly about vertical (crystals, tomes)
	Spin = true, -- turns slowly about vertical, nothing else (rings round a keel)
	Roll = true, -- turns slowly in its own plane, about its own Z (hoops over a path)
	Moored = true, -- a boat at a dock: a small bob and a slight rock along its keel
	Tumble = true, -- debris adrift: a bob, a mild rock, a slow turn
	Bird = true, -- the flock circles its piece's centre, nose along the path
}

--- Whether a placement of this detail tier is drawn at this quality scale
--- (0..1, AmbienceCore.qualityScale). Tier 1 is always drawn.
function PropCore.tierShown(tier: number, scale: number, cfg: any): boolean
	local need = cfg.TierMinQuality[tier]
	return need ~= nil and scale >= need
end

--- A stable 0..1 number per placement, so every prop moves out of step with
--- its neighbours and the same prop moves the same way on every device.
function PropCore.phase(index: number): number
	local x = math.sin(index * 12.9898) * 43758.5453
	return x - math.floor(x)
end

--- How a prop is displaced at time t, as the controller composes it:
---
---   layout * [orbit about the piece's vertical axis]
---          * translate(P + (0, lift, 0))
---          * turnAbout(vertical, turn) * R * Angles(tiltX, 0, tiltZ)
---
--- lift is studs; every angle is radians. `orbit` is only non-zero for
--- birds, whose own rotation R is replaced by `heading`/`bank` (see
--- PropCore.birdHeading). There is deliberately no scale term.
function PropCore.motion(anim: string, t: number, phase: number, cfg: any)
	local m = { lift = 0, turn = 0, tiltX = 0, tiltZ = 0, orbit = 0, bank = 0 }
	local tau = math.pi * 2
	local c = cfg[anim]
	if anim == "Static" or c == nil then
		return m
	end
	local offset = phase * tau
	if
		anim == "Float"
		or anim == "Hover"
		or anim == "Tumble"
		or anim == "Moored"
		or anim == "Bird"
	then
		m.lift = (c.Amplitude or c.Bob) * math.sin(tau * t / c.Period + offset)
	end
	if anim == "Hover" then
		m.turn = tau * t / c.SpinPeriod + offset
	elseif anim == "Spin" then
		m.turn = tau * t / c.Period + offset
	elseif anim == "Roll" then
		m.tiltZ = tau * t / c.Period + offset
	elseif anim == "Moored" then
		m.tiltX = c.Rock * math.sin(tau * t / (c.Period * 1.4) + offset)
		m.tiltZ = c.Rock * 0.4 * math.sin(tau * t / (c.Period * 1.9) + offset * 2)
	elseif anim == "Tumble" then
		m.tiltX = c.Rock * math.sin(tau * t / (c.Period * 1.3) + offset)
		m.tiltZ = c.Rock * math.cos(tau * t / (c.Period * 0.9) + offset * 2)
		m.turn = tau * t / (c.Period * 4) + offset
	elseif anim == "Bird" then
		-- One angle for the whole flock, no per-bird phase: the flock turns as
		-- a rigid body, so birds clear of each other at rest stay clear. The
		-- generator proves each bird's full circle clear (clear_bird_orbits).
		m.orbit = tau * t / c.Period
		m.bank = c.Bank
	end
	return m
end

--- The yaw (radians, CFrame.Angles convention about vertical) that points a
--- bird's nose -- its own +X -- along its circle, for a bird at (x, z) in its
--- piece's layout frame circling the vertical axis through the origin with
--- a growing orbit angle. Added to the orbit angle itself at draw time.
function PropCore.birdHeading(x: number, z: number): number
	-- d/dθ of Ry(θ)·(x, 0, z) at θ = 0 is (z, 0, -x); Ry(h)·(1, 0, 0) is
	-- (cos h, 0, -sin h). Equal when cos h = z/r and sin h = x/r.
	return math.atan2(x, z)
end

return PropCore
