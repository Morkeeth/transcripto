# hack.md — Transcripto night wave 2026-09-06

## NORTH STAR

A stranger cold-clones this repo, runs one shell command with no key and no
Oscar corpus, and re-derives the **file-age** retention method behind
"504 of 2,721 files older than 30 days" — plus STEP 0, a baseline arm that can
beat us, and a STEP 3 README ruling ready for Oscar's morning tick.

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
  arithmetic-faithful fixture + an independent find↔stat oracle; Oscar re-runs
  `find` on his machine tomorrow.
- **OQ-2 (blocking for ship surface):** KEEP vs trim the README launch example.
  Cloud prepares the ruling; **Oscar ticks**. Do not guess the tick.
- **OQ-3 (Oscar only):** Article post · X post · PyPI publish. Agent does not.

## CONSTITUTION

1. Run it; do not read it. Tick only after the done-when command executed.
2. Re-derive every number at its object. Never carry figures from this prompt
   or from an older doc into a live claim.
3. Open the bigger object. 504/2721 is **file retention by mtime** under a
   projects root (`find … ! -newermt`), **not** an authorship-gate count of
   human turns. Do not conflate the two.
4. A control that has not been watched going RED is not a control. Empty-input
   greens are bugs.
5. No outward acts. Branch push + draft PR for Oscar review is allowed; public
   post/publish/PyPI is not.
6. Do not reorganise, rename, or start a new project.
7. Privacy stays green on the real tree; the privacy guard itself must fail
   closed on an empty index.
8. A fixture that plants N and asserts N only proves the planter. Method truth
   requires an independent oracle (find vs Python mtime) that does not share
   the planted target.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object + independent oracle.**
   Risk: circular 504/2721 planter/assert, wrong-object conflation, green-on-outage.
   Done-when: `bash scripts/cold_verify.sh` exits 0; prints `ratio_30d: 504 of 2721`,
   `independent_oracle: PASS`, `anti_conflation: PASS`; output captured in
   `docs/COLD-VERIFY-2026-08-30.md`.
2. **Slice 2 — STEP 3 ruling at the README object.**
   Done-when: `docs/STEP-3-README-BELOEVED-RULING.md` exists with line refs from
   `sed`/`rg` tonight; checklist STEP 3 boxes unchecked for Oscar.
3. **Slice 3 — STEP 0 logged.**
   Done-when: `./test_small_n.sh` and `bash scripts/test_small_n.sh` → 7/7 in
   checklist footer with command cited.
4. **Slice 4 — baseline arm that can embarrass us.**
   Done-when: `docs/BASELINE-ARM.md` measures naive `find` vs transcripto on
   retention, and naive authorship vs gate on fixtures-coach; honest if naive wins.

## NOW

**Slice 1** — cold stranger script + independent find↔stat oracle +
embarrassment hunt on the retention claim. No other slice until this one's
done-when has been RUN.

## LOG

- 2026-09-06 start: main has no `hack.md`, no `docs/`, no `scripts/`. Prior
  night-wave branch `cursor/night-wave-p1-cold-verify-fed8` has a floor; this
  wave treats that as the floor, not the plan — add independent oracle so
  planted 504/2721 is not the only PASS path.
- `python3 -m venv` required `apt install python3.12-venv` (was missing).
- No live `~/.claude/projects` on this VM (OQ-1).
- hack.md written before any code.
