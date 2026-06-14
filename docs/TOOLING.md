# IceBot-Tools Tooling Guide

This file replaces per-folder README files for local tools. Keep detailed operational commands here or in the dedicated tool docs under each folder's `docs/` directory.

Tools should reduce context load. Do not make agents read tool docs before using a tool when the MCP description or command name is enough.

## Boundaries

| Tool | Boundary |
| --- | --- |
| `toolcore/` | Shared workspace paths, source config loading, ignore rules, and logging infrastructure. No RAG/scanner logic. |
| `mcp/` | Unified MCP adapter over RAG and Code Intelligence. |
| `rag/` | Semantic retrieval over docs/code chunks using Qdrant, dense embeddings, sparse/BM25, and optional reranking. |
| `code-intelligence/` | Exact structural index for symbols, endpoints, handlers, stores, DI, and relationships. |
| `docs-ops/` | Markdown link, doc index, and stale-reference checks. |
| `log-analyzer/` | Local log grouping and diagnostic checks. Not production monitoring. |
| `backend-preflight/` | Thin wrapper for backend build, docs checks, Code Intelligence coverage, and optional log checks. |
| `pdf/` | PDF extraction workflow for paper/source review. |
| `scripts/` | Small helper scripts for repeatable local operations. |
| `infrastructure/` | Public-safe templates for local machine/runtime notes. |
| `docker/` | Local tooling services such as Qdrant and Aspire Dashboard. Not backend runtime infrastructure. |

## RAG

Read:

- `rag/CONTEXT_ROUTING.md`
- `rag/docs/SETUP.md`
- `rag/docs/INDEXING.md`
- `rag/docs/RETRIEVAL.md`
- `rag/docs/HYBRID_SEARCH.md`
- `rag/docs/COLLECTION_SCHEMA.md`

Use RAG for meaning, background, contracts, rules, and semantic source-code context.

## Code Intelligence

Read:

- `code-intelligence/docs/CODE_INTELLIGENCE_SYSTEM.md`
- `code-intelligence/docs/USAGE.md`
- `code-intelligence/docs/INTERMEDIATE_CACHE.md`
- `code-intelligence/docs/SEMANTIC_CODE_INDEX.md`

Use Code Intelligence for exact structural lookup before semantic code retrieval.

## Docs Ops

Read:

- `docs-ops/docs/USAGE.md`

Use Docs Ops after moving, deleting, or splitting docs. It reports broken links, stale references, and important index/router doc problems.

MCP exposes this as `check_icebot_docs`. The MCP response is quiet on success and returns structured failures only when something needs action.

## MCP

Entrypoint:

```powershell
.\.venv\Scripts\python.exe .\mcp\server.py
```

MCP tools:

- `retrieve_icebot_context`
- `retrieve_icebot_docs`
- `retrieve_icebot_code`
- `lookup_icebot_symbol`
- `lookup_icebot_endpoint`
- `lookup_icebot_handler`
- `verify_icebot_code_index`
- `check_icebot_docs`
- `analyze_icebot_logs`
- `check_icebot_backend`

### MCP Response Rule

MCP tools should be quiet on success and verbose on failure.

On success, return only a compact status and one-line summary. On failure, return structured, actionable failures with a sensible maximum count.

This keeps successful checks from polluting agent context while still giving enough evidence to fix real issues.

## Log Analyzer

The log analyzer watches WebAPI and robot-style logs, groups repeated errors, and reports simple runtime/design violations.

Detailed commands live in `log-analyzer/docs/USAGE.md`.

MCP exposes this as `analyze_icebot_logs`. It runs once, returns capped structured output, and excludes RAG logs by default to avoid old ingest noise.

Current checks include:

- slow EF Core database commands;
- blocked robot control thread;
- repeated exception grouping.

It is local tooling, not production monitoring.

## Local Observability

Aspire Dashboard is available from the tools Docker Compose file as a local/dev observability viewer.

Boundary:

- Aspire Dashboard in `IceBot-Tools` is tooling/dev observability.
- It is not production monitoring.
- It is not a backend runtime dependency.
- The backend app should still run without cloning or starting `IceBot-Tools`.

Start it only when you need local OpenTelemetry/Aspire debugging:

```powershell
.\scripts\start_aspire_dashboard.ps1
```

UI:

```text
http://localhost:18888
```

OTLP endpoint:

```text
http://localhost:18889
```

## Backend Preflight

Backend preflight is a thin wrapper over existing checks. It does not replace focused tools; use it when you need one final backend readiness check.

Priority rule:

- use focused lookup/RAG/check tools while working;
- use `check_icebot_backend` only at the end of a meaningful backend task;
- do not read preflight internals unless changing or debugging the tool.

Command:

```powershell
python .\backend-preflight\commands\check_backend.py
```

MCP tool:

```text
check_icebot_backend
```

Default checks:

- `dotnet build` for `IceBot-Backend/src/IceBot.slnx`;
- Docs Ops aggregate check;
- Code Intelligence dry run + coverage check.

Log analyzer is optional because old/local logs can be noisy:

```powershell
python .\backend-preflight\commands\check_backend.py --include-logs
```

## Scripts

Script naming should be verb-first and target-specific, for example:

```text
start_qdrant
stop_qdrant
ingest_docs_rag
ingest_code_rag
start_icebot_mcp
```

Use `reset`, `delete`, or `clear` in a script name when it is destructive.
