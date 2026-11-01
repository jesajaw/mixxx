# One music folder for everything (SoundCloud, your Spotify app, purchases)

Mixxx cannot play Spotify or SoundCloud streams. The simplest "connection" between your tools and Mixxx is therefore
**one shared folder of real audio files**. Every tool writes into its own sub-folder, Mixxx watches the root.

```
~/Music/DJ                      <- Mixxx library folder (Preferences > Library > Add)  (env: DJ_MUSIC_DIR)
  SoundCloud/<artist>/<title>.mp3    tools/fetch_tracks.py   (only tracks with downloads enabled / your own)
  Spotify/...                        output of your own Spotify app (see below)
  Purchased/...                      Bandcamp, Beatport, ...
```
Windows: `C:\Users\<you>\Music\DJ`. Set the same folder everywhere (`DJ_MUSIC_DIR` or `--out`).

**Rules for every tool that writes there** (so Mixxx shows good data without any extra step):

1. Finished files only: write to a temporary name, rename when complete.
2. Tags inside the file: artist, title, album, cover, and BPM/key if known (Mixxx reads ID3/Vorbis/MP4 tags).
3. Formats Mixxx plays: MP3, FLAC, OGG, M4A/AAC (not DRM-protected files).
4. Playlists as `.m3u8` next to the files; in Mixxx: Library > Playlists > Import.

**Getting new files into Mixxx:** Mixxx does not notice new files by itself. Enable *Preferences > Library > Synchronize
library on start-up*, or use **Library > Rescan Library** while it runs. (Mixxx offers no control a script or the panel
could press for this.)

**What cannot work:** Spotify and SoundCloud streams are DRM/ToS-protected. Recording or ripping them is against their
terms; this repo only handles files you are allowed to have. Spotify's API gives metadata and playlists, never audio -
a Spotify app can still be useful here: it can **export a playlist as `.m3u8`** that points at your *own local copies*,
or list the tracks you do not own yet.
