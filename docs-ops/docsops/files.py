from pathlib import Path
from collections.abc import Iterable

from docsops.config import EXCLUDED_DIR_NAMES


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def iter_markdown_files(roots: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()

    for root in roots:
        root = root.resolve()
        if not root.exists():
            continue

        for path in root.rglob("*.md"):
            path = path.resolve()
            if path in seen or is_excluded(path):
                continue
            seen.add(path)
            files.append(path)

    return sorted(files)


def display_path(path: Path, *, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()
