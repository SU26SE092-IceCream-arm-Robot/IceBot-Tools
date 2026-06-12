from pathlib import Path

from toolcore.workspace import WORKSPACE_ROOT


DEFAULT_DOC_ROOTS = [
    WORKSPACE_ROOT,
]

EXCLUDED_DIR_NAMES = {
    ".git",
    ".local",
    ".venv",
    "__pycache__",
    "bin",
    "obj",
    "node_modules",
    "data",
    "logs",
}

IMPORTANT_DOC_PATHS = [
    "README.md",
    "Docs/README.md",
    "IceBot-Backend/AGENTS.md",
    "IceBot-Backend/ARCHITECTURE.md",
    "IceBot-Backend/docs/README.md",
    "IceBot-Backend/docs/RAG_CONTEXT_MAP.md",
    "IceBot-Tools/AGENTS.md",
    "IceBot-Tools/README.md",
    "IceBot-Tools/docs/ENTRYPOINTS.md",
    "IceBot-Tools/docs/TOOLING.md",
    "IceBot-Tools/docs/STORAGE.md",
    "Vault/README.md",
    "Vault/INDEX.md",
    "Vault/VAULT_STRUCTURE.md",
    "Vault/Research/Papers/PAPER_INDEX.md",
]

STALE_REFERENCE_PATTERNS = [
    "IceBot-Tools/rag/README.md",
    "IceBot-Tools\\rag\\README.md",
    "IceBot-Tools/mcp/README.md",
    "IceBot-Tools\\mcp\\README.md",
    "IceBot-Tools/code-intelligence/README.md",
    "IceBot-Tools\\code-intelligence\\README.md",
    "IceBot-Tools/scripts/README.md",
    "IceBot-Tools\\scripts\\README.md",
    "IceBot-Tools/infrastructure/README.md",
    "IceBot-Tools\\infrastructure\\README.md",
    "IceBot-Tools/log-analyzer/README.md",
    "IceBot-Tools\\log-analyzer\\README.md",
    "rag/README.md",
    "mcp/README.md",
    "code-intelligence/README.md",
    "scripts/README.md",
    "infrastructure/README.md",
    "log-analyzer/README.md",
    "Vault/Decisions/README.md",
    "Vault/Discussions/README.md",
    "Vault/Learning/Tooling/RAG/README.md",
    "Vault/Learning/Tooling/AgentHarness/README.md",
    "Vault/Research/Papers/Notes/README.md",
    "Vault/Research/Papers/Raw/README.md",
    "MCP_SETUP.md",
    "docs/WORKING_PROTOCOL.md",
]
