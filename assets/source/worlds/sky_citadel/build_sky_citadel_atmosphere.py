"""Sky Citadel scenario atmospheres -- Blender previews.

Run HEADLESS (the only tested route; see SKY_CITADEL.md, Render headless):

    blender -b --factory-startup --python build_sky_citadel_atmosphere.py
    blender -b --factory-startup --python build_sky_citadel_atmosphere.py -- --only rime --no-save

What it builds: sky_citadel_atmosphere.blend, one SCENE per profile (the base
kit plus the seven scenarios -- switch scenes to switch atmospheres). Each
scene joins nine pieces of that scenario's kit into a map the grammar allows
(the same chain render_review.py uses), and hangs the profile's atmosphere
round it. Pieces and props are LINKED from sky_citadel_scenarios.blend, never
copied, so this file stays small and always shows the current kit.

What it reads: sky_citadel_atmospheres.py -- the same data that becomes
Environments_Scenarios.luau. Nothing here is a second source of numbers.

How faithful it is:
* The cloud sea is AmbienceCore.layoutClouds ported line for line: the same
  clusters (cumulus, stratus banks), billows, tufts, headings, ceiling clamp
  and colour gradient, at full graphics quality. Only the RNG differs.
* The sun sits where Roblox puts it for the profile's ClockTime at the default
  GeographicLatitude; ColorShiftTop/Bottom become a key and a cool fill.
* The sky is a gradient from Atmosphere.Color at the horizon to Decay
  overhead, with Glare round the sun and StarCount's stars; distance haze is
  the Mist pass tinted by Atmosphere.Color and scaled by Density.
* Grade, Bloom and SunRays are the compositor's HueSat, BrightContrast, a
  multiply tint and Glare. Blender is not Roblox: judge hue and mood here,
  and judge brightness in Studio.
* The proposed blocks (Weather, Pulse, Flashes, Canopy, Plumes, Debris,
  Aurora, Searchlights, Dome) are drawn the way the runtime would draw them,
  frozen at one instant. Weather is placed round each shot's camera, at the
  steady-state count Rate x Lifetime.

Renders go to renders/atmosphere/<profile>_<shot>.jpg, plus a contact sheet
per shot when Pillow is available (it is optional).
"""

import importlib.util
import math
import os
import random
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
_spec = importlib.util.spec_from_file_location("sky_citadel_atmospheres", os.path.join(HERE, "sky_citadel_atmospheres.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

SCEN_BLEND = os.path.join(HERE, "sky_citadel_scenarios.blend")
OUT_BLEND = os.path.join(HERE, "sky_citadel_atmosphere.blend")
RENDERS = os.path.join(HERE, "renders", "atmosphere")

PROFILES = ["base"] + A.ORDER
KIT_COLLECTION = {
    "base": "SkyCitadel_Kit", "unmooring": "SkyCitadel_Unmooring", "siege": "SkyCitadel_Siege",
    "lockdown": "SkyCitadel_Lockdown", "stormhawk": "SkyCitadel_Stormhawk", "rime": "SkyCitadel_Rime",
    "reclaimed": "SkyCitadel_Reclaimed", "aether_surge": "SkyCitadel_AetherSurge",
}
PROPS_COLLECTION = "Preview_Props_NotExported"

# render_review.py's chain -- entry, crossroads (lookout east, sealed gate
# west), shattered span, west bend, then archive, court and arena turned a
# quarter -- shifted so the map's middle sits at the origin.
CHAIN = [
    ("chunk_entry", (0, 0), 0),
    ("chunk_crossroads", (0, 256), 0),
    ("chunk_side_lookout", (256, 256), -90),
    ("chunk_cap_sealed_gate", (-256, 256), 90),
    ("chunk_path_shattered", (0, 512), 0),
    ("chunk_path_bend_west", (0, 768), 0),
    ("chunk_archive", (-256, 768), 90),
    ("chunk_spire_court_b", (-512, 768), 90),
    ("chunk_boss_clearing", (-768, 768), 90),
]
SHIFT = Vector((256, -384, 0))

# Shots, in studs round the map (sun in the east, +X). The 5-stud figure
# the kit carries is too small to see at this range on purpose: these judge
# the AIR, render_review.py judges the pieces.
SHOTS = {
    # Over the entry, looking across the whole map at the far sky, the sea
    # below the islands filling the lower third.
    "vista": dict(eye=(760, -1080, 300), target=(-420, 380, -70), lens=22),
    # A player on the crossroads, looking out past the sealed gate.
    "deck": dict(eye=(196, -196, 6), target=(-900, 160, -30), lens=18),
    # Out past the west edge, below deck level, looking back east INTO the
    # sun: the keels, the clouds drifting under them, the glare.
    "sea": dict(eye=(-1250, -760, -40), target=(0, 60, -70), lens=24),
}
LATITUDE = 41.7331  # Roblox's default Lighting.GeographicLatitude
RES = (1280, 720)


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def lin(c):
    """sRGB 0..255 -> linear 0..1 (Roblox colours are sRGB)."""
    def one(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (one(c[0]), one(c[1]), one(c[2]))


def rgba(c, a=1.0):
    return (*lin(c), a)


def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def roblox_to_blender(x, y, z):
    """Roblox (X, Y up, Z) -> Blender (X, Y north, Z up). Heading 0 = -Z = north."""
    return Vector((x, -z, y))


def sun_direction(clock):
    """Unit vector toward the sun for a ClockTime, at Roblox's default latitude
    and no declination: rises due east at 6:00."""
    lat = math.radians(LATITUDE)
    h = math.radians(15 * (clock - 12))
    el = math.asin(max(-1, min(1, math.cos(lat) * math.cos(h))))
    az = math.atan2(-math.sin(h), -math.sin(lat) * math.cos(h))  # from north, through east
    return Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el))), math.degrees(el)


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links


