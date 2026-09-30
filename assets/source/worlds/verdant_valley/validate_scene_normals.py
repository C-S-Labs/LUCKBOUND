"""Conservative component-level normals audit/repair of the live Verdant Valley scene.

Run through Blender MCP with runpy; MODE is inspect, repair, or verify.
Only face winding changes. Open ambiguous surfaces are explicitly retained.
"""
import bpy
import bmesh
import json
import hashlib
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path('E:/BlenderAIProjects/Projects')


def components(bm):
    unseen = set(bm.faces)
    groups = []
    while unseen:
        face = unseen.pop()
        group, stack = {face}, [face]
        while stack:
            for edge in stack.pop().edges:
                for other in edge.link_faces:
                    if other in unseen:
                        unseen.remove(other)
                        group.add(other)
                        stack.append(other)
        groups.append(group)
    return groups


def invariant(obj):
    # Winding, normals and loop order excluded; all authoring data protected.
    data = (tuple(tuple(v.co) for v in obj.data.vertices),
            tuple(tuple(e.vertices) for e in obj.data.edges),
            tuple((tuple(sorted(p.vertices)), p.material_index, p.use_smooth)
                  for p in obj.data.polygons),
            tuple(tuple(r) for r in obj.matrix_world),
            tuple(m.name if m else None for m in obj.data.materials),
            tuple(sorted(c.name for c in obj.users_collection)),
            repr(dict(obj.items())))
    return hashlib.sha256(repr(data).encode()).hexdigest()


def volume(faces):
    center = sum((v.co for v in {v for f in faces for v in f.verts}), Vector())
    center /= len({v for f in faces for v in f.verts})
    return sum((f.verts[0].co-center).dot(
        (f.verts[i].co-center).cross(f.verts[i+1].co-center))/6
        for f in faces for i in range(1, len(f.verts)-1))


def exterior_probe(bm):
    """First-hit normals from 26 bounding-box exterior directions."""
    if not bm.faces:
        return 0, 0
    verts = list(bm.verts)
    low = Vector(tuple(min(v.co[i] for v in verts) for i in range(3)))
    high = Vector(tuple(max(v.co[i] for v in verts) for i in range(3)))
    center, radius = (low+high)/2, max((high-low).length, .1)*2
    tree = BVHTree.FromBMesh(bm)
    hits = backs = 0
    for x in (-1, 0, 1):
        for y in (-1, 0, 1):
            for z in (-1, 0, 1):
                if not (x or y or z):
                    continue
                direction = Vector((x, y, z)).normalized()
                hit, normal, _, _ = tree.ray_cast(center+direction*radius, -direction, radius*2)
                if hit is not None:
                    hits += 1
                    backs += normal.dot(direction) < -1e-5
    return hits, backs


