from qdrant_client.models import (
    Distance,
    PayloadSchemaType,
    SparseIndexParams,
    SparseVectorParams,
    VectorParams,
)

from raglib.collection_manifest import (
    build_collection_manifest,
    read_collection_manifest,
    validate_collection_manifest,
    write_collection_manifest,
)
from raglib.config import EMBEDDING_MODEL, ENABLE_HYBRID, SPARSE_MODEL


def build_expected_manifest(
    *,
    collection_lane_name: str,
    collection_lane: dict,
    embedding_dimension: int,
) -> dict:
    return build_collection_manifest(
        collection_lane=collection_lane_name,
        collection_base_name=collection_lane["base_name"],
        collection_name=collection_lane["name"],
        collection_version=collection_lane["version"],
        embedding_model=EMBEDDING_MODEL,
        embedding_dimension=embedding_dimension,
        vector_schema="named_dense_sparse" if ENABLE_HYBRID else "named_dense",
        hybrid_enabled=ENABLE_HYBRID,
        sparse_model=SPARSE_MODEL if ENABLE_HYBRID else None,
    )


def ensure_collection(
    *,
    client,
    collection_lane_name: str,
    collection_lane: dict,
    embedding_dimension: int,
    logger,
    missing_manifest_message: str,
) -> None:
    collection_name = collection_lane["name"]
    manifest_path = collection_lane["manifest_path"]
    expected_manifest = build_expected_manifest(
        collection_lane_name=collection_lane_name,
        collection_lane=collection_lane,
        embedding_dimension=embedding_dimension,
    )

    if not client.collection_exists(collection_name=collection_name):
        logger.info("Creating Qdrant collection: %s", collection_name)
        sparse_vectors_config = None

        if ENABLE_HYBRID:
            sparse_vectors_config = {
                "sparse": SparseVectorParams(index=SparseIndexParams()),
            }

        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": VectorParams(
                    size=embedding_dimension,
                    distance=Distance.COSINE,
                ),
            },
            sparse_vectors_config=sparse_vectors_config,
        )
        write_collection_manifest(manifest_path, expected_manifest)
        logger.info("Wrote collection manifest: %s", manifest_path)
        return

    manifest = read_collection_manifest(manifest_path)

    if manifest is None:
        raise SystemExit(
            f"Missing collection manifest: {manifest_path}\n"
            "Do not ingest into an existing collection without metadata. "
            f"{missing_manifest_message}"
        )

    validate_collection_manifest(manifest, expected_manifest)
    logger.info("Validated collection manifest: %s", manifest_path)


def default_payload_indexes() -> dict:
    return {
        "authority": PayloadSchemaType.KEYWORD,
        "status": PayloadSchemaType.KEYWORD,
        "source_type": PayloadSchemaType.KEYWORD,
        "source_group": PayloadSchemaType.KEYWORD,
        "doc_type": PayloadSchemaType.KEYWORD,
        "source": PayloadSchemaType.KEYWORD,
        "file_id": PayloadSchemaType.KEYWORD,
        "file_hash": PayloadSchemaType.KEYWORD,
        "source_path": PayloadSchemaType.TEXT,
    }


def ensure_payload_indexes(client, collection_name: str, payload_indexes: dict, logger) -> None:
    for field_name, field_schema in payload_indexes.items():
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=field_schema,
            )
            logger.info("Ensured payload index: %s", field_name)
        except Exception as ex:
            message = str(ex).lower()

            if "already exists" in message or "already has" in message:
                continue

            raise
