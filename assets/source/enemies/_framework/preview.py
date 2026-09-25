# Render chosen frames of the current action (for review). Env FRAMES="1,8,12,15,19,26,44" (default: every key).
import bpy, os
from mathutils import Vector
exec(open(os.path.join(FW, "render.py")).read().split("_tag = ")[0], G)       # lights/camera/pedestal only
def preview(action, frames=None, view=(-0.55, -0.8, 0.35)):
    frames = frames or [int(f) for f in os.environ.get("FRAMES", "").split(",") if f] or sorted(set(_ACT.get("keys", [1])))
    cam.location = T + Vector(view) * CD; _look(cam, T)
    for f in frames:
        bpy.context.scene.frame_set(f)
        bpy.context.scene.render.filepath = os.path.join(RENDER_DIR, f"{EID}_{action}_f{f:02d}.png")
        bpy.ops.render.render(write_still=True)
