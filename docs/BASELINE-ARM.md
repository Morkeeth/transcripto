# Baseline arm — naive path vs transcripto

Measured 2026-09-10. Numbers re-derived at their objects; not carried from
older docs.

## Arm A — retention story (the article claim)

**Question:** how many transcript files are older than 30 days?

| arm | how | result tonight | simplicity |
|-----|-----|----------------|------------|
| **naive `find`** | `find ROOT -name '*.jsonl' ! -newermt <30d> \| wc -l` | fixture: **504 of 2721**, old45=0 | one shell pipeline; no install |
| **transcripto (source)** | no file-age retention command | `product_boundary: PASS` | does not answer this question |
| **pip install only** | `pip install transcripto==0.2.0` then `transcripto retention` | exit **2**; help has no file-age verb | install friction; still cannot answer |

**Ruling: naive wins on the retention claim.**

Transcripto indexes and searches transcript *content*. It does not replace
`find` for mtime retention. If the article's proof is "504 of 2,721 files
older than 30 days", the honest tool is `find`. Shipping coach or stats
numbers as proof of that claim is the wrong-object failure mode.

Commands run:

```sh
bash scripts/cold_verify.sh
# → ratio_30d: 504 of 2721 · ASSERT fixture … PASS · product_boundary: PASS

bash scripts/pip_only_baseline.sh
# → naive_find_ratio: 504 of 2721
# → transcripto_retention_exit: 2
# → arm_a_ruling: naive find WINS retention
```

**PyPI package audit (bigger packaging object):** the published
`transcripto-0.2.0` wheel has **0** `cold_verify` entries (9 files total).
`pip install transcripto` alone cannot reproduce the stranger retention
script — that path requires a clone or git-archive of this repo.

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
```

**Inflation:** naive 12 vs gate 8 → naive counts 4 rows the gate rejects
(tool results / non-typed user rows). On this fixture the gate keeps
8/21 ≈ 38.1% of records as human turns.

**Ruling: naive wins on simplicity; transcripto wins when the question is
"what did I type".** Habit grading, `ask`, and cost-per-decision need the
gate. Raw `type:user` counting does not.

## What would embarrass us

- Using Arm B numbers to "verify" Arm A's retention claim.
- Quoting tonight's `stats` line `2,721 of the 2,721 messages … 100.0%` as
  retention evidence (DETECTED on cold_verify, wheel, and pip-only arms).
- Claiming transcripto is required to reproduce 504/2721.
- Printing a daily death rate of 75 from the 504→579 / 2721→2874 stamp pair
  (total rose; `death_rate_impossible: PASS`).
- Flattening "30-day deletion" onto Desktop/Cowork sessions (docs default 0 /
  no age limit).
- Hiding that `pip install` adds friction the retention story does not need,
  and still does not ship `scripts/cold_verify.sh`.

## Honest product sentence

> To see whether your agent is deleting old transcripts, run `find`.
> To read the words you typed inside what remains, run transcripto.
> To cold-verify the retention *method* without Oscar's corpus, clone this
> repo and run `bash scripts/cold_verify.sh` — not `pip install` alone.
