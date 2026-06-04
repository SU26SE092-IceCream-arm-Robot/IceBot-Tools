import os

from qdrant_client import QdrantClient

from raglib.config import (
    DEFAULT_QDRANT_URL,
    EMBEDDING_MODEL,
    MAX_CANDIDATE_LIMIT,
    MAX_RETRIEVAL_LIMIT,
    RERANKER_MODEL,
    get_collection_lane,
    setup_cache_env,
)
from raglib.retrieval import build_filter, rerank_results

_embed_model = None
_reranker = None
_client = None


def get_embed_model():
    global _embed_model

    setup_cache_env()

    if _embed_model is None:
        from sentence_transformers import SentenceTransformer

        _embed_model = SentenceTransformer(
            EMBEDDING_MODEL,
            trust_remote_code=True,
        )

    return _embed_model


def get_reranker():
    global _reranker

    setup_cache_env()

    if _reranker is None:
        from sentence_transformers import CrossEncoder

        _reranker = CrossEncoder(
            RERANKER_MODEL,
            trust_remote_code=True,
        )

    return _reranker


def get_qdrant_client():
    global _client

    setup_cache_env()

    if _client is None:
        _client = QdrantClient(url=os.getenv("QDRANT_URL", DEFAULT_QDRANT_URL))

    return _client


def retrieve_context(
    query: str,
    *,
    lane: str = "docs",
    include_vault: bool = False,
    statuses: list[str] | None = None,
    source_types: list[str] | None = None,
    source_groups: list[str] | None = None,
    doc_types: list[str] | None = None,
    path_contains: list[str] | None = None,
    include_overview: bool = True,
    authorities: list[str] | None = None,
    limit: int = 5,
    candidate_limit: int = 100,
    use_reranker: bool = True,
):
    limit = max(1, min(limit, MAX_RETRIEVAL_LIMIT))
    candidate_limit = max(limit, min(candidate_limit, MAX_CANDIDATE_LIMIT))

    embed_model = get_embed_model()
    reranker = get_reranker() if use_reranker else None
    client = get_qdrant_client()
    collection = get_collection_lane(lane)

    if lane == "code":
        authorities = authorities or ["implementation"]
        source_groups = source_groups or ["code"]
        doc_types = doc_types or ["source-code"]

    query_vector = embed_model.encode(
        query,
        prompt_name="query",
    ).tolist()

    response = client.query_points(
        collection_name=collection["name"],
        query=query_vector,
        query_filter=build_filter(
            include_vault,
            statuses,
            source_types,
            source_groups,
            doc_types,
            path_contains,
            include_overview,
            authorities,
        ),
        limit=max(limit, candidate_limit) if reranker is not None else limit,
    )
    results = response.points

    results = rerank_results(reranker, query, results)
    return results[:limit]
