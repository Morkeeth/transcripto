"""Memo comparison: does model disagreement improve an evidence-linked analytic memo?

A fixed writer model stands in for the analyst. It writes one memo per
condition (B, S, R, M; see fixtures/memo-protocol.json). Every memo is scored
by deterministic rules that were frozen before any live output. The human
packet is blind: it carries memo text under shuffled P-ids and no scores.
"""

from __future__ import annotations

import hashlib
import json
import random
import tempfile
from pathlib import Path
from typing import Any

from .citations import check_status_claim, episode_map, load_frozen, resolve_quote
from .compare import compare
from .review import load_receipts
from .run import _now, _write_private, parse_output_step

HERE = Path(__file__).resolve().parent.parent
LETTERS = "ABC"


def corpus_lines(index: dict[str, Any]) -> str:
    rows = []
    for ep in index["episodes"]:
        rows.append(f"{ep['episode_id']} ({ep['harness']})")
        for line in ep["lines"]:
            rows.append(f"  {ep['episode_id']} L{line['n']} [{line['field']}] {line['text']}")
    return "\n".join(rows)


def _arms_by_model(runs: Path) -> dict[str, dict[int, str]]:
    blind = json.loads((runs / "blind.json").read_text(encoding="utf8"))["arms"]
    out: dict[str, dict[int, str]] = {}
    for arm, row in blind.items():
        out.setdefault(row["model"], {})[int(row["run"])] = arm
    return out


