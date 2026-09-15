# Baseline arm — naive path vs transcripto

Measured **2026-09-15**. Numbers re-derived at their objects; not carried from
older docs or from this prompt.

## Arm A — retention story (the article claim)

**Question:** how many transcript files are older than 30 days?

| arm | how | result tonight | simplicity |
|-----|-----|----------------|------------|
| **naive `find`** | `find ROOT -type f -name '*.jsonl' ! -newermt <30d> \| wc -l` | fixture: **504 of 2721**, old45=0 | one shell pipeline; no install |
| **transcripto (source)** | no file-age retention command | `product_boundary: PASS` | does not answer this question |
| **pip install only** | `pip install transcripto==0.2.0` then `transcripto retention` | exit **2**; help has no file-age verb | install friction; still cannot answer |

**Ruling: naive wins on the retention claim.**

Transcripto indexes and searches transcript *content*. It does not replace
`find` for mtime retention. If the article's proof is "504 of 2,721 files
older than 30 days", the honest tool is `find`. Shipping coach or stats
numbers as proof of that claim is the wrong-object failure mode.

Commands run:

```sh
TRANSCRIPTO_COLD_DIR=/tmp/transcripto-cold-tonight bash scripts/cold_verify.sh
# → ratio_30d: 504 of 2721 · ASSERT fixture … PASS · product_boundary: PASS
# → stats_near_miss: DETECTED — "2,721 of the 2,721 messages…"

bash scripts/pip_only_baseline.sh
# → naive_find_ratio: 504 of 2721
# → transcripto_retention_exit: 2
# → stats_near_miss: DETECTED on pip-only arm
# → arm_a_ruling: naive find WINS retention
```

**PyPI package audit (bigger packaging object):** the published
`transcripto-0.2.0` wheel has **0** `cold_verify` entries (9 files total,
re-derived from the live wheel zip). `pip install transcripto` alone cannot
reproduce the stranger retention script — that path requires a clone or
git-archive of this repo.

## Arm B — authorship gate (different object)

**Question:** how many turns did the operator actually type?

Corpus: `fixtures-coach/coach-fixture.jsonl` (synthetic).

| arm | how | count | simplicity |
|-----|-----|------:|------------|
| **naive** | count JSON rows with `"type":"user"` | **12** | one Python/`jq` one-liner; no install |
| **transcripto (tree)** | `coach --json` → `human_turns` | **8** | needs tree + gate |
| **pip-only 0.2.0** | same coach gate from site-packages | **8** | needs pip + network once |

Commands run:

```sh
bash scripts/cold_verify.sh
# → naive type:user count: 12
# → transcripto human_turns (gated): 8

bash scripts/pip_only_baseline.sh
# → naive_type_user: 12
# → pip_only_human_turns: 8
# → arm_b_ruling: naive wins simplicity; pip-only gate is stricter
```

**Ruling on Arm B:** naive wins on simplicity; transcripto's gate is the
stricter (and intended) authorship object. Do not conflate Arm B with Arm A.

## What would embarrass us (and did)

1. Quoting `stats` `2,721` as retention evidence — **DETECTED** on source,
   pip-only, and wheel arms tonight.
2. Inventing a daily death rate from frozen 504/2721 → 579/2874 —
   **FAIL-TO-RECONCILE** (control refuses).
3. Claiming `pip install transcripto` reproduces cold verify — wheel has
   **0** `cold_verify` entries.
4. Verifying a wheel while cwd is the source tree — **cwd_shadow_trap:
   DETECTED** (`import transcripto` binds `/workspace/transcripto.py`).
