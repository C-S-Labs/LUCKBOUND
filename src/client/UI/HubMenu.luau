--!strict
-- THE HUB MENU: the side rail, its panels, and the arrow that hides it.
--
-- WHAT THIS MODULE IS ALLOWED TO DECIDE: pixels. Nothing else. Which panels
-- exist and in what order is Content/Hub/Menu; whether a panel may open,
-- whether travel is allowed and what "in the Crossroads" means is
-- HubMenuCore; every colour, pad and tween length is UITheme; every
-- behavioural number is GameConfig. If a rule appears in this file, it is in
-- the wrong file.
--
-- THREE THINGS THE OWNER ASKED FOR, AND WHERE THEY LIVE:
--
--  1. "Only visible while in the Crossroads" -- HubMenuCore.isVisible, driven
--     by ExpeditionController. An expedition is the game; a menu over it is
--     not.
--  2. "A toggled arrow that hides the side panel to reduce screen noise" --
--     the arrow is the only thing that survives a collapse, and it stays
--     pinned to the screen edge so the way back is never lost.
--  3. "Not overwhelming" -- one panel at a time (HubMenuCore's reducer holds
--     one open id), the rail starts collapsed on touch, and the whole thing
--     gets out of the way during a roll.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Root = ReplicatedStorage:WaitForChild("Luckbound")
local Constants = require(Root.Core.Constants)
local GameConfig = require(Root.Core.GameConfig)
local HubMenuCore = require(Root.Core.HubMenuCore)
local Menu = require(Root.Content.Hub.Menu)
local Net = require(Root.Core.Net)
local SettingsCore = require(Root.Core.SettingsCore)
local UITheme = require(Root.Core.UITheme)

local ExpeditionController = require(script.Parent.Parent.Controllers.ExpeditionController)
local PartyController = require(script.Parent.Parent.Controllers.PartyController)
local StateController = require(script.Parent.Parent.Controllers.StateController)
local FateRoll = require(script.Parent.FateRoll)
local LoadingScreen = require(script.Parent.LoadingScreen)
local UIKit = require(script.Parent.UIKit)

local HubMenu = {}

local player = Players.LocalPlayer

local gui: ScreenGui
local rail: Frame
local railList: Frame
local arrow: TextButton
local panelHolder: Frame
local panelTitle: TextLabel
local panelBody: ScrollingFrame
local fateLabel: TextLabel
local fateFill: Frame
local toast: TextLabel

local railButtons: { [string]: TextButton } = {}
local state = HubMenuCore.newState(GameConfig, UserInputService.TouchEnabled)
local hiddenForRoll = false
-- The menu is built while the loading screen is still up -- it has to be, so
-- that it is ready the moment PLAY is pressed -- but it must not be VISIBLE
-- behind it. The fourth walk caught the rail sitting over the title card.
local hiddenForLoading = not LoadingScreen.isFinished()
-- An expedition server (build spec §7.2) is the expedition, start to finish.
-- There is no Crossroads to travel around and no party to form there.
local onExpeditionServer = Root:GetAttribute(Constants.SERVER_KIND_ATTRIBUTE)
	== Constants.SERVER_KIND_EXPEDITION
local travelling = false
local veilGui: ScreenGui
local veil: Frame
local toastToken = 0

-- === toast ==========================================================

--- A one-line answer at the bottom of the panel. Travel refusals, code
--- results and "not built yet" all speak through this, so there is one place
--- the game talks back and the player learns where to look.
local function say(text: string, good: boolean)
	toastToken += 1
	local token = toastToken

	toast.Text = text
	toast.TextColor3 = if good then UITheme.AccentGold else UITheme.AccentWarn
	toast.TextTransparency = 1
	toast.Visible = true
	UIKit.tween(toast, UITheme.Motion.Quick, { TextTransparency = 0 })

	task.delay(GameConfig.UI.AnnouncementDurationSeconds, function()
		if token ~= toastToken then
			return
		end
		UIKit.tween(toast, UITheme.Motion.Normal, { TextTransparency = 1 }, true)
	end)
end

-- === travel =========================================================

