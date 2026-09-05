# Transcripto

**You might already be keeping a journal. Read your side of it.**

Your agent transcripts contain what you asked for, what you changed your mind
about, and what you kept coming back to. Transcripto helps you find those words
and read the recorded work around them.

Claude Code · Codex · Cursor. Local files. No account. No runtime dependencies.

**Development checkout:** source references, continuation packets and pinned
comparisons on this branch are not in PyPI 0.2.0 yet. To try them, install this
checkout with `python3 -m pip install .`. The pinned release commands below still
run the published version.

## Start with something you remember saying

Run `transcripto ask` without a query to discover local histories first.
It separates missing, empty, unsupported and unreadable sources and shows
which supported files are new or changed since indexing, without building the
index. `transcripto index --status --json` exposes this inventory to local
consumers. Discovery reads bounded file prefixes; unidentified files are
reported, not silently counted as supported. File modification time is not
proof of human activity or completed work.

```sh
uvx --from transcripto==0.2.0 transcripto ask "retry"
```

Replace `retry` with a word you remember using. `ask` searches recorded requests
and shows dated evidence, newest first. It refreshes the local index
automatically. The first search indexes the selected history; a large archive
can take minutes. Add `--harness claude`, `--harness codex`, or `--harness cursor`
to limit that scan. It does not generate a diary or interpret your personality.

Then open the surrounding work:

```sh
uvx --from transcripto==0.2.0 transcripto replay "retry"

# Or open your latest human session:
uvx --from transcripto==0.2.0 transcripto
```

Replay puts your request, tool calls and recorded results in order. Failed edits
stay failed. Missing results stay unknown. Status describes tool execution,
not whether the task was done correctly.

Or install with `python3 -m pip install transcripto==0.2.0`, then run
`transcripto ask "retry"`. Requires Python 3.9 or newer.

