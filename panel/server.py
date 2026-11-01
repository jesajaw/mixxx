#!/usr/bin/env python3
"""DJS touch panel server: browser touch UI  <->  virtual MIDI port  <->  Mixxx.

  pip install python-rtmidi          (only needed for real MIDI; --dry-run works without it)
  python3 panel/server.py            then open the printed address on the tablet / on this PC

Windows: create a loopMIDI port called "DJS Panel" first (https://www.tobias-erichsen.de/software/loopmidi.html).
Linux/macOS: the port is created automatically if it does not exist.
In Mixxx: Preferences > Controllers > "DJS Panel" > load mapping "DJS Touch Panel", enable.
Details: docs/PANEL.md.

Only the Python standard library is used for HTTP and WebSocket.
"""
import argparse
import asyncio
import base64
import hashlib
import json
import socket
import struct
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import protocol as P  # noqa: E402

WEB_DIR = Path(__file__).resolve().parent / "web"
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
MAX_HEAD = 16 * 1024
MAX_FRAME = 64 * 1024
DEFAULT_PORT_NAME = "DJS Panel"


# ------------------------------------------------------------------ WebSocket (RFC 6455, text frames only)

def ws_accept_key(client_key):
    return base64.b64encode(hashlib.sha1((client_key + WS_GUID).encode()).digest()).decode()


def ws_encode(opcode, payload=b""):
    """Server -> client frame (never masked)."""
    head = bytes([0x80 | opcode])
    n = len(payload)
    if n < 126:
        head += bytes([n])
    elif n < 65536:
        head += bytes([126]) + struct.pack(">H", n)
    else:
        head += bytes([127]) + struct.pack(">Q", n)
    return head + payload


async def ws_read(reader):
    """Reads one complete message -> (opcode, payload). Handles fragmentation; raises ValueError on garbage."""
    message, first_opcode = b"", None
    while True:
        b1, b2 = await reader.readexactly(2)
        fin, opcode = bool(b1 & 0x80), b1 & 0x0F
        if b1 & 0x70:
            raise ValueError("reserved bits set")
        if not b2 & 0x80:
            raise ValueError("client frames must be masked")
        n = b2 & 0x7F
        if n == 126:
            (n,) = struct.unpack(">H", await reader.readexactly(2))
        elif n == 127:
            (n,) = struct.unpack(">Q", await reader.readexactly(8))
        if n > MAX_FRAME or len(message) + n > MAX_FRAME:
            raise ValueError("frame too large")
        mask = await reader.readexactly(4)
        data = bytearray(await reader.readexactly(n))
        for i in range(n):
            data[i] ^= mask[i & 3]
        if opcode >= 0x8:                        # control frames are never fragmented
            if not fin or n > 125:
                raise ValueError("bad control frame")
            return opcode, bytes(data)
        if opcode != 0:
            first_opcode = opcode
        elif first_opcode is None:
            raise ValueError("unexpected continuation")
        message += bytes(data)
        if fin:
            return first_opcode, message


# ------------------------------------------------------------------ panel logic (no I/O)

class Panel:
    """Translates UI messages to MIDI and MIDI feedback to UI messages."""

    def __init__(self):
        self.state = {}                  # id -> last value reported by Mixxx
        self._note, self._cc7, self._msb, self._lsb = {}, {}, {}, {}
        for c in P.CONTROLS:
            st = P.midi_out_status(c)
            if st == P.NOTE_ON_OUT:
                self._note[c["num"]] = c["id"]
            elif st == P.CC_OUT and P.is_14bit(c):
                self._msb[c["num"]] = c["id"]
                self._lsb[c["num"] + 32] = c["id"]
            elif st == P.CC_OUT:
                self._cc7[c["num"]] = c["id"]
        self._pending_msb = {}

    @staticmethod
    def _clamp(v, lo, hi):
        return max(lo, min(hi, v))

    def from_ui(self, msg):
        """{"id": "d1.play", "v": 127} -> list of 3-byte MIDI messages (empty if the message is not valid)."""
        if not isinstance(msg, dict):
            return []
        c = P.BY_ID.get(msg.get("id"))
        v = msg.get("v")
        if c is None or isinstance(v, bool) or not isinstance(v, (int, float)):
            return []
        v = int(v)
        status = P.midi_in_status(c)
        if status is None:
            return []
        kind, num = c["kind"], c["num"]
        if kind == "button":
            return [bytes([status, num, 127 if v else 0])]
        if kind == "abs7":
            return [bytes([status, num, self._clamp(v, 0, 127)])]
        if kind == "abs14":
            v = self._clamp(v, 0, 16383)
            return [bytes([status, num, v >> 7]), bytes([status, num + 32, v & 0x7F])]
        if kind == "rel":
            v = self._clamp(v, -63, 63)
            return [bytes([status, num, 64 + v])] if v else []
        return []

    def from_midi(self, data):
        """Feedback from Mixxx (3 bytes) -> list of {"id", "v"} for the UI."""
        if len(data) != 3:
            return []
        status, d1, d2 = data
        out = []
        if status == P.NOTE_ON_OUT:
            cid = self._note.get(d1)
            if cid:
                out.append({"id": cid, "v": 127 if d2 else 0})
        elif status == P.CC_OUT:
            if d1 in self._cc7:
                out.append({"id": self._cc7[d1], "v": d2})
            elif d1 in self._msb:
                self._pending_msb[self._msb[d1]] = d2
            elif d1 in self._lsb:
                cid = self._lsb[d1]
                out.append({"id": cid, "v": (self._pending_msb.get(cid, 0) << 7) | d2})
        for m in out:
            self.state[m["id"]] = m["v"]
        return out

    def snapshot(self):
        return [{"id": k, "v": v} for k, v in self.state.items()]

    @staticmethod
    def request_state():
        """Asks Mixxx to resend everything (press + release of the request note)."""
        return [bytes([P.NOTE_ON_IN, P.REQUEST_NOTE, 127]), bytes([P.NOTE_ON_IN, P.REQUEST_NOTE, 0])]


