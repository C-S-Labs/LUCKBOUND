# Semi-mid-poly FINISH pass for chunk pieces (owner-approved 2026-09-24, Sky Citadel first).
# Low-poly shapes stay; the finish borrows the enemies' design language so map and bosses read as one world:
#   * long sharp edges get a narrow bevel whose faces carry the TRIM colour (violet trim lines)
#   * big wall panels are recessed a hair with a GLOW border (cyan seams, like the enemies' glow channels)
#   * big deck slabs get a flush TRIM-edged plate border (depth 0: walking surface unchanged)
# Seam-safe: nothing within SEAM of the tile edge (+/-HALF) or the keel/crown extremes is touched, so neighbouring
# chunks still meet flush and the 256^3 box is unchanged. Tri-safe: steps back (drops plates, raises the edge-length
# threshold) until the piece is under the tri limit. Flat shading is kept (Roblox look: one flat colour per face).
import bmesh, math

def refinish_piece(obj, mat_index, half=128.0, zmin=-96.0, zmax=160.0, tri_limit=10000, seam=1.0,
                   trim_width=0.6, glow_border=0.45, glow_depth=0.12, plate_border=0.6):
    """mat_index: {"trim": i, "glow": i, "walls": [i...], "decks": [i...] or None (any)}. Returns stats dict."""
    src = obj.data.copy()
    def near_edge(v):
        c = v.co
        return abs(abs(c.x) - half) < seam or abs(abs(c.y) - half) < seam or c.z < zmin + seam or c.z > zmax - seam
    def attempt(min_len, plates):
        bm = bmesh.new(); bm.from_mesh(src)
        # 1) glow seams on big vertical wall panels (clear of the tile seams)
        walls = [f for f in bm.faces if f.material_index in mat_index["walls"] and abs(f.normal.z) < 0.3
                 and f.calc_area() > 120 and not any(near_edge(v) for v in f.verts)]
        if walls:
            r = bmesh.ops.inset_individual(bm, faces=walls, thickness=glow_border, depth=-glow_depth)
            for f in r["faces"]: f.material_index = mat_index["glow"]
        # 2) trim-edged plates on big deck slabs (flush)
        if plates:
            decks = [f for f in bm.faces if f.normal.z > 0.9 and f.calc_area() > 300
                     and (mat_index.get("decks") is None or f.material_index in mat_index["decks"])]
            if decks:
                r = bmesh.ops.inset_individual(bm, faces=decks, thickness=plate_border, depth=0.0)
                for f in r["faces"]: f.material_index = mat_index["trim"]
        # 3) trim bevel on long sharp edges, never on seam/extreme edges
        edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(40)
                 and e.calc_length() > min_len and not any(near_edge(v) for v in e.verts)]
        if edges:
            r = bmesh.ops.bevel(bm, geom=edges, offset=trim_width/2, offset_type='WIDTH', segments=1,
                                profile=0.5, affect='EDGES', clamp_overlap=True)
            for f in r["faces"]: f.material_index = mat_index["trim"]
        tris = sum(len(f.verts) - 2 for f in bm.faces)
        return bm, tris, len(walls), len(edges)
    for min_len, plates in ((4.0, True), (6.0, True), (6.0, False), (10.0, False), (16.0, False), (1e9, False)):
        bm, tris, nw, ne = attempt(min_len, plates)
        if tris < tri_limit * 0.97: break
        bm.free()
    for f in bm.faces: f.smooth = False
    bm.to_mesh(obj.data); bm.free(); obj.data.update()
    return {"tris": tris, "wall_seams": nw, "trim_edges": ne, "plates": plates, "min_edge": min_len}
