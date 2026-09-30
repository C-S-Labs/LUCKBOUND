"""Blender check: multipart stress cases and actual FBX names, triangle budgets and alignment.

Run: blender -b --factory-startup --python tests/validate_ethereal_exports.py
"""
import json
import pathlib
import runpy
import bpy

ROOT = pathlib.Path(__file__).resolve().parents[1]
KIT = ROOT / "assets/source/worlds/ethereal_scape/build_ethereal_scape_kit.py"
api = runpy.run_path(str(KIT), run_name="export_validation")
G = api["G"]
mats = api["materials"]()
p = G.Piece("ES_TEST_ASSEMBLY", 128, [])
p.export_group = "temple"
for i in range(2501):
    G.box(p, "TempleIvory", i % 50, i // 50, 0, 0.5, 0.5, 1)
objects, metadata = api["split_piece"](p, mats, bpy.context.scene.collection)
assert len(objects) >= 4
assert sum(q["Triangles"] for q in metadata) == p.tri_count() == 30012
assert all(q["Triangles"] < api["TRI_LIMIT"] for q in metadata)
assert len({q["AssetKey"] for q in metadata}) == len(metadata)
# A grouped primitive above the limit must also split without dropping faces.
too_big = G.Piece("ES_TEST_OVERSIZED", 128, [])
too_big.group(True)
for i in range(1000):
    G.box(too_big, "TempleIvory", i, 0, 0, 1, 1, 1)
_, large_metadata = api["split_piece"](too_big, mats, bpy.context.scene.collection)
assert len(large_metadata) == 2
assert sum(q["Triangles"] for q in large_metadata) == 12000
assert all(q["Triangles"] < api["TRI_LIMIT"] for q in large_metadata)
print("PASS: 30k assembly and 12k grouped primitive split losslessly")

export_dir = ROOT / "assets/export/worlds/ethereal_scape"
parts = json.loads((export_dir / "ethereal_scape_structure.json").read_text())
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
bpy.ops.import_scene.fbx(filepath=str(export_dir / "ethereal_scape_structure.fbx"))
meshes = {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}
expected = {s["id"] for s in api["P"].PIECES}
expected.update(q["Object"] for assembly in parts.values() for q in assembly)
assert set(meshes) == expected, (set(meshes) - expected, expected - set(meshes))
for obj in meshes.values():
    obj.data.calc_loop_triangles()
    assert len(obj.data.loop_triangles) < api["TRI_LIMIT"], obj.name
    assert all(abs(s-1) < 1e-5 for s in obj.scale), (obj.name, obj.scale)
    assert obj.data.color_attributes, f"{obj.name}: vertex colours lost"
for assembly in parts.values():
    for q in assembly:
        obj = meshes[q["Object"]]
        assert len(obj.data.loop_triangles) == q["Triangles"]
        lo = [min(v.co[i] for v in obj.data.vertices) for i in range(3)]
        hi = [max(v.co[i] for v in obj.data.vertices) for i in range(3)]
        for i, axis in enumerate("XYZ"):
            assert abs(hi[i]-lo[i]-q["Size"+axis]) < 0.01, (obj.name, axis, "size")
            origin = (G.KEEL_BOTTOM+G.CROWN_TOP)/2 if axis == "Y" else 0
            assert abs((hi[i]+lo[i])/2-origin-q["Offset"+axis]) < 0.01, (obj.name, axis, "offset")
print(f"PASS: {len(meshes)} structure meshes round-trip with matching colours, units, bounds and multipart offsets")

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
bpy.ops.import_scene.fbx(filepath=str(export_dir / "ethereal_scape_props.fbx"))
props = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert len(props) == len(api["PR"].KINDS)
for obj in props:
    obj.data.calc_loop_triangles()
    assert len(obj.data.loop_triangles) < api["TRI_LIMIT"], obj.name
print(f"PASS: all {len(props)} prop meshes remain under the per-mesh limit")
