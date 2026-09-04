# Transcripto — read contract for consumers (ZUP, Helicon)

Transcripto is the **single writer + schema owner**. Consumers **read only, never write**. This is the one rule that keeps the suite a shared data layer and not a merged behemoth.

## Connect (read-only)
DB: `~/.trace/trace.db` (SQLite). _(Rename to `~/.transcripto/` planned; path is stable until then.)_
```python
import sqlite3, os
con = sqlite3.connect("file:%s?mode=ro" % os.path.expanduser("~/.trace/trace.db"), uri=True)
```
Read-only is enforced: a write raises `attempt to write a readonly database`.

## Stable views — the only supported surface (do not read raw tables)
- `v_sessions(session_id, project, last_ts, first_ts, n_messages)`
- `v_file_touches(name, path, action, session_id, ts, cwd)` — `action` ∈ write | edit | read
- `v_messages(id, session_id, project, ts, role, cwd, git_branch, text, is_human, prompt_source)`
  - `is_human = 1` marks a turn the operator actually **typed** (`promptSource` typed/queued, not meta/tool/sidechain/sdk/system). At fleet scale ~95% of `role='user'` rows are NOT him — filter `WHERE is_human=1` for his own words. `prompt_source` is the raw Claude Code value for auditing.
- Full-text search: `messages_fts` (FTS5 `MATCH`), join to `v_messages` on `id`.

## Rules (from ARCHITECTURE.md)
1. Never write to this db. Open `mode=ro`.
2. Keep consumer state (ZUP's needs-me flags, Helicon's verdicts) in the **consumer's own store**, keyed by `session_id` / message `id`.
3. Do not fork the schema. Need a field a view doesn't expose? Ask Transcripto to add a **view** — never read raw tables or write back. If you'd *have* to, STOP: that's the behemoth signal.
4. Refresh: `transcripto index` (or `transcripto watch`) updates the index; consumers just re-query.
