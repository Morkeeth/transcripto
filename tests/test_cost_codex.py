"""Cost on actual Codex rollout shapes, without reading the user's history."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import transcripto
import transcripto_core


def record(kind, payload, ts="2026-10-10T12:00:00Z"):
    return {"timestamp": ts, "type": kind, "payload": payload}


def counter(inp, cached, out):
    return record("event_msg", {"type": "token_count", "info": {
        "total_token_usage": {"input_tokens": inp, "cached_input_tokens": cached,
                              "cache_write_input_tokens": 0, "output_tokens": out}}})


class CodexCostTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def rollout(self, name, cwd, events):
        path = self.root / name
        rows = [record("session_meta", {"id": name, "cwd": cwd})] + events
        path.write_text("\n".join(map(json.dumps, rows)) + "\n")

    def test_session_cwd_cumulative_counters_and_zero_decision_folder(self):
        self.rollout("project.jsonl", "/tmp/my-project", [
            record("turn_context", {"model": "gpt-6-sol", "cwd": "/tmp/other-folder"}),
            record("response_item", {"type": "message", "role": "user", "content": "do it"}),
            counter(1000, 200, 100), counter(1000, 200, 100),
            counter(1500, 400, 150),
        ])
        self.rollout("home.jsonl", transcripto.HOME, [
            record("turn_context", {"model": "gpt-6-luna"}),
            counter(1000, 0, 100),
        ])
        rep = transcripto.collect_cost(0, [str(self.root)])
        self.assertEqual(rep["decisions"], 1)
        self.assertEqual(rep["agent_messages"], 3)
        self.assertEqual(rep["sessions"], 2)
        self.assertIn("/tmp/my-project", rep["by_repo"])
        self.assertNotIn("/tmp/other-folder", rep["by_repo"])
        self.assertEqual(rep["by_repo"]["(home folder, no project)"]["decisions"], 0)
        self.assertAlmostEqual(rep["by_repo"]["/tmp/my-project"]["usd"], 0.00378)
        self.assertAlmostEqual(rep["usd"], 0.00393)
        p = subprocess.run([sys.executable, "transcripto.py", "cost", "--days", "0",
                            "--root", str(self.root)], capture_output=True, text=True, check=True)
        self.assertIn("(home folder, no project)", p.stdout)
        self.assertIn("0 decisions", p.stdout)
        self.assertIn("n/a", p.stdout)

    def test_unknown_model_is_unpriced_and_folder_still_visible(self):
        self.rollout("unknown.jsonl", "/tmp/unknown", [
            record("turn_context", {"model": "future-model"}), counter(1000, 0, 100)])
        rep = transcripto.collect_cost(0, [str(self.root)])
        self.assertEqual(rep["usd"], 0)
        self.assertEqual(rep["unpriced_messages"], 1)
        self.assertEqual(rep["by_repo"]["/tmp/unknown"]["decisions"], 0)
        p = subprocess.run([sys.executable, "transcripto.py", "cost", "--days", "0",
                            "--root", str(self.root)], capture_output=True, text=True, check=True)
        self.assertIn("future-model", p.stdout)
        self.assertIn("/tmp/unknown", p.stdout)

    def test_decisions_share_replay_authorship_filter(self):
        self.rollout("authorship.jsonl", "/tmp/project", [
            record("response_item", {"type": "message", "role": "user",
                                     "content": [{"type": "input_text", "text": "# AGENTS.md instructions\n<INSTRUCTIONS>rules</INSTRUCTIONS>"}]}),
            record("response_item", {"type": "message", "role": "user",
                                     "content": [{"type": "input_text", "text": "<environment_context>\n<cwd>/tmp/project</cwd>\n</environment_context>"}]}),
            record("response_item", {"type": "message", "role": "user",
                                     "content": [{"type": "input_text", "text": "The following is the Codex agent history added since your last approval"}]}),
            record("response_item", {"type": "message", "role": "user",
                                     "content": [{"type": "input_text", "text": "Please fix the search result."}]}),
            record("turn_context", {"model": "gpt-6-sol"}), counter(1000, 0, 100),
        ])
        rep = transcripto.collect_cost(0, [str(self.root)])
        rows, harness = transcripto_core.read_session(str(self.root / "authorship.jsonl"))
        self.assertEqual(harness, "codex")
        self.assertEqual(sum(row.get("type") == "user" for row in rows), 1)
        self.assertEqual(rep["decisions"], 1)
        self.assertEqual(rep["raw_user_turns"], 1)
        self.assertEqual(rep["by_repo"]["/tmp/project"]["decisions"], 1)

    def test_large_rollout_streams_past_general_file_limit(self):
        self.rollout("large.jsonl", "/tmp/project", [
            record("turn_context", {"model": "gpt-6-sol"}),
            record("response_item", {"type": "message", "role": "user", "content": "Fix it"}),
            counter(1000, 200, 100),
        ])
        self.assertGreater((self.root / "large.jsonl").stat().st_size, 100)
        with mock.patch.object(transcripto_core, "MAX_FILE_BYTES", 100):
            rep = transcripto.collect_cost(0, [str(self.root)])
        self.assertEqual(rep["incomplete_files"], [])
        self.assertEqual(rep["decisions"], 1)
        self.assertAlmostEqual(rep["usd"], 0.00264)

    def test_oversize_record_marks_file_incomplete_and_excludes_partial_cost(self):
        self.rollout("oversize.jsonl", "/tmp/project", [
            record("turn_context", {"model": "gpt-6-sol"}),
            counter(1000, 200, 100),
            record("response_item", {"type": "message", "role": "user",
                                     "content": "x" * 1000}),
        ])
        with mock.patch.object(transcripto_core, "MAX_LINE_BYTES", 400):
            rep = transcripto.collect_cost(0, [str(self.root)])
        self.assertEqual(rep["usd"], 0)
        self.assertEqual(rep["decisions"], 0)
        self.assertEqual(len(rep["incomplete_files"]), 1)
        self.assertIn("oversized", rep["incomplete_files"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
