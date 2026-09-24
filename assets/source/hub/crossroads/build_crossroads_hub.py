"""THE CROSSROADS, rebuilt around the Fate Engine (owner, 2026-09-23: "the
detail and design of the biomes completely outshine the hub ... Scratch it
entirely, although keep dimensions as the size was good").

The Fate Engine is NOT built here and is never touched. It stays its own
prefab (HUB_FATE_ENGINE) and the hub is designed around it: the same palette
(basalt, pale marble, gold, cyan inlay, violet and rose shards), the same
16-fold radial rhythm, and the same idea -- stone held up by light, with air
gaps where struts would be.

Authored in STUDS (1 Blender unit = 1 stud; the export lands 1:1, as the Sky
Citadel kit does). Blender +Y is NORTH (Roblox -Z). The walk plane is z = 0 at
the hub centre, where the Engine stands.

    HUB PIECES (each ONE mesh, each <= 10k triangles, all in hub coordinates)
      HUB_PLATFORM           plaza, four bridges, the promenade ring, the keel
      HUB_HALL_OF_CHAMPIONS  north
      HUB_ARCHIVES           east
      HUB_SHOP               south
      HUB_TRAINING_GROUNDS   west
    BACKDROP (cloned round the hub in Studio, randomised per server)
      HUB_BACKDROP_PEAKS / _MESA / _SPIRES
    ORBITERS (each its own mesh, drift round the hub, randomised per server)
      hubprop_*

Run headless:
    blender -b --factory-startup --python build_crossroads_hub.py -- --export --render --save
"""

import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
KIT_PATH = os.path.join(REPO, "assets", "source", "worlds", "sky_citadel", "build_sky_citadel_kit.py")
K = {"__name__": "sky_citadel_kit", "__file__": KIT_PATH}
exec(open(KIT_PATH, encoding="utf-8").read(), K)

# The palette is the Fate Engine's AS PAINTED IN GAME (Content/Hub/Crossroads
# Theme), so the hub and the Engine read as one object. (rgb, emissive)
K["PALETTE"].clear()
K["PALETTE"].update({
    "Basalt": ((64, 58, 78), False),        # heavy structure, keels, roofs
    "BasaltLight": ((88, 82, 104), False),  # carved detail, shelving, posts (Theme.Slate)
    "Plaza": ((58, 52, 76), False),         # the plaza floor
    "Walkway": ((78, 70, 98), False),       # bridges and the promenade
    "Marble": ((226, 221, 234), False),     # columns, district floors, statues
    "MarbleDim": ((196, 190, 208), False),  # marble in shadow: plinths, balustrades
    "Gold": ((230, 178, 74), False),        # trim, capitals, curbs (Theme.MarbleTrim)
    "GoldBright": ((244, 218, 147), False), # the Engine's own gold, for highlights
    "Inlay": ((68, 135, 123), True),        # floor inlays (Theme.Inlay)
    "Cosmic": ((124, 245, 224), True),      # the undimmed cyan, sparingly
    "Shard": ((147, 235, 255), True),       # floating crystals, cyan
    "Violet": ((182, 131, 255), True),      # crystals, violet
    "Rose": ((255, 170, 220), True),        # crystals, rose
    "DeepTeal": ((27, 75, 74), False),      # the Archives' own colour
    "TealStone": ((44, 96, 94), False),     # the Archives' floor
    "Sand": ((150, 140, 122), False),       # the training yard
    "Ember": ((255, 160, 80), True),        # torches, braziers
    "Canvas": ((122, 84, 168), False),      # stall roofs, banners (violet)
    "CanvasTeal": ((52, 128, 132), False),  # stall roofs (teal)
    "Wood": ((112, 84, 64), False),         # crates, dummies, ship hulls
    "Iron": ((102, 109, 125), False),       # the Engine's Industrial_Iron
    "Book1": ((150, 60, 72), False), "Book2": ((60, 90, 150), False), "Book3": ((70, 120, 80), False),
    "Rock": ((70, 62, 92), False),          # backdrop stone
    "RockLight": ((104, 94, 130), False),
    "RockDeep": ((46, 40, 64), False),
    "Snow": ((236, 232, 246), False),
    "Cloud": ((222, 214, 240), False),
    "CloudShade": ((170, 160, 204), False),
    "Water": ((110, 200, 230), True),
    "Whale": ((92, 104, 150), False),
    "WhaleBelly": ((196, 204, 230), False),
})
K["MAT_ORDER"] = list(K["PALETTE"].keys())

Piece, box, frustum, crystal, torus, torus_arc, tube, orb, xf, frame = (
    K[n] for n in ("Piece", "box", "frustum", "crystal", "torus", "torus_arc", "tube", "orb", "xf", "frame"))
Matrix = K["Matrix"]

TRI_LIMIT = 10000
EXPORT_DIR = os.path.join(REPO, "assets", "export", "hub", "crossroads")
RENDER_DIR = os.path.join(HERE, "renders")
BLEND = os.path.join(HERE, "crossroads_hub.blend")
LAYOUT_JSON = os.path.join(EXPORT_DIR, "crossroads_layout.json")
ENGINE_BLEND = r"C:\Dev\CCBlender\Assets\Fate_Engine\Fate_Engine.blend"
ENGINE_SCALE = 0.232        # Content/Hub/Crossroads Prefab.Scale (0.464 * WorldScale)

# ---- The layout (studs). Kept to the old hub's footprint: ~560 across. ------
PLAZA_R = 118.0         # the round plaza: covers the spawn ring (GameConfig SpawnRing.Radius 105)
RESERVE_R = 30.0        # the Engine's dais (Platform 240 * 0.232 = 55.7 across) + a margin
DISTRICT_AT = 218.0     # hub centre -> district centre (GameConfig.HubLayout.ZoneRingRadius, was 200)
DISTRICT_R = 80.0       # district deck radius
DISTRICT_TOP = 0.5      # a half-stud step up onto a district
BRIDGE_W = 24.0
RING_W = 18.0           # the promenade loop joining the districts
DISTRICTS = {           # name: (centre, rz that turns local -Y toward the hub)
    "HUB_HALL_OF_CHAMPIONS": ((0.0, DISTRICT_AT), 0.0),
    "HUB_ARCHIVES": ((DISTRICT_AT, 0.0), -90.0),
    "HUB_SHOP": ((0.0, -DISTRICT_AT), 180.0),
    "HUB_TRAINING_GROUNDS": ((-DISTRICT_AT, 0.0), 90.0),
}
ANCHORS = {}            # named points for gameplay (prompts, dummies, obelisks), hub coords


def tris(p):
    return sum(len(f) - 2 for f in p.faces)


def anchor(p, name, x, y, z):
    """Record a gameplay point, in hub coordinates, from inside a local frame."""
    w = p.base @ Vector((x, y, z))
    ANCHORS[name] = [round(w.x, 2), round(w.y, 2), round(w.z, 2)]


def sector(p, mat, r0, r1, z0, z1, a0, a1, seg, cx=0.0, cy=0.0):
    """An annular sector (a0..a1 degrees, CCW from +X), closed solid."""
    v, f = [], []
    for i in range(seg + 1):
        a = math.radians(a0 + (a1 - a0) * i / seg)
        c, s = math.cos(a), math.sin(a)
        for r, z in ((r0, z0), (r1, z0), (r1, z1), (r0, z1)):
            v.append((cx + r * c, cy + r * s, z))
    for i in range(seg):
        A, B = 4 * i, 4 * (i + 1)
        for k in range(4):
            k2 = (k + 1) % 4
            f.append((A + k, B + k, B + k2, A + k2))
    f.append((0, 1, 2, 3)[::-1])
    L = 4 * seg
    f.append((L, L + 1, L + 2, L + 3))
    p.add(v, f, mat, Matrix.Identity(4))


def ring_with_gaps(p, mat, r0, r1, z0, z1, gaps, seg_per_90=6):
    """A full ring minus angular windows [(centre_deg, half_width_deg)]."""
    cuts = sorted(((c - h) % 360, (c + h) % 360) for c, h in gaps)
    spans, start = [], None
    if not cuts:
        spans = [(0, 360)]
    else:
        for i, (s, e) in enumerate(cuts):
            nxt = cuts[(i + 1) % len(cuts)][0]
            a0, a1 = e, nxt if nxt > e else nxt + 360
            spans.append((a0, a1))
    for a0, a1 in spans:
        seg = max(1, int(round((a1 - a0) / 90 * seg_per_90)))
        sector(p, mat, r0, r1, z0, z1, a0, a1, seg)


def ribbon_pts(n, r, z):
    return [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z) for i in range(n)]


def lamp(p, x, y, h=10.0, glow="Cosmic"):
    frustum(p, "Basalt", 8, 1.3, 1.0, 0, 1.0, x, y)
    frustum(p, "BasaltLight", 6, 0.45, 0.35, 1.0, h, x, y)
    frustum(p, "Gold", 8, 0.9, 1.2, h, h + 0.6, x, y)
    crystal(p, glow, x, y, h + 1.8, 0.8, 1.4, 1.2, n=6)


