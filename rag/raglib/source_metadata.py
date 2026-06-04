import hashlib
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


DOC_TYPE_BY_NAME = {
    "AGENTS.md": "agent-guide",
    "ARCHITECTURE.md": "architecture",
    "API_SURFACE_RULES.md": "api",
    "AUTHORIZATION_RULES.md": "authorization",
    "BOUNDARY_CONTEXTS.md": "domain",
    "BUSINESS_FLOWS.md": "flow",
    "DATA_MODELING_RULES.md": "data-modeling",
    "DEPENDENCY_RULES.md": "dependency",
    "DOCUMENTATION_RULES.md": "documentation",
    "IDEMPOTENCY_RETRY_RULES.md": "idempotency-retry",
    "IOT_CONTRACT.md": "contract",
    "JSON_FIELD_RULES.md": "json",
    "LOCAL_EDGE_RUNTIME_ERD.md": "local-edge-erd",
    "MULTI_TENANCY_RULES.md": "multi-tenancy",
    "NAMING_RULES.md": "naming",
    "RAG_CONTEXT_MAP.md": "routing",
    "SYSTEM_FLOWS.md": "flow",
    "WORKING_PROTOCOL.md": "working-protocol",
}


def calculate_file_hash(file_path: Path) -> str:
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def build_point_id(source_path: str, chunk_index: int, chunk: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"{source_path}:{chunk_index}:{chunk}"))


def build_section_path(section_metadata: dict) -> str | None:
    headings = [
        section_metadata.get("h1"),
        section_metadata.get("h2"),
        section_metadata.get("h3"),
        section_metadata.get("h4"),
    ]
    headings = [heading for heading in headings if heading]

    if not headings:
        return None

    return " > ".join(headings)


def build_source_path(file_path: Path, workspace_root: Path, source_root: Path | None = None) -> str:
    resolved_file_path = file_path.resolve()
    resolved_workspace_root = workspace_root.resolve()

    try:
        return resolved_file_path.relative_to(resolved_workspace_root).as_posix()
    except ValueError:
        pass

    if source_root is not None:
        resolved_source_root = source_root.resolve()

        if resolved_source_root.is_file():
            return resolved_source_root.name

        try:
            relative_to_source = resolved_file_path.relative_to(resolved_source_root).as_posix()
            return f"{resolved_source_root.name}/{relative_to_source}"
        except ValueError:
            pass

    return resolved_file_path.name


def get_vault_status(file_path: Path, workspace_root: Path) -> str:
    relative_path = build_source_path(file_path, workspace_root).lower()

    if "/raw/" in relative_path:
        return "raw"
    if "rejected" in file_path.name.lower():
        return "rejected"
    if "/evolution/" in relative_path or "future" in file_path.name.lower() or "migration" in file_path.name.lower():
        return "future"
    if "/decisions/" in relative_path or "decision" in file_path.name.lower():
        return "decision-note"
    if "/learning/" in relative_path:
        return "learning"

    return "exploration"


def get_source_group(source_type: str) -> str:
    if source_type in {"backend-doc", "project-doc"}:
        return "docs"
    if source_type == "vault":
        return "vault"
    if source_type in {"code", "backend-code"}:
        return "code"
    if source_type == "log":
        return "logs"

    return source_type


def get_doc_type(file_path: Path, source_type: str, workspace_root: Path) -> str:
    file_name = file_path.name

    if file_name in DOC_TYPE_BY_NAME:
        return DOC_TYPE_BY_NAME[file_name]

    if source_type == "vault":
        relative_path = build_source_path(file_path, workspace_root).lower()

        if "/raw/" in relative_path:
            return "raw"
        if "/decisions/" in relative_path:
            return "decision"
        if "/learning/" in relative_path:
            return "learning"
        if "/evolution/" in relative_path:
            return "evolution"
        if "/research/" in relative_path:
            return "research"

    if get_source_group(source_type) == "code":
        return "source-code"

    return "reference"


def is_excluded_source(
    file_path: Path,
    workspace_root: Path,
    excluded_paths: set[str],
    excluded_prefixes: set[str] | None = None,
) -> bool:
    relative_path = build_source_path(file_path, workspace_root)
    if relative_path in excluded_paths:
        return True

    if excluded_prefixes:
        return any(relative_path.startswith(prefix) for prefix in excluded_prefixes)

    return False


def build_metadata(source_config: dict, file_path: Path, workspace_root: Path) -> dict:
    relative_path = build_source_path(file_path, workspace_root, source_config["path"])
    source_type = source_config["source_type"]
    status = source_config["status"]
    authority = source_config["authority"]

    if source_type == "vault":
        status = get_vault_status(file_path, workspace_root)

    return {
        "file_id": str(uuid5(NAMESPACE_URL, relative_path)),
        "file_hash": calculate_file_hash(file_path),
        "source": file_path.name,
        "source_path": relative_path,
        "source_type": source_type,
        "source_group": get_source_group(source_type),
        "doc_type": get_doc_type(file_path, source_type, workspace_root),
        "authority": authority,
        "status": status,
    }
