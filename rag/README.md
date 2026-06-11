# IceBot RAG Tooling Notes

This folder contains local RAG scripts for searching and asking over IceBot project knowledge.

## Read First

- [CONTEXT_ROUTING.md](CONTEXT_ROUTING.md): when to use RAG and which sources to trust.
- [docs/SETUP.md](docs/SETUP.md): local environment, storage, run order, and MCP setup.
- [docs/INDEXING.md](docs/INDEXING.md): ingest, chunking, metadata, collection versioning, and cleanup.
- [docs/COLLECTION_SCHEMA.md](docs/COLLECTION_SCHEMA.md): Qdrant collection versioning, named vectors, manifests, and payload indexes.
- [docs/RETRIEVAL.md](docs/RETRIEVAL.md): search/context/ask behavior, reranking, filters, and safety limits.
- [docs/HYBRID_SEARCH.md](docs/HYBRID_SEARCH.md): dense + BM25 sparse hybrid retrieval and Qdrant RRF fusion.

## Files

- `commands/ingest_docs.py`: reads accepted docs and incrementally writes chunks into the docs Qdrant collection.
- `commands/ingest_code.py`: reads backend source code and incrementally writes chunks into the code Qdrant collection.
- `commands/context.py`: retrieves context without calling an LLM, intended for Codex IDE/CLI use.
- `commands/search.py`: retrieves and prints chunks for inspection.
- `commands/ask.py`: retrieves chunks and asks OpenAI to answer from that context.
- `mcp_server.py`: exposes local RAG retrieval as an MCP server without calling OpenAI directly.
- `raglib/config.py`: shared constants, workspace paths, model names, Qdrant URL, and cache environment setup.
- `raglib/logging.py`: shared console and file logging setup for RAG commands.
- `raglib/source_metadata.py`: source path normalization, file hash, point id, and metadata helpers.
- `raglib/markdown_chunking.py`: Markdown header-aware chunking before recursive text splitting.
- `raglib/code_chunking.py`: source-code chunking with basic language, namespace, symbol, and line metadata.
- `raglib/collection_manifest.py`: local collection manifest creation and validation.
- `raglib/retrieval.py`: shared Qdrant metadata filter and reranking helper.
- `raglib/vector_store.py`: shared Qdrant dense/sparse hybrid retrieval and rerank orchestration.

## Source Boundaries

- `rag/sources.docs.example.json` defines the default docs source list.
- `rag/sources.docs.local.json` is an ignored per-machine override for docs paths and source availability.
- `rag/sources.code.example.json` defines the default code source list.
- `rag/sources.code.local.json` is an ignored per-machine override for code paths and source availability.
- Missing optional sources are skipped during ingest. Use this for folders such as `Docs` or `Vault` that may not exist on every machine.
- Missing required sources abort ingest before cleanup.
- `IceBot-Backend` is implementation truth for backend code and backend docs when available.
- `Docs` is shared project/team truth when available.
- `Vault` is project-specific personal reasoning and draft knowledge when available. It is useful context, but not official truth.
- `IceBot-Tools` is tooling/runtime support. It should not become the source of truth for project knowledge.
- IceBot-Tools docs are operational tooling docs. They are not ingested into the default project knowledge collection.
- `IceBot-Backend/.project-memory` is working context only and must not be ingested into the long-lived vector database.

## Quick Start

Run commands from `IceBot-Tools`.

```powershell
docker compose -f docker\docker-compose.yml up -d
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .\rag\sources.docs.example.json .\rag\sources.docs.local.json
Copy-Item .\rag\sources.code.example.json .\rag\sources.code.local.json
# Edit local source files if your machine does not have every example source.
python .\rag\commands\ingest_docs.py
python .\rag\commands\ingest_code.py
python .\rag\commands\context.py "current payment flow"
python .\rag\commands\context.py --lane code "PaymentSessionsController"
```

See [docs/SETUP.md](docs/SETUP.md) for environment variables, storage boundaries, later usage, and MCP setup.

## MCP Server

See [docs/SETUP.md](docs/SETUP.md#codex-mcp-registration) for Codex MCP registration and manual server runtime.

## Operational Notes

- Keep Qdrant storage, model cache, and knowledge sources separate.
- Do not rename storage folders or change paths just because a naming question is being discussed. Apply structural changes only after an explicit decision.
- Hybrid search requires the current named-vector schema.
- Changing embedding model, vector dimension, sparse model, or vector schema requires a new collection version and manual re-ingest.
