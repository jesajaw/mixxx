"""Selects the StudioDeck skin in Mixxx's settings (mixxx.cfg).

mixxx.cfg is Mixxx's own format:  [Group]  then  "Key Value"  lines (value = everything after the first space).
The keys ([Config] ResizableSkin / Scheme, group [ControllerPreset]) were checked against the strings of a Mixxx 2.4.0 binary.
Only the skin is touched. The controller is NOT pre-enabled: Mixxx names a virtual ALSA port with client numbers, which
cannot be predicted, so it is enabled once in Preferences > Controllers (Mixxx remembers it).

  prepare(data_dir)              fills in the skin only when no skin is set (a fresh Mixxx profile)
  prepare(data_dir, force=True)  sets it (make install does that); the old file is kept as mixxx.cfg.bak.<time>
"""
import os
import re
import shutil
import time
from pathlib import Path

SKIN = "StudioDeck"
SCHEME = "Studio"
MAPPING = "DJS-Touch-Panel.midi.xml"


def parse(text):
    groups = {}
    current = None
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        m = re.fullmatch(r"\[(.+)\]\s*", line)
        if m:
            current = m.group(1)
            groups.setdefault(current, {})
        elif current is not None and line.strip():
            key, _, value = line.partition(" ")
            groups[current][key] = value
    return groups


def render(groups):
    out = []
    for group, items in groups.items():
        out.append(f"[{group}]")
        out.extend(f"{k} {v}" for k, v in items.items())
        out.append("")
    return "\n".join(out)


def read(data_dir):
    cfg = Path(data_dir) / "mixxx.cfg"
    return parse(cfg.read_text(encoding="utf-8-sig", errors="replace")) if cfg.exists() else {}


def prepare(data_dir, force=False):
    """Returns what was changed (empty list = nothing to do)."""
    data_dir = Path(data_dir)
    cfg = data_dir / "mixxx.cfg"
    groups = read(data_dir)
    items = groups.setdefault("Config", {})
    changes = []
    for key, value in (("ResizableSkin", SKIN), ("Scheme", SCHEME)):
        if (force or key not in items) and items.get(key) != value:
            items[key] = value
            changes.append(f"{key} = {value}")
    if changes:
        data_dir.mkdir(parents=True, exist_ok=True)
        if cfg.exists():
            shutil.copy2(cfg, cfg.with_name(f"mixxx.cfg.bak.{time.strftime('%Y%m%d-%H%M%S')}"))
        tmp = cfg.with_name(cfg.name + ".tmp")
        tmp.write_text(render(groups), encoding="utf-8")
        os.replace(tmp, cfg)
    return changes


def controller_configured(data_dir):
    """True when Mixxx has a controller using our mapping (so the first-run hint can be skipped)."""
    return any(re.split(r"[\\/]", v)[-1].lower() == MAPPING.lower() for v in read(data_dir).get("ControllerPreset", {}).values())
