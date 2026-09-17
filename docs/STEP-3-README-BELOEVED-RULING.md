# STEP 3 — README launch example ruling (Oscar ticks)

**Cloud recommendation: KEEP** the invented `replay --demo` block.
**Oscar ticks.** Agent does not guess the tick and does not post.

Measured at the README object tonight (`nl -ba README.md | sed -n '128,156p'`,
2026-09-17 ~08:19 UTC, tip `0b1cc06`).

## What is on the page right now

`README.md` L130–154 (via `nl -ba README.md | sed -n '128,156p'`):

- Heading `## The replay` (L130)
- Explicit label: all prompts and results in the example are **invented** (L132–133)
- Demo block: `THE COMEBACK · claude · request 1` with
  `You asked: "Fix the login redirect and run its tests."` (L135–154)
- Closing: `Recorded: 3 succeeded · 2 failed · 0 unknown` (L152)

`rg` for old author-prompt markers (`NO-DURABLE`, `worst looped`)
in `README.md`: **0 hits**. A search that includes the privacy-guarded
author fragment is intentionally not restated here — naming that fragment
in a public ruling is itself a disclosure (caught on a prior night-wave
branch when the ruling quoted the guard pattern).

## What changed since older rulings

Earlier ship checklists cited `README.md:79-81`, `:64-66`, or `:66-88` for an
author worst-prompt example or an older demo cut. Those line refs are **stale
on current main**. Opening the object tonight shows the launch surface is the
**invented** `replay --demo` block at **L132–154**, not an author prompt.

Restoring the author prompt is **blocked** by `test_privacy.sh` (the
guarded author-prompt phrases it scans for). Do not recommend RESTORE.

## Recommendation

| option | meaning | cloud view |
|--------|---------|------------|
| **KEEP** | leave invented demo at L132–154 | **recommended** — honest label ("invented"), shows evidence contract, no author text |
| **TRIM** | shorten or drop the demo block | allowed if Oscar wants less README surface; product still has `replay --demo` |
| RESTORE author prompt | put the old worst-prompt back | **rejected** — privacy guard; users must not see author prompts on the front page |

## Why KEEP

1. The demo is explicitly labelled invented (L132–133).
2. It exercises the real parser (`replay --demo`) — same evidence contract the
   tool ships.
3. Author text is already scrubbed; KEEP preserves that scrub.
4. Article 01 / launch posts that still quote an older cut are Oscar's edit
   problem on those drafts, not a reason to re-pollute the README.

## Oscar tick (do not guess)

On the checklist:

- `[ ] Oscar: keep invented replay demo (README.md:132–154) — recommended`
- `[ ] Oscar: or trim the demo further`

No code change is required for KEEP.
