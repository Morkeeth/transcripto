# Baseline arm — naive / pip-only / wheel vs transcripto

Measured 2026-09-14 ~00:11 UTC. Numbers re-derived at their objects; not
carried from older docs or from the prompt.

## Arm A — retention story (the article claim)

**Question:** how many transcript files are older than 30 days?

| arm | how | result tonight | simplicity |
|-----|-----|----------------|------------|
| **naive `find`** | `find ROOT -type f -name '*.jsonl' ! -newermt <30d> \| wc -l` | fixture: **504 of 2721**, old45=0; oracle find↔stat PASS | one shell pipeline; no install |
| **naive `-mtime +30`** | `find … -mtime +30` | **DISAGREES** with calendar cut on 6/10 near-boundary samples tonight | also one pipeline — and **wrong object** for the article method |
| **pip install only** | `pip install transcripto==0.2.0` then ask the CLI for file-age | no retention verb; `transcripto retention` exit **2** | needs PyPI once; still cannot answer |
| **local wheel** | `pip wheel` + offline `pip install --no-index` from clean cwd | same product boundary; `ratio_30d: 504 of 2721` via find | packaging proof; still cannot answer file-age |
| **transcripto (clone)** | no file-age retention command | `product_boundary: PASS` | does not answer this question |

**Ruling: naive `find` with `! -newermt` wins on the retention claim.**

Transcripto indexes and searches transcript *content*. It does not replace
`find` for mtime retention. If the article's proof is "504 of 2,721 files
older than 30 days", the honest tool is `find`. Shipping coach/`stats`
numbers as proof of that claim is the wrong-object failure mode. Shipping
`-mtime +30` as a synonym is also wrong — watched tonight.

Commands run:

```sh
bash scripts/cold_verify.sh
# → ratio_30d: 504 of 2721 · ASSERT fixture … PASS
# → independent_oracle: PASS (93/51) · boundary_probe: PASS · offline_core: PASS
# → negative_planter: PASS · mtime_vs_newermt: DETECTED (6/10)
# → hardlink_inflation: DETECTED · tz_pair_trap: DETECTED
# → frozen_quote_reconcile: FAIL-TO-RECONCILE · stats_near_miss: DETECTED

bash scripts/pip_only_baseline.sh
# → naive_find_ratio: 504 of 2721
# → transcripto_retention_exit: 2
# → arm_a_ruling: naive find WINS retention

bash scripts/wheel_stranger.sh
# → cwd_shadow_trap: DETECTED (repo cwd binds TREE)
# → import_source: wheel site-packages OK (clean cwd)
# → ASSERT fixture 504 of 2721 (old45=0): PASS
# → product_boundary_wheel: PASS
```

### Embarrassing near-miss (pip-only / wheel `stats`)

On the same arithmetic retention fixture, installed
`transcripto stats --root …` printed:

> 2,721 of the 2,721 messages in your index are things you typed. 100.0%

That **2,721** matches the retention denominator while measuring indexed
messages inside synthetic one-record files. A rushed article draft could
quote it as "retention evidence." It is not. Cold verify prints
`stats_near_miss: DETECTED` when this happens. Wheel and pip-only arms
reproduced it tonight.

### Embarrassing packaging trap (wheel + repo cwd)

Verifying a wheel install while `cwd` is the source checkout silently binds
`transcripto.py` from the tree (`sys.path[0] == ''`). Tonight:
`cwd_shadow_trap: DETECTED`. Clean-cwd import then showed site-packages.

### Embarrassing TZ pair trap (tonight)

UTC↔Tokyo↔London calendar cuts **agreed** (`2026-08-15`) while
America/Los_Angeles differed (`2026-08-14`). Which pair you pick decides
whether divergence looks absent. Publish TZ with any live figure.

### Embarrassing `-mtime +30` substitute (new tonight)

Near the calendar midnight cut, 6 of 10 planted ages were counted by
`! -newermt` but **not** by `-mtime +30`. A competent two-hour baseline that
uses `-mtime +30` is measuring a different object. Article method must name
the calendar cut.

### Embarrassing hardlink inflation (new tonight)

`find -type f -name '*.jsonl'` counted **2** names for **1** inode when a
hardlink was planted. Symlink inflation is fixed by `-type f`; hardlink
inflation is not. The article method counts names.

### Embarrassing fixture symlink dilution (new tonight)

Planting a young symlink into the 504/2721 tree made name-only find report
**504 of 2722** while `-type f` stayed **504 of 2721**. Omitting `-type f`
does not just inflate — it **dilutes** the old fraction. First draft of this
probe wrongly expected old30 to become 505 (symlink mtime is now); that guess
failed at the object and was corrected.

### Embarrassing frozen-quote non-reconciliation

504/2721 → 579/2874 moves both numerator (+75) and denominator (+153).
"Only young additions" and "only aging" are both rejected; a unique daily
death rate is **underdetermined**. Do not print one from those two stamps.

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
    if not line.strip():
        continue
    t += 1
    if json.loads(line).get('type') == 'user':
        n += 1
print(n, t)
"
# → 12 21

bash scripts/pip_only_baseline.sh
# → naive_type_user: 12
# → pip_only_human_turns: 8

bash scripts/cold_verify.sh
# → naive type:user count: 12
# → transcripto human_turns (gated): 8
```

**Ruling:** naive wins **simplicity**. Transcripto wins **honesty of the gate**
(8 < 12 — injected/tool-shaped user rows excluded). Do not use Arm B numbers
as retention evidence.

## What we would not want to publish (and why it is valuable)

| finding | why it hurts | why it ships |
|---------|--------------|--------------|
| naive `find` beats transcripto on retention | product cannot answer the article's headline method | honesty > demo |
| `-mtime +30` disagrees with article cut | easy wrong baseline looks "close enough" | catch the substitute |
| `stats` prints 2721 typed | looks like retention evidence | catch the wrong object |
| empty-index privacy used to exit 0 | green on outage | fail-closed now watched RED |
| frozen stamps ≠ death rate | tempting narrative | refuse the laundering |
| wheel cwd-shadow | false "wheel works" from tree import | clean-cwd required |
| hardlink name count ≠ inode count | inflated totals if trees hardlink | name the object |
| Desktop cleanup Default 0 | live 504/2721 may mix exempt Desktop files | OQ-4 for Oscar |