--- THE FADE. The server moves the character the moment it authorises the
--- request, so the swap itself is instant -- what makes it read as travel
--- rather than as a teleport glitch is that the player's screen is black
--- while it happens. The timings are HubMenuCore.travelTiming, so the fade
--- and the move are stated once and cannot drift apart.
---
--- It lives on its own ScreenGui above the menu: a veil drawn inside the menu
--- would be underneath the roll prompt and the expedition banner, and a
--- half-covered fade is worse than none.
local function travelTo(destinationId: string)
	if travelling then
		return
	end
	travelling = true

	local timing = HubMenuCore.travelTiming(GameConfig)
	veil.Visible = true
	UIKit.tween(veil, timing.FadeOut, { BackgroundTransparency = 0 })

	task.delay(UIKit.duration(timing.FadeOut), function()
		Net.get("Hub_RequestTravel"):FireServer({ DestinationId = destinationId })

		task.delay(UIKit.duration(timing.Hold), function()
			local back = UIKit.tween(veil, timing.FadeIn, { BackgroundTransparency = 1 }, true)
			back.Completed:Once(function()
				veil.Visible = false
				travelling = false
			end)
		end)
	end)
end

-- === panels =========================================================

local function clearBody()
	for _, child in panelBody:GetChildren() do
		if not child:IsA("UIListLayout") and not child:IsA("UIPadding") then
			child:Destroy()
		end
	end
end

local function section(text: string, order: number): TextLabel
	local label = UIKit.label(panelBody, string.upper(text), 12, "MUTED")
	label.Size = UDim2.new(1, 0, 0, 18)
	label.LayoutOrder = order
	return label
end

local function paragraph(text: string, order: number): TextLabel
	local label = UIKit.label(panelBody, text, 14, "SECONDARY")
	label.Size = UDim2.new(1, 0, 0, 0)
	label.AutomaticSize = Enum.AutomaticSize.Y
	label.LayoutOrder = order
	return label
end

--- TRAVEL. The five places the Crossroads is made of, and a cooldown that
--- keeps walking it the default rather than the punishment.
local function buildTravel()
	section("Crossroads", 1)

	local order = 2
	for _, destination in HubMenuCore.destinations(Menu) do
		local row = UIKit.surface(panelBody, "RAISED")
		row.Size = UDim2.new(1, 0, 0, 68)
		row.LayoutOrder = order
		order += 1

		local title = UIKit.label(row, destination.Label, 16, "PRIMARY")
		title.Position = UDim2.fromOffset(UITheme.Space.MD, UITheme.Space.SM + 2)
		title.Size = UDim2.new(1, -140, 0, 20)

		local subtitle = UIKit.label(row, destination.Subtitle, 13, "MUTED")
		subtitle.Position = UDim2.fromOffset(UITheme.Space.MD, UITheme.Space.SM + 26)
		subtitle.Size = UDim2.new(1, -140, 0, 18)

		local go = UIKit.button(row, "TRAVEL", "PRIMARY", function()
			travelTo(destination.Id)
		end)
		go.AnchorPoint = Vector2.new(1, 0.5)
		go.Position = UDim2.new(1, -UITheme.Space.MD, 0.5, 0)
		go.Size = UDim2.fromOffset(104, 38)
	end

	paragraph("Anywhere in the Crossroads, immediately.", order)

end

--- CODES. The one panel where the client sends a free string, so it is also
--- the one panel that validates nothing locally: the server decides, and
--- whatever it says is what the player reads.
local function buildCodes()
	section("Redeem", 1)

	local box = Instance.new("TextBox")
	box.Size = UDim2.new(1, 0, 0, 46)
	box.LayoutOrder = 2
	box.BackgroundColor3 = UITheme.RaisedColor
	box.BackgroundTransparency = UITheme.RaisedTransparency
	box.BorderSizePixel = 0
	box.ClearTextOnFocus = false
	box.Font = UITheme.LabelFont
	box.PlaceholderText = "ENTER CODE"
	box.PlaceholderColor3 = UITheme.TextMuted
	box.Text = ""
	box.TextColor3 = UITheme.TextPrimary
	box.TextSize = 16
	box.Parent = panelBody
	UITheme.corner(box, UITheme.RadiusSmall)
	UITheme.stroke(box)

	local submit = UIKit.button(panelBody, "REDEEM", "PRIMARY", function()
		if box.Text == "" then
			say("Enter a code.", false)
			return
		end
		Net.get("Code_Redeem"):FireServer({ Code = box.Text })
		box.Text = ""
	end)
	submit.LayoutOrder = 3

	box.FocusLost:Connect(function(enterPressed)
		if enterPressed and box.Text ~= "" then
			Net.get("Code_Redeem"):FireServer({ Code = box.Text })
			box.Text = ""
		end
	end)

	local redeemed = StateController.get().RedeemedCodes or {}
	local count = 0
	for _ in redeemed do
		count += 1
	end

	section("Redeemed", 4)
	paragraph(
		if count == 0
			then "None yet. Codes are posted with updates."
			else string.format("%d code%s used.", count, if count == 1 then "" else "s"),
		5
	)
