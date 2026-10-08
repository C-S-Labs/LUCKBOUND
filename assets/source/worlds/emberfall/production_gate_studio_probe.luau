--!strict
-- Isolated manually invoked Play-client probe; never production content.
local Probe = {}
function Probe.run(assetUri: string, parent: Instance): any
	local service = game:GetService("AssetService")
	local folder = Instance.new("Folder")
	folder.Name = "EmberfallGateClientOnly"
	folder.Parent = parent
	local results = {}
	local start = os.clock()
	for i = 1, 5 do
		local ok, result = pcall(function()
			local editable =
				service:CreateEditableMeshAsync(Content.fromUri(assetUri), { FixedSize = true })
			assert(editable, "editable allocation returned nil")
			local colour = if i <= 2
				then Color3.fromRGB(70, 102, 33)
				elseif i == 3 then Color3.fromRGB(122, 99, 38)
				else Color3.fromRGB(15, 13, 10)
			for _, id in editable:GetColors() do
				editable:SetColor(id, colour)
			end
			local mesh = service:CreateMeshPartAsync(Content.fromObject(editable))
			mesh.Anchored, mesh.CanCollide = true, false
			mesh.Color = Color3.new(1, 1, 1)
			mesh.CFrame = CFrame.new(5000 + (i - 1) * 256, 160, 500)
				* CFrame.Angles(0, -math.rad((i - 1) % 4 * 90), 0)
			mesh.Parent = folder
			return {
				vertices = #editable:GetVertices(),
				faces = #editable:GetFaces(),
				colors = #editable:GetColors(),
			}
		end)
		table.insert(results, {
			ok = ok,
			value = if ok then result else nil,
			err = if not ok then tostring(result) else nil,
		})
	end
	return { copies = results, seconds = os.clock() - start, folder = folder }
end
return Probe
