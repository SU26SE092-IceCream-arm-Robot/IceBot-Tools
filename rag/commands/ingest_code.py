import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[2]))

from qdrant_client.models import PayloadSchemaType

from raglib.code_chunking import CodeChunker, get_language
from raglib.config import WORKSPACE_ROOT, get_collection_lane, setup_cache_env
from raglib.ingestion import BaseIngester, validate_source_paths
from raglib.logging import configure_logger
from raglib.source_metadata import build_point_id, is_excluded_source


setup_cache_env()


EXCLUDED_SOURCE_PATHS = set()
EXCLUDED_SOURCE_PREFIXES = {
    "Vault/Learning/Personal/",
    "Vault/Learning/Tooling/",
    "Vault/Research/Papers/",
}
INCLUDED_CODE_SUFFIXES = {".cs", ".csproj", ".json", ".props", ".targets"}
EXCLUDED_CODE_PARTS = {
    ".git",
    ".vs",
    "bin",
    "obj",
    "Migrations",
    "logs",
    "node_modules",
}

LOGGER = configure_logger("icebot.rag.ingest_code", "ingest_code.log")
COLLECTION_LANE = get_collection_lane("code")


def is_code_file(file_path: Path) -> bool:
    if file_path.suffix not in INCLUDED_CODE_SUFFIXES:
        return False

    return not any(part in EXCLUDED_CODE_PARTS for part in file_path.parts)


class CodeIngester(BaseIngester):
    collection_lane_name = "code"
    missing_source_message = (
        "Create rag/sources.code.local.json or restore rag/sources.code.example.json."
    )
    missing_manifest_message = (
        "Create a new collection version or recreate the collection with ingest_code.py."
    )
    log_label = "code"

    def __init__(self) -> None:
        super().__init__(COLLECTION_LANE, LOGGER)
        self.chunker = CodeChunker()

    def payload_indexes(self) -> dict:
        return {
            **super().payload_indexes(),
            "language": PayloadSchemaType.KEYWORD,
            "namespace": PayloadSchemaType.KEYWORD,
            "symbol_kind": PayloadSchemaType.KEYWORD,
            "symbol_name": PayloadSchemaType.KEYWORD,
        }

    def iter_files(self, source_path: Path):
        if source_path.is_file() and is_code_file(source_path):
            if not is_excluded_source(
                source_path,
                WORKSPACE_ROOT,
                EXCLUDED_SOURCE_PATHS,
                EXCLUDED_SOURCE_PREFIXES,
            ):
                yield source_path
            return

        if source_path.is_dir():
            for file_path in source_path.rglob("*"):
                if not file_path.is_file() or not is_code_file(file_path):
                    continue

                if not is_excluded_source(
                    file_path,
                    WORKSPACE_ROOT,
                    EXCLUDED_SOURCE_PATHS,
                    EXCLUDED_SOURCE_PREFIXES,
                ):
                    yield file_path

    def build_chunks(self, file_path: Path) -> tuple[list[dict], int]:
        text = file_path.read_text(encoding="utf-8")
        chunks = self.chunker.split(text, file_path)
        return chunks, self.chunker.last_skipped_empty_chunks

    def build_chunk_payload(self, chunk: dict, file_path: Path) -> dict:
        return {
            "language": get_language(file_path),
            "namespace": chunk["namespace"],
            "symbol_kind": chunk["symbol_kind"],
            "symbol_name": chunk["symbol_name"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
        }

    def build_point_id(self, source_path: str, chunk_index: int, chunk_text: str) -> str:
        return build_point_id(source_path, chunk_index, chunk_text)


def main() -> None:
    ingester = CodeIngester()
    source_configs = ingester.load_source_configs()
    validate_source_paths(source_configs)
    ingester.run(source_configs)


if __name__ == "__main__":
    main()
