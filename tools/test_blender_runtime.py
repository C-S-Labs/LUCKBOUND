"""Small regression checks for launch ordering and fail-closed profile validation."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import blender_runtime
import run_blender


class ShellLookup:
    def __init__(self, ok, value):
        self.ok, self.value = ok, value

    def __call__(self, hwnd, buffer, folder, create):
        assert folder == 0x28 and not create
        buffer.value = self.value
        return self.ok


class RuntimeTests(unittest.TestCase):
    def lookup(self, ok, path):
        shell = type("Shell", (), {})()
        shell.SHGetSpecialFolderPathW = ShellLookup(ok, path)
        return patch.object(blender_runtime.ctypes, "WinDLL", return_value=shell)

    def test_failed_lookup_rejects_even_plausible_buffer(self):
        with self.lookup(False, str(Path.cwd())):
            with self.assertRaises(RuntimeError):
                blender_runtime.validate_profile()

    def test_relative_profile_rejected(self):
        with self.lookup(True, "."):
            with self.assertRaises(RuntimeError):
                blender_runtime.validate_profile()

    def test_repo_profile_rejected(self):
        with self.lookup(True, str(blender_runtime.REPO)):
            with self.assertRaises(RuntimeError):
                blender_runtime.validate_profile()

    def test_valid_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.lookup(True, directory):
                self.assertEqual(blender_runtime.validate_profile(), directory)

    def test_failed_parent_never_launches(self):
        with patch.object(run_blender, "validate_profile", side_effect=RuntimeError("probe")):
            with patch.object(run_blender.subprocess, "run") as launch:
                self.assertEqual(run_blender.main(), 78)
                launch.assert_not_called()

    def test_bootstrap_first_and_script_arguments_preserved(self):
        cwd = Path.cwd()
        argv, interactive = run_blender.command(["-b", "--factory-startup", "scene.blend", "--python", "script.py", "--", "--out", "relative"], cwd)
        self.assertFalse(interactive)
        self.assertLess(argv.index("--python"), argv.index(str(cwd / "scene.blend")))
        self.assertIn(str(cwd / "script.py"), argv)
        self.assertEqual(argv[-3:], ["--", "--out", "relative"])

    def test_interactive_still_bootstraps_before_file(self):
        argv, interactive = run_blender.command(["--interactive", "scene.blend"], Path.cwd())
        self.assertTrue(interactive)
        self.assertNotIn("--background", argv)
        self.assertLess(argv.index("--python"), argv.index(str(Path.cwd() / "scene.blend")))


if __name__ == "__main__":
    unittest.main()
