#!/usr/bin/env python3
"""Search everything your coding agents ever did, and find where any file came from.

Indexes coding-agent transcripts (Claude Code ~/.claude/projects, Codex ~/.codex)
into a local SQLite full-text index. Stdlib only. No network. Your data never
leaves the machine.
"""
import sys, os, json, glob, re, sqlite3, argparse, math
from datetime import datetime, timezone

# The tool ships under two console scripts (`transcripto` and `trace`) and is also
# run as `python3 transcripto.py`. Every hint we print must name the command the
# reader actually typed, otherwise we tell a stranger to run a binary they do not
# have on PATH.
def _prog():
    n = os.path.basename(sys.argv[0] or "")
    if n.endswith(".py"):
        n = n[:-3]
    return n if n in ("transcripto", "trace") else "transcripto"


PROG = _prog()

# The single source of truth for the version, so `--version` cannot drift from the
# packaging. A stranger who reads the README on GitHub and installs from PyPI can be
# holding a different build than the one the README describes, and until this flag
# existed there was no way for them to tell which.
VERSION = "0.1.4"

USAGE = """
  %(p)s index                 build / refresh the index (incremental)
  %(p)s ask "<topic>"         YOUR OWN messages about a topic, newest first + a rollup
  %(p)s search "<query>"      full-text search across every session (you + agents)
  %(p)s find <filename>       every session that wrote, edited, or read a file
  %(p)s sessions              recent sessions, newest first, with their opening ask
  %(p)s stats                 what you work on most: projects, files, volume
  %(p)s cost                  what ONE decision of yours costs: spend / turns you typed
  %(p)s coach                 which of YOUR prompt habits actually survive (a proxy)
  %(p)s coach --harness codex grade your Codex (~/.codex) transcripts instead\n  %(p)s coach --harness cursor grade your Cursor (~/.cursor) transcripts instead
  %(p)s coach --verified-human subtract likely-PASTED turns (echoes of agent output)
  %(p)s export-run <session|latest>  one run's numbers as JSON: typed turns, correction rate, commits
""" % {"p": PROG}

HOME = os.path.expanduser("~")
ROOTS = [os.path.join(HOME, ".claude", "projects")]
DB = os.path.join(HOME, ".trace", "trace.db")

FILE_TOOLS = {"Write": "write", "Edit": "edit", "Read": "read",
              "NotebookEdit": "edit", "MultiEdit": "edit"}


def connect(require_index=True):
    """Open the local index. Six commands (search/ask/find/trace/sessions/stats)
    READ it and are meaningless without it; `index` and `watch` BUILD it and pass
    require_index=False. Before this guard existed a cold start printed a raw
    `sqlite3.OperationalError: no such table: messages_fts` — and three of the six
    printed it and still exited 0."""
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    if require_index and not con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
    ).fetchone():
        print("\n  no index yet.  (looked in %s)\n" % DB)
        print("  this command reads a local index of your transcripts. build it once:\n")
        print("    transcripto index\n")
        print("  it takes a few minutes on a large corpus and is incremental after that.")
        print("  `coach` and `cost` read your transcripts directly and need no index.\n")
        sys.exit(2)
    return con


SCHEMA_VERSION = 2  # bump when a column/tokenizer change needs a full rebuild


def _needs_rebuild(con):
    """True if the messages table exists but predates the current schema
    (missing is_human, or an old FTS tokenizer). Triggers a one-time full reindex."""
    t = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'").fetchone()
    if not t:
        return False  # fresh db — nothing to migrate
    cols = {r[1] for r in con.execute("PRAGMA table_info(messages)")}
    if "is_human" not in cols:
        return True
    fts = con.execute("SELECT sql FROM sqlite_master WHERE name='messages_fts'").fetchone()
    if fts and "porter" not in (fts[0] or ""):
        return True
    return False


def init_schema(con):
    if _needs_rebuild(con):
        con.executescript(
            "DROP TABLE IF EXISTS messages_fts; DROP TABLE IF EXISTS messages;"
            "DROP TABLE IF EXISTS files; DROP TABLE IF EXISTS indexed;")
        con.commit()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS messages(
      id INTEGER PRIMARY KEY, session_id TEXT, session_file TEXT, project TEXT,
      ts TEXT, role TEXT, cwd TEXT, git_branch TEXT, text TEXT,
      is_human INTEGER DEFAULT 0, prompt_source TEXT);
    -- porter stemming: `ask "frustration"` also matches frustrated/frustrating.
    CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
      text, content='messages', content_rowid='id', tokenize="porter unicode61");
    CREATE TABLE IF NOT EXISTS files(
      id INTEGER PRIMARY KEY, path TEXT, name TEXT, action TEXT,
      session_id TEXT, session_file TEXT, ts TEXT, cwd TEXT);
    CREATE INDEX IF NOT EXISTS idx_files_name ON files(name);
    CREATE INDEX IF NOT EXISTS idx_msg_human ON messages(is_human, ts);
    CREATE TABLE IF NOT EXISTS indexed(session_file TEXT PRIMARY KEY, mtime REAL);

    -- Stable READ-ONLY views for consumers (ZUP, Helicon). The contract: consumers
    -- open the db read-only and SELECT from these views; they never write. See READ-CONTRACT.md.
    DROP VIEW IF EXISTS v_sessions;
    CREATE VIEW v_sessions AS
      SELECT m.session_id, m.project,
             MAX(m.ts) AS last_ts, MIN(m.ts) AS first_ts,
             COUNT(*) AS n_messages,
             SUM(CASE WHEN m.role='assistant' THEN 1 ELSE 0 END) AS assistant_turns,
             (SELECT cwd FROM messages c WHERE c.session_id=m.session_id AND c.cwd!=''
              ORDER BY c.ts DESC LIMIT 1) AS cwd
      FROM messages m GROUP BY m.session_id;
    CREATE VIEW IF NOT EXISTS v_file_touches AS
      SELECT name, path, action, session_id, ts, cwd FROM files;
    -- is_human=1 marks a turn Oscar actually typed (promptSource typed/queued, not
    -- injected/tool/peer). See ask_gate() + READ-CONTRACT.md.
    DROP VIEW IF EXISTS v_messages;
    CREATE VIEW v_messages AS
      SELECT id, session_id, project, ts, role, cwd, git_branch, text,
             is_human, prompt_source FROM messages;
    """)
    con.commit()


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
                if fp:
                    files.append((FILE_TOOLS.get(name, name.lower()), fp))
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
      keep:  promptSource in (typed, queued)   — he typed it, live or while busy
      drop:  isMeta (skill bodies/images) · toolUseResult (tool output) ·
             isSidechain (spawned agent's prompt) · sdk/system (judges, peers)
    """
    if d.get("type") != "user":
        return False
    if d.get("promptSource") not in ("typed", "queued"):
        return False
    if d.get("isMeta") or d.get("isSidechain") or d.get("toolUseResult") is not None:
        return False
    return True


