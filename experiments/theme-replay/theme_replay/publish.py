"""Copy aggregate, blind results out of .trial, and re-score them without network."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from .citations import load_frozen, validate_model_output
from .freeze import freeze
from .memo import aggregate, corpus_lines, decide, score_memo

HERE = Path(__file__).resolve().parent.parent
NEVER = ("blind.json", "packet-key.json")


def publish(trial: Path, results: Path) -> list[str]:
    results.mkdir(parents=True, exist_ok=True)
    copied = []
    plan = [
        (trial / "frozen" / "dataset-manifest.json", results / "dataset-manifest.json"),
        (trial / "spend.json", results / "spend.json"),
    ]
    for name in ("model-manifest.json", "summary.json", "verify.json", "compare.json"):
        plan.append((trial / "runs" / name, results / "runs" / name))
    for path in sorted((trial / "runs").glob("arm-*.json")):
        if not path.name.endswith(".raw.json"):
            plan.append((path, results / "runs" / path.name))
    for path in sorted((trial / "memos").glob("*")):
        if path.name in NEVER or path.name.endswith(".prompt.json"):
            continue
        plan.append((path, results / "memos" / path.name))
    for src, dest in plan:
        if src.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            dest.chmod(0o644)
            copied.append(str(dest))
    (results / "corpus-lines.txt").write_text(corpus_lines(load_frozen(trial / "frozen")) + "\n", encoding="utf8")
    for dest in copied:
        text = Path(dest).read_text(encoding="utf8")
        for marker in ("/Users/", "/home/", "sk-or-"):
            if marker in text:
                raise RuntimeError(f"{marker} found in {dest}; refusing to publish")
    return copied


def rescore(results: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        frozen = Path(tmp) / "frozen"
        fx = HERE / "fixtures"
        freeze(fx / "stage0-episodes.jsonl", frozen,
               question=(fx / "question.txt").read_text(encoding="utf8"),
               prompt=(fx / "analysis-prompt.txt").read_text(encoding="utf8"),
               protocol=json.loads((fx / "protocol.json").read_text(encoding="utf8")))
        index = load_frozen(frozen)
        manifest = json.loads((results / "dataset-manifest.json").read_text(encoding="utf8"))
        fresh = json.loads((frozen / "dataset-manifest.json").read_text(encoding="utf8"))
        corpus_same = manifest["files"]["episodes.jsonl"] == fresh["files"]["episodes.jsonl"]
    arms = {}
    for path in sorted((results / "runs").glob("arm-*.json")):
        receipt = json.loads(path.read_text(encoding="utf8"))
        errs = ["call failed"] if receipt.get("call_failed") else validate_model_output(receipt.get("output") or {}, index)
        arms[receipt["arm"]] = len(errs)
    calls = []
    for path in sorted((results / "memos").glob("memo-*.json")):
        if path.name == "memo-report.json":
            continue
        row = json.loads(path.read_text(encoding="utf8"))
        score = row["score"] if row.get("call_failed") else score_memo(row.get("output") or {}, index)
        calls.append((row["memo"], row["condition"], score))
    table = aggregate({m: s for m, _, s in calls}, {m: c for m, c, _ in calls})
    verdict = decide(table)
    stored = json.loads((results / "memos" / "memo-report.json").read_text(encoding="utf8"))
    return {
        "corpus_hash_matches": corpus_same,
        "arm_named_failures": arms,
        "verdict": verdict,
        "matches_committed_verdict": verdict == stored["verdict"] and table == stored["by_condition"],
        "by_condition": table,
    }
