"""Review renders for the Sky Citadel kit. Writes JPEGs to ./renders/.

Run it HEADLESS -- it builds the kit itself when the scene has none:

    blender -b --factory-startup --python render_review.py

Rendering from inside an interactive session through the Blender MCP bridge
crashed Blender twice on 2026-09-22 (same shot both times); the headless run
renders all ten images in about three seconds and never touches the open
session.

Lighting approximates the world's in-game Environment (Content/Worlds/
SkyCitadel.luau): a warm low morning sun, pale blue sky fill, no fog. Blender's
studio default makes flat-shaded work look washed out -- ART_DIRECTION.md says
to author for the game's light, so this is that.

Also builds two previews from linked duplicates, never exported:

* PREVIEW CHAIN -- a map the grammar allows, joined as the generator joins it,
  including the bend's quarter turn. The "place a copy beside itself and look
  at the join" check from CHUNK_AUTHORING.md.
* PREVIEW CORNER -- four pieces meeting at one corner at four different yaws,
  so the corner beacons can be seen not to clip. It is the "place a
copy beside itself and look at the join" check from CHUNK_AUTHORING.md.
"""

import math
import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(__file__) if "__file__" in globals() else \
    r"C:\Dev\LUCKBOUND_v1.0\assets\source\worlds\sky_citadel"
OUT = os.path.join(HERE, "renders")


def setup_world():
    scene = bpy.context.scene
    world = bpy.data.worlds.get("SC_Sky") or bpy.data.worlds.new("SC_Sky")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.42, 0.62, 0.92, 1.0)
    bg.inputs["Strength"].default_value = 0.9
    scene.world = world

    sun = bpy.data.objects.get("SC_Sun")
    if not sun:
        sun = bpy.data.objects.new("SC_Sun", bpy.data.lights.new("SC_Sun", "SUN"))
        scene.collection.objects.link(sun)
    sun.data.energy = 4.0
    sun.data.color = (1.0, 0.92, 0.75)
    sun.data.angle = math.radians(2)
    sun.rotation_euler = (math.radians(55), 0, math.radians(35))

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    # JPEG, not PNG: these are committed, and re-rendered every iteration.
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 85
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    try:
        scene.eevee.use_bloom = True
    except AttributeError:
        pass


def camera():
    cam = bpy.data.objects.get("SC_Cam")
    if not cam:
        cam = bpy.data.objects.new("SC_Cam", bpy.data.cameras.new("SC_Cam"))
        bpy.context.scene.collection.objects.link(cam)
    cam.data.lens = 35
    cam.data.clip_end = 20000
    bpy.context.scene.camera = cam
    return cam


def look_at(cam, eye, target):
    cam.location = eye
    d = Vector(target) - Vector(eye)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def _preview(pieces, coll_name, placements):
    """Linked duplicates (they share the piece's mesh) in a collection that is
    never exported. placements: (piece name, (x, y), yaw degrees)."""
    coll = bpy.data.collections.get(coll_name)
    if coll:
        for o in list(coll.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        coll = bpy.data.collections.new(coll_name)
        bpy.context.scene.collection.children.link(coll)
    for i, (name, (x, y), yaw) in enumerate(placements):
        dup = bpy.data.objects.new("%s_%d_%s" % (coll_name[:5], i, name), pieces[name].data)
        dup.location = (x, y, 0)
        dup.rotation_euler = (0, 0, math.radians(yaw))
        coll.objects.link(dup)
    return coll


CHAIN_BASE = Vector((0, -3200, 0))


def build_chain(pieces):
    """A map the grammar allows, joined as the generator joins it: entry ->
    crossroads (straight on) -> shattered span -> west bend -> archive ->
    Hall of Winds -> arena, with the side lookout hung off the crossroads'
    spare east socket. Pieces after the bend are turned a quarter (yaw +90) so
    their south SKYWAY meets the bend's west one; the lookout is turned -90
    so its only socket faces the crossroads."""
    b = CHAIN_BASE
    return _preview(pieces, "PreviewChain_NotExported", [
        ("chunk_entry", (b.x, b.y), 0),
        ("chunk_crossroads", (b.x, b.y + 256), 0),
        ("chunk_side_lookout", (b.x + 256, b.y + 256), -90),
        ("chunk_path_shattered", (b.x, b.y + 512), 0),
        ("chunk_path_bend_west", (b.x, b.y + 768), 0),
        ("chunk_archive", (b.x - 256, b.y + 768), 90),
        ("chunk_spire_court_b", (b.x - 512, b.y + 768), 90),
        ("chunk_boss_clearing", (b.x - 768, b.y + 768), 90),
    ])


CORNER = Vector((2000, -3200, 0))


def build_corner(pieces):
    """Four pieces meeting at one corner, each at a different yaw: the case
    where identical flush beacons used to fuse into one block."""
    c = CORNER
    return _preview(pieces, "PreviewCorner_NotExported", [
        ("chunk_armory", (c.x - 128, c.y - 128), 0),
        ("chunk_observatory", (c.x + 128, c.y - 128), 90),
        ("chunk_path_straight", (c.x + 128, c.y + 128), 180),
        ("chunk_garden_terrace", (c.x - 128, c.y + 128), 270),
    ])


def main():
    os.makedirs(OUT, exist_ok=True)
    setup_world()
    cam = camera()
    pieces = {o.name: o for o in bpy.data.objects if o.get("kit") == "SKY_CITADEL"}
    if not pieces:
        # Run standalone (blender -b --python render_review.py): build first.
        builder = os.path.join(HERE, "build_sky_citadel_kit.py")
        g = {"__name__": "sc_kit", "__file__": builder}
        exec(open(builder, encoding="utf-8").read(), g)
        g["main"](export=False, save=False)
        setup_world()
        cam = camera()
        pieces = {o.name: o for o in bpy.data.objects if o.get("kit") == "SKY_CITADEL"}
    written = []

    def shot(name, eye, target, lens=35):
        look_at(cam, eye, target)
        cam.data.lens = lens
        path = os.path.join(OUT, name + ".jpg")
        render(path)
        written.append(path)

    # The 5-stud reference figure stays in every shot: it IS the scale check.
    for name, obj in pieces.items():
        c = obj.location
        shot(name, c + Vector((210, -250, 150)), c + Vector((0, 0, 20)))
        shot(name + "_ground", c + Vector((0, -150, 8)), c + Vector((0, 0, 14)), lens=24)

    build_chain(pieces)
    b = CHAIN_BASE
    shot("preview_chain", b + Vector((520, -420, 760)), b + Vector((-300, 480, 0)), lens=22)

    build_corner(pieces)
    c = CORNER
    shot("preview_corner", c + Vector((70, -90, 60)), c + Vector((0, 0, 4)), lens=24)
    shot("preview_corner_top", c + Vector((0, -1, 520)), c, lens=35)

    xs = [o.location.x for o in pieces.values()]
    ys = [o.location.y for o in pieces.values()]
    mid = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0))
    shot("kit_overview", mid + Vector((0, -1900, 1650)), mid, lens=30)
    return written


if __name__ in ("__main__", "sc_review"):
    print(main())
