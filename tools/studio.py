#!/usr/bin/env python3
"""Helper behind the Makefile (Linux). Use it through make:  make help

  doctor                 checks everything Mixxx + the panel need and says what to do about each problem
  data-dir               prints Mixxx's settings folder (native ~/.mixxx or the Flatpak one)
  deps [--build]         installs the system packages for the Python side (venv, pip, ALSA tools)
  mixxx-install          installs Mixxx >= MIXXX_MIN_VERSION: official PPA on Ubuntu/Mint, otherwise Flatpak
  configure              selects the StudioDeck skin in Mixxx's settings (Mixxx must be closed)
  midi-test              self-test of the virtual MIDI port (server <-> a second MIDI client)

mixxx-install and deps take --dry-run (only print the commands).
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "panel"))
import mixxxcfg  # noqa: E402
import mixxxenv  # noqa: E402

SKIN_FILES = ("skins/StudioDeck/skin.xml",)
MAPPING_FILES = ("controllers/DJS-Touch-Panel.midi.xml", "controllers/DJS-Touch-Panel-scripts.js")


@dataclass
class Check:
    name: str
    status: str            # "ok" | "warn" | "fail"
    detail: str
    hint: str = ""


def probe_rtmidi():
    """(ok, detail): can python-rtmidi create a virtual ALSA port here?"""
    try:
        import rtmidi
    except ImportError:
        return False, "python-rtmidi is not installed in this Python (run: make venv, and use make doctor)"
    try:
        out = rtmidi.MidiOut()
        out.open_virtual_port("DJS Panel doctor")
        out.close_port()
        return True, "python-rtmidi can create a virtual MIDI port"
    except Exception as e:  # noqa: BLE001
        return False, f"python-rtmidi cannot create a virtual MIDI port: {e}"


def read_skin_xml(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def doctor_checks(root=ROOT, env=None, which=shutil.which, run=subprocess.run, exists=os.path.exists, probe=probe_rtmidi,
                  platform=sys.platform, home=None, read=read_skin_xml):
    env = os.environ if env is None else env
    checks = []
    add = lambda *a: checks.append(Check(*a))  # noqa: E731

    add("system", "ok" if platform.startswith("linux") else "fail",
        "Linux" if platform.startswith("linux") else f"{platform}: this setup is for Linux only")

    minimum = mixxxenv.read_min_version(root)
    wanted = ".".join(map(str, minimum))
    inst = None
    try:
        inst = mixxxenv.detect(env, which, run, home, minimum)
    except mixxxenv.MixxxMissing:
        add("Mixxx", "fail", "not installed", "make mixxx")
    if inst:
        if inst.kind == "custom":
            add("Mixxx", "ok", f"custom program ({inst.command[0]})")
        else:
            ver = mixxxenv.installed_version(inst.kind, which, run)
            shown = ".".join(map(str, ver)) if ver else "?"
            if ver is None:
                add("Mixxx", "warn", f"{inst.kind} install, version unknown")
            elif ver >= minimum:
                add("Mixxx", "ok", f"{shown} ({inst.kind})")
            else:
                add("Mixxx", "fail", f"{shown} ({inst.kind}) is older than {wanted}: the skin is for Mixxx 2.5.x",
                    "make mixxx   (adds the official PPA / Flatpak)")

    add("display", "ok" if (env.get("DISPLAY") or env.get("WAYLAND_DISPLAY")) else "fail",
        "graphical session found" if (env.get("DISPLAY") or env.get("WAYLAND_DISPLAY")) else
        "no DISPLAY / WAYLAND_DISPLAY: Mixxx cannot open its window",
        "" if (env.get("DISPLAY") or env.get("WAYLAND_DISPLAY")) else "run this in a desktop session (not plain SSH; on WSL you need WSLg)")

    seq = exists("/dev/snd/seq")
    add("ALSA MIDI", "ok" if seq else "fail", "/dev/snd/seq exists" if seq else "no ALSA sequencer (/dev/snd/seq): the panel cannot create its MIDI port",
        "" if seq else "real Linux: sudo modprobe snd-seq.  WSL2 and containers usually have no ALSA MIDI at all")
    if seq:
        ok, detail = probe()
        add("python-rtmidi", "ok" if ok else "fail", detail, "" if ok else "make venv")

    if inst:
        data = Path(inst.data_dir)
        missing = [f for f in SKIN_FILES + MAPPING_FILES if not exists(data / f)]
        add("skin + mapping", "ok" if not missing else "fail", f"installed in {data}" if not missing else f"missing in {data}: {', '.join(missing)}",
            "" if not missing else "make skin")
        if not missing and "skins:" + mixxxcfg.SKIN + "/" in read(data / "skins" / mixxxcfg.SKIN / "skin.xml"):
            add("skin files", "fail", "the installed skin is outdated: it calls itself skins:StudioDeck/, which Mixxx cannot resolve for a "
                "skin in the user folder (the skin then shows empty, log: 'Could not open template file')",
                "update this repo, then: make skin")
        elif not missing:
            add("skin files", "ok", "up to date")
        cfg = mixxxcfg.read(data)
        skin = cfg.get("Config", {}).get("ResizableSkin")
        add("skin selected", "ok" if skin == mixxxcfg.SKIN else "warn", f"skin is {skin or 'not set yet'}",
            "" if skin == mixxxcfg.SKIN else "make configure  (with Mixxx closed)")
        ok = mixxxcfg.controller_configured(data)
        add("controller", "ok" if ok else "warn", "mapping enabled in Mixxx" if ok else "not enabled in Mixxx yet",
            "" if ok else "once: make run, then Mixxx > Preferences > Controllers > DJS Panel > mapping DJS Touch Panel > Enabled")
    return checks


def print_checks(checks, say=print):
    mark = {"ok": "[ ok ]", "warn": "[warn]", "fail": "[FAIL]"}
    for c in checks:
        say(f"{mark[c.status]} {c.name}: {c.detail}")
        if c.hint:
            say(f"         -> {c.hint}")
    bad = [c for c in checks if c.status == "fail"]
    say("\nEverything needed is in place." if not bad and not any(c.status == "warn" for c in checks) else
        ("\n%d problem(s) to fix." % len(bad) if bad else "\nReady, with notes above."))
    return 1 if bad else 0


def run_plan(plan, dry_run=False, run=subprocess.run, say=print):
    for cmd in plan:
        say("+ " + " ".join(cmd))
        if dry_run:
            continue
        if run(cmd).returncode:
            say(f"ERROR: command failed: {' '.join(cmd)}")
            return 1
    return 0


def cmd_mixxx_install(args, root=ROOT, run=subprocess.run, which=shutil.which, say=print):
    minimum = mixxxenv.read_min_version(root)
    if not args.force:
        try:
            inst = mixxxenv.detect(minimum=minimum)
            ver = mixxxenv.installed_version(inst.kind) if inst.kind != "custom" else minimum
            if ver and ver >= minimum:
                say(f"Mixxx {'.'.join(map(str, ver))} ({inst.kind}) is already installed - nothing to do")
                return 0
        except mixxxenv.MixxxMissing:
            pass
    try:
        plan = mixxxenv.mixxx_plan(mixxxenv.read_os_release(), mixxxenv.sudo_prefix(), bool(which("flatpak")))
    except mixxxenv.MixxxMissing as e:
        say(f"ERROR: {e}")
        return 1
    rc = run_plan(plan, args.dry_run, run, say)
    if rc == 0 and not args.dry_run:
        inst = mixxxenv.detect(minimum=minimum)
        ver = mixxxenv.installed_version(inst.kind)
        say(f"Mixxx {'.'.join(map(str, ver)) if ver else '(version unknown)'} installed ({inst.kind})")
    return rc


def cmd_deps(args, run=subprocess.run, say=print):
    try:
        plan = mixxxenv.deps_plan(mixxxenv.read_os_release(), mixxxenv.sudo_prefix(), args.build)
    except mixxxenv.MixxxMissing as e:
        say(f"ERROR: {e}")
        return 1
    return run_plan(plan, args.dry_run, run, say)


def cmd_configure(run=subprocess.run, which=shutil.which, say=print):
    inst = mixxxenv.detect(minimum=mixxxenv.read_min_version(ROOT))
    if which("pgrep") and run(["pgrep", "-x", "mixxx"], capture_output=True).returncode == 0:
        say("ERROR: Mixxx is running. Close it first - it would overwrite the settings when it quits.")
        return 1
    changes = mixxxcfg.prepare(inst.data_dir, force=True)
    say(("Mixxx settings: " + "; ".join(changes)) if changes else "Mixxx already uses the StudioDeck skin")
    return 0


def midi_selftest(rtmidi=None, port_cls=None, name="DJS Panel selftest", timeout=3.0, sleep=time.sleep, clock=time.monotonic):
    """The server's virtual port against a second MIDI client: [(what, ok), ...]. Needs a working ALSA sequencer."""
    if rtmidi is None:
        import rtmidi
    if port_cls is None:
        import server
        port_cls = server.RtMidiPort
    from_panel_ui, from_mixxx = [], []
    port = port_cls(name, from_panel_ui.append)                  # creates the virtual port, like `make run` does
    results = []
    try:
        cli_out, cli_in = rtmidi.MidiOut(), rtmidi.MidiIn()

        def find(m):
            return next((i for i, p in enumerate(m.get_ports()) if name.lower() in p.lower()), None)

        i_out, i_in = find(cli_out), find(cli_in)
        results.append(("the port is visible to other programs (as a MIDI output and input)", i_out is not None and i_in is not None))
        if i_out is None or i_in is None:
            return results
        cli_out.open_port(i_out)
        cli_in.open_port(i_in)
        cli_in.set_callback(lambda event, _=None: from_mixxx.append(bytes(event[0])))

        def wait(box, want):
            end = clock() + timeout
            while clock() < end:
                if want in box:
                    return True
                sleep(0.02)
            return want in box

        cli_out.send_message([0xB0, 10, 99])                     # "Mixxx -> panel"  direction of the feedback
        results.append(("data sent to the port reaches the server", wait(from_panel_ui, bytes([0xB0, 10, 99]))))
        port.send([0xB1, 11, 55])                                # "panel -> Mixxx"
        results.append(("data sent by the server reaches other programs", wait(from_mixxx, bytes([0xB1, 11, 55]))))
        for m in (cli_out, cli_in):
            m.close_port()
    finally:
        port.close()
    return results


