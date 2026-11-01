# Skin StudioDeck

Derivative of **LateNight** (Mixxx 2.5.7, CC BY-SA 3.0). Changes compared to the original:

* New color scheme **Studio** (listed first in `skin.xml`, so it is the default):
  * Chassis: greys get a cool ink-blue tint (`#06070a` base, dark blue-grey panels)
  * Accents: teal/blue -> indigo (volume/crossfader bars, FX 3/4 knobs)
  * LEDs stay amber/green/red as in the original (functional colors)
  * Waveform: deck 1/2 amber `#f2b36d`, deck 3/4 violet-blue `#9fb0ff`, play position mint `#7cf0c8`
* The Mic/Aux rack is **visible by default** (for the system-audio route, see `audio-routing/`)
* The original schemes **PaleMoon** and **Classic** remain selectable.

## Layout

```
skins/StudioDeck/
  skin.xml              manifest + schemes (Studio is listed first)
  style.qss             shared layout
  style_studio.qss      GENERATED from style_palemoon.qss (tools/make_scheme.py)
  studio/               GENERATED: SVG icons/buttons recolored from palemoon/
  palemoon/ classic/    unmodified originals
```

## Changing colors

1. Edit `tools/palette.json` (chassis hue, saturation, accent hue).
2. Run `python3 tools/make_scheme.py` - regenerates `style_studio.qss` and `studio/`.
3. Waveform/bar colors are set by hand in the `<Scheme><Name>Studio</Name>` block in `skin.xml`
   (`SignalColor_12`, `PlayPosColor`, `BarColorVolume` ...).
4. `python3 tools/validate_skin.py` - checks XML, QSS braces and all fixed file references.
5. In Mixxx: start `mixxx --developer`, then **Ctrl+Shift+R** reloads the skin.

## Known limitations

* The static checks do not replace starting Mixxx. If Mixxx complains while loading: `~/.mixxx/mixxx.log`.
* The `skin_preview_*.png` for Studio is still missing (take a screenshot after the first start and save it as
  `skin_preview_Studio.png`).
* PNG assets (VU meters) are not recolored.
* The skin files belong to Mixxx 2.5.x (currently 2.5.7). To follow a newer 2.5.x release, rebuild `skins/StudioDeck/`
  from upstream LateNight (copy, rename `skins:LateNight` -> `skins:StudioDeck`, re-apply the `skin.xml` changes that
  `python3 tools/upstream_diff.py` lists, run `python3 tools/make_scheme.py`). 2.6 is still in beta.

## What exactly differs from Mixxx?

`python3 tools/upstream_diff.py` clones upstream Mixxx (stable branch 2.5, shallow) and lists every difference. Result for
this repo: **one changed file** (`skin.xml`: metadata, `show_microphones` = 1, the Studio scheme block) and the generated
Studio files (`studio/`, `style_studio.qss`). All other skin files are identical to LateNight apart from the renamed
`skins:LateNight` -> `skins:StudioDeck` paths.
