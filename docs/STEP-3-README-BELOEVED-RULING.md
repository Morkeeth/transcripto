# STEP 3 — README launch-example ruling (Oscar ticks)

**Status:** cloud recommendation only. Oscar ticks KEEP or TRIM. Agent does not.

**Object opened tonight:** `README.md` lines 64–90 via
`nl -ba README.md | sed -n '64,90p'` (2026-09-14).

## What is on the page

The launch surface under **The replay** is the invented `replay --demo` block:

- L66–67: explicitly labelled invented ("All prompts and results in this example
  are invented.")
- L69–88: demo transcript text (login redirect / pytest comeback)
- L90+: heading rules for comeback / snag / missing receipt / answer

Author worst-prompt / guarded personal fragments are **absent** from the README
object tonight (`rg` for the privacy-guarded literals → no README hits; the
privacy suite itself still watches those literals elsewhere).

## Options

| option | meaning | cloud view |
|--------|---------|------------|
| **KEEP** | leave invented demo at L66–88 | **recommended** — honest label ("invented"), shows evidence contract, no author text |
| **TRIM** | shorten or drop the demo block | allowed if Oscar wants less README surface; product still has `replay --demo` |
| RESTORE author prompt | put an old personal worst-prompt back | **rejected** — privacy guard; users must not see author prompts on the front page |

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

## Tonight's line evidence (command output)

```
$ nl -ba README.md | sed -n '64,90p'
    64	## The replay
    65	
    66	This is output from `replay --demo`. **All prompts and results in this example
    67	are invented.** The demo goes through the same parser as a real transcript.
    68	
    69	```text
    70	THE COMEBACK · claude · request 1
    71	You asked: "Fix the login redirect and run its tests."
    …
    86	Recorded: 3 succeeded · 2 failed · 0 unknown
    87	Status describes a tool result, not task correctness. Missing results stay unknown.
    88	```
    89	
    90	The headings have rules. **The comeback** means a recorded failure was followed
```
