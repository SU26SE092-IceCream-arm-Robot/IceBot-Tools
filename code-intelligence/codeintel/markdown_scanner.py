import re
import uuid

# Regex for Markdown headings
RE_HEADING = re.compile(r'^(#{1,6})\s+(.+)$')

def scan_markdown_file(file_content: str, file_id: str, repo_key: str, project_key: str) -> dict:
    """Scans a markdown file and extracts heading symbols."""
    symbols = []
    
    lines = file_content.splitlines()
    for idx, line in enumerate(lines):
        line_num = idx + 1
        match = RE_HEADING.match(line.strip())
        if match:
            level_chars = match.group(1)
            heading_text = match.group(2).strip()
            level = len(level_chars)
            
            symbols.append({
                "id": str(uuid.uuid4()),
                "file_id": file_id,
                "repository_key": repo_key,
                "project_key": project_key,
                "bounded_context": None,
                "language": "markdown",
                "kind": f"h{level}", # h1, h2, etc.
                "name": heading_text,
                "full_name": heading_text,
                "namespace": None,
                "containing_type": None,
                "signature": line.strip(),
                "line_start": line_num,
                "line_end": line_num
            })
            
    return {
        "symbols": symbols,
        "endpoints": [],
        "graphql_fields": [],
        "handlers": [],
        "stores_raw": [],
        "relationships": []
    }