def emissive_mat(name, color_lin, strength, alpha=1.0, gradient=None, striate=False):
    """Emission + transparency. gradient=(axis 'U'|'V', lo_rgb, hi_rgb, alpha lo..hi fade)."""
    m, n, l = new_mat(name)
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    em = n.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    tr = n.new("ShaderNodeBsdfTransparent")
    mix = n.new("ShaderNodeMixShader")
    if gradient:
        axis, lo, hi, fade = gradient
        uv = n.new("ShaderNodeUVMap")
        sep = n.new("ShaderNodeSeparateXYZ")
        l.new(uv.outputs["UV"], sep.inputs[0])
        t = sep.outputs["X" if axis == "U" else "Y"]
        cmix = n.new("ShaderNodeMix")
        cmix.data_type = "RGBA"
        cmix.inputs[6].default_value = (*lo, 1)
        cmix.inputs[7].default_value = (*hi, 1)
        l.new(t, cmix.inputs[0])
        l.new(cmix.outputs[2], em.inputs["Color"])
        # alpha: a soft band -- zero at both ends, peak where fade says.
        curve = n.new("ShaderNodeFloatCurve")
        cm = curve.mapping
        pts = cm.curves[0].points
        pts[0].location = (0, 0)
        pts[1].location = (1, 0)
        for x, y in fade:
            pts.new(x, y)
        cm.update()
        l.new(t, curve.inputs["Value"])
        mul = n.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = alpha
        l.new(curve.outputs[0], mul.inputs[0])
        if striate:
            # Vertical rays along the curtain: bands across U.
            wave = n.new("ShaderNodeTexNoise")
            wave.inputs["Scale"].default_value = 3.0
            wave.inputs["Detail"].default_value = 2
            comb = n.new("ShaderNodeCombineXYZ")
            l.new(sep.outputs["X"], comb.inputs["X"])
            scale = n.new("ShaderNodeVectorMath")
            scale.operation = "SCALE"
            scale.inputs["Scale"].default_value = 40
            l.new(comb.outputs[0], scale.inputs[0])
            l.new(scale.outputs[0], wave.inputs["Vector"])
            ramp = n.new("ShaderNodeMapRange")
            ramp.inputs["From Min"].default_value = 0.35
            ramp.inputs["From Max"].default_value = 0.7
            l.new(wave.outputs["Fac"], ramp.inputs["Value"])
            mul2 = n.new("ShaderNodeMath")
            mul2.operation = "MULTIPLY"
            l.new(mul.outputs[0], mul2.inputs[0])
            l.new(ramp.outputs[0], mul2.inputs[1])
            mul = mul2
        l.new(mul.outputs[0], mix.inputs[0])
    else:
        em.inputs["Color"].default_value = (*color_lin, 1)
        mix.inputs[0].default_value = alpha
    l.new(tr.outputs[0], mix.inputs[1])
    l.new(em.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs[0])
    m.surface_render_method = "BLENDED"
    return m


