"""Fill four Verdant Valley side pockets while preserving their travel lanes.

Run on the owner's VerdantValley_Extra_Details_Backup.blend. Re-running replaces
only this script's named scenery. Temp remains the reusable prop source.
"""

import bpy
import math
import random
import hashlib
import struct
from mathutils import Vector
from mathutils.bvhtree import BVHTree


SCENE = "VerdantValley_Extra_Details_Backup.blend"
TAG = "__detail_scatter_"
OLD_TAG = "__temp_scatter_"
TARGETS = {
    "chunk_side_treasure_hollow": {
        "patches": [(-49, 76), (-51, 35), (-45, -12), (48, -23), (55, -59)],
        "logs": [(-64, 14), (72, -38)],
        "trees": [(-58, 6), (61, -72)],
        "seed": 2001,
    },
    "chunk_longgrass_meadow": {
        "patches": [(-53, 61), (-52, 8), (-56, -57), (54, 60), (53, 2), (53, -57)],
        "logs": [(-78, -17), (77, 30)],
        "trees": [(72, 2), (70, -74)],
        "seed": 2002,
    },
    "chunk_deep_clearing": {
        "patches": [(-58, 57), (-55, -22), (-53, -69), (55, 65), (58, -65)],
        "logs": [(-76, -49), (78, 75)],
        "trees": [(-76, -13), (64, 76)],
        "seed": 2003,
    },
    "chunk_side_wardens_clearing": {
        "patches": [(-53, 64), (53, 62), (-53, 12), (53, 2), (-52, -59), (52, -66)],
        "logs": [(-78, -37), (73, -36)],
        "trees": [(50, -18), (-48, -68)],
        "seed": 2004,
    },
}

# Two anchor bushes, uneven offspring, and a few stone accents per patch.
# Each patch is rotated and slightly warped so repeated groups do not read as a stamp.
PATTERN = [
    ("flowering_bush", 0, 0, 1.7),
    ("Star_bush", -6, 5, 1.3),
    ("flowering_bush", 7, -3, 1.15),
    ("grass_tuft", -11, -5, 1.55),
    ("grass_tuft", 2, 10, 1.25),
    ("grass_tuft", 11, 7, 1.4),
    ("Star_bush", -12, 11, 0.9),
    ("grass_tuft", 13, -9, 1.05),
    ("rock", -15, -10, 0.73),
    ("grass_tuft", 18, 2, 1.15),
]


def terrain_hit(bvh, x, y, radius):
    checks = [(0, 0), (-radius, 0), (radius, 0), (0, -radius), (0, radius),
              (-radius, -radius), (-radius, radius), (radius, -radius), (radius, radius)]
    center = None
    for dx, dy in checks:
        hit, normal, _, _ = bvh.ray_cast(Vector((x + dx, y + dy, 150)), Vector((0, 0, -1)), 300)
        if hit is None or normal.z < 0.75:
            return None
        if dx == 0 and dy == 0:
            center = hit
    return center


def path_clear(name, x, y, radius):
    if abs(x) - radius < 35 or abs(x) + radius > 111 or abs(y) + radius > 111:
        return False
    if name == "chunk_deep_clearing" and x > 0 and abs(y) - radius < 35:
        return False  # east branch
    return True


