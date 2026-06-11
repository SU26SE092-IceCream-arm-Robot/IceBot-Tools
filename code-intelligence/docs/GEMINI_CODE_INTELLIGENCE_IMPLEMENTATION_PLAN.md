# Gemini Implementation Plan - Code Intelligence System V1

This plan is for implementing the first real version of IceBot-Tools code intelligence.

The goal is a stable foundation, not a throwaway prototype.

## Context

IceBot-Tools currently has:

- `rag/`: docs/code RAG, Qdrant retrieval, MCP tools.
- `code-intelligence/`: placeholder docs and folders.
- `log-analyzer/`, `pdf/`, `scripts/`: separate local tooling.

The user currently clones only:

```text
IceBot-Backend
```

Other repositories such as React web, Flutter mobile, and robot emulator may be added later. Do not assume they exist now.

## Final Direction

Implement:

```text
IceBot-Tools
|-- semantic code index
|-- intermediate caching
`-- better retrieval/router integration
```

Architectural decision:

```text
Code Intelligence = SQLite-backed structural index
RAG = Qdrant-backed semantic retrieval
Router = shared orchestration layer
Graph-RAG later = built from structural index tables, not a rewrite
```

Do not use JSON as the primary code-index storage. JSON exports are allowed only for debugging.

## Scope V1

Backend-only by default:

```text
../IceBot-Backend/src
../IceBot-Backend/docs
../IceBot-Backend/ARCHITECTURE.md
../IceBot-Backend/AGENTS.md
```

Multi-repository-ready by schema and config:

```text
repository_key = icebot-backend
project_key = WebAPI | Application | Domain | Infrastructure | docs
language = csharp | markdown
```

Do not index web/mobile/emulator repositories yet.

Do not index generated folders:

```text
bin/
obj/
.git/
.vs/
.idea/
logs/
data/
```

Do not index secrets/local files:

```text
.env
.local
*.user
appsettings.Development.json
```

EF migrations are opt-in later. Do not include all migrations by default in V1.

## Shared Code Organization

Defer creating a `shared/` package until V1.1 or later. In V1, keep all utilities inside `code-intelligence/codeintel/`. Extract to a shared package only when RAG actually imports the same logic.

When extraction happens later, only move code out of `rag/raglib` when both are true:

1. the logic is genuinely shared by RAG and code intelligence;
2. imports can be updated cleanly without changing behavior.

Good shared candidates for later extraction:

- workspace/tool root resolution;
- file hashing;
- source config loading;
- ignore/path filters;
- log setup conventions.

Do not move RAG-specific logic:

- Qdrant client;
- embedding model config;
- chunking;
- reranker;
- collection setup.

## Target Folder Structure

```text
code-intelligence/
|-- README.md
|-- commands/
|   |-- index_code.py
|   |-- lookup_symbol.py
|   |-- lookup_endpoint.py
|   |-- lookup_handler.py
|   |-- export_index.py
|   `-- verify_coverage.py
|-- codeintel/
|   |-- __init__.py
|   |-- config.py
|   |-- db.py
|   |-- schema.py
|   |-- source_loader.py
|   |-- csharp_scanner.py
|   |-- markdown_scanner.py
|   |-- indexer.py
|   |-- queries.py
|   |-- file_hashing.py
|   |-- ignore_rules.py
|   `-- router_hints.py
|-- sources.code-intelligence.example.json
|-- sources.code-intelligence.local.json   # ignored
`-- docs/
    |-- CODE_INTELLIGENCE_SYSTEM.md
    |-- SEMANTIC_CODE_INDEX.md
    |-- INTERMEDIATE_CACHE.md
    `-- GEMINI_CODE_INTELLIGENCE_IMPLEMENTATION_PLAN.md
```

Generated data:

```text
data/code_intelligence/
|-- icebot_code_index.sqlite
`-- exports/
```

Logs:

```text
logs/code-intelligence/
```

## SQLite Schema V1

Create SQLite tables with stable names.

### ID generation rules

