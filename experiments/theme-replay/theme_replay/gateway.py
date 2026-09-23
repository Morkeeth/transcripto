"""Optional Vercel AI Gateway client for generative Theme Replay arms.

This module posts to /v1/chat/completions only. Jev and other evaluation
models use POST /v1/evaluate and are a separate trial. Fail closed. Never
the Transcripto default path.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse


CHAT_COMPLETIONS_URL = "https://ai-gateway.vercel.sh/v1/chat/completions"
EVALUATE_URL = "https://ai-gateway.vercel.sh/v1/evaluate"
DEFAULT_GATEWAY_URL = CHAT_COMPLETIONS_URL


def gateway_url() -> str:
    return os.environ.get("AI_GATEWAY_URL", DEFAULT_GATEWAY_URL)


def require_key() -> str:
    key = os.environ.get("AI_GATEWAY_API_KEY") or os.environ.get("VERCEL_AI_GATEWAY_API_KEY")
    if not key:
        raise RuntimeError(
            "Gateway key missing. Stage 0 can use --offline. Live runs need AI_GATEWAY_API_KEY."
        )
    return key


def assert_generative_model(model: str) -> None:
    lowered = (model or "").strip().lower()
    if not lowered:
        raise RuntimeError("Live generative Gateway runs need a model id.")
    if "jev" in lowered:
        raise RuntimeError(
            f"{model} is an evaluation model. Jev uses POST {EVALUATE_URL}, "
            "not /v1/chat/completions. Keep generative Theme Replay arms and Jev trials distinct."
        )


def assert_chat_completions_url(url: str) -> None:
    path = urlparse(url).path.rstrip("/")
    if path.endswith("/evaluate"):
        raise RuntimeError(
            f"{url} is the evaluation endpoint. Generative arms use {CHAT_COMPLETIONS_URL}. "
            "Keep generative Theme Replay arms and Jev trials distinct."
        )
    if not path.endswith("/chat/completions"):
        raise RuntimeError(
            f"{url} is not /v1/chat/completions. Generative Theme Replay arms use "
            f"{CHAT_COMPLETIONS_URL}."
        )


def provider_options(*, zdr: bool, no_training: bool) -> dict[str, Any]:
    if not zdr or not no_training:
        raise RuntimeError(
            "Live generative Gateway runs require --zdr and --no-training "
            "(providerOptions.gateway.zeroDataRetention and disallowPromptTraining)."
        )
    return {
        "gateway": {
            "zeroDataRetention": True,
            "disallowPromptTraining": True,
        }
    }


def chat_completions_body(model: str, prompt: str, *, zdr: bool, no_training: bool) -> dict[str, Any]:
    assert_generative_model(model)
    options = provider_options(zdr=zdr, no_training=no_training)
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "providerOptions": options,
    }


def complete(model: str, prompt: str, *, zdr: bool, no_training: bool) -> dict[str, Any]:
    """POST /v1/chat/completions. Returns payload, wall-clock latency_ms, and providerOptions sent."""
    body = chat_completions_body(model, prompt, zdr=zdr, no_training=no_training)
    url = gateway_url()
    assert_chat_completions_url(url)
    key = require_key()
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read()
            payload = json.loads(raw.decode("utf8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Gateway {model} failed: {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Gateway {model} unreachable") from exc
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    return {
        "payload": payload,
        "latency_ms": latency_ms,
        "provider_options": body["providerOptions"],
    }
