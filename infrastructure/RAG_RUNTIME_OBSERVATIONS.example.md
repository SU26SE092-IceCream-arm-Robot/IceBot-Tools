# RAG Runtime Observations

Status: local-only template

This template records observed local RAG performance on a developer machine.
Copy it to `IceBot-Tools/.local/RAG_RUNTIME_OBSERVATIONS.md` before filling in real observations.

It is not a source of truth for project architecture or RAG configuration.

Machine profile: `IceBot-Tools/.local/MACHINE_PROFILE.md`

## YYYY-MM-DD - Observation Title

- Workload:
- Imported chunks:
- Embedding model:
- Reranker model:
- Observed CPU:
- Observed RAM:
- Observed GPU/VRAM:
- Duration:
- Result:
- Follow-up idea:

## Example Topics To Track

- ingest chunk count and duration
- embedding model cold-start cost
- reranker model cold-start cost
- MCP timeout behavior with reranker enabled
- MCP behavior with reranker disabled
- CPU/RAM/GPU pressure during local runs
