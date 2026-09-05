"""Transcript normalization and evidence. No execution, network, or persistent state.

Calls describe attempts. Only a matching tool result can establish execution status.
The normalized rows deliberately retain the Claude message envelope for consumers.
"""
import json
import hashlib
import os
import re
import shlex
import sys
from datetime import datetime, timedelta, timezone

MAX_FILE_BYTES = 128 * 1024 * 1024
MAX_LINE_BYTES = 8 * 1024 * 1024
MAX_TEXT = 16000
WRITES = {"Write", "Edit", "MultiEdit", "NotebookEdit", "StrReplace", "apply_patch"}
ALIASES = {"StrReplace": "Edit", "Shell": "Bash", "exec_command": "Bash",
           "shell_command": "Bash", "local_shell": "Bash", "shell": "Bash"}
INJECTED = ("AGENTS.md instructions", "<INSTRUCTIONS>", "<environment_context>",
            "<user_instructions>", "<collaboration_mode>", "permissions instructions",
            "The following is the Codex agent history")
PREFIXES = ("<image ", "</image>", "<codex_internal_context", "# Files mentioned by the user:")


def safe_text(value):
    """Remove terminal controls, including OSC clipboard/title sequences."""
    value = re.sub(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)", "", str(value))
    value = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", value)
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]", "", value)


def text_of(value):
    if isinstance(value, str):
        return value[:MAX_TEXT]
    if isinstance(value, list):
        return "\n".join(text_of(b.get("text", "")) for b in value if isinstance(b, dict))[:MAX_TEXT]
    if isinstance(value, dict):
        return text_of(value.get("output", value.get("content", value.get("text", ""))))
    return ""


def iter_json(path, diagnostics=None):
    counts = {"invalid": 0, "oversize": 0}
    try:
        with open(path, "rb") as f:
            if os.fstat(f.fileno()).st_size > MAX_FILE_BYTES:
                raise ValueError("file exceeds 128 MiB safety limit; split it into smaller JSONL files")
            line_no = 0
            while True:
                raw = f.readline(MAX_LINE_BYTES + 1)
                if not raw:
                    break
                line_no += 1
                if len(raw) > MAX_LINE_BYTES:
                    while raw and not raw.endswith(b"\n"):
                        raw = f.readline(MAX_LINE_BYTES + 1)
                    counts["oversize"] += 1
                    continue
                if not raw.strip():
                    continue
                try:
                    d = json.loads(raw)
                    if not isinstance(d, dict):
                        raise ValueError("record must be an object")
                    if "message" in d and not isinstance(d["message"], (dict, type(None))):
                        raise ValueError("message must be an object")
                    if "payload" in d and not isinstance(d["payload"], (dict, type(None))):
                        raise ValueError("payload must be an object")
                except (ValueError, UnicodeError, RecursionError):
                    counts["invalid"] += 1
                    continue
                d["_line"] = line_no
                d["_record_sha256"] = hashlib.sha256(raw.rstrip(b"\r\n")).hexdigest()
                yield d
    except (OSError, ValueError) as exc:
        warning = "%s: %s" % (path, exc)
        if diagnostics is not None:
            diagnostics.append(warning)
        else:
            print("warning: " + safe_text(warning), file=sys.stderr)
    if any(counts.values()):
        warning = "%s: skipped %d malformed and %d oversized record(s)" % (path, counts["invalid"], counts["oversize"])
        if diagnostics is not None:
            diagnostics.append(warning)
        else:
            print("warning: " + safe_text(warning), file=sys.stderr)


def human_text(row):
    if row.get("type") != "user" or row.get("promptSource") not in ("typed", "queued"):
        return ""
    if row.get("isMeta") or row.get("isSidechain") or row.get("toolUseResult") is not None:
        return ""
    content = (row.get("message") or {}).get("content")
    if isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
        return ""
    return text_of(content).strip()


