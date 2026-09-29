# LUCKBOUND - The Ascendant's spell orb (manifest "extras", after the staff). A glowing sphere cradled between the
# crescent (front blade) and the back-horn, where the Sanctum Staff casts its ranged spells from. Its own mesh piece
# "StaffOrb" (so Studio can tween its glow), skinned to Weapon_R, with a VFX_Orb socket bone at its centre.
# Positions are in the staff's own frame (haft = local +Z, the crescent bows toward local +Y), the same frame
# the_ascendant_staff.py builds in, so this also works on a hand-edited copy of the mesh.
import bpy, bmesh
from mathutils import Vector, Matrix
HEAD_U, ORB_UP, ORB_R = 1.55, 0.42, 0.095      # socket height on the haft, orb height above the socket, radius
_b = rig.data.bones["Weapon_R"]; _RW = rig.matrix_world
_p0 = _RW @ _b.head_local; _z = (_RW.to_3x3() @ (_b.tail_local - _b.head_local)).normalized()
_x = Vector((0, 0, 1)).cross(_z)
if _x.length < 1e-4: _x = Vector((1, 0, 0))
_x.normalize(); _y = _z.cross(_x)
_F = Matrix((_x, _y, _z)).transposed().to_4x4(); _F.translation = _p0
_C = _F @ Vector((0.0, 0.0, HEAD_U + ORB_UP))
_name = f"{NAME}_StaffOrb"
if _name not in bpy.data.objects:
    _bm = bmesh.new(); bmesh.ops.create_icosphere(_bm, subdivisions=2, radius=ORB_R)
    for _v in _bm.verts: _v.co += _C
    _me = bpy.data.meshes.new(_name); _bm.to_mesh(_me); _bm.free()
    _glow = next((m for m in bpy.data.materials if "glow" in m.name.lower()), None)
    _donor = bpy.data.objects.get(f"{NAME}_StaffGlow")
    if _donor is not None and len(_donor.data.materials):
        for _m in _donor.data.materials: _me.materials.append(_m)          # same slot layout as every other piece
        _gi = next((i for i, m in enumerate(_donor.data.materials) if m and "glow" in m.name.lower()), len(_donor.data.materials) - 1)
    else:
        if _glow: _me.materials.append(_glow)
        _gi = 0
    for _p in _me.polygons: _p.material_index = _gi; _p.use_smooth = False
    _o = bpy.data.objects.new(_name, _me)
    _o.vertex_groups.new(name="Weapon_R").add(list(range(len(_me.vertices))), 1.0, 'REPLACE')
    bpy.context.scene.collection.objects.link(_o); _o.parent = rig; _o.matrix_parent_inverse = _RW.inverted()
    _o.modifiers.new("Armature", 'ARMATURE').object = rig
    if "PARTS" in globals(): PARTS.append(_o)
    if "STAFF_OBJS" in globals(): STAFF_OBJS.append(_o)
    bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
    if "VFX_Orb" not in rig.data.edit_bones:
        _eb = rig.data.edit_bones.new("VFX_Orb"); _Mi = _RW.inverted()
        _eb.head = _Mi @ _C; _eb.tail = _Mi @ (_C + _z*0.06); _eb.parent = rig.data.edit_bones["Weapon_R"]
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"ORB {_name}: {len(_me.polygons)} tris at staff-local (0, 0, {HEAD_U + ORB_UP:.2f})")
