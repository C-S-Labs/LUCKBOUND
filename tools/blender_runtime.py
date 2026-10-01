"""Shared Windows profile validation for Blender CLI, interactive startup and MCP."""
import ctypes
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORKDIR = Path("E:/BlenderAIProjects/Runtime")


def validate_profile():
    """Check the same Shell API used by native thumbnails, not environment hints."""
    if os.name != "nt":
        return None
    from ctypes import wintypes
    lookup = ctypes.WinDLL("shell32").SHGetSpecialFolderPathW
    lookup.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int, wintypes.BOOL]
    lookup.restype = wintypes.BOOL
    buffer = ctypes.create_unicode_buffer(260)
    if not lookup(None, buffer, 0x28, False):
        raise RuntimeError("Windows CSIDL_PROFILE lookup failed. Blender must run with a normal user token; retry the shared launcher outside the restricted sandbox.")
    profile = Path(buffer.value)
    if not profile.is_absolute() or not profile.is_dir():
        raise RuntimeError("Windows returned an invalid CSIDL_PROFILE directory")
    if profile == REPO or REPO in profile.parents:
        raise RuntimeError("Windows profile must not be inside LUCKBOUND")
    return str(profile)


def protect():
    """Detach inherited repo cwd before checking; failed MCP checks stop dispatch."""
    cwd = Path.cwd().resolve()
    if cwd == REPO or REPO in cwd.parents:
        WORKDIR.mkdir(parents=True, exist_ok=True)
        os.chdir(WORKDIR)
    return validate_profile()


if __name__ == "__main__":
    try:
        protect()
        # Headless jobs historically use repo-relative output arguments. Restore
        # only after the child's own lookup succeeds, before running user scripts.
        original = os.environ.get("LUCKBOUND_BLENDER_JOB_CWD")
        if original:
            os.chdir(original)
        print("LUCKBOUND Blender profile check passed")
    except Exception as exc:
        print("LUCKBOUND Blender blocked:", exc, flush=True)
        os._exit(78)  # stop before any subsequent CLI file/script is processed