def scatter_chunk(name, config, templates, solid, nonsolid):
    rng = random.Random(config["seed"])
    chunk = bpy.data.objects[name]
    bvh = BVHTree.FromObject(chunk, bpy.context.evaluated_depsgraph_get())
    made = []
    skipped = 0
    specs = []
    accepted = []
    for attempt in range(1800):
        patch_index = rng.randrange(len(config["patches"]))
        px, py = config["patches"][patch_index]
        kind, _, _, size = PATTERN[attempt % len(PATTERN)]
        # Broad overlapping planting zones, with stray individuals between them.
        if attempt % 3:
            x, y = px + rng.uniform(-32, 32), py + rng.uniform(-34, 34)
        else:
            x, y = rng.choice((-1, 1)) * rng.uniform(40, 100), rng.uniform(-103, 103)
        radius = 6 if kind == "rock" else 4
        if not path_clear(name, x, y, radius) or terrain_hit(bvh, x, y, radius) is None:
            continue
        if any((x - ax) ** 2 + (y - ay) ** 2 < 8.5 ** 2 for ax, ay in accepted):
            continue
        accepted.append((x, y))
        specs.append((kind, x, y, size * rng.uniform(0.8, 1.15), patch_index + 1))
        if len(accepted) >= len(config["patches"]) * 10:
            break
    for index, (x, y) in enumerate(config["logs"], 1):
        specs.append(("log", x, y, 0.9 + 0.12 * index, 90 + index))

    for kind, x, y, size, patch_index in specs:
        radius = 6 if kind in {"log", "rock"} else 3
        if not path_clear(name, x, y, radius):
            skipped += 1
            continue
        hit = terrain_hit(bvh, x, y, radius)
        if hit is None:
            skipped += 1
            continue
        template = templates[kind]
        obj = template.copy()
        obj.data = template.data.copy()
        obj.name = f"{name}{TAG}{patch_index:02d}_{kind.lower()}_{len(made)+1:03d}"
        (solid if kind in {"rock", "log"} else nonsolid).objects.link(obj)
        obj.location = chunk.location + Vector((x, y, hit.z))
        obj.rotation_euler = (0, 0, rng.uniform(-math.pi, math.pi))
        obj.scale = tuple(s * size for s in template.scale)
        # Compute the template's base without updating thousands of scene objects.
        bottom = min(v.co.z * obj.scale.z for v in obj.data.vertices)
        obj.location.z -= bottom + (0.2 if kind == "rock" else 0.04)
        made.append(obj)
    return bvh, made, skipped


def material(name, rgba, emission=False):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = rgba
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        if emission:
            bsdf.inputs["Emission Color"].default_value = rgba
            bsdf.inputs["Emission Strength"].default_value = 2.0
    return mat


