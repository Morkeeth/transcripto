"""Human review surface: question, anonymised arms, citations, KEEP/REVISE/REJECT."""

from __future__ import annotations

import json
from pathlib import Path

from .schema import normalize_decision


def load_receipts(runs: Path) -> list[dict]:
    rows = []
    for file in sorted(runs.glob("*.json")):
        if file.name in {"summary.json", "verify.json", "decisions.json"}:
            continue
        rows.append(json.loads(file.read_text(encoding="utf8")))
    return rows


def render(frozen: Path, runs: Path) -> str:
    question = (frozen / "question.txt").read_text(encoding="utf8").strip()
    lines = [
        "THEME REPLAY · STAGE 0",
        f"QUESTION  {question}",
        "",
        "Readings are labelled arm-1 / arm-2 / arm-3. Generating models stay hidden.",
        "Decision field: KEEP · CHANGES MY VIEW (recorded as REVISE) · REJECT plus one sentence.",
        "",
    ]
    for receipt in load_receipts(runs):
        output = receipt.get("output") or {}
        lines.append(f"{receipt.get('arm', 'arm')}  errors={len(receipt.get('errors') or [])}")
        for theme in output.get("themes") or []:
            lines.append(f"  THEME  {theme.get('name')}")
            lines.append(f"         {theme.get('central_concept')}")
            lines.append(
                f"         support {theme.get('supporting_episodes')}  "
                f"disconfirm {theme.get('disconfirming_episodes')}"
            )
        for code in output.get("codes") or []:
            lines.append(f"  CODE   {code.get('label')}")
            for ev in code.get("evidence") or []:
                lines.append(
                    f"         Open: {ev.get('episode_id')} line {ev.get('line')}  {ev.get('quote')!r}"
                )
        lines.append("")
    return "\n".join(lines)


def record_decision(runs: Path, claim_id: str, decision: str, sentence: str) -> dict:
    path = runs / "decisions.json"
    rows = json.loads(path.read_text(encoding="utf8")) if path.exists() else []
    row = {
        "claim_id": claim_id,
        "decision": normalize_decision(decision),
        "sentence": sentence.strip(),
    }
    rows = [item for item in rows if item["claim_id"] != claim_id] + [row]
    path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf8")
    return row
