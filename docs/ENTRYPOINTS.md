# IceBot-Tools Entrypoints

Run commands from `IceBot-Tools`.

## Environment

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

When registering MCP with an IDE/tool, prefer the explicit venv Python:

```powershell
.\.venv\Scripts\python.exe
```

## RAG

```powershell
python .\rag\commands\ingest_docs.py
python .\rag\commands\ingest_code.py
python .\rag\commands\context.py "current payment flow"
python .\rag\commands\context.py --lane code "PaymentSessionsController"
python .\rag\commands\search.py "tenant scope rules"
python .\rag\commands\ask.py
```

Do not run ingest automatically from unrelated workflows. Ingest can be slow on weaker machines and should be started deliberately.

## Code Intelligence

```powershell
python .\code-intelligence\commands\index_code.py
python .\code-intelligence\commands\index_code.py --rebuild
python .\code-intelligence\commands\index_code.py --dry-run
python .\code-intelligence\commands\index_code.py --source icebot-backend
python .\code-intelligence\commands\lookup_symbol.py IOrderStore
python .\code-intelligence\commands\lookup_endpoint.py orders
python .\code-intelligence\commands\lookup_handler.py PlaceOrder --context Orders
python .\code-intelligence\commands\verify_coverage.py
python .\code-intelligence\commands\export_index.py
```

Use Code Intelligence for exact structural questions: symbols, endpoints, handlers, stores, and relationships.

See `code-intelligence/docs/USAGE.md` for schema notes and detailed command examples.

## MCP

```powershell
.\.venv\Scripts\python.exe .\mcp\server.py
```

Codex registration example:

```powershell
codex mcp add icebot-rag -- "<path-to-IceBot-Tools>\.venv\Scripts\python.exe" "<path-to-IceBot-Tools>\mcp\server.py"
```

MCP exposes both semantic RAG tools and Code Intelligence lookup tools.

## Docs Ops

```powershell
python .\docs-ops\commands\check_docs.py
```

Individual checks:

```powershell
python .\docs-ops\commands\check_links.py
python .\docs-ops\commands\check_doc_index.py
python .\docs-ops\commands\find_stale_refs.py
```

Use Docs Ops after moving, deleting, or splitting documentation.

MCP tool:

```text
check_icebot_docs
```

## Log Analyzer

```powershell
.\.venv\Scripts\python.exe .\log-analyzer\analyzer.py
.\.venv\Scripts\python.exe .\log-analyzer\generate_mock_logs.py --count 5
```

Generated log analyzer data belongs under `data/log-analyzer/` and `logs/log-analyzer/`.

For real logs:

```powershell
.\.venv\Scripts\python.exe .\log-analyzer\analyzer.py `
  --webapi-path "D:\path\to\webapi\logs" `
  --robot-path "D:\path\to\robot\logs"
```

See `log-analyzer/docs/USAGE.md`.

MCP tool:

```text
analyze_icebot_logs
```

## Scripts

Start Qdrant from `IceBot-Tools`:

```powershell
.\scripts\start_rag_qdrant.ps1
```

Recreate the pinned Qdrant container after changing the image tag:

```powershell
docker compose -f .\docker\docker-compose.yml down
docker compose -f .\docker\docker-compose.yml pull
docker compose -f .\docker\docker-compose.yml up -d
docker ps --filter "name=IceBot-rag-qdrant"
docker inspect IceBot-rag-qdrant --format "{{.Config.Image}}"
```

Expected image is currently:

```text
qdrant/qdrant:v1.18.1
```

Capture a local CPU/RAM/GPU/process snapshot:

```powershell
.\scripts\system_snapshot.ps1 -Label "before MCP reranker test"
```

Use snapshots before/during/after RAG ingest, MCP, reranker, or Docker debugging.

## PDF Workflow

Use the PDF tooling only to extract and review source material. Curated knowledge belongs in `Vault`, `Docs`, or repository docs after review.

See `pdf/docs/PDF_WORKFLOW.md`.
