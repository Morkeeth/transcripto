# Transcripto

**You might already be keeping a journal. Read your side of it.**

Your agent transcripts contain what you asked for, what you changed your mind
about, and what you kept coming back to. Transcripto helps you find those words
and read the recorded work around them.

Claude Code · Codex · Cursor. Local files. No account. No runtime dependencies.

## Start with something you remember saying

```sh
uvx --from transcripto==0.2.1 transcripto ask "retry"
```

Replace `retry` with a word you remember using. `ask` searches messages identified
as yours and shows dated snippets, newest first. It refreshes the local index
automatically. The first search indexes the selected history; a large archive
can take minutes. Add `--harness claude`, `--harness codex`, or `--harness cursor`
to limit that scan. It does not generate a diary or interpret your personality.

Each hit prints an `Open:` command. Run that command to open the exact request
and its recorded work. This also works when search matches a word variant
(such as `retry` matching `retried`) or several requests share the same words.

You can also search replay directly:

```sh
uvx --from transcripto==0.2.1 transcripto replay "retry"

# Or open your latest human session:
uvx --from transcripto==0.2.1 transcripto
```

Replay puts your request, tool calls and recorded results in order. Failed edits
stay failed. Missing results stay unknown. Status describes tool execution,
not whether the task was done correctly.

Or install with `python3 -m pip install transcripto==0.2.1`, then run
`transcripto ask "retry"`. Requires Python 3.9 or newer.

## Try the stranger flow without your transcripts

The bundled public example is synthetic. It works in an isolated home and does
not depend on agent dotfiles:

```sh
INSTALL="$(mktemp -d)"
python3 -m pip install --no-deps --no-build-isolation --target "$INSTALL" .
export HOME="$(mktemp -d)"
transcripto() { PYTHONPATH="$INSTALL" python3 -m transcripto "$@"; }

transcripto import-example
transcripto ask "What changed about the forecast cache?"
transcripto changes
```

`ask` cites the imported JSONL line for every hit. `changes` is a focused view
of the request that was revised, the correction, and its recorded follow-up.
It labels missing results rather than turning a change of mind into a score.

To carry that correction to a different receiver:

```sh
transcripto handoff "30 seconds" \
  --to-harness codex --output "$HOME/codex-inbox/correction.json"
transcripto receive-handoff \
  "$HOME/codex-inbox/correction.json" --as-harness codex \
  --output "$HOME/codex-work/receiver-brief.md"
cat "$HOME/codex-work/receiver-brief.md"
```

The brief includes the cited correction, recorded follow-up statuses
(failed / succeeded / unknown), and an `Open:` command for the exact request.
If the source moved, disappeared, or no longer holds the cited request, the brief
marks evidence uncertain and shows only the packet's own statuses as provisional. It does not invoke a receiver agent or prove
adoption. Synthetic provenance stays visible in search, changes, and handoffs.
Handoff files are local and mode `0600`; they can contain transcript text and
paths, so review them before sharing.

### Cross-harness lab (failed / succeeded / unknown)

For a receiving agent that needs to find a prior episode and reopen exact
evidence without private history:

```sh
transcripto import-lab
transcripto ask "retry"
# run each printed Open: command
```

All lab records are labelled synthetic. Claude shows a failed edit, Codex a
succeeded check, Cursor an unknown missing result.

### Offline flight card

```sh
transcripto quickstart --wheel /absolute/path/to/transcripto-0.2.1-py3-none-any.whl
```

Prints install, `import-lab`, search, and reopen commands for a built wheel
without PyPI. See also `docs/OFFLINE-QUICKSTART.md`.

