"""Helpers for an owner-edited live scene. Call on Blender's main thread only.

Never load, regenerate, save or export a blend automatically. Details are separate
exportable meshes. Targeted original edits require explicit owner authorization.
"""
import bpy
import math
from mathutils import Vector


class DetailMesh:
    """Closed coloured primitives in the source mesh's existing local coordinates."""
    def __init__(self, source, name):
        self.source, self.name = source, name
        self.vertices, self.faces, self.styles = [], [], []

    def solid(self, points, faces, style):
        start = len(self.vertices)
        self.vertices.extend(tuple(p) for p in points)
        self.faces.extend(tuple(start+i for i in f) for f in faces)
        self.styles.extend([style]*len(faces))

    def rod(self, a, b, radius, style, end_radius=None, sides=8):
        a, b = Vector(a), Vector(b)
        axis = (b-a).normalized()
        u = axis.cross(Vector((0,1,0)))
        if u.length < .01:
            u = axis.cross(Vector((1,0,0)))
        u.normalize()
        v = axis.cross(u)
        end_radius = radius if end_radius is None else end_radius
        points = [c+(u*math.cos(k*math.tau/sides)+v*math.sin(k*math.tau/sides))*r
                  for c,r in [(a,radius),(b,end_radius)] for k in range(sides)]
        faces = [tuple(reversed(range(sides))),tuple(range(sides,2*sides))]
        faces += [(k,(k+1)%sides,(k+1)%sides+sides,k+sides) for k in range(sides)]
        self.solid(points,faces,style)

    def box(self, center, u, n, width, height, depth, style):
        c,u,n = Vector(center),Vector(u),Vector(n)
        up = Vector((0,1,0))
        points = [c+u*x*width/2+up*y*height/2+n*z*depth/2
                  for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                                (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        self.solid(points,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),
                           (2,3,7,6),(3,0,4,7)],style)

    def ring(self, center, radius, thickness, style, sides=24):
        c = Vector(center)
        for k in range(sides):
            a,b = k*math.tau/sides,(k+1)*math.tau/sides
            self.rod(c+Vector((radius*math.cos(a),0,radius*math.sin(a))),
                     c+Vector((radius*math.cos(b),0,radius*math.sin(b))),
                     thickness,style,sides=6)

    def finish(self, limit=None):
        if self.name in bpy.data.objects:
            return {'name':self.name,'skipped':'already present'}
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.vertices,[],self.faces)
        mesh.update()
        mesh.calc_loop_triangles()
        triangles = len(mesh.loop_triangles)
        if limit is not None and triangles > limit:
            bpy.data.meshes.remove(mesh)
            raise ValueError(f'{self.name}: {triangles} exceeds {limit}')
        for m in self.source.data.materials:
            mesh.materials.append(m)
        colours = {}
        original = self.source.data.color_attributes.get('Col')
        for style in set(self.styles):
            index = next(i for i,m in enumerate(mesh.materials) if m.name.startswith(style))
            face = next((p for p in self.source.data.polygons if p.material_index==index),None)
            if face:
                colour=tuple(original.data[face.loop_start].color)
            else:
                reference=bpy.data.objects['ES_SANCTUM_TEMPLE_01'].data
                reference_index=next(i for i,m in enumerate(reference.materials) if m.name.startswith(style))
                reference_face=next((p for p in reference.polygons if p.material_index==reference_index),None)
                colour=tuple(mesh.materials[index].diffuse_color)
                if reference_face:
                    colour=tuple(reference.color_attributes['Col'].data[reference_face.loop_start].color)
                else:
                    # Emissive/foliage faces may already live in separate props.
                    for candidate in bpy.data.objects:
                        if candidate.type!='MESH' or not candidate.data.color_attributes.get('Col'):continue
                        ci=next((i for i,m in enumerate(candidate.data.materials) if m.name.startswith(style)),None)
                        cp=next((p for p in candidate.data.polygons if p.material_index==ci),None)
                        if cp:
                            colour=tuple(candidate.data.color_attributes['Col'].data[cp.loop_start].color);break
            colours[style] = index,colour
        attr = mesh.color_attributes.new(name='Col',type='BYTE_COLOR',domain='CORNER')
        for face,style in zip(mesh.polygons,self.styles):
            index,colour = colours[style]
            face.material_index = index
            for loop in face.loop_indices:
                attr.data[loop].color = colour
        obj = bpy.data.objects.new(self.name,mesh)
        self.source.users_collection[0].objects.link(obj)
        obj.matrix_world = self.source.matrix_world.copy()
        return {'name':self.name,'triangles':triangles}


def sanctum_curved_chair():
    """Replace only the requested chair slabs; retain crown, feet and the owner's hall."""
    import bmesh
    source=bpy.data.objects['ES_SANCTUM_TEMPLE_01']
    if source.mode!='OBJECT':return {'skipped':'owner editing temple'}
    if source.get('es_curved_chair'):return {'skipped':'already curved'}
    groups,polygons=components(source)
    remove=[]
    for ids,faces in zip(groups,polygons):
        pts=[source.data.vertices[i].co for i in ids]
        if not all(abs(p.x)<16 and 14.9<p.y<47 and -139<p.z<-124 for p in pts):continue
        lo=[min(p[a] for p in pts) for a in range(3)]
        hi=[max(p[a] for p in pts) for a in range(3)]
        names={source.data.materials[p.material_index].name for p in faces}
        is_block=len(ids)>=8 and max(hi[a]-lo[a] for a in range(3))>5
        mask=len(ids)==8 and any('PortalGlow' in n for n in names)
        post=(len(ids)==12 and 17.6<lo[1]<17.8 and 20.6<hi[1]<20.9
              and abs(sum(p.x for p in pts)/len(pts))>12)
        if is_block or mask or post:remove.extend(ids)
    if not 170<len(remove)<300:raise ValueError('Chair slabs changed; refusing broad replacement')
    backup=source.data.copy();bpy.app.driver_namespace['es_curved_chair_before']=backup
    out=DetailMesh(source,'ES_SANCTUM_CURVED_CHAIR_01')

    def loft(rings,style):
        n=len(rings[0]);points=[p for ring in rings for p in ring]
        faces=[tuple(reversed(range(n))),tuple(range((len(rings)-1)*n,len(rings)*n))]
        for row in range(len(rings)-1):
            faces += [(row*n+k,row*n+(k+1)%n,(row+1)*n+(k+1)%n,(row+1)*n+k) for k in range(n)]
        out.solid(points,faces,style)

    def pad(rx,rz,levels,style,center_z=-130.5):
        rings=[]
        for y,scale in levels:
            ring=[]
            for k in range(40):
                a=k*math.tau/40;c,s=math.cos(a),math.sin(a)
                ring.append((rx*scale*math.copysign(abs(c)**.5,c),y,
                             center_z+rz*scale*math.copysign(abs(s)**.5,s)))
            rings.append(ring)
        loft(rings,style)

    def bowed_panel(rows,front,thickness,style):
        # A subdivided front/back grid gives true curvature with an arched top.
        n=20;points=[]
        for depth in [0,-thickness]:
            for row,(y,width) in enumerate(rows):
                for k in range(n+1):
                    u=2*k/n-1;x=u*width
                    yy=y+(1.5*(1-u*u) if row==len(rows)-1 else 0)
                    points.append((x,yy,front+.85*(x/13)**2+depth))
        layer=len(rows)*(n+1);faces=[]
        for side in [0,1]:
            offset=side*layer
            for row in range(len(rows)-1):
                for k in range(n):
                    a=offset+row*(n+1)+k
                    f=(a,a+1,a+n+2,a+n+1)
                    faces.append(f if side==0 else tuple(reversed(f)))
        boundary=list(range(n+1))
        boundary += [row*(n+1)+n for row in range(1,len(rows))]
        boundary += list(range(layer-2,layer-n-2,-1))
        boundary += [row*(n+1) for row in range(len(rows)-2,0,-1)]
        for a,b in zip(boundary,boundary[1:]+boundary[:1]):faces.append((a,a+layer,b+layer,b))
        out.solid(points,faces,style)

    pad(14.2,5.8,[(15,.97),(15.35,1),(17.3,1),(17.65,.98)],'TempleGold')
    pad(11.3,4.3,[(17.64,.96),(17.83,1),(18.75,1),(19.05,.94)],'IndigoLeaves',-130.25)
    bowed_panel([(17.65,11.6),(19.2,12.3),(25,12.7),(32,12.9),(39,12.5),(44.7,12.1)],
                -136.15,1.45,'TempleIvory')
    bowed_panel([(20.3,8.6),(22,9.4),(31,9.8),(40.9,9.2)],-135.98,.13,'TempleGold')
    bowed_panel([(21.3,7.6),(23,8.35),(31,8.75),(39.9,8.2)],-135.79,.10,'IndigoLeaves')
    # Both rests curve vertically and close onto the original support posts.
    for sign in [-1,1]:
        rings=[]
        for k in range(17):
            t=k/16;z=-135.3+10.0*t;y=21.60+.40*math.sin(math.pi*t)
            radius=.15 if k in [0,16] else (0.75 if k in [1,15] else 1.0)
            rings.append([(sign*13.2+math.cos(a)*1.22*radius,y+math.sin(a)*.86*radius,z)
                          for a in [j*math.tau/12 for j in range(12)]])
        loft(rings,'TempleIvory')
        # The post's bottom meets the widened seat; cap reaches the rest's underside.
        for z in [-126.75,-134.25]:
            out.rod((sign*13.2,17.45,z),(sign*13.2,20.93,z),.48,'TempleGold',sides=12)
    # Gold mask shaped as a symmetric shallow lens, with an elongated crystal eye.
    rings=[]
    for z,scale in [(-135.58,.93),(-135.34,1),(-135.12,.93)]:
        rings.append([(math.cos(a)*2.55*scale,33.9+math.sin(a)*4.25*scale,z)
                      for a in [k*math.tau/24 for k in range(24)]])
    loft(rings,'TempleGold')
    profile=[(0,37.1),(.44,36.2),(.67,33.9),(.44,31.6),(0,30.7),(-.44,31.6),(-.67,33.9),(-.44,36.2)]
    pts=[(x,y,-135.04) for x,y in profile]+[(0,33.9,-134.73)]
    out.solid(pts,[tuple(reversed(range(8)))]+[(k,(k+1)%8,8) for k in range(8)],'PortalGlow')
    result=out.finish()
    obj=bpy.data.objects[out.name]
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data);bm.free();obj.data.update()
    for p in obj.data.polygons:
        style=obj.data.materials[p.material_index].name
        p.use_smooth=False
    # Only now remove the old slabs, after their replacements exist successfully.
    bm=bmesh.new();bm.from_mesh(source.data);bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[bm.verts[i] for i in remove],context='VERTS')
    bm.to_mesh(source.data);bm.free();source.data.update()
    source['es_curved_chair']=True
    # Refitting the existing filigree preserves its design on the bowed insert.
    from mathutils.bvhtree import BVHTree
    surface=BVHTree.FromPolygons([v.co for v in obj.data.vertices],[list(p.vertices) for p in obj.data.polygons])
    inlay=bpy.data.objects['ES_SANCTUM_THRONE_INLAY_01'];groups,_=components(inlay)
    for ids in groups:
        points=[inlay.data.vertices[i].co for i in ids];c=sum(points,Vector())/len(points)
        hit,_,_,_=surface.ray_cast(Vector((c.x,c.y,-120)),Vector((0,0,-1)))
        if hit:
            dz=hit.z+.035-min(p.z for p in points)
            for i in ids:inlay.data.vertices[i].co.z+=dz
    inlay.data.update()
    result['replaced_vertices']=len(remove)
    return result


def chunk_floor_accents(name):
    """Inset trim on genuine broad walking caps; skips props, stairs and thin decals."""
    source=bpy.data.objects[name]
    if source.mode!='OBJECT':return {'name':name,'skipped':'owner editing'}
    detail=name+'_FLOOR_TRIM_01'
    if detail in bpy.data.objects:return {'name':name,'skipped':'already trimmed'}
    mesh=source.data
    groups,group_faces=components(source)
    path_faces=set()
    # Decorative road strips and narrow bridge walking decks are protected.
    for ids,faces in zip(groups,group_faces):
        if not faces or not all(mesh.materials[p.material_index].name.startswith('GoldenPath') for p in faces):continue
        points=[mesh.vertices[i].co for i in ids]
        lo=min(p.y for p in points);hi=max(p.y for p in points)
        if hi-lo>.4:continue
        horizontal=[]
        group=set(ids)
        for edge in mesh.edges:
            a,b=edge.vertices
            if a in group and b in group:
                length=(mesh.vertices[a].co-mesh.vertices[b].co).length
                if length>.01:horizontal.append(length)
        if horizontal and min(horizontal)<35 and max(horizontal)>min(horizontal)*1.5:
            path_faces.update(p.index for p in faces)
    selected=set()
    for p in mesh.polygons:
        material=mesh.materials[p.material_index].name
        y=sum(mesh.vertices[i].co.y for i in p.vertices)/len(p.vertices)
        if (p.index not in path_faces and p.normal.y>.985 and 0<=y<=19 and p.area>2 and
                material.startswith(('AetherMintGrass','GoldenPath','TempleIvory','Cloudstone'))):
            selected.add(p.index)
    adjacency={i:set() for i in selected};edge_faces={}
    for i in selected:
        p=mesh.polygons[i]
        for a,b in zip(p.vertices,list(p.vertices[1:])+[p.vertices[0]]):
            edge_faces.setdefault(tuple(sorted((a,b))),[]).append(i)
    for faces in edge_faces.values():
        if len(faces)==2:
            a,b=faces;adjacency[a].add(b);adjacency[b].add(a)
    from mathutils.bvhtree import BVHTree
    surface=BVHTree.FromPolygons([v.co for v in mesh.vertices],[list(p.vertices) for p in mesh.polygons])

    def supported(a,b):
        for t in [0,.25,.5,.75,1]:
            p=a.lerp(b,t)
            hit,normal,index,distance=surface.ray_cast(p+Vector((0,.35,0)),Vector((0,-1,0)),.65)
            if index in path_faces:return False
            if hit is None or normal.y<.9 or abs(hit.y-(p.y-.12))>.07:return False
        return True
    out=DetailMesh(source,detail);seen=set();patches=0
    variant=sum(ord(c) for c in name)%3
    for start in selected:
        if start in seen:continue
        stack=[start];seen.add(start);region=[]
        while stack:
            i=stack.pop();region.append(i)
            for j in adjacency[i]:
                if j not in seen:seen.add(j);stack.append(j)
        if sum(mesh.polygons[i].area for i in region)<150:continue
        region_set=set(region)
        edges=[edge for edge,faces in edge_faces.items()
               if sum(i in region_set for i in faces)==1]
        graph={}
        for a,b in edges:graph.setdefault(a,[]).append(b);graph.setdefault(b,[]).append(a)
        if not graph or any(len(neighbours)!=2 for neighbours in graph.values()):continue
        remaining=set(graph)
        while remaining:
            first=next(iter(remaining));loop=[first];previous=None;current=first
            while True:
                choices=[i for i in graph[current] if i!=previous]
                nxt=choices[0]
                if nxt==first:break
                if nxt in loop:break
                loop.append(nxt);previous,current=current,nxt
            remaining.difference_update(loop)
            if len(loop)<3:continue
            pts=[mesh.vertices[i].co.copy() for i in loop]
            center=sum(pts,Vector())/len(pts)
            if max((p-center).length for p in pts)<5:continue
            # Convex caps are inset along corner bisectors, joining every trim segment.
            area=sum(a.x*b.z-b.x*a.z for a,b in zip(pts,pts[1:]+pts[:1]))
            sign=1 if area>0 else -1
            def inset(distance):
                result=[]
                for k,p in enumerate(pts):
                    before=p-pts[k-1];after=pts[(k+1)%len(pts)]-p
                    before.y=after.y=0
                    if before.length<.001 or after.length<.001:return []
                    before.normalize();after.normalize()
                    n1=Vector((-before.z,0,before.x))*sign
                    n2=Vector((-after.z,0,after.x))*sign
                    bisector=n1+n2
                    if bisector.length<.001:return []
                    bisector.normalize();denom=bisector.dot(n1)
                    if denom<.35:return []
                    q=p+bisector*distance/denom;q.y+=.12
                    result.append(q)
                return result
            band=inset(.65);inner=inset(1.55)
            if not band or not inner:continue
            for k,(a,b) in enumerate(zip(band,band[1:]+band[:1])):
                if not supported(a,b):continue
                out.rod(a,b,.09,'TempleGold',sides=8)
                if variant==0 or k%3==0:
                    c,d=inner[k],inner[(k+1)%len(inner)]
                    if variant==2:
                        mid=(c+d)/2;c=(c+mid)/2;d=(d+mid)/2
                    if supported(c,d):out.rod(c,d,.055,'TempleIvory',sides=8)
            patches+=1
    if not out.vertices:return {'name':name,'patches':0}
    result=out.finish();result.update({'patches':patches,'variant':variant})
    bpy.data.objects[detail]['CanCollide']=False
    return result


