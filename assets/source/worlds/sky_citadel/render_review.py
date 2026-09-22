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

Also builds a PREVIEW CHAIN -- the four pieces joined the way the generator
would join them (entry -> path -> path -> court -> arena) -- as linked
duplicates in a collection that is never exported. Every socket in this first
kit faces north or south, so every join is at yaw 0; once a bend piece exists
this chain should include a quarter turn. It is the "place a
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


def build_chain(pieces):
    """entry at the origin, north (+Y) through path, court, arena. The court
    and arena are the only pieces whose sockets differ in Kind, so this is the
    one order the grammar allows for a 4-piece kit."""
    coll = bpy.data.collections.get("PreviewChain_NotExported")
    if coll:
        for o in list(coll.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        coll = bpy.data.collections.new("PreviewChain_NotExported")
        bpy.context.scene.collection.children.link(coll)
    base = Vector((0, -1400, 0))
    for i, name in enumerate(["chunk_entry", "chunk_path_straight", "chunk_path_straight",
                              "chunk_spire_court", "chunk_boss_clearing"]):
        src = pieces[name]
        dup = bpy.data.objects.new("CHAIN_%d_%s" % (i, name), src.data)
        dup.location = base + Vector((0, 256 * i, 0))
        coll.objects.link(dup)
    return coll, base


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

    # hide the reference people from the per-piece hero shots? No -- keep
    # them: the 5-stud figure IS the scale check.
    for name, obj in pieces.items():
        c = obj.location
        look_at(cam, c + Vector((210, -250, 150)), c + Vector((0, 0, 20)))
        path = os.path.join(OUT, name + ".jpg")
        render(path)
        written.append(path)
        # ground-level view: what a player sees
        look_at(cam, c + Vector((0, -150, 8)), c + Vector((0, 0, 14)))
        cam.data.lens = 24
        path = os.path.join(OUT, name + "_ground.jpg")
        render(path)
        cam.data.lens = 35
        written.append(path)

    coll, base = build_chain(pieces)
    look_at(cam, base + Vector((520, 200, 420)), base + Vector((0, 560, 0)))
    cam.data.lens = 28
    path = os.path.join(OUT, "preview_chain.jpg")
    render(path)
    cam.data.lens = 35
    written.append(path)

    # the whole review row
    first = min(o.location.x for o in pieces.values())
    last = max(o.location.x for o in pieces.values())
    mid = (first + last) / 2
    look_at(cam, Vector((mid, -1100, 520)), Vector((mid, 0, 0)))
    path = os.path.join(OUT, "kit_overview.jpg")
    render(path)
    written.append(path)
    return written


if __name__ in ("__main__", "sc_review"):
    print(main())