def pylon_beacon(p, x, y, h=30.0, glow="Shard"):
    """The overlook beacon: a basalt needle with gold bands and, above it on
    nothing, a crystal like the Engine's shards."""
    frustum(p, "Basalt", 8, 4.0, 3.2, 0, 2.5, x, y)
    frustum(p, "BasaltLight", 4, 2.4, 1.2, 2.5, h, x, y, rot=45)
    for z in (h * 0.35, h * 0.7):
        frustum(p, "Gold", 4, 2.4 - z / h * 1.2 + 0.3, 2.4 - z / h * 1.2 + 0.3, z, z + 0.7, x, y, rot=45)
    frustum(p, "Gold", 4, 1.4, 0, h, h + 2.0, x, y, rot=45)
    crystal(p, glow, x, y, h + 7.5, 1.8, 4.0, 3.0, n=6, rz=20)
    torus(p, "Cosmic", 2.6, 0.18, x, y, h + 7.5, n=12, m=3)


def hanging_core(p, x, y, z, r, down, glow="Shard"):
    """The levitation core under a keel, echoing the Engine's LevitationCore."""
    crystal(p, glow, x, y, z, r, 0.1, down, n=8, rz=11)
    torus(p, "Cosmic", r * 1.35, 0.35, x, y, z - down * 0.35, n=16, m=3)


def stepped_keel(p, x, y, R, n, depth, glow="Shard", core=True):
    """Stepped basalt tiers under a deck, like the Engine's generator stack,
    ending in a floating crystal core below an air gap."""
    tiers = [(R, R * 0.92, 0, -0.18, "Basalt"), (R * 0.92, R * 0.78, -0.18, -0.32, "BasaltLight"),
             (R * 0.78, R * 0.77, -0.32, -0.36, "Gold"), (R * 0.77, R * 0.5, -0.36, -0.62, "Basalt"),
             (R * 0.5, R * 0.36, -0.62, -0.78, "BasaltLight"), (R * 0.36, R * 0.35, -0.78, -0.81, "Inlay"),
             (R * 0.35, R * 0.12, -0.81, -1.0, "Basalt")]
    for r0, r1, z0, z1, mat in tiers:
        frustum(p, mat, n, r1, r0, -4 + z1 * depth, -4 + z0 * depth, x, y)
    if core:
        hanging_core(p, x, y, -4 - depth - depth * 0.12, R * 0.16, depth * 0.55, glow)


def district_deck(p, floor, rim_gaps, keel_glow):
    """A district's round deck in its local frame: floor at DISTRICT_TOP, a gold
    curb round the edge with gaps, and its own keel."""
    frustum(p, floor, 16, DISTRICT_R, DISTRICT_R, -4, DISTRICT_TOP)
    ring_with_gaps(p, "Gold", DISTRICT_R - 1.6, DISTRICT_R, DISTRICT_TOP, DISTRICT_TOP + 1.0, rim_gaps, 8)
    sector(p, "Inlay", DISTRICT_R - 5.0, DISTRICT_R - 4.2, DISTRICT_TOP, DISTRICT_TOP + 0.06, 0, 360, 32)
    stepped_keel(p, 0, 0, DISTRICT_R, 16, 46, keel_glow)


# Openings in a district's curb, local degrees (CCW from +X): toward the hub
# (-Y = 270) and the two promenade arcs (east 0, west 180).
DISTRICT_GAPS = [(270, 12), (0, 8), (180, 8)]


# =============================================================================
#  HUB_PLATFORM
# =============================================================================

def build_platform():
    p = Piece("HUB_PLATFORM", "plaza + bridges + promenade ring + keel")
    # --- the plaza --------------------------------------------------------------
    frustum(p, "Plaza", 16, PLAZA_R, PLAZA_R, -4, 0)
    sector(p, "Gold", PLAZA_R - 4.5, PLAZA_R, 0, 0.7, 0, 360, 32)                  # curb
    sector(p, "Marble", RESERVE_R, RESERVE_R + 2.5, 0, 0.25, 0, 360, 32)           # the Engine's dais ring
    sector(p, "Inlay", RESERVE_R + 6.0, RESERVE_R + 7.2, 0, 0.06, 0, 360, 32)      # inner inlay
    sector(p, "Inlay", 64.0, 65.2, 0, 0.06, 0, 360, 32)                            # middle inlay
    sector(p, "Gold", 96.0, 97.0, 0, 0.06, 0, 360, 32)                              # outer inlay
    for k in range(32):                                                            # a ring of marble tiles
        a = 5.625 + 11.25 * k
        sector(p, "Marble" if k % 2 else "Walkway", 98.5, 108.0, 0, 0.04, a - 4.2, a + 4.2, 1)
    for k in range(16):                                                            # radial rays
        a = 11.25 + 22.5 * k
        sector(p, "BasaltLight" if k % 2 else "Walkway", RESERVE_R + 8.0, 63.0, 0, 0.04,
               a - 1.2, a + 1.2, 1)
    for k in range(4):                                                             # rune tiles on the diagonals
        a = math.radians(45 + 90 * k)
        cx, cy = math.cos(a) * 80, math.sin(a) * 80
        frustum(p, "Basalt", 8, 7.5, 7.5, 0, 0.5, cx, cy)
        frustum(p, "Gold", 8, 5.8, 5.8, 0.5, 0.7, cx, cy)
        # a crystal bed: the Engine's three shard colours
        for j, (dx, dy, col, h) in enumerate(((0, 0, "Shard", 7), (2.6, 1.4, "Violet", 4.5),
                                               (-2.2, 1.8, "Rose", 3.6), (0.4, -2.6, "Violet", 3.0))):
            crystal(p, col, cx + dx, cy + dy, 0.7, 1.4 if j == 0 else 0.9, h, 0.2, n=5, rz=j * 37)
    for k in range(8):                                                             # lamps
        a = math.radians(22.5 + 45 * k)
        lamp(p, math.cos(a) * (PLAZA_R - 9), math.sin(a) * (PLAZA_R - 9), 11.0)
    # --- the plaza's keel: the Engine's generator, scaled up and inverted -----
    stepped_keel(p, 0, 0, PLAZA_R, 16, 78, "Shard")
    for k in range(4):
        a = math.radians(45 + 90 * k)
        hanging_core(p, math.cos(a) * 70, math.sin(a) * 70, -30, 5.0, 26, ("Violet", "Rose")[k % 2])
    # --- the four bridges ---------------------------------------------------------
    for k in range(4):
        with frame(p, xf(rz=90 * k)):
            y0, y1 = PLAZA_R - 3, DISTRICT_AT - DISTRICT_R + 4
            box(p, "Walkway", 0, (y0 + y1) / 2, -1.5, BRIDGE_W, y1 - y0, 3)
            for s in (-1, 1):
                box(p, "Gold", s * (BRIDGE_W / 2 - 0.6), (y0 + y1) / 2 + 2, 0.4, 1.2, y1 - y0 - 4, 0.8)
                for yy in (y0 + 6, y1 - 6):                                    # gateposts at each end
                    frustum(p, "Marble", 4, 1.2, 1.0, 0, 7, s * (BRIDGE_W / 2 - 0.6), yy, rot=45)
                    crystal(p, "Shard", s * (BRIDGE_W / 2 - 0.6), yy, 8.2, 0.7, 1.3, 1.0, n=4)
            box(p, "Inlay", 0, (y0 + y1) / 2, 0.03, 1.4, y1 - y0 - 6, 0.06)
            # under the bridge: a spine, not a wall
            K["spine"](p, "Basalt", y0 + 2, y1 - 2, BRIDGE_W / 2 - 1, 16)
    # --- the promenade ring: the four arcs between districts, and the overlooks -
    half = math.degrees(math.asin((DISTRICT_R - 3) / DISTRICT_AT))
    for k in range(4):
        a0, a1 = 90 * k + half, 90 * (k + 1) - half
        sector(p, "Walkway", DISTRICT_AT - RING_W / 2, DISTRICT_AT + RING_W / 2, -3, 0, a0, a1, 10)
        for r in (DISTRICT_AT - RING_W / 2 + 0.6, DISTRICT_AT + RING_W / 2 - 0.6):
            sector(p, "Gold", r - 0.6, r + 0.6, 0, 0.8, a0 + 1.5, a1 - 1.5, 10)
        sector(p, "Basalt", DISTRICT_AT - 5, DISTRICT_AT + 5, -9, -3, a0, a1, 10)
        # the overlook on the diagonal, on the outside of the ring
        am = math.radians(45 + 90 * k)
        ox, oy = math.cos(am) * (DISTRICT_AT + 18), math.sin(am) * (DISTRICT_AT + 18)
        frustum(p, "Walkway", 12, 16, 16, -3, 0, ox, oy)
        sector(p, "Gold", 15, 16, 0, 1.0, 0, 360, 24, ox, oy)
        frustum(p, "Basalt", 12, 15, 4, -26, -3, ox, oy)
        pylon_beacon(p, ox + math.cos(am) * 6, oy + math.sin(am) * 6, 30.0, ("Shard", "Violet", "Rose", "Shard")[k])
        anchor(p, f"Overlook{k + 1}", ox, oy, 0)
    anchor(p, "EngineCentre", 0, 0, 0)
    return p


