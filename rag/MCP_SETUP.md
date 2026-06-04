# Codex MCP Setup

This document explains how to expose local IceBot RAG retrieval to Codex through MCP.

The MCP server does not call OpenAI and does not require `OPENAI_API_KEY`. It only retrieves context from local Qdrant. Codex remains responsible for reasoning over the returned context.

Run commands from `IceBot-Tools` unless noted otherwise.

## First-Time Setup

1. Start Qdrant:

```powershell
docker compose -f docker\docker-compose.yml up -d
```

2. Activate Python environment and install dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Ingest project knowledge:

```powershell
python .\rag\commands\ingest_docs.py
python .\rag\commands\ingest_code.py
```

4. Register the MCP server with Codex:

```powershell
codex mcp add icebot-rag -- "<path-to-IceBot-Tools>\.venv\Scripts\python.exe" "<path-to-IceBot-Tools>\rag\mcp_server.py"
```

Example if the repository is under your user profile:

```powershell
$toolsRoot = "$env:USERPROFILE\Projects\IceCream_arm_Robot\IceBot-Tools"
codex mcp add icebot-rag -- "$toolsRoot\.venv\Scripts\python.exe" "$toolsRoot\rag\mcp_server.py"
```

5. Verify:

```powershell
codex mcp list
```

Expected server name:

```text
icebot-rag
```

6. Restart Codex extension / IDE so the MCP config is reloaded.

## Manual Server Test

Run:

```powershell
.\.venv\Scripts\Activate.ps1
python .\rag\mcp_server.py
```

The process should stay running. Stop it with `Ctrl+C`.

## Usage Prompt

After setup, ask Codex to use the MCP tool explicitly:

```text
Use icebot-rag to retrieve context about the current payment flow, then review the payment code.
```

## Tool Exposed

```text
retrieve_icebot_context
retrieve_icebot_docs
retrieve_icebot_code
```

The tools return context chunks with metadata such as source path, authority, status, retrieval scores, and code symbol/line metadata when available.
Use `retrieve_icebot_context` with `mode=docs|code|both` when you want explicit routing in one tool. Use `retrieve_icebot_docs` and `retrieve_icebot_code` as shortcuts.
The tools accept `use_hybrid=true|false`. Hybrid uses Qdrant dense+sparse retrieval and is useful for exact symbols, paths, endpoints, and enum names.
