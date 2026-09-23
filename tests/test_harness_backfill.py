"""Unlabelled harness rows: detection, in-place migration, and path backfill.

Every record here is invented. The stores are built in a fresh HOME.

The defect this guards: a writer whose INSERT names fewer columns than the table
has leaves `harness` NULL with no error, and a schema check that only knew how to
drop and rebuild never repaired it. These tests fail on code that has no
`backfill-harness` command or that drops a version-3 store instead of migrating it.
"""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# The version-3 schema exactly as a v3 writer created it: harness present, no
# source_line, no synthetic, user_version 3.
V3_SCHEMA = """
CREATE TABLE messages(
  id INTEGER PRIMARY KEY, session_id TEXT, session_file TEXT, project TEXT,
  ts TEXT, role TEXT, cwd TEXT, git_branch TEXT, text TEXT,
  is_human INTEGER DEFAULT 0, prompt_source TEXT, harness TEXT);
CREATE VIRTUAL TABLE messages_fts USING fts5(
  text, content='messages', content_rowid='id', tokenize="porter unicode61");
CREATE TABLE files(
  id INTEGER PRIMARY KEY, path TEXT, name TEXT, action TEXT,
  session_id TEXT, session_file TEXT, ts TEXT, cwd TEXT, harness TEXT);
CREATE TABLE indexed(session_file TEXT PRIMARY KEY, mtime REAL, warnings TEXT);
PRAGMA user_version=3;
"""

# The legacy writer: ten named columns into a table that also has harness.
LEGACY_INSERT = ("INSERT INTO messages(session_id,session_file,project,ts,role,cwd,git_branch,text,"
                 "is_human,prompt_source) VALUES(?,?,?,?,?,?,?,?,?,?)")
LEGACY_FILE_INSERT = ("INSERT INTO files(path,name,action,session_id,session_file,ts,cwd)"
                      " VALUES(?,?,?,?,?,?,?)")


def legacy_row(sid, path, text):
    return (sid, str(path), "demo", "2026-09-12T10:00:00Z", "user", "/tmp/demo", "", text, 1, "typed")


class Home(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="transcripto-harness-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.db = self.home / ".trace" / "trace.db"
        self.env = dict(os.environ, HOME=str(self.home), PYTHONIOENCODING="utf-8")
        self.env.pop("PYTHONPATH", None)

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "transcripto.py")] + list(args),
                              cwd=self.home, env=self.env, capture_output=True, text=True, timeout=60)

    def write(self, relative, records):
        path = self.home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r) + "\n" for r in records))
        return path

    def claude_session(self, relative, text):
        return self.write(relative, [
            {"type": "user", "promptSource": "typed", "sessionId": "c-" + text[:4],
             "timestamp": "2026-09-12T09:00:00Z", "message": {"content": text}},
            {"type": "assistant", "timestamp": "2026-09-12T09:00:01Z", "message": {"content": [
                {"type": "tool_use", "name": "Edit", "id": "e1", "input": {"file_path": "/tmp/demo/a.py"}}]}},
        ])

    def query(self, sql, args=()):
        con = sqlite3.connect(str(self.db))
        try:
            return con.execute(sql, args).fetchall()
        finally:
            con.close()


class PathLabelTests(unittest.TestCase):
    def test_paths_name_their_harness(self):
        import transcripto
        cases = {
            "/h/.claude/projects/-tmp-demo/s.jsonl": "claude",
            "/h/.codex/sessions/2026/09/12/rollout.jsonl": "codex",
            "/h/.codex/archived_sessions/a.jsonl": "codex",
            "/h/.codex/history.jsonl": "codex-history",
            "/h/.cursor/projects/p/agent-transcripts/x/x.jsonl": "cursor",
            "/h/.transcripto/imports/cursor/lab.jsonl": "cursor",
            "/h/.transcripto/imports/unknown/lab.jsonl": None,
            "/h/archive/.codex/sessions/old.jsonl": "codex",
            "/h/notes/session.jsonl": None,
        }
        for path, expected in cases.items():
            self.assertEqual(transcripto.harness_from_path(path), expected, path)


