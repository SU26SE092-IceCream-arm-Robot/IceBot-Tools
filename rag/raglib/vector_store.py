import os

from qdrant_client import QdrantClient
from qdrant_client.models import Prefetch, Rrf, RrfQuery, SparseVector

from raglib.config import (
    DEFAULT_QDRANT_URL,
    EMBEDDING_MODEL,
    ENABLE_HYBRID,
    HYBRID_RRF_K,
    MAX_CANDIDATE_LIMIT,
    MAX_RETRIEVAL_LIMIT,
    RERANKER_MODEL,
    SPARSE_MODEL,
    get_collection_lane,
    setup_cache_env,
    get_qdrant_client as get_config_qdrant_client,
)
from raglib.retrieval import build_filter, rerank_results

_embed_model = None
_sparse_model = None
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


def get_sparse_model():
    global _sparse_model

    setup_cache_env()

    if _sparse_model is None:
        try:
            from fastembed import SparseTextEmbedding
        except ImportError as ex:
            raise SystemExit(
                "Hybrid retrieval is enabled but fastembed is not installed.\n"
                "Run `pip install -r requirements.txt` or set RAG_ENABLE_HYBRID=false."
            ) from ex

        _sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL)

    return _sparse_model


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
        _client = get_config_qdrant_client()

    return _client


def build_sparse_vector(text: str) -> SparseVector:
    sparse_embedding = next(iter(get_sparse_model().embed([text])))
    return SparseVector(
        indices=list(sparse_embedding.indices),
        values=list(sparse_embedding.values),
    )


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
    use_hybrid: bool = True,
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
    query_filter = build_filter(
        include_vault,
        statuses,
        source_types,
        source_groups,
        doc_types,
        path_contains,
        include_overview,
        authorities,
    )
    query_limit = max(limit, candidate_limit) if reranker is not None else limit

    if use_hybrid and ENABLE_HYBRID:
        response = client.query_points(
            collection_name=collection["name"],
            prefetch=[
                Prefetch(
                    query=query_vector,
                    using="dense",
                    filter=query_filter,
                    limit=candidate_limit,
                ),
                Prefetch(
                    query=build_sparse_vector(query),
                    using="sparse",
                    filter=query_filter,
                    limit=candidate_limit,
                ),
            ],
            query=RrfQuery(rrf=Rrf(k=HYBRID_RRF_K)),
            query_filter=query_filter,
            limit=query_limit,
        )
        results = response.points
        results = rerank_results(reranker, query, results, score_field="hybrid_score")
        return results[:limit]

    response = client.query_points(
        collection_name=collection["name"],
        query=query_vector,
        using="dense",
        query_filter=query_filter,
        limit=query_limit,
    )
    results = response.points

    results = rerank_results(reranker, query, results, score_field="vector_score")
    return results[:limit]
