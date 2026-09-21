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
  tonight) lacks tip stranger verbs (`import-example` / `changes` / `handoff` /
  `receive-handoff` / `import-lab` / `quickstart`) and the tip `stats`
  anti-conflation caveat. README stranger flow works from **source**;
  `pip install transcripto==0.2.0` is a different object.

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
    docs/scripts at start — that gap was tonight's object.
11. Two frozen stamps (504/2721 and 579/2874) must not be allowed to print a
    daily death rate. An executable control rejects that arithmetic.
12. `test_privacy.sh` must fail closed on an empty `git ls-files`. A green
    "0 hits in 0/1 files" on outage is a defect, not a pass.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object + RED controls + death-rate
   impossibility + docs desktop caveat.** DONE.
   Ran `bash scripts/cold_verify.sh` → `cold_verify: PASS`,
   `death_rate_impossible: PASS`, `empty_grep_control: PASS`,
   `independent_oracle: PASS` (87/40, seed 20260921), `negative_planter: PASS`,
   `offline_core: PASS`, docs dual-gate + desktop immortal,
   `pypi_package_audit: PASS`, `published_verb_gap: DETECTED`,
   `published_stats_caveat: ABSENT`. Artifact:
   `docs/COLD-VERIFY-2026-08-30.md`.
2. **Slice 2 — STEP 3 ruling at the README object.** DONE.
   `nl -ba README.md | sed -n '128,156p'` → invented demo L132–154;
   `docs/STEP-3-README-BELOEVED-RULING.md` recommends KEEP; checklist unchecked.
3. **Slice 3 — STEP 0 logged.** DONE.
   `./test_small_n.sh` and `bash scripts/test_small_n.sh` → 7/7 in checklist
   footer.
4. **Slice 4 — baseline arm that can embarrass us.** DONE.
   `docs/BASELINE-ARM.md` + `bash scripts/pip_only_baseline.sh` — naive `find`
   wins retention; pip-only `retention` exit 2; stats 2721/2721 near-miss
   DETECTED; gate 8 vs naive 12; archive + wheel + cold-clone strangers PASS;
   cwd-shadow DETECTED; PyPI wheel has no cold_verify; verb gap DETECTED.

## NOW

Done. Slices 1–4 shipped. Oscar morning clicks: STEP 3 KEEP/TRIM, live
`find` re-derive (with TZ + Desktop mix check), article/X/PyPI.

## LOG

- 2026-09-21T00:07Z start: `git pull origin main` ok; branch
  `cursor/night-wave-p1-launch-0583`. Main tip `c5f5bbf` had
  `docs/OFFLINE-QUICKSTART.md` + `docs/CLOUD-RECEIPT-…` but **no** `hack.md`,
  **no** `scripts/`, **no** ARTICLE/COLD-VERIFY/BASELINE/STEP-3 docs.
- START: `./test_small_n.sh` → **7/7 green** (command ran).
- `python3 -m pip install -e . -q` ok (script lands in `~/.local/bin`).
- Unit tests at start: **94 OK**.
- PyPI JSON at start: **0.2.0**.
- No live `~/.claude/projects` (OQ-1).
- Docs object opened at start (`curl` settings-reference.md):
  `cleanupPeriodDays` **Default: `30`**;
  `desktopSessionCleanupPeriodDays` **Default: `0`** (no age limit);
  deletion is a **background sweep after a session starts**; Desktop dual-gate
  with `cleanupPeriodDays`.
- Embarrassment at start (main `test_privacy.sh`): empty `git init` + copy
  script → `printf` blank-line `wc -l` invents **1** production file and exits
  **0** ("PRIVACY OK"). Fail-closed was missing on main.
- Prior remotes (esp. `cursor/night-wave-p1-launch-d229`) are the **floor** —
  evidence of what was attempted, **not** tonight's PASS.
- hack.md written before product/scripts code; committed; pushed.
- Slice 1: privacy fail-closed; `scripts/cold_verify.sh` with offline core,
  oracle (seed 20260921), negative planter, death-rate impossibility,
  empty-grep + blank-line wc, symlink inflation, boundary, TZ pair trap,
  stats near-miss, docs dual-gate, PyPI package audit + verb/caveat gaps,
  stranger product journey. `bash scripts/cold_verify.sh` → **PASS**
  (captured in `docs/COLD-VERIFY-2026-08-30.md`).
- Oracle tonight: old30=**87**, old45=**40** (not carried from prior waves).
- Death-rate: frozen delta old +75 / total +153 → laundered "75 deaths"
  FORBIDDEN.
- Stats near-miss: `2,721 of the 2,721 messages … 100.0%` DETECTED; tip caveat
  PRESENT; published ABSENT.
- duration_vs_calendar counted_by_bang_newermt=**0** tonight.
- TZ: **divergence OBSERVED** — LA `2026-08-21` vs UTC/Tokyo/London
  `2026-08-22`; pair trap DETECTED.
- Archive stranger → **PASS**. Wheel stranger → **PASS** (cwd shadow
  DETECTED). Cold clone → **PASS**. pip-only baseline → **PASS** (naive find
  wins).
- Slice 2: README L132–154 invented demo; KEEP ruling; Oscar ticks open.
- Slice 3: both small-n paths **7/7**; logged in checklist footer.
- Slice 4: baseline doc + pip_only; PyPI wheel audit 0 cold_verify hits;
  published verb gap DETECTED.
- Unit tests after: **94 OK**.
- README Development points at `bash scripts/cold_verify.sh`.
- `test_privacy_empty_index.sh` added to the matrix via `test_*.sh` glob.
- ensurepip absent on host → `venv_partial_without_pip: DETECTED`;
  virtualenv fallback used.
- Remote stranger clone of this branch → `bash scripts/cold_verify.sh` → **PASS**.
