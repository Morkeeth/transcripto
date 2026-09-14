# Changes

## 0.2.1 — search to exact replay

- Each search hit from `ask` prints a command that reopens its exact request,
  including when stemming matches a different word form. `replay --line` selects
  the cited source line; missing sources and invalid roots fail clearly.
- `changes` shows cited correction sequences. `handoff` and `receive-handoff`
  prepare local correction packets and receiver briefs without invoking another
  agent or claiming that the receiver used the instruction.
- The optional public example stays labelled synthetic through search, replay,
  sharing and handoff. Invented requests are excluded from personal counts.
- Handoff outputs are written atomically with private permissions and cannot
  overwrite their source through a path alias.
- Installed-wheel checks cover discovery and replay across Claude, archived
  Codex sessions and Cursor, plus the complete synthetic handoff flow.

Compatibility: Python 3.9+, no runtime dependencies. The local index rebuilds
at schema version 5. Message IDs must not be retained across rebuilds.


## 0.2.0 — instant replay

- Running `transcripto` opens the latest session with a submitted human request.
- Replay joins calls to results and shows succeeded, failed, and unknown execution,
  with source-line references, failure navigation, text search, JSON, and a
  numbers-only share mode. The synthetic demo uses the real parser.
- Claude Code, Codex, and Cursor use one normalizer for replay and retrieval.
  Cursor `StrReplace`, `Shell`, and path fields are recognized. Missing results
  remain unknown; a completed chat turn does not prove tool success.
- Search builds and refreshes its index automatically. Queries respect selected
  roots and harnesses. Incremental refresh removes stale full-text entries and
  deleted transcripts. Index files have private permissions.
- Coach no longer ranks prompt quality, treats read-only requests as failures,
  or projects the author's correction-rate estimate onto other users.
- Malformed records produce diagnostics. Oversized files and lines are bounded.
  Rendered transcript content has terminal controls removed.

Compatibility: `cost` remains Claude-only. Coach JSON is `transcripto.coach/2`;
legacy best/worst fields are null. The index schema rebuilds at version 3.
Consumers should not retain message IDs across rebuilds. See READ-CONTRACT.md.

Published to PyPI on 4 September 2026.
