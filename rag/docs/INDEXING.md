# RAG Indexing

This file documents how IceBot project knowledge is ingested into Qdrant.

IceBot uses separate collections for docs and code:

- docs knowledge: architecture, contracts, rules, flows, accepted docs
- code knowledge: source code, classes, methods, mappings, configuration

## Source Configuration

`commands/ingest_docs.py` loads docs source folders/files from:

1. `rag/sources.docs.local.json` when present
2. `rag/sources.docs.example.json` otherwise

`commands/ingest_code.py` loads code source folders/files from:

1. `rag/sources.code.local.json` when present
2. `rag/sources.code.example.json` otherwise

Local source config files are ignored by git and should be used for per-machine paths. Relative paths are resolved from the `IceBot-Tools` root.

Each source entry contains:

- `path`
- `source_type`
- `authority`
- `status`
- `required`

Optional missing sources are skipped. Missing required sources abort ingest before indexing or orphan cleanup. If no Markdown files are found from the configured sources, ingest aborts before orphan cleanup to avoid deleting an existing collection because of a bad local path configuration.

## Collection Versioning

Collection naming, named vector schema, manifests, and payload indexes are documented in [COLLECTION_SCHEMA.md](COLLECTION_SCHEMA.md).

## Vector Schema

The current collections use Qdrant named vectors: `dense` and optional `sparse`.

See [COLLECTION_SCHEMA.md](COLLECTION_SCHEMA.md) for schema details and re-ingest requirements.

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
- `status`
- `is_overview`
- `chunk_index`
- `section_index`
- `section_path`
- `text`

Code chunks may also include:

- `language`
- `namespace`
- `symbol_kind`
- `symbol_name`
- `start_line`
- `end_line`

## Excluded Sources

Some project-related notes are intentionally not embedded because they are about operating the RAG tool itself, not IceBot product/backend knowledge.

Currently excluded by prefix:

- `Vault/Learning/Personal/`
- `Vault/Learning/Tooling/`
- `Vault/Research/Papers/`

`Vault/Research/Papers/` contains intermediate paper-digestion notes. They are summaries and possible implementation ideas, not applied learning or project truth, so they should not enter the long-term RAG database by default.

## Payload Indexes

Payload indexes are documented in [COLLECTION_SCHEMA.md](COLLECTION_SCHEMA.md).

## Docs Chunking

Chunking logic lives in `raglib/markdown_chunking.py`.

Markdown files are split in two stages:

1. split by Markdown headers (`#` to `####`) to preserve section context
2. split long sections into smaller chunks with recursive character splitting

Empty or Markdown-noise-only chunks are skipped before embedding. `commands/ingest_docs.py` prints the skipped empty chunk count in the ingest summary for debugging.

## Code Chunking

Chunking logic lives in `raglib/code_chunking.py`.

The current code chunker is intentionally simple:

- includes `.cs`, `.csproj`, `.json`, `.props`, and `.targets`
- excludes noisy folders such as `bin`, `obj`, `.git`, `.vs`, `node_modules`, and `Migrations`
- captures rough C# metadata such as namespace, symbol name, symbol kind, and line range

This prepares for Code RAG and future Graph-RAG without forcing a complex parser upfront.

Chunk size and overlap are configurable through:

- `RAG_CHUNK_SIZE`
- `RAG_CHUNK_OVERLAP`

Defaults are `800` and `120`, preserving the current behavior. Changing these values changes chunk boundaries and point ids, so re-run ingest after changing them.

## Incremental Indexing

- Do not run ingest automatically after documentation-only edits unless the user explicitly asks for ingest. Ingest mutates the local vector database and can be slow on lower-memory machines.
- After metadata schema changes, old chunks will not have the new payload fields until ingest is run manually.
- After doc changes, normally provide this manual command instead:

```powershell
python .\rag\commands\ingest_docs.py
python .\rag\commands\ingest_code.py
```

- Ingest commands create the collection when missing and update indexed chunks per source file.
- Collection version metadata is written and validated through `raglib/collection_manifest.py`.
- Ingest commands skip files whose current `file_hash` already exists in Qdrant.
- Vectors are upserted in batches to avoid keeping the entire ingest result in memory.
- Changed files are read, chunked, and embedded successfully before old chunks for that file are deleted.
- Existing chunks for a source file are deleted only after replacement points are staged, preventing stale chunks when content shrinks or changes.
- Chunks for files no longer present in the configured source folders are removed as orphaned file points.
- If no source files are found, ingest aborts before orphan cleanup to avoid deleting the collection because of a bad path configuration.
- Ingest writes console output and `ingest.log` under `IceBot-Tools/logs/rag` by default. Override with `RAG_LOG_DIR`.
- Ingest logs use size-based rotation, not time-based retention. Defaults: 10 MB per file and 10 backups, for about 110 MB total per log stream.
- Routine ingest INFO logs are file-only by default. Set `RAG_LOG_CONSOLE=true` to show INFO logs in the terminal while debugging.

## Script Alignment

Embedding model and schema alignment rules are documented in [COLLECTION_SCHEMA.md](COLLECTION_SCHEMA.md).
