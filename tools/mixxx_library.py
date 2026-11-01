#!/usr/bin/env python3
"""Small helpers for the Mixxx library (mixxxdb.sqlite) - READ-ONLY.

  python3 tools/mixxx_library.py stats
  python3 tools/mixxx_library.py missing                 # without BPM / file missing on disk
  python3 tools/mixxx_library.py crates
  python3 tools/mixxx_library.py export-crate "Warmup" --out warmup.m3u8
  python3 tools/mixxx_library.py export-playlist "Set 1" --out set1.m3u8

Database: found automatically (Linux, Flatpak, Windows, macOS) or given with --db.
Tip: quit Mixxx or copy the file if SQLite reports "database is locked".
"""
import argparse
import os
import sqlite3
import sys
from collections import Counter
from pathlib import Path

CANDIDATES = [
    Path("~/.mixxx/mixxxdb.sqlite"),
    Path("~/.var/app/org.mixxx.Mixxx/data/mixxx/mixxxdb.sqlite"),
    Path("~/Library/Containers/org.mixxx.mixxx/Data/Library/Application Support/Mixxx/mixxxdb.sqlite"),
    Path(os.environ.get("LOCALAPPDATA", "~/AppData/Local")) / "Mixxx" / "mixxxdb.sqlite",
]


def find_db(explicit=None):
    if explicit:
        p = Path(explicit).expanduser()
        if not p.exists():
            sys.exit(f"Database not found: {p}")
        return p
    for c in CANDIDATES:
        if c.expanduser().exists():
            return c.expanduser()
    sys.exit("mixxxdb.sqlite not found - please pass --db.")


def connect(path):
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def columns(con, table):
    return {r["name"] for r in con.execute(f"PRAGMA table_info({table})")}


def track_select(con):
    """SELECT part that also works with older/newer schema versions."""
    cols = columns(con, "library")
    parts = ["l.id AS id", "l.artist AS artist", "l.title AS title", "l.bpm AS bpm", "l.duration AS duration",
             "tl.location AS path"]
    parts.append("l.key AS key" if "key" in cols else "NULL AS key")
    parts.append("l.genre AS genre" if "genre" in cols else "NULL AS genre")
    return ("SELECT " + ", ".join(parts) +
            " FROM library l JOIN track_locations tl ON l.location = tl.id"
            " WHERE COALESCE(l.mixxx_deleted, 0) = 0")


def cmd_stats(con, _a):
    rows = con.execute(track_select(con)).fetchall()
    total = len(rows)
    if not total:
        print("The library is empty.")
        return
    hours = sum((r["duration"] or 0) for r in rows) / 3600
    with_bpm = sum(1 for r in rows if (r["bpm"] or 0) > 0)
    with_key = sum(1 for r in rows if r["key"])
    print(f"Tracks:        {total}")
    print(f"Play time:     {hours:.1f} h")
    print(f"with BPM:      {with_bpm} ({100 * with_bpm / total:.0f} %)")
    print(f"with key:      {with_key} ({100 * with_key / total:.0f} %)")
    genres = Counter((r["genre"] or "(no genre)") for r in rows).most_common(8)
    print("Top genres:    " + ", ".join(f"{g} ({n})" for g, n in genres))
    bpms = [r["bpm"] for r in rows if (r["bpm"] or 0) > 0]
    if bpms:
        buckets = Counter(int(b // 10) * 10 for b in bpms)
        print("BPM distribution:")
        for b in sorted(buckets):
            print(f"  {b:>3}-{b + 9:<3} {'#' * max(1, round(40 * buckets[b] / max(buckets.values())))} {buckets[b]}")


def cmd_missing(con, _a):
    n = 0
    for r in con.execute(track_select(con) + " ORDER BY l.artist, l.title"):
        reasons = []
        if not (r["bpm"] or 0) > 0:
            reasons.append("no BPM")
        if not os.path.exists(r["path"]):
            reasons.append("file missing")
        if reasons:
            n += 1
            print(f"{r['artist'] or '?'} - {r['title'] or '?'}  [{', '.join(reasons)}]\n    {r['path']}")
    print(f"\n{n} track(s) with issues")


def cmd_crates(con, _a):
    q = ("SELECT c.name AS name, COUNT(ct.track_id) AS n FROM crates c "
         "LEFT JOIN crate_tracks ct ON ct.crate_id = c.id GROUP BY c.id ORDER BY c.name")
    for r in con.execute(q):
        print(f"{r['n']:>5}  {r['name']}")


def write_m3u(rows, out):
    lines = ["#EXTM3U"]
    for r in rows:
        dur = int(r["duration"] or 0)
        lines.append(f"#EXTINF:{dur},{r['artist'] or ''} - {r['title'] or ''}")
        lines.append(r["path"])
    text = "\n".join(lines) + "\n"
    if out:
        Path(out).write_text(text, encoding="utf8")
        print(f"{len(rows)} tracks -> {out}")
    else:
        sys.stdout.write(text)


def cmd_export_crate(con, a):
    q = track_select(con) + (" AND l.id IN (SELECT ct.track_id FROM crate_tracks ct JOIN crates c "
                             "ON c.id = ct.crate_id WHERE c.name = ?) ORDER BY l.artist, l.title")
    rows = con.execute(q, (a.name,)).fetchall()
    if not rows:
        sys.exit(f"Crate '{a.name}' not found or empty (see: crates).")
    write_m3u(rows, a.out)


def cmd_export_playlist(con, a):
    q = ("SELECT l.artist AS artist, l.title AS title, l.duration AS duration, tl.location AS path "
         "FROM Playlists p JOIN PlaylistTracks pt ON pt.playlist_id = p.id "
         "JOIN library l ON l.id = pt.track_id JOIN track_locations tl ON l.location = tl.id "
         "WHERE p.name = ? ORDER BY pt.position")
    rows = con.execute(q, (a.name,)).fetchall()
    if not rows:
        sys.exit(f"Playlist '{a.name}' not found or empty.")
    write_m3u(rows, a.out)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", help="path to mixxxdb.sqlite")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats").set_defaults(fn=cmd_stats)
    sub.add_parser("missing").set_defaults(fn=cmd_missing)
    sub.add_parser("crates").set_defaults(fn=cmd_crates)
    for name, fn in (("export-crate", cmd_export_crate), ("export-playlist", cmd_export_playlist)):
        s = sub.add_parser(name)
        s.add_argument("name")
        s.add_argument("--out", help="target file (.m3u8); stdout if omitted")
        s.set_defaults(fn=fn)
    a = p.parse_args(argv)
    con = connect(find_db(a.db))
    a.fn(con, a)


if __name__ == "__main__":
    main()