```text
file_id  = sha256(repository_key + ":" + relative_path)   # stable across machines
symbol id, endpoint id, etc. = uuid4()                     # generated at insert time
```

### `project_key` inference

```text
project_key = first directory component under src/
  src/WebAPI/...         -> WebAPI
  src/Application/...    -> Application
  src/Domain/...         -> Domain
  src/Infrastructure/... -> Infrastructure
  docs/...               -> docs
  ARCHITECTURE.md        -> docs
  AGENTS.md              -> docs
```

### `bounded_context` inference

Infer from the second-level directory under the project:

```text
src/Application/Orders/...     -> Orders
src/Application/Payments/...   -> Payments
src/Domain/Identity/...        -> Identity
src/Infrastructure/Catalog/... -> Catalog
src/WebAPI/Controllers/Tenants/... -> Tenants
src/WebAPI/GraphQL/Orders/...  -> Orders
```

If the file is not inside a bounded-context directory (e.g. `DependencyInjection.cs` at project root), set `bounded_context` to null.

### `indexed_files`

Fields:

- `id` text primary key
- `repository_key` text not null
- `project_key` text
- `language` text not null
- `source_root` text not null
- `source_path` text not null
- `relative_path` text not null
- `file_id` text not null
- `file_hash` text not null
- `indexed_at` text not null
- `status` text not null

Indexes:

- unique `(repository_key, file_id)`
- index `file_hash`
- index `language`
- index `project_key`

### `symbols`

Fields:

- `id` text primary key
- `file_id` text not null
- `repository_key` text not null
- `project_key` text
- `bounded_context` text
- `language` text not null
- `kind` text not null
- `name` text not null
- `full_name` text
- `namespace` text
- `containing_type` text
- `signature` text
- `line_start` integer
- `line_end` integer

`signature` stores the single-line declaration for methods and handlers. Example:

```text
public async Task<IActionResult> PlaceOrder(PlaceOrderRequest request, string? idempotencyKey, CancellationToken cancellationToken)
```

Kinds:

```text
class
interface
enum
method
property
record
struct
controller
handler
store
graphql_query
graphql_mutation
```

Indexes:

- index `name`
- index `full_name`
- index `kind`
- index `bounded_context`
- index `(repository_key, project_key)`

### `endpoints`

Fields:

- `id` text primary key
- `repository_key` text not null
- `project_key` text
- `bounded_context` text
- `http_method` text
- `route` text not null
- `api_version` text
- `controller` text
- `action` text
- `auth_type` text
- `policy` text
- `handler_name` text
- `file_id` text not null
- `line_start` integer

`route` stores the composed full route from class-level `[Route]` + method-level `[HttpX]` template.

`auth_type` values:

```text
anonymous       # [AllowAnonymous]
policy          # [Authorize(Policy = "...")]
authenticated   # [Authorize] without policy
unknown         # no attribute found
```

Indexes:

- index `route`
- index `controller`
- index `policy`
- index `auth_type`
- index `bounded_context`

### `graphql_fields`

Fields:

- `id` text primary key
- `repository_key` text not null
- `bounded_context` text
- `field_type` text not null
- `field_name` text not null
- `resolver` text
- `auth_type` text
- `policy` text
- `handler_name` text
- `file_id` text not null
- `line_start` integer

`field_type` values:

```text
query
mutation
subscription
```

Detect `field_type` from `[ExtendObjectType("Query")]` or `[ExtendObjectType("Mutation")]` on the containing class.

Indexes:

- index `field_name`
- index `field_type`
- index `policy`
- index `bounded_context`

### `handlers`

Fields:

- `id` text primary key
- `repository_key` text not null
- `project_key` text
- `handler_name` text not null
- `handler_type` text
- `request_name` text
- `result_name` text
- `bounded_context` text
- `file_id` text not null
- `line_start` integer

Handler types:

```text
command
query
unknown
```

### `stores`

Fields:

