import json
from pathlib import Path
from toolcore.workspace import TOOLS_DIR

def choose_config_path(local_path: Path, example_path: Path) -> Path:
    """Returns local_path if it exists, otherwise falls back to example_path."""
    if local_path.exists():
        return local_path
    return example_path

def load_json_array_config(config_path: Path) -> list:
    """Loads a JSON file at config_path and returns it as a list. Raises ValueError if format is incorrect."""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
        
    try:
        content = config_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as ex:
        raise ValueError(f"Invalid JSON in config file {config_path}: {ex}") from ex
        
    if not isinstance(data, list):
        raise ValueError(f"Config file must contain a JSON array: {config_path}")
        
    return data

def resolve_source_paths(raw_sources: list, *, base_dir: Path, workspace_root: Path) -> list:
    """Resolves relative 'path' keys in source config items to absolute Paths.
    Checks workspace_root first, then base_dir, then tools_dir, and defaults to workspace_root resolution."""
    resolved = []
    for item in raw_sources:
        if not isinstance(item, dict):
            continue
            
        raw_path = item.get("path")
        if raw_path is None:
            resolved.append(item)
            continue
            
        p = Path(raw_path)
        if p.is_absolute():
            resolved_path = p.resolve()
        else:
            # Check existence
            ws_path = (workspace_root / p).resolve()
            base_path = (base_dir / p).resolve()
            tools_path = (TOOLS_DIR / p).resolve()
            
            if ws_path.exists():
                resolved_path = ws_path
            elif base_path.exists():
                resolved_path = base_path
            elif tools_path.exists():
                resolved_path = tools_path
            else:
                resolved_path = ws_path
                
        resolved_item = {**item, "path": resolved_path}
        resolved.append(resolved_item)
        
    return resolved
