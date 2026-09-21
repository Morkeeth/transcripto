"""Run Stage 0 arms. Offline fixtures are the default for tests. Gateway is opt-in."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .citations import load_frozen, validate_model_output
from .gateway import complete


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_private(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf8")
    os.chmod(path, 0o600)


def build_user_prompt(frozen: Path) -> str:
    question = (frozen / "question.txt").read_text(encoding="utf8").strip()
    instructions = (frozen / "analysis-prompt.txt").read_text(encoding="utf8").strip()
    corpus = (frozen / "episodes.jsonl").read_text(encoding="utf8")
    return f"{instructions}\n\nQUESTION\n{question}\n\nCORPUS\n{corpus}\n"


def load_offline_arm(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf8"))


def run_offline(frozen: Path, arms_dir: Path, out: Path) -> dict[str, Any]:
    index = load_frozen(frozen)
    files = sorted(p for p in arms_dir.iterdir() if p.suffix == ".json")
    if len(files) < 2:
        raise ValueError("offline run needs at least two model-arm JSON files")
    results = []
    for i, file in enumerate(files, 1):
        output = load_offline_arm(file)
        errors = validate_model_output(output, index)
        receipt = {
            "arm": f"arm-{i}",
            "label": file.stem,
            "model": output.get("model", file.stem),
            "offline": True,
            "at": _now(),
            "latency_ms": 0,
            "tokens": 0,
            "cost": 0,
            "errors": errors,
            "output": output,
        }
        _write_private(out / f"{file.stem}.json", receipt)
        results.append({"arm": receipt["arm"], "label": file.stem, "errors": errors})
    summary = {"stage": 0, "offline": True, "arms": results, "prompt_hash": hashlib.sha256(build_user_prompt(frozen).encode()).hexdigest()}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf8")
    return summary


def run_gateway(frozen: Path, models: list[str], out: Path, *, zdr: bool, no_training: bool) -> dict[str, Any]:
    prompt = build_user_prompt(frozen)
    index = load_frozen(frozen)
    results = []
    for i, model in enumerate(models, 1):
        raw = complete(model, prompt, zdr=zdr, no_training=no_training)
        text = (
            raw.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        try:
            output = json.loads(text)
        except json.JSONDecodeError:
            output = {"raw_text": text}
        errors = validate_model_output(output, index) if "codes" in output else ["model did not return JSON schema"]
        usage = raw.get("usage") or {}
        receipt = {
            "arm": f"arm-{i}",
            "label": model.replace("/", "-"),
            "model": model,
            "offline": False,
            "at": _now(),
            "latency_ms": None,
            "tokens": usage.get("total_tokens", 0),
            "cost": raw.get("cost"),
            "zdr": zdr,
            "disallow_prompt_training": no_training,
            "errors": errors,
            "output": output,
        }
        _write_private(out / f"{receipt['label']}.json", receipt)
        _write_private(out / f"{receipt['label']}.raw.json", {"request_prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(), "response": raw})
        results.append({"arm": receipt["arm"], "label": receipt["label"], "errors": errors})
    summary = {"stage": 0, "offline": False, "arms": results, "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf8")
    return summary
