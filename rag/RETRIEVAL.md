# RAG Retrieval

This file documents search, context retrieval, reranking, and safety limits.

## Default Authority

Default search/ask behavior should use official sources only:

- `authority = official`

Vault should be opt-in:

- use `--include-vault`
- treat `draft`, `raw`, `future`, `learning`, and `rejected` as lower-authority context
- never treat rejected notes as recommended designs

## Useful Metadata Filters

```powershell
python .\rag\commands\search.py "payment flow" --source-type backend-doc
python .\rag\commands\search.py "authentication routes" --source-group docs --doc-type api
python .\rag\commands\search.py "business flow" --source-type project-doc
python .\rag\commands\search.py "robot workflow" --include-vault --source-type vault
python .\rag\commands\search.py "iot contract" --path-contains IOT_CONTRACT
python .\rag\commands\search.py "forgot password API" --doc-type api --exclude-overview
python .\rag\commands\context.py "payment flow" --format markdown
```

Useful fields:

- `source_group`: broad origin, such as `docs`, `vault`, `code`, or `logs`.
- `doc_type`: document intent, such as `api`, `flow`, `contract`, `architecture`, `domain`, or `decision`.
- `source_type`: source folder class, such as `backend-doc`, `project-doc`, or `vault`.
- `is_overview`: true for first/root chunks that often contain generic introduction text.

Prefer metadata and path filters before increasing reranker candidate limits.

## Reranking

`commands/context.py`, `commands/search.py`, and `commands/ask.py` use a reranker by default:

```text
Qwen/Qwen3-Reranker-0.6B
```

The retrieval flow is:

1. vector search retrieves `--candidate-limit` candidates from Qdrant, default `100`
2. reranker scores `(question, chunk text)` pairs
3. final output keeps the top `--limit` reranked chunks

When reranking is disabled, vector search retrieves only `--limit` results instead of `--candidate-limit`.

Use `--no-rerank` only for debugging raw vector search results or reducing local runtime cost.

## Safety Limits

Retrieval has process-level safety caps to prevent a CLI command or MCP agent call from requesting too much local work:

```text
RAG_MAX_RETRIEVAL_LIMIT=10
RAG_MAX_CANDIDATE_LIMIT=100
```

These caps apply in `raglib/vector_store.py`, so they cover `context.py`, `search.py`, `ask.py`, and `mcp_server.py`.

## Command Roles

- `commands/context.py` is for retrieving context for Codex IDE/CLI without a separate `OPENAI_API_KEY`.
- `commands/search.py` is for inspecting retrieved chunks and metadata.
- `commands/ask.py` is for generating an answer from retrieved chunks through OpenAI.
- `mcp_server.py` is long-running and reuses embedding/reranker models as process-level singletons.
- Retrieval outputs include `section_index` and `section_path` from Markdown header-aware chunking when available.
- Retrieval outputs include `source_group`, `doc_type`, `source_of_truth`, and `is_overview` after the collection is re-ingested with the current metadata schema.

## Runtime Notes

- Reranking improves precision but adds local model load time and inference latency.
- Lower `--candidate-limit` if local search feels too slow.
- CLI commands start a new Python process each run, so the embedding model and reranker are loaded each time.
- `Qwen3-Reranker-0.6B` is not lightweight. Use `--no-rerank` for quick debugging when precision is less important.
- MCP tool calls have a host timeout. If reranker cold start exceeds that timeout, use `use_reranker=false` for MCP/IDE retrieval and reserve reranking for warmed long-running sessions or direct CLI experimentation.
- On a local 16 GB RAM machine, MCP reranking with `candidate_limit=5` completed but `candidate_limit=50` timed out and pushed RAM close to full. Keep MCP reranker candidate limits low unless measured otherwise.
