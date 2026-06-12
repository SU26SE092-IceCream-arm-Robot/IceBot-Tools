import sys
import subprocess
from pathlib import Path
from typing import Any

# Determine workspace tools directory
tools_dir = Path(__file__).resolve().parent.parent.parent

# Add code-intelligence directory to path to allow importing codeintel
sys.path.append(str(tools_dir / "code-intelligence"))

from codeintel.queries import query_symbols, query_endpoints, query_handlers
from codeintel.indexer import run_indexing

def lookup_icebot_symbol(query: str) -> dict[str, Any]:
    """Lookup C# class, interface, struct, method, or enum symbol in the code index."""
    results = query_symbols(query)
    return {
        "query": query,
        "results": results
    }

def lookup_icebot_endpoint(query: str) -> dict[str, Any]:
    """Lookup WebAPI routes, HTTP methods, controllers, or actions in the code index."""
    results = query_endpoints(query)
    return {
        "query": query,
        "results": results
    }

def lookup_icebot_handler(query: str, context: str or None = None) -> dict[str, Any]:
    """Lookup CQRS Command/Query Handlers, request/result models, store dependencies, and callers."""
    results = query_handlers(query, context_filter=context)
    return {
        "query": query,
        "context_filter": context,
        "results": results
    }

def verify_icebot_code_index(dry_run: bool = True) -> dict[str, Any]:
    """Verify code index coverage against physical files on disk. Optionally runs a dry indexing run to verify updates."""
    stats = run_indexing(dry_run=True) if dry_run else None
    coverage_script = tools_dir / "code-intelligence" / "commands" / "verify_coverage.py"
    coverage = subprocess.run(
        [sys.executable, str(coverage_script)],
        cwd=str(tools_dir),
        capture_output=True,
        text=True,
    )

    if coverage.returncode != 0:
        return {
            "message": "Code index coverage verification failed.",
            "dry_run_stats": stats,
            "coverage_stdout": coverage.stdout,
            "coverage_stderr": coverage.stderr,
            "status": "failed",
        }

    return {
        "message": "Code index coverage verified successfully.",
        "dry_run_stats": stats,
        "coverage_stdout": coverage.stdout,
        "status": "passed",
    }
