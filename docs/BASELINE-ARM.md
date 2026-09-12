# Baseline arm — naive path vs transcripto

The ambitious question is not "does transcripto work?" It is "is it better
than the alternative a competent team builds in two hours?"

Tonight's baseline is **pip install only** (PyPI `transcripto==0.2.0`) plus
a naive `find` for file ages. Script: `bash scripts/pip_only_baseline.sh`.

## Arm A — file-age retention

| arm | what it does | tonight (RUN) |
|-----|--------------|---------------|
| Naive `find` | `find ROOT -type f -name '*.jsonl' ! -newermt <30d>` | **504 of 2721** — answers the object |
| Pip-only transcripto | `transcripto retention` / help scan | **exit 2** — no such command; help has no file-age verb |
| Pip-only `stats` | message counts on the retention fixture | prints `2,721 of the 2,721 messages … 100.0%` — **near-miss DETECTED** |

**Ruling: naive `find` wins retention.** Pip-only transcripto cannot answer
file-age. Quoting `stats` as retention evidence would be the wrong object.

## Arm B — authorship gate (separate object)

| arm | tonight (RUN) |
|-----|---------------|
| Naive `type:user` count on `fixtures-coach` | **12** |
| Pip-only `coach` `human_turns` | **8** |

Naive wins simplicity. Pip-only gate is stricter (expected). This is **not**
the retention story — do not conflate.

## Embarrassment list

1. Product cannot answer the article's central figure without shell `find`.
2. `stats` on a 2721-file fixture prints the retention denominator as a
   typed-message count — looks like confirmation, is not.
3. Wheel cwd-shadow: `import transcripto` from the repo cwd binds the tree,
   not the installed wheel (`cwd_shadow_trap: DETECTED` in
   `scripts/wheel_stranger.sh`).
4. Empty-index privacy on main was green until tonight's fail-closed fix.

## How to re-run

```sh
bash scripts/pip_only_baseline.sh
```

Requires network once for PyPI. Not a measure of this branch's source tree.