# =============================================================================
#  HALL OF CHAMPIONS (north) -- where the leaderboards stand
# =============================================================================

def statue(p, x, y, rz, pose=1):
    """A champion: pedestal, cloaked figure, sword raised. Abstract, low poly."""
    with frame(p, xf(x, y, 0, rz)):
        frustum(p, "Basalt", 8, 5.0, 4.4, DISTRICT_TOP, 3.5)
        frustum(p, "Gold", 8, 4.5, 4.5, 3.5, 4.0)
        frustum(p, "MarbleDim", 8, 3.6, 3.2, 4.0, 7.0)
        frustum(p, "Marble", 6, 2.6, 1.7, 7.0, 19.0)                 # robe
        frustum(p, "Marble", 6, 1.7, 2.4, 19.0, 22.0)                # shoulders
        orb(p, "Marble", 0, 0, 24.0, 1.4, n=6)                       # head
        tube(p, "Marble", [(1.9 * pose, 0, 21.0), (2.8 * pose, -0.6, 25.5), (2.4 * pose, -0.6, 28.5)],
             [0.55, 0.5, 0.45], n=5)                                 # the raised arm
        box(p, "GoldBright", 2.4 * pose, -0.6, 34.0, 0.5, 0.3, 11.0)  # the sword
        box(p, "Gold", 2.4 * pose, -0.6, 28.8, 2.6, 0.5, 0.5)
        tube(p, "Canvas", [(-1.2, 1.3, 21.5), (-2.6, 2.8, 13), (-2.0, 2.6, 7.4)], [1.6, 2.2, 2.6], n=6)  # cloak


def obelisk(p, x, y, h=24.0, glow="Shard"):
    frustum(p, "Basalt", 4, 5.0, 5.0, DISTRICT_TOP, 2.5, x, y, rot=45)
    frustum(p, "Gold", 4, 4.3, 4.3, 2.5, 3.0, x, y, rot=45)
    frustum(p, "Basalt", 4, 3.0, 2.1, 3.0, h, x, y, rot=45)
    frustum(p, "Gold", 4, 2.1, 0, h, h + 3.0, x, y, rot=45)
    crystal(p, glow, x, y, h + 8.0, 1.2, 2.4, 2.0, n=6)


def build_hall():
    p = Piece("HUB_HALL_OF_CHAMPIONS", "north district: colonnade, five champion obelisks, statues")
    (cx, cy), rz = DISTRICTS[p.name]
    with frame(p, xf(cx, cy, 0, rz)):
        district_deck(p, "Marble", DISTRICT_GAPS, "Violet")
        # the floor: a gold sunburst toward the stage
        sector(p, "Gold", 26, 27.4, DISTRICT_TOP, DISTRICT_TOP + 0.06, 0, 360, 24, 0, 12)
        for k in range(12):
            a = 15 + 30 * k
            sector(p, "MarbleDim", 29, 58, DISTRICT_TOP, DISTRICT_TOP + 0.04, a - 3, a + 3, 1, 0, 12)
        # the stage: a raised half-disc at the back
        sector(p, "Basalt", 0, 30, DISTRICT_TOP, DISTRICT_TOP + 2.0, 0, 180, 10, 0, 12)
        sector(p, "Gold", 29, 30.5, DISTRICT_TOP + 2.0, DISTRICT_TOP + 2.3, 0, 180, 10, 0, 12)
        box(p, "BasaltLight", 0, 11.2, DISTRICT_TOP + 1.0, 60, 1.6, 2.0)
        for s in range(3):                                           # steps up to the stage
            box(p, "MarbleDim", 0, 10.4 - s * 1.2, DISTRICT_TOP + 0.35 + s * 0.6, 20, 1.2, 0.7 + s * 1.2)
        # the five champion obelisks, on an arc at the back of the stage
        for i, a in enumerate((150, 120, 90, 60, 30)):
            ox, oy = math.cos(math.radians(a)) * 22, 12 + math.sin(math.radians(a)) * 22
            with frame(p, xf(0, 0, 2.0)):
                obelisk(p, ox, oy, 22.0 + (6 if i == 2 else 0), ("Shard", "Violet", "Rose", "Violet", "Shard")[i])
            anchor(p, f"Obelisk{i + 1}", ox, oy, DISTRICT_TOP + 2.0)
        # the colonnade: a half ring of columns carrying an entablature
        R, H = 66.0, 30.0
        for k in range(13):
            a = math.radians(-10 + 200 * k / 12)
            x, y = math.cos(a) * R, math.sin(a) * R + 4
            frustum(p, "MarbleDim", 8, 3.0, 3.0, DISTRICT_TOP, DISTRICT_TOP + 2.0, x, y)
            frustum(p, "Marble", 8, 2.1, 1.8, DISTRICT_TOP + 2.0, H - 2.0, x, y)
            frustum(p, "Gold", 8, 1.9, 3.0, H - 2.0, H, x, y)
            if k < 12:                                               # a banner between each pair
                b = math.radians(-10 + 200 * (k + 0.5) / 12)
                bx, by = math.cos(b) * (R - 0.4), math.sin(b) * (R - 0.4) + 4
                box(p, "Canvas" if k % 2 else "Basalt", bx, by, H - 9.5, 8.0, 0.4, 14.0,
                    rz=math.degrees(b) + 90)
                crystal(p, "Gold", bx, by, H - 17.0, 1.2, 0.6, 2.2, n=4, rz=math.degrees(b))
        sector(p, "Basalt", R - 3.4, R + 3.4, H, H + 3.2, -12, 192, 20, 0, 4)
        sector(p, "Gold", R - 3.5, R + 3.5, H + 3.2, H + 3.8, -12, 192, 20, 0, 4)
        # two champions guarding the approach
        statue(p, -24, -56, 180, 1)
        statue(p, 24, -56, 180, -1)
        # above the stage, on nothing: the laurel crown
        with frame(p, xf(0, 14, 52)):
            torus(p, "GoldBright", 12, 0.9, 0, 0, 0, n=24, m=4)
            for k in range(20):
                a = math.radians(360 * k / 20)
                crystal(p, "Gold", math.cos(a) * 12, math.sin(a) * 12, 0.6, 1.1, 3.2, 0.6, n=3,
                        rz=math.degrees(a))
            torus(p, "Cosmic", 16, 0.3, 0, 0, -4, n=24, m=3)
            crystal(p, "Rose", 0, 0, 0, 3.0, 5.5, 5.5, n=6)
        anchor(p, "HallPrompt", 0, -40, DISTRICT_TOP)
        anchor(p, "HallStage", 0, 12, DISTRICT_TOP + 2.0)
    return p


# =============================================================================
#  ARCHIVES (east) -- the rotunda of discoveries
# =============================================================================

def book_row(p, x, y, z, width, rz, rng):
    """A shelf's worth of book spines, varied heights, along local X."""
    with frame(p, xf(x, y, z, rz)):
        u = -width / 2
        while u < width / 2 - 0.8:
            w = rng.uniform(1.1, 2.0)
            h = rng.uniform(1.6, 2.4)
            box(p, rng.choice(("Book1", "Book2", "Book3", "DeepTeal", "Gold")), u + w / 2, 0, h / 2, w * 0.9, 1.2, h)
            u += w


