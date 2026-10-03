"""Exercise the installed console script outside the checkout, with no network.
Usage: python tests/check_packaged_jev_preview.py /absolute/bin/transcripto
All input is an explicitly synthetic committed fixture.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    executable = str(Path(sys.argv[1]).resolve())
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        corpus = base / "corpus"
        corpus.mkdir()
        (corpus / "session.jsonl").write_text("".join(json.dumps(row) + "\n" for row in json.loads((ROOT / "fixtures" / "jev-preview-episode.json").read_text())))
        guard = base / "guard"
        guard.mkdir()
        (guard / "sitecustomize.py").write_text(
            "import socket, ssl, urllib.request\n"
            "def refuse(*args, **kwargs):\n"
            "    raise RuntimeError('offline package check refused network')\n"
            "socket.socket = refuse\nsocket.create_connection = refuse\n"
            "urllib.request.urlopen = refuse\n", encoding="utf8")
        allowed = {"schema", "harness", "files", "total_records", "correction_detector",
                   "corrections", "correction_rate", "correction_rate_denominator", "jev"}
        for key in ("", "unused-offline-sentinel"):
            env = dict(os.environ, PYTHONPATH=str(guard), OPENROUTER_API_KEY=key)
            for command in (["coach", "--json"], ["export-run", "latest"]):
                result = subprocess.run([executable] + command + ["--root", str(corpus),
                    "--detector", "jev", "--jev-dry-run"], cwd=tmp, env=env,
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                data = json.loads(result.stdout)
                assert set(data) <= allowed, "Unexpected non-preview fields"
                assert data["schema"] == "transcripto.jev-privacy-preview/1"
                assert data["jev"]["turns"] == data["jev"]["eligible"] == 1
                assert data["jev"]["sent"] == data["jev"]["requests"] == 0
                assert data["corrections"] is data["correction_rate"] is None
                for private in ("private-preview", "synthetic-private-tool-output", "synthetic-privacy-preview-session", str(corpus)):
                    assert private not in result.stdout, "Preview exposed source details"
            human = subprocess.run([executable, "coach", "--root", str(corpus), "--detector", "jev",
                                    "--jev-dry-run"], cwd=tmp, env=env, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            assert "Nothing sent" in human.stdout and "YOUR REQUESTS" not in human.stdout
    print("Installed CLI: counts-only JSON and terminal preview pass, with and without key; network refused.")


if __name__ == "__main__":
    main()
