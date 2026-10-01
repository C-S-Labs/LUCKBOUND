"""Owner-directed Longgrass centerpiece refinement; edit only its two tree meshes."""
import bpy
import hashlib
import json
import math
import random
import struct
import sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).parent))
from scatter_sparse_chunks import MeshBuilder

PREFIX = 'chunk_longgrass_meadow__detail_scatter_flowering_tree_'
EDITABLE = {PREFIX + 'trunk', PREFIX + 'canopy', 'flowering_tree_trunk', 'flowering_tree_canopy'}


def digest():
    h = hashlib.sha256()
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        if o.name in EDITABLE:
            continue
        h.update(o.name.encode())
        h.update('|'.join(sorted(c.name for c in o.users_collection)).encode())
        h.update(struct.pack('16d', *(v for row in o.matrix_world for v in row)))
        if o.type == 'MESH':
            for v in o.data.vertices:
                h.update(struct.pack('3f', *v.co))
            for p in o.data.polygons:
                h.update(str((tuple(p.vertices), p.material_index, p.use_smooth)).encode())
            h.update('|'.join(m.name if m else '' for m in o.data.materials).encode())
    return h.hexdigest()


def branch(builder, start, end, radius, tip):
    a, b = Vector(start), Vector(end)
    direction = (b - a).normalized()
    u = direction.cross(Vector((0, 1, 0))).normalized()
    v = direction.cross(u).normalized()
    vertices = [tuple(p + r * (math.cos(i * math.tau / 7) * u + math.sin(i * math.tau / 7) * v))
                for p, r in ((a, radius), (b, tip)) for i in range(7)]
    builder.add(vertices, [tuple(range(6, -1, -1)), tuple(range(7, 14))]
                + [(i, (i+1)%7, (i+1)%7+7, i+7) for i in range(7)], 0)


def replace_mesh(obj, builder, materials):
    mesh = bpy.data.meshes.new(obj.data.name + '_Refined')
    mesh.from_pydata(builder.vertices, [], builder.faces)
    for mat in materials:
        mesh.materials.append(bpy.data.materials[mat])
    for p, index in zip(mesh.polygons, builder.material_ids):
        p.material_index = index
    mesh.update()
    obj.data = mesh


def seat_bark_marks(builder):
    """Embed each scar box in the actual tapered bark face, facing its normal."""
    bark_faces = [f for f, m in zip(builder.faces, builder.material_ids) if m == 0]
    surface = BVHTree.FromPolygons(builder.vertices, bark_faces, all_triangles=False)
    indices = sorted({index for face, mat in zip(builder.faces, builder.material_ids)
                      if mat == 1 for index in face})
    groups = indices[::8]
    for start in groups:
        center = sum((Vector(p) for p in builder.vertices[start:start+8]), Vector()) / 8
        hit, normal, _, _ = surface.ray_cast(Vector((center.x,-10,center.z)),Vector((0,1,0)),20)
        assert hit is not None, 'Bark mark has no trunk surface'
        side = normal.cross(Vector((0,0,1))).normalized()
        up = side.cross(normal).normalized()
        center = hit - normal * .018
        builder.vertices[start:start+8] = [tuple(center + side*x*.32 + normal*y*.026 + up*z*.11)
            for z in (-1,1) for x,y in ((-1,-1),(1,-1),(1,1),(-1,1))]


