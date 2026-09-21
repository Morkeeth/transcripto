"""Run Stage 0 arms. Offline fixtures are the default for tests. Gateway is opt-in.

Receipts are blind: files are named arm-N.json in a seeded random order. The
arm-to-model mapping lives only in blind.json (mode 0600). The review surface
never reads it.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .citations import load_frozen, validate_model_output
from .gateway import complete, require_key
from .models import fetch_catalog, freeze_model_manifest


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


def _new_seed(seed: int | None) -> int:
    return seed if seed is not None else int.from_bytes(os.urandom(4), "big")


def blind_order(jobs: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    """Shuffle jobs with a recorded seed so arm number does not reveal the model."""
    order = list(jobs)
    random.Random(seed).shuffle(order)
    return order


def _write_blind(out: Path, seed: int, mapping: dict[str, dict[str, Any]]) -> None:
    _write_private(
        out / "blind.json",
        {
            "seed": seed,
            "note": "Unblinding key. Do not open before human decisions are recorded.",
            "arms": mapping,
        },
    )


def run_offline(frozen: Path, arms_dir: Path, out: Path, *, seed: int | None = None) -> dict[str, Any]:
    index = load_frozen(frozen)
    files = sorted(p for p in arms_dir.iterdir() if p.suffix == ".json")
    if len(files) < 2:
        raise ValueError("offline run needs at least two model-arm JSON files")
    seed = _new_seed(seed)
    jobs = [{"source": f, "model": load_offline_arm(f).get("model", f.stem), "run": 1} for f in files]
    results = []
    mapping = {}
    for i, job in enumerate(blind_order(jobs, seed), 1):
        arm = f"arm-{i}"
        output = load_offline_arm(job["source"])
        errors = validate_model_output(output, index)
        receipt = {
            "arm": arm,
            "offline": True,
            "at": _now(),
            "latency_ms": 0,
            "tokens": 0,
            "cost": 0,
            "errors": errors,
            "output": output,
        }
        _write_private(out / f"{arm}.json", receipt)
        mapping[arm] = {"model": job["model"], "source": job["source"].name, "run": 1}
        results.append({"arm": arm, "errors": errors})
    _write_blind(out, seed, mapping)
    summary = {
        "stage": 0,
        "offline": True,
        "arms": results,
        "prompt_hash": hashlib.sha256(build_user_prompt(frozen).encode()).hexdigest(),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf8")
    return summary


def parse_output(text: str) -> dict[str, Any]:
    try:
        output = json.loads(text)
    except json.JSONDecodeError:
        return {"raw_text": text}
    return output if isinstance(output, dict) else {"raw_text": text}


def run_gateway(
    frozen: Path,
    models: list[str],
    out: Path,
    *,
    zdr: bool,
    no_training: bool,
    repeat: int = 1,
    seed: int | None = None,
) -> dict[str, Any]:
    """Issue one separate request per model per repeat. Never a fallback chain."""
    if repeat < 1:
        raise ValueError("repeat must be at least 1")
    require_key()  # fail closed before any network request, including the public catalogue
    prompt = build_user_prompt(frozen)
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    index = load_frozen(frozen)
    # Freeze exact model ids and published privacy metadata before any paid call.
    manifest = freeze_model_manifest(models, fetch_catalog())
    out.mkdir(parents=True, exist_ok=True)
    (out / "model-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    seed = _new_seed(seed)
    jobs = [{"model": m, "run": r} for r in range(1, repeat + 1) for m in models]
    results = []
    mapping = {}
    for i, job in enumerate(blind_order(jobs, seed), 1):
        arm = f"arm-{i}"
        call = complete(job["model"], prompt, zdr=zdr, no_training=no_training)
        raw = call["payload"]
        text = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        output = parse_output(text)
        errors = validate_model_output(output, index)
        usage = raw.get("usage") or {}
        gateway_meta = (raw.get("providerMetadata") or {}).get("gateway") or {}
        tokens = usage.get("total_tokens")
        if tokens is None:
            tokens = (usage.get("inputTokens") or 0) + (usage.get("outputTokens") or 0)
        receipt = {
            "arm": arm,
            "offline": False,
            "at": _now(),
            "latency_ms": call["latency_ms"],
            "tokens": tokens,
            "usage": usage,
            "cost": gateway_meta.get("cost", raw.get("cost")),
            "zdr": zdr,
            "disallow_prompt_training": no_training,
            "provider_options": call["provider_options"],
            # Stored whole. Which field proves ZDR routing is not verified against a live
            # response yet, so the receipt says so instead of inventing a field name.
            "gateway_metadata": gateway_meta,
            "zdr_confirmation": "unverified",
            "errors": errors,
            "output": {k: v for k, v in output.items() if k != "model"},
        }
        _write_private(out / f"{arm}.json", receipt)
        _write_private(
            out / f"{arm}.raw.json",
            {"request_prompt_hash": prompt_hash, "provider_options": call["provider_options"], "response": raw},
        )
        mapping[arm] = {"model": job["model"], "run": job["run"]}
        results.append({"arm": arm, "errors": errors})
    _write_blind(out, seed, mapping)
    summary = {"stage": 0, "offline": False, "repeat": repeat, "arms": results, "prompt_hash": prompt_hash}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf8")
    return summary
