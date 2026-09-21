"""Optional Vercel AI Gateway client. Fail closed. Never the Transcripto default path."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


GATEWAY_URL = os.environ.get(
    "AI_GATEWAY_URL",
    "https://ai-gateway.vercel.sh/v1/chat/completions",
)


def require_key() -> str:
    key = os.environ.get("AI_GATEWAY_API_KEY") or os.environ.get("VERCEL_AI_GATEWAY_API_KEY")
    if not key:
        raise RuntimeError(
            "Gateway key missing. Stage 0 can use --offline. Live runs need AI_GATEWAY_API_KEY."
        )
    return key


def complete(model: str, prompt: str, *, zdr: bool, no_training: bool) -> dict[str, Any]:
    key = require_key()
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "zeroDataRetention": zdr,
        "disallowPromptTraining": no_training,
    }
    request = urllib.request.Request(
        GATEWAY_URL,
        data=json.dumps(body).encode("utf8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read()
            payload = json.loads(raw.decode("utf8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Gateway {model} failed: {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Gateway {model} unreachable") from exc
    return payload
