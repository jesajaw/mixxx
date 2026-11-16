"""What `make run` does: prepare Mixxx's settings, then run the panel server and Mixxx together (see server.py --launch)."""
import subprocess
from pathlib import Path

import mixxxcfg

FIRST_RUN_HINT = """First start: in Mixxx open Preferences > Controllers, pick the "DJS Panel" device (it only exists while this
panel runs), load the mapping "DJS Touch Panel" and tick Enabled. Mixxx remembers it. Skin: Preferences > Interface > StudioDeck."""


def prepare(install, say=print):
    """Fills in the skin for a fresh Mixxx profile; says what is still to do by hand."""
    data = Path(install.data_dir)
    for change in mixxxcfg.prepare(data):
        say(f"Mixxx settings: {change}")
    if not mixxxcfg.controller_configured(data):
        say(FIRST_RUN_HINT)


def start_mixxx(install, spawn=subprocess.Popen):
    return spawn(install.command)
