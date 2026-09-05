#!/usr/bin/env bash
# Consumer integration check against READ-CONTRACT.md — tip tree as object.
# Builds a wheel, installs into a clean venv, indexes fixtures, opens stable
# views read-only, and probes ask/1 + packet/1 + coaching-snapshot/1.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT
python3 -m venv "$WORKDIR/venv"
# shellcheck disable=SC1091
source "$WORKDIR/venv/bin/activate"
pip install -q --upgrade pip
pip wheel --no-deps "$ROOT" --wheel-dir "$WORKDIR/wheels" >/dev/null
pip install -q --no-deps "$WORKDIR"/wheels/transcripto-*.whl
export HOME="$WORKDIR/home"
export TRANSCRIPTO_DB="$WORKDIR/trace.db"
mkdir -p "$HOME"
echo "consumer_check_workdir=$WORKDIR"
echo "installed=$(transcripto --version)"

transcripto index --root "$ROOT/fixtures-cursor" >/dev/null

python3 - <<'PY'
import os, sqlite3, sys
db = os.environ["TRANSCRIPTO_DB"]
con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
uv = con.execute("PRAGMA user_version").fetchone()[0]
print("user_version", uv)
fail = 0
for v in ("v_sessions", "v_messages", "v_file_touches", "v_index_health", "messages_fts"):
    try:
        n = con.execute("select count(*) from %s" % v).fetchone()[0]
        print("view", v, "rows", n)
    except Exception as e:
        print("view", v, "MISSING", e)
        fail = 1
names = [d[0] for d in con.execute("select * from v_messages limit 0").description]
need = [
    "session_file", "source_line", "record_sha256", "origin_session_id",
    "inherited", "session_kind", "timestamp_basis", "native_session_id",
    "parent_session_id",
]
missing = [c for c in need if c not in names]
print("v_messages_cols", names)
print("schema7_missing", missing)
if missing or uv < 7:
    print("FAIL READ-CONTRACT schema 7 columns / user_version")
    fail = 1
sys.exit(fail)
PY

transcripto ask "retry" --json --root "$ROOT/fixtures-cursor" >"$WORKDIR/ask.json"
python3 - <<PY
import json
r = json.load(open("$WORKDIR/ask.json"))
assert r.get("schema") == "transcripto.ask/1", r.get("schema")
assert "coverage" in r and "hits" in r and "selection" in r
print("ask_schema", r["schema"], "status", r.get("status"), "hits", len(r.get("hits") or []))
hit = (r.get("hits") or [None])[0]
if hit:
    src = hit.get("source") or {}
    for k in ("path", "line_start", "record_sha256", "source_sha256"):
        assert k in src, k
    print("ask_hit_source_ok", src.get("line_start"))
PY

session=$(python3 - <<'PY'
import os, sqlite3
con = sqlite3.connect(os.environ["TRANSCRIPTO_DB"])
print(con.execute("select session_file from messages limit 1").fetchone()[0])
PY
)
packet="$WORKDIR/packet.json"
transcripto export-run "$session" --packet --from-line 1 --to-line 20 \
  --output "$packet" --question "consumer-integration-check" >/dev/null
transcripto export-run "$packet" --check >"$WORKDIR/packet-check.json"
python3 - <<PY
import json
p = json.load(open("$packet"))
assert p.get("schema") == "transcripto.packet/1", p.get("schema")
c = json.load(open("$WORKDIR/packet-check.json"))
assert c.get("schema") == "transcripto.packet-check/1"
assert c.get("status") == "current", c
print("packet_schema", p["schema"], "check", c["status"])
PY

snap="$WORKDIR/baseline.json"
transcripto coach --root "$ROOT/fixtures-cursor" --snapshot "$snap" --json >"$WORKDIR/coach-snap.json"
transcripto coach --root "$ROOT/fixtures-cursor" --compare "$snap" --json >"$WORKDIR/coach-cmp.json"
python3 - <<PY
import json
s = json.load(open("$WORKDIR/coach-snap.json"))
c = json.load(open("$WORKDIR/coach-cmp.json"))
assert s.get("schema") == "transcripto.coaching-snapshot/1", s.get("schema")
assert c.get("schema") == "transcripto.coaching-comparison/1", c.get("schema")
print("coach_snapshot", s["schema"], "compare", c["schema"])
PY

echo "CONSUMER_INTEGRATION PASS"
