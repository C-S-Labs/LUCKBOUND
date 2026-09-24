# Sky Citadel chunk REFINISH test (owner request 2026-09-24): does a finish pass close the style gap between the
# low-poly chunks and the mid-poly enemies/weapons, without raising the chunks to mid-poly?
#   blender -b assets/source/worlds/sky_citadel/sky_citadel_kit.blend --python refinish_test.py -- chunk_a chunk_b ...
# Finish pass (non-destructive, on copies):
#   1. materials: same smooth, glossy finish as the enemies (kit palette kept: citadel white / alloy / violet / azure)
#   2. bevelled edges (angle-limited) whose bevel faces take the VIOLET trim material -> enemy-style trim lines
#   3. cyan glow seams: large dark-alloy wall panels get an inset border in the azure neon (enemy glow channels)
# Renders each chunk BEFORE / AFTER with the Winged Sentinel (idle pose, to scale) standing on its deck.
import bpy, bmesh, sys, os, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
ENEMIES = os.path.join(REPO, "assets", "source", "enemies")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
CHUNKS = argv or ["chunk_entry", "chunk_path_colonnade", "chunk_boss_clearing"]
OUT = os.path.join(HERE, "renders", "refinish")
os.makedirs(OUT, exist_ok=True)
STUDS_PER_M = 2.8                              # enemy scripts are in metres; the kit is in studs

# ---------------- 1. glossy materials ----------------
GLOSS = {"SC_CitadelWhite": (0.0, 0.2), "SC_PaleAlloy": (0.4, 0.2), "SC_DeepAlloy": (0.6, 0.18),
         "SC_HullSlate": (0.35, 0.25), "SC_SunGold": (1.0, 0.15), "SC_CitadelViolet": (0.35, 0.18)}
def glossy(m):
    if not m or not m.use_nodes: return
    b = m.node_tree.nodes.get("Principled BSDF")
    if b is None: return
    met, rough = GLOSS.get(m.name, (None, None))
    if met is None: return
    b.inputs["Metallic"].default_value = met; b.inputs["Roughness"].default_value = rough
    if "Coat Weight" in b.inputs: b.inputs["Coat Weight"].default_value = 0.6
def refinish(src):
    o = src.copy(); o.data = src.data.copy(); o.name = src.name + "_refinished"
    bpy.context.scene.collection.objects.link(o)
    mats = [m.name for m in o.data.materials]
    newmats = []
    for m in o.data.materials:
        g = m.copy(); g.name = m.name + "_Gloss"; glossy(g); newmats.append(g)
    for i, g in enumerate(newmats): o.data.materials[i] = g
    VIOLET = mats.index("SC_CitadelViolet"); NEON = mats.index("SC_AzureNeon"); DEEP = mats.index("SC_DeepAlloy")
    # ---------------- 3. glow seams on big dark wall panels ----------------
    bm = bmesh.new(); bm.from_mesh(o.data)
    WHITE = mats.index("SC_CitadelWhite"); PALE = mats.index("SC_PaleAlloy"); SLATE = mats.index("SC_HullSlate")
    walls = [f for f in bm.faces if f.material_index in (DEEP, SLATE, PALE) and abs(f.normal.z) < 0.3 and f.calc_area() > 120]
    if walls:                                                       # wall panels: recessed, cyan glow border
        r = bmesh.ops.inset_individual(bm, faces=walls, thickness=0.45, depth=-0.12)
        for f in r["faces"]: f.material_index = NEON
    decks = [f for f in bm.faces if f.normal.z > 0.9 and f.calc_area() > 300]
    if decks:                                                       # big deck slabs: violet-edged plates
        r = bmesh.ops.inset_individual(bm, faces=decks, thickness=0.6, depth=0.0)
        for f in r["faces"]: f.material_index = VIOLET
    # only the edges that read at play distance get trim: sharp (> 40 deg) AND long (> 4 studs)
    bw = bm.edges.layers.float.get("bevel_weight_edge") or bm.edges.layers.float.new("bevel_weight_edge")
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(40) and e.calc_length() > 4.0: e[bw] = 1.0
    bm.to_mesh(o.data); bm.free()
    # ---------------- 2. bevels with violet trim ----------------
    bv = o.modifiers.new("Trim", 'BEVEL'); bv.limit_method = 'WEIGHT'
    bv.width = 0.6; bv.segments = 1; bv.harden_normals = True; bv.material = VIOLET
    o.data.shade_smooth() if hasattr(o.data, "shade_smooth") else None
    return o