def object_color_mat(name, roughness=0.9, emission=0.0, snow=False):
    """A diffuse material whose colour and alpha come from each object's own
    colour -- one material for a whole cloud layer, like one Roblox part
    colour per puff."""
    m, n, l = new_mat(name)
    bsdf = n["Principled BSDF"]
    info = n.new("ShaderNodeObjectInfo")
    l.new(info.outputs["Color"], bsdf.inputs["Base Color"])
    l.new(info.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Specular IOR Level"].default_value = 0.15
    if emission:
        l.new(info.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emission
    if snow:
        # Roblox's Snow finish: a fine sparkle-and-lump normal.
        tex = n.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 0.35
        tex.inputs["Detail"].default_value = 6
        bump = n.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.25
        coord = n.new("ShaderNodeTexCoord")
        l.new(coord.outputs["Object"], tex.inputs["Vector"])
        l.new(tex.outputs["Fac"], bump.inputs["Height"])
        l.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    m.surface_render_method = "DITHERED"
    return m


_SPHERE = None


def sphere_mesh():
    """The one ellipsoid every cloud puff shares (Roblox: a SpecialMesh sphere)."""
    global _SPHERE
    if _SPHERE is None:
        me = bpy.data.meshes.new("AT_CloudPuff")
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.5)
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        _SPHERE = me
    return _SPHERE


def link(obj, coll):
    coll.objects.link(obj)
    return obj


# --------------------------------------------------------------------------
# AmbienceCore.layoutClouds, ported. nxt() is the RNG, 0..1.
# --------------------------------------------------------------------------
DEFAULT_MIX = {"Cumulus": 0.55, "Stratus": 0.3, "Wisp": 0.15}


def pick_style(mix, roll):
    total = sum(mix.values())
    acc = 0
    for name in ("Cumulus", "Stratus", "Wisp"):
        acc += mix.get(name, 0) / total
        if roll <= acc:
            return name
    return "Cumulus"


def layout_clouds(layer, count, billow_scale, nxt, ceiling, vertical="Depth"):
    clouds = []
    half = layer["Radius"]
    mix = layer.get("Mix") or DEFAULT_MIX
    max_billows = max(0, math.floor(layer.get("Billows", 0) * billow_scale + 0.5))
    max_tufts = max(0, math.floor(layer.get("Tufts", 0) * billow_scale * billow_scale + 0.5))
    for _ in range(count):
        size = layer["SizeMin"] + (layer["SizeMax"] - layer["SizeMin"]) * nxt()
        style = pick_style(mix, nxt())
        yaw = nxt() * math.pi * 2
        c, sn = math.cos(yaw), math.sin(yaw)
        parts = []

        def add(dx, dy, dz, w, h, l, shade, fade):
            parts.append({
                "DX": dx * c + dz * sn, "DY": dy, "DZ": -dx * sn + dz * c,
                "Width": w, "Height": h, "Length": l,
                "Shade": min(1, max(0, shade + (nxt() - 0.5) * 0.16)), "Fade": fade,
            })

        base_h = size * layer["Thickness"]
        if style == "Wisp":
            streaks = 2 + math.floor(nxt() * 3)
            for i in range(1, streaks + 1):
                along = (i - (streaks + 1) / 2) * size * 0.35
                add(along, (nxt() - 0.5) * base_h * 0.3, (nxt() - 0.5) * size * 0.25,
                    size * (1.1 + 0.6 * nxt()), base_h * (0.2 + 0.15 * nxt()), size * (0.2 + 0.15 * nxt()),
                    0.25, 0.3 + 0.2 * nxt())
        elif style == "Stratus":
            puffs = 4 + math.floor(nxt() * 3)
            span_l = size * 1.2
            for i in range(1, puffs + 1):
                t = (i - (puffs + 1) / 2) / puffs
                w = size * (0.3 + 0.15 * nxt())
                add((nxt() - 0.5) * size * 0.3, (nxt() - 0.5) * w * 0.15, t * span_l,
                    w, w * (0.4 + 0.15 * nxt()), w * (0.9 + 0.25 * nxt()), 0.5 + 0.3 * nxt(), 0)
            for _ in range(min(max_billows, 1 + math.floor(nxt() * 2))):
                w = size * (0.25 + 0.1 * nxt())
                add((nxt() - 0.5) * size * 0.2, w * 0.2, (nxt() - 0.5) * span_l * 0.6,
                    w, w * (0.45 + 0.15 * nxt()), w * (0.9 + 0.2 * nxt()), 0.2 * nxt(), 0)
        else:
            spread = size * 0.5
            lobes = 2 + math.floor(nxt() * 2)
            base_tall = 0
            for i in range(1, lobes + 1):
                t = (i - (lobes + 1) / 2) / lobes
                w = size * (0.45 + 0.15 * nxt())
                h = w * (0.4 + 0.1 * nxt())
                base_tall = max(base_tall, h)
                add(t * spread, 0, (nxt() - 0.5) * spread * 0.4, w, h, w * (0.8 + 0.3 * nxt()), 1, 0)
            n = max(1 if max_billows > 0 else 0, math.floor(max_billows * (0.5 + 0.5 * nxt()) + 0.5))
            for _ in range(n):
                w = size * (0.3 + 0.25 * nxt())
                h = w * (0.5 + 0.2 * nxt())
                bx = (nxt() * 2 - 1) * spread * 0.55
                by = base_tall * 0.3 + h * (0.2 + 0.2 * nxt())
                bz = (nxt() * 2 - 1) * spread * 0.35
                add(bx, by, bz, w, h, w * (0.8 + 0.4 * nxt()), 0.15 * nxt(), 0)
                tufts = math.floor(max_tufts * (0.4 + 0.6 * nxt()) + 0.5)
                for _ in range(tufts):
                    tw = w * (0.28 + 0.22 * nxt())
                    ang = nxt() * math.pi * 2
                    reach = w * 0.3 * nxt()
                    add(bx + math.cos(ang) * reach, by + h * (0.25 + 0.15 * nxt()), bz + math.sin(ang) * reach,
                        tw, tw * (0.55 + 0.2 * nxt()), tw * (0.85 + 0.3 * nxt()), 0.05 * nxt(), 0)
        y = (nxt() * 2 - 1) * base_h * 0.5
        if ceiling is not None:
            top = max(p["DY"] + p["Height"] / 2 for p in parts)
            y = min(y, layer[vertical] - ceiling - top)
        clouds.append({"X": (nxt() * 2 - 1) * half, "Z": (nxt() * 2 - 1) * half, "Y": y,
                       "Yaw": yaw, "Style": style, "Parts": parts})
    return clouds


def build_cloud_layer(layer, index, coll, rng, ceiling, above=False, tag="Sea"):
    """One layer as puff objects. Returns the clouds (for Flashes)."""
    vertical = "Height" if above else "Depth"
    clouds = layout_clouds(layer, layer["Count"], 1.0, rng.random, None if above else ceiling, vertical)
    mat = object_color_mat("AT_%s%d_%s" % (tag, index, coll.name), snow=layer.get("Material") == "Snow")
    shade = layer.get("Shade", layer["Color"])
    top, under = lin(layer["Color"]), lin(shade)
    plane = layer[vertical] if above else -layer[vertical]
    for ci, cloud in enumerate(clouds):
        for pi, p in enumerate(cloud["Parts"]):
            o = bpy.data.objects.new("%s%d_c%03d_%02d" % (tag, index, ci, pi), sphere_mesh())
            o.location = roblox_to_blender(cloud["X"] + p["DX"], plane + cloud["Y"] + p["DY"], cloud["Z"] + p["DZ"])
            o.rotation_euler = (0, 0, cloud["Yaw"])
            o.scale = (p["Width"], p["Length"], p["Height"])
            col = lerp3(top, under, p["Shade"])
            o.color = (*col, 1 - min(0.95, layer["Transparency"] + p["Fade"]))
            o.visible_shadow = False  # CastShadow = false
            link(o, coll)
            _assign(o, mat)
    return clouds


def _assign(obj, mat):
    """Per-object material on a shared mesh (the slot links to the object)."""
    if not obj.data.materials:
        obj.data.materials.append(None)
    obj.material_slots[0].link = "OBJECT"
    obj.material_slots[0].material = mat


# --------------------------------------------------------------------------
# the map: nine pieces of one scenario, with their props
# --------------------------------------------------------------------------
def load_library(profiles):
    wanted = {KIT_COLLECTION[p] for p in profiles} | {PROPS_COLLECTION}
    with bpy.data.libraries.load(SCEN_BLEND, link=True, relative=True) as (src, dst):
        dst.collections = [c for c in src.collections if c in wanted]
    kids = {}
    for o in bpy.data.collections[PROPS_COLLECTION].all_objects:
        if o.parent:
            kids.setdefault(o.parent.name, []).append(o)
    return kids


def build_map(profile, coll, kids):
    suffix = "" if profile == "base" else "__" + profile
    objs = bpy.data.collections[KIT_COLLECTION[profile]].all_objects
    for piece, (x, y), yaw in CHAIN:
        src = objs.get(piece + suffix)
        if src is None:
            print("  missing piece", piece + suffix)
            continue
        m = Matrix.Translation(Vector((x, y, 0)) + SHIFT) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
        o = link(bpy.data.objects.new("Map_" + piece, src.data), coll)
        o.matrix_world = m
        inv = src.matrix_world.inverted()
        for k in kids.get(src.name, []):
            c = link(bpy.data.objects.new("Map_" + k.name, k.data), coll)
            c.matrix_world = m @ inv @ k.matrix_world


# --------------------------------------------------------------------------
# sky, sun, haze
# --------------------------------------------------------------------------
def build_world(scene, env, sun_dir, sun_el):
    atm = env.get("Atmosphere") or {"Density": 0, "Offset": 0, "Color": env["FogColor"],
                                    "Decay": env["FogColor"], "Glare": 0, "Haze": 0}
    sky = env.get("Sky") or {}
    w = bpy.data.worlds.new("AT_Sky_" + scene.name)
    scene.world = w
    w.use_nodes = True
    n, l = w.node_tree.nodes, w.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputWorld")

    def math_node(op, a=None, b=None):
        m = n.new("ShaderNodeMath")
        m.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                l.new(v, m.inputs[i])
        return m.outputs[0]

    def mix_rgb(fac, a, b, blend="MIX"):
        m = n.new("ShaderNodeMix")
        m.data_type = "RGBA"
        m.blend_type = blend
        if isinstance(fac, (int, float)):
            m.inputs[0].default_value = fac
        else:
            l.new(fac, m.inputs[0])
        for sock, v in ((m.inputs[6], a), (m.inputs[7], b)):
            if isinstance(v, tuple):
                sock.default_value = (*v, 1)
            else:
                l.new(v, sock)
        return m.outputs[2]

    coord = n.new("ShaderNodeTexCoord")
    norm = n.new("ShaderNodeVectorMath")
    norm.operation = "NORMALIZE"
    l.new(coord.outputs["Generated"], norm.inputs[0])
    d = norm.outputs[0]
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(d, sep.inputs[0])
    z = sep.outputs["Z"]

    horizon, zenith = lin(atm["Color"]), lin(atm["Decay"])
    # Haze lifts the horizon colour up the sky; Offset pushes it higher still.
    band = 0.12 + atm.get("Offset", 0) * 0.8 + atm["Haze"] * 0.06
    f = math_node("POWER", math_node("MINIMUM", math_node("MAXIMUM", math_node("DIVIDE", z, band), 0), 1), 0.65)
    sky_col = mix_rgb(f, horizon, zenith)

    # Below the horizon: the far sea, hazed toward the horizon colour.
    deep = env["CloudSea"][-1] if env.get("CloudSea") else {"Color": atm["Color"], "Shade": atm["Color"]}
    under = lerp3(lin(deep["Color"]), lin(deep.get("Shade", deep["Color"])), 0.4)
    g = math_node("MINIMUM", math_node("MAXIMUM", math_node("DIVIDE", z, -0.25), 0), 1)
    sky_col = mix_rgb(g, sky_col, lerp3(horizon, under, 0.6))

    # The sun: a halo scaled by Glare and a small hot disc (when it is up).
    dot = n.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    l.new(d, dot.inputs[0])
    dot.inputs[1].default_value = sun_dir
    s = math_node("MAXIMUM", dot.outputs["Value"], 0)
    up = max(0.0, min(1.0, (sun_el + 4) / 6))
    halo = math_node("ADD", math_node("MULTIPLY", math_node("POWER", s, 6), 0.35),
                     math_node("MULTIPLY", math_node("POWER", s, 90), 1.4))
    halo = math_node("MULTIPLY", halo, atm["Glare"] * up)
    sky_col = mix_rgb(halo, sky_col, lerp3(horizon, (1, 0.95, 0.85), 0.5), "ADD")
    size = math.radians(max(1.0, sky.get("SunAngularSize", 21)) * 0.14)
    disc = math_node("GREATER_THAN", s, math.cos(size))
    sky_col = mix_rgb(math_node("MULTIPLY", disc, 1.0 * up), sky_col, (2.6, 2.4, 2.1), "ADD")

    # Stars: fewer and dimmer the more sun there is.
    stars = sky.get("StarCount", 3000)
    if stars > 0:
        vor = n.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = 260
        l.new(d, vor.inputs["Vector"])
        radius = 0.02 + 0.05 * min(1, stars / 3000)
        dotm = math_node("LESS_THAN", vor.outputs["Distance"], radius)
        noise = n.new("ShaderNodeTexWhiteNoise")
        noise.noise_dimensions = "3D"
        l.new(vor.outputs["Position"], noise.inputs["Vector"])
        keep = math_node("LESS_THAN", noise.outputs["Value"], min(1, 0.15 + stars / 2000))
        daylight = max(0.0, min(1.0, (sun_el + 6) / 10))
        star = math_node("MULTIPLY", math_node("MULTIPLY", dotm, keep),
                         math_node("MINIMUM", math_node("MAXIMUM", math_node("MULTIPLY", z, 5), 0), 1))
        star = math_node("MULTIPLY", star, 2.5 * (1 - 0.85 * daylight))
        sky_col = mix_rgb(star, sky_col, (1, 1, 1), "ADD")

    cam_bg = n.new("ShaderNodeBackground")
    l.new(sky_col, cam_bg.inputs["Color"])
    # What LIGHTS the scene is OutdoorAmbient, not the painted sky.
    amb_bg = n.new("ShaderNodeBackground")
    amb_bg.inputs["Color"].default_value = (*lin(env.get("OutdoorAmbientColor", env["AmbientColor"])), 1)
    amb_bg.inputs["Strength"].default_value = 0.75
    lp = n.new("ShaderNodeLightPath")
    mix = n.new("ShaderNodeMixShader")
    l.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    l.new(amb_bg.outputs[0], mix.inputs[1])
    l.new(cam_bg.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs["Surface"])

    w.mist_settings.start = 120
    w.mist_settings.depth = 4200
    w.mist_settings.falloff = "LINEAR"


def build_lights(scene, env, coll, sun_dir, sun_el):
    top = lerp3((1, 1, 1), lin(env.get("ColorShiftTop", (255, 255, 255))), 0.7)
    key = bpy.data.objects.new("AT_Sun", bpy.data.lights.new("AT_Sun_" + scene.name, "SUN"))
    key.data.color = top
    key.data.angle = math.radians(1.5)
    # A sun under the horizon lights nothing; the blue hour is ambient only.
    key.data.energy = env["Brightness"] * 1.6 * max(0.0, min(1.0, (sun_el + 1) / 4))
    key.rotation_euler = sun_dir.to_track_quat("Z", "Y").to_euler()
    link(key, coll)
    if sun_el < 0:
        # Below the horizon Roblox lights the scene from the MOON, opposite.
        moon = bpy.data.objects.new("AT_Moon", bpy.data.lights.new("AT_Moon_" + scene.name, "SUN"))
        moon.data.color = lerp3((0.75, 0.82, 1.0), top, 0.3)
        moon.data.energy = env["Brightness"] * 0.9
        moon_dir = Vector((-sun_dir.x, -sun_dir.y, 0.55)).normalized()
        moon.rotation_euler = moon_dir.to_track_quat("Z", "Y").to_euler()
        link(moon, coll)
    fill = bpy.data.objects.new("AT_ShadowFill", bpy.data.lights.new("AT_Fill_" + scene.name, "SUN"))
    fill.data.color = lin(env.get("ColorShiftBottom", env["AmbientColor"]))
    fill.data.energy = 0.55
    fill.data.use_shadow = False
    away = Vector((-sun_dir.x, -sun_dir.y, 0.6)).normalized()
    fill.rotation_euler = away.to_track_quat("Z", "Y").to_euler()
    link(fill, coll)


# --------------------------------------------------------------------------
# the proposed blocks
# --------------------------------------------------------------------------
def particle_cloud(name, w, coll, rng, seed_count=None):
    """A Weather stream frozen at one instant: Rate x Lifetime particles in its
    Box, each a small ball or, with Streak, a thin rod along its direction."""
    count = seed_count or max(1, int(w["Rate"] * w["Lifetime"] * 0.8))
    bx, by, bz = w["Box"]
    d = roblox_to_blender(*w["Direction"]).normalized()
    travel = w["Speed"] * w["Lifetime"] * 0.5
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    size = w["Size"]
    streak = max(1.0, w.get("Streak", 0) or 1.0)
    for _ in range(count):
        centre = Vector(((rng.random() - 0.5) * bx, (rng.random() - 0.5) * bz, (rng.random() - 0.5) * by))
        centre += d * (rng.random() - 0.5) * min(travel, 60)
        if streak > 1:
            geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=size / 2, radius2=size / 2,
                                         depth=size * streak)
            rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
            bmesh.ops.transform(bm, matrix=Matrix.Translation(centre) @ rot, verts=geom["verts"])
        else:
            geom = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=size / 2)
            bmesh.ops.translate(bm, vec=centre, verts=geom["verts"])
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me), coll)
    col = lin(w["Color"])
    alpha = 1 - w.get("Transparency", 0)
    if w.get("Emission", 0) > 0:
        mat = emissive_mat(name + "_M", col, 6 * w["Emission"], alpha)
    else:
        mat = emissive_mat(name + "_M", col, 1.4, alpha)
    me.materials.append(mat)
    o.visible_shadow = False
    return o


