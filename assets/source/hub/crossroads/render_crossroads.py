"""Review renders for the Crossroads. Called by build_crossroads_hub.py --render.

The Fate Engine is APPENDED from its own .blend at its in-game scale, for the
renders only: it is never exported from here and never modified. Lighting
approximates the hub's Theme: a purple pre-dawn sky, a low warm sun.
"""

import math
import os

import bpy
from mathutils import Vector


def setup_world():
    scene = bpy.context.scene
    world = bpy.data.worlds.new("Hub_Sky")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.16, 0.11, 0.30, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world
    sun = bpy.data.objects.new("Hub_Sun", bpy.data.lights.new("Hub_Sun", "SUN"))
    scene.collection.objects.link(sun)
    sun.data.energy = 3.2
    sun.data.color = (1.0, 0.84, 0.66)
    sun.rotation_euler = (math.radians(62), 0, math.radians(-40))
    fill = bpy.data.objects.new("Hub_Fill", bpy.data.lights.new("Hub_Fill", "SUN"))
    scene.collection.objects.link(fill)
    fill.data.energy = 0.9
    fill.data.color = (0.62, 0.55, 1.0)
    fill.rotation_euler = (math.radians(-50), 0, math.radians(140))
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 800
    scene.render.image_settings.file_format = "JPEG"
    scene.view_settings.view_transform = "Standard"
    for m in bpy.data.materials:                     # the palette materials glow where emissive
        if m.use_nodes:
            b = m.node_tree.nodes.get("Principled BSDF")
            if b and b.inputs["Emission Strength"].default_value > 0:
                b.inputs["Emission Strength"].default_value = 1.2


def append_engine(path, scale):
    if not os.path.exists(path):
        print("ENGINE NOT FOUND", path)
        return
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = [n for n in src.objects if not n.startswith("AI_") and n != "SpotAnchor"]
    root = bpy.data.objects.new("REF_FateEngine", None)
    bpy.context.scene.collection.objects.link(root)
    root.scale = (scale, scale, scale)
    coll = bpy.data.collections.new("REF_Engine")
    bpy.context.scene.collection.children.link(coll)
    for o in dst.objects:
        if o is None:
            continue
        coll.objects.link(o)
        if o.parent is None:
            o.parent = root


