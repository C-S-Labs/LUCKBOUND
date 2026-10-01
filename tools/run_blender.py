"""Launch Blender only after Windows profile validation, with safe startup cwd.

Usage: python tools/run_blender.py -b --factory-startup <scene.blend> --python <script> -- <script args>
Pass --interactive as the first argument for the GUI; all remaining args use Blender syntax.
"""
import os
from pathlib import Path
import subprocess
import sys

from blender_runtime import WORKDIR, validate_profile

BINARY = Path("C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe")


def command(args, cwd):
    args = list(args)
    interactive = bool(args and args[0] == "--interactive")
    if interactive:
        args.pop(0)
    # Blender evaluates arguments in order. Bootstrap MUST precede .blend loads,
    # Python expressions/scripts, imports and rendering, including factory startup.
    prefix = [] if interactive else ["--background"]
    prefix += ["--python-exit-code", "78", "--python", str(Path(__file__).with_name("blender_runtime.py").resolve())]
    paths = {"--python", "-P", "--python-text", "-o", "--render-output"}
    previous = None
    normalized = []
    for arg in args:
        if arg == "--":
            normalized.extend(args[len(normalized):])
            break
        if previous in paths and previous != "--python-text" or arg.lower().endswith((".blend", ".blend1")):
            if not Path(arg).is_absolute():
                arg = str(cwd / arg)
        normalized.append(arg)
        previous = arg
    return [str(BINARY), *prefix, *normalized], interactive


def main():
    try:
        validate_profile()  # no Blender process is created under a failed token
        cwd = Path.cwd().resolve()
        argv, interactive = command(sys.argv[1:], cwd)
        WORKDIR.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        if not interactive:
            env["LUCKBOUND_BLENDER_JOB_CWD"] = str(cwd)
        else:
            env.pop("LUCKBOUND_BLENDER_JOB_CWD", None)
        return subprocess.run(argv, cwd=WORKDIR, env=env).returncode
    except (RuntimeError, OSError) as exc:
        print("LUCKBOUND Blender blocked:", exc, file=sys.stderr)
        return 78


if __name__ == "__main__":
    sys.exit(main())
