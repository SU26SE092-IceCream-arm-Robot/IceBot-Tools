# IceBot Code Intelligence

This module provides a SQLite-backed structural code index for C# source code, acting as a foundation for code exploration, intent-based routing, and semantic search integration.

Unlike semantic RAG which relies on vector similarity, Code Intelligence processes the repository structurally: building symbol tables, endpoint mappings, handler relationships, and constructor-injected dependencies.

---

## Architecture Overview

```text
               +----------------------------------+
               |           User Query             |
               +----------------+-----------------+
                                |
                                v
               +----------------------------------+
               |        RAG Router Classifier     |
               |       (codeintel/router_hints.py)|
               +-------+------------------+-------+
                       |                  |
           (If matches symbol/verb)  (Otherwise)
                       |                  |
                       v                  v
        +--------------+-----+      +-----+--------------+
        | SQLite Code Index  |      | Qdrant Semantic RAG|
        |  (Exact Search)    |      | (Vector Retrieval) |
        +--------------------+      +--------------------+
```

- **SQLite Code Index**: Structural database mapping file hashes, classes, interfaces, methods, HTTP API routes, GraphQL queries/mutations, and CQRS Command/Query handlers. Used for exact lookups.
- **RAG / Vector Database**: Semantic retrieval used for open-ended, concept-based queries (implemented under `rag/`).
- **Router hints**: Intercepts queries to determine if they contain exact symbol names or API/handler terms. If yes, it routes them to exact SQLite queries first.

---

## Configuration

To customize target source paths, copy `sources.code-intelligence.example.json` to `sources.code-intelligence.local.json` and adjust the paths:

```powershell
cp .\code-intelligence\sources.code-intelligence.example.json .\code-intelligence\sources.code-intelligence.local.json
```

By default, the indexer walks:
- `IceBot-Backend` source root (`../IceBot-Backend`)
- Filters `.cs` files in `src/` and `.md` files in `docs/`
- Ignores build outputs (`bin/`, `obj/`), migrations, and designer code.

---

## CLI Commands

### 1. Indexing Code
Walks the workspace, hashes files, skips unchanged files, cleans deleted files, and parses structures:

```powershell
# Standard incremental indexing run
python .\code-intelligence\commands\index_code.py

# Force rebuild the index (ignore cached hashes)
python .\code-intelligence\commands\index_code.py --rebuild

# Index a specific repository key
python .\code-intelligence\commands\index_code.py --source icebot-backend

# Dry run (checks files and prints summary without writing to SQLite)
python .\code-intelligence\commands\index_code.py --dry-run
```

### 2. Symbol Lookup
Searches for classes, interfaces, records, structs, methods, or enums:

```powershell
# Search for a store implementation
python .\code-intelligence\commands\lookup_symbol.py OrderStore

# Search for a controller class
python .\code-intelligence\commands\lookup_symbol.py OrdersController
```

### 3. Endpoint Lookup
Searches for REST API endpoints by route, controller, or action name:

```powershell
# Search by API path
python .\code-intelligence\commands\lookup_endpoint.py "/api/v1/orders"

# Search by controller/action substring
python .\code-intelligence\commands\lookup_endpoint.py payment-sessions
```

### 4. CQRS Handler Lookup
Locates query or command handlers, identifying their request/result models, store dependencies, and triggering controllers or GraphQL queries:

```powershell
# Look up a command handler
python .\code-intelligence\commands\lookup_handler.py PlaceOrder

# Look up handlers in a specific bounded context (e.g. Orders context)
python .\code-intelligence\commands\lookup_handler.py PlaceOrder --context Orders
```

### 5. Verify Indexing Coverage
Performs a structural coverage audit comparing index entries against actual `.cs` files on disk:

```powershell
python .\code-intelligence\commands\verify_coverage.py
```

### 6. Debug Index Export
Exports index tables to JSON documents for quick inspection:

```powershell
python .\code-intelligence\commands\export_index.py
```
Outputs are written to `data/code_intelligence/exports/`.

---

## Shared Database Schema

The index is written to `data/code_intelligence/icebot_code_index.sqlite` and consists of 8 tables:
1. `indexed_files`: Tracks file paths, hashes, languages, and indexing times.
2. `symbols`: Lists declarations of classes, interfaces, structs, enums, records, and methods.
3. `endpoints`: Composed REST routes with HTTP methods, API versions, action routes, and auth policies.
4. `graphql_fields`: HotChocolate GraphQL queries/mutations with resolver bindings and auth rules.
5. `handlers`: CQRS command/query handlers mapped to request/result types.
6. `stores`: Paired interface stores and their implementations.
7. `relationships`: Graph edges showing class inheritance, constructor parameter injection, DI registration, and handler usage.
8. `index_runs`: Execution logs of indexing runs.
