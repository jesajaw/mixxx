# mixxx-dj-studio

Personal setup for **[Mixxx](https://mixxx.org) 2.5.x** (see [git/Mixxx](https://github.com/mixxxdj/mixxx)): a **touch-screen DJ panel** (virtual controller for tablets, so a computer with one sound card is enough), custom skin, keyboard layout, system-audio routing for Spotify/SoundCloud, a download helper for SoundCloud tracks with downloads enabled, and library tools.

Mixxx provides the complete DJ engine (decks, EQ, crossfader, loops, cues, sync, effects, recording); this repo adds everything personal around it.

## Quick start (Linux)

```bash
git clone <your-repo> && cd mixxx-dj-studio
make install      # once: system packages (asks for sudo), Mixxx >= 2.5, Python env, skin, settings
make run          # every day: touch panel + Mixxx in one command; closing Mixxx stops the panel
make doctor       # anything wrong? it checks everything and says what to do about each problem
```

`make help` lists all targets. What `make install` does, in this order: `deps` (venv, pip, ALSA tools), `mixxx` (Mixxx >= 2.5:
the official PPA `ppa:mixxx/mixxx` on Ubuntu/Mint, otherwise the Flatpak from Flathub; skipped if a new enough Mixxx exists),
`venv` (`.venv` with python-rtmidi), `skin` (skin, controller mapping and keyboard layout into Mixxx's settings folder),
`configure` (selects the StudioDeck skin, with Mixxx closed; the old `mixxx.cfg` is kept as `.bak`).

**Once, in Mixxx** (it cannot be done from outside): `make run`, then *Preferences -> Controllers -> DJS Panel* -> mapping
**DJS Touch Panel** -> tick *Enabled*. Mixxx remembers it. The device exists only while the panel runs. On the tablet (same
Wi-Fi) open the address that `make run` prints and tap FULLSCREEN (details: `docs/PANEL.md`).

Overrides (environment variables): `MIXXX=native|flatpak` (if both exist), `MIXXX_BIN=/path/to/mixxx`,
`MIXXX_DATA=<settings folder>` (passed as `--settings-path`), `PY=python3.12`, `VENV=.venv`. Undo: `make uninstall`.

### If something does not work

Run `make doctor` first. It prints one line per check and the command that fixes it.

| Symptom | Cause / fix |
|---|---|
| `doctor`: *no DISPLAY / WAYLAND_DISPLAY* | Mixxx needs a graphical session. Plain SSH has none; on WSL you need WSLg (Windows 11 or a current WSL). |
| `doctor`: *no ALSA sequencer (/dev/snd/seq)* | The panel creates a virtual ALSA MIDI port and needs the kernel's sequencer: real Linux `sudo modprobe snd-seq`. WSL2 and containers usually have **no** ALSA MIDI at all, so the panel cannot work there. |
| `doctor`: *Mixxx is older than 2.5* | `make mixxx`. Ubuntu's own package is 2.4.0; the skin is derived from 2.5.x. |
| `make venv` prints *no prebuilt python-rtmidi* | Normal for new Pythons (3.13+; the project has wheels only up to 3.12): it installs compilers and ALSA headers (sudo) and builds python-rtmidi itself, which takes about a minute. If that fails, the messages above name the missing header or tool. |
| Skin installed but not listed | Check the Mixxx version (`make doctor`). Flatpak: the skin is copied (a symlink would be invisible in the sandbox); data folder `~/.var/app/org.mixxx.Mixxx/data/mixxx`. |
| Wrong data folder | `make doctor` shows it; override with `MIXXX_DATA=<folder>`. |
| `make configure` says Mixxx is running | Close Mixxx first, it would overwrite the settings when it quits. |
| `Permission denied` on `install/install.sh` | Run it as `bash install/install.sh` (the make targets do). |

If it still fails, send the output of `make doctor` and, if Mixxx starts but shows the wrong skin, `~/.mixxx/mixxx.log`.

## Contents

| Path | What |
|---|---|
| `Makefile`, `tools/studio.py` | the one entry point: install, run, doctor, tests (`make help`); the helper behind it |
| `skins/StudioDeck/` | LateNight derivative with the *Studio* color scheme, Mic/Aux rack visible by default -> `docs/SKIN.md` |
| `keyboard/Custom.kbd.cfg` | German Mixxx layout + extra keys (below) |
| `audio-routing/` | Spotify/SoundCloud as an Aux channel via a virtual audio device (Linux script, Spotify Connect service) |
| `tools/fetch_tracks.py` | SoundCloud links (only with downloads enabled / your own tracks) -> files with tags & cover |
| `tools/mixxx_library.py` | Read the library: statistics, tracks without BPM, export crates/playlists as M3U8 |
| `tools/make_scheme.py`, `palette.json` | generates the Studio scheme from PaleMoon; palette is changeable in one place |
| `tools/validate_skin.py` | static skin checks (XML, QSS, file references) |
| `tools/upstream_diff.py` | shows exactly how this repo differs from upstream Mixxx (skin, keyboard) |
| `panel/` | **touch panel**: `server.py` (browser <-> virtual MIDI), `web/index.html` (the touch UI), `protocol.py` (all controls) -> `docs/PANEL.md` |
| `controllers/` | generated Mixxx mapping of the panel (`DJS-Touch-Panel*`); place for your own MIDI/HID mappings |
| `tools/make_panel.py` | generates that mapping from `panel/protocol.py` (`--check` in `make check`) |
| `docs/PANEL.md` | panel setup, one-sound-card setup, usage, tuning, troubleshooting |
| `docs/DOWNLOAD-FOLDER.md` | one shared music folder for SoundCloud, your Spotify app and purchases |
| `docs/SOURCES.md` | what works and what does not with Spotify/SoundCloud (API, system audio, alternatives) |

## Spotify & SoundCloud - in short

* **System audio**: app/browser -> virtual device -> Mixxx *Auxiliary 1*. Works, but without waveform, BPM,
  sync, loops. Linux: `audio-routing/linux/dj-stream.sh up && ./dj-stream.sh move spotify`.
* **SoundCloud downloads**: `python3 tools/fetch_tracks.py <soundcloud-link>` for tracks you are allowed to save.
* **APIs**: Spotify provides no audio (and, since 2024/2026, less metadata); the SoundCloud API requires an
  Artist Pro subscription to register an app, according to the developer site. Details and alternatives: `docs/SOURCES.md`.

## Keyboard: extra keys (in addition to the German Mixxx default)

| Key | Action |
|---|---|
| `Shift+W` / `Shift+E` | Deck 1 filter (quick effect) left / right |
| `Shift+I` / `Shift+O` | Deck 2 filter left / right |
| `Shift+B` / `Shift+N` | Deck 1 / Deck 2 mid kill (low kill stays `B` / `N`) |
| `Shift+T` | Auxiliary 1 to headphones (PFL) |

Mnemonic: Shift + the loop-halve/loop-double key = filter left/right. Everything else matches Mixxx's
`de_DE.kbd.cfg` (play `D`/`L`, cue `F`/`Ö`, crossfader `G`/`H`, hotcues, loops ...). Full list: `keyboard/Custom.kbd.cfg`.

## Development

```bash
make validate     # skin checks
make test         # unit tests of the Python tools
make scheme       # regenerate the Studio scheme after a palette change
make upstream-diff # what differs from Mixxx? (clones upstream 2.5 shallow, read-only)
make mapping      # regenerate controllers/DJS-Touch-Panel* after editing panel/protocol.py
make panel        # start the touch panel server (make panel-dry: without MIDI)
make check        # scheme + validate + test + "no uncommitted generated changes"
```

## Transparency: what differs from Mixxx?

No fork needed. This repo is the whole personal layer, and Mixxx itself stays unmodified (install it from the official
sources). `make upstream-diff` compares the repo with upstream Mixxx 2.5 (stable) and prints every difference:
the skin differs from LateNight in **one file** (`skin.xml`) plus the generated Studio files; the keyboard layout
differs from `de_DE.kbd.cfg` by 9 added lines.

## Honest test status

**Tested (automatically, `make check`):** the Mixxx script against a mock of the Mixxx API (Node), server + WebSocket tests,
UI tests in Chromium with simulated multi-touch, the skin (XML, QSS, 1046 file references, the Studio scheme regenerates
identically), `install.sh`, and the Makefile flow: distribution detection (Ubuntu/Mint -> PPA, others -> Flatpak), the
install commands per distribution, Mixxx detection (native / Flatpak / overrides), `make doctor` with fake systems, the MIDI
self-test against an in-memory MIDI fake, and `make run` with a stand-in for Mixxx (starts it with the right arguments, ends
the panel when Mixxx ends).

**Run for real in an Ubuntu 24.04 container (no display, no sound, no MIDI):** `make venv`, `make skin`, `make configure`,
`make doctor` (it correctly reported the old Mixxx 2.4.0, the missing display and the missing ALSA sequencer), `make run`
with a stand-in for Mixxx, and Mixxx 2.4.0 starting headless.

**Skin in a real Mixxx:** loaded in Mixxx 2.4.0 under a virtual display (screenshot checked: decks, mixer, effects, samplers,
library). That found a real bug (the skin addressed itself as `skins:StudioDeck/`, which Mixxx does not resolve for a user skin; see
`docs/SKIN.md`). On 2.4.0 the log still shows ~47 warnings about tooltip IDs: those exist only in 2.5, so they are expected there.

**Not tested:** the PPA / Flatpak installation itself (no access to them from the test machine), the skin in a
running Mixxx 2.5.x (your 2.5.6 will tell), **real ALSA MIDI between the panel and Mixxx** (including whether Mixxx lists the panel's virtual port
as one controller: run `make midi-test` for the port itself, then check *Preferences -> Controllers*), the feel of the jog
on a real touchscreen, and the system-audio chain with real hardware. `dj-stream.sh` and the tools are tested against
stand-ins (fake `pactl`, a test database in the Mixxx schema). Errors on first start are written to `~/.mixxx/mixxx.log`.

## Licenses

Own code and docs: MIT (`LICENSE`). The skin is a derivative of LateNight and is under
**CC BY-SA 3.0**; the keyboard layout derives from Mixxx (**GPL-2.0-or-later**). Details: `NOTICE.md`.
