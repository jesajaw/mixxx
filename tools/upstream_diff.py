#!/usr/bin/env python3
"""Shows exactly how this repo differs from upstream Mixxx (transparency tool).

Compares against the stable Mixxx branch (default: 2.5):
  * skins/StudioDeck/        vs  res/skins/LateNight/   (the rename "skins:LateNight" -> "skins:StudioDeck" is
                                                          normalized away; generated Studio files are summarized)
  * keyboard/Custom.kbd.cfg  vs  res/keyboard/de_DE.kbd.cfg

Usage:
  python3 tools/upstream_diff.py                      # shallow-clones mixxxdj/mixxx (branch 2.5) into a temp folder
  python3 tools/upstream_diff.py --upstream ~/mixxx   # use an existing Mixxx checkout instead
  python3 tools/upstream_diff.py --branch 2.6         # compare against another branch
  python3 tools/upstream_diff.py --full               # print every changed file's diff, not only skin.xml

Read-only: nothing in this repo or in the checkout is changed.
"""
import argparse
import difflib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_URL = "https://github.com/mixxxdj/mixxx.git"
SKIN_NAME, UPSTREAM_SKIN = "StudioDeck", "LateNight"
GENERATED = ("studio/", "style_studio.qss")  # produced by tools/make_scheme.py from PaleMoon


def _text(path):
    return path.read_text(encoding="utf8", errors="surrogateescape")


def _normalize(text):
    return text.replace(f"skins:{UPSTREAM_SKIN}", f"skins:{SKIN_NAME}")


def _files(base):
    return {p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()}


def compare_skin(upstream_skin, own_skin):
    """-> dict(added, removed, changed, generated); lists of relative paths."""
    up, own = _files(upstream_skin), _files(own_skin)
    generated = sorted(p for p in own if p.startswith(GENERATED))
    added = sorted(p for p in own - up if not p.startswith(GENERATED))
    removed = sorted(up - own)
    changed = []
    for rel in sorted(up & own):
        a, b = upstream_skin / rel, own_skin / rel
        if a.read_bytes() == b.read_bytes():
            continue
        try:
            if _normalize(_text(a)) == _text(b):
                continue
        except OSError:
            pass
        changed.append(rel)
    return {"added": added, "removed": removed, "changed": changed, "generated": generated}


def unified(upstream_file, own_file, label):
    a = _normalize(_text(upstream_file)).splitlines(keepends=True)
    b = _text(own_file).splitlines(keepends=True)
    return "".join(difflib.unified_diff(a, b, f"upstream/{label}", f"DJS/{label}", n=2))


def clone_upstream(branch, dest):
    subprocess.run(["git", "clone", "--quiet", "--depth", "1", "--branch", branch, UPSTREAM_URL, str(dest)], check=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--upstream", type=Path, help="existing Mixxx checkout (otherwise a shallow clone is made)")
    ap.add_argument("--branch", default="2.5", help="Mixxx branch to clone (default: 2.5)")
    ap.add_argument("--full", action="store_true", help="print the diff of every changed file")
    args = ap.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmp:
        if args.upstream:
            mixxx = args.upstream
        else:
            mixxx = Path(tmp) / "mixxx"
            print(f"Cloning {UPSTREAM_URL} (branch {args.branch}, shallow) ...")
            clone_upstream(args.branch, mixxx)
        up_skin = mixxx / "res" / "skins" / UPSTREAM_SKIN
        up_kbd = mixxx / "res" / "keyboard" / "de_DE.kbd.cfg"
        if not up_skin.is_dir() or not up_kbd.is_file():
            print(f"Not a Mixxx checkout: {mixxx}", file=sys.stderr)
            return 1

        print(f"\n== Skin: skins/{SKIN_NAME} vs res/skins/{UPSTREAM_SKIN} (rename normalized) ==")
        r = compare_skin(up_skin, ROOT / "skins" / SKIN_NAME)
        print(f"changed files : {len(r['changed'])}")
        for p in r["changed"]:
            print(f"   ~ {p}")
        print(f"added files   : {len(r['added'])}")
        for p in r["added"]:
            print(f"   + {p}")
        print(f"removed files : {len(r['removed'])}")
        for p in r["removed"]:
            print(f"   - {p}")
        print(f"generated     : {len(r['generated'])} files (studio/, style_studio.qss; tools/make_scheme.py)")
        shown = r["changed"] if args.full else [p for p in r["changed"] if p == "skin.xml"]
        for rel in shown:
            d = unified(up_skin / rel, ROOT / "skins" / SKIN_NAME / rel, f"skins/{rel}")
            print(f"\n--- diff: {rel} ---\n{d if len(d) < 6000 or args.full else d[:6000] + chr(10) + '... (truncated, use --full)'}")

        print("\n== Keyboard: keyboard/Custom.kbd.cfg vs res/keyboard/de_DE.kbd.cfg ==")
        d = unified(up_kbd, ROOT / "keyboard" / "Custom.kbd.cfg", "keyboard/de_DE.kbd.cfg")
        print(d if d else "identical")
    return 0


if __name__ == "__main__":
    sys.exit(main())
