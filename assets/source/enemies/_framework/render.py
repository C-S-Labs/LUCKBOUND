# Standard review renders for any enemy (EEVEE, AgX, 3-point light, pedestal, 2 m player reference block).
# Frames the camera from the enemy's real bounding box, so no per-enemy camera numbers are needed.
# Views: 34 / side / back / front (+ optional close-up via env CLOSE="cx,cy,cz;tx,ty,tz" relative to the enemy).
import bpy, bmesh, os
from mathutils import Vector
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x, sc.render.resolution_y = 1000, 1250
sc.view_settings.view_transform = 'AgX'
_w = bpy.data.worlds.new("W"); sc.world = _w; _w.use_nodes = True
_w.node_tree.nodes["Background"].inputs[0].default_value = (0.45, 0.5, 0.6, 1)
_w.node_tree.nodes["Background"].inputs[1].default_value = 0.3
bpy.context.view_layer.update()
_pts = [o.matrix_world @ Vector(c) for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(PREFIX) and not o.hide_render for c in o.bound_box]
_lo = Vector((min(p.x for p in _pts), min(p.y for p in _pts), min(p.z for p in _pts)))
_hi = Vector((max(p.x for p in _pts), max(p.y for p in _pts), max(p.z for p in _pts)))
T = (_lo + _hi) / 2
CD = max((_hi - _lo).length * 1.25, 3.0)
def _look(o, t): o.rotation_euler = (t - o.location).to_track_quat('-Z', 'Y').to_euler()
for n, off, e in (("Key", (-0.6, -0.8, 0.9), 350), ("Rim", (0.6, 0.6, 0.8), 300), ("Fill", (0.8, -0.5, 0.2), 80)):
    d = bpy.data.lights.new(n, 'AREA'); d.energy = e * (CD / 4) ** 2; d.size = 2 * CD / 4
    o = bpy.data.objects.new(n, d); sc.collection.objects.link(o); o.location = T + Vector(off) * CD; _look(o, T)
_ref = bpy.data.meshes.new("Ref"); b = bmesh.new(); bmesh.ops.create_cube(b, size=1)
bmesh.ops.scale(b, vec=(0.5, 0.28, 2.0), verts=b.verts); bmesh.ops.translate(b, vec=(0, 0, 1.0), verts=b.verts); b.to_mesh(_ref)
_ref.materials.append(mat("Ref", (0.9, 0.35, 0.3), 0, 0.7))
_r = bpy.data.objects.new("PlayerRef", _ref); sc.collection.objects.link(_r)
_r.location = (_hi.x + 0.6, T.y + 0.4, _lo.z if _lo.z > -0.5 else 0)
_g = bpy.data.meshes.new("G"); b = bmesh.new()
bmesh.ops.create_cone(b, cap_ends=True, segments=48, radius1=CD * 0.45, radius2=CD * 0.45, depth=0.05); b.to_mesh(_g)
_g.materials.append(mat("Ped", (0.45, 0.46, 0.5), 0, 0.8))
_go = bpy.data.objects.new("Ped", _g); sc.collection.objects.link(_go); _go.location = (T.x, T.y, -0.025)
_cd = bpy.data.cameras.new("C"); _cd.lens = 50
cam = bpy.data.objects.new("C", _cd); sc.collection.objects.link(cam); sc.camera = cam
_tag = os.environ.get("TAG", EID)
for k, off in (("34", (-0.55, -0.8, 0.35)), ("front", (0, -1, 0.2)), ("side", (0.95, 0.05, 0.15)), ("back", (0.45, 0.85, 0.4))):
    cam.location = T + Vector(off) * CD; _look(cam, T)
    sc.render.filepath = os.path.join(RENDER_DIR, f"{_tag}_{k}.png"); bpy.ops.render.render(write_still=True)
_close = os.environ.get("CLOSE")
if _close:
    c_, t_ = [Vector([float(v) for v in part.split(",")]) for part in _close.split(";")]
    cam.location = T + c_; _look(cam, T + t_)
    sc.render.filepath = os.path.join(RENDER_DIR, f"{_tag}_close.png"); bpy.ops.render.render(write_still=True)
