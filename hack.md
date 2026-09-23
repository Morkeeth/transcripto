# hack.md — Transcripto night wave 2026-09-23 (15b6)

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
  be re-derived on a cloud VM with no corpus (confirmed tonight:
  `~/.claude/projects` absent). Ship the method + an arithmetic-faithful
  fixture + an independent find↔stat oracle + a negative planter that must go
  RED + a death-rate impossibility control; Oscar re-runs `find` on his
  machine tomorrow (publish TZ; refuse invented death rate; name calendar vs
  duration).
- **OQ-2 (blocking for ship surface):** KEEP vs trim the README launch example.
  Cloud prepares the ruling with tonight's line refs; **Oscar ticks**. Do not
  guess the tick.
- **OQ-3 (Oscar only):** Article post · X post · PyPI publish. Agent does not.
- **OQ-4 (non-blocking, article honesty):** Do Desktop/Cowork transcripts under
  the same projects root inherit `desktopSessionCleanupPeriodDays` Default `0`
  (no age limit)? Docs object must be opened tonight; live CLI/Desktop mix is
  Oscar's.
- **OQ-5 (non-blocking, launch honesty):** Published PyPI `0.2.0` may lack tip
  stranger verbs and the tip `stats` anti-conflation caveat. Re-derive at the
  PyPI / wheel object tonight; do not carry yesterday's audit. Whether Oscar
  cuts a new version before article post is his click (OQ-3).

## CONSTITUTION

1. Run it; do not read it. Tick only after the done-when command executed.
2. Re-derive every number at its object. Never carry figures from this prompt
   or from an older doc into a live claim.
3. Open the bigger object. 504/2721 is **file retention by mtime** under a
   projects root (`find … ! -newermt`), **not** an authorship-gate count of
   human turns, and **not** `stats` message counts. Do not conflate.
4. A control that has not been watched going RED is not a control. Empty-input
   greens are bugs. `grep -q` on empty input is not a pass.
   `printf '%s\n' "" | wc -l` invents `1` — never trust a blank-line count.
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
10. Prior night-wave branches (`8b78`, `d229`, …) are the **floor**, not the
    plan. Re-run tonight; do not copy old PASS lines as evidence. Main at
    start lacked cold-verify docs/scripts — that gap is tonight's object.
11. Two frozen stamps (504/2721 and 579/2874) must not be allowed to print a
    daily death rate. An executable control rejects that arithmetic.
12. `test_privacy.sh` must fail closed on an empty `git ls-files`. A green
    "0 hits in 0/1 files" on outage is a defect, not a pass.
13. Ambition beyond the floor must be able to embarrass us: naive `find`
    winning retention, `stats` near-miss looking like retention, empty-index
    privacy going green on outage, published 0.2.0 missing tip verbs/caveat,
    wheel cwd-shadow, TZ/calendar traps, and a true cold clone outside the
    agent worktree — all must be watched, not narrated.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object + RED controls + beyond-floor
   traps.** NOW. Bring the under-built cold_verify path onto main tip; re-run
   at the object; capture stdout in `docs/COLD-VERIFY-2026-08-30.md`. Must
   include independent oracle (no shared 504/2721 target), negative planter
   watched RED, death-rate impossibility, empty-grep / blank-line wc traps,
   stats near-miss, stranger product journey, archive/wheel/cold-clone paths.
2. **Slice 2 — STEP 3 ruling at the README object.** Prepare keep/trim
   recommendation with tonight's `nl -ba` line refs; Oscar ticks. Do not guess.
3. **Slice 3 — STEP 0 logged.** Re-run `./test_small_n.sh` and
   `bash scripts/test_small_n.sh`; log 7/7 (or whatever the object returns)
   in the checklist footer with the command.
4. **Slice 4 — baseline arm that can embarrass us.** Document pip-install-only
   naive path vs transcripto; honest if naive wins on retention simplicity.

## NOW

**Slice 1** — cold stranger + RED controls + beyond-floor traps. hack.md exists;
product/scripts code may begin.

## LOG

- 2026-09-23T00:17Z start: `git fetch origin main` → already at `c5f5bbf`.
  Main had **no** `hack.md`, **no** `scripts/`, **no**
  `docs/ARTICLE-01-SHIP-CHECKLIST.md`, **no** `docs/COLD-VERIFY-2026-08-30.md`.
  Existing `docs/` held OFFLINE-QUICKSTART + CLOUD-RECEIPT only.
- Queue empty (`cursor-cloud-get-message-queue` → `queuedMessageCount: 0`).
- Branch: `cursor/night-wave-p1-launch-15b6`.
- START at object: `python3 -m pip install -e . -q` OK;
  `./test_small_n.sh` → **7/7 green**;
  `bash scripts/test_small_n.sh` → missing (no `scripts/` yet);
  `python3 -m unittest discover -s tests -q` → **94 OK** (re-derived).
- No live `~/.claude/projects` on this VM (OQ-1).
- Host `TZ=` unset (UTC tools). README invented demo at **L132–154**
  (`nl -ba README.md | sed -n '120,170p'`).
- `printf '' | grep -q .` → exit **1**. `printf '' | grep -qv x` → exit **1**.
- `printf '%s\n' "" | wc -l` → **1** (blank-line invents a count).
- Embarrassment at start (main, RUN): empty `git init` + copy of
  `test_privacy.sh` → `PRIVACY OK: … in 1 production/doc files` exit **0**
  (`wc -l` blank line / empty-index green-on-outage). That is tonight's
  privacy fail-closed object.
- Prior tip `8b78` @ `dc83a5b` is the **floor** — not tonight's PASS.
  Floor already ships cold_verify + docs; main never absorbed it. Tonight
  re-runs and must beat the floor on embarrassment honesty, not line count.
- hack.md written before any product/scripts code.
