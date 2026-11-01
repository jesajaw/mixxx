"""Runs tests/panel_mapping.test.js (the Mixxx script against a mock of Mixxx's scripting API) with Node.js."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@unittest.skipIf(shutil.which("node") is None, "node is not installed")
class MappingScript(unittest.TestCase):
    def test_script_logic(self):
        r = subprocess.run(["node", str(ROOT / "tests" / "panel_mapping.test.js")], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("tests passed", r.stdout)

    def test_script_is_valid_javascript(self):
        r = subprocess.run(["node", "--check", str(ROOT / "controllers" / "DJS-Touch-Panel-scripts.js")],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
