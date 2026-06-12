# IceBot-Tools Storage Boundaries

Generated data, logs, and local machine notes are not project source of truth.

## Generated Data

| Path | Purpose |
| --- | --- |
| `data/qdrant/` | Qdrant data mounted by Docker. |
| `data/qdrant_local/` | Qdrant local-mode fallback data. |
| `data/rag_collections/` | RAG collection manifests. |
| `data/code_intelligence/` | SQLite structural code index and exports. |
| `data/pdf_extracts/` | Raw PDF extraction output before curation. |
| `data/log-analyzer/` | Log analyzer mock/generated input data. |

These folders are generated state and should stay ignored by git.

## Logs

| Path | Purpose |
| --- | --- |
| `logs/rag/` | RAG ingest/retrieval logs. |
| `logs/system/` | Local system snapshot logs. |
| `logs/log-analyzer/` | Log analyzer violation reports. |

Logs are local runtime artifacts. Do not commit secrets, customer logs, or machine-private data.

## Local Machine Notes

| Path | Purpose |
| --- | --- |
| `.local/` | Private machine-specific notes and observations. |
| `infrastructure/*.example.md` | Public-safe templates for `.local/` files. |

Copy templates from `infrastructure/` into `.local/` when needed.

## RAG Cache

- `RAG_CACHE_ROOT` controls local model/cache files.
- If unset, cache files default to `~/.cache/icebot-rag`.
- `FASTEMBED_CACHE_PATH` is set automatically to `RAG_CACHE_ROOT/fastembed` unless overridden.

## Rules

- Source docs stay in their original folders; do not copy canonical docs into `data/`.
- Generated indexes can be deleted and rebuilt.
- If generated cache conflicts with source code/docs, source code/docs win.
- Do not auto-ingest or auto-index from unrelated workflows.
