"""Sky Citadel scenario atmospheres -- the data, one file.

Each of the seven scenario kits (build_sky_citadel_scenarios.py) changes what
is ON the citadel. This file changes the air AROUND it: the hour, the sky, the
haze, the cloud sea under the islands, and the weather moving past the camera.
A scenario should be readable from the sky before the player has looked at a
single prop -- that is half of "Fate gave me this".

It is plain data plus three helpers, and it is the single source for:
  * build_sky_citadel_atmosphere.py -- the Blender previews (one scene each)
  * assets/export/worlds/sky_citadel/scenarios/Environments_Scenarios.luau
    -- the same data as Luau, STAGED like Props_Scenarios.luau: nothing in
    src/ reads it until the scenario layer is wired (SKY_CITADEL.md).

Run it on its own to validate and write the Luau:

    python sky_citadel_atmospheres.py

HOW A PROFILE APPLIES (the rule the runtime should implement)
A profile is an OVERRIDE of the world's Environment, the same idea as the
Blueprint's ModifierOverride:
  * a scalar or Color3 key replaces the world's;
  * a block (Atmosphere, Sky, Bloom, SunRays, Grade, Motes) merges key by key;
  * a LIST (CloudSea, Canopy, Weather) replaces the world's list outright;
  * `False` removes the block (Luau `false`), e.g. Motes = False.

NEW BLOCKS -- proposed extensions to Types.Environment, read by nothing yet.
Every one is generic (any world may use it) and optional:
  Weather       directional particle streams: snow, rain, embers, pollen...
  Pulse         a slow or sharp oscillation of the grade: alarms, breathing
  Flashes       lightning: brief brightness spikes that light the cloud sea
  Canopy        cloud layers ABOVE the map (Height instead of Depth)
  Plumes        far-off columns of smoke rising from below the horizon
  Debris        fragments falling past the islands into the cloud sea
  Aurora        curtains of light high in the sky
  Searchlights  beams sweeping the sky from a ring below the citadel
  Dome          a shield bubble round the map (ForceField material)

Colours are (r, g, b) 0..255, exactly as Color3.fromRGB takes them.
"""

import copy
import os
from collections import namedtuple

# A Vector3 -- kept distinct from a colour, which is also three numbers.
Vec = namedtuple("Vec", "x y z")

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
LUAU_OUT = os.path.join(REPO, "assets", "export", "worlds", "sky_citadel", "scenarios",
                        "Environments_Scenarios.luau")

# The kit's deepest keel is 96 below the walk plane (SKY_CITADEL.md), and
# Unmooring sinks a loose islet up to 3.5 more. The crown is +160.
KEEL_DEPTH = 96
CROWN_TOP = 160

# --------------------------------------------------------------------------
# BASE -- a mirror of Content/Worlds/SkyCitadel.luau's Environment, so the
# previews can render the base kit beside the scenarios and every profile
# can be resolved and validated here. If the Luau changes, change this.
# --------------------------------------------------------------------------
BASE = {
    "AmbientColor": (118, 124, 168),
    "OutdoorAmbientColor": (150, 150, 196),
    "ColorShiftTop": (255, 196, 140),
    "ColorShiftBottom": (84, 104, 176),
    "FogColor": (236, 206, 196),
    "FogStart": 400,
    "FogEnd": 2600,
    "Brightness": 2.6,
    "ExposureCompensation": 0.15,
    "ClockTime": 6.4,
    "Atmosphere": {"Density": 0.3, "Offset": 0.12, "Color": (255, 212, 176),
                   "Decay": (96, 104, 196), "Glare": 0.7, "Haze": 1.4},
    "Sky": {"SunAngularSize": 16, "StarCount": 300},
    "Bloom": {"Intensity": 0.7, "Size": 26, "Threshold": 0.9},
    "SunRays": {"Intensity": 0.1, "Spread": 0.7},
    "Grade": {"Brightness": 0.02, "Contrast": 0.08, "Saturation": 0.06, "Tint": (255, 246, 238)},
    "CloudCeiling": 130,
    "CloudSea": [
        {"Depth": 200, "Count": 30, "Radius": 1600, "Speed": 7, "Heading": 80,
         "SizeMin": 150, "SizeMax": 340, "Thickness": 0.3, "Billows": 6, "Tufts": 3,
         "Mix": {"Cumulus": 0.8, "Stratus": 0.2},
         "Color": (255, 238, 228), "Shade": (196, 176, 206), "Transparency": 0},
        {"Depth": 330, "Count": 30, "Radius": 2200, "Speed": 4, "Heading": 95,
         "SizeMin": 240, "SizeMax": 520, "Thickness": 0.22, "Billows": 4, "Tufts": 1,
         "Mix": {"Cumulus": 0.5, "Stratus": 0.5},
         "Color": (236, 214, 226), "Shade": (150, 146, 196), "Transparency": 0},
        {"Depth": 520, "Count": 18, "Radius": 2800, "Speed": 2, "Heading": 70,
         "SizeMin": 400, "SizeMax": 800, "Thickness": 0.12, "Billows": 0,
         "Mix": {"Stratus": 1},
         "Color": (206, 196, 232), "Shade": (140, 140, 190), "Transparency": 0.1},
    ],
    "Motes": {"Rate": 6, "Lifetime": 9, "Color": (255, 236, 200), "Size": 0.35, "Speed": 3},
}

BASE_FLAVOR = "Nothing above you but sun. The clouds are somewhere below the floor."


# --------------------------------------------------------------------------
# THE SEVEN
#
# Every profile keeps three things of Sky Citadel's so the world stays the
# world: the white citadel, the cloud sea BELOW, and an hour near sunrise
# (5.5 .. 7.6). Nothing may land on another world's slot: Emberfall is an
# ash-red dusk (18:00), Astral Reach midnight, Ethereal Scape a white
# afternoon, Verdant Valley midday.
# --------------------------------------------------------------------------
SCENARIOS = {}

