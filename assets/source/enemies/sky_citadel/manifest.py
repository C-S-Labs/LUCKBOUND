# Sky Citadel enemy manifest: the ONE place that lists this biome's enemies for the framework runner.
# Copy this file for a new biome and fill in its roster; nothing else in _framework needs to change.
#   tier:  basic | miniboss | boss        (drives validation + detail expectations, see docs/ENEMY_FRAMEWORK.md)
#   body:  humanoid (R15 names, humanoid.py) | creature (custom bones)
#   role:  combat archetype id (shared Studio behaviour, see docs/ENEMY_FRAMEWORK.md "Archetypes")
#   extras: extra build scripts run after the body (unique boss weapon, etc.)
WORLD = "sky_citadel"
PALETTE = "graphite plate, violet trim, pale stone inlay, cyan aether glow"
ENEMIES = {
    # ---- basic (10) ----
    "gilded_sentinel":  {"script": "gilded_sentinel_basic.py", "tier": "basic", "body": "humanoid", "role": "melee_guard"},
    "aviary_harrier":   {"script": "aviary_harrier.py",   "tier": "basic", "body": "creature", "role": "diver"},
    "lantern_wisp":     {"script": "lantern_wisp.py",     "tier": "basic", "body": "creature", "role": "hover_melee"},
    "cloud_skirmisher": {"script": "cloud_skirmisher.py", "tier": "basic", "body": "humanoid", "role": "ranged_thrower"},
    "turbine_drone":    {"script": "turbine_drone.py",    "tier": "basic", "body": "creature", "role": "hover_ranged"},
    "prism_crawler":    {"script": "prism_crawler.py",    "tier": "basic", "body": "creature", "role": "swarm"},
    "archive_scribe":   {"script": "archive_scribe.py",   "tier": "basic", "body": "humanoid", "role": "caster"},
    "rootbound_warden": {"script": "rootbound_warden.py", "tier": "basic", "body": "humanoid", "role": "brute"},
    "spring_eel":       {"script": "spring_eel.py",       "tier": "basic", "body": "creature", "role": "ambusher", "sunk": True},
    "skyport_hauler":   {"script": "skyport_hauler.py",   "tier": "basic", "body": "humanoid", "role": "brute"},
    # ---- minibosses (3) ----
    "armory_warden":    {"script": "armory_warden.py",    "tier": "miniboss", "body": "humanoid", "role": "miniboss"},
    "orrery_engine":    {"script": "orrery_engine.py",    "tier": "miniboss", "body": "creature", "role": "miniboss"},
    "beacon_keeper":    {"script": "beacon_keeper.py",    "tier": "miniboss", "body": "humanoid", "role": "miniboss"},
    # ---- bosses (3) ----
    "spire_regent":     {"script": "spire_regent.py",     "tier": "boss", "body": "humanoid", "role": "boss"},
    "gale_leviathan":   {"script": "gale_leviathan.py",   "tier": "boss", "body": "creature", "role": "boss"},
    "winged_sentinel":  {"script": "winged_sentinel.py",  "tier": "boss", "body": "humanoid", "role": "boss",
                         "extras": ["ws_lance.py"], "moveset": "WS_MOVESET.md"},
}
