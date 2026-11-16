import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "panel"))

import launcher as L  # noqa: E402
import mixxxcfg  # noqa: E402


class Prepare(unittest.TestCase):
    def test_fresh_profile_gets_the_skin_and_the_first_run_hint(self):
        with tempfile.TemporaryDirectory() as d:
            said = []
            L.prepare(SimpleNamespace(data_dir=Path(d) / "profile"), said.append)
            self.assertTrue(any("ResizableSkin" in m for m in said))
            self.assertTrue(any("Preferences > Controllers" in m for m in said))

    def test_no_hint_once_the_controller_is_set_up(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "mixxx.cfg").write_text("[Config]\nResizableSkin StudioDeck\nScheme Studio\n\n"
                                               "[ControllerPreset]\nx /p/" + mixxxcfg.MAPPING + "\n")
            said = []
            L.prepare(SimpleNamespace(data_dir=Path(d)), said.append)
            self.assertEqual(said, [])


class StartMixxx(unittest.TestCase):
    def test_runs_exactly_the_detected_command(self):
        seen = []
        L.start_mixxx(SimpleNamespace(command=["flatpak", "run", "org.mixxx.Mixxx"]), spawn=lambda cmd: seen.append(cmd) or "proc")
        self.assertEqual(seen, [["flatpak", "run", "org.mixxx.Mixxx"]])


class EndToEnd(unittest.TestCase):
    """The real server program with --launch: it starts 'Mixxx' and ends when Mixxx ends."""

    def run_server(self, d, fake, extra_env=None):
        env = dict(os.environ, MIXXX_DATA=str(Path(d) / "profile"), **(extra_env or {}))
        return subprocess.run([sys.executable, str(ROOT / "panel" / "server.py"), "--launch", "--dry-run", "--host", "127.0.0.1",
                               "--port", "0", "--mixxx-exe", str(fake)], capture_output=True, text=True, timeout=30, env=env)

    def test_server_launches_mixxx_and_quits_when_it_is_closed(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "args.txt"
            fake = Path(d) / "fake-mixxx"
            fake.write_text(f'#!/bin/sh\necho "$@" > "{log}"\nsleep 2\n')
            fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
            t0 = time.time()
            r = self.run_server(d, fake)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertLess(time.time() - t0, 20)                                  # it ended by itself
            self.assertIn("Mixxx started", r.stdout)
            self.assertEqual(log.read_text().split(), ["--settings-path", str(Path(d) / "profile")])
            self.assertIn("ResizableSkin", (Path(d) / "profile" / "mixxx.cfg").read_text())     # skin set up before the start

    def test_unstartable_mixxx_is_reported_and_the_panel_does_not_hang(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_server(d, Path(d) / "does-not-exist")
            self.assertIn("Mixxx could not be started", r.stderr)

    def test_missing_mixxx_says_what_to_do(self):
        with tempfile.TemporaryDirectory() as d:
            env = {k: v for k, v in os.environ.items() if k not in ("MIXXX_BIN", "MIXXX")}
            env["PATH"] = str(Path(d))                                               # no mixxx, no flatpak
            r = subprocess.run([sys.executable, str(ROOT / "panel" / "server.py"), "--launch", "--dry-run", "--port", "0"],
                               capture_output=True, text=True, timeout=30, env=env)
            self.assertEqual(r.returncode, 1)
            self.assertIn("make install", r.stderr)


class ServerStop(unittest.TestCase):
    def test_stop_ends_run_from_another_thread(self):
        import asyncio
        import threading

        import server as S
        srv = S.Server(S.NullPort)
        ready, done = threading.Event(), threading.Event()

        def run():
            asyncio.run(srv.run("127.0.0.1", 0, lambda s: ready.set()))
            done.set()

        threading.Thread(target=run, daemon=True).start()
        self.assertTrue(ready.wait(10))
        srv.stop()
        self.assertTrue(done.wait(10), "run() did not end after stop()")


if __name__ == "__main__":
    unittest.main()
