# Machine Profile

Status: local-only template

This template records the local machine profile used to run project tooling.
Copy it to `IceBot-Tools/.local/MACHINE_PROFILE.md` before filling in real local values.

It is not project architecture truth and should not be treated as a long-lived RAG knowledge source.

## Machine

- CPU:
- RAM:
- GPU:
- VRAM:
- OS:
- Docker:
- Python:

## Local Runtime Paths

- Workspace:
- Backend repo:
- IceBot-Tools repo:
- Vault repo:
- Model/cache root:
- Qdrant storage:

## RAG Runtime

- RAG env file: `IceBot-Tools/rag/.env`
- RAG env template: `IceBot-Tools/rag/.env.example`
- RAG usage guide: `IceBot-Tools/rag/docs/SETUP.md`
- RAG runtime constants: `IceBot-Tools/rag/raglib/config.py`
- Optional cache override: `RAG_CACHE_ROOT`

Do not duplicate model names, collection names, or Qdrant endpoint details here.
Those values should be read from the RAG setup docs and config code.

## Expected Usage

Use this machine profile when deciding local tooling defaults, such as:

- whether local reranking is acceptable
- where model cache should be stored
- where generated vector database files should live
- whether a local Docker service is expected

Do not use this file to decide domain, API, database, or architecture rules.

## Local Constraints And Notes

- RAM constraints:
- Model load observations:
- Docker/runtime constraints:
- Known bottlenecks:

Runtime observations can be tracked in `IceBot-Tools/.local/RAG_RUNTIME_OBSERVATIONS.md`.

## Do Not Store Here

- API keys
- passwords
- database credentials
- payment provider secrets
- Firebase service account content
- private tokens