def chunk_structure_accents(name):
    """Fitted shaft collars/ribs, missing crystal-window frames and wall friezes."""
    source=bpy.data.objects[name]
    if source.mode!='OBJECT':return {'name':name,'skipped':'owner editing'}
    detail=name+'_STRUCTURE_TRIM_01'
    if detail in bpy.data.objects:return {'name':name,'skipped':'already accented'}
    mesh=source.data;groups,polygons=components(source)
    out=DetailMesh(source,detail);bodies=windows=walls=0
    existing_arch=name+'_ARCH_DETAIL_01' in bpy.data.objects
    existing_windows=existing_arch or name=='ES_SANCTUM_TEMPLE_01'
    from mathutils.bvhtree import BVHTree
    surface=BVHTree.FromPolygons([v.co for v in mesh.vertices],[list(p.vertices) for p in mesh.polygons])

    window_bounds=[]
    for ids,faces in zip(groups,polygons):
        points=[mesh.vertices[i].co for i in ids]
        if len(ids)==8 and all(mesh.materials[p.material_index].name.startswith('SkyCrystal') for p in faces) and max(p.y for p in points)-min(p.y for p in points)>=5:
            window_bounds.append(([min(p[j] for p in points)-.35 for j in range(3)],
                                  [max(p[j] for p in points)+.35 for j in range(3)]))

    def clear_spans(a,b):
        """Subtract window prisms from trim runs, keeping solid capped ends."""
        spans=[(0.,1.)]
        for low,high in window_bounds:
            lo,hi=0.,1.
            for j in range(3):
                delta=b[j]-a[j]
                if abs(delta)<1e-8:
                    if not low[j]<=a[j]<=high[j]:lo,hi=1.,0.;break
                else:
                    t0,t1=sorted(((low[j]-a[j])/delta,(high[j]-a[j])/delta))
                    lo=max(lo,t0);hi=min(hi,t1)
            if lo>=hi:continue
            next_spans=[]
            for start,end in spans:
                if hi<=start or lo>=end:next_spans.append((start,end));continue
                if start<lo:next_spans.append((start,lo))
                if hi<end:next_spans.append((hi,end))
            spans=next_spans
        return [(a.lerp(b,start),a.lerp(b,end)) for start,end in spans if (end-start)*(b-a).length>.05]
    def collar(bottom,top,y,height):
        n=len(bottom);low=min(p.y for p in bottom);high=max(p.y for p in top)
        c=sum(bottom,Vector())/n
        rings=[]
        for yy,lift in [(y-height/2,.04),(y-height/2,.25),(y+height/2,.25),(y+height/2,.04)]:
            t=(yy-low)/(high-low)
            ring=[]
            for a,b in zip(bottom,top):
                p=a.lerp(b,t);radial=Vector((p.x-c.x,0,p.z-c.z)).normalized()
                ring.append(p+radial*lift)
            rings.append(ring)
        # Each band segment is clipped around the full framed window footprint.
        for k in range(n):
            nxt=(k+1)%n
            a=(rings[1][k]+rings[2][k])/2;b=(rings[1][nxt]+rings[2][nxt])/2
            for start,end in clear_spans(a,b):
                length=(b-a).length
                t0=(start-a).length/length;t1=(end-a).length/length
                points=[ring[k].lerp(ring[nxt],t) for t in [t0,t1] for ring in rings]
                out.solid(points,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'TempleGold')

    for ids,faces in zip(groups,polygons):
        pts=[mesh.vertices[i].co for i in ids];low=min(p.y for p in pts);high=max(p.y for p in pts)
        height=high-low;names={mesh.materials[p.material_index].name for p in faces}
        width=max(p.x for p in pts)-min(p.x for p in pts)
        depth=max(p.z for p in pts)-min(p.z for p in pts)
        if (all(n.startswith('TempleIvory') for n in names) and height>14
                and 2<max(width,depth)<35 and height>max(width,depth)*1.5):
            bottom=[p.copy() for p in pts if abs(p.y-low)<.005]
            top=[p.copy() for p in pts if abs(p.y-high)<.005]
            if len(bottom)==len(top) and len(bottom)>=4:
                cb=sum(bottom,Vector())/len(bottom);ct=sum(top,Vector())/len(top)
                if (Vector((cb.x,0,cb.z))-Vector((ct.x,0,ct.z))).length<.1:
                    bottom.sort(key=lambda p:math.atan2(p.z-cb.z,p.x-cb.x))
                    top.sort(key=lambda p:math.atan2(p.z-ct.z,p.x-ct.x))
                    # Skip existing gold collars; place smaller bands between them.
                    levels=[low+height*.22,low+height*.52,low+height*.80] if height>45 else [low+height*.35,low+height*.72]
                    for y in levels:
                        hit,_,index,_=surface.ray_cast(Vector((cb.x+max(width,depth),y,cb.z)),Vector((-1,0,0)),max(width,depth)*2)
                        if hit is not None and mesh.materials[mesh.polygons[index].material_index].name.startswith('TempleGold'):continue
                        collar(bottom,top,y,.45 if height>45 else .25)
                    if not existing_arch:
                        for k in range(0,len(bottom),max(1,len(bottom)//8)):
                            a=bottom[k].lerp(top[k],.12);b=bottom[k].lerp(top[k],.88)
                            radial=Vector((a.x-cb.x,0,a.z-cb.z)).normalized()
                            for start,end in clear_spans(a+radial*.065,b+radial*.065):
                                out.rod(start,end,.045,'TempleGold',sides=6)
                    bodies+=1
        if len(ids)!=8:continue
        center=sum(pts,Vector())/8
        if (not existing_windows and all(n.startswith('SkyCrystal') for n in names) and height>=5):
            candidates=[p for p in faces if abs(p.normal.y)<.01]
            if not candidates:continue
            area=max(p.area for p in candidates);normals=[]
            for p in candidates:
                if p.area>area*.95 and not any(p.normal.dot(n)>.99 for n in normals):normals.append(p.normal.copy())
            for normal in normals:
                u=Vector((normal.z,0,-normal.x))
                w=max(p.dot(u) for p in pts)-min(p.dot(u) for p in pts)
                d=max(p.dot(normal) for p in pts)-min(p.dot(normal) for p in pts)
                if d>5 or w<1.2:continue
                c=center+normal*(d/2+.08);trim=min(.18,w*.07)
                for sign in [-1,1]:
                    out.box(c+u*sign*(w/2+trim/2),u,normal,trim,height+.36,.14,'TempleGold')
                    out.box(c+Vector((0,sign*(height/2+trim/2),0)),u,normal,w,trim,.14,'TempleGold')
                out.box(c+normal*.015,u,normal,.10,height,.10,'TempleIvory')
                out.box(c+normal*.025,u,normal,w,.10,.10,'TempleGold')
            windows+=1
        if (name!='ES_SANCTUM_TEMPLE_01' and all(n.startswith('TempleIvory') for n in names)
                and height>22 and max(width,depth)>40 and min(width,depth)<5):
            candidates=[p for p in faces if abs(p.normal.y)<.01]
            area=max((p.area for p in candidates),default=0);normals=[]
            for p in candidates:
                if p.area>area*.95 and not any(p.normal.dot(n)>.99 for n in normals):normals.append(p.normal.copy())
            for normal in normals:
                u=Vector((normal.z,0,-normal.x));w=max(p.dot(u) for p in pts)-min(p.dot(u) for p in pts)
                d=max(p.dot(normal) for p in pts)-min(p.dot(normal) for p in pts)
                c=center+normal*(d/2+.14);c.y=low+height*.82
                out.box(c,u,normal,w*.75,.28,.16,'TempleGold')
                for k in [-2,-1,0,1,2]:
                    q=c+u*k*w*.11+Vector((0,-1.3,0))
                    out.rod(q-Vector((0,.45,0)),q,.02,'SkyCrystal',end_radius=.32,sides=4)
                    out.rod(q,q+Vector((0,.45,0)),.32,'SkyCrystal',end_radius=.02,sides=4)
            walls+=1
    if not out.vertices:return {'name':name,'bodies':0,'windows':0,'walls':0}
    result=out.finish();result.update({'bodies':bodies,'windows':windows,'walls':walls})
    obj=bpy.data.objects[detail]
    import bmesh
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
    for p in obj.data.polygons:
        if obj.data.materials[p.material_index].name.startswith('TempleGold') and abs(p.normal.y)<.95:p.use_smooth=True
    obj.data.update()
    return result


def sanctum_throne_filigree():
    source=bpy.data.objects['ES_SANCTUM_TEMPLE_01']
    if source.mode!='OBJECT':
        return {'skipped':'owner editing temple'}
    out=DetailMesh(source,'ES_SANCTUM_THRONE_INLAY_01')
    # Curved paired strokes echo the Ascendant's cuirass filigree, framing its slit.
    for sign in [-1,1]:
        for offset in [0,.7]:
            points=[]
            for k in range(15):
                t=k/14
                x=sign*(5.45+offset-4.0*t*t)
                y=39.0-offset*.4-15.6*t
                points.append((x,y,-135.04))
            for a,b in zip(points,points[1:]):
                out.rod(a,b,.085,'TempleGold',sides=8)
    # A tiny portal core and two branch-like lines break up the lower empty panel.
    out.rod((0,25.2,-135.01),(0,24.4,-135.01),.025,'PortalGlow',end_radius=.55,sides=6)
    out.rod((0,24.4,-135.01),(0,23.2,-135.01),.55,'PortalGlow',end_radius=.025,sides=6)
    for sign in [-1,1]:
        out.rod((sign*.6,23.5,-135.03),(sign*2.5,22.5,-135.03),.07,'TempleGold',sides=6)
    result=out.finish()
    from mathutils.bvhtree import BVHTree
    surface=BVHTree.FromPolygons([v.co for v in source.data.vertices],
                                [list(p.vertices) for p in source.data.polygons])
    obj=bpy.data.objects[out.name]
    groups,_=components(obj)
    for ids in groups:
        pts=[obj.data.vertices[i].co for i in ids]
        center=sum(pts,Vector())/len(pts)
        loc,_,_,_=surface.ray_cast(Vector((center.x,center.y,-120)),Vector((0,0,-1)))
        if loc is None:
            raise ValueError('Throne inlay lacks backing')
        dz=loc.z+.035-min(p.z for p in pts)
        for i in ids:obj.data.vertices[i].co.z+=dz
    obj.data.update()
    return result


def soften_chunk(name):
    """Reversible edge rounding; no base vertices move and no terrain seams bevel."""
    import bmesh
    obj=bpy.data.objects[name]
    if obj.mode!='OBJECT':
        return {'name':name,'skipped':'owner editing'}
    if 'CURVED_CHAIR' in name or 'THRONE_DETAIL' in name or 'THRONE_INLAY' in name:
        return {'name':name,'skipped':'throne retains faceted curved geometry'}
    if 'ES_ARCH_SOFTEN' in obj.modifiers:
        return {'name':name,'skipped':'already softened'}
    mesh=obj.data
    groups,polygons=components(obj)
    eligible=set()
    round_faces=set()
    lookup={i:k for k,ids in enumerate(groups) for i in ids}
    shortest=[math.inf for _ in groups]
    for edge in mesh.edges:
        a,b=edge.vertices
        group=lookup[a]
        shortest[group]=min(shortest[group],(mesh.vertices[a].co-mesh.vertices[b].co).length)
    accepted=0
    architecture=('TempleIvory','TempleGold','SoftWood')
    for k,(ids,faces) in enumerate(zip(groups,polygons)):
        styles={mesh.materials[p.material_index].name for p in faces}
        if not styles or not all(n.startswith(architecture) for n in styles):
            continue
        # Exclude sheets, roofs, walls, plinth floors and all socket boundaries.
        pts=[mesh.vertices[i].co for i in ids]
        dims=[max(p[a] for p in pts)-min(p[a] for p in pts) for a in range(3)]
        if len(ids)>=12:
            round_faces.update(p.index for p in faces)
        if len(ids)!=8 or min(dims)<.7 or shortest[k]<.7 or max(dims[0],dims[2])>35 or dims[1]<3:
            continue
        if min(p.y for p in pts)<.4:
            continue
        if any(max(abs(p.x),abs(p.z))>=127.9 for p in pts):
            continue
        eligible.add(k)
        accepted+=1
    # Edge weights stay on the original mesh; modifier can be removed for exact recovery.
    weight=mesh.attributes.get('bevel_weight_edge')
    if weight is None:
        weight=mesh.attributes.new(name='bevel_weight_edge',type='FLOAT',domain='EDGE')
    bm=bmesh.new();bm.from_mesh(mesh);bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table()
    sharp=mesh.attributes.get('sharp_edge')
    if sharp is None:
        sharp=mesh.attributes.new(name='sharp_edge',type='BOOLEAN',domain='EDGE')
    for edge in bm.edges:
        group=lookup[edge.verts[0].index]
        angle=edge.calc_face_angle(0) if edge.is_manifold else math.pi
        weight.data[edge.index].value=1 if group in eligible and edge.is_manifold and angle>math.radians(60) else 0
        # Keep cap planes and material boundaries crisp; rounded side faces blend.
        if any(f.index in round_faces for f in edge.link_faces):
            sharp.data[edge.index].value=(not edge.is_manifold or angle>math.radians(70)
                or len({f.material_index for f in edge.link_faces})>1)
    bm.free()
    for i in round_faces:
        # Large planar caps retain flat shading.
        p=mesh.polygons[i]
        if abs(p.normal.y)<.98:
            p.use_smooth=True
    mesh.update()
    if accepted:
        bevel=obj.modifiers.new('ES_ARCH_SOFTEN','BEVEL')
        bevel.limit_method='WEIGHT';bevel.width=.18;bevel.segments=3
        bevel.use_clamp_overlap=True;bevel.harden_normals=True
        bevel.material=-1
        normals=obj.modifiers.new('ES_ARCH_NORMALS','WEIGHTED_NORMAL')
        normals.keep_sharp=True;normals.weight=50
    return {'name':name,'rounded_blocks':accepted,'curved_faces':len(round_faces)}


def soften_island_sides(name):
    """Keep terrain undersides faceted; architectural edge bevels are separate."""
    import bmesh
    obj=bpy.data.objects[name]
    if obj.mode!='OBJECT':
        return {'name':name,'skipped':'owner editing'}
    mesh=obj.data
    groups, polygons = components(obj)
    faces=set()
    for group in polygons:
        if any(mesh.materials[p.material_index].name.startswith('Cloudstone') for p in group):
            faces.update(p.index for p in group if
                         mesh.materials[p.material_index].name.startswith(('Cloudstone','TempleGold')))
    sharp=mesh.attributes.get('sharp_edge')
    if sharp is None:
        sharp=mesh.attributes.new(name='sharp_edge',type='BOOLEAN',domain='EDGE')
    bm=bmesh.new();bm.from_mesh(mesh);bm.edges.ensure_lookup_table()
    for e in bm.edges:
        if any(f.index in faces for f in e.link_faces):
            sharp.data[e.index].value=(not e.is_manifold or e.calc_face_angle(0)>math.radians(70)
                or len({f.material_index for f in e.link_faces})>1)
    bm.free()
    for i in faces:mesh.polygons[i].use_smooth=False
    mesh.update()
    return {'name':name,'side_faces':len(faces)}


def sanctum_windows():
    source = bpy.data.objects['ES_SANCTUM_TEMPLE_01']
    if source.mode != 'OBJECT':
        return {'skipped':'owner editing temple'}
    out = DetailMesh(source,'ES_SANCTUM_WINDOW_DETAIL_01')
    groups,polygons = components(source)
    count = 0
    for ids,faces in zip(groups,polygons):
        if len(ids)!=8 or not all('SkyCrystal' in source.data.materials[p.material_index].name for p in faces):
            continue
        pts = [source.data.vertices[i].co for i in ids]
        height = max(p.y for p in pts)-min(p.y for p in pts)
        if height < 12:
            continue
        candidates = [p for p in faces if abs(p.normal.y)<.01]
        area = max(p.area for p in candidates)
        normals = []
        for p in candidates:
            if p.area > area*.95 and not any(p.normal.dot(n)>.99 for n in normals):
                normals.append(p.normal.copy())
        center = sum(pts,Vector())/8
        count += 1
        # Both faces: interior hall and exterior, including the lantern above it.
        for normal in normals:
            u = Vector((normal.z,0,-normal.x))
            width = max(p.dot(u) for p in pts)-min(p.dot(u) for p in pts)
            depth = max(p.dot(normal) for p in pts)-min(p.dot(normal) for p in pts)
            c = center+normal*(depth/2+.14)
            trim = .25
            for sign in [-1,1]:
                out.box(c+u*sign*(width/2+trim/2),u,normal,trim,height+.5,.18,'TempleGold')
                out.box(c+Vector((0,sign*(height/2+trim/2),0)),u,normal,width,trim,.18,'TempleGold')
            out.box(c+normal*.03,u,normal,.18,height,.14,'TempleIvory')
            out.box(c+normal*.04,u,normal,width,.16,.14,'TempleGold')
            # A narrow diamond lattice gives the panes a ceremonial crystal pattern.
            diamond = [c+Vector((0,height*.30,0)),c+u*width*.32,
                       c-Vector((0,height*.30,0)),c-u*width*.32]
            for a,b in zip(diamond,diamond[1:]+diamond[:1]):
                out.rod(a+normal*.09,b+normal*.09,.075,'TempleGold',sides=4)
    result = out.finish()
    result['windows'] = count
    return result


def sanctum_chandelier():
    source = bpy.data.objects['ES_SANCTUM_TEMPLE_01']
    if source.mode != 'OBJECT':
        return {'skipped':'owner editing temple'}
    out = DetailMesh(source,'ES_SANCTUM_CHANDELIER_01')
    center = Vector((0,63,-23))
    out.rod((0,114,-23),(0,86,-23),.32,'TempleGold')
    out.rod((0,85.7,-23),(0,87,-23),1.2,'TempleGold',end_radius=.7)
    out.ring(center,13,.32,'TempleGold')
    out.ring(center+Vector((0,1,0)),13,.17,'TempleIvory')
    out.ring(center+Vector((0,7,0)),8,.27,'TempleGold')
    for k in range(12):
        a = k*math.tau/12
        radial = Vector((math.cos(a),0,math.sin(a)))
        rim = center+radial*13
        upper = center+Vector((0,7,0))+radial*8
        if k%3==0:
            out.rod((0,86,-23),upper,.13,'TempleGold',sides=6)
        out.rod(upper,rim+Vector((0,.6,0)),.16,'TempleGold',sides=6)
        out.rod(rim+Vector((0,.55,0)),rim+Vector((0,1.05,0)),.65,'TempleGold',end_radius=.45)
        out.rod(rim+Vector((0,1.05,0)),rim+Vector((0,3,0)),.5,'SkyCrystal',end_radius=.02,sides=6)
        out.rod(rim-Vector((0,.2,0)),rim-Vector((0,1.5,0)),.12,'TempleGold',sides=6)
        out.rod(rim-Vector((0,1.5,0)),rim-Vector((0,2.2,0)),.08,'SkyCrystal',end_radius=.48,sides=6)
        out.rod(rim-Vector((0,2.2,0)),rim-Vector((0,3.7,0)),.48,'SkyCrystal',end_radius=.02,sides=6)
    out.rod((0,70,-23),(0,65,-23),.25,'TempleGold')
    out.rod((0,65,-23),(0,63,-23),.05,'PortalGlow',end_radius=2,sides=8)
    out.rod((0,63,-23),(0,59,-23),2,'PortalGlow',end_radius=.03,sides=8)
    return out.finish(limit=10000)


def sanctum_door_reliefs():
    source = bpy.data.objects['ES_SANCTUM_TEMPLE_01']
    if source.mode != 'OBJECT':
        return {'skipped':'owner editing temple'}
    out = DetailMesh(source,'ES_SANCTUM_DOOR_DETAIL_01')
    u,n = Vector((1,0,0)),Vector((0,0,1))
    groups,polygons = components(source)
    doors = []
    for ids,faces in zip(groups,polygons):
        if len(ids)!=8 or not all('SoftWood' in source.data.materials[p.material_index].name for p in faces):
            continue
        pts = [source.data.vertices[i].co for i in ids]
        height = max(p.y for p in pts)-min(p.y for p in pts)
        width = max(p.x for p in pts)-min(p.x for p in pts)
        if 35<height<45 and 25<width<32:
            doors.append((sum(pts,Vector())/8,max(p.z for p in pts)))
    if len(doors)!=2:
        raise ValueError('Expected two existing sanctum door leaves; no changes made')
    for c,z in doors:
        x=c.x
        # Recessed perimeter and corner diamonds, clear of the existing central rail.
        for sign in [-1,1]:
            out.box((x+sign*12,27,z+.18),u,n,.30,36,.18,'TempleGold')
            out.box((x,27+sign*18,z+.18),u,n,24,.30,.18,'TempleGold')
        # Faceted mask cheek plates flank the existing luminous slit.
        for sign in [-1,1]:
            points=[(x+sign*.65,37.65,z+.55),(x+sign*2.35,37,z+.55),
                    (x+sign*2.25,33.1,z+.55),(x+sign*.65,32.45,z+.55),
                    (x+sign*.65,37.65,z+.84),(x+sign*2.35,37,z+.70),
                    (x+sign*2.25,33.1,z+.70),(x+sign*.65,32.45,z+.84)]
            if sign<0:
                points=[points[i] for i in [3,2,1,0,7,6,5,4]]
            out.solid(points,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),
                              (2,3,7,6),(3,0,4,7)],'TempleIvory')
        out.box((x,37.8,z+.73),u,n,5.8,.40,.18,'TempleGold')
        # Five gold crown rays surround the existing three crystal shards.
        for dx in [-3,-1.5,0,1.5,3]:
            out.rod((x+dx,38.25,z+.90),(x+dx*1.25,44-abs(dx)*.8,z+.90),
                    .16,'TempleGold',end_radius=.055,sides=6)
        # Robe folds beneath the rail echo the ruler's layered silhouette.
        for dx in [-3,-1.5,0,1.5,3]:
            out.rod((x+dx*.5,24,z+.3),(x+dx*1.6,17,z+.3),.12,
                    'TempleIvory' if dx else 'PortalGlow',sides=4)
        for yy in [13,45]:
            out.rod((x,yy-.75,z+.2),(x,yy,z+.2),.02,'SkyCrystal',end_radius=.7,sides=4)
            out.rod((x,yy,z+.2),(x,yy+.75,z+.2),.7,'SkyCrystal',end_radius=.02,sides=4)
    return out.finish()


