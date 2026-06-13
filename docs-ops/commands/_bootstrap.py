import sys
from pathlib import Path


def bootstrap_imports() -> None:
    project_root = Path(__file__).resolve().parents[2]
    docs_ops_root = Path(__file__).resolve().parents[1]

    for path in (project_root, project_root.parent, docs_ops_root):
        path_value = str(path)
        if path_value not in sys.path:
            sys.path.append(path_value)
