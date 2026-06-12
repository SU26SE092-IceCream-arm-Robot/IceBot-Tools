import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))
sys.path.append(str(Path(__file__).resolve().parents[1]))

import argparse
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
    for item in result["failures"]:
        print(f"- {item['file']}:{item['line']} -> {item['target']} ({item['reason']})", file=sys.stderr)

    sys.exit(1)


if __name__ == "__main__":
    main()
