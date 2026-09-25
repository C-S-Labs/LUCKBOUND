# PHASE 2 pose: the phase-1 duelist stance (lance levelled, fingers gripping), armour shed, wings fanned wide, lance opened.
exec(open(HERE + r"\ws_pose.py").read())
for o in PARTS:
    if "_Break" in o.name:
        o.hide_render = True
if "wings_open" in globals():
    wings_open(1.0)
if "lance_open" in globals():
    lance_open(1.0)
bpy.context.view_layer.update()
