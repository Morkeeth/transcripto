# Baseline arm — pip-install-only / naive vs transcripto

**Captured:** 2026-09-23  
**Command:** `bash scripts/pip_only_baseline.sh`  
**Exit:** 0 (`pip_only_baseline: PASS`)

## Why this arm exists

A number scored only against our own source answers “does tip work.”
It cannot answer “is it better than the alternative.” This arm is the
naive / pip-only path any competent team builds in two hours.

## Arm A — file-age retention

| path | result (re-derived tonight) |
|------|-----------------------------|
| Naive `find -type f -name '*.jsonl' ! -newermt … \| wc -l` | **504 of 2721** (threshold `2026-08-24`) |
| `pip install transcripto==0.2.0` then ask for retention | **exit 2** — no such command |
| pip-only `stats` on the same fixture | prints **2,721 of 2,721 messages** (near-miss) |

**Ruling:** naive `find` **WINS** retention. Pip-only transcripto cannot
answer file-age. Tip `cold_verify.sh` is the stranger method; it is not
on the published wheel (`pypi_wheel_cold_verify_entries: 0`).

## Arm B — authorship gate

| path | result |
|------|--------|
| Naive `type == "user"` count on `fixtures-coach` | **12** |
| Pip-only `coach --json` → `human_turns` | **8** |

**Ruling:** naive wins simplicity; pip-only gate is stricter (expected).
Do not quote the naive count as “human turns.”

## Embarrassment on the published object

Re-derived tonight against live PyPI **0.2.0**:

- `pip_only_stats_caveat: ABSENT` — wheel lacks tip anti-conflation line
- `pip_only_verb_gap: DETECTED` — missing `import-example`, `changes`,
  `handoff`, `receive-handoff`, `import-lab`, `quickstart`
- README stranger flow therefore needs **source/tip**, not `pip install`
  alone (OQ-5; Oscar decides whether article waits on a cut)

## Honest scoreboard

| question | winner tonight |
|----------|----------------|
| Reproduce file-age retention with one shell line | **naive find** |
| Gate authorship below raw `type:user` | **transcripto coach** |
| Stranger product journey from PyPI 0.2.0 | **neither** (verbs absent) |
| Stranger product journey from source tip | **transcripto** (`cold_verify` journey PASS) |
