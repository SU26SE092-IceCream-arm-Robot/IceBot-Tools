import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[2]))

from qdrant_client.models import PayloadSchemaType

from raglib.config import WORKSPACE_ROOT, get_collection_lane, setup_cache_env
from raglib.ingestion import BaseIngester, validate_source_paths
from raglib.logging import configure_logger
from raglib.markdown_chunking import MarkdownChunker
from raglib.source_metadata import build_point_id, is_excluded_source


setup_cache_env()


EXCLUDED_SOURCE_PATHS = set()
EXCLUDED_SOURCE_PREFIXES = {
    "Vault/Learning/Personal/",
    "Vault/Learning/Tooling/",
    "Vault/Research/Papers/",
}

LOGGER = configure_logger("icebot.rag.ingest", "ingest.log")
COLLECTION_LANE = get_collection_lane("docs")


class DocsIngester(BaseIngester):
    collection_lane_name = "docs"
    missing_source_message = (
        "Create rag/sources.docs.local.json or restore rag/sources.docs.example.json."
    )
    missing_manifest_message = (
        "Create a new collection version or recreate the collection with ingest_docs.py."
    )
    log_label = "docs"

    def __init__(self) -> None:
        super().__init__(COLLECTION_LANE, LOGGER)
        self.chunker = MarkdownChunker()

    def payload_indexes(self) -> dict:
        return {
            **super().payload_indexes(),
            "is_overview": PayloadSchemaType.BOOL,
        }

    def iter_files(self, source_path: Path):
        if source_path.is_file() and source_path.suffix.lower() == ".md":
            if not is_excluded_source(
                source_path,
                WORKSPACE_ROOT,
                EXCLUDED_SOURCE_PATHS,
                EXCLUDED_SOURCE_PREFIXES,
            ):
                yield source_path
            return

        if source_path.is_dir():
            for file_path in source_path.rglob("*.md"):
                if not is_excluded_source(
                    file_path,
                    WORKSPACE_ROOT,
                    EXCLUDED_SOURCE_PATHS,
                    EXCLUDED_SOURCE_PREFIXES,
                ):
                    yield file_path

    def build_chunks(self, file_path: Path) -> tuple[list[dict], int]:
        text = file_path.read_text(encoding="utf-8")
        chunks = self.chunker.split(text)
        return chunks, self.chunker.last_skipped_empty_chunks

    def build_chunk_payload(self, chunk: dict, file_path: Path) -> dict:
        return {
            "section_index": chunk["section_index"],
            "section_path": chunk["section_path"],
            "is_overview": chunk["section_index"] == 0,
        }

    def build_point_id(self, source_path: str, chunk_index: int, chunk_text: str) -> str:
        return build_point_id(source_path, chunk_index, chunk_text)


def main() -> None:
    ingester = DocsIngester()
    source_configs = ingester.load_source_configs()
    validate_source_paths(source_configs)
    ingester.run(source_configs)


if __name__ == "__main__":
    main()
