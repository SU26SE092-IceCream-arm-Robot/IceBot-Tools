import os
from pathlib import Path

# Paths resolved relative to this module
TOOLCORE_DIR = Path(__file__).resolve().parent
TOOLS_DIR = TOOLCORE_DIR.parent
WORKSPACE_ROOT = TOOLS_DIR.parent

def resolve_from_tools(path: str or Path) -> Path:
    """Resolves path relative to the TOOLS_DIR, returning an absolute Path."""
    p = Path(path)
    if p.is_absolute():
        return p
    return (TOOLS_DIR / p).resolve()

def resolve_from_workspace(path: str or Path) -> Path:
    """Resolves path relative to the WORKSPACE_ROOT, returning an absolute Path."""
    p = Path(path)
    if p.is_absolute():
        return p
    return (WORKSPACE_ROOT / p).resolve()

def resolve_existing_path(path: str or Path, *, base: Path or None = None) -> Path:
    """Resolves a path by checking workspace root, base directory, or tools directory.
    Returns the path resolved relative to base if exists, workspace next, tools next,
    defaulting to absolute tools path."""
    p = Path(path)
    if p.is_absolute():
        return p
        
    if base:
        resolved = (base / p).resolve()
        if resolved.exists():
            return resolved
            
    resolved_ws = (WORKSPACE_ROOT / p).resolve()
    if resolved_ws.exists():
        return resolved_ws
        
    resolved_tools = (TOOLS_DIR / p).resolve()
    if resolved_tools.exists():
        return resolved_tools
        
    # Default fallback
    return resolved_tools
