# Baseline arm — naive path vs transcripto

The ambitious question is not "does transcripto work?" It is "is it better
than the alternative a competent team builds in two hours?"

Tonight's baseline is **pip install only** (PyPI `transcripto==0.2.0`,
re-derived) plus a naive `find` for file ages. Script:
`bash scripts/pip_only_baseline.sh` (RUN 2026-09-21T12:15:13Z,
branch `cursor/night-wave-p1-launch-8b78`).

## Arm A — file-age retention

| arm | what it does | tonight (RUN) |
|-----|--------------|---------------|
| Naive `find` | `find ROOT -type f -name '*.jsonl' ! -newermt <30d>` | **504 of 2721** — answers the object |
| Pip-only transcripto | `transcripto retention` / help scan | **exit 2** — no such command; help has no file-age verb |
| Pip-only `stats` | message counts on the retention fixture | prints `2,721 of the 2,721 messages … 100.0%` — **near-miss DETECTED**; caveat **ABSENT** on 0.2.0 |

**Ruling: naive `find` wins retention.** Pip-only transcripto cannot answer
file-age. Quoting `stats` as retention evidence would be the wrong object.

## Arm B — authorship gate (separate object)

| arm | tonight (RUN) |
|-----|---------------|
| Naive `type:user` count on `fixtures-coach` | **12** |
| Pip-only `coach` `human_turns` | **8** |

Naive wins simplicity. Pip-only gate is stricter (expected). This is **not**
the retention story — do not conflate.

## Embarrassment list (tonight)

1. Product cannot answer the article's central figure without shell `find`.
2. `stats` on a 2721-file fixture prints the retention denominator as a
   typed-message count — looks like confirmation, is not. Tip now names the
   object; **published 0.2.0 does not** (ABSENT). Re-proved: pip-only
   `import-example` → exit 2 (`invalid choice`).
3. **Published verb gap:** live 0.2.0 lacks `import-example` / `changes` /
   `handoff` / `receive-handoff` / `import-lab` / `quickstart`. README
   stranger flow (L48–71) installs from **source** (`.` target); readers who
   jump from the `uvx …==0.2.0` lines above into those verbs will hit exit 2.
4. Wheel cwd-shadow: `import transcripto` from the repo cwd binds the tree,
   not the installed wheel (`cwd_shadow_trap: DETECTED` in
   `scripts/wheel_stranger.sh`).
5. Empty-index privacy on main was green until tonight's fail-closed fix
   (`test_privacy_empty_index.sh` watched RED).
6. Blank-line `wc -l` invents "1 file" from an empty list (watched DETECTED).
7. `python3 -m venv` on this host left a partial tree without pip
   (`venv_partial_without_pip: DETECTED`); fallback to `virtualenv`.
8. **Desktop dual-gate** (docs object opened tonight): Default `0` keeps
   Desktop/Cowork at any age; deletion requires older than **both** Desktop
   and CLI cleanup periods. Managed `cleanupPeriodDays` ignores the Desktop key.
9. **TZ probe tonight:** all four zones agreed on `2026-08-22` (no divergence
   at this clock). A prior wave saw LA differ — clock-dependent; publish TZ.
10. Symlink inflation: `find -name` counted 2; `find -type f -name` counted 1.
11. `find … \| head` under `pipefail` exited 0 tonight (SIGPIPE trap DETECTED)
    — retention counts must use `find|wc -l`, never `find|head`.

## How to re-run

```sh
bash scripts/pip_only_baseline.sh
```

Requires network once for PyPI. Not a measure of this branch's source tree.
