# Ethereal Scape enemy manifest: the ONE place that lists this biome's enemies for the framework runner.
#   tier:  basic | miniboss | boss        (drives validation + detail expectations, see docs/ENEMY_FRAMEWORK.md)
#   body:  joint profile -> _framework/bodies/<body>.py (or <biome>/bodies/<body>.py):
#          humanoid (R15 elbows/knees/grips) | creature (no joint rules) | any custom profile (e.g. "finned")
#   role:  combat archetype id (shared Studio behaviour, see docs/ENEMY_FRAMEWORK.md "Archetypes")
#   extras: extra build scripts run after the body (unique boss weapon, etc.)
WORLD = "ethereal_scape"
PALETTE = "mint grass, gold soil/path, cloud white, cloudstone, teal/indigo leaves, temple ivory/gold, sky crystal, portal glow"
ENEMIES = {
    # ---- basic (5) ----
    "aether_wisp":       {"script": "aether_wisp.py",       "tier": "basic", "body": "creature", "role": "hover_melee"},
    "temple_acolyte":    {"script": "temple_acolyte.py",    "tier": "basic", "body": "humanoid", "role": "caster"},          # NOT BUILT YET
    "meadow_stag":       {"script": "meadow_stag.py",       "tier": "basic", "body": "creature", "role": "charger"},        # NOT BUILT YET
    "crystal_warden":    {"script": "crystal_warden.py",    "tier": "basic", "body": "humanoid", "role": "brute"},          # NOT BUILT YET
    "skyborne_harrier":  {"script": "skyborne_harrier.py",  "tier": "basic", "body": "creature", "role": "diver"},          # NOT BUILT YET
    # ---- minibosses (3) ----
    "waystone_sentinel": {"script": "waystone_sentinel.py", "tier": "miniboss", "body": "humanoid", "role": "miniboss"},    # NOT BUILT YET
    "reliquary_keeper":  {"script": "reliquary_keeper.py",  "tier": "miniboss", "body": "humanoid", "role": "miniboss"},    # NOT BUILT YET
    "gatewarden":        {"script": "gatewarden.py",        "tier": "miniboss", "body": "humanoid", "role": "miniboss"},    # NOT BUILT YET
    # ---- boss (1) ----
    "the_ascendant":     {"script": "the_ascendant.py",     "tier": "boss", "body": "humanoid", "role": "boss",
                          "extras": ["the_ascendant_staff.py"], "moveset": "ASCENDANT_MOVESET.md"},
}
