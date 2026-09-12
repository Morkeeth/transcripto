# hack.md — Transcripto night wave 2026-09-12

## NORTH STAR

A stranger cold-clones or git-archives this repo, runs one shell command with
no key and no Oscar corpus, and re-derives the **file-age** retention method
behind "504 of 2,721 files older than 30 days" — with controls that can go
RED, a baseline arm that can beat us, and a STEP 3 README ruling ready for
Oscar's morning tick.

## PROMISE LINE

**GET:** `bash scripts/cold_verify.sh` exits 0; captured output lives in
`docs/COLD-VERIFY-2026-08-30.md`; `docs/ARTICLE-01-SHIP-CHECKLIST.md` is ready
for Oscar to tick STEP 3 and the ship clicks.

**CONSTRAINT:** No outward acts (no article post, no X, no PyPI bump, no
publish). A checkbox is truth only when its done-when was RUN. Branch push +
draft PR for Oscar review is the handoff, not a public post.

## OPEN QUESTIONS

- **OQ-1 (non-blocking):** Oscar's live 504/2721 on `~/.claude/projects` cannot
  be re-derived on a cloud VM with no corpus. Ship the method + an
  arithmetic-faithful fixture + an independent find↔stat oracle + a negative
  planter that must go RED; Oscar re-runs `find` on his machine tomorrow
  (publish TZ; refuse invented death rate; name calendar vs duration).
- **OQ-2 (blocking for ship surface):** KEEP vs trim the README launch example.
  Cloud prepares the ruling with tonight's line refs; **Oscar ticks**. Do not
  guess the tick.
- **OQ-3 (Oscar only):** Article post · X post · PyPI publish. Agent does not.
- **OQ-4 (non-blocking, article honesty):** Desktop/Cowork transcripts under the
  same projects root inherit `desktopSessionCleanupPeriodDays` Default `0`
  (no age limit) per tonight's docs object. Live CLI vs Desktop mix on Oscar's
  machine is not knowable here.

## CONSTITUTION

1. Run it; do not read it. Tick only after the done-when command executed.
2. Re-derive every number at its object. Never carry figures from this prompt
   or from an older doc into a live claim.
3. Open the bigger object. 504/2721 is **file retention by mtime** under a
   projects root (`find … ! -newermt`), **not** an authorship-gate count of
   human turns, and **not** `stats` message counts. Do not conflate.
4. A control that has not been watched going RED is not a control. Empty-input
   greens are bugs. `grep -q` / `grep -qv` on empty input is not a pass.
5. No outward acts. Branch push + draft PR for Oscar review is allowed; public
   post/publish/PyPI is not.
6. Do not reorganise, rename, or start a new project.
7. A fixture that plants N and asserts N only proves the planter. Method truth
   requires an independent oracle that does not share the planted target, plus
   a negative planter that must FAIL.
8. Cold stranger means: after source install, retention + oracle + suites must
   PASS with no network. Docs/PyPI probes are separate and may use network;
   their absence must not paint retention green-by-skip.
9. A stranger path that only works with `.git` present is not fully cold —
   archive extracts must be exercised.
10. Prior night-wave branches are the floor, not the plan. Re-run tonight;
    do not copy old PASS lines as evidence. Main still lacks docs/scripts —
    that gap is tonight's object, not a reason to paste yesterday's artifact.
11. Ambition beyond the floor must be able to embarrass us: naive `find`
    winning retention, `stats` near-miss looking like retention, empty-index
    privacy going green on outage, frozen quotes that do not reconcile, wheel
    cwd-shadow binding the tree, TZ pair traps (including inverse pairs),
    calendar↔duration count deltas, touch↔utime planter disagreement,
    symlink inflation of `find` totals, death-rate laundering of two stamps —
    all must be watched, not narrated.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object + RED controls.** NOW.
   One command: fresh venv, offline core, arithmetic fixture, independent
   oracle, negative planter, empty-grep + empty-privacy RED, death-rate
   impossibility, symlink `-type f` trap, multi-TZ + pair trap, frozen-quote
   non-reconciliation, calendar↔duration, touch↔utime, stats near-miss,
   product boundary (no `retention` CLI), docs/PyPI probes separate.
   Artifact: `docs/COLD-VERIFY-2026-08-30.md`. Archive + wheel strangers.
2. **Slice 2 — STEP 3 ruling at the README object.**
   Open README with line refs; write
   `docs/STEP-3-README-BELOEVED-RULING.md`; checklist leaves Oscar ticks open.
3. **Slice 3 — STEP 0 logged.**
   Re-run `./test_small_n.sh` and `bash scripts/test_small_n.sh` at object;
   log 7/7 in checklist footer with the commands.
4. **Slice 4 — baseline arm that can embarrass us.**
   `docs/BASELINE-ARM.md` + `bash scripts/pip_only_baseline.sh` — naive `find`
   vs pip-only transcripto; honest if naive wins.

## NOW

Slice 1 — cold stranger path + RED controls + beyond-floor symlink /
death-rate / empty-grep embarrassment hunt. hack.md is this file; no other
product/scripts code exists yet on this branch.

## LOG

- 2026-09-12 ~13:07 UTC start: main tip `fa15f1b`. No `hack.md`, no `docs/`,
  no `scripts/`. Prior remotes (`night-wave-p1-cold-verify-910a`,
  `night-wave-p1-launch-fcb9`, `cold-verify-904c`, …) are the **floor** —
  evidence of what was attempted, **not** tonight's PASS. This wave re-runs
  at the object.
- Branch: `cursor/night-wave-p1-cold-verify-ebe8`.
- START: `git pull origin main` (Already up to date). System
  `pip install -e . -q` wrote to `~/.local` (PATH warning). Root
  `./test_small_n.sh` → **7/7 green**. Unit tests → **73 OK**.
- Embarrassment at start (main, RUN): empty `git init` + copy of
  `test_privacy.sh` → printed `PRIVACY OK: 0 hits in 0 tracked files` and
  exited **0**. Must fail-closed tonight.
- `grep -qv` on empty input → exit **1** (confirmed). `grep -q` on empty →
  exit **1**. Callers that treat exit 1 as CLEAN without a non-empty guard
  are broken.
- README object opened: invented demo at L66–88
  (`nl -ba README.md | sed -n '64,90p'`). Author "beloeved" text absent from
  README (privacy pattern still guards the fragment in `test_privacy.sh`).
- No live `~/.claude/projects` (OQ-1).
- PyPI JSON re-derived: **0.2.0**.
- CLI object: `transcripto` subcommands are
  `index,watch,ask,search,find,trace,sessions,stats,cost,coach,export-run,replay`
  — **no `retention`**. Naive `find` is the only honest file-age answer.
- Docs object (`curl` settings-reference.md): `cleanupPeriodDays` Default
  **30**; `desktopSessionCleanupPeriodDays` Default **0** (no age limit);
  deletion is a background sweep after a session starts.
- Host `TZ=UTC`. `python3-venv` was missing → installed `python3.12-venv`
  via apt; `python3 -m venv` now succeeds.
- Symlink probe (RUN): one real `.jsonl` + one symlink → `find -name '*.jsonl'`
  counted **2**; `find -type f` counted **1**. Symlink inflation is a live
  trap for anyone who omits `-type f`.
- hack.md written before any product/scripts code.