def build_weather(env, coll, rng):
    followers = []
    for w in env.get("Weather") or []:
        followers.append(particle_cloud("AT_Weather_" + w["Name"], w, coll, rng))
    m = env.get("Motes")
    if m:
        mote = {"Name": "Motes", "Rate": m["Rate"], "Lifetime": m["Lifetime"], "Speed": m["Speed"],
                "Size": m["Size"], "Color": m["Color"], "Direction": A.Vec(0, 1, 0), "Streak": 0,
                "Emission": 1, "Transparency": 0.3, "Box": A.Vec(160, 60, 160)}
        followers.append(particle_cloud("AT_Motes", mote, coll, rng))
    return followers


def rock_mesh(name, rng):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.5)
    for v in bm.verts:
        v.co *= 0.6 + 0.6 * rng.random()
    bm.to_mesh(me)
    bm.free()
    return me


def build_debris(env, coll, rng):
    d = env.get("Debris")
    if not d:
        return
    near = env["CloudSea"][0]["Depth"] if env.get("CloudSea") else 200
    fall = near / d["Speed"]
    count = max(3, int(d["Rate"] * fall * 1.5))
    mat, n, l = new_mat("AT_Debris")
    n["Principled BSDF"].inputs["Base Color"].default_value = rgba(d["Color"])
    n["Principled BSDF"].inputs["Roughness"].default_value = 0.8
    for i in range(count):
        o = link(bpy.data.objects.new("AT_Debris_%02d" % i, rock_mesh("AT_Rock_%02d" % i, rng)), coll)
        o.data.materials.append(mat)
        ang = rng.random() * math.tau
        r = d["Radius"] * (0.3 + 0.7 * math.sqrt(rng.random()))
        o.location = (math.cos(ang) * r, math.sin(ang) * r, -20 - rng.random() * (near - 40))
        o.rotation_euler = (rng.random() * 6.3, rng.random() * 6.3, rng.random() * 6.3)
        s = d["SizeMin"] + (d["SizeMax"] - d["SizeMin"]) * rng.random()
        o.scale = (s, s * (0.6 + 0.5 * rng.random()), s * (0.5 + 0.4 * rng.random()))