def _codex_human_content(content):
    blocks = content if isinstance(content, list) else [{"text": content}]
    kept = []
    starts = ("# AGENTS.md instructions", "<INSTRUCTIONS>", "<environment_context>",
              "<user_instructions>", "<collaboration_mode>", "<permissions instructions>",
              "The following is the Codex agent history added since your last approval")
    for block in blocks:
        if not isinstance(block, dict):
            continue
        text = text_of(block.get("text", ""))
        if text.lstrip().startswith(starts + PREFIXES):
            continue
        kept.append(text)
    return "\n".join(kept).strip()


def _arguments(value):
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except (ValueError, RecursionError):
            pass
    return {}


def normalize_call(block, codex=False):
    b = dict(block)
    original = b.get("name") if isinstance(b.get("name"), str) else "tool"
    name = original.split(".")[-1]
    raw = b.get("arguments", b.get("input", {}))
    inp = _arguments(raw)
    command = inp.get("command", inp.get("cmd", ""))
    if isinstance(command, list):
        command = shlex.join(str(x) for x in command)
    if original == "container.exec" and command:
        name = "exec_command"
    # Read a single static exec_command argument inside a Codex JS wrapper.
    # Multiple child calls cannot be associated with individual results reliably.
    if name in ("exec", "js") and isinstance(raw, str):
        matches = re.findall(r"\b(?:cmd|command)\s*:\s*(\"(?:\\.|[^\"\\])*\")", raw)
        if len(matches) == 1 and len(re.findall(r"\btools\.\w+\s*\(", raw)) == 1 and re.search(r"\b(?:tools\.)?exec_command\s*\(", raw):
            try:
                command = json.loads(matches[0])
                name = "exec_command"
            except ValueError:
                pass
        patch_call = re.search(r"\btools\.apply_patch\s*\(\s*(\"(?:\\.|[^\"\\])*\"|[A-Za-z_]\w*)\s*\)", raw)
        if patch_call and len(re.findall(r"\btools\.\w+\s*\(", raw)) == 1:
            literal = patch_call.group(1)
            if not literal.startswith('"'):
                assignment = re.search(r"\b(?:const|let|var)\s+" + re.escape(literal) + r"\s*=\s*(\"(?:\\.|[^\"\\])*\")", raw)
                literal = assignment.group(1) if assignment else ""
            try:
                patch = json.loads(literal)
                raw = patch.replace("\\n", "\n")
                name = "apply_patch"
            except ValueError:
                pass
    if name == "apply_patch":
        patch = inp.get("patch", inp.get("input", ""))
        if not isinstance(patch, str) or not patch:
            patch = raw if isinstance(raw, str) else ""
            try:
                decoded = json.loads(patch)
                if isinstance(decoded, str):
                    patch = decoded
            except ValueError:
                pass
        paths = re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", patch, re.M)
        inp["paths"] = paths
        if paths:
            inp["file_path"] = paths[0]
        name = "Edit"
    if "path" in inp and "file_path" not in inp:
        inp["file_path"] = inp["path"]
    if "paths" in inp:
        inp["paths"] = [p for p in inp["paths"] if isinstance(p, str)] if isinstance(inp["paths"], list) else []
    if command:
        inp["command"] = command
    call_id = b.get("call_id") or b.get("id")
    b.update(type="tool_use", name=ALIASES.get(name, name), input=inp,
             original_name=original, id=call_id if isinstance(call_id, str) else None,
             execution_status="unknown", result_line=None,
             evidence="No matching tool result recorded.")
    return b


