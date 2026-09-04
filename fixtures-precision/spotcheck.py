#!/usr/bin/env python3
"""Resolve the correction labels back to their text, on this machine only.

    python3 fixtures-precision/spotcheck.py            # 20 rows, seeded
    python3 fixtures-precision/spotcheck.py --all      # every labelled row
    python3 fixtures-precision/spotcheck.py --group flagged --label NOT

`labels-2026-09-03.jsonl` is LOCAL-ONLY (gitignored, never committed). It
carries no transcript text — only a session id, a turn uuid and the label — but
those ids point at the operator's real sessions, and this repo is public. Every
fixture that IS in git is synthetic.

So the text stays where it already is — in ~/.claude/projects, on the machine
that wrote it — and this script joins the two at read time. On any other machine
the labels file is absent and the script says so and exits.
"""
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import transcripto as T  # noqa: E402

LABELS = os.path.join(HERE, "labels-2026-09-03.jsonl")


def index_by_uuid(wanted):
    """uuid -> text, for the wanted uuids only. One pass over the local logs."""
    found = {}
    for p in T._coach_files(T._coach_roots(None, "claude"), "claude"):
        rows, fh = T._rows_for_file(p)
        if fh == "codex-history":
            continue
        for row in rows:
            u = row.get("uuid")
            if u in wanted and u not in found:
                t = T._human_prompt(row)
                if t:
                    found[u] = t
        if len(found) == len(wanted):
            break
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--group", choices=["flagged", "unflagged"])
    ap.add_argument("--label", choices=["CORRECTION", "NOT"])
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--chars", type=int, default=220)
    a = ap.parse_args()

    if not os.path.exists(LABELS):
        sys.exit("no labels file at %s (it is local-only and never committed; "
                 "see docs/CORRECTION-PRECISION-2026-09-03.md)" % LABELS)
    rows = [json.loads(l) for l in open(LABELS) if l.strip()]
    if a.group:
        rows = [r for r in rows if r["group"] == a.group]
    if a.label:
        rows = [r for r in rows if r["label"] == a.label]
    if not a.all:
        rows = random.Random(20260903).sample(rows, min(a.n, len(rows)))

    text = index_by_uuid({r["uuid"] for r in rows})
    agree = 0
    for r in rows:
        t = " ".join(text.get(r["uuid"], "<not found in local logs>").split())
        verdict = "TP" if r["flagged"] and r["label"] == "CORRECTION" else \
                  "FP" if r["flagged"] else \
                  "FN" if r["label"] == "CORRECTION" else "TN"
        agree += verdict in ("TP", "TN")
        print("[%s] flagged=%-5s label=%-10s w=%d\n     %s\n"
              % (verdict, r["flagged"], r["label"], r["words"], t[:a.chars]))
    print("%d rows · classifier and label agree on %d" % (len(rows), agree))


if __name__ == "__main__":
    main()
