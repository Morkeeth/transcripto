#!/usr/bin/env python3
"""Instant replay for coding agents. Calls are attempts; results are evidence.

Local transcript inspection for Claude Code, Codex, and Cursor. Stdlib only.
"""
import sys, os, json, glob, re, sqlite3, argparse, math, shlex, tempfile
import transcripto_core as core
from transcripto_replay import cmd_replay
from datetime import datetime, timezone

# The tool ships under the `transcripto` console script and is also
# run as `python3 transcripto.py`. Every hint we print must name the command the
# reader actually typed, otherwise we tell a stranger to run a binary they do not
# have on PATH.
def _prog():
    n = os.path.basename(sys.argv[0] or "")
    if n.endswith(".py"):
        n = n[:-3]
    return "transcripto"


PROG = _prog()

# The single source of truth for the version, so `--version` cannot drift from the
# packaging. A stranger who reads the README on GitHub and installs from PyPI can be
# holding a different build than the one the README describes, and until this flag
# existed there was no way for them to tell which.
VERSION = "0.2.1"

USAGE = """
  transcripto                         replay your latest human session
  transcripto replay --demo           try a labelled synthetic session
  transcripto replay --failures       jump to a failed tool call
  transcripto replay "<request>"       find and replay something you asked
  transcripto import-example           add a public synthetic trace locally
  transcripto import-lab               add labelled cross-harness failed/ok/? traces
  transcripto ask "<topic>"            find your own words across harnesses
  transcripto changes                  inspect cited before/correction sequences
  transcripto handoff "<correction>"   prepare a correction for another receiver
  transcripto receive-handoff …        prepare a brief with Open + outcomes
  transcripto quickstart               offline wheel install / search / reopen
  transcripto search "<topic>"         search prompts, replies, and tool text
  transcripto find <file>              find recorded attempts and file operations
  transcripto coach                    descriptive request history, never grades
  transcripto export-run latest        machine-readable session summary

  --harness claude|codex|cursor        select one harness (default: all)
  --root <dir>                        use a transcript directory
  cost is Claude-only; replay needs no index. Search refreshes its index automatically.
"""


HOME = os.path.expanduser("~")
ROOTS = [os.path.join(HOME, ".claude", "projects"),
         os.path.join(HOME, ".codex"), os.path.join(HOME, ".cursor"),
         os.path.join(HOME, ".transcripto", "imports")]
DB = os.path.join(HOME, ".trace", "trace.db")
HARNESS = None

FILE_TOOLS = {"Write": "write", "Edit": "edit", "Read": "read",
              "NotebookEdit": "edit", "MultiEdit": "edit"}


def connect(require_index=True):
    """Open the local index. Six commands (search/ask/find/trace/sessions/stats)
    READ it and are meaningless without it; `index` and `watch` BUILD it and pass
    require_index=False. Before this guard existed a cold start printed a raw
    `sqlite3.OperationalError: no such table: messages_fts` — and three of the six
    printed it and still exited 0."""
    os.makedirs(os.path.dirname(DB), mode=0o700, exist_ok=True)
    if not os.path.exists(DB):
        fd = os.open(DB, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
    os.chmod(DB, 0o600)
    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    for sidecar in (DB + "-wal", DB + "-shm"):
        if os.path.exists(sidecar):
            os.chmod(sidecar, 0o600)
    if require_index:
        init_schema(con)
        _index_once(con, progress=sys.stderr.isatty())
        # Temporary read views keep --root/--harness queries inside their selected
        # corpus while the persistent index can retain other harnesses.
        clauses = []
        for root in ROOTS:
            root = os.path.abspath(os.path.expanduser(root))
            literal = root.replace("'", "''")
            clauses.append("session_file='%s' OR substr(session_file,1,%d)='%s/'" %
                           (literal, len(root) + 1, literal))
        scope = "(" + (" OR ".join(clauses) or "0") + ")"
        if HARNESS:
            scope += " AND harness='%s'" % HARNESS
        for table in ("messages", "files"):
            con.execute("CREATE TEMP VIEW %s AS SELECT * FROM main.%s WHERE %s" % (table, table, scope))
    return con


SCHEMA_VERSION = 5  # new columns go in ADDITIVE_COLUMNS; only a tokenizer or is_human change rebuilds


# Columns added after the first schema. A store that lacks only these is migrated in
# place with ALTER TABLE ADD COLUMN, never dropped. Before this, a version mismatch
# dropped every table, and an older writer that did not know a column inserted rows
# with it NULL and no error (the unlabelled-harness rows of September 2026).
ADDITIVE_COLUMNS = (
    ("messages", "harness", "TEXT"),
    ("messages", "source_line", "INTEGER"),
    ("messages", "synthetic", "INTEGER DEFAULT 0"),
    ("files", "harness", "TEXT"),
    ("indexed", "warnings", "TEXT"),
)
KNOWN_HARNESSES = ("claude", "codex", "codex-history", "cursor")


def _columns(con, table):
    return {r[1] for r in con.execute("PRAGMA table_info(%s)" % table)}


def _needs_rebuild(con):
    """True only when the store cannot be migrated in place: messages predates
    is_human (every row would need its authorship recomputed) or the FTS table
    uses an old tokenizer. Missing ADDITIVE_COLUMNS are migrated, not rebuilt."""
    t = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'").fetchone()
    if not t:
        return False  # fresh db, nothing to migrate
    if "is_human" not in _columns(con, "messages"):
        return True
    fts = con.execute("SELECT sql FROM sqlite_master WHERE name='messages_fts'").fetchone()
    if fts and "porter" not in (fts[0] or ""):
        return True
    return False


def _migrate_columns(con):
    """Add any missing ADDITIVE_COLUMNS. Returns the list of 'table.column' added.
    If source_line was missing, every indexed file is marked stale so files still
    on disk are re-read with line numbers on this index pass."""
    added = []
    for table, column, decl in ADDITIVE_COLUMNS:
        if not con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
            continue  # created fresh below
        if column not in _columns(con, table):
            con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, column, decl))
            added.append("%s.%s" % (table, column))
    if "messages.source_line" in added:
        con.execute("UPDATE indexed SET mtime=-1")
    return added


def harness_from_path(path):
    """The harness a transcript came from, read from its path alone, or None.
    The innermost known directory wins: ~/.claude, ~/.codex, ~/.cursor, or
    ~/.transcripto/imports/<harness>/."""
    parts = [p for p in str(path).replace("\\", "/").split("/") if p]
    found = None
    for i, part in enumerate(parts):
        if part == ".claude":
            found = "claude"
        elif part == ".codex":
            found = "codex-history" if parts[-1] == "history.jsonl" else "codex"
        elif part == ".cursor":
            found = "cursor"
        elif part == ".transcripto" and parts[i + 1:i + 2] == ["imports"] and len(parts) > i + 2:
            if parts[i + 2] in KNOWN_HARNESSES:
                found = parts[i + 2]
    return found


def unlabelled_counts(con):
    """(messages, files) rows whose harness is NULL or empty."""
    return tuple(con.execute("SELECT COUNT(*) FROM %s WHERE harness IS NULL OR harness=''" % t).fetchone()[0]
                 for t in ("messages", "files"))


def backfill_harness(con, apply=False):
    """Label unlabelled rows from their session_file path. Returns a report dict.
    With apply=False nothing is written. Never touches user_version or the schema."""
    by_file = {}
    for table in ("messages", "files"):
        for f, n in con.execute("SELECT session_file, COUNT(*) FROM %s WHERE harness IS NULL OR harness='' "
                                "GROUP BY session_file" % table):
            by_file.setdefault(f, {"messages": 0, "files": 0})[table] = n
    report = {"unlabelled_before": dict(zip(("messages", "files"), unlabelled_counts(con))),
              "labels": {}, "unresolved_files": 0, "unresolved_rows": 0, "applied": bool(apply)}
    for f, counts in sorted(by_file.items(), key=lambda kv: kv[0] or ""):
        label = harness_from_path(f or "")
        if not label:
            report["unresolved_files"] += 1
            report["unresolved_rows"] += counts["messages"] + counts["files"]
            continue
        slot = report["labels"].setdefault(label, {"files": 0, "messages": 0, "file_rows": 0})
        slot["files"] += 1
        slot["messages"] += counts["messages"]
        slot["file_rows"] += counts["files"]
        if apply:
            for table in ("messages", "files"):
                con.execute("UPDATE %s SET harness=? WHERE session_file=? AND (harness IS NULL OR harness='')"
                            % table, (label, f))
    if apply:
        con.commit()
    report["unlabelled_after"] = dict(zip(("messages", "files"), unlabelled_counts(con)))
    return report


