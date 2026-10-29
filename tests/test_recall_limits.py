"""Recall limits: long agent sessions are indexed, and every full-text query reads the FTS index first."""
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import transcripto as app
import transcripto_core as core

ROOT = Path(__file__).resolve().parents[1]


class FileCap(unittest.TestCase):
    def test_long_sessions_fit_under_the_default_cap(self):
        # a long-running agent session reached 363 MB; 128 MiB skipped it whole
        self.assertGreaterEqual(core.MAX_FILE_BYTES, 363 * 1000 * 1000)

    def test_cap_reads_the_environment_and_bad_values_fall_back(self):
        for value, expected in (("2048", 2048), ("lots", 1024), ("0", 1024), ("-5", 1024)):
            with patch.dict(os.environ, {"TRANSCRIPTO_MAX_FILE_MIB": value}):
                self.assertEqual(core._file_cap_mib(), expected, value)

    def test_skip_warning_names_the_cap_in_force(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "big.jsonl")
            with open(p, "wb") as f:
                f.truncate(3 * 1024 * 1024)
            warnings = []
            with patch.object(core, "MAX_FILE_BYTES", 2 * 1024 * 1024):
                rows, _ = core.read_session(p, warnings)
            self.assertEqual(rows, [])
            self.assertIn("2 MiB safety limit", warnings[0])


class FtsJoinOrder(unittest.TestCase):
    def test_every_fts_query_pins_the_fts_table_first(self):
        # A plain JOIN let the planner walk idx_msg_human and probe FTS per message: seconds per ask on a large index.
        source = (ROOT / "transcripto.py").read_text()
        joins = re.findall(r"messages_fts\"?\s*\"?\s*(\w+(?: \w+)?) messages m ON m\.id=messages_fts\.rowid", source)
        self.assertTrue(joins)
        self.assertEqual(set(joins), {"CROSS JOIN"}, joins)

    def test_cross_join_plan_starts_at_the_fts_index(self):
        con = sqlite3.connect(":memory:")
        app.init_schema(con)
        con.executemany("INSERT INTO messages(id,text,is_human,ts) VALUES(?,?,1,?)",
                        [(i, "word%d filler" % i, "2026-10-%02dT00:00:00" % (i % 28 + 1)) for i in range(1, 3001)])
        con.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")
        con.execute("ANALYZE")
        plan = con.execute("EXPLAIN QUERY PLAN SELECT m.text FROM messages_fts CROSS JOIN messages m "
                           "ON m.id=messages_fts.rowid WHERE messages_fts MATCH ? AND m.is_human=1 "
                           "ORDER BY m.ts DESC LIMIT 5", ("word7",)).fetchall()
        steps = [row[-1] for row in plan if row[-1].startswith(("SCAN", "SEARCH"))]
        self.assertTrue(steps[0].startswith("SCAN messages_fts VIRTUAL TABLE"), plan)
        self.assertTrue(any(s.startswith("SEARCH m USING INTEGER PRIMARY KEY") for s in steps), plan)


if __name__ == "__main__":
    unittest.main()