def person(x, y, z=0.0):
    me = bpy.data.meshes.new("REF_person")
    v = [(-0.7, -0.4, 0), (0.7, -0.4, 0), (0.7, 0.4, 0), (-0.7, 0.4, 0),
         (-0.7, -0.4, 5), (0.7, -0.4, 5), (0.7, 0.4, 5), (-0.7, 0.4, 5)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(v, [], f)
    me.materials.append(bpy.data.materials.get("SC_Ember"))
    o = bpy.data.objects.new("REF_person", me)
    o.location = (x, y, z)
    bpy.context.scene.collection.objects.link(o)


def shot(name, loc, target, lens=30, out=None, ortho=None):
    scene = bpy.context.scene
    cam = bpy.data.objects.get("REF_Cam")
    if not cam:
        cam = bpy.data.objects.new("REF_Cam", bpy.data.cameras.new("REF_Cam"))
        scene.collection.objects.link(cam)
    cam.data.clip_end = 20000
    cam.data.type = "ORTHO" if ortho else "PERSP"
    if ortho:
        cam.data.ortho_scale = ortho
    cam.data.lens = lens
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.filepath = os.path.join(out, name + ".jpg")
    bpy.ops.render.render(write_still=True)
    print("RENDER", name)


def lineup(objs, y=0.0, gap=40.0):
    """Lay objects out along X for a lineup shot; returns the span."""
    x = 0.0
    for o in objs:
        w = o.dimensions.x
        o.location = (x + w / 2 - (sum((c[0] for c in o.bound_box), 0) / 8), y, 0)
        x += w + gap
    return x


def render_all(groups, engine_blend, engine_scale, out):
    os.makedirs(out, exist_ok=True)
    setup_world()
    append_engine(engine_blend, engine_scale)
    for k in range(8):                                # the spawn ring, radius 105
        a = math.radians(45 * k)
        person(math.cos(a) * 105, math.sin(a) * 105)
    person(0, 160.5, 0.5)
    hub = groups["Hub"]
    hub = hub + groups["Animated"]
    others = groups["Backdrop"] + groups["Orbiters"] + groups.get("Sky", [])
    for o in others:
        o.hide_render = True
    shot("01_overview", (420, -520, 360), (0, 0, -20), 26, out)
    shot("02_top", (0, 0, 900), (0, 0.01, 0), out=out, ortho=640)
    shot("03_arrival", (0, -112, 7), (0, 0, 14), 24, out)
    shot("04_hall_north", (0, 88, 26), (0, 215, 20), 24, out)
    shot("05_archives_east", (95, -30, 22), (210, 8, 26), 24, out)
    shot("06_shop_south", (-10, -95, 18), (0, -205, 10), 24, out)
    shot("07_training_west", (-92, 30, 20), (-205, 0, 6), 24, out)
    shot("08_underside", (380, -380, -260), (0, 0, -60), 26, out)
    shot("09_promenade", (150, 150, 6), (0, 200, 8), 24, out)
    shot("12_levitator", (260, -300, -150), (0, 0, -130), 26, out)
    shot("13_stall", (-8, -178, 7), (-40, -208, 4), 28, out)
    for o in hub:
        o.hide_render = True
    for n in ("REF_Engine",):
        c = bpy.data.collections.get(n)
        if c:
            c.hide_render = True
    for o in bpy.data.objects:
        if o.name.startswith("REF_person"):
            o.hide_render = True
    bd = groups["Backdrop"]
    for o in bd:
        o.hide_render = False
    span = lineup(bd, gap=80)
    shot("10_backdrop", (span / 2, -1100, 250), (span / 2, 0, 80), 30, out)
    for o in bd:
        o.hide_render = True
    orb = groups["Orbiters"]
    cols, cell = 4, 90.0
    for i, o in enumerate(orb):                      # a grid, each prop centred in its cell
        o.hide_render = False
        cs = [Vector(c) for c in o.bound_box]
        c = sum(cs, Vector()) / 8
        o.location = (cell * (i % cols) - c.x, -cell * (i // cols) - c.y, -c.z)
    rows = (len(orb) + cols - 1) // cols
    cx, cy = cell * (cols - 1) / 2, -cell * (rows - 1) / 2
    shot("11_orbiters", (cx + 60, cy - 330, 260), (cx, cy, 0), 28, out)
    for o in orb:
        o.hide_render = True
    ships = [o for o in orb if "ship" in o.name or "whale" in o.name]
    x = 0.0
    for o in ships:
        o.hide_render = False
        cs = [Vector(c) for c in o.bound_box]
        c = sum(cs, Vector()) / 8
        w = o.dimensions.x
        o.location = (x + w / 2 - c.x, -c.y, -c.z)
        x += w + 25
    shot("14_ships", (x / 2, -520, 120), (x / 2, 0, 10), 22, out)
    shot("15_carrier", (ships[-2].location.x + 160, -190, 90), (ships[-2].location.x, 0, 20), 28, out)
    for o in bpy.data.objects:
        o.hide_render = True
    x = 0.0
    for o in groups.get("Sky", []):
        o.hide_render = False
        cs = [Vector(c) for c in o.bound_box]
        c = sum(cs, Vector()) / 8
        w = o.dimensions.x
        o.location = (x + w / 2 - c.x, -c.y, -c.z)
        x += w + 60
    for n in ("Hub_Sun", "Hub_Fill"):
        if bpy.data.objects.get(n):
            bpy.data.objects[n].hide_render = False
    shot("16_sky", (x / 2, -1500, 500), (x / 2, 0, 0), 26, out)
