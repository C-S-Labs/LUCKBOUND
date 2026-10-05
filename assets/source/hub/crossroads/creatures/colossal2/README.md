# Colossal2 (Crossroads V2 round 2): cinder_wyrm, aether_nautilus

    python tools/run_blender.py -b --factory-startup --python build_colossal2.py -- --export --render [--final --closeups]
    python tools/run_blender.py -b --factory-startup --python pose_preview.py -- [--final]

Writes `assets/export/hub/crossroads/creatures_colossal2.fbx` and `.json` (top-level `"frame": "orbiter"`; same frame convention
as the colossal group: Blender (x,y,z) -> (-x, z, y)). `pose_preview.py` applies the SkyTraffic maths (hingeAbout, acc = chain.acc * hinge,
effective phase = parent phase - lag) to the sidecar data and renders six phases per creature.
cinder_wyrm: head is the body root, so the assembly trails 775 studs behind the body centre. Pulse = scale fraction about the part centre.