def init_schema(con):
    if _needs_rebuild(con):
        con.executescript(
            "DROP TABLE IF EXISTS messages_fts; DROP TABLE IF EXISTS messages;"
            "DROP TABLE IF EXISTS files; DROP TABLE IF EXISTS indexed;")
        con.commit()
    added = _migrate_columns(con)
    if added:
        print("migrated index schema: added " + ", ".join(added), file=sys.stderr)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS messages(
      id INTEGER PRIMARY KEY, session_id TEXT, session_file TEXT, project TEXT,
      ts TEXT, role TEXT, cwd TEXT, git_branch TEXT, text TEXT,
      is_human INTEGER DEFAULT 0, prompt_source TEXT, harness TEXT,
      source_line INTEGER, synthetic INTEGER DEFAULT 0);
    -- porter stemming: `ask "frustration"` also matches frustrated/frustrating.
    CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
      text, content='messages', content_rowid='id', tokenize="porter unicode61");
    CREATE TABLE IF NOT EXISTS files(
      id INTEGER PRIMARY KEY, path TEXT, name TEXT, action TEXT,
      session_id TEXT, session_file TEXT, ts TEXT, cwd TEXT, harness TEXT);
    CREATE INDEX IF NOT EXISTS idx_files_name ON files(name);
    CREATE INDEX IF NOT EXISTS idx_msg_human ON messages(is_human, ts);
    -- Partial indexes keep the unlabelled-row check on every open to a lookup.
    CREATE INDEX IF NOT EXISTS idx_msg_unlabelled ON messages(session_file) WHERE harness IS NULL OR harness='';
    CREATE INDEX IF NOT EXISTS idx_files_unlabelled ON files(session_file) WHERE harness IS NULL OR harness='';
    CREATE TABLE IF NOT EXISTS indexed(session_file TEXT PRIMARY KEY, mtime REAL, warnings TEXT);

    -- Stable READ-ONLY views for consumers (ZUP, Helicon). The contract: consumers
    -- open the db read-only and SELECT from these views; they never write. See READ-CONTRACT.md.
    DROP VIEW IF EXISTS v_sessions;
    CREATE VIEW v_sessions AS
      SELECT m.session_id, m.project, m.harness,
             MAX(m.ts) AS last_ts, MIN(m.ts) AS first_ts,
             COUNT(*) AS n_messages,
             SUM(CASE WHEN m.role='assistant' THEN 1 ELSE 0 END) AS assistant_turns,
             (SELECT cwd FROM messages c WHERE c.session_id=m.session_id AND c.harness=m.harness AND c.cwd!=''
              ORDER BY c.ts DESC LIMIT 1) AS cwd
      FROM messages m GROUP BY m.session_id, m.harness;
    DROP VIEW IF EXISTS v_file_touches;
    CREATE VIEW v_file_touches AS
      SELECT name, path, action, session_id, ts, cwd, harness FROM files;
    DROP VIEW IF EXISTS v_index_health;
    CREATE VIEW v_index_health AS SELECT session_file, mtime, warnings FROM indexed;
    -- is_human=1 marks a turn the operator actually typed (promptSource typed/queued, not
    -- injected/tool/peer). See ask_gate() + READ-CONTRACT.md.
    DROP VIEW IF EXISTS v_messages;
    CREATE VIEW v_messages AS
      SELECT id, session_id, project, ts, role, cwd, git_branch, text,
             is_human, prompt_source, harness, source_line, synthetic FROM messages;
    """)
    con.execute("PRAGMA user_version=%d" % SCHEMA_VERSION)
    con.commit()
    # A writer that does not know the harness column leaves it NULL without error.
    # Detect that on every open and label the rows from their paths.
    if any(unlabelled_counts(con)):
        report = backfill_harness(con, apply=True)
        labelled = report["unlabelled_before"]["messages"] - report["unlabelled_after"]["messages"]
        if labelled:
            print("labelled %d unlabelled message row(s) from their source paths; %d row(s) unresolved"
                  % (labelled, report["unresolved_rows"]), file=sys.stderr)


def extract(d):
    """Return (role, text, [(action, path)]) from one transcript record."""
    msg = d.get("message") or {}
    role = msg.get("role") or d.get("type")
    parts, files = [], []
    c = msg.get("content")
    if isinstance(c, str):
        parts.append(c)
    elif isinstance(c, list):
        for b in c:
            if not isinstance(b, dict):
                continue
            bt = b.get("type")
            if bt == "text":
                parts.append(b.get("text", ""))
            elif bt == "tool_use":
                name, inp = b.get("name", ""), _tool_input(b)
                fp = inp.get("file_path") or inp.get("path") or inp.get("notebook_path")
                paths = inp.get("paths") or ([fp] if fp else [])
                for fp in paths:
                    if not isinstance(fp, str):
                        continue
                    action = FILE_TOOLS.get(name, name.lower())
                    if action in ("write", "edit") and b.get("execution_status") != "succeeded":
                        action = "attempt:" + action
                    files.append((action, fp))
                for k in ("command", "description", "prompt", "pattern", "query", "url", "file_path"):
                    v = inp.get(k)
                    if isinstance(v, str) and v:
                        parts.append("[%s.%s] %s" % (name, k, v))
            elif bt == "tool_result":
                cont = b.get("content")
                if isinstance(cont, str):
                    parts.append(cont[:2000])
                elif isinstance(cont, list):
                    for x in cont:
                        if isinstance(x, dict) and x.get("type") == "text":
                            parts.append(x.get("text", "")[:2000])
    return role, "\n".join(p for p in parts if p), files


def is_human_turn(d):
    """True iff this transcript record is a message the operator actually TYPED.

    The measured gate (see reference_transcript_authorship_gate.md): at fleet scale
    ~95% of `type: user` records are NOT the operator — tool results, injected skill
    bodies, spawned sub-agent prompts, and cross-session peer messages all arrive as
    `type: user`. The one reliable signal is Claude Code's own `promptSource`.
      keep:  promptSource in (typed, queued)   — operator input, live or while busy
      drop:  isMeta (skill bodies/images) · toolUseResult (tool output) ·
             isSidechain (spawned agent's prompt) · sdk/system (judges, peers)
    """
    return bool(core.human_text(d))


def _drop_indexed_file(con, path):
    for mid, text in con.execute("SELECT id,text FROM messages WHERE session_file=?", (path,)).fetchall():
        con.execute("INSERT INTO messages_fts(messages_fts,rowid,text) VALUES('delete',?,?)", (mid, text))
    con.execute("DELETE FROM messages WHERE session_file=?", (path,))
    con.execute("DELETE FROM files WHERE session_file=?", (path,))
    con.execute("DELETE FROM indexed WHERE session_file=?", (path,))


def _index_once(con, progress=False):
    """Incrementally index every changed/new transcript. Returns (new_sessions, new_msgs).

    progress=True prints a heartbeat to stderr. A first index over a few thousand
    transcripts takes minutes, and a silent terminal for that long reads as a hang,
    which is the point at which a first-time user kills it.
    """
    seen = _coach_files(ROOTS, HARNESS)
    for (path,) in con.execute("SELECT session_file FROM indexed").fetchall():
        try:
            os.stat(path)
        except FileNotFoundError:
            _drop_indexed_file(con, path)
        except OSError:
            pass  # unreadable is not deleted
    con.commit()
    if progress:
        sys.stderr.write("scanning %d transcript file(s) in %s\n"
                         % (len(seen), ", ".join(r.replace(HOME, "~") for r in ROOTS)))
        sys.stderr.flush()
    new = msgs = 0
    for done, f in enumerate(sorted(seen), 1):
        if progress and done % 250 == 0:
            sys.stderr.write("  %d/%d files · %d changed · %d messages\r"
                             % (done, len(seen), new, msgs))
            sys.stderr.flush()
        try:
            mt = os.path.getmtime(f)
        except OSError:
            continue
        row = con.execute("SELECT mtime,warnings FROM indexed WHERE session_file=?", (f,)).fetchone()
        if row and abs(row[0] - mt) < 1e-6:
            for warning in json.loads(row[1] or "[]"):
                print("warning: partial index: " + core.safe_text(warning), file=sys.stderr)
            continue
        diagnostics = []
        rows, harness = core.read_session(f, diagnostics)
        if diagnostics:
            for warning in diagnostics:
                print("warning: " + core.safe_text(warning), file=sys.stderr)
            if not rows:
                print("warning: file could not be indexed; any previous indexed copy is retained", file=sys.stderr)
                continue
            print("warning: indexing the valid records only", file=sys.stderr)
        harness = harness or harness_from_path(f) or "claude"
        _drop_indexed_file(con, f)
        proj = core.safe_text(os.path.basename(os.path.dirname(f)))
        fallback_sid = os.path.basename(f)[:-6]
        for d in rows:
            role, text, fl = extract(d)
            text = core.safe_text(text)
            fl = [(action, core.safe_text(path)) for action, path in fl if isinstance(path, str)]
            ts = core.safe_text(d.get("timestamp") or "")
            cwd = core.safe_text(d.get("cwd") or "")
            gb = core.safe_text(d.get("gitBranch") or "")
            sid = core.safe_text(d.get("sessionId") or fallback_sid)
            synthetic = d.get("transcripto_synthetic") is True
            human = 1 if is_human_turn(d) and not synthetic else 0
            psrc = d.get("promptSource")
            if text:
                cur = con.execute(
                    "INSERT INTO messages(session_id,session_file,project,ts,role,cwd,git_branch,text,is_human,prompt_source,harness,source_line,synthetic)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (sid, f, proj, ts, role, cwd, gb, text, human, psrc, harness, d.get("_line"), int(synthetic)))
                con.execute("INSERT INTO messages_fts(rowid,text) VALUES(?,?)", (cur.lastrowid, text))
                msgs += 1
            for action, path in fl:
                con.execute(
                    "INSERT INTO files(path,name,action,session_id,session_file,ts,cwd,harness)"
                    " VALUES(?,?,?,?,?,?,?,?)", (path, os.path.basename(path), action, sid, f, ts, cwd, harness))
        con.execute("INSERT OR REPLACE INTO indexed(session_file,mtime,warnings) VALUES(?,?,?)", (f, mt, json.dumps(diagnostics)))
        con.commit(); new += 1
    return new, msgs


def cmd_index(args):
    con = connect(require_index=False); init_schema(con)
    new, msgs = _index_once(con, progress=sys.stderr.isatty())
    if sys.stderr.isatty():
        sys.stderr.write(" " * 60 + "\r"); sys.stderr.flush()
    tot = con.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    print("indexed %d changed sessions · +%d messages · %d total searchable" % (new, msgs, tot))


def cmd_backfill_harness(args):
    """Label rows whose harness is NULL from their source path. Opens the store
    directly: no schema change, no rebuild, no index pass, no user_version write.
    Dry run unless --apply; the dry run opens the file read-only."""
    db = os.path.abspath(os.path.expanduser(args.db or DB))
    if not os.path.exists(db):
        print("no index at %s" % db, file=sys.stderr); return 2
    if args.apply:
        con = sqlite3.connect(db, timeout=30)
        con.execute("PRAGMA busy_timeout=30000")
        con.execute("BEGIN IMMEDIATE")
    else:
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    missing = [t for t in ("messages", "files") if "harness" not in _columns(con, t)]
    if missing:
        print("the %s table has no harness column; run `transcripto index` to migrate the schema first"
              % " and ".join(missing), file=sys.stderr)
        con.close(); return 2
    report = backfill_harness(con, apply=args.apply)
    con.close()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        before, after = report["unlabelled_before"], report["unlabelled_after"]
        print("%s %s" % ("APPLIED" if args.apply else "DRY RUN (nothing written; add --apply)", db.replace(HOME, "~")))
        print("unlabelled before: %d message rows, %d file rows" % (before["messages"], before["files"]))
        for label, slot in sorted(report["labels"].items()):
            print("  %-13s %d source file(s), %d message rows, %d file rows"
                  % (label, slot["files"], slot["messages"], slot["file_rows"]))
        print("  unresolved    %d source file(s), %d rows (path names no harness)"
              % (report["unresolved_files"], report["unresolved_rows"]))
        print("unlabelled after: %d message rows, %d file rows" % (after["messages"], after["files"]))
    return 0


def cmd_watch(args):
    """Live indexing: pick up new transcripts + trace lines automatically as they land."""
    import time
    con = connect(require_index=False); init_schema(con)
    _index_once(con)
    tot = con.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    print(PROG + " watch, live. %d messages indexed; polling %s every %ds. Ctrl-C to stop."
          % (tot, ROOTS[0].replace(HOME, "~"), args.interval), flush=True)
    while True:
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nstopped.", flush=True); return
        new, msgs = _index_once(con)
        if msgs:
            tot += msgs
            print("  \033[32m+%d\033[0m messages · %d session(s) · %d total" % (msgs, new, tot), flush=True)


_QUESTION_FILLER = {
    "a", "an", "the", "about", "did", "do", "does", "i", "is", "my", "was",
    "were", "what", "when", "where", "which", "who", "why", "how",
}


def _match(query):
    words = re.findall(r"[\w.-]+", query.lower())
    useful = [word for word in words if word not in _QUESTION_FILLER]
    terms = useful or words
    return " AND ".join('"%s"' % t.replace('"', '') for t in terms) or '""'


def _day(ts):
    return (ts or "")[:10] or "????-??-??"


def _citation(path, line):
    """A local source reference. Output is explicit because it may be private."""
    shown = os.path.relpath(path, HOME) if path.startswith(HOME + os.sep) else path
    return "%s:L%s" % (shown, line or "?")


def _public_example_rows():
    """An invented change-of-mind trace safe to install on an empty machine."""
    base = {"sessionId": "public-change-example", "cwd": "/example/weather-service",
            "transcripto_synthetic": True}
    rows = [
        dict(base, type="user", promptSource="typed", timestamp="2026-01-12T10:00:00Z",
             message={"role": "user", "content":
                      "Set the forecast cache timeout to 60 seconds in config/cache.toml."}),
        dict(base, type="assistant", timestamp="2026-01-12T10:00:05Z",
             message={"role": "assistant", "content": [
                 {"type": "text", "text": "I will update the forecast cache timeout."},
                 {"type": "tool_use", "id": "edit-1", "name": "Edit",
                  "input": {"file_path": "config/cache.toml",
                            "old_string": "timeout = 15", "new_string": "timeout = 60"}}]}),
        dict(base, type="user", timestamp="2026-01-12T10:00:06Z",
             message={"role": "user", "content": [
                 {"type": "tool_result", "tool_use_id": "edit-1",
                  "content": "File updated successfully", "is_error": False}]}),
        dict(base, type="user", promptSource="typed", timestamp="2026-01-12T10:02:00Z",
             message={"role": "user", "content":
                      "No, use 30 seconds instead for the forecast cache; upstream data changes twice a minute."}),
        dict(base, type="assistant", timestamp="2026-01-12T10:02:05Z",
             message={"role": "assistant", "content": [
                 {"type": "text", "text": "I will apply the corrected 30-second timeout."},
                 {"type": "tool_use", "id": "edit-2", "name": "Edit",
                  "input": {"file_path": "config/cache.toml",
                            "old_string": "timeout = 60", "new_string": "timeout = 30"}}]}),
        dict(base, type="user", timestamp="2026-01-12T10:02:06Z",
             message={"role": "user", "content": [
                 {"type": "tool_result", "tool_use_id": "edit-2",
                  "content": "File updated successfully", "is_error": False}]}),
        dict(base, type="user", promptSource="typed", timestamp="2026-01-12T10:03:00Z",
             message={"role": "user", "content": "Run the forecast cache tests."}),
        dict(base, type="assistant", timestamp="2026-01-12T10:03:05Z",
             message={"role": "assistant", "content": [
                 {"type": "tool_use", "id": "test-1", "name": "Bash",
                  "input": {"command": "python -m unittest tests.test_cache"}}]}),
    ]
    return rows


def _write_labelled_import(path, rows, force=False):
    """Write a private labelled import; refuse to clobber unexpected edits."""
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    payload = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            if f.read() != payload and not force:
                print("Refusing to replace a changed import. Use --force or choose an isolated HOME.",
                      file=sys.stderr)
                return None
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(payload)
    os.chmod(path, 0o600)
    return path


def cmd_import_example(args):
    """Install one labelled synthetic transcript into the local import corpus."""
    path = os.path.join(HOME, ".transcripto", "imports", "claude", "public-change-example.jsonl")
    written = _write_labelled_import(path, _public_example_rows(), force=args.force)
    if written is None:
        return 2
    print("Imported synthetic public example: " + written)
    print('Ask it: transcripto ask "What changed about the forecast cache?"')
    print("Explore the disagreement: transcripto changes")
    return 0


def _lab_rows():
    """Invented cross-harness records: failed Claude edit, succeeded Codex check, unknown Cursor."""
    mark = {"transcripto_synthetic": True}
    claude = [
        dict(mark, type="user", promptSource="typed", sessionId="lab-claude",
             timestamp="2026-09-14T18:00:00Z",
             message={"role": "user", "content": "We retried the amber upload."}),
        dict(mark, type="assistant", sessionId="lab-claude", timestamp="2026-09-14T18:00:01Z",
             message={"role": "assistant", "content": [
                 {"type": "tool_use", "name": "Edit", "id": "edit",
                  "input": {"file_path": "upload.py"}}]}),
        dict(mark, type="user", sessionId="lab-claude", timestamp="2026-09-14T18:00:02Z",
             message={"role": "user", "content": [
                 {"type": "tool_result", "tool_use_id": "edit", "is_error": True,
                  "content": "Permission denied"}]}),
        dict(mark, type="user", promptSource="typed", sessionId="lab-claude",
             timestamp="2026-09-14T18:01:00Z",
             message={"role": "user", "content": "Explain caching instead."}),
    ]
    codex = [
        dict(mark, type="session_meta", payload={"id": "lab-codex", "cwd": "/example/upload"}),
        dict(mark, type="response_item",
             payload={"type": "message", "role": "user",
                      "content": [{"type": "input_text", "text": "We retried the cobalt upload."}]}),
        dict(mark, type="response_item",
             payload={"type": "function_call", "call_id": "shell", "name": "exec_command",
                      "arguments": json.dumps({"cmd": "pytest upload.py"})}),
        dict(mark, type="response_item",
             payload={"type": "function_call_output", "call_id": "shell",
                      "output": json.dumps({"exit_code": 0, "output": "1 passed"})}),
    ]
    cursor = [
        dict(mark, role="user",
             message={"content": "<user_query>We retried the jade upload.</user_query>"}),
        dict(mark, role="assistant",
             message={"content": [{"type": "tool_use", "name": "StrReplace", "id": "replace",
                                   "input": {"path": "upload.py", "old_string": "a",
                                             "new_string": "b"}}]}),
        dict(mark, role="assistant", message={"content": "All fixed."}),
    ]
    return {
        "claude": ("cross-harness-lab.jsonl", claude),
        "codex": ("cross-harness-lab.jsonl", codex),
        "cursor": ("cross-harness-lab.jsonl", cursor),
    }


def cmd_import_lab(args):
    """Install labelled synthetic failed/succeeded/unknown traces for receiving-agent practice."""
    written = []
    for harness, (name, rows) in _lab_rows().items():
        path = os.path.join(HOME, ".transcripto", "imports", harness, name)
        result = _write_labelled_import(path, rows, force=args.force)
        if result is None:
            return 2
        written.append(result)
    print("Imported SYNTHETIC cross-harness lab (invented; not measured user data):")
    for path in written:
        print("  " + path)
    print('Find them: transcripto ask "retry"')
    print("Open each printed Open command. Expect failed / succeeded / unknown.")
    return 0


OFFLINE_QUICKSTART = """# Transcripto offline quickstart (flight)

Use a built wheel. Do not require PyPI. All lab records are invented.

## 1. Install from a wheel path

```sh
WHEEL=/absolute/path/to/transcripto-0.2.1-py3-none-any.whl
python3 -m venv /tmp/transcripto-flight
/tmp/transcripto-flight/bin/python -m pip install --no-index --no-deps "$WHEEL"
export PATH="/tmp/transcripto-flight/bin:$PATH"
FLIGHT_HOME="$(mktemp -d)"   # clean home for the lab; your own HOME is never changed
```

Replace WHEEL with the path printed by `python3 -m build` (dist/*.whl) or the
file you copied onto the laptop. Every lab command below sets HOME for that one
command only. Drop the HOME= prefix to use your own history instead.

## 2. Seed labelled synthetic history

```sh
HOME="$FLIGHT_HOME" transcripto import-lab
HOME="$FLIGHT_HOME" transcripto ask "retry"
```

## 3. Reopen exact evidence

Run each printed `Open:` line, or:

```sh
transcripto replay /path/from/open --line N
transcripto replay /path/from/open --line N --json
```

replay reads the cited file directly and needs no HOME prefix.
Claude lab hit: failed edit. Codex: succeeded check. Cursor: unknown (no result).

## 4. Receiver brief with outcomes

```sh
HOME="$FLIGHT_HOME" transcripto import-example
HOME="$FLIGHT_HOME" transcripto handoff "30 seconds" --to-harness codex --output "$FLIGHT_HOME/packet.json"
HOME="$FLIGHT_HOME" transcripto receive-handoff "$FLIGHT_HOME/packet.json" --as-harness codex --output "$FLIGHT_HOME/brief.md"
cat "$FLIGHT_HOME/brief.md"
```

The brief includes recorded follow-up statuses and an Open command. If the source
moved, vanished, or no longer holds the cited request, the brief marks evidence
uncertain and shows only the packet's own statuses as provisional. Re-run ask
after restoring the file, or pass the new path to replay.

Status describes tool execution, not task correctness. Missing results stay unknown.
"""


WHEEL_PLACEHOLDER = "/absolute/path/to/transcripto-0.2.1-py3-none-any.whl"


def cmd_quickstart(args):
    """Print the offline wheel install / search / reopen card."""
    text = OFFLINE_QUICKSTART
    if args.wheel:
        wheel = os.path.abspath(os.path.expanduser(args.wheel))
        if core.safe_text(wheel) != wheel:
            print("Refusing a wheel path with control characters.", file=sys.stderr)
            return 2
        # The path lands in a shell assignment a stranger will paste. Quote it so
        # spaces, apostrophes and $(...) travel as one literal argument.
        text = text.replace("WHEEL=" + WHEEL_PLACEHOLDER, "WHEEL=" + shlex.quote(wheel))
        if not os.path.isfile(wheel):
            print("warning: wheel path does not exist yet: " + wheel, file=sys.stderr)
    print(text.rstrip())
    return 0


def cmd_search(args):
    """Your own prompts first, and never call a machine record "you".

    The label used to be `"you" if role == "user"`. On a real corpus 93,004 rows
    carry role='user' and only 4,218 were typed: the label was wrong on 95.5% of
    them, on the second command a curious reader runs, in a tool whose whole
    argument is the difference between what you wrote and what the machine did.
    `is_human` already existed and every other command used it.

    Hits you typed sort first, because those are the ones worth finding.
    """
    con = connect()
    try:
        rows = con.execute(
            "SELECT m.ts,m.project,m.role,m.is_human,m.cwd,"
            " snippet(messages_fts,0,'\033[1m','\033[0m','…',14)"
            " FROM messages_fts JOIN messages m ON m.id=messages_fts.rowid"
            " WHERE messages_fts MATCH ?"
            " ORDER BY m.is_human DESC, m.ts DESC LIMIT ?",
            (_match(args.query), args.limit)).fetchall()
    except sqlite3.OperationalError as e:
        print("search error:", e); return
    if not rows:
        print("no matches. Try broader terms, or --root <dir> to select your transcript folder."); return
    for ts, proj, role, human, cwd, snip in rows:
        repo = os.path.basename(cwd.rstrip("/")) if cwd else proj
        if human:
            who, colour = "you", "\033[1m"
        elif role == "user":
            # role='user' but nobody typed it: a tool result or a harness injection.
            who, colour = "harness", "\033[2m"
        else:
            who, colour = "agent", "\033[2m"
        print("\033[2m%s\033[0m  \033[36m%-16s\033[0m %s%-7s\033[0m %s"
              % (_day(ts), repo[:16], colour, who, " ".join(snip.split())))
    typed = sum(1 for r in rows if r[3])
    print("\n\033[2m%d of %d hits are prompts you typed.\033[0m" % (typed, len(rows)))


def _repo(cwd, proj):
    return core.safe_text(os.path.basename(cwd) if cwd else proj)


def cmd_ask(args):
    """YOUR OWN messages about a topic — the question that kills 'did I lose something?'.

    Filters to turns the operator actually typed (is_human=1), newest first, each with
    date + repo + session id + snippet, and opens with a deterministic rollup of
    the arc: how many, how long, which repos, and your latest thought on it.
    """
    con = connect()
    examples = con.execute(
        "SELECT m.text,m.session_file,m.source_line FROM messages_fts "
        "JOIN messages m ON m.id=messages_fts.rowid "
        "WHERE messages_fts MATCH ? AND m.synthetic=1 AND m.prompt_source IN ('typed','queued') "
        "ORDER BY m.ts DESC LIMIT ?", (_match(args.query), args.limit)).fetchall()
    if examples:
        print("SYNTHETIC EXAMPLE — invented requests, excluded from your message counts")
        for text, source, line in examples:
            print("  %s [%s]" % (" ".join(text.split()), _citation(source, line)))
            if line and core.safe_text(source) == source:
                print("  Open: %s replay %s --line %d" % (PROG, shlex.quote(source), line))
        print()
    try:
        rows = con.execute(
            "SELECT m.id,m.ts,m.project,m.cwd,m.session_id,m.text,m.session_file,m.source_line,"
            " snippet(messages_fts,0,'\033[1m','\033[0m','…',16)"
            " FROM messages_fts JOIN messages m ON m.id=messages_fts.rowid"
            " WHERE messages_fts MATCH ? AND m.is_human=1"
            " ORDER BY m.ts DESC LIMIT ?",
            (_match(args.query), args.limit)).fetchall()
    except sqlite3.OperationalError as e:
        print("ask error:", e); return
    if not rows:
        if examples:
            return 0
        # Did the topic exist at all (just not in the operator's words)? Say so honestly.
        try:
            any_hit = con.execute(
                "SELECT COUNT(*) FROM messages_fts JOIN messages m ON m.id=messages_fts.rowid WHERE messages_fts MATCH ?",
                (_match(args.query),)).fetchone()[0]
        except sqlite3.OperationalError:
            any_hit = 0
        if any_hit:
            print("no messages YOU typed about '%s', but %d agent/tool turns mention it."
                  "\ntry `%s search \"%s\"` to see those, or `%s index` if it's new."
                  % (args.query, any_hit, PROG, args.query, PROG))
        else:
            print("nothing about '%s' in the selected history. Try broader terms, or --root <dir> to select your transcript folder."
                  % args.query)
        return

    # ---- rollup: the arc across ALL your matches, not just the shown page ----
    allm = con.execute(
        "SELECT m.ts,m.project,m.cwd,m.session_id"
        " FROM messages_fts JOIN messages m ON m.id=messages_fts.rowid"
        " WHERE messages_fts MATCH ? AND m.is_human=1",
        (_match(args.query),)).fetchall()
    total = len(allm)
    days = sorted(_day(r[0]) for r in allm if r[0])
    sessions = {r[3] for r in allm}
    repos = {}
    for ts, proj, cwd, sid in allm:
        repos[_repo(cwd, proj)] = repos.get(_repo(cwd, proj), 0) + 1
    top = sorted(repos.items(), key=lambda kv: -kv[1])
    span = ("%s → %s" % (days[0], days[-1])) if days else "?"
    shown = len(rows)
    more = " (showing newest %d)" % shown if shown < total else ""
    headcount = ("%d" % total) if shown >= total else ("%d of %d" % (shown, total))
    print("\033[1m%s\033[0m  %s message%s you typed · %d session%s · %d repo%s · %s%s"
          % (args.query, headcount, "" if total == 1 else "s",
             len(sessions), "" if len(sessions) == 1 else "s",
             len(top), "" if len(top) == 1 else "s", span, more))
    print("\033[2mwhat you were doing about this\033[0m")
    print("  most active in: " + " · ".join(
        "\033[36m%s\033[0m (%d)" % (r, c) for r, c in top[:4]))
    lid, lts, lproj, lcwd, lsid, ltext, lfile, lline, lsnip = rows[0]
    latest = " ".join(ltext.split())[:240]
    print("  latest (\033[2m%s\033[0m %s): \"%s\" [%s]"
          % (_day(lts), _repo(lcwd, lproj), latest, _citation(lfile, lline)))

    print("\n\033[2myour messages, newest first\033[0m")
    for _id, ts, proj, cwd, sid, text, source, line, snip in rows:
        print("%s  \033[36m%-20s\033[0m %s  \033[2m%s · %s\033[0m"
              % (_day(ts), _repo(cwd, proj)[:20], " ".join(snip.split()),
                 (sid or "")[:8], _citation(source, line)))
        if line and core.safe_text(source) == source:
            print("  Open: %s replay %s --line %d" % (PROG, shlex.quote(source), line))


def cmd_find(args):
    con = connect()
    n = args.name
    rows = con.execute(
        "SELECT ts,action,path,cwd,session_id FROM files"
        " WHERE name=? OR path LIKE ? ORDER BY ts", (n, "%" + n + "%")).fetchall()
    if not rows:
        print("no file matching '%s' in any session. try `%s index`." % (n, PROG)); return
    writes = [r for r in rows if r[1] in ("write", "edit")]
    print("\033[1m%s\033[0m  %d touches across sessions (%d were writes/edits)\n"
          % (n, len(rows), len(writes)))
    for ts, action, path, cwd, sid in rows:
        tag = {"write": "\033[32mWROTE\033[0m", "edit": "\033[33mEDIT \033[0m",
               "read": "\033[2mread \033[0m"}.get(action, action.upper())
        print("%s  %s  %s  \033[2m%s\033[0m" % (_day(ts), tag, path, sid[:8]))


def cmd_trace(args):
    replay = argparse.Namespace(target=args.query, episode=None, events=12, limit=args.limit,
        all=args.all, failures=False, demo=False, json=False, share=False)
    return cmd_replay(replay, _coach_files(_coach_roots(args.root, args.harness), args.harness))


def cmd_sessions(args):
    """List the sessions YOU typed in. The rest get one line, not eighteen rows.

    This used to list every session by recency. On a real corpus 1,306 of 1,530
    sessions contain no typed prompt at all, so 8 of 18 rows printed
    "(no prompt you typed)" on the command most likely to be somebody's first
    screenshot. Those rows were not a rendering bug. 85% is the finding, and
    listing machine sessions in date order was burying it.

    --all brings them back, because sometimes you want the subagent run.
    """
    con = connect()
    HUMAN = ("is_human=1 AND text!='' AND text NOT LIKE '<command-name>%'"
             " AND text NOT LIKE '<local-command-%'")
    having = "" if getattr(args, "all", False) else (
        " HAVING SUM(CASE WHEN " + HUMAN + " THEN 1 ELSE 0 END) > 0")
    rows = con.execute(
        "SELECT session_id,project,MAX(ts) mx,COUNT(*),"
        " SUM(CASE WHEN " + HUMAN + " THEN 1 ELSE 0 END) typed,"
        " MAX(cwd) FROM messages GROUP BY session_id" + having +
        " ORDER BY mx DESC LIMIT ?", (args.limit,)).fetchall()
    for sid, proj, mx, cnt, typed, cwd in rows:
        t = con.execute("SELECT text FROM messages WHERE session_id=? AND role='user'"
                        " AND " + HUMAN + " ORDER BY ts LIMIT 1", (sid,)).fetchone()
        title = (t[0][:78].replace("\n", " ") if t
                 else "\033[2mno prompt you typed — agent-only run\033[0m")
        where = os.path.basename((cwd or proj or "").rstrip("/")) or (proj or "")
        print("\033[2m%s\033[0m  \033[36m%-18s\033[0m %3d typed \033[2m/%-5d\033[0m %s"
              % (_day(mx), where[:18], typed or 0, cnt, title))
    if not rows:
        total = con.execute("SELECT COUNT(DISTINCT session_id) FROM messages").fetchone()[0]
        if not total:
            print("Your index is empty. `%s index` found no transcripts to read." % PROG)
        else:
            print("None of your %s indexed sessions has a prompt you typed in it."
                  % f"{total:,}")
            print("\033[2mthat is the finding, not an empty list. `--all` lists them.\033[0m")
        return
    if not getattr(args, "all", False):
        quiet = con.execute("SELECT COUNT(*) FROM (SELECT session_id FROM messages"
                            " GROUP BY session_id HAVING SUM(CASE WHEN " + HUMAN +
                            " THEN 1 ELSE 0 END)=0)").fetchone()[0]
        ses = con.execute("SELECT COUNT(DISTINCT session_id) FROM messages").fetchone()[0]
        if quiet:
            print("\n\033[2m%s of your %s sessions have no prompt you typed in them (%.0f%%)."
                  " They ran\n  without you. `--all` lists them.\033[0m"
                  % (f"{quiet:,}", f"{ses:,}", 100 * quiet / ses if ses else 0))


def cmd_stats(args):
    """Rank what the operator typed, not what the machine emitted.

    This used to be COUNT(*) FROM messages GROUP BY project. On a real corpus that
    put a single home-directory bucket on top with 110,569 rows and filled eight of
    twelve rows with `wf_*` workflow hashes: the tool ranking its own internals.
    Two things were wrong. It counted machine messages, in a product whose argument
    is that the typed share is the scarce part. And `project` is the harness's
    folder encoding, so every typed prompt from one machine lands in one bucket;
    `cwd` is where work happened and `cost` already keys on it.
    """
    con = connect()
    HUMAN = ("is_human=1 AND text!='' AND text NOT LIKE '<command-name>%'"
             " AND text NOT LIKE '<local-command-%'")
    typed = con.execute("SELECT COUNT(*) FROM messages WHERE " + HUMAN).fetchone()[0]
    tot = con.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    # The empty state is the one a stranger sees first, straight after install.
    # "0 of 0 ... 0.0%" is a ratio over nothing, printed by a tool whose argument
    # is that a rate needs a denominator.
    if not tot:
        print("Your index is empty, so there is no share to show and this prints none.")
        print("\033[2m`%s index` found no transcripts under ~/.claude/projects. either"
              " no agent has\n  run on this machine yet, or they are somewhere else."
              "\033[0m" % PROG)
        return

    # The headline, because it is the whole argument and it used to be a footnote.
    # Name the population. `coach` reads the raw JSONL and reports the same
    # numerator over ~499k RECORDS, which is 0.8%. This reads the index, which
    # keeps ~205k MESSAGES, and the same numerator over that is 2.1%. Both are
    # true of different populations, and a tool that prints two shares for one
    # claim without saying which population it read is doing the thing this tool
    # exists to catch.
    print("\033[1m%s of the %s messages in your index are things you typed.  %.1f%%\033[0m"
          % (f"{typed:,}", f"{tot:,}", 100 * typed / tot if tot else 0.0))
    print("\033[2mthe rest is the machine answering. `coach` counts raw transcript records"
          " instead\n  of indexed messages, so its share is smaller; same numerator, wider"
          " population.\033[0m")

    print("\n\033[1mwhere you typed them\033[0m")
    rows = con.execute("SELECT cwd,COUNT(*) n FROM messages WHERE " + HUMAN +
                       " AND cwd IS NOT NULL AND cwd!='' GROUP BY cwd"
                       " ORDER BY n DESC LIMIT 10").fetchall()
    for cwd, n in rows:
        print("  %5d  %s" % (n, os.path.basename(cwd.rstrip("/")) or cwd))

    print("\n\033[1mfiles your prompts moved most\033[0m")
    for name, c in con.execute("SELECT name,COUNT(*) c FROM files WHERE action IN('write','edit')"
                               " GROUP BY name ORDER BY c DESC LIMIT 10"):
        print("  %5d  %s" % (c, name))

    ses = con.execute("SELECT COUNT(DISTINCT session_id) FROM messages").fetchone()[0]
    quiet = con.execute("SELECT COUNT(*) FROM (SELECT session_id FROM messages"
                        " GROUP BY session_id HAVING SUM(CASE WHEN " + HUMAN +
                        " THEN 1 ELSE 0 END)=0)").fetchone()[0]
    fil = con.execute("SELECT COUNT(DISTINCT path) FROM files").fetchone()[0]
    print("\n%s sessions · %s of them you never typed in · %s files touched"
          % (f"{ses:,}", f"{quiet:,}", f"{fil:,}"))


# ─────────────────────────────────────────────────────────────────────────────
# cost — what one HUMAN decision costs
#
# ccusage and friends answer "what did I spend". They cannot answer "what did
# one decision of mine cost", because the denominator does not exist in the
# transcript: ~95% of `type: user` records at fleet scale are not the operator.
# trace already has that gate (is_human_turn). Joining it to token spend is the
# whole feature: spend / decisions-you-actually-made.
#
# There is no cost field in a Claude Code transcript — only token counts — so
# every dollar here is API-EQUIVALENT: what those tokens would cost at
# Anthropic list price. On a Max/Pro subscription you did not pay it. It is
# still the only comparable unit, and it is what ccusage reports too.
# ─────────────────────────────────────────────────────────────────────────────

# USD per 1M tokens (input, output), Anthropic list price, cached 2026-10-04
# from platform.claude.com/docs/en/about-claude/pricing.
PRICES = {
    "claude-fable-5-1":  (10.0, 50.0),
    "claude-mythos-5-1": (10.0, 50.0),
    "claude-fable-5":    (10.0, 50.0),
    "claude-mythos-5":   (10.0, 50.0),
    "claude-opus-5-5":   (4.0, 20.0),
    "claude-opus-5":     (5.0, 25.0),
    "claude-opus-4-8":   (5.0, 25.0),
    "claude-opus-4-7":   (5.0, 25.0),
    "claude-opus-4-6":   (5.0, 25.0),
    "claude-opus-4-5":   (5.0, 25.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-sonnet-5":   (2.0, 10.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-haiku-5-5":  (0.10, 0.50),
    "claude-haiku-4-5":  (1.0, 5.0),
}
# Haiku 5.5 is priced by prompt length: a request whose prompt (input, cache
# reads and cache writes together) is over the threshold pays the higher rate.
TIERED = {"claude-haiku-5-5": (100_000, (0.50, 2.50))}
# fast mode is the same model at premium rates — Opus 5.5 / 5 / 4.8 only.
FAST_PRICES = {"claude-opus-5-5": (8.0, 40.0), "claude-opus-5": (10.0, 50.0),
               "claude-opus-4-8": (10.0, 50.0)}
# Sonnet 5's $2/$10 launch price became the standard price; the increase to
# $3/$15 planned for 2026-09-01 did not occur, so there is no intro window.
INTRO = {}
CACHE_WRITE_5M, CACHE_WRITE_1H, CACHE_READ = 1.25, 2.0, 0.10
# Cache reads are a multiple of input price, and the multiple is per model.
CACHE_READ_BY_MODEL = {"claude-opus-5-5": 0.05, "claude-sonnet-5-5": 0.05,
                       "claude-fable-5-1": 0.025, "claude-mythos-5-1": 0.025}


def normalise_model(model):
    """`claude-haiku-4-5-20251001` and `claude-haiku-4-5` are the same price.
    Dated snapshots appear in real transcripts; strip the -YYYYMMDD suffix."""
    if not model:
        return "(unknown)"
    head, _, tail = model.rpartition("-")
    if head and len(tail) == 8 and tail.isdigit():
        return head
    return model


def price_message(model, usage, ts=""):
    """(usd, tokens) for one API message. usd is None when the model is unpriced —
    an unknown model must show up as an unpriced line, never as a silent $0."""
    u = usage or {}
    inp = u.get("input_tokens") or 0
    out = u.get("output_tokens") or 0
    read = u.get("cache_read_input_tokens") or 0
    cc = u.get("cache_creation") or {}
    w1h = cc.get("ephemeral_1h_input_tokens") or 0
    w5m = cc.get("ephemeral_5m_input_tokens") or 0
    written = u.get("cache_creation_input_tokens") or 0
    if not (w1h or w5m):          # older records carry only the aggregate
        w5m = written
    tokens = {"input": inp, "output": out, "cache_read": read,
              "cache_write_5m": w5m, "cache_write_1h": w1h,
              "total": inp + out + read + w5m + w1h}
    model = normalise_model(model)
    rate = None
    if u.get("speed") == "fast" and model in FAST_PRICES:
        rate = FAST_PRICES[model]
    elif model in INTRO and ts and ts[:10] <= INTRO[model][1]:
        rate = INTRO[model][0]
    elif model in PRICES:
        rate = PRICES[model]
    if rate is None:
        return None, tokens
    if model in TIERED and inp + read + w5m + w1h > TIERED[model][0]:
        rate = TIERED[model][1]
    pin, pout = rate[0] / 1e6, rate[1] / 1e6
    usd = (inp * pin + out * pout
           + read * pin * CACHE_READ_BY_MODEL.get(model, CACHE_READ)
           + w5m * pin * CACHE_WRITE_5M + w1h * pin * CACHE_WRITE_1H)
    return usd, tokens


def _msg_key(d, msg):
    """Claude Code writes one transcript line per content BLOCK of the same API
    message, repeating the usage object 2-3x. Summing lines inflates spend
    ~2.7x on a real session. Dedupe on the API message id. The repeats are not
    always identical: a streamed message's first line can carry a placeholder
    output count, so the caller keeps the largest record per id, not the first."""
    return msg.get("id") or d.get("requestId") or d.get("uuid")


def collect_cost(days=30, roots=None):
    """Walk the transcripts once. Returns a report dict. Numerator = deduped
    assistant token spend (sub-agent runs included — that is real money).
    Denominator = is_human_turn, the gate `ask` already uses."""
    roots = roots or [os.path.join(HOME, ".claude", "projects")]
    cutoff = cut_iso = None
    if days:
        cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
        cut_iso = datetime.fromtimestamp(cutoff, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    rep = {"days": days, "usd": 0.0, "decisions": 0, "raw_user_turns": 0, "agent_messages": 0,
           "unpriced_messages": 0, "unpriced_tokens": 0, "sessions": set(),
           "by_model": {}, "by_repo": {}, "tokens": {}, "first_ts": "", "last_ts": ""}
    final = {}   # message key -> (total, model, usage, ts, repo), the largest record wins
    for root in roots:
        for f in sorted(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True)):
            # append-only files: an mtime before the window means every record is older
            if cutoff and os.path.getmtime(f) < cutoff:
                continue
            for d in core.iter_json(f):
                t = d.get("type")
                if t not in ("user", "assistant"):
                    continue
                ts = d.get("timestamp") or ""
                if cut_iso and ts and ts[:19] < cut_iso[:19]:
                    continue
                repo = _repo(d.get("cwd"), os.path.basename(os.path.dirname(f)))
                if ts:
                    rep["first_ts"] = min(rep["first_ts"] or ts, ts)
                    rep["last_ts"] = max(rep["last_ts"], ts)
                if t == "user":
                    # the naive denominator, kept so the gate's effect is checkable
                    # rather than asserted: raw_user_turns / decisions is the factor.
                    rep["raw_user_turns"] += 1
                    if is_human_turn(d):
                        rep["decisions"] += 1
                        rep["by_repo"].setdefault(repo, {"usd": 0.0, "decisions": 0})
                        rep["by_repo"][repo]["decisions"] += 1
                        rep["sessions"].add(d.get("sessionId") or f)
                    continue
                msg = d.get("message") or {}
                if not isinstance(msg, dict):
                    continue
                usage = msg.get("usage")
                if not usage:
                    continue
                key = _msg_key(d, msg)
                total = price_message(None, usage)[1]["total"]
                if key not in final or total > final[key][0]:
                    final[key] = (total, normalise_model(msg.get("model")), usage, ts, repo)
    for _, model, usage, ts, repo in final.values():
        usd, tok = price_message(model, usage, ts)
        rep["agent_messages"] += 1
        for k, v in tok.items():
            rep["tokens"][k] = rep["tokens"].get(k, 0) + v
        m = rep["by_model"].setdefault(model, {"usd": 0.0, "messages": 0,
                                               "tokens": 0, "priced": usd is not None})
        m["messages"] += 1
        m["tokens"] += tok["total"]
        if usd is None:
            if tok["total"]:      # a 0-token <synthetic> row costs nothing either way
                rep["unpriced_messages"] += 1
                rep["unpriced_tokens"] += tok["total"]
            continue
        rep["usd"] += usd
        m["usd"] += usd
        rep["by_repo"].setdefault(repo, {"usd": 0.0, "decisions": 0})
        rep["by_repo"][repo]["usd"] += usd
    rep["sessions"] = len(rep["sessions"])
    rep["per_decision"] = (rep["usd"] / rep["decisions"]) if rep["decisions"] else None
    rep["gate_factor"] = (rep["raw_user_turns"] / rep["decisions"]) if rep["decisions"] else None
    rep["turns_per_decision"] = (rep["agent_messages"] / rep["decisions"]) if rep["decisions"] else None
    return rep


def _hm(n):
    for unit, div in (("B", 1e9), ("M", 1e6), ("k", 1e3)):
        if n >= div:
            return "%.1f%s" % (n / div, unit)
    return str(int(n))


def cmd_cost(args):
    rep = collect_cost(args.days, [os.path.expanduser(args.root)] if args.root else None)
    if args.json:
        print(json.dumps(rep, indent=2, sort_keys=True))
        return
    win = ("last %d days" % args.days) if args.days else "all time"
    span = ""
    if rep["first_ts"]:
        span = "  \033[2m%s → %s\033[0m" % (rep["first_ts"][:10], rep["last_ts"][:10])
    print("\033[1mcost per human decision\033[0m  %s%s\n" % (win, span))
    if not rep["decisions"]:
        print("  no turns you typed in this window. widen it with --days.")
        return
    print("  API-equivalent spend      \033[1m$%s\033[0m" % format(rep["usd"], ",.2f"))
    print("  your decisions            \033[1m%d\033[0m   \033[2mturns you actually typed"
          " (promptSource typed/queued)\033[0m" % rep["decisions"])
    print("  " + "─" * 52)
    print("  \033[1mcost per human decision   $%.2f\033[0m" % rep["per_decision"])
    print("\n  %s agent messages · %.0f per decision · %s tokens · %d sessions"
          % (_hm(rep["agent_messages"]), rep["turns_per_decision"],
             _hm(rep["tokens"].get("total", 0)), rep["sessions"]))
    print("  \033[2m%s raw `type: user` records in the same window. dividing by those"
          " instead\n  would read $%.2f, %.1fx too cheap.\033[0m"
          % (_hm(rep["raw_user_turns"]), rep["usd"] / rep["raw_user_turns"],
             rep["gate_factor"]))
    if rep["unpriced_messages"]:
        print("  \033[33m%d message(s) unpriced (%s tokens): model not in the price table\033[0m"
              % (rep["unpriced_messages"], _hm(rep["unpriced_tokens"])))
    print("\n\033[1mby model\033[0m")
    for model, m in sorted(rep["by_model"].items(), key=lambda kv: -kv[1]["usd"])[:8]:
        tag = "$%8.2f" % m["usd"] if m["priced"] else "unpriced"
        print("  %10s  %-18s %5d msg  %6s tok" % (tag, model[:18], m["messages"], _hm(m["tokens"])))
    rows = [(r, v) for r, v in rep["by_repo"].items() if v["decisions"]]
    if rows:
        print("\n\033[1mby repo\033[0m  \033[2m(spend attributed by the cwd of each turn)\033[0m")
        for repo, v in sorted(rows, key=lambda kv: -kv[1]["usd"])[:8]:
            per = "$%.2f" % (v["usd"] / v["decisions"])
            print("  %8s  %3d decisions  %8s / decision  \033[36m%s\033[0m"
                  % ("$%.2f" % v["usd"], v["decisions"], per, repo[:28]))
    print("\n\033[2mno cost field exists in a transcript. these are list-price equivalents"
          " for the tokens spent.\n  on a subscription you did not pay this; it is the"
          " comparable unit, same as ccusage.\033[0m")



# ============================================================================
# coach — descriptive request history. Execution status comes from transcripto_core.
# These lexical tags describe prompts; they do not establish which prompts work best.

_FILE_RE = re.compile(r"\b[\w./-]+\.[A-Za-z]{1,5}\b|\b[\w-]+/[\w./-]+\b")
_CHECK_RE = re.compile(r"\b(test|tests|verify|verif|prove|proof|done[- ]?when|"
                       r"make sure|ensure|confirm|check that|assert|so that|"
                       r"screenshot|render)\b")
_TOKEN_RE = re.compile(r"[A-Za-z0-9_.]+")

_INTENT_PHRASES = {"roll back": "REVERT", "rolling back": "REVERT"}
_INTENT_WORDS = {
    "make": "CHANGE", "let": "CHANGE", "get": "CHANGE", "do": "CHANGE", "have": "CHANGE",
    "fix": "CHANGE", "refactor": "CHANGE", "extract": "CHANGE", "add": "CHANGE",
    "implement": "CHANGE", "build": "CHANGE", "create": "CHANGE", "write": "CHANGE",
    "update": "CHANGE", "bump": "CHANGE", "upgrade": "CHANGE", "change": "CHANGE",
    "edit": "CHANGE", "modify": "CHANGE", "wrap": "CHANGE", "optimize": "CHANGE",
    "optimise": "CHANGE", "improve": "CHANGE", "speed": "CHANGE", "harden": "CHANGE",
    "rename": "CHANGE", "move": "CHANGE", "migrate": "CHANGE", "tidy": "CHANGE",
    "clean": "CHANGE", "cleanup": "CHANGE", "format": "CHANGE", "debug": "CHANGE",
    "diagnose": "CHANGE", "trace": "CHANGE", "reproduce": "CHANGE", "broken": "CHANGE",
    "crash": "CHANGE", "crashes": "CHANGE", "failing": "CHANGE", "handle": "CHANGE",
    "document": "DESCRIBE", "describe": "DESCRIBE", "explain": "DESCRIBE",
    "summarize": "DESCRIBE", "summarise": "DESCRIBE", "comment": "DESCRIBE",
    "review": "DESCRIBE", "audit": "DESCRIBE", "benchmark": "DESCRIBE",
    "measure": "DESCRIBE", "profile": "DESCRIBE", "analyze": "DESCRIBE",
    "analyse": "DESCRIBE", "translate": "DESCRIBE", "localize": "DESCRIBE",
    "localise": "DESCRIBE",
    "revert": "REVERT", "rollback": "REVERT", "undo": "REVERT", "remove": "REVERT",
    "delete": "REVERT", "downgrade": "REVERT", "disable": "REVERT", "deprecate": "REVERT",
    "test": "TEST", "tests": "TEST", "coverage": "TEST", "cover": "TEST",
    "assert": "TEST", "spec": "TEST",
    "deploy": "CHANGE", "ship": "CHANGE", "release": "CHANGE", "publish": "CHANGE",
}
_NON_OBJECTS = {"it", "this", "that", "them", "these", "those", "everything",
                "anything", "stuff", "things", "thing", "something", "better",
                "faster", "cleaner", "nicer", "here", "there"}
_STOP = {"the", "a", "an", "to", "of", "in", "into", "on", "for", "and", "or",
         "but", "with", "from", "by", "at", "as", "is", "are", "be", "been",
         "was", "were", "why", "how", "what", "when", "which", "who", "whose",
         "returns", "return", "yields", "yield", "keep", "green", "show", "me",
         "my", "our", "your", "new", "old", "up", "down", "out", "over",
         "under", "whole", "two", "word", "words", "page", "flow", "layer",
         "module", "so", "if", "then", "before", "after", "please", "can",
         "you", "do", "does", "not", "no", "all", "some", "any", "edge",
         "case", "cases", "set", "result", "nothing", "empty", "load", "box"}

MIN_PATTERN_N = 8  # display floor for descriptive habit groups
MIN_EPISODES_TO_RANK = 30  # legacy threshold; no inferential rankings are produced


def _c_tokens(text):
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _intent(text):
    """The HEAD intent: the earliest intent token in reading order, or None.

    Deliberately the FIRST verb, not the strongest. "refactor auth, keep tests
    green" is a refactor with a constraint, not a test task.
    """
    low, toks, hits = text.lower(), _c_tokens(text), []
    for i, tok in enumerate(toks):
        b = _INTENT_WORDS.get(tok)
        if b:
            hits.append((float(i), b))
    for phrase, bucket in _INTENT_PHRASES.items():
        if phrase in low:
            first = phrase.split()[0]
            if first in toks:
                hits.append((toks.index(first) - 0.5, bucket))
    if not hits:
        return None
    hits.sort(key=lambda x: x[0])
    return hits[0][1]


def _norm_obj(tok):
    out = []
    for p in re.split(r"[_.]", tok):
        if len(p) < 2:
            continue
        if len(p) > 3 and p.endswith("s"):
            p = p[:-1]
        out.append(p)
    return out


def _objects(text):
    objs = set()
    for tok in _c_tokens(text):
        if tok in _STOP or tok in _NON_OBJECTS or tok in _INTENT_WORDS:
            continue
        for n in _norm_obj(tok):
            if n not in _STOP and n not in _INTENT_WORDS:
                objs.add(n)
    return objs


# ============================================================================
# correction rate — the inverse of a landed prompt
# ============================================================================
# Of the turns you TYPED, how many were spent telling the agent it got the last
# one wrong. The denominator is the same authorship gate every other number here
# uses (is_human_turn: typed OR queued, never isMeta / isSidechain / tool_result),
# so a tool result that happens to contain the word "wrong" cannot inflate it.
# The classifier is lexical and it is a FLOOR, stated so it can be argued with:
# a correction phrased without a marker ("the header one") is missed, and a
# genuine "no" inside a fresh request ("no tests needed") is counted. Read it as
# a trend on your own history, never as a verdict on one turn.

_CORRECTION_MARKERS = ("no,", "no ", "not that", "wrong", "i meant", "i said",
                       "again", "that's not", "you didn't", "revert", "undo",
                       "stop", "instead")
_CORRECTION_HEAD = 80     # markers are looked for in the first N characters only
_CORRECTION_SHORT = 12    # a turn under this many words, right after an agent
                          # turn that names the same file, is a nudge = correction
_CORRECTION_RE = re.compile(
    "(?<![a-z0-9_])(?:" + "|".join(
        re.escape(m).replace("'", "['\u2019]")
        + ("" if m[-1] in ", " else "(?![a-z0-9_])")
        for m in _CORRECTION_MARKERS) + ")")

# ---------------------------------------------------------------------------
# v1 — the same question, rebuilt against a measured failure set.
#
# v0 was measured on 2026-09-03 over 200 agent-labelled turns (see
# docs/CORRECTION-PRECISION-2026-09-03.md): precision 0.54, recall 0.12, and a
# printed rate of 6% against a measured ~26%. The two biggest markers were the
# two worst: bare "no " ran at 56% precision because it is the commonest way to
# say something about the WORLD ("no worries", "no clue"), and bare "again" ran
# at 54% because resuming work ("lets pick this up again") is lexically identical
# to rejecting it. The NUDGE rule went 0-for-5.
#
# So v1 keeps the two words only where the grammar makes them about the agent.
#
# WHAT THIS STILL IS NOT: a classifier that understands the sentence. It is a
# better lexicon, tested on a held-out sample, and it will still miss a
# correction phrased without any of these words.

# "no" only where a pronoun, an imperative, or a comma makes it a rejection of
# what the agent just did, rather than a description of the world.
_V1_NO = (r"(?:^|[\s,;:])no[,!]"
          r"|(?:^|[\s,;:])no\s+(?:you|we|i|it|that|thats|dont|don't|need\s+to|"
          r"please|wait|new\s+work|not)"
          r"|(?:^|[\s,;:])(?:thats|that's|its|it's)\s+not\b"
          r"|(?:^|[\s,;:])no\b\s*$")

# "again" only next to a retry imperative or a complaint. "once again" alone is
# continuation; "try again" and "once again <negative>" are not.
_V1_AGAIN = (r"\btry(?:ing)?\s+again\b"
             r"|\bagain\?"
             r"|\b(?:once\s+)?again\b[^.!?]{0,40}?\b(?:wrong|not|no|never|"
             r"broke|broken|fail|failed|mix(?:ed)?\s+up|missing|stuck|horrible|"
             r"bad|lost|misunderstood|conflict)"
             r"|\b(?:wrong|not|never|broke|broken|fail|failed|missing|stuck|"
             r"horrible|misunderstood|conflict|mix(?:ed)?\s+up|lo[os]t|lose|"
             r"loose|swamp(?:ed|ing)?)\b[^.!?]{0,40}?\b(?:once\s+)?again\b")

# The register v0 had no words for at all, measured from its 24 misses.
_V1_EXTRA = (r"\bfix\s+(?:it|this|that)\b"
             r"|\bi\s+mean\b"
             r"|\bdon'?t\s+like\b"
             r"|\b(?:doesn'?t|does\s+not|isn'?t|is\s+not)\s+work"
             r"|\bnot\s+working\b"
             r"|\bnonsense\b|\bgibberish\b"
             r"|\bshould\s?n'?t\b|\bshouldnt\b"
             r"|\bmisunderstood\b|\bmisunderstanding\b"
             r"|\byou\s+did\s?n'?t\b|\byou'?re\s+(?:wrong|lost|on\s+the\s+wrong)\b"
             r"|\bwhere'?s?\s+the\b"
             r"|\bis\s+this\s+(?:accurate|right|correct)\b"
             r"|\bmakes\s+no\s+sense\b"
             r"|\bmeans\s+nothing\b"
             r"|\b(?:change|redo|rewrite|remove)\s+(?:it|this|that)\b")

_V1_RE = re.compile("(?:%s|%s|%s|%s)" % (
    _V1_NO, _V1_AGAIN, _V1_EXTRA,
    # the v0 markers that measured well enough to keep, unchanged
    r"\bwrong\b|\bnot\s+that\b|\bi\s+meant\b|\brevert\b|\bundo\b"
    r"|\bstop\b|\binstead\b"), re.I)

# A head taken in WORDS after URLs and paths are stripped. v0 read the first 80
# CHARACTERS raw, so a turn opening with a pasted URL spent its whole window on
# the URL and was unclassifiable — measured, not hypothesised: one sampled row's
# "once again ... change it" sat at roughly character 100.
_V1_HEAD_WORDS = 80
_URLISH = re.compile(r"(?:https?://|file://|/(?:Users|tmp|var|home)/)\S+|\S+\.(?:png|jpe?g|gif|pdf|mp4|mov)\b", re.I)


def _v1_head(text):
    """The first _V1_HEAD_WORDS words, with URLs and absolute paths removed."""
    return " ".join(_URLISH.sub(" ", text).split()[:_V1_HEAD_WORDS]).lower()


# Which classifier runs. v1 is the default; v0 stays reachable so the two can be
# compared on one corpus. An explicit selector rather than a bare boolean, so a
# caller comparing versions cannot accidentally compare v1 to itself.
_CORRECTION_VERSION = os.environ.get("TRANSCRIPTO_CORRECTION", "v1")
if _CORRECTION_VERSION not in ("v0", "v1"):
    _CORRECTION_VERSION = "v1"


def _quoted_things(text):
    """The file basenames and `backticked` spans a text names, lower-cased.
    A path is reduced to its basename so "docs/caching.md" in your turn and
    "/repo/docs/caching.md" in the agent's tool call read as the same file."""
    out = set()
    for m in _FILE_RE.finditer(text):
        out.add(os.path.basename(m.group(0).rstrip(".,;:")).lower())
    for m in re.finditer(r"`([^`\n]{2,80})`", text):
        out.add(m.group(1).strip().lower())
    return {t for t in out if len(t) >= 3}


def is_correction(text, prev_agent="", version=None):
    """True iff a typed turn reads as a correction of the agent's previous turn.

    PURE: text in, bool out, no state. Two rules, both lexical:

      1. MARKER - the first 80 characters (case-insensitive) start with or
         contain one of _CORRECTION_MARKERS as a whole word: "no," "no " "not
         that" "wrong" "I meant" "I said" "again" "that's not" "you didn't"
         "revert" "undo" "stop" "instead". Whole-word, so "against" is not
         "again", "undone" is not "undo", "now" and "know" are not "no ". A
         bare "no" as the entire turn counts (the head is padded with a space).
      2. NUDGE - the turn is short (< 12 words) and the agent turn immediately
         before it, `prev_agent`, names the same file (matched by basename) or
         the same `backticked` span. "docs/caching.md, shorter please" right
         after the agent wrote docs/caching.md is a correction with no marker.

    `prev_agent` is the extract()-rendered text of everything the assistant did
    since the previous typed turn (its prose plus its tool commands and file
    paths), or "" when this turn opened the session. The caller owns the
    authorship gate; this function never sees a record, only text.
    """
    if (version or _CORRECTION_VERSION) == "v0":
        head = text[:_CORRECTION_HEAD].lower().strip() + " "
        if _CORRECTION_RE.search(head):
            return True
        # NUDGE. Kept in v0 exactly as it shipped; v1 drops it, because measured
        # over 100 flagged rows it fired alone five times and was wrong five
        # times. A rule with no true positive is not a loose rule, it is noise
        # with a cost — it renders every assistant record since the last turn.
        if prev_agent and len(text.split()) < _CORRECTION_SHORT:
            return bool(_quoted_things(text) & _quoted_things(prev_agent))
        return False
    return bool(_V1_RE.search(_v1_head(text)))


def _typed_turns(rows, pasted=None):
    """Yield (typed_text, prev_agent) over one transcript, in order. Same gate
    and same paste subtraction as the episode grader. prev_agent is only
    rendered when the NUDGE rule could use it (a short turn)."""
    pasted = pasted or set()
    agent = []                       # assistant records since the last typed turn
    for row in rows:
        t = _human_prompt(row)
        if t:
            if t in pasted:
                continue             # an echo of agent output, not a turn of yours
            prev = ""
            if agent and len(t.split()) < _CORRECTION_SHORT:
                prev = "\n".join(extract(r)[1] for r in agent)
            yield t, prev
            agent = []
        elif row.get("type") == "assistant":
            agent.append(row)


def count_corrections(rows, pasted=None, version=None):
    """(typed_turns, corrections) over one transcript, walked in order so each
    typed turn is classified against the agent turn it answers. Same gate and
    same paste subtraction as the episode grader, so the denominator returned
    here IS the `typed by you` count coach prints."""
    typed = corrections = 0
    for t, prev in _typed_turns(rows, pasted):
        typed += 1
        if is_correction(t, prev, version=version):
            corrections += 1
    return typed, corrections


# ---------------------------------------------------------------------------
# --detector jev: the opt-in network detector (transcripto_jev.py)
# ---------------------------------------------------------------------------
# The default above is local and offline. Jev is used only when a run passes
# --detector jev; nothing in the environment or a config file can select it.
# The module is imported here, on that path only, so the default path never
# loads urllib's network code or opens a socket.

def _jev_detector(args):
    """A JevDetector for this run, or None when the user asked to fall back to
    the regex because no key is set. Exits 2 with a clear message otherwise."""
    if getattr(args, "detector", "regex") != "jev":
        return None
    if getattr(args, "jev_dry_run", False):
        import transcripto_jev
        return transcripto_jev.JevPreview()
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        if getattr(args, "jev_fallback_regex", False):
            sys.stderr.write("transcripto: OPENROUTER_API_KEY is not set; "
                             "--jev-fallback-regex given, using the local regex. "
                             "Nothing was sent.\n")
            return None
        sys.stderr.write("transcripto: --detector jev needs OPENROUTER_API_KEY in the "
                         "environment. Nothing was sent. Set the key, drop the flag, or "
                         "add --jev-fallback-regex to use the local regex instead.\n")
        sys.exit(2)
    import transcripto_jev
    return transcripto_jev.JevDetector(key, threshold=args.jev_threshold,
                                       batch=args.jev_batch, max_usd=args.jev_max_usd)


def _jev_score(detector, texts):
    """Run the detector over typed turns. Returns the keys coach and export-run
    add to their JSON. correction_rate's denominator is the SCORED turns: turns
    the privacy filter excluded or whose request failed have no verdict and are
    not counted either way."""
    import transcripto_jev
    try:
        verdicts = detector.score(texts)
    except transcripto_jev.JevAuthError as e:
        sys.stderr.write("transcripto: %s Stopped; no verdicts.\n" % e)
        sys.exit(2)
    if getattr(detector, "dry_run", False):
        return {"correction_detector": "jev", "corrections": None,
                "correction_rate": None, "correction_rate_denominator": None,
                "jev": detector.stats}
    scored = [(t, v) for t, v in zip(texts, verdicts) if v is not None]
    corr = sum(1 for _, v in scored if v)
    st = detector.stats
    if st.get("auth_error"):
        sys.stderr.write("transcripto: %s Stopped part way: %d turns scored, %d failed, "
                         "%d not sent. The rate below covers the scored turns only.\n" % (
                             st["auth_error"], st["scored"], st["errors"], st["auth_unsent"]))
    return {
        "correction_detector": "jev",
        "corrections": corr,
        "correction_rate": round(corr / len(scored), 3) if scored else None,
        "correction_rate_denominator": "jev.scored",
        "regex_corrections_on_scored": sum(1 for t, _ in scored if is_correction(t)),
        "jev": st,
    }


def _jev_preview_report(detector, texts, harness, files=1, records=None):
    """Counts-only boundary for the full command, not just detector metadata."""
    out = {"schema": "transcripto.jev-privacy-preview/1", "harness": harness,
           "files": files}
    if records is not None:
        out["total_records"] = records
    out.update(_jev_score(detector, texts))
    return out


def _print_jev_line(r):
    j = r["jev"]
    if j.get("dry_run"):
        print("Jev privacy preview: %d of %d typed turns eligible; %d excluded; "
              "%d spans would be redacted (max %d chars per turn)." % (
                  j["eligible"], j["turns"], j["excluded"], j["redactions"],
                  j["max_chars_per_turn"]))
        for reason, count in j["excluded_reasons"].items():
            print("  %s: %d" % (reason, count))
        print("Nothing sent. No API key needed. No correction verdicts or cost estimate.")
        return
    print("Corrections (Jev, P(correction) >= %.2f): %d of %d scored turns (%s). "
          "The local regex flags %d of the same turns." % (
              j["threshold"], r["corrections"], j["scored"],
              "%d%%" % round(r["correction_rate"] * 100) if r["correction_rate"] is not None else "n/a",
              r["regex_corrections_on_scored"]))
    print("Unscored: %d excluded by the privacy filter, %d failed requests%s. "
          "Reported spend $%.4f over %d requests (%s)." % (
              j["excluded"], j["errors"],
              (", %d not sent (spend cap)" % j["budget_unsent"] if j["budget_stopped"] else "")
              + (", %d not sent (key refused)" % j["auth_unsent"] if j.get("auth_error") else ""),
              j["cost_usd"], j["requests"], j["served_by"] or j["model"]))
    if j.get("cost_unknown"):
        print("Some request costs are unknown. No further requests were started; "
              "reported spend is an incomplete subtotal.")


def cmd_jev_findings(args):
    from transcripto_findings import observe
    from transcripto_jev import JevError
    if args.detector != "jev" or args.jev_fallback_regex:
        print("jev-findings requires explicit --detector jev; regex fallback is not a recorded model observation.", file=sys.stderr)
        return 2
    source = _resolve_run(args.target, _coach_roots(args.root, args.harness), args.harness)
    if not source:
        print("Selected session not found.", file=sys.stderr)
        return 2
    if args.output and os.path.realpath(args.output) == os.path.realpath(source):
        print("Output must not overwrite the source transcript.", file=sys.stderr)
        return 2
    try:
        report = observe(source, _jev_detector(args))
        if args.output and not args.jev_dry_run:
            for finding in report["findings"]:
                finding["replay"] = "transcripto replay --findings %s --line %d" % (shlex.quote(os.path.abspath(os.path.expanduser(args.output))), finding["line"])
        if args.output:
            _write_private(os.path.expanduser(args.output), json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        if args.output and not args.jev_dry_run:
            print("Inspect: transcripto replay --findings %s --line LINE\nPrepare: transcripto handoff --findings %s --line LINE --to-harness codex --output /your/local/packet.json" % (shlex.quote(args.output), shlex.quote(args.output)), file=sys.stderr)
    except (OSError, ValueError, JevError) as exc:
        print("Cannot inspect selected session: " + str(exc), file=sys.stderr)
        return 2
    return 0


def _change_records(roots, harness=None):
    """Return correction episodes with the request they revise and recorded follow-up."""
    found = []
    for path in _coach_files(roots, harness):
        rows, detected = core.read_session(path)
        eps = core.episodes(rows, path)
        for number, ep in enumerate(eps):
            if not is_correction(ep["prompt"]):
                continue
            prior = eps[number - 1] if number else None
            found.append({
                "timestamp": ep["timestamp"],
                "synthetic": any(row.get("transcripto_synthetic") is True for row in rows),
                "harness": detected,
                "correction": ep["prompt"],
                "source": path,
                "line": ep["line"],
                "previous_request": prior["prompt"] if prior else None,
                "previous_line": prior["line"] if prior else None,
                "reply": ep["reply"] or None,
                "events": ep["events"],
            })
    return sorted(found, key=lambda r: (r["timestamp"], r["source"], r["line"] or 0),
                  reverse=True)


def cmd_changes(args):
    """Explore disagreements as before/correction/follow-up sequences."""
    records = _change_records(_coach_roots(args.root, args.harness), args.harness)
    if not records:
        print("No correction-shaped requests found. The classifier can have misses.")
        return 0
    for item in records[:args.limit]:
        if item["synthetic"]:
            print("SYNTHETIC EXAMPLE — invented request and recorded follow-up")
        print("CHANGE OF DIRECTION · %s · %s"
              % (item["harness"], _citation(item["source"], item["line"])))
        if item["previous_request"]:
            print('  Before: "%s" [%s]' % (
                " ".join(item["previous_request"].split()),
                _citation(item["source"], item["previous_line"])))
        else:
            print("  Before: not present in this transcript")
        print('  Correction: "%s"' % " ".join(item["correction"].split()))
        statuses = [event["status"] for event in item["events"]]
        if not statuses:
            print("  Follow-up: no tool attempt recorded; receiver use is missing.")
        else:
            print("  Follow-up: %s" % ", ".join(
                "%s %s (%s)" % (event["kind"], event["target"], event["status"])
                for event in item["events"]))
            if "unknown" in statuses:
                print("  Missing: a matching result for at least one follow-up attempt.")
        print()
    print("Correction detection is lexical; inspect the cited source before relying on it.")
    return 0


def _write_private(path, text):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, mode=0o700, exist_ok=True)
    # Replace atomically: never expose new private text through an existing 0644
    # file, and never follow an output symlink into an unrelated source file.
    fd, temporary = tempfile.mkstemp(prefix=".transcripto-", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def cmd_selected_context(args):
    from transcripto_selected import main
    return main(args)


def cmd_handoff(args):
    """Write one cited correction packet for an explicitly named receiver."""
    observation = None
    if not getattr(args,"source",None) and any(getattr(args,key,None) for key in ("instruction","accept_sha","consent")):
        print("Authored instruction flags require --source; model findings keep their own admission rule.",file=sys.stderr)
        return 2
    if getattr(args, "source", None):
        if args.findings or args.query or not getattr(args,"consent",False):
            print("Selected source requires explicit --consent and no query/findings.",file=sys.stderr)
            return 2
        from transcripto_selected import authored
        try: item=authored(args.source,args.accept_sha,args.line,args.instruction)
        except (OSError,ValueError,TypeError) as exc:
            print("Cannot prepare authored instruction: "+str(exc),file=sys.stderr)
            return 2
    elif args.findings:
        from transcripto_findings import selected
        try:
            report, ep, prior, harness, observation = selected(args.findings, args.line, candidate=True)
        except (OSError, ValueError, TypeError) as exc:
            print("Cannot hand off selected finding: " + str(exc), file=sys.stderr)
            return 2
        item = {"harness": harness, "source": report["source"], "line": ep["line"],
                "correction": ep["prompt"], "previous_request": prior["prompt"] if prior else None,
                "synthetic": report.get("synthetic") is True, "events": ep["events"]}
    else:
        if not args.query or args.line is not None:
            print("Use a correction query, or --findings REPORT --line LINE.", file=sys.stderr)
            return 2
        matches = [item for item in _change_records(_coach_roots(args.root, args.harness), args.harness)
                   if args.query.lower() in item["correction"].lower()]
        if not matches:
            print("No correction-shaped request matches '%s'." % args.query, file=sys.stderr)
            return 2
        item = matches[0]
    if item["harness"] == args.to_harness:
        print("Choose a receiver harness different from the source harness (%s)."
              % item["harness"], file=sys.stderr)
        return 2
    statuses = [event["status"] for event in item["events"]]
    missing = ["receiver acknowledgement", "task correctness verification"]
    if not statuses or "unknown" in statuses:
        missing.insert(0, "matching result for the source follow-up")
    packet = {
        "schema": "transcripto.handoff/1",
        "synthetic": item["synthetic"],
        "receiver_harness": args.to_harness,
        "correction": item["correction"],
        "citation": {"source": item["source"], "line": item["line"],
                     "harness": item["harness"]},
        "previous_request": item["previous_request"],
        "recorded_follow_up": [
            {"kind": event["kind"], "target": event["target"], "status": event["status"]}
            for event in item["events"]],
        "missing": missing,
        "caveat": "A packet carries an instruction, not proof that the receiver completed it.",
    }
    if item.get("instruction_origin"):
        packet["instruction_origin"]=item["instruction_origin"]
        packet["source_request"]=item["previous_request"]
        packet["citation"]["source_sha256"]=item["source_sha256"]
    if observation:
        packet["detector_observation"] = observation
        packet["citation"]["source_sha256"] = observation["source_sha256"]
        packet["missing"].insert(0, "human confirmation of the model suggestion")
    output = os.path.expanduser(args.output)
    if args.findings and os.path.realpath(output) == os.path.realpath(args.findings):
        print("Handoff must not overwrite its findings report.", file=sys.stderr)
        return 2
    if os.path.realpath(output) == os.path.realpath(item["source"]) or (os.path.exists(output) and os.path.samefile(output,item["source"])):
        print("Handoff output must not overwrite the source transcript.", file=sys.stderr)
        return 2
    _write_private(output, json.dumps(packet, indent=2) + "\n")
    print("Handoff written for %s: %s" % (args.to_harness, os.path.expanduser(args.output)))
    print("Missing: " + "; ".join(missing))
    return 0


def _normal(text):
    return " ".join(core.safe_text(text).split()).lower()


def _source_evidence_state(citation, correction):
    """Check whether the cited source still opens the intended request.

    Returns a dict: state is 'available', 'missing', 'unreadable', or 'uncertain'.
    events is a list only when state is 'available'; a source that no longer holds
    the cited request must never lend another episode's outcomes to this brief.
    """
    citation = citation or {}
    path = citation.get("source")
    line = citation.get("line")
    result = {"state": "uncertain", "open": None, "events": None, "synthetic": False}
    if (not isinstance(path, str) or not path or core.safe_text(path) != path
            or isinstance(line, bool) or not isinstance(line, int) or line < 1):
        return result
    path = os.path.expanduser(path)
    result["open"] = "%s replay %s --line %d" % (PROG, shlex.quote(path), line)
    if not os.path.isfile(path):
        result["state"] = "missing"
        return result
    expected_hash = citation.get("source_sha256")
    if expected_hash:
        from transcripto_findings import file_hash
        try:
            if file_hash(path) != expected_hash:
                return result
        except OSError:
            result["state"] = "unreadable"
            return result
    diagnostics = []
    rows, _harness = core.read_session(path, diagnostics)
    if diagnostics and not rows:
        result["state"] = "unreadable"
        return result
    match = next((ep for ep in core.episodes(rows, path) if ep["line"] == line), None)
    if match is None or _normal(match["prompt"]) != _normal(correction):
        return result
    if expected_hash and file_hash(path) != expected_hash:
        return result
    result["state"] = "available"
    result["synthetic"] = match["synthetic"]
    result["events"] = [
        {"kind": event["kind"], "target": event["target"], "status": event["status"]}
        for event in match["events"]]
    return result


def _packet_error(packet):
    """Return a one-line reason a handoff packet cannot be used, or None."""
    if not isinstance(packet, dict):
        return "Handoff packet must be a JSON object."
    if packet.get("schema") != "transcripto.handoff/1":
        return "Unsupported handoff schema."
    if packet.get("instruction_origin") is not None:
        if packet["instruction_origin"] != "explicitly authored instruction; not a detector verdict or research label" or not isinstance(packet.get("source_request"),str) or not packet["source_request"].strip():
            return "Invalid authored instruction provenance."
    observation = packet.get("detector_observation")
    if observation is not None and not isinstance(observation, dict):
        return "Detector observation must be an object."
    citation = packet.get("citation")
    if citation is not None and not isinstance(citation, dict):
        return "Handoff citation must be an object."
    for item in (citation or {}).get("source"), packet.get("previous_request"):
        if item is not None and not isinstance(item, str):
            return "Handoff citation source and previous_request must be strings."
    follow = packet.get("recorded_follow_up")
    if follow is not None and (not isinstance(follow, list) or not all(
            isinstance(item, dict) and all(
                item.get(key) is None or isinstance(item.get(key), str)
                for key in ("kind", "target", "status"))
            for item in follow)):
        return "Handoff recorded_follow_up must be a list of string-valued objects."
    missing = packet.get("missing")
    if missing is not None and (not isinstance(missing, list)
                                or not all(isinstance(item, str) for item in missing)):
        return "Handoff missing must be a list of strings."
    return None


def cmd_receive_handoff(args):
    """Write a prepared receiver brief from a packet. Does not invoke a receiver agent."""
    source = os.path.abspath(os.path.expanduser(args.packet))
    output = os.path.abspath(os.path.expanduser(args.output))
    if os.path.realpath(source) == os.path.realpath(output):
        print("Receiver output must be a different path from the handoff packet.",
              file=sys.stderr)
        return 2
    try:
        with open(source, encoding="utf-8") as f:
            packet = json.load(f)
    except (OSError, ValueError) as exc:
        print("Cannot read handoff: %s" % exc, file=sys.stderr)
        return 2
    problem = _packet_error(packet)
    if problem:
        print(problem, file=sys.stderr)
        return 2
    if packet.get("receiver_harness") != args.as_harness:
        print("Packet targets %s, not %s."
              % (core.safe_text(packet.get("receiver_harness") or "(unnamed)"), args.as_harness),
              file=sys.stderr)
        return 2
    correction = core.safe_text(packet.get("correction") or "")
    if not correction:
        print("Handoff has no correction to use.", file=sys.stderr)
        return 2
    # Keep acknowledgement pending until a real receiver leaves evidence.
    remaining = list(packet.get("missing") or [])
    if "receiver acknowledgement" not in remaining:
        remaining.append("receiver acknowledgement")
    citation = packet.get("citation") or {}
    if citation.get("source") and os.path.realpath(output) == os.path.realpath(citation["source"]):
        print("Receiver brief must not overwrite source transcript.", file=sys.stderr)
        return 2
    evidence = _source_evidence_state(citation, packet.get("source_request") if packet.get("instruction_origin") else correction)
    state, open_cmd = evidence["state"], evidence["open"]
    # Outcomes come from the live source only when it still holds this exact
    # request. Otherwise the packet's own record is shown, labelled provisional.
    follow = evidence["events"] if state == "available" else (packet.get("recorded_follow_up") or [])
    if state == "missing" and "matching source transcript" not in remaining:
        remaining.insert(0, "matching source transcript")
    elif state != "available" and "source request confirmation" not in remaining:
        remaining.insert(0, "source request confirmation")

    if state == "available":
        evidence_status = "source available; Open command below reopens the exact request."
        follow_title = "Recorded follow-up (tool execution, not task correctness):"
    else:
        follow_title = "Recorded follow-up (provisional, copied from the packet; not read from the source):"
        if state == "missing":
            evidence_status = (
                "source missing or moved. Recorded follow-up below is provisional from the packet. "
                "Restore the file and re-run ask, or pass the new path to replay --line.")
        elif state == "unreadable":
            evidence_status = (
                "source present but could not be read. Treat outcomes as provisional. "
                "Check the file, then re-run ask to refresh citations.")
        else:
            evidence_status = (
                "source present but the cited line no longer holds this request. "
                "Treat outcomes as provisional. Re-run ask to refresh citations, then Open again.")

    follow_lines = "".join(
        "- %s %s (%s)\n" % (core.safe_text(item.get("kind") or "tool"),
                            core.safe_text(item.get("target") or "?"),
                            core.safe_text(item.get("status") or "unknown"))
        for item in follow) or "- (none recorded)\n"
    previous = core.safe_text(packet.get("previous_request") or "")
    synthetic = packet.get("synthetic") is True or evidence["synthetic"]
    brief = (
        "# Prepared receiver brief\n\n"
        "Harness: %s\n\n"
        "Provenance: %s\n\n"
        "Status: acknowledgement pending. No receiver agent was invoked by this command.\n\n"
        "Evidence: %s\n\n"
        "Prepared instruction for receiver: %s\n\n"
        "Previous request: %s\n\n"
        "Source: %s:L%s\n\n"
        "%s"
        "%s\n%s\n"
        "Still missing before completion can be claimed:\n%s\n"
        % (args.as_harness,
           "SYNTHETIC EXAMPLE. Invented instruction; not a real user request"
           if synthetic else "source transcript (not independently verified)",
           evidence_status,
           correction,
           previous or "(not recorded)",
           core.safe_text(citation.get("source") or "?"),
           core.safe_text(citation.get("line") or "?"),
           ("Open: %s\n\n" % open_cmd) if open_cmd else "",
           follow_title,
           follow_lines,
           "".join("- %s\n" % core.safe_text(item) for item in remaining)
           or "- task correctness verification\n")
    )
    if packet.get("instruction_origin"):
        brief += "\nInstruction provenance: explicitly authored for this handoff; not a detector verdict, inferred human REDO or research label.\n"
    observation = packet.get("detector_observation")
    if observation:
        brief += "\nDetector observation (historical model suggestion, not a human label):\n" + json.dumps(observation, indent=2) + "\n"
        if observation.get("fixture"):
            brief += "TEST FIXTURE transport; no real model observation.\n"
    _write_private(output, brief)
    print("Prepared receiver brief: " + output)
    if open_cmd:
        print("Open: " + open_cmd)
    if state != "available":
        print("Evidence: " + evidence_status, file=sys.stderr)
    print("Still missing: " + ("; ".join(remaining) or "task correctness verification"))
    return 0


def _human_prompt(d):
    """The text of a genuine human turn, or '' — reuses the measured gate."""
    return core.human_text(d)


def _tool_input(b):
    """A tool_use block's arguments as a dict, or {} when it is not one.

    Cursor persists an IN-FLIGHT tool call with its arguments still a raw JSON
    string prefix (`{"contents": "`), and one such record in a corpus was enough
    to abort `coach --harness cursor` with an AttributeError. A partial call has
    no arguments to read yet, so it reads as no arguments rather than as a crash."""
    inp = b.get("input")
    return inp if isinstance(inp, dict) else {}


def _tool_uses(rec):
    if rec.get("type") != "assistant":
        return []
    c = (rec.get("message") or {}).get("content")
    return [b for b in c if isinstance(b, dict) and b.get("type") == "tool_use"] \
        if isinstance(c, list) else []


# ============================================================================
# JSON reader and file discovery. Harness normalization lives in transcripto_core.

def _iter_json(path):
    return core.iter_json(path)


def _sniff(path):
    """'codex' (rollout), 'codex-history' (history.jsonl), or 'claude', from the
    first parseable record. Lets `--root ~/.codex` and mixed dirs just work."""
    for d in _iter_json(path):
        if d.get("type") == "session_meta" or ("payload" in d and "timestamp" in d):
            return "codex"
        if {"session_id", "ts", "text"}.issubset(d) and "message" not in d:
            return "codex-history"
        # Cursor: role + message only, and none of Claude's envelope fields.
        if "role" in d and "message" in d and "promptSource" not in d:
            return "cursor"
        return "claude"
    return "claude"


def _rows_for_file(path):
    return core.read_session(path)


def _coach_files(roots, harness):
    """Discover transcript files. For a Codex tree we name the two real episode
    dirs explicitly — a blind **/*.jsonl over ~/.codex swallows session_index,
    the .tmp scratch, and history.jsonl (double-counted turns)."""
    paths = []
    for r in roots:
        r = os.path.expanduser(r)
        if os.path.isfile(r):
            paths.append(r)
            continue
        base = os.path.basename(r.rstrip("/"))
        if base == ".cursor" or (harness == "cursor" and os.path.isdir(os.path.join(r, "projects"))):
            paths += sorted(glob.glob(
                os.path.join(r, "projects", "*", "agent-transcripts", "*", "*.jsonl")))
            continue
        if harness == "codex" or base == ".codex":
            got = sorted(glob.glob(os.path.join(r, "archived_sessions", "*.jsonl")))
            got += sorted(glob.glob(os.path.join(r, "sessions", "**", "*.jsonl"),
                                    recursive=True))
            if not got:  # a flat dir of rollouts (e.g. a test fixture)
                got = [p for p in sorted(glob.glob(os.path.join(r, "**", "*.jsonl"),
                                                   recursive=True))
                       if os.path.basename(p) not in ("session_index.jsonl",
                                                       "history.jsonl")
                       and os.sep + ".tmp" + os.sep not in p]
            paths += got
        else:
            paths += sorted(glob.glob(os.path.join(r, "**", "*.jsonl"), recursive=True))
    paths = sorted({os.path.abspath(p) for p in paths})
    if harness:
        paths = [p for p in paths if _sniff(p) == harness]
    return paths


# ============================================================================
# paste detection — subtract echoed agent output from the human signal
# ============================================================================
# A `typed` turn is flagged likely-PASTED when its text is a verbatim substring
# or a high n-gram overlap of an EARLIER agent/tool message in the SAME session.
# Cheap tier only: session-scoped, 8-gram overlap, whitespace-normalised. The
# length floor is load-bearing — a short genuine turn ("run the tests") can never
# echo a long agent message, and the floor is exactly what keeps it unflagged.

_PASTE_MIN_WORDS = 15
_PASTE_THRESH = 0.6
_PASTE_N = 8


def _pnorm(s):
    return " ".join(s.lower().split())


def _pgrams(s, n=_PASTE_N):
    toks = _pnorm(s).split()
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)} \
        if len(toks) >= n else set()


def _is_echo(text, prior, thresh=_PASTE_THRESH, n=_PASTE_N):
    """True if `text` verbatim-appears in, or shares >= thresh of its n-grams
    with, any earlier agent/tool message. `prior` is a list of precomputed
    (anorm, agrams) pairs — each agent text is normalised and n-grammed ONCE
    when it enters the stream, not re-derived per human turn (was O(n^2))."""
    hnorm, hg = _pnorm(text), _pgrams(text, n)
    for anorm, ag in prior:
        if len(hnorm) >= 40 and hnorm in anorm:
            return True
        if hg and ag and len(hg & ag) / len(hg) >= thresh:
            return True
    return False


def _paste_stream(path, harness):
    """Use the same normalized authorship and result records on every harness."""
    items = []
    rows, _ = core.read_session(path)
    for row in rows:
        human = core.human_text(row)
        if human:
            items.append(("human", human))
        else:
            text = extract(row)[1]
            if text:
                items.append(("agent", text))
    return items


def detect_pastes(stream, min_words=_PASTE_MIN_WORDS):
    """Set of human turn texts that are likely-pasted echoes of earlier output."""
    flagged, prior = set(), []
    for kind, text in stream:
        if kind == "agent":
            # cache (normalised, n-gram-set) ONCE per agent/tool text so each is
            # computed a single time, not recomputed for every later human turn.
            prior.append((_pnorm(text), _pgrams(text)))
            continue
        if len(text.split()) < min_words:
            continue
        if _is_echo(text, prior):
            flagged.add(text)
    return flagged


def extract_episodes(rows, source="", pasted=None):
    result = []
    for ep in core.episodes(rows, source):
        if ep["prompt"] in (pasted or set()):
            continue
        mutations = [e for e in ep["events"] if e["kind"] in ("edit", "commit", "rollback")]
        success = [e for e in mutations if e["status"] == "succeeded"]
        unknown = any(e["status"] == "unknown" for e in mutations)
        # A rollback's affected revision cannot be inferred from its presence.
        # Preserve the call in replay; do not claim continued durability.
        last_success = max((i for i, e in enumerate(mutations) if e["status"] == "succeeded"), default=-1)
        later_rollback = any(e["kind"] == "rollback" and e["status"] != "failed" for e in mutations[last_success + 1:])
        if later_rollback or (success and success[-1]["kind"] == "rollback"):
            tier = "unknown"
        elif success:
            tier = "commit" if success[-1]["kind"] == "commit" else "artifact"
        elif unknown:
            tier = "unknown"
        else:
            tier = "none"
        witnessed = success[-1] if success else (mutations[-1] if mutations else None)
        result.append({"opener": ep["prompt"], "source": source, "line": ep["line"],
            "tier": tier, "probe": {"commit": "COMMIT-WITNESSED", "artifact": "ARTIFACT-WITNESSED",
                "unknown": "OUTCOME-UNKNOWN", "none": "NO-SUCCESSFUL-CHANGE"}[tier],
            "score": 2 if tier == "commit" else int(tier == "artifact"),
            "survived": None if tier == "unknown" else tier in ("commit", "artifact"), "corrective_turns": 0,
            "assistant_turns": len(ep["events"]), "has_mutation": bool(mutations),
            "witness": ((witnessed["kind"] + " " + witnessed["target"]) if witnessed else "No change call recorded"),
            "events": ep["events"]})
    return result


def prompt_patterns(text):
    """Mechanical, observable tags for one prompt. Every tag is a feature of the
    text itself, never an inferred 'style'."""
    tags, wc = [], len(text.split())
    intent = _intent(text)
    tags.append("intent:%s" % intent if intent else "intent:none")
    tags.append("names-a-concrete-object" if _objects(text) else "no-object (pronoun/vague)")
    tags.append("terse (<8 words)" if wc < 8 else
                ("medium (8-40 words)" if wc <= 40 else "detailed (>40 words)"))
    if _FILE_RE.search(text):
        tags.append("cites-a-file-or-path")
    if _CHECK_RE.search(text.lower()):
        tags.append("states-a-check-or-done-condition")
    return tags


def _wilson(k, n, z=1.96):
    """95% Wilson score interval for a proportion. Returns (lo, hi)."""
    if not n:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - margin) / denom, (centre + margin) / denom


def rank_patterns(episodes, baseline=None):
    """Descriptive proportions only. Correlated, overlapping habits are not advice."""
    buckets = {}
    for ep in episodes:
        if ep.get("has_mutation", True) and ep.get("tier") != "unknown":
            for tag in prompt_patterns(ep["opener"]):
                buckets.setdefault(tag, []).append(ep)
    out = []
    for tag, eps in sorted(buckets.items()):
        n = len(eps)
        k = sum(bool(e["survived"]) for e in eps)
        lo, hi = _wilson(k, n)
        out.append({"pattern": tag, "n": n, "survived": k, "survival_rate": k / n,
                    "ci_lo": lo, "ci_hi": hi, "rankable": n >= MIN_PATTERN_N,
                    "distinguishable": False, "reason": "descriptive_only"})
    return out


def _codex_history_overlap(roots, human_texts):
    """C1 control: ~/.codex/history.jsonl records the SAME typed turns the rollouts
    carry as user items, minus all context. Ingest it and check the overlap — it
    proves the gate reads the rollouts right, without letting a stale, context-free
    input log double-count into the episode grades. Returns (lines, matched)."""
    lines = matched = 0
    full = [t for t in human_texts if t]
    for r in roots:
        hp = os.path.join(os.path.expanduser(r), "history.jsonl")
        if not (os.path.isfile(hp) and _sniff(hp) == "codex-history"):
            continue
        for d in _iter_json(hp):
            txt = (d.get("text") or "").strip()
            # a one-word input ("n", "yes") is a substring of nearly every turn,
            # so it would match trivially and make this control unfailable. Only
            # count lines long enough that a match actually proves the gate read
            # the rollouts right, and match against the FULL turn, not a head.
            if len(txt) < 12:
                continue
            lines += 1
            if any(txt in h or h in txt for h in full):
                matched += 1
    return lines, matched


def _coach_roots(root=None, harness=None):
    """The directories coach will read, given an explicit --root and --harness.
    Single source of truth so the empty-result message names the real path."""
    if root:
        return [root]
    if harness == "codex":
        return [os.path.expanduser("~/.codex")]
    if harness == "cursor":
        return [os.path.expanduser("~/.cursor")]
    if harness == "claude":
        return [os.path.join(HOME, ".claude", "projects")]
    return list(ROOTS)


def coach(roots=None, harness=None, verified_human=False, detector=None):
    """Describe submitted requests and the execution evidence attached to them.
    detector: None (the local regex) or a JevDetector, see _jev_detector()."""
    if not roots:
        roots = _coach_roots(None, harness)
    paths = _coach_files(roots, harness)
    episodes, records, humans, pastes, corrections = [], 0, 0, 0, 0
    human_texts, harnesses, typed_texts = [], set(), []
    for p in paths:
        rows, fh = _rows_for_file(p)
        rows = [row for row in rows if row.get("transcripto_synthetic") is not True]
        if fh == "codex-history":
            continue
        harnesses.add(fh)
        records += len(rows)
        pasted = set()
        if verified_human:
            pasted = detect_pastes(_paste_stream(p, fh))
            pastes += len(pasted)
        for row in rows:
            t = _human_prompt(row)
            if t and t not in pasted:
                human_texts.append(t)
        typed, corr = count_corrections(rows, pasted)   # same gate as the line above
        humans += typed
        corrections += corr
        if detector is not None:
            typed_texts.extend(t for t, _ in _typed_turns(rows, pasted))
        if not getattr(detector, "dry_run", False):
            episodes += extract_episodes(rows, source=p, pasted=pasted)

    if getattr(detector, "dry_run", False):
        resolved = harness or (next(iter(harnesses)) if len(harnesses) == 1 else "mixed" if harnesses else "auto")
        return _jev_preview_report(detector, typed_texts, resolved, len(paths), records)

    patterns = rank_patterns(episodes)
    indistinct = [p for p in patterns if p["rankable"]]
    durable = sum(1 for e in episodes if e["survived"])
    known_changes = sum(e["has_mutation"] and e["tier"] != "unknown" for e in episodes)
    tiers = {t: sum(1 for e in episodes if e["tier"] == t)
             for t in ("commit", "artifact", "reverted", "none", "unknown")}
    resolved = (harness or ("codex" if harnesses == {"codex"}
                            else "claude" if harnesses == {"claude"}
                            else "cursor" if harnesses == {"cursor"}
                            else "mixed" if harnesses else "auto"))
    hist_lines, hist_matched = (_codex_history_overlap(roots, human_texts)
                                if "codex" in harnesses or harness == "codex"
                                else (0, 0))
    out = {
        "schema": "transcripto.coach/2",
        "harness": resolved,
        "verified_human": verified_human, "pastes_flagged": pastes,
        "history_lines": hist_lines, "history_matched": hist_matched,
        "files": len(paths), "total_records": records, "human_turns": humans,
        "human_pct": round(100 * humans / records, 2) if records else 0.0,
        # correction rate = typed turns that correct the agent / typed turns.
        # See is_correction(); lexical markers can have false positives and misses.
        "corrections": corrections,
        "correction_rate": round(corrections / humans, 3) if humans else 0.0,
        "episodes": len(episodes), "durable": durable,
        "durable_rate": round(durable / known_changes, 3) if known_changes else None,
        "known_change_requests": known_changes,
        "tiers": tiers,
        "top_patterns": [],
        "all_patterns": patterns,
        "bottom_patterns": [],
        "best_prompt": None,  # deprecated: execution evidence is not prompt quality
        "worst_prompt": None,
        "successful_request": next((e for e in reversed(episodes) if e["survived"] is True), None),
        "failed_request": next((e for e in reversed(episodes) if any(x["status"] == "failed" for x in e["events"])), None),
        "indistinct_patterns": indistinct,
        "sparse": len(indistinct) < 5,
        "rankable_corpus": False,
        "proxy": ("PROXY: a matching tool result reported a successful change. "
                  "Not proof of correctness, durability, or shipping. Unknown outcomes are excluded from habit proportions."),
    }
    if detector is not None:
        out.update(_jev_score(detector, typed_texts))
    return out



def cmd_coach(args):
    r = coach([args.root] if args.root else None, harness=args.harness,
              verified_human=args.verified_human, detector=_jev_detector(args))
    if args.json:
        print(json.dumps(r, indent=2)); return
    if r.get("jev", {}).get("dry_run"):
        _print_jev_line(r)
        return
    if not r["episodes"]:
        print("No prompt episodes found. Looked in: " + ", ".join(_coach_roots(args.root, args.harness)))
        print("Try transcripto replay --demo, --harness codex, --harness cursor, or --root <dir>.")
        return
    print("YOUR REQUESTS, ON THE RECORD\n")
    print("%s submitted turns · %s requests · %s transcript(s) · %s" % (
        r["human_turns"], r["episodes"], r["files"], r["harness"]))
    print("episodes: %s observed, %s with a successful change result" % (r["episodes"], r["durable"]))
    print("%s unknown change outcomes; missing evidence is not failure." % r["tiers"]["unknown"])
    print("\n" + r["proxy"])
    if r["episodes"] < MIN_EPISODES_TO_RANK:
        print("\nSmall history: %d requests. Replay works from one request." % r["episodes"])
    print("\nMEASURED, NOT RANKED")
    print("Change attempts with known outcomes only. These overlapping groups are descriptive, not instructions.")
    for p in r["indistinct_patterns"]:
        print("  %3d%% (%d/%d) %s" % (round(p["survival_rate"] * 100), p["survived"], p["n"], p["pattern"]))
    if r.get("correction_detector") == "jev":
        print()
        _print_jev_line(r)
    else:
        print("\nCorrection markers: %d of %d turns (%d%%). A lexical estimate, with false positives and misses." % (
            r["corrections"], r["human_turns"], round(r["correction_rate"] * 100)))
    if r["history_lines"]:
        print("Codex history overlap: %d/%d checkable entries." % (r["history_matched"], r["history_lines"]))
    if r["verified_human"]:
        print("%d likely pasted turns excluded." % r["pastes_flagged"])
    print("\nInspect the evidence: transcripto replay --failures or transcripto replay latest")


# ============================================================================
# export-run — one run's numbers as JSON, the contract Agent Grinder and ZUP read
# ============================================================================
# Reads the transcript file directly (no index needed), applies the same
# authorship gate and the same correction classifier coach uses, and adds the
# run envelope: when it started and ended, what the agent touched, and what got
# committed in that window. Every key is documented in README.md > export-run.


def _epoch(ts):
    """ISO-8601 transcript stamp -> unix seconds, or None. Accepts the 'Z' Claude
    Code and Codex write and the naive local stamp the Cursor connector yields."""
    if not isinstance(ts, str) or not ts:
        return None
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.astimezone()           # naive = local wall clock
    return d.timestamp()


def _iso(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat(
        timespec="seconds").replace("+00:00", "Z")


def _git_dir(cwd):
    """The .git directory governing `cwd` (walking up), resolving a `.git` FILE
    (worktree / submodule) to the gitdir it points at. None if not in a repo."""
    d = os.path.abspath(os.path.expanduser(cwd or ""))
    while True:
        g = os.path.join(d, ".git")
        if os.path.isdir(g):
            return g
        if os.path.isfile(g):
            try:
                first = open(g).readline().strip()
            except OSError:
                return None
            if first.startswith("gitdir:"):
                target = first[len("gitdir:"):].strip()
                return os.path.normpath(os.path.join(d, target))
            return None
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def _reflog_commits(cwd, start=None, end=None):
    """Commits recorded in cwd's reflog (.git/logs/HEAD) stamped inside
    [start, end] (unix seconds, either side open when None), as a list of
    {sha, ts, subject}; None when cwd is not inside a git repo.

    Read straight from the file, not from `git log`: the README's privacy claim
    is that nothing here shells out, and this is the one place that would have
    crept in. The reflog is the record of what THIS working tree did: a commit made
    here lands in it, a commit pulled in from elsewhere does not, which is the
    right side of the line for a run receipt. It is local and git expires it
    (90 days by default), so a run older than that can read 0 here while
    `git log` would still show its commits. `commit (amend)` counts as a
    commit; a rebase's `pick` lines do not."""
    g = _git_dir(cwd)
    if not g:
        return None
    out = []
    try:
        f = open(os.path.join(g, "logs", "HEAD"), "r", errors="replace")
    except OSError:
        return out
    with f:
        for line in f:
            head, _, msg = line.rstrip("\n").partition("\t")
            parts = head.split()
            if len(parts) < 4 or not msg.startswith("commit"):
                continue
            try:
                stamp = int(parts[-2])
            except ValueError:
                continue
            if (start is not None and stamp < start) or (end is not None and stamp > end):
                continue
            out.append({"sha": parts[1][:7], "ts": _iso(stamp),
                        "subject": msg.partition(": ")[2]})
    return out


def _resolve_run(target, roots, harness):
    """The transcript file `target` names: 'latest' (newest by mtime; a spawned
    sub-agent's file is not a run of yours and is skipped), a session id or a
    prefix of one, or a path to a .jsonl. None when nothing matches."""
    if target != "latest" and os.path.isfile(target):
        return target
    paths = [p for p in _coach_files(roots, harness)
             if os.sep + "subagents" + os.sep not in p
             and os.path.basename(p) not in ("history.jsonl", "session_index.jsonl")]
    if not paths:
        return None
    if target == "latest":
        for path in sorted(paths, key=os.path.getmtime, reverse=True):
            if any(core.human_text(r) for r in _rows_for_file(path)[0]):
                return path
        return None
    hits = [p for p in paths if os.path.basename(p).startswith(target)]
    if not hits:                     # codex names rollouts rollout-<date>-<id>.jsonl
        hits = [p for p in paths if target in os.path.basename(p)]
    return max(hits, key=os.path.getmtime) if hits else None


def export_run(path, detector=None):
    """The run-level numbers of one transcript file, as a JSON-ready dict.
    detector: None (the local regex) or a JevDetector, see _jev_detector()."""
    rows, harness = _rows_for_file(path)
    if getattr(detector, "dry_run", False):
        return _jev_preview_report(detector, [t for t, _ in _typed_turns(rows)], harness, records=len(rows))
    sid = next((r.get("sessionId") for r in rows if r.get("sessionId")), "") \
        or os.path.splitext(os.path.basename(path))[0]
    cwd = next((r.get("cwd") for r in reversed(rows) if r.get("cwd")), "")
    stamps = [e for e in (_epoch(r.get("timestamp")) for r in rows) if e is not None]
    start, end = (min(stamps), max(stamps)) if stamps else (None, None)
    typed, corrections = count_corrections(rows)
    tool_calls, files = 0, set()
    for r in rows:
        for b in _tool_uses(r):
            tool_calls += 1
            if b.get("name") in FILE_TOOLS:
                inp = _tool_input(b)
                fp = inp.get("file_path") or inp.get("notebook_path")
                files.update(p for p in (inp.get("paths") or ([fp] if fp else [])) if isinstance(p, str))
    commits = _reflog_commits(cwd, start, end) if cwd and start is not None and end is not None else None
    out = {
        "schema": "transcripto.export-run/1",
        "session_id": sid,
        "project": cwd,
        "harness": harness,
        "transcript": path,
        "started": _iso(start) if start is not None else None,
        "ended": _iso(end) if end is not None else None,
        "duration_s": int(round(end - start)) if stamps else None,
        "records": len(rows),
        "typed_turns": typed,
        "corrections": corrections,
        "correction_rate": round(corrections / typed, 3) if typed else None,
        "tool_calls": tool_calls,
        "files_touched": sorted(files),
        "commits_in_window": len(commits) if commits is not None else None,
        "commits": commits,
        "proxy": ("typed_turns is the authorship gate (typed/queued, never meta, "
                  "sidechain or tool output); correction_rate is a lexical estimate; "
                  "commits_in_window is this tree's reflog inside the run window, "
                  "null when the project is not a git repo."),
    }
    if detector is not None:
        out.update(_jev_score(detector, [t for t, _ in _typed_turns(rows)]))
        out["proxy"] = out["proxy"].replace("correction_rate is a lexical estimate", "correction_rate is a Jev model estimate over scored turns, not a human correction label")
    return out


def cmd_export_run(args):
    roots = _coach_roots(args.root, args.harness)
    path = _resolve_run(args.target, roots, args.harness)
    if not path:
        sys.stderr.write("\n  no transcript matches '%s'.\n" % args.target)
        sys.stderr.write("  looked in: %s\n" % ", ".join(roots))
        sys.stderr.write("  pass a session id (or a prefix of one), 'latest', or a path "
                         "to a .jsonl; --root / --harness as for coach.\n\n")
        sys.exit(2)
    print(json.dumps(export_run(path, detector=_jev_detector(args)), indent=2))


def _add_detector_args(s):
    g = s.add_argument_group("correction detector")
    g.add_argument("--detector", choices=["regex", "jev"], default="regex",
                   help="regex (default): local, offline. jev: SENDS privacy-filtered "
                        "typed turns to OpenRouter (TypeSafe Jev). Needs OPENROUTER_API_KEY. "
                        "Opt-in per run; no env var or config file turns it on.")
    g.add_argument("--jev-dry-run", action="store_true",
                   help="with --detector jev, preview privacy counts locally; no key or network")
    g.add_argument("--jev-threshold", type=float, default=0.30,
                   help="P(correction) at or above this is a correction (default 0.30)")
    g.add_argument("--jev-batch", type=int, default=1,
                   help="turns per Jev request (default 1, the measured formulation). "
                        "Above 1 is cheaper but MOVES the answers: on 10 live rows, "
                        "P(correction) shifted by up to 0.55 at batch 5 and 10")
    g.add_argument("--jev-max-usd", type=float, default=1.00,
                   help="stop sending once this much is spent (default 1.00)")
    g.add_argument("--jev-fallback-regex", action="store_true",
                   help="with --detector jev and no key, use the local regex instead of failing")


def main():
    p = argparse.ArgumentParser(prog=PROG, description=__doc__ + USAGE,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version="%s %s" % (PROG, VERSION))
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("import-example", help="install a synthetic public trace locally")
    s.add_argument("--force", action="store_true", help="replace a changed example import")
    s.set_defaults(fn=cmd_import_example)
    s = sub.add_parser("import-lab", help="install labelled cross-harness failed/ok/? traces")
    s.add_argument("--force", action="store_true", help="replace a changed lab import")
    s.set_defaults(fn=cmd_import_lab)
    s = sub.add_parser("quickstart", help="print offline wheel install / search / reopen card")
    s.add_argument("--wheel", help="absolute wheel path to embed in the install commands")
    s.set_defaults(fn=cmd_quickstart)
    sub.add_parser("index").set_defaults(fn=cmd_index)
    s = sub.add_parser("backfill-harness", help="label unlabelled rows from their source path (dry run by default)")
    s.add_argument("--db", help="index file (default ~/.trace/trace.db)")
    s.add_argument("--apply", action="store_true", help="write the labels; without it nothing is written")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_backfill_harness)
    s = sub.add_parser("watch"); s.add_argument("--interval", type=int, default=5); s.set_defaults(fn=cmd_watch)
    s = sub.add_parser("ask"); s.add_argument("query"); s.add_argument("-n", "--limit", type=int, default=25); s.set_defaults(fn=cmd_ask)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("-n", "--limit", type=int, default=25); s.set_defaults(fn=cmd_search)
    s = sub.add_parser("find"); s.add_argument("name"); s.set_defaults(fn=cmd_find)
    s = sub.add_parser("trace"); s.add_argument("query"); s.add_argument("-n", "--limit", type=int, default=10)
    s.add_argument("-a", "--all", action="store_true", help="show the complete replay sequence")
    s.set_defaults(fn=cmd_trace)
    s = sub.add_parser("sessions"); s.add_argument("-n", "--limit", type=int, default=30)
    s.add_argument("--all", action="store_true",
                   help="include sessions you never typed in (85%% of them, on a real corpus)")
    s.set_defaults(fn=cmd_sessions)
    s = sub.add_parser("changes", help="show cited disagreement and correction sequences")
    s.add_argument("-n", "--limit", type=int, default=10)
    s.set_defaults(fn=cmd_changes)
    s = sub.add_parser("selected-context", help="bounded local run metadata and consented selected replay; no refresh or model")
    s.add_argument("mode",choices=["runs","describe","episodes","authored-continuation"])
    s.add_argument("--index",default=DB,help="existing local index, read-only")
    s.add_argument("--cwd",help="exact existing repository directory")
    s.add_argument("--source",help="explicit local session file")
    s.add_argument("--limit",type=int,default=20)
    s.add_argument("--accept-sha",help="source SHA256 shown before consent")
    s.add_argument("--consent",action="store_true",help="allow reading selected session locally")
    s.add_argument("--line",type=int,help="exact selected request for authored continuation")
    s.add_argument("--instruction",help="explicit authored change; separate from cross-harness handoff")
    s.set_defaults(fn=cmd_selected_context)
    s = sub.add_parser("handoff", help="write a cited correction packet")
    s.add_argument("query", nargs="?", help="words from the correction to hand off")
    s.add_argument("--findings", help="recorded selected-session Jev report")
    s.add_argument("--line", type=int, help="exact selected request source line")
    s.add_argument("--source",help="explicit session for an authored instruction, no model report required")
    s.add_argument("--accept-sha",help="source hash shown before local-view consent")
    s.add_argument("--instruction",help="explicitly authored correction; not a detector verdict")
    s.add_argument("--consent",action="store_true",help="allow selected replay in the private packet")
    s.add_argument("--to-harness", required=True, choices=["claude", "codex", "cursor"])
    s.add_argument("--output", required=True, help="receiver inbox JSON path")
    s.set_defaults(fn=cmd_handoff)
    s = sub.add_parser("receive-handoff", help="prepare a receiver brief (does not invoke a receiver)")
    s.add_argument("packet", help="handoff packet JSON")
    s.add_argument("--as-harness", required=True, choices=["claude", "codex", "cursor"])
    s.add_argument("--output", required=True, help="separate receiver brief path")
    s.set_defaults(fn=cmd_receive_handoff)
    sub.add_parser("stats").set_defaults(fn=cmd_stats)
    s = sub.add_parser("cost")
    s.add_argument("--days", type=int, default=30, help="window in days (0 = all time)")
    s.add_argument("--root", help="scan this transcript dir instead of ~/.claude/projects")
    s.add_argument("--json", action="store_true", help="machine-readable, for other tools")
    s.set_defaults(fn=cmd_cost)
    s = sub.add_parser("coach")
    s.add_argument("--root", help="read this transcript directory")
    s.add_argument("--harness", choices=["claude", "codex", "cursor"],
                   help="which agent's transcripts to grade. codex reads "
                        "~/.codex (archived_sessions + sessions); cursor reads "
                        "~/.cursor/projects/*/agent-transcripts. default: all three")
    s.add_argument("--verified-human", dest="verified_human", action="store_true",
                   help="subtract likely-PASTED turns: a typed turn whose text is a "
                        "verbatim/high n-gram echo of an earlier agent or tool message "
                        "in the same session, from the human signal before grading")
    s.add_argument("--json", action="store_true", help="machine-readable, for other tools")
    _add_detector_args(s)
    s.set_defaults(fn=cmd_coach)
    s = sub.add_parser("jev-findings", help="inspect one selected session with explicit Jev opt-in; reference-only report")
    s.add_argument("target", help="explicit session path, ID or latest")
    s.add_argument("--output", help="private local findings report for replay/handoff")
    _add_detector_args(s)
    s.set_defaults(fn=cmd_jev_findings)
    s = sub.add_parser("export-run")
    s.add_argument("target", help="a session id (or a prefix of one), 'latest', or a "
                                  "path to a .jsonl transcript")
    s.add_argument("--root", help="look in this transcript dir instead of ~/.claude/projects")
    s.add_argument("--harness", choices=["claude", "codex", "cursor"],
                   help="which agent's transcripts to look in. default: all three")
    _add_detector_args(s)
    s.set_defaults(fn=cmd_export_run)
    s = sub.add_parser("replay", help="replay requests and their recorded tool results")
    s.add_argument("target", nargs="?", default="latest", help="latest, a transcript path, or words from a request")
    s.add_argument("--findings", help="reopen an exact line from a source-bound Jev findings report")
    s.add_argument("--session", help="explicit session ID or an unambiguous filename prefix")
    selection = s.add_mutually_exclusive_group()
    selection.add_argument("--episode", type=int, help="request number within the session")
    selection.add_argument("--line", type=int, help="exact human request source line (requires a transcript path)")
    s.add_argument("--events", type=int, default=12, help="events displayed per request (default 12)")
    s.add_argument("--limit", type=int, default=5, help="matching requests to show")
    s.add_argument("--all", action="store_true", help="all requests and events in the selected session")
    s.add_argument("--failures", action="store_true", help="jump to a request with a failed tool call")
    s.add_argument("--demo", action="store_true", help="run an explicitly synthetic replay")
    output = s.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--share", action="store_true", help="counts and caveat only; no prompts or paths")
    s.set_defaults(fn=lambda a: sys.exit(cmd_replay(a, _coach_files(_coach_roots(a.root, a.harness), a.harness))))
    for name, parser in sub.choices.items():
        if name not in ("coach", "cost", "export-run", "import-example", "import-lab",
                        "quickstart", "receive-handoff", "backfill-harness"):
            parser.add_argument("--root", help="read transcripts in this directory")
            parser.add_argument("--harness", choices=["claude", "codex", "cursor"], help="default: all three")
    a = p.parse_args(["replay"] if len(sys.argv) == 1 else None)
    if getattr(a, "events", 1) < 1 or getattr(a, "limit", 1) < 1 or (getattr(a, "episode", None) is not None and a.episode < 1):
        p.error("episode, events, and limit must be positive")
    if a.cmd == "replay" and getattr(a, "line", None) is not None and (a.line < 1 or (a.target == "latest" and not a.findings) or getattr(a, "session", None) or a.demo):
        p.error("--line requires a positive line number and an explicit transcript path")
    if getattr(a, "session", None) and a.target != "latest":
        p.error("use either a positional query/path or --session")
    if getattr(a, "jev_dry_run", False) and a.detector != "jev":
        p.error("--jev-dry-run requires --detector jev")
    if getattr(a, "detector", "regex") == "jev":
        if not 0.0 < a.jev_threshold < 1.0:
            p.error("--jev-threshold must be between 0 and 1")
        if a.jev_batch < 1 or not math.isfinite(a.jev_max_usd) or a.jev_max_usd <= 0:
            p.error("--jev-batch must be at least 1 and --jev-max-usd finite and above 0")
    if getattr(a, "root", None) and not os.path.exists(os.path.expanduser(a.root)):
        p.error("--root does not exist: " + core.safe_text(a.root))
    global ROOTS, HARNESS
    if a.cmd not in ("coach", "cost", "export-run", "replay", "backfill-harness",
                     "import-example", "import-lab", "quickstart", "receive-handoff"):
        HARNESS = getattr(a, "harness", None)
        ROOTS = _coach_roots(getattr(a, "root", None), HARNESS)
    if not getattr(a, "fn", None):
        p.print_help(); return
    status = a.fn(a)
    if isinstance(status, int):
        sys.exit(status)


if __name__ == "__main__":
    main()
