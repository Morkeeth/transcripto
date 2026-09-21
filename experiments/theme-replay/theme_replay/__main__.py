"""python -m theme_replay freeze|run|verify|review"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .freeze import freeze
from .review import record_decision, render
from .run import run_gateway, run_offline
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
            summary = run_offline(Path(args.frozen), Path(args.offline), out)
        else:
            models = [item.strip() for item in args.models.split(",") if item.strip()]
            if not models:
                raise SystemExit("run needs --offline or --models")
            summary = run_gateway(
                Path(args.frozen),
                models,
                out,
                zdr=args.zdr,
                no_training=args.no_training,
            )
        print(json.dumps(summary, indent=2))
        return 0
    if args.cmd == "verify":
        report = verify(Path(args.frozen), Path(args.runs))
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 2
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