# ------------------------------------------------------------------ MIDI ports

class NullPort:
    """--dry-run: nothing is sent, messages are only printed."""

    def __init__(self, on_message=None, verbose=True):
        self.verbose, self.sent = verbose, []

    def send(self, data):
        self.sent.append(bytes(data))
        if self.verbose:
            print("MIDI out:", " ".join(f"{b:02X}" for b in data))

    def close(self):
        pass


class RtMidiPort:
    """Both directions of one MIDI port (opened by name, or created virtual on Linux/macOS)."""

    def __init__(self, name, on_message, allow_virtual=True):
        try:
            import rtmidi
        except ImportError as e:
            raise RuntimeError("python-rtmidi is missing: pip install python-rtmidi   (or use --dry-run)") from e
        self.out, self.inp = rtmidi.MidiOut(), rtmidi.MidiIn()
        out_i = self._find(self.out, name)
        in_i = self._find(self.inp, name)
        if out_i is not None and in_i is not None:
            self.out.open_port(out_i)
            self.inp.open_port(in_i)
        elif allow_virtual and sys.platform != "win32":
            self.out.open_virtual_port(name)
            self.inp.open_virtual_port(name)
        else:
            ports = sorted(set(self.out.get_ports()) | set(self.inp.get_ports()))
            raise RuntimeError(
                f'MIDI port "{name}" not found. On Windows create it in loopMIDI (name: {name}). '
                f"Available ports: {ports or 'none'}")
        self.inp.ignore_types(sysex=True, timing=True, active_sense=True)
        self.inp.set_callback(lambda event, _=None: on_message(bytes(event[0])))

    @staticmethod
    def _find(midi, name):
        for i, p in enumerate(midi.get_ports()):
            if name.lower() in p.lower():
                return i
        return None

    def send(self, data):
        self.out.send_message(list(data))

    def close(self):
        for m in (self.inp, self.out):
            try:
                m.close_port()
            except Exception:  # noqa: BLE001
                pass


# ------------------------------------------------------------------ HTTP + WebSocket server

