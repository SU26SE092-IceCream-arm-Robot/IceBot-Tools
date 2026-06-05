# Collection Schema

This file documents Qdrant collection naming, vector schema, manifests, and payload indexes for IceBot-Tools RAG.

## Collection Versioning

The active Qdrant collections are versioned:

```text
icebot_docs_knowledge_v1
icebot_code_knowledge_v1
```

`icebot_docs_knowledge` and `icebot_code_knowledge` are logical base names.
Bump `RAG_DOCS_COLLECTION_VERSION` or `RAG_CODE_COLLECTION_VERSION` when changing embedding model, embedding dimension, vector schema, sparse model, or chunking strategy for that lane.

## Vector Schema

Collection `v1` uses Qdrant named vectors:

```text
dense  -> Qwen/Qwen3-Embedding-0.6B cosine vector
sparse -> Qdrant/bm25 sparse vector, when RAG_ENABLE_HYBRID=true
```

Hybrid retrieval requires this named vector schema. Because `v1` has not been used as an active production collection yet, `v1` remains the initial collection version for the current schema.

Set `RAG_ENABLE_HYBRID=false` only when you need a named dense-only collection for debugging or dependency troubleshooting.

## Re-ingest After Schema Setup

Re-ingest both lanes manually after vector schema setup or collection version changes:

```powershell
python .\rag\commands\ingest_docs.py
python .\rag\commands\ingest_code.py
```

Do not run ingest automatically after docs-only edits or schema discussion.

## Collection Manifest

Ingest commands write generated manifests under:

```text
IceBot-Tools/data/rag_collections
```

The manifest records:

- collection lane
- collection base name
- collection name
- collection version
- vector schema
- embedding model
- embedding dimension
- hybrid enabled flag
- sparse model
- schema version
- creation time

The manifest is local generated state and should not be committed.

`raglib/collection_manifest.py` validates the manifest before ingesting into an existing collection. If collection metadata does not match the current config, ingest aborts instead of mixing schemas.

## Payload Indexes

Ingest commands create Qdrant payload indexes for frequently filtered fields:

| Field | Schema | Reason |
| --- | --- | --- |
| `authority` | keyword | default official-only retrieval |
| `status` | keyword | current/draft/raw/future/rejected filtering |
| `source_type` | keyword | backend-doc/project-doc/vault filtering |
| `source_group` | keyword | broad docs/vault/code/logs filtering |
| `doc_type` | keyword | api/flow/contract/architecture/domain filtering |
| `language` | keyword | code language filtering |
| `namespace` | keyword | C# namespace filtering |
| `symbol_kind` | keyword | class/interface/method-style filtering |
| `symbol_name` | keyword | symbol lookup and future Graph-RAG preparation |
| `source` | keyword | filename filtering if needed |
| `file_id` | keyword | incremental re-index and orphan cleanup |
| `file_hash` | keyword | unchanged-file skip checks |
| `is_overview` | bool | allow specific retrieval to skip generic overview chunks |
| `source_path` | text | `--path-contains` matching |

## Script Alignment

`commands/ingest_docs.py`, `commands/ingest_code.py`, `commands/context.py`, `commands/search.py`, and `commands/ask.py` must use the same embedding model:

```text
Qwen/Qwen3-Embedding-0.6B
```

Changing the embedding model requires a new collection version and full re-ingest because vector dimensions and embedding spaces may change.

Changing `RAG_ENABLE_HYBRID` or `RAG_SPARSE_MODEL` also requires a new collection version and full re-ingest because the Qdrant vector schema or sparse vector space changes.