def audit(mode):
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    before = {o.name: invariant(o) for o in objects}
    users = defaultdict(list)
    for obj in objects:
        users[obj.data.as_pointer()].append(obj)
    results = []
    for instances in users.values():
        obj = instances[0]
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        bm.normal_update()
        original = {f.index: f.normal.copy() for f in bm.faces}
        groups = components(bm)
        group_bounds = []
        for group in groups:
            vs = {v for f in group for v in f.verts}
            group_bounds.append(([min(v.co[i] for v in vs) for i in range(3)],
                                 [max(v.co[i] for v in vs) for i in range(3)]))
        tree = BVHTree.FromBMesh(bm)
        group_ids = {f.index: i for i, fs in enumerate(groups) for f in fs}
        self_crossing = {group_ids[a] for a, b in tree.overlap(tree)
                         if a < b and group_ids[a] == group_ids[b]
                         and not set(bm.faces[a].verts).intersection(bm.faces[b].verts)}
        ambiguous, reasons = [], []
        closed_count = 0
        for group_index, faces in enumerate(groups):
            edges = {e for f in faces for e in f.edges}
            closed = all(len(e.link_faces) == 2 for e in edges)
            vertices = {v for f in faces for v in f.verts}
            if closed:
                # Independently orient each closed shell; never the whole scene.
                bmesh.ops.recalc_face_normals(bm, faces=list(faces))
                bm.normal_update()
                signed = volume(faces)
                if abs(signed) < 1e-8:
                    ambiguous.append({'faces': sorted(f.index for f in faces),
                                      'reason': 'Closed shell has negligible signed volume.'})
                    for face in faces:
                        if original[face.index].dot(face.normal) < 0:
                            face.normal_flip()
                else:
                    if signed < 0:
                        bmesh.ops.reverse_faces(bm, faces=list(faces))
                    closed_count += 1
                bm.normal_update()
                low, high = group_bounds[group_index]
                enclosed_bounds = any(all(low[i] > a[i]+1e-4 and high[i] < b[i]-1e-4
                                          for i in range(3))
                                      for j, (a, b) in enumerate(group_bounds) if j != group_index)
                changing = any(original[f.index].dot(f.normal) < 0 for f in faces)
                if changing and (enclosed_bounds or group_index in self_crossing):
                    ambiguous.append({'faces': sorted(f.index for f in faces),
                                      'reason': 'Potential nested interior shell or self-intersection; preserve for manual review.'})
                    for face in faces:
                        if original[face.index].dot(face.normal) < 0:
                            face.normal_flip()
            elif obj.data == bpy.data.objects['VV_Vine'].data:
                # Authoring placement uses local +Y toward the passage on both walls.
                for face in faces:
                    if face.normal.y < 0:
                        face.normal_flip()
                reasons.append('Vine leaf fronts face authored passage-facing local +Y.')
            elif '__water_' in obj.name:
                for face in faces:
                    world = obj.matrix_world.to_3x3().inverted().transposed() @ face.normal
                    if world.z < 0:
                        face.normal_flip()
                reasons.append('Horizontal water surface faces world +Z.')
            else:
                # Accept a partial convex shell only with geometric support evidence.
                center = sum((v.co for v in vertices), Vector()) / len(vertices)
                dots = [f.normal.dot(f.calc_center_median()-center) for f in faces]
                convex = all(all(f.normal.dot(v.co-f.verts[0].co) <= 1e-4
                                 for v in vertices) for f in faces)
                if convex and max(dots, default=0) > 1e-4 and min(dots) >= -1e-4:
                    reasons.append('Open convex exterior shell: all normals support vertex hull.')
                else:
                    ambiguous.append({'faces': sorted(f.index for f in faces),
                                      'reason': 'Open/nonmanifold surface: intended side cannot be proved by topology.'})
        bm.normal_update()
        flips = sorted(f.index for f in bm.faces if original[f.index].dot(f.normal) < 0)
        hits, backs = exterior_probe(bm)
        inconsistent = sum(not e.is_contiguous for e in bm.edges if len(e.link_faces) == 2)
        if backs and not ambiguous:
            # The sparse probe is supporting evidence, not an automatic repair criterion.
            reasons.append(f'Exterior probe returned {backs} back hits; review ray accessibility.')
        if mode == 'repair' and flips:
            # Flip source polygons directly to preserve UV/color loop association and indices.
            for index in flips:
                obj.data.polygons[index].flip()
            obj.data.update()
        results.append({'objects': [o.name for o in instances], 'mesh': obj.data.name,
                        'faces': len(bm.faces), 'closed_components': closed_count,
                        'flip_faces': flips, 'ambiguous': ambiguous,
                        'reasons': sorted(set(reasons)), 'exterior_hits': hits,
                        'exterior_back_hits': backs, 'inconsistent_edges_after': inconsistent})
        bm.free()
    assert len(objects) == len(bpy.context.scene.objects)
    assert all(invariant(o) == before[o.name] for o in objects), 'Non-winding scene change!'
    (ROOT/f'Normals_{mode}.json').write_text(json.dumps(results, indent=2))
    summary = {'objects': len(objects), 'unique_meshes': len(users),
               'affected_objects': sum(len(r['objects']) for r in results if r['flip_faces']),
               'faces_instances': sum(len(r['objects'])*len(r['flip_faces']) for r in results),
               'unique_faces': sum(len(r['flip_faces']) for r in results),
               'ambiguous_objects': sum(len(r['objects']) for r in results if r['ambiguous']),
               'exterior_back_objects': sum(len(r['objects']) for r in results if r['exterior_back_hits'])}
    print(json.dumps(summary))
    return results


if __name__ == '__main__':
    audit(globals().get('MODE', 'inspect'))
