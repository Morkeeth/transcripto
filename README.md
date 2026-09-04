# transcripto

**wait, my agent has been writing all of this down?**

it has. every session, to a `.jsonl` file on your disk, since the day you installed it.
nobody told you and there is no UI for it.

on the machine this was built on that is **2.0 GB across 3,731 transcripts and 1,188
project folders**, going back to the day the tool was installed. it is the most detailed
record of how you actually work that exists anywhere, and it has never been read once.

then the part that made this a tool instead of a curiosity. of **504,785 records in there,
4,261 are turns a human typed. 0.84 percent.** everything else is the machine talking to
itself. so the thing you would actually want to look at is under a hundredth of the pile,
and there is no way to scroll to it.

**transcripto indexes it, throws away everything you did not type, and grades what is left:
which of your prompts produced work that survived, and which produced work you threw away.**

one command, no account, no signup, no cloud. it reads files that are already on your disk
and never opens a socket.

> those numbers are one machine, read on 2026-09-04 with the commands in this README. yours
> will differ. the 0.84 percent is the one worth checking on your own disk first.

```
uvx transcripto coach
```

> **which build you got.** `uvx transcripto --version` should print **0.1.5**. If it prints
> **0.1.4** you have the build whose `coach` ranked habits it could not tell apart, printing
> them under "do more of these" when their 95% interval straddled your own baseline. If
> `--version` is not a recognised flag at all you are on 0.1.1, which predates `trace`, Cursor
> support and this README. `uvx --refresh transcripto` forces a fresh resolve past uv's cache.
>
> The repo always matches this README and needs nothing installed:
>
> ```
> git clone https://github.com/Morkeeth/transcripto && cd transcripto
> python3 transcripto.py coach
> ```

## three harnesses, one instrument

```
transcripto coach                     # Claude Code, ~/.claude/projects
transcripto coach --harness codex     # Codex, ~/.codex
transcripto coach --harness cursor    # Cursor, ~/.cursor/projects/*/agent-transcripts
```

**Authorship is not the same gate in all three, and the tool says so rather than pooling them.**
Claude Code stamps `promptSource: typed`, which is the measured-reliable signal: about 95% of raw
`type: user` records are not the operator at all. Cursor has no such field. Its one honest
equivalent is the `<user_query>` wrapper it puts around a submitted prompt, which injected and
tool-result records do not carry. That is a weaker signal and it is labelled weaker.

## `trace` — what actually happened after you asked

`ask` shows what you typed. `find` shows what a file went through. Neither answers the
question that matters after the fact: **you asked for X, did anything durable happen?**

```
transcripto trace "the gate"
```

It walks each of your matching prompts forward inside its own session and lists the writes
and edits that followed, stopping at your next prompt so one turn cannot claim the next
turn's work. Green dot = something durable landed. Red = nothing was touched.

**Honest limit:** a write following a prompt in the same session is CO-OCCURRENCE, not proof
the write was caused by that prompt or that it was correct. Same proxy `coach` uses, labelled
the same way.

## what you get back

this is a real run on one machine, 2026-08-31. The numbers are unedited; the two quoted prompts are synthetic stand-ins of the same shape, because your prompts never leave your machine and neither do mine:

```

  YOUR PROMPT HABITS, GRADED   (offline, your machine only)

  - your worst looped prompt, with its witness:
      "hmm ok lets just try again and see if it works this time, same thing as before but…"
      NO-DURABLE-RECORD: read-only Bash only, no file change  ·  corrections: 15  ·  assistant turns: 221

  + your best landed prompt, with its witness:
      "TERMINAL 3 — parser · ~/CODE/demo Read hack.md. Fix the counter, run the suite, commit if green…"
      COMMIT-WITNESSED: git commit  ·  corrections: 0

  SURVIVAL IS A PROXY: survival = a durable Write/Edit or an un-reverted git commit in-episode. A PROXY, not proof the work was correct or shipped.

  SURVIVES MOST  do more of these:
     65%  (71/110)  states-a-check-or-done-condition
     64%  (178/276)  detailed (>40 words)
     59%  (22/37)  no-object (pronoun/vague)
     59%  (451/763)  intent:CHANGE
     57%  (106/187)  cites-a-file-or-path

  SURVIVES LEAST  these tend to loop:
     31%  (4/13)  intent:REVERT
     40%  (451/1129)  intent:none
     42%  (320/765)  terse (<8 words)
     42%  (81/192)  intent:DESCRIBE
     45%  (5/11)  intent:TEST

  harness claude  ·  2957 transcript(s), 431,085 records  ·  3969 typed by you (0.92%)
  episodes: 2108 ranked, 992 survived (47%)
  commit 454  ·  write/edit 538  ·  reverted 2  ·  nothing durable 1114

  ─────────────────────────────────────────────────────────
   compare yours. numbers only, nothing from your prompts:

   transcripto coach · claude · 2108 episodes · 47% survived
   states-a-check-or-done-condition    65%  (71/110)
   intent:none                         40%  (451/1129)
   gap                                 1.6x
  ─────────────────────────────────────────────────────────
```

