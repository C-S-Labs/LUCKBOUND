# FBX export for Roblox Studio (one static mesh+rig file, then one file per action).
# Studio import: File > Import 3D > the FBX; rig becomes an AnimationController/Humanoid model, each action FBX
# imports as an animation (Animation Editor > Import > From FBX). Names: <Name>.fbx and <Name>_<Action>.fbx.
import bpy, os
def _select():
    for o in bpy.data.objects:
        o.select_set(o == rig or (o.type == 'MESH' and o.name.startswith(PREFIX)))
    bpy.context.view_layer.objects.active = rig
def bake_vertex_colors():
    """Roblox MeshParts take ONE colour per part: bake every face's material colour into a vertex-colour layer
    (same as the chunk kits), so the imported model keeps its plate / trim / glow colours."""
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.startswith(PREFIX): continue
        me = o.data
        for a in [a for a in me.color_attributes if a.name == "Col"]: me.color_attributes.remove(a)
        col = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
        for poly in me.polygons:
            m = me.materials[poly.material_index] if poly.material_index < len(me.materials) else None
            c = (0.8, 0.8, 0.8, 1.0)
            if m is not None:
                b = m.node_tree.nodes.get("Principled BSDF") if m.use_nodes and m.node_tree else None
                c = tuple(b.inputs["Base Color"].default_value) if b else tuple(m.diffuse_color)
            for li in poly.loop_indices:
                col.data[li].color = c            # linear -> the FBX writer stores it; importer shows it as vertex colour
        me.color_attributes.active_color = col
def skin_bone_parented():
    """Meshes PARENTED to a bone (the boss's lance, its blade halves, the halo...) import into Roblox as static parts
    that ignore animation. Convert each into a SKINNED mesh bound 100% to that bone, so it follows the rig."""
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.startswith(PREFIX) or o.parent_type != 'BONE' or o.parent is None: continue
        arm, bone = o.parent, o.parent_bone
        mw = o.matrix_world.copy()
        o.parent_type = 'OBJECT'; o.parent = arm; o.matrix_world = mw
        vg = o.vertex_groups.get(bone) or o.vertex_groups.new(name=bone)
        vg.add(range(len(o.data.vertices)), 1.0, 'REPLACE')
        if not any(m.type == 'ARMATURE' for m in o.modifiers):
            o.modifiers.new("Armature", 'ARMATURE').object = arm
        print("SKINNED", o.name, "->", bone)
def export_static():
    skin_bone_parented()
    bake_vertex_colors()
    _select()
    fp = os.path.join(OUT_DIR, f"{NAME}.fbx")
    bpy.ops.export_scene.fbx(filepath=fp, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             bake_anim=False, mesh_smooth_type='FACE', colors_type='SRGB')
    print("EXPORTED", fp)
def export_action(action):
    skin_bone_parented()
    bake_vertex_colors()
    _select()
    fp = os.path.join(OUT_DIR, f"{NAME}_{action}.fbx")
    bpy.ops.export_scene.fbx(filepath=fp, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                             mesh_smooth_type='FACE', colors_type='SRGB')
    print("EXPORTED", fp)
