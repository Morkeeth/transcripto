# STEP 3 — README launch-example ruling

**Cloud recommendation (2026-09-08): KEEP the current invented replay demo.**

Oscar ticks KEEP or TRIM on `docs/ARTICLE-01-SHIP-CHECKLIST.md` tomorrow.
This file is the evidence packet, not the tick.

## Object opened tonight

Commands:

```sh
nl -ba README.md | sed -n '64,88p'
rg -n 'NO-DURABLE|worst looped' README.md || true
```

Observed at `README.md:64–88` (via `nl -ba README.md | sed -n '64,88p'`):

- Heading `## The replay` (L64)
- Explicit label: all prompts and results in the example are **invented** (L66–67)
- Demo block: `THE COMEBACK · claude · request 1` with
  `You asked: "Fix the login redirect and run its tests."` (L69–88)
- Closing: `Recorded: 3 succeeded · 2 failed · 0 unknown` (L86)

`rg` for old author-prompt markers (`NO-DURABLE`, `worst looped`)
in `README.md`: **0 hits**. Tonight the same search including the
privacy-guarded author fragment also returned **0 hits** (fragment not
restated here — naming it in a public doc is itself a disclosure).

## What changed since older rulings

Earlier ship checklists cited `README.md:79-81` (and sometimes `:64-66`) for an
author worst-prompt example. Those line refs are **stale on current main**.
Opening the object tonight shows the launch surface is the **invented**
`replay --demo` block at **L66–88**, not an author prompt.

Restoring the author prompt is **blocked** by `test_privacy.sh` (the
guarded author-prompt phrases it scans for). Do not recommend RESTORE.

## Recommendation

| option | meaning | cloud view |
|--------|---------|------------|
| **KEEP** | leave invented demo at L66–88 | **recommended** — honest label ("invented"), shows evidence contract, no author text |
| **TRIM** | shorten or drop the demo block | allowed if Oscar wants less README surface; product still has `replay --demo` |
| RESTORE author prompt | put the old worst-prompt back | **rejected** — privacy guard; users must not see author prompts on the front page |

## Why KEEP

1. The demo is explicitly labelled invented (L66–67).
2. It exercises the real parser (`replay --demo`) — same evidence contract the
   tool ships.
3. Author text is already scrubbed; KEEP preserves that scrub.
4. Article 01 / launch posts that still quote an older cut are Oscar's edit
   problem on those drafts, not a reason to re-pollute the README.

## Oscar tick (do not guess)

On the checklist:

- `[ ] Oscar: keep invented replay demo (README.md:66–88) — recommended`
- `[ ] Oscar: or trim the demo further`

No code change is required for KEEP.
