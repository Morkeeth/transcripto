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
