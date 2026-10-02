"""--detector jev: offline tests. No test here reaches the network.

HTTP is mocked by passing a fake urlopen, or by a socket guard that records and
refuses every connection attempt. The guard has a positive control (the jev
path with real urllib DOES hit it), so a green "zero sockets on the default
path" result is about the right object.
"""
import contextlib
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import transcripto  # noqa: E402
import transcripto_jev as J  # noqa: E402

# Built by concatenation so the repository's own privacy scan has nothing to match.
FAKE_GH = "gh" + "p_" + "a" * 30
FAKE_SK = "s" + "k-" + "b" * 24
HOME_PATH = "/" + "Users" + "/someone/repo/app.py"


class FakeResponse(object):
    def __init__(self, payload):
        self._b = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeOpenRouter(object):
    """Records every request body; answers each question with p from `p_for`."""

    def __init__(self, p_for=lambda text: 0.9, cost=0.00003, fail=None):
        self.bodies, self.p_for, self.cost, self.fail = [], p_for, cost, fail

    def __call__(self, req, timeout=None):
        body = json.loads(req.data.decode("utf-8"))
        self.bodies.append(body)
        self.headers = dict(req.header_items())
        if self.fail:
            raise self.fail
        answers = {}
        for name in body["questions"]:
            text = body["state"]["message"] if name == "kind" else body["state"][name]
            p = self.p_for(text)
            answers[name] = {"choice": "correction" if p >= 0.5 else "new_request",
                             "confidence": 0.9, "probabilities": {
                                 "correction": p, "new_request": 1 - p}}
        return FakeResponse({"model": "typesafe/jev-1.13-test", "answers": answers,
                             "usage": {"cost": self.cost}})


def detector(fake, **kw):
    kw.setdefault("notice", lambda line: None)
    kw.setdefault("sleep", lambda s: None)
    kw.setdefault("home", "/nonexistent/alicebob")
    return J.JevDetector("test-key", urlopen=fake, **kw)


class PrivacyFilterTests(unittest.TestCase):
    def test_private_topics_are_excluded_not_redacted(self):
        for text, why in (("move the money to savings", "topic:money"),
                          ("my wallet seed is in the drawer", "topic:wallet"),
                          ("rotate the API key please", "topic:key"),
                          ("mail me at a.b@example.org", "email"),
                          ("call +33 6 12 34 56 78 tonight", "phone"),
                          ("open 07 " + "Garden/plants.md", "note-path"),
                          ("ask alicebob about it", "account-name")):
            clean, reason, _ = J.privacy(text, home="/nonexistent/alicebob")
            self.assertIsNone(clean, text)
            self.assertEqual(reason, why, text)

    def test_secrets_and_home_paths_are_redacted(self):
        text = "no, use %s and %s in %s" % (FAKE_GH, FAKE_SK, HOME_PATH)
        clean, reason, n = J.privacy(text, home="/nonexistent/alicebob")
        self.assertIsNone(reason)
        self.assertEqual(n, 3)
        self.assertNotIn(FAKE_GH, clean)
        self.assertNotIn(FAKE_SK, clean)
        self.assertNotIn("someone", clean)
        self.assertIn("~/repo/app.py", clean)

    def test_own_home_path_is_redacted_not_excluded(self):
        home = "/" + "Users" + "/alicebob"
        clean, reason, n = J.privacy("no, edit %s/repo/app.py and -Users-alicebob-repo" % home,
                                     home=home)
        self.assertIsNone(reason)
        self.assertEqual(n, 2)
        self.assertNotIn("alicebob", clean)

    def test_ordinary_turn_passes_and_is_truncated(self):
        clean, reason, n = J.privacy("that is wrong, redo it " * 500)
        self.assertIsNone(reason)
        self.assertEqual(len(clean), J.MAX_CHARS)

    def test_whole_word_only(self):
        # "keyboard", "tokenizer", "monkey" are not the topic words.
        clean, reason, _ = J.privacy("the keyboard tokenizer monkey test", home="/x/alicebob")
        self.assertIsNone(reason)


