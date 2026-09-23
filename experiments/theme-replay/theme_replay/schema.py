"""Frozen Stage 0 schema. No private transcript fields."""

from __future__ import annotations

REQUIRED_EPISODE = (
    "episode_id",
    "harness",
    "kind",
    "provenance",
    "request",
    "events",
)
REQUIRED_EVENT = ("tool", "kind", "target", "status", "evidence")
HARNESSES = ("claude", "codex", "cursor")
KINDS = ("succeeded", "failed", "unknown", "changed-decision")
STATUSES = ("succeeded", "failed", "unknown")
DECISIONS = ("KEEP", "REVISE", "REJECT")
DECISION_ALIASES = {
    "CHANGES_MY_VIEW": "REVISE",
    "CHANGES MY VIEW": "REVISE",
    "CHANGE": "REVISE",
}
FORBIDDEN_PATH_MARKERS = (
    "/Users/",
    "/home/",
    "Library/Mobile Documents",
    ".claude/projects",
    ".codex/sessions",
    ".cursor/projects",
)


def normalize_decision(value: str) -> str:
    raw = (value or "").strip().upper().replace("-", "_")
    raw = DECISION_ALIASES.get(raw, raw)
    if raw not in DECISIONS:
        raise ValueError("decision must be KEEP, REVISE, or REJECT")
    return raw
