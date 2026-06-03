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
- Snapshot log: `IceBot-Tools/logs/system/system_snapshot.log`

## Example Topics To Track

- ingest chunk count and duration
- embedding model cold-start cost
- reranker model cold-start cost
- MCP timeout behavior with reranker enabled
- MCP behavior with reranker disabled
- CPU/RAM/GPU pressure during local runs

## Measuring Local Runtime

Run from `IceBot-Tools`:

```powershell
.\scripts\system_snapshot.ps1 -Label "before test"
# Run or trigger the workload.
.\scripts\system_snapshot.ps1 -Label "after test"
```

For MCP reranker timeout debugging, take snapshots before the MCP request and immediately after the timeout or while the process is still loading.
