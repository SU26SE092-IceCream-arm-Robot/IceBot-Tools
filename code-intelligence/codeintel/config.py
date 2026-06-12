from pathlib import Path
from toolcore.workspace import WORKSPACE_ROOT, TOOLS_DIR
from toolcore.source_config import choose_config_path, load_json_array_config, resolve_source_paths

# Paths relative to this file
CODEINTEL_DIR = Path(__file__).resolve().parent
CODE_INTEL_ROOT = CODEINTEL_DIR.parent

# Generated output locations
DATA_DIR = TOOLS_DIR / "data" / "code_intelligence"
LOG_DIR = TOOLS_DIR / "logs" / "code-intelligence"
DB_PATH = DATA_DIR / "icebot_code_index.sqlite"
EXPORT_DIR = DATA_DIR / "exports"

def get_config_path() -> Path:
    """Returns the path to the configuration file, prioritizing local over example."""
    local_path = CODE_INTEL_ROOT / "sources.code-intelligence.local.json"
    example_path = CODE_INTEL_ROOT / "sources.code-intelligence.example.json"
    return choose_config_path(local_path, example_path)

def load_sources_config(config_path: Path = None) -> list:
    """Loads and resolves repository source configurations."""
    if not config_path:
        config_path = get_config_path()
        
    raw_sources = load_json_array_config(config_path)
    resolved = resolve_source_paths(raw_sources, base_dir=CODE_INTEL_ROOT, workspace_root=WORKSPACE_ROOT)
    
    resolved_sources = []
    for source in resolved:
        resolved_source = {
            "repository_key": source.get("repository_key", ""),
            "display_name": source.get("display_name", ""),
            "path": source["path"],
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