def build_archives():
    p = Piece("HUB_ARCHIVES", "east district: domed rotunda, shelves, the orrery")
    rng = random.Random("archives")
    (cx, cy), rz = DISTRICTS[p.name]
    with frame(p, xf(cx, cy, 0, rz)):
        district_deck(p, "TealStone", DISTRICT_GAPS, "Shard")
        sector(p, "Marble", 0, 48, DISTRICT_TOP, DISTRICT_TOP + 0.8, 0, 360, 24, 0, 10)   # rotunda floor
        sector(p, "Gold", 47, 48.6, DISTRICT_TOP + 0.8, DISTRICT_TOP + 1.1, 0, 360, 24, 0, 10)
        sector(p, "Inlay", 14, 15, DISTRICT_TOP + 0.8, DISTRICT_TOP + 0.86, 0, 360, 24, 0, 10)
        z0 = DISTRICT_TOP + 0.8
        R, H = 42.0, 34.0
        for k in range(8):                                                # columns
            a = math.radians(22.5 + 45 * k)
            x, y = math.cos(a) * R, 10 + math.sin(a) * R
            frustum(p, "Marble", 8, 3.2, 3.0, z0, z0 + 2.2, x, y)
            frustum(p, "DeepTeal", 8, 2.3, 2.0, z0 + 2.2, H, x, y)
            frustum(p, "Gold", 8, 2.1, 3.2, H, H + 1.6, x, y)
        zd = H + 1.6
        sector(p, "Basalt", R - 5, R + 4, zd, zd + 5, 0, 360, 24, 0, 10)             # drum
        sector(p, "Cosmic", R + 3.9, R + 4.2, zd + 1.8, zd + 2.6, 0, 360, 24, 0, 10)
        prof = [(R + 3.0, zd + 5), (R - 1, zd + 12), (R - 9, zd + 19), (R - 20, zd + 24), (8, zd + 27)]
        for (r0, a0), (r1, a1) in zip(prof, prof[1:]):                    # the dome
            frustum(p, "DeepTeal", 16, r0, r1, a0, a1, 0, 10)
        for k in range(8):                                                # gold ribs
            a = math.radians(360 * k / 8)
            tube(p, "Gold", [(math.cos(a) * (r + 0.6), 10 + math.sin(a) * (r + 0.6), z) for r, z in prof],
                 [0.7, 0.7, 0.6, 0.5, 0.4], n=4)
        torus(p, "Gold", 8.4, 0.7, 0, 10, zd + 27, n=16, m=4)            # the oculus
        crystal(p, "Shard", 0, 10, zd + 36, 3.0, 7.0, 5.0, n=6)            # floats above it
        # shelves: the back five bays, between the columns
        for k in range(5):
            a = 90 + (k - 2) * 45
            ar = math.radians(a)
            x, y = math.cos(ar) * (R - 5), 10 + math.sin(ar) * (R - 5)
            with frame(p, xf(x, y, z0, a - 90)):
                box(p, "BasaltLight", 0, 0.9, 11, 26, 1.2, 22)            # the back
                for s in (-1, 1):
                    box(p, "Basalt", s * 13.2, 0, 11, 1.0, 3.2, 22)
                for lvl in range(4):
                    box(p, "Basalt", 0, -0.4, 1.2 + lvl * 5.2, 26, 3.0, 0.6)
                    if lvl < 3:
                        book_row(p, 0, -0.4, 1.5 + lvl * 5.2, 24, 0, rng)
                box(p, "Gold", 0, -0.2, 22.4, 27.6, 3.4, 0.8)
        # the orrery on its lectern, in the middle
        frustum(p, "Basalt", 8, 5, 4, z0, z0 + 1.2, 0, 10)
        frustum(p, "BasaltLight", 6, 1.6, 1.2, z0 + 1.2, z0 + 6, 0, 10)
        frustum(p, "Gold", 8, 2.6, 3.2, z0 + 6, z0 + 6.6, 0, 10)
        with frame(p, xf(0, 10, z0 + 16)):
            orb(p, "GoldBright", 0, 0, 0, 2.6, n=10)
            torus(p, "Gold", 7.5, 0.25, 0, 0, 0, n=24, m=3, rx=18)
            torus(p, "Gold", 11.5, 0.25, 0, 0, 0, n=28, m=3, rx=-12, ry=10)
            torus(p, "Cosmic", 15.0, 0.2, 0, 0, 0, n=32, m=3, ry=24)
            orb(p, "Violet", 7.5, 0, 2.2, 1.0, n=6)
            orb(p, "Shard", -8.0, 7.5, -1.4, 1.3, n=6)
            orb(p, "Rose", 3.0, -14.6, 5.0, 0.9, n=6)
        # open books drifting round the rotunda
        for k in range(8):
            a = math.radians(360 * k / 8 + 20)
            x, y, z = math.cos(a) * 24, 10 + math.sin(a) * 24, z0 + 12 + (k % 3) * 5
            with frame(p, xf(x, y, z, math.degrees(a) + 90, rng.uniform(-15, 15))):
                box(p, "Marble", -1.3, 0, 0, 2.6, 3.4, 0.35, ry=12)
                box(p, "Marble", 1.3, 0, 0, 2.6, 3.4, 0.35, ry=-12)
                box(p, rng.choice(("Book1", "Book2", "Book3")), 0, 0, -0.4, 5.6, 3.6, 0.3)
        # the approach: steps onto the rotunda and two lamps
        box(p, "MarbleDim", 0, -39, DISTRICT_TOP + 0.4, 22, 4, 0.8)
        for s in (-1, 1):
            lamp(p, s * 16, -46, 12.0, "Shard")
        anchor(p, "ArchivePrompt", 0, -40, DISTRICT_TOP)
        anchor(p, "ArchiveOrrery", 0, 10, z0 + 6.6)
    return p


# =============================================================================
#  SHOP (south) -- the market ring round a fountain
# =============================================================================

def stall(p, x, y, facing, roof):
    with frame(p, xf(x, y, DISTRICT_TOP, facing)):
        box(p, "Wood", 0, -2.5, 1.9, 13, 3.4, 3.8)                  # counter
        box(p, "Gold", 0, -4.1, 3.9, 13.4, 0.5, 0.3)
        for sx in (-6.2, 6.2):
            for sy in (-4.2, 4.6):
                box(p, "BasaltLight", sx, sy, 5.0, 0.8, 0.8, 10.0)
        box(p, "BasaltLight", 0, 5.4, 4.5, 13, 0.6, 9.0)               # back wall
        frustum(p, roof, 4, 10.6, 2.2, 10.0, 15.5, 0, 0.2, rot=45)    # hipped roof
        frustum(p, "Gold", 4, 10.8, 10.8, 9.6, 10.0, 0, 0.2, rot=45)
        frustum(p, "Gold", 4, 2.4, 0, 15.5, 17.5, 0, 0.2, rot=45)
        for i, g in enumerate(("Shard", "Violet", "Rose", "Gold")):  # goods on the counter
            crystal(p, g, -4.5 + i * 3, -2.5, 4.3, 0.6, 1.4, 0.3, n=5)
        box(p, "Wood", 7.8, -1, 1.2, 2.4, 2.4, 2.4, rz=18)            # crates
        box(p, "Wood", 8.3, 1.4, 1.0, 2.0, 2.0, 2.0, rz=-10)
        tube(p, "Iron", [(0, -4.6, 10.2), (0, -5.0, 8.4)], [0.12, 0.12], n=3)   # a lantern
        crystal(p, "Ember", 0, -5.0, 7.6, 0.7, 0.6, 0.9, n=6)


def build_shop():
    p = Piece("HUB_SHOP", "south district: market stalls round a fountain, entrance arch")
    (cx, cy), rz = DISTRICTS[p.name]
    with frame(p, xf(cx, cy, 0, rz)):
        district_deck(p, "MarbleDim", DISTRICT_GAPS, "Rose")
        sector(p, "Walkway", 20, 58, DISTRICT_TOP, DISTRICT_TOP + 0.05, 0, 360, 24)   # market ring paving
        sector(p, "Gold", 58, 59, DISTRICT_TOP, DISTRICT_TOP + 0.08, 0, 360, 24)
        # the fountain
        frustum(p, "Basalt", 16, 15, 15, DISTRICT_TOP, DISTRICT_TOP + 2.2)
        frustum(p, "Gold", 16, 15.4, 15.4, DISTRICT_TOP + 2.2, DISTRICT_TOP + 2.7)
        frustum(p, "Water", 16, 13.6, 13.6, DISTRICT_TOP + 2.2, DISTRICT_TOP + 2.3)
        frustum(p, "Marble", 8, 3.0, 2.0, DISTRICT_TOP + 2.3, DISTRICT_TOP + 9)
        frustum(p, "Basalt", 12, 7.5, 7.5, DISTRICT_TOP + 9, DISTRICT_TOP + 10)
        frustum(p, "Gold", 12, 7.8, 7.8, DISTRICT_TOP + 10, DISTRICT_TOP + 10.4)
        frustum(p, "Water", 12, 6.8, 6.8, DISTRICT_TOP + 10, DISTRICT_TOP + 10.1)
        frustum(p, "Marble", 8, 1.8, 1.2, DISTRICT_TOP + 10.1, DISTRICT_TOP + 15)
        frustum(p, "Basalt", 8, 3.6, 3.6, DISTRICT_TOP + 15, DISTRICT_TOP + 15.6)
        frustum(p, "Water", 8, 3.0, 3.0, DISTRICT_TOP + 15.6, DISTRICT_TOP + 15.7)
        # the coin of fortune, turning above the water on nothing
        with frame(p, xf(0, 0, DISTRICT_TOP + 28, 0, 90)):
            frustum(p, "GoldBright", 24, 6.5, 6.5, -0.7, 0.7)
            torus(p, "Gold", 6.5, 0.6, 0, 0, 0, n=24, m=4)
            frustum(p, "Gold", 6, 2.2, 2.2, 0.7, 0.9)
            frustum(p, "Gold", 6, 2.2, 2.2, -0.9, -0.7)
        torus(p, "Cosmic", 9.0, 0.3, 0, 0, DISTRICT_TOP + 21, n=24, m=3)
        torus(p, "Rose", 11.5, 0.2, 0, 0, DISTRICT_TOP + 19, n=24, m=3)
        # banner masts between the stalls
        for k, deg in enumerate((10, 50, 90, 130, 170, 210)):
            a = math.radians(deg)
            mx_, my_ = math.cos(a) * 56, math.sin(a) * 56
            frustum(p, "Basalt", 6, 1.2, 1.0, DISTRICT_TOP, DISTRICT_TOP + 1.5, mx_, my_)
            frustum(p, "BasaltLight", 6, 0.5, 0.35, DISTRICT_TOP + 1.5, DISTRICT_TOP + 24, mx_, my_)
            crystal(p, ("Rose", "Shard", "Violet")[k % 3], mx_, my_, DISTRICT_TOP + 25.5, 0.8, 1.6, 1.0, n=5)
            with frame(p, xf(mx_, my_, DISTRICT_TOP + 18, deg + 90)):
                box(p, ("Canvas", "CanvasTeal")[k % 2], 2.6, 0, 0, 5.0, 0.2, 7.5)
                crystal(p, "Gold", 2.6, 0, -4.6, 0.8, 0.4, 1.4, n=4)
        # the stalls, a ring of six, open toward the middle
        for i, a in enumerate((-10, 30, 70, 110, 150, 190)):
            ar = math.radians(a)
            stall(p, math.cos(ar) * 44, math.sin(ar) * 44, a - 90 + 180, ("Canvas", "CanvasTeal")[i % 2])
            anchor(p, f"Stall{i + 1}", math.cos(ar) * 38, math.sin(ar) * 38, DISTRICT_TOP)
        # the entrance arch, facing the hub
        for s in (-1, 1):
            frustum(p, "Basalt", 4, 3.4, 3.0, DISTRICT_TOP, DISTRICT_TOP + 2.0, s * 11, -64, rot=45)
            frustum(p, "Marble", 4, 2.4, 2.0, DISTRICT_TOP + 2.0, DISTRICT_TOP + 20, s * 11, -64, rot=45)
            frustum(p, "Gold", 4, 2.6, 2.8, DISTRICT_TOP + 20, DISTRICT_TOP + 21, s * 11, -64, rot=45)
        torus_arc(p, "Gold", 11, 1.2, 0, -64, DISTRICT_TOP + 21, 0, 180, n=12, m=4, rx=90)
        box(p, "Basalt", 0, -64, DISTRICT_TOP + 27.5, 14, 1.2, 4.2)                # the sign
        box(p, "GoldBright", 0, -64.7, DISTRICT_TOP + 27.5, 12.4, 0.2, 3.0)
        crystal(p, "Rose", 0, -64, DISTRICT_TOP + 34, 1.8, 3.4, 2.4, n=6)          # keystone
        # lanterns on posts round the market
        for k in range(6):
            a = math.radians(10 + 60 * k)
            lamp(p, math.cos(a) * 66, math.sin(a) * 66, 9.0, "Ember")
        anchor(p, "ShopPrompt", 0, -40, DISTRICT_TOP)
        anchor(p, "ShopFountain", 0, 0, DISTRICT_TOP)
    return p