def operation(call):
    name, inp = call.get("name"), call.get("input") or {}
    if name in WRITES:
        return "edit"
    if name != "Bash":
        return "read" if name in ("Read", "Glob", "Grep", "WebSearch", "WebFetch") else "tool"
    command = inp.get("command", "")
    if not isinstance(command, str):
        return "shell"
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>()")
        lexer.whitespace_split = True
        words = list(lexer)
    except ValueError:
        return "shell"
    # No substring matching: echo 'git commit' and git commit --dry-run are not commits.
    if not words or any(w and all(c in ";&|<>()" for c in w) for w in words) or "$(" in command or "`" in command or "\n" in command:
        return "shell"
    if os.path.basename(words[0]) in ("bash", "sh", "zsh") and len(words) == 3 and words[1] in ("-c", "-lc"):
        # Classify a single shell script without executing it.
        return operation({"name": "Bash", "input": {"command": words[2]}})
    executable = os.path.basename(words[0])
    if executable == "git":
        rest = words[1:]
        while rest and rest[0] in ("-C", "-c", "--git-dir", "--work-tree"):
            rest = rest[2:]
        if rest and rest[0] == "commit" and not any(x in rest for x in ("--dry-run", "--help", "-h")):
            return "commit"
        if rest and (rest[0] == "revert" or (rest[0] == "reset" and "--hard" in rest)):
            return "rollback"
    if executable in ("pytest", "jest", "vitest", "unittest") or (
            executable in ("python", "python3") and any(x in words for x in ("pytest", "unittest"))) or (
            executable in ("npm", "pnpm", "yarn", "cargo", "go", "bun") and "test" in words):
        return "check"
    return "shell"


def result_status(value, is_error=None, call=None):
    """Read result metadata before stdout. Printed exit-code text is not metadata."""
    if is_error is True:
        detail = " ".join(safe_text(text_of(value)).split())[:160]
        return "failed", ("Tool error: " + detail) if detail else "Tool returned an error."
    if call and call.get("name") in ("Read", "Glob", "Grep", "WebFetch", "WebSearch"):
        return "succeeded", "Tool returned a result."
    text = text_of(value)
    structured = value if isinstance(value, dict) else _arguments(value)
    if isinstance(value, list):
        for block in value:
            candidate = _arguments(block.get("text")) if isinstance(block, dict) else {}
            if "exit_code" in candidate or "metadata" in candidate:
                structured = candidate
                break
    metadata = structured.get("metadata") if isinstance(structured.get("metadata"), dict) else {}
    if "exit_code" not in structured and "exit_code" in metadata:
        structured = dict(structured, exit_code=metadata["exit_code"])
    if structured.get("isError") is True or structured.get("is_error") is True:
        return "failed", "Tool returned an error."
    running = re.search(r"^(?:Script running with cell ID|Process running with session ID|Command running in background)", text, re.M)
    if running or (structured.get("session_id") is not None and structured.get("exit_code") is None):
        return "unknown", "Command still running at this result."
    code = structured.get("exit_code")
    if isinstance(code, int):
        return ("succeeded", "Exit code 0.") if code == 0 else ("failed", "Exit code %d." % code)
    if is_error is False:
        return "succeeded", "Tool reported success."
    # Native text-only command envelopes put exit status before the Output section.
    header = re.split(r"(?:^|\n)(?:Final output:|Output:)", text, maxsplit=1)[0]
    codes = [int(x) for x in re.findall(r"^(?:Process exited with code|Process exit code:|Exit code:)\s*(-?\d+)\s*$", header, re.M | re.I)]
    if codes:
        if any(c != 0 for c in codes):
            return "failed", "Exit code %d." % next(c for c in codes if c != 0)
        return "succeeded", "Exit code 0."
    # Codex exec wraps child results as JSON text blocks. Decode the envelope;
    # never search the quoted stdout value for an exit code.
    decoded = []
    decoder = json.JSONDecoder()
    for line in text.splitlines():
        if line.lstrip().startswith("{"):
            try:
                obj, _ = decoder.raw_decode(line.lstrip())
                if isinstance(obj, dict) and "exit_code" in obj:
                    decoded.append(obj)
            except ValueError:
                pass
    if decoded:
        codes = [o.get("exit_code") for o in decoded]
        if any(isinstance(c, int) and c != 0 for c in codes):
            return "failed", "A child command returned a nonzero exit code."
        if all(c == 0 for c in codes):
            return "succeeded", "Recorded child commands exited 0."
        return "unknown", "A child command has no final exit status."
    if call and call.get("name") == "Bash":
        return "unknown", "Result recorded without an exit status."
    if call and call.get("name") in WRITES:
        if re.match(r"(?:Error:|Failed to |.*patch verification failed)", text):
            return "failed", "Change tool reported an error."
        if re.match(r"(?:Success[.!] Updated the following files:|Successfully |Applied patch|Applied \d+ edits to [^\n]+:|The file [^\n]+ has been [^\n]*successfully)", text, re.I):
            return "succeeded", "Tool reported a successful change."
        return "unknown", "Result recorded without an explicit change status."
    return "unknown", "Result recorded, but this tool has no recognized completion contract."


