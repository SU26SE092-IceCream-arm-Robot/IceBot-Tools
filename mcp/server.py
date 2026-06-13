import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Ensure the mcp folder itself and its parent are in sys.path to resolve module imports
mcp_dir = Path(__file__).resolve().parent
project_root = mcp_dir.parent
if str(mcp_dir) not in sys.path:
    sys.path.insert(0, str(mcp_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools import rag_tools, code_intelligence_tools, docs_ops_tools, log_analyzer_tools, backend_preflight_tools

# Initialize Unified FastMCP Server
mcp = FastMCP("icebot")

# --- Register RAG Tools ---

@mcp.tool()
def retrieve_icebot_context(
    query: str,
    mode: str = "docs",
    limit: int = 5,
    candidate_limit: int = 100,
    include_vault: bool = False,
    authorities: list[str] | None = None,
    statuses: list[str] | None = None,
    source_types: list[str] | None = None,
    source_groups: list[str] | None = None,
    doc_types: list[str] | None = None,
    path_contains: list[str] | None = None,
    include_overview: bool = True,
    use_reranker: bool = False,
    use_hybrid: bool = True,
) -> dict:
    """Retrieve IceBot context by mode: docs, code, or both. Default to docs. Use docs for design/flows, and code for implementation details."""
    return rag_tools.retrieve_icebot_context(
        query=query,
        mode=mode,
        limit=limit,
        candidate_limit=candidate_limit,
        include_vault=include_vault,
        authorities=authorities,
        statuses=statuses,
        source_types=source_types,
        source_groups=source_groups,
        doc_types=doc_types,
        path_contains=path_contains,
        include_overview=include_overview,
        use_reranker=use_reranker,
        use_hybrid=use_hybrid,
    )

@mcp.tool()
def retrieve_icebot_docs(
    query: str,
    limit: int = 5,
    candidate_limit: int = 100,
    include_vault: bool = False,
    authorities: list[str] | None = None,
    statuses: list[str] | None = None,
    source_types: list[str] | None = None,
    source_groups: list[str] | None = None,
    doc_types: list[str] | None = None,
    path_contains: list[str] | None = None,
    include_overview: bool = True,
    use_reranker: bool = False,
    use_hybrid: bool = True,
) -> dict:
    """Retrieve IceBot docs knowledge. Prefer this for architecture, rules, flows, and contracts."""
    return rag_tools.retrieve_icebot_docs(
        query=query,
        limit=limit,
        candidate_limit=candidate_limit,
        include_vault=include_vault,
        authorities=authorities,
        statuses=statuses,
        source_types=source_types,
        source_groups=source_groups,
        doc_types=doc_types,
        path_contains=path_contains,
        include_overview=include_overview,
        use_reranker=use_reranker,
        use_hybrid=use_hybrid,
    )

@mcp.tool()
def retrieve_icebot_code(
    query: str,
    limit: int = 5,
    candidate_limit: int = 50,
    statuses: list[str] | None = None,
    path_contains: list[str] | None = None,
    use_reranker: bool = False,
    use_hybrid: bool = True,
) -> dict:
    """Retrieve IceBot source-code knowledge. Prefer this for implementation, classes, endpoints, and mappings."""
    return rag_tools.retrieve_icebot_code(
        query=query,
        limit=limit,
        candidate_limit=candidate_limit,
        statuses=statuses,
        path_contains=path_contains,
        use_reranker=use_reranker,
        use_hybrid=use_hybrid,
    )

# --- Register Code Intelligence Tools ---

@mcp.tool()
def lookup_icebot_symbol(query: str) -> dict:
    """Lookup C# class, interface, struct, method, or enum symbol in the code index."""
    return code_intelligence_tools.lookup_icebot_symbol(query)

@mcp.tool()
def lookup_icebot_endpoint(query: str) -> dict:
    """Lookup WebAPI routes, HTTP methods, controllers, or actions in the code index."""
    return code_intelligence_tools.lookup_icebot_endpoint(query)

@mcp.tool()
def lookup_icebot_handler(query: str, context: str or None = None) -> dict:
    """Lookup CQRS Command/Query Handlers, request/result models, store dependencies, and callers."""
    return code_intelligence_tools.lookup_icebot_handler(query, context)

@mcp.tool()
def verify_icebot_code_index(dry_run: bool = True) -> dict:
    """Verify code index coverage against physical files on disk. Optionally runs a dry indexing run to verify updates."""
    return code_intelligence_tools.verify_icebot_code_index(dry_run)

# --- Register Docs Ops Tools ---

@mcp.tool()
def check_icebot_docs(max_failures_per_check: int = 30) -> dict:
    """Run docs hygiene checks. Quiet on success, structured failures on broken links, stale refs, or missing index docs."""
    return docs_ops_tools.check_icebot_docs(max_failures_per_check=max_failures_per_check)

# --- Register Log Analyzer Tools ---

@mcp.tool()
def analyze_icebot_logs(
    webapi_path: str | None = None,
    robot_path: str | None = None,
    rag_path: str | None = None,
    include_rag: bool = False,
    max_items: int = 5,
) -> dict:
    """Analyze IceBot logs once with capped output. Default excludes RAG logs to avoid old ingest noise."""
    return log_analyzer_tools.analyze_icebot_logs(
        webapi_path=webapi_path,
        robot_path=robot_path,
        rag_path=rag_path,
        include_rag=include_rag,
        max_items=max_items,
    )

# --- Register Backend Preflight Tools ---

@mcp.tool()
def check_icebot_backend(
    include_build: bool = True,
    include_docs: bool = True,
    include_code_index: bool = True,
    include_logs: bool = False,
    code_index_dry_run: bool = True,
    max_failures_per_check: int = 20,
    max_log_items: int = 5,
) -> dict:
    """Run backend preflight checks. Quiet on success, structured failures on build/docs/code-index/log issues."""
    return backend_preflight_tools.check_icebot_backend(
        include_build=include_build,
        include_docs=include_docs,
        include_code_index=include_code_index,
        include_logs=include_logs,
        code_index_dry_run=code_index_dry_run,
        max_failures_per_check=max_failures_per_check,
        max_log_items=max_log_items,
    )

def main():
    """Starts the FastMCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