# =============================================================================
#  TRAINING GROUNDS (west) -- the yard
# =============================================================================

def brazier(p, x, y):
    frustum(p, "Iron", 6, 1.2, 0.8, DISTRICT_TOP, DISTRICT_TOP + 6, x, y)
    frustum(p, "Iron", 8, 1.2, 2.6, DISTRICT_TOP + 6, DISTRICT_TOP + 7.6, x, y)
    for k in range(3):
        crystal(p, "Ember", x + math.cos(k * 2.1) * 0.8, y + math.sin(k * 2.1) * 0.8, DISTRICT_TOP + 7.4,
                0.9, 2.6 - k * 0.5, 0.2, n=4, rz=k * 40)


def rack(p, x, y, rz):
    with frame(p, xf(x, y, DISTRICT_TOP, rz)):
        for s in (-4, 4):
            box(p, "Wood", s, 0, 3.5, 0.6, 0.6, 7)
        box(p, "Wood", 0, 0, 6.6, 9, 0.6, 0.6)
        box(p, "Wood", 0, 0, 1.4, 9, 0.6, 0.6)
        for i in range(4):
            box(p, "Iron", -3 + i * 2, 0.5, 3.8, 0.3, 0.2, 5.6, ry=6)
            box(p, "Gold", -3 + i * 2, 0.5, 5.2, 1.0, 0.3, 0.3)


def target(p, x, y, rz):
    with frame(p, xf(x, y, DISTRICT_TOP, rz)):
        box(p, "Wood", 0, 0, 3.0, 0.6, 0.6, 6)
        with frame(p, xf(0, -0.4, 7.2, 0, 90)):
            for r, m in ((3.0, "Marble"), (2.1, "Canvas"), (1.2, "Marble"), (0.5, "Gold")):
                frustum(p, m, 12, r, r, 0, 0.3 + (3.0 - r) * 0.05)


def build_training():
    p = Piece("HUB_TRAINING_GROUNDS", "west district: sand yard, sparring ring, braziers, racks, tower")
    (cx, cy), rz = DISTRICTS[p.name]
    with frame(p, xf(cx, cy, 0, rz)):
        district_deck(p, "Sand", DISTRICT_GAPS, "Violet")
        # the sparring ring
        sector(p, "BasaltLight", 0, 22, DISTRICT_TOP, DISTRICT_TOP + 0.05, 0, 360, 24, 0, 8)
        sector(p, "Gold", 22, 23.6, DISTRICT_TOP, DISTRICT_TOP + 0.3, 0, 360, 24, 0, 8)
        sector(p, "Inlay", 10, 10.8, DISTRICT_TOP, DISTRICT_TOP + 0.08, 0, 360, 24, 0, 8)
        # the yard wall: low, open to the hub and the promenade
        ring_with_gaps(p, "BasaltLight", 68, 71, DISTRICT_TOP, DISTRICT_TOP + 3.4, [(270, 16), (0, 10), (180, 10)], 8)
        ring_with_gaps(p, "Gold", 67.8, 71.2, DISTRICT_TOP + 3.4, DISTRICT_TOP + 3.8, [(270, 16), (0, 10), (180, 10)], 8)
        for k in range(8):                                            # braziers
            a = math.radians(22.5 + 45 * k)
            if abs(((math.degrees(a) - 270) + 180) % 360 - 180) < 20:
                continue
            brazier(p, math.cos(a) * 63, math.sin(a) * 63)
        # the dummy stands: the dummies themselves are built by the game
        for i, (x, y, r) in enumerate(((-28, 34, 3.5), (0, 44, 3.5), (28, 34, 3.5), (0, 8, 5.5))):
            frustum(p, "Basalt", 12, r + 0.8, r + 0.8, DISTRICT_TOP, DISTRICT_TOP + 0.6, x, y)
            sector(p, "Gold", r, r + 0.8, DISTRICT_TOP + 0.6, DISTRICT_TOP + 0.8, 0, 360, 12, x, y)
            anchor(p, "BossDummy" if i == 3 else f"Dummy{i + 1}", x, y, DISTRICT_TOP + 0.6)
        for k, deg in enumerate((40, 64, 88, 112, 136, 160)):          # banner poles on the wall
            a = math.radians(deg)
            bx, by = math.cos(a) * 69.5, math.sin(a) * 69.5
            frustum(p, "Basalt", 6, 0.6, 0.45, DISTRICT_TOP + 3.8, DISTRICT_TOP + 20, bx, by)
            frustum(p, "Gold", 6, 0.9, 0, DISTRICT_TOP + 20, DISTRICT_TOP + 21.5, bx, by)
            with frame(p, xf(bx, by, DISTRICT_TOP + 14, deg + 90)):
                box(p, ("Canvas", "Basalt")[k % 2], 0, -0.4, 0, 4.2, 0.2, 9.0)
                box(p, "Gold", 0, -0.55, 2.4, 2.2, 0.1, 2.2, ry=45)
        rack(p, -48, 10, 90)
        rack(p, -48, -10, 90)
        for i in range(4):                                            # archery targets, east side
            target(p, 40 + (i % 2) * 6, -12 + i * 10, -90)
        # the watchtower at the back
        with frame(p, xf(-38, 50, DISTRICT_TOP, 20)):
            frustum(p, "Basalt", 4, 7.5, 6.5, 0, 26, rot=45)
            frustum(p, "Gold", 4, 7.2, 7.2, 26, 27, rot=45)
            for s in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                box(p, "BasaltLight", s[0] * 5.6, s[1] * 5.6, 30, 1.2, 1.2, 6)
            frustum(p, "Canvas", 4, 9.5, 0.8, 33, 41, rot=45)
            box(p, "Canvas", 0, -6.2, 18, 5, 0.4, 12)                # a banner down the face
            crystal(p, "Ember", 0, 0, 44, 1.2, 2.4, 1.6, n=6)
        # the gong
        with frame(p, xf(0, 62, DISTRICT_TOP)):
            for s in (-7, 7):
                box(p, "Wood", s, 0, 7, 1.0, 1.0, 14)
            box(p, "Wood", 0, 0, 14, 16, 1.0, 1.0)
            torus(p, "GoldBright", 5.0, 0.6, 0, 0, 7.5, n=20, m=4, rx=90)
            frustum(p, "Gold", 20, 4.6, 4.6, -0.2, 0.2, M=xf(0, 0, 7.5, 0, 90))
        anchor(p, "TrainingPrompt", 0, -40, DISTRICT_TOP)
    return p


