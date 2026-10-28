"""Command-line entry point for public benchmark tools."""

import argparse
import json
import sys
from importlib.resources import files
from pathlib import Path


def public_ids():
    return files("codesignbench").joinpath("resources/case_ids_me96.txt").read_text().splitlines()


def load_cases(path):
    with Path(path).open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, list) or not value:
        raise ValueError("cases.json must be a nonempty array")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(prog="cdb", description="Co-Design Bench public tools")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="list the 96 public ME task IDs")

    prepare = commands.add_parser("prepare", help="bind fixed criteria to candidate workspaces")
    prepare.add_argument("--dataset", required=True, type=Path, help="extracted evaluation archive root")
    prepare.add_argument("--submissions", required=True, type=Path, help="candidate applications under <case_id>/")
    prepare.add_argument("--out", required=True, type=Path, help="directory to write cases.json")
    prepare.add_argument("--case", action="append", help="public task ID to include; repeat for a subset")

    judge = commands.add_parser("judge", help="run a reference Claude judge and a separate refutation pass")
    judge.add_argument("--cases", required=True, type=Path)
    judge.add_argument("--out", required=True, type=Path)
    judge.add_argument("--model", required=True, help="model name accepted by your Claude CLI")
    judge.add_argument("--claude-bin", default="claude")
    judge.add_argument("--concurrency", type=int, default=1)
    judge.add_argument("--timeout", type=int, default=1800, help="seconds per agent stage or application build")

    score = commands.add_parser("score", help="compute task-weighted scores from fixed final verdicts")
    score.add_argument("--cases", required=True, type=Path)
    score.add_argument("--results", required=True, type=Path, help="final journal.jsonl or result JSON")
    score.add_argument("--out", type=Path, help="optional JSON report path")

    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            print("\n".join(public_ids()))
        elif args.command == "prepare":
            from .data import prepare_cases

            whitelist = public_ids()
            if args.case:
                unknown = set(args.case) - set(whitelist)
                if unknown:
                    raise ValueError("unknown public task IDs: " + ", ".join(sorted(unknown)))
                if len(set(args.case)) != len(args.case):
                    raise ValueError("duplicate --case IDs")
                selected = set(args.case)
                whitelist = [task_id for task_id in whitelist if task_id in selected]
            result = prepare_cases(args.dataset, args.submissions, args.out, whitelist,
                                   expected_criterion_count=521 if len(whitelist) == 96 else None)
            print(json.dumps(result, indent=2))
        elif args.command == "judge":
            from .judge import run_judge

            if args.concurrency < 1 or args.timeout < 1:
                raise ValueError("concurrency and timeout must be positive")
            cases = load_cases(args.cases)
            ok = run_judge(cases, args.out, args.model, args.claude_bin, args.concurrency, args.timeout)
            if not ok:
                return 1
        elif args.command == "score":
            from .scoring import load_results, score_results

            result = score_results(load_cases(args.cases), load_results(args.results))
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                with args.out.open("x", encoding="utf-8") as stream:
                    json.dump(result, stream, indent=2, ensure_ascii=False)
                    stream.write("\n")
            print(json.dumps(result["summary"], indent=2))
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"cdb: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
