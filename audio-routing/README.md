# audio-routing - streaming services via system audio into Mixxx

This is the pragmatic route for Spotify & co.: the service plays into a **virtual audio device**,
Mixxx reads it as an **auxiliary input** and mixes it with fader, EQ, filter, effects, crossfader and cue.

| Platform | Files |
|----------|-------|
| Linux (PulseAudio / PipeWire) | `linux/dj-stream.sh`, optional `linux/librespot-deck.service` |
| Windows | `windows/README.md` (VB-CABLE / VoiceMeeter) |
| macOS | BlackHole (open-source loopback), same idea as on Windows: app output = BlackHole, Mixxx input = BlackHole |

**What Aux cannot do** (the stream runs through "live"): no waveform, no BPM analysis, no sync,
no hotcues/loops, no tempo/pitch control. You mix by ear; cueing in the headphones (PFL)
only works if the track is already playing (fader down, PFL on).
For the full DJ experience use local files (see `docs/SOURCES.md`).