# =============================================================================
#  BACKDROP -- floating mountains, cloned round the hub (1-3 chunks)
# =============================================================================

def lump(p, mat, profile, n, seed, jitter=0.2, cx=0.0, cy=0.0, sx=1.0, sy=1.0, bands=None):
    """A lathe of rings (radius, z) with per-column jitter: rock, cloud, hull."""
    rng = random.Random(seed)
    cols = [1.0 + rng.uniform(-jitter, jitter) for _ in range(n)]
    verts, faces, idx, mats = [], [], [], []
    for r, z in profile:
        ring = []
        if r <= 1e-6:
            verts.append((cx, cy, z))
            ring.append(len(verts) - 1)
        else:
            for i in range(n):
                a = 2 * math.pi * i / n
                verts.append((cx + math.cos(a) * r * cols[i] * sx, cy + math.sin(a) * r * cols[i] * sy, z))
                ring.append(len(verts) - 1)
        idx.append(ring)
    for k, (A, B) in enumerate(zip(idx, idx[1:])):
        m = bands[k] if bands else mat
        if len(A) > 1 and len(B) > 1:
            fs = [(A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]) for i in range(n)]
        elif len(B) == 1:
            fs = [(A[i], A[(i + 1) % n], B[0]) for i in range(n)]
        else:
            fs = [(A[0], B[(i + 1) % n], B[i]) for i in range(n)]
        faces += fs
        mats += [m] * len(fs)
    if len(idx[0]) > 1:
        faces.append(tuple(reversed(idx[0])))
        mats.append(bands[0] if bands else mat)
    if len(idx[-1]) > 1:
        faces.append(tuple(idx[-1]))
        mats.append(bands[-1] if bands else mat)
    base = len(p.verts)
    p.verts.extend(p.base @ Vector(v) for v in verts)
    p.faces.extend([base + i for i in f] for f in faces)
    p.fmat.extend(mats)
    p.ftag.extend(["lump"] * len(faces))


def peak(p, x, y, r, h, seed, snow=True, n=13):
    prof = [(r, 0), (r * 0.9, h * 0.12), (r * 0.74, h * 0.3), (r * 0.6, h * 0.46), (r * 0.44, h * 0.62),
            (r * 0.3, h * 0.76), (r * 0.17, h * 0.88), (0, h)]
    bands = ["Rock", "Rock", "RockLight", "Rock", "Rock"] + (["Snow", "Snow"] if snow else ["RockLight", "RockLight"])
    lump(p, "Rock", prof, n, seed, 0.3, x, y, bands=bands)


def crag(p, x, y, z, r, h, seed):
    lump(p, "Rock", [(r, z), (r * 0.8, z + h * 0.4), (r * 0.45, z + h * 0.75), (0, z + h)], 7, seed, 0.35, x, y,
         bands=["RockLight", "Rock", "RockLight"])


def island_base(p, x, y, r, depth, seed, top="RockLight", n=16):
    """A floating rock: flat-ish top, a craggy underside hung with stone roots."""
    prof = [(r, 0), (r * 0.96, -depth * 0.06), (r * 0.86, -depth * 0.16), (r * 0.74, -depth * 0.3),
            (r * 0.58, -depth * 0.46), (r * 0.42, -depth * 0.62), (r * 0.26, -depth * 0.78),
            (r * 0.12, -depth * 0.92), (0, -depth)]
    lump(p, "Rock", [(r * 0.97, 3.0)] + prof, n, seed, 0.2, x, y,
         bands=[top, "RockLight", "Rock", "Rock", "Rock", "RockDeep", "RockDeep", "RockDeep", "RockDeep"])
    rng = random.Random(seed + "roots")
    for k in range(9):                                           # hanging stone roots
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.3, 0.75) * r
        z = -depth * (0.2 + 0.5 * (1 - d / r))
        lump(p, "RockDeep", [(r * 0.12, z + 2), (r * 0.09, z - depth * 0.15), (r * 0.04, z - depth * 0.3),
                             (0, z - depth * rng.uniform(0.38, 0.5))], 6, seed + str(k), 0.3,
             x + math.cos(a) * d, y + math.sin(a) * d, bands=["Rock", "RockDeep", "RockDeep"])
    for k in range(10):                                          # boulders round the rim
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.82, 0.95) * r
        crag(p, x + math.cos(a) * d, y + math.sin(a) * d, 1.0, r * rng.uniform(0.04, 0.08),
             r * rng.uniform(0.06, 0.16), seed + "b" + str(k))


def vein(p, x, y, z, s, seed):
    rng = random.Random(seed)
    for k in range(7):
        crystal(p, rng.choice(("Shard", "Violet", "Shard", "Rose")), x + rng.uniform(-s, s), y + rng.uniform(-s, s),
                z + rng.uniform(-s, s) * 0.5, rng.uniform(1.5, 3.5) * s / 8, rng.uniform(6, 14) * s / 8,
                rng.uniform(2, 5) * s / 8, n=5, rz=rng.uniform(0, 90))


def ruin_spire(p, x, y, z, h, glow="Shard"):
    frustum(p, "MarbleDim", 8, 9, 7, z, z + h * 0.6, x, y)
    frustum(p, "Gold", 8, 7.6, 7.6, z + h * 0.6, z + h * 0.6 + 2, x, y)
    frustum(p, "Marble", 8, 6, 5, z + h * 0.6 + 2, z + h * 0.85, x, y)
    frustum(p, "Basalt", 8, 6.6, 0, z + h * 0.85, z + h, x, y)
    crystal(p, glow, x, y, z + h + 12, 4, 8, 6, n=6)
    torus(p, "Cosmic", 6.5, 0.4, x, y, z + h + 12, n=16, m=3)


def build_backdrop_peaks():
    p = Piece("HUB_BACKDROP_PEAKS", "floating massif: snow peaks, crags, crystal veins, a ruined spire")
    island_base(p, 0, 0, 180, 280, "bd peaks base")
    for k, (x, y, r, h, snow) in enumerate(((0, 0, 120, 340, True), (95, 40, 72, 230, True),
                                              (-85, -50, 80, 190, True), (-40, 95, 55, 140, False),
                                              (60, -90, 50, 120, False), (120, -30, 40, 90, False),
                                              (-120, 40, 45, 110, True))):
        peak(p, x, y, r, h, f"pk{k}", snow)
    rng = random.Random("peak crags")
    for k in range(14):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(60, 150)
        crag(p, math.cos(a) * d, math.sin(a) * d, 0, rng.uniform(10, 22), rng.uniform(25, 70), f"pc{k}")
    vein(p, 110, -60, 20, 26, "v1")
    vein(p, -120, 40, 10, 20, "v2")
    vein(p, 30, -130, -60, 22, "v3")
    vein(p, -60, -140, -20, 24, "v4")
    ruin_spire(p, -95, 60, 60, 110, "Shard")
    for k in range(8):                                                  # hanging crystal roots
        a = math.radians(45 * k + 15)
        crystal(p, ("Shard", "Violet")[k % 2], math.cos(a) * 70, math.sin(a) * 70, -130 - (k % 3) * 25,
                8, 1, 45 + (k % 2) * 30, n=6)
    return p


def build_backdrop_mesa():
    p = Piece("HUB_BACKDROP_MESA", "floating mesa: terraced cliffs, a ruined temple, falling streams of light")
    island_base(p, 0, 0, 240, 260, "bd mesa base", top="RockLight")
    lump(p, "Rock", [(215, 0), (205, 30), (190, 48), (172, 56), (160, 84), (140, 98), (122, 104), (60, 106),
                     (0, 106)], 18, "mesa top", 0.1,
         bands=["Rock", "RockLight", "RockLight", "Rock", "RockLight", "RockLight", "RockLight", "RockLight"])
    rng = random.Random("mesa crags")
    for k in range(16):                                                 # cliff buttresses
        a = 2 * math.pi * k / 16 + rng.uniform(-0.1, 0.1)
        crag(p, math.cos(a) * 196, math.sin(a) * 196, 0, rng.uniform(14, 24), rng.uniform(40, 70), f"mc{k}")
    for k in range(8):
        a = rng.uniform(0, 2 * math.pi)
        crag(p, math.cos(a) * 150, math.sin(a) * 150, 56, rng.uniform(8, 14), rng.uniform(20, 40), f"mt{k}")
    # the temple: a ring of broken columns round a crystal
    for k in range(12):
        a = math.radians(30 * k)
        h = rng.choice((40, 26, 14, 40, 33, 8))
        x, y = math.cos(a) * 55, math.sin(a) * 55
        frustum(p, "MarbleDim", 8, 7, 7, 106, 110, x, y)
        frustum(p, "Marble", 8, 5, 4.6, 110, 110 + h, x, y)
        if h == 40:
            frustum(p, "Gold", 8, 5, 6.5, 150, 152, x, y)
    frustum(p, "MarbleDim", 16, 70, 70, 104, 106.5)
    frustum(p, "Basalt", 16, 30, 30, 106.5, 109)
    crystal(p, "Violet", 0, 0, 140, 10, 18, 14, n=6)
    torus(p, "Cosmic", 16, 0.8, 0, 0, 140, n=24, m=3)
    torus(p, "Gold", 20, 0.8, 0, 0, 136, n=24, m=3, rx=20)
    # streams of light pouring off the edge into the void
    for a, w in ((0, 22), (140, 14)):
        ar = math.radians(a)
        with frame(p, xf(math.cos(ar) * 212, math.sin(ar) * 212, 0, a)):
            box(p, "Water", 0, 0, 10, 6, w, 170)
            box(p, "Water", -8, 0, 98, 16, w + 4, 4)
    vein(p, -180, 60, 30, 30, "mv1")
    vein(p, 60, -190, 10, 26, "mv2")
    vein(p, 120, 150, 0, 22, "mv3")
    for k in range(6):
        a = math.radians(60 * k)
        crystal(p, ("Shard", "Violet")[k % 2], math.cos(a) * 95, math.sin(a) * 95, -120, 10, 1, 60, n=6)
    return p


