--!strict
-- CODE REDEMPTION RULES. Pure, so every branch is testable without a player.
--
-- The server is the only thing that may call `redeem` for real: it reads the
-- profile, it decides, it awards. The client's code box does no validation at
-- all beyond emptiness -- it sends the string and shows what comes back.
-- Anything else would tell a would-be brute-forcer which half of their guess
-- was wrong (CLAUDE.md rule 5).

local Result = require(script.Parent.Result)

local CodeCore = {}

--- Case, spaces and punctuation do not matter. A player retyping a code off a
--- video should not fail on a hyphen.
function CodeCore.normalise(input: any): string
	if type(input) ~= "string" then
		return ""
	end
	return (string.upper(input):gsub("[^%w]", ""))
end

--- The definition a player's input names, or nil.
function CodeCore.find(codes: any, input: any): any?
	local wanted = CodeCore.normalise(input)
	if wanted == "" then
		return nil
	end
	for _, definition in codes do
		if CodeCore.normalise(definition.Code) == wanted then
			return definition
		end
	end
	return nil
end

function CodeCore.hasRedeemed(profile: any, codeId: string): boolean
	local redeemed = profile.RedeemedCodes
	if type(redeemed) ~= "table" then
		return false
	end
	return redeemed[codeId] ~= nil
end

--- Decides a redemption. Returns Result.ok{ Id, Fate, Message } or an error
--- whose message is written to be READ BY A PLAYER -- these strings go
--- straight to the screen.
---
--- Does not mutate the profile: the caller records the redemption, so the
--- decision and the write stay separable and the decision stays testable.
function CodeCore.redeem(codes: any, profile: any, input: any, now: number, config: any): any
	if not config.Codes.Enabled then
		return Result.err("Codes are closed right now.")
	end

	if type(input) ~= "string" then
		return Result.err("Enter a code.")
	end

	if #input > config.Codes.MaxLength then
		-- Length is checked on the RAW string, before normalising: the cap
		-- exists to stop a megabyte arriving over the wire, and normalising
		-- first would mean doing the work the cap is meant to avoid.
		return Result.err("That code is too long.")
	end

	local normalised = CodeCore.normalise(input)
	if normalised == "" then
		return Result.err("Enter a code.")
	end

	local definition = CodeCore.find(codes, input)
	if not definition then
		return Result.err("That code is not valid.")
	end

	if definition.ExpiresAt and now >= definition.ExpiresAt then
		return Result.err("That code has expired.")
	end

	if CodeCore.hasRedeemed(profile, definition.Id) then
		return Result.err("You have already redeemed that code.")
	end

	return Result.ok({
		Id = definition.Id,
		Fate = definition.Fate,
		Message = definition.Message,
	})
end

--- Records a successful redemption on a profile. Separate from `redeem` on
--- purpose: one decides, one writes.
function CodeCore.record(profile: any, codeId: string, now: number): ()
	if type(profile.RedeemedCodes) ~= "table" then
		profile.RedeemedCodes = {}
	end
	profile.RedeemedCodes[codeId] = now
end

return CodeCore