def tris(o):
    dg = bpy.context.evaluated_depsgraph_get(); m = o.evaluated_get(dg).to_mesh()
    n = sum(len(p.vertices) - 2 for p in m.polygons); o.evaluated_get(dg).to_mesh_clear(); return n

# ---------------- the boss, to scale ----------------
def load_boss():
    G = {"__name__": "boss"}
    FW = os.path.join(ENEMIES, "_framework"); H = os.path.join(ENEMIES, "sky_citadel")
    G.update(FW=FW, HERE=H, OUT_DIR=OUT, RENDER_DIR=OUT, bpy=bpy)
    before = set(bpy.data.objects)
    exec(open(os.path.join(H, "winged_sentinel.py")).read(), G)
    exec(open(os.path.join(H, "ws_lance.py")).read(), G)
    G["G"] = G; G["BODY"] = "humanoid"
    exec(open(os.path.join(H, "ws_pose_idle.py")).read(), G)
    rig = G["rig"]; rig.scale = (STUDS_PER_M,)*3
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.type == "MESH" and ("_Break" in o.name or "Beam" in o.name): o.hide_render = True
    return rig, new
def deck_point(o):
    """The main walkable deck: the most common first-hit height over a grid (ignores rails, roofs, props)."""
    dg = bpy.context.evaluated_depsgraph_get(); m = o.evaluated_get(dg).to_mesh()
    t = BVHTree.FromPolygons([o.matrix_world @ v.co for v in m.vertices], [tuple(p.vertices) for p in m.polygons])
    o.evaluated_get(dg).to_mesh_clear()
    c = o.matrix_world.translation; hits_ = []
    for i in range(-6, 7):
        for j in range(-6, 7):
            h = t.ray_cast(Vector((c.x + i*10, c.y + j*10, c.z + 300)), Vector((0, 0, -1)))
            if h[0] is not None and h[1].z > 0.9: hits_.append(h[0])
    from collections import Counter
    zmode = Counter(round(p.z) for p in hits_).most_common(1)[0][0]
    cand = sorted((p for p in hits_ if round(p.z) == zmode), key=lambda p: (p.xy - c.xy).length)
    return cand[0]
# ---------------- render ----------------
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
sc.view_settings.view_transform = 'AgX'
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.68, 0.9, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.5; sun.rotation_euler = (math.radians(50), 0, math.radians(35))
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 35
def look(o, t): o.rotation_euler = (Vector(t) - o.location).to_track_quat('-Z', 'Y').to_euler()
keep = set(CHUNKS)
for o in bpy.data.objects:
    if o.type == "MESH" and o.name not in keep: o.hide_render = True
rig, boss = load_boss()
sc.camera = cam
for o in bpy.data.objects:
    if o.name.startswith(("PlayerRef", "Ped", "Ground")) or (o.type == "MESH" and o.name.startswith("WingedSentinel") is False and o.name not in keep and not o.name.endswith("_refinished")): o.hide_render = True
for ch in CHUNKS:
    src = bpy.data.objects[ch]; ref = refinish(src)
    print(f"REFINISH {ch}: {tris(src)} -> {tris(ref)} tris")
    ref.hide_render = True
    p = deck_point(src)
    for variant, obj in (("before", src), ("after", ref)):
        for o in (src, ref): o.hide_render = o is not obj
        rig.location = p + Vector((0, 0, 0.05))
        for view, off, tgt in (("wide", Vector((-70, -95, 55)), p + Vector((0, 0, 8))), ("close", Vector((-14, -20, 9)), p + Vector((0, 0, 5)))):
            cam.location = p + off; look(cam, tgt)
            sc.render.filepath = os.path.join(OUT, f"{ch}_{variant}_{view}.png"); bpy.ops.render.render(write_still=True)
    src.hide_render = True; ref.hide_render = True
print("REFINISH done ->", OUT)