def cmd_midi_test(say=print):
    try:
        results = midi_selftest()
    except Exception as e:  # noqa: BLE001
        say(f"ERROR: the MIDI self-test could not run: {e}\n  (no ALSA sequencer? run: make doctor)")
        return 1
    for what, ok in results:
        say(f"[ {'ok' if ok else 'FAIL'} ] {what}")
    good = bool(results) and all(ok for _, ok in results)
    say("\nThe virtual MIDI port works. (Whether Mixxx lists it as ONE controller is checked in Mixxx: make run, Preferences > Controllers.)"
        if good else "\nThe virtual MIDI port does not work here: make doctor")
    return 0 if good else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    sub.add_parser("data-dir")
    sub.add_parser("configure")
    sub.add_parser("midi-test")
    d = sub.add_parser("deps")
    d.add_argument("--build", action="store_true", help="also compilers and ALSA headers (only if no prebuilt python-rtmidi exists)")
    d.add_argument("--dry-run", action="store_true")
    m = sub.add_parser("mixxx-install")
    m.add_argument("--dry-run", action="store_true")
    m.add_argument("--force", action="store_true", help="run the installation even if a new enough Mixxx exists")
    args = ap.parse_args(argv)

    if args.cmd == "doctor":
        return print_checks(doctor_checks())
    if args.cmd == "data-dir":
        try:
            print(mixxxenv.detect(minimum=mixxxenv.read_min_version(ROOT)).data_dir)
            return 0
        except mixxxenv.MixxxMissing as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
    if args.cmd == "configure":
        return cmd_configure()
    if args.cmd == "midi-test":
        return cmd_midi_test()
    if args.cmd == "deps":
        return cmd_deps(args)
    return cmd_mixxx_install(args)


if __name__ == "__main__":
    sys.exit(main())
