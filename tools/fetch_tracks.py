#!/usr/bin/env python3
"""SoundCloud -> local files for Mixxx (thin wrapper around yt-dlp).

Intended for tracks you are allowed to save: your own uploads, tracks with downloads
enabled, Creative Commons music, promos with downloads enabled. SoundCloud's terms of use
and the artists' rights are your responsibility.

Examples:
  python3 tools/fetch_tracks.py https://soundcloud.com/artist/track
  python3 tools/fetch_tracks.py --out ~/Music/DJ/SoundCloud https://soundcloud.com/artist/sets/my-set
  python3 tools/fetch_tracks.py --format mp3 --dry-run <url>

Afterwards in Mixxx: Library > Rescan library (or restart Mixxx). BPM/key are analyzed there.
Requirements: yt-dlp (pip install -U yt-dlp) and ffmpeg on the PATH.
"""
import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_HOSTS = {"soundcloud.com", "www.soundcloud.com", "m.soundcloud.com", "on.soundcloud.com"}
DEFAULT_OUT = Path(os.environ.get("DJ_MUSIC_DIR", "~/Music/DJ")).expanduser() / "SoundCloud"
FORMATS = ("best", "mp3", "m4a", "opus", "flac", "wav")


def build_command(args, urls):
    out = Path(args.out).expanduser()
    cmd = [
        "yt-dlp",
        "-x", "--audio-format", args.format, "--audio-quality", "0",
        "--embed-metadata", "--embed-thumbnail",
        "--download-archive", str(out / ".downloaded.txt"),
        "-o", str(out / "%(uploader)s" / "%(title)s.%(ext)s"),
    ]
    if not args.no_parse_title:
        # "Artist - Title" in the title -> tags artist/title (only applies if the pattern matches)
        cmd += ["--parse-metadata", r"title:(?P<artist>.+?)\s+-\s+(?P<title>.+)"]
    if args.no_playlist:
        cmd.append("--no-playlist")
    return cmd + list(urls)


def check_urls(urls):
    for u in urls:
        host = (urlparse(u).hostname or "").lower()
        if host not in ALLOWED_HOSTS:
            sys.exit(f"Only soundcloud.com links are allowed, not: {u}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("urls", nargs="+", help="SoundCloud track, playlist or profile links")
    p.add_argument("--out", default=str(DEFAULT_OUT), help=f"Target folder (default: {DEFAULT_OUT})")
    p.add_argument("--format", choices=FORMATS, default="best",
                   help="best = keep the audio stream unchanged (no re-encoding)")
    p.add_argument("--no-playlist", action="store_true", help="for set/track links, download only that one track")
    p.add_argument("--no-parse-title", action="store_true", help="do not split the title into artist/title")
    p.add_argument("--dry-run", action="store_true", help="only print the yt-dlp command")
    args = p.parse_args(argv)

    check_urls(args.urls)
    cmd = build_command(args, args.urls)
    if args.dry_run:
        print(" ".join(shlex.quote(c) for c in cmd))
        return 0
    if not shutil.which("yt-dlp"):
        sys.exit("yt-dlp is missing: pip install -U yt-dlp   (also install ffmpeg)")
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is missing (needed for audio extraction and cover embedding).")
    Path(args.out).expanduser().mkdir(parents=True, exist_ok=True)
    print("Note: only download tracks you are allowed to save (your own / downloads enabled / CC).")
    rc = subprocess.call(cmd)
    if rc == 0:
        print(f"\nDone -> {Path(args.out).expanduser()}\nIn Mixxx: Library > Rescan library.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
