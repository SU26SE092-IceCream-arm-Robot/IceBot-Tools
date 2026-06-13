import argparse
import sys

from _bootstrap import bootstrap_imports

bootstrap_imports()

from docsops.reporting import format_aggregate_cli_report
from docsops.checks import run_all_docs_checks


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all IceBot docs hygiene checks.")
    parser.add_argument(
        "--max-failures-per-check",
        type=int,
        default=30,
        help="Maximum failure entries to print for each check.",
    )
    args = parser.parse_args()

    result = run_all_docs_checks(max_failures_per_check=args.max_failures_per_check)

    if result["passed"]:
        print(format_aggregate_cli_report(result)[0])
        return

    print("\n".join(format_aggregate_cli_report(result)), file=sys.stderr)

    sys.exit(1)


if __name__ == "__main__":
    main()
