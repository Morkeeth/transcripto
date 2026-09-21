# hack.md — Transcripto night wave 2026-09-21

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
  (no age limit)? Docs object opened tonight (`settings-reference.md` →
  Default `0` **and** dual-gate with `cleanupPeriodDays` Default `30`); live
  CLI/Desktop mix is Oscar's.
- **OQ-5 (non-blocking, launch honesty):** Published PyPI `0.2.0` (re-derived
  tonight) may lack tip stranger verbs and/or the tip `stats` anti-conflation
  caveat. README stranger flow works from **source** (`.`); `pip install
  transcripto==0.2.0` is a different object — measure it, do not assume.

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
    do not copy old PASS lines as evidence. Main still lacks docs/scripts for
    cold verify — that gap is tonight's object, not a reason to paste
    yesterday's artifact.
11. Two frozen stamps (504/2721 and 579/2874) must not be allowed to print a
    daily death rate. An executable control rejects that arithmetic.
12. `test_privacy.sh` must fail closed on an empty `git ls-files`. A green
    "0 hits in 0/1 files" on outage is a defect, not a pass.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object + RED controls + death-rate
   impossibility + docs desktop caveat.** NOW.
   Deliverable: `scripts/cold_verify.sh` + `docs/COLD-VERIFY-2026-08-30.md`
   with tonight's command output. Floor: prior `night-wave-p1-launch-d229`.
2. **Slice 2 — STEP 3 ruling at the README object.**
   `nl -ba README.md` on tonight's tip; ruling doc; checklist unchecked.
3. **Slice 3 — STEP 0 logged.**
   `./test_small_n.sh` and `bash scripts/test_small_n.sh` → 7/7 in checklist
   footer (START already showed 7/7 on `./test_small_n.sh` tonight).
4. **Slice 4 — baseline arm that can embarrass us.**
   `docs/BASELINE-ARM.md` + `bash scripts/pip_only_baseline.sh` — honest if
   naive `find` wins retention / pip-only cannot reproduce cold_verify.

## NOW

**Slice 1** — land cold_verify + privacy fail-closed + capture COLD-VERIFY
artifact by running the script. Do not tick PASS from a prior wave.

## LOG

- 2026-09-21T00:07Z start: `git pull origin main` ok; branch
  `cursor/night-wave-p1-launch-0583`. Main tip `c5f5bbf` has
  `docs/OFFLINE-QUICKSTART.md` + `docs/CLOUD-RECEIPT-…` but **no** `hack.md`,
  **no** `scripts/`, **no** ARTICLE/COLD-VERIFY/BASELINE/STEP-3 docs.
- START: `./test_small_n.sh` → **7/7 green** (command ran).
- `python3 -m pip install -e . -q` ok (script lands in `~/.local/bin`).
- Unit tests at start: **94 OK** (`python3 -m unittest discover -s tests -q`).
- PyPI JSON at start: **0.2.0** (`curl …/pypi/transcripto/json`).
- No live `~/.claude/projects` (OQ-1).
- Docs object opened at start (`curl` settings-reference.md):
  `cleanupPeriodDays` **Default: `30`**;
  `desktopSessionCleanupPeriodDays` **Default: `0`** (no age limit);
  deletion is a **background sweep after a session starts**; Desktop dual-gate
  with `cleanupPeriodDays`.
- Embarrassment at start (main `test_privacy.sh`): empty `git init` + copy
  script → `printf` blank-line `wc -l` invents **1** production file and exits
  **0** ("PRIVACY OK"). Fail-closed is missing on main; prior waves fixed it
  off-main and it never landed.
- Prior remotes (esp. `cursor/night-wave-p1-launch-d229`) are the **floor** —
  evidence of what was attempted, **not** tonight's PASS.
- hack.md written before product/scripts code.