- `id` text primary key
- `repository_key` text not null
- `interface_name` text
- `implementation_name` text
- `bounded_context` text
- `interface_file_id` text
- `implementation_file_id` text

### `relationships`

Fields:

- `id` text primary key
- `repository_key` text not null
- `from_kind` text not null
- `from_name` text not null
- `from_context` text
- `to_kind` text not null
- `to_name` text not null
- `to_context` text
- `relation_type` text not null
- `evidence_file_id` text
- `line_start` integer

Relation types:

```text
implements
injects
calls_handler
uses_store
maps_route_to_action
maps_graphql_to_handler
registers_di
```

V1.1 stretch relation:

```text
operates_on_entity
```

Do not block V1 on perfect handler-to-entity inference. Prefer accurate endpoint, handler, store, DI, and GraphQL extraction first.

### `index_runs`

Fields:

- `id` text primary key
- `started_at` text not null
- `finished_at` text
- `repository_key` text
- `files_scanned` integer
- `files_indexed` integer
- `files_skipped` integer
- `status` text not null
- `message` text

## Parser Strategy V1

Use Python in V1.

Do not add a .NET Roslyn project yet unless necessary. Keep the architecture ready for a Roslyn indexer later.

Use conservative regex/path scanning:

- class/interface/enum/record/struct declarations;
- namespace declarations;
- controller classes ending with `Controller`;
- `[Route(...)]`, `[HttpGet(...)]`, `[HttpPost(...)]`, `[HttpPut(...)]`, `[HttpDelete(...)]`, `[HttpPatch(...)]`;
- `[Authorize(Policy = "...")]`, `[Authorize]`, `[AllowAnonymous]`;
- `[ApiVersion("...")]`;
- handler classes ending with `CommandHandler` or `QueryHandler`;
- store interfaces beginning with `I` and ending with `Store`;
- store implementations ending with `Store`;
- DI registrations containing `AddScoped`, `AddTransient`, `AddSingleton`;
- HotChocolate GraphQL decorators `[ExtendObjectType("Query")]` and `[ExtendObjectType("Mutation")]`;
- GraphQL method-level `[Authorize(Policy = "...")]` and `[Service]` parameter injection.

### Route composition

Endpoint routes must be composed from class-level and method-level attributes:

```text
class:  [Route("api/v{version:apiVersion}/orders")]
method: [HttpPost("{orderId:guid}/cancel")]
-> full_route = "api/v{version:apiVersion}/orders/{orderId:guid}/cancel"
-> http_method = POST
```

If the method attribute has no template (e.g. `[HttpPost]`), the full route is the class-level route only.

### DI registration scanning

DI registrations are distributed across module files, not centralized in one file. Scan all `.cs` files for `AddScoped`, `AddTransient`, `AddSingleton`. Known registration files include:

```text
Infrastructure/DependencyInjection.cs           # central hub
Infrastructure/Orders/OrdersInfrastructureModule.cs
Infrastructure/Identity/IdentityInfrastructureRegistration.cs
Infrastructure/Tenants/TenantsInfrastructureRegistration.cs
Infrastructure/Payments/PaymentsInfrastructureModule.cs
Application/DependencyInjection.cs
Application/Tenants/TenantsApplicationRegistration.cs
Application/SalesCatalog/SalesCatalogModule.cs
... and other module registration files
```

Application-layer registration files register handler classes. Infrastructure-layer registration files register store implementations. Both must be scanned.

### HotChocolate GraphQL pattern

The backend uses HotChocolate with the following pattern:

```csharp
[ExtendObjectType("Query")]
public sealed class OrderQueries
{
    [Authorize(Policy = "orders.view")]
    public async Task<OrderOverviewResult> GetOrderOverview(
        ...,
        [Service] GetOrderOverviewQueryHandler handler,
        ...)
```

Extract:

- class with `[ExtendObjectType("Query")]` -> GraphQL query container;
- class with `[ExtendObjectType("Mutation")]` -> GraphQL mutation container;
- each public method inside -> a `graphql_fields` row;
- `[Service] XxxHandler handler` parameter -> `handler_name`;
- `[Authorize(Policy = "...")]` on the method -> `policy` and `auth_type`.

