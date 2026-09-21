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


def check_status_upgrade(episode: dict[str, Any], claimed: str | None) -> dict[str, Any] | None:
    if not claimed:
        return None
    claimed = claimed.strip().lower()
    actual = {event["status"] for event in episode["events"]}
    if claimed == "succeeded" and actual and actual <= {"failed", "unknown"}:
        return {
            "ok": False,
            "reason": f"{episode['episode_id']} upgrades {sorted(actual)} to succeeded",
        }
    if claimed not in STATUSES:
        return {"ok": False, "reason": f"unknown status {claimed}"}
    return None


def validate_model_output(output: dict[str, Any], index: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    by_id = episode_map(index)
    dumped = json.dumps(output)
    for marker in FORBIDDEN_PATH_MARKERS:
        if marker in dumped:
            errors.append(f"private-path marker {marker} entered a model output")
    for code in output.get("codes") or []:
        errors.extend(_check_bundle(code, by_id, "code"))
    for theme in output.get("themes") or []:
        errors.extend(_check_bundle(theme, by_id, "theme"))
        if not theme.get("disconfirming_episodes"):
            errors.append(f"theme {theme.get('name')!r} has no disconfirming episode")
    return errors


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
        upgrade = check_status_upgrade(episode, ev.get("claimed_status"))
        if upgrade:
            errors.append(upgrade["reason"])
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