def sanctum_throne_presence():
    """Scale only the existing chair, retaining its footing and rear-wall clearance."""
    source = bpy.data.objects['ES_SANCTUM_TEMPLE_01']
    if source.mode != 'OBJECT':
        return {'skipped':'owner editing temple'}
    if source.get('es_throne_enlarged'):
        return {'skipped':'already enlarged'}
    groups,_ = components(source)
    selected = []
    for ids in groups:
        pts = [source.data.vertices[i].co for i in ids]
        if all(abs(p.x)<11 and 9<p.y<48 and -137<p.z<-121 for p in pts):
            selected.extend(ids)
    if not 300<len(selected)<500:
        raise ValueError('Throne topology changed; refusing broad edits')
    # Keep a reversible exact coordinate snapshot in this live session.
    bpy.app.driver_namespace['es_throne_scale_before'] = {
        i:tuple(source.data.vertices[i].co) for i in selected}
    for i in selected:
        p = source.data.vertices[i].co
        p.x *= 1.65
        p.y = 9.6+(p.y-9.6)*1.35
        p.z = -130.5+(p.z+130.5)*1.25
    source.data.update()
    source['es_throne_enlarged'] = True
    out = DetailMesh(source,'ES_SANCTUM_THRONE_DETAIL_01')
    u,n = Vector((1,0,0)),Vector((0,0,1))
    # A wall-side canopy frames the ruler and stays behind the arena boundary.
    for sign in [-1,1]:
        out.box((sign*23,29,-138),u,n,1.4,40,.7,'TempleIvory')
        out.box((sign*23,10,-138),u,n,3.4,1.5,1.2,'TempleGold')
        out.rod((sign*23,49,-138),(sign*14,57,-138),.45,'TempleGold',sides=6)
        out.rod((sign*14,57,-138),(0,62,-138),.45,'TempleGold',sides=6)
        # Armrest sockets, jewels and chased seat edging scale with the chair.
        out.box((sign*13.2,22,-126),u,n,.9,3,.7,'TempleGold')
        out.rod((sign*13.2,23.5,-126),(sign*13.2,25,-126),.55,'SkyCrystal',end_radius=.03,sides=6)
        out.box((sign*9.8,19,-135.6),u,n,.25,18,.20,'TempleGold')
    out.box((0,17.2,-124.6),u,n,25,.30,.20,'TempleGold')
    result = out.finish()
    result['scaled_vertices'] = len(selected)
    result['scale'] = [1.65,1.35,1.25]
    return result


