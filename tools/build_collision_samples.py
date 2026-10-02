"""Blender feasibility sample, not a production SC regeneration.

Capture simple authored boxes and floor prisms from two existing builders.
Writes lightweight collision data and optional review FBX; never changes kits.
"""
import importlib.util
import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'assets/source/worlds/sky_citadel/build_sky_citadel_kit.py'
spec = importlib.util.spec_from_file_location('collision_sample_source', path)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
boxes, floors = [], []
original_box, original_slab = kit.box, kit.slab


def capture_box(p, mat, cx, cy, cz, sx, sy, sz, rz=0, rx=0, ry=0):
    matrix = p.base @ kit.xf(cx, cy, cz, rz, rx, ry)
    # Exclude ambient props and fixtures removed from final structure geometry.
    before = len(p.verts)
    original_box(p, mat, cx, cy, cz, sx, sy, sz, rz, rx, ry)
    boxes.append({'Piece': p, 'Vertices': [tuple(v) for v in p.verts[before:]],
                  'Size': [sx, sz, sy], 'Matrix': matrix.copy()})


def capture_slab(p, mat, points, z0, z1):
    world = [tuple(p.base @ kit.Vector((x, y, z1))) for x, y in points]
    original_slab(p, mat, points, z0, z1)
    floors.append({'Piece': p, 'Points': world, 'Thickness': z1 - z0})


kit.box, kit.slab = capture_box, capture_slab
kit.REFINISH = False  # proxy intentionally omits visual bevel/detail passes
pieces = [kit.build_path_hoops(), kit.build_path_shattered()]


def roblox(point):
    return [round(point[0], 7), round(point[2], 7), round(-point[1], 7)]


def literal(value):
    if isinstance(value, dict):
        return '{' + ','.join(k + '=' + literal(v) for k, v in value.items()) + '}'
    if isinstance(value, list):
        return '{' + ','.join(map(literal, value)) + '}'
    return json.dumps(value)


result = {}
for piece in pieces:
    vertices = {tuple(round(float(c), 6) for c in v) for v in piece.verts}
    records = []
    for box in boxes:
        if box['Piece'] is not piece:
            continue
        if not all(tuple(round(float(c), 6) for c in v) in vertices for v in box['Vertices']):
            continue
        matrix = box['Matrix']
        # Convert Blender basis to Roblox +X,+Y,-Z while preserving handedness.
        records.append({'Kind': 'Box', 'Size': box['Size'],
                        'Position': roblox(matrix.translation),
                        'Right': roblox(matrix.col[0]),
                        'Up': roblox(matrix.col[2]),
                        'Back': [-v for v in roblox(matrix.col[1])]})
    for floor in floors:
        if floor['Piece'] is piece:
            records.append({'Kind': 'Floor', 'Points': [roblox(p) for p in floor['Points']],
                            'Thickness': floor['Thickness']})
    chunk_id = 'SC_' + piece.name.removeprefix('chunk_').upper()
    result[chunk_id] = records
output = ROOT / 'src/shared/Content/CollisionSamples.luau'
output.write_text('--!strict\n-- GENERATED experimental collision feasibility data; not production content.\nreturn ' + literal(result) + '\n', encoding='utf-8')
report = {key: {'AuthoredShapes': len(value),
                'Boxes': sum(row['Kind'] == 'Box' for row in value),
                'FloorPrisms': sum(row['Kind'] == 'Floor' for row in value)} for key, value in result.items()}
(ROOT / 'docs/benchmarks/collision_sample_authoring.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('COLLISION SAMPLE:', json.dumps(report))
