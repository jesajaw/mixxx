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

## Setup (Linux)

```bash
make install       # once (see README): Mixxx >= 2.5, Python env, skin, mapping
make run           # panel + Mixxx together
```

1. **Mixxx, once:** Preferences > Controllers > `DJS Panel` > *Load Mapping* = **DJS Touch Panel** > tick *Enabled* > Apply.
   The device exists only while the panel server runs (it creates the virtual ALSA MIDI port "DJS Panel" itself), so
   `make run` starts the server first and Mixxx after it.
2. **On the tablet** (same Wi-Fi): open the address that `make run` prints, e.g. `http://192.168.1.20:8765/`, tap
   **FULLSCREEN**. On the PC that runs Mixxx itself: `http://localhost:8765/`.
3. The tablet only needs a browser. If it cannot connect, a firewall on the PC may block port 8765 (e.g. `sudo ufw allow 8765/tcp`
   from your local network only).

Without Mixxx or MIDI: `make dry-run` prints every MIDI message the panel would send. `python3 panel/server.py --list-ports`
shows the MIDI ports the server can see, `make midi-test` checks that the virtual port works (server <-> a second MIDI
client), `make doctor` checks the whole chain.

## One sound card only (no second output for headphones)

Mixxx's manual calls this the **"Computer Only"** setup. You hear everything through *one* stereo output. Cueing works
by switching what that output carries:

1. Mixxx > Preferences > **Sound Hardware** > *Output*: set **Headphones** to your sound card (channels 1-2).
   Leave **Main** empty. (Recording and streaming still use Mixxx's internal main mix.)
2. *Sound API* **ALSA** (or JACK if you use it), latency 20 ms or less if the sound stays clean.
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
  then `make skin` (copies the mapping into Mixxx) and re-select the mapping in Mixxx.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Server: `MIDI port "DJS Panel" not found` / ALSA error | No ALSA sequencer (`make doctor`): real Linux `sudo modprobe snd-seq`; WSL2 and containers have none. Or the name differs: `--list-ports`, `--midi-port NAME` |
| Panel says *waiting for Mixxx* | The mapping is not enabled in Mixxx, or Mixxx uses a different port. Start Mixxx with `--controller-debug` and check `mixxx.log` |
| Tablet cannot open the address | Same WiFi? Firewall prompt answered with *private networks*? Try `http://localhost:8765/` on the PC first |
| Buttons work, nothing lights up | The mapping is loaded but the output does not arrive: in Mixxx the controller must be *Enabled* for input **and** output (the same "DJS Panel" device) |
| Mixxx lists two "DJS Panel" devices (an input-only and an output-only one) | Then Mixxx did not pair the server's two virtual ALSA ports. Tell me what *Preferences > Controllers* and `aconnect -l` show; a single in/out ALSA client is the fix to build |
| Server prints `screen dropped: ...` | A screen stopped answering (tablet asleep, Wi-Fi lost). The server pings every 15 s and cuts a screen that is silent for 25 s or that does not read its data (64 KB backlog). The panel reconnects by itself and gets the full state again - nothing to fix |
| Linux: panel says *waiting for Mixxx* although the mapping is enabled | The server creates the virtual MIDI port, so start `panel/server.py` **before** Mixxx (or rescan controllers in Mixxx preferences) |

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
* **Not verified:** loading in a running Mixxx, real MIDI through ALSA/python-rtmidi into Mixxx (the test machine has no
  ALSA sequencer, no display and no MIDI hardware), and the feel of the jog on a real touchscreen. Expect to tune the numbers above.

## Protocol constants

All protocol numbers (7/14 bit full scale, centres, jog ticks per revolution, BPM scale, record speed ...) are defined once in `panel/protocol.py`. The Mixxx script gets them through `tools/make_panel.py`, the server imports them, and the browser UI loads them from `/protocol.json` before it builds the screen. `tests/test_panel.py` (*SingleSource*) fails if one of these numbers is hard-coded again in the UI, the script template or the server.
