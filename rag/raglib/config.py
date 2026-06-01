import os
from pathlib import Path

RAGLIB_DIR = Path(__file__).resolve().parent
RAG_DIR = RAGLIB_DIR.parent
TOOLS_DIR = RAG_DIR.parent
WORKSPACE_ROOT = TOOLS_DIR.parent


def load_rag_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv(RAG_DIR / ".env")
    load_dotenv(TOOLS_DIR / ".env")
    load_dotenv()


load_rag_env()

CACHE_ROOT = Path(os.getenv("RAG_CACHE_ROOT", str(Path.home() / ".cache" / "icebot-rag")))
COLLECTION_BASE_NAME = os.getenv("RAG_COLLECTION_BASE_NAME", "icebot_project_knowledge")
COLLECTION_VERSION = os.getenv("RAG_COLLECTION_VERSION", "v1")
COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", f"{COLLECTION_BASE_NAME}_{COLLECTION_VERSION}")
COLLECTION_MANIFEST_DIR = TOOLS_DIR / "data" / "rag_collections"
COLLECTION_MANIFEST_PATH = COLLECTION_MANIFEST_DIR / f"{COLLECTION_NAME}.json"
SOURCES_EXAMPLE_PATH = RAG_DIR / "sources.example.json"
SOURCES_LOCAL_PATH = RAG_DIR / "sources.local.json"
MAX_RETRIEVAL_LIMIT = int(os.getenv("RAG_MAX_RETRIEVAL_LIMIT", "10"))
MAX_CANDIDATE_LIMIT = int(os.getenv("RAG_MAX_CANDIDATE_LIMIT", "100"))

EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
RERANKER_MODEL = os.getenv("RAG_RERANKER_MODEL", "Qwen/Qwen3-Reranker-0.6B")
DEFAULT_LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
DEFAULT_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")


def setup_cache_env() -> None:
    os.environ.setdefault("HF_HOME", str(CACHE_ROOT / "huggingface"))
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(CACHE_ROOT / "sentence-transformers"))
