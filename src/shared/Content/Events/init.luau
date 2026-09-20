--!strict
-- Live-event registry. Adding an event = adding one file in this folder.
-- No System changes, ever. Build spec §1 prime directive, §4.2 for scope.
--
-- An event is the game happening TO the player rather than because of them:
-- the sky changes, the hub reacts, and everyone sees the same thing at the
-- same time. What an event may declare is deliberately bounded -- a scope, a
-- length, an announcement, a lighting palette and a sky layer -- so that
-- "author a new event" stays a data change rather than a code change.

local registry: { [string]: any } = {}

for _, module in script:GetChildren() do
	if module:IsA("ModuleScript") then
		local event = require(module) :: any
		assert(registry[event.Id] == nil, `duplicate event Id: {event.Id}`)
		registry[event.Id] = event
	end
end

return registry