def build_plumes(env, coll, rng):
    p = env.get("Plumes")
    if not p:
        return
    mat = object_color_mat("AT_Plume", emission=0)
    glow = object_color_mat("AT_PlumeGlow", emission=6)
    lean = math.radians(p["Lean"])
    head = math.radians(p["Heading"])
    wind = roblox_to_blender(math.sin(head), 0, -math.cos(head)).normalized()
    base_z = -(env["CloudSea"][0]["Depth"] if env.get("CloudSea") else 200)
    for i in range(p["Count"]):
        ang = (i + 0.3 * rng.random()) / p["Count"] * math.tau + 0.4
        dist = p["DistanceMin"] + (p["DistanceMax"] - p["DistanceMin"]) * rng.random()
        root = Vector((math.cos(ang) * dist, math.sin(ang) * dist, base_z))
        height = p["Height"] * (0.7 + 0.5 * rng.random())
        steps = 34
        for k in range(steps):
            t = k / (steps - 1)
            z = t * height
            centre = root + Vector((0, 0, z)) + wind * math.tan(lean) * z * (0.4 + 0.6 * t)
            wdt = p["Width"] * (0.8 + 2.2 * t) * (0.8 + 0.4 * rng.random())
            o = link(bpy.data.objects.new("AT_Plume%d_%02d" % (i, k), sphere_mesh()), coll)
            o.location = centre + Vector(((rng.random() - 0.5) * wdt * 0.3, (rng.random() - 0.5) * wdt * 0.3, 0))
            o.scale = (wdt, wdt * (0.8 + 0.3 * rng.random()), wdt * 0.55)
            o.rotation_euler = (0, 0, rng.random() * 6.3)
            col = lerp3(lin(p["Shade"]), lin(p["Color"]), min(1, t * 1.6))
            o.color = (*col, 1)
            _assign(o, mat)
            o.visible_shadow = False
        g = link(bpy.data.objects.new("AT_PlumeGlow%d" % i, sphere_mesh()), coll)
        g.location = root + Vector((0, 0, 30))
        g.scale = (p["Width"] * 0.6, p["Width"] * 0.6, p["Width"] * 0.25)
        g.color = (*lin(p["Glow"]), 1)
        _assign(g, glow)


