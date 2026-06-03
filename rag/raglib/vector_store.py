import os

from qdrant_client import QdrantClient
from sentence_transformers import CrossEncoder, SentenceTransformer

from raglib.config import (
    COLLECTION_NAME,
    DEFAULT_QDRANT_URL,
    EMBEDDING_MODEL,
    MAX_CANDIDATE_LIMIT,
    MAX_RETRIEVAL_LIMIT,
    RERANKER_MODEL,
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
        _embed_model = SentenceTransformer(
            EMBEDDING_MODEL,
            trust_remote_code=True,
        )

    return _embed_model


def get_reranker():
    global _reranker

    setup_cache_env()

    if _reranker is None:
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
    include_vault: bool = False,
    statuses: list[str] | None = None,
    source_types: list[str] | None = None,
    path_contains: list[str] | None = None,
    limit: int = 5,
    candidate_limit: int = 100,
    use_reranker: bool = True,
):
    limit = max(1, min(limit, MAX_RETRIEVAL_LIMIT))
    candidate_limit = max(limit, min(candidate_limit, MAX_CANDIDATE_LIMIT))

    embed_model = get_embed_model()
    reranker = get_reranker() if use_reranker else None
    client = get_qdrant_client()

    query_vector = embed_model.encode(
        query,
        prompt_name="query",
    ).tolist()

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=build_filter(include_vault, statuses, source_types, path_contains),
        limit=max(limit, candidate_limit) if reranker is not None else limit,
    )
    results = response.points

    results = rerank_results(reranker, query, results)
    return results[:limit]
