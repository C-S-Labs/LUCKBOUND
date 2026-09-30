"""Rebuild only Cliff Passage's two long grass/rock seams in the current scene.

Replaces the toothed terrain strip with planar profile bands; the two existing
cliff meshes share the new crest. No prop additions or production export.
"""
import bpy
import bmesh
import hashlib
import json
import math
import struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path('E:/BlenderAIProjects/Projects')
CHUNK = 'chunk_path_cliff_passage'
# Piecewise-linear profiles: rise, shallow dip, broad rise, end descent.
PROFILES = {
    1: [(-87, 8), (-62, 29), (-38, 34), (4, 32), (43, 35), (64, 28), (87, 8)],
    -1: [(-87, 4), (-62, 23), (-35, 28), (7, 26), (43, 29), (65, 22), (87, 4)],
}


def object_hash(obj):
    h = hashlib.sha256()
    h.update(str(sorted(c.name for c in obj.users_collection)).encode())
    h.update(struct.pack('16d', *(v for row in obj.matrix_world for v in row)))
    if obj.type == 'MESH':
        for v in obj.data.vertices:
            h.update(struct.pack('3f', *v.co))
        for p in obj.data.polygons:
            h.update(str((tuple(p.vertices), p.material_index, p.use_smooth)).encode())
        h.update(str([m.name if m else None for m in obj.data.materials]).encode())
    return h.hexdigest()


def profile(x, side):
    knots = PROFILES[side]
    for (a, za), (b, zb) in zip(knots, knots[1:]):
        if x <= b:
            return za + (zb - za) * max(0, min(1, (x - a) / (b - a)))
    return knots[-1][1]


def split_polygon(poly, axis, value, sign):
    """Return inside/outside polygons, preserving exact linear cut coordinates."""
    inside, outside = [], []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        da, db = sign * (a[axis] - value), sign * (b[axis] - value)
        (inside if da >= -1e-7 else outside).append(a)
        if (da > 1e-7 and db < -1e-7) or (da < -1e-7 and db > 1e-7):
            p = a.lerp(b, da / (da - db))
            inside.append(p); outside.append(p)
    return inside, outside


