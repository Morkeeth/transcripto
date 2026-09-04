# Read contract

Transcripto owns `~/.trace/trace.db`. External consumers open it read-only:

```python
import os
import sqlite3
con = sqlite3.connect(
    'file:%s?mode=ro' % os.path.expanduser('~/.trace/trace.db'), uri=True)
```

Use the stable views:

- `v_sessions`: session ID, project, first/last timestamps, message and assistant counts, cwd, harness.
- `v_messages`: ID, session ID, project, timestamp, role, cwd, branch, text, human flag, prompt source, harness.
- `v_file_touches`: name, path, action, session ID, timestamp, cwd, harness.
- `v_index_health`: source file, indexed modification time, JSON warnings for partial reads.
- `messages_fts`: full-text search joined to `v_messages.id`.

Version 0.2.0 rebuilds older indexes with the shared Claude Code, Codex, and
Cursor normalizer. `is_human` follows the harness-specific gate documented in
the README. For Codex and Cursor, `prompt_source` is a normalized value, not a
native authorship stamp.

File actions `write` and `edit` require a successful tool result. `attempt:write`
and `attempt:edit` include failed or unknown changes. `read` and other named
actions describe recorded calls. Use replay JSON for full execution statuses
and call/result line references; the SQLite file view is not an outcome API.

`transcripto index` refreshes all default harnesses. Search also refreshes
incrementally. `--root` and `--harness` scope CLI queries; external readers of
the stable views see the full indexed corpus. Deleted transcript files are
removed at refresh. Partially readable files index their valid records and retain diagnostics in
`v_index_health`. Wholly unreadable files retain any prior indexed copy, with an
explicit warning on each query. Use the health view before treating partial
index results as a complete corpus.

Consumers must not write to these tables. Store consumer state separately,
keyed by session ID. Message IDs can change during reindexing and schema
rebuilds; they are not durable foreign keys. Read-only connections must be
reopened after a schema migration if a query fails.

## Source references (SQLite schema 5)

`transcripto ask "offline parser" --json` returns `transcripto.ask/1` with
original request text, provider, session ID, recorded timestamp and cwd, plus
the source path, one-based JSONL line, record SHA-256 and indexed source SHA-256.
These identify evidence, not a synthesized answer. Text is normalized and bounded;
the referenced original record is authoritative. No-match returns an empty hit
list and source coverage. Request authorship is `human` only with Claude's native
typed/queued gate; Codex/Cursor envelopes return `unknown`.

Natural-question openings remove common question words before matching topic
terms. The JSON `selection` lists both retained and ignored words; `--literal`
keeps every word. This is lexical retrieval, not semantic understanding. Negation
is retained. There is no automatic synonym or spelling substitution. Coverage
includes indexed parser diagnostics, including when valid records match in a
partially readable source. Consumers must inspect coverage even on `matches`.

`v_messages` adds `session_file`, `source_line`, and `record_sha256`. An indexed
source hash describes the bytes observed at indexing, not perpetual freshness.
Refresh checks nanosecond modification time and size; changed files are hashed
before and after parsing. A writer changing a source during indexing causes a
retry warning. Hash-check a source before using saved evidence. File timestamps
alone cannot detect a same-size rewrite with deliberately preserved metadata.

Set `TRANSCRIPTO_DB` to an explicit local SQLite path for an isolated consumer
index or reproducible corpus. The default remains `~/.trace/trace.db`.

## Recover → inspect → continue

```sh
transcripto ask "offline parser" --json
transcripto trace /path/to/session.jsonl --from-line 10 --to-line 25
transcripto export-run /path/to/session.jsonl --packet --from-line 10 --to-line 25 --output /private/path/context.json
transcripto export-run /private/path/context.json --check
```

Use the path and one-based line numbers from the actual search result, not the
example above. `trace --json` or `export-run --timeline` returns
`transcripto.session/1`. `identity` separates the file owner, native session ID,
provider, parent ID and the basis for each identity. Codex fork metadata stays
attached to the child even when its file includes a second parent metadata
record. Each event identifies inherited context and its origin session when
available. Child actions never become consequences in a parent replay episode.
Claude sidechain identities combine the native parent session ID and subagent
filename, with that derivation stated. Unknown parent identity is null.

`repository` distinguishes recorded cwd from the worktree and Git common directory
observed now. An unavailable recorded path remains unavailable; Transcripto does
not guess where a repository moved. `started_at` and `last_observed_at` use native,
timezone-bearing timestamps of non-inherited records. Cursor context clocks are
labelled separately and do not establish per-message activity time. `work_state`
is unknown: a transcript timestamp does not prove a process is running.

The timeline preserves requests, assistant responses, calls and matching result
references. Its order does not imply causality. Only results inside the selected
range contribute execution evidence. Raw tool output is omitted. Coverage lists
partial-read warnings and record types not mapped into the timeline.

Packets require an explicit range containing a request. They include that selected
evidence, full-source SHA-256, current question, uncertainty, and optional caller
annotations. `--settled-line N` and `--reversed-line N` classify a selected request
after review; repeat the option for more decisions. They cannot classify an
assistant response. `--question` and `--next-action` are explicitly caller-supplied
annotations. No decision or next action is invented when these are omitted.

`--output` creates a new local file with mode 0600 and refuses an existing path.
Nothing is uploaded. Packets contain private text; choosing a local range is not
permission to publish it. A freshness check returns exit 0 for matching source
bytes, exit 3 for stale or unverifiable source, and exit 2 for an invalid input.
Appending even unrelated evidence invalidates a packet conservatively. Freshness
does not verify decision correctness or detect edits to the packet itself.

The legacy `export-run/1` summary adds identity, repository, source version and
coverage without exporting the timeline text. Its counts exclude inherited Codex
parent records. `typed_turns` remains a legacy name for request-envelope counts;
it is not proof of human typing in Codex or Cursor. Consumers should use the
timeline authorship field for that distinction. SQLite `v_messages` adds
`origin_session_id`, `inherited`, `session_kind` and `timestamp_basis`; NULL is
unknown, not false. Reopen readers after migration.
