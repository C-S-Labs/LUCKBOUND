# LUCKBOUND enemy framework - single headless entry point for EVERY enemy in EVERY biome.
#
#   blender -b --factory-startup --python assets/source/enemies/_framework/run.py -- <world> <enemy_id> [steps...]
#
#   steps (any order, default = --validate --render):
#     --validate        tri budget / rig / grounding / clipping report (framework/validate.py)
#     --render          standard review views (34, side, back) into <world>/renders/
#     --export          static mesh + rig FBX  -> assets/export/enemies/<world>/<Name>.fbx
#     --anims A,B|all   build + export the listed actions from <world>/anims/<enemy_id>/<Action>.py
#     --preview         with --anims: render each key frame to <world>/renders/<enemy>_<Action>_fNN.png
#     --save            save a .blend next to the FBX (for review in the owner's Blender session)
#
# An enemy is found through the biome manifest (<world>/manifest.py): id -> script, tier, role.
# Scripts only ever see four globals for paths: FW (this folder), HERE (the biome folder), OUT_DIR, RENDER_DIR.
import bpy, sys, os, importlib.util
FW = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(FW)                                   # assets/source/enemies
REPO = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 2:
    raise SystemExit(__doc__ if __doc__ else "usage: run.py -- <world> <enemy_id> [steps]")
WORLD, EID = argv[0], argv[1]
STEPS = argv[2:] or ["--validate", "--render"]
HERE = os.path.join(ROOT, WORLD)
OUT_DIR = os.path.join(REPO, "assets", "export", "enemies", WORLD)
RENDER_DIR = os.path.join(HERE, "renders")
os.makedirs(OUT_DIR, exist_ok=True); os.makedirs(RENDER_DIR, exist_ok=True)

spec = importlib.util.spec_from_file_location("manifest", os.path.join(HERE, "manifest.py"))
MAN = importlib.util.module_from_spec(spec); spec.loader.exec_module(MAN)
ENTRY = MAN.ENEMIES[EID]
TIER = ENTRY["tier"]                                         # "basic" | "miniboss" | "boss"

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
G = globals()
exec(open(os.path.join(HERE, ENTRY["script"])).read(), G)   # builds rig + PARTS (enemy_kit.assemble)
for extra in ENTRY.get("extras", []):                         # e.g. the boss's unique weapon
    exec(open(os.path.join(HERE, extra)).read(), G)
PREFIX = NAME + "_"

def _run(fw_file):
    exec(open(os.path.join(FW, fw_file)).read(), G)

if "--validate" in STEPS:
    _run("validate.py")
if "--render" in STEPS:
    _run("render.py")
if "--export" in STEPS:
    _run("export.py"); export_static()
if "--anims" in STEPS:
    want = STEPS[STEPS.index("--anims") + 1]
    adir = os.path.join(HERE, "anims", EID)
    names = sorted(f[:-3] for f in os.listdir(adir) if f.endswith(".py") and not f.startswith("_")) if want == "all" else want.split(",")
    _run("anim_core.py"); _run("export.py")
    for a in names:
        reset_pose()
        exec(open(os.path.join(adir, a + ".py")).read(), G)
        export_action(a)
        if "--preview" in STEPS:
            if "preview" not in G: _run("preview.py")
            preview(a)
if "--save" in STEPS:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, f"{NAME}.blend"))
if os.environ.get("POST"):                                  # ad-hoc review/debug script run after all steps
    exec(open(os.environ["POST"]).read(), G)
