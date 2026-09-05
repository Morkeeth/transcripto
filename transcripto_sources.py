"""Read-only discovery of local histories. Inventory is not an indexed corpus."""
import json
import os
import sqlite3
import shlex
from datetime import datetime, timezone
from pathlib import Path


def identify(path):
    """Inspect a bounded prefix; unknown data never defaults to Claude."""
    try:
        with open(path, "rb") as stream:
            nonblank = False
            for _ in range(32):
                line = stream.readline(65537)
                if not line:
                    return ("unidentified", "No recognized JSON record.") if nonblank else ("empty", None)
                nonblank = nonblank or bool(line.strip())
                if len(line) > 65536:
                    return "unidentified", "First records exceed the discovery prefix limit."
                try:
                    row = json.loads(line)
                except (ValueError, UnicodeError):
                    continue
                if not isinstance(row, dict):
                    continue
                kind = row.get("type")
                if kind == "session_meta" or (kind in ("response_item", "event_msg", "turn_context") and isinstance(row.get("payload"), dict)):
                    return "codex", None
                if {"session_id", "ts", "text"}.issubset(row):
                    return "input-history", "Input history has no agent response or action evidence."
                if "role" in row and isinstance(row.get("message"), dict) and "promptSource" not in row:
                    return "cursor", None
                if (kind in ("user", "assistant") and isinstance(row.get("message"), dict)) or kind in ("file-history-snapshot", "queue-operation", "progress") or "sessionId" in row:
                    return "claude", None
                return "unsupported", "Unrecognized transcript envelope."
            return "unidentified", "No recognized record in the first 32 lines."
    except OSError as exc:
        return "inaccessible", str(exc)


def candidates(root):
    """Visit provider transcript directories, never configuration or session indexes."""
    root = Path(os.path.abspath(os.path.expanduser(root)))
    errors = []
    try:
        root.stat()
    except FileNotFoundError:
        return [], "missing", []
    except OSError as exc:
        return [], "inaccessible", [str(exc)]
    if root.is_file():
        return [str(root)], "available", []
    bases = [root]
    if root.name == ".codex":
        bases = [root / "sessions", root / "archived_sessions"]
    elif root.name == ".cursor":
        bases = list((root / "projects").glob("*/agent-transcripts"))
    found = []
    for base in bases:
        if not base.exists():
            continue
        for folder, dirs, files in os.walk(base, onerror=lambda e: errors.append(str(e))):
            dirs[:] = [d for d in dirs if d not in (".git", ".tmp", "node_modules")]
            found.extend(str(Path(folder) / f) for f in files
                         if f.endswith(".jsonl") and f not in ("history.jsonl", "session_index.jsonl"))
    return sorted(set(found)), "partial" if errors else ("available" if found else "empty"), errors


def inventory(roots, harness=None, database=None):
    indexed = {}
    index_warnings = {}
    cache_error = None
    if database and os.path.isfile(database):
        try:
            with sqlite3.connect(Path(database).absolute().as_uri() + "?mode=ro", uri=True) as con:
                indexed = dict(con.execute("SELECT session_file,mtime FROM indexed"))
                if 'warnings' in {r[1] for r in con.execute('PRAGMA table_info(indexed)')}:
                    for path, encoded in con.execute('SELECT session_file,warnings FROM indexed'):
                        try:
                            index_warnings[path] = json.loads(encoded or '[]')
                        except (ValueError, TypeError):
                            index_warnings[path] = ['Index warnings could not be decoded.']
        except sqlite3.Error as exc:
            cache_error = str(exc)
    sources = []
    for root in roots:
        paths, state, warnings = candidates(root)
        counts = {}
        selected = fresh = stale = 0
        latest = None
        for path in paths:
            provider, warning = identify(path)
            counts[provider] = counts.get(provider, 0) + 1
            if warning:
                warnings.append({"path": path, "reason": warning})
            for message in index_warnings.get(path, []):
                warnings.append({"path": path, "reason": message, "basis": "indexed parse diagnostics"})
            if provider not in ("claude", "codex", "cursor") or (harness and provider != harness):
                continue
            selected += 1
            try:
                modified = os.stat(path).st_mtime
            except OSError as exc:
                warnings.append({"path": path, "reason": str(exc)})
                continue
            if path in indexed:
                if abs(indexed[path] - modified) < 1e-6:
                    fresh += 1
                else:
                    stale += 1
            if latest is None or modified > latest[0]:
                latest = (modified, path, provider)
        if state == "available" and not selected:
            state = "inaccessible" if set(counts) == {'inaccessible'} else ("unsupported" if counts and not any(p in counts for p in ("claude", "codex", "cursor")) else "no-selected-harness")
        if state == 'available' and warnings:
            state = 'partial'
        not_indexed = selected - fresh - stale
        index_state = ('no-selected-sources' if not selected else 'not-indexed' if not_indexed == selected
                       else 'partial' if stale or not_indexed or warnings else 'fresh-by-mtime')
        sources.append({"root": os.path.abspath(os.path.expanduser(root)), "state": state,
                        "files": len(paths), "formats": counts, "selected_files": selected,
                        "index": {"state": index_state, "fresh_by_mtime": fresh, "changed": stale, "not_indexed": not_indexed},
                        "latest_file": {"path": latest[1], "provider": latest[2], "modified_at": datetime.fromtimestamp(latest[0], timezone.utc).isoformat()} if latest else None,
                        "warnings": warnings})
    return {"schema": "transcripto.sources/1", "observed_at": datetime.now(timezone.utc).isoformat(),
            "index_coverage": "partial" if cache_error or any(s['index']['state'] != 'fresh-by-mtime' for s in sources) else "fresh-by-mtime",
            "sources": sources, "index_error": cache_error,
            "limitations": ["Format detection inspects at most 32 records of 64 KiB each; unidentified is not empty.",
                            "File modification time orders discovery, not human activity or completed work.",
                            "Fresh-by-mtime is an index hint, not content-version verification."]}


def describe(report):
    lines = ["YOUR LOCAL HISTORIES"]
    for source in report["sources"]:
        cache = source["index"]
        lines.append("%s · %s · %d supported file(s) · %d not indexed · %d changed" % (
            source["root"], source["state"], source["selected_files"], cache["not_indexed"], cache["changed"]))
        for provider, count in sorted(source["formats"].items()):
            lines.append("  %s: %d" % (provider, count))
        if source["warnings"]:
            lines.append("  %d discovery warning(s); use index --status --json for details." % len(source["warnings"]))
    available = next((s for s in report["sources"] if s["selected_files"]), None)
    if available:
        latest = available["latest_file"]
        selector = " --root " + shlex.quote(available["root"])
        if latest:
            selector += " --harness " + latest["provider"]
        lines.extend(["", 'Try: transcripto ask "a word you remember"' + selector,
                      "Search builds its local index on first use.",
                      "Or: transcripto replay latest" + selector + "   (no index required)"])
    else:
        lines.extend(["", "No supported history is available in this selection.",
                      "Point --root at an existing transcript directory, or try transcripto replay --demo."])
    if report["index_error"]:
        lines.append("Index could not be read: " + report["index_error"])
    return "\n".join(lines)
