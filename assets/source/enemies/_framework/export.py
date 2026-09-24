# FBX export for Roblox Studio (one static mesh+rig file, then one file per action).
# Studio import: File > Import 3D > the FBX; rig becomes an AnimationController/Humanoid model, each action FBX
# imports as an animation (Animation Editor > Import > From FBX). Names: <Name>.fbx and <Name>_<Action>.fbx.
import bpy, os
def _select():
    for o in bpy.data.objects:
        o.select_set(o == rig or (o.type == 'MESH' and o.name.startswith(PREFIX)))
    bpy.context.view_layer.objects.active = rig
def export_static():
    _select()
    fp = os.path.join(OUT_DIR, f"{NAME}.fbx")
    bpy.ops.export_scene.fbx(filepath=fp, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             bake_anim=False, mesh_smooth_type='FACE')
    print("EXPORTED", fp)
def export_action(action):
    _select()
    fp = os.path.join(OUT_DIR, f"{NAME}_{action}.fbx")
    bpy.ops.export_scene.fbx(filepath=fp, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                             mesh_smooth_type='FACE')
    print("EXPORTED", fp)
