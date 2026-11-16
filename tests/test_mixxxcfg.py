import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "panel"))

import mixxxcfg as C  # noqa: E402


class SkinSettings(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = Path(self.tmp.name) / "data"
        self.cfg = self.data / "mixxx.cfg"

    def groups(self):
        return C.parse(self.cfg.read_text(encoding="utf-8"))

    def backups(self):
        return sorted(p.name for p in self.data.glob("mixxx.cfg.bak.*"))

    def test_fresh_profile_gets_skin_and_scheme_and_no_backup(self):
        self.assertEqual(len(C.prepare(self.data)), 2)
        g = self.groups()
        self.assertEqual((g["Config"]["ResizableSkin"], g["Config"]["Scheme"]), ("StudioDeck", "Studio"))
        self.assertEqual(self.backups(), [])

    def test_second_run_changes_nothing(self):
        C.prepare(self.data)
        before = self.cfg.read_bytes()
        self.assertEqual(C.prepare(self.data), [])
        self.assertEqual(self.cfg.read_bytes(), before)

    def test_without_force_a_skin_the_user_chose_stays(self):
        self.data.mkdir(parents=True)
        self.cfg.write_text("[Config]\nResizableSkin LateNight\nScheme Dark\n", encoding="utf-8")
        self.assertEqual(C.prepare(self.data), [])
        self.assertEqual(self.groups()["Config"]["ResizableSkin"], "LateNight")

    def test_force_sets_the_skin_and_keeps_a_backup_of_the_old_settings(self):
        self.data.mkdir(parents=True)
        self.cfg.write_text("[Config]\nResizableSkin LateNight\nScheme Dark\n", encoding="utf-8")
        C.prepare(self.data, force=True)
        self.assertEqual(self.groups()["Config"]["ResizableSkin"], "StudioDeck")
        self.assertEqual(len(self.backups()), 1)
        self.assertIn("LateNight", (self.data / self.backups()[0]).read_text())

    def test_other_settings_and_values_with_spaces_survive(self):
        self.data.mkdir(parents=True)
        self.cfg.write_text("[Library]\nDirectory /home/dj/My Music/Sets\n\n[Master]\nenabled 1\n", encoding="utf-8")
        C.prepare(self.data, force=True)
        g = self.groups()
        self.assertEqual(g["Library"]["Directory"], "/home/dj/My Music/Sets")
        self.assertEqual(g["Master"]["enabled"], "1")

    def test_tolerates_bom_and_windows_line_endings(self):
        self.data.mkdir(parents=True)
        self.cfg.write_bytes(b"\xef\xbb\xbf[Config]\r\nResizableSkin LateNight\r\n")
        C.prepare(self.data, force=True)
        self.assertEqual(self.groups()["Config"]["ResizableSkin"], "StudioDeck")

    def test_leaves_no_temp_file_and_creates_the_folder(self):
        C.prepare(self.data)
        self.assertEqual([p.name for p in self.data.iterdir()], ["mixxx.cfg"])

    def test_controller_with_our_mapping_is_recognised_whatever_the_device_is_called(self):
        self.assertFalse(C.controller_configured(self.data))
        self.data.mkdir(parents=True)
        self.cfg.write_text("[ControllerPreset]\nSome_ALSA_name_128-0 /home/dj/.mixxx/controllers/DJS-Touch-Panel.midi.xml\n", encoding="utf-8")
        self.assertTrue(C.controller_configured(self.data))
        self.cfg.write_text("[ControllerPreset]\nOther /x/akai.midi.xml\n", encoding="utf-8")
        self.assertFalse(C.controller_configured(self.data))


if __name__ == "__main__":
    unittest.main()