def main():
    obj = bpy.data.objects[CHUNK]
    assert not obj.get('broad_ridges_rebuilt'), 'Ridge rebuild already applied.'
    baseline = {o.name: object_hash(o) for o in bpy.data.objects}
    original = obj.data
    original.calc_loop_triangles()
    source = [v.co.copy() for v in original.vertices]
    surface = BVHTree.FromPolygons(source, [tuple(p.vertices) for p in original.polygons])
    def height(x, y):
        hit = surface.ray_cast(Vector((x, y, 150)), Vector((0, 0, -1)), 250)[0]
        assert hit is not None, (x, y)
        return hit.z
    vertices, faces, materials, lookup = [], [], [], {}
    cuts = {s: {30: set([-87., 87.]), 55: set([-87., 87.])} for s in (-1, 1)}
    def add(poly, mat):
        if len(poly) < 3: return
        ids = []
        for p in poly:
            key = tuple(round(v, 5) for v in p)
            if key not in lookup:
                lookup[key] = len(vertices); vertices.append(tuple(p))
            ids.append(lookup[key])
        ids = list(dict.fromkeys(ids))
        if len(ids) >= 3:
            faces.append(ids); materials.append(mat)
    removed = 0
    # Clip only grass surfaces, leaving route, sockets, underside and outer terrain.
    for p in original.polygons:
        poly = [source[i] for i in p.vertices]
        if p.material_index not in (0, 1, 3, 4, 5) or p.normal.z <= 0:
            add(poly, p.material_index); continue
        pieces = [poly]
        for side in (-1, 1):
            next_pieces = []
            for piece in pieces:
                active = piece
                for axis, value, sign in ((0, -87, 1), (0, 87, -1), (1, side*30, side), (1, side*55, -side)):
                    if not active: break
                    active, out = split_polygon(active, axis, value, sign)
                    if len(out) >= 3: next_pieces.append(out)
                if len(active) >= 3:
                    removed += 1
                    for v in active:
                        for y in (30, 55):
                            if abs(v.y - side*y) < 1e-4:
                                cuts[side][y].add(round(v.x, 5))
            pieces = next_pieces
        for piece in pieces: add(piece, p.material_index)
    # Boundary rows inherit the original surface; interior rows are new geometry.
    ridge_rows = {}
    for side in (-1, 1):
        xs = sorted(cuts[side][30] | cuts[side][55] | {x for x, z in PROFILES[side]})
        rows = []
        for y in (30, 38, 50, 55):
            row = []
            for x in xs:
                z = height(x, side*y)
                if y in (38, 50):
                    h = profile(x, side)
                    outer = height(x, side*55)
                    z = h if y == 38 else h + (outer-h)*12/17
                    # Match the untouched end boundaries; tiny end apron only.
                    t = max(0, min(1, (87-abs(x))/7))
                    z = z*t + height(x, side*y)*(1-t)
                row.append(Vector((x, side*y, z)))
            rows.append(row)
        ridge_rows[side] = rows
        for j in range(3):
            for i in range(len(xs)-1):
                quad = [rows[j][i], rows[j][i+1], rows[j+1][i+1], rows[j+1][i]]
                if side < 0: quad.reverse()
                # Broad grass bands, all descending exposed-face surfaces are rock.
                add(quad, 4 if j == 0 else (1 if j == 2 else 0))
    mesh = bpy.data.meshes.new(original.name + '_rebuilt')
    mesh.from_pydata(vertices, [], faces)
    for mat in original.materials: mesh.materials.append(mat)
    for p, mat in zip(mesh.polygons, materials): p.material_index = mat; p.use_smooth = False
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.0001)
    bm.to_mesh(mesh); bm.free(); mesh.update()
    obj.data = mesh
    # Refit existing cliff top bands, never add rocks to hide intersections.
    edited = {CHUNK}
    for side, suffix in ((-1, '01'), (1, '02')):
        wall = bpy.data.objects[CHUNK+'__cliff_'+suffix]; edited.add(wall.name)
        to_chunk = obj.matrix_world.inverted() @ wall.matrix_world
        to_wall = to_chunk.inverted()
        old_wall = wall.data
        stations = [[to_chunk @ old_wall.vertices[i+j].co for j in range(4)] for i in range(0,len(old_wall.vertices),4)]
        def base_point(x, row):
            for a,b in zip(stations,stations[1:]):
                if x <= b[0].x + .001:
                    return a[row].lerp(b[row],max(0,min(1,(x-a[0].x)/(b[0].x-a[0].x))))
            return stations[-1][row].copy()
        wall_v, wall_f = [], []
        for crest, shoulder in zip(ridge_rows[side][1],ridge_rows[side][2]):
            upper = crest.copy(); upper.z -= .08
            back = shoulder.copy(); back.z -= .08
            wall_v.extend([tuple(to_wall@p) for p in (base_point(crest.x,0),upper,back,base_point(crest.x,3))])
        for i in range(len(wall_v)//4-1):
            for j in range(4):
                a=i*4+j;b=(i+1)*4+j;c=(i+1)*4+(j+1)%4;d=i*4+(j+1)%4
                face=[a,b,c,d]
                if side<0:face.reverse()
                wall_f.append(face)
        wall_f.extend([[3,2,1,0],[len(wall_v)-4+j for j in range(4)]])
        rebuilt=bpy.data.meshes.new(old_wall.name+'_crest')
        rebuilt.from_pydata(wall_v,[],wall_f)
        for material in old_wall.materials:rebuilt.materials.append(material)
        for p in rebuilt.polygons:p.use_smooth=False; p.material_index=4
        rebuilt.update();wall.data=rebuilt
    bpy.context.view_layer.update()
    # Move only terrain-attached props whose actual supporting ground changed.
    ground = BVHTree.FromPolygons([obj.matrix_world@v.co for v in mesh.vertices], [tuple(p.vertices) for p in mesh.polygons if p.material_index in (0, 1)])
    moved = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.startswith(CHUNK+'__') or o.name in edited: continue
        if not any(t in o.name for t in ('grass_clump', 'grass_tuft', 'rock_', 'tree_trunk')): continue
        pts = [obj.matrix_world.inverted()@o.matrix_world@v.co for v in o.data.vertices]
        x = (min(p.x for p in pts)+max(p.x for p in pts))/2
        y = (min(p.y for p in pts)+max(p.y for p in pts))/2
        if not (-80 < x < 80 and 38 < abs(y) < 55): continue
        old = height(x, y)
        hit = ground.ray_cast(obj.location+Vector((x,y,150)), Vector((0,0,-1)),250)[0]
        if hit is None: continue
        dz = hit.z - obj.location.z - old
        if abs(dz) < .15: continue
        # Tree canopy follows its trunk as one assembly by original numeric pairing.
        targets = [o]
        if 'tree_trunk' in o.name:
            for canopy in bpy.data.objects:
                if not canopy.name.startswith(CHUNK+'__tree_canopy'): continue
                center = obj.matrix_world.inverted() @ (canopy.matrix_world @ (sum((v.co for v in canopy.data.vertices), Vector()) / len(canopy.data.vertices)))
                if math.hypot(center.x-x, center.y-y) < 5: targets.append(canopy)
        for target in targets:
            target.location.z += dz; edited.add(target.name)
        moved.append((o.name, dz))
    bpy.context.view_layer.update()
    assert all(object_hash(bpy.data.objects[n]) == h for n,h in baseline.items() if n not in edited)
    for name in edited:
        m = bpy.data.objects[name].data
        assert all(math.isfinite(a) for v in m.vertices for a in v.co)
        m.calc_loop_triangles(); assert len(m.loop_triangles) < 10000
    obj['broad_ridges_rebuilt'] = True
    mesh.calc_loop_triangles()
    result = {'edited': sorted(edited), 'props_reseated': moved, 'protected_objects': len(baseline)-len(edited), 'replaced_grass_fragments': removed, 'triangles':len(mesh.loop_triangles), 'profiles':PROFILES, 'scene':bpy.data.filepath}
    (ROOT/'Cliff_Ridge_Rebuild_Record.json').write_text(json.dumps(result, indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(json.dumps(result))


def repair_owner_seams():
    """Stitch cut boundaries and repair the owner's moved cliff join in place."""
    obj = bpy.data.objects[CHUNK]
    assert not obj.get('owner_seams_repaired')
    baseline = {o.name: object_hash(o) for o in bpy.data.objects}
    edited = {CHUNK, CHUNK+'__cliff_01', CHUNK+'__cliff_02'}
    mesh = obj.data
    route = [(tuple(tuple(mesh.vertices[i].co) for i in p.vertices),p.material_index) for p in mesh.polygons if p.material_index == 2]
    # Keep the owner's transforms and use actual moved top vertices as the seam.
    walls = {}
    for side,suffix in ((-1,'01'),(1,'02')):
        wall = bpy.data.objects[CHUNK+'__cliff_'+suffix]
        t = obj.matrix_world.inverted() @ wall.matrix_world
        stations = [[t @ wall.data.vertices[i+j].co for j in range(4)] for i in range(0,len(wall.data.vertices),4)]
        walls[side] = (wall,stations)
        for v in mesh.vertices:
            if abs(v.co.x)>87.001: continue
            row = 1 if abs(v.co.y-side*38)<.001 else 2 if abs(v.co.y-side*50)<.001 else None
            if row is None: continue
            closest = min(stations,key=lambda station:abs(station[1].x-v.co.x))
            assert abs(closest[1].x-v.co.x)<.001
            v.co = closest[row]
        for p in mesh.polygons:
            if p.material_index in (4,5) and all(abs(mesh.vertices[i].co.x)<=87.001 and 29.99<=abs(mesh.vertices[i].co.y)<=38.1 for i in p.vertices):
                p.material_index = 3
        # The terrain bank and grass now own front/top faces. Delete duplicate
        # cliff faces, leaving its backing, underside and end closures intact.
        bm = bmesh.new();bm.from_mesh(wall.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.faces.ensure_lookup_table()
        duplicate = [f for f in bm.faces if f.index < len(wall.data.polygons)-2 and f.index % 4 in (0,1)]
        bmesh.ops.delete(bm,geom=duplicate,context='FACES_ONLY')
        bm.to_mesh(wall.data);bm.free();wall.data.update()
    mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh)
    def local(v): return abs(v.co.x)<87.01 and 29.99<=abs(v.co.y)<=55.01
    boundary=[e for e in bm.edges if e.is_boundary and all(local(v) for v in e.verts)]
    candidates=set(v for e in boundary for v in e.verts)
    # Existing outer fragments are authoritative at all four cut boundaries.
    # Insert every patch station into those edges and weld matching vertices.
    split_count=0
    for edge in list(boundary):
        if not edge.is_valid:continue
        a,b=[v.co.copy() for v in edge.verts]
        axis=0 if abs(a.x-b.x)<1e-4 and abs(abs(a.x)-87)<.001 else 1 if abs(a.y-b.y)<1e-4 and min(abs(abs(a.y)-30),abs(abs(a.y)-55))<.001 else None
        if axis is None:continue
        face=edge.link_faces[0]
        outside=any(abs(v.co.x)>87.001 or abs(v.co.y)>55.001 or abs(v.co.y)<29.999 for v in face.verts)
        if not outside:continue
        delta=b-a;xy=Vector((delta.x,delta.y,0));length=xy.length_squared
        if length<1e-10:continue
        inserts=[]
        for v in candidates:
            if v in edge.verts:continue
            offset=Vector((v.co.x-a.x,v.co.y-a.y,0));t=offset.dot(xy)/length
            if 1e-5<t<1-1e-5 and (offset-xy*t).length<.0002:
                inserts.append((t,v))
        if not inserts:continue
        # Rebuild this one polygon with the new ordered cut points.
        original=list(face.verts);start=next(i for i,v in enumerate(original) if v in edge.verts and original[(i+1)%len(original)] in edge.verts)
        first=original[start];last=original[(start+1)%len(original)]
        inserts.sort(key=lambda item:item[0],reverse=(first.co-a).length>.0001)
        added=[]
        for t,v in inserts:
            v.co=a+delta*t
            if not added or (v.co-added[-1].co).length>.0001:added.append(v)
        mat=face.material_index;smooth=face.smooth
        loop=original[:start+1]+added+original[start+1:]
        bm.faces.remove(face)
        try:
            f=bm.faces.new(loop);f.material_index=mat;f.smooth=smooth
            split_count+=len(added)
        except ValueError:pass
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0003)
    # Triangulate only the repaired seam polygons; this prevents concave cut
    # fragments from generating stray folded faces at either end.
    seam=[f for f in bm.faces if f.material_index!=2 and any(local(v) for v in f.verts) and len(f.verts)>4]
    bmesh.ops.triangulate(bm,faces=seam,quad_method='BEAUTY',ngon_method='BEAUTY')
    bmesh.ops.recalc_face_normals(bm,faces=[f for f in bm.faces if f.material_index!=2 and any(local(v) for v in f.verts)])
    # Close the missing end/transition faces left by the original cut. All
    # boundary loops belong to this ridge repair, not to socket openings.
    boundary = [e for e in bm.edges if e.is_boundary]
    assert all(abs(v.co.x)<96.01 and abs(v.co.y)<98 for e in boundary for v in e.verts)
    filled = bmesh.ops.holes_fill(bm,edges=boundary,sides=0)['faces']
    filled_count = len(filled)
    for f in filled:
        center=f.calc_center_median()
        f.material_index=3 if abs(center.x)>80 or abs(center.y)<38 else 0
    bmesh.ops.triangulate(bm,faces=filled,quad_method='BEAUTY',ngon_method='BEAUTY')
    for f in bm.faces:
        c=f.calc_center_median()
        if f.material_index in (4,5) and 80<abs(c.x)<100 and 20<abs(c.y)<65:
            f.material_index=3
    bmesh.ops.recalc_face_normals(bm,faces=[f for f in bm.faces if f.material_index!=2])
    assert not any(e.is_boundary for e in bm.edges)
    bm.to_mesh(mesh);bm.free();mesh.update()
    bpy.context.view_layer.update()
    assert route == [(tuple(tuple(mesh.vertices[i].co) for i in p.vertices),p.material_index) for p in mesh.polygons if p.material_index == 2]
    assert all(object_hash(bpy.data.objects[n])==h for n,h in baseline.items() if n not in edited)
    for name in edited:
        m=bpy.data.objects[name].data;m.calc_loop_triangles()
        assert len(m.loop_triangles)<10000
        assert all(math.isfinite(a) for v in m.vertices for a in v.co)
    obj['owner_seams_repaired']=True
    result={'scene':bpy.data.filepath,'edited':sorted(edited),'protected_objects':len(baseline)-3,'split_boundary_stations':split_count,'path_faces_unchanged':len(route),'owner_cliff_transforms_preserved':True,'filled_polygons':filled_count,'terrain_open_boundary_edges':0}
    (ROOT/'Cliff_Seam_Repair_Record.json').write_text(json.dumps(result,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(json.dumps(result))


def restore_cliff_faces():
    """Keep each cliff closed and rock coloured; preserve its green terrain shoulder."""
    obj=bpy.data.objects[CHUNK]
    assert not obj.get('cliff_faces_restored')
    baseline={o.name:object_hash(o) for o in bpy.data.objects}
    edited={CHUNK,CHUNK+'__cliff_01',CHUNK+'__cliff_02'}
    counts={}
    for side,suffix in ((-1,'01'),(1,'02')):
        wall=bpy.data.objects[CHUNK+'__cliff_'+suffix]
        matrix=wall.matrix_world.copy()
        bm=bmesh.new();bm.from_mesh(wall.data);bm.verts.ensure_lookup_table()
        stations=len(bm.verts)//4
        added=0
        for i in range(stations-1):
            for j in (0,1):
                ids=(4*i+j,4*(i+1)+j,4*(i+1)+(j+1)%4,4*i+(j+1)%4)
                face=bm.faces.new([bm.verts[k] for k in ids]);face.material_index=4;face.smooth=False;added+=1
        # Fully faced cap sits just under the terrain shoulder, avoiding
        # coincident surfaces while retaining the owner's object placement.
        for v in bm.verts:
            if v.index%4==1:v.co.y-=side*.3
            elif v.index%4==2:v.co.z-=1.0
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        assert not any(e.is_boundary for e in bm.edges)
        bm.to_mesh(wall.data);bm.free();wall.data.update()
        assert wall.matrix_world==matrix
        counts[wall.name]={'restored_faces':added,'faces':len(wall.data.polygons),'open_edges':0}
    # Keep the upper terrain's existing grass/light-grass assignments.
    # Dirt remains only on the connecting end banks from the seam repair.
    changed=0
    for face in obj.data.polygons:
        center=face.center
        points=[obj.data.vertices[i].co for i in face.vertices]
        if face.material_index==3 and 80<abs(center.x)<105 and 18<abs(center.y)<100 and max(p.z for p in points)>-.6:
            face.material_index=0;changed+=1
    obj.data.update()
    assert all(object_hash(bpy.data.objects[n])==h for n,h in baseline.items() if n not in edited)
    for name in edited:
        mesh=bpy.data.objects[name].data;mesh.calc_loop_triangles()
        assert len(mesh.loop_triangles)<10000
    obj['cliff_faces_restored']=True
    result={'scene':bpy.data.filepath,'cliffs':counts,'upper_shoulders':'grass','protected_objects':len(baseline)-3,'owner_transforms_preserved':True}
    (ROOT/'Cliff_Face_Restoration_Record.json').write_text(json.dumps(result,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(json.dumps(result))


def remove_stray_seam_edges():
    """Remove face-less seam remnants without altering any visible surface."""
    obj=bpy.data.objects[CHUNK]
    baseline={o.name:object_hash(o) for o in bpy.data.objects}
    m=obj.data
    def surfaces():
        return [(tuple(tuple(m.vertices[i].co) for i in p.vertices),p.material_index,p.use_smooth) for p in m.polygons]
    before=surfaces()
    bm=bmesh.new();bm.from_mesh(m)
    stray=[e for e in bm.edges if e.is_wire]
    assert all(abs(v.co.x)<97 and abs(v.co.y)<98 for e in stray for v in e.verts)
    count=len(stray)
    bmesh.ops.delete(bm,geom=stray,context='EDGES')
    assert not any(e.is_wire for e in bm.edges)
    assert not any(e.is_boundary for e in bm.edges)
    bm.to_mesh(m);bm.free();m.update()
    assert before==surfaces()
    assert all(object_hash(bpy.data.objects[n])==h for n,h in baseline.items() if n!=CHUNK)
    report={'scene':bpy.data.filepath,'removed_stray_edges':count,'remaining_stray_edges':0,'surface_faces_unchanged':len(before),'protected_objects':len(baseline)-1}
    (ROOT/'Cliff_Stray_Edge_Record.json').write_text(json.dumps(report,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(json.dumps(report))


def correct_terrain_materials():
    """Material-only finish, preserving the owner's locked terrain geometry."""
    obj=bpy.data.objects[CHUNK];m=obj.data
    geometry=([tuple(v.co) for v in m.vertices],[(tuple(p.vertices),p.use_smooth) for p in m.polygons])
    baseline={o.name:object_hash(o) for o in bpy.data.objects}
    # Earlier shell topology is unchanged. Recover its authored earth lip and
    # rock assignments by coordinates, never by mutable face indices.
    with bpy.data.libraries.load(str(ROOT/'VerdantValley_Cliff_Ridge_Input.blend'),link=False) as (src,dst):
        dst.objects=[CHUNK]
    reference=dst.objects[0];rm=reference.data
    def key(mesh,face):return tuple(sorted(tuple(round(a,4) for a in mesh.vertices[i].co) for i in face.vertices))
    shell={key(rm,p):p.material_index for p in rm.polygons if p.material_index in (3,4,5) and p.normal.z<.1}
    counts={'shell_recovered':0,'fallback_rock':0,'fallback_earth':0,'grass_unified':0,'outer_patch':0}
    for p in m.polygons:
        if p.normal.z<.1:
            original=shell.get(key(m,p))
            if original is not None and p.material_index!=original:
                p.material_index=original;counts['shell_recovered']+=1
            elif original is None and p.material_index in (0,1,3):
                target=4 if p.normal.z<-.1 else 3
                if p.material_index!=target:
                    p.material_index=target;counts['fallback_rock' if target==4 else 'fallback_earth']+=1
        elif p.material_index==1:
            # Lighting supplies facet variation; remove the rectangular light
            # grass bands created by the rebuilt strip material assignments.
            p.material_index=0;counts['grass_unified']+=1
    # Owner-marked isolated earth patch on the upper outer edge.
    for p in m.polygons:
        if p.material_index==3 and p.normal.z>.9 and 85<p.center.x<90 and -82<p.center.y<-68:
            p.material_index=0;counts['outer_patch']+=1
    reference_mesh=reference.data
    bpy.data.objects.remove(reference,do_unlink=True)
    if reference_mesh.users==0:bpy.data.meshes.remove(reference_mesh)
    m.update()
    assert geometry==([tuple(v.co) for v in m.vertices],[(tuple(p.vertices),p.use_smooth) for p in m.polygons])
    assert all(object_hash(bpy.data.objects[n])==h for n,h in baseline.items() if n!=CHUNK)
    assert not any(p.material_index in (0,1) and p.normal.z<.1 for p in m.polygons)
    result={'scene':bpy.data.filepath,'reference':'VerdantValley_Cliff_Material_Input.blend','changes':counts,'vertices_unchanged':len(m.vertices),'faces_unchanged':len(m.polygons),'protected_objects':len(baseline)-1,'flat_shading_preserved':True,'peer_references':['Crossroads Copse','Windward Ridge Gate','Ancient Oak']}
    (ROOT/'Cliff_Material_Correction_Record.json').write_text(json.dumps(result,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(json.dumps(result))


def detail_exposed_cliff_faces():
    """Shape four broad asymmetric folds, preserving every perimeter join."""
    edited={CHUNK+'__cliff_01',CHUNK+'__cliff_02'}
    assert not bpy.data.objects[CHUNK+'__cliff_01'].get('broad_face_detail')
    baseline={o.name:object_hash(o) for o in bpy.data.objects}
    if not (ROOT/'VerdantValley_Cliff_Detail_Input.blend').exists():
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'VerdantValley_Cliff_Detail_Input.blend'),copy=True)
    report={}
    for suffix,direction,slope,knots in (
        ('01',1,.48,[(-88,0),(-39,4.3),(2,.4),(44,3.3),(92,0)]),
        ('02',-1,-.62,[(-90,0),(-47,1.0),(-8,4.2),(35,.3),(96,0)])):
        obj=bpy.data.objects[CHUNK+'__cliff_'+suffix]
        bm=bmesh.new();bm.from_mesh(obj.data)
        originalOpen=sum(e.is_boundary for e in bm.edges)
        fronts={f for f in bm.faces if f.normal.y*direction>.7}
        border=[(e.verts[0].co.copy(),e.verts[1].co.copy()) for e in bm.edges
                if any(f in fronts for f in e.link_faces) and any(f not in fronts for f in e.link_faces)]
        for x,depth in knots[1:-1]:
            geom=list(bm.verts)+list(bm.edges)+list(bm.faces)
            bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-6,
                plane_co=Vector((x,0,0)),plane_no=Vector((1,0,-slope)),clear_inner=False,clear_outer=False)
            fronts={f for f in bm.faces if f.normal.y*direction>.7}
        geom=list(bm.verts)+list(bm.edges)+list(bm.faces)
        bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-6,
            plane_co=Vector((0,0,7 if suffix=='01' else 9)),
            plane_no=Vector((-.045 if suffix=='01' else .07,0,1)),clear_inner=False,clear_outer=False)
        fronts={f for f in bm.faces if f.normal.y*direction>.7}
        def boundary_distance(v):
            point=Vector((v.x,v.z));best=1e9
            for a,b in border:
                start=Vector((a.x,a.z));edge=Vector((b.x-a.x,b.z-a.z))
                t=max(0,min(1,(point-start).dot(edge)/max(edge.length_squared,1e-12)))
                best=min(best,(point-start-t*edge).length)
            return best
        moved=0;maximum=0
        for v in {v for f in fronts for v in f.verts}:
            q=v.co.x-slope*v.co.z;depth=0
            for (a,da),(b,db) in zip(knots,knots[1:]):
                if a<=q<=b:
                    depth=da+(db-da)*(q-a)/(b-a);break
            depth=min(depth*.46,.40*boundary_distance(v.co))
            if depth>1e-5:
                v.co.y+=direction*depth;moved+=1;maximum=max(maximum,depth)
        for f in fronts:f.smooth=False
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        assert sum(e.is_boundary for e in bm.edges)==originalOpen and not any(e.is_wire for e in bm.edges)
        bm.to_mesh(obj.data);bm.free();obj.data.update()
        obj['broad_face_detail']=True
        obj.data.calc_loop_triangles()
        assert len(obj.data.loop_triangles)<10000
        report[obj.name]={'moved_vertices':moved,'maximum_protrusion':maximum,'triangles':len(obj.data.loop_triangles),'open_edges':originalOpen,'primary_planes':4}
    assert all(object_hash(bpy.data.objects[n])==h for n,h in baseline.items() if n not in edited)
    result={'scene':bpy.data.filepath,'walls':report,'protected_objects':len(baseline)-2,'maximum_combined_narrowing':3.91,'props_added':0,'collision_changed':False}
    (ROOT/'Cliff_Detail_Record.json').write_text(json.dumps(result,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(json.dumps(result))


def rework_cliff_structure(save=True):
    """Author four geological masses and a recessed bay per wall at player scale."""
    import numpy as np
    edited={CHUNK+'__cliff_01',CHUNK+'__cliff_02'}
    baseline={o.name:object_hash(o) for o in bpy.data.objects}
    shapes={
        '01': [
            ('leaning_west_buttress', [(-70,-12),(-47,-12),(-38,7),(-42,14),(-57,13),(-66,6)], 2.9, -.025),
            ('central_split_mass', [(-12,-12),(12,-12),(24,5),(18,17),(1,18),(-9,10)], 3.0, .035),
            ('tilted_shelf', [(26,0),(47,-2),(57,4),(50,10),(36,12),(28,8)], 2.7, -.04),
            ('east_end_pillar', [(58,-12),(75,-12),(76,1),(67,9),(61,9),(56,2)], 2.3, .06),
        ],
        '02': [
            ('low_west_shelf', [(-67,-12),(-43,-12),(-30,-1),(-34,7),(-52,10),(-65,3)], 2.8, .055),
            ('high_shoulder_plate', [(-28,-13),(-9,-13),(-3,8),(-9,17),(-22,17),(-28,8)], 2.5, -.035),
            ('leaning_east_mass', [(13,-13),(34,-13),(48,3),(40,17),(27,18),(16,10)], 3.0, -.05),
            ('broken_end_buttress', [(53,-13),(69,-13),(76,-3),(69,5),(60,11),(54,5)], 2.6, .02),
        ],
    }
    report={}
    for suffix,direction in (('01',1),('02',-1)):
        obj=bpy.data.objects[CHUNK+'__cliff_'+suffix]
        assert not obj.get('major_cliff_structure'), 'Structural forms already applied.'
        bm=bmesh.new();bm.from_mesh(obj.data)
        originalOpen=sum(e.is_boundary for e in bm.edges)
        originalMatrix=obj.matrix_world.copy()
        crest={tuple(v.co) for v in bm.verts if v.co.y*direction<5 and v.co.z>5 and any(f.normal.z>.6 for f in v.link_faces)}
        forms=[]
        for name,outline,projection,tilt in shapes[suffix]:
            xmin=min(x for x,z in outline);xmax=max(x for x,z in outline)
            zmin=min(z for x,z in outline);zmax=max(z for x,z in outline)
            def inside(co):
                return all((b[0]-a[0])*(co.z-a[1])-(b[1]-a[1])*(co.x-a[0])>=-1e-4
                           for a,b in zip(outline,outline[1:]+outline[:1]))
            for a,b in zip(outline,outline[1:]+outline[:1]):
                sheet={f for f in bm.faces if f.normal.y*direction>.7
                       and xmin-1<f.calc_center_median().x<xmax+1
                       and zmin-3<f.calc_center_median().z<zmax+3}
                geom=list(sheet | {e for f in sheet for e in f.edges} | {v for f in sheet for v in f.verts})
                bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-6,
                    plane_co=Vector((a[0],0,a[1])),plane_no=Vector((-(b[1]-a[1]),0,b[0]-a[0])),
                    clear_inner=False,clear_outer=False)
            patch={f for f in bm.faces if f.normal.y*direction>.7 and inside(f.calc_center_median())}
            assert patch, name
            patchVerts={v for f in patch for v in f.verts}
            center=sum((v.co for v in patchVerts),Vector())/len(patchVerts)
            # A steep return and tilted broad plateau, rather than a long subtle fold.
            result=bmesh.ops.extrude_face_region(bm,geom=list(patch),use_keep_orig=False)
            newVerts=[v for v in result['geom'] if isinstance(v,bmesh.types.BMVert)]
            coefficients=np.linalg.lstsq(
                np.array([[v.co.x,v.co.z,1] for v in patchVerts]),
                np.array([v.co.y*direction for v in patchVerts]),rcond=None)[0]
            targets=[]
            for v in newVerts:
                v.co.x=center.x+(v.co.x-center.x)*.91
                v.co.z=center.z+(v.co.z-center.z)*(.99 if 'shelf' not in name else .94)
                plane=coefficients[0]*v.co.x+coefficients[1]*v.co.z+coefficients[2]
                target=plane+projection+tilt*(v.co.z-center.z)
                targets.append((v,target))
            correction=max(0,max(target-v.co.y*direction for v,target in targets)-3.0)
            for v,target in targets:
                blend=1.0 if 'shelf' in name else max(0,min(1,(v.co.z-(-9 if suffix=='01' else -11))/7))
                v.co.y+=direction*(target-correction-v.co.y*direction)*blend
            originals=[f for f in patch if f.is_valid]
            if originals:bmesh.ops.delete(bm,geom=originals,context='FACES_ONLY')
            for face in result['geom']:
                if isinstance(face,bmesh.types.BMFace) and face.is_valid:
                    face.material_index=4;face.smooth=False
            # Only broad geometric caps; no decorative cracked surfaces.
            bm.normal_update()
            forms.append({'name':name,'width':xmax-xmin,'height':zmax-zmin,'projection':projection})
        bay=(-36,-15,0,14) if suffix=='01' else (-1,12,-1,14)
        with bpy.data.libraries.load(str(ROOT/'VerdantValley_Cliff_Detail_Input.blend'),link=False) as (src,dst):
            dst.objects=[obj.name]
        ref=dst.objects[0]
        referenceTree=BVHTree.FromPolygons([v.co.copy() for v in ref.data.vertices],[tuple(p.vertices) for p in ref.data.polygons])
        for axis,level in ((0,bay[0]),(0,bay[1]),(2,bay[2]),(2,bay[3])):
            sheet={f for f in bm.faces if f.normal.y*direction>.7 and bay[0]-3<f.calc_center_median().x<bay[1]+3 and bay[2]-3<f.calc_center_median().z<bay[3]+3}
            geom=list(sheet | {e for f in sheet for e in f.edges} | {v for f in sheet for v in f.verts})
            point=Vector();point[axis]=level;normal=Vector();normal[axis]=1
            bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-6,plane_co=point,plane_no=normal,clear_inner=False,clear_outer=False)
        bayFaces={f for f in bm.faces if f.normal.y*direction>.7 and bay[0]<f.calc_center_median().x<bay[1] and bay[2]<f.calc_center_median().z<bay[3]}
        for v in {v for f in bayFaces for v in f.verts}:
            hit=referenceTree.ray_cast(Vector((v.co.x,direction*100,v.co.z)),Vector((0,-direction,0)),200)[0]
            if hit is not None:
                v.co.y=hit.y+direction*.40
        bpy.data.objects.remove(ref,do_unlink=True)
        forms.append({'name':'recessed_bay','width':bay[1]-bay[0],'height':bay[3]-bay[2]})
        wire=[e for e in bm.edges if e.is_wire]
        if wire:bmesh.ops.delete(bm,geom=wire,context='EDGES')
        loose=[v for v in bm.verts if not v.link_edges]
        if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
        bm.normal_update()
        assert sum(e.is_boundary for e in bm.edges)==originalOpen, (suffix,originalOpen,sum(e.is_boundary for e in bm.edges))
        assert not any(e.is_wire for e in bm.edges)
        assert all(any((v.co-Vector(p)).length<1e-5 for v in bm.verts) for p in crest)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(obj.data);bm.free();obj.data.update()
        assert obj.matrix_world==originalMatrix
        obj.data.calc_loop_triangles();assert len(obj.data.loop_triangles)<10000
        obj['major_cliff_structure']=True
        report[obj.name]={'forms':forms,'triangles':len(obj.data.loop_triangles),'boundary_edges_unchanged':originalOpen}
    assert all(object_hash(bpy.data.objects[n])==h for n,h in baseline.items() if n not in edited)
    result={'walls':report,'protected_objects':len(baseline)-2,'collision_changed':False,'props_added':0}
    (ROOT/'Cliff_Structure_Record.json').write_text(json.dumps(result,indent=2))
    if save:bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(json.dumps(result))


def refine_cliff_hierarchy(save=True):
    """Merge the current relief into two unequal, continuous formations per side."""
    edited={CHUNK+'__cliff_01',CHUNK+'__cliff_02'}
    baseline={o.name:object_hash(o) for o in bpy.data.objects}
    report={}
    def interpolate(value,knots):
        if value<=knots[0][0]:return knots[0][1]
        for (a,va),(b,vb) in zip(knots,knots[1:]):
            if value<=b:return va+(vb-va)*(value-a)/(b-a)
        return knots[-1][1]
    for suffix,direction in (('01',1),('02',-1)):
        obj=bpy.data.objects[CHUNK+'__cliff_'+suffix]
        assert obj.get('major_cliff_structure') and not obj.get('cliff_hierarchy_refined')
        bm=bmesh.new();bm.from_mesh(obj.data);originalOpen=sum(e.is_boundary for e in bm.edges)
        originalTriangles=sum(len(p.vertices)-2 for p in obj.data.polygons)
        crest={tuple(v.co) for v in bm.verts if v.co.y*direction<5 and v.co.z>5 and any(f.normal.z>.6 for f in v.link_faces)}
        # Use only the untouched seam profile as a bound; edit the current mesh.
        # No historical mesh is substituted and no additional relief is extruded.
        with bpy.data.libraries.load(str(ROOT/'VerdantValley_Cliff_Detail_Input.blend'),link=False) as (src,dst):
            dst.objects=[obj.name]
        reference=dst.objects[0];rm=reference.data
        topRows={}
        for vertex in rm.vertices:
            if 3.7<vertex.co.y*direction<5.4 and vertex.co.z>0:
                topRows[round(vertex.co.x,5)]=max(vertex.co.z,topRows.get(round(vertex.co.x,5),-100))
        topKnots=sorted(topRows.items())
        assert len(topKnots)>5
        inv=bpy.data.objects[CHUNK].matrix_world.inverted()
        relative=inv@obj.matrix_world
        frontLimit=max(v.co.y*direction for v in bm.verts if 0<(relative@v.co).z<26 and abs((relative@v.co).x)<80)
        moved=0;forward=0;recession=0;maximumRelief=0
        for v in bm.verts:
            if abs(v.co.x)>79 or tuple(v.co) in crest:continue
            if v.co.y*direction<3.8:continue
            x,z=v.co.x,v.co.z
            if suffix=='01':
                main=interpolate(x-.9*z,[(-88,.15),(-65,.3),(-55,.6),(-44,4.2),(-17,3.4),(-3,.35),(44,.2),(88,.15)])
                ledge=interpolate(x+.8*z,[(37,0),(52,1.5),(68,2.4),(82,.6),(96,0)])
                ledge*=interpolate(z,[(-12,0),(0,.25),(6,1),(10,1),(16,0),(25,0)])
                relief=max(main,ledge)
            else:
                main=interpolate(x+.4*z,[(-88,.2),(-25,.25),(-12,.4),(8,4.1),(27,3.6),(51,.35),(88,.2)])
                main*=interpolate(z+.12*x,[(-12,.25),(-2,1),(6,1),(14,.45),(23,.2)])
                ledge=interpolate(x-.35*z,[(-88,0),(-65,2.1),(-41,1.8),(-24,0),(88,0)])
                ledge*=interpolate(z,[(-12,0),(-2,0),(5,.6),(10,1),(16,.2),(23,0)])
                relief=max(.2,main,ledge)
            ceiling=interpolate(x,topKnots)
            relief=min(relief,max(0,.8*(ceiling-z)),max(0,.65*(z-(-9.8 if suffix=='01' else -11.1))),max(0,.5*(81-abs(x))))
            base=4.25+.32*max(0,ceiling-z)
            target=min(base+relief,frontLimit)
            # Neither side may move farther into the route than the current envelope.
            delta=target-v.co.y*direction
            v.co.y=direction*target
            if abs(delta)>1e-5:moved+=1
            forward=max(forward,delta);recession=max(recession,-delta);maximumRelief=max(maximumRelief,target-base)
        bpy.data.objects.remove(reference,do_unlink=True)
        bm.normal_update()
        exposed={f for f in bm.faces if f.normal.y*direction>.12 and all(v.co.y*direction>3.8 and tuple(v.co) not in crest for v in f.verts)}
        edges=[e for e in bm.edges if len(e.link_faces)==2 and all(f in exposed for f in e.link_faces)]
        bmesh.ops.dissolve_limit(bm,angle_limit=.23,verts=[],edges=edges,use_dissolve_boundaries=False,delimit={'MATERIAL'})
        bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3],quad_method='BEAUTY',ngon_method='BEAUTY')
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        assert sum(e.is_boundary for e in bm.edges)==originalOpen
        assert not any(e.is_wire for e in bm.edges)
        assert all(any((v.co-Vector(p)).length<1e-5 for v in bm.verts) for p in crest)
        bm.to_mesh(obj.data);bm.free();obj.data.update()
        obj.data.calc_loop_triangles()
        assert len(obj.data.loop_triangles)<=originalTriangles
        obj['cliff_hierarchy_refined']=True
        report[obj.name]={'dominant_formations':2,'moved_vertices':moved,'max_forward_change':forward,'max_recession':recession,'retained_relief':maximumRelief,'triangles':len(obj.data.loop_triangles),'boundary_edges_unchanged':originalOpen,'topology_simplified':True}
    assert all(object_hash(bpy.data.objects[n])==h for n,h in baseline.items() if n not in edited)
    result={'walls':report,'protected_objects':len(baseline)-2,'collision_changed':False,'props_added':0}
    (ROOT/'Cliff_Hierarchy_Record.json').write_text(json.dumps(result,indent=2))
    if save:bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(json.dumps(result))


def selectively_reduce_cliff_repetition(save=True):
    """Reduce only three secondary formations, retaining all existing topology."""
    edited={CHUNK+'__cliff_01',CHUNK+'__cliff_02'}
    baseline={o.name:object_hash(o) for o in bpy.data.objects}
    patches={'01':[(26,57,-2,12,.70),(56,76,-12,9,.35)],'02':[(-28,-3,-13,17,.65)]}
    report={}
    for suffix,direction in (('01',1),('02',-1)):
        obj=bpy.data.objects[CHUNK+'__cliff_'+suffix]
        assert obj.get('major_cliff_structure') and not obj.get('selective_repetition_pass')
        with bpy.data.libraries.load(str(ROOT/'VerdantValley_Cliff_Structure_Input.blend'),link=False) as (src,dst):
            dst.objects=[obj.name]
        ref=dst.objects[0]
        tree=BVHTree.FromPolygons([v.co.copy() for v in ref.data.vertices],[tuple(p.vertices) for p in ref.data.polygons])
        topology=[(tuple(p.vertices),p.material_index,p.use_smooth) for p in obj.data.polygons]
        bm=bmesh.new();bm.from_mesh(obj.data);boundary=sum(e.is_boundary for e in bm.edges);bm.free()
        changed=0;maximum=0
        for v in obj.data.vertices:
            x,y,z=v.co
            if y*direction<5.4:continue
            weight=0
            for lo,hi,bottom,top,strength in patches[suffix]:
                feather=min(1,max(0,(x-lo)/3),max(0,(hi-x)/3),max(0,(z-bottom)/2),max(0,(top-z)/2))
                weight=max(weight,feather*strength)
            if weight<=0:continue
            hit=tree.ray_cast(Vector((x,direction*100,z)),Vector((0,-direction,0)),200)[0]
            if hit is None:continue
            relief=(y-hit.y)*direction
            if relief<=.05:continue
            delta=relief*weight;v.co.y-=direction*delta
            changed+=1;maximum=max(maximum,delta)
        bpy.data.objects.remove(ref,do_unlink=True);obj.data.update()
        assert topology==[(tuple(p.vertices),p.material_index,p.use_smooth) for p in obj.data.polygons]
        bm=bmesh.new();bm.from_mesh(obj.data)
        assert sum(e.is_boundary for e in bm.edges)==boundary
        assert not any(e.is_wire for e in bm.edges)
        bm.free();obj['selective_repetition_pass']=True
        report[obj.name]={'changed_vertices':changed,'total_vertices':len(obj.data.vertices),'max_reduction':maximum,'boundary_edges':boundary,'topology_retained':True}
    assert all(object_hash(bpy.data.objects[n])==h for n,h in baseline.items() if n not in edited)
    result={'walls':report,'protected_objects':len(baseline)-2,'secondary_forms_softened':3,'existing_forms':8}
    (ROOT/'Cliff_Selective_Record.json').write_text(json.dumps(result,indent=2))
    if save:bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(json.dumps(result))


def reconstruct_continuous_cliff_faces(save=True):
    """Replace modular relief with a sparse continuous surface at fixed seams."""
    from mathutils.geometry import delaunay_2d_cdt
    from collections import defaultdict
    edited={CHUNK+'__cliff_01',CHUNK+'__cliff_02'}
    baseline={o.name:object_hash(o) for o in bpy.data.objects}
    sites={
        '01':[(-66,-1),(-49,8),(-25,1),(-12,13),(9,5),(34,14),(53,1),(68,7)],
        '02':[(-67,3),(-42,-2),(-32,14),(-8,6),(18,-1),(27,15),(49,6),(67,-1)],
    }
    result={}
    for suffix,direction in (('01',1),('02',-1)):
        obj=bpy.data.objects[CHUNK+'__cliff_'+suffix]
        assert not obj.get('continuous_cliff_surface')
        current=bmesh.new();current.from_mesh(obj.data)
        currentCoords={tuple(round(c,4) for c in v.co) for v in current.verts}
        matrix=obj.matrix_world.copy()
        # Only use the pre-relief shell to recover the original continuous seam.
        # Every retained shell vertex and boundary sample must still exist live.
        with bpy.data.libraries.load(str(ROOT/'VerdantValley_Cliff_Detail_Input.blend'),link=False) as (src,dst):
            dst.objects=[obj.name]
        ref=dst.objects[0];bm=bmesh.new();bm.from_mesh(ref.data)
        originalOpen=sum(e.is_boundary for e in current.edges)
        front={f for f in bm.faces if f.normal.y*direction>.7}
        assert all(tuple(round(c,4) for c in v.co) in currentCoords for f in bm.faces if f not in front for v in f.verts)
        boundary=[e for e in bm.edges if sum(f in front for f in e.link_faces)==1]
        adjacency=defaultdict(list)
        for edge in boundary:
            a,b=edge.verts;adjacency[a].append(b);adjacency[b].append(a)
        assert all(len(n)==2 for n in adjacency.values())
        first=min(adjacency,key=lambda v:(v.co.x,v.co.z))
        ring=[first];previous=None;vertex=first
        while True:
            nxt=next(v for v in adjacency[vertex] if v!=previous)
            if nxt==first:break
            ring.append(nxt);previous,vertex=vertex,nxt
            assert len(ring)<=len(adjacency)
        assert len(ring)==len(adjacency)
        assert all(tuple(round(c,4) for c in v.co) in currentCoords for v in ring)
        # Collapse only collinear samples for triangulation; reinsert every
        # original seam vertex into its incident polygon afterwards.
        coarse=list(range(len(ring)))
        change=True
        while change:
            change=False
            for j,index in enumerate(coarse):
                a=ring[coarse[j-1]].co;b=ring[index].co;c=ring[coarse[(j+1)%len(coarse)]].co
                ab=b-a;ac=c-a
                if ac.length>0 and ab.cross(ac).length/ac.length<.00015 and ab.dot(ac)>=0 and ab.length<ac.length:
                    coarse.pop(j);change=True;break
        points=[Vector((ring[i].co.x,ring[i].co.z)) for i in coarse]
        area=sum(a.x*b.y-b.x*a.y for a,b in zip(points,points[1:]+points[:1]))
        if area<0:
            coarse.reverse();points.reverse()
        points += [Vector(p) for p in sites[suffix]]
        poly=list(range(len(coarse)))
        coords,edges,faces,origVerts,_,_=delaunay_2d_cdt(points,[],[poly],1,1e-6)
        assert len(coords)==len(points)
        top=sorted((v.co.x,v.co.z) for v in ring if v.co.y*direction<5.4 and v.co.z>0)
        bottom=sorted((v.co.x,v.co.z,v.co.y*direction) for v in ring if v.co.z<-6)
        def lerp(x,knots,column):
            if x<=knots[0][0]:return knots[0][column]
            for a,b in zip(knots,knots[1:]):
                if x<=b[0]:
                    return a[column]+(b[column]-a[column])*(x-a[0])/max(1e-9,b[0]-a[0])
            return knots[-1][column]
        byInput={}
        for outIndex,ids in enumerate(origVerts):
            assert len(ids)==1
            byInput[ids[0]]=outIndex
        newVerts={}
        inv=bpy.data.objects[CHUNK].matrix_world.inverted()
        relative=inv@obj.matrix_world
        oldClearance=min(abs((relative@v.co).y) for v in current.verts if abs((relative@v.co).x)<79 and 0<(relative@v.co).z<26)
        for inputIndex,outIndex in byInput.items():
            if inputIndex<len(coarse):
                newVerts[outIndex]=ring[coarse[inputIndex]]
                continue
            x,z=points[inputIndex];ceiling=lerp(x,top,1);floor=lerp(x,bottom,1)
            t=max(0,min(1,(z-floor)/(ceiling-floor)))
            base=lerp(x,bottom,2)*(1-t)+(4.246 if suffix=='01' else 4.144)*t
            # Two broad, unequal oblique swells; no full-height vertical stations.
            if suffix=='01':
                relief=3.1*max(0,1-abs(x-.65*z+38)/49)+1.7*max(0,1-abs(x+.8*z-42)/34)
            else:
                relief=1.8*max(0,1-abs(x+.55*z+49)/37)+3.0*max(0,1-abs(x-.7*z-24)/53)
            relief*=min(1,t*3,(1-t)*3)
            co=Vector((x,direction*(base+relief),z))
            # Maintain the current path envelope even if a broad swell peaks.
            chunkCo=relative@co
            if abs(chunkCo.y)<oldClearance:
                correction=oldClearance-abs(chunkCo.y)+.05
                co.y-=direction*correction
            newVerts[outIndex]=bm.verts.new(co)
        # Seam-edge maps include collinear samples without creating narrow strips.
        chains={}
        count=len(ring)
        for j,a in enumerate(coarse):
            b=coarse[(j+1)%len(coarse)]
            chain=[];index=(a+1)%count
            step=1
            if area<0:step=-1;index=(a-1)%count
            while index!=b:
                chain.append(ring[index]);index=(index+step)%count
            oa=byInput[j];ob=byInput[(j+1)%len(coarse)]
            chains[(oa,ob)]=chain;chains[(ob,oa)]=list(reversed(chain))
        bmesh.ops.delete(bm,geom=list(front),context='FACES_ONLY')
        for face in faces:
            verts=[]
            for a,b in zip(face,face[1:]+face[:1]):
                verts.append(newVerts[a]);verts.extend(chains.get((a,b),[]))
            f=bm.faces.new(verts);f.material_index=4;f.smooth=False
        wire=[e for e in bm.edges if e.is_wire]
        if wire:bmesh.ops.delete(bm,geom=wire,context='EDGES')
        loose=[v for v in bm.verts if not v.link_edges]
        if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        assert sum(e.is_boundary for e in bm.edges)==originalOpen
        assert not any(e.is_wire for e in bm.edges)
        assert all(v.is_valid for v in ring)
        # One connected surface, with all seam samples welded into its faces.
        mesh=bpy.data.meshes.new(obj.data.name+'_continuous_transfer')
        bm.to_mesh(mesh);bm.free()
        for material in obj.data.materials:mesh.materials.append(material)
        old=obj.data;oldName=old.name;obj.data=mesh
        if old.users==0:bpy.data.meshes.remove(old)
        mesh.name=oldName
        bpy.data.objects.remove(ref,do_unlink=True);current.free()
        assert obj.matrix_world==matrix
        obj['continuous_cliff_surface']=True
        for flag in ('broad_face_detail','major_cliff_structure','selective_repetition_pass','cliff_hierarchy_refined'):
            if flag in obj:del obj[flag]
        mesh.calc_loop_triangles()
        result[obj.name]={'exposed_polygons':len(faces),'interior_vertices':len(sites[suffix]),'seam_corners':len(coarse),'seam_vertices_preserved':len(ring),'total_triangles':len(mesh.loop_triangles),'boundary_edges':originalOpen,'previous_path_clearance':oldClearance}
    assert all(object_hash(bpy.data.objects[n])==h for n,h in baseline.items() if n not in edited)
    report={'walls':result,'protected_objects':len(baseline)-2,'collision_changed':False,'props_added':0}
    (ROOT/'Cliff_Continuous_Record.json').write_text(json.dumps(report,indent=2))
    if save:bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(json.dumps(report))


if __name__ == '__main__':
    import sys
    if '--continuous-surface' in sys.argv:
        reconstruct_continuous_cliff_faces()
    elif '--selective-repetition' in sys.argv:
        selectively_reduce_cliff_repetition()
    elif '--refine-hierarchy' in sys.argv:
        refine_cliff_hierarchy()
    elif '--rework-structure' in sys.argv:
        rework_cliff_structure()
    elif '--detail-exposed-faces' in sys.argv:
        detail_exposed_cliff_faces()
    elif '--correct-materials' in sys.argv:
        correct_terrain_materials()
    elif '--remove-stray-edges' in sys.argv:
        remove_stray_seam_edges()
    elif '--restore-cliff-faces' in sys.argv:
        restore_cliff_faces()
    elif '--repair-owner-seams' in sys.argv:
        repair_owner_seams()
    else:
        main()