those are my numbers on that date, and they move every session i run, so treat
them as a snapshot rather than a constant. yours will be different, which is the
whole point. the last two lines are the ones that sting: it hands you back your
own best and worst prompt, verbatim, with the receipt for why it scored each one.

on that machine, on that date, prompts that wrote down what done looks like
survived **63% of the time (66 of 104)**. prompts with no stated intent survived
**39% (411 of 1043)**. i had spent a year blaming the model.

one day later, 2026-08-29, the same command on the same machine read 63% (67 of
107) and 40% (424 of 1072) over 2,874 transcripts. the percentages held and the
denominators moved, which is what a snapshot is supposed to do.

## the proxy caveat, which travels with every number

an episode "survived" if a Write or Edit landed, or a git commit ran and nothing
reverted it inside the same transcript.

that is a durable **keystroke**, not a durable **outcome**. a commit is not proof
the code was right. a revert in a later session is invisible to it. a prompt
whose payoff was a decision rather than an edit reads as dead. it is a coaching
signal, not a verdict. if it ever prints something that flatters you, distrust it.

the caveat is printed in the output itself, every run, on purpose.

## correction rate

> in the repo since 2026-09-02, not yet on PyPI. `python3 transcripto.py coach` prints it.

one more line under the coach footer:

```
  correction rate: 6% measured (227 of 4061 typed turns) · v1 catches ~1 in 6, so the real rate is ~26-37%
```

