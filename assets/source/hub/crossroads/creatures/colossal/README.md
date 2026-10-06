# Colossal creatures (Crossroads V2 sky ecosystem)

`starweaver` (Astral Reach) and `elder_greatturtle` (Verdant), per `docs/design/SKY_ECOSYSTEM_CONTRACT.md` 2, 3, 4.1.

    python tools/run_blender.py -b --factory-startup --python assets/source/hub/crossroads/creatures/colossal/build_colossal.py -- --export --render [--final --closeups]

Writes `assets/export/hub/crossroads/creatures_colossal.fbx` and `.json`. Helpers come read-only from `build_crossroads_hub.py` (runpy).
Built at final stud size, head +X, up +Z, body bbox centre at the origin. Studio import is an owner gate.

Sidecar frames: `offset`/`hinge`/`axis` use the `OrbiterParts` frame of `make_layout_luau.local()` (Blender (x,y,z) -> (-x, z, y)); `size` is the body mesh bbox as (x, z, y).
`Pulse` = uniform scale `1 + amp*sin` about `hinge` (amp is a scale fraction, not radians); `Spin` rate is rad/s; Flap/Pulse/Flicker rate is Hz.