# UNMOORING -- anti-grav failing. The same dawn gone WRONG: drained of gold,
# a hard white sun, a sickly sage haze. The cloud sea has come up to meet the
# islands and its layers slide in OPPOSITE directions (vertigo); towering
# cumulus heave up toward the keels; pieces of the citadel fall past into it;
# grit drifts UP where gravity has let go; the light browns out.
SCENARIOS["unmooring"] = {
    "Name": "Unmooring",
    "Flavor": "Something under the floor has let go.",
    "Environment": {
        "AmbientColor": (116, 122, 134),
        "OutdoorAmbientColor": (146, 152, 162),
        "ColorShiftTop": (238, 230, 206),
        "ColorShiftBottom": (86, 100, 132),
        "Brightness": 2.3,
        "ExposureCompensation": 0.05,
        "ClockTime": 6.9,
        "Atmosphere": {"Density": 0.36, "Offset": 0.18, "Color": (212, 220, 198),
                       "Decay": (82, 94, 146), "Glare": 0.35, "Haze": 2.2},
        "Sky": {"SunAngularSize": 11, "StarCount": 120},
        "SunRays": {"Intensity": 0.05, "Spread": 0.5},
        "Grade": {"Brightness": 0, "Contrast": 0.14, "Saturation": -0.14, "Tint": (236, 244, 238)},
        # The sea has risen: the near layer is 50 studs closer and heaped high.
        "CloudCeiling": 112,
        "CloudSea": [
            {"Depth": 150, "Count": 32, "Radius": 1500, "Speed": 13, "Heading": 80,
             "SizeMin": 170, "SizeMax": 380, "Thickness": 0.36, "Billows": 8, "Tufts": 3,
             "Mix": {"Cumulus": 0.9, "Stratus": 0.1},
             "Color": (240, 238, 230), "Shade": (142, 144, 170), "Transparency": 0},
            # ...while the layer under it runs the other way.
            {"Depth": 290, "Count": 30, "Radius": 2200, "Speed": 9, "Heading": 250,
             "SizeMin": 240, "SizeMax": 520, "Thickness": 0.24, "Billows": 4, "Tufts": 1,
             "Mix": {"Cumulus": 0.5, "Stratus": 0.5},
             "Color": (214, 216, 214), "Shade": (120, 124, 156), "Transparency": 0},
            {"Depth": 480, "Count": 18, "Radius": 2800, "Speed": 5, "Heading": 120,
             "SizeMin": 400, "SizeMax": 800, "Thickness": 0.14, "Billows": 0,
             "Mix": {"Stratus": 1},
             "Color": (176, 182, 200), "Shade": (104, 110, 146), "Transparency": 0.1},
        ],
        "Motes": False,
        "Weather": [
            # Grit that has forgotten which way is down.
            {"Name": "RisingGrit", "Rate": 14, "Lifetime": 10, "Speed": 3, "Size": 0.25,
             "Color": (214, 210, 196), "Direction": Vec(0.1, 1, 0.05), "Spread": 25,
             "Streak": 0, "Emission": 0, "Transparency": 0.2, "Box": Vec(180, 80, 180)},
        ],
        "Debris": {"Rate": 2.5, "SizeMin": 3, "SizeMax": 14, "Speed": 28, "Spin": 70,
                   "Color": (206, 212, 224), "Radius": 700},
        # A brown-out, not an alarm: an irregular sag in the light.
        "Pulse": {"Period": 3.7, "Tint": (220, 226, 214), "Amount": 0.12, "Shape": "Flicker"},
    },
}