def _index_once(con, progress=False):
    """Incrementally index every changed/new transcript. Returns (new_sessions, new_msgs).

    progress=True prints a heartbeat to stderr. A first index over a few thousand
    transcripts takes minutes, and a silent terminal for that long reads as a hang,
    which is the point at which a first-time user kills it.
    """
    seen = []
    for root in ROOTS:
        seen += glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True)
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
        mt = os.path.getmtime(f)
        row = con.execute("SELECT mtime FROM indexed WHERE session_file=?", (f,)).fetchone()
        if row and abs(row[0] - mt) < 1e-6:
            continue
        con.execute("DELETE FROM messages WHERE session_file=?", (f,))
        con.execute("DELETE FROM files WHERE session_file=?", (f,))
        proj = os.path.basename(os.path.dirname(f))
        fallback_sid = os.path.basename(f)[:-6]
        for line in open(f, errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("type") not in ("user", "assistant"):
                continue
            role, text, fl = extract(d)
            ts = d.get("timestamp") or ""
            cwd = d.get("cwd") or ""
            gb = d.get("gitBranch") or ""
            sid = d.get("sessionId") or fallback_sid
            human = 1 if is_human_turn(d) else 0
            psrc = d.get("promptSource")
            if text:
                cur = con.execute(
                    "INSERT INTO messages(session_id,session_file,project,ts,role,cwd,git_branch,text,is_human,prompt_source)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?)", (sid, f, proj, ts, role, cwd, gb, text, human, psrc))
                con.execute("INSERT INTO messages_fts(rowid,text) VALUES(?,?)", (cur.lastrowid, text))
                msgs += 1
            for action, path in fl:
                con.execute(
                    "INSERT INTO files(path,name,action,session_id,session_file,ts,cwd)"
                    " VALUES(?,?,?,?,?,?,?)", (path, os.path.basename(path), action, sid, f, ts, cwd))
        con.execute("INSERT OR REPLACE INTO indexed(session_file,mtime) VALUES(?,?)", (f, mt))
        con.commit(); new += 1
    return new, msgs


def cmd_index(args):
    con = connect(require_index=False); init_schema(con)
    new, msgs = _index_once(con, progress=sys.stderr.isatty())
    if sys.stderr.isatty():
        sys.stderr.write(" " * 60 + "\r"); sys.stderr.flush()
    tot = con.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    print("indexed %d changed sessions · +%d messages · %d total searchable" % (new, msgs, tot))


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


def _match(query):
    terms = [t for t in query.split() if t]
    return " AND ".join('"%s"' % t.replace('"', '') for t in terms) or '""'


def _day(ts):
    return (ts or "")[:10] or "????-??-??"


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
        print("no matches. try `%s index` first, or broader terms." % PROG); return
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
    return os.path.basename(cwd) if cwd else proj


def cmd_ask(args):
    """YOUR OWN messages about a topic — the question that kills 'did I lose something?'.

    Filters to turns Oscar actually typed (is_human=1), newest first, each with
    date + repo + session id + snippet, and opens with a deterministic rollup of
    the arc: how many, how long, which repos, and your latest thought on it.
    """
    con = connect()
    try:
        rows = con.execute(
            "SELECT m.id,m.ts,m.project,m.cwd,m.session_id,m.text,"
            " snippet(messages_fts,0,'\033[1m','\033[0m','…',16)"
            " FROM messages_fts JOIN messages m ON m.id=messages_fts.rowid"
            " WHERE messages_fts MATCH ? AND m.is_human=1"
            " ORDER BY m.ts DESC LIMIT ?",
            (_match(args.query), args.limit)).fetchall()
    except sqlite3.OperationalError as e:
        print("ask error:", e); return
    if not rows:
        # Did the topic exist at all (just not in his own words)? Say so honestly.
        try:
            any_hit = con.execute(
                "SELECT COUNT(*) FROM messages_fts WHERE messages_fts MATCH ?",
                (_match(args.query),)).fetchone()[0]
        except sqlite3.OperationalError:
            any_hit = 0
        if any_hit:
            print("no messages YOU typed about '%s', but %d agent/tool turns mention it."
                  "\ntry `%s search \"%s\"` to see those, or `%s index` if it's new."
                  % (args.query, any_hit, PROG, args.query, PROG))
        else:
            print("nothing about '%s' yet. try `%s index` first, or broader terms."
                  % (args.query, PROG))
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
    lid, lts, lproj, lcwd, lsid, ltext, lsnip = rows[0]
    latest = " ".join(ltext.split())[:240]
    print("  latest (\033[2m%s\033[0m %s): \"%s\"" % (_day(lts), _repo(lcwd, lproj), latest))

    print("\n\033[2myour messages, newest first\033[0m")
    for _id, ts, proj, cwd, sid, text, snip in rows:
        print("%s  \033[36m%-20s\033[0m %s  \033[2m%s\033[0m"
              % (_day(ts), _repo(cwd, proj)[:20], " ".join(snip.split()), (sid or "")[:8]))


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
    """WHAT ACTUALLY HAPPENED after you asked. The join nothing else makes.

    `ask` shows what you typed. `find` shows what a file went through. Neither
    answers the only question that matters after the fact: you asked for X, did
    anything durable happen? This walks each of your matching prompts forward
    inside its own session and lists the writes and edits that followed it,
    stopping at your next prompt so one turn cannot claim the next turn's work.

    HONEST LIMIT, stated because the product is about claims: a write following
    a prompt in the same session is CO-OCCURRENCE, not proof the write was caused
    by that prompt or that it was correct. It is the same proxy `coach` uses and
    it is labelled the same way.
    """
    con = connect()
    try:
        rows = con.execute(
            "SELECT m.id,m.ts,m.project,m.cwd,m.session_id,m.text,m.git_branch"
            " FROM messages_fts JOIN messages m ON m.id=messages_fts.rowid"
            " WHERE messages_fts MATCH ? AND m.is_human=1"
            " ORDER BY m.ts DESC LIMIT ?",
            (_match(args.query), args.limit)).fetchall()
    except sqlite3.OperationalError as e:
        print("trace error:", e); return
    if not rows:
        print("no prompts YOU typed matching '%s'. try `%s ask \"%s\"` or `%s index`."
              % (args.query, PROG, args.query, PROG)); return

    landed = stalled = 0
    blocks = []
    for _id, ts, proj, cwd, sid, text, branch in rows:
        nxt = con.execute(
            "SELECT MIN(ts) FROM messages WHERE session_id=? AND is_human=1 AND ts>?",
            (sid, ts)).fetchone()[0]
        if nxt:
            files = con.execute(
                "SELECT ts,action,path FROM files WHERE session_id=? AND ts>? AND ts<?"
                " ORDER BY ts", (sid, ts, nxt)).fetchall()
        else:
            files = con.execute(
                "SELECT ts,action,path FROM files WHERE session_id=? AND ts>?"
                " ORDER BY ts", (sid, ts)).fetchall()
        durable = [f for f in files if f[1] in ("write", "edit")]
        if durable: landed += 1
        else: stalled += 1
        blocks.append((ts, proj, cwd, sid, text, branch, files, durable))

    total = len(blocks)
    pct = (100.0 * landed / total) if total else 0.0
    print("\033[1m%s\033[0m  %d prompt%s you typed · \033[32m%d landed\033[0m · "
          "\033[31m%d produced nothing durable\033[0m · %.0f%%"
          % (args.query, total, "" if total == 1 else "s", landed, stalled, pct))
    print("\033[2mdurable = a Write or Edit in the same session before your next prompt. "
          "CO-OCCURRENCE, not proof of cause or correctness.\033[0m\n")

    for ts, proj, cwd, sid, text, branch, files, durable in blocks:
        mark = "\033[32m●\033[0m" if durable else "\033[31m○\033[0m"
        head = " ".join((text or "").split())[:110]
        br = (" \033[2m%s\033[0m" % branch) if branch else ""
        print("%s %s  \033[36m%s\033[0m%s  \033[2m%s\033[0m"
              % (mark, _day(ts), _repo(cwd, proj)[:22], br, (sid or "")[:8]))
        print("   \033[1m\"%s\"\033[0m" % head)
        if not files:
            print("   \033[31mnothing touched\033[0m")
        else:
            shown = files if args.all else files[:8]
            for fts, action, path in shown:
                tag = {"write": "\033[32mWROTE\033[0m", "edit": "\033[33mEDIT \033[0m",
                       "read": "\033[2mread \033[0m"}.get(action, action.upper())
                print("   %s %s" % (tag, path))
            if len(files) > len(shown):
                print("   \033[2m… %d more, -a to show all\033[0m" % (len(files) - len(shown)))
        print()


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

# USD per 1M tokens (input, output), Anthropic list price, cached 2026-08-25.
PRICES = {
    "claude-fable-5":    (10.0, 50.0),
    "claude-mythos-5":   (10.0, 50.0),
    "claude-opus-5":     (5.0, 25.0),
    "claude-opus-4-8":   (5.0, 25.0),
    "claude-opus-4-7":   (5.0, 25.0),
    "claude-opus-4-6":   (5.0, 25.0),
    "claude-opus-4-5":   (5.0, 25.0),
    "claude-sonnet-5":   (3.0, 15.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-haiku-4-5":  (1.0, 5.0),
}
# fast mode is the same model at premium rates — Opus 5 / 4.8 only.
FAST_PRICES = {"claude-opus-5": (10.0, 50.0), "claude-opus-4-8": (10.0, 50.0)}
# Sonnet 5 shipped at intro pricing through 2026-08-31.
INTRO = {"claude-sonnet-5": ((2.0, 10.0), "2026-08-31")}
CACHE_WRITE_5M, CACHE_WRITE_1H, CACHE_READ = 1.25, 2.0, 0.10


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
    pin, pout = rate[0] / 1e6, rate[1] / 1e6
    usd = (inp * pin + out * pout + read * pin * CACHE_READ
           + w5m * pin * CACHE_WRITE_5M + w1h * pin * CACHE_WRITE_1H)
    return usd, tokens


def _msg_key(d, msg):
    """Claude Code writes one transcript line per content BLOCK of the same API
    message, repeating the identical usage object 2-3x. Summing lines inflates
    spend ~2.7x on a real session. Dedupe on the API message id."""
    return msg.get("id") or d.get("requestId") or d.get("uuid")


def collect_cost(days=30, roots=None):
    """Walk the transcripts once. Returns a report dict. Numerator = deduped
    assistant token spend (sub-agent runs included — that is real money).
    Denominator = is_human_turn, the gate `ask` already uses."""
    roots = roots or ROOTS
    cutoff = cut_iso = None
    if days:
        cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
        cut_iso = datetime.fromtimestamp(cutoff, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    rep = {"days": days, "usd": 0.0, "decisions": 0, "raw_user_turns": 0, "agent_messages": 0,
           "unpriced_messages": 0, "unpriced_tokens": 0, "sessions": set(),
           "by_model": {}, "by_repo": {}, "tokens": {}, "first_ts": "", "last_ts": ""}
    seen = set()
    for root in roots:
        for f in sorted(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True)):
            # append-only files: an mtime before the window means every record is older
            if cutoff and os.path.getmtime(f) < cutoff:
                continue
            for line in open(f, errors="replace"):
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
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
                if key in seen:
                    continue
                seen.add(key)
                model = normalise_model(msg.get("model"))
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
# coach — rank YOUR OWN prompt habits by whether the work survived
# ============================================================================
# Ported from hack-fleet-ata/fleet/coach.py + contract/deterministic.py so it
# runs here with no imports beyond the stdlib. Same gate (is_human_turn), same
# survival proxy, same deterministic pattern tags. Offline. Nothing leaves the
# machine.
#
# SURVIVAL IS A PROXY, NOT TRUTH. An episode "survived" iff a Write/Edit landed
# or a git commit ran after the prompt and nothing reverted it inside the SAME
# transcript. That is a durable KEYSTROKE, not a durable OUTCOME:
#   - a commit is not proof the code was correct, merged, or kept;
#   - cross-session reverts are invisible to us;
#   - a prompt whose payoff was a decision rather than an edit reads as dead.
# This caveat travels with every number the command prints. It is a coaching
# signal, not a verdict.

_ABANDON_MARKERS = ("never mind", "forget it", "abandon", "scrap this", "drop it")
_CORRECTIVE_MARKERS = ("no,", "no ", "no.", "not that", "not this", "not the",
                       "i meant", "i mean", "actually", "wait,", "wrong ",
                       "other file", "other one")
_WRITE_TOOLS = {"Write", "Edit", "NotebookEdit", "MultiEdit"}
_COMMIT_RE = re.compile(r"\bgit\s+commit\b")
_REVERT_RE = re.compile(r"\bgit\s+(revert|reset\s+--hard)\b")
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

MIN_PATTERN_N = 8   # a habit is only rankable once you have this many episodes
MAX_CI_WIDTH = 0.30  # and its 95% interval must be narrower than this to be advice
MIN_EPISODES_TO_RANK = 30   # below this, refuse to rank the corpus at all — a
                            # rate over a handful of episodes is the exact thing
                            # this tool exists to distrust. Raised from 3 after a
                            # 9-transcript run printed a ranked table over n=3 buckets.
_DURABLE = ("commit", "artifact")
_PROBE = {"commit": "COMMIT-WITNESSED", "artifact": "ARTIFACT-WITNESSED",
          "reverted": "COMMIT-THEN-REVERTED", "none": "NO-DURABLE-RECORD"}


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


def _same_task(a, b):
    """Offline SAME/DIFFERENT floor. No network, no synonym table, no key.

    No placeable object in either prompt -> not the same (we refuse to guess).
    Disjoint objects -> different. Overlapping objects but incompatible intent
    families (change vs describe vs revert vs test) -> different.
    """
    oa, ob = _objects(a), _objects(b)
    if not oa or not ob:
        return False
    hit = bool(oa & ob)
    if not hit:
        for x in oa:
            if len(x) < 5:
                continue
            for y in ob:
                if len(y) >= 5 and x[:4] == y[:4]:
                    hit = True
                    break
            if hit:
                break
    if not hit:
        return False
    return (_intent(a) or "CHANGE") == (_intent(b) or "CHANGE")


def _looks_corrective(text):
    low = " " + text.lower().strip()
    return any(low.startswith(" " + m) or (" " + m) in low for m in _CORRECTIVE_MARKERS)


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


def count_corrections(rows, pasted=None, version=None):
    """(typed_turns, corrections) over one transcript, walked in order so each
    typed turn is classified against the agent turn it answers. Same gate and
    same paste subtraction as the episode grader, so the denominator returned
    here IS the `typed by you` count coach prints."""
    pasted = pasted or set()
    typed = corrections = 0
    agent = []                       # assistant records since the last typed turn
    for row in rows:
        t = _human_prompt(row)
        if t:
            if t in pasted:
                continue             # an echo of agent output, not a turn of yours
            typed += 1
            prev = ""
            if agent and len(t.split()) < _CORRECTION_SHORT:
                prev = "\n".join(extract(r)[1] for r in agent)
            if is_correction(t, prev, version=version):
                corrections += 1
            agent = []
        elif row.get("type") == "assistant":
            agent.append(row)
    return typed, corrections


def _human_prompt(d):
    """The text of a genuine human turn, or '' — reuses the measured gate."""
    if not is_human_turn(d):
        return ""
    msg = d.get("message") or {}
    c = msg.get("content")
    if isinstance(c, str):
        return c.strip()
    if isinstance(c, list):
        return "\n".join(b.get("text", "") for b in c
                         if isinstance(b, dict) and b.get("type") == "text").strip()
    return ""


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
# harness connectors — Claude Code is the native shape; Codex is a SECOND source
# ============================================================================
# Codex writes rollout transcripts with a different record shape than Claude
# Code, so we NORMALISE each rollout into the same Claude-shaped rows the coach
# already understands (is_human_turn / _human_prompt / _tool_uses). One parser,
# no forked coach — which is also why test_coach.sh stays green by construction.
#
# The Codex human gate (measured, see the C1 probe over 77 real rollouts): the
# reliable, universal signal is a `response_item` `message` with role `user`,
# MINUS the context blocks Codex threads in wearing the user's role — AGENTS.md,
# environment_context, permissions, user_instructions, image attachments, the
# goal context, and file-mention headers. The cleaner `user_message` EVENT is
# absent from 9 of 77 rollouts (older CLI builds), so the filtered role:user
# item is the one gate that holds across every build.

_CODEX_INJECTED_WRAPPERS = (
    "<environment_context>", "AGENTS.md instructions", "<INSTRUCTIONS>",
    "permissions instructions", "<user_instructions>", "<collaboration_mode>",
    # the auto-continuation Codex injects between turns wearing the user's role
    "The following is the Codex agent history",
)
_CODEX_INJECTED_BLOCK_PREFIXES = (
    "<image ", "</image>", "<codex_internal_context",
    "# Files mentioned by the user:",
)
# apply_patch envelope: `*** Add File: <path>` / `*** Update File: <path>`.
_CODEX_ADDFILE_RE = re.compile(r"\*\*\* (?:Add|Update) File: ([^\n\\\"]+)")


def _iter_json(path):
    """Yield each parseable JSON record from a .jsonl file. Skips blank/bad lines."""
    try:
        f = open(path, "r", errors="replace")
    except OSError:
        return
    with f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def _codex_user_text(content):
    """The genuinely-typed text of a Codex role:user item, or '' if it is one of
    the injected context blocks Codex sends as a user turn."""
    parts = []
    if isinstance(content, str):
        parts.append(content)
    elif isinstance(content, list):
        for b in content:
            if not isinstance(b, dict) or b.get("type") not in ("input_text", "text"):
                continue
            t = b.get("text", "")
            if any(t.lstrip().startswith(p) for p in _CODEX_INJECTED_BLOCK_PREFIXES):
                continue
            parts.append(t)
    txt = "\n".join(parts).strip()
    if not txt or any(w in txt for w in _CODEX_INJECTED_WRAPPERS):
        return ""
    return txt


def _codex_out_text(content):
    """Assistant output text of a Codex role:assistant item."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content
                         if isinstance(b, dict)
                         and b.get("type") in ("output_text", "text")).strip()
    return ""


def _codex_tool_block(payload):
    """Map one Codex tool call to a synthetic Claude tool_use block, so the same
    survival proxy applies: an apply_patch -> Edit (artifact), a `git commit` ->
    a commit, a `git reset --hard`/revert -> a revert, anything else -> read-only
    Bash. We regex the raw serialised call rather than parse the embedded JS."""
    blob = json.dumps(payload)
    m = _CODEX_ADDFILE_RE.search(blob)
    if m:
        return {"type": "tool_use", "name": "Edit",
                "input": {"file_path": m.group(1).strip()}}
    if _COMMIT_RE.search(blob):
        return {"type": "tool_use", "name": "Bash", "input": {"command": "git commit"}}
    if _REVERT_RE.search(blob):
        return {"type": "tool_use", "name": "Bash",
                "input": {"command": "git reset --hard"}}
    return {"type": "tool_use", "name": "Bash", "input": {"command": "exec"}}


_CODEX_TOOL_TYPES = ("function_call", "custom_tool_call", "local_shell_call")


def _codex_rows(path):
    """Normalise one Codex rollout .jsonl into ordered Claude-shaped rows that
    extract_episodes / _human_prompt / _tool_uses consume unchanged."""
    rows, sid, cwd = [], "", ""
    for d in _iter_json(path):
        p = d.get("payload") or {}
        if d.get("type") == "session_meta":
            sid, cwd = p.get("id") or sid, p.get("cwd") or cwd
            continue
        if d.get("type") != "response_item":
            continue
        # the envelope export-run reads; coach ignores it
        meta = {"timestamp": d.get("timestamp") or "", "cwd": cwd, "sessionId": sid}
        pt = p.get("type")
        if pt == "message":
            role = p.get("role")
            if role == "user":
                txt = _codex_user_text(p.get("content"))
                if txt:
                    rows.append(dict(meta, type="user", promptSource="typed",
                                     message={"role": "user", "content": txt}))
            elif role == "assistant":
                txt = _codex_out_text(p.get("content"))
                rows.append(dict(meta, type="assistant", message={
                    "role": "assistant",
                    "content": [{"type": "text", "text": txt}] if txt else []}))
        elif pt in _CODEX_TOOL_TYPES:
            rows.append(dict(meta, type="assistant", message={
                "role": "assistant", "content": [_codex_tool_block(p)]}))
    return rows


# --- Cursor CLI ------------------------------------------------------------
# Cursor writes ~/.cursor/projects/<slug>/agent-transcripts/<uuid>/<uuid>.jsonl
# with the SAME {role, message:{content:[...]}} shape Claude Code uses, so
# extract() already reads it. Three things are missing and this connector adds
# them: there is no timestamp field (it is embedded in the user text), no cwd
# field (it is the directory slug), and the human turn is wrapped in
# <user_query> tags that would otherwise be graded as part of the prompt.

_CUR_TS = re.compile(r"<timestamp>(.*?)</timestamp>", re.S)
_CUR_Q = re.compile(r"<user_query>\s*(.*?)\s*</user_query>", re.S)


def _cursor_ts(text):
    """'Thursday, Aug 13, 2026, 5:53 PM (UTC+2)' -> ISO-ish, or ''. Never guesses
    a date it cannot parse: an unparsed stamp yields '' rather than today."""
    m = _CUR_TS.search(text or "")
    if not m:
        return ""
    raw = m.group(1).strip()
    for fmt in ("%A, %b %d, %Y, %I:%M %p", "%A, %B %d, %Y, %I:%M %p"):
        try:
            import datetime
            return datetime.datetime.strptime(raw.split(" (")[0], fmt).isoformat()
        except Exception:
            pass
    return ""


def _cursor_cwd(path):
    """~/.cursor/projects/Users-dev-CODE-proj/... -> /Users/dev/CODE/proj.
    The slug is lossy (a real hyphen in a directory name is indistinguishable
    from the separator), so the result is checked on disk and dropped if it is
    not a real directory. A wrong cwd is worse than no cwd."""
    parts = os.path.normpath(path).split(os.sep)
    try:
        slug = parts[parts.index("projects") + 1]
    except (ValueError, IndexError):
        return ""
    cand = "/" + slug.replace("-", "/")
    if os.path.isdir(cand):
        return cand
    # try collapsing trailing segments back into hyphenated names
    segs = slug.split("-")
    for join_from in range(len(segs) - 1, 0, -1):
        cand = "/" + "/".join(segs[:join_from] + ["-".join(segs[join_from:])])
        if os.path.isdir(cand):
            return cand
    return ""


def _cursor_rows(path):
    """Normalise Cursor records onto the Claude shape the indexer already reads.

    AUTHORSHIP, stated because it is a DIFFERENT gate with different provenance.
    Claude Code stamps `promptSource: typed`, which is the measured-reliable signal
    (~95% of raw `type: user` records are not the operator). Cursor has no such
    field. Its one honest equivalent is the `<user_query>` wrapper: Cursor puts it
    around a prompt the operator submitted, and injected/tool-result user records
    do not carry it. So a Cursor record counts as typed IFF it carried that
    wrapper. This is a weaker signal than Claude's and it is labelled as such
    rather than silently pooled with it.
    """
    cwd = _cursor_cwd(path)
    sid = os.path.splitext(os.path.basename(path))[0]
    last_ts = ""
    out = []
    for d in _iter_json(path):
        if not isinstance(d, dict) or "message" not in d:
            continue
        msg = d.get("message") or {}
        c = msg.get("content")
        wrapped = False
        if isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and b.get("type") == "text":
                    t = b.get("text") or ""
                    ts = _cursor_ts(t)
                    if ts:
                        last_ts = ts
                    q = _CUR_Q.search(t)
                    if q:
                        b["text"] = q.group(1)
                        wrapped = True
                    elif _CUR_TS.search(t):
                        b["text"] = _CUR_TS.sub("", t).strip()
        role = d.get("role") or msg.get("role")
        d["type"] = "user" if role == "user" else "assistant"
        if role == "user" and wrapped:
            d["promptSource"] = "typed"
        d["timestamp"] = last_ts
        d["cwd"] = cwd
        d["sessionId"] = sid
        out.append(d)
    return out


def _sniff(path):
    """'codex' (rollout), 'codex-history' (history.jsonl), or 'claude', from the
    first parseable record. Lets `--root ~/.codex` and mixed dirs just work."""
    for d in _iter_json(path):
        if d.get("type") == "session_meta" or ("payload" in d and "timestamp" in d):
            return "codex"
        if set(d.keys()) == {"session_id", "ts", "text"}:
            return "codex-history"
        # Cursor: role + message only, and none of Claude's envelope fields.
        if set(d.keys()) <= {"role", "message"} and "message" in d:
            return "cursor"
        return "claude"
    return "claude"


def _rows_for_file(path):
    """(rows, harness) for one transcript file, auto-detected. history.jsonl is a
    witness (a typed-input log), not an episode source, so it yields no rows."""
    h = _sniff(path)
    if h == "codex":
        return _codex_rows(path), "codex"
    if h == "codex-history":
        return [], "codex-history"
    if h == "cursor":
        return _cursor_rows(path), "cursor"
    return list(_iter_json(path)), "claude"


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
        if harness == "cursor" or base == ".cursor":
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
    """Ordered [(kind, text)] with kind in {'human','agent'} for one transcript.
    'agent' pools everything the operator could have copied FROM: assistant
    messages, tool commands, and tool results, all EARLIER in the session."""
    items = []
    if harness == "codex":
        for d in _iter_json(path):
            if d.get("type") != "response_item":
                continue
            p = d.get("payload") or {}
            pt = p.get("type")
            if pt == "message":
                role = p.get("role")
                if role == "user":
                    t = _codex_user_text(p.get("content"))
                    if t:
                        items.append(("human", t))
                elif role == "assistant":
                    t = _codex_out_text(p.get("content"))
                    if t:
                        items.append(("agent", t))
            elif pt in _CODEX_TOOL_TYPES:
                items.append(("agent", json.dumps(p)))
            elif pt in ("function_call_output", "custom_tool_call_output"):
                o = p.get("output")
                t = o if isinstance(o, str) else json.dumps(o)
                if t:
                    items.append(("agent", t[:4000]))
    else:
        for d in _iter_json(path):
            if is_human_turn(d):
                t = _human_prompt(d)
                if t:
                    items.append(("human", t))
            elif d.get("type") == "assistant":
                _, t, _ = extract(d)
                if t:
                    items.append(("agent", t))
            elif d.get("type") == "user" and d.get("toolUseResult") is not None:
                _, t, _ = extract(d)
                if t:
                    items.append(("agent", t))
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
    """Split one transcript into episodes: one human intent, opened and closed.
    A `pasted` set (opener texts flagged by detect_pastes) is treated as non-human
    so echoed agent output never counts as one of the operator's own prompts."""
    pasted = pasted or set()
    eps, n, i = [], len(rows), 0
    while i < n:
        opener = _human_prompt(rows[i])
        if not opener or opener in pasted:
            i += 1
            continue
        start, corrective, assistants = i, 0, 0
        wrote = committed = reverted = read_only = False
        witness, j = "", i + 1
        while j < n:
            row = rows[j]
            nxt = _human_prompt(row)
            if nxt and nxt in pasted:
                nxt = ""              # a pasted turn is agent output, not a new intent
            if nxt:
                low = nxt.lower()
                if any(m in low for m in _ABANDON_MARKERS):
                    break
                if _looks_corrective(nxt) or _same_task(opener, nxt):
                    corrective += 1
                    j += 1
                    continue
                break                      # a genuinely new intent ends the episode
            if row.get("type") == "assistant":
                assistants += 1
            for b in _tool_uses(row):
                name = b.get("name")
                if name in _WRITE_TOOLS:
                    wrote = True
                    if not witness:
                        inp = _tool_input(b)
                        tgt = inp.get("file_path") or inp.get("notebook_path") or "?"
                        witness = "%s %s" % (name, os.path.basename(tgt))
                elif name == "Bash":
                    cmd = _tool_input(b).get("command", "") or ""
                    if _COMMIT_RE.search(cmd):
                        committed, witness = True, "git commit"
                    elif _REVERT_RE.search(cmd):
                        reverted = True
                    else:
                        read_only = True
            j += 1

        if committed and reverted:
            tier = "reverted"
        elif committed:
            tier = "commit"
        elif wrote:
            tier = "artifact"
        else:
            tier = "none"
            witness = ("read-only Bash only, no file change" if read_only
                       else "no tool ran after the prompt")

        eps.append({"opener": opener, "source": os.path.basename(source),
                    "tier": tier, "probe": _PROBE[tier],
                    "score": 2 if tier == "commit" else (1 if tier == "artifact" else 0),
                    "survived": tier in _DURABLE, "corrective_turns": corrective,
                    "assistant_turns": assistants, "witness": witness})
        i = j if j > start else start + 1
    return eps


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
    """Rank habits by survival, and refuse to rank one we cannot tell from average.

    MIN_PATTERN_N alone is not enough. On a real corpus (2026-09-04, 2244 episodes)
    a band of n=40 at 55% sat fifth in "do more of these" beside a band of n=815,
    and its 95% interval was [39.8, 69.3] — it straddled the 47% corpus baseline and
    overlapped the WORST band. The tool told its user to write vaguer prompts.

    So a habit is ranked only when its interval EXCLUDES the corpus baseline, i.e.
    when we can actually say it differs from average. Everything else is still
    measured and still printed, just not under a heading that says "do more of these".
    A denominator too small to rank does not get ranked.
    """
    buckets = {}
    for ep in episodes:
        for tag in prompt_patterns(ep["opener"]):
            buckets.setdefault(tag, []).append(ep)
    if baseline is None:
        baseline = (sum(1 for e in episodes if e["survived"]) / len(episodes)
                    if episodes else 0.0)
    out = []
    for tag, eps in buckets.items():
        n = len(eps)
        durable = sum(1 for e in eps if e["survived"])
        lo, hi = _wilson(durable, n)
        out.append({"pattern": tag, "n": n, "survived": durable,
                    "survival_rate": durable / n if n else 0.0,
                    "ci_lo": lo, "ci_hi": hi,
                    # Two conditions, both necessary. (1) the interval must EXCLUDE
                    # the corpus baseline, or we cannot say the habit differs from
                    # average. (2) the interval must be narrower than MAX_CI_WIDTH,
                    # because an estimate of "somewhere between 49% and 94%" is not
                    # advice at any position in a list. n>=8 alone allowed both a
                    # baseline-straddling band and a 45pp-wide one to be printed
                    # under "do more of these".
                    "distinguishable": (n >= MIN_PATTERN_N
                                        and not (lo <= baseline <= hi)
                                        and (hi - lo) <= MAX_CI_WIDTH),
                    "rankable": n >= MIN_PATTERN_N})
    out.sort(key=lambda p: (p["survival_rate"], p["n"]), reverse=True)
    return out


def _pick(episodes, survived, key):
    cand = [e for e in episodes if e["survived"] is survived and len(e["opener"]) >= 25]
    if not cand:
        cand = [e for e in episodes if e["survived"] is survived]
    return max(cand, key=key) if cand else None


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
    return list(ROOTS)


def coach(roots=None, harness=None, verified_human=False):
    """Rank the operator's own prompt habits by the survival proxy. Offline.

    harness: None (auto-detect per file), 'claude', or 'codex'. A Codex root is
    normalised into the same rows, so the survival proxy is identical.
    verified_human: subtract likely-PASTED turns (echoes of earlier agent/tool
    output in the same session) from the human signal before grading."""
    if not roots:
        roots = _coach_roots(None, harness)
    paths = _coach_files(roots, harness)
    episodes, records, humans, pastes, corrections = [], 0, 0, 0, 0
    human_texts, harnesses = [], set()
    for p in paths:
        rows, fh = _rows_for_file(p)
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
        episodes += extract_episodes(rows, source=p, pasted=pasted)

    _coach_baseline = (sum(1 for e in episodes if e["survived"]) / len(episodes)
                       if episodes else 0.0)
    patterns = rank_patterns(episodes, baseline=_coach_baseline)
    rankable = [p for p in patterns if p["distinguishable"]]
    # Measured, but the interval straddles the corpus baseline, so we cannot say it
    # differs from average. Printed under its own heading, never as advice.
    indistinct = [p for p in patterns if p["rankable"] and not p["distinguishable"]]
    durable = sum(1 for e in episodes if e["survived"])
    tiers = {t: sum(1 for e in episodes if e["tier"] == t)
             for t in ("commit", "artifact", "reverted", "none")}
    resolved = (harness or ("codex" if harnesses == {"codex"}
                            else "claude" if harnesses == {"claude"}
                            else "mixed" if harnesses else "claude"))
    hist_lines, hist_matched = (_codex_history_overlap(roots, human_texts)
                                if "codex" in harnesses or harness == "codex"
                                else (0, 0))
    return {
        "harness": resolved,
        "verified_human": verified_human, "pastes_flagged": pastes,
        "history_lines": hist_lines, "history_matched": hist_matched,
        "files": len(paths), "total_records": records, "human_turns": humans,
        "human_pct": round(100 * humans / records, 2) if records else 0.0,
        # correction rate = typed turns that correct the agent / typed turns.
        # See is_correction() for the two rules; it is a lexical floor.
        "corrections": corrections,
        "correction_rate": round(corrections / humans, 3) if humans else 0.0,
        "episodes": len(episodes), "durable": durable,
        "durable_rate": round(durable / len(episodes), 3) if episodes else 0.0,
        "tiers": tiers,
        "top_patterns": [p for p in rankable
                         if p["survival_rate"] > _coach_baseline][:5],
        # The share block needs named habits by name, and a habit can land in either
        # half of the most/least split depending on corpus. Give it the whole list
        # rather than making it guess which slice to look in.
        "all_patterns": rankable,
        # SURVIVES LEAST must draw only from habits SURVIVES MOST did not take.
        # The old guard was `len(rankable) > 5`, which only protected the <=5 case:
        # with 6-9 rankable habits, rankable[:5] and rankable[-5:] overlap, and the
        # tool printed the SAME row under "do more of these" and "these tend to
        # loop" with the same denominator. A first-time user has 6-9 habits, so the
        # first outside run was the one that saw it. Slicing from index 5 makes the
        # two lists disjoint by construction at every corpus size, and is
        # byte-identical to the old output once there are >=10 rankable habits.
        # Direction, not list position. A band is "survives least" because it sits
        # BELOW the corpus baseline, never because it fell outside the first five
        # slots. Position slicing put a 42% band under "do more of these" the moment
        # the baseline filter shortened the list.
        "bottom_patterns": [p for p in rankable
                            if p["survival_rate"] <= _coach_baseline][-5:][::-1],
        "best_prompt": _pick(episodes, True,
                             lambda e: (e["score"], -e["corrective_turns"],
                                        e["assistant_turns"])),
        "worst_prompt": _pick(episodes, False,
                              lambda e: (e["corrective_turns"], e["assistant_turns"])),
        "indistinct_patterns": indistinct,
        "sparse": len(rankable) < 5,
        "rankable_corpus": len(episodes) >= MIN_EPISODES_TO_RANK,
        "proxy": ("survival = a durable Write/Edit or an un-reverted git commit "
                  "in-episode. A PROXY, not proof the work was correct or shipped."),
    }



def _share_block(r):
    """Four lines a person can paste into a thread.

    The tool asks people to compare their numbers with someone else's; before this
    existed, answering that meant hand-retyping rows out of two tables, which is
    why those threads fill with opinions instead of data. Numbers only: no prompt
    text, no paths, no repo names, so pasting it cannot leak anything.
    """
    pats = {p["pattern"]: p for p in r.get("all_patterns") or []}
    good = pats.get("states-a-check-or-done-condition")
    bad = pats.get("intent:none")
    if not (good and bad):                       # fall back to the extremes we do have
        top = (r.get("top_patterns") or [None])[0]
        bot = (r.get("bottom_patterns") or [None])[0]
        good, bad = good or top, bad or bot
    if not (good and bad) or good is bad:
        return                                   # nothing honest to compare
    W = 57
    print("  " + "\u2500" * W)
    print("   compare yours. numbers only, nothing from your prompts:\n")
    print("   transcripto coach \u00b7 %s \u00b7 %s episodes \u00b7 %d%% survived"
          % (r["harness"], r["episodes"], int(round(r["durable_rate"] * 100))))
    for label, p in ((good["pattern"], good), (bad["pattern"], bad)):
        print("   %-34s %3d%%  (%s/%s)"
              % (label, round(p["survival_rate"] * 100), p["survived"], p["n"]))
    if bad["survival_rate"]:
        print("   %-34s  %.1fx" % ("gap", good["survival_rate"] / bad["survival_rate"]))
    print("  " + "\u2500" * W)


def _one_line(text, width=100):
    one = " ".join(text.split())
    return one if len(one) <= width else one[:width - 1] + "…"


def cmd_coach(args):
    r = coach([args.root] if args.root else None, harness=args.harness,
              verified_human=args.verified_human)
    if args.json:
        print(json.dumps(r, indent=2)); return
    if not r["episodes"]:
        # A stranger's first run lands here whenever they have no logs for this
        # harness. Name where we looked, so "it printed nothing" is diagnosable.
        looked = _coach_roots(args.root, args.harness)
        print("\n  no prompt episodes found for harness '%s'.\n" % r["harness"])
        print("  looked in: %s" % (", ".join(looked) or "(no default root)"))
        print("\n  this reads transcripts that already exist on your machine; it does not")
        print("  create them. if that directory is empty, use the agent for a session first.\n")
        print("  otherwise:")
        # All three supported harnesses are offered here. Listing only two while the
        # README sells three is how a stranger concludes cursor is unsupported.
        print("    %s coach --harness codex       grade Codex (~/.codex) instead" % PROG)
        print("    %s coach --harness cursor      grade Cursor "
              "(~/.cursor/projects/*/agent-transcripts)" % PROG)
        print("    %s coach --root <dir>          point at a folder of .jsonl transcripts\n" % PROG)
        return
    B, D = "\033[1m", "\033[0m"
    # The share you typed is the argument the whole tool rests on, and it used to
    # sit in grey at the bottom under the fold. It is the first thing now.
    print("\n  %s%s of the %s records in your transcripts are things you typed.  %.2f%%%s"
          % (B, f"{r['human_turns']:,}", f"{r['total_records']:,}",
             r["human_pct"], D))
    print("  \033[2mthe rest is the machine answering you. this grades the %s.\033[0m"
          % f"{r['human_turns']:,}")
    print("\n  %sYOUR PROMPT HABITS, GRADED%s   (offline, your machine only)\n" % (B, D))
    w = r["worst_prompt"]
    if w:
        print("  \033[31m-\033[0m your worst looped prompt, with its witness:")
        print("      \"%s\"" % _one_line(w["opener"]))
        print("      %s: %s  ·  corrections: %s  ·  assistant turns: %s"
              % (w["probe"], w["witness"], w["corrective_turns"], w["assistant_turns"]))
    b = r["best_prompt"]
    if b:
        print("\n  \033[32m+\033[0m your best landed prompt, with its witness:")
        print("      \"%s\"" % _one_line(b["opener"]))
        print("      %s: %s  ·  corrections: %s" % (b["probe"], b["witness"],
                                                    b["corrective_turns"]))
    print("\n  \033[2mSURVIVAL IS A PROXY: %s\033[0m" % r["proxy"])
    if not r["rankable_corpus"]:
        # The refusal IS the product's argument, not an error. A rate needs a
        # denominator large enough to mean something; %d episodes is not it, and a
        # tool that prints "65%%" over three episodes is doing the exact thing this
        # one exists to catch. So no ranking. The two things below need no sample
        # size — one episode each — and they are the honest half of the output.
        print("\n  %sNot enough episodes to rank your habits yet.%s" % (B, D))
        print("  You have %s. At %s the tool starts looking, and a habit ranks once its"
              % (r["episodes"], MIN_EPISODES_TO_RANK))
        print("  own count is large enough to separate it from your average, which is a"
              "\n  bigger number than %s. A survival percentage over"
              % MIN_EPISODES_TO_RANK)
        print("  a handful of episodes is the number this tool was built to distrust,")
        print("  so it will not print one. Your raw survival and your single best and")
        print("  worst prompt need no sample size — here they are.")
    else:
        if r["sparse"] and r["top_patterns"]:
            print("\n  \033[2m(few habits cleared the %s-episode minimum, showing what is "
                  "rankable)\033[0m" % MIN_PATTERN_N)
        # An empty header under a promise is a claim about rows that do not exist.
        # The baseline-overlap rule can empty this list entirely on a small corpus,
        # where no single band's interval clears the user's own average. Say that,
        # rather than printing "do more of these" over nothing.
        if not r["top_patterns"]:
            print("\n  %sNo habit beats your own average by enough to call it.%s" % (B, D))
            print("  \033[2mEvery band's 95%% interval straddles your %d%% baseline. That is a"
                  "\n  finding, not a gap: at this corpus size the differences are noise.\033[0m"
                  % round(r["durable_rate"] * 100))
        else:
            print("\n  %sSURVIVES MOST%s  do more of these:" % (B, D))
        for p in r["top_patterns"]:
            print("    %3d%%  (%s/%s)  %s" % (round(p["survival_rate"] * 100),
                                              p["survived"], p["n"], p["pattern"]))
        # With <=5 rankable habits SURVIVES MOST already showed all of them, so
        # there is no honest "least" left to print. An empty header under a
        # promise ("these tend to loop") is a claim about rows that do not exist.
        if r["bottom_patterns"]:
            print("\n  %sSURVIVES LEAST%s  these tend to loop:" % (B, D))
            for p in r["bottom_patterns"]:
                print("    %3d%%  (%s/%s)  %s" % (round(p["survival_rate"] * 100),
                                                  p["survived"], p["n"], p["pattern"]))
        elif r["top_patterns"]:
            print("\n  \033[2m(every rankable habit is listed above; too few to split "
                  "into a most/least pair)\033[0m")
        # Measured, but the 95% interval straddles your own survival rate, so the
        # honest statement is "cannot tell this apart from your average", not a
        # ranking. These used to appear under "do more of these".
        if r.get("indistinct_patterns"):
            print("\n  \033[2mMEASURED, NOT RANKED  the 95%% interval straddles your "
                  "%d%% baseline, so these cannot be told apart from your average:\033[0m"
                  % round(r["durable_rate"] * 100))
            for p in r["indistinct_patterns"]:
                print("    \033[2m%3d%%  (%s/%s)  [%d-%d%%]  %s\033[0m"
                      % (round(p["survival_rate"] * 100), p["survived"], p["n"],
                         round(p["ci_lo"] * 100), round(p["ci_hi"] * 100), p["pattern"]))
    print("\n  \033[2mharness %s  ·  %s transcript(s), %s records  ·  %s typed by you "
          "(%s%%)\033[0m"
          % (r["harness"], r["files"], format(r["total_records"], ","),
             r["human_turns"], r["human_pct"]))
    # Keep the phrasing "episodes: N ranked, M survived (P%)" verbatim. test_small_n.sh
    # greps for it to prove the raw survival count still shows when habit ranking is
    # refused, which is the honest half of a small-corpus run. Reword it and that check
    # goes green-by-absence for a reason unrelated to what it is testing.
    print("  \033[2mepisodes: %s ranked, %s survived (%s%%)\033[0m"
          % (r["episodes"], r["durable"], int(round(r["durable_rate"] * 100))))
    t = r["tiers"]
    print("  \033[2mcommit %s  ·  write/edit %s  ·  reverted %s  ·  nothing durable %s\033[0m"
          % (t["commit"], t["artifact"], t["reverted"], t["none"]))
    # correction rate: the inverse of a landed prompt. n travels with it because
    # a percentage without its denominator is the number this tool distrusts.
    #
    # It used to say "a floor" and stop. That was true and useless — it named a
    # direction without a size, so nobody could tell whether the real figure was
    # 7% or 40%. Both were measured on 2026-09-03 (200 rows each, agent-labelled,
    # one tuning sample and one held-out): v1 runs at precision 0.80 and recall
    # 0.16, so the printed count is roughly a FIFTH of the real one, and the two
    # samples put the true rate between 26% and 37%.
    #
    # The interval is printed rather than a point estimate because the two
    # samples disagree by more than sampling error, and hiding that behind one
    # confident number is the failure this tool exists to catch.
    # Each version states ITS OWN measured recall. Printing one figure for both
    # would attach v1's recall to v0's count — a true number about the wrong
    # object, which is the exact error this tool was built to surface.
    caught = {"v0": "~1 in 18", "v1": "~1 in 6"}.get(_CORRECTION_VERSION, "?")
    print("  \033[2mcorrection rate: %s%% measured (%s of %s typed turns) · "
          "%s catches %s, so the real rate is ~26-37%%\033[0m"
          % (int(round(r["correction_rate"] * 100)), r["corrections"],
             r["human_turns"], _CORRECTION_VERSION, caught))
    if r["verified_human"]:
        print("  \033[2m%s typed turn(s) flagged likely-PASTED and subtracted\033[0m"
              % r["pastes_flagged"])
    if r["history_lines"]:
        print("  \033[2mcodex history.jsonl: %s/%s checkable input lines also appear as "
              "typed rollout turns (gate control)\033[0m"
              % (r["history_matched"], r["history_lines"]))
    print()
    _share_block(r)
    print()


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
    if not ts:
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
        return max(paths, key=os.path.getmtime)
    hits = [p for p in paths if os.path.basename(p).startswith(target)]
    if not hits:                     # codex names rollouts rollout-<date>-<id>.jsonl
        hits = [p for p in paths if target in os.path.basename(p)]
    return max(hits, key=os.path.getmtime) if hits else None


def export_run(path):
    """The run-level numbers of one transcript file, as a JSON-ready dict."""
    rows, harness = _rows_for_file(path)
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
                fp = _tool_input(b).get("file_path") or _tool_input(b).get("notebook_path")
                if fp:
                    files.add(fp)
    commits = _reflog_commits(cwd, start, end) if cwd else None
    return {
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
                  "sidechain or tool output); correction_rate is a lexical floor; "
                  "commits_in_window is this tree's reflog inside the run window, "
                  "null when the project is not a git repo."),
    }


def cmd_export_run(args):
    roots = _coach_roots(args.root, args.harness)
    path = _resolve_run(args.target, roots, args.harness)
    if not path:
        sys.stderr.write("\n  no transcript matches '%s'.\n" % args.target)
        sys.stderr.write("  looked in: %s\n" % ", ".join(roots))
        sys.stderr.write("  pass a session id (or a prefix of one), 'latest', or a path "
                         "to a .jsonl; --root / --harness as for coach.\n\n")
        sys.exit(2)
    print(json.dumps(export_run(path), indent=2))


def main():
    p = argparse.ArgumentParser(prog=PROG, description=__doc__ + USAGE,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version="%s %s" % (PROG, VERSION))
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("index").set_defaults(fn=cmd_index)
    s = sub.add_parser("watch"); s.add_argument("--interval", type=int, default=5); s.set_defaults(fn=cmd_watch)
    s = sub.add_parser("ask"); s.add_argument("query"); s.add_argument("-n", "--limit", type=int, default=25); s.set_defaults(fn=cmd_ask)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("-n", "--limit", type=int, default=25); s.set_defaults(fn=cmd_search)
    s = sub.add_parser("find"); s.add_argument("name"); s.set_defaults(fn=cmd_find)
    s = sub.add_parser("trace"); s.add_argument("query"); s.add_argument("-n", "--limit", type=int, default=10)
    s.add_argument("-a", "--all", action="store_true", help="show every file, not the first 8")
    s.set_defaults(fn=cmd_trace)
    s = sub.add_parser("sessions"); s.add_argument("-n", "--limit", type=int, default=30)
    s.add_argument("--all", action="store_true",
                   help="include sessions you never typed in (85%% of them, on a real corpus)")
    s.set_defaults(fn=cmd_sessions)
    sub.add_parser("stats").set_defaults(fn=cmd_stats)
    s = sub.add_parser("cost")
    s.add_argument("--days", type=int, default=30, help="window in days (0 = all time)")
    s.add_argument("--root", help="scan this transcript dir instead of ~/.claude/projects")
    s.add_argument("--json", action="store_true", help="machine-readable, for other tools")
    s.set_defaults(fn=cmd_cost)
    s = sub.add_parser("coach")
    s.add_argument("--root", help="grade this transcript dir instead of ~/.claude/projects")
    s.add_argument("--harness", choices=["claude", "codex", "cursor"],
                   help="which agent's transcripts to grade. codex reads "
                        "~/.codex (archived_sessions + sessions); cursor reads "
                        "~/.cursor/projects/*/agent-transcripts. default: auto-detect")
    s.add_argument("--verified-human", dest="verified_human", action="store_true",
                   help="subtract likely-PASTED turns: a typed turn whose text is a "
                        "verbatim/high n-gram echo of an earlier agent or tool message "
                        "in the same session, from the human signal before grading")
    s.add_argument("--json", action="store_true", help="machine-readable, for other tools")
    s.set_defaults(fn=cmd_coach)
    s = sub.add_parser("export-run")
    s.add_argument("target", help="a session id (or a prefix of one), 'latest', or a "
                                  "path to a .jsonl transcript")
    s.add_argument("--root", help="look in this transcript dir instead of ~/.claude/projects")
    s.add_argument("--harness", choices=["claude", "codex", "cursor"],
                   help="which agent's transcripts to look in. default: claude")
    s.set_defaults(fn=cmd_export_run)
    a = p.parse_args()
    if not getattr(a, "fn", None):
        p.print_help(); return
    a.fn(a)


if __name__ == "__main__":
    main()
