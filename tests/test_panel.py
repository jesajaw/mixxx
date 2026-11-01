"""Tests of the touch panel: protocol, MIDI translation, WebSocket/HTTP server, generated Mixxx mapping."""
import asyncio
import base64
import json
import os
import struct
import subprocess
import sys
import threading
import unittest
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "panel"))
sys.path.insert(0, str(ROOT / "tools"))

import make_panel  # noqa: E402
import protocol as P  # noqa: E402
import server as S  # noqa: E402


class LoopPort:
    """MIDI port stand-in: remembers what was sent, lets the test inject feedback from 'Mixxx'."""

    def __init__(self, on_message):
        self.on_message, self.sent = on_message, []

    def send(self, data):
        self.sent.append(bytes(data))

    def close(self):
        pass

    def inject(self, data):
        self.on_message(bytes(data))


class RunningServer:
    """The real Server (HTTP + WebSocket) on a free port in a background thread."""

    def __enter__(self):
        self.ready, self.port = threading.Event(), None
        self.server = S.Server(LoopPort)
        self.loop = asyncio.new_event_loop()

        def run():
            asyncio.set_event_loop(self.loop)
            self.task = self.loop.create_task(self.server.run("127.0.0.1", 0, self._ready))
            try:
                self.loop.run_until_complete(self.task)
            except asyncio.CancelledError:
                pass

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        assert self.ready.wait(10), "server did not start"
        return self

    def _ready(self, srv):
        self.port = srv.sockets[0].getsockname()[1]
        self.ready.set()

    @property
    def midi(self):
        return self.server.midi

    def __exit__(self, *a):
        self.loop.call_soon_threadsafe(self.task.cancel)
        self.thread.join(5)
        if not self.thread.is_alive():
            self.loop.close()


# ---- tiny WebSocket client (masked frames) -----------------------------------------------------

def _frame(opcode, payload=b"", fin=True, mask=b"\x01\x02\x03\x04"):
    n = len(payload)
    head = bytes([(0x80 if fin else 0) | opcode])
    head += bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack(">H", n)
    return head + mask + bytes(b ^ mask[i & 3] for i, b in enumerate(payload))


async def _read_frame(r):
    b1, b2 = await r.readexactly(2)
    n = b2 & 0x7F
    if n == 126:
        (n,) = struct.unpack(">H", await r.readexactly(2))
    return b1 & 0x0F, await r.readexactly(n)


