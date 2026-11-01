"""Browser test of the touch panel UI (multi-touch via Chrome DevTools). Skipped if Playwright/Chromium is missing.

  pip install playwright && playwright install chromium
  python3 -m unittest tests/test_panel_ui.py          (SCREENSHOT=/path/panel.png saves a picture)
"""
import math
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "panel"))

import protocol as P  # noqa: E402
from test_panel import RunningServer  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:                                  # pragma: no cover
    sync_playwright = None


class Fingers:
    """Several simultaneous touches through the DevTools protocol (they become pointer events)."""

    def __init__(self, page):
        self.cdp = page.context.new_cdp_session(page)
        self.points = {}

    def _send(self, kind):
        pts = [{"x": x, "y": y, "id": i} for i, (x, y) in self.points.items()]
        self.cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": pts})

    def down(self, i, x, y):
        self.points[i] = (x, y)
        self._send("touchStart")

    def move(self, i, x, y):
        self.points[i] = (x, y)
        self._send("touchMove")

    def up(self, i):
        self.points.pop(i, None)
        self.cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd",
                      "touchPoints": [{"x": x, "y": y, "id": j} for j, (x, y) in self.points.items()]})


@unittest.skipIf(sync_playwright is None, "playwright is not installed")
class PanelUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rs = RunningServer().__enter__()
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch()
        except Exception as e:  # noqa: BLE001
            cls.pw.stop()
            cls.rs.__exit__()
            raise unittest.SkipTest(f"Chromium not available: {e}")
        cls.ctx = cls.browser.new_context(viewport={"width": 1280, "height": 800}, has_touch=True)

    @classmethod
    def tearDownClass(cls):
        cls.ctx.close()
        cls.browser.close()
        cls.pw.stop()
        cls.rs.__exit__()

    def setUp(self):
        self.errors = []
        self.rs.server.panel.state.clear()           # every test starts like a fresh Mixxx session
        self.page = self.ctx.new_page()
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.on("console", lambda m: self.errors.append(m.text) if m.type == "error" else None)
        self.page.goto(f"http://127.0.0.1:{self.rs.port}/")
        self.page.wait_for_selector("#status.wait", timeout=8000)
        self.page.wait_for_timeout(150)
        self.rs.midi.sent.clear()
        self.fingers = Fingers(self.page)

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors, [])

    # helpers
    def center(self, cid):
        b = self.page.locator(f'[data-id="{cid}"]').bounding_box()
        return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, b

    def sent(self):
        self.page.wait_for_timeout(150)
        return list(self.rs.midi.sent)

    def feed(self, data):
        self.rs.midi.inject(bytes(data))
        self.page.wait_for_timeout(120)

    # tests
    def test_every_protocol_control_has_a_widget_and_every_widget_exists(self):
        widgets = set(self.page.evaluate("Object.keys(widgets)"))
        proto = {c["id"] for c in P.CONTROLS if c["id"] != "request"}
        self.assertEqual(proto - widgets, set(), "controls without a widget")
        self.assertEqual(widgets - proto, set(), "widgets that are not in the protocol")
        dom = set(self.page.evaluate("[...document.querySelectorAll('[data-id]')].map(e => e.dataset.id)"))
        self.assertEqual(dom - proto, set())
        # everything a DJ can touch is really on screen
        touchable = {c["id"] for c in P.CONTROLS if P.midi_in_status(c) and c["id"] not in ("request",)}
        hidden_ok = {"d1.jog_touch", "d2.jog_touch", "d1.nudge", "d2.nudge"}      # parts of the jog wheel
        self.assertEqual(touchable - dom - hidden_ok, set())

    def test_tap_sends_press_and_release(self):
        x, y, _ = self.center("d1.play")
        self.fingers.down(1, x, y)
        self.fingers.up(1)
        n = P.BY_ID["d1.play"]["num"]
        self.assertEqual(self.sent(), [bytes([0x90, n, 127]), bytes([0x90, n, 0])])

    def test_two_fingers_at_once_cue_held_while_crossfading(self):
        cx, cy, _ = self.center("d1.cue")
        fx, fy, box = self.center("xfader")
        self.fingers.down(1, cx, cy)                                   # finger 1 holds CUE
        self.fingers.down(2, fx, fy)                                   # finger 2 grabs the crossfader
        for step in range(1, 9):
            self.fingers.move(2, fx + step * box["width"] / 20, fy)
        cue_state = self.page.evaluate("document.querySelector('[data-id=\"d1.cue\"]').classList.contains('down')")
        self.assertTrue(cue_state, "CUE must still be held while the other finger moves")
        self.fingers.up(2)
        self.fingers.up(1)
        msgs = self.sent()
        cue, xf = P.BY_ID["d1.cue"]["num"], P.BY_ID["xfader"]["num"]
        self.assertEqual(msgs[0], bytes([0x90, cue, 127]))
        self.assertEqual(msgs[-1], bytes([0x90, cue, 0]))
        xvals = [m[2] for m in msgs if m[0] == 0xB0 and m[1] == xf]
        self.assertGreater(len(xvals), 2)
        self.assertEqual(xvals, sorted(xvals))                          # moved to the right only
        self.assertGreater(xvals[-1], 64)

    def test_pitch_fader_sends_14_bit_pairs(self):
        x, y, box = self.center("d1.rate")
        self.fingers.down(1, x, y)
        self.fingers.move(1, x, y - box["height"] * 0.2)
        self.fingers.up(1)
        msgs = [m for m in self.sent() if m[0] == 0xB0]
        rate = P.BY_ID["d1.rate"]["num"]
        self.assertTrue(msgs and len(msgs) % 2 == 0)
        for msb, lsb in zip(msgs[::2], msgs[1::2]):
            self.assertEqual((msb[1], lsb[1]), (rate, rate + 32))
        final = (msgs[-2][2] << 7) | msgs[-1][2]
        self.assertGreater(final, 8192)                                 # dragged up = faster

    def test_knob_double_tap_resets_to_center(self):
        x, y, _ = self.center("d1.eq_hi")
        self.fingers.down(1, x, y); self.fingers.move(1, x, y - 60); self.fingers.up(1)
        self.page.wait_for_timeout(100)
        self.rs.midi.sent.clear()
        self.fingers.down(1, x, y); self.fingers.up(1)
        self.page.wait_for_timeout(60)
        self.fingers.down(1, x, y); self.fingers.up(1)
        msgs = [m for m in self.sent() if m[0] == 0xB0 and m[1] == P.BY_ID["d1.eq_hi"]["num"]]
        self.assertTrue(msgs)
        self.assertEqual(msgs[-1][2], 64)

    def test_jog_platter_scratches_and_ring_nudges(self):
        x, y, box = self.center("d1.jog")
        r = box["width"] / 2
        touch, jog, nudge = (P.BY_ID[f"d1.{n}"]["num"] for n in ("jog_touch", "jog", "nudge"))
        # platter: quarter turn clockwise -> 256 ticks in total, sent as several positive deltas
        self.fingers.down(1, x + r * 0.4, y)
        for k in range(1, 13):
            a = k * (math.pi / 2) / 12
            self.fingers.move(1, x + r * 0.4 * math.cos(a), y + r * 0.4 * math.sin(a))
        self.fingers.up(1)
        msgs = self.sent()
        self.assertEqual(msgs[0], bytes([0x90, touch, 127]))
        self.assertEqual(msgs[-1], bytes([0x90, touch, 0]))
        ticks = [m[2] - 64 for m in msgs if m[0] == 0xB0 and m[1] == jog]
        self.assertTrue(all(t > 0 for t in ticks) and ticks)
        self.assertAlmostEqual(sum(ticks), 256, delta=24)
        # ring: counter-clockwise -> negative nudges, and no touch message
        self.rs.midi.sent.clear()
        self.fingers.down(1, x + r * 0.9, y)
        for k in range(1, 9):
            a = -k * (math.pi / 3) / 8
            self.fingers.move(1, x + r * 0.9 * math.cos(a), y + r * 0.9 * math.sin(a))
        self.fingers.up(1)
        msgs = self.sent()
        self.assertFalse([m for m in msgs if m[0] == 0x90])
        nud = [m[2] - 64 for m in msgs if m[0] == 0xB0 and m[1] == nudge]
        self.assertTrue(nud and all(t < 0 for t in nud))

    def test_shift_is_latching_and_precedes_the_hotcue(self):
        sx, sy, _ = self.center("shift")
        self.fingers.down(1, sx, sy); self.fingers.up(1)
        hx, hy, _ = self.center("d2.hotcue3")
        self.fingers.down(1, hx, hy); self.fingers.up(1)
        self.fingers.down(1, sx, sy); self.fingers.up(1)
        n_shift, n_hc = P.BY_ID["shift"]["num"], P.BY_ID["d2.hotcue3"]["num"]
        self.assertEqual(self.sent(), [bytes([0x90, n_shift, 127]), bytes([0x90, n_hc, 127]),
                                       bytes([0x90, n_hc, 0]), bytes([0x90, n_shift, 0])])

    def test_library_browse_swipe_and_buttons(self):
        x, y, box = self.center("lib")
        self.fingers.down(1, x, y - 8)                                   # start inside the strip
        self.fingers.move(1, x, y - 8 + 80)                              # swipe down 80 px -> about 3 rows
        self.fingers.up(1)
        rel = [m[2] - 64 for m in self.sent() if m[0] == 0xB0 and m[1] == P.BY_ID["lib"]["num"]]
        self.assertTrue(rel and all(v > 0 for v in rel))
        self.assertAlmostEqual(sum(rel), 3, delta=1)

    def test_feedback_updates_the_screen(self):
        n = P.BY_ID["d1.sync"]["num"]
        self.feed([0x91, n, 127])
        self.assertTrue(self.page.evaluate("document.querySelector('[data-id=\"d1.sync\"]').classList.contains('lit')"))
        self.feed([0x91, n, 0])
        self.assertFalse(self.page.evaluate("document.querySelector('[data-id=\"d1.sync\"]').classList.contains('lit')"))
        # bpm 128.0, duration 200 s, position 50 % -> 1:40 left
        for cid, v in (("d1.bpm", 1280), ("d1.dur", 200), ("d1.pos", 8192)):
            num = P.BY_ID[cid]["num"]
            self.feed([0xB1, num, v >> 7])
            self.feed([0xB1, num + 32, v & 127])
        txt = self.page.evaluate("document.querySelector('[data-id=\"d1.bpm\"]').textContent")
        self.assertIn("128.0", txt)
        self.assertEqual(self.page.evaluate("document.querySelector('[data-view=\"d1.time\"]').textContent"), "-1:40")
        width = self.page.evaluate("document.querySelector('[data-id=\"d1.pos\"]').firstChild.style.width")
        self.assertTrue(width.startswith("50"), width)
        # volume fader follows Mixxx (e.g. moved with the mouse in Mixxx), but not while it is being touched
        vol = P.BY_ID["d2.vol"]["num"]
        self.feed([0xB1, vol, 127])
        _, _, box = self.center("d2.vol")
        cap_bottom = self.page.evaluate("document.querySelector('[data-id=\"d2.vol\"] .cap').style.bottom")
        self.assertEqual(cap_bottom, "100%")

    def test_status_text_and_reconnect(self):
        self.assertIn("waiting for Mixxx", self.page.inner_text("#status"))
        self.feed([0xB1, P.BY_ID["xfader"]["num"], 10])
        self.assertIn("connected to Mixxx", self.page.inner_text("#status"))

    def test_screenshot(self):
        path = os.environ.get("SCREENSHOT")
        if not path:
            self.skipTest("set SCREENSHOT=/path/panel.png to save a picture")
        for cid, v in (("d1.bpm", 1280), ("d2.bpm", 1325), ("d1.dur", 215), ("d2.dur", 187), ("d1.pos", 5000), ("d2.pos", 12000)):
            num = P.BY_ID[cid]["num"]
            self.feed([0xB1, num, v >> 7]); self.feed([0xB1, num + 32, v & 127])
        for cid in ("d1.play", "d1.sync", "d2.play", "d2.pfl", "d1.hotcue1", "d1.hotcue3", "d2.hotcue2", "d1.reloop", "autodj"):
            self.feed([0x91, P.BY_ID[cid]["num"], 127])
        for cid, v in (("d1.vu", 90), ("d2.vu", 60), ("d1.vol", 110), ("d2.vol", 80), ("xfader", 40), ("d1.eq_hi", 64),
                       ("d1.eq_lo", 100), ("d2.filter", 30), ("main_gain", 80), ("cue_mix", 64), ("head_gain", 90), ("d1.gain", 70)):
            self.feed([0xB1, P.BY_ID[cid]["num"], v])
        self.page.screenshot(path=path)


if __name__ == "__main__":
    unittest.main()
