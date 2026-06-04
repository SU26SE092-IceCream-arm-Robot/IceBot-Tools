from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchText, MatchValue


def build_filter(
    include_vault: bool,
    statuses: list[str] | None,
    source_types: list[str] | None = None,
    source_groups: list[str] | None = None,
    doc_types: list[str] | None = None,
    path_contains: list[str] | None = None,
    include_overview: bool = True,
    authorities: list[str] | None = None,
) -> Filter:
    conditions = []

    if authorities:
        conditions.append(
            FieldCondition(
                key="authority",
                match=MatchAny(any=authorities),
            )
        )
    elif include_vault:
        conditions.append(
            FieldCondition(
                key="authority",
                match=MatchAny(any=["official", "draft"]),
            )
        )
    else:
        conditions.append(
            FieldCondition(
                key="authority",
                match=MatchValue(value="official"),
            )
        )

    if statuses:
        conditions.append(
            FieldCondition(
                key="status",
                match=MatchAny(any=statuses),
            )
        )

    if source_types:
        conditions.append(
            FieldCondition(
                key="source_type",
                match=MatchAny(any=source_types),
            )
        )

    if source_groups:
        conditions.append(
            FieldCondition(
                key="source_group",
                match=MatchAny(any=source_groups),
            )
        )

    if doc_types:
        conditions.append(
            FieldCondition(
                key="doc_type",
                match=MatchAny(any=doc_types),
            )
        )

    if not include_overview:
        conditions.append(
            FieldCondition(
                key="is_overview",
                match=MatchValue(value=False),
            )
        )

    if path_contains:
        for value in path_contains:
            conditions.append(
                FieldCondition(
                    key="source_path",
                    match=MatchText(text=value),
                )
            )

    return Filter(must=conditions)


def rerank_results(reranker, query: str, results, score_field: str = "vector_score"):
    if reranker is None:
        # Set the retrieval score on payload for consistency even without reranking.
        for result in results:
            result.payload = result.payload or {}
            result.payload[score_field] = result.score
        return results

    rerank_pairs = [
        [query, (result.payload or {}).get("text") or ""]
        for result in results
    ]
    rerank_scores = reranker.predict(rerank_pairs)

    for result, rerank_score in zip(results, rerank_scores):
        result.payload = result.payload or {}
        result.payload[score_field] = result.score
        result.payload["rerank_score"] = float(rerank_score)

    return sorted(
        results,
        key=lambda result: (result.payload or {}).get("rerank_score", result.score),
        reverse=True,
    )