def _cursor_stamp(text):
    m = re.search(r"<timestamp>(.*?)</timestamp>", text, re.S)
    if not m:
        return ""
    raw = m.group(1)
    offset = re.search(r"UTC([+-])(\d{1,2})(?::(\d{2}))?", raw)
    if not offset:
        return ""  # the machine reading this transcript may have a different timezone
    tz = timezone(timedelta(minutes=(int(offset[2]) * 60 + int(offset[3] or 0)) * (1 if offset[1] == "+" else -1)))
    for fmt in ("%A, %b %d, %Y, %I:%M %p", "%A, %B %d, %Y, %I:%M %p"):
        try:
            return datetime.strptime(raw.split(" (")[0], fmt).replace(tzinfo=tz).isoformat()
        except ValueError:
            pass
    return ""


def read_session(path, diagnostics=None):
    rows, harness, sid, cwd = [], "claude", os.path.splitext(os.path.basename(path))[0], ""
    calls, results = {}, []
    last_ts = ""
    owner_sid, context_sid, history_boundary, session_kind = None, None, None, None
    for d in iter_json(path, diagnostics):
        if d.get("type") == "session_meta":
            harness = "codex"
            p = d.get("payload") or {}
            if owner_sid is None:
                owner_sid = p.get("id") or sid
                history_boundary = p.get("subagent_history_start_ordinal")
                session_kind = p.get("thread_source")
            context_sid = p.get("id") or owner_sid
            sid, cwd = owner_sid, p.get("cwd") or cwd
            continue
        if d.get("type") == "turn_context" and harness == "codex":
            cwd = (d.get("payload") or {}).get("cwd") or cwd
            continue
        if d.get("type") == "response_item":
            harness = "codex"
            p = d.get("payload") or {}
            meta = {"timestamp": d.get("timestamp", ""), "cwd": cwd, "sessionId": sid, "_line": d["_line"], "_record_sha256": d["_record_sha256"]}
            meta['_channel'] = p.get('channel') if isinstance(p.get('channel'), str) else None
            ordinal = d.get("ordinal")
            inherited = (ordinal < history_boundary) if isinstance(ordinal, int) and isinstance(history_boundary, int) else None
            meta.update(_inherited=inherited, _origin_session_id=context_sid if inherited else owner_sid,
                        _session_kind=session_kind, _timestamp_basis="native record" if d.get("timestamp") else "unknown")
            pt = p.get("type")
            if pt == "message":
                text = text_of(p.get("content"))
                role = p.get("role")
                if role == "user":
                    text = _codex_human_content(p.get("content"))
                    if not text:
                        continue
                    d = dict(meta, type="user", promptSource="typed", message={"role": "user", "content": text})
                elif role == "assistant":
                    d = dict(meta, type="assistant", message={"role": "assistant", "content": [{"type": "text", "text": text}]})
                else:
                    continue
            elif pt in ("function_call", "custom_tool_call", "local_shell_call"):
                b = dict(p, type="tool_use")
                if pt == "local_shell_call":
                    b["name"] = "local_shell"
                    b["input"] = p.get("action") if isinstance(p.get("action"), dict) else {}
                d = dict(meta, type="assistant", message={"role": "assistant", "content": [b]})
            elif pt in ("function_call_output", "custom_tool_call_output"):
                d = dict(meta, type="user", message={"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": p.get("call_id"),
                    "content": p.get("output")}]})
            elif pt == "agent_message":
                d = dict(meta, type="user", promptSource="agent", message={"role": "user", "content": text_of(p.get("content", p.get("message", "")))})
            else:
                continue
        elif {"session_id", "ts", "text"}.issubset(d) and "message" not in d:
            harness = "codex-history"
            continue
        elif "role" in d and "message" in d and "promptSource" not in d:
            harness = "cursor"
            is_child = 'subagents' in os.path.normpath(path).split(os.sep)
            msg = d.get("message") or {}
            content = msg.get("content")
            raw_text = content if isinstance(content, str) else "\n".join(
                b.get("text", "") for b in (content if isinstance(content, list) else [])
                if isinstance(b, dict) and isinstance(b.get("text"), str))
            last_ts = _cursor_stamp(raw_text) or last_ts
            match = re.search(r"<user_query>\s*(.*?)\s*</user_query>", raw_text, re.S)
            d["type"] = d.get("role")
            if d["type"] == "user" and match:
                d["promptSource"] = "agent" if is_child else "typed"
                msg["content"] = match.group(1)
            if is_child:
                d['_session_kind'] = 'subagent'
            d["_timestamp_basis"] = "native record" if d.get("timestamp") else ("context clock, carried forward" if last_ts else "unknown")
            d.update(timestamp=d.get("timestamp") or last_ts, sessionId=sid)
        if d.get("type") not in ("user", "assistant"):
            continue
        d.setdefault("sessionId", sid)
        for field in ("sessionId", "timestamp", "cwd", "gitBranch"):
            if field in d and not isinstance(d[field], str):
                d[field] = ""
        msg = d.get("message") or {}
        d["message"] = msg
        c = msg.get("content")
        if isinstance(c, list):
            clean = []
            for b in c:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use":
                    b = normalize_call(b)
                    b["line"] = d["_line"]
                    if b.get("id"):
                        calls.setdefault(b["id"], []).append(b)
                elif b.get("type") == "tool_result":
                    results.append((b.get("tool_use_id"), b.get("content"), b.get("is_error"), d["_line"]))
                    b = dict(b, content=text_of(b.get("content")))
                elif b.get("type") == "text":
                    b = dict(b, text=text_of(b.get("text")))
                clean.append(b)
            msg["content"] = clean
        elif isinstance(c, str):
            msg["content"] = c[:MAX_TEXT]
        rows.append(d)
    for call_id, result, error, line in results:
        if not isinstance(call_id, str):
            continue
        eligible = [c for c in calls.get(call_id, []) if c["line"] < line and c.get("result_line") is None]
        # A repeated ID does not authorize copying a later result to earlier calls.
        for call in eligible[-1:]:
            status, evidence = result_status(result, error, call)
            if call.get("name") in ("exec", "js") and status == "succeeded":
                status, evidence = "unknown", "Wrapper returned; child operations were not fully reconstructed."
            call.update(execution_status=status, evidence=evidence, result_line=line)
    return rows, harness


