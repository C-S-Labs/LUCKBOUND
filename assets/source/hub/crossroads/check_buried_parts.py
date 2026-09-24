"""Find loose parts buried inside other parts of the same static mesh (points
more than 0.2 studs inside a solid). Most hits are intended joins; read the list.

    blender -b --factory-startup --python check_buried_parts.py
"""
import bpy, bmesh, sys, runpy
from mathutils.bvhtree import BVHTree
sys.argv = ["x"]
g = runpy.run_path(r"C:\Dev\luckbound\assets\source\hub\crossroads\build_crossroads_hub.py", run_name="lib")
groups = g["build_all"]()
for o in groups["Hub"]:
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
    seen, parts = set(), []
    for f in bm.faces:
        if f.index in seen: continue
        stack, comp = [f], []
        seen.add(f.index)
        while stack:
            c = stack.pop(); comp.append(c)
            for e in c.edges:
                for n in e.link_faces:
                    if n.index not in seen: seen.add(n.index); stack.append(n)
        parts.append(comp)
    parts.sort(key=len, reverse=True)
    trees = []
    for comp in parts:
        vs = {v.index: i for i, v in enumerate({v for f in comp for v in f.verts})}
        verts = [None]*len(vs)
        for v, i in vs.items(): verts[i] = bm.verts[v].co.copy()
        tris = [[vs[v.index] for v in f.verts] for f in comp]
        cen = sum(verts, verts[0]*0)/len(verts)
        trees.append((BVHTree.FromPolygons(verts, tris), cen, len(comp)))
    from mathutils import Vector
    def inside(tree, pt):
        n, o_ = 0, pt.copy()
        d = Vector((0.013, 0.021, 1)).normalized()
        for _ in range(50):
            h = tree.ray_cast(o_, d)
            if h[0] is None: break
            n += 1; o_ = h[0] + d * 1e-4
        return n % 2 == 1
    bad = []
    for i in range(len(trees)):
        for j in range(len(trees)):
            if i == j or trees[i][2] < trees[j][2]: continue
            if (trees[i][1]-trees[j][1]).length > 60 or not trees[i][0].overlap(trees[j][0]): continue
            comp = parts[j]
            pts = [v.co for f in comp for v in f.verts]
            deep = sum(1 for q in pts if inside(trees[i][0], q) and trees[i][0].find_nearest(q)[3] > 0.2)
            if deep >= max(2, len(pts)//4):
                bad.append((i, j, deep, len(pts)))
    print("DEEP", o.name, len(bad))
    for i, j, d_, n_ in bad[:40]:
        c = trees[j][1]
        print("   part", j, "in", i, f"{d_}/{n_}", tuple(round(x,1) for x in c))
    continue
    hits = []
    for i in range(1, len(trees)):
        for j in range(i+1, len(trees)):
            if (trees[i][1]-trees[j][1]).length < 60 and trees[i][0].overlap(trees[j][0]):
                hits.append((i, j))
    print("INTRA", o.name, len(parts), "parts", len(hits), "touching pairs")
    import collections
    near = collections.Counter()
    for i, j in hits:
        c = (trees[i][1]+trees[j][1])/2
        near[(round(c.x/10)*10, round(c.y/10)*10, round(c.z/5)*5)] += 1
    print("   top spots", near.most_common(8))
