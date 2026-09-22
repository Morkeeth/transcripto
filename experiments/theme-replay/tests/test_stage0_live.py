import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from theme_replay import openrouter
from theme_replay.citations import load_frozen
from theme_replay.memo import decide, score_memo, write_packet
from theme_replay.run import parse_output_step, run_openrouter

from test_theme_replay import freeze_stage0

CORPUS_SHA = "ad4cd9260a25d6561cd5421e4eb07b189284df22626a59bac4c04739ec8b5392"


def good_memo():
    return {
        "memo": [
            {
                "claim": "Corrections appear where the request named the wrong object.",
                "type": "pattern",
                "evidence": [
                    {"episode_id": "E04", "line": 2, "quote": "No, I meant the header parser"},
                    {"episode_id": "E08", "line": 2, "quote": "shorter please"},
                    {"episode_id": "E04", "line": 4, "quote": "File updated successfully", "claimed_status": "succeeded"},
                ],
                "counter_episodes": ["E02"],
            },
            {
                "claim": "Unknown results stay unknown.",
                "type": "exception",
                "evidence": [
                    {"episode_id": "E03", "line": 2, "quote": "No matching tool result recorded.", "claimed_status": "unknown"},
                    {"episode_id": "E07", "line": 2, "quote": "No matching tool result recorded.", "claimed_status": "unknown"},
                ],
                "counter_episodes": [],
            },
        ],
        "reading_decisions": [],
        "what_changed_my_view": "no readings",
    }


class OpenRouterTransportTests(unittest.TestCase):
    def test_corpus_hash_is_frozen(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen = freeze_stage0(Path(tmp) / "frozen")
            manifest = json.loads((frozen / "dataset-manifest.json").read_text())
            self.assertEqual(manifest["files"]["episodes.jsonl"], CORPUS_SHA)

    def test_body_asks_for_zdr_and_cost_and_is_not_gateway_shaped(self):
        body = openrouter.request_body("openai/gpt-5.6-sol", "hi", max_tokens=99)
        self.assertEqual(body["provider"]["zdr"], True)
        self.assertEqual(body["provider"]["data_collection"], "deny")
        self.assertEqual(body["usage"], {"include": True})
        self.assertEqual(body["max_tokens"], 99)
        self.assertNotIn("providerOptions", body)
        self.assertNotIn("temperature", body)

    def test_jev_is_refused_on_openrouter_too(self):
        with self.assertRaises(RuntimeError):
            openrouter.request_body("typesafe/jev-1.13", "hi")

    def test_fenced_json_is_parsed_and_marked(self):
        out, step = parse_output_step('```json\n{"codes": []}\n```')
        self.assertEqual(out, {"codes": []})
        self.assertEqual(step, "fence_stripped")
        out, step = parse_output_step('Here you go {"codes": []}')
        self.assertIn("raw_text", out)
        self.assertEqual(step, "not_json")

    def test_ledger_stops_at_ceiling(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = openrouter.Ledger(Path(tmp) / "spend.json", 0.05)
            ledger.check()
            ledger.add("a", "m", 0.03)
            ledger.check()
            ledger.add("b", "m", 0.03)
            with self.assertRaises(openrouter.SpendCeiling):
                ledger.check()
            # A second process reading the same ledger also stops.
            with self.assertRaises(openrouter.SpendCeiling):
                openrouter.Ledger(Path(tmp) / "spend.json", 0.05).check()

    def test_no_key_means_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen = freeze_stage0(Path(tmp) / "frozen")
            env = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}
            with mock.patch.dict(os.environ, env, clear=True), \
                 mock.patch("urllib.request.urlopen") as net:
                with self.assertRaises(RuntimeError):
                    run_openrouter(frozen, ["openai/gpt-5.6-sol"], Path(tmp) / "runs",
                                   ledger_path=Path(tmp) / "spend.json", max_cost=1.0)
                net.assert_not_called()

    def test_run_records_cost_tokens_latency_and_stays_blind(self):
        catalog = {"data": [{"id": m, "supported_parameters": []} for m in ("a/one", "b/two")]}
        valid = json.dumps({
            "codes": [{"label": "c", "episode_ids": ["E04"], "evidence": [{"episode_id": "E04", "line": 2, "quote": "No, I meant"}]}],
            "themes": [{"name": "t", "codes": ["c"], "supporting_episodes": ["E04"], "disconfirming_episodes": ["E01"]}],
        })

        def fake_complete(model, prompt, max_tokens=None):
            return {"payload": {"model": model, "provider": "P", "choices": [{"message": {"content": "```json\n" + valid + "\n```"}, "finish_reason": "stop"}],
                                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15, "cost": 0.01}},
                    "http_status": 200, "latency_ms": 12.5, "request_meta": {"model": model}}

        with tempfile.TemporaryDirectory() as tmp:
            frozen = freeze_stage0(Path(tmp) / "frozen")
            runs = Path(tmp) / "runs"
            with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "x"}), \
                 mock.patch.object(openrouter, "fetch_catalog", return_value=catalog), \
                 mock.patch.object(openrouter, "complete", side_effect=fake_complete):
                summary = run_openrouter(frozen, ["a/one", "b/two"], runs, ledger_path=Path(tmp) / "spend.json",
                                         max_cost=1.0, repeat=2, seed=3)
            self.assertEqual(len(summary["arms"]), 4)
            self.assertAlmostEqual(summary["spent_usd_ledger_total"], 0.04)
            receipt = json.loads((runs / "arm-1.json").read_text())
            self.assertEqual(receipt["cost"], 0.01)
            self.assertEqual(receipt["tokens"], 15)
            self.assertEqual(receipt["latency_ms"], 12.5)
            self.assertEqual(receipt["parse_step"], "fence_stripped")
            self.assertEqual(receipt["errors"], [])
            self.assertEqual(receipt["zdr_confirmation"], "unverified")
            text = (runs / "arm-1.json").read_text()
            self.assertNotIn("a/one", text)
            self.assertNotIn("b/two", text)

    def test_run_stops_when_ceiling_reached_mid_run(self):
        catalog = {"data": [{"id": "a/one", "supported_parameters": []}]}

        def fake_complete(model, prompt, max_tokens=None):
            return {"payload": {"choices": [{"message": {"content": "{}"}}], "usage": {"cost": 0.6}},
                    "http_status": 200, "latency_ms": 1, "request_meta": {}}

        with tempfile.TemporaryDirectory() as tmp:
            frozen = freeze_stage0(Path(tmp) / "frozen")
            with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "x"}), \
                 mock.patch.object(openrouter, "fetch_catalog", return_value=catalog), \
                 mock.patch.object(openrouter, "complete", side_effect=fake_complete) as calls:
                with self.assertRaises(openrouter.SpendCeiling):
                    run_openrouter(frozen, ["a/one"], Path(tmp) / "runs", ledger_path=Path(tmp) / "spend.json",
                                   max_cost=1.0, repeat=3, seed=1)
            self.assertEqual(calls.call_count, 2)


class MemoScoringTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.index = load_frozen(freeze_stage0(Path(self.tmp.name) / "frozen"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_good_memo_has_no_hard_failure_and_counts_proxies(self):
        score = score_memo(good_memo(), self.index)
        self.assertEqual(score["hard_failures"], [])
        self.assertTrue(score["proxies"]["F1"])
        self.assertTrue(score["proxies"]["F2"])
        self.assertTrue(score["proxies"]["F3"])
        self.assertFalse(score["proxies"]["F4"])
        self.assertFalse(score["proxies"]["F5"])
        self.assertEqual(score["proxy_count"], 3)

    def test_upgraded_unknown_is_a_hard_failure_and_earns_no_proxy(self):
        memo = good_memo()
        memo["memo"][1]["evidence"][0]["claimed_status"] = "succeeded"
        score = score_memo(memo, self.index)
        self.assertTrue(any("records unknown" in h for h in score["hard_failures"]))
        self.assertFalse(score["proxies"]["F3"])

    def test_fabricated_quote_and_ghost_episode_are_hard_failures(self):
        memo = good_memo()
        memo["memo"][0]["evidence"][0]["quote"] = "the user was angry"
        memo["memo"][0]["counter_episodes"] = ["E99"]
        score = score_memo(memo, self.index)
        self.assertTrue(any("does not resolve" in h for h in score["hard_failures"]))
        self.assertTrue(any("E99" in h for h in score["hard_failures"]))

    def test_non_json_memo_is_a_hard_failure(self):
        score = score_memo({"raw_text": "prose"}, self.index)
        self.assertEqual(score["hard_failures"], ["output is not the JSON object"])

    def test_decision_rule(self):
        def row(p, h=0, e=1.0):
            return {"proxy_count_mean": p, "hard_failures_total": h, "exception_plus_open_mean": e}
        self.assertEqual(decide({"M": row(4), "R": row(2.5), "S": row(2)})["answer"], "YES")
        self.assertEqual(decide({"M": row(2), "R": row(2), "S": row(3)})["answer"], "NO")
        self.assertEqual(decide({"M": row(3), "R": row(2.5), "S": row(2)})["answer"], "CANNOT_TELL")
        self.assertEqual(decide({"M": row(4, h=1), "R": row(2), "S": row(2)})["answer"], "NO")
        self.assertEqual(decide({"M": row(4)})["answer"], "CANNOT_TELL")

    def test_packet_is_blind(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = [{"memo": m, "condition": m[0], "output": good_memo()} for m in ("B1", "S1", "R1", "M1")]
            write_packet(Path(tmp), calls, seed=5)
            text = (Path(tmp) / "human-packet.md").read_text()
            for label in ("B1", "S1", "R1", "M1", "condition", "proxy"):
                self.assertNotIn(label, text)
            self.assertEqual(oct((Path(tmp) / "packet-key.json").stat().st_mode & 0o777), "0o600")


if __name__ == "__main__":
    unittest.main()
