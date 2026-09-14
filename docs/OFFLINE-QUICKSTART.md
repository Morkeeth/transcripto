# Offline quickstart (flight)

Use a built wheel. Do not require PyPI. All lab records are invented.

Print the same card from an installed CLI:

```sh
transcripto quickstart --wheel /absolute/path/to/transcripto-0.2.0-py3-none-any.whl
```

## 1. Install from a wheel path

```sh
WHEEL=/absolute/path/to/transcripto-0.2.0-py3-none-any.whl
python3 -m venv /tmp/transcripto-flight
/tmp/transcripto-flight/bin/python -m pip install --no-index --no-deps "$WHEEL"
export PATH="/tmp/transcripto-flight/bin:$PATH"
FLIGHT_HOME="$(mktemp -d)"   # clean home for the lab; your own HOME is never changed
```

Replace WHEEL with the path printed by `python3 -m build` (dist/*.whl) or the
file you copied onto the laptop. Every lab command below sets HOME for that one
command only. Drop the HOME= prefix to use your own history instead.

## 2. Seed labelled synthetic history

```sh
HOME="$FLIGHT_HOME" transcripto import-lab
HOME="$FLIGHT_HOME" transcripto ask "retry"
```

## 3. Reopen exact evidence

Run each printed `Open:` line, or:

```sh
transcripto replay /path/from/open --line N
transcripto replay /path/from/open --line N --json
```

replay reads the cited file directly and needs no HOME prefix.
Claude lab hit: failed edit. Codex: succeeded check. Cursor: unknown (no result).

## 4. Receiver brief with outcomes

```sh
HOME="$FLIGHT_HOME" transcripto import-example
HOME="$FLIGHT_HOME" transcripto handoff "30 seconds" --to-harness codex --output "$FLIGHT_HOME/packet.json"
HOME="$FLIGHT_HOME" transcripto receive-handoff "$FLIGHT_HOME/packet.json" --as-harness codex --output "$FLIGHT_HOME/brief.md"
cat "$FLIGHT_HOME/brief.md"
```

The brief includes recorded follow-up statuses and an Open command. If the source
moved, vanished, or no longer holds the cited request, the brief marks evidence
uncertain and shows only the packet's own statuses as provisional. Re-run ask
after restoring the file, or pass the new path to replay.

Status describes tool execution, not task correctness. Missing results stay unknown.

Source publication and registry publication stay distinct. This card does not
upload to PyPI.
