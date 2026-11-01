# Music sources for Mixxx: Spotify, SoundCloud and alternatives

As of October 2026 (research on 2026-10-21). Services change their rules often - check the linked developer
pages before building anything.

## Short version

| Source | Real DJ experience (waveform, BPM, sync, loops) | Effort | Note |
|---|---|---|---|
| Local files (Bandcamp, Beatport/Beatsource, Traxsource, Juno, your own CDs/rips) | yes | low | The cleanest route |
| Free/CC music (Jamendo, Free Music Archive, Internet Archive, SoundCloud with downloads enabled) | yes | low | `tools/fetch_tracks.py` for SoundCloud |
| Spotify via system audio (`audio-routing/`) | no - Aux channel only | medium | Works technically; mind the terms of service |
| SoundCloud via system audio (browser tab) | no - Aux channel only | medium | same as Spotify |
| SoundCloud API | possible, but restricted | high | See below |
| Spotify API | metadata/control only, no audio | - | See below |

## Spotify

* **Web API**: provides metadata, playlists, remote control - **no audio stream**. Since November 2024,
  `audio-features` (BPM, energy ...) and `audio-analysis` are disabled for newly created apps; since February 2026
  further restrictions apply to development-mode apps, and the app owner needs Premium
  (according to the Spotify developer forum and developer summaries; please check against the current docs).
* **Web Playback SDK**: plays DRM-protected inside the browser; no raw data for a DJ engine.
* **Consequence**: Spotify can only get into Mixxx as a *running audio signal* (system audio or a
  Spotify Connect receiver such as librespot -> virtual sink -> Aux). You would have to determine BPM/key yourself
  (e.g. tap tempo, or own the file locally).
* Recording/downloading Spotify streams violates Spotify's terms - this repo deliberately has no tool for that.

## SoundCloud

* **Official API** (developers.soundcloud.com): OAuth 2.1, endpoints for search, tracks, playlists, upload.
  **Registering an app** requires an **Artist Pro subscription**, according to the developer site. Stream URLs are only
  available as far as the API terms and the uploaders' permissions allow; Mixxx has no connector for this,
  you would have to build a download/cache service yourself and comply with the terms.
* **Downloads enabled**: you may save tracks that have downloads enabled (or a CC license).
  `tools/fetch_tracks.py` is a thin yt-dlp wrapper (soundcloud.com links only) with cover/tags and a
  download archive; Mixxx then imports the files normally.
* **Go+/streaming quality** via browser + system audio is technically the same Aux route as for Spotify.

## On the Mixxx side

As far as I know, Mixxx 2.5.7 (the current stable release) has no direct integration with Spotify or
SoundCloud; watch the release notes for 2.6 (https://mixxx.org/news/).
Streaming integrations are offered by commercial DJ programs - that is the main reason why only the
system-audio detour exists here.

## Recommended split

1. **Main library local** (Bandcamp/Beatport purchases, your own files, free downloads) -> full Mixxx features.
2. **Aux channel** for spontaneous stuff from Spotify/SoundCloud: fade it in, EQ/filter/FX, mix by ear.
3. Use API metadata only for pre-sorting (playlists/charts), not as an audio source.
