# IceBot Unified MCP Server

This directory contains the unified Model Context Protocol (MCP) server for `IceBot-Tools`. It consolidates both semantic search retrieval (RAG) and structural code indexing (Code Intelligence) into a single, cohesive adapter interface for AI coding assistants.

---

## Architecture

```text
                  +--------------------------------+
                  |           AI Coding            |
                  |           Assistant            |
                  +---------------+----------------+
                                  |
                                  | (MCP Session)
                                  v
                  +--------------------------------+
                  |         FastMCP Server         |
                  |        (mcp/server.py)         |
                  +---------------+-------+--------+
                                  |       |
                 +----------------+       +----------------+
                 |                                         |
                 v                                         v
       +------------------+                      +------------------+
       |   RAG Lane       |                      |  CodeIntel Lane  |
       |  (Semantic)      |                      |  (Structural)    |
       |  - rag/          |                      |  - code-intel/   |
       +------------------+                      +------------------+
```

---

## Running the Server

Start the FastMCP server with the project virtual environment:

```powershell
.\.venv\Scripts\python.exe .\mcp\server.py
```

If the virtual environment is already activated, `python .\mcp\server.py` is also fine.

---

## Registered MCP Tools

### 1. Semantic Retrieval Tools (RAG Lane)

-   **`retrieve_icebot_context(query, mode="docs", limit=5)`**
    Retreive contextual information using semantic search.
    -   `mode`: `"docs"` (default), `"code"`, or `"both"`.
-   **`retrieve_icebot_docs(query, limit=5)`**
    Retrieve documentation chunks. Prefer this for architectural concepts, business flows, contracts, and setup guides.
-   **`retrieve_icebot_code(query, limit=5)`**
    Retrieve code snippets semantically. Prefer this for open-ended implementation context.

### 2. Exact Lookup Tools (Code Intelligence Lane)

-   **`lookup_icebot_symbol(query)`**
    Search the C# index for class, interface, method, struct, record, or enum definitions.
-   **`lookup_icebot_endpoint(query)`**
    Search the C# index for matching REST routes, HTTP verbs, or actions.
-   **`lookup_icebot_handler(query, context=None)`**
    Retrieve matching CQRS Command/Query handlers, request/response models, and store parameters.
-   **`verify_icebot_code_index(dry_run=True)`**
    Verify the code index coverage metrics.

---

## Capability Lane Guidelines

-   **Use Code Intelligence tools** when you know the exact name of a symbol (`IOrderStore`), route (`orders/cancel`), or handler (`PlaceOrder`).
-   **Use RAG tools** when seeking background explanations, design rationale, or high-level architecture.
