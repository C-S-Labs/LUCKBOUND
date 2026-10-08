--!strict
-- Explicit Client command: bounded preload of this review's actual world assets.
local world = workspace.ExpeditionStage.EmberfallBatch2Review
local items = {}
for _, part in world:GetDescendants() do
	if part:IsA("MeshPart") then
		table.insert(items, part)
	end
end
workspace:SetAttribute("EmberfallBatch2PreloadStatus", "Running")
task.spawn(function()
	local results, failures = {}, {}
	game:GetService("ContentProvider"):PreloadAsync(items, function(id, status)
		results[id] = tostring(status)
		if status ~= Enum.AssetFetchStatus.Success then
			failures[id] = tostring(status)
		end
	end)
	local result = { parts = #items, results = results, failures = failures }
	workspace:SetAttribute(
		"EmberfallBatch2PreloadResult",
		game:GetService("HttpService"):JSONEncode(result)
	)
	workspace:SetAttribute("EmberfallBatch2PreloadStatus", "Finished")
end)
return "Bounded imported-world preload queued"