def sanctum_floor_inlay():
    source = bpy.data.objects['ES_SANCTUM_TEMPLE_01']
    if source.mode != 'OBJECT':
        return {'skipped':'owner editing temple'}
    out = DetailMesh(source,'ES_SANCTUM_FLOOR_DETAIL_01')

    def slab(points,style):
        # Solid thin inlay, 0.024 studs above the floor at its highest point.
        n = len(points)
        vertices = [(x,y,z) for y in [6.006,6.024] for x,z in points]
        faces = [tuple(range(n)),tuple(reversed(range(n,2*n)))]
        faces += [(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
        out.solid(vertices,faces,style)

    for k in range(48):
        a,b = k*math.tau/48,(k+1)*math.tau/48
        slab([(r*math.cos(t),-23+r*math.sin(t))
              for r,t in [(83.5,a),(84.2,a),(84.2,b),(83.5,b)]],'TempleGold')
    for k in range(12):
        a=k*math.tau/12
        u=Vector((math.cos(a),math.sin(a)))
        v=Vector((-math.sin(a),math.cos(a)))
        pts=[u*72.5,u*77+v*1.65,u*81.7,u*77-v*1.65]
        slab([(p.x,p.y-23) for p in pts],'SkyCrystal' if k%3==0 else 'TempleGold')
    # Small aisle mosaics leave the central circle, existing rays and dais untouched.
    for sign in [-1,1]:
        for z in [-88,-64,-40,-16,8,32,56]:
            x=sign*94
            outer=[(x,z+3),(x+2,z),(x,z-3),(x-2,z)]
            inner=[(x,z+1.8),(x+1,z),(x,z-1.8),(x-1,z)]
            for k in range(4):
                slab([outer[k],outer[(k+1)%4],inner[(k+1)%4],inner[k]],'TempleGold')
            slab([(x,z+1.5),(x+.7,z),(x,z-1.5),(x-.7,z)],'SkyCrystal')
    # Three approach chevrons inside the doorway, clear of the ring and thresholds.
    for z in [73,79,85]:
        slab([(-9,z),(0,z-3),(9,z),(9,z+.4),(0,z-2.6),(-9,z+.4)],'TempleGold')
    result=out.finish()
    obj=bpy.data.objects.get(out.name)
    if obj:
        obj['CanCollide']=False
    return result


def sanctum_throne_definition():
    """Single-segment chamfers and tapered back, restricted to the enlarged chair."""
    import bmesh
    source=bpy.data.objects['ES_SANCTUM_TEMPLE_01']
    if source.mode!='OBJECT':
        return {'skipped':'owner editing temple'}
    if source.get('es_throne_defined'):
        return {'skipped':'already defined'}
    groups,polygons=components(source)
    target=[]
    tapered=[]
    for ids,faces in zip(groups,polygons):
        if len(ids)!=8:
            continue
        pts=[source.data.vertices[i].co for i in ids]
        if not all(abs(p.x)<15 and 9<p.y<60 and -138.2<p.z<-124 for p in pts):
            continue
        names={source.data.materials[p.material_index].name for p in faces}
        if any('SkyCrystal' in n or 'PortalGlow' in n for n in names):
            continue
        lo=[min(p[a] for p in pts) for a in range(3)]
        hi=[max(p[a] for p in pts) for a in range(3)]
        if hi[1]-lo[1]>15 and hi[0]-lo[0]>10:
            tapered.append((ids,lo[1],hi[1]))
        if min(b-a for a,b in zip(lo,hi))>.30:
            target.append(ids)
    if not target or len(target)>12:
        raise ValueError('Unexpected chair blocks; no edits made')
    backup=source.data.copy()
    bpy.app.driver_namespace['es_throne_definition_before']=backup
    for ids,low,high in tapered:
        for i in ids:
            p=source.data.vertices[i].co
            p.x *= 1-.12*(p.y-low)/(high-low)
    bm=bmesh.new();bm.from_mesh(source.data);bm.verts.ensure_lookup_table()
    edges=[]
    for ids in target:
        verts={bm.verts[i] for i in ids}
        edges.extend(e for e in bm.edges if all(v in verts for v in e.verts))
    try:
        bmesh.ops.bevel(bm,geom=edges,offset=.28,segments=1,affect='EDGES',
                       clamp_overlap=True,profile=.5)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(source.data)
        source.data.update()
        restore_throne_colours(source,backup)
        source['es_throne_defined']=True
    finally:
        bm.free()
    return {'chamfered_blocks':len(target),'tapered_panels':len(tapered),'segments':1}


def restore_throne_colours(source,backup):
    # Bevel interpolation of imported triangle loop colours can pick unrelated
    # defaults. Restore the chair's existing material colours on its faces only.
    original=backup.color_attributes.get('Col')
    current=source.data.color_attributes.get('Col')
    from mathutils.bvhtree import BVHTree
    surface=BVHTree.FromPolygons([v.co for v in backup.vertices],
                                [list(p.vertices) for p in backup.polygons])
    samples={}
    for p in backup.polygons:
        if all(abs(backup.vertices[i].co.x)<15 and 9<backup.vertices[i].co.y<60
               and -138.2<backup.vertices[i].co.z<-124 for i in p.vertices):
            samples.setdefault(p.material_index,tuple(original.data[p.loop_start].color))
    count=0
    for p in source.data.polygons:
        if all(abs(source.data.vertices[i].co.x)<15
               and 9<source.data.vertices[i].co.y<60 and -138.2<source.data.vertices[i].co.z<-124
               for i in p.vertices):
            if p.material_index not in samples:
                _,_,index,_=surface.find_nearest(p.center)
                p.material_index=backup.polygons[index].material_index
            colour=samples.get(p.material_index)
            if colour is None:
                raise ValueError('Unexpected material on a chair bevel')
            for loop in p.loop_indices:current.data[loop].color=colour
            count+=1
    source.data.update()
    return count


def sanctum_facade_reliefs():
    source = bpy.data.objects['ES_SANCTUM_TEMPLE_01']
    if source.mode != 'OBJECT':
        return {'skipped':'owner editing temple'}
    out = DetailMesh(source,'ES_SANCTUM_FACADE_DETAIL_01')
    u,n=Vector((1,0,0)),Vector((0,0,1))
    # Pediment wings echo the Ascendant's rising silhouette around its existing gem.
    for sign in [-1,1]:
        for row in range(3):
            y=70+row*2.7
            points=[(sign*8,y+4,108.25),(sign*28,y,108.25),(sign*(60-row*13),y,108.25)]
            for a,b in zip(points,points[1:]):
                out.rod(a,b,.21,'TempleGold',sides=6)
        out.box((sign*83,68,108.16),u,n,12,.35,.2,'TempleGold')
    # A restrained frieze above the doorway and between the portico capitals.
    for x in [-112,-94,-66,-38,38,66,94,112]:
        out.box((x,62.7,98.25),u,n,6,.35,.18,'TempleGold')
        out.rod((x,60.8,98.27),(x,61.7,98.27),.02,'SkyCrystal',end_radius=.48,sides=4)
        out.rod((x,61.7,98.27),(x,62.5,98.27),.48,'SkyCrystal',end_radius=.02,sides=4)
    # Raised narrow panels on exposed tower faces, below their window belt.
    for tx in [-127,127]:
        for tz in [-143,99]:
            for k in range(8):
                angle=(k+.5)*math.tau/8
                normal=Vector((math.cos(angle),0,math.sin(angle)))
                horizontal=Vector((normal.z,0,-normal.x))
                for y in [16,47]:
                    # Tapering octagonal tower radius determines the actual face plane.
                    radius=11+(9.5-11)*(y-5.5)/(108-5.5)
                    c=Vector((tx,y,tz))+normal*(radius*math.cos(math.pi/8)+.13)
                    out.box(c,horizontal,normal,3.3,14,.16,'TempleIvory')
                    for sign in [-1,1]:
                        out.box(c+horizontal*sign*1.9+normal*.015,horizontal,normal,.18,15,.13,'TempleGold')
    return out.finish()


def sanctum_inner_entry_reliefs():
    source=bpy.data.objects['ES_SANCTUM_TEMPLE_01']
    if source.mode!='OBJECT':
        return {'skipped':'owner editing temple'}
    out=DetailMesh(source,'ES_SANCTUM_ENTRY_WALL_DETAIL_01')
    u,n=Vector((-1,0,0)),Vector((0,0,-1))
    for x in [-94,-58,58,94]:
        out.box((x,31,93.82),u,n,13,32,.18,'TempleIvory')
        for sign in [-1,1]:
            out.box((x+sign*7,31,93.72),u,n,.24,34,.18,'TempleGold')
            out.rod((x+sign*7,48,93.70),(x+sign*4,51,93.70),.15,'TempleGold',sides=4)
            out.rod((x+sign*4,51,93.70),(x,53,93.70),.15,'TempleGold',sides=4)
        out.box((x,14,93.72),u,n,14.5,.30,.18,'TempleGold')
        # Central elongated crystal motif surrounded by two ascending gold strokes.
        diamond=[(x,42,93.62),(x+2.5,35,93.62),(x,28,93.62),(x-2.5,35,93.62)]
        for a,b in zip(diamond,diamond[1:]+diamond[:1]):
            out.rod(a,b,.10,'SkyCrystal',sides=4)
        for sign in [-1,1]:
            out.rod((x+sign*4,23,93.62),(x+sign*4,44,93.62),.10,'TempleGold',sides=4)
            out.rod((x+sign*4,44,93.62),(x+sign*1.3,48,93.62),.10,'TempleGold',sides=4)
        out.box((x,20,93.60),u,n,4.5,.25,.15,'TempleGold')
    out.box((0,51.5,93.76),u,n,62,.35,.18,'TempleGold')
    crest=[(-3,57,93.63),(0,60,93.63),(3,57,93.63),(0,54,93.63)]
    for a,b in zip(crest,crest[1:]+crest[:1]):
        out.rod(a,b,.14,'TempleGold',sides=4)
    for sign in [-1,1]:
        out.rod((sign*5,57,93.63),(sign*14,57,93.63),.10,'SkyCrystal',sides=4)
    return out.finish()


def components(obj):
    mesh = obj.data
    adjacency = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].append(b)
        adjacency[b].append(a)
    seen, groups = set(), []
    for vertex in mesh.vertices:
        if vertex.index in seen:
            continue
        stack, ids = [vertex.index], []
        seen.add(vertex.index)
        while stack:
            index = stack.pop()
            ids.append(index)
            for neighbor in adjacency[index]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        groups.append(ids)
    lookup = {index: k for k, ids in enumerate(groups) for index in ids}
    polygons = [[] for _ in groups]
    for polygon in mesh.polygons:
        polygons[lookup[polygon.vertices[0]]].append(polygon)
    return groups, polygons


def detail_chunk(name):
    source = bpy.data.objects[name]
    if source.mode != 'OBJECT':
        return {'name': name, 'skipped': 'owner editing'}
    detail_name = name + '_ARCH_DETAIL_01'
    if detail_name in bpy.data.objects:
        return {'name': name, 'skipped': 'already detailed'}
    mesh = source.data
    groups, polygons = components(source)
    vertices, faces, styles = [], [], []
    up = Vector((0, 1, 0))

    def box(center, horizontal, normal, width, height, depth, material):
        start = len(vertices)
        corners = [(-1,-1,-1), (1,-1,-1), (1,1,-1), (-1,1,-1),
                   (-1,-1,1), (1,-1,1), (1,1,1), (-1,1,1)]
        vertices.extend(tuple(center + horizontal*x*width/2 + up*y*height/2
                              + normal*z*depth/2) for x,y,z in corners)
        for indices in [(0,3,2,1), (4,5,6,7), (0,1,5,4),
                        (1,2,6,5), (2,3,7,6), (3,0,4,7)]:
            faces.append(tuple(start+i for i in indices))
            styles.append(material)

    windows, bodies = [], []
    edges_by_group = [[] for _ in groups]
    lookup = {index: k for k, ids in enumerate(groups) for index in ids}
    for edge in mesh.edges:
        edges_by_group[lookup[edge.vertices[0]]].append(edge)
    for k, ids in enumerate(groups):
        if len(ids) != 8:
            continue
        points = [mesh.vertices[i].co for i in ids]
        center = sum(points, Vector()) / 8
        low, high = min(p.y for p in points), max(p.y for p in points)
        height = high-low
        names = {mesh.materials[p.material_index].name for p in polygons[k]}
        edges = [mesh.vertices[e.vertices[1]].co-mesh.vertices[e.vertices[0]].co
                 for e in edges_by_group[k]]
        horizontal = [e.length for e in edges if abs(e.y) < .01]
        normals = []
        for p in polygons[k]:
            if abs(p.normal.y) < .01 and not any(p.normal.dot(n) > .99 for n in normals):
                normals.append(p.normal.copy())
        if (any('TempleIvory' in n for n in names) and height > 45
                and horizontal and min(horizontal)>5 and max(horizontal)<35
                and len(normals)==4):
            bodies.append((center, points, low, high, normals))
        lengths = sorted(e.length for e in edges)
        if (not all('SkyCrystal' in n for n in names) or height < 1.5
                or not lengths or lengths[0] > .65):
            continue
        vertical = [p for p in polygons[k] if abs(p.normal.y)<.01]
        if not vertical:
            continue
        area = max(p.area for p in vertical)
        windows.append((center, points, height, lengths[0],
                        [p for p in vertical if p.area>area*.95]))
    for center, points, height, depth, candidates in windows:
        # Panel normal points away from the wall, including rotated towers.
        if bodies:
            origin = min((b[0] for b in bodies), key=lambda v:(v-center).length)
        else:
            nearby = [p.center for p in mesh.polygons
                      if 'TempleIvory' in mesh.materials[p.material_index].name
                      and (p.center-center).length < height*3]
            origin = min(nearby, key=lambda v:(v-center).length) if nearby else Vector((0,center.y,0))
        normal = max(candidates, key=lambda p:p.normal.dot(center-origin)).normal.copy()
        horizontal = Vector((normal.z,0,-normal.x))
        width = max(p.dot(horizontal) for p in points)-min(p.dot(horizontal) for p in points)
        center = center+normal*(depth/2+.10)
        trim = min(.22,width*.055)
        for side in [-1,1]:
            box(center+horizontal*side*(width/2+trim/2),horizontal,normal,
                trim,height+2*trim,.16,'TempleGold')
            box(center+up*side*(height/2+trim/2),horizontal,normal,
                width,trim,.16,'TempleGold')
        box(center+normal*.025,horizontal,normal,trim*.65,height,.12,'TempleIvory')
        box(center+normal*.035,horizontal,normal,width,trim*.65,.12,'TempleGold')
    for center, points, low, high, normals in bodies:
        floors = max(2,round((high-low)/22))
        for normal in normals:
            horizontal = Vector((normal.z,0,-normal.x))
            width = max(p.dot(horizontal) for p in points)-min(p.dot(horizontal) for p in points)
            depth = max(p.dot(normal) for p in points)-min(p.dot(normal) for p in points)
            face_center = center+normal*(depth/2+.09)
            for floor in range(floors):
                bottom = low+2+(high-low-11)*floor/floors
                top = low+2+(high-low-11)*(floor+1)/floors
                height = top-bottom-2
                panel_center = face_center.copy()
                panel_center.y = (top+bottom)/2
                box(panel_center,horizontal,normal,width*.68,height*.76,.14,'TempleIvory')
                for side in [-1,1]:
                    box(panel_center+horizontal*side*width*.38+normal*.035,
                        horizontal,normal,.18,height,.12,'TempleGold')
    if not vertices:
        return {'name':name,'windows':0,'columns':0}
    spec = {}
    for style in set(styles):
        material = next(i for i,m in enumerate(mesh.materials) if m.name.startswith(style))
        polygon = next(p for p in mesh.polygons if p.material_index==material)
        attribute = mesh.color_attributes.get('Col')
        color = tuple(attribute.data[polygon.loop_start].color) if attribute else (1,1,1,1)
        spec[style] = material,color
    out = bpy.data.meshes.new(detail_name)
    out.from_pydata(vertices,[],faces)
    out.update()
    for material in mesh.materials:
        out.materials.append(material)
    attribute = out.color_attributes.new(name='Col',type='BYTE_COLOR',domain='CORNER')
    for polygon,style in zip(out.polygons,styles):
        material,color = spec[style]
        polygon.material_index = material
        for loop in polygon.loop_indices:
            attribute.data[loop].color = color
    obj = bpy.data.objects.new(detail_name,out)
    source.users_collection[0].objects.link(obj)
    obj.matrix_world = source.matrix_world.copy()
    return {'name':name,'windows':len(windows),'columns':len(bodies),'triangles':len(faces)*2}


def clear_floor_trim_collisions(name):
    """Remove complete decorative trim primitives crossing roads or solid structures."""
    import bmesh
    from mathutils.bvhtree import BVHTree
    source=bpy.data.objects[name];trim=bpy.data.objects.get(name+'_FLOOR_TRIM_01')
    if not trim:return {'name':name,'trim_removed':0}
    if source.mode!='OBJECT' or trim.mode!='OBJECT':return {'name':name,'skipped':'owner editing'}
    groups,faces=components(trim)
    own=BVHTree.FromPolygons([v.co for v in trim.data.vertices],[list(p.vertices) for p in trim.data.polygons])
    group_for_face={p.index:k for k,polys in enumerate(faces) for p in polys}
    remove=set()
    targets=[source]+[o for o in source.users_collection[0].objects if o.type=='MESH' and o.name.startswith(name+'_') and o!=trim and not any(t in o.name for t in ['FOLIAGE','FLOOR_TRIM','STRUCTURE_TRIM'])]
    for target in targets:
        transform=trim.matrix_world.inverted()@target.matrix_world
        tree=BVHTree.FromPolygons([transform@v.co for v in target.data.vertices],[list(p.vertices) for p in target.data.polygons])
        remove.update(group_for_face[a] for a,b in own.overlap(tree))
    # Flat roads can sit just above the trim; test their full footprint.
    roads=[list(p.vertices) for p in source.data.polygons if abs(p.normal.y)>.99 and source.data.materials[p.material_index].name.startswith('GoldenPath')]
    road_tree=BVHTree.FromPolygons([v.co for v in source.data.vertices],roads) if roads else None
    if road_tree:
        for k,ids in enumerate(groups):
            if k in remove:continue
            points=[trim.data.vertices[i].co for i in ids]
            samples=points+[sum(points,Vector())/len(points)]
            if any(road_tree.ray_cast(point+Vector((0,.5,0)),Vector((0,-1,0)),1.)[0] is not None for point in samples):remove.add(k)
    if remove:
        bpy.app.driver_namespace.setdefault('es_trim_clearance_before',{})[trim.name]=trim.data.copy()
        bm=bmesh.new();bm.from_mesh(trim.data);bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm,geom=[bm.verts[i] for k in remove for i in groups[k]],context='VERTS');bm.to_mesh(trim.data);bm.free();trim.data.update()
    return {'name':name,'trim_removed':len(remove)}


