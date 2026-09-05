"""The replay CLI: requests, attempts, and their recorded results."""
import json
import os
import shlex
import tempfile
from collections import Counter

from transcripto_core import episodes, human_text, read_session, safe_text
from transcripto_evidence import authorship

PROXY = "Status describes a tool result, not task correctness. Missing results stay unknown."


def title(ep):
    failed = {(e["kind"], e["target"]) for e in ep["events"] if e["status"] == "failed"}
    seen = set()
    for i in range(len(ep["events"]) - 1, -1, -1):
        e = ep["events"][i]
        key = (e["kind"], e["target"])
        if key in seen:
            continue
        seen.add(key)
        if e["status"] == "succeeded" and key in failed:
            if any(x["status"] == "failed" and (x["kind"], x["target"]) == key for x in ep["events"][:i]):
                return "THE COMEBACK"
    if failed:
        return "THE SNAG"
    if any(e["status"] == "unknown" for e in ep["events"]):
        return "THE MISSING RECEIPT"
    return "ON THE RECORD" if ep["events"] else "THE ANSWER"


def _short(text, width=100):
    text = " ".join(safe_text(text).split())
    return text if len(text) <= width else text[:width - 1] + "…"


def _demo(path):
    rows = [{"type": "user", "promptSource": "typed", "message": {"content": "Fix the login redirect and run its tests."}}]
    for n, name, inp, result, error in [
        (1, "Edit", {"file_path": "src/login.py"}, "Error: text not found", True),
        (2, "Edit", {"file_path": "src/login.py"}, "File updated successfully", False),
        (3, "Bash", {"command": "pytest tests/test_login.py"}, "Process exited with code 1", True),
        (4, "Edit", {"file_path": "src/login.py"}, "File updated successfully", False),
        (5, "Bash", {"command": "pytest tests/test_login.py"}, "Process exited with code 0", False),
    ]:
        rows += [{"type": "assistant", "message": {"content": [{"type": "tool_use", "id": str(n), "name": name, "input": inp}]}},
                 {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": str(n), "content": result, "is_error": error}]}}]
    rows.append({"type": "assistant", "message": {"content": [{"type": "text", "text": "The redirect is fixed and the tests pass."}]}})
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def cmd_replay(args, paths):
    diagnostics = []
    target = args.target
    temp = tempfile.TemporaryDirectory(prefix="transcripto-demo-") if args.demo else None
    try:
        if temp:
            target = os.path.join(temp.name, "demo.jsonl")
            _demo(target)
        is_path = os.path.isfile(os.path.expanduser(target))
        if is_path:
            candidates = [os.path.expanduser(target)]
            query = None
        else:
            candidates = sorted(paths, key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)
            session = getattr(args, "session", None)
            query = None if target == "latest" or session else target.lower()
            if session:
                matches = [p for p in candidates if session in os.path.basename(p)]
                if len(matches) > 1:
                    print("Session prefix is ambiguous. Use a full transcript path.")
                    return 2
                candidates = matches
        selected, seen = [], 0
        for path in candidates:
            # Subagent transcripts have no submitted request from this operator.
            if not is_path and "subagents" in path.split(os.sep):
                continue
            rows, harness = read_session(path, diagnostics)
            if not is_path and target == 'latest' and any(r.get('_session_kind') == 'subagent' for r in rows):
                continue
            if not any(human_text(r) for r in rows):
                continue
            eps = episodes(rows, path)
            for i, ep in enumerate(eps, 1):
                ep.update(number=i, harness=harness, title=title(ep), authorship=authorship(harness, ep.get('prompt_source')))
            if args.episode is not None:
                eps = [ep for ep in eps if ep["number"] == args.episode]
            if query:
                eps = [ep for ep in eps if query in ep["prompt"].lower()]
            if args.failures:
                eps = [ep for ep in eps if any(e["status"] == "failed" for e in ep["events"])]
            if not eps:
                if args.episode is not None and not query:
                    break  # an absent request number must not select an older session
                continue
            if not args.all and not query:
                # Last request with a tool attempt, unless an episode was explicitly selected.
                eps = [next((ep for ep in reversed(eps) if ep["events"]), eps[-1])]
            selected.extend(reversed(eps) if query else eps)
            seen += 1
            if not query or len(selected) >= args.limit:
                break
        if query:
            selected = selected[:args.limit]
        if not selected:
            if args.json:
                print(json.dumps({"schema": "transcripto.replay/1", "episodes": [], "warnings": diagnostics, "proxy": PROXY}))
            else:
                print("No matching request session found.")
                print("Try: transcripto replay --demo, --harness codex, --harness cursor, or --root <dir>.")
                for warning in diagnostics:
                    print("warning: " + safe_text(warning))
            return 2
        if args.share:
            counts = Counter(e["status"] for ep in selected for e in ep["events"])
            print("Transcripto replay · %d request(s) · %d succeeded · %d failed · %d unknown" % (
                len(selected), counts["succeeded"], counts["failed"], counts["unknown"]))
            print(PROXY)
            if args.demo:
                print("Synthetic demo; not measured user data.")
            return 0
        if args.json:
            print(json.dumps({"schema": "transcripto.replay/1", "synthetic": args.demo,
                              "episodes": selected, "warnings": diagnostics, "proxy": PROXY}, indent=2))
            return 0
        if args.demo:
            print("SYNTHETIC DEMO · all prompts and results below are invented\n")
        for ep in selected:
            print("%s · %s · request %d" % (ep["title"], ep["harness"], ep["number"]))
            label = 'You asked' if ep['authorship']['kind'] == 'human' else 'Request (authorship unknown)'
            print('%s: "%s"\n' % (label, _short(ep["prompt"], 160)))
            if ep["events"] and all(e["result_line"] is None for e in ep["events"]):
                print("  This export has no matching result records. These are attempts; '?' does not mean failure.\n")
            if not ep["events"]:
                print("  No tool calls recorded. An answer may have been the whole task.")
            start = 0
            if not args.all and len(ep["events"]) > args.events:
                anchor = next((i for i, e in enumerate(ep["events"]) if e["status"] == "failed"),
                              next((i for i, e in enumerate(ep["events"]) if e["kind"] in ("edit", "commit", "check")), 0))
                start = max(0, anchor - 2)
            end = len(ep["events"]) if args.all else min(start + args.events, len(ep["events"]))
            if start:
                print("  … %d earlier events. Showing the context around the first failure or change." % start)
            # A contiguous window retains the sequence around the failure.
            for i, e in enumerate(ep["events"][start:end], start + 1):
                mark = {"succeeded": "OK", "failed": "FAIL", "unknown": "?"}[e["status"]]
                print("  %2d  %-4s %-10s %s" % (i, mark, e["kind"], _short(e["target"], 90)))
                ref = "call L%s" % e["line"]
                if e["result_line"]:
                    ref += " → result L%s" % e["result_line"]
                print("                 %s  [%s]" % (e["evidence"], ref))
            if len(ep["events"]) > end:
                print("  … %d more events. Use --all to inspect the full sequence." % (len(ep["events"]) - end))
            if ep["reply"]:
                print('\nAgent said: "%s"' % _short(ep["reply"], 160))
            counts = Counter(e["status"] for e in ep["events"])
            print("\nRecorded: %d succeeded · %d failed · %d unknown" % (counts["succeeded"], counts["failed"], counts["unknown"]))
            if not args.demo:
                print("Source: %s:%s" % (safe_text(ep["source"]), ep["line"]))
                print("Replay this request: transcripto replay %s --episode %d --all" % (safe_text(shlex.quote(ep["source"])), ep["number"]))
            print(PROXY + "\n")
        for warning in diagnostics:
            print("warning: " + safe_text(warning))
        print("Next: replay --failures · replay \"a request you remember\" · search \"a topic\"")
        return 0
    finally:
        if temp:
            temp.cleanup()
