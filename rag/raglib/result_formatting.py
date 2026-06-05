from typing import Any


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
