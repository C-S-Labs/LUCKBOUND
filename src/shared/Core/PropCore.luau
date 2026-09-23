--!strict
-- The pure half of a world's ambient scenery (CHUNK_AUTHORING.md convention
-- 6): which props a device draws, and how each kind of prop moves. The
-- client's PropController turns this into MeshParts and CFrames.
--
-- PURE: no Roblox types, so the motion is testable headlessly.

local PropCore = {}

-- Every animation class a placement may name. Kept here, not in content,
-- because each is behaviour -- adding one means writing its motion below.
PropCore.ANIMS = {
	Static = true, -- never moves
	Float = true, -- slow bob up and down
	Hover = true, -- a gentler bob while turning slowly
	Spin = true, -- turns about its vertical axis
	Roll = true, -- turns about its own Z (a ring's axis)
	Tumble = true, -- a slow lopsided rock, like debris adrift
	Bird = true, -- circles its placed spot, facing along its path
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

--- How a prop is displaced at time t. Returns the pieces the controller
--- composes, in this order:
---   CFrame.Angles(0, orbitAngle, 0) * CFrame.new(0, dy, orbitRadius)
---     * CFrame.Angles(pitch, yaw, roll)
--- applied in the prop's placement frame. Angles are radians.
function PropCore.motion(anim: string, t: number, phase: number, cfg: any)
	local m = { dy = 0, pitch = 0, yaw = 0, roll = 0, orbitAngle = 0, orbitRadius = 0 }
	local tau = math.pi * 2
	local c = cfg[anim]
	if anim == "Static" or c == nil then
		return m
	end
	local offset = phase * tau
	if anim == "Float" or anim == "Hover" or anim == "Tumble" then
		m.dy = c.Amplitude * math.sin(tau * t / c.Period + offset)
	end
	if anim == "Hover" then
		m.yaw = tau * t / c.SpinPeriod + offset
	elseif anim == "Spin" then
		m.yaw = tau * t / c.Period + offset
	elseif anim == "Roll" then
		m.roll = tau * t / c.Period + offset
	elseif anim == "Tumble" then
		m.pitch = c.Rock * math.sin(tau * t / (c.Period * 1.3) + offset)
		m.roll = c.Rock * math.cos(tau * t / (c.Period * 0.9) + offset * 2)
		m.yaw = tau * t / (c.Period * 4) + offset
	elseif anim == "Bird" then
		m.orbitAngle = tau * t / c.Period + offset
		m.orbitRadius = c.Radius
		m.dy = c.Bob * math.sin(tau * t / (c.Period * 0.37) + offset)
	end
	return m
end

return PropCore