async def _connect(port, origin="same", path="/ws", key="dGhlIHNhbXBsZSBub25jZQ=="):
    r, w = await asyncio.open_connection("127.0.0.1", port)
    host = f"127.0.0.1:{port}"
    org = f"Origin: http://{host}\r\n" if origin == "same" else (f"Origin: {origin}\r\n" if origin else "")
    w.write((f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
             f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n{org}\r\n").encode())
    head = (await asyncio.wait_for(r.readuntil(b"\r\n\r\n"), 5)).decode()
    return r, w, head


async def _http(port, request):
    r, w = await asyncio.open_connection("127.0.0.1", port)
    w.write(request.encode())
    data = await asyncio.wait_for(r.read(), 5)
    w.close()
    return data.decode("latin-1")


# ---- tests -------------------------------------------------------------------------------------

class Protocol(unittest.TestCase):
    def test_ids_unique_and_midi_numbers_unique(self):
        ids = [c["id"] for c in P.CONTROLS]
        self.assertEqual(len(ids), len(set(ids)))
        notes, ccs = set(), set()
        for c in P.CONTROLS:
            if c["kind"] in ("button", "led"):
                self.assertNotIn(c["num"], notes, c["id"])
                notes.add(c["num"])
            else:
                used = {c["num"], c["num"] + 32} if P.is_14bit(c) else {c["num"]}
                self.assertFalse(used & ccs, c["id"])
                ccs |= used
        for n in notes | ccs:
            self.assertTrue(0 <= n <= 127)

    def test_every_control_does_something(self):
        for c in P.CONTROLS:
            self.assertTrue(P.midi_in_status(c) or P.midi_out_status(c), c["id"])
            if P.midi_in_status(c):
                self.assertIn("mode", c["mixxx"], c["id"])

    def test_feedback_controls_have_a_return_path(self):
        for c in P.CONTROLS:
            if c.get("feedback"):
                self.assertIsNotNone(P.midi_out_status(c), c["id"])


class PanelLogic(unittest.TestCase):
    def setUp(self):
        self.p = S.Panel()

    def test_button_abs_rel_translation(self):
        play = P.BY_ID["d1.play"]
        self.assertEqual(self.p.from_ui({"id": "d1.play", "v": 127}), [bytes([0x90, play["num"], 127])])
        self.assertEqual(self.p.from_ui({"id": "d1.play", "v": 0}), [bytes([0x90, play["num"], 0])])
        xf = P.BY_ID["xfader"]
        self.assertEqual(self.p.from_ui({"id": "xfader", "v": 500}), [bytes([0xB0, xf["num"], 127])])   # clamped
        self.assertEqual(self.p.from_ui({"id": "xfader", "v": -4}), [bytes([0xB0, xf["num"], 0])])
        jog = P.BY_ID["d2.jog"]
        self.assertEqual(self.p.from_ui({"id": "d2.jog", "v": -5}), [bytes([0xB0, jog["num"], 59])])
        self.assertEqual(self.p.from_ui({"id": "d2.jog", "v": 999}), [bytes([0xB0, jog["num"], 127])])
        self.assertEqual(self.p.from_ui({"id": "d2.jog", "v": 0}), [])

    def test_14bit_goes_out_msb_then_lsb(self):
        rate = P.BY_ID["d1.rate"]
        self.assertEqual(self.p.from_ui({"id": "d1.rate", "v": 8192}),
                         [bytes([0xB0, rate["num"], 64]), bytes([0xB0, rate["num"] + 32, 0])])
        self.assertEqual(self.p.from_ui({"id": "d1.rate", "v": 99999})[1], bytes([0xB0, rate["num"] + 32, 127]))

    def test_garbage_is_ignored(self):
        for bad in (None, 5, "x", {}, {"id": "nope", "v": 1}, {"id": "d1.play"}, {"id": "d1.play", "v": "1"},
                    {"id": "d1.play", "v": True}, {"id": "d1.vu", "v": 3}, {"id": "d1.loaded", "v": 1}):
            self.assertEqual(self.p.from_ui(bad), [], bad)

    def test_feedback_decoding(self):
        play = P.BY_ID["d1.play"]
        self.assertEqual(self.p.from_midi(bytes([0x91, play["num"], 127])), [{"id": "d1.play", "v": 127}])
        self.assertEqual(self.p.from_midi(bytes([0x91, play["num"], 0])), [{"id": "d1.play", "v": 0}])
        vu = P.BY_ID["d2.vu"]
        self.assertEqual(self.p.from_midi(bytes([0xB1, vu["num"], 99])), [{"id": "d2.vu", "v": 99}])
        pos = P.BY_ID["d1.pos"]
        self.assertEqual(self.p.from_midi(bytes([0xB1, pos["num"], 100])), [])           # MSB alone
        self.assertEqual(self.p.from_midi(bytes([0xB1, pos["num"] + 32, 5])), [{"id": "d1.pos", "v": (100 << 7) | 5}])

    def test_own_messages_and_foreign_channels_are_ignored(self):
        play = P.BY_ID["d1.play"]
        self.assertEqual(self.p.from_midi(bytes([0x90, play["num"], 127])), [])          # channel 1 = our own echo
        self.assertEqual(self.p.from_midi(bytes([0x92, play["num"], 127])), [])
        self.assertEqual(self.p.from_midi(bytes([0xB1, 100, 1])), [])                    # unused controller
        self.assertEqual(self.p.from_midi(b"\xF8"), [])

    def test_snapshot_remembers_last_values(self):
        self.p.from_midi(bytes([0xB1, P.BY_ID["xfader"]["num"], 10]))
        self.p.from_midi(bytes([0xB1, P.BY_ID["xfader"]["num"], 20]))
        self.assertEqual(self.p.snapshot(), [{"id": "xfader", "v": 20}])


class Network(unittest.TestCase):
    def test_http_pages(self):
        with RunningServer() as rs:
            page = asyncio.run(_http(rs.port, "GET / HTTP/1.1\r\nHost: x\r\n\r\n"))
            self.assertIn("200 OK", page.split("\r\n")[0])
            self.assertIn("DJS PANEL", page)
            self.assertIn("Content-Security-Policy", page)
            self.assertIn("404", asyncio.run(_http(rs.port, "GET /etc/passwd HTTP/1.1\r\nHost: x\r\n\r\n")).split("\r\n")[0])
            self.assertIn("404", asyncio.run(_http(rs.port, "GET /../server.py HTTP/1.1\r\nHost: x\r\n\r\n")).split("\r\n")[0])
            self.assertIn("405", asyncio.run(_http(rs.port, "POST / HTTP/1.1\r\nHost: x\r\n\r\n")).split("\r\n")[0])
            self.assertIn("404", asyncio.run(_http(rs.port, "GET /ws HTTP/1.1\r\nHost: x\r\n\r\n")).split("\r\n")[0])

    def test_websocket_roundtrip(self):
        async def scenario(rs):
            r, w, head = await _connect(rs.port)
            self.assertIn("101", head.split("\r\n")[0])
            self.assertIn("s3pPLMBiTxaQ9kYGzzhZRbK+xOo=", head)            # RFC 6455 sample accept key
            await asyncio.sleep(0.1)
            # a new screen makes the server ask Mixxx for its state: press + release of the request note
            self.assertEqual(rs.midi.sent[-2:], [bytes([0x90, 127, 127]), bytes([0x90, 127, 0])])
            rs.midi.sent.clear()
            w.write(_frame(0x1, json.dumps({"id": "d1.cue", "v": 127}).encode()))
            await w.drain()
            await asyncio.sleep(0.1)
            self.assertEqual(rs.midi.sent, [bytes([0x90, P.BY_ID["d1.cue"]["num"], 127])])
            # feedback from Mixxx reaches the screen (injected like rtmidi's thread does)
            rs.midi.inject(bytes([0x91, P.BY_ID["d1.cue"]["num"], 127]))
            op, payload = await asyncio.wait_for(_read_frame(r), 5)
            self.assertEqual((op, json.loads(payload)), (1, {"id": "d1.cue", "v": 127}))
            # ping -> pong, then close handshake
            w.write(_frame(0x9, b"hi"))
            self.assertEqual(await asyncio.wait_for(_read_frame(r), 5), (0xA, b"hi"))
            w.write(_frame(0x8, b"\x03\xe8"))
            self.assertEqual((await asyncio.wait_for(_read_frame(r), 5))[0], 0x8)
            w.close()

        with RunningServer() as rs:
            asyncio.run(scenario(rs))

    def test_second_screen_gets_the_current_state(self):
        async def scenario(rs):
            rs.midi.inject(bytes([0xB1, P.BY_ID["xfader"]["num"], 33]))
            await asyncio.sleep(0.1)
            r, w, _ = await _connect(rs.port)
            op, payload = await asyncio.wait_for(_read_frame(r), 5)
            self.assertEqual(json.loads(payload), {"id": "xfader", "v": 33})
            w.close()

        with RunningServer() as rs:
            asyncio.run(scenario(rs))

    def test_foreign_websites_are_rejected(self):
        async def scenario(rs):
            for origin in ("https://evil.example", "http://localhost:1"):
                r, w, head = await _connect(rs.port, origin=origin)
                self.assertIn("403", head.split("\r\n")[0], origin)
                w.close()
            r, w, head = await _connect(rs.port, origin=None)       # not a browser: allowed
            self.assertIn("101", head.split("\r\n")[0])
            w.close()

        with RunningServer() as rs:
            asyncio.run(scenario(rs))

    def test_bad_input_does_not_kill_the_server(self):
        async def scenario(rs):
            r, w, _ = await _connect(rs.port)
            await asyncio.sleep(0.05)
            rs.midi.sent.clear()
            w.write(_frame(0x1, b"not json"))
            w.write(_frame(0x1, b"\xff\xfe"))
            w.write(_frame(0x1, json.dumps({"id": "d1.cue", "v": 127}).encode(), fin=False)
                    + _frame(0x0, b"", fin=True))                                   # fragmented message
            await w.drain()
            await asyncio.sleep(0.15)
            self.assertEqual(rs.midi.sent[-1], bytes([0x90, P.BY_ID["d1.cue"]["num"], 127]))
            # an unmasked frame is a protocol error: this client is dropped, others still work
            w.write(bytes([0x81, 0x02]) + b"{}")
            await w.drain()
            self.assertEqual(await asyncio.wait_for(r.read(), 5), b"")
            r2, w2, head = await _connect(rs.port)
            self.assertIn("101", head.split("\r\n")[0])
            w2.close()

        with RunningServer() as rs:
            asyncio.run(scenario(rs))


class GeneratedMapping(unittest.TestCase):
    def test_committed_files_are_up_to_date(self):
        self.assertEqual(make_panel.main(["--check"]), 0)

    def test_xml_matches_protocol(self):
        doc = xml.dom.minidom.parse(str(make_panel.OUT_XML))
        keys = set()
        for c in doc.getElementsByTagName("control"):
            def text(tag):
                return c.getElementsByTagName(tag)[0].firstChild.data
            keys.add((int(text("status"), 16), int(text("midino"), 16)))
            self.assertEqual(text("key"), "DJSPanel.input")
            self.assertEqual(len(c.getElementsByTagName("script-binding")), 1)
        expected = set()
        for c in P.CONTROLS:
            st = P.midi_in_status(c)
            if st is not None:
                expected.add((st, c["num"]))
                if c["kind"] == "abs14":
                    expected.add((st, c["num"] + 32))
        self.assertEqual(keys, expected)
        self.assertEqual(len(doc.getElementsByTagName("control")), len(expected))     # no duplicates
        self.assertEqual(doc.getElementsByTagName("file")[0].getAttribute("functionprefix"), "DJSPanel")
        self.assertTrue((ROOT / "controllers" / doc.getElementsByTagName("file")[0].getAttribute("filename")).is_file())


class Cli(unittest.TestCase):
    def test_dry_run_starts_and_prints_urls(self):
        proc = subprocess.Popen([sys.executable, "-I", str(ROOT / "panel" / "server.py"), "--dry-run",
                                 "--host", "127.0.0.1", "--port", "0"], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
        lines = []

        def read():
            for _ in range(3):
                lines.append(proc.stdout.readline())

        t = threading.Thread(target=read, daemon=True)
        t.start()
        t.join(20)
        proc.terminate()
        proc.wait(10)
        out = "".join(lines)
        self.assertIn("DJS touch panel is running", out)
        self.assertIn("http://127.0.0.1:", out)
        self.assertNotIn(":0/", out)          # the real port is printed, not the requested 0

    def test_missing_midi_library_or_port_is_a_clear_error(self):
        r = subprocess.run([sys.executable, "-I", str(ROOT / "panel" / "server.py"), "--port", "0",
                            "--midi-port", "definitely-not-there"], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 1)
        self.assertTrue("python-rtmidi" in r.stderr or "not found" in r.stderr, r.stderr)


if __name__ == "__main__":
    unittest.main()
