# Utility Script Notes

This folder is for small local helper scripts used while developing or operating project tooling.

Keep scripts narrow and explicit. Do not hide important destructive behavior behind vague names.

## Current Scripts

- `start_rag_qdrant.ps1`
  - Starts the Qdrant Docker Compose stack used by the local RAG tools.
  - PowerShell/Windows script. Run it from `IceBot-Tools`.
  - Qdrant is pinned to `qdrant/qdrant:v1.18.1` instead of `latest`.
  - Qdrant ports are bound to `127.0.0.1` because this local setup has no Qdrant auth configured.

Linux/macOS equivalent:

```bash
docker compose -f ./docker/docker-compose.yml up -d
```

## Qdrant Image Update / Recreate

Run script commands from `IceBot-Tools` unless a note explicitly says otherwise.

When `docker-compose.yml` changes the pinned Qdrant image tag, recreate the container from `IceBot-Tools`:

```powershell
docker compose -f .\docker\docker-compose.yml down
docker compose -f .\docker\docker-compose.yml pull
docker compose -f .\docker\docker-compose.yml up -d
```

Verify the running image:

```powershell
docker ps --filter "name=IceBot-rag-qdrant"
docker inspect IceBot-rag-qdrant --format "{{.Config.Image}}"
```

Expected image:

```text
qdrant/qdrant:v1.18.1
```

If Docker still keeps an old container, remove and recreate it:

```powershell
docker rm -f IceBot-rag-qdrant
docker compose -f .\docker\docker-compose.yml up -d
```

This does not delete persisted Qdrant data because storage is mounted at `IceBot-Tools\data\qdrant`.

## Python Dependencies

From `IceBot-Tools`, activate the local virtual environment and install dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`requirements.txt` pins direct tooling dependencies. Update pins deliberately after testing RAG commands, not opportunistically during unrelated work.

## Useful Scripts To Add Later

- `stop_qdrant`
  - Stop the Qdrant container without deleting persisted data.

- `reset_qdrant_data`
  - Stop Qdrant and delete `IceBot-Tools/data/qdrant`.
  - This is destructive and should require a clear confirmation step.

- `activate_tools_env`
  - Print or run the command to activate `IceBot-Tools/.venv`.
  - Useful because most RAG scripts depend on the local Python environment.

- `install_tools_dependencies`
  - Install dependencies from `IceBot-Tools/requirements.txt`.

- `ingest_rag`
  - Run `IceBot-Tools/rag/commands/ingest.py`.
  - Should mention that ingest updates chunks per source file and does not recreate the collection.

- `context_rag`
  - Run `IceBot-Tools/rag/commands/context.py` for Codex IDE/CLI context without calling OpenAI directly.

- `start_rag_mcp`
  - Run `IceBot-Tools/rag/mcp_server.py` as a long-running MCP server for IDE/tool integration.
  - Full Codex MCP setup is documented in `IceBot-Tools/rag/MCP_SETUP.md`.

- `search_rag`
  - Run `IceBot-Tools/rag/commands/search.py` with common defaults.

- `ask_rag`
  - Run `IceBot-Tools/rag/commands/ask.py` with common defaults.

- `check_rag_scripts`
  - Run Python syntax checks for RAG scripts:
    - `python -m py_compile IceBot-Tools/rag/commands/ingest.py`
    - `python -m py_compile IceBot-Tools/rag/commands/context.py`
    - `python -m py_compile IceBot-Tools/rag/commands/search.py`
    - `python -m py_compile IceBot-Tools/rag/commands/ask.py`
    - `python -m py_compile IceBot-Tools/rag/mcp_server.py`

## Naming Rules

- Use verb-first names: `start_qdrant`, `stop_qdrant`, `ingest_rag`.
- Include the target system when the script touches a service or data store.
- Add `reset`, `delete`, or `clear` in the name for destructive scripts.
- Prefer PowerShell scripts on Windows if the command needs environment setup or confirmation logic.
