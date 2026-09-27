# Verdant Valley enemy manifest: the ONE place that lists this biome's enemies for the framework runner.
# STAGING (2026-09-26): the biome itself isn't built yet. Rootbound Warden was moved here from sky_citadel
# because its braided-root / grove-statue design (see rootbound_warden.py) reads as Verdant Valley, not the
# citadel. Fill in the rest of the roster when this biome's build pass starts.
#   tier:  basic | miniboss | boss        (drives validation + detail expectations, see docs/ENEMY_FRAMEWORK.md)
#   body:  joint profile -> _framework/bodies/<body>.py (or <biome>/bodies/<body>.py):
#          humanoid (R15 elbows/knees/grips) | creature (no joint rules) | any custom profile (e.g. "finned")
#   role:  combat archetype id (shared Studio behaviour, see docs/ENEMY_FRAMEWORK.md "Archetypes")
#   extras: extra build scripts run after the body (unique boss weapon, etc.)
WORLD = "verdant_valley"
PALETTE = "TBD (Rootbound Warden's bark/moss/stone/blossom palette is a starting point)"
ENEMIES = {
    "rootbound_warden": {"script": "rootbound_warden.py", "tier": "basic", "body": "humanoid", "role": "brute"},
}
