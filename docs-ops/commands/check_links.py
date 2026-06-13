import sys
from pathlib import Path

from _bootstrap import bootstrap_imports

bootstrap_imports()

import argparse
from docsops.reporting import format_check_failure
from docsops.checks import check_markdown_links


def main() -> None:
    parser = argparse.ArgumentParser(description="Check local Markdown links.")
    parser.add_argument("paths", nargs="*", help="Optional files/directories to scan.")
    args = parser.parse_args()

    roots = [Path(path).resolve() for path in args.paths] if args.paths else None
    result = check_markdown_links(roots)

    if result["passed"]:
        print(f"Markdown link check passed: {result['files_scanned']} files scanned.")
        return

    print(f"Markdown link check failed: {result['failure_count']} broken link(s).", file=sys.stderr)
    for line in format_check_failure(result)[1:]:
        print(line, file=sys.stderr)

    sys.exit(1)


if __name__ == "__main__":
    main()
