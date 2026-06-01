import hashlib
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


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


def is_excluded_source(file_path: Path, workspace_root: Path, excluded_paths: set[str]) -> bool:
    relative_path = build_source_path(file_path, workspace_root)
    return relative_path in excluded_paths


def build_metadata(source_config: dict, file_path: Path, workspace_root: Path) -> dict:
    relative_path = build_source_path(file_path, workspace_root, source_config["path"])
    source_type = source_config["source_type"]
    status = source_config["status"]

    if source_type == "vault":
        status = get_vault_status(file_path, workspace_root)

    return {
        "file_id": str(uuid5(NAMESPACE_URL, relative_path)),
        "file_hash": calculate_file_hash(file_path),
        "source": file_path.name,
        "source_path": relative_path,
        "source_type": source_type,
        "authority": source_config["authority"],
        "status": status,
    }