# SIEGE -- the raiders attacked at dawn. The SAME hour as the base, seen
# through smoke: a swollen orange sun, shafts cutting through the haze, an
# ochre horizon under a slate-cobalt sky (the blue overhead is what keeps it
# from being Emberfall), the near clouds stained with soot, smoke banks
# drifting just under the keels, the far districts burning in columns, and
# embers on the wind.
SCENARIOS["siege"] = {
    "Name": "Siege",
    "Flavor": "Their fires were lit before sunrise. Yours will have to wait.",
    "Environment": {
        "AmbientColor": (116, 106, 118),
        "OutdoorAmbientColor": (150, 132, 138),
        "ColorShiftTop": (255, 168, 104),
        "ColorShiftBottom": (72, 78, 124),
        "Brightness": 2.4,
        "ExposureCompensation": 0.1,
        "ClockTime": 6.4,
        "Atmosphere": {"Density": 0.42, "Offset": 0.06, "Color": (232, 166, 116),
                       "Decay": (84, 90, 134), "Glare": 1.1, "Haze": 2.6},
        "Sky": {"SunAngularSize": 21, "StarCount": 0},
        "Bloom": {"Intensity": 0.8, "Size": 28, "Threshold": 0.85},
        "SunRays": {"Intensity": 0.22, "Spread": 0.55},
        "Grade": {"Brightness": 0, "Contrast": 0.12, "Saturation": -0.04, "Tint": (255, 236, 220)},
        "CloudSea": [
            {"Depth": 200, "Count": 30, "Radius": 1600, "Speed": 7, "Heading": 80,
             "SizeMin": 150, "SizeMax": 340, "Thickness": 0.3, "Billows": 6, "Tufts": 3,
             "Mix": {"Cumulus": 0.8, "Stratus": 0.2},
             "Color": (240, 212, 190), "Shade": (132, 112, 122), "Transparency": 0},
            # SMOKE BANKS: flat, dark, fast, downwind -- low under the keels.
            {"Depth": 165, "Count": 14, "Radius": 1600, "Speed": 11, "Heading": 110,
             "SizeMin": 160, "SizeMax": 300, "Thickness": 0.16, "Billows": 1, "Tufts": 0,
             "Mix": {"Stratus": 1},
             "Color": (126, 116, 118), "Shade": (74, 68, 78), "Transparency": 0.15},
            {"Depth": 330, "Count": 30, "Radius": 2200, "Speed": 4, "Heading": 95,
             "SizeMin": 240, "SizeMax": 520, "Thickness": 0.22, "Billows": 4, "Tufts": 1,
             "Mix": {"Cumulus": 0.5, "Stratus": 0.5},
             "Color": (224, 190, 184), "Shade": (126, 116, 146), "Transparency": 0},
            {"Depth": 520, "Count": 18, "Radius": 2800, "Speed": 2, "Heading": 70,
             "SizeMin": 400, "SizeMax": 800, "Thickness": 0.12, "Billows": 0,
             "Mix": {"Stratus": 1},
             "Color": (190, 170, 190), "Shade": (120, 110, 150), "Transparency": 0.1},
        ],
        "Motes": False,
        "Weather": [
            {"Name": "Embers", "Rate": 16, "Lifetime": 7, "Speed": 6, "Size": 0.3,
             "Color": (255, 150, 70), "Direction": Vec(0.55, 0.8, 0.2), "Spread": 30,
             "Streak": 0, "Emission": 1, "Transparency": 0, "Box": Vec(160, 60, 160)},
            {"Name": "Ash", "Rate": 10, "Lifetime": 12, "Speed": 2.5, "Size": 0.4,
             "Color": (120, 114, 116), "Direction": Vec(0.6, -0.5, 0.2), "Spread": 40,
             "Streak": 0, "Emission": 0, "Transparency": 0.25, "Box": Vec(180, 80, 180)},
        ],
        # The rest of the citadel is burning, out past the edge of the map.
        "Plumes": {"Count": 5, "DistanceMin": 1300, "DistanceMax": 2300, "Height": 900,
                   "Width": 150, "Color": (92, 86, 92), "Shade": (54, 50, 58),
                   "Glow": (255, 132, 60), "Lean": 14, "Heading": 110, "Rise": 8},
    },
}

# LOCKDOWN -- the citadel has decided you are the intruder. The only profile
# BEFORE sunrise (5.5): a deep blue hour with the stars still out and a thin
# mauve glow on the horizon, so every alarm-red light on the props owns the
# frame. A red aegis dome shimmers over the whole map, searchlights sweep up
# from beneath the islands, the cloud sea below is lit red from its
# underside, and the whole grade pulses with the alarm.
SCENARIOS["lockdown"] = {
    "Name": "Lockdown",
    "Flavor": "The citadel has decided you are the intruder.",
    "Environment": {
        "AmbientColor": (72, 78, 112),
        "OutdoorAmbientColor": (92, 100, 146),
        "ColorShiftTop": (150, 170, 224),
        "ColorShiftBottom": (46, 52, 102),
        "Brightness": 1.3,
        "ExposureCompensation": 0.3,
        "ClockTime": 5.5,
        "Atmosphere": {"Density": 0.34, "Offset": 0.2, "Color": (132, 108, 150),
                       "Decay": (30, 40, 96), "Glare": 0.1, "Haze": 1.0},
        "Sky": {"SunAngularSize": 12, "StarCount": 1600},
        "Bloom": {"Intensity": 1.1, "Size": 30, "Threshold": 0.75},
        "SunRays": False,
        "Grade": {"Brightness": 0, "Contrast": 0.14, "Saturation": -0.1, "Tint": (236, 238, 255)},
        "CloudSea": [
            {"Depth": 200, "Count": 30, "Radius": 1600, "Speed": 5, "Heading": 80,
             "SizeMin": 150, "SizeMax": 340, "Thickness": 0.3, "Billows": 6, "Tufts": 3,
             "Mix": {"Cumulus": 0.8, "Stratus": 0.2},
             # Tops catch the blue hour; undersides catch the alarms.
             "Color": (122, 132, 176), "Shade": (120, 50, 76), "Transparency": 0},
            {"Depth": 330, "Count": 30, "Radius": 2200, "Speed": 3, "Heading": 95,
             "SizeMin": 240, "SizeMax": 520, "Thickness": 0.22, "Billows": 4, "Tufts": 1,
             "Mix": {"Cumulus": 0.5, "Stratus": 0.5},
             "Color": (92, 100, 150), "Shade": (70, 42, 80), "Transparency": 0},
            {"Depth": 520, "Count": 18, "Radius": 2800, "Speed": 1.5, "Heading": 70,
             "SizeMin": 400, "SizeMax": 800, "Thickness": 0.12, "Billows": 0,
             "Mix": {"Stratus": 1},
             "Color": (64, 70, 120), "Shade": (46, 44, 90), "Transparency": 0.1},
        ],
        "Motes": False,
        "Pulse": {"Period": 2.4, "Tint": (255, 110, 110), "Amount": 0.3, "Shape": "Beat"},
        "Dome": {"Radius": 1100, "Color": (255, 64, 76), "Transparency": 0.86,
                 "Material": "ForceField"},
        "Searchlights": {"Count": 6, "Radius": 620, "Color": (255, 96, 104), "Length": 1500,
                         "Width": 22, "Sweep": 14, "Tilt": 24},
    },
}