def build_backdrop_spires():
    p = Piece("HUB_BACKDROP_SPIRES", "needle spires joined by bridges, a great crystal")
    island_base(p, 0, 0, 160, 220, "bd spires base")
    tips = []
    rng = random.Random("spires")
    for k, (x, y, r, h) in enumerate(((0, 0, 42, 400), (82, 30, 28, 290), (-72, 52, 30, 260), (30, -88, 26, 240),
                                       (-62, -62, 22, 210), (100, -60, 16, 150), (-110, -10, 18, 170),
                                       (40, 100, 20, 190), (-20, 120, 14, 120))):
        prof = [(r, 0), (r * 0.86, h * 0.18), (r * 0.72, h * 0.38), (r * 0.6, h * 0.55), (r * 0.44, h * 0.72),
                (r * 0.26, h * 0.88), (0, h)]
        lump(p, "Rock", prof, 9, f"sp{k}", 0.2, x, y,
             bands=["Rock", "Rock", "RockLight", "Rock", "Rock", "RockLight"])
        tips.append((x, y, h))
        if k in (1, 2, 3):                                             # a gold band on the tall ones
            frustum(p, "Gold", 9, r * 0.63, r * 0.63, h * 0.5, h * 0.5 + 3, x, y)
    for (x0, y0, h0), (x1, y1, h1) in ((tips[0], tips[1]), (tips[0], tips[2]), (tips[0], tips[3]),
                                       (tips[2], tips[6]), (tips[1], tips[5])):
        z = min(h0, h1) * 0.55
        L = math.hypot(x1 - x0, y1 - y0)
        rz = math.degrees(math.atan2(y1 - y0, x1 - x0))
        box(p, "Basalt", (x0 + x1) / 2, (y0 + y1) / 2, z, L, 7, 3, rz=rz)
        box(p, "Gold", (x0 + x1) / 2, (y0 + y1) / 2, z + 1.8, L, 7.4, 0.6, rz=rz)
        for t in (0.3, 0.7):                                           # lanterns under the bridge
            crystal(p, "Ember", x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z - 6, 1.6, 1.2, 2.4, n=6)
    crystal(p, "Shard", 0, 0, 450, 22, 50, 30, n=8)
    torus(p, "Cosmic", 34, 1.2, 0, 0, 450, n=32, m=3)
    torus(p, "Gold", 40, 1.6, 0, 0, 444, n=32, m=4, rx=14)
    torus(p, "Violet", 46, 0.8, 0, 0, 456, n=32, m=3, ry=-18)
    for k in range(10):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(60, 140)
        crag(p, math.cos(a) * d, math.sin(a) * d, 0, rng.uniform(8, 16), rng.uniform(20, 50), f"sc{k}")
    vein(p, 110, -20, 40, 26, "sv1")
    vein(p, -100, 90, 20, 22, "sv2")
    for k in range(6):
        a = math.radians(60 * k)
        crystal(p, ("Violet", "Shard")[k % 2], math.cos(a) * 60, math.sin(a) * 60, -110, 9, 1, 55, n=6)
    return p


# =============================================================================
#  ORBITERS -- props that drift round the hub (each its own mesh)
# =============================================================================

def prop_isle_shrine():
    p = Piece("hubprop_isle_shrine", "small floating isle with a domed shrine and a lantern")
    island_base(p, 0, 0, 22, 34, "isle shrine")
    for k in range(6):
        a = math.radians(60 * k)
        frustum(p, "Marble", 6, 0.8, 0.7, 2, 11, math.cos(a) * 7, math.sin(a) * 7)
    frustum(p, "Gold", 12, 8.4, 8.4, 11, 11.8)
    frustum(p, "Canvas", 12, 8.4, 0.6, 11.8, 16.5)
    crystal(p, "Shard", 0, 0, 7, 1.4, 2.4, 1.6, n=6)
    frustum(p, "MarbleDim", 12, 8, 8, 2, 2.6)
    lamp(p, 14, 4, 6, "Ember")
    crystal(p, "Violet", -6, -8, -26, 2, 1, 8, n=5)
    return p


def prop_isle_grove():
    p = Piece("hubprop_isle_grove", "floating isle with three crystal trees")
    island_base(p, 0, 0, 26, 38, "isle grove")
    for k, (x, y, h, col) in enumerate(((0, 0, 16, "Shard"), (10, 6, 11, "Violet"), (-9, 7, 12, "Rose"))):
        tube(p, "Wood", [(x, y, 2), (x + 0.6, y, h * 0.5), (x, y + 0.4, h)], [1.0, 0.7, 0.3], n=5)
        for j in range(5):
            a = math.radians(72 * j + k * 20)
            crystal(p, col, x + math.cos(a) * 2.6, y + math.sin(a) * 2.6, h + (j % 2) * 1.5, 1.5, 3.4, 1.2,
                    n=4, rz=j * 30)
        crystal(p, col, x, y, h + 1.5, 1.8, 4.5, 1.0, n=5)
    return p


def prop_isle_ruin():
    p = Piece("hubprop_isle_ruin", "floating isle with a broken arch")
    island_base(p, 0, 0, 24, 36, "isle ruin")
    for s in (-1, 1):
        frustum(p, "MarbleDim", 4, 2.2, 2.2, 2, 4, s * 8, 0, rot=45)
        frustum(p, "Marble", 4, 1.6, 1.4, 4, 18 if s < 0 else 12, s * 8, 0, rot=45)
    torus_arc(p, "Marble", 8, 1.1, 0, 0, 18, 90, 180, n=6, m=4, rx=90)
    box(p, "MarbleDim", 5, -6, 3, 4, 3, 2, rz=25)
    box(p, "MarbleDim", -3, 7, 2.6, 3, 2.4, 1.4, rz=-15)
    crystal(p, "Shard", 0, 0, 10, 1.2, 2.2, 1.8, n=6)
    return p


def prop_airship():
    p = Piece("hubprop_airship", "a trade galleon under a gas envelope; bow along +X")
    lump(p, "Wood", [(0, -30), (3.5, -26), (6.5, -16), (7.5, 0), (7, 16), (4, 26), (0, 32)], 10, "hull", 0.02,
         sy=0.8, bands=["Wood", "Wood", "Gold", "Wood", "Wood", "Wood"])
    for q in p.verts:                               # the lathe runs along Z: lay it along X, keel down
        q.x, q.z = q.z, q.x
    for i in range(len(p.verts)):
        v = p.verts[i]
        if v.z > 0.5:
            v.z = 0.5 + (v.z - 0.5) * 0.35           # flatten the top into a deck
    box(p, "Wood", 0, 0, 1.4, 52, 9.4, 0.6)                                     # deck
    box(p, "Gold", 0, 0, 2.1, 54, 10.2, 0.4)
    lump(p, "Canvas", [(0, -34), (6, -30), (10, -18), (11, 0), (10, 18), (6, 30), (0, 36)], 12, "envelope",
         0.0, sy=1.0)
    for q in p.verts[-(12 * 5 + 2):]:
        q.x, q.z = q.z, q.x + 26
    for x in (-18, 0, 18):                                                     # rigging
        for s in (-1, 1):
            tube(p, "Iron", [(x, s * 4, 2), (x, s * 7, 17)], [0.2, 0.2], n=3)
    for s in (-1, 1):                                                          # side sails
        box(p, "Marble", -4, s * 12, 7, 18, 0.4, 9, rx=s * 20)
        frustum(p, "Iron", 6, 1.2, 1.2, -2, 2, M=xf(-30, s * 6, 3, 0, 0, 90))  # propellers
        box(p, "BasaltLight", -32.4, s * 6, 3, 0.4, 1.0, 7)
    box(p, "Basalt", -24, 0, 5, 10, 7, 6)                                      # the cabin
    box(p, "Gold", -24, 0, 8.3, 11, 8, 0.6)
    crystal(p, "Ember", 30, 0, 3, 0.8, 1.2, 1.2, n=6)                         # bow lantern
    return p


