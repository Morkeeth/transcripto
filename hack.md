# hack.md — Transcripto night wave 2026-09-16

## NORTH STAR

A stranger cold-clones or git-archives this repo, runs one shell command with
no key and no Oscar corpus, and re-derives the **file-age** retention method
behind "504 of 2,721 files older than 30 days" — with controls that can go
RED, a baseline arm that can beat us, a live stranger product journey on
tonight's main, and a STEP 3 README ruling ready for Oscar's morning tick.

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
- **OQ-4 (non-blocking, article honesty):** Do Desktop/Cowork transcripts under
  the same projects root inherit `desktopSessionCleanupPeriodDays` Default `0`
  (no age limit)? Live mix of CLI vs Desktop files on Oscar's machine is not
  knowable here. Docs object opened tonight; live split is Oscar's.

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
    do not copy old PASS lines as evidence. Main still lacks tonight's
    docs/scripts for this launch path — that gap is tonight's object, not a
    reason to paste yesterday's artifact.
11. Ambition beyond the floor must be able to embarrass us: naive `find`
    winning retention, `stats` near-miss looking like retention, empty-index
    privacy going green on outage, frozen quotes that do not reconcile, wheel
    cwd-shadow binding the tree, TZ pair traps, calendar↔duration deltas,
    touch↔utime planter disagreement, **published 0.2.0 missing the stats
    anti-conflation caveat**, **ensurepip/`python3 -m venv` outage looking
    green**, and a true cold clone outside the agent worktree — all must be
    watched, not narrated.
12. Preserve the approved NORTH STAR and PROMISE LINE. Do not shrink the vision
    to whatever dataset is easiest. The stranger product journey on main
    (`import-example` → `ask` → `changes` → `handoff` → `receive-handoff`) is
    in scope for verification at the object, not a side demo.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object + RED controls + stranger
   product journey + beyond-floor traps.** Riskiest. Main has no
   `scripts/cold_verify.sh`. Bring the floor from prior waves, then tonight:
   virtualenv fallback when `ensurepip` is missing; published-0.2.0 stats
   caveat absence as an embarrassment probe; true cold clone outside
   `/workspace`. Capture `docs/COLD-VERIFY-2026-08-30.md` from a RUN.
2. **Slice 2 — STEP 3 ruling at the README object.** Open
   `nl -ba README.md` tonight; write KEEP/TRIM ruling with line refs;
   Oscar boxes unticked.
3. **Slice 3 — STEP 0 logged.** Re-run `./test_small_n.sh` and
   `bash scripts/test_small_n.sh`; log 7/7 at object in checklist footer.
4. **Slice 4 — baseline arm that can embarrass us.** Document naive
   `find` / pip-only vs transcripto; honest if naive wins. Include the
   published-package caveat gap vs tip.

## NOW

**Slice 1** — cold stranger path + RED controls + beyond-floor traps.
hack.md exists; no scripts yet. Next: write `scripts/cold_verify.sh` and
related floor scripts, then RUN them.

## LOG

- 2026-09-16T18:55Z start: `git pull origin main` → already up to date at
  `c5f5bbf`. Main has **no** `hack.md`, **no** `scripts/`, **no**
  `docs/ARTICLE-01-SHIP-CHECKLIST.md`, **no** `docs/COLD-VERIFY-2026-08-30.md`.
  Existing `docs/` holds OFFLINE-QUICKSTART + CLOUD-RECEIPT only.
- Queue empty (`cursor-cloud-get-message-queue` → `queuedMessageCount: 0`).
- START: `bash scripts/test_small_n.sh` failed as expected (no `scripts/`).
  `./test_small_n.sh` → **7/7 green** (command run at object).
- `python3 -m unittest discover -s tests -q` → **94 OK** (re-derived).
- `curl`/PyPI JSON → **0.2.0** live (re-derived).
- No live `~/.claude/projects` on this VM (OQ-1).
- `python3 -m venv` fails here: `ensurepip` missing; apt has no
  `python3.12-venv` candidate. `python3 -m virtualenv` works (installed
  via `pip install --user virtualenv`). Cold verify must not paint this
  outage green — fall back or refuse with a clear FAIL.
- Prior night-wave tips on origin (latest
  `origin/cursor/night-wave-p1-cold-verify-6e6c`) are the **floor**; tonight
  re-runs and goes beyond (published caveat gap + venv outage + cold clone).
- hack.md written before any code (this file).
