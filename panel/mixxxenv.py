"""Where Mixxx is and how to start it (Linux): native package or Flatpak; plus how to install it per distribution.

Pure functions with injectable system calls, so that tests/test_studio.py checks the logic without Mixxx or root.
Sources (mixxx.org/download): Ubuntu/Mint -> official PPA ppa:mixxx/mixxx (the distribution's own package is old);
every other distribution -> Flatpak org.mixxx.Mixxx from Flathub.
"""
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

FLATPAK_ID = "org.mixxx.Mixxx"
PPA = "ppa:mixxx/mixxx"
FLATHUB = "https://dl.flathub.org/repo/flathub.flatpakrepo"


class MixxxMissing(RuntimeError):
    pass


@dataclass
class Install:
    kind: str                                   # "native" | "flatpak" | "custom"
    command: list = field(default_factory=list)
    data_dir: Path = None


def parse_version(text):
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text or "")
    return tuple(int(x or 0) for x in m.groups()) if m else None


def read_min_version(root):
    p = Path(root) / "MIXXX_MIN_VERSION"
    return parse_version(p.read_text()) if p.exists() else (2, 5, 0)


def read_os_release(path="/etc/os-release"):
    info = {}
    try:
        for line in Path(path).read_text().splitlines():
            k, sep, v = line.partition("=")
            if sep:
                info[k.strip()] = v.strip().strip('"')
    except OSError:
        pass
    return info


def _ids(osr):
    return {osr.get("ID", "")} | set(osr.get("ID_LIKE", "").split())


def ubuntu_like(osr):
    return "ubuntu" in _ids(osr)


def family(osr):
    ids = _ids(osr)
    for name, members in (("debian", {"debian", "ubuntu"}), ("fedora", {"fedora", "rhel", "centos"}),
                          ("arch", {"arch"}), ("suse", {"suse", "opensuse", "opensuse-leap", "opensuse-tumbleweed"})):
        if ids & members:
            return name
    return None


def sudo_prefix(euid=None):
    euid = os.geteuid() if euid is None else euid
    return [] if euid == 0 else ["sudo"]


def flatpak_data_dir(home):
    return Path(home) / ".var" / "app" / FLATPAK_ID / "data" / "mixxx"


def installed_version(kind, which=shutil.which, run=subprocess.run):
    """Version tuple of the installed Mixxx or None (package manager first, no GUI start needed)."""
    try:
        if kind == "flatpak":
            r = run(["flatpak", "info", FLATPAK_ID], capture_output=True, text=True)
            m = re.search(r"^\s*Version:\s*(\S+)", r.stdout or "", re.M)
            return parse_version(m.group(1)) if m else None
        if which("dpkg-query"):
            r = run(["dpkg-query", "-W", "-f=${Version}", "mixxx"], capture_output=True, text=True)
            return parse_version(r.stdout) if r.returncode == 0 else None
        if which("rpm"):
            r = run(["rpm", "-q", "--qf", "%{VERSION}", "mixxx"], capture_output=True, text=True)
            return parse_version(r.stdout) if r.returncode == 0 else None
        if which("pacman"):
            r = run(["pacman", "-Q", "mixxx"], capture_output=True, text=True)
            return parse_version(r.stdout.split()[-1]) if r.returncode == 0 and r.stdout.split() else None
    except OSError:
        pass
    return None