def clear_window_trim_collisions(name):
    """Remove added architectural trim penetrating source window glass."""
    import bmesh
    from mathutils.bvhtree import BVHTree
    source=bpy.data.objects[name]
    if source.mode!='OBJECT':return {'window_trim_skipped':name}
    groups,polys=components(source)
    glass=[]
    for ids,faces in zip(groups,polys):
        points=[source.data.vertices[i].co for i in ids]
        if len(ids)==8 and max(p.y for p in points)-min(p.y for p in points)>5 and all(source.data.materials[p.material_index].name.startswith('SkyCrystal') for p in faces):
            glass.extend(list(p.vertices) for p in faces)
    if not glass:return {'window_trim_removed':0}
    tree=BVHTree.FromPolygons([v.co for v in source.data.vertices],glass)
    count=0
    for suffix in ['_STRUCTURE_TRIM_01','_ARCH_DETAIL_01']:
        trim=bpy.data.objects.get(name+suffix)
        if not trim or trim.mode!='OBJECT':continue
        groups,faces=components(trim)
        lookup={p.index:k for k,polys in enumerate(faces) for p in polys}
        own=BVHTree.FromPolygons([v.co for v in trim.data.vertices],[list(p.vertices) for p in trim.data.polygons])
        remove={lookup[a] for a,b in own.overlap(tree)}
        if remove:
            bpy.app.driver_namespace.setdefault('es_trim_clearance_before',{})[trim.name]=trim.data.copy()
            bm=bmesh.new();bm.from_mesh(trim.data);bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm,geom=[bm.verts[i] for k in remove for i in groups[k]],context='VERTS');bm.to_mesh(trim.data);bm.free();trim.data.update();count+=len(remove)
    return {'window_trim_removed':count}


def fit_path_bridge_transitions(name):
    """Clip flat path decals against nearby bridge decks, preserving road seams."""
    import bmesh
    source=bpy.data.objects[name]
    if source.mode!='OBJECT':return {'name':name,'skipped':'owner editing'}
    mesh=source.data;groups,polygons=components(source);decks=[]
    for ids,faces in zip(groups,polygons):
        pts=[mesh.vertices[i].co for i in ids]
        if len(ids)==8 and all(mesh.materials[p.material_index].name.startswith('GoldenPath') for p in faces) and max(p.y for p in pts)-min(p.y for p in pts)>=1:
            top=max(faces,key=lambda p:p.normal.y)
            if top.normal.y>.7:
                # Studio/FBX imports triangulate the top: recover its entire boundary.
                indices={i for p in faces if p.normal.dot(top.normal)>.999 and abs((p.center-top.center).dot(top.normal))<.02 for i in p.vertices}
                points=sorted((mesh.vertices[i].co.copy() for i in indices),key=lambda p:(p.x,p.z))
                cross=lambda a,b,c:(b.x-a.x)*(c.z-a.z)-(b.z-a.z)*(c.x-a.x)
                lower=[];upper=[]
                for point in points:
                    while len(lower)>=2 and cross(lower[-2],lower[-1],point)<=0:lower.pop()
                    lower.append(point)
                for point in reversed(points):
                    while len(upper)>=2 and cross(upper[-2],upper[-1],point)<=0:upper.pop()
                    upper.append(point)
                decks.append(lower[:-1]+upper[:-1])
    stair=bpy.data.objects.get(name+'_STAIR_DETAIL_01')
    if stair and source.get('es_garden_stair_rebuilt'):
        decks.extend([[stair.data.vertices[i].co.copy() for i in p.vertices] for p in stair.data.polygons if p.normal.y>.7 and stair.data.materials[p.material_index].name.startswith('GoldenPath')])
    if not decks:return {'name':name,'path_faces':0}
    trim=bpy.data.objects.get(name+'_FLOOR_TRIM_01')
    if trim and trim.mode=='OBJECT':
        trim_groups,_=components(trim);remove=[]
        for ids in trim_groups:
            points=[trim.data.vertices[i].co for i in ids]
            a=min(points,key=lambda p:(p.x,p.z));b=max(points,key=lambda p:(p.x,p.z))
            samples=points+[a.lerp(b,t) for t in [.25,.5,.75]]
            blocked=False
            for deck in decks:
                normal=(deck[1]-deck[0]).cross(deck[2]-deck[0])
                if abs(normal.y)<1e-5:continue
                for p in samples:
                    height=deck[0].y-(normal.x*(p.x-deck[0].x)+normal.z*(p.z-deck[0].z))/normal.y
                    signs=[(v.x-u.x)*(p.z-u.z)-(v.z-u.z)*(p.x-u.x) for u,v in zip(deck,deck[1:]+deck[:1])]
                    if abs(p.y-height)<.35 and (all(s>=-.01 for s in signs) or all(s<=.01 for s in signs)):blocked=True;break
                if blocked:break
            if blocked:remove.extend(ids)
        if remove:
            bm=bmesh.new();bm.from_mesh(trim.data);bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm,geom=[bm.verts[i] for i in remove],context='VERTS');bm.to_mesh(trim.data);bm.free();trim.data.update()
    def half(poly,value):
        inside=[];outside=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            av,bv=value(a),value(b)
            (inside if av>=0 else outside).append(a)
            if (av>=0)!=(bv>=0):
                hit=a.lerp(b,av/(av-bv));inside.append(hit);outside.append(hit)
        return inside,outside
    def area(poly):
        return abs(sum(a.x*b.z-b.x*a.z for a,b in zip(poly,poly[1:]+poly[:1])))/2 if len(poly)>=3 else 0
    replacements=[]
    for ids,faces in zip(groups,polygons):
        pts=[mesh.vertices[i].co for i in ids]
        if max(p.y for p in pts)-min(p.y for p in pts)>.001:continue
        for p in faces:
            style=mesh.materials[p.material_index].name
            if not style.startswith(('GoldenPath','TempleGold','PaleGoldSoil')) or abs(p.normal.y)<.99:continue
            original=[mesh.vertices[i].co.copy() for i in p.vertices];parts=[original]
            for deck in decks:
                if not min(v.y for v in deck)-.35<=p.center.y<=max(v.y for v in deck)+.35:continue
                # A road stops at the complete deck edge. Clipping only the height
                # intersection leaves a stripe protruding underneath a sloping stair.
                clip=list(deck)
                if area(clip)<.01:continue
                if sum(a.x*b.z-b.x*a.z for a,b in zip(clip,clip[1:]+clip[:1]))<0:clip.reverse()
                fragments=[]
                for part in parts:
                    inside=part
                    for a,b in zip(clip,clip[1:]+clip[:1]):
                        inside,outside=half(inside,lambda v:(b.x-a.x)*(v.z-a.z)-(b.z-a.z)*(v.x-a.x))
                        if area(outside)>.001:fragments.append(outside)
                        if len(inside)<3:break
                parts=fragments
            if abs(sum(area(part) for part in parts)-area(original))>.001:
                replacements.append((p.index,parts))
    if not replacements:return {'name':name,'path_faces':0}
    bpy.app.driver_namespace.setdefault('es_path_transition_before',{})[name]=mesh.copy()
    bm=bmesh.new();bm.from_mesh(mesh);bm.faces.ensure_lookup_table()
    original_faces=list(bm.faces)
    colours=bm.loops.layers.color.get('Col')
    for index,parts in replacements:
        face=original_faces[index];material=face.material_index;normal=face.normal.copy()
        colour=tuple(face.loops[0][colours]) if colours else None
        for points in parts:
            fresh=bm.faces.new([bm.verts.new(p) for p in points]);fresh.material_index=material
            if colours:
                for loop in fresh.loops:loop[colours]=colour
            fresh.normal_update()
            if fresh.normal.dot(normal)<0:fresh.normal_flip()
        bm.faces.remove(face)
    loose=[v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm,geom=loose,context='VERTS');bm.to_mesh(mesh);bm.free();mesh.update()
    return {'name':name,'path_faces':len(replacements)}


def garden_stair_rebuild():
    """Replace the diagonal stair and foot landing with one continuous route."""
    import bmesh
    source=bpy.data.objects['ES_TERRACED_GARDENS']
    assert source.mode=='OBJECT', 'Owner is editing Gardens'
    name=source.name+'_STAIR_DETAIL_01'
    assert not source.get('es_garden_stair_rebuilt'), 'Already rebuilt'
    mesh=source.data
    assert len(mesh.vertices)>2110 and abs(mesh.vertices[1630].co.y-10.06)<.1
    bpy.app.driver_namespace['es_garden_stair_rebuild_before']=mesh.copy()
    out=DetailMesh(source,name)
    upper=[mesh.vertices[i].co.copy() for i in [1630,1633]]
    # Keep the accepted upper landing; terminate the slope well inside the lower
    # platform, then turn smoothly into its north/south approach direction.
    center=(upper[0]+upper[1])/2
    foot=Vector((0,.06,-98))
    direction=Vector((foot.x-center.x,0,foot.z-center.z)).normalized()
    across=Vector((-direction.z,0,direction.x))
    feet=[foot+across*8,foot-across*8]
    # Pair left/right sides using the closest corresponding upper edge.
    if (feet[0]-upper[0]).length>(feet[1]-upper[0]).length:feet.reverse()
    ends=[Vector((8 if p.x>0 else -8,.06,-109)) for p in feet]
    footprint=[upper[0],feet[0],ends[0],ends[1],feet[1],upper[1]]
    bottom=[p-Vector((0,1.2,0)) for p in footprint]
    faces=[(0,1,4,5),(1,2,3,4),(11,10,7,6),(10,9,8,7)]
    faces += [(k,(k+1)%6,(k+1)%6+6,k+6) for k in range(6)]
    out.solid(footprint+bottom,faces,'GoldenPath')
    for t in [k/10 for k in range(1,10)]:
        a=upper[0].lerp(feet[0],t);b=upper[1].lerp(feet[1],t)
        out.rod(a+Vector((0,.055,0)),b+Vector((0,.055,0)),.12,'SoftWood',sides=4)
    # Posts and handrails follow both deck edges through the landing turn.
    for start,foot,end in zip(upper,feet,ends):
        points=[start.lerp(foot,k/5) for k in range(6)]+[foot.lerp(end,.5),end]
        for p in points:
            out.box(p+Vector((0,2.8,0)),(1,0,0),(0,0,1),.9,5.6,.9,'SoftWood')
        for a,b in zip(points,points[1:]):
            for height in [3.0,5.0]:
                out.rod(a+Vector((0,height,0)),b+Vector((0,height,0)),.22,'TempleGold',sides=4)
        # Continuous stringers meet the underside; no detached support blocks.
        for a,b in [(start,foot),(foot,end)]:
            out.rod(a+Vector((0,-1.65,0)),b+Vector((0,-1.65,0)),.6,'SoftWood',sides=4)
    old=bpy.data.objects.get(name)
    if old:
        assert old.mode=='OBJECT'
        bpy.data.objects.remove(old,do_unlink=True)
    report=out.finish()
    new=bpy.data.objects[name]
    bm=bmesh.new();bm.from_mesh(new.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(new.data);bm.free()
    # Only this stair/foot assembly's original components are replaced.
    bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[bm.verts[i] for i in range(1626,2110)],context='VERTS')
    bm.to_mesh(mesh);bm.free();mesh.update()
    source['es_garden_stair_rebuilt']=True
    report['foot_landing_inside_platform']=True
    return report


def garden_bridge_joint():
    """Miter the existing deck ends together, fitting their actual supports."""
    source = bpy.data.objects['ES_TERRACED_GARDENS']
    assert source.mode == 'OBJECT', 'Owner is editing Gardens'
    if source.get('es_garden_bridge_joint'):
        return {'already_fitted': True}
    mesh = source.data
    assert abs(mesh.vertices[1630].co.y-10.0121)<.01, 'Unexpected deck topology'
    bpy.app.driver_namespace['es_garden_joint_before'] = mesh.copy()
    def intersection(a,b,c,d):
        p = Vector((a.x,a.z)); r = Vector((b.x-a.x,b.z-a.z))
        q = Vector((c.x,c.z)); s = Vector((d.x-c.x,d.z-c.z))
        cross = lambda u,v:u.x*v.y-u.y*v.x
        return p+r*cross(q-p,s)/cross(r,s)
    v = mesh.vertices
    joints = [intersection(v[1630].co,v[1631].co,v[1471].co,v[1470].co),
              intersection(v[1633].co,v[1632].co,v[1472].co,v[1473].co)]
    for joint,top,bottom in zip(joints,[(1630,1471),(1633,1472)],[(1626,1467),(1629,1468)]):
        for i in top:v[i].co = (joint.x,10.06,joint.y)
        for i in bottom:v[i].co = (joint.x,8.86,joint.y)
    # Carry both existing stringers through to the same miter plane.
    a,b = joints
    for base in [1818,1930]:
        for end,start in [(base,base+1),(base+3,base+2),(base+4,base+5),(base+7,base+6)]:
            p = v[end].co.copy()
            q = v[start].co.copy()
            hit = intersection(p,q,Vector((a.x,0,a.y)),Vector((b.x,0,b.y)))
            v[end].co = (hit.x,8.86 if end in [base+4,base+7] else 6.46,hit.y)
    # Seat the landing's cross members against its underside.
    for i in range(1610,1626):v[i].co.y += 1.9
    mesh.update()
    filler=bpy.data.objects.get(source.name+'_STAIR_DETAIL_01')
    if filler:
        assert filler.mode=='OBJECT'
        # Only the rejected upper junction is in scope; preserve the foot landing.
        import bmesh
        bm=bmesh.new();bm.from_mesh(filler.data);bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm,geom=list(bm.verts)[6:],context='VERTS')
        bm.to_mesh(filler.data);bm.free();filler.data.update()
    source['es_garden_bridge_joint']=True
    return {'shared_deck_seam': [list(p) for p in joints], 'upper_fillers':0}


