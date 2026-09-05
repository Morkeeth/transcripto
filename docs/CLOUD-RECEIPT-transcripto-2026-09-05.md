# CLOUD-RECEIPT · transcripto · 2026-09-05

Agent: https://cursor.com/agents/bc-dc89dfc0-1c3b-431e-be03-f8247caf0026  
Branch: `cursor/review-findings-install-checks-0026` (from `origin/feat/instant-replay` @ `81a0986`)  
Base preferred for PR: `main` (note: tip is 8 commits ahead of `main`; this branch carries that tip + triage fixes)

---

## SHIPPED

What exists now that did not at the start of this run:

1. `hack.md` — seven-part contract (was missing on main and on feat tip).
2. `docs/REVIEW-FINDINGS-TRIAGE-2026-09-05.md` — each finding classified with the command that decided it.
3. `docs/CLOUD-RECEIPT-transcripto-2026-09-05.md` — this file.
4. Privacy empty-index RED guard in `test_privacy.sh` (ported from overnight `fed8`; was absent on tip).
5. Hard-fail README install-pin / `should print` checks in `test_version.sh` (control watched RED).
6. `scripts/check_consumer_integration.sh` — tip wheel → READ-CONTRACT views + ask/1 + packet/1 + coaching snapshot/compare.
7. `scripts/check_installed_package.sh` — opens **live PyPI wheel** METADATA/bytes; reports longdesc gate + version/schema collision.
8. `scripts/check_baseline_arms.sh` — tip wheel vs clean-room PyPI on the schema-7 consumer select (PyPI loses today).
9. Artifact logs under `/opt/cursor/artifacts/` (`consumer-integration*.txt`, `installed-package*.txt`, `baseline-arms.txt`, suite outputs).

Not shipped (Oscar’s click / blocked): PyPI publish, version bump off `0.2.0`, article/X, merging `fed8` retention cold-verify pack, live corpus re-derive, correction v2.

---

## VERIFIED

| Claim | Command | Result |
|---|---|---|
| Cloud main tip | `git rev-parse origin/main` | `fa15f1b…` SCHEMA 3 |
| Oscar tip | `git rev-parse origin/feat/instant-replay` | `81a0986…` SCHEMA 7 |
| Ahead/behind | `git rev-list --left-right --count origin/main...origin/feat/instant-replay` | `0 8` |
| Uncommitted local deltas on cloud | `git status --porcelain` at start | clean (divergence is branch, not dirty tree) |
| Unit tests on tip | `python3 -m unittest discover -s tests -v` (clean `HOME`) | **103 OK** |
| Shell suites | `for t in test_*.sh; do bash "$t"; done` | all PASS |
| Privacy empty RED | `git init` + `bash test_privacy.sh` | exit **1** |
| Privacy tip green | `bash test_privacy.sh` | exit **0** |
| Version pin RED | sed README pin to `0.1.3` + `bash test_version.sh` | exit **1**; restore → **0** |
| Consumer integration | `bash scripts/check_consumer_integration.sh` | **PASS** (schema 7, ask/1, packet current, coaching schemas) |
| Installed-package wheel gate | `bash scripts/check_installed_package.sh` | longdesc **green**; **collision True** (0.2.0 SCHEMA 7 vs 3) |
| Live PyPI clean-room | cwd `/tmp`, `pip install --no-cache-dir transcripto==0.2.0` | SCHEMA **3**; no tip modules; `ask --json` unrecognized |
| Naive baseline vs tip contract | `bash scripts/check_baseline_arms.sh` | tip wins; PyPI **FAIL** `no such column` |
| uvx stranger version | `uvx --from transcripto==0.2.0 transcripto --version` | `transcripto 0.2.0` |
| Helicon on tip | `helicon ci --path . --fail-on none` | **UNMEASURED** (0 memories) — not a pass |

---

## WRONG

1. **Assumed installed-package checks from `/workspace` were clean.** First `pip install transcripto==0.2.0` while cwd was the tip tree reported schema 7 + `transcripto_sources` — path leakage, not PyPI. Corrected by re-running from `/tmp` with `--no-cache-dir`. Logged in triage F8.
2. **Assumed `sessions` empty silence still present.** On tip it already speaks (“Your index is empty…”). Old finding not reproducible; nearly filed as still-open from memory.
3. **Unit tests failed twice with polluted `HOME`/`TRANSCRIPTO_DB` from earlier probes** before a clean re-run showed 103 OK. Env leakage looked like product failure.
4. **Could not open Oscar’s live corpus** — retention 504/2721 and live correction P/R remain blocked (OQ-1). Fixture/method only.
5. **No prior `REVIEW-FINDINGS-*.md` object existed** on any remote branch. Triage reconstructs from agent receipts + PR prose; adversarial Fable/Cursor finding IDs from PR #1 were not recoverable as a document — only the claim that reproduced issues were fixed at merge.
6. **Did not merge overnight `fed8` cold-verify retention scripts** — would re-theatre work the prompt said not to redo; privacy empty-index alone was ported.
7. **Left F1 version collision open** — tip still labels itself `0.2.0` while PyPI `0.2.0` is schema 3. Bumping/publishing is Oscar’s click.
8. **Correction v2 / `test_trace.sh` from trace-analysis wave are not on this tip** — still open / absent, not fixed tonight.
9. **Helicon is UNMEASURED here** — cannot be cited as health.

---

## Divergence note (cloud main ≠ Oscar disk)

Oscar’s tip is remote branch `feat/instant-replay` (`81a0986`), **8 commits ahead** of cloud/GitHub `main` (`fa15f1b`). Those commits are the overnight search / evidence / continuation / coaching work. Live PyPI `0.2.0` matches **main’s schema-3 shape**, not the tip. Cloud agent started on `main`; this work branched from Oscar’s tip so triage hit the real object.