Be explicit in docs that V1 extraction is best-effort structural indexing, not compiler-grade semantic analysis.

## Commands

### `index_code.py`

Responsibilities:

- load `sources.code-intelligence.local.json` if present, else example;
- scan enabled source roots;
- apply ignore rules;
- compute file hashes;
- skip unchanged files;
- remove orphaned rows for deleted files;
- populate SQLite tables;
- write one `index_runs` row;
- print a stats summary.

Stats summary format:

```text
Index completed in 2.3s
  Files scanned: 527
  Files indexed: 412
  Files skipped: 115 (unchanged)
  Symbols: 1,247
  Endpoints: 48
  GraphQL fields: 12
  Handlers: 67
  Stores: 14
  Relationships: 183
```

Example:

```powershell
python .\code-intelligence\commands\index_code.py
```

Optional:

```powershell
python .\code-intelligence\commands\index_code.py --rebuild
python .\code-intelligence\commands\index_code.py --source icebot-backend
python .\code-intelligence\commands\index_code.py --dry-run
```

`--dry-run` scans and prints the stats summary without writing to SQLite. Useful for validating source config and ignore rules.

### `lookup_symbol.py`

Example:

```powershell
python .\code-intelligence\commands\lookup_symbol.py OrderStore
python .\code-intelligence\commands\lookup_symbol.py PlaceOrderCommandHandler
```

Output should include:

- name;
- kind;
- file path;
- line;
- project;
- related endpoint/handler/store where available.

### `lookup_endpoint.py`

Example:

```powershell
python .\code-intelligence\commands\lookup_endpoint.py "/api/v1/orders"
python .\code-intelligence\commands\lookup_endpoint.py "payment-sessions"
```

Output should include:

- method;
- route;
- controller;
- action;
- policy;
- handler hint if found;
- file path and line.

### `lookup_handler.py`

Example:

```powershell
python .\code-intelligence\commands\lookup_handler.py PlaceOrder
python .\code-intelligence\commands\lookup_handler.py --context Orders
```

Output should include:

- handler name;
- handler type (command/query);
- request and result names;
- bounded context;
- related endpoint or GraphQL field where available;
- related store dependencies;
- file path and line.

### `export_index.py`

Debug export only:

```powershell
python .\code-intelligence\commands\export_index.py
```

Writes:

```text
data/code_intelligence/exports/symbol_index.json
data/code_intelligence/exports/endpoint_map.json
data/code_intelligence/exports/relationships.json
```

### `verify_coverage.py`

Compare index contents against the actual filesystem to detect missed symbols:

```powershell
python .\code-intelligence\commands\verify_coverage.py
```

Checks:

- number of `*Controller.cs` files vs controller rows in `symbols`;
- number of `*Handler.cs` files vs handler rows in `handlers`;
- number of `I*Store.cs` files vs store rows in `stores`;
- number of `[Route]` attributes found by grep vs endpoint rows in `endpoints`;
- number of `[ExtendObjectType]` methods vs graphql_fields rows.

Output a coverage report with any missed items listed.

## Source Config

Create:

```text
code-intelligence/sources.code-intelligence.example.json
```

Example content:

```json
[
  {
    "repository_key": "icebot-backend",
    "display_name": "IceBot Backend",
    "path": "../IceBot-Backend",
    "enabled": true,
    "language": "mixed",
    "include": [
      "src/**/*.cs",
      "docs/**/*.md",
      "ARCHITECTURE.md",
      "AGENTS.md"
    ],
    "exclude": [
      "**/bin/**",
      "**/obj/**",
      "**/.git/**",
      "**/Migrations/**",
      "**/*.Designer.cs",
      "**/appsettings.Development.json"
    ]
  }
]
```

Add `code-intelligence/sources.code-intelligence.local.json` to `.gitignore`.

## Router Integration

