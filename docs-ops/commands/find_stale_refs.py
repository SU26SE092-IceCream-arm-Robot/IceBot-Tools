import argparse
import sys
from pathlib import Path

from _bootstrap import bootstrap_imports

bootstrap_imports()

from docsops.reporting import format_check_failure
from docsops.checks import find_stale_references


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find stale documentation path references.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional files/directories to scan. Defaults to the workspace root.",
    )
    parser.add_argument(
        "--pattern",
        action="append",
        dest="extra_patterns",
        default=[],
        help="Additional stale string pattern to search for.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    roots = [Path(path).resolve() for path in args.paths] if args.paths else None
    result = find_stale_references(roots, extra_patterns=args.extra_patterns)

    if result["passed"]:
        print(f"Stale reference check passed: {result['files_scanned']} files scanned.")
        return

    print(f"Stale reference check failed: {result['failure_count']} hit(s).", file=sys.stderr)
    for line in format_check_failure(result)[1:]:
        print(line, file=sys.stderr)

    sys.exit(1)


if __name__ == "__main__":
    main()