**Your files remain yours.** Transcripto does not upload transcript content or
execute commands found in it. Search output, replay and JSON can contain private
words and paths; review anything you choose to share. It reads existing files,
not deleted history. Check your agent's retention settings and keep your own
backup if you want a lasting record. Authorship detection differs by harness;
[see the limits below](#what-each-harness-supports).

## Find the thing you remember

Search automatically refreshes a local index. No setup command is required.

```sh
transcripto ask "retry"                 # your submitted words
transcripto search "retry"              # prompts, replies, and tool text
transcripto find parser.py              # recorded file operations and attempts
transcripto trace "retry"               # an alias into result-aware replay
transcripto sessions                    # sessions with submitted prompts
transcripto stats                       # activity counts
```

A failed or unconfirmed file change is labelled an **attempt**, never `WROTE`.
Queries with `--harness` or `--root` are scoped to that selection even if the
index already contains another corpus. `index` and `watch` remain available for
explicit refresh and background polling.

## The replay

This is output from `replay --demo`. **All prompts and results in this example
are invented.** The demo goes through the same parser as a real transcript.

```text
THE COMEBACK · claude · request 1
You asked: "Fix the login redirect and run its tests."

   1  FAIL edit       src/login.py
                 Tool error: Error: text not found  [call L2 → result L3]
   2  OK   edit       src/login.py
                 Tool reported success.  [call L4 → result L5]
   3  FAIL check      pytest tests/test_login.py
                 Tool error: Process exited with code 1  [call L6 → result L7]
   4  OK   edit       src/login.py
                 Tool reported success.  [call L8 → result L9]
   5  OK   check      pytest tests/test_login.py
                 Tool reported success.  [call L10 → result L11]

Agent said: "The redirect is fixed and the tests pass."

Recorded: 3 succeeded · 2 failed · 0 unknown
Status describes a tool result, not task correctness. Missing results stay unknown.
```

The headings have rules. **The comeback** means a recorded failure was followed
by success for the same operation and target, without a later failed or unknown
attempt on that target. **The snag** means a failure is
present. **The missing receipt** means a result is unknown. **The answer** means
there were no recorded tool calls; an explanation may have been the whole task.
These are descriptions of the sequence, not grades for you or your agent.

On your own history, each replay names its source file and line numbers, plus a
command that reopens that exact request. Long sequences open around the first
failure or change and tell you what was omitted. `--all` shows the full sequence.

```sh
transcripto                                # latest session you submitted a request in
transcripto replay --failures               # most recent request with a recorded failure
transcripto replay "login redirect"         # find requests containing these words
transcripto replay path/to/session.jsonl    # inspect one transcript
transcripto replay --session 3f9c1a2b        # explicitly select a session prefix
transcripto replay path/to/session.jsonl --episode 3 --all
transcripto replay path/to/session.jsonl --line 42  # exact request from an ask hit
transcripto replay latest --json            # structured events, evidence, source lines
transcripto replay latest --share           # counts + caveat; no prompts or paths
```

`--share` is intentionally small. Full replay output and JSON contain your own
words and local paths. Replay does not upload either.

## What each harness supports

| Feature | Claude Code | Codex | Cursor |
|---|---|---|---|
| Replay, search, ask, find, trace, sessions, stats | Yes | Yes | Yes |
| Tool attempts | Native tool calls | Direct calls and supported static wrappers | `StrReplace`, `Shell`, `Write`, and other calls |
| Execution status | Matched results | Matched results; ambiguous wrappers stay unknown | Unknown when the export omits results or call IDs |
| Authorship | `promptSource` typed/queued, excluding injected/tool records | User messages with known injected context excluded | `<user_query>` wrapper; a weaker signal |
| Coach, export-run | Yes | Yes | Yes, with missing evidence preserved |
| API-equivalent cost | Yes | Not supported | Not supported |

```sh
transcripto replay --harness claude
transcripto replay --harness codex
transcripto replay --harness cursor
transcripto search "retry" --harness codex
transcripto replay --root /path/to/transcripts
```

Default roots are `~/.claude/projects`, `~/.codex`, and `~/.cursor`.
Codex reads sessions and archived sessions. Cursor reads the per-session files
under `projects/*/agent-transcripts/*/`. Latest-session replay skips subagents
and files without a submitted human request.

Cursor exports often contain calls without results. That is useful evidence
of an attempt, but not enough to claim success. Transcripto does not substitute
an assistant's closing message or a `turn_ended` record for the missing result.

## The evidence contract

1. A tool call is an **attempt**.
2. A matching result may establish **succeeded** or **failed** execution.
3. A missing result, a running command, or an ambiguous result is **unknown**.
4. An exit code of zero is not proof that the requested task is correct.
5. A later human request opens a new episode. Its work is never absorbed into
   the previous request because the words happen to overlap.
6. A command mentioning `git commit` is not necessarily a commit. Quoted text,
   dry runs, and compound shell commands are not promoted to commit evidence.

The tool never executes transcript commands. It parses a limited set of static
Codex wrapper forms; arbitrary JavaScript and multiple nested child calls are
not reconstructed. A long-running call can remain unknown when completion is
only present in a later polling call. Cross-session durability, semantic task
completion, and live repository state are not inferred from transcript text.

## Coach without invented grades

`transcripto coach` shows descriptive request history. It no longer recommends
prompt habits, labels a no-edit answer a bad prompt, or applies one person's
correction-rate calibration to someone else's data.

Habit proportions include **change attempts with known outcomes**. Unknown
outcomes and read-only tasks are excluded. The groups overlap and the requests
can be correlated, so these proportions are not significance tests or causal
advice. No best/worst ranking is printed. Correction markers are a lexical
estimate with false positives and misses, not a guaranteed lower bound.

Coach JSON is marked `transcripto.coach/2`. Legacy `durable`/`survived` fields
refer only to observed successful change results, not lasting work. Unknown
request outcomes have `survived: null`. `durable_rate` uses only known change
requests as its denominator and is null when there are none. `best_prompt` and `worst_prompt` are
retained as null compatibility fields. Use `successful_request`,
`failed_request`, and replay's event status to inspect evidence.

`export-run latest` always prints JSON. Its
existing `transcripto.export-run/1` keys remain available. `records` counts
normalized message records. `files_touched` lists attempted file targets,
including reads; it is not a successful-change count. Reflog commits are local
working-tree events inside the available timestamp window, not proof that this
agent caused them. Without a usable window, the commit fields are null.

## Privacy and limits

The default commands process transcripts locally, without telemetry or an
account flow. The optional Jev detector below sends filtered typed text only
when explicitly selected. Package installation (`pip` or `uvx`) is a separate
operation that may contact a package registry and write a package cache.

### Optional network detector: `--detector jev`

`coach` and `export-run` can count corrections with TypeSafe Jev instead of the
local regex. This is the one path that sends text off the machine, and it runs
only when you pass the flag on that run. No environment variable or config file
turns it on. The code lives in its own module, `transcripto_jev.py`, which the
default path never imports.

```sh
OPENROUTER_API_KEY=... transcripto coach --detector jev
```

Before the first request it prints one line to stderr: how many typed turns it
may send, how many the privacy filter excluded, and the URL
(`https://openrouter.ai/api/alpha/decisions`, model `typesafe/jev-1.13`).
Only your typed turns are sent, at most 2,000 characters each, with the fixed
question. No separate path/session metadata, agent output or tool results are
sent. Typed text can still contain paths and private details the filter misses.

The privacy filter runs before any request is built:

- **Excluded, never sent:** a turn that names your account, cites a numbered
  notes-folder path (two digits, a space, a folder name, a `.md` file), mentions a private topic (money,
  finance, wallet, seed, key, password, token, salary, bank, journal, health,
  family, whole words), or holds an email address or phone-like number.
- **Redacted, then sent:** API keys and tokens, AWS key ids, private-key blocks,
  40-hex `0x` addresses, and home directory paths.

Excluded turns and failed requests get no verdict. They are reported, never
filled in with the regex. The correction rate then uses the scored turns as its
denominator (`correction_rate_denominator: "jev.scored"`). JSON gains a `jev`
block with `sent`, `excluded`, `excluded_reasons`, `scored`, `errors`,
`cost_usd` and the served model.

Preview the privacy counts before choosing to send anything:

```sh
transcripto coach --detector jev --jev-dry-run --json
transcripto export-run latest --detector jev --jev-dry-run
```

This needs no API key and makes no requests, even with a key in the environment.
Both commands return the dedicated `transcripto.jev-privacy-preview/1` JSON
schema in dry-run mode (`coach` needs `--json`). The `jev` count block and null
correction fields stay available to existing count consumers. Ordinary coach
episodes and export session, file, tool and commit details are omitted; dry runs
do not inspect the project reflog or build an episode report.

It reports eligible turns, exclusions by reason, and redaction counts. It does
not print turn text, estimate cost, or produce correction verdicts. Eligibility
means the current filter permits a turn; it is not a guarantee that the text
contains no private information.

Options: `--jev-threshold` (default 0.30 on P(correction)), `--jev-max-usd`
(default 1.00, stops sending once reached), `--jev-batch` (default 1; larger
batches are cheaper but change the answers), `--jev-fallback-regex` (with no
key set, use the regex instead of exiting). A refused key (HTTP 401, 402, 403)
on the first request stops before any later batch. If a later request is refused,
completed verdicts are retained and no further wave starts.

The `eligible` count describes turns allowed by the filter; `sent` counts turns
submitted to transport, excluding later turns skipped by the spending stop.
Neither count proves that the remote service received a request successfully.

The spend limit must be finite and positive. Costs are reported after requests,
so requests already in flight can exceed the limit; it is not a provider-side
hard cap. If any request cost is missing or invalid, no further batch is sent
and the displayed cost is labelled an incomplete subtotal. Invalid probabilities
produce no verdict rather than a guessed correction label.

The default 0.30 comes from a local experiment on 185 turns, labelled by a
single model rater: agreement F1 about 0.77 to 0.83 against that rater, versus
0.68 to 0.70 for the regex. That is agreement with a model, not accuracy.

Replay and coach read transcripts without making an index. Search writes text
and file metadata to `~/.trace/trace.db`. A new index directory is private;
database and WAL files use mode `0600`. The index stays after the command exits.
Schema upgrades rebuild it locally. `replay --demo` briefly writes an invented
transcript to a temporary directory and removes it afterward.

Malformed records and unreadable files produce diagnostics. Search indexes the
valid records of partially malformed files and repeats the warning on later
queries until the source is repaired. A wholly unreadable file keeps any prior
indexed copy, with an explicit warning; replay always reads the source. Files larger than
128 MiB are skipped before parsing; lines larger than 8 MiB are discarded as
whole records. Split larger files into smaller JSONL files to inspect them.
Individual displayed text fields are bounded at 16,000 characters. Replay's
source references let you inspect the original. Terminal control sequences are
removed from rendered transcript content.

## Development

Python 3.9+, standard library only. The CLI remains in `transcripto.py`;
`transcripto_core.py` owns normalization and evidence; `transcripto_replay.py`
owns replay selection and presentation. All fixtures committed here are synthetic.

```sh
python3 -m unittest discover -s tests -v
for test in test_*.sh; do bash "$test" || exit; done
```

`test_distribution.sh` requires the development-only `build` package. It builds
an sdist, builds the wheel from that archive, installs without dependencies in a
fresh virtual environment, and exercises discovery, search and exact replay
across all three harnesses in an isolated synthetic HOME.

The regression cases include failed edits and commits, missing/mismatched
results, Cursor call shapes, Codex wrappers, result attribution across prompts,
rollback order, malformed JSON, a sparse 2 GiB file, terminal controls, private
index permissions, incremental search, and cross-harness retrieval.

MIT. Open an issue with the **record shape** that fails, or a synthetic
reproduction. Your real prompt text is not needed.

### Inspect one session's Jev findings, then carry one candidate

This source candidate adds a selected-session path; it is not part of the pinned
PyPI 0.2.1 release above. Build/install this checkout before using these commands.
Preview remains counts-only, offline and keyless:

```sh
transcripto jev-findings /path/session.jsonl --detector jev --jev-dry-run
```

Only when you choose to send that session's privacy-filtered typed turns:

```sh
transcripto jev-findings /path/session.jsonl --detector jev \
  --jev-max-usd 0.05 --output /your/private/findings.json
```

The local report contains references, source/request hashes, exact lines,
probabilities, threshold, model metadata and observation time, without transcript
text. It marks candidate, not-candidate, excluded and unknown separately. Each
row prints its exact replay command. A candidate is a recorded model suggestion,
not a confirmed human correction. The serving-model hint is not a per-turn
model guarantee. The cap and provider/privacy limits above still apply.

After inspecting a candidate's request and recorded work, select its exact line:

```sh
transcripto replay --findings /your/private/findings.json --line 3
transcripto handoff --findings /your/private/findings.json --line 3 \
  --to-harness codex --output /your/private/candidate.json
transcripto receive-handoff /your/private/candidate.json --as-harness codex \
  --output /your/private/receiver-brief.md
```

Use the actual line shown by your report and choose a receiver different from
the source harness. Replay and handoff refuse a changed source, including changed
follow-up records around an unchanged request. Excluded, unknown and negative
findings cannot become candidate handoffs. A previously prepared packet whose
source changes remains historical; its receiver brief marks outcomes provisional.

The packet and receiver brief are private local files and contain selected
transcript text. They retain detector provenance, synthetic/test labels, and
pending human confirmation and receiver acknowledgement. They do not invoke an
agent or send a message. Reports, packets and briefs use mode `0600`; inspect
before sharing. `replay --share` remains counts-only.

### Choose a local replay and author a handoff

A model report is optional. List metadata from an existing index, choose a source,
then explicitly permit local viewing of its requests and recorded tool outcomes:

```sh
transcripto selected-context runs --cwd /your/repo
transcripto selected-context describe --source /your/session.jsonl
transcripto selected-context episodes --source /your/session.jsonl \
  --accept-sha SHA256_FROM_DESCRIBE --consent
transcripto handoff --source /your/session.jsonl \
  --accept-sha SHA256_FROM_DESCRIBE --line 3 \
  --instruction 'Repair the selected output and verify the stated condition.' \
  --consent --to-harness claude --output /your/private/packet.json
transcripto receive-handoff /your/private/packet.json --as-harness claude \
  --output /your/private/brief.md
```

`runs` accepts `--index /your/existing.sqlite`; it does not create or refresh an
index. It reads only metadata from at most the most recent 20,000 indexed records,
returning up to 20 runs by default (maximum 30). Suggestions are unbound: sharing a
working directory does not prove that a run produced your artifact. No title or
body is read by this query. SQLite may use locking sidecars. Choose a file explicitly
when the bounded index window has no suitable run.

`describe` reads bytes to compute identity without returning transcript text. The
consented replay returns at most the first 100 requests from one file of at most
16 MiB; changed bytes or parsing warnings refuse replay. Authored handoffs retain
the original request, source hash, exact line and recorded outcomes. The new
instruction is explicit authorship for this handoff, not a detector verdict,
inferred human REDO or research label. Same-harness refusal and synthetic labels
remain. These commands prepare private local files; they do not invoke a receiver
or send a message. Review the full brief before giving it to another process.
