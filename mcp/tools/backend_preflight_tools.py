import sys
from pathlib import Path
from typing import Any

tools_dir = Path(__file__).resolve().parent.parent.parent
preflight_dir = tools_dir / "backend-preflight"

sys.path.append(str(tools_dir))
sys.path.append(str(preflight_dir))

from backendpreflight import run_backend_preflight


def check_icebot_backend(
    include_build: bool = True,
    include_docs: bool = True,
    include_code_index: bool = True,
    include_logs: bool = False,
    code_index_dry_run: bool = True,
    max_failures_per_check: int = 20,
    max_log_items: int = 5,
) -> dict[str, Any]:
    """Run backend preflight checks with quiet success and structured failure output."""
    return run_backend_preflight(
        include_build=include_build,
        include_docs=include_docs,
        include_code_index=include_code_index,
        include_logs=include_logs,
        code_index_dry_run=code_index_dry_run,
        max_failures_per_check=max_failures_per_check,
        max_log_items=max_log_items,
    )
