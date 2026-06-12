import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))
sys.path.append(str(Path(__file__).resolve().parents[1]))

from docsops.checks import check_important_doc_index


def main() -> None:
    result = check_important_doc_index()

    if result["passed"]:
        print(f"Doc index check passed: {result['docs_checked']} important docs checked.")
        return

    print(f"Doc index check failed: {result['failure_count']} issue(s).", file=sys.stderr)
    for item in result["failures"]:
        if item["line"] is None:
            print(f"- {item['file']} ({item['reason']})", file=sys.stderr)
        else:
            print(f"- {item['file']}:{item['line']} -> {item['target']} ({item['reason']})", file=sys.stderr)

    sys.exit(1)


if __name__ == "__main__":
    main()