class MeshBuilder:
    """Small flat-shaded primitives sharing the scene's material palette."""

    def __init__(self):
        self.vertices, self.faces, self.material_ids = [], [], []

    def add(self, vertices, faces, mat):
        start = len(self.vertices)
        self.vertices.extend(vertices)
        self.faces.extend(tuple(start + i for i in face) for face in faces)
        self.material_ids.extend([mat] * len(faces))

    def box(self, center, size, mat):
        x, y, z = center
        a, b, c = (v / 2 for v in size)
        self.add([(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
                  (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)],
                 [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], mat)

    def beam(self, start, end, width, mat):
        a, b = Vector(start), Vector(end)
        axis = (b-a).normalized()
        side = axis.cross(Vector((0,1,0)))
        if side.length < 0.01:
            side = axis.cross(Vector((1,0,0)))
        side.normalize()
        up = axis.cross(side).normalized()
        verts = [tuple(p + s*side*width/2 + t*up*width/2)
                 for p in (a,b) for s,t in ((-1,-1),(1,-1),(1,1),(-1,1))]
        self.add(verts, [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], mat)

    def frustum(self, center, bottom, top, height, mat, sides=8):
        x,y,z = center
        verts = [(x+radius*math.cos(i*math.tau/sides), y+radius*math.sin(i*math.tau/sides), z+dz)
                 for radius,dz in ((bottom,0),(top,height)) for i in range(sides)]
        faces = [tuple(range(sides-1,-1,-1)), tuple(range(sides,2*sides))]
        faces.extend((i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides))
        self.add(verts, faces, mat)

    def ring(self, center, radius, thickness, mat, plane='XZ'):
        # Faceted chain links and decorative hoops.
        verts=[]
        for i in range(12):
            angle=i*math.tau/12
            for j in range(4):
                cross=j*math.tau/4
                r=radius+thickness*math.cos(cross)
                p=Vector((r*math.cos(angle),thickness*math.sin(cross),r*math.sin(angle)))
                if plane=='YZ': p=Vector((p.y,p.x,p.z))
                verts.append(tuple(p+Vector(center)))
        faces=[(i*4+j,((i+1)%12)*4+j,((i+1)%12)*4+(j+1)%4,i*4+(j+1)%4)
               for i in range(12) for j in range(4)]
        self.add(verts,faces,mat)

    def foliage(self, center, scale, mat):
        g=(1+math.sqrt(5))/2
        vertices=[(-1,g,0),(1,g,0),(-1,-g,0),(1,-g,0),(0,-1,g),(0,1,g),
                  (0,-1,-g),(0,1,-g),(g,0,-1),(g,0,1),(-g,0,-1),(-g,0,1)]
        faces=[(0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),(1,5,9),(5,11,4),
               (11,10,2),(10,7,6),(7,1,8),(3,9,4),(3,4,2),(3,2,6),(3,6,8),
               (3,8,9),(4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1)]
        self.add([tuple(Vector(center)+Vector((p.x*scale[0],p.y*scale[1],p.z*scale[2])))
                  for p in (Vector(v).normalized() for v in vertices)],faces,mat)

    def finish(self, name, collection, materials):
        mesh=bpy.data.meshes.new(name+'Mesh')
        mesh.from_pydata(self.vertices, [], self.faces)
        mesh.update()
        for mat in materials: mesh.materials.append(mat)
        for face,index in zip(mesh.polygons,self.material_ids): face.material_index=index
        obj=bpy.data.objects.new(name,mesh)
        collection.objects.link(obj)
        return obj


def build_lantern_object(collection, name='lantern_post'):
    m=MeshBuilder()
    # Tapered post, metal shoe, collars, joinery, and a diagonal support.
    m.frustum((0,0,-0.15),1.05,0.72,14.2,0,4)
    # Align square timber faces with the shoe and crossbeam.
    for i, (x,y,z) in enumerate(m.vertices):
        m.vertices[i]=((x-y)/math.sqrt(2),(x+y)/math.sqrt(2),z)
    m.box((0,0,0.45),(1.65,1.65,1.1),1)
    for z in (1.15,10.8,13.6):
        width=math.sqrt(2)*(1.05-0.33*(z+0.15)/14.2)+0.12
        m.box((0,0,z),(width,width,0.22),1)
    m.box((3.0,0,12.4),(7.3,1.15,1.0),0)
    m.beam((0,0,8.5),(3.4,0,12.0),0.5,0)
    for x in (0,3.1):
        for y in (-0.64,0.64): m.frustum((x,y,12.55),0.16,0.16,0.12,3,6)
    m.frustum((0,0,14.0),0.9,0.15,0.8,0,4)
    for i in range(len(m.vertices)-8,len(m.vertices)):
        x,y,z=m.vertices[i]
        m.vertices[i]=((x-y)/math.sqrt(2),(x+y)/math.sqrt(2),z)
    # Three alternating chain links suspend an eight-sided lantern.
    for i in range(3): m.ring((5.5,0,11.6-i*0.5),0.36,0.09,1,'XZ' if i%2==0 else 'YZ')
    lamp_start=len(m.vertices)
    m.ring((5.5,0,9.95),0.35,0.08,1)
    m.frustum((5.5,0,9.45),1.8,0.35,0.75,4,8)
    m.frustum((5.5,0,9.32),1.9,1.9,0.16,3,8)
    m.frustum((5.5,0,6.2),1.35,1.5,0.35,1,8)
    m.frustum((5.5,0,6.53),1.5,1.5,0.15,3,8)
    m.frustum((5.5,0,6.72),1.24,1.36,2.5,2,8)
    for i in range(8):
        a=i*math.tau/8
        m.beam((5.5+1.5*math.cos(a),1.5*math.sin(a),6.65),
               (5.5+1.5*math.cos(a),1.5*math.sin(a),9.35),0.16,1)
    for z in (7.55,8.5): m.frustum((5.5,0,z),1.51,1.51,0.09,1,8)
    m.frustum((5.5,0,5.98),0.45,0.7,0.23,3,8)
    m.frustum((5.5,0,5.5),0.04,0.25,0.5,1,6)
    # Keep the suspension fixed and reduce only the hanging lantern by 15%.
    for i in range(lamp_start,len(m.vertices)):
        x,y,z=m.vertices[i]
        m.vertices[i]=(5.5+(x-5.5)*0.85,y*0.85,10.2+(z-10.2)*0.85)
    mats=[material('VV_ScatterDarkWood',(0.18,0.12,0.08,1)),
          material('VV_ScatterLanternIron',(0.12,0.14,0.13,1)),
          material('VV_ScatterLanternAmber',(1.0,0.63,0.19,1),True),
          material('VV_LanternBrass',(0.52,0.36,0.14,1)),
          material('VV_LanternPatina',(0.19,0.29,0.23,1))]
    return m.finish(name,collection,mats)


def lantern_template():
    temp=bpy.data.collections['Temp']
    old=temp.objects.get('lantern_post')
    if old: bpy.data.objects.remove(old,do_unlink=True)
    obj=build_lantern_object(temp)
    obj.location=(-1325,-625,145)
    return obj


def lantern_post(name, chunk, bvh, solid, template):
    x,y=46.0,-42.0
    hit=terrain_hit(bvh,x,y,5)
    if hit is None: raise RuntimeError('Lantern site has no safe ground')
    obj=template.copy()
    obj.data=template.data.copy()
    obj.name=name+TAG+'lantern_post'
    solid.objects.link(obj)
    obj.location=chunk.location+Vector((x,y,hit.z))
    obj.rotation_euler.z=math.pi
    return obj


def make_sapling(name, chunk, bvh, solid, nonsolid, index, x, y, rng):
    if not path_clear(name, x, y, 11):
        return []
    hit = terrain_hit(bvh, x, y, 9)
    if hit is None:
        return []
    height = rng.uniform(12.0, 15.0)
    spread = rng.uniform(7.5, 10.0)
    trunk_vertices = []
    for z, radius in ((-0.2, 1.25), (height, 0.62)):
        trunk_vertices.extend((math.cos(i * math.tau / 7) * radius,
                               math.sin(i * math.tau / 7) * radius, z) for i in range(7))
    trunk_faces = [tuple(range(6, -1, -1)), tuple(range(7, 14))]
    trunk_faces.extend((i, (i + 1) % 7, (i + 1) % 7 + 7, i + 7) for i in range(7))
    trunk_mesh = bpy.data.meshes.new(f"VVScatterSaplingTrunk{index}")
    trunk_mesh.from_pydata(trunk_vertices, [], trunk_faces)
    trunk_mesh.materials.append(material("VV_ScatterTreeBark", (0.29, 0.22, 0.14, 1)))
    trunk = bpy.data.objects.new(f"{name}{TAG}tree_{index:02d}_trunk", trunk_mesh)
    solid.objects.link(trunk)

    golden = (1 + math.sqrt(5)) / 2
    ico_vertices = [(-1, golden, 0), (1, golden, 0), (-1, -golden, 0), (1, -golden, 0),
                    (0, -1, golden), (0, 1, golden), (0, -1, -golden), (0, 1, -golden),
                    (golden, 0, -1), (golden, 0, 1), (-golden, 0, -1), (-golden, 0, 1)]
    ico_faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
                 (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
                 (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
                 (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    canopy_vertices, canopy_faces = [], []
    for dx, dy, dz, radius in ((0, 0, height + 4.5, spread),
                               (spread * 0.25, -spread * 0.18, height + 9.0, spread * 0.78)):
        start = len(canopy_vertices)
        canopy_vertices.extend(tuple(Vector(vertex).normalized() * radius + Vector((dx, dy, dz)))
                               for vertex in ico_vertices)
        canopy_faces.extend(tuple(start + v for v in face) for face in ico_faces)
    canopy_mesh = bpy.data.meshes.new(f"VVScatterSaplingCanopy{index}")
    canopy_mesh.from_pydata(canopy_vertices, [], canopy_faces)
    canopy_mesh.materials.append(material("VV_ScatterLeafDark", (0.20, 0.34, 0.18, 1)))
    canopy_mesh.materials.append(material("VV_ScatterLeafLight", (0.29, 0.43, 0.23, 1)))
    for face in canopy_mesh.polygons:
        face.material_index = int(face.index % 7 == 0)
    canopy = bpy.data.objects.new(f"{name}{TAG}tree_{index:02d}_canopy", canopy_mesh)
    nonsolid.objects.link(canopy)
    origin = chunk.location + Vector((x, y, hit.z))
    trunk.location = origin
    canopy.location = origin
    canopy.rotation_euler.z = rng.uniform(-math.pi, math.pi)
    return [trunk, canopy]


def unique_feature(name, chunk, bvh, solid, nonsolid):
    made=[]
    if name=='chunk_side_treasure_hollow':
        x,y=58,-52
        hit=terrain_hit(bvh,x,y,4)
        if hit is None: raise RuntimeError('Traveller pack site has no ground')
        m=MeshBuilder()
        m.box((0,0,1.7),(3.2,2.3,3.4),0)
        m.box((0,-1.23,1.3),(2.5,0.5,1.4),0)
        m.box((0,-1.3,3.0),(3.3,0.3,0.7),1)
        for xstrap in (-0.95,0.95):
            m.box((xstrap,-1.53,2.0),(0.28,0.13,2.7),1)
            m.box((xstrap,-1.62,2.2),(0.46,0.12,0.36),3)
        # Horizontal octagonal bedroll, with two leather retaining bands.
        for left,length,radius,mat in ((-2.1,4.2,0.68,2),(-1.4,0.25,0.73,1),(1.1,0.25,0.73,1)):
            start=len(m.vertices)
            m.frustum((0,0,0),radius,radius,length,mat,8)
            for i in range(start,len(m.vertices)):
                vx,vy,vz=m.vertices[i]
                m.vertices[i]=(left+vz,vy,4.0+vx)
        mats=[material('VV_ExplorerLeather',(0.36,0.25,0.14,1)),material('VV_ExplorerStraps',(0.19,0.15,0.09,1)),
              material('VV_ExplorerBedroll',(0.49,0.52,0.32,1)),material('VV_LanternBrass',(0.52,0.36,0.14,1))]
        obj=m.finish(name+TAG+'traveller_pack',solid,mats)
        obj.location=chunk.location+Vector((x,y,hit.z)); made.append(obj)
    elif name=='chunk_longgrass_meadow':
        x,y=-57,8
        hit=terrain_hit(bvh,x,y,8)
        if hit is None: raise RuntimeError('Flowering tree site has no ground')
        m=MeshBuilder()
        m.beam((0,0,-0.1),(-1,0,12),1.8,0)
        m.beam((-1,0,12),(-5,1,21),1.3,0)
        m.beam((-1,0,11),(6,-2,17),0.9,0)
        for z in (3,6,9): m.box((-z/12,-0.92,z),(1.1,0.05,0.27),1)
        bark=[material('VV_PaleBark',(0.72,0.69,0.55,1)),material('VV_BarkScars',(0.22,0.24,0.17,1))]
        trunk=m.finish(name+TAG+'flowering_tree_trunk',solid,bark)
        trunk.location=chunk.location+Vector((x,y,hit.z)); made.append(trunk)
        m=MeshBuilder()
        m.foliage((-5,1,21),(10,7,6),0)
        m.foliage((5,-2,17),(6,5,4),1)
        for dx,dy,dz in ((-10,-3,21),(-3,-5,24),(2,-1,24),(7,-5,18),(-9,4,23)):
            m.foliage((dx,dy,dz),(1.4,1.2,0.8),2)
        mats=[material('VV_MeadowLeaf',(0.38,0.49,0.25,1)),material('VV_MeadowLeafLight',(0.48,0.56,0.30,1)),
              material('VV_MeadowBlossom',(0.91,0.72,0.61,1))]
        canopy=m.finish(name+TAG+'flowering_tree_canopy',nonsolid,mats)
        canopy.location=trunk.location; made.append(canopy)
        # Loose wildflowers echo the blossoms across both meadow shoulders.
        blossom=mats[2]
        for i,(fx,fy) in enumerate([(-49,-30),(-62,4),(-92,-5),(-55,36),(-48,72),(48,24),(63,-25),(48,-62)]):
            h=terrain_hit(bvh,fx,fy,3)
            if h is None: continue
            m=MeshBuilder()
            for dx,dy,height in ((0,0,2.3),(1.7,0.5,1.6),(-1.0,1.4,1.9)):
                m.beam((dx,dy,0),(dx,dy,height),0.12,0)
                for p in range(5):
                    a=p*math.tau/5
                    m.foliage((dx+0.5*math.cos(a),dy+0.5*math.sin(a),height),(0.6,0.4,0.18),1+i%2)
                m.foliage((dx,dy,height+0.12),(0.22,0.22,0.17),3)
            flower_mats=[material('VV_FlowerStem',(0.24,0.36,0.16,1)),blossom,
                  material('VV_FlowerCream',(0.91,0.85,0.59,1)),material('VV_FlowerHeart',(0.67,0.45,0.16,1))]
            flower=m.finish(name+TAG+f'wildflowers_{i+1:02d}',nonsolid,flower_mats)
            flower.location=chunk.location+Vector((fx,fy,h.z)); made.append(flower)
    elif name=='chunk_deep_clearing':
        x,y=54,45
        hit=terrain_hit(bvh,x,y,5)
        if hit is None: raise RuntimeError('Waymarker site has no ground')
        m=MeshBuilder()
        m.frustum((0,0,-0.1),4.2,3.0,1.6,0,5)
        m.frustum((0,0,1.4),2.2,1.65,9.0,0,5)
        m.frustum((0,0,10.2),2.3,0.5,1.4,0,5)
        m.box((0,-1.7,5.8),(2.4,0.18,1.2),1)
        # Three weathered wooden arrows follow the three authored entrances.
        for z,sign in ((8.7,1),(6.8,-1)):
            m.box((sign*2.2,0,z),(6.0,0.65,1.1),2)
            m.add([(sign*5.2,-0.32,z-0.55),(sign*6.3,0,z),(sign*5.2,0.32,z-0.55),
                   (sign*5.2,-0.32,z+0.55),(sign*5.2,0.32,z+0.55)],
                  [(0,1,2),(3,4,1),(0,3,1),(2,1,4),(0,2,4,3)],2)
        m.box((0,1.7,4.6),(0.7,5.0,1.0),2)
        mats=[material('VV_WaymarkerStone',(0.43,0.45,0.38,1)),material('VV_WaymarkerMoss',(0.26,0.36,0.18,1)),
              material('VV_WaymarkerWood',(0.40,0.32,0.20,1))]
        obj=m.finish(name+TAG+'trail_waymarker',solid,mats)
        obj.location=chunk.location+Vector((x,y,hit.z)); made.append(obj)
    elif name=='chunk_side_wardens_clearing':
        x,y=-47,-20
        hit=terrain_hit(bvh,x,y,7)
        if hit is None: raise RuntimeError('Split stump site has no ground')
        m=MeshBuilder()
        sides=9
        verts=[(r*math.cos(i*math.tau/sides),r*math.sin(i*math.tau/sides),z+(0 if z==0 else (i%3)*0.8))
               for r,z in ((5.8,0),(4.2,7.0),(2.7,6.6)) for i in range(sides)]
        m.add(verts,[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)],0)
        m.add(verts,[(i+sides,(i+1)%sides+sides,(i+1)%sides+2*sides,i+2*sides)
                     for i in range(sides)],1)
        m.frustum((0,0,1),2.7,2.7,5.8,2,9)
        for i in (0,2,5,7):
            a=i*math.tau/sides
            m.beam((3*math.cos(a),3*math.sin(a),2.5),(8*math.cos(a),8*math.sin(a),0.2),1.4,0)
        for i,z in enumerate((2.2,4.0,5.5)):
            a=-1.4+i*0.5
            m.frustum((4.1*math.cos(a),4.1*math.sin(a),z),1.6,0.8,0.5,3,7)
        mats=[material('VV_StumpBark',(0.25,0.20,0.12,1)),material('VV_StumpHeartwood',(0.57,0.43,0.24,1)),
              material('VV_StumpHollow',(0.11,0.13,0.07,1)),material('VV_ShelfFungus',(0.65,0.52,0.31,1))]
        obj=m.finish(name+TAG+'split_stump',solid,mats)
        obj.location=chunk.location+Vector((x,y,hit.z)); made.append(obj)
    return made


def protected_digest():
    digest=hashlib.sha256()
    for obj in sorted(bpy.data.objects,key=lambda o:o.name):
        if obj.name=='lantern_post' or any(obj.name.startswith(name+'__detail_scatter_') for name in TARGETS):
            continue
        digest.update(obj.name.encode())
        for row in obj.matrix_world: digest.update(struct.pack('4d',*row))
        if obj.type=='MESH':
            for vertex in obj.data.vertices: digest.update(struct.pack('3f',*vertex.co))
            for face in obj.data.polygons: digest.update(str(tuple(face.vertices)).encode())
    return digest.hexdigest()


def main():
    if bpy.path.basename(bpy.data.filepath) != SCENE:
        raise RuntimeError(f"Open {SCENE} first")
    original_digest=protected_digest()
    for obj in list(bpy.data.objects):
        if any(obj.name.startswith(name + tag) for name in TARGETS for tag in (TAG, OLD_TAG)):
            bpy.data.objects.remove(obj, do_unlink=True)
    templates = bpy.data.collections["Temp"].objects
    lantern = lantern_template()
    solid = bpy.data.collections["VV_PROPS_SOLID"]
    nonsolid = bpy.data.collections["VV_PROPS_NONSOLID"]
    report = {}
    for name, config in TARGETS.items():
        bvh, made, skipped = scatter_chunk(name, config, templates, solid, nonsolid)
        rng = random.Random(config["seed"] + 100)
        for index, (x, y) in enumerate(config["trees"], 1):
            trees = make_sapling(name, bpy.data.objects[name], bvh, solid, nonsolid, index, x, y, rng)
            made.extend(trees)
            if not trees:
                skipped += 1
        if name == "chunk_side_treasure_hollow":
            made.append(lantern_post(name, bpy.data.objects[name], bvh, solid, lantern))
        made.extend(unique_feature(name, bpy.data.objects[name], bvh, solid, nonsolid))
        report[name] = {"added": len(made), "skipped": skipped}
        if len(made) < 25:
            raise RuntimeError(f"Too few suitable placements: {name} {report[name]}")
    bpy.context.view_layer.update()
    assert protected_digest()==original_digest, 'Protected scene geometry or transforms changed'
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print("SCATTER_REPORT", report)


if __name__ == "__main__":
    main()