**Your files remain yours.** Transcripto does not upload transcript content or
execute commands found in it. Search output, replay and JSON can contain private
words and paths; review anything you choose to share. It reads existing files,
not deleted history. Check your agent's retention settings and keep your own
backup if you want a lasting record. Authorship detection differs by harness;
[see the limits below](#what-each-harness-supports).

## Find the thing you remember

Search automatically refreshes a local index. No setup command is required.

```sh
transcripto ask "retry"                 # your submitted words
transcripto search "retry"              # prompts, replies, and tool text
transcripto find parser.py              # recorded file operations and attempts
transcripto trace "retry"               # an alias into result-aware replay
transcripto sessions                    # sessions with submitted prompts
transcripto stats                       # activity counts
```

A failed or unconfirmed file change is labelled an **attempt**, never `WROTE`.
Queries with `--harness` or `--root` are scoped to that selection even if the
index already contains another corpus. `index` and `watch` remain available for
explicit refresh and background polling.

## Carry a decision into tomorrow

In this checkout, `transcripto ask "why did we choose SQLite?" --json` returns
the original request, source line and hashes. It shows which question words were
ignored; `--literal` keeps them. It returns evidence, not an invented answer.
During a cold index, the first matching request appears in stderr while the full
search continues. Recent files are indexed first; final results still cover the
selected history. Unknown and partially readable sources remain visible.

Use the returned transcript path with `trace --from-line N --to-line M` to read
the request, responses and recorded actions in that range. Then
`export-run <path> --packet --from-line N --to-line M --output <new-local-file>`
saves only that selected evidence. Decisions remain unclassified until you
explicitly mark their request lines as settled or reversed. A read-only answer
is a valid part of the history. `export-run <packet-file> --check` checks whether
the source bytes have changed before you hand the context to another agent.

For a return visit, save `coach --snapshot <new-local-file>` and later use
`coach --compare <that-file>`. The old population stays fixed. New requests,
rewritten requests and changed old results are separate; missing results are
not failures. Counts and uncertainty travel with the comparison, without grades.

Packets and snapshots are local files, created privately and never overwritten.
No upload is performed. See the [consumer contract](READ-CONTRACT.md) for exact
commands, selection rules and machine-readable fields.

## The replay

This is output from `replay --demo`. **All prompts and results in this example
are invented.** The demo goes through the same parser as a real transcript.

```text
THE COMEBACK · claude · request 1
You asked: "Fix the login redirect and run its tests."

   1  FAIL edit       src/login.py
                 Tool error: Error: text not found  [call L2 → result L3]
   2  OK   edit       src/login.py
                 Tool reported success.  [call L4 → result L5]
   3  FAIL check      pytest tests/test_login.py
                 Tool error: Process exited with code 1  [call L6 → result L7]
   4  OK   edit       src/login.py
                 Tool reported success.  [call L8 → result L9]
   5  OK   check      pytest tests/test_login.py
                 Tool reported success.  [call L10 → result L11]

Agent said: "The redirect is fixed and the tests pass."

Recorded: 3 succeeded · 2 failed · 0 unknown
Status describes a tool result, not task correctness. Missing results stay unknown.
```

The headings have rules. **The comeback** means a recorded failure was followed
by success for the same operation and target, without a later failed or unknown
attempt on that target. **The snag** means a failure is
present. **The missing receipt** means a result is unknown. **The answer** means
there were no recorded tool calls; an explanation may have been the whole task.
These are descriptions of the sequence, not grades for you or your agent.

On your own history, each replay names its source file and line numbers, plus a
command that reopens that exact request. Long sequences open around the first
failure or change and tell you what was omitted. `--all` shows the full sequence.

```sh
transcripto                                # latest session you submitted a request in
transcripto replay --failures               # most recent request with a recorded failure
transcripto replay "login redirect"         # find requests containing these words
transcripto replay path/to/session.jsonl    # inspect one transcript
transcripto replay --session 3f9c1a2b        # explicitly select a session prefix
transcripto replay path/to/session.jsonl --episode 3 --all
transcripto replay latest --json            # structured events, evidence, source lines
transcripto replay latest --share           # counts + caveat; no prompts or paths
```

`--share` is intentionally small. Full replay output and JSON contain your own
words and local paths. The tool does not upload either.

## What each harness supports

| Feature | Claude Code | Codex | Cursor |
|---|---|---|---|
| Replay, search, ask, find, trace, sessions, stats | Yes | Yes | Yes |
| Tool attempts | Native tool calls | Direct calls and supported static wrappers | `StrReplace`, `Shell`, `Write`, and other calls |
| Execution status | Matched results | Matched results; ambiguous wrappers stay unknown | Unknown when the export omits results or call IDs |
| Authorship | `promptSource` typed/queued, excluding injected/tool records | User messages with known injected context excluded | `<user_query>` wrapper; a weaker signal |
| Coach, export-run | Yes | Yes | Yes, with missing evidence preserved |
| API-equivalent cost | Yes | Not supported | Not supported |

```sh
transcripto replay --harness claude
transcripto replay --harness codex
transcripto replay --harness cursor
transcripto search "retry" --harness codex
transcripto replay --root /path/to/transcripts
```

Default roots are `~/.claude/projects`, `~/.codex`, and `~/.cursor`.
Codex reads sessions and archived sessions. Cursor reads the per-session files
under `projects/*/agent-transcripts/*/`. Latest-session replay skips subagents
and files without a submitted human request.

Cursor exports often contain calls without results. That is useful evidence
of an attempt, but not enough to claim success. Transcripto does not substitute
an assistant's closing message or a `turn_ended` record for the missing result.

## The evidence contract

1. A tool call is an **attempt**.
2. A matching result may establish **succeeded** or **failed** execution.
3. A missing result, a running command, or an ambiguous result is **unknown**.
4. An exit code of zero is not proof that the requested task is correct.
5. A later human request opens a new episode. Its work is never absorbed into
   the previous request because the words happen to overlap.
6. A command mentioning `git commit` is not necessarily a commit. Quoted text,
   dry runs, and compound shell commands are not promoted to commit evidence.

The tool never executes transcript commands. It parses a limited set of static
Codex wrapper forms; arbitrary JavaScript and multiple nested child calls are
not reconstructed. A long-running call can remain unknown when completion is
only present in a later polling call. Cross-session durability, semantic task
completion, and live repository state are not inferred from transcript text.

## Coach without invented grades

`transcripto coach` shows descriptive request history. It no longer recommends
prompt habits, labels a no-edit answer a bad prompt, or applies one person's
correction-rate calibration to someone else's data.

Habit proportions include **change attempts with known outcomes**. Unknown
outcomes and read-only tasks are excluded. The groups overlap and the requests
can be correlated, so these proportions are not significance tests or causal
advice. No best/worst ranking is printed. Correction markers are a lexical
estimate with false positives and misses, not a guaranteed lower bound.

Coach JSON is marked `transcripto.coach/2`. Legacy `durable`/`survived` fields
refer only to observed successful change results, not lasting work. Unknown
request outcomes have `survived: null`. `durable_rate` uses only known change
requests as its denominator and is null when there are none. `best_prompt` and `worst_prompt` are
retained as null compatibility fields. Use `successful_request`,
`failed_request`, and replay's event status to inspect evidence.

`export-run latest` always prints JSON. Its
existing `transcripto.export-run/1` keys remain available. `records` counts
normalized message records. `files_touched` lists attempted file targets,
including reads; it is not a successful-change count. Reflog commits are local
working-tree events inside the available timestamp window, not proof that this
agent caused them. Without a usable window, the commit fields are null.

## Privacy and limits

The three runtime modules contain no network client, telemetry, account flow,
or process execution. Package installation (`pip` or `uvx`) is a separate
operation that may contact a package registry and write a package cache.

Replay and coach read transcripts without making an index. Search writes text
and file metadata to `~/.trace/trace.db`. A new index directory is private;
database and WAL files use mode `0600`. The index stays after the command exits.
Schema upgrades rebuild it locally. `replay --demo` briefly writes an invented
transcript to a temporary directory and removes it afterward.

Malformed records and unreadable files produce diagnostics. Search indexes the
valid records of partially malformed files and repeats the warning on later
queries until the source is repaired. A wholly unreadable file keeps any prior
indexed copy, with an explicit warning; replay always reads the source. Files larger than
128 MiB are skipped before parsing; lines larger than 8 MiB are discarded as
whole records. Split larger files into smaller JSONL files to inspect them.
Individual displayed text fields are bounded at 16,000 characters. Replay's
source references let you inspect the original. Terminal control sequences are
removed from rendered transcript content.

## Development

Python 3.9+, standard library only. The CLI remains in `transcripto.py`;
`transcripto_core.py` owns normalization and evidence; `transcripto_replay.py`
owns replay selection and presentation. All fixtures committed here are synthetic.

```sh
python3 -m unittest discover -s tests -v
for test in test_*.sh; do bash "$test" || exit; done
```

The regression cases include failed edits and commits, missing/mismatched
results, Cursor call shapes, Codex wrappers, result attribution across prompts,
rollback order, malformed JSON, a sparse 2 GiB file, terminal controls, private
index permissions, incremental search, and cross-harness retrieval.

MIT. Open an issue with the **record shape** that fails, or a synthetic
reproduction. Your real prompt text is not needed.
