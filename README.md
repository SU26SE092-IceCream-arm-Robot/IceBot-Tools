# IceBot-Tools

Local tooling for IceBot development: RAG, MCP, Code Intelligence, diagnostics, local observability, PDF extraction, Docker helpers, and scripts.

This repository is not project source of truth and is not the future public harness. Project-facing simulator, smoke-test, or demo automation should live in a separate `IceBot-Harness` repository when needed.

## Read First

- Main commands: [docs/ENTRYPOINTS.md](docs/ENTRYPOINTS.md)
- Tool boundaries: [docs/TOOLING.md](docs/TOOLING.md)
- Storage and generated data: [docs/STORAGE.md](docs/STORAGE.md)
- RAG setup: [rag/docs/SETUP.md](rag/docs/SETUP.md)
- Code Intelligence design: [code-intelligence/docs/CODE_INTELLIGENCE_SYSTEM.md](code-intelligence/docs/CODE_INTELLIGENCE_SYSTEM.md)
- Code Intelligence commands: [code-intelligence/docs/USAGE.md](code-intelligence/docs/USAGE.md)
- Docs Ops commands: [docs-ops/docs/USAGE.md](docs-ops/docs/USAGE.md)
- Log Analyzer commands: [log-analyzer/docs/USAGE.md](log-analyzer/docs/USAGE.md)
- PDF workflow: [pdf/docs/PDF_WORKFLOW.md](pdf/docs/PDF_WORKFLOW.md)

## Folder Map

| Folder | Purpose |
| --- | --- |
| `toolcore/` | Shared workspace paths, source config loading, ignore rules, and logging infrastructure. |
| `mcp/` | Unified MCP server over RAG and Code Intelligence. |
| `rag/` | Semantic retrieval, indexing, and context routing. |
| `code-intelligence/` | Structural code index and exact lookups. |
| `docs-ops/` | Markdown link, doc index, and stale-reference checks. |
| `log-analyzer/` | Local log grouping and diagnostic checks. |
| `pdf/` | PDF extraction and paper/source review workflow. |
| `docker/` | Docker Compose files for local tooling services such as Qdrant and Aspire Dashboard. |
| `scripts/` | Helper scripts for local workflows. |
| `infrastructure/` | Public-safe templates for local machine/runtime notes. |
| `data/` | Generated local data. Ignored by git. |
| `.local/` | Private machine-specific notes. Ignored by git. |

## Rules

- Keep generated data in `data/`.
- Keep runtime logs in `logs/`.
- Keep machine-specific notes in `.local/`.
- Keep shared helper infrastructure in `toolcore/`.
- Keep RAG and Code Intelligence as separate capability lanes.
- Keep MCP as the adapter over both lanes.
- Do not commit secrets, provider credentials, real customer logs, or private machine details.
