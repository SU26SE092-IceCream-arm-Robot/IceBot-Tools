# Semantic Code Index

## Purpose

Build a structural index for source code so coding agents can answer implementation questions without relying only on vector search.

## Useful Indexes

- classes
- methods
- interfaces
- interface implementations
- controllers
- command/query handlers
- stores/repositories
- endpoint-to-handler mapping
- write operations for important fields
- references and call chains

## Example Questions

```text
Which handler owns this endpoint?
Where is OrderStatus updated?
Which class implements this interface?
What code writes ProviderOrderCode?
```

## Initial Direction

Start simple:

1. Parse file paths and names.
2. Extract C# class/interface/enum names.
3. Extract controller routes and action names.
4. Extract handler class names.
5. Build endpoint-to-handler and interface-to-implementation maps where obvious.

Use `rg` and compiler-friendly source inspection first. Add deeper parsing later only when needed.

## Non-Goals For Now

- no full static analyzer platform yet;
- no graph database yet;
- no automatic refactor engine;
- no replacement for build/tests;
- no ingestion into project docs RAG by default.

