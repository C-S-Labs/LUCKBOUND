# Emberfall — pending map authoring requirements

This records the owner's 2026-09-30 safety requirement; it does not replace the existing
world blueprint or define a new kit/connection vocabulary. Full map schema remains pending.

Every playable chunk needs invisible player-collision boundaries along exposed platform
and walkway sides, following local floor height and accompanying its parent chunk.
Initial height is 64 studs. Leave all socket mouths, bridges and doorways clear.
Backdrops need no boundaries; enclosed rooms use their solid walls.
Camera queries explicitly exclude the boundaries. Future animated visual identification
is a separate noncollidable prop, independent of the fixed collision wall.
Verify drop edges, traversal clearance and jump escape attempts in Studio.
See [shared map requirement](../MODULAR_MAPS.md). Generic runtime support is pending.
