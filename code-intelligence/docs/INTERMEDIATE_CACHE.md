# Intermediate Cache

## Purpose

Cache stable derived project facts so agents do not repeatedly rebuild the same context.

In V1, the intermediate cache is the SQLite-backed structural code index:

```text
data/code_intelligence/icebot_code_index.sqlite
```

This is generated state. It is useful for exact lookup, router decisions, and compact context assembly, but it is not project source of truth.

## Current V1 Contents

The SQLite cache currently stores:

- indexed file inventory;
- file hash and last-indexed metadata;
- C# symbols: classes, interfaces, records, structs, enums, and methods;
- REST endpoint mappings;
- endpoint-to-handler mappings;
- GraphQL resolver-to-handler mappings;
- CQRS command/query handlers;
- store interface-to-implementation mappings;
- constructor-injected dependency relationships;
- DI registration relationships;
- indexing run history.

## Storage Boundary

Generated cache files should live under:

```text
data/code_intelligence/
```

This folder should stay ignored by git.

Debug exports may be written under:

```text
data/code_intelligence/exports/
```

Exports are inspection artifacts only. They should not be treated as durable documentation.

## Rules

- Cache derived facts, not secrets.
- Cache can be deleted and rebuilt.
- Cache must never become source of truth.
- If cache conflicts with source code, source code wins.
- Use file hashes so tools can skip unchanged files.
- Keep generated cache outside committed source and docs.
- Use code intelligence before semantic code RAG for exact symbols, endpoints, handlers, and store mappings.

## Rebuild And Verification

Rebuild the cache manually when source structure changes:

```powershell
python .\code-intelligence\commands\index_code.py
```

Force a full rebuild when scanner logic changes:

```powershell
python .\code-intelligence\commands\index_code.py --rebuild
```

Check structural coverage:

```powershell
python .\code-intelligence\commands\verify_coverage.py
```

Do not auto-run indexing from unrelated workflows. Let the user decide when to refresh generated state.

## Future Extensions

This cache can support:

- repo/module summaries;
- write-operation indexes;
- dependency and call-chain reports;
- agent review checklists;
- graph-RAG experiments;
- endpoint and dependency visualization;
- semantic code index refresh.
