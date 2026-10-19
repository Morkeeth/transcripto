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

    def test_ask_with_no_transcripts_says_nothing_was_indexed(self):
        r = run(self.home, "ask", "retry")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("No transcripts indexed", r.stdout)
        self.assertIn(".claude/projects", r.stdout)
        self.assertIn("import-example", r.stdout)
        self.assertNotIn("nothing about", r.stdout)

    def test_ask_with_transcripts_and_no_hit_keeps_the_old_message(self):
        run(self.home, "import-example")
        r = run(self.home, "ask", "zzqqxx")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("nothing about 'zzqqxx'", r.stdout)



if __name__ == "__main__":
    unittest.main()
