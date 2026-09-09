#!/usr/bin/env python3
"""Run the synthetic import-to-receiver acceptance without personal data."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "transcripto.py"
APP_PYTHONPATH = None


def records():
    base = {
        "sessionId": "synthetic-airport-acceptance-001",
        "cwd": "/synthetic/airport-acceptance",
    }
    return [
        dict(base, type="user", promptSource="typed",
             timestamp="2026-09-09T09:00:00Z",
             message={"role": "user", "content":
                      "For the synthetic airport project, prepare the release checklist."}),
        dict(base, type="assistant", timestamp="2026-09-09T09:00:05Z",
             message={"role": "assistant", "content": [{
                 "type": "tool_use", "id": "edit-1", "name": "Edit",
                 "input": {"file_path": "CHECKLIST.md"}}]}),
        dict(base, type="user", timestamp="2026-09-09T09:00:06Z",
             message={"role": "user", "content": [{
                 "type": "tool_result", "tool_use_id": "edit-1",
                 "content": "File updated successfully", "is_error": False}]}),
        dict(base, type="user", promptSource="typed",
             timestamp="2026-09-09T09:01:00Z",
             message={"role": "user", "content":
                      "The synthetic airport release conclusion is gate A."}),
        dict(base, type="assistant", timestamp="2026-09-09T09:01:05Z",
             message={"role": "assistant", "content": [{
                 "type": "tool_use", "id": "check-1", "name": "Bash",
                 "input": {"command": "python -m unittest tests.test_gate"}}]}),
        dict(base, type="user", promptSource="typed",
             timestamp="2026-09-09T09:02:00Z",
             credentials={"api_key": "SYNTHETIC-EXCLUDED-VALUE"},
             message={"role": "user", "content":
                      "Synthetic private record must be excluded."}),
    ]


def run_app(home, *args, expected=(0,)):
    env = dict(os.environ, HOME=str(home), PYTHONIOENCODING="utf-8")
    command = [sys.executable, str(APP)]
    if APP_PYTHONPATH:
        env["PYTHONPATH"] = APP_PYTHONPATH
        command = [sys.executable, "-m", "transcripto"]
    proc = subprocess.run(
        [*command, *map(str, args)],
        cwd=home, env=env, text=True, capture_output=True, timeout=30)
    print("$ transcripto " + " ".join(map(str, args)))
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)
    if proc.returncode not in expected:
        raise RuntimeError("command exited %d" % proc.returncode)
    return proc


def known_receiver(harness):
    if harness == "codex" and shutil.which("codex"):
        return ["codex", "exec", "--full-auto", "--skip-git-repo-check"]
    if harness == "claude" and shutil.which("claude"):
        return ["claude", "-p", "--allowedTools", "Read,Write"]
    return None


def main():
    global APP_PYTHONPATH
    parser = argparse.ArgumentParser()
    parser.add_argument("--receiver-harness", choices=("codex", "claude"),
                        default="codex")
    parser.add_argument(
        "--receiver-command", nargs=argparse.REMAINDER,
        help="authenticated subscription CLI plus flags; the bounded prompt is appended")
    parser.add_argument(
        "--receiver-unavailable",
        help="record an already-probed capability gap without probing again")
    parser.add_argument(
        "--pythonpath",
        help="exercise an installed package target instead of the source module")
    args = parser.parse_args()
    APP_PYTHONPATH = args.pythonpath

    with tempfile.TemporaryDirectory(prefix="transcripto-airport-") as temp:
        home = Path(temp)
        source = home / "synthetic-airport-session.jsonl"
        source.write_text("".join(json.dumps(row) + "\n" for row in records()))

        run_app(home, "import-session", source, "--name", "airport")
        asked = run_app(home, "ask", "What about synthetic airport release?")
        refs = re.findall(
            r"(\.transcripto/imports/claude/airport\.jsonl:L\d+)",
            asked.stdout)
        conclusion_ref = next(ref for ref in refs if ref.endswith(":L4"))
        run_app(home, "turn", conclusion_ref)
        run_app(home, "correct", conclusion_ref,
                "Gate B is required; gate A alone is not sufficient.")
        run_app(home, "import-session", source, "--name", "airport")
        run_app(home, "turn", conclusion_ref)

        brief = home / "receiver" / "continuation.md"
        run_app(
            home, "continue", "synthetic airport release",
            "--to-harness", args.receiver_harness,
            "--goal", "Finish the synthetic airport release decision.",
            "--next-action", "Write one gate-B verification note.",
            "--output", brief)
        run_app(home, "continuation-status", brief, expected=(3,))

        if args.receiver_unavailable:
            print("PENDING: " + args.receiver_unavailable)
            print("Exact missing capability: an installed, authenticated %s CLI"
                  " able to read the brief and create the bounded artifact."
                  % args.receiver_harness)
            return 3

        command = args.receiver_command or known_receiver(args.receiver_harness)
        if not command:
            print("PENDING: no installed supported receiver CLI was found.")
            print("Exact missing capability: an installed, authenticated %s CLI"
                  " able to read the brief and create the bounded artifact."
                  % args.receiver_harness)
            return 3

        continuation_id = re.search(
            r"id=([0-9a-f]{16})", brief.read_text()).group(1)
        artifact = home / "receiver" / "gate-b-verification.md"
        prompt = (
            "This is a bounded synthetic acceptance task. Read %s. "
            "Write only %s with a short gate-B verification note derived from the brief. "
            "The first line must be exactly `Continuation-ID: %s`. "
            "Do not inspect other home files or use network tools."
            % (brief, artifact, continuation_id))
        print("$ receiver: " + " ".join(command) + " <bounded synthetic prompt>")
        try:
            receiver = subprocess.run(
                [*command, prompt], cwd=home, text=True, capture_output=True,
                timeout=120)
        except subprocess.TimeoutExpired:
            print("PENDING: receiver timed out; no consumption receipt recorded.")
            return 3
        if receiver.stdout:
            print(receiver.stdout.rstrip())
        if receiver.stderr:
            print(receiver.stderr.rstrip(), file=sys.stderr)
        if receiver.returncode:
            print("PENDING: receiver exited %d; no consumption receipt recorded."
                  % receiver.returncode)
            return 3
        try:
            run_app(home, "consume-continuation", brief, "--as-harness",
                    args.receiver_harness, "--artifact", artifact)
            run_app(home, "continuation-status", brief)
        except RuntimeError as exc:
            print("PENDING: receiver output did not establish consumption (%s)." % exc)
            return 3
        return 0


if __name__ == "__main__":
    sys.exit(main())