# STORMHAWK -- it hunts in its own weather. Sunrise has been swallowed: a
# thunderhead ROOF overhead (the only profile with a canopy), shafts of light
# through its gaps, a steel-grey haze, a churning cloud sea lit from within by
# lightning, and wind-driven rain streaking sideways across the decks.
SCENARIOS["stormhawk"] = {
    "Name": "Stormhawk",
    "Flavor": "It hunts in its own weather.",
    "Environment": {
        "AmbientColor": (98, 106, 130),
        "OutdoorAmbientColor": (116, 126, 152),
        "ColorShiftTop": (196, 204, 222),
        "ColorShiftBottom": (62, 72, 104),
        "Brightness": 1.7,
        "ExposureCompensation": 0.2,
        "ClockTime": 6.4,
        "Atmosphere": {"Density": 0.48, "Offset": 0.0, "Color": (150, 158, 178),
                       "Decay": (58, 64, 94), "Glare": 0.2, "Haze": 3.0},
        "Sky": {"SunAngularSize": 10, "StarCount": 0},
        "Bloom": {"Intensity": 0.6, "Size": 24, "Threshold": 0.9},
        "SunRays": {"Intensity": 0.26, "Spread": 0.4},
        "Grade": {"Brightness": -0.02, "Contrast": 0.16, "Saturation": -0.18, "Tint": (230, 238, 255)},
        "CloudSea": [
            {"Depth": 200, "Count": 32, "Radius": 1600, "Speed": 16, "Heading": 60,
             "SizeMin": 170, "SizeMax": 360, "Thickness": 0.34, "Billows": 7, "Tufts": 3,
             "Mix": {"Cumulus": 0.85, "Stratus": 0.15},
             "Color": (196, 202, 216), "Shade": (88, 94, 122), "Transparency": 0},
            {"Depth": 330, "Count": 30, "Radius": 2200, "Speed": 10, "Heading": 75,
             "SizeMin": 240, "SizeMax": 520, "Thickness": 0.24, "Billows": 4, "Tufts": 1,
             "Mix": {"Cumulus": 0.5, "Stratus": 0.5},
             "Color": (150, 158, 180), "Shade": (74, 80, 110), "Transparency": 0},
            {"Depth": 520, "Count": 18, "Radius": 2800, "Speed": 5, "Heading": 70,
             "SizeMin": 400, "SizeMax": 800, "Thickness": 0.12, "Billows": 0,
             "Mix": {"Stratus": 1},
             "Color": (112, 120, 150), "Shade": (70, 76, 106), "Transparency": 0.1},
        ],
        # The storm's roof, well clear of the +160 crown.
        "Canopy": [
            {"Height": 520, "Count": 16, "Radius": 2000, "Speed": 9, "Heading": 60,
             "SizeMin": 420, "SizeMax": 760, "Thickness": 0.18, "Billows": 3, "Tufts": 0,
             "Mix": {"Cumulus": 0.3, "Stratus": 0.7},
             "Color": (132, 138, 160), "Shade": (56, 60, 80), "Transparency": 0},
        ],
        "Motes": False,
        "Weather": [
            {"Name": "Rain", "Rate": 120, "Lifetime": 1.6, "Speed": 90, "Size": 0.12,
             "Color": (200, 212, 232), "Direction": Vec(0.55, -1, 0.2), "Spread": 4,
             "Streak": 14, "Emission": 0, "Transparency": 0.55, "Box": Vec(160, 70, 160)},
        ],
        "Flashes": {"IntervalMin": 4, "IntervalMax": 11, "Duration": 0.18,
                    "Color": (210, 222, 255), "Brightness": 2.5, "Bolts": 2, "Layer": 1},
    },
}

# RIME -- frozen at altitude. Crisp, still and blinding: a pale white sun
# wearing a halo, cyan in every shadow, an ice-pale horizon, strong glare and
# bloom off the snow. The cloud sea has frozen into flat banks with Roblox's
# Snow finish and barely moves; snow falls on the per-piece wind and diamond
# dust glitters in the air. Clear rather than hazy is what keeps it from being
# Ethereal Scape's white afternoon: the colour is cold, the hour is early.
SCENARIOS["rime"] = {
    "Name": "Rime",
    "Flavor": "The air has stopped moving. So has everything it touched.",
    "Environment": {
        "AmbientColor": (150, 168, 204),
        "OutdoorAmbientColor": (170, 194, 232),
        "ColorShiftTop": (242, 238, 255),
        "ColorShiftBottom": (108, 150, 214),
        "Brightness": 3.0,
        "ExposureCompensation": 0.0,
        "ClockTime": 7.0,
        "Atmosphere": {"Density": 0.33, "Offset": 0.25, "Color": (214, 232, 248),
                       "Decay": (104, 146, 212), "Glare": 1.6, "Haze": 0.9},
        "Sky": {"SunAngularSize": 24, "StarCount": 60},
        "Bloom": {"Intensity": 0.9, "Size": 32, "Threshold": 0.82},
        "SunRays": {"Intensity": 0.14, "Spread": 0.5},
        "Grade": {"Brightness": 0.03, "Contrast": 0.1, "Saturation": -0.2, "Tint": (232, 244, 255)},
        "CloudSea": [
            {"Depth": 200, "Count": 28, "Radius": 1600, "Speed": 2, "Heading": 80,
             "SizeMin": 170, "SizeMax": 360, "Thickness": 0.22, "Billows": 3, "Tufts": 1,
             "Mix": {"Cumulus": 0.4, "Stratus": 0.6}, "Material": "Snow",
             "Color": (246, 250, 255), "Shade": (160, 186, 222), "Transparency": 0},
            {"Depth": 330, "Count": 30, "Radius": 2200, "Speed": 1, "Heading": 95,
             "SizeMin": 260, "SizeMax": 540, "Thickness": 0.16, "Billows": 2, "Tufts": 0,
             "Mix": {"Cumulus": 0.2, "Stratus": 0.8}, "Material": "Snow",
             "Color": (222, 236, 252), "Shade": (140, 168, 214), "Transparency": 0},
            {"Depth": 520, "Count": 18, "Radius": 2800, "Speed": 0.5, "Heading": 70,
             "SizeMin": 400, "SizeMax": 800, "Thickness": 0.1, "Billows": 0,
             "Mix": {"Stratus": 1},
             "Color": (192, 212, 240), "Shade": (132, 158, 204), "Transparency": 0.1},
        ],
        # Diamond dust: tiny, bright, and slow.
        "Motes": {"Rate": 14, "Lifetime": 8, "Color": (232, 248, 255), "Size": 0.2, "Speed": 1},
        "Weather": [
            {"Name": "Snow", "Rate": 40, "Lifetime": 14, "Speed": 7, "Size": 0.5,
             "Color": (248, 250, 255), "Direction": Vec(0.35, -1, 0.1), "Spread": 20,
             "Streak": 0, "Emission": 0, "Transparency": 0.05, "Box": Vec(180, 90, 180)},
        ],
    },
}