end

--- SETTINGS. Drawn entirely from SettingsCore.SPEC -- adding a setting adds a
--- row here with no edit to this function, which is the same content/system
--- split the rest of the project runs on.
local function buildSettings()
	section("Preferences", 1)

	local order = 2
	for _, entry in SettingsCore.ordered() do
		if entry.Kind == "boolean" then
			local row = UIKit.toggle(panelBody, entry.Label, StateController.setting(entry.Id) == true, function(value)
				StateController.applySetting(entry.Id, value)
			end)
			row.LayoutOrder = order
		else
			local row = UIKit.slider(
				panelBody,
				entry.Label,
				StateController.setting(entry.Id),
				entry.Min,
				entry.Max,
				function(value)
					StateController.applySetting(entry.Id, value)
				end
			)
			row.LayoutOrder = order
		end
		order += 1
	end

	paragraph("Settings save to your profile and follow you between servers.", order)
end

--- One row of the party panel: a name, an optional tag under it, and up to two
--- buttons on the right. Buttons are {Text, Style, Enabled, OnClick}.
local function partyRow(order: number, name: string, tag: string?, buttons: { any })
	local row = UIKit.surface(panelBody, "RAISED")
	row.Size = UDim2.new(1, 0, 0, 56)
	row.LayoutOrder = order

	local reserved = #buttons * (UITheme.Space.SM + 92) + UITheme.Space.MD
	local title = UIKit.label(row, name, 15, "PRIMARY")
	title.Position = UDim2.fromOffset(UITheme.Space.MD, if tag then UITheme.Space.SM else 0)
	title.Size = UDim2.new(1, -reserved, 0, if tag then 20 else 56)

	if tag then
		local sub = UIKit.label(row, tag, 12, "MUTED")
		sub.Position = UDim2.fromOffset(UITheme.Space.MD, UITheme.Space.SM + 22)
		sub.Size = UDim2.new(1, -reserved, 0, 16)
	end

	local right = UITheme.Space.MD
	for index = #buttons, 1, -1 do
		local spec = buttons[index]
		local button = UIKit.button(row, spec.Text, spec.Style, spec.OnClick)
		button.AnchorPoint = Vector2.new(1, 0.5)
		button.Position = UDim2.new(1, -right, 0.5, 0)
		button.Size = UDim2.fromOffset(92, 34)
		button.TextSize = 13
		if spec.Enabled == false then
			UIKit.setEnabled(button, false)
		end
		right += 92 + UITheme.Space.SM
	end
end

