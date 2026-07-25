import argparse
import sys

from _bootstrap import bootstrap_imports

bootstrap_imports()

from docsops.api_inventory import check_policy_inventory
from docsops.reporting import format_check_failure


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify REST/GraphQL authorization policies exist in the backend permission matrix."
    )
    parser.add_argument("--max-failures", type=int, default=30)
    args = parser.parse_args()

    result = check_policy_inventory(max_failures=args.max_failures)
    if result["passed"]:
        print(
            "API policy inventory check passed: "
            f"{result['rest_endpoint_count']} REST endpoints, "
            f"{result['graphql_policy_count']} GraphQL policies."
        )
        return

    print("\n".join(format_check_failure(result)), file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
