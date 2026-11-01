# mixxx-dj-studio

Personal setup for **[Mixxx](https://mixxx.org) 2.5.x** (see [git/Mixxx](https://github.com/mixxxdj/mixxx)): a **touch-screen DJ panel** (virtual controller for tablets, so a computer with one sound card is enough), custom skin, keyboard layout, system-audio routing for Spotify/SoundCloud, a download helper for SoundCloud tracks with downloads enabled, and library tools.

Mixxx provides the complete DJ engine (decks, EQ, crossfader, loops, cues, sync, effects, recording); this repo adds everything personal around it.

## Quick start

```bash
# Linux / macOS
git clone <your-repo> && cd mixxx-dj-studio
bash install/install.sh            # link the skin + keyboard layout (backs up an existing one)
```
```bat
:: Windows: double-click install\install.bat, or from a terminal:
install\install.bat
:: equivalent: powershell -NoProfile -ExecutionPolicy Bypass -File install\install.ps1
```

Then in Mixxx: *Preferences -> Interface -> Skin = **StudioDeck**, Color scheme = **Studio***; restart Mixxx
(keyboard layout). To undo: `bash install/install.sh --uninstall` or `install\install.bat -Uninstall`.

### If the install does not work

| Symptom | Cause / fix |
|---|---|
| `Permission denied` on `install/install.sh` | Run it as `bash install/install.sh`. (The executable bit was missing in older commits; fixed now.) |
| Windows: "running scripts is disabled on this system" | Use `install\install.bat` (it bypasses the execution policy for that one run). |
| Windows: junction error | The script falls back to copying the skin automatically. You can also force it: `install\install.bat -Copy`. |
| Skin installed but not listed in Mixxx | Check `mixxx --version`. The skin is derived from Mixxx **2.5.x**; distribution packages are often older (Ubuntu 24.04 ships 2.4.0). Use the official Mixxx PPA, Flatpak or installer. |
| Flatpak Mixxx | The installer detects it and copies the skin (a symlink would be invisible inside the sandbox). Data folder: `~/.var/app/org.mixxx.Mixxx/data/mixxx`. |
| Wrong data folder | Pass it explicitly: `--data-dir <folder>` (Linux/macOS) or `-DataDir <folder>` (Windows). The installer prints the folder it uses. |

If it still fails, send the full installer output and, if Mixxx starts but shows the wrong skin, `~/.mixxx/mixxx.log`
(Windows: `%LOCALAPPDATA%\Mixxx\mixxx.log`).

## Contents

| Path | What |
|---|---|
| `skins/StudioDeck/` | LateNight derivative with the *Studio* color scheme, Mic/Aux rack visible by default -> `docs/SKIN.md` |
| `keyboard/Custom.kbd.cfg` | German Mixxx layout + extra keys (below) |
| `audio-routing/` | Spotify/SoundCloud as an Aux channel via a virtual audio device (Linux script, Windows guide, Spotify Connect service) |
| `tools/fetch_tracks.py` | SoundCloud links (only with downloads enabled / your own tracks) -> files with tags & cover |
| `tools/mixxx_library.py` | Read the library: statistics, tracks without BPM, export crates/playlists as M3U8 |
| `tools/make_scheme.py`, `palette.json` | generates the Studio scheme from PaleMoon; palette is changeable in one place |
| `tools/validate_skin.py` | static skin checks (XML, QSS, file references) |
| `tools/upstream_diff.py` | shows exactly how this repo differs from upstream Mixxx (skin, keyboard) |
| `panel/` | **touch panel**: `server.py` (browser <-> virtual MIDI), `web/index.html` (the touch UI), `protocol.py` (all controls) -> `docs/PANEL.md` |
| `controllers/` | generated Mixxx mapping of the panel (`DJS-Touch-Panel*`); place for your own MIDI/HID mappings |
| `tools/make_panel.py` | generates that mapping from `panel/protocol.py` (`--check` in `make check`) |
| `docs/PANEL.md` | panel setup (Windows/loopMIDI), one-sound-card setup, usage, tuning, troubleshooting |
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

Touch panel: Mixxx script tested against a mock of the Mixxx API (Node), server + WebSocket tests, UI tests in Chromium with
simulated multi-touch; **not** tested in a running Mixxx or with real loopMIDI (see `docs/PANEL.md`).
Skin rebuilt on Mixxx 2.5.7 (stable, Oct 2026); re-verified with `make check` (unit tests, 1046 file references,
Studio scheme regenerates identically) and an install/uninstall round trip into a temporary data folder.
Earlier rounds: static skin checks (XML, QSS braces, 1046 file references), the unit tests, `install.sh` (including
re-install, uninstall and the Flatpak path), `install.ps1` under PowerShell 7 on Linux (link, copy, re-install,
uninstall), shellcheck on the shell scripts, and Mixxx 2.4.0 starting headless.

**Not** tested: loading the skin in a running Mixxx 2.5.x (the skin targets 2.5.x), `install.ps1` under Windows
PowerShell 5.1 / real Windows, and the system-audio chain with real hardware. `dj-stream.sh` and the tools are tested
against stand-ins (fake `pactl`, a test database in the Mixxx schema). Errors on first start are written to
`~/.mixxx/mixxx.log` (Windows: `%LOCALAPPDATA%\Mixxx\mixxx.log`).

## Licenses

Own code and docs: MIT (`LICENSE`). The skin is a derivative of LateNight and is under
**CC BY-SA 3.0**; the keyboard layout derives from Mixxx (**GPL-2.0-or-later**). Details: `NOTICE.md`.
