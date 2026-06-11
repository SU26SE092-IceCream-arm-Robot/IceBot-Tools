import os
import json
from pathlib import Path

# Paths relative to this file
CODEINTEL_DIR = Path(__file__).resolve().parent
CODE_INTEL_ROOT = CODEINTEL_DIR.parent
WORKSPACE_ROOT = CODE_INTEL_ROOT.parent

# Generated output locations
DATA_DIR = WORKSPACE_ROOT / "data" / "code_intelligence"
LOG_DIR = WORKSPACE_ROOT / "logs" / "code-intelligence"
DB_PATH = DATA_DIR / "icebot_code_index.sqlite"
EXPORT_DIR = DATA_DIR / "exports"

def get_config_path() -> Path:
    """Returns the path to the configuration file, prioritizing local over example."""
    local_path = CODE_INTEL_ROOT / "sources.code-intelligence.local.json"
    if local_path.exists():
        return local_path
    return CODE_INTEL_ROOT / "sources.code-intelligence.example.json"

def load_sources_config(config_path: Path = None) -> list:
    """Loads and resolves repository source configurations."""
    if not config_path:
        config_path = get_config_path()
        
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
        
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
        
    resolved_sources = []
    for source in config_data:
        if not isinstance(source, dict):
            continue
            
        # Resolve the relative repository path, trying WORKSPACE_ROOT first, then config_dir
        raw_path = source.get("path", "")
        config_dir = config_path.parent
        
        path_via_workspace = Path(os.path.abspath(WORKSPACE_ROOT / raw_path))
        path_via_config = Path(os.path.abspath(config_dir / raw_path))
        
        if path_via_workspace.exists():
            resolved_path = path_via_workspace
        elif path_via_config.exists():
            resolved_path = path_via_config
        else:
            resolved_path = path_via_workspace  # fallback default
        
        resolved_source = {
            "repository_key": source.get("repository_key", ""),
            "display_name": source.get("display_name", ""),
            "path": resolved_path,
            "enabled": source.get("enabled", True),
            "language": source.get("language", "mixed"),
            "include": source.get("include", []),
            "exclude": source.get("exclude", [])
        }
        resolved_sources.append(resolved_source)
        
    return resolved_sources

def ensure_directories():
    """Ensure all generated folders exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
