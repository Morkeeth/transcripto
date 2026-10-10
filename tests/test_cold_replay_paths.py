"""What a stranger sees on a cold start. Found with the published 0.3.1 on
2026-10-11 in an empty HOME: `replay /nonexistent/session.jsonl` and
`replay <directory>` both said "No matching human session found", and
`ask retry` with no transcripts at all said "nothing about 'retry' in the
selected history", as if a history had been searched."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run(home, *args):
    env = dict(os.environ, HOME=str(home), PYTHONIOENCODING="utf-8")
    env.pop("PYTHONPATH", None)
    return subprocess.run([sys.executable, str(ROOT / "transcripto.py"), *args],
                          cwd=str(home), env=env, capture_output=True, text=True, timeout=60)


class ColdPaths(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="transcripto-cold-"))

    def test_replay_missing_transcript_file_names_the_file(self):
        missing = str(self.home / "nowhere" / "session.jsonl")
        r = run(self.home, "replay", missing)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("No transcript file at", r.stdout)
        self.assertIn("session.jsonl", r.stdout)
        self.assertNotIn("No matching human session", r.stdout)

    def test_replay_directory_points_at_root_flag(self):
        folder = self.home / "transcripts"
        folder.mkdir()
        r = run(self.home, "replay", str(folder))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("is a directory", r.stdout)
        self.assertIn("--root", r.stdout)
        self.assertNotIn("No matching human session", r.stdout)

    def test_replay_bare_json_name_is_a_word_search(self):
        run(self.home, "import-example")
        r = run(self.home, "replay", "package.json")
        self.assertNotIn("No transcript file", r.stdout)

    def test_replay_words_with_a_slash_still_search(self):
        r = run(self.home, "replay", "fix src/app.py please")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("No matching human session", r.stdout)


if __name__ == "__main__":
    unittest.main()