# RECLAIMED -- nobody has come up here in a long time. A later, softer,
# humid morning (7.6): warm gold light, teal-green shadows, a milky
# gold-green haze, god rays, a faded grade. The cloud sea is close and soft
# (mist rising off it), and pollen and seed-fluff hang in the air. Dead
# lights mean less bloom. Verdant Valley is a clear midday; this is its
# opposite -- hazy, low, quiet.
SCENARIOS["reclaimed"] = {
    "Name": "Reclaimed",
    "Flavor": "Nobody has come up here in a long time. Something else has.",
    "Environment": {
        "AmbientColor": (118, 134, 122),
        "OutdoorAmbientColor": (150, 172, 152),
        "ColorShiftTop": (255, 222, 160),
        "ColorShiftBottom": (68, 110, 112),
        "Brightness": 2.4,
        "ExposureCompensation": 0.1,
        "ClockTime": 7.6,
        "Atmosphere": {"Density": 0.34, "Offset": 0.3, "Color": (238, 232, 198),
                       "Decay": (100, 142, 172), "Glare": 0.5, "Haze": 3.2},
        "Sky": {"SunAngularSize": 18, "StarCount": 0},
        "Bloom": {"Intensity": 0.45, "Size": 24, "Threshold": 0.95},
        "SunRays": {"Intensity": 0.22, "Spread": 0.9},
        "Grade": {"Brightness": 0.01, "Contrast": -0.02, "Saturation": -0.08, "Tint": (246, 255, 236)},
        "CloudCeiling": 125,
        "CloudSea": [
            {"Depth": 180, "Count": 30, "Radius": 1600, "Speed": 3, "Heading": 80,
             "SizeMin": 170, "SizeMax": 360, "Thickness": 0.26, "Billows": 5, "Tufts": 2,
             "Mix": {"Cumulus": 0.6, "Stratus": 0.4},
             "Color": (255, 250, 236), "Shade": (184, 190, 196), "Transparency": 0},
            {"Depth": 310, "Count": 30, "Radius": 2200, "Speed": 2, "Heading": 95,
             "SizeMin": 240, "SizeMax": 520, "Thickness": 0.2, "Billows": 3, "Tufts": 1,
             "Mix": {"Cumulus": 0.4, "Stratus": 0.6},
             "Color": (238, 238, 226), "Shade": (160, 172, 186), "Transparency": 0},
            {"Depth": 500, "Count": 18, "Radius": 2800, "Speed": 1, "Heading": 70,
             "SizeMin": 400, "SizeMax": 800, "Thickness": 0.12, "Billows": 0,
             "Mix": {"Stratus": 1},
             "Color": (212, 218, 216), "Shade": (150, 164, 180), "Transparency": 0.1},
        ],
        "Motes": {"Rate": 16, "Lifetime": 14, "Color": (255, 248, 214), "Size": 0.45, "Speed": 1.5},
        "Weather": [
            # A few petals and seeds drifting off the overgrowth.
            {"Name": "Petals", "Rate": 5, "Lifetime": 12, "Speed": 3, "Size": 0.6,
             "Color": (246, 206, 222), "Direction": Vec(0.35, -0.35, 0.2), "Spread": 35,
             "Streak": 0, "Emission": 0, "Transparency": 0, "Box": Vec(160, 60, 160)},
        ],
    },
}

