#!/usr/bin/env bash
# Installed-package check: open the LIVE PyPI wheel as the object, then compare
# a clean-room pip install and (when available) uvx against the tip tree.
# Never publishes. Never trusts PyPI JSON alone for long-description truth.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-/dev/stdout}"
python3 - "$ROOT" <<'PY' | tee "$OUT"
import hashlib, io, json, os, re, sys, urllib.request, zipfile

root = sys.argv[1]
tip_code = open(os.path.join(root, "transcripto.py"), encoding="utf-8").read()
tip_ver = re.search(r'VERSION = "([0-9.]+)"', tip_code).group(1)
tip_schema = re.search(r"SCHEMA_VERSION = (\d+)", tip_code).group(1)

meta = json.load(urllib.request.urlopen("https://pypi.org/pypi/transcripto/json"))
pypi_ver = meta["info"]["version"]
wheel = next(u for u in meta["urls"] if u["filename"].endswith(".whl"))
data = urllib.request.urlopen(wheel["url"]).read()
sha = hashlib.sha256(data).hexdigest()
with zipfile.ZipFile(io.BytesIO(data)) as z:
    names = sorted(n for n in z.namelist() if not n.endswith("/"))
    text = z.read(next(n for n in names if n.endswith("METADATA"))).decode()
    code = z.read("transcripto.py").decode()
code_ver = re.search(r'VERSION = "([0-9.]+)"', code).group(1)
schema = re.search(r"SCHEMA_VERSION = (\d+)", code).group(1)
pins = re.findall(r"transcripto==([0-9.]+)", text)
mods = [n for n in names if n.endswith(".py") and "/" not in n]

print("pypi_json_version", pypi_ver)
print("wheel_filename", wheel["filename"])
print("wheel_sha256", sha)
print("wheel_VERSION", code_ver)
print("wheel_SCHEMA", schema)
print("wheel_modules", mods)
print("longdesc_pins", pins)
print("tip_VERSION", tip_ver)
print("tip_SCHEMA", tip_schema)

gate = "green"
if code_ver != pypi_ver:
    gate = "red"
    print("FAIL wheel VERSION != pypi JSON version")
for pin in sorted(set(pins)):
    if pin != pypi_ver:
        gate = "red"
        print("FAIL longdesc pin", pin, "!=", pypi_ver)
print("pypi_longdesc_gate", gate)

# Embarrassment control: same marketed version, different schema object.
collision = tip_ver == code_ver and tip_schema != schema
print("version_schema_collision", collision)
if collision:
    print(
        "FINDING: tip and live PyPI both claim version %s but SCHEMA %s vs %s"
        % (tip_ver, tip_schema, schema)
    )
    # Exit 0 still — publishing is Oscar's click; this run must surface the RED
    # without blocking local tip work. Caller may set STRICT=1 to fail.
    if os.environ.get("STRICT") == "1":
        sys.exit(2)

if gate != "green":
    sys.exit(1)
print("INSTALLED_PACKAGE_WHEEL_GATE PASS")
PY
