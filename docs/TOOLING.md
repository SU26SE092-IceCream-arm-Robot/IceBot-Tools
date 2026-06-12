# IceBot-Tools Tooling Guide

This file replaces per-folder README files for local tools. Keep detailed operational commands here or in the dedicated tool docs under each folder's `docs/` directory.

## Boundaries

| Tool | Boundary |
| --- | --- |
| `toolcore/` | Shared workspace paths, source config loading, ignore rules, and logging infrastructure. No RAG/scanner logic. |
| `mcp/` | Unified MCP adapter over RAG and Code Intelligence. |
| `rag/` | Semantic retrieval over docs/code chunks using Qdrant, dense embeddings, sparse/BM25, and optional reranking. |
| `code-intelligence/` | Exact structural index for symbols, endpoints, handlers, stores, DI, and relationships. |
| `log-analyzer/` | Local log grouping and diagnostic checks. Not production monitoring. |
| `pdf/` | PDF extraction workflow for paper/source review. |
| `scripts/` | Small helper scripts for repeatable local operations. |
| `infrastructure/` | Public-safe templates for local machine/runtime notes. |

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

## Log Analyzer

The log analyzer watches WebAPI and robot-style logs, groups repeated errors, and reports simple runtime/design violations.

Detailed commands live in `log-analyzer/docs/USAGE.md`.

Current checks include:

- slow EF Core database commands;
- blocked robot control thread;
- repeated exception grouping.

It is local tooling, not production monitoring.

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
