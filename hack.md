# hack.md — Transcripto night wave 2026-09-19

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
  (no age limit)? Must open the docs object tonight; live CLI/Desktop mix is
  Oscar's.
- **OQ-5 (non-blocking, launch honesty):** Published PyPI `0.2.0` (re-derived
  tonight) lacks `import-example` / `changes` / `handoff` / `receive-handoff` /
  `import-lab` / `quickstart` and any tip `stats` anti-conflation caveat.
  README stranger flow works from **source** (`.`); `pip install transcripto==0.2.0`
  alone cannot run it. Whether Oscar cuts 0.2.1 before article post is his click
  (OQ-3). Do not bump PyPI from this agent.

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
    privacy going green on outage (including `wc -l` inventing "1 file" from a
    blank line), frozen quotes that do not reconcile, wheel cwd-shadow binding
    the tree, TZ pair traps, calendar↔duration deltas, touch↔utime planter
    disagreement, **published 0.2.0 missing tip stranger verbs and the stats
    caveat**, **`python3 -m venv` leaving python without pip**, and a true cold
    clone outside the agent worktree — all must be watched, not narrated.
12. Preserve the approved NORTH STAR and PROMISE LINE. Do not shrink the vision
    to whatever dataset is easiest. The stranger product journey on main
    (`import-example` → `ask` → `changes` → `handoff` → `receive-handoff`) is
    in scope for verification at the object, not a side demo.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object + RED controls + stranger
   product journey + beyond-floor traps.** (riskiest: wrong object / green on
   outage / planter-only "proof")
2. **Slice 2 — STEP 3 ruling at the README object** with tonight's line refs;
   Oscar ticks; agent does not guess.
3. **Slice 3 — STEP 0 logged:** re-run `test_small_n.sh` 7/7 at object; footer
   on the checklist names the command.
4. **Slice 4 — baseline arm** that can embarrass us: pip-install-only + naive
   `find` vs transcripto; honest if naive wins.

## NOW

**Slice 1.** Write and run `scripts/cold_verify.sh` (and the archive / wheel /
cold-clone wrappers) until `cold_verify: PASS` at the object with RED controls
watched, stranger product journey PASS, and capture output into
`docs/COLD-VERIFY-2026-08-30.md`. Do not advance to Slice 2 until Slice 1's
done-when has been RUN.

## LOG

- 2026-09-19T12:15Z start on `main` @ `c5f5bbf`. `git pull origin main` →
  already up to date. Main had **no** `hack.md`, **no** `scripts/`, **no**
  `docs/ARTICLE-01-SHIP-CHECKLIST.md`, **no** `docs/COLD-VERIFY-2026-08-30.md`.
  Existing `docs/` held OFFLINE-QUICKSTART + CLOUD-RECEIPT only.
- Queue empty (`cursor-cloud-get-message-queue` → `queuedMessageCount: 0`).
- Branch: `cursor/night-wave-p1-launch-d229`.
- START at object: `python3 -m pip install -e . -q` then `./test_small_n.sh`
  → **7/7 green**. `bash scripts/test_small_n.sh` → missing (no `scripts/` yet).
- `python3 -m unittest discover -s tests -q` → **94 OK** (re-derived).
- `curl`/PyPI JSON → **0.2.0** live (re-derived). Wheel audit: missing
  `import-example,changes,handoff,receive-handoff,import-lab,quickstart`;
  tip stats caveat string **ABSENT** in published wheel; also **ABSENT** on
  main tip `transcripto.py` tonight.
- No live `~/.claude/projects` on this VM (OQ-1).
- Host `TZ=` empty (UTC tools). README invented demo at **L132–154**
  (`nl -ba README.md | sed -n '128,156p'`).
- `printf '' | grep -q .` → exit **1**. `printf '' | grep -qv x` → exit **1**.
- Embarrassment at start (main, RUN):
  - Empty `git init` + copy of `test_privacy.sh` →
    `PRIVACY OK: … in 1 production/doc files` exit **0**
    (`printf '%s\n' "" | wc -l` → **1** invents a file count).
  - `python3 -m venv` → ensurepip missing, exit **1**, left `bin/python`
    without pip (`ModuleNotFoundError: No module named 'pip'`).
  - Published wheel lacks tip stranger verbs; tip lacks file-age caveat.
- Prior tips (`47f3` @ `c5874bb`, …) are the **floor** — not tonight's PASS.
  hack.md written before any product/scripts code.
