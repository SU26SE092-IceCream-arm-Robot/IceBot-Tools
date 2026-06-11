import os
from pathlib import Path
from codeintel.ignore_rules import FileFilter
from codeintel.file_hashing import generate_file_id, compute_file_hash

def infer_project_key(relative_path: str) -> str:
    """Infers project_key from the relative path."""
    path_str = relative_path.replace('\\', '/')
    parts = path_str.split('/')
    if len(parts) > 1 and parts[0] == 'src':
        return parts[1]
    if parts[0] == 'docs' or parts[0] in ('ARCHITECTURE.md', 'AGENTS.md'):
        return 'docs'
    return 'unknown'

def infer_bounded_context(relative_path: str) -> str or None:
    """Infers bounded_context from the relative path."""
    path_str = relative_path.replace('\\', '/')
    parts = path_str.split('/')
    
    # Must be inside src/
    if len(parts) > 2 and parts[0] == 'src':
        # Special case: WebAPI controllers or GraphQL queries/mutations
        if parts[1] == 'WebAPI' and parts[2] in ('Controllers', 'GraphQL'):
            if len(parts) > 4:  # e.g., src/WebAPI/Controllers/Tenants/TenantsController.cs
                return parts[3]
            return None  # file is directly under Controllers/ or GraphQL/
            
        # Standard projects: e.g. src/Application/Orders/PlaceOrderCommand.cs
        if len(parts) > 3:
            return parts[2]
            
    return None

def infer_language(relative_path: str) -> str:
    """Infers language from the file extension."""
    ext = Path(relative_path).suffix.lower()
    if ext == '.cs':
        return 'csharp'
    elif ext == '.md':
        return 'markdown'
    return 'unknown'

def scan_source_files(source_config: dict) -> list:
    """Scans and filters files in a source directory based on its configuration."""
    repo_key = source_config["repository_key"]
    source_root = Path(source_config["path"])
    
    if not source_root.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_root}")
        
    file_filter = FileFilter(source_config.get("include", []), source_config.get("exclude", []))
    
    scanned_files = []
    # Walk recursive using Path
    for p in source_root.rglob("*"):
        if not p.is_file():
            continue
            
        # Get relative path with respect to the source root
        try:
            rel_path = p.relative_to(source_root)
        except ValueError:
            continue
            
        rel_path_str = str(rel_path)
        
        # Check against include/exclude patterns
        if not file_filter.should_include(rel_path_str):
            continue
            
        language = infer_language(rel_path_str)
        project_key = infer_project_key(rel_path_str)
        
        # Calculate file ID and hash
        file_id = generate_file_id(repo_key, rel_path_str)
        file_hash = compute_file_hash(p)
        
        scanned_files.append({
            "repository_key": repo_key,
            "project_key": project_key,
            "language": language,
            "source_root": str(source_root),
            "source_path": str(p.resolve()),
            "relative_path": rel_path_str,
            "file_id": file_id,
            "file_hash": file_hash
        })
        
    return scanned_files
