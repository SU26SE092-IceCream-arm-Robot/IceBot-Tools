# IceBot Code Intelligence

This folder is a placeholder for future coding-agent support tools that inspect source code structurally.

It is separate from `rag/` because code intelligence should not depend only on vector search. It should use symbols, references, handlers, interfaces, dependencies, and cached repo maps.

## Planned Parts

- [Semantic Code Index](docs/SEMANTIC_CODE_INDEX.md)
- [Intermediate Cache](docs/INTERMEDIATE_CACHE.md)

## Boundary

- This folder supports agent/tooling workflows.
- It is not backend source of truth.
- It should not replace compiler checks, `rg`, or direct code review.
- Generated indexes and caches should live under `data/` and stay ignored by git.

