# hack.md — Transcripto remaining · review findings + install checks

## NORTH STAR

Prove what is true about Transcripto tonight: triage every open review finding against the tip Oscar is actually building, log consumer and installed-package checks at their objects, and leave a receipt a stranger can re-run.

## PROMISE LINE

A stranger gets a triage doc where every finding is fixed / still open / not reproducible with the command that decided it, plus logged consumer-integration and installed-package checks — without publishing, yanks, history rewrites, or guessing Oscar’s disk.

## OPEN QUESTIONS

- **OQ-1 (blocking for live corpus claims):** Oscar’s `~/.claude/projects` is not on this VM. Live retention (504/2721) and live correction P/R cannot be re-derived here. Fixture/method checks only.
- **OQ-2 (blocking for ship surface):** STEP 3 KEEP vs TRIM on the invented README demo is Oscar’s tick. Prior overnight ruling exists on `cursor/night-wave-p1-cold-verify-fed8`; not re-decided here.
- **OQ-3 (non-blocking):** Desktop/Cowork `desktopSessionCleanupPeriodDays` default is a separate object from CLI `cleanupPeriodDays`. Not re-derived tonight unless that object is opened.
- **OQ-4 (non-blocking):** Whether empty-index `sessions` should exit non-zero vs speak loudly is a product call once the current tip’s behaviour is measured.

## CONSTITUTION

1. A box is truth only when its done-when was RUN. Tick → name the command.
2. Run it; do not read it. Defects are found by executing.
3. A control that has not been watched going RED is not a control.
4. Never carry a number from a prompt or prior receipt. Re-derive at the object.
5. Never rank by title or name. Open the object (wheel METADATA, branch tip, DB view).
6. No history rewrite, force-push, yank, visibility rename, or `uv publish`.
7. Outward acts (PyPI bump, article, X, public post) are Oscar’s click.
8. Do not redo overnight search / evidence timelines / continuation packets / frozen comparisons as theater.
9. Do not start a new project or reorganise the tree for comfort.

## PLAN

1. **Slice 1 (riskiest):** Inventory the three objects — cloud `main`, Oscar tip `feat/instant-replay` (this branch base), live PyPI `0.2.0` wheel — and write ahead/behind + schema/module divergence from measured commands. Without this, every later “fixed” claim may target the wrong tree.
2. **Slice 2:** Reconstruct the independent-review / overnight finding set; re-run each against the current tip; classify fixed / still open / not reproducible with commands → `docs/REVIEW-FINDINGS-TRIAGE-2026-09-05.md`.
3. **Slice 3:** Fix only findings that reproduce on this tip and are in lane (privacy empty-index RED, version/install hard-fail, consumer honesty gaps). Leave Oscar ticks and live-corpus blockers open.
4. **Slice 4:** Consumer integration check at `READ-CONTRACT.md` objects (read-only DB views + ask/packet/coach JSON shapes) against an installed tip wheel — log it.
5. **Slice 5:** Installed-package check (build wheel + `pip`/`uvx`/`pipx` path; open live PyPI wheel METADATA) — no publish — log it.
6. **Slice 6:** `docs/CLOUD-RECEIPT-transcripto-2026-09-05.md` with SHIPPED / VERIFIED / WRONG.

## NOW

**Done for this wave:** slices 1–6 complete enough to ship the triage + checks. Remaining Oscar ticks are OQ-1/2/3 and F1 version bump/publish — not agent scope.

## LOG

- 2026-09-05: No `hack.md` on cloud `main` or `feat/instant-replay`. First deliverable: this file. No product code written before it existed.
- 2026-09-05: `git rev-parse origin/main` → `fa15f1b…`; `origin/feat/instant-replay` → `81a0986…`; `git rev-list --left-right --count origin/main...origin/feat/instant-replay` → `0 8` (main behind tip by 8 commits).
- 2026-09-05: Live PyPI wheel opened: version `0.2.0`, `SCHEMA_VERSION` in wheel `transcripto.py` = **3**, top-level modules = `transcripto`, `transcripto_core`, `transcripto_replay` only. Tip on this branch: `SCHEMA_VERSION` = **7**, seven `py-modules`. Same marketed version, different object.
- 2026-09-05: Overnight branch `cursor/night-wave-p1-cold-verify-fed8` (`1121014`) has cold-verify docs + privacy empty-index RED; not merged to main or feat tip.
- 2026-09-05: Slice 2–5 RAN. Privacy empty-index watched RED then fixed. `test_version` install-pin watched RED then hardened. `scripts/check_consumer_integration.sh` PASS. `scripts/check_installed_package.sh` longdesc green + collision True. Naive PyPI arm FAIL on schema-7 select.
- 2026-09-05: First pip/uvx import from `/workspace` falsely showed tip modules on “PyPI” install — re-derived clean-room from `/tmp`.
- 2026-09-05: Docs shipped: `docs/REVIEW-FINDINGS-TRIAGE-2026-09-05.md`, `docs/CLOUD-RECEIPT-transcripto-2026-09-05.md`.
- 2026-09-05: `bash scripts/check_baseline_arms.sh` → tip wins consumer contract; live PyPI 0.2.0 loses schema-7 select.
