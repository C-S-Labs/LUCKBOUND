--!strict
-- THE UNIVERSAL MENU (SIGIL): a small ring, top-right, holding only what is
-- not a place in the world -- Party, Settings and Codes. (Party was tried as
-- its own ring first and was too easy to miss; owner, 2026-09-29.) Panels themselves are still
-- the HubMenu's until the full-screen rebuild.

local Players = game:GetService("Players")

local HubMenu = require(script.Parent.HubMenu)
local Sigil = require(script.Parent.Sigil.Sigil)

local UniversalMenu = {}

function UniversalMenu.init(): ()
	local gui = Instance.new("ScreenGui")
	gui.Name = "LuckboundUniversalMenu"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.DisplayOrder = 6
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")

	Sigil.menu(gui, {
		{
			text = "Settings",
			onClick = function()
				HubMenu.open("SETTINGS")
			end,
		},
		{
			text = "Codes",
			onClick = function()
				HubMenu.open("CODES")
			end,
		},
	})

	HubMenu.follow(gui)
end

return UniversalMenu