def shrine_portal_and_room():
    """Revamp the shrine and add a separate, named indoor arena to the live kit."""
    import bmesh
    from mathutils import Matrix
    source=bpy.data.objects['ES_CAP_SEALED_SHRINE']
    assert source.mode=='OBJECT', 'Owner is editing shrine'
    assert 'ES_SHRINE_MINIBOSS_ROOM' not in bpy.data.objects, 'Room already exists'
    mesh=source.data;groups,polys=components(source);remove=[]
    for ids,faces in zip(groups,polys):
        pts=[mesh.vertices[i].co for i in ids]
        styles={mesh.materials[p.material_index].name for p in faces}
        if (max(abs(p.x) for p in pts)<=16 and min(p.z for p in pts)>=22
                and max(p.z for p in pts)<=31 and min(p.y for p in pts)>=-.1
                and max(p.y for p in pts)<=25
                and all(n.startswith(('TempleIvory','TempleGold','Cloudstone','PortalGlow')) for n in styles)):
            remove.extend(ids)
    assert len(remove)>100, 'Unexpected original shrine geometry'
    bpy.app.driver_namespace['es_shrine_before']=mesh.copy()
    def box(out,c,w,h,d,style):out.box(c,(1,0,0),(0,0,1),w,h,d,style)
    def slab(out,outline,top,bottom,style):
        n=len(outline)
        pts=[(x,y,z) for y in [top,bottom] for x,z in outline]
        out.solid(pts,[tuple(range(n)),tuple(reversed(range(n,2*n)))]+
                  [(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)],style)
    def arch(out,cx,spring,z,inner,outer,depth,style,sides=16):
        pts=[]
        for zz,r in [(z-depth/2,inner),(z-depth/2,outer),(z+depth/2,inner),(z+depth/2,outer)]:
            pts.extend((cx+r*math.cos(k*math.pi/sides),spring+r*math.sin(k*math.pi/sides),zz) for k in range(sides+1))
        n=sides+1;faces=[]
        for k in range(sides):
            faces.extend([(k,k+1,n+k+1,n+k),(2*n+k,3*n+k,3*n+k+1,2*n+k+1),
                          (k,2*n+k,2*n+k+1,k+1),(n+k,n+k+1,3*n+k+1,3*n+k)])
        faces += [(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)]
        out.solid(pts,faces,style)
    def gem(out,c,r,h,style,sides=8):
        c=Vector(c);points=[c+Vector((r*math.cos(k*math.tau/sides),0,r*math.sin(k*math.tau/sides))) for k in range(sides)]
        points += [c+Vector((0,h*.6,0)),c-Vector((0,h*.4,0))]
        out.solid(points,[(k,(k+1)%sides,sides) for k in range(sides)]+
                         [((k+1)%sides,k,sides+1) for k in range(sides)],style)
    made=[]
    def finish(out,matrix=None,parent=None,collision=True):
        report=out.finish();obj=bpy.data.objects[out.name]
        bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
        for p in obj.data.polygons:p.use_smooth=False
        if parent:obj.parent=parent
        if matrix is not None:obj.matrix_world=matrix
        obj['CanCollide']=collision
        made.append(report)
        return obj
    entrance=DetailMesh(source,'ES_SHRINE_PORTAL_ENTRANCE_01')
    for x in [-10.5,10.5]:
        box(entrance,(x,7.5,24),3,15,4,'TempleIvory')
        for y,height,width in [(.35,.7,3.8),(2.4,.35,3.2),(14.65,.7,3.6)]:
            box(entrance,(x,y,24),width,height,4.4,'TempleGold')
        # Front relief stays outside the walk-through aperture.
        box(entrance,(x,8,26.08),.3,9,.12,'TempleGold')
        gem(entrance,(x,11,26.35),.52,1.7,'SkyCrystal')
    arch(entrance,0,15,24,9,12,4,'TempleIvory')
    arch(entrance,0,15,26.07,9.05,9.32,.12,'TempleGold')
    arch(entrance,0,15,26.07,11.6,11.9,.12,'TempleGold')
    box(entrance,(0,26.2,24),3.2,1.8,4.2,'TempleGold')
    gem(entrance,(0,28,24),1.3,4,'PortalGlow')
    for k in range(1,16):
        a=k*math.pi/16
        entrance.rod((9.55*math.cos(a),15+9.55*math.sin(a),26.16),
                     (11.35*math.cos(a),15+11.35*math.sin(a),26.16),.055,'TempleGold',sides=4)
    # Threshold is flush with the island floor; no steps or center obstruction.
    box(entrance,(0,-.35,24),18,.7,5,'GoldenPath')
    finish(entrance)
    veil=DetailMesh(source,'ES_SHRINE_PORTAL_SURFACE_01')
    profile=[(-8.85,.06),(8.85,.06),(8.85,15)]+[(8.85*math.cos(k*math.pi/16),15+8.85*math.sin(k*math.pi/16)) for k in range(1,17)]
    n=len(profile);pts=[(x,y,z) for z in [23.94,24.02] for x,y in profile]
    veil.solid(pts,[tuple(reversed(range(n))),tuple(range(n,2*n))]+
               [(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)],'PortalGlow')
    surface=finish(veil,collision=False);surface['purpose']='walk-through portal visual; teleport trigger supplied in Studio'
    # Remove only the original sealed facade after replacements exist.
    bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[bm.verts[i] for i in remove],context='VERTS');bm.to_mesh(mesh);bm.free();mesh.update()
    # Put the standalone interior beyond the rightmost existing kit geometry.
    right=max((o.matrix_world@Vector(c)).x for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('ES_') for c in o.bound_box)
    matrix=source.matrix_world.copy();matrix.translation.x=right+160
    root=bpy.data.objects.new('ES_SHRINE_MINIBOSS_ROOM',None);source.users_collection[0].objects.link(root);root.matrix_world=matrix
    root.empty_display_type='PLAIN_AXES';root.empty_display_size=8
    root['purpose']='standalone indoor miniboss arena; owner controls hidden placement and teleport'
    root['clear_fighting_area']='76 x 76 studs; floor y=0, ceiling y=42 in author coordinates'
    outline=[(-42,-56),(42,-56),(48,-50),(48,50),(42,56),(-42,56),(-48,50),(-48,-50)]
    shell=DetailMesh(source,'ES_SHRINE_MINIBOSS_ROOM_SHELL_01')
    slab(shell,outline,0,-2,'TempleIvory')
    for a,b in zip(outline,outline[1:]+outline[:1]):
        if a[1]==56 and b[1]==56:continue
        delta=Vector((b[0]-a[0],0,b[1]-a[1]));u=delta.normalized();normal=Vector((-u.z,0,u.x))
        shell.box(((a[0]+b[0])/2,21,(a[1]+b[1])/2),u,normal,delta.length,42,3,'TempleIvory')
    for x in [-27.5,27.5]:box(shell,(x,21,56),39,42,3,'TempleIvory')
    box(shell,(0,31,56),16,22,3,'TempleIvory')
    slab(shell,[(-10,56),(10,56),(10,72),(-10,72)],0,-2,'TempleIvory')
    for x in [-11.5,11.5]:box(shell,(x,11,64),3,22,16,'TempleIvory')
    finish(shell,matrix,root)
    detail=DetailMesh(source,'ES_SHRINE_MINIBOSS_ROOM_DETAIL_01')
    # Collars and vertical ribs are wall-side; the center stays open.
    for x in [-43,43]:
        for z in [-32,0,32]:
            detail.rod((x,1,z),(x,36,z),1.1,'TempleIvory',sides=12)
            for y in [1,5,34.5,36]:detail.rod((x,y-.2,z),(x,y+.2,z),1.35,'TempleGold',sides=12)
            for dx in [-.5,.5]:detail.rod((x+dx,6,z+1.03),(x+dx,33,z+1.03),.045,'TempleGold',sides=4)
    for a,b in zip(outline,outline[1:]+outline[:1]):
        if a[1]==56 and b[1]==56:continue
        inward=Vector((-(a[0]+b[0])/2,0,-(a[1]+b[1])/2)).normalized()*1.56
        for y in [3,37.5]:detail.rod(Vector((a[0],y,a[1]))+inward,Vector((b[0],y,b[1]))+inward,.12,'TempleGold',sides=6)
    # Blue wall panels with diamond tracery, in alternating wall bays.
    for x in [-46.42,46.42]:
        for z in [-16,16]:
            box(detail,(x,22,z),.12,17,9,'SkyCrystal')
            inward=-1 if x>0 else 1
            xx=x+inward*.1
            for zz in [z-4.65,z+4.65]:detail.rod((xx,13.3,zz),(xx,30.7,zz),.085,'TempleGold',sides=4)
            for yy in [13.3,30.7]:detail.rod((xx,yy,z-4.65),(xx,yy,z+4.65),.085,'TempleGold',sides=4)
            diamond=[(xx,28,z),(xx,22,z+3),(xx,16,z),(xx,22,z-3)]
            for a,b in zip(diamond,diamond[1:]+diamond[:1]):detail.rod(a,b,.055,'TempleGold',sides=4)
            detail.rod((xx,13.4,z),(xx,30.6,z),.045,'TempleIvory',sides=4)
    # Rear reliquary is outside the 76 x 76 fighting floor.
    box(detail,(0,1,-49),22,2,8,'TempleGold')
    box(detail,(0,2.5,-49),15,1,6,'TempleIvory')
    detail.rod((0,3,-49),(0,6,-49),2.1,'TempleGold',sides=12)
    gem(detail,(0,10,-49),2.9,8,'PortalGlow')
    arch(detail,0,18,-54.38,8,8.4,.14,'TempleGold')
    for x in [-8.2,8.2]:detail.rod((x,5,-54.38),(x,18,-54.38),.2,'TempleGold',sides=6)
    for x in [-22,22]:
        detail.rod((x,0,-49),(x,8,-49),1.1,'TempleIvory',sides=12)
        detail.rod((x,7.8,-49),(x,8.4,-49),1.5,'TempleGold',sides=12)
        gem(detail,(x,9.5,-49),1.1,2.8,'SkyCrystal')
    # Return doorway stays visibly open and matches the outdoor arch motif.
    for x in [-8.5,8.5]:detail.rod((x,0,54.4),(x,20,54.4),.2,'TempleGold',sides=6)
    detail.rod((-8.5,20,54.4),(8.5,20,54.4),.2,'TempleGold',sides=6)
    finish(detail,matrix,root,collision=False)
    floor=DetailMesh(source,'ES_SHRINE_MINIBOSS_ROOM_FLOOR_DETAIL_01')
    for radius,style in [(29,'TempleGold'),(20,'SkyCrystal')]:floor.ring((0,.06,0),radius,.045,style,sides=48)
    for k in range(8):
        a=k*math.tau/8
        floor.rod((20.15*math.cos(a),.06,20.15*math.sin(a)),(28.85*math.cos(a),.06,28.85*math.sin(a)),.045,'TempleGold',sides=4)
    slab(floor,[(0,-3),(3,0),(0,3),(-3,0)],.045,.015,'PortalGlow')
    finish(floor,matrix,root,collision=False)
    roof=DetailMesh(source,'ES_SHRINE_MINIBOSS_ROOM_ROOF_01')
    slab(roof,outline,44,42,'TempleIvory');box(roof,(0,23,64),26,2,16,'TempleIvory')
    for z in [-36,-12,12,36]:box(roof,(0,41.5,z),93,1,1.6,'TempleGold')
    for x in [-24,24]:box(roof,(x,41.3,0),1.2,1.4,108,'TempleGold')
    finish(roof,matrix,root)
    source['shrine_role']='walk-through portal entrance'
    return {'objects':made,'room_group':root.name,'room_world_position':list(root.location),'old_shrine_vertices_removed':len(remove)}