class DetectorTests(unittest.TestCase):
    def test_excluded_turns_never_reach_the_request(self):
        fake = FakeOpenRouter()
        texts = ["no, that broke the parser", "MARKER-ZX9 my bank statement is wrong",
                 "add a test for expiry"]
        d = detector(fake)
        v = d.score(texts)
        sent = json.dumps(fake.bodies)
        self.assertNotIn("MARKER-ZX9", sent)
        self.assertNotIn("bank", sent)
        self.assertEqual(v[1], None)
        self.assertEqual(d.stats["excluded"], 1)
        self.assertEqual(d.stats["excluded_reasons"], {"topic:bank": 1})
        self.assertEqual(d.stats["sent"], 2)
        self.assertEqual(len(fake.bodies), 2)

    def test_redaction_happens_before_send(self):
        fake = FakeOpenRouter()
        detector(fake).score(["no, use %s here in %s" % (FAKE_GH, HOME_PATH)])
        sent = json.dumps(fake.bodies)
        self.assertNotIn(FAKE_GH, sent)
        self.assertNotIn("someone", sent)

    def test_single_turn_body_is_the_experiment_request(self):
        fake = FakeOpenRouter()
        detector(fake).score(["that is not what I asked"])
        body = fake.bodies[0]
        self.assertEqual(body["model"], "typesafe/jev-1.13")
        self.assertEqual(body["state"], {"message": "that is not what I asked"})
        q = body["questions"]["kind"]
        self.assertEqual(q["type"], "choice")
        self.assertEqual(q["instructions"], J.INSTRUCTIONS)
        self.assertEqual(set(q["criteria"]), {"correction", "new_request", "continue_or_approve",
                                              "information_or_question", "other"})
        self.assertEqual(fake.headers.get("Authorization"), "Bearer test-key")

    def test_threshold_applies_to_p_correction(self):
        fake = FakeOpenRouter(p_for=lambda t: 0.32)
        self.assertEqual(detector(fake, threshold=0.30).score(["x y"]), [True])
        self.assertEqual(detector(fake, threshold=0.35).score(["x y"]), [False])

    def test_batching_sends_keyed_questions_and_maps_answers_back(self):
        fake = FakeOpenRouter(p_for=lambda t: 0.9 if t.startswith("wrong") else 0.1)
        texts = ["wrong %d" % i if i % 2 else "fine %d" % i for i in range(5)]
        d = detector(fake, batch=3)
        v = d.score(texts)
        self.assertEqual(len(fake.bodies), 2)
        self.assertEqual(sorted(fake.bodies[0]["questions"]), ["m0", "m1", "m2"])
        self.assertEqual(fake.bodies[0]["state"]["m1"], "wrong 1")
        self.assertIn('"m1"', fake.bodies[0]["questions"]["m1"]["instructions"])
        self.assertEqual(v, [False, True, False, True, False])
        self.assertEqual(d.stats["requests"], 2)
        self.assertAlmostEqual(d.stats["cost_usd"], 0.00006)

    def test_network_error_gives_no_verdict(self):
        fake = FakeOpenRouter(fail=urllib.error.URLError("down"))
        d = detector(fake)
        self.assertEqual(d.score(["no, wrong", "redo it"]), [None, None])
        self.assertEqual(d.stats["errors"], 1)
        self.assertEqual(d.stats["budget_unsent"], 1)
        self.assertTrue(d.stats["cost_unknown"])
        self.assertEqual(d.stats["scored"], 0)
        self.assertEqual(len(fake.bodies), J.RETRIES)

    def test_server_error_and_bad_payload_give_no_verdict(self):
        err = urllib.error.HTTPError(J.URL, 500, "boom", {}, None)
        self.assertEqual(detector(FakeOpenRouter(fail=err)).score(["redo"]), [None])

        def empty(req, timeout=None):
            return FakeResponse({"answers": {}})
        self.assertEqual(detector(empty).score(["redo"]), [None])

    def test_refused_key_stops_after_one_request(self):
        for code in (401, 402, 403):
            fake = FakeOpenRouter(fail=urllib.error.HTTPError(J.URL, code, "no", {}, None))
            with self.assertRaises(J.JevAuthError) as cm:
                detector(fake).score(["a b", "c d", "e f"])
            self.assertEqual(len(fake.bodies), 1)
            self.assertNotIn("test-key", str(cm.exception))

    def test_key_refused_mid_run_keeps_scored_turns(self):
        calls = []

        def flaky(req, timeout=None):
            calls.append(1)
            if len(calls) > 2:
                raise urllib.error.HTTPError(J.URL, 402, "no credit", {}, None)
            return FakeOpenRouter(p_for=lambda t: 0.9)(req, timeout)
        d = detector(flaky, workers=1)
        v = d.score(["t %d" % i for i in range(6)])
        self.assertEqual(v[:2], [True, True])
        self.assertEqual(v[2:], [None] * 4)
        self.assertEqual(d.stats["scored"], 2)
        self.assertIn("402", d.stats["auth_error"])
        self.assertEqual(d.stats["auth_unsent"], 3)
        self.assertEqual(len(calls), 3)

    def test_spend_cap_stops_sending(self):
        fake = FakeOpenRouter(cost=0.6)
        d = detector(fake, max_usd=1.0, workers=1)
        v = d.score(["t %d" % i for i in range(6)])
        self.assertTrue(d.stats["budget_stopped"])
        self.assertEqual(len(fake.bodies), 2)
        self.assertEqual(v.count(None), 4)
        self.assertEqual(d.stats["budget_unsent"], 4)

    def test_notice_names_what_and_where_before_the_first_request(self):
        fake, seen = FakeOpenRouter(), []
        d = detector(fake, notice=lambda line: seen.append((line, len(fake.bodies))))
        d.score(["no, wrong", "my salary"])
        self.assertEqual(len(seen), 1)
        line, requests_before = seen[0]
        self.assertEqual(requests_before, 0)
        self.assertIn("sends 1 of 2", line)
        self.assertIn("excluded 1", line)
        self.assertIn(J.URL, line)
        self.assertIn(J.MODEL, line)
        self.assertNotIn("\n", line)


