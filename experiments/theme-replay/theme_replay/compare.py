"""Deterministic divergence view for arm M.

It shows overlap, unique readings, contested episodes, counterexamples and
repeat drift. It does not vote, rank, or produce one number. Agreement between
arms is a description, never evidence that a theme is correct.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .citations import load_frozen
from .review import load_receipts

# Two themes are the same reading when their supporting episode sets overlap
# by at least half (intersection over union). Fixed before any live output.
SAME_READING_OVERLAP = 0.5


def _overlap(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _cited(output: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    support: set[str] = set()
    against: set[str] = set()
    for code in output.get("codes") or []:
        support.update(code.get("episode_ids") or [])
        support.update(ev.get("episode_id") for ev in code.get("evidence") or [])
        against.update(row.get("episode_id") for row in code.get("counterevidence") or [])
    for theme in output.get("themes") or []:
        support.update(theme.get("supporting_episodes") or [])
        against.update(theme.get("disconfirming_episodes") or [])
    support.discard(None)
    against.discard(None)
    return support, against, support | against


def _clusters(nodes: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    parent = list(range(len(nodes)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if nodes[i]["arm"] == nodes[j]["arm"]:
                continue
            if _overlap(nodes[i]["support"], nodes[j]["support"]) >= SAME_READING_OVERLAP:
                parent[find(j)] = find(i)
    groups: dict[int, list[dict[str, Any]]] = {}
    for i, node in enumerate(nodes):
        groups.setdefault(find(i), []).append(node)
    return list(groups.values())


def _reading(group: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "arms": sorted({n["arm"] for n in group}),
        "themes": [{"arm": n["arm"], "name": n["name"], "central_concept": n["central_concept"],
                    "supporting": sorted(n["support"]), "disconfirming": sorted(n["against"])}
                   for n in group],
    }


def _drift(runs: Path, receipts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    blind_path = runs / "blind.json"
    if not blind_path.exists():
        return []
    arms = json.loads(blind_path.read_text(encoding="utf8"))["arms"]
    groups: dict[str, list[str]] = {}
    for arm in sorted(arms, key=lambda a: int(a.split("-")[1])):
        groups.setdefault(arms[arm]["model"], []).append(arm)
    rows = []
    for n, (_, members) in enumerate(groups.items(), 1):
        if len(members) < 2:
            continue
        concepts = []
        supports = []
        for arm in members:
            themes = (receipts.get(arm, {}).get("output") or {}).get("themes") or []
            concepts.append(sorted(t.get("central_concept") or "" for t in themes))
            supports.append(set().union(*[set(t.get("supporting_episodes") or []) for t in themes]) if themes else set())
        rows.append({
            "model_group": f"G{n}",
            "arms": members,
            "central_concepts_changed": any(c != concepts[0] for c in concepts[1:]),
            "supporting_overlap_min": round(min(_overlap(supports[0], s) for s in supports[1:]), 3),
        })
    return rows


def compare(frozen: Path, runs: Path) -> dict[str, Any]:
    index = load_frozen(frozen)
    all_ids = [row["episode_id"] for row in index["episodes"]]
    receipts = {r["arm"]: r for r in load_receipts(runs)}
    nodes = []
    arms_view = {}
    support_by_arm: dict[str, set[str]] = {}
    against_by_arm: dict[str, set[str]] = {}
    for arm, receipt in receipts.items():
        output = receipt.get("output") or {}
        support, against, cited = _cited(output)
        support_by_arm[arm] = support
        against_by_arm[arm] = against
        arms_view[arm] = {
            "themes": [t.get("name") for t in output.get("themes") or []],
            "codes": len(output.get("codes") or []),
            "cited_episodes": sorted(cited),
            "disconfirming": sorted(against),
            "named_failures": len(receipt.get("errors") or []),
            "questions_for_human": output.get("questions_for_human") or [],
        }
        for theme in output.get("themes") or []:
            nodes.append({
                "arm": arm,
                "name": theme.get("name"),
                "central_concept": theme.get("central_concept"),
                "support": set(theme.get("supporting_episodes") or []),
                "against": set(theme.get("disconfirming_episodes") or []),
            })
    clusters = _clusters(nodes)
    shared = [_reading(g) for g in clusters if len({n["arm"] for n in g}) > 1]
    unique = [_reading(g) for g in clusters if len({n["arm"] for n in g}) == 1]
    contested = []
    for ep in all_ids:
        pro = sorted(a for a, s in support_by_arm.items() if ep in s)
        con = sorted(a for a, s in against_by_arm.items() if ep in s)
        if pro and con and set(pro) != set(con):
            contested.append({"episode_id": ep, "supports_in": pro, "counterexample_in": con})
    cited_any = set().union(*support_by_arm.values(), *against_by_arm.values()) if receipts else set()
    report = {
        "rule": f"same reading when supporting-episode overlap >= {SAME_READING_OVERLAP}",
        "arms": arms_view,
        "shared_readings": shared,
        "unique_readings": unique,
        "contested_episodes": contested,
        "disconfirming_surfaced": sorted(set().union(*against_by_arm.values())) if receipts else [],
        "uncited_episodes": [ep for ep in all_ids if ep not in cited_any],
        "repeat_drift": _drift(runs, receipts),
        "note": "Descriptive only. Overlap is not validity. A unique reading is a question for the human, not an error.",
    }
    (runs / "compare.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    return report