def main():
    before = digest()
    trunk, canopy = (bpy.data.objects[PREFIX + part] for part in ('trunk', 'canopy'))
    transforms = {o.name: o.matrix_world.copy() for o in (trunk, canopy)}
    wood = MeshBuilder()
    for a, b, r, t in [((0,0,-.2),(-.7,.2,8),1.65,1.18),
                       ((-.7,.2,8),(-2,1,17),1.18,.86),
                       ((-2,1,17),(-5,1.5,25),.86,.45),
                       ((-1,.4,10),(5,-2,17),.8,.52),
                       ((5,-2,17),(10,-3,24),.52,.22),
                       ((-2,1,15),(-9,-2,21),.7,.38),
                       ((-9,-2,21),(-13,-3,25),.38,.16),
                       ((-3,1,19),(-2,7,25),.58,.2),
                       ((-5,1.5,24),(-8,3,29),.42,.16),
                       ((5,-2,17),(3,-6,23),.4,.16)]:
        branch(wood,a,b,r,t)
    for angle, length in ((.2,4.5),(1.7,3.8),(3.1,5.2),(4.4,4.0),(5.5,3.0)):
        branch(wood,(0,0,1.2),(length*math.cos(angle),length*math.sin(angle),.05),.8,.16)
    for z in (3.5,6.5,9,13):
        wood.box((-.10*z,-1.03,z),(.64,.12,.22),1)
    seat_bark_marks(wood)
    replace_mesh(trunk,wood,['VV_PaleBark','VV_BarkScars'])
    leaves = MeshBuilder()
    lobes = [((-6,1,26),(9,7,6)),((-12,-2,24),(6,5,4.6)),
             ((2,-3,24),(8,6,5.5)),((10,-2,24),(6,5,4.6)),
             ((-3,6,26),(7,5,5)),((-7,2,30),(6.5,5,4.5)),
             ((1,1,28),(6,5,5))]
    rng = random.Random(133)
    for i,(center,scale) in enumerate(lobes):
        leaves.foliage(center,scale,i%2)
        # Blossoms sit on the crown surface, with a deliberate mix of top and side views.
        for j in range(7):
            azimuth = j * math.tau / 7 + rng.uniform(-.24,.24)
            elevation = rng.uniform(.05,1.10)
            normal = Vector((math.cos(azimuth)*math.cos(elevation),
                             math.sin(azimuth)*math.cos(elevation),math.sin(elevation)))
            c = Vector(center) + Vector(tuple(normal[k]*scale[k]*.86 for k in range(3)))
            u = normal.cross(Vector((0,0,1))).normalized()
            v = normal.cross(u).normalized()
            size = rng.uniform(1.15,1.55)
            for petal in range(5):
                angle = petal * math.tau / 5
                pos = c + size*.72*(math.cos(angle)*u + math.sin(angle)*v)
                # Broad flattened petals read as flowers without fine realistic detail.
                start = len(leaves.vertices)
                leaves.foliage((0,0,0),(size*.67,size*.49,size*.22),2 if j%3 else 3)
                for k in range(start,len(leaves.vertices)):
                    p = leaves.vertices[k]
                    leaves.vertices[k] = tuple(pos + u*p[0] + v*p[1] + normal*p[2])
            leaves.foliage(tuple(c+normal*.18),(.30,.30,.24),4)
    replace_mesh(canopy,leaves,['VV_MeadowLeaf','VV_MeadowLeafLight','VV_Blossom',
                                'VV_FlowerCream','VV_FlowerHeart'])
    for name in ('flowering_tree_trunk','flowering_tree_canopy'):
        obj = bpy.data.objects.get(name)
        if obj:
            assert [c.name for c in obj.users_collection] == ['Temp']
            bpy.data.objects.remove(obj,do_unlink=True)
    bpy.context.view_layer.update()
    assert digest() == before, 'Protected scene changed'
    assert all(o.matrix_world == transforms[o.name] for o in (trunk,canopy))
    assert all(math.isfinite(v) for o in (trunk,canopy) for vert in o.data.vertices for v in vert.co)
    for o in (trunk,canopy):
        points = [o.matrix_world @ v.co - bpy.data.objects['chunk_longgrass_meadow'].location for v in o.data.vertices]
        assert max(p.x for p in points) < -35, 'Tree approaches playable route'
        assert all(abs(p.x)<112 and abs(p.y)<112 for p in points), 'Tree approaches chunk boundary'
    result = {'protected_digest':before,'protected_objects':len(bpy.data.objects)-2,
              'temp_sources':len(bpy.data.collections['Temp'].objects),
              'tree':[{'name':o.name,'faces':len(o.data.polygons),'dimensions':list(o.dimensions)} for o in (trunk,canopy)]}
    Path('E:/BlenderAIProjects/Projects/Flowering_Tree_Verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath='E:/BlenderAIProjects/Projects/VerdantValley_Extra_Details_Backup.blend')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
