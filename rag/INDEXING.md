# RAG Indexing

This file documents how IceBot project knowledge is ingested into Qdrant.

## Source Configuration

`commands/ingest.py` loads source folders/files from:

1. `rag/sources.local.json` when present
2. `rag/sources.example.json` otherwise

`sources.local.json` is ignored by git and should be used for per-machine paths. Relative paths are resolved from the `IceBot-Tools` root.

Each source entry contains:

- `path`
- `source_type`
- `authority`
- `status`
- `required`

Optional missing sources are skipped. Missing required sources abort ingest before indexing or orphan cleanup. If no Markdown files are found from the configured sources, ingest aborts before orphan cleanup to avoid deleting an existing collection because of a bad local path configuration.

## Collection Versioning

The active Qdrant collection is versioned:

```text
icebot_project_knowledge_v1
```

`icebot_project_knowledge` is the logical base name. Bump `RAG_COLLECTION_VERSION`
when changing embedding model or embedding dimension, then re-ingest the source docs
into the new collection version.

`commands/ingest.py` writes a generated manifest under `IceBot-Tools/data/rag_collections`
with the collection version, embedding model, embedding dimension, and creation time.
The manifest is local generated state and should not be committed.

## Metadata Rules

Every ingested chunk should include:

- `file_id`
- `file_hash`
- `source`
- `source_path`
- `source_type`
- `authority`
- `status`
- `chunk_index`
- `section_index`
- `section_path`
- `text`

## Excluded Sources

Some project-related notes are intentionally not embedded because they are about operating the RAG tool itself, not IceBot product/backend knowledge.

Currently excluded:

- `Vault/Learning/RAG_LEARNING_NOTES.md`

## Payload Indexes

`commands/ingest.py` creates Qdrant payload indexes for frequently filtered fields:

| Field | Schema | Reason |
| --- | --- | --- |
| `authority` | keyword | default official-only retrieval |
| `status` | keyword | current/draft/raw/future/rejected filtering |
| `source_type` | keyword | backend-doc/project-doc/vault filtering |
| `source` | keyword | filename filtering if needed |
| `file_id` | keyword | incremental re-index and orphan cleanup |
| `file_hash` | keyword | unchanged-file skip checks |
| `source_path` | text | `--path-contains` matching |

## Markdown Chunking

Markdown files are split in two stages:

1. split by Markdown headers (`#` to `####`) to preserve section context
2. split long sections into smaller chunks with recursive character splitting

## Incremental Indexing

- `commands/ingest.py` creates the collection when missing and updates indexed chunks per source file.
- `commands/ingest.py` skips files whose current `file_hash` already exists in Qdrant.
- Vectors are upserted in batches to avoid keeping the entire ingest result in memory.
- Changed files are read, chunked, and embedded successfully before old chunks for that file are deleted.
- Existing chunks for a source file are deleted only after replacement points are staged, preventing stale chunks when content shrinks or changes.
- Chunks for files no longer present in the configured source folders are removed as orphaned file points.
- If no source files are found, ingest aborts before orphan cleanup to avoid deleting the collection because of a bad path configuration.

## Script Alignment

`commands/ingest.py`, `commands/context.py`, `commands/search.py`, and `commands/ask.py` must use the same embedding model:

```text
Qwen/Qwen3-Embedding-0.6B
```

Changing the embedding model requires a new collection version and full re-ingest because vector dimensions and embedding spaces may change.
