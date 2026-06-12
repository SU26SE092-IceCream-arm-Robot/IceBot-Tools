import sys
from pathlib import Path
from typing import Any

tools_dir = Path(__file__).resolve().parent.parent.parent
docs_ops_dir = tools_dir / "docs-ops"

sys.path.append(str(tools_dir))
sys.path.append(str(docs_ops_dir))

from docsops.checks import run_all_docs_checks


def check_icebot_docs(max_failures_per_check: int = 30) -> dict[str, Any]:
    """Run docs hygiene checks with quiet success and structured failure output."""
    return run_all_docs_checks(max_failures_per_check=max_failures_per_check)
