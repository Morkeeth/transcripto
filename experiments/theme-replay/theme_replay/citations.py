"""Exact citation and status checks against a frozen corpus."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import FORBIDDEN_PATH_MARKERS, STATUSES


def load_frozen(frozen_dir: str | Path) -> dict[str, Any]:
    root = Path(frozen_dir)
    index = json.loads((root / "corpus-index.json").read_text(encoding="utf8"))
    return index


def episode_map(index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["episode_id"]: row for row in index["episodes"]}


def resolve_quote(episode: dict[str, Any], quote: str, line: int | None) -> dict[str, Any]:
    quote = (quote or "").strip()
    if not quote:
        return {"ok": False, "reason": "empty quote"}
    lines = {int(item["n"]): item["text"] for item in episode["lines"]}
    if line is not None:
        text = lines.get(int(line))
        if text is None:
            return {"ok": False, "reason": f"line {line} is not in {episode['episode_id']}"}
        if quote not in text:
            return {
                "ok": False,
                "reason": f"quote does not resolve on {episode['episode_id']} line {line}",
            }
        return {"ok": True, "episode_id": episode["episode_id"], "line": int(line), "text": text}
    for n, text in lines.items():
        if quote in text:
            return {"ok": True, "episode_id": episode["episode_id"], "line": n, "text": text}
    return {"ok": False, "reason": f"quote does not resolve in {episode['episode_id']}"}


def check_status_claim(episode: dict[str, Any], line: int | None, claimed: str | None) -> str | None:
    """A claimed status must equal the status recorded on the cited line.

    Checking against the episode as a whole let a failed line pass as succeeded
    whenever some other event in the same episode succeeded.
    """
    if not claimed:
        return None
    claimed = claimed.strip().lower()
    if claimed not in STATUSES:
        return f"unknown status {claimed}"
    if line is None:
        return f"{episode['episode_id']} claims status {claimed} without a line"
    row = next((item for item in episode["lines"] if int(item["n"]) == int(line)), None)
    if row is None or not str(row.get("field", "")).startswith("event:"):
        return f"{episode['episode_id']} line {line} is not a tool result, so it has no status"
    actual = row["field"].split(":", 1)[1]
    if actual != claimed:
        return f"{episode['episode_id']} line {line} records {actual}, claim says {claimed}"
    return None


def validate_model_output(output: Any, index: dict[str, Any]) -> list[str]:
    """Name every failure. Never skip an arm because a key is missing."""
    if not isinstance(output, dict) or "raw_text" in output:
        return ["model did not return the JSON schema"]
    errors: list[str] = []
    by_id = episode_map(index)
    dumped = json.dumps(output)
    for marker in FORBIDDEN_PATH_MARKERS:
        if marker in dumped:
            errors.append(f"private-path marker {marker} entered a model output")
    codes = output.get("codes") or []
    themes = output.get("themes") or []
    if not codes:
        errors.append("output has no codes")
    if not themes:
        errors.append("output has no themes")
    labels = {code.get("label") for code in codes}
    for code in codes:
        name = code.get("label")
        if not code.get("evidence"):
            errors.append(f"code {name!r} cites no evidence")
        errors.extend(_check_bundle(code, by_id, "code"))
        errors.extend(_check_ids(code.get("episode_ids"), by_id, f"code {name!r} episode_ids"))
        errors.extend(
            _check_ids(
                [row.get("episode_id") for row in code.get("counterevidence") or []],
                by_id,
                f"code {name!r} counterevidence",
            )
        )
    for theme in themes:
        name = theme.get("name")
        errors.extend(_check_bundle(theme, by_id, "theme"))
        if not theme.get("disconfirming_episodes"):
            errors.append(f"theme {name!r} has no disconfirming episode")
        errors.extend(_check_ids(theme.get("supporting_episodes"), by_id, f"theme {name!r} supporting"))
        errors.extend(_check_ids(theme.get("disconfirming_episodes"), by_id, f"theme {name!r} disconfirming"))
        for label in theme.get("codes") or []:
            if label not in labels:
                errors.append(f"theme {name!r} names code {label!r} that no code defines")
    return errors


def _check_ids(ids: Any, by_id: dict[str, dict[str, Any]], where: str) -> list[str]:
    return [f"{where} names missing episode {ep}" for ep in (ids or []) if ep not in by_id]


def _check_bundle(bundle: dict[str, Any], by_id: dict[str, dict[str, Any]], kind: str) -> list[str]:
    errors: list[str] = []
    for ev in bundle.get("evidence") or []:
        ep_id = ev.get("episode_id")
        episode = by_id.get(ep_id)
        if not episode:
            errors.append(f"{kind} cites missing episode {ep_id}")
            continue
        hit = resolve_quote(episode, ev.get("quote", ""), ev.get("line"))
        if not hit["ok"]:
            errors.append(hit["reason"])
            continue
        status = check_status_claim(episode, hit["line"], ev.get("claimed_status"))
        if status:
            errors.append(status)
    return errors


def flatten_episode(episode: dict[str, Any]) -> list[dict[str, Any]]:
    lines = [{"n": 1, "field": "request", "text": episode["request"]}]
    n = 2
    if episode.get("correction"):
        lines.append({"n": n, "field": "correction", "text": episode["correction"]})
        n += 1
    for event in episode.get("events") or []:
        lines.append(
            {
                "n": n,
                "field": f"event:{event['status']}",
                "text": f"{event['tool']} {event['target']} {event['status']}: {event['evidence']}",
            }
        )
        n += 1
    return lines
