# controllers

* `DJS-Touch-Panel.midi.xml` + `DJS-Touch-Panel-scripts.js` - the mapping of the touch panel (see `docs/PANEL.md`).
  **Generated** by `python3 tools/make_panel.py` from `panel/protocol.py`; do not edit by hand.
* Put your own MIDI/HID mappings (XML + JavaScript) here once you have hardware. `install/install.sh`
  (`install\install.bat` on Windows) copies every `*.xml` / `*.js` here to `<Mixxx data folder>/controllers/`,
  where Mixxx picks them up. You can also copy them there manually.

Steps for a new mapping:
1. Start Mixxx with `--controller-debug` and move the controls -> the MIDI messages show up in the log.
2. Use a template from the Mixxx wiki ("MIDI Scripting"): a file pair `My-Controller.midi.xml` + `My-Controller-scripts.js`.
3. Put the files here and commit.