def ribbon(name, length, drop, waves, phase, coll, mat, rng, centre, heading):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    cols, rows = 96, 10
    d_along = Vector((math.cos(heading), math.sin(heading), 0))
    d_side = Vector((-d_along.y, d_along.x, 0))
    grid = []
    for i in range(cols + 1):
        u = i / cols
        s = (u - 0.5) * length
        sway = math.sin(u * math.tau * waves + phase) * length * 0.11 + math.sin(u * 23 + phase * 2) * 40
        row = []
        for j in range(rows + 1):
            v = j / rows
            p = centre + d_along * s + d_side * (sway + v * 25) + Vector((0, 0, -drop * (1 - v)))
            row.append(bm.verts.new(p))
        grid.append(row)
    for i in range(cols):
        for j in range(rows):
            f = bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
            for loop, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uv].uv = (a / cols, b / rows)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me), coll)
    me.materials.append(mat)
    o.visible_shadow = False
    return o


def build_aurora(env, coll, rng):
    au = env.get("Aurora")
    if not au:
        return
    mat = emissive_mat("AT_Aurora", None, 1.6, (1 - au["Transparency"]) * 0.8,
                       gradient=("V", lin(au["Color"]), lin(au["Tip"]),
                                 [(0.08, 0.7), (0.3, 0.5), (0.7, 0.15)]), striate=True)
    for i in range(au["Count"]):
        centre = Vector(((rng.random() - 0.5) * 900, 500 + i * 380 + rng.random() * 200, au["Height"] + i * 60))
        ribbon("AT_Aurora%d" % i, au["Length"] * (0.8 + 0.4 * rng.random()), au["Drop"], au["Waves"],
               rng.random() * 6.3, coll, mat, rng, centre, math.radians(-10 + rng.random() * 30))


def build_searchlights(env, coll, rng):
    s = env.get("Searchlights")
    if not s:
        return
    mat = emissive_mat("AT_Beam", None, 4.0, 1.0,
                       gradient=("V", lin(s["Color"]), lin(s["Color"]), [(0.05, 0.28), (0.5, 0.1), (0.95, 0.0)]))
    for i in range(s["Count"]):
        ang = (i + 0.5 * rng.random()) / s["Count"] * math.tau
        root = Vector((math.cos(ang) * s["Radius"], math.sin(ang) * s["Radius"], -90))
        tilt = math.radians(s["Tilt"] * (0.5 + rng.random()))
        az = rng.random() * math.tau
        axis = Vector((math.sin(tilt) * math.cos(az), math.sin(tilt) * math.sin(az), math.cos(tilt)))
        me = bpy.data.meshes.new("AT_Beam%d" % i)
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new("UVMap")
        seg = 16
        ring0 = [bm.verts.new((math.cos(a) * s["Width"] * 0.25, math.sin(a) * s["Width"] * 0.25, 0))
                 for a in (k / seg * math.tau for k in range(seg))]
        ring1 = [bm.verts.new((math.cos(a) * s["Width"] * 2.2, math.sin(a) * s["Width"] * 2.2, s["Length"]))
                 for a in (k / seg * math.tau for k in range(seg))]
        for k in range(seg):
            f = bm.faces.new((ring0[k], ring0[(k + 1) % seg], ring1[(k + 1) % seg], ring1[k]))
            for loop, v in zip(f.loops, (0, 0, 1, 1)):
                loop[uvl].uv = (k / seg, v)
        bm.to_mesh(me)
        bm.free()
        o = link(bpy.data.objects.new("AT_Beam%d" % i, me), coll)
        me.materials.append(mat)
        o.location = root
        o.rotation_euler = axis.to_track_quat("Z", "Y").to_euler()
        o.visible_shadow = False
        lamp = link(bpy.data.objects.new("AT_BeamLamp%d" % i, bpy.data.lights.new("AT_BeamLamp%d" % i, "POINT")), coll)
        lamp.data.color = lin(s["Color"])
        lamp.data.energy = 4e5
        lamp.data.shadow_soft_size = 20
        lamp.location = root + Vector((0, 0, -10))


def build_dome(env, coll):
    dm = env.get("Dome")
    if not dm:
        return
    m, n, l = new_mat("AT_Dome")
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    em = n.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = rgba(dm["Color"])
    em.inputs["Strength"].default_value = 2.0
    tr = n.new("ShaderNodeBsdfTransparent")
    mix = n.new("ShaderNodeMixShader")
    # ForceField reads as cells and a bright rim: a Voronoi cell edge on the
    # sphere, plus a fresnel so the silhouette glows.
    coord = n.new("ShaderNodeTexCoord")
    vor = n.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 1 / 120  # ~120-stud cells
    l.new(coord.outputs["Object"], vor.inputs["Vector"])
    edge = n.new("ShaderNodeMath")
    edge.operation = "LESS_THAN"
    edge.inputs[1].default_value = 0.012
    l.new(vor.outputs["Distance"], edge.inputs[0])
    fres = n.new("ShaderNodeLayerWeight")
    fres.inputs["Blend"].default_value = 0.35
    base = 1 - dm["Transparency"]
    a = n.new("ShaderNodeMath")
    a.operation = "MULTIPLY_ADD"
    l.new(edge.outputs[0], a.inputs[0])
    a.inputs[1].default_value = base * 0.9
    a.inputs[2].default_value = base * 0.08
    b = n.new("ShaderNodeMath")
    b.operation = "MULTIPLY_ADD"
    l.new(fres.outputs["Facing"], b.inputs[0])
    b.inputs[1].default_value = base * 0.7
    l.new(a.outputs[0], b.inputs[2])
    l.new(b.outputs[0], mix.inputs[0])
    l.new(tr.outputs[0], mix.inputs[1])
    l.new(em.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs[0])
    m.surface_render_method = "BLENDED"
    m.use_backface_culling = False
    me = bpy.data.meshes.new("AT_Dome")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=dm["Radius"])
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = link(bpy.data.objects.new("AT_Dome", me), coll)
    me.materials.append(m)
    o.location = (0, 0, -80)
    o.visible_shadow = False


