"""Freeze the Gateway model manifest before any generative call.

The catalogue at /v1/models is public and needs no key. Nothing from the corpus
is sent. A requested model that is missing, or that publishes no ZDR or
no-training route, stops the run before a paid request.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from typing import Any

MODELS_URL = "https://ai-gateway.vercel.sh/v1/models"
KEEP_FIELDS = (
    "id", "owned_by", "name", "released", "zdr", "no_training", "temperature",
    "supported_parameters", "pricing", "regions", "context_window", "max_tokens",
)
ACCEPTED_PRIVACY = ("all", "some")


def fetch_catalog(url: str = MODELS_URL) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf8"))


def freeze_model_manifest(models: list[str], catalog: dict[str, Any]) -> dict[str, Any]:
    rows = {row.get("id"): row for row in (catalog.get("data") or [])}
    frozen = []
    problems = []
    for model in models:
        row = rows.get(model)
        if row is None:
            problems.append(f"{model} is not in the Gateway catalogue")
            continue
        if row.get("zdr") not in ACCEPTED_PRIVACY:
            problems.append(f"{model} publishes zdr={row.get('zdr')!r}")
        if row.get("no_training") not in ACCEPTED_PRIVACY:
            problems.append(f"{model} publishes no_training={row.get('no_training')!r}")
        frozen.append({key: row.get(key) for key in KEEP_FIELDS})
    if problems:
        raise RuntimeError("Model manifest refused before any call: " + "; ".join(problems))
    body = json.dumps(frozen, sort_keys=True)
    return {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "source": MODELS_URL,
        "models": frozen,
        "sha256": hashlib.sha256(body.encode()).hexdigest(),
        "note": "temperature=false means the model does not take a temperature setting. Recorded, not equalised.",
    }
