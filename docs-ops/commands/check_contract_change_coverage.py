import argparse
import subprocess
import sys
from pathlib import Path

from _bootstrap import bootstrap_imports

bootstrap_imports()

from toolcore.workspace import WORKSPACE_ROOT


PRODUCT_ROOT = WORKSPACE_ROOT / "IceBot-Product"
LEDGER_PATH = "delivery/changes/CONTRACT_CHANGES.yaml"
IMPACT_PATHS = (
    "product/",
    "delivery/catalogs/FLOW_CATALOG.yaml",
    "delivery/catalogs/MESSAGE_CATALOG.yaml",
    "delivery/catalogs/OPERATION_CATALOG.json",
)


def changed_paths(base_ref: str, head_ref: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}..{head_ref}"],
        cwd=PRODUCT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git diff failed")
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Require a Product contract impact ledger update when contract-owning files change."
    )
    parser.add_argument("--base", required=True, help="Committed Product repository base ref, for example origin/main")
    parser.add_argument("--head", default="HEAD", help="Product repository head ref; defaults to HEAD")
    args = parser.parse_args()

    try:
        changed = changed_paths(args.base, args.head)
    except RuntimeError as error:
        print(f"Cannot inspect Product contract diff: {error}", file=sys.stderr)
        sys.exit(2)

    impacted = sorted(
        path for path in changed if any(path == prefix or path.startswith(prefix) for prefix in IMPACT_PATHS)
    )
    if not impacted or LEDGER_PATH in changed:
        print("Contract change coverage check passed.")
        return

    print("Contract-owning files changed without an impact ledger update:", file=sys.stderr)
    for path in impacted:
        print(f"- {path}", file=sys.stderr)
    print(f"Add {LEDGER_PATH} or classify the change as non-contract before merging.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