def bolt(name, start, end, rng, coll, mat, jag=40):
    pts = [start]
    steps = 14
    for k in range(1, steps):
        t = k / steps
        p = start.lerp(end, t) + Vector(((rng.random() - 0.5) * jag, (rng.random() - 0.5) * jag, 0))
        pts.append(p)
    pts.append(end)
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.6
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for sp_pt, p in zip(sp.points, pts):
        sp_pt.co = (*p, 1)
    o = link(bpy.data.objects.new(name, cu), coll)
    cu.materials.append(mat)
    return o


def build_flash(env, coll, clouds_by_layer, rng):
    """The instant of a flash: bolts (if any) and the named layer lit from
    inside. Lives in its own collection, hidden except in the flash shot."""
    f = env.get("Flashes")
    if not f:
        return None
    col = lin(f["Color"])
    mat = emissive_mat("AT_Bolt", col, 40, 1.0)
    layer_def = env["CloudSea"][f["Layer"] - 1]
    clouds = clouds_by_layer[f["Layer"] - 1]
    lit = sorted(clouds, key=lambda c: (c["X"] - 300) ** 2 + (c["Z"] + 600) ** 2)[:3]
    for i, c in enumerate(lit):
        p = roblox_to_blender(c["X"], -layer_def["Depth"] + c["Y"], c["Z"])
        lamp = link(bpy.data.objects.new("AT_FlashLamp%d" % i, bpy.data.lights.new("AT_FlashLamp%d" % i, "POINT")), coll)
        lamp.data.color = col
        lamp.data.energy = 2.5e7 * f["Brightness"] / 2.5
        lamp.data.shadow_soft_size = 60
        lamp.location = p + Vector((0, 0, 10))
    top = (env.get("Canopy") or [{"Height": 600}])[0]["Height"]
    for i in range(f["Bolts"]):
        c = lit[i % len(lit)]
        end = roblox_to_blender(c["X"], -layer_def["Depth"] + c["Y"], c["Z"])
        start = Vector((end.x + (rng.random() - 0.5) * 300, end.y + (rng.random() - 0.5) * 300, top))
        bolt("AT_Bolt%d" % i, start, end, rng, coll, mat)
    return coll


# --------------------------------------------------------------------------
# compositor: haze, bloom, sun rays, grade
# --------------------------------------------------------------------------
def build_compositor(scene, env):
    scene.view_layers[0].use_pass_mist = True
    ng = bpy.data.node_groups.new("AT_Comp_" + scene.name, "CompositorNodeTree")
    scene.compositing_node_group = ng
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    n, l = ng.nodes, ng.links
    rl = n.new("CompositorNodeRLayers")
    rl.scene = scene
    out = n.new("NodeGroupOutput")
    atm = env.get("Atmosphere") or {"Density": 0, "Color": env["FogColor"]}

    def math_node(op, a, b):
        m = n.new("ShaderNodeMath")
        m.operation = op
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                l.new(v, m.inputs[i])
        return m.outputs[0]

    def mix(fac, a, b, blend="MIX"):
        m = n.new("ShaderNodeMix")
        m.data_type = "RGBA"
        m.blend_type = blend
        if isinstance(fac, (int, float)):
            m.inputs[0].default_value = fac
        else:
            l.new(fac, m.inputs[0])
        for sock, v in ((m.inputs[6], a), (m.inputs[7], b)):
            if isinstance(v, tuple):
                sock.default_value = (*v, 1)
            else:
                l.new(v, sock)
        return m.outputs[2]

    img = rl.outputs["Image"]
    # HAZE: geometry only (the painted sky already is the atmosphere), by
    # distance, toward the horizon colour, scaled by Density.
    mist = rl.outputs["Mist"]
    geo = math_node("LESS_THAN", mist, 0.999)
    fac = math_node("MULTIPLY", math_node("MULTIPLY", mist, geo), min(0.9, atm["Density"] * 2.2))
    img = mix(fac, img, lerp3(lin(atm["Color"]), lin(atm.get("Decay", atm["Color"])), 0.25))

    def glare(src, kind, strength, threshold=1.0, size=0.5, sun=None):
        g = n.new("CompositorNodeGlare")
        g.inputs["Type"].default_value = kind
        try:
            g.inputs["Quality"].default_value = "High"
        except Exception:
            pass
        g.inputs["Threshold"].default_value = threshold
        g.inputs["Strength"].default_value = strength
        g.inputs["Size"].default_value = size
        if sun is not None:
            g.inputs["Sun Position"].default_value = sun
        l.new(src, g.inputs["Image"])
        return g.outputs["Image"], g

    bloom = env.get("Bloom")
    if bloom:
        img, _ = glare(img, "Bloom", bloom["Intensity"] * 0.6, threshold=0.8 + (bloom["Threshold"] - 0.7),
                       size=min(1.0, bloom["Size"] / 50))
    rays_node = None
    if env.get("SunRays"):
        img, rays_node = glare(img, "Sun Beams", env["SunRays"]["Intensity"] * 2.2, threshold=0.9,
                               size=env["SunRays"]["Spread"] * 0.4, sun=(0.5, 0.5))

    grade = env.get("Grade") or {"Brightness": 0, "Contrast": 0, "Saturation": 0, "Tint": (255, 255, 255)}
    hs = n.new("CompositorNodeHueSat")
    hs.inputs["Saturation"].default_value = 1 + grade["Saturation"]
    l.new(img, hs.inputs["Image"])
    bc = n.new("CompositorNodeBrightContrast")
    bc.inputs["Brightness"].default_value = grade["Brightness"] * 100 * 0.5
    bc.inputs["Contrast"].default_value = grade["Contrast"] * 100 * 0.6
    l.new(hs.outputs[0], bc.inputs["Image"])
    tint = n.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs[0].default_value = 1
    tint.inputs[7].default_value = rgba(grade["Tint"])
    l.new(bc.outputs[0], tint.inputs[6])
    l.new(tint.outputs[2], out.inputs[0])
    return {"tint": tint, "rays": rays_node, "grade_tint": grade["Tint"]}