def detect(env=None, which=shutil.which, run=subprocess.run, home=None, minimum=None):
    """The Mixxx to use. MIXXX=native|flatpak picks one when both exist; MIXXX_BIN / MIXXX_DATA override the program / settings folder."""
    env = os.environ if env is None else env
    home = Path(home) if home else Path.home()
    data_override = env.get("MIXXX_DATA")

    def with_data(cmd, default):
        return (cmd + ["--settings-path", data_override]) if data_override else cmd, Path(data_override or default)

    if env.get("MIXXX_BIN"):
        cmd, data = with_data([env["MIXXX_BIN"]], home / ".mixxx")
        return Install("custom", cmd, data)
    native = which("mixxx")
    has_flatpak = False
    if which("flatpak"):
        try:
            has_flatpak = run(["flatpak", "info", FLATPAK_ID], capture_output=True, text=True).returncode == 0
        except OSError:
            has_flatpak = False
    prefer = env.get("MIXXX")
    kind = prefer if prefer in ("native", "flatpak") else ("native" if native else "flatpak" if has_flatpak else None)
    if prefer not in ("native", "flatpak") and native and has_flatpak and minimum:
        old_native = (installed_version("native", which, run) or (0,)) < minimum          # e.g. the distribution's 2.4.0
        if old_native and (installed_version("flatpak", which, run) or (0,)) >= minimum:
            kind = "flatpak"
    if kind == "native" and native:
        cmd, data = with_data([native], home / ".mixxx")
    elif kind == "flatpak" and has_flatpak:
        cmd, data = with_data(["flatpak", "run", FLATPAK_ID], flatpak_data_dir(home))
    else:
        raise MixxxMissing("Mixxx is not installed (or MIXXX=%s is not available). Run:  make install" % (prefer or "auto"))
    return Install(kind, cmd, data)


def mixxx_plan(osr, sudo, have_flatpak=False):
    """Commands that install Mixxx (>= 2.5) on this distribution."""
    if ubuntu_like(osr):
        return [sudo + ["apt-get", "update"],
                sudo + ["apt-get", "install", "-y", "software-properties-common"],
                sudo + ["add-apt-repository", "-y", PPA],
                sudo + ["apt-get", "update"],
                sudo + ["apt-get", "install", "-y", "mixxx"]]
    plan = []
    if not have_flatpak:
        fam = family(osr)
        install = {"debian": ["apt-get", "install", "-y", "flatpak"], "fedora": ["dnf", "install", "-y", "flatpak"],
                   "arch": ["pacman", "-S", "--needed", "--noconfirm", "flatpak"],
                   "suse": ["zypper", "--non-interactive", "install", "flatpak"]}.get(fam)
        if not install:
            raise MixxxMissing("Cannot tell how to install Flatpak on this distribution: see https://flatpak.org/setup/ , then run make mixxx again")
        plan.append(sudo + install)
    plan.append(["flatpak", "remote-add", "--user", "--if-not-exists", "flathub", FLATHUB])
    plan.append(["flatpak", "install", "--user", "-y", "flathub", FLATPAK_ID])
    return plan


def deps_plan(osr, sudo, build=False):
    """System packages the Python side needs (venv, pip, ALSA tools); build=True adds what compiling python-rtmidi needs."""
    fam = family(osr)
    if fam == "debian":
        pkgs = ["python3-venv", "python3-pip", "alsa-utils"] + (["build-essential", "pkg-config", "python3-dev", "libasound2-dev"] if build else [])
        return [sudo + ["apt-get", "update"], sudo + ["apt-get", "install", "-y"] + pkgs]
    if fam == "fedora":
        pkgs = ["python3-pip", "alsa-utils"] + (["gcc-c++", "pkgconf-pkg-config", "python3-devel", "alsa-lib-devel"] if build else [])
        return [sudo + ["dnf", "install", "-y"] + pkgs]
    if fam == "arch":
        pkgs = ["python-pip", "alsa-utils"] + (["base-devel", "alsa-lib"] if build else [])
        return [sudo + ["pacman", "-S", "--needed", "--noconfirm"] + pkgs]
    if fam == "suse":
        pkgs = ["python3-pip", "alsa-utils"] + (["gcc-c++", "pkg-config", "python3-devel", "alsa-devel"] if build else [])
        return [sudo + ["zypper", "--non-interactive", "install"] + pkgs]
    raise MixxxMissing("Unknown distribution: install Python 3 with venv/pip and alsa-utils yourself, then run make venv")
