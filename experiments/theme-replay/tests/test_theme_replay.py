import json
import os
import tempfile
import unittest
from pathlib import Path

from theme_replay.freeze import freeze
from theme_replay.gateway import require_key
from theme_replay.review import record_decision, render
from theme_replay.run import run_offline
from theme_replay.schema import FORBIDDEN_PATH_MARKERS
from theme_replay.verify import verify

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


def freeze_stage0(out: Path) -> Path:
    freeze(
        FIXTURES / "stage0-episodes.jsonl",
        out,
        question=(FIXTURES / "question.txt").read_text(encoding="utf8"),
        prompt=(FIXTURES / "analysis-prompt.txt").read_text(encoding="utf8"),
        protocol=json.loads((FIXTURES / "protocol.json").read_text(encoding="utf8")),
    )
    return out


class Stage0Tests(unittest.TestCase):
    def test_freeze_has_twelve_synthetic_episodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen = freeze_stage0(Path(tmp) / "frozen")
            manifest = json.loads((frozen / "dataset-manifest.json").read_text())
            self.assertEqual(manifest["n"], 12)
            self.assertEqual(manifest["harnesses"], {"claude": 4, "codex": 4, "cursor": 4})
            self.assertFalse(manifest["private_transcripts"])
            self.assertEqual(len(manifest["files"]["episodes.jsonl"]), 64)
            raw = (frozen / "episodes.jsonl").read_text()
            for marker in FORBIDDEN_PATH_MARKERS:
                self.assertNotIn(marker, raw)

    def test_offline_arms_disagree_and_citations_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen = freeze_stage0(Path(tmp) / "frozen")
            runs = Path(tmp) / "runs"
            summary = run_offline(frozen, FIXTURES / "offline-arms", runs)
            self.assertTrue(summary["offline"])
            report = verify(frozen, runs)
            self.assertTrue(report["ok"], report)
            names = {
                json.loads((runs / name).read_text())["output"]["themes"][0]["name"]
                for name in ("arm-a.json", "arm-b.json")
            }
            self.assertEqual(len(names), 2)

    def test_fabricated_quote_is_a_named_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen = freeze_stage0(Path(tmp) / "frozen")
            runs = Path(tmp) / "runs"
            run_offline(frozen, FIXTURES / "offline-bad", runs)
            report = verify(frozen, runs)
            self.assertFalse(report["ok"])
            errors = " ".join(" ".join(row["errors"]) for row in report["arms"])
            self.assertIn("does not resolve", errors)
            self.assertIn("disconfirming", errors)

    def test_review_records_keep_revise_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen = freeze_stage0(Path(tmp) / "frozen")
            runs = Path(tmp) / "runs"
            run_offline(frozen, FIXTURES / "offline-arms", runs)
            text = render(frozen, runs)
            self.assertIn("What makes an agent-work episode require correction?", text)
            self.assertIn("KEEP", text)
            self.assertIn("Open: E04 line 2", text)
            keep = record_decision(runs, "finish-line-moves", "KEEP", "The correction is on the page.")
            revise = record_decision(runs, "tool-result-wound", "CHANGES MY VIEW", "Failed edits matter too.")
            reject = record_decision(runs, "smooth-story", "REJECT", "That reading is not in the corpus.")
            self.assertEqual(keep["decision"], "KEEP")
            self.assertEqual(revise["decision"], "REVISE")
            self.assertEqual(reject["decision"], "REJECT")

    def test_gateway_fails_closed_without_a_key(self):
        os.environ.pop("AI_GATEWAY_API_KEY", None)
        os.environ.pop("VERCEL_AI_GATEWAY_API_KEY", None)
        with self.assertRaises(RuntimeError):
            require_key()

    def test_freeze_rejects_private_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "private.jsonl"
            forbidden_target = FORBIDDEN_PATH_MARKERS[0] + "oscar/.claude/projects/x"
            source.write_text(
                '{"episode_id":"E99","harness":"claude","kind":"succeeded","provenance":"synthetic",'
                f'"request":"x","events":[{{"tool":"Read","kind":"read","target":"{forbidden_target}",'
                '"status":"succeeded","evidence":"ok"}]}\n',
                encoding="utf8",
            )
            with self.assertRaises(ValueError):
                freeze(
                    source,
                    Path(tmp) / "frozen",
                    question="q",
                    prompt="p",
                    protocol={"stage": 0},
                )

    def test_does_not_write_transcripto_store(self):
        store = Path.home() / ".trace" / "trace.db"
        before = store.stat().st_mtime if store.exists() else None
        with tempfile.TemporaryDirectory() as tmp:
            frozen = freeze_stage0(Path(tmp) / "frozen")
            run_offline(frozen, FIXTURES / "offline-arms", Path(tmp) / "runs")
        after = store.stat().st_mtime if store.exists() else None
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