# --------------------------------------------------------------------------
# one scene per profile
# --------------------------------------------------------------------------
def build_scene(profile, kids):
    env = A.resolve(profile)
    name = "Atmos_" + ("Base" if profile == "base" else A.SCENARIOS[profile]["Name"].replace(" ", ""))
    scene = bpy.data.scenes.new(name)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = RES
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 88
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = env.get("ExposureCompensation", 0) * 0.6
    ee = scene.eevee
    ee.taa_render_samples = 24
    ee.use_raytracing = False
    ee.use_shadows = True
    ee.shadow_resolution_scale = 1.0
    ee.shadow_pool_size = "1024"
    scene["profile"] = profile
    scene["flavor"] = A.BASE_FLAVOR if profile == "base" else A.SCENARIOS[profile]["Flavor"]

    rng = random.Random("sky-citadel-atmosphere-" + profile)
    sun_dir, sun_el = sun_direction(env["ClockTime"])
    colls = {}
    for key in ("Map", "Light", "CloudSea", "Canopy", "Effects", "Weather", "Flash"):
        c = bpy.data.collections.new("%s_%s" % (key, name))
        scene.collection.children.link(c)
        colls[key] = c

    build_map(profile, colls["Map"], kids)
    build_world(scene, env, sun_dir, sun_el)
    build_lights(scene, env, colls["Light"], sun_dir, sun_el)
    by_layer = []
    for i, layer in enumerate(env.get("CloudSea") or [], 1):
        by_layer.append(build_cloud_layer(layer, i, colls["CloudSea"], rng, env["CloudCeiling"]))
    for i, layer in enumerate(env.get("Canopy") or [], 1):
        build_cloud_layer(layer, i, colls["Canopy"], rng, None, above=True, tag="Canopy")
    build_debris(env, colls["Effects"], rng)
    build_plumes(env, colls["Effects"], rng)
    build_aurora(env, colls["Effects"], rng)
    build_searchlights(env, colls["Effects"], rng)
    build_dome(env, colls["Effects"])
    followers = build_weather(env, colls["Weather"], rng)
    flash = build_flash(env, colls["Flash"], by_layer, rng)
    if flash:
        flash.hide_render = True
    comp = build_compositor(scene, env)

    cams = {}
    for shot, s in SHOTS.items():
        cam = link(bpy.data.objects.new("Cam_%s" % shot, bpy.data.cameras.new("Cam_%s_%s" % (shot, name))), scene.collection)
        cam.data.lens = s["lens"]
        cam.data.clip_start = 0.5
        cam.data.clip_end = 30000
        cam.location = s["eye"]
        cam.rotation_euler = (Vector(s["target"]) - Vector(s["eye"])).to_track_quat("-Z", "Y").to_euler()
        cams[shot] = cam
    scene.camera = cams["vista"]
    return scene, env, {"followers": followers, "flash": flash, "comp": comp, "cams": cams, "sun": sun_dir}


def aim_sun_rays(scene, ctx, cam):
    rays = ctx["comp"]["rays"]
    if not rays:
        return
    far = cam.location + ctx["sun"] * 10000
    p = world_to_camera_view(scene, cam, far)
    on = p.z > 0 and -0.2 <= p.x <= 1.2 and -0.2 <= p.y <= 1.2
    rays.inputs["Sun Position"].default_value = (p.x, p.y)
    rays.mute = not on


def render_scene(scene, env, ctx, profile, written):
    shots = list(SHOTS)
    extra = []
    if ctx["flash"]:
        extra.append("flash")
    if env.get("Pulse"):
        extra.append("pulse")
    for shot in shots + extra:
        cam = ctx["cams"]["vista" if shot in ("flash", "pulse") else shot]
        scene.camera = cam
        for f in ctx["followers"]:
            f.location = cam.location
        aim_sun_rays(scene, ctx, cam)
        tint = ctx["comp"]["tint"]
        base_tint = env.get("Grade", {}).get("Tint", (255, 255, 255))
        if shot == "pulse":
            p = env["Pulse"]
            peak = lerp3(base_tint, p["Tint"], p["Amount"] * 1.6)
            tint.inputs[7].default_value = rgba(tuple(int(v) for v in peak))
        else:
            tint.inputs[7].default_value = rgba(base_tint)
        if ctx["flash"]:
            ctx["flash"].hide_render = shot != "flash"
        path = os.path.join(RENDERS, "%s_%s.jpg" % (profile, shot))
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True, scene=scene.name)
        written.append(path)
        print("  rendered", os.path.basename(path))
    if ctx["flash"]:
        ctx["flash"].hide_render = True
    tint.inputs[7].default_value = rgba(env.get("Grade", {}).get("Tint", (255, 255, 255)))


def contact_sheets(written):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow not available -- no contact sheets")
        return
    for shot in SHOTS:
        files = [os.path.join(RENDERS, "%s_%s.jpg" % (p, shot)) for p in PROFILES]
        files = [f for f in files if os.path.exists(f)]
        if not files:
            continue
        ims = [Image.open(f) for f in files]
        tw, th = ims[0].size[0] // 2, ims[0].size[1] // 2
        cols = 4
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * th), "black")
        draw = ImageDraw.Draw(sheet)
        for i, (im, f) in enumerate(zip(ims, files)):
            x, y = (i % cols) * tw, (i // cols) * th
            sheet.paste(im.resize((tw, th)), (x, y))
            draw.text((x + 8, y + 6), os.path.basename(f)[:-4], fill=(255, 255, 0))
        path = os.path.join(RENDERS, "sheet_%s.jpg" % shot)
        sheet.save(path, quality=85)
        print("  sheet", path)


def main(argv):
    only = None
    if "--only" in argv:
        only = argv[argv.index("--only") + 1].split(",")
    problems = A.validate_all()
    if problems:
        raise SystemExit("atmosphere data invalid:\n  " + "\n  ".join(problems))
    A.write_luau()
    profiles = [p for p in PROFILES if not only or p in only]

    # Start clean: the factory scene is dropped once ours exist.
    first = bpy.context.scene
    kids = load_library(profiles)
    os.makedirs(RENDERS, exist_ok=True)
    built = []
    for profile in profiles:
        print("profile", profile)
        built.append((profile,) + build_scene(profile, kids))
    for obj in list(first.collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    try:
        bpy.data.scenes.remove(first)
    except RuntimeError as err:
        print("kept the factory scene:", err)

    written = []
    if "--no-render" not in argv:
        for profile, scene, env, ctx in built:
            render_scene(scene, env, ctx, profile, written)
        contact_sheets(written)
    if "--no-save" not in argv:
        if bpy.context.window:
            bpy.context.window.scene = built[0][1]
        bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, compress=True, relative_remap=True)
        print("saved", OUT_BLEND)
    return written


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(argv)
