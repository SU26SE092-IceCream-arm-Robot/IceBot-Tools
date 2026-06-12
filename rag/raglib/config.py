import os
from pathlib import Path

from toolcore.workspace import TOOLS_DIR, WORKSPACE_ROOT
RAGLIB_DIR = Path(__file__).resolve().parent
RAG_DIR = RAGLIB_DIR.parent


def load_rag_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv(RAG_DIR / ".env")
    load_dotenv(TOOLS_DIR / ".env")
    load_dotenv()


load_rag_env()


def parse_bool_env(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


CACHE_ROOT = Path(os.getenv("RAG_CACHE_ROOT", str(Path.home() / ".cache" / "icebot-rag")))
DOCS_COLLECTION_BASE_NAME = os.getenv("RAG_DOCS_COLLECTION_BASE_NAME", "icebot_docs_knowledge")
DOCS_COLLECTION_VERSION = os.getenv("RAG_DOCS_COLLECTION_VERSION", "v1")
DOCS_COLLECTION_NAME = os.getenv(
    "RAG_DOCS_COLLECTION_NAME",
    f"{DOCS_COLLECTION_BASE_NAME}_{DOCS_COLLECTION_VERSION}",
)
CODE_COLLECTION_BASE_NAME = os.getenv("RAG_CODE_COLLECTION_BASE_NAME", "icebot_code_knowledge")
CODE_COLLECTION_VERSION = os.getenv("RAG_CODE_COLLECTION_VERSION", "v1")
CODE_COLLECTION_NAME = os.getenv(
    "RAG_CODE_COLLECTION_NAME",
    f"{CODE_COLLECTION_BASE_NAME}_{CODE_COLLECTION_VERSION}",
)
COLLECTION_MANIFEST_DIR = TOOLS_DIR / "data" / "rag_collections"
DOCS_COLLECTION_MANIFEST_PATH = COLLECTION_MANIFEST_DIR / f"{DOCS_COLLECTION_NAME}.json"
CODE_COLLECTION_MANIFEST_PATH = COLLECTION_MANIFEST_DIR / f"{CODE_COLLECTION_NAME}.json"
DOCS_SOURCES_EXAMPLE_PATH = RAG_DIR / "sources.docs.example.json"
DOCS_SOURCES_LOCAL_PATH = RAG_DIR / "sources.docs.local.json"
CODE_SOURCES_EXAMPLE_PATH = RAG_DIR / "sources.code.example.json"
CODE_SOURCES_LOCAL_PATH = RAG_DIR / "sources.code.local.json"
RAG_LOG_DIR = Path(os.getenv("RAG_LOG_DIR", str(TOOLS_DIR / "logs" / "rag")))
RAG_LOG_MAX_BYTES = int(os.getenv("RAG_LOG_MAX_BYTES", str(10 * 1024 * 1024)))
RAG_LOG_BACKUP_COUNT = int(os.getenv("RAG_LOG_BACKUP_COUNT", "10"))
RAG_LOG_CONSOLE = parse_bool_env("RAG_LOG_CONSOLE", default=False)
RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "800"))
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "120"))
MAX_RETRIEVAL_LIMIT = int(os.getenv("RAG_MAX_RETRIEVAL_LIMIT", "10"))
MAX_CANDIDATE_LIMIT = int(os.getenv("RAG_MAX_CANDIDATE_LIMIT", "100"))

EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
SPARSE_MODEL = os.getenv("RAG_SPARSE_MODEL", "Qdrant/bm25")
ENABLE_HYBRID = parse_bool_env("RAG_ENABLE_HYBRID", default=True)
HYBRID_RRF_K = int(os.getenv("RAG_HYBRID_RRF_K", "60"))
RERANKER_MODEL = os.getenv("RAG_RERANKER_MODEL", "Qwen/Qwen3-Reranker-0.6B")
DEFAULT_LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
DEFAULT_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")


COLLECTION_LANES = {
    "docs": {
        "base_name": DOCS_COLLECTION_BASE_NAME,
        "version": DOCS_COLLECTION_VERSION,
        "name": DOCS_COLLECTION_NAME,
        "manifest_path": DOCS_COLLECTION_MANIFEST_PATH,
        "sources_example_path": DOCS_SOURCES_EXAMPLE_PATH,
        "sources_local_path": DOCS_SOURCES_LOCAL_PATH,
    },
    "code": {
        "base_name": CODE_COLLECTION_BASE_NAME,
        "version": CODE_COLLECTION_VERSION,
        "name": CODE_COLLECTION_NAME,
        "manifest_path": CODE_COLLECTION_MANIFEST_PATH,
        "sources_example_path": CODE_SOURCES_EXAMPLE_PATH,
        "sources_local_path": CODE_SOURCES_LOCAL_PATH,
    },
}


def get_collection_lane(lane: str = "docs") -> dict:
    try:
        return COLLECTION_LANES[lane]
    except KeyError as ex:
        supported_lanes = ", ".join(sorted(COLLECTION_LANES))
        raise ValueError(f"Unsupported RAG collection lane: {lane}. Supported: {supported_lanes}") from ex


def setup_cache_env() -> None:
    os.environ.setdefault("HF_HOME", str(CACHE_ROOT / "huggingface"))
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(CACHE_ROOT / "sentence-transformers"))
    os.environ.setdefault("FASTEMBED_CACHE_PATH", str(CACHE_ROOT / "fastembed"))


def get_qdrant_client():
    from qdrant_client import QdrantClient
    url = os.getenv("QDRANT_URL", "http://localhost:6333")

    local_path = Path(os.getenv("QDRANT_LOCAL_PATH", str(TOOLS_DIR / "data" / "qdrant_local")))

    if url.lower() == "local":
        local_path.mkdir(parents=True, exist_ok=True)
        return QdrantClient(path=str(local_path))

    try:
        import urllib.request
        # Check if the url has schema
        test_url = url
        if not test_url.startswith("http://") and not test_url.startswith("https://"):
            test_url = "http://" + test_url
        urllib.request.urlopen(test_url, timeout=1.0)
        return QdrantClient(url=url)
    except Exception:
        local_path.mkdir(parents=True, exist_ok=True)
        import logging
        logging.getLogger("icebot.rag").warning(
            f"Failed to connect to Qdrant at {url}. Falling back to local storage: {local_path}"
        )
        return QdrantClient(path=str(local_path))