def prop_skiff():
    p = Piece("hubprop_skiff", "small courier skiff with a sail; bow along +X")
    lump(p, "Wood", [(0, -9), (2.2, -6), (2.8, 0), (2.2, 6), (0, 10)], 8, "skiff", 0.02, sy=0.8)
    for q in p.verts:
        q.x, q.z = q.z, q.x * 0.6
    box(p, "Wood", 0, 0, 1.0, 15, 3.4, 0.3)
    tube(p, "Wood", [(1, 0, 1), (1, 0, 13)], [0.3, 0.2], n=4)
    box(p, "Marble", -1.6, 0, 7.5, 5.4, 0.25, 9.5)
    box(p, "Gold", -1.6, 0, 12.4, 6, 0.4, 0.4)
    crystal(p, "Shard", -8.5, 0, 0.4, 0.8, 0.6, 1.4, n=6)                      # the lift crystal at the stern
    return p


def cloud(name, seed, blobs):
    p = Piece(name, "a low-poly cloud; no collision")
    rng = random.Random(seed)
    for k in range(blobs):
        x, y = rng.uniform(-30, 30), rng.uniform(-10, 10)
        r = rng.uniform(9, 16)
        z = rng.uniform(0, 5)
        lump(p, "Cloud", [(0, z - r * 0.5), (r * 0.9, z - r * 0.35), (r, z), (r * 0.7, z + r * 0.55), (0, z + r * 0.8)],
             8, f"{seed}{k}", 0.15, x, y, sy=0.7, bands=["CloudShade", "Cloud", "Cloud", "Cloud"])
    return p


def prop_crystal_cluster():
    p = Piece("hubprop_crystal_cluster", "a floating crystal cluster")
    rng = random.Random("cluster")
    crystal(p, "Shard", 0, 0, 0, 3.2, 12, 8, n=6)
    for k in range(7):
        a = rng.uniform(0, 2 * math.pi)
        crystal(p, rng.choice(("Violet", "Rose", "Shard")), math.cos(a) * 3, math.sin(a) * 3, rng.uniform(-3, 3),
                rng.uniform(1, 2), rng.uniform(4, 8), rng.uniform(2, 4), n=5, rz=rng.uniform(0, 90))
    torus(p, "Gold", 6.5, 0.3, 0, 0, 0, n=16, m=3, rx=20)
    return p


def prop_rune_ring():
    p = Piece("hubprop_rune_ring", "a great rune ring, like the Engine's, adrift")
    torus(p, "Basalt", 30, 2.2, 0, 0, 0, n=40, m=4)
    torus(p, "Gold", 26.8, 0.6, 0, 0, 0, n=40, m=3)
    for k in range(12):
        a = math.radians(30 * k)
        box(p, "Cosmic", math.cos(a) * 30, math.sin(a) * 30, 2.4, 2.6, 2.6, 0.4, rz=30 * k + 45)
    return p


def prop_sky_lantern():
    p = Piece("hubprop_sky_lantern", "a paper sky-lantern with a flame inside")
    frustum(p, "Rose", 6, 1.8, 2.4, 0, 4.2)
    frustum(p, "Rose", 6, 2.4, 1.2, 4.2, 5.0)
    frustum(p, "Gold", 6, 1.9, 1.9, -0.3, 0)
    crystal(p, "Ember", 0, 0, 1.6, 0.6, 1.0, 0.4, n=4)
    return p


def prop_sky_whale():
    p = Piece("hubprop_sky_whale", "a sky whale; head along +X")
    lump(p, "Whale", [(0, -44), (3, -36), (9, -22), (12, -4), (12.5, 8), (10, 22), (5, 32), (0, 36)], 12, "whale",
         0.03, sy=0.85, bands=["Whale", "Whale", "Whale", "Whale", "Whale", "Whale", "Whale"])
    n0 = len(p.faces)
    for q in p.verts:
        q.x, q.z = q.z, q.x
    for i, f in enumerate(p.faces):                  # the belly, pale
        if sum(p.verts[j].z for j in f) / len(f) < -4:
            p.fmat[i] = "WhaleBelly"
    for s in (-1, 1):                                                  # flippers
        box(p, "Whale", 14, s * 14, -5, 10, 12, 1.2, rz=s * 30, rx=s * 15)
    box(p, "Whale", -44, 0, 0, 8, 26, 1.2, rz=0)                      # the flukes
    for s in (-1, 1):
        crystal(p, "Shard", 22, s * 8.6, 3, 0.9, 0.6, 0.6, n=5)        # eyes
    for k in range(5):                                                 # crystals grown on its back
        crystal(p, ("Shard", "Violet")[k % 2], -8 + k * 6, (k % 2 - 0.5) * 3, 11, 1.4, 4 + k % 3, 1.0, n=5)
    return p


def prop_waystone():
    p = Piece("hubprop_waystone", "a drifting waystone circled by gold rings")
    frustum(p, "Basalt", 4, 2.6, 1.6, -10, 10, rot=45)
    frustum(p, "Gold", 4, 1.6, 0, 10, 13, rot=45)
    frustum(p, "Gold", 4, 2.6, 0, -10, -13, rot=45)
    box(p, "Cosmic", 0, -1.9, 2, 1.2, 0.2, 9)
    torus(p, "Gold", 5, 0.3, 0, 0, 3, n=16, m=3, rx=70)
    torus(p, "Gold", 6.2, 0.3, 0, 0, -3, n=16, m=3, ry=60)
    return p


# =============================================================================
#  Build, check, export, render
# =============================================================================

HUB_BUILDERS = (build_platform, build_hall, build_archives, build_shop, build_training)
BACKDROP_BUILDERS = (build_backdrop_peaks, build_backdrop_mesa, build_backdrop_spires)
PROP_BUILDERS = (prop_isle_shrine, prop_isle_grove, prop_isle_ruin, prop_airship, prop_skiff,
                 lambda: cloud("hubprop_cloud_a", "ca", 6), lambda: cloud("hubprop_cloud_b", "cb", 4),
                 prop_crystal_cluster, prop_rune_ring, prop_sky_lantern, prop_sky_whale, prop_waystone)


def build_all():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = K["ensure_materials"]()
    groups = {}
    for gname, builders in (("Hub", HUB_BUILDERS), ("Backdrop", BACKDROP_BUILDERS), ("Orbiters", PROP_BUILDERS)):
        coll = bpy.data.collections.new("Crossroads_" + gname)
        bpy.context.scene.collection.children.link(coll)
        objs = []
        for b in builders:
            p = b()
            n = tris(p)
            o = K["to_object"](p, mats, coll)
            o["kit"] = "CROSSROADS"
            o["tris"] = n
            print(f"PIECE {p.name:28s} {n:6d} tris {'OVER' if n > TRI_LIMIT else 'ok'}")
            objs.append(o)
        groups[gname] = objs
    return groups


def check(groups):
    over = [(o.name, o["tris"]) for objs in groups.values() for o in objs if o["tris"] > TRI_LIMIT]
    return over


def export(groups):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    files = {"Hub": "crossroads_hub.fbx", "Backdrop": "crossroads_backdrop.fbx", "Orbiters": "crossroads_orbiters.fbx"}
    layout = {"pieces": {}, "anchors": ANCHORS, "note": "Blender coords (x, y north, z up), studs. "
              "Roblox = (x, z, -y). Bounding-box centre = where the MeshPart's Position goes."}
    for gname, objs in groups.items():
        path = os.path.join(EXPORT_DIR, files[gname])
        # Hub pieces keep their hub coordinates (they assemble where they land);
        # backdrop and orbiters are exported at their own origin.
        if gname == "Hub":
            bpy.ops.object.select_all(action="DESELECT")
            for o in objs:
                o.select_set(True)
            bpy.context.view_layer.objects.active = objs[0]
            with K["_ui_override"](selected_objects=list(objs), active_object=objs[0], object=objs[0]):
                K["_export_fbx"](path)
        else:
            K["_export_selected"](objs, path)
        for o in objs:
            cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
            mn = [min(c[i] for c in cs) for i in range(3)]
            mx = [max(c[i] for c in cs) for i in range(3)]
            layout["pieces"][o.name] = {"group": gname, "tris": o["tris"],
                                        "centre": [round((a + b) / 2, 3) for a, b in zip(mn, mx)],
                                        "size": [round(b - a, 3) for a, b in zip(mn, mx)]}
        print("EXPORTED", path)
    with open(LAYOUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(layout, fh, indent=1)
    print("LAYOUT", LAYOUT_JSON)


def main(argv):
    groups = build_all()
    over = check(groups)
    if over:
        print("OVER TRI LIMIT:", over)
    if "--export" in argv:
        export(groups)
    if "--save" in argv:
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
        print("SAVED", BLEND)
    if "--render" in argv:
        ns = {"__name__": "crossroads_render", "__file__": os.path.join(HERE, "render_crossroads.py")}
        exec(open(os.path.join(HERE, "render_crossroads.py"), encoding="utf-8").read(), ns)
        ns["render_all"](groups, ENGINE_BLEND, ENGINE_SCALE, RENDER_DIR)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