# AETHER SURGE -- the crystals are singing; the sky sings back. A dawn gone
# violet (6.2, the sun ON the horizon): magenta horizon, indigo overhead with
# the stars showing through, aurora curtains high in the sky, the cloud sea
# glowing violet from underneath and flickering with discharge, sparks
# rising, and the whole grade breathing slowly with the crystals.
SCENARIOS["aether_surge"] = {
    "Name": "Aether Surge",
    "Flavor": "The crystals are singing. The sky is singing back.",
    "Environment": {
        "AmbientColor": (122, 102, 172),
        "OutdoorAmbientColor": (150, 122, 202),
        "ColorShiftTop": (236, 172, 255),
        "ColorShiftBottom": (72, 60, 162),
        "Brightness": 2.2,
        "ExposureCompensation": 0.15,
        "ClockTime": 6.2,
        "Atmosphere": {"Density": 0.34, "Offset": 0.1, "Color": (232, 160, 228),
                       "Decay": (72, 50, 162), "Glare": 1.0, "Haze": 1.6},
        "Sky": {"SunAngularSize": 14, "StarCount": 900},
        "Bloom": {"Intensity": 1.2, "Size": 34, "Threshold": 0.7},
        "SunRays": {"Intensity": 0.08, "Spread": 0.7},
        "Grade": {"Brightness": 0.01, "Contrast": 0.1, "Saturation": 0.12, "Tint": (246, 236, 255)},
        "CloudSea": [
            {"Depth": 200, "Count": 30, "Radius": 1600, "Speed": 6, "Heading": 80,
             "SizeMin": 150, "SizeMax": 340, "Thickness": 0.3, "Billows": 6, "Tufts": 3,
             "Mix": {"Cumulus": 0.8, "Stratus": 0.2},
             "Color": (246, 228, 255), "Shade": (168, 116, 232), "Transparency": 0},
            {"Depth": 330, "Count": 30, "Radius": 2200, "Speed": 4, "Heading": 95,
             "SizeMin": 240, "SizeMax": 520, "Thickness": 0.22, "Billows": 4, "Tufts": 1,
             "Mix": {"Cumulus": 0.5, "Stratus": 0.5},
             "Color": (214, 184, 246), "Shade": (126, 88, 210), "Transparency": 0},
            {"Depth": 520, "Count": 18, "Radius": 2800, "Speed": 2, "Heading": 70,
             "SizeMin": 400, "SizeMax": 800, "Thickness": 0.12, "Billows": 0,
             "Mix": {"Stratus": 1},
             "Color": (160, 130, 222), "Shade": (96, 70, 176), "Transparency": 0.1},
        ],
        "Motes": False,
        "Weather": [
            {"Name": "AetherSparks", "Rate": 20, "Lifetime": 8, "Speed": 5, "Size": 0.35,
             "Color": (206, 164, 255), "Direction": Vec(0, 1, 0), "Spread": 20,
             "Streak": 2, "Emission": 1, "Transparency": 0, "Box": Vec(170, 70, 170)},
        ],
        "Aurora": {"Count": 3, "Height": 420, "Length": 1900, "Drop": 240,
                   "Color": (168, 118, 255), "Tip": (110, 236, 255), "Transparency": 0.5,
                   "Speed": 0.2, "Waves": 3},
        # Discharge in the sea: glow only, no bolts.
        "Flashes": {"IntervalMin": 6, "IntervalMax": 14, "Duration": 0.35,
                    "Color": (190, 140, 255), "Brightness": 0.8, "Bolts": 0, "Layer": 1},
        "Pulse": {"Period": 6, "Tint": (206, 168, 255), "Amount": 0.16, "Shape": "Sine"},
    },
}

ORDER = ["unmooring", "siege", "lockdown", "stormhawk", "rime", "reclaimed", "aether_surge"]
assert sorted(ORDER) == sorted(SCENARIOS), "ORDER must list every scenario"

MERGED_BLOCKS = ("Atmosphere", "Sky", "Bloom", "SunRays", "Grade", "Motes")


def resolve(name):
    """The Environment a scenario actually runs with: BASE with the profile
    applied by the override rule in this module's docstring. 'base' -> BASE."""
    env = copy.deepcopy(BASE)
    if name == "base":
        return env
    for key, value in SCENARIOS[name]["Environment"].items():
        if value is False:
            env.pop(key, None)
        elif key in MERGED_BLOCKS and isinstance(value, dict) and isinstance(env.get(key), dict):
            env[key].update(copy.deepcopy(value))
        else:
            env[key] = copy.deepcopy(value)
    return env


# --------------------------------------------------------------------------
# VALIDATION -- AmbienceCore.validate, ported line for line, plus the new
# blocks. A profile that fails here would fail on a player's device.
# --------------------------------------------------------------------------
def _num(errors, label, value, lo, hi):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < lo or value > hi:
        errors.append("%s must be a number in %s..%s (got %r)" % (label, lo, hi, value))


def _color(errors, label, value):
    if isinstance(value, Vec) or not (isinstance(value, tuple) and len(value) == 3 and all(isinstance(c, int) and 0 <= c <= 255 for c in value)):
        errors.append("%s must be an (r, g, b) colour 0..255 (got %r)" % (label, value))


CLOUD_MATERIALS = {"SmoothPlastic", "Plastic", "Sand", "Fabric", "Snow"}


def _cloud_layer(errors, l, layer, vertical_key, lo, hi):
    _num(errors, l + "." + vertical_key, layer.get(vertical_key), lo, hi)
    _num(errors, l + ".Count", layer.get("Count"), 1, 400)
    _num(errors, l + ".Radius", layer.get("Radius"), 64, 10000)
    _num(errors, l + ".Speed", layer.get("Speed"), 0, 200)
    _num(errors, l + ".SizeMin", layer.get("SizeMin"), 1, 2000)
    _num(errors, l + ".SizeMax", layer.get("SizeMax"), 1, 2000)
    _num(errors, l + ".Thickness", layer.get("Thickness"), 0.01, 1)
    _num(errors, l + ".Transparency", layer.get("Transparency"), 0, 1)
    if "Billows" in layer:
        _num(errors, l + ".Billows", layer["Billows"], 0, 12)
    if "Tufts" in layer:
        _num(errors, l + ".Tufts", layer["Tufts"], 0, 6)
    if "Material" in layer and layer["Material"] not in CLOUD_MATERIALS:
        errors.append("%s.Material %r is not an allowed cloud material" % (l, layer["Material"]))
    mix = layer.get("Mix")
    if mix is not None:
        for k in mix:
            if k not in ("Cumulus", "Stratus", "Wisp"):
                errors.append("%s.Mix: unknown cloud kind %r" % (l, k))
        if sum(v for v in mix.values() if isinstance(v, (int, float))) <= 0:
            errors.append("%s.Mix must give at least one kind a positive weight" % l)
    if isinstance(layer.get("SizeMin"), (int, float)) and isinstance(layer.get("SizeMax"), (int, float)) \
            and layer["SizeMin"] > layer["SizeMax"]:
        errors.append("%s: SizeMin is larger than SizeMax" % l)
    _color(errors, l + ".Color", layer.get("Color"))
    if "Shade" in layer:
        _color(errors, l + ".Shade", layer["Shade"])


