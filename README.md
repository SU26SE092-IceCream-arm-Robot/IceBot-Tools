# IceBot-Tools

This repository contains personal/local tooling used while developing and researching the IceBot project.

It is not the official project harness. Project-facing demo, integration, simulator, or smoke-test automation should live in a future `IceBot-Harness` repository.

## Folder Map

| Folder | Purpose |
| --- | --- |
| `rag/` | Local RAG, MCP server, indexing, retrieval, and context routing. |
| `code-intelligence/` | Future symbol/reference/endpoint indexing and derived cache for coding-agent workflows. |
| `pdf/` | PDF extraction workflow for turning source PDFs into reviewed curated notes. |
| `docker/` | Local Docker Compose files for tooling services. |
| `scripts/` | Small helper scripts for local tooling workflows. |
| `infrastructure/` | Public-safe templates for local machine/runtime notes. |
| `data/` | Generated local data such as Qdrant storage. Ignored by git. |
| `.local/` | Private machine-specific notes. Ignored by git. |

## Read First

- RAG setup and usage: [rag/README.md](rag/README.md)
- Code intelligence direction: [code-intelligence/README.md](code-intelligence/README.md)
- PDF extraction workflow: [pdf/docs/PDF_WORKFLOW.md](pdf/docs/PDF_WORKFLOW.md)
- Helper scripts: [scripts/README.md](scripts/README.md)
- Local infrastructure note templates: [infrastructure/README.md](infrastructure/README.md)

## Boundaries

- Keep machine-specific notes in `.local/`.
- Keep generated data in `data/`.
- Keep raw PDF extracts in `data/pdf_extracts/`; review and curate notes before moving knowledge into `Vault`.
- Keep operational RAG instructions in `rag/`.
- Keep generated code-intelligence indexes and caches in `data/code_intelligence/`.
- Keep reusable project-facing harness code out of this repo until `IceBot-Harness` exists.
- Do not commit API keys, tokens, passwords, or provider credentials.
