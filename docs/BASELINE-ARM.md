# Baseline arm — naive path vs transcripto

Measured 2026-09-05. Numbers re-derived at their objects; not carried from
older docs.

## Arm A — retention story (the article claim)

**Question:** how many transcript files are older than 30 days?

| arm | how | result tonight | simplicity |
|-----|-----|----------------|------------|
| **naive `find`** | `find ROOT -name '*.jsonl' ! -newermt <30d> \| wc -l` | fixture: **504 of 2721**, old45=0 | one shell pipeline; no install |
| **transcripto** | no file-age retention command | n/a | does not answer this question |

**Ruling: naive wins on the retention claim.**

Transcripto indexes and searches transcript *content*. It does not replace
`find` for mtime retention. If the article's proof is "504 of 2,721 files
older than 30 days", the honest tool is `find`. Shipping coach numbers as
proof of that claim is the wrong-object failure mode.

Commands run:

```sh
bash scripts/cold_verify.sh
# → ratio_30d: 504 of 2721 · ASSERT fixture … PASS
```

## Arm B — authorship gate (different object)

**Question:** how many turns did the operator actually type?

Corpus: `fixtures-coach/coach-fixture.jsonl` (synthetic).

| arm | how | count | simplicity |
|-----|-----|------:|------------|
| **naive** | count JSON rows with `"type":"user"` | **12** | one Python/`jq` one-liner; no install |
| **transcripto** | `coach --json` → `human_turns` (typed/queued gate) | **8** | needs install + gate |

Commands run:

```sh
python3 -c "
import json
from pathlib import Path
n=t=0
for line in Path('fixtures-coach/coach-fixture.jsonl').read_text().splitlines():
    if not line.strip(): continue
    t+=1
    if json.loads(line).get('type')=='user': n+=1
print('naive', n, 'of', t)
"
python3 transcripto.py coach --root fixtures-coach --json
# → human_turns: 8, total_records: 21
```

**Inflation:** naive 12 vs gate 8 → naive counts 4 rows the gate rejects
(tool results / non-typed user rows). On this fixture the gate keeps
8/21 ≈ 38.1% of records as human turns.

**Ruling: naive wins on simplicity; transcripto wins when the question is
"what did I type".** Habit grading, `ask`, and cost-per-decision need the
gate. Raw `type:user` counting does not.

## What would embarrass us

- Using Arm B numbers to "verify" Arm A's retention claim.
- Claiming transcripto is required to reproduce 504/2721.
- Hiding that `pip install` adds friction the retention story does not need.

## Honest product sentence

> To see whether your agent is deleting old transcripts, run `find`.
> To read the words you typed inside what remains, run transcripto.