def shrine_room_props():
    """Separate animation pivots, matching return portal and recessed locked vault."""
    import bmesh
    from mathutils import Matrix
    root=bpy.data.objects['ES_SHRINE_MINIBOSS_ROOM']
    source=bpy.data.objects['ES_CAP_SEALED_SHRINE']
    assert all(o.mode=='OBJECT' for o in root.children if o.type=='MESH')
    assert 'ES_SHRINE_VAULT_BODY_PROP_01' not in bpy.data.objects
    made=[]
    def finish(out,collision=False):
        report=out.finish();obj=bpy.data.objects[out.name]
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
        obj.parent=root;obj.matrix_world=root.matrix_world.copy();obj['CanCollide']=collision
        obj['asset_role']='PROP' if not collision else 'STRUCTURE'
        made.append(report);return obj
    def box(out,c,w,h,d,style):out.box(c,(1,0,0),(0,0,1),w,h,d,style)
    # Same arched visual, scaled into the vestibule; the fight floor stays clear.
    for original,name in [('ES_SHRINE_PORTAL_ENTRANCE_01','ES_SHRINE_RETURN_FRAME_PROP_01'),
                          ('ES_SHRINE_PORTAL_SURFACE_01','ES_SHRINE_RETURN_SURFACE_PROP_01')]:
        src=bpy.data.objects[original];obj=src.copy();obj.data=src.data.copy();obj.name=name
        source.users_collection[0].objects.link(obj)
        for v in obj.data.vertices:
            v.co=Vector((v.co.x*.68,v.co.y*.68,(v.co.z-24)*.68+70))
        obj.parent=root;obj.matrix_world=root.matrix_world.copy()
        obj['CanCollide']=False;obj['asset_role']='PROP';made.append({'name':name})
    # Opaque backing beyond the portal, with roof and sidewalls hiding all sky.
    backing=DetailMesh(source,'ES_SHRINE_RETURN_DARK_BACKING_01')
    box(backing,(0,11,73),23,22,1,'IndigoLeaves')
    obj=finish(backing,True)
    dark=bpy.data.materials.new('ES_PORTAL_DARK_BACKING');dark.diffuse_color=(.003,.004,.009,1)
    dark.use_nodes=True;shader=dark.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=(.003,.004,.009,1)
    obj.data.materials.clear();obj.data.materials.append(dark)
    for p in obj.data.polygons:p.material_index=0
    for attr in obj.data.color_attributes:
        for value in attr.data:value.color=(.003,.004,.009,1)
    # Open a rear-side alcove beyond the fighting area, replacing only one wall.
    shell=bpy.data.objects['ES_SHRINE_MINIBOSS_ROOM_SHELL_01']
    groups,faces=components(shell);remove=[]
    for ids,pp in zip(groups,faces):
        pts=[shell.data.vertices[i].co for i in ids]
        if len(ids)==8 and min(p.z for p in pts)<-57 and max(p.z for p in pts)<-54 and max(p.x for p in pts)-min(p.x for p in pts)>80:
            remove=ids
    assert len(remove)==8,'Rear wall changed; refusing replacement'
    alcove=DetailMesh(source,'ES_SHRINE_VAULT_ALCOVE_01')
    for c,w,h,d in [((-11,21,-56),62,42,3),((39,21,-56),6,42,3),
                    ((28,29.5,-56),16,25,3),((28,-1,-66),20,2,23),
                    ((17.5,11,-66),3,22,23),((38.5,11,-66),3,22,23),
                    ((28,11,-77),24,22,3),((28,23,-66),24,2,23)]:
        box(alcove,c,w,h,d,'TempleIvory')
    finish(alcove,True)
    bm=bmesh.new();bm.from_mesh(shell.data);bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[bm.verts[i] for i in remove],context='VERTS')
    bm.to_mesh(shell.data);bm.free();shell.data.update()
    body=DetailMesh(source,'ES_SHRINE_VAULT_BODY_PROP_01')
    box(body,(28,3.5,-70),10,7,6,'Cloudstone')
    for y in [.4,6.6]:box(body,(28,y,-70),10.4,.6,6.4,'TempleGold')
    for x in [23.3,32.7]:box(body,(x,3.5,-66.9),.6,6.2,.25,'TempleGold')
    obj=finish(body,True);obj['asset_role']='PROP';obj['fixture_kind']='VAULT'
    obj['key_id']='ETHEREAL_SCAPE_VAULT_KEY'
    door=DetailMesh(source,'ES_SHRINE_VAULT_DOOR_PROP_01')
    box(door,(28,3.5,-66.72),8.6,5.4,.22,'IndigoLeaves')
    for x in [24,32]:box(door,(x,3.5,-66.55),.12,5.1,.12,'TempleGold')
    for y in [1,6]:box(door,(28,y,-66.55),8,.12,.12,'TempleGold')
    door.rod((28,3.5,-66.5),(28,3.5,-66.25),.65,'TempleGold',sides=12)
    box(door,(28,3.5,-66.08),.18,.7,.1,'PortalGlow')
    obj=finish(door);obj['fixture_role']='Door'
    # Extract new light crystals only; framed window panes remain structural.
    for name in ['ES_SHRINE_PORTAL_ENTRANCE_01','ES_SHRINE_RETURN_FRAME_PROP_01','ES_SHRINE_MINIBOSS_ROOM_DETAIL_01']:
        src=bpy.data.objects[name];groups,pp=components(src);cut=[]
        for ids,polygons in zip(groups,pp):
            styles={src.data.materials[p.material_index].name for p in polygons}
            if len(ids)!=10 or not all(n.startswith(('SkyCrystal','PortalGlow')) for n in styles):continue
            out=DetailMesh(src,name.replace('_01','')+'_LIGHT_PROP_'+str(len(made)).zfill(2))
            remap={v:i for i,v in enumerate(ids)}
            out.solid([src.data.vertices[i].co for i in ids],
                      [tuple(remap[i] for i in p.vertices) for p in polygons],next(iter(styles)).split('.')[0])
            report=out.finish();light=bpy.data.objects[out.name]
            light.parent=src.parent;light.matrix_world=src.matrix_world.copy()
            light['CanCollide']=False;light['asset_role']='PROP';made.append(report);cut.extend(ids)
        if cut:
            bm=bmesh.new();bm.from_mesh(src.data);bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm,geom=[bm.verts[i] for i in cut],context='VERTS');bm.to_mesh(src.data);bm.free()
    # Proper local pivots for animated effects and vault door, preserving positions.
    for obj in list(bpy.data.objects):
        if obj.type!='MESH' or obj.get('asset_role')!='PROP' or not obj.name.startswith('ES_SHRINE'):continue
        center=sum((v.co for v in obj.data.vertices),Vector())/len(obj.data.vertices)
        world=obj.matrix_world.copy()
        for v in obj.data.vertices:v.co-=center
        obj.matrix_world=world@Matrix.Translation(center)
        if 'SURFACE' in obj.name:
            obj['animation_hint']='RiftController pulse; do not spin the doorway surface'
    for name in ['ES_SHRINE_PORTAL_ENTRANCE_01','ES_SHRINE_PORTAL_SURFACE_01']:
        bpy.data.objects[name]['asset_role']='PROP'
    root['vault_alcove']='x 20..36, z -56..-77; outside fighting floor'
    root['runtime_pending']='walk-through teleport and room fixture registration; not a chunk loader change'
    return {'objects':made,'clear_fighting_area':root['clear_fighting_area']}


def garden_stair_landing():
    if not bpy.data.objects['ES_TERRACED_GARDENS'].get('es_garden_bridge_joint'):
        garden_bridge_joint()
    return garden_stair_rebuild()


def enlarge_shrine_miniboss_room():
    """Enlarge only the detached room; fit structural side supports and ceiling murals."""
    import bmesh
    from mathutils import Matrix
    root=bpy.data.objects['ES_SHRINE_MINIBOSS_ROOM']
    assert not root.get('es_large_arena'), 'Room already enlarged'
    descendants=set()
    def visit(obj):
        for child in obj.children:descendants.add(child);visit(child)
    visit(root)
    assert all(o.mode=='OBJECT' for o in descendants if o.type=='MESH'), 'Owner is editing room'
    # Scale the room group rather than replacing any owner-edited meshes.
    resuming=bool(bpy.data.objects.get('ES_SHRINE_MINIBOSS_ROOM_SUPPORTS_01'))
    if not resuming:root.scale.x*=1.5;root.scale.y*=1.45;root.scale.z*=1.5
    bpy.context.view_layer.update()
    source=bpy.data.objects['ES_CAP_SEALED_SHRINE']
    detail=bpy.data.objects['ES_SHRINE_MINIBOSS_ROOM_DETAIL_01']
    bpy.app.driver_namespace['es_room_columns_before']=detail.data.copy()
    groups,pp=components(detail);extended=0
    for ids,faces in ([] if resuming else zip(groups,pp)):
        pts=[detail.data.vertices[i].co for i in ids]
        center=sum(pts,Vector())/len(pts)
        if abs(abs(center.x)-43)>.9 or not any(abs(center.z-z)<1.5 for z in [-32,0,32]):continue
        # Side shafts and their highest collars/ribs meet the roof underside.
        if max(p.y for p in pts)>32:
            for i in ids:
                if detail.data.vertices[i].co.y>32:detail.data.vertices[i].co.y+=5.6
            extended+=1
    detail.data.update()
    supports=DetailMesh(source,'ES_SHRINE_MINIBOSS_ROOM_SUPPORTS_01')
    for x in [-43,43]:
        for z in [-32,0,32]:
            supports.box((x,41.8,z),(1,0,0),(0,0,1),3.4,.4,3.4,'TempleGold')
            supports.box((x,40.7,z),(1,0,0),(0,0,1),2.7,.45,2.7,'TempleIvory')
            for dx in [-.72,.72]:supports.rod((x+dx,6,z+1.1),(x+dx,39.8,z+1.1),.045,'TempleGold',sides=6)
    supports.finish();obj=bpy.data.objects[supports.name]
    obj.parent=root;obj.matrix_world=root.matrix_world.copy();obj['CanCollide']=True
    # Five shallow ceiling pictures occupy coffer bays, between structural beams.
    mural=DetailMesh(source,'ES_SHRINE_MINIBOSS_ROOM_CEILING_MURALS_01')
    for z in [-24,0,24]:
        for x in [-12,12]:
            mural.box((x,41.83,z),(1,0,0),(0,0,1),21,.12,20,'IndigoLeaves')
            for dx in [-10.55,10.55]:mural.rod((x+dx,41.74,z-10),(x+dx,41.74,z+10),.09,'TempleGold',sides=6)
            for dz in [-10.05,10.05]:mural.rod((x-10.5,41.74,z+dz),(x+10.5,41.74,z+dz),.09,'TempleGold',sides=6)
            # Symmetrical halo, crystal eye and six radial rays: shared temple language.
            mural.ring((x,41.68,z),6,.09,'TempleGold',sides=24)
            eye=[(x,41.61,z-3.5),(x+2,41.61,z),(x,41.61,z+3.5),(x-2,41.61,z)]
            for a,b in zip(eye,eye[1:]+eye[:1]):mural.rod(a,b,.13,'SkyCrystal',sides=6)
            for k in range(6):
                angle=k*math.tau/6
                mural.rod((x+6.5*math.cos(angle),41.65,z+6.5*math.sin(angle)),
                          (x+8.7*math.cos(angle),41.65,z+8.7*math.sin(angle)),.08,'TempleGold',sides=6)
            mural.rod((x,41.6,z-1),(x,41.6,z+1),.16,'PortalGlow',sides=8)
    report=mural.finish();obj=bpy.data.objects[mural.name]
    obj.parent=root;obj.matrix_world=root.matrix_world.copy();obj['CanCollide']=False
    for name in [supports.name,mural.name]:
        obj=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
        for face in obj.data.polygons:face.use_smooth=False
    root['clear_fighting_area']='114 x 114 studs; ceiling 60.9 studs; side columns outside clear floor'
    root['es_large_arena']=True
    return {'clear_fighting_area':root['clear_fighting_area'],'extended_support_components':extended,'mural':report,'ceiling_panels':6}


def separate_animation_props():
    """Extract effect surfaces and tree crowns without moving any scene geometry."""
    import bmesh,json,os,re
    from mathutils import Matrix
    root_path=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    metadata_path=os.path.join(root_path,'assets','export','worlds','ethereal_scape','live_animation_props.json')
    collection=bpy.data.collections.get('ES_ANIMATION_PROPS')
    if not collection:
        collection=bpy.data.collections.new('ES_ANIMATION_PROPS');bpy.context.scene.collection.children.link(collection)
    records=json.load(open(metadata_path,encoding='utf-8')) if os.path.exists(metadata_path) else []
    content=open(os.path.join(root_path,'src/shared/Content/Chunks/EtherealScape.luau'),encoding='utf-8').read()
    chunk_names=set(re.findall(r'\t\tId = "(ES_[^"]+)"',content))
    for source in list(bpy.data.objects):
        if source.type!='MESH' or not source.name.startswith('ES_') or source.get('asset_role')=='PROP':continue
        if source.mode!='OBJECT' or source.get('es_animation_separated'):continue
        if any(c.name=='ES_ENTRY_PORTAL_PREVIEW' for c in source.users_collection):continue
        if 'CHANDELIER' in source.name:
            source['asset_role']='PROP';source['CanCollide']=False
            source['animation_hint']='Sway as a complete suspended assembly; pivot at ceiling attachment'
            center=max((v.co.copy() for v in source.data.vertices),key=lambda p:p.y)
            old=source.matrix_world.copy()
            for v in source.data.vertices:v.co-=center
            source.matrix_world=old@Matrix.Translation(center)
            if source.name not in collection.objects:collection.objects.link(source)
            continue
        groups,pp=components(source);buckets={};cut=[]
        structural=source.name in chunk_names
        for ids,faces in zip(groups,pp):
            styles={source.data.materials[p.material_index].name.split('.')[0] for p in faces}
            pts=[source.data.vertices[i].co for i in ids]
            lo=min(p.y for p in pts);height=max(p.y for p in pts)-lo
            kind=None
            if styles=={'PortalGlow'} and lo>=0 and height>.15:kind='LIGHT'
            elif styles=={'SkyCrystal'} and lo>=0 and len(ids) in [5,6,7,9,10] and height>.2:kind='LIGHT'
            elif structural and styles and styles<= {'DeepTealLeaves','IndigoLeaves'} and lo>2:
                cx=sum(p.x for p in pts)/len(pts);cz=sum(p.z for p in pts)/len(pts)
                kind='CANOPY_'+str(round(cx,1)).replace('-','M').replace('.','_')+'_'+str(round(cz,1)).replace('-','M').replace('.','_')
            if kind:buckets.setdefault(kind,[]).extend(ids)
        for kind,ids in buckets.items():
            name=source.name+'_'+kind+'_PROP_01'
            assert name not in bpy.data.objects,name+' already exists without separation marker'
            mesh=source.data.copy();bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
            keep=set(ids);bmesh.ops.delete(bm,geom=[v for i,v in enumerate(bm.verts) if i not in keep],context='VERTS')
            bm.to_mesh(mesh);bm.free();mesh.update()
            obj=source.copy();obj.data=mesh;obj.name=name;collection.objects.link(obj)
            old=source.matrix_world.copy();center=sum((v.co for v in mesh.vertices),Vector())/len(mesh.vertices)
            if kind.startswith('CANOPY'):center.y=min(v.co.y for v in mesh.vertices)
            for v in mesh.vertices:v.co-=center
            obj.parent=source;obj.matrix_world=old@Matrix.Translation(center)
            obj['asset_role']='PROP';obj['CanCollide']=False;obj['source_object']=source.name
            obj['animation_hint']='Sway: tree crown pivot' if kind.startswith('CANOPY') else 'Static placement; pulse light/material without moving attached lights'
            records.append({'Object':name,'Source':source.name,'Kind':kind,'LocalPivot':list(center),'CanCollide':False})
            cut+=ids
        if cut:
            bpy.app.driver_namespace[source.name+'_before_prop_separation']=source.data.copy()
            bm=bmesh.new();bm.from_mesh(source.data);bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm,geom=[bm.verts[i] for i in cut],context='VERTS');bm.to_mesh(source.data);bm.free();source.data.update()
        source['es_animation_separated']=True
    for obj in bpy.data.objects:
        if obj.type=='MESH' and obj.name.startswith('ES_') and obj.get('asset_role')=='PROP':
            if obj.name not in collection.objects:collection.objects.link(obj)
    # This sidecar is authoring metadata, not an automatically loaded content schema.
    os.makedirs(os.path.dirname(metadata_path),exist_ok=True)
    with open(metadata_path,'w',encoding='utf-8') as f:json.dump(records,f,indent=2)
    return {'new_props':len(records),'light_groups':sum(r['Kind']=='LIGHT' for r in records),
            'tree_crowns':sum(r['Kind'].startswith('CANOPY') for r in records),'metadata':metadata_path}


