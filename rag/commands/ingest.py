import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from raglib.config import (
    COLLECTION_BASE_NAME,
    COLLECTION_MANIFEST_PATH,
    COLLECTION_NAME,
    COLLECTION_VERSION,
    DEFAULT_QDRANT_URL,
    EMBEDDING_MODEL,
    SOURCES_EXAMPLE_PATH,
    SOURCES_LOCAL_PATH,
    TOOLS_DIR,
    WORKSPACE_ROOT,
    setup_cache_env,
)
from raglib.collection_manifest import (
    build_collection_manifest,
    read_collection_manifest,
    validate_collection_manifest,
    write_collection_manifest,
)
from raglib.markdown_chunking import MarkdownChunker
from raglib.source_metadata import (
    build_metadata,
    build_point_id,
    is_excluded_source,
)

setup_cache_env()

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

EXCLUDED_SOURCE_PATHS = {
    "Vault/Learning/RAG_LEARNING_NOTES.md",
}

BATCH_SIZE = 128


# ---------------------------------------------------------------------------
# Source configuration and pure helpers
# ---------------------------------------------------------------------------

def load_source_configs() -> list[dict]:
    source_config_path = SOURCES_LOCAL_PATH if SOURCES_LOCAL_PATH.exists() else SOURCES_EXAMPLE_PATH

    if not source_config_path.exists():
        raise SystemExit(
            f"Missing source config: {source_config_path}\n"
            "Create rag/sources.local.json or restore rag/sources.example.json."
        )

    try:
        raw_sources = json.loads(source_config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        raise SystemExit(f"Invalid JSON source config: {source_config_path}\n{ex}") from ex

    if not isinstance(raw_sources, list):
        raise SystemExit(f"Source config must be a JSON array: {source_config_path}")

    source_configs = []

    for index, source in enumerate(raw_sources):
        if not isinstance(source, dict):
            raise SystemExit(f"Source config item #{index + 1} must be an object.")

        missing_fields = [
            field_name for field_name in ("path", "source_type", "authority", "status")
            if not source.get(field_name)
        ]

        if missing_fields:
            raise SystemExit(
                f"Source config item #{index + 1} is missing: {', '.join(missing_fields)}"
            )

        source_path = Path(source["path"])

        if not source_path.is_absolute():
            source_path = TOOLS_DIR / source_path

        source_configs.append(
            {
                **source,
                "path": source_path.resolve(),
                "required": bool(source.get("required", False)),
            }
        )

    return source_configs


def validate_source_paths(source_configs: list[dict]) -> None:
    missing_required_sources = [
        source_config["path"]
        for source_config in source_configs
        if source_config["required"] and not source_config["path"].exists()
    ]

    if not missing_required_sources:
        return

    formatted_paths = "\n".join(f"- {source_path}" for source_path in missing_required_sources)
    raise SystemExit(f"Missing required RAG source(s):\n{formatted_paths}")


def iter_markdown_files(source_path: Path):
    if source_path.is_file() and source_path.suffix.lower() == ".md":
        if not is_excluded_source(source_path, WORKSPACE_ROOT, EXCLUDED_SOURCE_PATHS):
            yield source_path
        return

    if source_path.is_dir():
        for file_path in source_path.rglob("*.md"):
            if not is_excluded_source(file_path, WORKSPACE_ROOT, EXCLUDED_SOURCE_PATHS):
                yield file_path


# ---------------------------------------------------------------------------
# Ingester: groups all stateful operations so no implicit global state
# ---------------------------------------------------------------------------

class Ingester:
    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=True)
        self.client = QdrantClient(url=DEFAULT_QDRANT_URL)
        self.embedding_dimension = len(self.model.encode("dimension probe"))

        self.chunker = MarkdownChunker()
        self._points: list[PointStruct] = []

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def build_collection_manifest(self) -> dict:
        return build_collection_manifest(
            collection_base_name=COLLECTION_BASE_NAME,
            collection_name=COLLECTION_NAME,
            collection_version=COLLECTION_VERSION,
            embedding_model=EMBEDDING_MODEL,
            embedding_dimension=self.embedding_dimension,
        )

    def ensure_collection(self) -> None:
        if not self.client.collection_exists(collection_name=COLLECTION_NAME):
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE,
                ),
            )
            write_collection_manifest(COLLECTION_MANIFEST_PATH, self.build_collection_manifest())
            return

        manifest = read_collection_manifest(COLLECTION_MANIFEST_PATH)

        if manifest is None:
            raise SystemExit(
                f"Missing collection manifest: {COLLECTION_MANIFEST_PATH}\n"
                "Do not ingest into an existing collection without metadata. "
                "Create a new collection version or recreate the collection with ingest.py."
            )

        validate_collection_manifest(manifest, self.build_collection_manifest())

    def ensure_payload_indexes(self) -> None:
        indexed_fields = {
            "authority": PayloadSchemaType.KEYWORD,
            "status": PayloadSchemaType.KEYWORD,
            "source_type": PayloadSchemaType.KEYWORD,
            "source": PayloadSchemaType.KEYWORD,
            "file_id": PayloadSchemaType.KEYWORD,
            "file_hash": PayloadSchemaType.KEYWORD,
            "source_path": PayloadSchemaType.TEXT,
        }

        for field_name, field_schema in indexed_fields.items():
            try:
                self.client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name=field_name,
                    field_schema=field_schema,
                )
            except Exception as ex:
                message = str(ex).lower()

                if "already exists" in message or "already has" in message:
                    continue

                raise

    def delete_existing_file_points(self, file_id: str) -> None:
        self.client.delete(
            collection_name=COLLECTION_NAME,
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
            collection_name=COLLECTION_NAME,
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
                collection_name=COLLECTION_NAME,
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
            collection_name=COLLECTION_NAME,
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
            collection_name=COLLECTION_NAME,
            points=self._points,
        )
        self._points.clear()
        return flushed_count

    def build_file_points(self, metadata: dict, file_path: Path) -> list[PointStruct]:
        text = file_path.read_text(encoding="utf-8")
        chunks = self.chunker.split(text)
        file_points = []

        for index, chunk in enumerate(chunks):
            chunk_text = chunk["text"]
            vector = self.model.encode(chunk_text).tolist()

            file_points.append(
                PointStruct(
                    id=build_point_id(metadata["source_path"], index, chunk_text),
                    vector=vector,
                    payload={
                        **metadata,
                        "chunk_index": index,
                        "section_index": chunk["section_index"],
                        "section_path": chunk["section_path"],
                        "text": chunk_text,
                    },
                )
            )

        return file_points

    # ------------------------------------------------------------------
    # Main ingest loop
    # ------------------------------------------------------------------

    def run(self, source_configs: list[dict]) -> None:
        self.ensure_collection()
        self.ensure_payload_indexes()

        indexed_chunks = 0
        indexed_files = 0
        skipped_files = 0
        seen_file_ids: set[str] = set()

        for source_config in source_configs:
            source_path = source_config["path"]

            if not source_path.exists():
                print(f"Skipped optional missing source: {source_path}")
                continue

            for file_path in iter_markdown_files(source_path):
                metadata = build_metadata(source_config, file_path, WORKSPACE_ROOT)
                seen_file_ids.add(metadata["file_id"])

                if self.is_file_unchanged(metadata["file_id"], metadata["file_hash"]):
                    skipped_files += 1
                    continue

                file_points = self.build_file_points(metadata, file_path)

                self.delete_existing_file_points(metadata["file_id"])
                self._points.extend(file_points)
                indexed_chunks += len(file_points)
                indexed_files += 1

                if len(self._points) >= BATCH_SIZE:
                    self.flush_points()

        if not seen_file_ids:
            raise SystemExit("No source files found. Abort cleanup to avoid deleting collection.")

        self.flush_points()

        orphaned_files = self.cleanup_orphaned_file_points(seen_file_ids)

        print(
            f"Indexed {indexed_chunks} chunks from {indexed_files} changed files; "
            f"skipped {skipped_files} unchanged files; "
            f"removed {orphaned_files} orphaned files"
        )


def main() -> None:
    source_configs = load_source_configs()
    validate_source_paths(source_configs)
    Ingester().run(source_configs)


if __name__ == "__main__":
    main()
