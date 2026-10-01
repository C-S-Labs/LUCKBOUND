"""Export the owner's live scene, never rebuild or save it. Run on Blender's main thread.

Bake world transforms/modifiers into temporary objects; preserve original objects,
selection, active object and mesh data. Runtime positions use the walk-plane frame.
"""
import bpy
import json
import math
import re
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'assets/export/worlds/ethereal_scape'


def lua(value):
    if isinstance(value, dict):
        return '{' + ','.join('[' + json.dumps(k) + ']=' + lua(v) for k, v in value.items()) + '}'
    if isinstance(value, (list, tuple)):
        return '{' + ','.join(lua(v) for v in value) + '}'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, float):
        assert math.isfinite(value)
        return format(value, '.7g')
    return json.dumps(value)


def deliver():
    chunk_path = ROOT / 'src/shared/Content/Chunks/EtherealScape.luau'
    text = chunk_path.read_text(encoding='utf-8')
    ids = re.findall(r'Id = "(ES_[A-Z0-9_]+)"', text.split('-- LIVE DELIVERY')[0])
    room_id = 'ES_SHRINE_MINIBOSS_ROOM'
    origins = {n: bpy.data.objects[n].matrix_world.translation.copy() for n in ids}
    # The imported grounds part has a bbox pivot; the actual tile centre is unchanged.
    origins['ES_SANCTUM'] = Vector((0, 1350, 0))
    origins[room_id] = bpy.data.objects[room_id].matrix_world.translation.copy()
    ordered = sorted(ids, key=len, reverse=True)
    def owner(o):
        p = o
        while p:
            if p.name == room_id:
                return room_id
            p = p.parent
        if o.name.startswith('ES_SHRINE_RETURN') or o.name.startswith('ES_SHRINE_VAULT'):
            return room_id
        if o.name.startswith('ES_SHRINE_PORTAL'):
            return 'ES_CAP_SEALED_SHRINE'
        return next((n for n in ordered if o.name == n or o.name.startswith(n + '_')), None)
    def point(o, p, n):
        v = o.matrix_world @ p
        # Owner pulled the temple sideways for inspection. Assemble only the export.
        if n == 'ES_SANCTUM' and abs(o.matrix_world.translation.x - 450) < 1:
            v.x -= 450
        return v - origins[n]
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    coll = bpy.data.collections.new('ES_DELIVERY_TEMP')
    bpy.context.scene.collection.children.link(coll)
    created, meshes, appended = [], [], []
    structures, props, parts, placements = [], [], {n: [] for n in origins}, {}
    audit = []
    try:
        source_objects = list(bpy.data.objects)
        for o in sorted(source_objects, key=lambda o: o.name):
            n = owner(o)
            if not n or o.type != 'MESH' or o.get('asset_role') == 'COLLISION_BOUNDARY' or not o.data.polygons:
                continue
            ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True,
                                                  depsgraph=bpy.context.evaluated_depsgraph_get())
            meshes.append(mesh)
            coords = [point(o, v.co, n) for v in mesh.vertices]
            mesh.calc_loop_triangles()
            triangles = list(mesh.loop_triangles)
            is_prop = o.get('asset_role') == 'PROP'
            # Gate and locked chest door are server fixtures; never duplicate them as ambient props.
            special = o.name in ('ES_SHRINE_VAULT_GATE_PROP_01', 'ES_SHRINE_VAULT_DOOR_PROP_01')
            for batch, start in enumerate(range(0, len(triangles), 9999)):
                tris = triangles[start:start + 9999]
                used = sorted({v for t in tris for v in t.vertices})
                remap = {v: i for i, v in enumerate(used)}
                lo = Vector(tuple(min(coords[v][a] for v in used) for a in range(3)))
                hi = Vector(tuple(max(coords[v][a] for v in used) for a in range(3)))
                centre = (lo + hi) / 2
                suffix = '' if batch == 0 else '_PART_' + str(batch + 1).zfill(2)
                short = o.name[3:].lower()
                if len(short) > 46:
                    import hashlib
                    short = short[:37] + '_' + hashlib.sha1(short.encode()).hexdigest()[:8]
                name = ('prop_es_' if is_prop else 'chunk_') + short + suffix
                data = bpy.data.meshes.new(name)
                meshes.append(data)
                data.from_pydata([coords[v] - centre for v in used], [],
                                 [[remap[v] for v in t.vertices] for t in tris])
                for mat in mesh.materials:
                    data.materials.append(mat)
                color = data.color_attributes.new(name='Col', type='BYTE_COLOR', domain='CORNER')
                src = mesh.color_attributes.get('Col')
                for i, t in enumerate(tris):
                    face = data.polygons[i]
                    face.material_index = t.material_index
                    face.use_smooth = mesh.polygons[t.polygon_index].use_smooth
                    for j, li in enumerate(face.loop_indices):
                        if src:
                            ix = t.loops[j] if src.domain == 'CORNER' else t.vertices[j]
                            color.data[li].color = src.data[ix].color
                        else:
                            mat = mesh.materials[t.material_index] if mesh.materials else None
                            color.data[li].color = mat.diffuse_color if mat else (1,1,1,1)
                obj = bpy.data.objects.new(name, data)
                coll.objects.link(obj)
                created.append(obj)
                size = [max(hi.x-lo.x, .001), max(hi.z-lo.z, .001), max(hi.y-lo.y, .001)]
                pos = [centre.x, centre.z, -centre.y]
                if is_prop:
                    props.append(obj)
                    row = dict(Prop=name, Anim='Static', Tier=1, P=pos,
                               R=[1,0,0,0,1,0,0,0,1], S=size)
                    if '_CANOPY_' in o.name and 'CURVED_CHAIR' not in o.name:
                        row['Anim'] = 'Sway'
                        row['Hinge'] = [0, -size[1]/2, 0]
                    elif '_LIGHT_' in o.name or 'SURFACE' in o.name:
                        row['Anim'] = 'Pulse'
                    if special:
                        row['Object'] = o.name
                        audit.append(dict(Fixture=row, Chunk=n))
                    else:
                        placements.setdefault(n, []).append(row)
                else:
                    structures.append(obj)
                    key = 'ES_' + name.upper()
                    # Offsets in imported (-X,Z,Y) axes, relative to full box centre Y32.
                    parts[n].append(dict(AssetKey=key, Object=name, Triangles=len(tris), SizeX=size[0], SizeY=size[1], SizeZ=size[2],
                                         OffsetX=-centre.x, OffsetY=centre.z-32,
                                         OffsetZ=centre.y, CanCollide=o.get('CanCollide', 'FOLIAGE' not in o.name)))
                audit.append(dict(Object=o.name, Export=name, Chunk=n, Triangles=len(tris), Prop=is_prop))
        # Keep the existing atmospheric library; append copies, do not load a scene.
        blend = ROOT / 'assets/source/worlds/ethereal_scape/ethereal_scape_kit.blend'
        with bpy.data.libraries.load(str(blend), link=False) as (available, dest):
            dest.objects = [n for n in available.objects if n.startswith('prop_es_') and not n.startswith('prop_es_live_')]
        for obj in dest.objects:
            if obj and obj.type == 'MESH':
                coll.objects.link(obj)
                obj.location = (0,0,0)
                appended.append(obj)
                props.append(obj)
        assert len(appended) == 13, f'Expected thirteen atmospheric meshes, got {len(appended)}'
        def export(objects, filename):
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = objects[0]
            bpy.ops.export_scene.fbx(filepath=str(OUT / filename), use_selection=True,
                apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z',
                axis_up='Y', object_types={'MESH'}, use_mesh_modifiers=True,
                add_leaf_bones=False, bake_anim=False, bake_space_transform=True)
        export(structures, 'ethereal_scape_structure.fbx')
        export(props, 'ethereal_scape_props.fbx')
        boundary_rows = json.loads((OUT / 'live_safety_boundaries.json').read_text())
        boundaries = {}
        for row in boundary_rows:
            n = row['Chunk']
            src = bpy.data.objects[n]
            segments = []
            for seg in row['Segments']:
                endpoints = []
                for k in ('A','B'):
                    v = point(src, Vector(seg[k]), n)
                    endpoints.append([v.x,v.z,-v.y])
                segments.append(dict(A=endpoints[0], B=endpoints[1]))
            boundaries[n] = dict(Height=64, Thickness=.36, Segments=segments)
        (OUT / 'live_delivery.json').write_text(json.dumps(dict(Parts=parts, Placements=placements,
                            Boundaries=boundaries, Audit=audit), indent=2), encoding='utf-8')
        return dict(Structures=len(structures), Props=len(props), Chunks=len(ids),
                    Boundaries=len(boundaries), MaxTriangles=max(a['Triangles'] for a in audit if 'Triangles' in a))
    finally:
        for o in created + appended:
            bpy.data.objects.remove(o, do_unlink=True)
        for m in meshes:
            if m.users == 0:
                bpy.data.meshes.remove(m)
        bpy.data.collections.remove(coll)
        for o in selected:
            o.select_set(True)
        bpy.context.view_layer.objects.active = active


if __name__ == '__main__':
    print(deliver())
