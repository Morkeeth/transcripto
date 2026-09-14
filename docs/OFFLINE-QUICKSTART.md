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
export HOME="$(mktemp -d)"   # optional clean home; skip to use your own
```

Replace `WHEEL` with the path from `python3 -m build` (`dist/*.whl`) or the file
you copied onto the laptop.

## 2. Seed labelled synthetic history

```sh
transcripto import-lab
transcripto ask "retry"
```

## 3. Reopen exact evidence

Run each printed `Open:` line, or:

```sh
transcripto replay /path/from/open --line N
transcripto replay /path/from/open --line N --json
```

Claude lab hit: failed edit. Codex: succeeded check. Cursor: unknown (no result).

## 4. Receiver brief with outcomes

```sh
transcripto import-example
transcripto handoff "30 seconds" --to-harness codex --output "$HOME/packet.json"
transcripto receive-handoff "$HOME/packet.json" --as-harness codex --output "$HOME/brief.md"
cat "$HOME/brief.md"
```

The brief includes recorded follow-up statuses and an Open command. If the source
moved or vanished, the brief marks evidence uncertain and keeps packet statuses
as provisional. Re-run ask after restoring the file, or pass the new path to replay.

Status describes tool execution, not task correctness. Missing results stay unknown.

Source publication and registry publication stay distinct. This card does not
upload to PyPI.
