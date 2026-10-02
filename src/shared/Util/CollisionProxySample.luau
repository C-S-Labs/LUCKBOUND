--!strict
-- Materializes the small Blender-authored experiment only; never used by boot.
local Sample = {}
local function vector(value: any): Vector3
	return Vector3.new(value[1], value[2], value[3])
end
local function configure(part: BasePart, model: Model)
	part.Anchored = true
	part.CanCollide = true
	part.CanQuery = true
	part.CanTouch = false
	part.Transparency = 1
	part.Parent = model
end
local function triangle(a: Vector3, b: Vector3, c: Vector3, thickness: number, model: Model)
	local ab, ac, bc = b - a, c - a, c - b
	local ab2, ac2, bc2 = ab:Dot(ab), ac:Dot(ac), bc:Dot(bc)
	if ab2 > ac2 and ab2 > bc2 then
		c, a = a, c
	elseif ac2 > bc2 and ac2 > ab2 then
		a, b = b, a
	end
	ab, ac, bc = b - a, c - a, c - b
	local cross = ac:Cross(ab)
	if cross.Magnitude < 1e-6 then
		return
	end
	local right = cross.Unit
	local up = bc:Cross(right).Unit
	local back = bc.Unit
	local width = math.abs(ab:Dot(up))
	for _, spec in
		{
			{ a, b, right, back, math.abs(ab:Dot(back)) },
			{ a, c, -right, -back, math.abs(ac:Dot(back)) },
		}
	do
		if spec[5] < 1e-6 then
			continue
		end
		local wedge = Instance.new("WedgePart")
		wedge.Size = Vector3.new(thickness, width, spec[5])
		wedge.CFrame = CFrame.fromMatrix(
			(spec[1] + spec[2]) / 2 - Vector3.new(0, thickness / 2, 0),
			spec[3],
			up,
			spec[4]
		)
		configure(wedge, model)
	end
end

function Sample.build(name: string, definitions: any, parent: Instance): Model
	local model = Instance.new("Model")
	model.Name = name
	for _, definition in definitions do
		if definition.Kind == "Box" then
			local part = Instance.new("Part")
			part.Size = vector(definition.Size)
			part.CFrame = CFrame.fromMatrix(
				vector(definition.Position),
				vector(definition.Right),
				vector(definition.Up),
				vector(definition.Back)
			)
			configure(part, model)
		else
			local points = definition.Points
			for index = 2, #points - 1 do
				triangle(
					vector(points[1]),
					vector(points[index]),
					vector(points[index + 1]),
					definition.Thickness,
					model
				)
			end
		end
	end
	model.WorldPivot = CFrame.identity
	model.Parent = parent
	return model
end

return Sample
