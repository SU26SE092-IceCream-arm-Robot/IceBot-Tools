from typing import Any

from mcp.server.fastmcp import FastMCP

from raglib.config import setup_cache_env
from raglib.vector_store import retrieve_context

setup_cache_env()

mcp = FastMCP("icebot-rag")


def result_to_dict(result) -> dict[str, Any]:
    payload = result.payload or {}

    return {
        "source": payload.get("source"),
        "source_path": payload.get("source_path"),
        "source_type": payload.get("source_type"),
        "source_group": payload.get("source_group"),
        "doc_type": payload.get("doc_type"),
        "authority": payload.get("authority"),
        "status": payload.get("status"),
        "is_overview": payload.get("is_overview"),
        "chunk_index": payload.get("chunk_index"),
        "section_index": payload.get("section_index"),
        "section_path": payload.get("section_path"),
        "language": payload.get("language"),
        "namespace": payload.get("namespace"),
        "symbol_kind": payload.get("symbol_kind"),
        "symbol_name": payload.get("symbol_name"),
        "start_line": payload.get("start_line"),
        "end_line": payload.get("end_line"),
        "vector_score": payload.get("vector_score"),
        "hybrid_score": payload.get("hybrid_score"),
        "rerank_score": payload.get("rerank_score"),
        "text": payload.get("text") or "",
    }


def result_score(result) -> float:
    payload = result.payload or {}
    return (
        payload.get("rerank_score")
        or payload.get("hybrid_score")
        or payload.get("vector_score")
        or result.score
        or 0.0
    )


def retrieve_by_mode(
    query: str,
    *,
    mode: str,
    limit: int,
    candidate_limit: int,
    include_vault: bool,
    authorities: list[str] | None,
    statuses: list[str] | None,
    source_types: list[str] | None,
    source_groups: list[str] | None,
    doc_types: list[str] | None,
    path_contains: list[str] | None,
    include_overview: bool,
    use_reranker: bool,
    use_hybrid: bool,
):
    normalized_mode = mode.strip().lower()

    if normalized_mode not in {"docs", "code", "both"}:
        raise ValueError("mode must be one of: docs, code, both")

    if normalized_mode in {"docs", "code"}:
        return retrieve_context(
            query,
            lane=normalized_mode,
            include_vault=include_vault if normalized_mode == "docs" else False,
            authorities=authorities,
            statuses=statuses,
            source_types=source_types,
            source_groups=source_groups,
            doc_types=doc_types,
            path_contains=path_contains,
            include_overview=include_overview,
            limit=limit,
            candidate_limit=candidate_limit,
            use_reranker=use_reranker,
            use_hybrid=use_hybrid,
        )

    docs_results = retrieve_context(
        query,
        lane="docs",
        include_vault=include_vault,
        authorities=authorities,
        statuses=statuses,
        source_types=source_types,
        source_groups=source_groups,
        doc_types=doc_types,
        path_contains=path_contains,
        include_overview=include_overview,
        limit=limit,
        candidate_limit=candidate_limit,
        use_reranker=use_reranker,
        use_hybrid=use_hybrid,
    )
    code_results = retrieve_context(
        query,
        lane="code",
        include_vault=False,
        authorities=authorities,
        statuses=statuses,
        source_types=source_types,
        source_groups=source_groups,
        doc_types=doc_types,
        path_contains=path_contains,
        include_overview=include_overview,
        limit=limit,
        candidate_limit=candidate_limit,
        use_reranker=use_reranker,
        use_hybrid=use_hybrid,
    )
    return sorted(
        [*docs_results, *code_results],
        key=result_score,
        reverse=True,
    )[:limit]


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
