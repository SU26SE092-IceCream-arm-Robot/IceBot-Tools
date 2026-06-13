import subprocess
import sys
from pathlib import Path
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = TOOLS_DIR.parent
BACKEND_DIR = WORKSPACE_ROOT / "IceBot-Backend"

sys.path.append(str(TOOLS_DIR))
sys.path.append(str(TOOLS_DIR / "docs-ops"))
sys.path.append(str(TOOLS_DIR / "code-intelligence"))
sys.path.append(str(TOOLS_DIR / "log-analyzer"))

from docsops.checks import run_all_docs_checks
from codeintel.indexer import run_indexing


def _tail(text: str, *, max_lines: int = 60) -> str:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[-max_lines:])


def _run_process(name: str, command: list[str], cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )

    if completed.returncode == 0:
        return {
            "name": name,
            "passed": True,
            "summary": f"{name} passed.",
        }

    return {
        "name": name,
        "passed": False,
        "summary": f"{name} failed.",
        "exit_code": completed.returncode,
        "stdout": _tail(completed.stdout),
        "stderr": _tail(completed.stderr),
    }


def _run_backend_build() -> dict[str, Any]:
    if not BACKEND_DIR.exists():
        return {
            "name": "backend_build",
            "passed": False,
            "summary": "IceBot-Backend directory was not found.",
            "path": str(BACKEND_DIR),
        }

    return _run_process(
        "backend_build",
        ["dotnet", "build", "src\\IceBot.slnx"],
        BACKEND_DIR,
    )


def _run_docs_check(max_failures_per_check: int) -> dict[str, Any]:
    result = run_all_docs_checks(max_failures_per_check=max_failures_per_check)
    if result.get("passed"):
        return {
            "name": "docs_check",
            "passed": True,
            "summary": result.get("summary", "Docs checks passed."),
        }

    return {
        "name": "docs_check",
        "passed": False,
        "summary": result.get("summary", "Docs checks failed."),
        "checks": result.get("checks", []),
    }


def _run_code_index_check(dry_run: bool) -> dict[str, Any]:
    try:
        stats = run_indexing(dry_run=dry_run)
    except Exception as exc:
        return {
            "name": "code_index",
            "passed": False,
            "summary": "Code index dry run failed.",
            "error": str(exc),
        }

    coverage_script = TOOLS_DIR / "code-intelligence" / "commands" / "verify_coverage.py"
    coverage = subprocess.run(
        [sys.executable, str(coverage_script)],
        cwd=str(TOOLS_DIR),
        capture_output=True,
        text=True,
    )

    if coverage.returncode == 0:
        return {
            "name": "code_index",
            "passed": True,
            "summary": "Code index coverage passed.",
            "dry_run_stats": stats if not dry_run else _compact_index_stats(stats),
        }

    return {
        "name": "code_index",
        "passed": False,
        "summary": "Code index coverage failed.",
        "dry_run_stats": _compact_index_stats(stats),
        "stdout": _tail(coverage.stdout),
        "stderr": _tail(coverage.stderr),
    }


def _compact_index_stats(stats: Any) -> Any:
    if not isinstance(stats, dict):
        return stats

    keys = [
        "files_scanned",
        "files_indexed",
        "files_skipped",
        "symbols",
        "endpoints",
        "graphql_fields",
        "handlers",
        "relationships",
        "orphaned_files_removed",
    ]
    return {key: stats[key] for key in keys if key in stats}


def _run_log_check(max_items: int) -> dict[str, Any]:
    from analyzer import (
        DEFAULT_MOCK_LOG_ROOT,
        DEFAULT_RAG_LOG_ROOT,
        DEFAULT_VIOLATIONS_LOG_PATH,
        LogAnalyzer,
    )

    analyzer = LogAnalyzer(
        str(DEFAULT_MOCK_LOG_ROOT / "webapi"),
        str(DEFAULT_MOCK_LOG_ROOT / "robot"),
        str(DEFAULT_RAG_LOG_ROOT),
        str(DEFAULT_VIOLATIONS_LOG_PATH),
        write_violations=False,
        verbose=False,
    )
    result = analyzer.analyze_once(include_rag=False, max_items=max_items)
    return {
        "name": "log_analyzer",
        "passed": bool(result.get("passed")),
        "summary": result.get("summary", "Log analyzer completed."),
        **({} if result.get("passed") else result),
    }


def run_backend_preflight(
    *,
    include_build: bool = True,
    include_docs: bool = True,
    include_code_index: bool = True,
    include_logs: bool = False,
    code_index_dry_run: bool = True,
    max_failures_per_check: int = 20,
    max_log_items: int = 5,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    if include_build:
        checks.append(_run_backend_build())
    if include_docs:
        checks.append(_run_docs_check(max_failures_per_check=max_failures_per_check))
    if include_code_index:
        checks.append(_run_code_index_check(dry_run=code_index_dry_run))
    if include_logs:
        checks.append(_run_log_check(max_items=max_log_items))

    failed = [check for check in checks if not check.get("passed")]
    if not failed:
        names = ", ".join(check["name"] for check in checks)
        return {
            "passed": True,
            "summary": f"Backend preflight passed: {names}.",
        }

    return {
        "passed": False,
        "summary": f"Backend preflight failed: {len(failed)} of {len(checks)} checks failed.",
        "checks": checks,
    }