def chunk_safety_boundaries():
    """Author collision-only boundaries around the union of walkable deck surfaces."""
    import bmesh,json,os,re
    from mathutils import geometry
    repo=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    with open(os.path.join(repo,'assets/export/worlds/ethereal_scape/ethereal_scape_structure.json'),encoding='utf-8') as f:catalogue=json.load(f)
    # Export sidecar only lists multipart pieces; include single-part chunks too.
    with open(os.path.join(repo,'src/shared/Content/Chunks/EtherealScape.luau'),encoding='utf-8') as f:content=f.read()
    for chunk in re.findall(r'\t\tId = "(ES_[^"]+)"',content):
        catalogue.setdefault(chunk,[{'SizeX':256,'SizeZ':256}])
    collection=bpy.data.collections.get('ES_SAFETY_BOUNDARIES')
    if not collection:collection=bpy.data.collections.new('ES_SAFETY_BOUNDARIES');bpy.context.scene.collection.children.link(collection)
    reports=[]
    def cross(a,b):return a.x*b.y-a.y*b.x
    def inside(q,poly):
        hit=False
        for a,b in zip(poly,poly[1:]+poly[:1]):
            if (a.y>q.y)!=(b.y>q.y) and q.x<(b.x-a.x)*(q.y-a.y)/(b.y-a.y)+a.x:hit=not hit
        return hit
    for name,parts in catalogue.items():
        if name.startswith('ES_BACKDROP'):continue
        source=bpy.data.objects.get(name)
        if not source or source.mode!='OBJECT':continue
        if bpy.data.objects.get(name+'_SAFETY_BOUNDARY_01'):continue
        groups,pp=components(source);surfaces=[]
        for ids,faces in zip(groups,pp):
            pts=[source.data.vertices[i].co for i in ids]
            if max(p.y for p in pts)-min(p.y for p in pts)<.3:continue
            for face in faces:
                style=source.data.materials[face.material_index].name
                if not style.startswith(('AetherMintGrass','GoldenPath')) or face.normal.y<.35:continue
                xyz=[source.data.vertices[i].co.copy() for i in face.vertices]
                if face.area<4:continue
                poly=[Vector((p.x,p.z)) for p in xyz]
                normal=face.normal.copy();origin=xyz[0]
                surfaces.append((poly,normal,origin))
        if not surfaces:continue
        def covered(q,y):
            for poly,n,p in surfaces:
                if inside(q,poly):
                    yy=p.y-(n.x*(q.x-p.x)+n.z*(q.y-p.z))/n.y
                    if abs(yy-y)<2:return True
            return False
        out=DetailMesh(source,name+'_SAFETY_BOUNDARY_01');segments=[];seen=set()
        half=max(float(parts[0]['SizeX']),float(parts[0]['SizeZ']))/2
        for poly,n,p in surfaces:
            for a,b in zip(poly,poly[1:]+poly[:1]):
                d=b-a
                if d.length<.05:continue
                cuts=[0.,1.]
                for other,nn,oo in surfaces:
                    for c,e in zip(other,other[1:]+other[:1]):
                        s=e-c;den=cross(d,s)
                        if abs(den)<1e-8:continue
                        t=cross(c-a,s)/den;u=cross(c-a,d)/den
                        if .00001<t<.99999 and -.00001<=u<=1.00001:cuts.append(t)
                cuts=sorted(set(round(t,7) for t in cuts))
                for t0,t1 in zip(cuts,cuts[1:]):
                    aa=a+d*t0;bb=a+d*t1
                    if (bb-aa).length<.15:continue
                    mid=(aa+bb)/2;yy=p.y-(n.x*(mid.x-p.x)+n.z*(mid.y-p.z))/n.y
                    perp=Vector((-d.y,d.x)).normalized()*.06
                    if covered(mid+perp,yy)==covered(mid-perp,yy):continue
                    # Leave the face on a tile socket plane open for its neighbour.
                    if any(abs(abs(aa[k])-half)<.08 and abs(aa[k]-bb[k])<.08 for k in [0,1]):continue
                    key=tuple(sorted((tuple(round(x,3) for x in aa),tuple(round(x,3) for x in bb))))
                    if key in seen:continue
                    seen.add(key)
                    ya=p.y-(n.x*(aa.x-p.x)+n.z*(aa.y-p.z))/n.y
                    yb=p.y-(n.x*(bb.x-p.x)+n.z*(bb.y-p.z))/n.y
                    tangent=Vector((bb.x-aa.x,0,bb.y-aa.y)).normalized()
                    side=Vector((-tangent.z,0,tangent.x))*.18
                    points=[Vector((q.x,y+height,q.y))+side*sign for height in [-.35,64] for q,y in [(aa,ya),(bb,yb)] for sign in [-1,1]]
                    out.solid(points,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],'SkyCrystal')
                    segments.append({'A':[aa.x,ya,aa.y],'B':[bb.x,yb,bb.y]})
        if not segments:continue
        out.finish();obj=bpy.data.objects[out.name]
        for coll in list(obj.users_collection):coll.objects.unlink(obj)
        collection.objects.link(obj)
        obj.display_type='WIRE';obj.hide_render=True
        world=obj.matrix_world.copy();obj.parent=source;obj.matrix_world=world
        obj['asset_role']='COLLISION_BOUNDARY';obj['parent_chunk']=name
        for k,v in {'CanCollide':True,'CanQuery':False,'CanTouch':False,'Transparency':1.,'boundary_height':64.}.items():obj[k]=v
        obj['animation_hint']='Future visual identification uses separate noncollidable effect props; collision stays fixed'
        obj['camera_requirement']='Explicit raycast exclusion; CanQuery false is ineffective on collidable parts'
        reports.append({'Chunk':name,'Object':obj.name,'Segments':segments,'Height':32,'CanCollide':True,'CanQuery':False,'CanTouch':False,'Transparency':1})
    path=os.path.join(repo,'assets/export/worlds/ethereal_scape/live_safety_boundaries.json')
    # Preserve all existing chunk groups on incremental runs.
    reports=[]
    for obj in collection.objects:
        if obj.type!='MESH' or obj.get('asset_role')!='COLLISION_BOUNDARY':continue
        segments=[]
        for i in range(0,len(obj.data.vertices),8):
            a=(obj.data.vertices[i].co+obj.data.vertices[i+1].co)/2
            b=(obj.data.vertices[i+2].co+obj.data.vertices[i+3].co)/2
            a.y+=.35;b.y+=.35
            segments.append({'A':list(a),'B':list(b)})
        reports.append({'Chunk':obj['parent_chunk'],'Object':obj.name,'Segments':segments,
                        'Height':obj.get('boundary_height',64),'CanCollide':True,'CanQuery':False,'CanTouch':False,'Transparency':1})
    with open(path,'w',encoding='utf-8') as f:json.dump(reports,f,indent=2)
    return {'chunks':len(reports),'segments':sum(len(r['Segments']) for r in reports),'metadata':path}


def refine_connector_profiles_and_boundaries():
    """Chamfer matching keel profiles; remove walls across actual authored mouths."""
    import bmesh,json,os,re
    repo=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    text=open(os.path.join(repo,'src/shared/Content/Chunks/EtherealScape.luau'),encoding='utf-8').read()
    names=re.findall(r'\t\tId = "(ES_[^"]+)"',text)
    planes={};count=0
    for name in names:
        source=bpy.data.objects.get(name)
        if not source or source.mode!='OBJECT':continue
        saved=bpy.app.driver_namespace.get(name+'_connector_before')
        reference=source.copy();reference.data=saved if saved else source.data
        groups,pp=components(reference);out=DetailMesh(source,name+'_CONNECTOR_KEEL_01');cut=[]
        for ids,faces in zip(groups,pp):
            if len(ids)!=5 or not all(reference.data.materials[p.material_index].name.startswith('Cloudstone') for p in faces):continue
            pts=[reference.data.vertices[i].co.copy() for i in ids]
            top=max(p.y for p in pts);bottom=min(p.y for p in pts)
            corners=[p for p in pts if abs(p.y-top)<.02]
            if len(corners)!=4 or not 20<top-bottom<65 or not -10<top<10:continue
            axis=0 if max(abs(p.x) for p in corners)>max(abs(p.z) for p in corners) else 2
            other=2 if axis==0 else 0;sign=1 if sum(p[axis] for p in corners)>0 else -1
            outer=max(sign*p[axis] for p in corners);apex=min(pts,key=lambda p:p.y)
            outside=[p for p in corners if abs(sign*p[axis]-outer)<.02]
            inner=[p for p in corners if abs(sign*p[axis]-outer)>=.02]
            if len(outside)!=2 or len(inner)!=2:continue
            rings=[]
            for pair,is_outer in [(outside,True),(inner,False)]:
                left,right=sorted(pair,key=lambda p:p[other]);center=(left[other]+right[other])/2
                half=(right[other]-left[other])/2 if is_outer else 5
                axis_bottom=left[axis] if is_outer else apex[axis]
                bevel=2.0
                ring=[left.copy(),right.copy()]
                for sideways,yy in [(half,bottom+bevel),(half-bevel,bottom),(-half+bevel,bottom),(-half,bottom+bevel)]:
                    p=Vector((0,yy,0));p[axis]=axis_bottom;p[other]=center+sideways;ring.append(p)
                rings.append(ring)
            out.solid(rings[0]+rings[1],[tuple(range(6)),tuple(reversed(range(6,12)))]+
                      [(k,(k+1)%6,(k+1)%6+6,k+6) for k in range(6)],'Cloudstone')
            planes.setdefault(name,[]).append((axis,sign,outer,min(p[other] for p in outside),max(p[other] for p in outside)))
            if not saved:cut+=ids
            count+=1
        bpy.data.objects.remove(reference)
        if not out.vertices:continue
        obj=bpy.data.objects.get(out.name)
        if obj:
            assert obj.mode=='OBJECT';old=obj.data;mesh=bpy.data.meshes.new(out.name)
            mesh.from_pydata(out.vertices,[],out.faces)
            for mat in old.materials:mesh.materials.append(mat)
            index=next(i for i,m in enumerate(mesh.materials) if m.name.startswith('Cloudstone'))
            colour=next((tuple(old.color_attributes['Col'].data[p.loop_start].color) for p in old.polygons if p.material_index==index),(.32,.4,.48,1))
            attr=mesh.color_attributes.new(name='Col',type='BYTE_COLOR',domain='CORNER')
            for p in mesh.polygons:
                p.material_index=index
                for loop in p.loop_indices:attr.data[loop].color=colour
            obj.data=mesh
        else:out.finish();obj=bpy.data.objects[out.name]
        bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
        obj['CanCollide']=True;obj['socket_profile']='2-stud lower chamfer; shared flat bottom and identical join silhouette'
        if cut:
            bpy.app.driver_namespace[name+'_connector_before']=source.data.copy()
            bm=bmesh.new();bm.from_mesh(source.data);bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm,geom=[bm.verts[i] for i in cut],context='VERTS');bm.to_mesh(source.data);bm.free()
        source['es_flush_connector_keels']=True
    removed=0
    for obj in bpy.data.collections['ES_SAFETY_BOUNDARIES'].objects:
        assert obj.mode=='OBJECT'
        groups,pp=components(obj);cut=[]
        for ids in groups:
            pts=[obj.data.vertices[i].co for i in ids]
            for axis,sign,value,lo,hi in planes.get(obj.get('parent_chunk'),[]):
                other=2 if axis==0 else 0
                if all(abs(sign*p[axis]-value)<.4 for p in pts) and min(p[other] for p in pts)>=lo-.4 and max(p[other] for p in pts)<=hi+.4:
                    cut+=ids;removed+=1;break
            # Height changes per segment, preserving slope and floor anchoring.
            floor=min(p.y for p in pts)
            lift=64-obj.get('boundary_height',32)
            for i in ids:
                if obj.data.vertices[i].co.y>floor+20:obj.data.vertices[i].co.y+=lift
        if cut:
            bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm,geom=[bm.verts[i] for i in cut],context='VERTS');bm.to_mesh(obj.data);bm.free()
        obj['boundary_height']=64
    return {'connector_profiles':count,'removed_mouth_walls':removed,'boundary_height':64}


def connector_undersides():
    """Replace mouth pyramids with socket-flush faceted keels, preserving decks."""
    import bmesh
    reports=[]
    for source in list(bpy.data.objects):
        if source.type!='MESH' or not source.name.startswith('ES_') or source.get('asset_role')=='PROP':continue
        if source.get('es_flush_connector_keels'):continue
        if source.mode!='OBJECT':continue  # Never touch the owner's active mesh edit.
        groups,pp=components(source);cut=[]
        out=DetailMesh(source,source.name+'_CONNECTOR_KEEL_01')
        socket_planes=[]
        for ids,faces in zip(groups,pp):
            if len(ids)!=5:continue
            pts=[source.data.vertices[i].co.copy() for i in ids]
            if not all(source.data.materials[p.material_index].name.startswith('Cloudstone') for p in faces):continue
            top=max(p.y for p in pts);bottom=min(p.y for p in pts)
            if abs(top+3)>.02 or bottom>=-20:continue
            corners=[p for p in pts if abs(p.y-top)<.01]
            apex=min(pts,key=lambda p:p.y)
            axis=0 if max(abs(p.x) for p in corners)>max(abs(p.z) for p in corners) else 2
            other=2 if axis==0 else 0
            sign=1 if sum(p[axis] for p in corners)>0 else -1
            outer=max(sign*p[axis] for p in corners)
            ordered=sorted(corners,key=lambda p:math.atan2(p.z-sum(q.z for q in corners)/4,p.x-sum(q.x for q in corners)/4))
            lower=[]
            for p in ordered:
                q=p.copy();q.y=bottom
                if abs(sign*p[axis]-outer)>.01:
                    q[axis]=apex[axis];q[other]=4 if p[other]>0 else -4
                lower.append(q)
            out.solid(ordered+lower,[(0,1,2,3),(7,6,5,4)]+[(k,k+4,(k+1)%4+4,(k+1)%4) for k in range(4)],'Cloudstone')
            socket_planes.append((axis,sign,outer));cut+=ids
        if not cut:continue
        report=out.finish();obj=bpy.data.objects[out.name]
        bm=bmesh.new();bm.from_mesh(obj.data)
        # Bevel only edges wholly away from every socket plane.
        edges=[e for e in bm.edges if all(all(abs(sign*v.co[axis]-value)>.01 for v in e.verts) for axis,sign,value in socket_planes)]
        if edges:bmesh.ops.bevel(bm,geom=edges,offset=.22,segments=1,affect='EDGES',clamp_overlap=True)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        assert all(e.is_manifold for e in bm.edges)
        bm.to_mesh(obj.data);bm.free()
        for p in obj.data.polygons:p.use_smooth=False
        obj['CanCollide']=True
        source_backup=source.data.copy();bpy.app.driver_namespace[source.name+'_connector_before']=source_backup
        bm=bmesh.new();bm.from_mesh(source.data);bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm,geom=[bm.verts[i] for i in cut],context='VERTS')
        bm.to_mesh(source.data);bm.free();source.data.update()
        source['es_flush_connector_keels']=True
        report['connectors']=len(socket_planes);reports.append(report)
    return reports
