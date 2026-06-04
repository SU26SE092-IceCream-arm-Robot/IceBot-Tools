import json
from datetime import datetime, timezone
from pathlib import Path


def build_collection_manifest(
    *,
    collection_lane: str,
    collection_base_name: str,
    collection_name: str,
    collection_version: str,
    embedding_model: str,
    embedding_dimension: int,
) -> dict:
    return {
        "collection_lane": collection_lane,
        "collection_base_name": collection_base_name,
        "collection_name": collection_name,
        "collection_version": collection_version,
        "embedding_model": embedding_model,
        "embedding_dimension": embedding_dimension,
        "distance": "cosine",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": 1,
    }


def read_collection_manifest(manifest_path: Path) -> dict | None:
    if not manifest_path.exists():
        return None

    return json.loads(manifest_path.read_text(encoding="utf-8"))


def write_collection_manifest(manifest_path: Path, manifest: dict) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def validate_collection_manifest(manifest: dict, expected: dict) -> None:
    mismatches = []

    for key in ["collection_lane", "collection_name", "collection_version", "embedding_model", "embedding_dimension"]:
        if manifest.get(key) != expected[key]:
            mismatches.append(f"{key}: manifest={manifest.get(key)!r}, current={expected[key]!r}")

    if mismatches:
        mismatch_text = "\n".join(f"- {item}" for item in mismatches)
        raise SystemExit(
            "RAG collection metadata does not match the current embedding configuration.\n"
            "Create a new collection version or reset the current collection before ingesting.\n"
            f"{mismatch_text}"
        )
