"""OpenRouter transport for generative Theme Replay arms.

Added 2026-09-22 because the Vercel AI Gateway path has no key on this machine.
This is a different transport, and receipts say so: `transport: openrouter`.
It never writes `providerOptions.gateway` and never freezes a Vercel manifest.

Stage 0 is synthetic. The request still asks for `zdr: true` and
`data_collection: deny`. Whether a provider honoured that is recorded as
`unverified`. Stage 1 real data must not use this path until that is proven.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from .gateway import assert_generative_model

CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_URL = "https://openrouter.ai/api/v1/models"
KEEP_FIELDS = ("id", "name", "created", "context_length", "pricing", "supported_parameters", "top_provider")
DEFAULT_MAX_TOKENS = 12000


class SpendCeiling(RuntimeError):
    """Raised before a call when the ledger has reached the ceiling."""


def require_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY missing. Stage 0 can use --offline.")
    return key


def request_body(model: str, prompt: str, *, max_tokens: int = DEFAULT_MAX_TOKENS) -> dict[str, Any]:
    assert_generative_model(model)
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        # Asked for, not proven. See module docstring.
        "provider": {"zdr": True, "data_collection": "deny", "allow_fallbacks": True},
        # Returns usage.cost in USD on the response.
        "usage": {"include": True},
    }


def complete(model: str, prompt: str, *, max_tokens: int = DEFAULT_MAX_TOKENS, timeout: int = 600) -> dict[str, Any]:
    body = request_body(model, prompt, max_tokens=max_tokens)
    key = require_key()
    request = urllib.request.Request(
        CHAT_URL,
        data=json.dumps(body).encode("utf8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf8"))
            status = response.status
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf8", "replace")[:400]
        raise RuntimeError(f"OpenRouter {model} failed: HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter {model} unreachable: {exc.reason}") from exc
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    return {
        "payload": payload,
        "http_status": status,
        "latency_ms": latency_ms,
        "request_meta": {k: v for k, v in body.items() if k != "messages"},
    }


def usage_numbers(payload: dict[str, Any]) -> dict[str, Any]:
    usage = payload.get("usage") or {}
    return {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "cost_usd": usage.get("cost"),
    }


def fetch_catalog(url: str = MODELS_URL) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf8"))


def freeze_manifest(models: list[str], catalog: dict[str, Any]) -> dict[str, Any]:
    rows = {row.get("id"): row for row in (catalog.get("data") or [])}
    missing = [m for m in models if m not in rows]
    if missing:
        raise RuntimeError("Model manifest refused before any call: not in OpenRouter catalogue: " + ", ".join(missing))
    frozen = []
    for model in models:
        row = {key: rows[model].get(key) for key in KEEP_FIELDS}
        row["temperature_supported"] = "temperature" in (rows[model].get("supported_parameters") or [])
        frozen.append(row)
    body = json.dumps(frozen, sort_keys=True)
    return {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "transport": "openrouter",
        "source": MODELS_URL,
        "models": frozen,
        "sha256": hashlib.sha256(body.encode()).hexdigest(),
        "note": "No temperature is sent. temperature_supported is recorded, not equalised. ZDR routing is requested, not proven.",
    }


class Ledger:
    """Running USD spend across every command that shares one ledger file."""

    def __init__(self, path, ceiling: float):
        from pathlib import Path

        self.path = Path(path)
        self.ceiling = float(ceiling)
        self.rows = json.loads(self.path.read_text(encoding="utf8"))["calls"] if self.path.exists() else []

    @property
    def spent(self) -> float:
        return round(sum(float(r.get("cost_usd") or 0) for r in self.rows), 6)

    def check(self) -> None:
        if self.spent >= self.ceiling:
            raise SpendCeiling(f"spend {self.spent} USD reached ceiling {self.ceiling} USD; no further calls")

    def add(self, label: str, model: str, cost: Any) -> None:
        self.rows.append({"label": label, "model": model, "cost_usd": cost})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"ceiling_usd": self.ceiling, "spent_usd": self.spent, "calls": self.rows}, indent=2) + "\n",
            encoding="utf8",
        )
