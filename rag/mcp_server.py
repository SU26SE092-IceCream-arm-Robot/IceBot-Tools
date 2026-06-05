from typing import Any

from mcp.server.fastmcp import FastMCP

from raglib.config import setup_cache_env
from raglib.context_router import retrieve_by_mode
from raglib.result_formatting import result_to_dict


setup_cache_env()

mcp = FastMCP("icebot-rag")


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
) -> dict[str, Any]:
    """Retrieve IceBot context by mode: docs, code, or both. Default to docs."""
    results = retrieve_by_mode(
        query,
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

    return {
        "query": query,
        "mode": mode,
        "contexts": [result_to_dict(result) for result in results],
    }


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
) -> dict[str, Any]:
    """Retrieve IceBot docs knowledge. Prefer this for architecture, rules, flows, and contracts."""
    return retrieve_icebot_context(
        query=query,
        mode="docs",
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
) -> dict[str, Any]:
    """Retrieve IceBot source-code knowledge. Prefer this for implementation, classes, endpoints, and mappings."""
    return retrieve_icebot_context(
        query=query,
        mode="code",
        limit=limit,
        candidate_limit=candidate_limit,
        include_vault=False,
        statuses=statuses,
        path_contains=path_contains,
        include_overview=True,
        use_reranker=use_reranker,
        use_hybrid=use_hybrid,
    )


if __name__ == "__main__":
    mcp.run()
