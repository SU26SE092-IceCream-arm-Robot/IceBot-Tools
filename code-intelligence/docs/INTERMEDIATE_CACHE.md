# Intermediate Cache

## Purpose

Cache stable derived project facts so agents do not repeatedly rebuild the same context.

## Cache Candidates

- repo summary
- module map
- symbol index
- endpoint-to-handler map
- interface implementation map
- dependency graph
- RAG collection manifests
- file hash and last-indexed metadata

## Storage Direction

Generated cache files should live under:

```text
data/code_intelligence/
```

This folder should stay ignored by git.

## Rules

- Cache derived facts, not secrets.
- Cache can be deleted and rebuilt.
- Cache must never become source of truth.
- If cache conflicts with source code, source code wins.
- Prefer file hashes or timestamps so tools can skip unchanged files.

## Future Use

This cache can support:

- faster context assembly;
- semantic code index refresh;
- agent review checklists;
- graph-RAG experiments;
- endpoint and dependency visualization.

