# Baseline arm — naive / pip-only / wheel vs transcripto

Measured 2026-09-11 ~00:15–00:16 UTC. Numbers re-derived at their objects; not
carried from older docs or from the prompt.

## Arm A — retention story (the article claim)

**Question:** how many transcript files are older than 30 days?

| arm | how | result tonight | simplicity |
|-----|-----|----------------|------------|
| **naive `find`** | `find ROOT -name '*.jsonl' ! -newermt <30d> \| wc -l` | fixture: **504 of 2721**, old45=0; oracle find↔stat PASS (103/44) | one shell pipeline; no install |
| **pip install only** | `pip install transcripto==0.2.0` then ask the CLI for file-age | no retention verb; `transcripto retention` exit **2** | needs PyPI once; still cannot answer |
| **local wheel** | `pip wheel` + offline `pip install --no-index` from clean cwd | same product boundary; `ratio_30d: 504 of 2721` via find | packaging proof; still cannot answer file-age |
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
# → independent_oracle: PASS (old30=103, old45=44; seed 20260911)
# → negative_planter: PASS · boundary_probe: PASS · offline_core: PASS
# → calendar_duration_delta: none on fixture (skew 950s; ages 31–44d)
# → duration boundary file counted_by_bang_newermt=0 (calendar stricter)
# → touch_utime_planter: PASS (7 of 10 each)
# → tz_divergence: OBSERVED · tz_pair_trap: DETECTED (UTC↔Tokyo agree; LA differs)
# → frozen_quote_reconcile: FAIL-TO-RECONCILE

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

### Embarrassing TZ pair trap (inverse of prior wave)

Tonight UTC/Tokyo/London calendar cuts **agreed** (`2026-08-12`) while
America/Los_Angeles differed (`2026-08-11`). Prior wave's detector only
watched "UTC↔LA agree, Tokyo differs" — that condition was **false** tonight.
Extending the detector caught the inverse. **Which pair you pick decides
whether divergence looks absent.** Publish TZ with any live figure.

### Embarrassing frozen-quote non-reconciliation

504/2721 → 579/2874 moves both numerator (+75) and denominator (+153).
"Only young additions" and "only aging" are both rejected; a unique daily
death rate is **underdetermined**. Do not print one from those two stamps.

### Embarrassing calendar↔duration boundary (fixture quiet, boundary loud)

On the full planted fixture (ages 31–44d), calendar and duration both counted
**504** despite a **950s** skew between midnight and `now-30*86400`. A file
aged *exactly* `30*86400` seconds was **not** counted by `! -newermt`
(`counted_by_bang_newermt=0`). Agreement on far-from-boundary ages does not
license treating the two methods as identical.

### Touch↔utime planter (watched; agreed tonight)

Shell `touch -d "$N days ago"` and Python `os.utime(now - N*86400)` both
yielded **7 of 10** under tonight's calendar cut. Cold fixture uses `os.utime`.
Divergence would be a planter bug, not a retention finding.

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
| Naive find beats us on retention | product cannot answer the article's proof question | keeps the article honest |
| `stats` 2721 lookalike | draft could launder message counts as file retention | control is watched |
| Main privacy empty-index green | "PRIVACY OK: 0 hits in 0 tracked files" exit 0 | fail-closed fix + empty-index test |
| TZ pair trap (inverse tonight) | UTC↔Tokyo green while LA differs; old detector missed it | multi-zone + inverse pair |
| Frozen quotes underdetermined | death-rate headline would be invented | FAIL-TO-RECONCILE marker |
| Wheel cwd-shadow | packaging "proof" can silently test the tree | trap watched then clean-cwd re-proof |
| Calendar quieter than duration at boundary | one-file probe counted 0 under calendar | name the method in the article |
