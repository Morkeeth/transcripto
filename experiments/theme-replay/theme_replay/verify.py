"""Name citation and status failures. Do not average them into a quality score."""

from __future__ import annotations

import json
from pathlib import Path

from .citations import load_frozen, validate_model_output


def verify(frozen: Path, runs: Path) -> dict:
    index = load_frozen(frozen)
    findings = []
    for file in sorted(runs.glob("*.json")):
        if file.name == "summary.json":
            continue
        receipt = json.loads(file.read_text(encoding="utf8"))
        output = receipt.get("output") or {}
        errors = list(receipt.get("errors") or [])
        if "codes" in output:
            errors.extend(validate_model_output(output, index))
        # unique
        errors = sorted(set(errors))
        findings.append(
            {
                "file": file.name,
                "arm": receipt.get("arm"),
                "ok": not errors,
                "errors": errors,
            }
        )
    hard = [row for row in findings if not row["ok"]]
    report = {
        "ok": not hard,
        "unresolved_citations": sum(len(row["errors"]) for row in hard),
        "arms": findings,
        "note": "Failures are named. They are not a single quality score.",
    }
    (runs / "verify.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    return report
