# Baseline arm — naive / pip-only vs transcripto

Measured 2026-09-06 (bc-fa7a9e70). Numbers re-derived at their objects; not
carried from older docs or from the prompt.

## Arm A — retention story (the article claim)

**Question:** how many transcript files are older than 30 days?

| arm | how | result tonight | simplicity |
|-----|-----|----------------|------------|
| **naive `find`** | `find ROOT -name '*.jsonl' ! -newermt <30d> \| wc -l` | fixture: **504 of 2721**, old45=0; oracle find↔stat PASS | one shell pipeline; no install |
| **pip install only** | `pip install transcripto==0.2.0` then ask the CLI for file-age | no retention verb; `transcripto retention` exit **2** | needs PyPI once; still cannot answer |
| **transcripto (clone)** | no file-age retention command | `product_boundary: PASS` | does not answer this question |

**Ruling: naive `find` wins on the retention claim.**

Transcripto indexes and searches transcript *content*. It does not replace
`find` for mtime retention. If the article's proof is "504 of 2,721 files
older than 30 days", the honest tool is `find`. Shipping coach/`stats`
numbers as proof of that claim is the wrong-object failure mode.

Commands run:

```sh
bash scripts/cold_verify.sh
# → ratio_30d: 504 of 2721 · ASSERT fixture … PASS
# → independent_oracle: PASS · boundary_probe: PASS · offline_core: PASS

bash scripts/pip_only_baseline.sh
# → naive_find_ratio: 504 of 2721
# → transcripto_retention_exit: 2
# → arm_a_ruling: naive find WINS retention
```

### Embarrassing near-miss (pip-only `stats`)

On the same arithmetic retention fixture, pip-installed
`transcripto stats --root …` printed:

> 2,721 of the 2,721 messages in your index are things you typed. 100.0%

That **2,721** matches the retention denominator while measuring indexed
messages inside synthetic one-record files. A rushed article draft could
quote it as "retention evidence." It is not.

## Arm B — authorship gate (different object)

**Question:** how many turns did the operator actually type?

Corpus: `fixtures-coach/coach-fixture.jsonl` (synthetic).

| arm | how | count | simplicity |
|-----|-----|------:|------------|
| **naive** | count JSON rows with `"type":"user"` | **12** | one Python/`jq` one-liner; no install |
| **pip install only** | `transcripto coach --json` → `human_turns` from live PyPI 0.2.0 | **8** | needs PyPI; no clone |
| **clone / editable** | same coach gate on source | **8** | needs clone |

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
# → naive 12 of 21

bash scripts/pip_only_baseline.sh
# → naive_type_user: 12 · pip_only_human_turns: 8
# → import_source: site-packages OK (not /workspace)
```

**Ruling: naive wins on simplicity; transcripto (pip or clone) wins when the
question is "what did I type".** Habit grading, `ask`, and cost-per-decision
need the gate. Raw `type:user` counting does not.

## What would embarrass us

- Using Arm B numbers (or `stats` 2721/2721) to "verify" Arm A's retention claim.
- Claiming transcripto is required to reproduce 504/2721.
- Hiding that `pip install` adds friction the retention story does not need.
- Treating a planter that asserts its own plant as method proof (fixed via
  independent oracle).
- Treating the calendar `find ! -newermt` cut as identical to
  `age_seconds > 30*86400` (`duration_vs_calendar=0` tonight).
- Claiming stranger-cold PASS after only testing a git clone (archive extract
  failed privacy until tonight's fix).

## Honest product sentence

> To see whether your agent is deleting old transcripts, run `find`.
> To read the words you typed inside what remains, run transcripto
> (`pip install transcripto==0.2.0` is enough; no clone required for ask/coach).
