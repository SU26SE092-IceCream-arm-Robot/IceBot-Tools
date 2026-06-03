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

Metadata construction lives in `raglib/source_metadata.py`.

Every ingested chunk should include:

- `file_id`
- `file_hash`
- `source`
- `source_path`
- `source_type`
- `source_group`
- `doc_type`
- `authority`
- `source_of_truth`
- `status`
- `is_overview`
- `chunk_index`
- `section_index`
- `section_path`
- `text`

## Excluded Sources

Some project-related notes are intentionally not embedded because they are about operating the RAG tool itself, not IceBot product/backend knowledge.

Currently excluded:

- `Vault/Learning/AGENT_HARNESS_LEARNING_NOTES.md`
- `Vault/Learning/RAG_LEARNING_NOTES.md`

## Payload Indexes

`commands/ingest.py` creates Qdrant payload indexes for frequently filtered fields:

| Field | Schema | Reason |
| --- | --- | --- |
| `authority` | keyword | default official-only retrieval |
| `status` | keyword | current/draft/raw/future/rejected filtering |
| `source_type` | keyword | backend-doc/project-doc/vault filtering |
| `source_group` | keyword | broad docs/vault/code/logs filtering |
| `doc_type` | keyword | api/flow/contract/architecture/domain filtering |
| `source` | keyword | filename filtering if needed |
| `file_id` | keyword | incremental re-index and orphan cleanup |
| `file_hash` | keyword | unchanged-file skip checks |
| `source_of_truth` | bool | distinguish accepted sources from advisory notes |
| `is_overview` | bool | allow specific retrieval to skip generic overview chunks |
| `source_path` | text | `--path-contains` matching |

## Markdown Chunking

Chunking logic lives in `raglib/markdown_chunking.py`.

Markdown files are split in two stages:

1. split by Markdown headers (`#` to `####`) to preserve section context
2. split long sections into smaller chunks with recursive character splitting

Empty or Markdown-noise-only chunks are skipped before embedding. `commands/ingest.py` prints the skipped empty chunk count in the ingest summary for debugging.

Chunk size and overlap are configurable through:

- `RAG_CHUNK_SIZE`
- `RAG_CHUNK_OVERLAP`

Defaults are `800` and `120`, preserving the current behavior. Changing these values changes chunk boundaries and point ids, so re-run ingest after changing them.

## Incremental Indexing

- Do not run ingest automatically after documentation-only edits unless the user explicitly asks for ingest. Ingest mutates the local vector database and can be slow on lower-memory machines.
- After metadata schema changes, old chunks will not have the new payload fields until ingest is run manually.
- After doc changes, normally provide this manual command instead:

```powershell
python .\rag\commands\ingest.py
```

- `commands/ingest.py` creates the collection when missing and updates indexed chunks per source file.
- Collection version metadata is written and validated through `raglib/collection_manifest.py`.
- `commands/ingest.py` skips files whose current `file_hash` already exists in Qdrant.
- Vectors are upserted in batches to avoid keeping the entire ingest result in memory.
- Changed files are read, chunked, and embedded successfully before old chunks for that file are deleted.
- Existing chunks for a source file are deleted only after replacement points are staged, preventing stale chunks when content shrinks or changes.
- Chunks for files no longer present in the configured source folders are removed as orphaned file points.
- If no source files are found, ingest aborts before orphan cleanup to avoid deleting the collection because of a bad path configuration.
- Ingest writes console output and `ingest.log` under `IceBot-Tools/logs/rag` by default. Override with `RAG_LOG_DIR`.
- Ingest logs use size-based rotation, not time-based retention. Defaults: 10 MB per file and 10 backups, for about 110 MB total per log stream.
- Routine ingest INFO logs are file-only by default. Set `RAG_LOG_CONSOLE=true` to show INFO logs in the terminal while debugging.

## Script Alignment

`commands/ingest.py`, `commands/context.py`, `commands/search.py`, and `commands/ask.py` must use the same embedding model:

```text
Qwen/Qwen3-Embedding-0.6B
```

Changing the embedding model requires a new collection version and full re-ingest because vector dimensions and embedding spaces may change.
