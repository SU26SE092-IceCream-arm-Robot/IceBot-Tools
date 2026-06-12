# Code Intelligence Usage

Code Intelligence is the exact structural lookup lane for IceBot source code.

Use it before semantic code RAG when the question names a symbol, route, handler, store, controller, or structural relationship.

## Configuration

To customize target source paths, copy the example source config:

```powershell
Copy-Item .\code-intelligence\sources.code-intelligence.example.json .\code-intelligence\sources.code-intelligence.local.json
```

By default, the indexer targets the sibling `IceBot-Backend` repository and scans backend source/docs according to the configured include and exclude rules.

## Index Code

```powershell
python .\code-intelligence\commands\index_code.py
python .\code-intelligence\commands\index_code.py --rebuild
python .\code-intelligence\commands\index_code.py --source icebot-backend
python .\code-intelligence\commands\index_code.py --dry-run
```

## Lookup Symbols

```powershell
python .\code-intelligence\commands\lookup_symbol.py OrderStore
python .\code-intelligence\commands\lookup_symbol.py OrdersController
```

## Lookup Endpoints

```powershell
python .\code-intelligence\commands\lookup_endpoint.py "/api/v1/orders"
python .\code-intelligence\commands\lookup_endpoint.py payment-sessions
```

## Lookup CQRS Handlers

```powershell
python .\code-intelligence\commands\lookup_handler.py PlaceOrder
python .\code-intelligence\commands\lookup_handler.py PlaceOrder --context Orders
```

## Verify Coverage

```powershell
python .\code-intelligence\commands\verify_coverage.py
```

Use this after scanner changes or large backend refactors.

## Export For Debugging

```powershell
python .\code-intelligence\commands\export_index.py
```

Exports are written under:

```text
data/code_intelligence/exports/
```

## SQLite Schema

The generated index lives at:

```text
data/code_intelligence/icebot_code_index.sqlite
```

Main tables:

| Table | Purpose |
| --- | --- |
| `indexed_files` | File paths, hashes, languages, and indexing timestamps. |
| `symbols` | Classes, interfaces, structs, enums, records, and methods. |
| `endpoints` | REST routes, HTTP methods, API versions, actions, and auth policies. |
| `graphql_fields` | GraphQL fields/resolvers and auth rules. |
| `handlers` | CQRS command/query handlers and request/result types. |
| `stores` | Store interfaces and implementations. |
| `relationships` | Edges such as inheritance, constructor injection, DI registration, and handler usage. |
| `index_runs` | Indexing run summaries. |