def validate(env, label):
    errors = []
    a = env.get("Atmosphere")
    if a is not None:
        _num(errors, label + ".Atmosphere.Density", a.get("Density"), 0, 1)
        _num(errors, label + ".Atmosphere.Haze", a.get("Haze"), 0, 10)
        _num(errors, label + ".Atmosphere.Glare", a.get("Glare"), 0, 10)
    _num(errors, label + ".ClockTime", env.get("ClockTime"), 0, 24)

    sea = env.get("CloudSea")
    if sea is not None:
        _num(errors, label + ".CloudCeiling", env.get("CloudCeiling"), 0, 5000)
        # Sky Citadel's own rule: the ceiling must clear the deepest keel.
        if isinstance(env.get("CloudCeiling"), (int, float)) and env["CloudCeiling"] < KEEL_DEPTH + 12:
            errors.append("%s.CloudCeiling %s is within 12 studs of the keels (%s)"
                          % (label, env["CloudCeiling"], KEEL_DEPTH))
        if not sea:
            errors.append(label + ".CloudSea must be a non-empty list of layers")
        for i, layer in enumerate(sea, 1):
            l = "%s.CloudSea[%d]" % (label, i)
            _cloud_layer(errors, l, layer, "Depth", 1, 5000)
            if isinstance(layer.get("Depth"), (int, float)) and isinstance(env.get("CloudCeiling"), (int, float)) \
                    and layer["Depth"] <= env["CloudCeiling"]:
                errors.append("%s.Depth must be below CloudCeiling (%s)" % (l, env["CloudCeiling"]))

    m = env.get("Motes")
    if m is not None:
        _num(errors, label + ".Motes.Rate", m.get("Rate"), 0, 200)
        _num(errors, label + ".Motes.Lifetime", m.get("Lifetime"), 0.1, 60)

    # ---- proposed blocks ----
    for i, layer in enumerate(env.get("Canopy") or [], 1):
        l = "%s.Canopy[%d]" % (label, i)
        _cloud_layer(errors, l, layer, "Height", CROWN_TOP + 100, 5000)

    for i, w in enumerate(env.get("Weather") or [], 1):
        l = "%s.Weather[%d]" % (label, i)
        _num(errors, l + ".Rate", w.get("Rate"), 0, 400)
        _num(errors, l + ".Lifetime", w.get("Lifetime"), 0.1, 60)
        _num(errors, l + ".Speed", w.get("Speed"), 0, 300)
        _num(errors, l + ".Size", w.get("Size"), 0.05, 20)
        _num(errors, l + ".Spread", w.get("Spread"), 0, 180)
        _num(errors, l + ".Streak", w.get("Streak"), 0, 20)
        _num(errors, l + ".Emission", w.get("Emission"), 0, 1)
        _num(errors, l + ".Transparency", w.get("Transparency"), 0, 1)
        _color(errors, l + ".Color", w.get("Color"))
        d = w.get("Direction")
        if not (isinstance(d, tuple) and len(d) == 3 and any(abs(c) > 0 for c in d)):
            errors.append("%s.Direction must be a non-zero (x, y, z)" % l)
        b = w.get("Box")
        if not (isinstance(b, tuple) and len(b) == 3 and all(8 <= c <= 600 for c in b)):
            errors.append("%s.Box must be (x, y, z), each 8..600" % l)

    p = env.get("Pulse")
    if p is not None:
        _num(errors, label + ".Pulse.Period", p.get("Period"), 0.2, 60)
        _num(errors, label + ".Pulse.Amount", p.get("Amount"), 0, 1)
        _color(errors, label + ".Pulse.Tint", p.get("Tint"))
        if p.get("Shape") not in ("Sine", "Beat", "Flicker"):
            errors.append("%s.Pulse.Shape must be Sine, Beat or Flicker" % label)

    f = env.get("Flashes")
    if f is not None:
        _num(errors, label + ".Flashes.IntervalMin", f.get("IntervalMin"), 0.5, 120)
        _num(errors, label + ".Flashes.IntervalMax", f.get("IntervalMax"), 0.5, 120)
        _num(errors, label + ".Flashes.Duration", f.get("Duration"), 0.02, 2)
        _num(errors, label + ".Flashes.Brightness", f.get("Brightness"), 0, 10)
        _num(errors, label + ".Flashes.Bolts", f.get("Bolts"), 0, 4)
        _color(errors, label + ".Flashes.Color", f.get("Color"))
        if (f.get("IntervalMin") or 0) > (f.get("IntervalMax") or 0):
            errors.append(label + ".Flashes: IntervalMin is larger than IntervalMax")
        n = len(env.get("CloudSea") or [])
        if not (isinstance(f.get("Layer"), int) and 1 <= f["Layer"] <= max(n, 1)):
            errors.append("%s.Flashes.Layer must name one of the %d CloudSea layers" % (label, n))

    pl = env.get("Plumes")
    if pl is not None:
        _num(errors, label + ".Plumes.Count", pl.get("Count"), 1, 16)
        _num(errors, label + ".Plumes.DistanceMin", pl.get("DistanceMin"), 400, 8000)
        _num(errors, label + ".Plumes.DistanceMax", pl.get("DistanceMax"), 400, 8000)
        _num(errors, label + ".Plumes.Height", pl.get("Height"), 50, 3000)
        _num(errors, label + ".Plumes.Width", pl.get("Width"), 10, 800)
        _num(errors, label + ".Plumes.Lean", pl.get("Lean"), 0, 60)
        for k in ("Color", "Shade", "Glow"):
            _color(errors, label + ".Plumes." + k, pl.get(k))

    d = env.get("Debris")
    if d is not None:
        _num(errors, label + ".Debris.Rate", d.get("Rate"), 0, 20)
        _num(errors, label + ".Debris.SizeMin", d.get("SizeMin"), 0.5, 60)
        _num(errors, label + ".Debris.SizeMax", d.get("SizeMax"), 0.5, 60)
        _num(errors, label + ".Debris.Speed", d.get("Speed"), 1, 300)
        _num(errors, label + ".Debris.Radius", d.get("Radius"), 100, 4000)
        _color(errors, label + ".Debris.Color", d.get("Color"))

    au = env.get("Aurora")
    if au is not None:
        _num(errors, label + ".Aurora.Count", au.get("Count"), 1, 6)
        _num(errors, label + ".Aurora.Height", au.get("Height"), CROWN_TOP + 100, 5000)
        _num(errors, label + ".Aurora.Length", au.get("Length"), 100, 8000)
        _num(errors, label + ".Aurora.Drop", au.get("Drop"), 10, 2000)
        _num(errors, label + ".Aurora.Transparency", au.get("Transparency"), 0, 1)
        _color(errors, label + ".Aurora.Color", au.get("Color"))
        _color(errors, label + ".Aurora.Tip", au.get("Tip"))

    s = env.get("Searchlights")
    if s is not None:
        _num(errors, label + ".Searchlights.Count", s.get("Count"), 1, 12)
        _num(errors, label + ".Searchlights.Radius", s.get("Radius"), 200, 4000)
        _num(errors, label + ".Searchlights.Length", s.get("Length"), 100, 6000)
        _num(errors, label + ".Searchlights.Width", s.get("Width"), 2, 200)
        _num(errors, label + ".Searchlights.Tilt", s.get("Tilt"), 0, 80)
        _color(errors, label + ".Searchlights.Color", s.get("Color"))

    dm = env.get("Dome")
    if dm is not None:
        # The map is 3-9 pieces of 256; the dome must hold it and sit inside
        # the near cloud layer's reach.
        _num(errors, label + ".Dome.Radius", dm.get("Radius"), 600, 5000)
        _num(errors, label + ".Dome.Transparency", dm.get("Transparency"), 0.5, 1)
        _color(errors, label + ".Dome.Color", dm.get("Color"))
        if dm.get("Material") not in ("ForceField", "Neon", "Glass"):
            errors.append(label + ".Dome.Material must be ForceField, Neon or Glass")
    return errors


