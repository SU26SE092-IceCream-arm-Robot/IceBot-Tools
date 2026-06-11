from abc import ABC, abstractmethod
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PointStruct,
    SparseVector,
)

from raglib.collection_setup import (
    default_payload_indexes,
    ensure_collection,
    ensure_payload_indexes,
)
from raglib.config import (
    DEFAULT_QDRANT_URL,
    EMBEDDING_MODEL,
    ENABLE_HYBRID,
    SPARSE_MODEL,
    WORKSPACE_ROOT,
    get_qdrant_client,
)
from raglib.source_config import load_source_configs, validate_source_paths
from raglib.source_metadata import build_metadata


BATCH_SIZE = 128


class BaseIngester(ABC):
    collection_lane_name: str
    missing_source_message: str
    missing_manifest_message: str
    log_label: str

    def __init__(self, collection_lane: dict, logger) -> None:
        from sentence_transformers import SentenceTransformer

        self.collection_lane = collection_lane
        self.logger = logger
        self.model = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=True)
        self.sparse_model = self.load_sparse_model() if ENABLE_HYBRID else None
        self.client = get_qdrant_client()
        self.embedding_dimension = len(self.model.encode("dimension probe"))
        self._points: list[PointStruct] = []

    @property
    def collection_name(self) -> str:
        return self.collection_lane["name"]

    def load_source_configs(self) -> list[dict]:
        return load_source_configs(
            self.collection_lane,
            self.logger,
            self.missing_source_message,
        )

    def load_sparse_model(self):
        try:
            from fastembed import SparseTextEmbedding
        except ImportError as ex:
            raise SystemExit(
                "Hybrid retrieval is enabled but fastembed is not installed.\n"
                "Run `pip install -r requirements.txt` or set RAG_ENABLE_HYBRID=false."
            ) from ex

        return SparseTextEmbedding(model_name=SPARSE_MODEL)

    def ensure_collection(self) -> None:
        ensure_collection(
            client=self.client,
            collection_lane_name=self.collection_lane_name,
            collection_lane=self.collection_lane,
            embedding_dimension=self.embedding_dimension,
            logger=self.logger,
            missing_manifest_message=self.missing_manifest_message,
        )

    def ensure_payload_indexes(self) -> None:
        ensure_payload_indexes(
            self.client,
            self.collection_name,
            self.payload_indexes(),
            self.logger,
        )

    def payload_indexes(self) -> dict:
        return default_payload_indexes()

    def delete_existing_file_points(self, file_id: str) -> None:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="file_id",
                        match=MatchValue(value=file_id),
                    )
                ]
            ),
        )

    def is_file_unchanged(self, file_id: str, file_hash: str) -> bool:
        existing_points, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="file_id",
                        match=MatchValue(value=file_id),
                    )
                ]
            ),
            limit=1,
            with_payload=["file_hash"],
            with_vectors=False,
        )

        if not existing_points:
            return False

        return existing_points[0].payload.get("file_hash") == file_hash

    def iter_indexed_file_ids(self):
        offset = None
        seen: set[str] = set()

        while True:
            records, offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=256,
                offset=offset,
                with_payload=["file_id"],
                with_vectors=False,
            )

            for record in records:
                file_id = record.payload.get("file_id") if record.payload else None

                if file_id and file_id not in seen:
                    seen.add(file_id)
                    yield file_id

            if offset is None:
                break

    def cleanup_orphaned_file_points(self, active_file_ids: set[str]) -> int:
        orphaned_file_ids = [
            file_id for file_id in self.iter_indexed_file_ids()
            if file_id not in active_file_ids
        ]

        if not orphaned_file_ids:
            return 0

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="file_id",
                        match=MatchAny(any=orphaned_file_ids),
                    )
                ]
            ),
        )

        return len(orphaned_file_ids)

    def flush_points(self) -> int:
        if not self._points:
            return 0

        flushed_count = len(self._points)
        self.client.upsert(
            collection_name=self.collection_name,
            points=self._points,
        )
        self._points.clear()
        return flushed_count

    def build_point_vector(self, chunk_text: str) -> dict:
        dense_vector = self.model.encode(chunk_text).tolist()
        point_vector = {
            "dense": dense_vector,
        }

        if self.sparse_model is None:
            return point_vector

        sparse_embedding = next(iter(self.sparse_model.embed([chunk_text])))
        point_vector["sparse"] = SparseVector(
            indices=list(sparse_embedding.indices),
            values=list(sparse_embedding.values),
        )
        return point_vector

    def build_file_points(self, metadata: dict, file_path: Path) -> tuple[list[PointStruct], int]:
        chunks, skipped_empty_chunks = self.build_chunks(file_path)
        file_points = []

        for index, chunk in enumerate(chunks):
            chunk_text = chunk["text"]
            vector = self.build_point_vector(chunk_text)
            payload = {
                **metadata,
                "chunk_index": index,
                **self.build_chunk_payload(chunk, file_path),
                "text": chunk_text,
            }

            file_points.append(
                PointStruct(
                    id=self.build_point_id(metadata["source_path"], index, chunk_text),
                    vector=vector,
                    payload=payload,
                )
            )

        return file_points, skipped_empty_chunks

    def run(self, source_configs: list[dict]) -> None:
        self.logger.info("Starting %s ingest into collection: %s", self.log_label, self.collection_name)
        self.ensure_collection()
        self.ensure_payload_indexes()

        indexed_chunks = 0
        indexed_files = 0
        skipped_files = 0
        skipped_empty_chunks = 0
        seen_file_ids: set[str] = set()

        for source_config in source_configs:
            source_path = source_config["path"]

            if not source_path.exists():
                self.logger.info("Skipped optional missing source: %s", source_path)
                continue

            for file_path in self.iter_files(source_path):
                metadata = build_metadata(source_config, file_path, WORKSPACE_ROOT)
                seen_file_ids.add(metadata["file_id"])

                if self.is_file_unchanged(metadata["file_id"], metadata["file_hash"]):
                    self.logger.info("Skipped unchanged file: %s", metadata["source_path"])
                    skipped_files += 1
                    continue

                file_points, file_skipped_empty_chunks = self.build_file_points(metadata, file_path)
                skipped_empty_chunks += file_skipped_empty_chunks

                self.delete_existing_file_points(metadata["file_id"])
                self._points.extend(file_points)
                indexed_chunks += len(file_points)
                indexed_files += 1
                self.logger.info(
                    "Staged changed file: %s chunks=%s skipped_empty_chunks=%s",
                    metadata["source_path"],
                    len(file_points),
                    file_skipped_empty_chunks,
                )

                if len(self._points) >= BATCH_SIZE:
                    self.flush_points()

        if not seen_file_ids:
            raise SystemExit("No source files found. Abort cleanup to avoid deleting collection.")

        self.flush_points()

        orphaned_files = self.cleanup_orphaned_file_points(seen_file_ids)

        summary = (
            f"Indexed {indexed_chunks} chunks from {indexed_files} changed files; "
            f"skipped {skipped_files} unchanged files; "
            f"skipped {skipped_empty_chunks} empty chunks; "
            f"removed {orphaned_files} orphaned files"
        )
        self.logger.info(summary)
        print(summary)

    @abstractmethod
    def iter_files(self, source_path: Path):
        pass

    @abstractmethod
    def build_chunks(self, file_path: Path) -> tuple[list[dict], int]:
        pass

    @abstractmethod
    def build_chunk_payload(self, chunk: dict, file_path: Path) -> dict:
        pass

    @abstractmethod
    def build_point_id(self, source_path: str, chunk_index: int, chunk_text: str) -> str:
        pass