def episodes(rows, source=""):
    """One submitted request per episode. Never absorb a later human request."""
    out, current = [], None
    for row in rows:
        if current is not None and current.get("inherited") is True and row.get("_inherited") is False:
            current = None  # child actions cannot become consequences of an inherited parent request
        prompt = human_text(row)
        if prompt:
            current = {"prompt": prompt, "line": row.get("_line"), "timestamp": row.get("timestamp", ""),
                       "source": source, "session_id": row.get("sessionId", ""), "prompt_source": row.get('promptSource'), "inherited": row.get("_inherited"), "events": [], "reply": ""}
            out.append(current)
            continue
        if current is None or row.get("type") != "assistant":
            continue
        content = (row.get("message") or {}).get("content")
        for b in content if isinstance(content, list) else []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text":
                current["reply"] = text_of(b.get("text"))
            elif b.get("type") == "tool_use":
                inp = b.get("input") or {}
                target = inp.get("file_path") or inp.get("notebook_path") or inp.get("command") or b.get("original_name", b.get("name", "tool"))
                if inp.get("paths"):
                    target = ", ".join(inp["paths"])
                current["events"].append({"tool": b.get("original_name", b.get("name")),
                    "kind": operation(b), "target": str(target), "status": b.get("execution_status", "unknown"),
                    "evidence": b.get("evidence", "No matching tool result recorded."),
                    "timestamp": row.get("timestamp") or None,
                    "line": row.get("_line"), "result_line": b.get("result_line")})
        if isinstance(content, str):
            current["reply"] = text_of(content)
    return out
