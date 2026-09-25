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
def pin_anchor_bones():
    """Roblox's importer drops bones that deform nothing. Anchor bones (lightning / FX sockets: names in
    ANCHOR_PREFIXES) get the few vertices nearest them (within 4 cm, e.g. the web node sitting on them) bound 100%,
    so every anchor survives import. They move rigidly with their parent anyway, so nothing visibly deforms."""
    pref = tuple(globals().get("ANCHOR_PREFIXES", ()))
    if not pref: return
    from mathutils.kdtree import KDTree
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(PREFIX)]
    pts = []
    for o in meshes:
        for v in o.data.vertices: pts.append((o, v.index, o.matrix_world @ v.co))
    kd = KDTree(len(pts))
    for i, (_, _, co) in enumerate(pts): kd.insert(co, i)
    kd.balance()
    missing = []
    for b in rig.data.bones:
        if not b.name.startswith(pref): continue
        head = rig.matrix_world @ b.head_local
        parent = b.parent.name if b.parent else None
        def owns(i):                       # only vertices of meshes skinned to the anchor's own parent bone
            o, vi, _ = pts[i]
            g = o.vertex_groups.get(parent) if parent else None
            if g is None: return False
            try: return g.weight(vi) > 0.5
            except RuntimeError: return False
        hits = [h for h in kd.find_range(head, 0.04) if owns(h[1])][:6]
        if not hits:
            near = [h for h in kd.find_n(head, 400) if owns(h[1])]
            hits = near[:1]
        if not hits:
            print("ANCHOR skipped (no mesh on its parent):", b.name); continue
        for co, i, d in hits:
            o, vi, _ = pts[i]
            for g in list(o.vertex_groups):
                try: g.remove([vi])
                except RuntimeError: pass
            vg = o.vertex_groups.get(b.name) or o.vertex_groups.new(name=b.name)
            vg.add([vi], 1.0, 'REPLACE')
            if not any(m.type == 'ARMATURE' for m in o.modifiers): o.modifiers.new("Armature", 'ARMATURE').object = rig
        if hits[0][2] > 0.04: missing.append(b.name)
    print("ANCHORS pinned", sum(1 for b in rig.data.bones if b.name.startswith(pref)), "far:", missing)
def export_static():
    skin_bone_parented()
    pin_anchor_bones()
    bake_vertex_colors()
    _select()
    fp = os.path.join(OUT_DIR, f"{NAME}.fbx")
    bpy.ops.export_scene.fbx(filepath=fp, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             bake_anim=False, mesh_smooth_type='FACE', colors_type='SRGB')
    print("EXPORTED", fp)
def export_action(action):
    skin_bone_parented()
    pin_anchor_bones()
    bake_vertex_colors()
    _select()
    fp = os.path.join(OUT_DIR, f"{NAME}_{action}.fbx")
    bpy.ops.export_scene.fbx(filepath=fp, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                             mesh_smooth_type='FACE', colors_type='SRGB')
    print("EXPORTED", fp)
