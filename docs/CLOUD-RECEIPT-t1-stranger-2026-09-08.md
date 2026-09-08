# T1 stranger-flow cloud receipt

Date: 2026-09-08  
Starting commit: `fa15f1b23dc190df62b96da02b6ed160583ad3a1`

## Privacy gate

- Inspected the tracked tree, repository instructions, README, package/build
  configuration, ignore rules, and CI build context before preparing cloud-visible
  content. No `AGENTS.md` or `CLAUDE.md` was present.
- Used only an embedded, explicitly synthetic weather-service transcript.
- Found and removed a category of person-specific denylist literals from the privacy
  guard itself. No value or sensitive path from that category is reproduced here.
- The replacement guard checks structural home paths, credential forms, and
  personal-note path shapes in production and documentation. Synthetic parser
  fixtures are kept separate.
- The flow requires no existing harness dotfiles. Generated transcript, packet, and
  receiver files use mode `0600`.

## Stranger path exercised

From a clean package target and isolated `HOME`:

```sh
python3 -m pip install --no-deps --no-build-isolation --target /tmp/t1-install .
HOME=/tmp/t1-home PYTHONPATH=/tmp/t1-install python3 -m transcripto import-example
HOME=/tmp/t1-home PYTHONPATH=/tmp/t1-install python3 -m transcripto \
  ask "What changed about the forecast cache?"
HOME=/tmp/t1-home PYTHONPATH=/tmp/t1-install python3 -m transcripto changes
```

The question returned the correction from the imported example with its exact
JSONL source line. `changes` showed the earlier 60-second request, the 30-second
correction, and the recorded successful edit instead of a general activity dump.

## Receiver handoff

```sh
HOME=/tmp/t1-home PYTHONPATH=/tmp/t1-install python3 -m transcripto \
  handoff "30 seconds" --to-harness codex \
  --output /tmp/t1-home/codex-inbox/correction.json
HOME=/tmp/t1-home PYTHONPATH=/tmp/t1-install python3 -m transcripto \
  receive-handoff /tmp/t1-home/codex-inbox/correction.json \
  --as-harness codex --output /tmp/t1-home/codex-work/receiver-brief.md
```

The separate Codex receiver path adopted the correction in its brief. It explicitly
named task-correctness verification as still missing; packet delivery and a recorded
edit result do not prove semantic completion.

## Verification

- `python3 -m unittest discover -s tests -v` — 75 tests passed.
- `for test in test_*.sh; do bash "$test" || exit 1; done` — all shell suites passed.
- `bash test_privacy.sh` — zero structural hits in production/documentation files.
- Isolated target install and the complete import → cited question → change
  exploration → handoff → receiver flow exited successfully.
- `git diff --check` — clean.

No deployment, publication, paid service, or child-agent fanout was used.
