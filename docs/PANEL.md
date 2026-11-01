# Touch panel: a DJ controller made of software

Mixxx is only the DJ engine; normally a hardware controller (jog wheels, faders, pads) and an audio interface with a
second output for headphones sit around it. The **DJS touch panel** replaces the controller: a web page with two decks,
jog wheels, EQ, crossfader, hotcues, loops and library buttons that you operate on a tablet or touchscreen
(several fingers at once, like real hardware). Your computer's normal sound card is enough.

```
tablet / Surface (browser)  --WiFi-->  panel/server.py  --virtual MIDI port "DJS Panel"-->  Mixxx
        touch                          (on the PC with Mixxx)                      (mapping "DJS Touch Panel")
        <-- play LEDs, VU, BPM, position, fader positions -- (Mixxx answers on the same port) --
```

## Setup (Windows, once)

1. **Python 3** for Windows (python.org or Microsoft Store), then in a normal terminal (not WSL):
   `pip install python-rtmidi`
2. **loopMIDI** (free, https://www.tobias-erichsen.de/software/loopmidi.html): create **one port called `DJS Panel`** and
   leave loopMIDI running (it can start with Windows). Windows has no built-in virtual MIDI cable; this is it.
3. **Install the mapping into Mixxx:** `install\install.bat` (copies `controllers/DJS-Touch-Panel*` to Mixxx).
4. **Mixxx:** Preferences > Controllers > `DJS Panel` > *Load Mapping* = **DJS Touch Panel** > tick *Enabled* > Apply.
5. **Start the panel:** `python panel\server.py` (or `make panel`). Windows asks once whether Python may use the network:
   allow *private networks*. The window prints the addresses, e.g. `http://192.168.1.20:8765/`.
6. **On the tablet** (same WiFi): open that address, tap **FULLSCREEN**. On the Surface that runs Mixxx itself:
   `http://localhost:8765/`.

Linux/macOS: the MIDI port is created automatically (`pip install python-rtmidi`, then `python3 panel/server.py`);
Mixxx then lists a controller named `DJS Panel`.

Check without Mixxx or MIDI: `python3 panel/server.py --dry-run` prints every MIDI message the panel would send.
`python3 panel/server.py --list-ports` shows the MIDI ports the server can see.

## One sound card only (no second output for headphones)

Mixxx's manual calls this the **"Computer Only"** setup. You hear everything through *one* stereo output. Cueing works
by switching what that output carries:

1. Mixxx > Preferences > **Sound Hardware** > *Output*: set **Headphones** to your sound card (channels 1-2).
   Leave **Main** empty. (Recording and streaming still use Mixxx's internal main mix.)
2. *Sound API* **Windows WASAPI**, latency 20 ms or less if the sound stays clean.
3. On the panel the knob **CUE/MAIN** decides what you hear: left = only the cue (the deck(s) with **HEAD** lit),
   right = only the main mix, middle = both. Normal playing: knob right. To pre-listen a track: turn it left (or middle),
   press **HEAD** on that deck.

Limits (they come from having one output, not from the panel): you cannot play the main mix for an audience and
pre-listen at the same time. For that you need a second output: a USB sound card or USB headphones (~10 EUR) as
*Headphones* while the built-in output stays *Main*. Nothing in the panel changes then; CUE/MAIN just becomes the
usual cue mix.

## Using it

| Area | What |
|---|---|
| Deck (left/right) | Jog wheel: **finger on the platter = scratch**, **finger on the outer ring = pitch nudge**. Fader right of it = pitch (up = faster, double-tap = back to 0.0 %; `+`/`-` = temporary bend). **CUE** (hold), **PLAY**, **SYNC**, **HEAD** (pre-listen), **KEY** (key lock), 4 hotcue pads, loop **IN/OUT/LOOP**, **4** = 4-beat loop, **1/2**, **x2** |
| Mixer (middle) | Per channel: GAIN, FILTER, HI/MID/LO, level meter, channel fader. Top: MAIN, CUE/MAIN, PHONES. Bottom: crossfader. Double-tap an EQ/filter knob = back to center |
| Bottom bar | **LOAD 1/2** loads the selected library row, **UP/DOWN** and the **BROWSE** strip (drag up/down) move through the library, **AUTO DJ** on/off, **FADE** (fade now), **SKIP** |
| SHIFT (top) | Latching. While on, a hotcue pad **deletes** its cue instead of jumping to it |

Everything the panel shows comes from Mixxx: if you move a fader with the mouse in Mixxx, the panel follows. A second
tablet shows the same state.

## Tuning (if the feel is not right)

The mapping was verified against a mock of Mixxx's scripting API, not against a running Mixxx (see below). Values that
depend on taste or hardware:

* Jog sensitivity: `JOG_TICKS_PER_REV` (`panel/protocol.py`, default 1024) and the nudge `scale` of `dN.nudge`.
* Knob drag length: `/ 160` in `knob()` in `panel/web/index.html`.
* After editing `panel/protocol.py` or `panel/mapping.template.js`: `python3 tools/make_panel.py` (or `make mapping`),
  then reinstall (`install\install.bat`) and re-select the mapping in Mixxx.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Server: `MIDI port "DJS Panel" not found` | loopMIDI is not running or the port has another name (`--list-ports`, or `--midi-port NAME`) |
| Panel says *waiting for Mixxx* | The mapping is not enabled in Mixxx, or Mixxx uses a different port. Start Mixxx with `--controller-debug` and check `mixxx.log` |
| Tablet cannot open the address | Same WiFi? Firewall prompt answered with *private networks*? Try `http://localhost:8765/` on the PC first |
| Buttons work, nothing lights up | The mapping is loaded but the output does not arrive: in Mixxx the controller must be *Enabled* for input **and** output (same loopMIDI port) |
| Server in WSL | Use Windows Python instead. WSL cannot see Windows MIDI ports |

## Security

By default the server listens on the whole local network (`--host 0.0.0.0`) so the tablet can reach it; anybody in that
network can then press your buttons. Use `--host 127.0.0.1` if Mixxx and the screen are the same PC. Web pages from
other sites cannot control it (the WebSocket checks the page origin).

## Protocol (for hackers)

`panel/protocol.py` is the single source: every control with its MIDI number and the Mixxx control it drives.
Panel to Mixxx uses MIDI channel 1, Mixxx to panel channel 2 (so a loopback port never feeds Mixxx its own echo).
`tools/make_panel.py` generates `controllers/DJS-Touch-Panel.midi.xml` and `-scripts.js` from it; `make check` fails if
they are out of date.

## What is verified

* The Mixxx script runs against a mock of Mixxx's API (14 tests: buttons, toggles, hotcue+shift, 14-bit pitch, jog,
  feedback, polling, shutdown) and the mutation of the script makes the tests fail.
* All control names used exist in the Mixxx 2.5 source.
* The server (HTTP, WebSocket, origin check, malformed input) and the UI in Chromium with real multi-touch (two fingers
  at once, jog, 14-bit fader, shift, feedback display) have automated tests.
* **Not verified:** loading in a running Mixxx, real MIDI through loopMIDI/python-rtmidi (no Windows, no Mixxx and no
  MIDI hardware here), and the feel of the jog on a real touchscreen. Expect to tune the numbers above.
