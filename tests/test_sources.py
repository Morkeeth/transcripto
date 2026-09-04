"""Discovery must distinguish unavailable evidence from an empty corpus."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import transcripto_sources as sources


class SourceInventoryTests(unittest.TestCase):
    def test_missing_empty_unsupported_and_incomplete_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            empty = root / "empty"
            empty.mkdir()
            unsupported = root / "unknown.jsonl"
            unsupported.write_text('{"unrelated": true}\n')
            incomplete = root / "active.jsonl"
            incomplete.write_text('{"type":')
            report = sources.inventory([root / "missing", empty, unsupported, incomplete])
            self.assertEqual([r["state"] for r in report["sources"]],
                             ["missing", "empty", "unsupported", "unsupported"])
            self.assertEqual(report["sources"][3]["formats"], {"unidentified": 1})
            self.assertTrue(report["sources"][3]["warnings"])

    def test_index_inspection_does_not_create_or_modify_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            transcript = root / "session.jsonl"
            transcript.write_text(json.dumps({"type": "session_meta", "payload": {"id": "one"}}) + "\n")
            db = root / "index.db"
            report = sources.inventory([transcript], database=str(db))
            self.assertFalse(db.exists())
            self.assertEqual(report["sources"][0]["index"]["not_indexed"], 1)
            with sqlite3.connect(db) as con:
                con.execute("CREATE TABLE indexed(session_file TEXT,mtime REAL)")
                con.execute("INSERT INTO indexed VALUES(?,?)", (str(transcript), transcript.stat().st_mtime))
            before = db.read_bytes()
            report = sources.inventory([transcript], database=str(db))
            self.assertEqual(db.read_bytes(), before)
            self.assertEqual(report["sources"][0]["index"]["fresh_by_mtime"], 1)
            transcript.write_text(transcript.read_text() + '{}\n')
            report = sources.inventory([transcript], database=str(db))
            self.assertEqual(report["sources"][0]["index"]["changed"], 1)

    def test_codex_inventory_excludes_input_history_and_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / ".codex"
            (root / "sessions").mkdir(parents=True)
            (root / "history.jsonl").write_text('{"text":"not another session"}\n')
            (root / "sessions" / "one.jsonl").write_text('{"type":"session_meta","payload":{}}\n')
            result = sources.inventory([root])["sources"][0]
            self.assertEqual((result["files"], result["formats"]), (1, {"codex": 1}))

    def test_mixed_harness_scope_is_not_missing_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one.jsonl").write_text('{"role":"user","message":{"content":"hello"}}\n')
            result = sources.inventory([root], harness="codex")["sources"][0]
            self.assertEqual(result["state"], "no-selected-harness")
            self.assertEqual(result["formats"], {"cursor": 1})


if __name__ == "__main__":
    unittest.main()
