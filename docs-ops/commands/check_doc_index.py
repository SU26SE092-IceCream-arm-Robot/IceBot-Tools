import sys

from _bootstrap import bootstrap_imports

bootstrap_imports()

from docsops.reporting import format_check_failure
from docsops.checks import check_important_doc_index


def main() -> None:
    result = check_important_doc_index()

    if result["passed"]:
        print(f"Doc index check passed: {result['docs_checked']} important docs checked.")
        return

    print(f"Doc index check failed: {result['failure_count']} issue(s).", file=sys.stderr)
    for line in format_check_failure(result)[1:]:
        print(line, file=sys.stderr)

    sys.exit(1)


if __name__ == "__main__":
    main()