def validate_all():
    errors = validate(resolve("base"), "SKY_CITADEL")
    for name in ORDER:
        errors += validate(resolve(name), "SKY_CITADEL/" + name)
        for key in SCENARIOS[name]["Environment"]:
            if key not in BASE and key not in ("Weather", "Pulse", "Flashes", "Canopy", "Plumes",
                                               "Debris", "Aurora", "Searchlights", "Dome"):
                errors.append("%s: unknown Environment key %r" % (name, key))
    return errors


# --------------------------------------------------------------------------
# LUAU -- the profiles (overrides, not resolved) as a staged content table.
# --------------------------------------------------------------------------
def _lua(value, indent):
    pad = "\t" * indent
    if value is False:
        return "false"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value) if isinstance(value, float) else str(value)
    if isinstance(value, str):
        return '"%s"' % value.replace('"', '\\"')
    if isinstance(value, Vec):
        return "Vector3.new(%s, %s, %s)" % tuple(value)
    if isinstance(value, tuple) and len(value) == 3:
        return "Color3.fromRGB(%d, %d, %d)" % value
    if isinstance(value, list):
        inner = "".join("%s\t%s,\n" % (pad, _lua(v, indent + 1)) for v in value)
        return "{\n%s%s}" % (inner, pad)
    if isinstance(value, dict):
        inner = "".join("%s\t%s = %s,\n" % (pad, k, _lua(v, indent + 1)) for k, v in value.items())
        return "{\n%s%s}" % (inner, pad)
    raise TypeError(value)


def to_luau():
    out = [
        "--!strict",
        "-- GENERATED by assets/source/worlds/sky_citadel/sky_citadel_atmospheres.py.",
        "-- Do not edit by hand: change the Python and re-run it.",
        "--",
        "-- STAGED, NOT IN src/. The seven Sky Citadel scenario atmospheres, each an",
        "-- OVERRIDE of Worlds/SkyCitadel.luau's Environment: scalars and colours",
        "-- replace, blocks (Atmosphere, Sky, Bloom, SunRays, Grade, Motes) merge key",
        "-- by key, lists (CloudSea, Canopy, Weather) replace whole, and `false`",
        "-- removes a block. Weather, Pulse, Flashes, Canopy, Plumes, Debris, Aurora,",
        "-- Searchlights and Dome are PROPOSED Environment blocks that no System reads",
        "-- yet -- see docs/biomes/SKY_CITADEL.md, Scenario atmospheres.",
        "return {",
    ]
    for name in ORDER:
        s = SCENARIOS[name]
        out.append("\t%s = %s," % (name.upper(), _lua({"Name": s["Name"], "Flavor": s["Flavor"],
                                                        "Environment": s["Environment"]}, 1)))
    out.append("}")
    return "\n".join(out) + "\n"


def write_luau(path=LUAU_OUT):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(to_luau())
    return path


if __name__ == "__main__":
    problems = validate_all()
    if problems:
        raise SystemExit("INVALID:\n  " + "\n  ".join(problems))
    print("7 scenario atmospheres valid; wrote", write_luau())
