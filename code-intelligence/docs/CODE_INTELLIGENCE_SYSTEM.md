# Code Intelligence System

This document describes the planned IceBot-Tools code-intelligence system.

It is a tooling roadmap, not project source of truth.

## Goal

Improve coding-agent workflows by combining:

```text
semantic code index
+ intermediate caching
+ better retrieval/router
```

The goal is not to put every file into a vector database.

The goal is to help agents find the smallest useful context for a task:

```text
task
  -> identify relevant area
  -> route to docs/code/memory
  -> inspect structural code facts
  -> reuse cached derived facts
  -> review or implement with less noise
```

## Why This Exists

RAG is useful for semantic questions, but source code often needs exact structure.

Examples:

```text
Which handler owns this endpoint?
Where is OrderStatus updated?
Which class implements IOrderStore?
Which GraphQL query calls this application handler?
Which files write PaymentStatus?
```

Embedding search can find related text, but it is not the best tool for exact symbol, reference, route, or dependency questions.

## System Lanes

```text
IceBot-Tools
|-- rag
|   |-- docs/code semantic retrieval
|   |-- dense + BM25 hybrid search
|   `-- MCP retrieval tools
|
|-- code-intelligence
|   |-- symbol and reference indexes
|   |-- endpoint-to-handler maps
|   |-- interface-to-implementation maps
|   `-- generated caches
|
`-- scripts
    |-- diagnostics
    |-- environment helpers
    `-- local automation
```

Use RAG for meaning.

Use code intelligence for structure.

Use scripts for repeatable local operation.

## Semantic Code Index

The first useful index should track:

- source files;
- file hashes;
- projects and modules;
- classes;
- interfaces;
- enums;
- methods;
- controllers and routes;
- GraphQL query/resolver entrypoints;
- command/query handlers;
- stores and repositories;
- DI registrations;
- endpoint-to-handler mapping;
- interface-to-implementation mapping;
- important field write locations.

Preferred lookup order for implementation questions:

```text
exact path/symbol search
  -> code index
  -> reference/write-operation search
  -> semantic code RAG
  -> direct file inspection
```

## Intermediate Cache

Agents should not rebuild the same project map every time.

Cache derived facts such as:

- repo summary;
- file inventory;
- file hash state;
- symbol index;
- endpoint-to-handler map;
- interface implementation map;
- DI registration map;
- bounded-context/module map;
- RAG collection manifests.

Generated cache should live under:

```text
data/code_intelligence/
```

Rules:

- cache is generated state;
- cache can be deleted and rebuilt;
- cache must not contain secrets;
- source code and official docs always beat cache;
- cache should use file hashes to skip unchanged files.

## Better Retrieval And Router

Retrieval should be routed instead of searching everything.

Target flow:

```text
question
  -> classify intent
  -> choose source lane
  -> apply metadata/path filters
  -> retrieve candidates
  -> rerank only when useful
  -> return compact context with citations
```

Useful modes:

```text
docs
  Architecture, business rules, API contracts, decisions.

code
  Implementation, symbols, handlers, stores, mappings.

both
  Cross-check docs vs code.

memory
  Previous failure modes and review heuristics.

auto
  Router chooses, but should expose what it chose.
```

Default direction:

```text
docs first
  -> code only when implementation detail is needed
  -> both only for contract/implementation cross-check
```

## Dynamic Context Assembly

Do not preload the entire repository.

Assemble context per task:

```text
task
  -> directly touched files
  -> nearest docs/routing hints
  -> official contracts
  -> code index
  -> RAG retrieval
  -> memory only if useful
```

Example:

```text
Task: review refund API behavior
  -> API docs
  -> order/payment/refund handlers
  -> refund entity/store
  -> related failure memory
```

Do not include unrelated robot runtime, inventory internals, or raw research notes unless the task asks for them.

## Failure Memory

Failure memory should not be mixed into normal source-of-truth retrieval.

It is useful for review tasks and repeated model-collaboration patterns.

Examples:

- build success does not prove authorization correctness;
- endpoint-level auth and field-level GraphQL auth are separate;
- duplicate REST and GraphQL read surfaces confuse frontend contracts;
- SMTP SSL-on-connect and STARTTLS are different;
- rare numeric edge cases can break payment code generation;
- larger embedding models can improve retrieval but may be too slow on CPU.

Store durable learning notes outside generated indexes.

## Graph-RAG Later

Graph-RAG can be considered after simple indexes are useful.

Potential graph nodes:

```text
BoundedContext
Entity
Controller
GraphQLQuery
CommandHandler
QueryHandler
Store
Interface
Endpoint
Policy
DTO
Document
Decision
```

Potential edges:

```text
endpoint -> handler
GraphQL query -> handler
handler -> store
store -> entity
handler -> policy
document -> domain concept
decision -> affected module
```

Do not start with a graph database by default.

Start with SQLite generated indexes. JSON exports are debug/human-inspection artifacts only. Add graph storage only when queries need it.

## Implementation Phases

### Phase 1: Stable Inventory

- scan source files;
- compute file hashes;
- list projects/modules;
- extract class/interface/enum names;
- cache results under `data/code_intelligence`.

### Phase 2: Backend Structure Index

- controllers and routes;
- GraphQL root fields/resolvers;
- command/query handlers;
- store interfaces and implementations;
- DI registrations.

### Phase 3: Router Integration

- route docs/code/both/memory;
- expose retrieval mode decisions;
- use code index before code vector search where possible;
- keep exact search fallback.

### Phase 4: Review Support

- retrieve relevant failure memory;
- generate domain-specific review checklists;
- cross-check docs vs code;
- surface stale docs or duplicate API surfaces.

### Phase 5: Optional Graph Layer

- convert stable indexes into graph edges;
- support dependency/path queries;
- generate diagrams or relationship reports.

## Non-Goals For Now

- no autonomous refactor engine;
- no full compiler/analyzer replacement;
- no embedding secrets or local env files;
- no automatic ingest after every docs edit;
- no graph database before simpler indexes prove useful;
- no treating personal notes as backend source of truth.
