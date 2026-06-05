from raglib.result_formatting import result_score
from raglib.vector_store import retrieve_context


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
