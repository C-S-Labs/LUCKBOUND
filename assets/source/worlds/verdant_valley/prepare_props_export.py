"""Consolidate the owner's live VV props without replacing collection organization.

Run inside Blender. The retained full-scene input is the recovery source; the
JSON ledger accounts for every original production prop exactly once.
"""
import bpy
import collections
import hashlib
import json
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path('E:/BlenderAIProjects/Projects')
REPORT = Path('C:/Users/jhpel/LUCKBOUND/assets/source/worlds/verdant_valley')
BACKUP = ROOT / 'VerdantValley_Props_Export_Input.blend'
MARKERS = ('vv_export_vertex', 'vv_export_face', 'vv_export_loop')


def object_digest(obj):
    mesh = obj.data
    payload = [obj.name, mesh.name, [list(r) for r in obj.matrix_world],
               sorted(c.name for c in obj.users_collection), dict(obj.items()),
               obj.hide_viewport, obj.hide_render, obj.hide_get(),
               [tuple(v.co) for v in mesh.vertices],
               [tuple(e.vertices) for e in mesh.edges],
               [(tuple(p.vertices), p.material_index, p.use_smooth) for p in mesh.polygons],
               [m.name if m else None for m in mesh.materials]]
    for attr in mesh.attributes:
        values = []
        for item in attr.data:
            for field in ('value', 'vector', 'color'):
                if hasattr(item, field):
                    value = getattr(item, field)
                    values.append(value if isinstance(value, (bool, int, float)) else tuple(value))
                    break
        payload.append((attr.name, attr.domain, attr.data_type, values))
    payload.append([tuple(n.vector) for n in mesh.corner_normals])
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def classify(obj, chunks):
    matches = [c for c in chunks if obj.name.startswith(c + '__')]
    chunk = matches[0] if len(matches) == 1 else None
    if not chunk:
        return chunk, 'review', 'Ambiguous chunk name'
    if 'canopy' in obj.name.lower():
        return chunk, 'canopy', 'Independent wind/sway canopy; origin unchanged'
    if obj.get('chest_role') or 'chest' in obj.name.lower():
        return chunk, 'special', 'Chest component: ' + str(obj.get('chest_role', 'review'))
    suffix = obj.name.split('__', 1)[1].lower()
    if suffix == 'fire' or suffix.startswith('flame_'):
        return chunk, 'review', 'Fire/flame may require runtime flicker or effects'
    if 'unclassified' in suffix:
        return chunk, 'review', 'Unclassified source lacks an established static role'
    if (obj.type != 'MESH' or obj.modifiers or obj.constraints or obj.animation_data
            or obj.parent or obj.data.shape_keys or len(obj.users_collection) != 1
            or obj.hide_get() or obj.hide_viewport or obj.hide_render):
        return chunk, 'review', 'Object behavior, visibility or memberships require review'
    return chunk, 'join', 'Ordinary static prop'