class Server:
    def __init__(self, port_factory, verbose=False):
        self.panel = Panel()
        self.clients = set()
        self.verbose = verbose
        self.loop = None
        self.midi = port_factory(self._midi_thread_callback)

    # MIDI input arrives on rtmidi's thread
    def _midi_thread_callback(self, data):
        if self.loop is not None:
            self.loop.call_soon_threadsafe(self.on_midi, data)

    def on_midi(self, data):
        for m in self.panel.from_midi(data):
            self.broadcast(m)

    def broadcast(self, msg):
        frame = ws_encode(0x1, json.dumps(msg, separators=(",", ":")).encode())
        for w in list(self.clients):
            try:
                w.write(frame)
            except Exception:  # noqa: BLE001
                self.clients.discard(w)

    def on_ui(self, msg):
        for data in self.panel.from_ui(msg):
            self.midi.send(data)

    async def handle(self, reader, writer):
        try:
            head = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 10)
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, asyncio.LimitOverrunError, ConnectionError):
            writer.close()
            return
        try:
            await self._serve(head, reader, writer)
        except (asyncio.IncompleteReadError, ConnectionError, ValueError):
            pass
        finally:
            self.clients.discard(writer)
            try:
                writer.close()
            except Exception:  # noqa: BLE001
                pass

    @staticmethod
    def _parse(head):
        lines = head.decode("latin-1").split("\r\n")
        parts = lines[0].split(" ")
        headers = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        return (parts[0], parts[1]) if len(parts) >= 2 else ("", ""), headers

    @staticmethod
    def _respond(writer, status, body=b"", ctype="text/plain; charset=utf-8", extra=""):
        writer.write(
            (f"HTTP/1.1 {status}\r\nContent-Type: {ctype}\r\nContent-Length: {len(body)}\r\n"
             "Cache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nConnection: close\r\n"
             f"{extra}\r\n").encode() + body)

    async def _serve(self, head, reader, writer):
        (method, target), headers = self._parse(head)
        path = urlsplit(target).path
        if path == "/ws" and headers.get("upgrade", "").lower() == "websocket":
            return await self._websocket(headers, reader, writer)
        if method not in ("GET", "HEAD"):
            return self._respond(writer, "405 Method Not Allowed")
        if path in ("/", "/index.html"):
            body = (WEB_DIR / "index.html").read_bytes()
            csp = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
                   "connect-src 'self' ws: wss:; img-src data:; base-uri 'none'; form-action 'none'")
            return self._respond(writer, "200 OK", b"" if method == "HEAD" else body, "text/html; charset=utf-8",
                                 f"Content-Security-Policy: {csp}\r\nReferrer-Policy: no-referrer\r\n")
        return self._respond(writer, "404 Not Found", b"not found\n")

    async def _websocket(self, headers, reader, writer):
        key = headers.get("sec-websocket-key")
        origin, host = headers.get("origin"), headers.get("host", "")
        # Only pages served by this server may control Mixxx (blocks other websites in the same browser).
        if not key or headers.get("sec-websocket-version") != "13" or (origin and urlsplit(origin).netloc != host):
            return self._respond(writer, "403 Forbidden", b"forbidden\n")
        writer.write(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                      f"Sec-WebSocket-Accept: {ws_accept_key(key)}\r\n\r\n").encode())
        self.clients.add(writer)
        for m in self.panel.snapshot():
            writer.write(ws_encode(0x1, json.dumps(m, separators=(",", ":")).encode()))
        for data in self.panel.request_state():          # a new screen gets the current state of Mixxx
            self.midi.send(data)
        await writer.drain()
        while True:
            opcode, payload = await ws_read(reader)
            if opcode == 0x1:
                try:
                    self.on_ui(json.loads(payload.decode("utf-8")))
                except (ValueError, UnicodeDecodeError):
                    pass
            elif opcode == 0x9:
                writer.write(ws_encode(0xA, payload))
            elif opcode == 0x8:
                writer.write(ws_encode(0x8, payload[:2]))
                await writer.drain()
                return
            await writer.drain()

    async def run(self, host, port, ready=None):
        self.loop = asyncio.get_running_loop()
        server = await asyncio.start_server(self.handle, host, port, limit=MAX_HEAD)
        if ready:
            ready(server)
        async with server:
            await server.serve_forever()


def local_addresses():
    """Best-effort list of this PC's LAN addresses (for the URL that is typed on the tablet)."""
    found = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))          # no packet is sent
        found.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        found.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass
    return sorted(a for a in found if not a.startswith("127."))


def main(argv=None):
    ap = argparse.ArgumentParser(description="DJS touch panel server")
    ap.add_argument("--host", default="0.0.0.0", help="address to listen on (default: all; use 127.0.0.1 for this PC only)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--midi-port", default=DEFAULT_PORT_NAME, help=f'MIDI port name (default: "{DEFAULT_PORT_NAME}")')
    ap.add_argument("--dry-run", action="store_true", help="do not open MIDI, only print what would be sent")
    ap.add_argument("--list-ports", action="store_true", help="list MIDI ports and exit")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(line_buffering=True)   # lines show up at once, also when redirected
    except (AttributeError, ValueError):
        pass

    if args.list_ports:
        try:
            import rtmidi
        except ImportError:
            print("python-rtmidi is missing: pip install python-rtmidi")
            return 1
        print("MIDI out:", rtmidi.MidiOut().get_ports())
        print("MIDI in :", rtmidi.MidiIn().get_ports())
        return 0

    if args.dry_run:
        factory = lambda cb: NullPort(cb)  # noqa: E731
    else:
        factory = lambda cb: RtMidiPort(args.midi_port, cb)  # noqa: E731
    try:
        server = Server(factory)
    except RuntimeError as e:
        print("ERROR:", e, file=sys.stderr)
        return 1

    def ready(srv):
        port = srv.sockets[0].getsockname()[1]
        print("DJS touch panel is running. Open on the tablet / this PC:")
        shown = ["127.0.0.1"] if args.host in ("127.0.0.1", "localhost") else ["localhost"] + local_addresses()
        for a in shown:
            print(f"   http://{a}:{port}/")
        if args.host == "0.0.0.0":
            print("Everyone in this network can open it. Use --host 127.0.0.1 to allow this PC only.")
        print("MIDI:", "dry run (nothing is sent)" if args.dry_run else f'port "{args.midi_port}"')

    try:
        asyncio.run(server.run(args.host, args.port, ready))
    except KeyboardInterrupt:
        pass
    finally:
        server.midi.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
