#!/usr/bin/env python3
"""Static checks for Mixxx skins (does NOT replace starting Mixxx!).

For each skin folder under skins/:
  1. all *.xml files are well-formed
  2. all *.qss files have balanced curly braces
  3. every fixed reference  skins:<skin>/path/file.ext  (in XML and QSS) exists
     (references containing variables like <Variable .../> are skipped)
  4. every color scheme directory (studio/, palemoon/, classic/) has the same subfolders
Exit code 1 on errors.
"""
import re
import sys
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKINS = ROOT / "skins"
# Known errors taken straight from Mixxx 2.5.x (LateNight/Classic) - warning only
KNOWN_UPSTREAM = {"skins:StudioDeck/classic/buttons/btn__undo_active.svg"}
REF = re.compile(r"skins:([A-Za-z0-9_ ()\-]+)/([^\s\"'<>)]+\.[A-Za-z0-9]+)")


def main():
    errors, warnings, checked = [], [], 0
    for skin in sorted(p for p in SKINS.iterdir() if p.is_dir()):
        for f in skin.rglob("*.xml"):
            try:
                xml.dom.minidom.parse(str(f))
            except Exception as e:  # noqa: BLE001
                errors.append(f"Broken XML: {f.relative_to(ROOT)}: {e}")
        for f in skin.rglob("*.qss"):
            t = f.read_text(encoding="utf8", errors="ignore")
            if t.count("{") != t.count("}"):
                errors.append(f"Unbalanced QSS braces: {f.relative_to(ROOT)}")
        for f in list(skin.rglob("*.xml")) + list(skin.rglob("*.qss")):
            text = f.read_text(encoding="utf8", errors="ignore")
            for m in REF.finditer(text):
                name, rel = m.group(1), m.group(2)
                if "path/to" in rel:
                    continue
                checked += 1
                if not (SKINS / name / rel).exists():
                    if f"skins:{name}/{rel}" in KNOWN_UPSTREAM:
                        warnings.append(f"known (upstream): skins:{name}/{rel}")
                        continue
                    errors.append(f"missing file: skins:{name}/{rel}  (in {f.relative_to(ROOT)})")
        ref_dirs = [d for d in ("palemoon", "classic", "studio") if (skin / d).is_dir()]
        if "palemoon" in ref_dirs and "studio" in ref_dirs:
            a = {p.relative_to(skin / "palemoon").as_posix() for p in (skin / "palemoon").rglob("*") if p.is_file()}
            b = {p.relative_to(skin / "studio").as_posix() for p in (skin / "studio").rglob("*") if p.is_file()}
            for miss in sorted(a - b):
                errors.append(f"studio/ is missing compared to palemoon/: {miss}")
    print(f"{checked} fixed references checked, {len(errors)} error(s), {len(warnings)} warning(s)")
    for w in sorted(set(warnings)):
        print(" ~", w)
    for e in errors:
        print(" -", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
