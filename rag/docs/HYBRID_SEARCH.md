# Hybrid Search

This file documents IceBot-Tools hybrid retrieval: dense vector search + BM25 sparse search + Qdrant RRF fusion.

## Flow

By default retrieval uses Qdrant-native hybrid search when `RAG_ENABLE_HYBRID=true`:

```text
query
  -> dense embedding
  -> BM25 sparse embedding
  -> Qdrant dense prefetch + sparse prefetch
  -> RRF fusion
  -> optional cross-encoder rerank
  -> top-k context
```

Dense vectors use the configured `RAG_EMBEDDING_MODEL`.
Sparse vectors use `Qdrant/bm25` through `fastembed`.

## Why Hybrid

Dense retrieval is strong for semantic questions:

- business flow meaning
- architecture rationale
- rule descriptions
- concepts expressed with different wording

BM25 sparse retrieval is strong for exact keywords:

- class names
- method names
- endpoint paths
- enum values
- field names
- file names
- rare project-specific terms

Hybrid retrieval combines both before optional reranking.

## RRF Fusion

Qdrant merges dense and sparse candidates with reciprocal rank fusion.

RRF uses rank positions rather than raw scores, which is useful because dense cosine scores and BM25 sparse scores are not directly comparable.

The default constant is:

```text
RAG_HYBRID_RRF_K=60
```

## Debugging

Use `--no-hybrid` to compare against dense-only retrieval:

```powershell
python .\rag\commands\search.py --lane code "PaymentSessionsController" --no-hybrid
python .\rag\commands\search.py --lane code "PaymentSessionsController"
```

MCP tools accept:

```text
use_hybrid=true|false
```

Use `use_hybrid=false` when debugging timeout or local resource pressure.

## Scores

Hybrid/RRF results expose:

- `hybrid_score`: Qdrant RRF score
- `rerank_score`: optional cross-encoder score after fusion
- `vector_score`: dense-only score, present when hybrid is disabled

Do not compare `hybrid_score` and `vector_score` as if they were the same scale.

## Cache

`fastembed` cache is routed through:

```text
FASTEMBED_CACHE_PATH
```

By default `setup_cache_env()` sets it to:

```text
CACHE_ROOT/fastembed
```

where `CACHE_ROOT` comes from `RAG_CACHE_ROOT` or defaults to `~/.cache/icebot-rag`.

## Guardrails

- Keep candidate limits capped.
- Keep MCP reranker disabled by default.
- Keep code lane candidate limits conservative because code chunks are numerous.
- Do not embed secrets or local-only config.
- Do not embed all migrations by default; migration history is noisy and should be opt-in.
- Code RAG does not replace `rg`; use `rg` for exact symbol, route, call graph, and usage verification.

## Fallback

If `fastembed`, ONNX runtime, or local resource usage causes problems:

```text
RAG_ENABLE_HYBRID=false
```

Then use dense-only named vector retrieval.
