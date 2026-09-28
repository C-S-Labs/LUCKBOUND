# Cloud bpy Setup

Working versions confirmed in Claude Code cloud sessions:

- Python: 3.11.15
- bpy: 4.2.0 (Blender 4.2.0)

Setup: `bash setup_cloud.sh` (creates `.venv/`, installs `bpy==4.2.0`).

Verified with `python test_rock.py`: generates a 642-vertex / 1280-face rock
mesh and exports `exports/test_rock.fbx`.
