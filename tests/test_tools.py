import io
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import fetch_tracks  # noqa: E402
import make_scheme  # noqa: E402
import upstream_diff  # noqa: E402
import mixxx_library  # noqa: E402

SCHEMA = """
CREATE TABLE track_locations(id INTEGER PRIMARY KEY AUTOINCREMENT, location varchar(512) UNIQUE);
CREATE TABLE library(id INTEGER PRIMARY KEY AUTOINCREMENT, artist TEXT, title TEXT, genre TEXT,
  location INTEGER, duration FLOAT, bpm FLOAT, key TEXT, mixxx_deleted INTEGER);
CREATE TABLE crates(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL);
CREATE TABLE crate_tracks(crate_id INTEGER, track_id INTEGER);
CREATE TABLE Playlists(id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE PlaylistTracks(id INTEGER PRIMARY KEY, playlist_id INTEGER, track_id INTEGER, position INTEGER);
INSERT INTO track_locations(location) VALUES('/nope/a.mp3'),('/nope/b.mp3'),('/nope/c.mp3');
INSERT INTO library(artist,title,genre,location,duration,bpm,key,mixxx_deleted) VALUES
 ('A','One','House',1,300,124,'8A',0),('B','Two','Techno',2,360,0,NULL,0),('C','Gone','House',3,200,128,'1B',1);
INSERT INTO crates(name) VALUES('Warmup'); INSERT INTO crate_tracks VALUES(1,1),(1,3);
INSERT INTO Playlists(name) VALUES('Set 1'); INSERT INTO PlaylistTracks(playlist_id,track_id,position) VALUES(1,2,1),(1,1,2);
"""


def run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        mixxx_library.main(argv)
    return buf.getvalue()


class LibraryTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = os.path.join(cls.tmp.name, "mixxxdb.sqlite")
        con = sqlite3.connect(cls.db)
        con.executescript(SCHEMA)
        con.commit()
        con.close()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_stats_ignores_deleted(self):
        out = run(["--db", self.db, "stats"])
        self.assertIn("Tracks:        2", out)
        self.assertIn("with BPM:      1", out)

    def test_missing(self):
        out = run(["--db", self.db, "missing"])
        self.assertIn("B - Two", out)
        self.assertIn("no BPM", out)

    def test_export_crate_skips_deleted_track(self):
        out = run(["--db", self.db, "export-crate", "Warmup"])
        self.assertIn("/nope/a.mp3", out)
        self.assertNotIn("/nope/c.mp3", out)

    def test_export_playlist_keeps_order(self):
        out = run(["--db", self.db, "export-playlist", "Set 1"])
        self.assertLess(out.index("/nope/b.mp3"), out.index("/nope/a.mp3"))

    def test_db_is_read_only(self):
        con = mixxx_library.connect(Path(self.db))
        with self.assertRaises(sqlite3.OperationalError):
            con.execute("DELETE FROM library")


class FetchTracks(unittest.TestCase):
    def test_only_soundcloud_hosts(self):
        with self.assertRaises(SystemExit):
            fetch_tracks.check_urls(["https://example.com/x"])
        fetch_tracks.check_urls(["https://soundcloud.com/a/b", "https://on.soundcloud.com/xyz"])

    def test_command_contains_archive_and_template(self):
        class A:  # noqa: D401
            out, format, no_parse_title, no_playlist = "/tmp/o", "best", False, True
        cmd = fetch_tracks.build_command(A, ["https://soundcloud.com/a/b"])
        self.assertIn("--download-archive", cmd)
        self.assertIn("--no-playlist", cmd)
        self.assertEqual(cmd[-1], "https://soundcloud.com/a/b")


class Recolor(unittest.TestCase):
    def test_grey_gets_cool_tint_and_teal_becomes_indigo(self):
        grey = make_scheme.recolor_text("color: #1e1e20;")
        r, g, b = (int(grey[8:][i:i + 2], 16) for i in (0, 2, 4))
        self.assertGreater(b, r)
        teal = make_scheme.recolor_text("color: #257b82;")
        r, g, b = (int(teal[8:][i:i + 2], 16) for i in (0, 2, 4))
        self.assertGreater(b, g)  # indigo instead of teal

    def test_functional_colors_untouched(self):
        for c in ("#ffaa26", "#da0606", "#7bd002", "#000001"):
            self.assertEqual(make_scheme.recolor_text(c), c)

    def test_selectors_outside_braces_untouched(self):
        css = "#abc { color: #999; }\n#def, #123 { border: 1px solid #333; }"
        out = make_scheme.recolor_qss(css)
        self.assertTrue(out.startswith("#abc {"))
        self.assertIn("#def, #123 {", out)
        self.assertNotIn("#999", out)

    def test_url_fragments_untouched(self):
        s = 'fill="url(#abc)"'
        self.assertEqual(make_scheme.recolor_text(s), s)


class UpstreamDiff(unittest.TestCase):
    def _skin(self, root, name, files):
        for rel, text in files.items():
            p = Path(root) / name / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf8")
        return Path(root) / name

    def test_rename_is_not_a_difference_but_real_changes_are(self):
        with tempfile.TemporaryDirectory() as d:
            up = self._skin(d, "up", {
                "a.xml": '<x src="skins:LateNight/a.svg"/>', "b.xml": "same", "gone.xml": "x", "c.xml": "old"})
            own = self._skin(d, "own", {
                "a.xml": '<x src="skins:StudioDeck/a.svg"/>', "b.xml": "same", "c.xml": "new",
                "extra.xml": "e", "studio/x.svg": "g", "style_studio.qss": "q"})
            r = upstream_diff.compare_skin(up, own)
        self.assertEqual(r["changed"], ["c.xml"])
        self.assertEqual(r["added"], ["extra.xml"])
        self.assertEqual(r["removed"], ["gone.xml"])
        self.assertEqual(r["generated"], ["studio/x.svg", "style_studio.qss"])

    def test_own_repo_is_close_to_upstream_shape(self):
        # the repo's skin must still contain everything LateNight needs: every changed/added file is known
        own = ROOT / "skins" / "StudioDeck"
        self.assertTrue((own / "skin.xml").is_file())
        self.assertTrue((own / "style_studio.qss").is_file())
        self.assertTrue((own / "studio").is_dir())


if __name__ == "__main__":
    unittest.main()