--- PARTY. Live 2026-09-22 (build spec §7.2). Everything drawn here comes from
--- PartyController's last sync; every button sends one request and waits for
--- the server's answer, which redraws the panel. Buttons the server would
--- refuse are greyed rather than hidden, so the rule explains itself.
local function buildParty()
	local party = PartyController.get()
	local me = player.UserId
	local inParty = party.PartyId ~= nil
	local full = inParty and #party.Members >= party.MaxSize
	local order = 1

	local function nextOrder(): number
		order += 1
		return order
	end

	section(if inParty then string.format("Your party  %d / %d", #party.Members, party.MaxSize) else "Your party", order)

	if not inParty then
		paragraph("You are not in a party. Invite someone below.", nextOrder())
	else
		for _, userId in party.Members do
			local isLeader = userId == party.LeaderUserId
			local isMe = userId == me
			local tag = if isLeader and isMe
				then "Leader · you"
				elseif isLeader then "Leader"
				elseif isMe then "You"
				else nil
			local buttons = {}
			if party.IsLeader and not isMe then
				table.insert(buttons, {
					Text = "LEAD",
					OnClick = function()
						PartyController.request("PROMOTE", userId)
					end,
				})
				table.insert(buttons, {
					Text = "REMOVE",
					Style = "DANGER",
					OnClick = function()
						PartyController.request("KICK", userId)
					end,
				})
			end
			partyRow(nextOrder(), PartyController.nameOf(userId), tag, buttons)
		end

		local leave = UIKit.button(panelBody, "LEAVE PARTY", "DANGER", function()
			PartyController.request("LEAVE")
		end)
		leave.LayoutOrder = nextOrder()
	end

	if #party.Invites > 0 then
		section("Invites", nextOrder())
		for _, invite in party.Invites do
			partyRow(nextOrder(), PartyController.nameOf(invite.FromUserId), "wants you in their party", {
				{
					Text = "ACCEPT",
					Style = "PRIMARY",
					Enabled = not inParty,
					OnClick = function()
						PartyController.request("ACCEPT", invite.FromUserId)
					end,
				},
				{
					Text = "DECLINE",
					OnClick = function()
						PartyController.request("DECLINE", invite.FromUserId)
					end,
				},
			})
		end
	end

	section("Players here", nextOrder())
	local canInvite = (not inParty or party.IsLeader) and not full
	local anyone = false
	for _, other in party.Others or {} do
		local isMember = inParty and table.find(party.Members, other.UserId) ~= nil
		if isMember then
			continue
		end
		anyone = true
		partyRow(nextOrder(), other.Name, if other.InParty then "In a party" else nil, {
			{
				Text = "INVITE",
				Style = "PRIMARY",
				Enabled = canInvite and not other.InParty,
				OnClick = function()
					PartyController.request("INVITE", other.UserId)
				end,
			},
		})
	end
	if not anyone then
		paragraph("Nobody else is in this server yet.", nextOrder())
	end

	paragraph(
		if inParty and not party.IsLeader
			then "Your leader opens the portal. When they step in, you go with them — to their world, on their map."
			else "When the leader steps into the portal, the whole party goes with them: one world, one map, one timer. Everyone keeps their own Fate and level.",
		nextOrder()
	)
end

--- The PREVIEW panels. These draw their real design over placeholder data and
--- say so on the badge, because the owner's direction is that they are
--- designed now and implemented after testing. A button that silently does
--- nothing would be worse than no button at all.
local function buildPreview(panel: any, lines: { string })
	UIKit.previewBadge(panelBody, "IN DESIGN — not yet playable").LayoutOrder = 1

	local order = 2
	paragraph(panel.Summary, order)
	order += 1

	for _, line in lines do
		local row = UIKit.surface(panelBody, "RAISED")
		row.Size = UDim2.new(1, 0, 0, 0)
		row.AutomaticSize = Enum.AutomaticSize.Y
		row.LayoutOrder = order
		order += 1

		UITheme.pad(row, UITheme.Space.MD)
		local label = UIKit.label(row, line, 14, "SECONDARY")
		label.Size = UDim2.new(1, 0, 0, 0)
		label.AutomaticSize = Enum.AutomaticSize.Y
	end
end

local PREVIEW_LINES: { [string]: { string } } = {
	SHOP = {
		"<b>Stock rotates.</b> A handful of items a day, so the shop is a reason to come back rather than a list to read once.",
		"<b>Fate is the currency</b> for now — the same number the roll already grows.",
		"<b>Weapons carry their own rules.</b> A sword's damage, effects and animations live on the sword, never on you.",
	},
	SKILLS = {
		"<b>Four branches.</b> Fortune (what the roll can reach), Endurance (how long an expedition lasts), Discovery (what a world yields) and Craft (what your gear becomes).",
		"<b>Spent in Fate levels</b>, not points — so levelling stays the thing that unlocks, and points stay the score.",
		"<b>Nothing in it touches the odds.</b> Decision D-8: Fate unlocks which pools you draw from, never how a draw resolves.",
	},
	REBIRTH = {
		"<b>Rebirth trades everything</b> — Fate level, tree, inventory — for a permanent multiplier and a tier you keep.",
		"<b>Prestige lives inside it.</b> One screen, two scales: Rebirth is the loop, Prestige is the shelf the loop fills.",
		"<b>Nothing is lost that was rolled.</b> Roll history, discoveries and the Hall of Legends survive every rebirth.",
	},
}

local function buildPanelBody(panelId: string)
	clearBody()
	local panel = HubMenuCore.panelById(Menu, panelId)
	if not panel then
		return
	end

	panelTitle.Text = panel.Label

	if panelId == "TRAVEL" then
		buildTravel()
	elseif panelId == "CODES" then
		buildCodes()
	elseif panelId == "SETTINGS" then
		buildSettings()
	elseif panelId == "PARTY" then
		buildParty()
	else
		buildPreview(panel, PREVIEW_LINES[panelId] or {})
	end
end

-- === the rail =======================================================

local function railRestingPosition(): UDim2
	if state.Collapsed then
		-- Off the left edge entirely, leaving only the arrow. "Hide the side
		-- panel" was the ask, and a rail shrunk to a strip of glyphs is still
		-- a rail on the screen.
		return UDim2.new(0, -UITheme.RailWidthExpanded - UITheme.Space.LG, 0.5, 0)
	end
	return UDim2.new(0, UITheme.Space.MD, 0.5, 0)
end

local function panelRestingPosition(): UDim2
	local left = if state.Collapsed
		then UITheme.Space.LG * 2
		else UITheme.RailWidthExpanded + UITheme.Space.MD * 2
	return UDim2.new(0, left, 0.5, 0)
end

local function refreshRailSelection()
	for id, button in railButtons do
		local selected = state.OpenPanelId == id
		UIKit.tween(button, UITheme.Motion.Quick, {
			BackgroundColor3 = if selected
				then UITheme.RaisedColor:Lerp(UITheme.AccentGold, 0.28)
				else UITheme.RaisedColor,
		})
	end
end

local function applyPanelVisibility()
	if state.OpenPanelId then
		buildPanelBody(state.OpenPanelId)
		panelHolder.Visible = true
		UIKit.revealFrom(panelHolder, panelRestingPosition())
	elseif panelHolder.Visible then
		local target = panelRestingPosition() + UDim2.fromOffset(0, UITheme.Motion.SlideOffset)
		local tween = UIKit.tween(
			panelHolder,
			UITheme.Motion.Quick,
			{ Position = target, BackgroundTransparency = 1 },
			true
		)
		tween.Completed:Once(function()
			if not state.OpenPanelId then
				panelHolder.Visible = false
			end
		end)
	end
end

local function applyState()
	UIKit.tween(rail, UITheme.Motion.Normal, { Position = railRestingPosition() })

	-- The arrow is the one thing a collapse leaves on screen, so it moves
	-- WITH the rail rather than staying put: it sits against the rail's edge
	-- when open and against the screen's when closed, and either way it is
	-- the obvious thing to press.
	arrow.Text = if state.Collapsed then "›" else "‹"
	local arrowTarget = if state.Collapsed
		then UDim2.new(0, UITheme.Space.SM, 0.5, 0)
		else UDim2.new(0, UITheme.RailWidthExpanded + UITheme.Space.MD + UITheme.Space.XS, 0.5, 0)
	UIKit.tween(arrow, UITheme.Motion.Normal, { Position = arrowTarget })

	refreshRailSelection()
	applyPanelVisibility()
end

local function dispatch(action: any)
	state = HubMenuCore.reduce(state, action, GameConfig)
	applyState()
end

--- THE ONE PLACE THAT DECIDES WHETHER THE MENU IS ON SCREEN.
---
--- Three things can hide it and they are independent: leaving the Crossroads,
--- a roll resolving, and the loading screen still being up. Each used to set
--- gui.Enabled itself, which is how the rail ended up visible behind the
--- title card -- one of them said "show" without knowing another said "hide".
local function refreshVisibility()
	gui.Enabled = state.Visible and not hiddenForRoll and not hiddenForLoading and not onExpeditionServer
end

local function setVisible(visible: boolean)
	-- Visibility is a property of the GUI, not of the state machine's idea of
	-- itself: the reducer still closes panels on the way out, so returning to
	-- the hub never restores a panel left open ten minutes ago.
	dispatch({ Kind = "SET_VISIBLE", Visible = visible })
	refreshVisibility()
end

-- === build ==========================================================

local function buildRail()
	rail = UIKit.surface(gui, "RAIL")
	rail.Name = "Rail"
	rail.AnchorPoint = Vector2.new(0, 0.5)
	rail.Position = railRestingPosition()
	rail.Size = UDim2.new(0, UITheme.RailWidthExpanded, 0, 0)
	rail.AutomaticSize = Enum.AutomaticSize.Y
	UITheme.pad(rail, UITheme.Space.MD)

	local layout = UIKit.list(rail, UITheme.Space.SM)
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center

	-- The Fate card. The rail's header is the number the whole progression
	-- runs on, so the menu always answers "how am I doing" without opening
	-- anything.
	local header = UIKit.surface(rail, "RAISED")
	header.Size = UDim2.new(1, 0, 0, 58)
	header.LayoutOrder = 0

	fateLabel = UIKit.label(header, "FATE 1", 15, "ACCENT")
	fateLabel.Position = UDim2.fromOffset(UITheme.Space.SM + 2, UITheme.Space.SM)
	fateLabel.Size = UDim2.new(1, -UITheme.Space.MD, 0, 18)

	local barTrack = Instance.new("Frame")
	barTrack.Position = UDim2.fromOffset(UITheme.Space.SM + 2, 36)
	barTrack.Size = UDim2.new(1, -(UITheme.Space.SM + 2) * 2, 0, 6)
	barTrack.BackgroundColor3 = UITheme.BackgroundColor
	barTrack.BorderSizePixel = 0
	barTrack.Parent = header
	UITheme.corner(barTrack, UDim.new(0, 3))

	fateFill = Instance.new("Frame")
	fateFill.Size = UDim2.fromScale(0, 1)
	fateFill.BackgroundColor3 = UITheme.AccentGold
	fateFill.BorderSizePixel = 0
	fateFill.Parent = barTrack
	UITheme.corner(fateFill, UDim.new(0, 3))

	railList = rail

	for index, panel in HubMenuCore.panels(Menu) do
		local button = UIKit.button(railList, "", nil, function()
			dispatch({ Kind = "TOGGLE_PANEL", PanelId = panel.Id })
		end)
		button.Name = panel.Id
		button.LayoutOrder = index
		button.Size = UDim2.new(1, 0, 0, 42)
		button.Text = ""

		local glyph = UIKit.label(button, panel.Glyph, 20, "ACCENT")
		glyph.Position = UDim2.fromOffset(UITheme.Space.MD, 0)
		glyph.Size = UDim2.fromOffset(24, 42)
		glyph.TextXAlignment = Enum.TextXAlignment.Center

		local label = UIKit.label(button, panel.Label, 15)
		label.Position = UDim2.fromOffset(UITheme.Space.MD + 30, 0)
		label.Size = UDim2.new(1, -(UITheme.Space.MD + 42), 1, 0)

		if panel.Status == "PREVIEW" then
			-- A dot rather than a word: the panel itself explains, and a rail
			-- full of "SOON" labels is exactly the noise the owner asked to
			-- avoid.
			local dot = Instance.new("Frame")
			dot.AnchorPoint = Vector2.new(1, 0.5)
			dot.Position = UDim2.new(1, -UITheme.Space.MD, 0.5, 0)
			dot.Size = UDim2.fromOffset(6, 6)
			dot.BackgroundColor3 = UITheme.AccentCool
			dot.BorderSizePixel = 0
			dot.Parent = button
			UITheme.corner(dot, UDim.new(0, 3))
		end

		railButtons[panel.Id] = button
	end
end

local function buildArrow()
	arrow = Instance.new("TextButton")
	arrow.Name = "CollapseArrow"
	arrow.AnchorPoint = Vector2.new(0, 0.5)
	arrow.Size = UDim2.fromOffset(26, 64)
	arrow.BackgroundColor3 = UITheme.RailColor
	arrow.BackgroundTransparency = UITheme.RailTransparency
	arrow.BorderSizePixel = 0
	arrow.Font = UITheme.HeaderFont
	arrow.Text = "‹"
	arrow.TextColor3 = UITheme.AccentGold
	arrow.TextSize = 22
	arrow.AutoButtonColor = false
	arrow.Parent = gui
	UITheme.corner(arrow, UITheme.RadiusSmall)
	UITheme.stroke(arrow)

	arrow.Activated:Connect(function()
		dispatch({ Kind = "TOGGLE_COLLAPSE" })
	end)
end

local function buildPanel()
	panelHolder = UIKit.surface(gui, "PANEL")
	panelHolder.Name = "Panel"
	panelHolder.AnchorPoint = Vector2.new(0, 0.5)
	panelHolder.Position = panelRestingPosition()
	panelHolder.Size = UDim2.new(0.34, 0, 0.72, 0)
	panelHolder.Visible = false

	local constraint = Instance.new("UISizeConstraint")
	constraint.MinSize = Vector2.new(UITheme.PanelMinWidth, 240)
	constraint.MaxSize = Vector2.new(UITheme.PanelMaxWidth, 720)
	constraint.Parent = panelHolder

	UITheme.pad(panelHolder, UITheme.Space.LG)

	panelTitle = UIKit.label(panelHolder, "", 22, "PRIMARY")
	panelTitle.Font = UITheme.HeaderFont
	panelTitle.Size = UDim2.new(1, -40, 0, 30)

	local close = UIKit.button(panelHolder, "✕", nil, function()
		dispatch({ Kind = "CLOSE_PANEL" })
	end)
	close.AnchorPoint = Vector2.new(1, 0)
	close.Position = UDim2.new(1, 0, 0, 0)
	close.Size = UDim2.fromOffset(30, 30)
	close.TextSize = 14

	panelBody = Instance.new("ScrollingFrame")
	panelBody.Position = UDim2.fromOffset(0, 44)
	panelBody.Size = UDim2.new(1, 0, 1, -76)
	panelBody.BackgroundTransparency = 1
	panelBody.BorderSizePixel = 0
	panelBody.ScrollBarThickness = 3
	panelBody.ScrollBarImageColor3 = UITheme.DividerColor
	panelBody.CanvasSize = UDim2.new()
	panelBody.AutomaticCanvasSize = Enum.AutomaticSize.Y
	panelBody.Parent = panelHolder
	UIKit.list(panelBody, UITheme.Space.SM)

	toast = UIKit.label(panelHolder, "", 13, "ACCENT")
	toast.AnchorPoint = Vector2.new(0, 1)
	toast.Position = UDim2.new(0, 0, 1, 0)
	toast.Size = UDim2.new(1, 0, 0, 24)
	toast.Visible = false
end

local function build()
	gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundHubMenu"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	-- Explicitly below every other Luckbound screen. The menu is chrome; the
	-- roll, the expedition banner and a global announcement are the game, and
	-- none of them may end up behind it because of creation order.
	gui.DisplayOrder = -1
	gui.Parent = player:WaitForChild("PlayerGui")

	veilGui = Instance.new("ScreenGui")
	veilGui.Name = "LuckboundTravelVeil"
	veilGui.ResetOnSpawn = false
	veilGui.IgnoreGuiInset = true
	veilGui.DisplayOrder = 50
	veilGui.Parent = player:WaitForChild("PlayerGui")

	veil = Instance.new("Frame")
	veil.Size = UDim2.fromScale(1, 1)
	veil.BackgroundColor3 = UITheme.ScrimColor
	veil.BackgroundTransparency = 1
	veil.BorderSizePixel = 0
	veil.Visible = false
	veil.Parent = veilGui

	buildRail()
	buildArrow()
	buildPanel()
end

-- === wiring =========================================================

--- Resolves a KeyCode NAME to its EnumItem, safely.
---
--- Indexing an Enum with a name it does not have RAISES; it does not return
--- nil. Content naming the collapse key "Backslash" (Roblox calls it
--- "BackSlash") therefore threw on every keypress and took the panel
--- shortcuts down with it. Content is now checked against
--- Constants.HOTKEY_NAMES at boot, and this is the belt to that braces: an
--- unknown name degrades to "no shortcut" rather than to an error per
--- keystroke.
local function keyCodeNamed(name: any): EnumItem?
	if type(name) ~= "string" or not Constants.HOTKEY_NAMES[name] then
		return nil
	end
	local ok, value = pcall(function()
		return (Enum.KeyCode :: any)[name]
	end)
	if ok and typeof(value) == "EnumItem" then
		return value
	end
	return nil
end

local function bindHotkeys()
	-- Resolved ONCE, not per keystroke: this used to be an Enum index inside
	-- the input handler, which is both the slowest place to put it and the
	-- worst place for it to throw.
	local collapseKey = keyCodeNamed(Menu.CollapseHotkey)
	local panelKeys: { [any]: string } = {}
	for _, panel in Menu.Panels do
		local key = keyCodeNamed(panel.Hotkey)
		if key then
			panelKeys[key] = panel.Id
		elseif panel.Hotkey ~= nil then
			warn(`[HubMenu] panel '{panel.Id}' has an unusable hotkey '{tostring(panel.Hotkey)}'`)
		end
	end

	UserInputService.InputBegan:Connect(function(input, processed)
		if processed or not gui.Enabled then
			return
		end
		if input.UserInputType ~= Enum.UserInputType.Keyboard then
			return
		end

		if input.KeyCode == Enum.KeyCode.Escape and state.OpenPanelId then
			dispatch({ Kind = "CLOSE_PANEL" })
			return
		end

		if collapseKey and input.KeyCode == collapseKey then
			dispatch({ Kind = "TOGGLE_COLLAPSE" })
			return
		end

		local panelId = panelKeys[input.KeyCode]
		if panelId then
			if state.Collapsed then
				-- A hotkey for a hidden rail opens the rail with it, rather
				-- than opening a panel next to nothing.
				dispatch({ Kind = "SET_COLLAPSED", Collapsed = false })
			end
			dispatch({ Kind = "TOGGLE_PANEL", PanelId = panelId })
		end
	end)
end

function HubMenu.init(): ()
	build()
	bindHotkeys()
	applyState()
	refreshVisibility()

	-- The loading screen owns the screen until PLAY.
	LoadingScreen.onFinished(function()
		hiddenForLoading = false
		refreshVisibility()
	end)

	StateController.onChanged(function(snapshot)
		fateLabel.Text = string.format("FATE %d", snapshot.FateLevel)
		UIKit.tween(fateFill, UITheme.Motion.Slow, {
			Size = UDim2.fromScale(math.clamp(snapshot.Progress or 0, 0, 1), 1),
		})
	end)

	-- THE VISIBILITY RULE. nil expedition means "in the Crossroads"; the
	-- decision itself belongs to HubMenuCore so the server agrees with it.
	ExpeditionController.onChanged(function(expedition)
		setVisible(HubMenuCore.isVisible(expedition, GameConfig))
	end)

	-- ...and out of the way for the roll, which is the one screen in this
	-- game that gets the whole display.
	FateRoll.onRollingChanged(function(rolling)
		if not GameConfig.HubMenu.HideDuringRoll then
			return
		end
		hiddenForRoll = rolling
		if rolling then
			refreshVisibility()
		else
			task.delay(GameConfig.HubMenu.RestoreDelaySeconds, function()
				refreshVisibility()
			end)
		end
	end)

	Net.get("Hub_TravelResult").OnClientEvent:Connect(function(payload)
		if payload.Ok then
			local destination = HubMenuCore.destinationById(Menu, payload.DestinationId)
			say(if destination then `Arrived: {destination.Label}` else "Arrived.", true)
		else
			say(payload.Reason or "You cannot travel right now.", false)
		end
	end)

	-- The party panel redraws on every sync while it is open, and whatever
	-- the server said about the last request lands in the toast. Syncs with
	-- no message (someone else joined the server) redraw silently.
	PartyController.onChanged(function(snapshot)
		if state.OpenPanelId == "PARTY" then
			buildPanelBody("PARTY")
		end
		if snapshot.Message and state.OpenPanelId == "PARTY" then
			say(snapshot.Message, snapshot.Good == true)
		end
	end)

	Net.get("Code_Result").OnClientEvent:Connect(function(payload)
		if payload.Ok then
			say(string.format("%s  +%d Fate", payload.Message, payload.Fate or 0), true)
		else
			say(payload.Message or "That code is not valid.", false)
		end
	end)

	-- The player's own preference wins over the platform default -- ONCE,
	-- when their profile first arrives. Applying it on every state change
	-- would re-collapse the rail every time they closed a panel, which is a
	-- setting turning into a fight.
	local appliedAutoHide = false
	local unsubscribe: (() -> ())?
	unsubscribe = StateController.onChanged(function(snapshot)
		if appliedAutoHide or not snapshot.Loaded then
			return
		end
		appliedAutoHide = true
		if StateController.setting("AutoHideMenu") == true then
			dispatch({ Kind = "SET_COLLAPSED", Collapsed = true })
		end
		if unsubscribe then
			unsubscribe()
		end
	end)
end

return HubMenu
