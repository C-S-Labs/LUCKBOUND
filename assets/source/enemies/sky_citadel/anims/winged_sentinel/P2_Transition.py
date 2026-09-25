# Phase-2 transition (60 f, markers ArmourBreak / LanceIgnite / P2Start). See ws_anim_p2.py.
exec(open(HERE + r"\ws_anim_p2.py").read())
for o in bpy.data.objects:
    if "_Break" in o.name and o.animation_data:
        o.animation_data_clear(); o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
