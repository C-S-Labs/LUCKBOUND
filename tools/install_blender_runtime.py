"""Install shared runtime checks into the current Blender startup and MCP dispatch."""
import ast
import inspect
from pathlib import Path
import runpy

RUNTIME = Path(__file__).with_name("blender_runtime.py").resolve()
MARKER = "# LUCKBOUND shared Blender runtime"


def install():
    import bpy
    # Locate the actual current MCP dispatch globals rather than importing a
    # second add-on or restarting the server/scene.
    namespace = next((frame.frame.f_globals for frame in inspect.stack()
                      if "_dispatch" in frame.frame.f_globals and "HANDLERS" in frame.frame.f_globals), None)
    if namespace is None:
        raise RuntimeError("Run this installer through the active Blender MCP execute-code tool")
    addon = Path(namespace["__file__"])
    text = addon.read_text(encoding="utf-8")
    hook = f"runpy.run_path({str(RUNTIME)!r})['protect']()"
    if MARKER not in text:
        anchor = "        # _dispatch is invoked by _process_command_queue on Blender's main thread."
        if text.count(anchor) != 1:
            raise RuntimeError("MCP dispatch changed; inspect before installing")
        text = text.replace(anchor, "        " + MARKER + "\n        import runpy\n        " + hook + "\n" + anchor)
    ast.parse(text)
    # Keep the pre-install add-on for recovery; never overwrite a prior recovery.
    backup = Path("E:/BlenderAIProjects/Runtime/addon_before_runtime.txt")
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        backup.write_bytes(addon.read_bytes())
    addon.write_text(text, encoding="utf-8")
    tree = ast.parse(text)
    dispatch = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_dispatch")
    exec(compile(ast.Module(body=[dispatch], type_ignores=[]), str(addon), "exec"), namespace)
    startup = Path(bpy.utils.user_resource("SCRIPTS")) / "startup" / "luckbound_runtime.py"
    startup.parent.mkdir(parents=True, exist_ok=True)
    startup.write_text('"""LUCKBOUND shared Blender runtime startup integration."""\nimport runpy\n'
                       f'def register():\n    {hook}\ndef unregister():\n    pass\n', encoding="utf-8")
    profile = runpy.run_path(str(RUNTIME))["protect"]()
    print({"profile": profile, "addon": str(addon), "startup": str(startup), "recovery": str(backup)})


if __name__ == "__main__":
    install()
