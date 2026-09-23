import json
import os
import tempfile
import unittest
from pathlib import Path

from theme_replay.freeze import freeze
from theme_replay.gateway import (
    CHAT_COMPLETIONS_URL,
    EVALUATE_URL,
    assert_chat_completions_url,
    chat_completions_body,
    complete,
    require_key,
)
from theme_replay.review import load_receipts, record_decision, render
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
                receipt["output"]["themes"][0]["name"] for receipt in load_receipts(runs)
            }
            self.assertGreaterEqual(len(names), 2)

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

    def test_generative_request_puts_privacy_flags_under_provider_options(self):
        body = chat_completions_body(
            "anthropic/claude-sonnet-5",
            "prompt",
            zdr=True,
            no_training=True,
        )
        gateway = body["providerOptions"]["gateway"]
        self.assertEqual(gateway["zeroDataRetention"], True)
        self.assertEqual(gateway["disallowPromptTraining"], True)
        self.assertNotIn("zeroDataRetention", body)
        self.assertNotIn("disallowPromptTraining", body)

    def test_generative_run_refuses_jev_and_evaluate_url(self):
        with self.assertRaises(RuntimeError) as raised:
            chat_completions_body("typesafe-ai/jev", "prompt", zdr=True, no_training=True)
        self.assertIn("/v1/evaluate", str(raised.exception))
        self.assertIn(EVALUATE_URL, str(raised.exception))
        with self.assertRaises(RuntimeError):
            assert_chat_completions_url(EVALUATE_URL)
        assert_chat_completions_url(CHAT_COMPLETIONS_URL)

    def test_live_generative_run_requires_zdr_flags(self):
        with self.assertRaises(RuntimeError):
            chat_completions_body("anthropic/claude-sonnet-5", "prompt", zdr=False, no_training=True)
        with self.assertRaises(RuntimeError):
            chat_completions_body("anthropic/claude-sonnet-5", "prompt", zdr=True, no_training=False)

    def test_complete_records_wall_clock_latency(self):
        import json as json_lib
        from unittest import mock
        from urllib.request import Request

        class FakeResp:
            def read(self):
                return json_lib.dumps({"choices": [{"message": {"content": "{}"}}]}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        os.environ["AI_GATEWAY_API_KEY"] = "test-not-a-live-key"
        try:
            with mock.patch("urllib.request.urlopen", return_value=FakeResp()) as opener:
                call = complete(
                    "anthropic/claude-sonnet-5",
                    "prompt",
                    zdr=True,
                    no_training=True,
                )
            request = opener.call_args[0][0]
            self.assertIsInstance(request, Request)
            self.assertEqual(request.full_url, CHAT_COMPLETIONS_URL)
            sent = json_lib.loads(request.data.decode())
            self.assertEqual(sent["providerOptions"]["gateway"]["zeroDataRetention"], True)
            self.assertNotIn("zeroDataRetention", sent)
            self.assertIsInstance(call["latency_ms"], float)
            self.assertIsNotNone(call["latency_ms"])
            self.assertIn("payload", call)
        finally:
            os.environ.pop("AI_GATEWAY_API_KEY", None)

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


def arm(label="x", *, codes=None, themes=None, model=None):
    out = {"model": model or f"offline-{label}", "analytic_position": "synthetic"}
    if codes is not None:
        out["codes"] = codes
    if themes is not None:
        out["themes"] = themes
    return out


def good_code(label="c", episode="E04", quote="No, I meant the header parser", line=2, **extra):
    row = {
        "label": label,
        "episode_ids": [episode],
        "evidence": [{"episode_id": episode, "quote": quote, "line": line}],
        "interpretation": "i",
        "counterevidence": [{"episode_id": "E01", "reason": "r"}],
        "confidence": "tentative",
    }
    row.update(extra)
    return row


def good_theme(name="T", codes=("c",), support=("E04",), disconfirm=("E01",)):
    return {
        "name": name,
        "central_concept": "cc",
        "codes": list(codes),
        "supporting_episodes": list(support),
        "disconfirming_episodes": list(disconfirm),
        "limits": "synthetic",
    }


def verify_arms(tmp: Path, arms: dict) -> dict:
    frozen = freeze_stage0(tmp / "frozen")
    src = tmp / "arms"
    src.mkdir()
    for name, body in arms.items():
        (src / f"{name}.json").write_text(json.dumps(body))
    runs = tmp / "runs"
    run_offline(frozen, src, runs, seed=7)
    return verify(frozen, runs)


def all_errors(report: dict) -> str:
    return " | ".join(" | ".join(row["errors"]) for row in report["arms"])


class VerifyHardeningTests(unittest.TestCase):
    """Each case below passed PR 6 verify silently. Each must now be a named failure."""

    def test_control_good_arms_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = verify_arms(Path(tmp), {
                "a": arm(codes=[good_code()], themes=[good_theme()]),
                "b": arm("b", codes=[good_code()], themes=[good_theme()]),
            })
            self.assertTrue(report["ok"], report)

    def test_arm_without_codes_is_still_checked(self):
        bad_theme = good_theme()
        bad_theme["evidence"] = [{"episode_id": "E02", "quote": "invented words", "line": 1}]
        with tempfile.TemporaryDirectory() as tmp:
            report = verify_arms(Path(tmp), {
                "a": arm(themes=[bad_theme]),
                "b": arm("b", codes=[good_code()], themes=[good_theme()]),
            })
            self.assertFalse(report["ok"])
            errors = all_errors(report)
            self.assertIn("has no codes", errors)
            self.assertIn("does not resolve", errors)

    def test_code_without_evidence_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = verify_arms(Path(tmp), {
                "a": arm(codes=[good_code(evidence=[])], themes=[good_theme()]),
                "b": arm("b", codes=[good_code()], themes=[good_theme()]),
            })
            self.assertFalse(report["ok"])
            self.assertIn("cites no evidence", all_errors(report))

    def test_missing_episode_ids_are_named_everywhere(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = good_code(episode_ids=["E04", "E77"], counterevidence=[{"episode_id": "E88", "reason": "r"}])
            report = verify_arms(Path(tmp), {
                "a": arm(codes=[code], themes=[good_theme(support=("E04", "E66"), disconfirm=("E99",))]),
                "b": arm("b", codes=[good_code()], themes=[good_theme()]),
            })
            self.assertFalse(report["ok"])
            errors = all_errors(report)
            for missing in ("E77", "E88", "E66", "E99"):
                self.assertIn(missing, errors)

    def test_theme_names_a_code_nobody_wrote(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = verify_arms(Path(tmp), {
                "a": arm(codes=[good_code()], themes=[good_theme(codes=("c", "ghost code"))]),
                "b": arm("b", codes=[good_code()], themes=[good_theme()]),
            })
            self.assertFalse(report["ok"])
            self.assertIn("ghost code", all_errors(report))

    def test_status_claim_must_match_the_cited_line(self):
        # E04 line 3 is the failed Edit. E04 also has a succeeded event, which fooled the old check.
        code = good_code(episode="E04", quote="Edit failed", line=3)
        code["evidence"][0]["claimed_status"] = "succeeded"
        unknown_as_failed = good_code(label="u", episode="E03", quote="No matching tool result", line=2)
        unknown_as_failed["evidence"][0]["claimed_status"] = "failed"
        with tempfile.TemporaryDirectory() as tmp:
            report = verify_arms(Path(tmp), {
                "a": arm(codes=[code, unknown_as_failed], themes=[good_theme(codes=("c", "u"))]),
                "b": arm("b", codes=[good_code()], themes=[good_theme()]),
            })
            self.assertFalse(report["ok"])
            errors = all_errors(report)
            self.assertIn("E04 line 3 records failed", errors)
            self.assertIn("E03 line 2 records unknown", errors)

    def test_verify_recomputes_instead_of_trusting_receipt_errors(self):
        bad_theme = good_theme()
        bad_theme["evidence"] = [{"episode_id": "E02", "quote": "invented words", "line": 1}]
        with tempfile.TemporaryDirectory() as tmp:
            frozen = freeze_stage0(Path(tmp) / "frozen")
            runs = Path(tmp) / "runs"
            runs.mkdir()
            receipt = {"arm": "arm-1", "offline": True, "errors": [], "output": arm(themes=[bad_theme])}
            (runs / "arm-1.json").write_text(json.dumps(receipt))
            report = verify(frozen, runs)
            self.assertFalse(report["ok"])
            self.assertIn("does not resolve", all_errors(report))

    def test_non_json_live_output_is_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = verify_arms(Path(tmp), {
                "a": {"raw_text": "Here are the themes!"},
                "b": arm("b", codes=[good_code()], themes=[good_theme()]),
            })
            self.assertFalse(report["ok"])


MODELS = ["anthropic/claude-sonnet-5", "openai/gpt-5.6-sol", "google/gemini-3.7-flash"]


def fake_catalog(models=MODELS, zdr="all"):
    return {"data": [
        {"id": m, "zdr": zdr, "no_training": "all", "temperature": m.startswith("openai"),
         "pricing": {"input": "1", "output": "2"}, "owned_by": m.split("/")[0]}
        for m in models
    ]}


def fake_complete_factory(calls):
    good = json.loads((FIXTURES / "offline-arms" / "arm-a.json").read_text())

    def fake_complete(model, prompt, *, zdr, no_training):
        calls.append(model)
        body = dict(good, model=model)
        return {
            "payload": {
                "choices": [{"message": {"content": json.dumps(body)}}],
                "usage": {"total_tokens": 1234},
                "providerMetadata": {"gateway": {"cost": "0.01", "routing": {"finalProvider": "p"}}},
            },
            "latency_ms": 12.5,
            "provider_options": {"gateway": {"zeroDataRetention": True, "disallowPromptTraining": True}},
        }
    return fake_complete


class BlindAndRepeatTests(unittest.TestCase):
    def run_live(self, tmp: Path, repeat=1, seed=3):
        from unittest import mock
        from theme_replay import run as run_mod

        frozen = freeze_stage0(tmp / "frozen")
        runs = tmp / "runs"
        calls = []
        with mock.patch.object(run_mod, "complete", fake_complete_factory(calls)), \
                mock.patch.dict(os.environ, {"AI_GATEWAY_API_KEY": "test-not-a-live-key"}), \
                mock.patch.object(run_mod, "fetch_catalog", return_value=fake_catalog()):
            summary = run_mod.run_gateway(frozen, MODELS, runs, zdr=True, no_training=True,
                                          repeat=repeat, seed=seed)
        return frozen, runs, calls, summary

    def test_live_receipts_are_blind(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen, runs, calls, _ = self.run_live(Path(tmp))
            names = " ".join(p.name for p in runs.iterdir())
            text = render(frozen, runs)
            receipts_text = " ".join(
                p.read_text() for p in runs.glob("arm-*.json") if not p.name.endswith(".raw.json")
            )
            for model in MODELS:
                vendor = model.split("/")[0]
                self.assertNotIn(vendor, names)
                self.assertNotIn(model, text)
                self.assertNotIn(vendor, text)
                self.assertNotIn(model, receipts_text)
            blind = runs / "blind.json"
            self.assertEqual(oct(blind.stat().st_mode & 0o777), "0o600")
            mapping = json.loads(blind.read_text())["arms"]
            self.assertEqual(sorted(row["model"] for row in mapping.values()), sorted(MODELS))

    def test_arm_order_is_shuffled_by_a_recorded_seed(self):
        orders = set()
        with tempfile.TemporaryDirectory() as tmp:
            for seed in range(6):
                _, runs, _, _ = self.run_live(Path(tmp) / str(seed), seed=seed)
                blind = json.loads((runs / "blind.json").read_text())
                self.assertEqual(blind["seed"], seed)
                orders.add(tuple(blind["arms"][f"arm-{i}"]["model"] for i in (1, 2, 3)))
        self.assertGreater(len(orders), 1)

    def test_repeat_issues_separate_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, runs, calls, _ = self.run_live(Path(tmp), repeat=2)
            self.assertEqual(len(calls), 6)
            self.assertEqual(len(load_receipts(runs)), 6)

    def test_live_receipt_keeps_gateway_metadata_and_marks_zdr_unverified(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, runs, _, _ = self.run_live(Path(tmp))
            receipt = load_receipts(runs)[0]
            self.assertEqual(receipt["gateway_metadata"]["routing"]["finalProvider"], "p")
            self.assertEqual(receipt["zdr_confirmation"], "unverified")
            self.assertEqual(receipt["tokens"], 1234)
            self.assertIsNone(receipt.get("model"))

    def test_model_manifest_is_frozen_before_any_call(self):
        from unittest import mock
        from theme_replay import run as run_mod

        with tempfile.TemporaryDirectory() as tmp:
            frozen = freeze_stage0(Path(tmp) / "frozen")
            calls = []
            os.environ["AI_GATEWAY_API_KEY"] = "test-not-a-live-key"
            self.addCleanup(os.environ.pop, "AI_GATEWAY_API_KEY", None)
            with mock.patch.object(run_mod, "complete", fake_complete_factory(calls)), \
                    mock.patch.object(run_mod, "fetch_catalog", return_value=fake_catalog(MODELS[:2])):
                with self.assertRaises(RuntimeError) as raised:
                    run_mod.run_gateway(frozen, MODELS, Path(tmp) / "runs", zdr=True, no_training=True)
            self.assertIn("gemini-3.7-flash", str(raised.exception))
            self.assertEqual(calls, [])
            with mock.patch.object(run_mod, "complete", fake_complete_factory(calls)), \
                    mock.patch.object(run_mod, "fetch_catalog", return_value=fake_catalog(zdr="none")):
                with self.assertRaises(RuntimeError):
                    run_mod.run_gateway(frozen, MODELS, Path(tmp) / "runs2", zdr=True, no_training=True)
            self.assertEqual(calls, [])
            _, runs, _, _ = self.run_live(Path(tmp) / "ok")
            manifest = json.loads((runs / "model-manifest.json").read_text())
            self.assertEqual([row["id"] for row in manifest["models"]], MODELS)
            self.assertEqual(len(manifest["sha256"]), 64)


    def test_live_run_without_key_makes_no_network_request(self):
        from unittest import mock
        from theme_replay import run as run_mod

        with tempfile.TemporaryDirectory() as tmp:
            frozen = freeze_stage0(Path(tmp) / "frozen")
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("AI_GATEWAY_API_KEY", None)
                os.environ.pop("VERCEL_AI_GATEWAY_API_KEY", None)
                with mock.patch("urllib.request.urlopen") as opener:
                    with self.assertRaises(RuntimeError):
                        run_mod.run_gateway(frozen, MODELS, Path(tmp) / "runs", zdr=True, no_training=True)
                opener.assert_not_called()


class CompareTests(unittest.TestCase):
    def compare_arms(self, tmp: Path, arms: dict) -> dict:
        from theme_replay.compare import compare

        frozen = freeze_stage0(tmp / "frozen")
        src = tmp / "arms"
        src.mkdir()
        for name, body in arms.items():
            (src / f"{name}.json").write_text(json.dumps(body))
        runs = tmp / "runs"
        run_offline(frozen, src, runs, seed=1)
        return compare(frozen, runs)

    def test_identical_arms_have_no_unique_reading(self):
        body = json.loads((FIXTURES / "offline-arms" / "arm-a.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            report = self.compare_arms(Path(tmp), {"a": body, "b": dict(body, model="offline-b")})
            self.assertEqual(report["unique_readings"], [])
            self.assertEqual(len(report["shared_readings"]), 1)
            self.assertNotIn("score", json.dumps(report).lower())

    def test_bundled_arms_show_disagreement_and_counterexamples(self):
        from theme_replay.compare import compare

        with tempfile.TemporaryDirectory() as tmp:
            frozen = freeze_stage0(Path(tmp) / "frozen")
            runs = Path(tmp) / "runs"
            run_offline(frozen, FIXTURES / "offline-arms", runs, seed=1)
            report = compare(frozen, runs)
            self.assertEqual(len(report["arms"]), 3)
            self.assertGreaterEqual(len(report["unique_readings"]), 2)
            self.assertTrue(report["shared_readings"])
            # E04 is support for one arm and a counterexample for another. That is the disagreement.
            contested = {row["episode_id"] for row in report["contested_episodes"]}
            self.assertIn("E04", contested)
            self.assertIn("E01", report["disconfirming_surfaced"])
            self.assertIn("E03", report["uncited_episodes"] + [
                e for row in report["arms"].values() for e in row["cited_episodes"]])
            self.assertTrue((runs / "compare.json").exists())
            hidden = json.loads((runs / "blind.json").read_text())["arms"]
            receipts_text = " ".join(p.read_text() for p in runs.glob("arm-*.json"))
            for row in hidden.values():
                self.assertNotIn(row["model"], json.dumps(report))
                self.assertNotIn(row["model"], receipts_text)

    def test_repeat_drift_is_reported_per_hidden_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen, runs, _, _ = BlindAndRepeatTests.run_live(BlindAndRepeatTests(), Path(tmp), repeat=2)
            from theme_replay.compare import compare

            report = compare(frozen, runs)
            self.assertEqual(len(report["repeat_drift"]), 3)
            for row in report["repeat_drift"]:
                self.assertEqual(row["central_concepts_changed"], False)
                self.assertNotIn("/", row["model_group"])


if __name__ == "__main__":
    unittest.main()
