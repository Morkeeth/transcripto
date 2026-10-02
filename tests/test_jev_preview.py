"""Privacy previews exercise the production CLI under a refusing transport."""
import contextlib
import io
import json
import os
import socket
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import transcripto
import transcripto_jev as J


class PreviewTests(unittest.TestCase):
    def test_counts_use_real_filter_and_never_emit_text_or_verdicts(self):
        preview = J.JevPreview(home="/nonexistent/alicebob")
        texts = json.loads((ROOT / "fixtures" / "jev-preview-texts.json").read_text())
        with mock.patch.object(J, "_post", side_effect=AssertionError("network")):
            result = transcripto._jev_score(preview, texts)
        self.assertEqual(result["jev"]["eligible"], 2)
        self.assertEqual(result["jev"]["excluded_reasons"], {"topic:bank": 1})
        self.assertEqual(result["jev"]["redactions"], 1)
        self.assertIsNone(result["corrections"])
        self.assertIsNone(result["correction_rate"])
        for text in texts:
            self.assertNotIn(text, json.dumps(result))

    def test_cli_with_and_without_key_never_uses_transport(self):
        for command in (["coach", "--json"], ["export-run", "latest"]):
            for key in ("", "unused-sentinel"):
                out = io.StringIO()
                argv = ["transcripto"] + command + ["--root", str(ROOT / "fixtures-correction"),
                        "--detector", "jev", "--jev-dry-run"]
                with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": key}), \
                        mock.patch.object(sys, "argv", argv), \
                        mock.patch.object(socket, "socket", side_effect=AssertionError("socket")), \
                        mock.patch.object(J, "_post", side_effect=AssertionError("transport")), \
                        contextlib.redirect_stdout(out):
                    transcripto.main()
                result = json.loads(out.getvalue())
                self.assertGreater(result["jev"]["turns"], 0)
                self.assertEqual(result["jev"]["sent"], 0)
                self.assertEqual(result["jev"]["requests"], 0)
                self.assertIsNone(result["correction_rate"])

    def test_requires_explicit_detector(self):
        with mock.patch.object(sys, "argv", ["transcripto", "coach", "--jev-dry-run"]), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as ctx:
            transcripto.main()
        self.assertEqual(ctx.exception.code, 2)

if __name__ == "__main__":
    unittest.main()
