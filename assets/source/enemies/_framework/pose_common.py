# Body-agnostic pose helpers (every body type): collision counts between pieces and grounding.
# Joint rules are NOT here - they live in the body profile (bodies/<body>.py), e.g. humanoid elbows/shoulders.
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
PREFIX = globals().get("PREFIX") or NAME + "_"
P = rig.pose.bones
RW = rig.matrix_world
BODY_PIECES = globals().get("BODY_PIECES", ("Torso", "Waist", "LegLeft", "LegRight"))   # a profile may override
def _upd(): bpy.context.view_layer.update()
def _tree(pn):
    o = bpy.data.objects.get(PREFIX + pn)
    if o is None: return None
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); m = oe.to_mesh()
    t = BVHTree.FromPolygons([o.matrix_world @ v.co for v in m.vertices], [tuple(p.vertices) for p in m.polygons])
    oe.to_mesh_clear(); return t
def hits(a, others=None):
    _upd(); ta = _tree(a); n = 0
    for b in (others or BODY_PIECES):
        tb = _tree(b)
        if ta and tb: n += len(ta.overlap(tb))
    return n
def ground(extra=()):
    _upd(); dg = bpy.context.evaluated_depsgraph_get(); minz = 1e9
    for o in list(PARTS) + list(extra):
        if o.hide_render or "_Break" in o.name: continue
        oe = o.evaluated_get(dg); m = oe.to_mesh()
        if len(m.vertices): minz = min(minz, min((o.matrix_world @ v.co).z for v in m.vertices))
        oe.to_mesh_clear()
    r_ = P["HumanoidRootNode"]; r_.location = r_.location + Vector((0, -minz, 0)); _upd()
# ---------------- joint sanity (natural hinges, wrists, shoulders) ----------------
HINGES = {"LeftLowerArm": "arm", "RightLowerArm": "arm", "LeftLowerLeg": "leg", "RightLowerLeg": "leg"}
