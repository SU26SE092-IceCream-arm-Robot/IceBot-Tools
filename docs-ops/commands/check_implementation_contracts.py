import argparse
import sys

from _bootstrap import bootstrap_imports

bootstrap_imports()

from docsops.implementation_contracts import check_implementation_contracts


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify IceBot cross-repository implementation contracts.")
    parser.add_argument("--max-failures", type=int, default=30)
    args = parser.parse_args()
    result = check_implementation_contracts(max_failures=args.max_failures)
    if result["passed"]:
        print("Implementation contract check passed.")
        return
    for failure in result["failures"]:
        print(f"{failure['file']}: {failure['target']}: {failure['reason']}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
