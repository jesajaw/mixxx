"""Mixxx detection, install plans, doctor, MIDI self-test and the Makefile - all with fake system calls (no root, no Mixxx)."""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "panel"))
sys.path.insert(0, str(ROOT / "tools"))

import mixxxcfg  # noqa: E402
import mixxxenv as E  # noqa: E402
import studio as S  # noqa: E402

UBUNTU = {"ID": "ubuntu", "ID_LIKE": "debian"}
MINT = {"ID": "linuxmint", "ID_LIKE": "ubuntu debian"}
DEBIAN = {"ID": "debian"}
FEDORA = {"ID": "fedora"}
ARCH = {"ID": "arch"}


def res(rc=0, out=""):
    return SimpleNamespace(returncode=rc, stdout=out)


class Versions(unittest.TestCase):
    def test_parse_real_package_versions(self):
        self.assertEqual(E.parse_version("2.5.6-0ubuntu1~noble1"), (2, 5, 6))
        self.assertEqual(E.parse_version("2.4.0+dfsg-2build4"), (2, 4, 0))
        self.assertEqual(E.parse_version("1:2.5.0-1"), (2, 5, 0))
        self.assertEqual(E.parse_version("2.5"), (2, 5, 0))
        self.assertIsNone(E.parse_version("n/a"))

    def test_min_version_file_is_read(self):
        self.assertGreaterEqual(E.read_min_version(ROOT), (2, 5, 0))

    def test_os_release_is_parsed_with_quotes(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "os-release"
            f.write_text('NAME="Linux Mint"\nID=linuxmint\nID_LIKE="ubuntu debian"\n# comment\n')
            self.assertEqual(E.read_os_release(f)["ID_LIKE"], "ubuntu debian")
        self.assertEqual(E.read_os_release("/nonexistent"), {})


class InstallPlans(unittest.TestCase):
    def test_ubuntu_and_mint_use_the_official_ppa(self):
        for osr in (UBUNTU, MINT):
            plan = E.mixxx_plan(osr, ["sudo"])
            flat = [" ".join(c) for c in plan]
            self.assertIn("sudo add-apt-repository -y ppa:mixxx/mixxx", flat)
            self.assertEqual(flat[-1], "sudo apt-get install -y mixxx")
            self.assertLess(flat.index("sudo add-apt-repository -y ppa:mixxx/mixxx"), len(flat) - 2)    # an update follows the PPA
            self.assertIn("sudo apt-get install -y software-properties-common", flat)

    def test_other_distributions_use_flatpak_installing_it_first_when_needed(self):
        flat = [" ".join(c) for c in E.mixxx_plan(DEBIAN, [], have_flatpak=False)]
        self.assertEqual(flat[0], "apt-get install -y flatpak")
        self.assertIn("flatpak install --user -y flathub org.mixxx.Mixxx", flat)
        self.assertEqual([" ".join(c) for c in E.mixxx_plan(FEDORA, [], False)][0], "dnf install -y flatpak")
        self.assertEqual([" ".join(c) for c in E.mixxx_plan(ARCH, [], False)][0], "pacman -S --needed --noconfirm flatpak")
        have = E.mixxx_plan(DEBIAN, [], have_flatpak=True)
        self.assertEqual(have[0][:2], ["flatpak", "remote-add"])                  # no package install when flatpak exists

    def test_flathub_remote_is_added_for_the_user_not_system_wide(self):
        remote = next(c for c in E.mixxx_plan(FEDORA, [], True) if c[1] == "remote-add")
        self.assertIn("--user", remote)
        self.assertIn("--if-not-exists", remote)

    def test_unknown_distribution_gets_an_explanation_instead_of_a_wrong_command(self):
        with self.assertRaises(E.MixxxMissing) as e:
            E.mixxx_plan({"ID": "weirdos"}, [], False)
        self.assertIn("flatpak.org", str(e.exception))
        with self.assertRaises(E.MixxxMissing):
            E.deps_plan({"ID": "weirdos"}, [])

    def test_deps_per_family_and_build_extras(self):
        flat = lambda plan: " ".join(" ".join(c) for c in plan)  # noqa: E731
        d = flat(E.deps_plan(UBUNTU, ["sudo"]))
        for pkg in ("python3-venv", "python3-pip", "alsa-utils"):
            self.assertIn(pkg, d)
        self.assertNotIn("libasound2-dev", d)
        build = flat(E.deps_plan(UBUNTU, [], build=True))
        for pkg in ("build-essential", "pkg-config", "python3-dev", "libasound2-dev"):      # what the python-rtmidi build needs
            self.assertIn(pkg, build)
        self.assertIn("alsa-lib-devel", flat(E.deps_plan(FEDORA, [], build=True)))
        self.assertIn("python-pip", flat(E.deps_plan(ARCH, [])))

    def test_sudo_is_skipped_for_root(self):
        self.assertEqual(E.sudo_prefix(0), [])
        self.assertEqual(E.sudo_prefix(1000), ["sudo"])


class Detect(unittest.TestCase):
    def fake(self, native=None, flatpak_info=None, versions=None):
        which = lambda n: {"mixxx": native, "dpkg-query": "/usr/bin/dpkg-query",  # noqa: E731
                           "flatpak": "/usr/bin/flatpak" if flatpak_info is not None else None}.get(n)

        def run(cmd, **kw):
            if cmd[:2] == ["flatpak", "info"]:
                return res(0 if flatpak_info else 1, f"Version: {flatpak_info}\n" if flatpak_info else "")
            if cmd[0] == "dpkg-query":
                return res(0 if native else 1, (versions or {}).get("native", ""))
            return res(1)

        return which, run

    def test_native_install_uses_the_default_profile_folder(self):
        which, run = self.fake(native="/usr/bin/mixxx")
        inst = E.detect({}, which, run, home="/home/dj")
        self.assertEqual((inst.kind, inst.command, inst.data_dir), ("native", ["/usr/bin/mixxx"], Path("/home/dj/.mixxx")))

    def test_flatpak_uses_its_own_data_folder_and_run_command(self):
        which, run = self.fake(flatpak_info="2.5.6")
        inst = E.detect({}, which, run, home="/home/dj")
        self.assertEqual(inst.command, ["flatpak", "run", "org.mixxx.Mixxx"])
        self.assertEqual(inst.data_dir, Path("/home/dj/.var/app/org.mixxx.Mixxx/data/mixxx"))

    def test_nothing_installed_says_make_install(self):
        which, run = self.fake()
        with self.assertRaises(E.MixxxMissing) as e:
            E.detect({}, which, run, home="/h")
        self.assertIn("make install", str(e.exception))

    def test_old_native_loses_against_a_new_enough_flatpak_but_not_otherwise(self):
        which, run = self.fake(native="/usr/bin/mixxx", flatpak_info="2.5.6", versions={"native": "2.4.0+dfsg"})
        self.assertEqual(E.detect({}, which, run, home="/h", minimum=(2, 5, 0)).kind, "flatpak")
        self.assertEqual(E.detect({}, which, run, home="/h").kind, "native")                        # no minimum asked
        which, run = self.fake(native="/usr/bin/mixxx", flatpak_info="2.5.6", versions={"native": "2.5.2-0ubuntu1"})
        self.assertEqual(E.detect({}, which, run, home="/h", minimum=(2, 5, 0)).kind, "native")

    def test_explicit_choice_and_overrides_win(self):
        which, run = self.fake(native="/usr/bin/mixxx", flatpak_info="2.5.6")
        self.assertEqual(E.detect({"MIXXX": "flatpak"}, which, run, home="/h").kind, "flatpak")
        inst = E.detect({"MIXXX_DATA": "/tmp/profile"}, which, run, home="/h")
        self.assertEqual(inst.command, ["/usr/bin/mixxx", "--settings-path", "/tmp/profile"])
        self.assertEqual(inst.data_dir, Path("/tmp/profile"))
        custom = E.detect({"MIXXX_BIN": "/opt/mixxx/bin/mixxx"}, which, run, home="/h")
        self.assertEqual((custom.kind, custom.command), ("custom", ["/opt/mixxx/bin/mixxx"]))

    def test_installed_version_from_the_package_managers(self):
        run = lambda cmd, **kw: res(0, "Version: 2.5.6\n") if cmd[0] == "flatpak" else res(0, "2.5.2-0ubuntu1~noble1")  # noqa: E731
        self.assertEqual(E.installed_version("flatpak", lambda n: None, run), (2, 5, 6))
        self.assertEqual(E.installed_version("native", lambda n: "/usr/bin/dpkg-query" if n == "dpkg-query" else None, run), (2, 5, 2))
        self.assertIsNone(E.installed_version("native", lambda n: None, run))


class Doctor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.data = self.home / ".mixxx"

    def run_doctor(self, version="2.5.6-1", display="x11", seq=True, rtmidi=(True, "ok"), installed=True, files=True, platform="linux"):
        if files:
            for f in S.SKIN_FILES + S.MAPPING_FILES:
                (self.data / f).parent.mkdir(parents=True, exist_ok=True)
                (self.data / f).write_text("x")
        which = lambda n: {"mixxx": "/usr/bin/mixxx", "dpkg-query": "/usr/bin/dpkg-query"}.get(n) if installed else None  # noqa: E731
        run = lambda cmd, **kw: res(0, version)  # noqa: E731
        env = {"DISPLAY": ":0"} if display == "x11" else ({"WAYLAND_DISPLAY": "w"} if display == "wayland" else {})
        checks = S.doctor_checks(ROOT, env, which, run, exists=lambda p: seq if str(p) == "/dev/snd/seq" else Path(p).exists(),
                                 probe=lambda: rtmidi, platform=platform, home=self.home)
        return {c.name: c for c in checks}

    def test_everything_in_place_means_no_failures(self):
        c = self.run_doctor()
        self.assertFalse([x for x in c.values() if x.status == "fail"])
        self.assertEqual(c["Mixxx"].detail, "2.5.6 (native)")

    def test_old_mixxx_is_a_failure_with_the_fix(self):
        c = self.run_doctor(version="2.4.0+dfsg")
        self.assertEqual(c["Mixxx"].status, "fail")
        self.assertIn("make mixxx", c["Mixxx"].hint)

    def test_missing_mixxx_points_to_make_mixxx(self):
        c = self.run_doctor(installed=False)
        self.assertEqual((c["Mixxx"].status, c["Mixxx"].hint), ("fail", "make mixxx"))
        self.assertNotIn("skin + mapping", c)

    def test_no_display_and_no_alsa_are_explained_like_the_wsl_case(self):
        c = self.run_doctor(display=None, seq=False)
        self.assertEqual(c["display"].status, "fail")
        self.assertIn("WSLg", c["display"].hint)
        self.assertEqual(c["ALSA MIDI"].status, "fail")
        self.assertIn("WSL2", c["ALSA MIDI"].hint)
        self.assertNotIn("python-rtmidi", c)                      # only probed when there is a sequencer

    def test_wayland_counts_as_a_display(self):
        self.assertEqual(self.run_doctor(display="wayland")["display"].status, "ok")

    def test_rtmidi_failure_is_reported(self):
        c = self.run_doctor(rtmidi=(False, "cannot create"))
        self.assertEqual((c["python-rtmidi"].status, c["python-rtmidi"].hint), ("fail", "make venv"))

    def test_missing_skin_files_are_listed_with_make_skin(self):
        c = self.run_doctor(files=False)
        self.assertEqual(c["skin + mapping"].status, "fail")
        self.assertIn("skin.xml", c["skin + mapping"].detail)
        self.assertEqual(c["skin + mapping"].hint, "make skin")

    def test_an_outdated_installed_skin_is_a_failure_with_the_fix(self):
        for f in S.SKIN_FILES + S.MAPPING_FILES:
            (self.data / f).parent.mkdir(parents=True, exist_ok=True)
            (self.data / f).write_text("x")
        (self.data / "skins" / "StudioDeck" / "skin.xml").write_text('<Template src="skins:StudioDeck/decks/deck.xml"/>')
        c = self.run_doctor(files=False)
        self.assertEqual(c["skin files"].status, "fail")
        self.assertIn("make skin", c["skin files"].hint)
        (self.data / "skins" / "StudioDeck" / "skin.xml").write_text('<Template src="skin:decks/deck.xml"/>')
        self.assertEqual(self.run_doctor(files=False)["skin files"].status, "ok")

    def test_skin_selection_and_controller_are_warnings_not_failures(self):
        c = self.run_doctor()
        self.assertEqual((c["skin selected"].status, c["controller"].status), ("warn", "warn"))
        (self.data / "mixxx.cfg").write_text("[Config]\nResizableSkin StudioDeck\n\n[ControllerPreset]\nd /x/" + mixxxcfg.MAPPING + "\n")
        c = self.run_doctor()
        self.assertEqual((c["skin selected"].status, c["controller"].status), ("ok", "ok"))

    def test_other_systems_fail_the_first_check(self):
        self.assertEqual(self.run_doctor(platform="win32")["system"].status, "fail")

    def test_output_and_exit_code(self):
        said = []
        self.assertEqual(S.print_checks([S.Check("a", "ok", "fine"), S.Check("b", "warn", "meh", "do x")], said.append), 0)
        self.assertIn("         -> do x", said)
        said.clear()
        self.assertEqual(S.print_checks([S.Check("a", "fail", "bad", "fix it")], said.append), 1)
        self.assertIn("[FAIL] a: bad", said)


class InstallCommands(unittest.TestCase):
    def test_commands_run_in_order_and_a_failure_stops_the_rest(self):
        seen, said = [], []

        def run(cmd, **kw):
            seen.append(cmd)
            return res(1 if cmd == ["b"] else 0)

        self.assertEqual(S.run_plan([["a"], ["b"], ["c"]], False, run, said.append), 1)
        self.assertEqual(seen, [["a"], ["b"]])
        self.assertTrue(any("failed" in m for m in said))

    def test_dry_run_prints_but_runs_nothing(self):
        said = []
        self.assertEqual(S.run_plan([["sudo", "apt-get", "install", "x"]], True, lambda *a, **k: self.fail("ran"), said.append), 0)
        self.assertEqual(said, ["+ sudo apt-get install x"])

    def test_mixxx_install_is_skipped_when_a_new_enough_mixxx_exists(self):
        said = []
        inst = E.Install("native", ["/usr/bin/mixxx"], Path("/h/.mixxx"))
        with mock.patch.object(E, "detect", return_value=inst), mock.patch.object(E, "installed_version", return_value=(2, 5, 6)):
            rc = S.cmd_mixxx_install(SimpleNamespace(force=False, dry_run=False), run=lambda *a, **k: self.fail("installed again"), say=said.append)
        self.assertEqual(rc, 0)
        self.assertIn("already installed", said[0])

    def test_force_installs_anyway(self):
        said = []
        with mock.patch.object(E, "read_os_release", return_value=UBUNTU), mock.patch.object(E, "sudo_prefix", return_value=[]):
            rc = S.cmd_mixxx_install(SimpleNamespace(force=True, dry_run=True), say=said.append)
        self.assertEqual(rc, 0)
        self.assertIn("+ add-apt-repository -y ppa:mixxx/mixxx", said)

    def test_configure_refuses_while_mixxx_is_running(self):
        said = []
        inst = E.Install("native", ["m"], Path("/nonexistent/profile"))
        with mock.patch.object(E, "detect", return_value=inst):
            rc = S.cmd_configure(run=lambda cmd, **kw: res(0), which=lambda n: "/usr/bin/pgrep", say=said.append)
        self.assertEqual(rc, 1)
        self.assertIn("Close it first", said[0])


class FakeRtMidi:
    """Just enough of python-rtmidi for the server's virtual port and a second client (in memory)."""

    def __init__(self, hide_ports=False):
        self.readable, self.writable, self.hide = {}, {}, hide_ports
        outer = self

        class MidiOut:
            def __init__(s):
                s.virtual = s.target = None

            def get_ports(s):
                return [] if outer.hide else [f"{n} 128:0" for n in outer.writable]

            def open_virtual_port(s, name):
                s.virtual = name
                outer.readable.setdefault(name, [])

            def open_port(s, i):
                s.target = list(outer.writable)[i]

            def send_message(s, data):
                if s.virtual:
                    for cb in outer.readable[s.virtual]:
                        cb((list(data), 0.0), None)
                else:
                    outer.writable[s.target]((list(data), 0.0), None)

            def close_port(s):
                pass

        class MidiIn:
            def __init__(s):
                s.virtual = s.source = None

            def get_ports(s):
                return [] if outer.hide else [f"{n} 129:0" for n in outer.readable]

            def open_virtual_port(s, name):
                s.virtual = name
                outer.writable[name] = lambda ev, _=None: None

            def open_port(s, i):
                s.source = list(outer.readable)[i]

            def ignore_types(s, **kw):
                pass

            def set_callback(s, cb):
                if s.virtual:
                    outer.writable[s.virtual] = cb
                else:
                    outer.readable[s.source].append(cb)

            def close_port(s):
                pass

        self.MidiOut, self.MidiIn = MidiOut, MidiIn


class MidiSelftest(unittest.TestCase):
    def go(self, fake):
        t = [0.0]
        with mock.patch.dict(sys.modules, {"rtmidi": fake}):
            import server
            return S.midi_selftest(rtmidi=fake, port_cls=server.RtMidiPort, timeout=1, sleep=lambda s: t.__setitem__(0, t[0] + s),
                                   clock=lambda: t[0])

    def test_server_port_and_a_second_client_talk_in_both_directions(self):
        results = self.go(FakeRtMidi())
        self.assertEqual(len(results), 3)
        self.assertTrue(all(ok for _, ok in results), results)

    def test_a_port_that_other_programs_cannot_see_fails_the_first_check_and_stops(self):
        results = self.go(FakeRtMidi(hide_ports=True))
        self.assertEqual([ok for _, ok in results], [False])

    def test_cli_reports_failure_when_alsa_is_missing(self):
        said = []
        with mock.patch.object(S, "midi_selftest", side_effect=RuntimeError("no ALSA")):
            self.assertEqual(S.cmd_midi_test(said.append), 1)
        self.assertIn("make doctor", " ".join(said))


@unittest.skipUnless(shutil.which("make"), "make is not installed")
class Makefile(unittest.TestCase):
    def make(self, *args):
        flags = [] if "-n" in args else ["-s"]                     # -s would also silence the commands that -n prints
        return subprocess.run(["make", *flags, *args], cwd=ROOT, capture_output=True, text=True, timeout=60)

    def test_install_runs_the_steps_in_order(self):
        out = self.make("-n", "-B", "install").stdout           # -B: independent of an already existing .venv
        order = [out.index(s) for s in ("studio.py deps", "studio.py mixxx-install", "-m venv", "install/install.sh", "studio.py configure")]
        self.assertEqual(order, sorted(order))

    def test_every_target_is_documented_in_help(self):
        text = (ROOT / "Makefile").read_text().replace("\\\n", " ")
        phony = re.search(r"^\.PHONY:(.*?)(?=\n\S)", text, re.S | re.M).group(1).split()
        helped = set(re.findall(r"make (\S+)", self.make("help").stdout))
        self.assertFalse(set(phony) - helped, f"not in make help: {sorted(set(phony) - helped)}")

    def test_run_passes_extra_arguments_and_needs_the_python_env(self):
        out = self.make("-n", "-B", "run", "ARGS=--dry-run").stdout
        self.assertIn("panel/server.py --launch --dry-run", out)
        self.assertIn(".venv", out)

    def test_venv_falls_back_to_a_source_build_by_itself(self):
        out = self.make("-n", "-B", "venv").stdout
        wheel_only = out.index("--only-binary=:all:")
        self.assertLess(wheel_only, out.index("studio.py deps --build"))                     # build tools only when no wheel exists
        self.assertLess(out.index("studio.py deps --build"), out.rindex("pip install -r requirements.txt"))
        self.assertIn("rm -rf .venv", out)                                                   # a failed build leaves no half venv

    def test_dry_run_target_needs_no_python_env(self):
        self.assertNotIn("-m venv", self.make("-n", "dry-run").stdout)

    def test_no_windows_leftovers_in_the_makefile(self):
        self.assertNotRegex((ROOT / "Makefile").read_text().lower(), r"windows|\.bat|loopmidi|powershell")


if __name__ == "__main__":
    unittest.main()
