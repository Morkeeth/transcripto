# hack.md — Transcripto night wave 2026-09-21 (8b78)

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
  planter that must go RED + a death-rate impossibility control; Oscar re-runs
  `find` on his machine tomorrow (publish TZ; refuse invented death rate; name
  calendar vs duration).
- **OQ-2 (blocking for ship surface):** KEEP vs trim the README launch example.
  Cloud prepares the ruling with tonight's line refs; **Oscar ticks**. Do not
  guess the tick.
- **OQ-3 (Oscar only):** Article post · X post · PyPI publish. Agent does not.
- **OQ-4 (non-blocking, article honesty):** Do Desktop/Cowork transcripts under
  the same projects root inherit `desktopSessionCleanupPeriodDays` Default `0`
  (no age limit)? Docs object must be opened tonight; live CLI/Desktop mix is
  Oscar's.
- **OQ-5 (non-blocking, launch honesty):** Published PyPI version (re-derive
  tonight) may lack tip stranger verbs and the tip `stats` anti-conflation
  caveat. README stranger flow from **source** vs `pip install transcripto==…`
  are different objects — audit at both.

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
10. Prior night-wave branches are the floor, not the plan. Re-run tonight;
    do not copy old PASS lines as evidence. Main still lacked cold-verify
    docs/scripts at start — that gap is tonight's object.
11. Two frozen stamps (504/2721 and 579/2874) must not be allowed to print a
    daily death rate. An executable control rejects that arithmetic.
12. `test_privacy.sh` must fail closed on an empty `git ls-files`. A green
    "0 hits in 0/1 files" on outage is a defect, not a pass.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object + RED controls + death-rate
   impossibility + docs desktop caveat.** Riskiest: wrong object (stats /
   authorship) masquerades as retention; empty-grep greens; planter-only
   "proof". DONE-WHEN: `bash scripts/cold_verify.sh` exits 0; artifact
   `docs/COLD-VERIFY-2026-08-30.md` contains tonight's captured stdout.
2. **Slice 2 — STEP 3 ruling at the README object.** DONE-WHEN:
   `nl -ba README.md | sed -n '128,156p'` run tonight; ruling doc with line
   refs; checklist STEP 3 boxes left **unchecked** for Oscar.
3. **Slice 3 — STEP 0 logged.** DONE-WHEN: `./test_small_n.sh` and
   `bash scripts/test_small_n.sh` both print 7/7; footer in checklist.
4. **Slice 4 — baseline arm that can embarrass us.** DONE-WHEN:
   `docs/BASELINE-ARM.md` + `bash scripts/pip_only_baseline.sh` — honest if
   naive `find` / pip-only wins on simplicity or on the wrong-object near-miss.

## NOW

**Slice 1** — cold stranger at the file object. hack.md exists; product /
scripts / artifact do not yet on this branch. Next: land privacy fail-closed,
`scripts/cold_verify.sh` (+ archive/wheel/clone strangers), run it, capture
output in `docs/COLD-VERIFY-2026-08-30.md`.

## LOG

- 2026-09-21 start: `git pull origin main` → Already up to date. Tip
  `c5f5bbf`. Branch `cursor/night-wave-p1-launch-8b78`.
- Main tip had `docs/OFFLINE-QUICKSTART.md` + `docs/CLOUD-RECEIPT-…` but
  **no** `hack.md`, **no** `scripts/`, **no** ARTICLE / COLD-VERIFY /
  BASELINE / STEP-3 docs.
- START: `python3 -m pip install -e . -q` ok (script → `~/.local/bin`).
- START: `./test_small_n.sh` → **7/7 green** (command ran).
- START: `bash scripts/test_small_n.sh` → **No such file** (scripts absent).
- Unit tests at start: `python3 -m unittest discover -s tests -q` → **94 OK**.
- PyPI at start: `curl`/urllib → **0.2.0**.
- No live `~/.claude/projects` (OQ-1).
- Embarrassment at start (main `test_privacy.sh`): empty `git init` + copy
  script → `printf` blank-line `wc -l` invents **1** production file and exits
  **0** ("PRIVACY OK"). Fail-closed missing on main. Watched RED by hand before
  any fix: `cd $(mktemp -d) && git init && cp …/test_privacy.sh . && bash
  test_privacy.sh` → exit 0 with "1 production/doc files".
- Prior remotes (esp. `cursor/night-wave-p1-launch-0583`) are the **floor** —
  evidence of what was attempted, **not** tonight's PASS. Re-run required.
- hack.md written before product/scripts code (this commit).
