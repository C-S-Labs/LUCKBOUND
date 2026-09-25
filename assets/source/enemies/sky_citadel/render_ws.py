import bpy, sys
from mathutils import Vector
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
exec(open(HERE + r"\winged_sentinel.py").read())
out = HERE
sc = bpy.context.scene
LANCE = "--lance" in sys.argv
if LANCE:
    exec(open(HERE + r"\ws_lance.py").read())
pose = "--pose" in sys.argv or "--p2" in sys.argv
pose = pose or "--idle" in sys.argv or "--guard" in sys.argv
tag = ("p2" if "--p2" in sys.argv else ("idle" if "--idle" in sys.argv else ("guard2h" if "--guard" in sys.argv else ("pose" if pose else "rest")))) + ("_lance" if LANCE else "")
if "--anim" in sys.argv:
    exec(open(out + r"\ws_anim_p2.py").read())
    tag = "p2anim"
    pose = True
elif pose:
    exec(open(out + (r"\ws_pose_p2.py" if tag.startswith("p2") else (r"\ws_pose_idle.py" if tag.startswith("idle") else (r"\ws_pose_guard2h.py" if tag.startswith("guard") else r"\ws_pose.py")))).read())
views = {"34": (-4.4, -7.6, 2.9), "front": (0, -8.8, 2.4), "side": (8.8, 0, 2.4), "back": (3.6, 8.0, 3.2)}
if "--lanceonly" in sys.argv:
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and o.name.startswith("WingedSentinel_") and not o.name.startswith("WingedSentinel_Lance"): o.hide_render = True
    sc.objects["PlayerRef"].hide_render = True
    views = {"lance_side": (7.4, -0.9, 2.8), "lance_top": (-4.6, -1.0, 4.0), "lance_head": (0.3, -3.3, 1.95)}
elif "--grip" in sys.argv:
    import os as _o
    gh = rig.matrix_world @ rig.pose.bones[_o.environ.get("GRIPBONE", "RightHand")].head
    views = {"grip_a": tuple(gh + Vector((-0.9, -0.9, 0.5))), "grip_b": tuple(gh + Vector((0.2, -1.1, -0.3))), "grip_c": tuple(gh + Vector((0.9, -0.7, 0.3)))}
elif "--p2lance" in sys.argv:
    tip = rig.matrix_world @ rig.pose.bones["LanceBladeL"].tail
    views = {"p2lance_a": tuple(tip + Vector((-2.2, -1.2, 1.5))), "p2lance_b": tuple(tip + Vector((1.8, -1.8, 1.0)))}
    gh = tip
elif "--head" in sys.argv: views = {"head34": (-1.3, -2.2, 3.7), "headside": (2.4, -0.3, 3.5)}
elif "--quick" in sys.argv: views = {"34": views["34"], "back": views["back"]}
if "--anim" in sys.argv:
    views = {}
    for f in (1, 18, 30, 38, 44, 60):
        sc.frame_set(f); cam.location = (-4.4, -7.6, 2.9); _look(cam)
        sc.render.filepath = f"{RENDER_DIR}\ws_p2anim_f{f:02d}.png"; bpy.ops.render.render(write_still=True)
for k, loc in views.items():
    cam.location = loc; _look(cam, tuple(gh) if (k.startswith('grip') or k.startswith('p2lance')) else (0, -0.05, 3.2) if k.startswith('head') else (((-0.66, -2.0, 1.3) if k == 'lance_head' else (-0.66, -0.75, 1.3)) if k.startswith('lance') else (0, 0, 1.8)))
    sc.render.filepath = f"{RENDER_DIR}\ws_{tag}_{k}.png"
    bpy.ops.render.render(write_still=True)
if not pose and not LANCE:
    bpy.ops.wm.save_as_mainfile(filepath=OUT_DIR + r"\boss_winged_sentinel.blend")
