# Context Routing Rules

This note defines how local IceBot RAG tooling should choose context sources.

## Default Routing

Use the smallest source that can answer correctly:

- Current project/backend truth: use RAG over official docs.
- Exact code/config lookup: use keyword search, `rg`, or filesystem tools.
- Runtime status: use SQL, API, logs, or service tools.
- External/current facts: use web/search tools.
- General programming knowledge: use the LLM directly.
- Personal preference or working style: use memory, not RAG.

## RAG Usage

RAG is for retrieving relevant project knowledge. It should not retrieve everything.

`commands/ask.py` is an explicit RAG command. Use it only after deciding that the question needs IceBot project knowledge.

Do not route every prompt through RAG.

Good RAG sources:

- architecture docs
- boundary/context docs
- API surface rules
- domain rules
- business/system flows
- accepted implementation rules

Poor RAG sources:

- live runtime data
- exact secret/config lookup
- general industry comparison
- new brainstorming with no project context
- RAG tooling setup/learning notes, unless debugging the RAG tool itself

## Vault Handling

Vault is useful but lower authority.

- Default retrieval excludes Vault by requiring `authority = official`.
- Use `--include-vault` only when draft reasoning or history is explicitly useful.
- Treat `rejected`, `raw`, `future`, and `learning` notes as context, not truth.
- Do not recommend rejected designs as current direction.

## Principle

Wrong context is worse than missing context.

If the right source is unclear, prefer no retrieved context and state the uncertainty instead of mixing official docs with stale or rejected notes.

Score thresholds only answer this question:

```text
The prompt has already been routed into RAG.
Are the retrieved chunks relevant enough to use?
```

They do not answer this question:

```text
Should this prompt use RAG in the first place?
```

That decision belongs to context routing.

## Reranker Runtime Note

The local CLI commands load models on each run because every command starts a new Python process.

This is acceptable for local inspection, but not ideal for always-on workflows.

If RAG becomes an MCP server, API, daemon, or long-running assistant:

- keep embedding and reranker models loaded once
- reuse them across requests
- avoid treating CLI startup time as representative of long-running runtime cost

For quick debugging, use:

```powershell
--no-rerank
```
