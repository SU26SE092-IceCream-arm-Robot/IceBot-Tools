# IceBot RAG Tooling Notes

This folder contains local RAG scripts for searching and asking over IceBot project knowledge.

## Read First

- [CONTEXT_ROUTING.md](CONTEXT_ROUTING.md): when to use RAG and which sources to trust.
- [INDEXING.md](INDEXING.md): ingest, chunking, metadata, collection versioning, and cleanup.
- [RETRIEVAL.md](RETRIEVAL.md): search/context/ask behavior, reranking, filters, and safety limits.
- [MCP_SETUP.md](MCP_SETUP.md): exposing local retrieval to Codex through MCP.

## Files

- `commands/ingest.py`: reads source docs and incrementally writes chunks into Qdrant.
- `commands/context.py`: retrieves context without calling an LLM, intended for Codex IDE/CLI use.
- `commands/search.py`: retrieves and prints chunks for inspection.
- `commands/ask.py`: retrieves chunks and asks OpenAI to answer from that context.
- `mcp_server.py`: exposes local RAG retrieval as an MCP server without calling OpenAI directly.
- `raglib/config.py`: shared constants, workspace paths, model names, Qdrant URL, and cache environment setup.
- `raglib/retrieval.py`: shared Qdrant metadata filter and reranking helper.
- `raglib/vector_store.py`: shared Qdrant vector search and rerank orchestration.

## Source Boundaries

- `rag/sources.example.json` defines the default example source list.
- `rag/sources.local.json` is an ignored per-machine override for local paths and source availability.
- Missing optional sources are skipped during ingest. Use this for folders such as `Docs` or `Vault` that may not exist on every machine.
- Missing required sources abort ingest before cleanup.
- `IceBot-Backend` is implementation truth for backend code and backend docs when available.
- `Docs` is shared project/team truth when available.
- `Vault` is project-specific personal reasoning and draft knowledge when available. It is useful context, but not official truth.
- `IceBot-Tools` is tooling/runtime support. It should not become the source of truth for project knowledge.
- IceBot-Tools docs are operational tooling docs. They are not ingested into the default project knowledge collection.
- `IceBot-Backend/.project-memory` is working context only and must not be ingested into the long-lived vector database.

## Storage Boundaries

- `IceBot-Tools/data/qdrant` stores generated Qdrant data mounted by Docker.
- `RAG_CACHE_ROOT` controls where local model/cache files are stored.
- If `RAG_CACHE_ROOT` is unset, cache files use the user home cache folder: `~/.cache/icebot-rag`.
- Do not copy canonical docs into `IceBot-Tools/data` as a permanent source. Ingest should read from the original source folders.

## Qdrant Local Dashboard

When the local Qdrant container is running, open:

```text
http://localhost:6333/dashboard
```

## Run Order

Run commands from `IceBot-Tools`.

Local environment:

- `IceBot-Tools/rag/.env` stores local-only values and is ignored by git.
- `IceBot-Tools/rag/.env.example` is the safe template.
- `IceBot-Tools/rag/sources.local.json` stores local source overrides and is ignored by git.
- `OPENAI_API_KEY` is required only for `commands/ask.py`.
- `RAG_CACHE_ROOT` is optional. If unset, model/cache files use the user home cache folder: `~/.cache/icebot-rag`.
- `commands/context.py`, `commands/search.py`, `commands/ingest.py`, and `mcp_server.py` do not call OpenAI directly.

First-time setup:

```powershell
docker compose -f docker\docker-compose.yml up -d
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .\rag\sources.example.json .\rag\sources.local.json
# Edit .\rag\sources.local.json if your machine does not have every example source.
python .\rag\commands\ingest.py
python .\rag\commands\context.py "current payment flow"
python .\rag\commands\ask.py
```

Later usage:

```powershell
docker compose -f docker\docker-compose.yml up -d
.\.venv\Scripts\Activate.ps1
python .\rag\commands\context.py "current payment flow"
```

## MCP Server

`mcp_server.py` exposes local retrieval as an MCP tool:

```text
retrieve_icebot_context
```

It does not call OpenAI and does not need `OPENAI_API_KEY`. The IDE/model using MCP is responsible for reasoning over the returned context.

Run from `IceBot-Tools`:

```powershell
.\.venv\Scripts\Activate.ps1
python .\rag\mcp_server.py
```

The MCP server is a long-running process, so `raglib/vector_store.py` keeps the embedding model, reranker, and Qdrant client loaded and reuses them across tool calls.

## Operational Notes

- Keep Qdrant storage, model cache, and knowledge sources separate.
- Do not rename storage folders or change paths just because a naming question is being discussed. Apply structural changes only after an explicit decision.
