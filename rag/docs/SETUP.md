# RAG Setup

This file documents local setup, environment variables, storage boundaries, and run order for IceBot RAG tooling.

Run commands from `IceBot-Tools`.

## Storage Boundaries

- `IceBot-Tools/data/qdrant` stores generated Qdrant data mounted by Docker.
- `IceBot-Tools/logs/rag` stores runtime logs such as `ingest.log`.
- `RAG_CACHE_ROOT` controls where local model/cache files are stored.
- `FASTEMBED_CACHE_PATH` is set automatically to `CACHE_ROOT/fastembed`; set it explicitly only when you need a custom sparse-model cache location.
- `RAG_LOG_DIR` controls where RAG runtime logs are stored.
- RAG logs use size-based rotation by default: 10 MB per file and 10 backups.
- `RAG_LOG_CONSOLE=false` keeps routine INFO logs in files only; console shows WARNING+ plus command summaries.
- If `RAG_CACHE_ROOT` is unset, cache files use the user home cache folder: `~/.cache/icebot-rag`.
- Do not copy canonical docs into `IceBot-Tools/data` as a permanent source. Ingest should read from the original source folders.

## Qdrant Local Dashboard

When the local Qdrant container is running, open:

```text
http://localhost:6333/dashboard
```

## Local Environment

- `IceBot-Tools/rag/.env` stores local-only values and is ignored by git.
- `IceBot-Tools/rag/.env.example` is the safe template.
- `IceBot-Tools/rag/sources.docs.local.json` stores docs source overrides and is ignored by git.
- `IceBot-Tools/rag/sources.code.local.json` stores code source overrides and is ignored by git.
- `OPENAI_API_KEY` is required only for `commands/ask.py`.
- `RAG_CACHE_ROOT` is optional. If unset, model/cache files use the user home cache folder: `~/.cache/icebot-rag`.
- `RAG_LOG_DIR` is optional. If unset, logs use `IceBot-Tools/logs/rag`.
- `RAG_LOG_MAX_BYTES` and `RAG_LOG_BACKUP_COUNT` are optional. Defaults keep about 110 MB per log stream.
- `RAG_LOG_CONSOLE` is optional. Set `true` to show INFO logs in the terminal while debugging.
- `RAG_CHUNK_SIZE` and `RAG_CHUNK_OVERLAP` are optional. Defaults are `800` and `120`.
- `RAG_ENABLE_HYBRID` controls Qdrant dense+sparse hybrid retrieval. Default is `true`.
- `RAG_SPARSE_MODEL` controls the sparse model used by `fastembed`. Default is `Qdrant/bm25`.
- `commands/context.py`, `commands/search.py`, `commands/ingest_docs.py`, `commands/ingest_code.py`, and `mcp_server.py` do not call OpenAI directly.

## First-Time Setup

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
python .\rag\commands\ask.py
```

## Later Usage

```powershell
docker compose -f docker\docker-compose.yml up -d
.\.venv\Scripts\Activate.ps1
python .\rag\commands\context.py "current payment flow"
```

## MCP Server

`mcp_server.py` exposes local retrieval as an MCP tool:

```text
retrieve_icebot_context
retrieve_icebot_docs
retrieve_icebot_code
```

It does not call OpenAI and does not need `OPENAI_API_KEY`. The IDE/model using MCP is responsible for reasoning over the returned context.

`retrieve_icebot_context` is the router-level tool and accepts `mode=docs|code|both`; it defaults to docs. The docs/code tools are shortcuts.

Run from `IceBot-Tools`:

```powershell
.\.venv\Scripts\Activate.ps1
python .\rag\mcp_server.py
```

The MCP server is a long-running process, so `raglib/vector_store.py` keeps the embedding model, reranker, Qdrant client, and optional sparse BM25 model loaded and reuses them across tool calls.

## Codex MCP Registration

Register the MCP server with Codex:

```powershell
codex mcp add icebot-rag -- "<path-to-IceBot-Tools>\.venv\Scripts\python.exe" "<path-to-IceBot-Tools>\rag\mcp_server.py"
```

Example if the repository is under your user profile:

```powershell
$toolsRoot = "$env:USERPROFILE\Projects\IceCream_arm_Robot\IceBot-Tools"
codex mcp add icebot-rag -- "$toolsRoot\.venv\Scripts\python.exe" "$toolsRoot\rag\mcp_server.py"
```

Verify:

```powershell
codex mcp list
```

Expected server name:

```text
icebot-rag
```

Restart the Codex extension or IDE so MCP config is reloaded.

After setup, ask Codex to use the MCP tool explicitly:

```text
Use icebot-rag to retrieve context about the current payment flow, then review the payment code.
```

The exposed tools are:

```text
retrieve_icebot_context
retrieve_icebot_docs
retrieve_icebot_code
```

The tools return context chunks with metadata such as source path, authority, status, retrieval scores, and code symbol/line metadata when available.
Use `retrieve_icebot_context` with `mode=docs|code|both` when you want explicit routing in one tool. Use `retrieve_icebot_docs` and `retrieve_icebot_code` as shortcuts.
The tools accept `use_hybrid=true|false`. Hybrid uses Qdrant dense+sparse retrieval and is useful for exact symbols, paths, endpoints, and enum names.

## Operational Notes

- Keep Qdrant storage, model cache, and knowledge sources separate.
- Do not rename storage folders or change paths just because a naming question is being discussed. Apply structural changes only after an explicit decision.
- Hybrid search requires the current named-vector schema. `v1` is the initial active collection version because no earlier collection data is being preserved.
