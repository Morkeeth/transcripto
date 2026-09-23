"""python -m theme_replay freeze|run|verify|compare|review"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .compare import compare
from .freeze import freeze
from .review import record_decision, render
from .run import run_gateway, run_offline, run_openrouter
from .verify import verify


def _here() -> Path:
    return Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="theme_replay")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_freeze = sub.add_parser("freeze")
    p_freeze.add_argument("source", nargs="+")
    p_freeze.add_argument("--question", required=True)
    p_freeze.add_argument("--prompt", dest="prompt_file")
    p_freeze.add_argument("--protocol")
    p_freeze.add_argument("--out", required=True)

    p_run = sub.add_parser("run")
    p_run.add_argument("frozen")
    p_run.add_argument("--models", default="")
    p_run.add_argument("--offline")
    p_run.add_argument("--out", required=True)
    p_run.add_argument("--zdr", action="store_true")
    p_run.add_argument("--no-training", action="store_true")
    p_run.add_argument("--repeat", type=int, default=1)
    p_run.add_argument("--seed", type=int)
    p_run.add_argument("--transport", choices=("gateway", "openrouter"), default="gateway")
    p_run.add_argument("--max-cost", type=float, default=10.0, help="USD ceiling across the shared ledger")
    p_run.add_argument("--ledger", help="spend ledger JSON; default <out>/../spend.json")
    p_run.add_argument("--max-tokens", type=int)

    p_memo = sub.add_parser("memo", help="memo comparison B/S/R/M with a fixed writer model")
    p_memo.add_argument("frozen")
    p_memo.add_argument("runs")
    p_memo.add_argument("--out", required=True)
    p_memo.add_argument("--models", required=True)
    p_memo.add_argument("--writer", required=True)
    p_memo.add_argument("--seed", type=int, required=True)
    p_memo.add_argument("--max-cost", type=float, default=10.0)
    p_memo.add_argument("--ledger")

    p_pub = sub.add_parser("publish", help="copy blind aggregate results out of .trial")
    p_pub.add_argument("trial")
    p_pub.add_argument("results")

    p_rescore = sub.add_parser("rescore", help="re-verify and re-score committed results, no network")
    p_rescore.add_argument("results")

    p_lines = sub.add_parser("corpus-lines", help="print the frozen corpus as numbered citation lines")
    p_lines.add_argument("frozen")

    p_compare = sub.add_parser("compare")
    p_compare.add_argument("frozen")
    p_compare.add_argument("runs")

    p_verify = sub.add_parser("verify")
    p_verify.add_argument("frozen")
    p_verify.add_argument("runs")

    p_review = sub.add_parser("review")
    p_review.add_argument("runs")
    p_review.add_argument("--frozen")
    p_review.add_argument("--decide", nargs=3, metavar=("CLAIM", "DECISION", "SENTENCE"))

    args = parser.parse_args(argv)
    if args.cmd == "freeze":
        source = Path(args.source[0])
        question = Path(args.question).read_text(encoding="utf8") if Path(args.question).exists() else args.question
        prompt_path = Path(args.prompt_file) if args.prompt_file else _here() / "fixtures" / "analysis-prompt.txt"
        protocol_path = Path(args.protocol) if args.protocol else _here() / "fixtures" / "protocol.json"
        manifest = freeze(
            source,
            Path(args.out),
            question=question,
            prompt=prompt_path.read_text(encoding="utf8"),
            protocol=json.loads(protocol_path.read_text(encoding="utf8")),
        )
        print(json.dumps({"ok": True, "manifest": manifest["files"]}, indent=2))
        return 0
    if args.cmd == "run":
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        if args.offline:
            summary = run_offline(Path(args.frozen), Path(args.offline), out, seed=args.seed)
        else:
            models = [item.strip() for item in args.models.split(",") if item.strip()]
            if not models:
                raise SystemExit("run needs --offline or --models")
            if args.transport == "openrouter":
                summary = run_openrouter(
                    Path(args.frozen),
                    models,
                    out,
                    ledger_path=Path(args.ledger) if args.ledger else out.parent / "spend.json",
                    max_cost=args.max_cost,
                    repeat=args.repeat,
                    seed=args.seed,
                    max_tokens=args.max_tokens,
                )
                print(json.dumps(summary, indent=2))
                return 0
            summary = run_gateway(
                Path(args.frozen),
                models,
                out,
                zdr=args.zdr,
                no_training=args.no_training,
                repeat=args.repeat,
                seed=args.seed,
            )
        print(json.dumps(summary, indent=2))
        return 0
    if args.cmd == "memo":
        from .memo import run_memos

        out = Path(args.out)
        report = run_memos(
            Path(args.frozen),
            Path(args.runs),
            out,
            models=[m.strip() for m in args.models.split(",") if m.strip()],
            writer=args.writer,
            ledger_path=Path(args.ledger) if args.ledger else out.parent / "spend.json",
            max_cost=args.max_cost,
            seed=args.seed,
        )
        print(json.dumps({"verdict": report["verdict"], "by_condition": report["by_condition"],
                          "spent_usd": report["spent_usd_ledger_total"]}, indent=2))
        return 0
    if args.cmd == "publish":
        from .publish import publish

        print(json.dumps({"copied": publish(Path(args.trial), Path(args.results))}, indent=2))
        return 0
    if args.cmd == "rescore":
        from .publish import rescore

        report = rescore(Path(args.results))
        print(json.dumps(report, indent=2))
        return 0 if report["corpus_hash_matches"] and report["matches_committed_verdict"] else 2
    if args.cmd == "corpus-lines":
        from .citations import load_frozen
        from .memo import corpus_lines

        print(corpus_lines(load_frozen(Path(args.frozen))))
        return 0
    if args.cmd == "verify":
        report = verify(Path(args.frozen), Path(args.runs))
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 2
    if args.cmd == "compare":
        print(json.dumps(compare(Path(args.frozen), Path(args.runs)), indent=2))
        return 0
    if args.cmd == "review":
        frozen = Path(args.frozen) if args.frozen else Path(args.runs).parent / "frozen"
        print(render(frozen, Path(args.runs)))
        if args.decide:
            row = record_decision(Path(args.runs), args.decide[0], args.decide[1], args.decide[2])
            print(json.dumps(row))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
