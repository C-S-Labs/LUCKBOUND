--!strict
-- THE HUB MENU'S RULES, WITH NO ROBLOX IN THEM.
--
-- Same split the rest of the project uses and for the same reason: the client
-- draws, this decides. Which panels exist and in what order, what "in the
-- Crossroads" means, whether a travel request is allowed, and where a
-- traveller lands are all decided here, so all four are testable headlessly
-- and the server and the client cannot disagree about them.
--
-- The server calls `canTravel` to authorise; the client calls the same
-- function to grey out a button. One rule, two callers, no drift -- and the
-- client's copy is a courtesy, never the authority (AGENTS.md rule 5).

local Result = require(script.Parent.Result)

local HubMenuCore = {}

--- Panels in rail order. Copies, so a caller sorting the result cannot
--- reorder the frozen content table underneath it.
function HubMenuCore.panels(menu: any): { any }
	local list = {}
	for _, panel in menu.Panels do
		table.insert(list, panel)
	end
	table.sort(list, function(a, b)
		return a.Order < b.Order
	end)
	return list
end

function HubMenuCore.panelById(menu: any, id: string): any?
	for _, panel in menu.Panels do
		if panel.Id == id then
			return panel
		end
	end
	return nil
end

--- Destinations in menu order.
function HubMenuCore.destinations(menu: any): { any }
	local list = {}
	for _, destination in menu.Destinations do
		table.insert(list, destination)
	end
	table.sort(list, function(a, b)
		return a.Order < b.Order
	end)
	return list
end

function HubMenuCore.destinationById(menu: any, id: string): any?
	for _, destination in menu.Destinations do
		if destination.Id == id then
			return destination
		end
	end
	return nil
end

--- Where a destination puts a player, before the server's floor probe.
--- Anchor + Landing, kept in one function so nobody re-derives it with the
--- two the wrong way round.
function HubMenuCore.landingPoint(destination: any): Vector3
	return destination.Anchor + destination.Landing
end

--- THE VISIBILITY RULE, owner-directed: the hub menu exists in the
--- Crossroads and nowhere else. `expedition` is whatever
--- ExpeditionController holds -- nil means "in the hub".
function HubMenuCore.isVisible(expedition: any, config: any): boolean
	if not config.HubMenu.Enabled then
		return false
	end
	return expedition == nil
end

--- The rail's starting shape. Collapsed on a phone, open on a desktop, both
--- overridable by config and by the player's own setting afterwards.
function HubMenuCore.newState(config: any, isTouch: boolean): any
	local collapsed = if isTouch
		then config.HubMenu.StartCollapsedOnTouch
		else config.HubMenu.StartCollapsedOnDesktop
	return {
		OpenPanelId = nil :: string?,
		Collapsed = collapsed,
		Visible = true,
	}
end

--- The whole menu as a reducer: state in, action in, new state out, nothing
--- touched. It is here rather than inside the UI module because "opening
--- Travel closes Shop" is a RULE, and a rule buried in a click handler can
--- only be tested by clicking.
---
--- Actions: TOGGLE_PANEL {PanelId}, OPEN_PANEL {PanelId}, CLOSE_PANEL,
--- TOGGLE_COLLAPSE, SET_COLLAPSED {Collapsed}, SET_VISIBLE {Visible}.
function HubMenuCore.reduce(state: any, action: any, config: any): any
	local updated = {
		OpenPanelId = state.OpenPanelId,
		Collapsed = state.Collapsed,
		Visible = state.Visible,
	}

	if action.Kind == "TOGGLE_PANEL" then
		if updated.OpenPanelId == action.PanelId then
			updated.OpenPanelId = nil
		else
			updated.OpenPanelId = action.PanelId
		end
	elseif action.Kind == "OPEN_PANEL" then
		updated.OpenPanelId = action.PanelId
	elseif action.Kind == "CLOSE_PANEL" then
		updated.OpenPanelId = nil
	elseif action.Kind == "TOGGLE_COLLAPSE" then
		updated.Collapsed = not updated.Collapsed
	elseif action.Kind == "SET_COLLAPSED" then
		updated.Collapsed = action.Collapsed
	elseif action.Kind == "SET_VISIBLE" then
		updated.Visible = action.Visible
	end

	-- COLLAPSING HIDES THE PANEL TOO. The arrow's promise is "give me my
	-- screen back", and a collapsed rail with a panel still open beside it
	-- keeps most of the screen -- which is the opposite of what was asked for.
	if updated.Collapsed then
		updated.OpenPanelId = nil
	end

	-- Leaving the hub closes everything rather than hiding it open, so coming
	-- back does not restore a panel the player left behind ten minutes ago.
	if not updated.Visible then
		updated.OpenPanelId = nil
	end

	-- SinglePanel is the mode this reducer implements: it holds ONE open id,
	-- so "opening Travel closes Shop" is structural rather than enforced. A
	-- future two-column desktop layout would hold a set here instead, which
	-- is why the flag exists in config and is asserted by test.
	assert(config.HubMenu.SinglePanel, "HubMenuCore.reduce implements SinglePanel only")

	return updated
end

--- IS THIS TRAVEL REQUEST ALLOWED? The server's authority and the client's
--- button state, decided once.
---
--- `request` = { DestinationId, OnExpedition, Rolling }
function HubMenuCore.canTravel(menu: any, request: any, config: any): any
	if not config.HubMenu.Enabled then
		return Result.err("Travel is disabled.")
	end

	local destination = HubMenuCore.destinationById(menu, request.DestinationId)
	if not destination then
		-- The Id is the ONLY thing the client chooses, so this is the guard
		-- that matters: a fabricated destination is refused by name, never
		-- resolved into a position.
		return Result.err("Unknown destination.")
	end

	if request.OnExpedition then
		return Result.err("You cannot travel the Crossroads from an expedition.")
	end

	if request.Rolling then
		return Result.err("Wait for the roll to finish.")
	end

	-- NO COOLDOWN. Owner-directed: travel is quick and effectively
	-- instantaneous. The server's rate limit is a spam guard living in
	-- HubUISystem, not a rule about play, so it is deliberately not checked
	-- here -- the client must never grey a button out for it.
	return Result.ok(destination)
end

--- How long the client's fade covers the swap. The server moves the character
--- at the midpoint, so both halves are stated once, here. Short by design:
--- this is the ONLY thing between pressing TRAVEL and arriving.
function HubMenuCore.travelTiming(config: any): any
	local hub = config.HubMenu
	return {
		FadeOut = hub.TeleportFadeOutSeconds,
		Hold = hub.TeleportHoldSeconds,
		FadeIn = hub.TeleportFadeInSeconds,
		Total = hub.TeleportFadeOutSeconds + hub.TeleportHoldSeconds + hub.TeleportFadeInSeconds,
	}
end

return HubMenuCore
