# AGENTS.md

Minimal workflow for agents using `IceBot-Tools`.

Tools exist to reduce context load, not create more context to read.

## Default Workflow

1. Identify what the user needs.
2. Choose the smallest useful tool.
3. Run the tool.
4. Use only the returned evidence.
5. Read tool docs only when editing the tool, debugging the tool, or answering a question about the tool itself.

Do not read `README.md`, `docs/TOOLING.md`, or per-tool docs just to use a tool when the command name or MCP description is enough.

## Tool Choice

| Need | Use |
| --- | --- |
| Architecture, business rules, contracts, docs context | `retrieve_icebot_docs` |
| Open-ended implementation context | `retrieve_icebot_code` |
| Exact symbol/class/interface lookup | `lookup_icebot_symbol` |
| Exact REST endpoint lookup | `lookup_icebot_endpoint` |
| Exact CQRS handler lookup | `lookup_icebot_handler` |
| Docs link/stale-reference verification | `check_icebot_docs` |
| One-shot capped log diagnostics | `analyze_icebot_logs` |
| Code index health | `verify_icebot_code_index` |
| Final backend readiness check | `check_icebot_backend` |

Prefer exact lookup tools before semantic retrieval when the query contains a concrete symbol, endpoint, handler, or file name.

## Tool Priority

Use focused tools first, and use wrapper tools last.

1. Use exact lookup tools for concrete symbols, endpoints, handlers, and file names.
2. Use RAG only when exact lookup is not enough or the question needs meaning, rules, or background.
3. Use `check_icebot_docs`, `verify_icebot_code_index`, or `analyze_icebot_logs` when checking one specific concern.
4. Use `check_icebot_backend` only as the final backend readiness check after a meaningful backend task.

Do not run `check_icebot_backend` at the start of a task, for design discussion, or when a narrower tool answers the question.

`check_icebot_backend` intentionally wraps existing checks. It is not a new source of truth and agents should not read its implementation unless changing or debugging the preflight tool itself.

## When To Read Docs

Read docs only for these cases:

- user asks how a tool works;
- changing tool code or config;
- debugging a failing tool;
- adding a new tool;
- command/MCP description is not enough to choose safely.

Then read the smallest relevant doc:

- RAG: `rag/docs/SETUP.md`, `rag/docs/INDEXING.md`, or `rag/docs/RETRIEVAL.md`
- Code Intelligence: `code-intelligence/docs/USAGE.md`
- Docs Ops: `docs-ops/docs/USAGE.md`
- Log Analyzer: `log-analyzer/docs/USAGE.md`
- PDF workflow: `pdf/docs/PDF_WORKFLOW.md`

## MCP Output Rule

MCP tools should be quiet on success and verbose on failure.

- Success: compact status and one-line summary.
- Failure: structured, actionable failures with a maximum count.

Do not dump successful check output into agent context.

## Safety

- Do not run RAG ingest unless explicitly requested.
- Do not commit generated data, logs, local cache, secrets, credentials, or private machine notes.
- Generated data belongs under `data/`; logs belong under `logs/`; private local notes belong under `.local/`.

## Verification Shortcuts

Automation triggers:

- Backend code/API/domain changed -> `check_icebot_backend` at the end.
- Docs moved/split/deleted -> `check_icebot_docs`.
- Handler/controller/store moved or renamed -> `verify_icebot_code_index`.
- Runtime/log issue -> `analyze_icebot_logs`.

Docs-only change:

```powershell
python .\docs-ops\commands\check_docs.py
```

Python tooling change:

```powershell
python -m compileall -q .\toolcore .\mcp .\rag .\code-intelligence .\docs-ops .\log-analyzer
```

Code Intelligence scanner change:

```powershell
python .\code-intelligence\commands\index_code.py --dry-run
python .\code-intelligence\commands\verify_coverage.py
```

Final backend preflight:

```powershell
python .\backend-preflight\commands\check_backend.py
```

Use this after backend code/API/domain changes, not for ordinary explanation or design-review questions.