def _divergence(frozen: Path, receipts: list[dict[str, Any]]) -> dict[str, Any]:
    """Run the deterministic compare on a lettered subset. No blind key is present."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for i, receipt in enumerate(receipts, 1):
            row = dict(receipt)
            row["arm"] = f"arm-{i}"
            (tmp_path / f"arm-{i}.json").write_text(json.dumps(row), encoding="utf8")
        report = compare(frozen, tmp_path)
    text = json.dumps(
        {k: report[k] for k in ("rule", "shared_readings", "unique_readings", "contested_episodes",
                                "disconfirming_surfaced", "uncited_episodes", "note")}
    )
    for i in range(len(receipts), 0, -1):
        text = text.replace(f"arm-{i}", f"reading {LETTERS[i - 1]}")
    return json.loads(text)


def _reading_block(letter: str, receipt: dict[str, Any]) -> str:
    output = receipt.get("output") or {}
    return (
        f"READING {letter}\n"
        f"mechanical check: {json.dumps(receipt.get('errors') or [])}\n"
        f"{json.dumps(output, indent=1)}\n"
    )


def build_conditions(frozen: Path, runs: Path, models: list[str], seed: int) -> list[dict[str, Any]]:
    receipts = {r["arm"]: r for r in load_receipts(runs)}
    by_model = _arms_by_model(runs)
    rng = random.Random(seed)
    conditions: list[dict[str, Any]] = []
    for k in (1, 2, 3):
        conditions.append({"memo": f"B{k}", "condition": "B", "arms": []})
    for f, model in enumerate(models, 1):
        conditions.append({"memo": f"S{f}", "condition": "S", "arms": [by_model[model][1]]})
    for f, model in enumerate(models, 1):
        conditions.append({"memo": f"R{f}", "condition": "R", "arms": [by_model[model][r] for r in (1, 2, 3)]})
    for k in (1, 2, 3):
        conditions.append({"memo": f"M{k}", "condition": "M", "arms": [by_model[m][k] for m in models]})
    for row in conditions:
        arms = list(row["arms"])
        rng.shuffle(arms)
        row["arms"] = arms
        row["receipts"] = [receipts[a] for a in arms]
    return conditions


def build_prompt(frozen: Path, row: dict[str, Any]) -> str:
    index = load_frozen(frozen)
    question = (frozen / "question.txt").read_text(encoding="utf8").strip()
    instructions = (HERE / "fixtures" / "memo-prompt.txt").read_text(encoding="utf8").strip()
    parts = [instructions, "", "QUESTION", question, "", "CORPUS (numbered lines)", corpus_lines(index), ""]
    if not row["receipts"]:
        parts.append("CANDIDATE READINGS\nnone")
    else:
        parts.append("CANDIDATE READINGS")
        for letter, receipt in zip(LETTERS, row["receipts"]):
            parts.append(_reading_block(letter, receipt))
        if len(row["receipts"]) > 1:
            parts.append("DIVERGENCE VIEW (deterministic, descriptive only)")
            parts.append(json.dumps(_divergence(frozen, row["receipts"]), indent=1))
    return "\n".join(parts) + "\n"


def _field(episode: dict[str, Any], n: int) -> str | None:
    for line in episode["lines"]:
        if int(line["n"]) == int(n):
            return line["field"]
    return None


def score_memo(output: dict[str, Any], index: dict[str, Any]) -> dict[str, Any]:
    try:
        return _score_memo(output, index)
    except (TypeError, AttributeError, ValueError) as exc:
        return {"hard_failures": [f"memo does not follow the schema: {type(exc).__name__}"], "claims": 0,
                "proxies": {}, "proxy_count": 0}


def _score_memo(output: dict[str, Any], index: dict[str, Any]) -> dict[str, Any]:
    by_id = episode_map(index)
    hard: list[str] = []
    if not isinstance(output, dict) or "raw_text" in output or not isinstance(output.get("memo"), list):
        return {"hard_failures": ["output is not the JSON object"], "claims": 0, "proxies": {}, "proxy_count": 0}
    claims = output["memo"]
    cited_eps: set[str] = set()
    counter: set[str] = set()
    types = {"pattern": 0, "exception": 0, "open_question": 0, "other": 0}
    per_claim: list[list[tuple[str, int, str]]] = []
    unknown_lines: set[tuple[str, int]] = set()
    n_cites = 0
    for i, claim in enumerate(claims, 1):
        kind = (claim.get("type") or "").strip()
        types[kind if kind in types else "other"] += 1
        evidence = claim.get("evidence") or []
        if not evidence:
            hard.append(f"claim {i} cites no evidence")
        resolved: list[tuple[str, int, str]] = []
        for ev in evidence:
            n_cites += 1
            ep_id = ev.get("episode_id")
            episode = by_id.get(ep_id)
            if not episode:
                hard.append(f"claim {i} cites missing episode {ep_id}")
                continue
            try:
                line = int(ev.get("line")) if ev.get("line") is not None else None
            except (TypeError, ValueError):
                line = None
            hit = resolve_quote(episode, ev.get("quote", ""), line)
            if not hit["ok"]:
                hard.append(f"claim {i}: {hit['reason']}")
                continue
            status = check_status_claim(episode, hit["line"], ev.get("claimed_status"))
            if status:
                hard.append(f"claim {i}: {status}")
                continue
            field = _field(episode, hit["line"]) or ""
            resolved.append((ep_id, hit["line"], field))
            cited_eps.add(ep_id)
            if field == "event:unknown" and (ev.get("claimed_status") or "").lower() == "unknown":
                unknown_lines.add((ep_id, hit["line"]))
        for ep in claim.get("counter_episodes") or []:
            if ep not in by_id:
                hard.append(f"claim {i} counter names missing episode {ep}")
            else:
                counter.add(ep)
        per_claim.append(resolved)

    def any_claim(pred) -> bool:
        return any(pred(c) for c in per_claim)

    proxies = {
        "F1": any_claim(lambda c: len({e for e, _, f in c if f == "correction" and e in ("E04", "E08", "E12")}) >= 2),
        "F2": any_claim(lambda c: any(
            {f for e2, _, f in c if e2 == e} >= {"correction", "event:succeeded"} for e, _, _ in c)),
        "F3": len(unknown_lines) >= 2,
        "F4": any_claim(lambda c: len({e for e, _, f in c if f == "event:failed" and e in ("E02", "E06", "E10")}) >= 2),
        "F5": any_claim(lambda c: {"E02", "E04"} <= {e for e, _, _ in c}),
    }
    decisions: dict[str, int] = {}
    for row in output.get("reading_decisions") or []:
        d = str(row.get("decision", "")).upper()
        decisions[d] = decisions.get(d, 0) + 1
    return {
        "hard_failures": sorted(set(hard)),
        "claims": len(claims),
        "citations": n_cites,
        "types": types,
        "distinct_episodes_cited": len(cited_eps),
        "distinct_counter_episodes": len(counter),
        "proxies": proxies,
        "proxy_count": sum(proxies.values()),
        "reading_decisions": decisions,
    }


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def aggregate(scores: dict[str, dict[str, Any]], key: dict[str, str]) -> dict[str, Any]:
    by_cond: dict[str, list[dict[str, Any]]] = {}
    for memo, cond in key.items():
        if memo in scores:
            by_cond.setdefault(cond, []).append(scores[memo])
    table = {}
    for cond, rows in sorted(by_cond.items()):
        table[cond] = {
            "n": len(rows),
            "memos_with_hard_failure": sum(1 for r in rows if r["hard_failures"]),
            "hard_failures_total": sum(len(r["hard_failures"]) for r in rows),
            "proxy_count_mean": _mean([r["proxy_count"] for r in rows]),
            "proxy_counts": [r["proxy_count"] for r in rows],
            "exception_plus_open_mean": _mean([r.get("types", {}).get("exception", 0) + r.get("types", {}).get("open_question", 0) for r in rows]),
            "distinct_episodes_cited_mean": _mean([r.get("distinct_episodes_cited", 0) for r in rows]),
            "distinct_counter_episodes_mean": _mean([r.get("distinct_counter_episodes", 0) for r in rows]),
            "claims_mean": _mean([r["claims"] for r in rows]),
        }
    return table


def decide(table: dict[str, Any]) -> dict[str, Any]:
    m, r, s = table.get("M"), table.get("R"), table.get("S")
    if not (m and r and s):
        return {"answer": "CANNOT_TELL", "why": "a condition is missing"}
    gap_r = round(m["proxy_count_mean"] - r["proxy_count_mean"], 3)
    gap_s = round(m["proxy_count_mean"] - s["proxy_count_mean"], 3)
    if gap_r >= 1.0 and m["hard_failures_total"] == 0 and m["exception_plus_open_mean"] >= r["exception_plus_open_mean"]:
        answer = "YES"
    elif (gap_r <= 0 and gap_s <= 0) or m["hard_failures_total"] > r["hard_failures_total"]:
        answer = "NO"
    else:
        answer = "CANNOT_TELL"
    return {"answer": answer, "M_minus_R_proxy": gap_r, "M_minus_S_proxy": gap_s,
            "rule": "fixtures/memo-protocol.json decision_rule, frozen before any live output"}


def run_memos(frozen: Path, runs: Path, out: Path, *, models: list[str], writer: str,
              ledger_path: Path, max_cost: float, seed: int, max_tokens: int = 12000) -> dict[str, Any]:
    from . import openrouter

    openrouter.require_key()
    ledger = openrouter.Ledger(ledger_path, max_cost)
    ledger.check()
    index = load_frozen(frozen)
    out.mkdir(parents=True, exist_ok=True)
    manifest = openrouter.freeze_manifest([writer], openrouter.fetch_catalog())
    (out / "writer-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    rows = build_conditions(frozen, runs, models, seed)
    key: dict[str, str] = {}
    calls = []
    for row in rows:
        ledger.check()
        prompt = build_prompt(frozen, row)
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        key[row["memo"]] = row["condition"]
        record: dict[str, Any] = {"memo": row["memo"], "condition": row["condition"], "arms": row["arms"],
                                  "prompt_sha256": prompt_hash, "prompt_chars": len(prompt), "at": _now()}
        try:
            call = openrouter.complete(writer, prompt, max_tokens=max_tokens)
        except RuntimeError as exc:
            record.update({"call_failed": str(exc)[:300], "score": {"hard_failures": ["call failed"], "claims": 0, "proxies": {}, "proxy_count": 0}})
            _write_private(out / f"memo-{row['memo']}.json", record)
            calls.append(record)
            continue
        raw = call["payload"]
        choice = (raw.get("choices") or [{}])[0]
        text = (choice.get("message") or {}).get("content") or ""
        usage = openrouter.usage_numbers(raw)
        ledger.add(f"memo-{row['memo']}", writer, usage["cost_usd"])
        output, step = parse_output_step(text)
        record.update({
            "latency_ms": call["latency_ms"], "usage": usage, "finish_reason": choice.get("finish_reason"),
            "upstream_provider": raw.get("provider"), "parse_step": step, "output": output,
            "score": score_memo(output, index),
        })
        _write_private(out / f"memo-{row['memo']}.json", record)
        _write_private(out / f"memo-{row['memo']}.prompt.json", {"prompt": prompt, "sha256": prompt_hash})
        calls.append(record)
        if usage["cost_usd"] is None:
            raise openrouter.SpendCeiling("writer returned no usage.cost; stopping")
    return finish(out, calls, seed, ledger.spent)


def finish(out: Path, calls: list[dict[str, Any]], seed: int, spent: float) -> dict[str, Any]:
    key = {c["memo"]: c["condition"] for c in calls}
    scores = {c["memo"]: c["score"] for c in calls}
    table = aggregate(scores, key)
    verdict = decide(table)
    report = {
        "question": "Does model disagreement improve an evidence-linked analytic memo?",
        "verdict": verdict,
        "by_condition": table,
        "per_memo": [
            {"memo": c["memo"], "condition": c["condition"], "latency_ms": c.get("latency_ms"),
             "usage": c.get("usage"), "parse_step": c.get("parse_step"), "finish_reason": c.get("finish_reason"),
             "call_failed": c.get("call_failed"), **c["score"]}
            for c in calls
        ],
        "spent_usd_ledger_total": spent,
    }
    (out / "memo-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    write_packet(out, calls, seed)
    return report


def write_packet(out: Path, calls: list[dict[str, Any]], seed: int) -> None:
    """Blind human packet: memo text under shuffled P-ids, no condition, no score."""
    order = [c for c in calls if isinstance(c.get("output"), dict) and isinstance(c["output"].get("memo"), list)]
    random.Random(seed + 7919).shuffle(order)
    lines = [
        "# Theme Replay Stage 0 · blind memo packet",
        "",
        "Question: What makes an agent-work episode require correction?",
        "",
        "Rate each memo before you open memo-report.json. For each memo write KEEP, REVISE or REJECT and one sentence.",
        "Also rank the three memos you find most useful. Citations are `Eyy Ln`; open them with `corpus-lines.txt`.",
        "",
    ]
    key = {}
    for i, c in enumerate(order, 1):
        pid = f"P{i:02d}"
        key[pid] = c["memo"]
        lines.append(f"## {pid}")
        lines.append("")
        for claim in c["output"]["memo"]:
            cites = ", ".join(f"{e.get('episode_id')} L{e.get('line')}" for e in claim.get("evidence") or [])
            counter = ", ".join(claim.get("counter_episodes") or [])
            lines.append(f"- ({claim.get('type')}) {claim.get('claim')}  [{cites}]" + (f"  counter: {counter}" if counter else ""))
        lines.append("")
        lines.append("Decision: ______  Sentence: ______________________")
        lines.append("")
    (out / "human-packet.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    _write_private(out / "packet-key.json", {"note": "Unblinding key. Open only after Oscar rates.", "key": key})