**correction rate = typed turns that correct the agent ÷ typed turns.** the denominator
is the same authorship gate as every other number here (`typed` or `queued`, never
`isMeta`, `isSidechain` or a tool result), so a tool result that happens to say "wrong"
cannot move it. a typed turn counts as a correction when a **marker** fires in its head:
the first 80 words after URLs and file paths are stripped, case-insensitive, whole-word:
a leading or bare `no`, `again`, `wrong`, `not that`, `I meant`, `revert`, `undo`, `stop`,
`instead`, plus a few measured additions. whole-word, so "against" is not "again" and
"now" is not "no". the v0 "nudge" rule (a short turn naming the agent's last file) is gone:
measured over 100 flagged rows it fired alone five times and was wrong five times.
`TRANSCRIPTO_CORRECTION=v0` brings the old classifier back for comparison.

it is one pure function, `is_correction(text)`, and it is a **floor**, now measured rather
than asserted: on a 200-row labelled sample the v1 classifier has precision 0.81 and recall
0.16 (`docs/CORRECTION-PRECISION-2026-09-03.md`), which is why the printed line carries the
"~1 in 6" correction and a range. read it as a trend on your own history.
`test_correction.sh` pins the rule and the gate on `fixtures-correction/`.

## export-run

> in the repo since 2026-09-02, not yet on PyPI.

```
transcripto export-run latest                 # the newest session on this machine
transcripto export-run 3f9c1a2b               # a session id, or a prefix of one
transcripto export-run path/to/session.jsonl  # a transcript file
transcripto export-run latest --harness codex # --root / --harness as for coach
```

one run's numbers as JSON, read straight from the transcript file (no index needed).
this is the contract other tools read (Agent Grinder's card, ZUP's board); the keys are
frozen under `schema`, and a new key is an addition, never a rename.

| key | meaning |
|---|---|
| `schema` | `transcripto.export-run/1` |
| `session_id` | the harness's session id (Claude Code: the file name; Codex: `session_meta.id`; Cursor: the file name) |
| `project` | the run's `cwd` |
| `harness` | `claude` · `codex` · `cursor` |
| `transcript` | absolute path of the file read |
| `started` · `ended` | first and last record timestamp, UTC, `…Z`; `null` if the file carries none |
| `duration_s` | `ended − started`, whole seconds |
| `records` | every record in the file, before any gate |
| `typed_turns` | records that pass the authorship gate: `promptSource` typed or queued, never meta, sidechain or tool result. the same count coach prints as "typed by you" |
| `corrections` | typed turns `is_correction()` flags (see above) |
| `correction_rate` | `corrections / typed_turns`, 3 decimals; `null` when nothing was typed |
| `tool_calls` | every `tool_use` block the agent emitted |
| `files_touched` | sorted set of `file_path` (or `notebook_path`) from Edit / Write / Read / MultiEdit / NotebookEdit calls |
| `commits_in_window` | commits stamped inside `[started, ended]` in the project's git reflog; `null` when `project` is not inside a git repo |
| `commits` | those commits as `{sha, ts, subject}`, oldest first; `null` when not a repo |
| `proxy` | the caveat, in the JSON so it travels with the numbers |

`commits_in_window` reads `.git/logs/HEAD` directly, not `git log`, because this file
does not shell out (see privacy). the reflog is the record of what **that working tree**
did: a commit made there in the window is in it, a commit pulled in from elsewhere is not.
git expires the reflog after 90 days by default, so a run older than that can read 0 here
while `git log` would still show its commits. `commit (amend)` counts; a rebase's `pick`
lines do not. a `.git` file (a worktree) is followed to its gitdir.

## why your own gate matters here

at fleet scale roughly 95% of the `type: user` records in a transcript are not
you. they are tool results, injected skill bodies, sub-agent prompts, and
messages from other terminals, all wearing your role. transcripto gates on
`promptSource` (typed/queued, no meta, no sidechain) so it grades what you typed.

you can watch the gate do work: in the run above, 3678 of 381,804 records
survived it. that is 0.96%.

the same gate is what makes `cost` produce a number a spend tracker cannot:

```
cost per human decision  last 30 days  2026-07-28 → 2026-08-27

  API-equivalent spend      $8,892.49
  your decisions            2934   turns you actually typed (promptSource typed/queued)
  ────────────────────────────────────────────────────
  cost per human decision   $3.03

  46.4k agent messages · 16 per decision · 11.5B tokens · 149 sessions
  57.7k raw `type: user` records in the same window. dividing by those instead
  would read $0.15, 19.7x too cheap.
```

it prints both, so the gate's effect is something you can check rather than
something i am asserting. these are API-equivalent dollars at list rates,
because a transcript has no cost field, only token counts. on a subscription you
did not pay this.

## honest limits

read these before you quote a number at anyone.

- **survival is a proxy**, described above. durable keystroke, not durable outcome.
- **one operator's corpus.** every figure in this README comes from one machine.
  it is an existence proof that the measurement runs, not a finding about how
  people prompt. run it on yours and you get yours.
- **three harnesses today: Claude Code, Codex, Cursor.** nothing else is supported.
  aider and the rest are not read. and the three are not equal: Claude Code has a
  measured-reliable authorship field, Cursor has only the `<user_query>` wrapper,
  which is weaker and is labelled weaker wherever it is used.
- **the habit labels are heuristics.** "states-a-check-or-done-condition" is a
  pattern match over your text, not comprehension. it will misfile some prompts.
- **correlation, not instruction.** detailed prompts surviving more often does not
  prove that padding a prompt causes survival.

## privacy

it runs locally and never touches the network. there is no socket, no urllib, no
requests, no subprocess, no telemetry, no analytics, and no account. that is a
claim, so here is the grep that settles it against the single file it ships as:

```
$ grep -nE '^[[:space:]]*(import|from) ' transcripto.py
8:import sys, os, json, glob, re, sqlite3, argparse
9:from datetime import datetime, timezone
261:    import time
1160:            import datetime
1170:    from the separator), so the result is checked on disk and dropped if it is
```

five lines, four of which are imports and all four are stdlib. `time` and
`datetime` sit inside functions, which is why the pattern allows for indentation —
anchor it at `^import` and you would miss two, so do not take my word for the
anchor either. line 1170 is the pattern catching a docstring that happens to begin
with the word `from`; it is prose, not an import, and it is left in rather than
tuned out, because a grep you tuned until it agreed with you proves nothing.

what the list does NOT contain is the actual claim: no `socket`, no `urllib`, no
`requests`, no `http.client`, no `subprocess`. that one is checkable too, and the
right answer is no output at all:

```
$ grep -nE '\b(socket|urllib|requests|http\.client|subprocess)\b' transcripto.py
$
```

your transcripts stay in `~/.claude`, `~/.codex` and `~/.cursor`. the index it
builds stays in `~/.trace`.

## the rest of it

`coach` and `cost` read your transcript files directly and need nothing set up.
**the other six read a local index, so run this once first:**

```
transcripto index      # a few minutes on a large corpus, incremental after that
```

on a 2,874-file corpus that was 164 seconds, measured 2026-08-29. if you skip it,
the six say so and exit 2.

```
transcripto index      build / refresh (incremental)
transcripto watch      live, new sessions get picked up as your agents work
transcripto ask        YOUR OWN messages about a topic, newest first + a rollup
transcripto search     full-text across everything (you + agents + tool logs)
transcripto find       every session that wrote / edited / read a file
transcripto trace      what durably happened after each prompt you typed (0.1.2+)
transcripto sessions   recent sessions + the first prompt YOU typed in each
transcripto stats      what you actually work on
transcripto cost       what ONE of your decisions costs
transcripto coach      which of YOUR prompt habits survive (a proxy)
transcripto export-run one run's numbers as JSON (typed turns, correction rate, commits)
```

`ask` is the one that kills "wait, did i lose something?". it answers "what was i
thinking about X across ALL my sessions", in your own words only.

```
$ transcripto find USER-JOURNEY.md          # run 2026-08-29
USER-JOURNEY.md  4 touches across sessions (3 were writes/edits)

2026-08-20  WROTE  ~/CODE/demo/USER-JOURNEY.md                              abd9e871
2026-08-21  WROTE  ~/CODE/demo/docs/onboarding-notes.md                       0f845ede
2026-08-27  read   ~/CODE/demo-api/docs/USER-JOURNEY.md                       cddfde29
2026-08-27  WROTE  ~/CODE/demo-api/docs/USER-JOURNEY.md                       cddfde29
```

the file you lost, found across every session you ever ran, with the session id
that touched it. `find` needs `transcripto index` first.

## Codex

```
transcripto coach --harness codex
```

reads `~/.codex` (sessions + archived_sessions), normalises it into the same rows,
and applies the identical survival proxy. it also ingests `history.jsonl` purely
as a control on the gate: it reports how many of its input lines also show up as
typed rollout turns, so you can see the gate agreeing with a second source.

## install

```
uvx transcripto coach
```

no install, nothing to set up. or put it on your PATH:

```
pipx install transcripto
```

or run the single file with no packaging at all:

```
git clone https://github.com/Morkeeth/transcripto
cd transcripto
python3 transcripto.py coach
```

no dependencies, stdlib only, one file. the packaging adds nothing at runtime, it
just gives the file a name on your PATH.

## tests

```
./test_coach.sh        15 assertions
./test_codex.sh        14 assertions
./test_cost.sh         12 assertions
./test_small_n.sh       7 assertions
./test_label_bands.sh  13 assertions
./test_correction.sh   32 assertions   (correction rate + export-run, 2026-09-02)
./test_cursor_partial.sh 7 assertions
./test_version.sh       1 assertion    (VERSION matches in transcripto.py and pyproject.toml)
```

91 assertions, all green, re-run 2026-09-02.

offline, no keys, on fixtures that inherit the real transcript shape including
all four ways a non-human record disguises itself as `type: user`.

the load-bearing one in `test_coach.sh` is `REVERTED IS NOT SURVIVED`: a commit
that got `reset --hard` in the same session left no durable record. flip that one
line and the suite goes red, which is the point. a generous proxy is a broken one.

`test_label_bands.sh` is the other one, and it exists because 0.1.1 shipped the
defect it pins. `SURVIVES MOST` took the top five habits and `SURVIVES LEAST` took
the bottom five, which overlap whenever you have fewer than ten rankable habits —
so a new user, who necessarily has few, read the same habit at the same percentage
under both "do more of these" and "these tend to loop". on a 3-habit corpus 0.1.1
reprinted all three, all at 65% (22/34). the suite is red on the published 0.1.1
file and green on this one, and its `wide` band asserts the fix leaves a large
corpus byte-identical.

## why though

your agent history is proof. every "yeah it's done" has a real trace sitting
behind it. transcripto is the index that makes it checkable.

it is the fuel layer. on top of it you check what your agents *claim* against what
the trace *shows*, which is [mountain of helicon](https://github.com/Morkeeth/mountain-of-helicon).
the pitch was never "search your history". it is *prove your agent did what it
said, from your own local traces.*

local, MIT, no telemetry. star it if it finds you something you'd lost ™