Do not fully refactor existing RAG router in this task.

Add a small integration layer:

```text
code-intelligence/codeintel/router_hints.py
```

It should expose functions such as:

```python
classify_code_intent(query: str) -> dict
```

Example output:

```json
{
  "suggested_source": "code-index",
  "reason": "Query references endpoint/handler/interface style terms",
  "lookup_type": "endpoint"
}
```

V1 uses keyword/regex matching. When the SQLite index is available, `classify_code_intent` should also check whether a mentioned symbol actually exists in the index before routing. For example, if the query mentions `OrderStore`, verify that `OrderStore` exists in the `symbols` or `stores` table.

RAG/MCP integration can be done later after CLI tools are verified.

## Documentation Updates

Update:

- `README.md`
- `code-intelligence/README.md`
- `code-intelligence/docs/CODE_INTELLIGENCE_SYSTEM.md`
- `code-intelligence/docs/SEMANTIC_CODE_INDEX.md`
- `code-intelligence/docs/INTERMEDIATE_CACHE.md`
- `code-intelligence/docs/GEMINI_CODE_INTELLIGENCE_IMPLEMENTATION_PLAN.md` if implementation changes the final command/schema names.

Mention:

- backend-only default;
- multi-repository-ready schema/config;
- SQLite generated index;
- no Graph-RAG database yet;
- JSON exports are debug only;
- exact search/code index should be used before code RAG for structural questions.

## Gitignore Updates

Ensure ignored:

```text
data/code_intelligence/
logs/code-intelligence/
code-intelligence/sources.code-intelligence.local.json
```

## Verification

Compile check:

```powershell
python -m py_compile .\code-intelligence\commands\index_code.py `
  .\code-intelligence\commands\lookup_symbol.py `
  .\code-intelligence\commands\lookup_endpoint.py `
  .\code-intelligence\commands\lookup_handler.py `
  .\code-intelligence\commands\export_index.py `
  .\code-intelligence\commands\verify_coverage.py
```

Functional test:

```powershell
python .\code-intelligence\commands\index_code.py
python .\code-intelligence\commands\lookup_symbol.py OrdersController
python .\code-intelligence\commands\lookup_symbol.py PlaceOrderCommandHandler
python .\code-intelligence\commands\lookup_endpoint.py orders
python .\code-intelligence\commands\lookup_handler.py PlaceOrder
python .\code-intelligence\commands\lookup_handler.py --context Orders
python .\code-intelligence\commands\export_index.py
python .\code-intelligence\commands\verify_coverage.py
```

Expected:

- index command completes without crashing;
- SQLite database is created under `data/code_intelligence/`;
- repeated index run skips unchanged files;
- stats summary shows plausible counts (500+ files, 40+ endpoints, 60+ handlers);
- lookup commands return backend symbols/endpoints/handlers;
- `verify_coverage.py` reports 90%+ coverage for controllers, handlers, stores;
- bounded_context is populated for symbols inside context directories;
- endpoint routes are correctly composed from class + method attributes;
- auth_type correctly distinguishes anonymous kiosk endpoints from policy-protected management endpoints;
- generated data remains ignored by git;
- no RAG ingest is triggered;
- no backend code is changed.

## Guardrails

- Do not modify IceBot-Backend.
- Do not run backend migrations.
- Do not auto-ingest RAG.
- Do not add Graph-RAG storage yet.
- Do not add a server process.
- Do not require Docker.
- Do not commit generated SQLite/export/log files.
- Keep implementation public-safe: no machine-specific paths in docs or sample data.

## Completion Criteria

The task is complete when:

1. `code-intelligence` has working SQLite-backed indexing.
2. The default source config indexes `IceBot-Backend` only.
3. The schema contains repository/language/project fields for future repos.
4. Lookup commands work for symbols, endpoints, and handlers.
5. Generated cache/index files are ignored.
6. Docs clearly describe the boundary between RAG, code intelligence, cache, router, and future Graph-RAG.
7. No backend source files are changed.