def join_group(objects, name, collection, frame):
    """Native join with temporary provenance and per-element preservation checks."""
    assert not bpy.data.objects.get(name), 'Already prepared: ' + name
    vertices, faces, corners, edges = [], [], [], []
    source_names = [o.name for o in objects]
    for obj in objects:
        # Never tag shared data: protected canopies/Temp may share source meshes.
        obj.data = obj.data.copy()
        mesh = obj.data
        assert not any(mesh.attributes.get(n) for n in MARKERS)
        offsets = (len(vertices), len(faces), len(corners))
        normal_matrix = obj.matrix_world.to_3x3().inverted().transposed()
        for vertex in mesh.vertices:
            vertices.append(obj.matrix_world @ vertex.co)
        for edge in mesh.edges:
            edges.append(tuple(sorted(offsets[0] + v for v in edge.vertices)))
        for face in mesh.polygons:
            material = mesh.materials[face.material_index] if mesh.materials else None
            faces.append((tuple(offsets[0] + v for v in face.vertices), material, face.use_smooth))
        for loop in mesh.loops:
            colors = {a.name: tuple(a.data[loop.index].color) for a in mesh.color_attributes
                      if a.domain == 'CORNER'}
            uvs = {a.name: tuple(a.data[loop.index].uv) for a in mesh.uv_layers}
            normal = (normal_matrix @ mesh.corner_normals[loop.index].vector).normalized()
            corners.append((offsets[0] + loop.vertex_index, colors, uvs, normal))
        for marker, domain, offset, count in zip(MARKERS, ('POINT', 'FACE', 'CORNER'), offsets,
                                               (len(mesh.vertices), len(mesh.polygons), len(mesh.loops))):
            attr = mesh.attributes.new(marker, 'INT', domain)
            attr.data.foreach_set('value', list(range(offset, offset + count)))
    result = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    collection.objects.link(result)
    result.matrix_world = frame
    with bpy.context.temp_override(active_object=result, object=result,
                                   selected_objects=[result] + objects,
                                   selected_editable_objects=[result] + objects):
        assert bpy.ops.object.join() == {'FINISHED'}
    mesh = result.data
    assert (len(mesh.vertices), len(mesh.polygons), len(mesh.loops), len(mesh.edges)) == (
        len(vertices), len(faces), len(corners), len(edges))
    vid = [a.value for a in mesh.attributes[MARKERS[0]].data]
    fid = [a.value for a in mesh.attributes[MARKERS[1]].data]
    lid = [a.value for a in mesh.attributes[MARKERS[2]].data]
    assert sorted(vid) == list(range(len(vertices)))
    assert sorted(fid) == list(range(len(faces)))
    assert sorted(lid) == list(range(len(corners)))
    max_error = max(((result.matrix_world @ v.co - vertices[vid[v.index]]).length
                     for v in mesh.vertices), default=0)
    assert max_error < 0.001, (name, 'World vertex error', max_error)
    assert collections.Counter(tuple(sorted(vid[v] for v in e.vertices)) for e in mesh.edges) == collections.Counter(edges)
    for face in mesh.polygons:
        original_vertices, material, smooth = faces[fid[face.index]]
        assert tuple(vid[v] for v in face.vertices) == original_vertices
        assert (mesh.materials[face.material_index] if mesh.materials else None) == material
        assert face.use_smooth == smooth
    local_normals = []
    normal_to_local = result.matrix_world.to_3x3().transposed()
    for loop in mesh.loops:
        original_vertex, colors, uvs, normal = corners[lid[loop.index]]
        assert vid[loop.vertex_index] == original_vertex
        for key, value in colors.items():
            assert max(abs(a-b) for a, b in zip(mesh.color_attributes[key].data[loop.index].color, value)) < 1e-6
        for key, value in uvs.items():
            assert max(abs(a-b) for a, b in zip(mesh.uv_layers[key].data[loop.index].uv, value)) < 1e-6
        local_normals.append((normal_to_local @ normal).normalized())
    # Nonuniformly scaled smooth sources need their original shading preserved.
    mesh.normals_split_custom_set(local_normals)
    for actual, expected in zip(mesh.corner_normals, local_normals):
        assert (actual.vector - expected).length < 0.001, (name, 'Normal mismatch')
    for marker in MARKERS:
        mesh.attributes.remove(mesh.attributes[marker])
    result['source_object_count'] = len(source_names)
    result['solid'] = collection.name == 'VV_PROPS_SOLID'
    mesh.calc_loop_triangles()
    return {'object': result.name, 'sources': source_names, 'count': len(source_names),
            'triangles': len(mesh.loop_triangles), 'max_world_vertex_error': max_error}


