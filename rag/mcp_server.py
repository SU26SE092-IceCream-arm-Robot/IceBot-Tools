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
        "vector_score": payload.get("vector_score", result.score),
        "rerank_score": payload.get("rerank_score"),
        "text": payload.get("text") or "",
    }


@mcp.tool()
def retrieve_icebot_context(
    query: str,
    limit: int = 5,
    candidate_limit: int = 100,
    include_vault: bool = False,
    statuses: list[str] | None = None,
    source_types: list[str] | None = None,
    source_groups: list[str] | None = None,
    doc_types: list[str] | None = None,
    path_contains: list[str] | None = None,
    include_overview: bool = True,
    use_reranker: bool = True,
) -> dict[str, Any]:
    """Retrieve IceBot project context from local Qdrant without calling an LLM."""
    results = retrieve_context(
        query,
        include_vault=include_vault,
        statuses=statuses,
        source_types=source_types,
        source_groups=source_groups,
        doc_types=doc_types,
        path_contains=path_contains,
        include_overview=include_overview,
        limit=limit,
        candidate_limit=candidate_limit,
        use_reranker=use_reranker,
    )

    return {
        "query": query,
        "contexts": [result_to_dict(result) for result in results],
    }


if __name__ == "__main__":
    mcp.run()