# ---------------------------------------------------------------------------
# CLI: the default path opens no socket, and the guard can go red
# ---------------------------------------------------------------------------
class SocketGuard(object):
    def __init__(self):
        self.attempts = 0

    def refuse(self, *a, **k):
        self.attempts += 1
        raise OSError("socket guard: network access in an offline test")

    def __enter__(self):
        self._p = [mock.patch.object(socket, "socket", side_effect=self.refuse),
                   mock.patch.object(socket, "create_connection", side_effect=self.refuse),
                   mock.patch.object(socket, "getaddrinfo", side_effect=self.refuse)]
        for p in self._p:
            p.start()
        return self

    def __exit__(self, *a):
        for p in self._p:
            p.stop()
        return False


def human(text):
    return {"type": "user", "promptSource": "typed", "sessionId": "jev-test",
            "message": {"content": text}}


def agent(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="transcripto-jev-")
        self.addCleanup(self.tmp.cleanup)
        self.root = os.path.join(self.tmp.name, "projects")
        os.makedirs(os.path.join(self.root, "p"))
        self.session = os.path.join(self.root, "p", "jev-test.jsonl")
        with open(self.session, "w") as f:
            for r in (human("Refactor the parser in src/parser.py to stream lines"),
                      agent("Done, the parser streams now."),
                      human("no, that broke the header handling, revert it"),
                      agent("Reverted."),
                      human("MARKER-QQ7 my bank login expired, skip that for now"),
                      agent("OK."),
                      human("add a unit test for the expiry branch")):
                f.write(json.dumps(r) + "\n")

    def run_main(self, *argv, env=None):
        out, err = io.StringIO(), io.StringIO()
        code = 0
        environ = dict(os.environ)
        environ.pop("OPENROUTER_API_KEY", None)
        environ.update(env or {})
        with mock.patch.object(sys, "argv", ["transcripto"] + list(argv)), \
                mock.patch.dict(os.environ, environ, clear=True), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                transcripto.main()
            except SystemExit as e:
                code = e.code or 0
        return code, out.getvalue(), err.getvalue()

    def test_default_path_opens_no_socket(self):
        with SocketGuard() as g:
            # Even with a key in the environment, the default path stays local.
            env = {"OPENROUTER_API_KEY": "should-not-be-used",
                   "TRANSCRIPTO_CORRECTION": "jev"}
            c1, out1, _ = self.run_main("coach", "--root", self.root, "--json", env=env)
            c2, out2, _ = self.run_main("export-run", self.session, "--root", self.root, env=env)
            c3, _, _ = self.run_main("coach", "--root", self.root, env=env)
        self.assertEqual((c1, c2, c3), (0, 0, 0))
        self.assertEqual(g.attempts, 0)
        r1, r2 = json.loads(out1), json.loads(out2)
        self.assertNotIn("correction_detector", r1)
        self.assertNotIn("jev", r2)
        self.assertEqual(r1["human_turns"], 4)

    def test_default_path_never_imports_the_network_module(self):
        # A fresh interpreter, so this test's own import of transcripto_jev
        # cannot hide a top-level import in transcripto.py.
        code = ("import sys; sys.path.insert(0, %r); sys.argv = ['transcripto', 'coach', "
                "'--root', %r, '--json']\nimport transcripto\ntry:\n    transcripto.main()\n"
                "except SystemExit:\n    pass\nsys.stderr.write('JEV_LOADED=%%s' %% "
                "('transcripto_jev' in sys.modules))" % (str(ROOT), self.root))
        env = dict(os.environ, OPENROUTER_API_KEY="should-not-be-used")
        p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           env=env, timeout=60)
        self.assertIn("JEV_LOADED=False", p.stderr)

    def test_guard_positive_control_jev_path_does_hit_it(self):
        # Without this, a guard that never fires would make the test above green
        # about the wrong object.
        with SocketGuard() as g:
            d = J.JevDetector("dummy", notice=lambda l: None, sleep=lambda s: None,
                              home="/nonexistent/alicebob")
            self.assertEqual(d.score(["no, wrong file"]), [None])
        self.assertGreater(g.attempts, 0)

    def test_missing_key_is_a_clear_error_and_sends_nothing(self):
        with SocketGuard() as g:
            code, out, err = self.run_main("coach", "--root", self.root, "--detector", "jev")
        self.assertEqual(code, 2)
        self.assertIn("OPENROUTER_API_KEY", err)
        self.assertIn("Nothing was sent", err)
        self.assertEqual(g.attempts, 0)

    def test_missing_key_falls_back_to_regex_only_when_asked(self):
        with SocketGuard() as g:
            code, out, err = self.run_main("coach", "--root", self.root, "--json",
                                           "--detector", "jev", "--jev-fallback-regex")
        self.assertEqual(code, 0)
        self.assertEqual(g.attempts, 0)
        self.assertIn("using the local regex", err)
        self.assertNotIn("correction_detector", json.loads(out))

    def test_bad_threshold_is_rejected(self):
        code, _, err = self.run_main("coach", "--root", self.root, "--detector", "jev",
                                     "--jev-threshold", "1.5")
        self.assertEqual(code, 2)
        self.assertIn("--jev-threshold", err)

    def test_coach_with_jev_reports_scored_denominator_and_exclusions(self):
        fake = FakeOpenRouter(p_for=lambda t: 0.8 if "broke" in t else 0.05)
        real = J.JevDetector.__init__

        def init(self, key, **kw):
            kw.update(urlopen=fake, sleep=lambda s: None, home="/nonexistent/alicebob")
            real(self, key, **kw)
        with mock.patch.object(J.JevDetector, "__init__", init):
            code, out, err = self.run_main("coach", "--root", self.root, "--json",
                                           "--detector", "jev",
                                           env={"OPENROUTER_API_KEY": "test-key"})
        self.assertEqual(code, 0, err)
        r = json.loads(out)
        self.assertNotIn("MARKER-QQ7", json.dumps(fake.bodies))
        self.assertEqual(r["correction_detector"], "jev")
        self.assertEqual(r["human_turns"], 4)
        self.assertEqual(r["jev"]["excluded"], 1)
        self.assertEqual(r["jev"]["scored"], 3)
        self.assertEqual(r["corrections"], 1)
        self.assertEqual(r["correction_rate"], round(1 / 3, 3))
        self.assertEqual(r["correction_rate_denominator"], "jev.scored")
        self.assertIn("transcripto: --detector jev sends 3 of 4", err)
        self.assertNotIn("test-key", out + err)

    def test_export_run_with_jev(self):
        fake = FakeOpenRouter(p_for=lambda t: 0.8 if "broke" in t else 0.05)
        real = J.JevDetector.__init__

        def init(self, key, **kw):
            kw.update(urlopen=fake, sleep=lambda s: None, home="/nonexistent/alicebob")
            real(self, key, **kw)
        with mock.patch.object(J.JevDetector, "__init__", init):
            code, out, err = self.run_main("export-run", self.session, "--root", self.root,
                                           "--detector", "jev", "--jev-batch", "2",
                                           env={"OPENROUTER_API_KEY": "test-key"})
        self.assertEqual(code, 0, err)
        r = json.loads(out)
        self.assertEqual(r["typed_turns"], 4)
        self.assertEqual(r["jev"]["scored"], 3)
        self.assertEqual(r["corrections"], 1)
        self.assertEqual(len(fake.bodies), 2)

    def test_refused_key_exits_with_no_verdicts(self):
        fake = FakeOpenRouter(fail=urllib.error.HTTPError(J.URL, 402, "no", {}, None))
        real = J.JevDetector.__init__

        def init(self, key, **kw):
            kw.update(urlopen=fake, sleep=lambda s: None, home="/nonexistent/alicebob")
            real(self, key, **kw)
        with mock.patch.object(J.JevDetector, "__init__", init):
            code, out, err = self.run_main("coach", "--root", self.root, "--json",
                                           "--detector", "jev",
                                           env={"OPENROUTER_API_KEY": "test-key"})
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("HTTP 402", err)
        self.assertEqual(len(fake.bodies), 1)


if __name__ == "__main__":
    unittest.main()