def main():
    assert bpy.context.mode == 'OBJECT'
    assert bpy.data.filepath and not BACKUP.exists(), 'Require fresh backup path before running'
    chunks = sorted(o.name for o in bpy.data.collections['VV_STRUCTURE'].all_objects
                    if o.name.startswith('chunk_') and '__' not in o.name)
    prop_collections = [bpy.data.collections[n] for n in ('VV_PROPS_SOLID', 'VV_PROPS_NONSOLID')]
    ledger, groups = [], collections.defaultdict(list)
    originals = set()
    for collection in prop_collections:
        for obj in collection.all_objects:
            assert obj.name not in originals, 'Duplicate production membership'
            originals.add(obj.name)
            chunk, category, reason = classify(obj, chunks)
            outcome = ('joined solid' if collection.name == 'VV_PROPS_SOLID' else 'joined nonsolid') if category == 'join' else category
            ledger.append({'source': obj.name, 'chunk': chunk, 'collection': collection.name,
                           'outcome': outcome, 'reason': reason})
            if category == 'join':
                groups[chunk, collection.name].append(obj)
    joined_names = {o.name for group in groups.values() for o in group}
    protected = {o.name: object_digest(o) for o in bpy.context.scene.objects if o.name not in joined_names}
    collection_memberships = {c.name: sorted(o.name for o in c.objects) for c in bpy.data.collections
                              if c.name not in ('VV_PROPS_SOLID', 'VV_PROPS_NONSOLID')}
    hierarchy = {c.name: sorted(x.name for x in c.children) for c in bpy.data.collections}
    source_path = bpy.data.filepath
    bpy.ops.wm.save_as_mainfile(filepath=str(BACKUP), copy=True)
    assert BACKUP.exists() and BACKUP.stat().st_size > 0 and bpy.data.filepath == source_path
    result_groups = {}
    for (chunk, collection_name), objects in sorted(groups.items()):
        role = 'PropsSolid' if collection_name == 'VV_PROPS_SOLID' else 'PropsNonSolid'
        result_groups[chunk, role] = join_group(objects, chunk + '__' + role,
                                              bpy.data.collections[collection_name],
                                              Matrix.Translation(bpy.data.objects[chunk].matrix_world.translation))
    bpy.context.view_layer.update()
    assert all(bpy.data.objects.get(n) and object_digest(bpy.data.objects[n]) == h for n, h in protected.items())
    assert hierarchy == {c.name: sorted(x.name for x in c.children) for c in bpy.data.collections}
    assert all(sorted(o.name for o in bpy.data.collections[n].objects) == members
               for n, members in collection_memberships.items())
    assert not any(bpy.data.objects.get(n) for n in joined_names)
    preserved_names = originals - joined_names
    results = {r['object'] for r in result_groups.values()}
    assert {o.name for c in prop_collections for o in c.all_objects} == preserved_names | results
    assert len(ledger) == len(originals) == len({row['source'] for row in ledger})
    report = {'scene': source_path, 'backup': str(BACKUP), 'original_props': len(originals),
              'outcomes': dict(collections.Counter(r['outcome'] for r in ledger)),
              'protected_objects_verified': len(protected), 'ledger': ledger, 'chunks': []}
    for chunk in chunks:
        entries = [r for r in ledger if r['chunk'] == chunk]
        report['chunks'].append({'chunk': chunk,
            'solid': result_groups.get((chunk, 'PropsSolid')),
            'nonsolid': result_groups.get((chunk, 'PropsNonSolid')),
            'canopies': [r['source'] for r in entries if r['outcome'] == 'canopy'],
            'special': [r['source'] for r in entries if r['outcome'] == 'special'],
            'review': [r for r in entries if r['outcome'] == 'review']})
    (REPORT / 'PROPS_EXPORT_REPORT.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    lines = ['# Verdant Valley prop export preparation', '',
             'Saved current scene; existing collection hierarchy retained. Structure, collision, Temp and all preserved props verified unchanged.',
             '', 'All original production props are recorded exactly once in `PROPS_EXPORT_REPORT.json`.', '',
             '| Chunk (prefix `chunk_`) | Solid sources | Solid result | Nonsolid sources | Nonsolid result | Canopies | Chest components | Review |',
             '|---|---:|---|---:|---|---:|---:|---:|']
    for row in report['chunks']:
        short = row['chunk'][6:]
        a, b = row['solid'], row['nonsolid']
        lines.append(f"| {short} | {a['count'] if a else 0} | `{a['object'] if a else 'none'}` | {b['count'] if b else 0} | `{b['object'] if b else 'none'}` | {len(row['canopies'])} | {len(row['special'])} | {len(row['review'])} |")
    lines += ['', '## Preserved interactive components and review objects', '']
    for r in ledger:
        if r['outcome'] in ('special', 'review'):
            lines.append(f"- `{r['source']}`: {r['reason']}.")
    large = [r for r in result_groups.values() if r['triangles'] > 10000]
    lines += ['', '## Validation and export follow-up', '',
              f"Outcomes: {report['outcomes']}. {len(protected)} unchanged objects verified.",
              'Per-element provenance checks passed for world vertices (under 0.001 stud), edges, ordered faces, materials, smooth flags, corner colors and normals. Source meshes have no UV layers; no UVs were removed. Custom corner normals preserve transformed source shading.',
              'Canopy transforms/origins and all three existing chest hinge pivots remain untouched. No animation or scripts added.',
              'Existing unresolved normals-review cases remain unchanged; this pass does not resolve them.',
              f'{len(large)} consolidated meshes exceed the documented 10,000-triangle single-mesh budget. These are preparation meshes; no decimation, splitting, material baking, FBX export or Roblox upload performed. Check Studio import limits and material/color preservation before production replacement.', '',
              '## Cleanup recommendation', '',
              f'Keep `{BACKUP}` and all previous production exports until owner Blender review, Studio import/visual check and applicable CI pass. This scene consolidation supersedes the separate ordinary source props only; recovery copies live in the retained backup. No production exports, manifest entries or kept assets were replaced or deleted.']
    (REPORT / 'PROPS_EXPORT_REVIEW.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=source_path)
    print(json.dumps({k: v for k, v in report.items() if k not in ('ledger', 'chunks')}))
    print('Joined meshes above 10k triangles:', len(large))


if __name__ == '__main__':
    main()