class LegacyInsertTests(Home):
    def test_backfill_labels_rows_a_ten_column_insert_left_null(self):
        self.claude_session(".claude/projects/-tmp-demo/one.jsonl", "Rename the amber helper.")
        done = self.cli("index")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.query("SELECT COUNT(*) FROM messages WHERE harness IS NULL")[0][0], 0,
                         "a current index pass must never write an unlabelled row")

        codex = self.home / ".codex/sessions/2026/09/12/rollout-legacy.jsonl"
        cursor = self.home / ".cursor/projects/p/agent-transcripts/x/x.jsonl"
        claude = self.home / ".claude/projects/-tmp-demo/legacy.jsonl"
        stray = self.home / "notes/unknown.jsonl"
        con = sqlite3.connect(str(self.db))
        for i, path in enumerate((codex, codex, cursor, claude, stray)):
            con.execute(LEGACY_INSERT, legacy_row("s%d" % i, path, "invented cobalt request %d" % i))
        con.execute(LEGACY_FILE_INSERT, ("/tmp/demo/b.py", "b.py", "edit", "s0", str(codex),
                                         "2026-09-12T10:00:00Z", "/tmp/demo"))
        con.commit(); con.close()
        self.assertEqual(self.query("SELECT COUNT(*) FROM messages WHERE harness IS NULL")[0][0], 5)

        dry = self.cli("backfill-harness", "--json")
        self.assertEqual(dry.returncode, 0, dry.stderr)
        report = json.loads(dry.stdout)
        self.assertFalse(report["applied"])
        self.assertEqual(report["unlabelled_before"], {"messages": 5, "files": 1})
        self.assertEqual(report["unlabelled_after"], {"messages": 5, "files": 1}, "dry run wrote")
        self.assertEqual(report["labels"]["codex"], {"files": 1, "messages": 2, "file_rows": 1})
        self.assertEqual(report["unresolved_rows"], 1)

        applied = self.cli("backfill-harness", "--apply", "--json")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertEqual(json.loads(applied.stdout)["unlabelled_after"], {"messages": 1, "files": 0})
        got = dict(self.query("SELECT session_file, harness FROM messages WHERE text LIKE 'invented cobalt%'"))
        self.assertEqual(got[str(codex)], "codex")
        self.assertEqual(got[str(cursor)], "cursor")
        self.assertEqual(got[str(claude)], "claude")
        self.assertIsNone(got[str(stray)], "a path that names no harness must stay unlabelled")
        self.assertEqual(self.query("SELECT harness FROM files WHERE session_file=?", (str(codex),)),
                         [("codex",)])

    def test_open_detects_and_labels_unlabelled_rows(self):
        self.claude_session(".claude/projects/-tmp-demo/one.jsonl", "Rename the amber helper.")
        self.assertEqual(self.cli("index").returncode, 0)
        con = sqlite3.connect(str(self.db))
        con.execute(LEGACY_INSERT, legacy_row("s9", self.home / ".codex/sessions/r.jsonl", "invented"))
        con.commit(); con.close()
        again = self.cli("index")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("labelled 1 unlabelled message row", again.stderr)
        self.assertEqual(self.query("SELECT COUNT(*) FROM messages WHERE harness IS NULL")[0][0], 0)


class VersionThreeStoreTests(Home):
    def v3_store(self):
        self.db.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(str(self.db))
        con.executescript(V3_SCHEMA)
        # A transcript indexed earlier from a --root outside the default roots. It is
        # still on disk, so an index pass keeps it; a rebuild would lose it.
        kept = self.claude_session("archive/.codex/sessions/old.jsonl", "Kept archive request.")
        cur = con.execute(LEGACY_INSERT, legacy_row("old", kept, "invented archive request"))
        con.execute("INSERT INTO messages_fts(rowid,text) VALUES(?,?)", (cur.lastrowid, "invented archive request"))
        con.execute("INSERT INTO indexed(session_file,mtime,warnings) VALUES(?,?,?)",
                    (str(kept), os.path.getmtime(kept), "[]"))
        con.commit(); con.close()
        return kept

    def test_index_migrates_a_version_three_store_in_place(self):
        kept = self.v3_store()
        self.claude_session(".claude/projects/-tmp-demo/new.jsonl", "Rename the amber helper.")
        done = self.cli("index")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("migrated index schema: added messages.source_line, messages.synthetic", done.stderr)
        self.assertEqual(self.query("PRAGMA user_version")[0][0], 5)
        cols = {r[1] for r in self.query("PRAGMA table_info(messages)")}
        self.assertTrue({"harness", "source_line", "synthetic"} <= cols)
        self.assertEqual(self.query("SELECT harness FROM messages WHERE session_file=?", (str(kept),)),
                         [("codex",)], "the version-3 row was dropped or left unlabelled")
        self.assertEqual(self.query("SELECT COUNT(*) FROM messages WHERE harness IS NULL")[0][0], 0)
        self.assertEqual(len(self.query("SELECT rowid FROM messages_fts WHERE messages_fts MATCH 'archive'")), 1,
                         "full-text index lost the migrated row")

    def test_backfill_on_a_version_three_store_leaves_the_schema_alone(self):
        kept = self.v3_store()
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        dry = self.cli("backfill-harness", "--db", str(self.db))
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertIn("DRY RUN", dry.stdout)
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(), before, "dry run changed the file")

        applied = self.cli("backfill-harness", "--db", str(self.db), "--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        # A v3 writer rebuilds on any other user_version, so backfill must not bump it.
        self.assertEqual(self.query("PRAGMA user_version")[0][0], 3)
        self.assertEqual(len(self.query("PRAGMA table_info(messages)")), 12)
        self.assertEqual(self.query("SELECT harness FROM messages WHERE session_file=?", (str(kept),)),
                         [("codex",)])


if __name__ == "__main__":
    unittest.main()
