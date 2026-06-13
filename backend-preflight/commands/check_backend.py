import argparse
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))
sys.path.append(str(project_root / "backend-preflight"))

from backendpreflight import run_backend_preflight


def main() -> None:
    parser = argparse.ArgumentParser(description="Run IceBot backend preflight checks.")
    parser.add_argument("--skip-build", action="store_true", help="Skip dotnet build.")
    parser.add_argument("--skip-docs", action="store_true", help="Skip docs hygiene checks.")
    parser.add_argument("--skip-code-index", action="store_true", help="Skip Code Intelligence coverage checks.")
    parser.add_argument("--include-logs", action="store_true", help="Include one-shot log analyzer check.")
    parser.add_argument("--no-code-index-dry-run", action="store_true", help="Skip dry indexing before coverage verification.")
    parser.add_argument("--max-failures-per-check", type=int, default=20)
    parser.add_argument("--max-log-items", type=int, default=5)
    args = parser.parse_args()

    result = run_backend_preflight(
        include_build=not args.skip_build,
        include_docs=not args.skip_docs,
        include_code_index=not args.skip_code_index,
        include_logs=args.include_logs,
        code_index_dry_run=not args.no_code_index_dry_run,
        max_failures_per_check=args.max_failures_per_check,
        max_log_items=args.max_log_items,
    )

    print(result["summary"])
    if result["passed"]:
        return

    for check in result.get("checks", []):
        if check.get("passed"):
            continue
        print(f"\n[{check['name']}] {check['summary']}", file=sys.stderr)
        for key in ("stdout", "stderr", "error"):
            value = check.get(key)
            if value:
                print(f"{key}:\n{value}", file=sys.stderr)
        if "checks" in check:
            print(f"details: {check['checks']}", file=sys.stderr)

    sys.exit(1)


if __name__ == "__main__":
    main()
