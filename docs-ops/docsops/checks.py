from pathlib import Path

from docsops.config import DEFAULT_DOC_ROOTS, IMPORTANT_DOC_PATHS, STALE_REFERENCE_PATTERNS
from docsops.files import display_path, iter_markdown_files
from docsops.markdown_links import check_link, extract_markdown_links
from toolcore.workspace import WORKSPACE_ROOT


def check_markdown_links(paths: list[Path] | None = None, *, max_failures: int = 30) -> dict:
    roots = paths if paths else DEFAULT_DOC_ROOTS
    files = iter_markdown_files(roots)
    failures = []
    total_broken = 0

    for file_path in files:
        for link in extract_markdown_links(file_path):
            result = check_link(link)
            if not result:
                continue

            total_broken += 1
            if len(failures) < max_failures:
                failures.append({
                    "file": display_path(result.source_file, root=WORKSPACE_ROOT),
                    "line": result.line_number,
                    "target": result.target,
                    "reason": result.reason,
                })

    return {
        "check": "links",
        "passed": total_broken == 0,
        "files_scanned": len(files),
        "failure_count": total_broken,
        "truncated": total_broken > len(failures),
        "failures": failures,
    }


def check_important_doc_index(*, max_failures: int = 30) -> dict:
    failures = []
    missing_count = 0
    broken_count = 0

    for relative_path in IMPORTANT_DOC_PATHS:
        path = (WORKSPACE_ROOT / relative_path).resolve()
        if not path.exists():
            missing_count += 1
            if len(failures) < max_failures:
                failures.append({
                    "file": relative_path,
                    "line": None,
                    "target": None,
                    "reason": "important doc is missing",
                })
            continue

        for link in extract_markdown_links(path):
            result = check_link(link)
            if not result:
                continue

            broken_count += 1
            if len(failures) < max_failures:
                failures.append({
                    "file": display_path(result.source_file, root=WORKSPACE_ROOT),
                    "line": result.line_number,
                    "target": result.target,
                    "reason": result.reason,
                })

    failure_count = missing_count + broken_count
    return {
        "check": "doc_index",
        "passed": failure_count == 0,
        "docs_checked": len(IMPORTANT_DOC_PATHS),
        "failure_count": failure_count,
        "missing_count": missing_count,
        "broken_link_count": broken_count,
        "truncated": failure_count > len(failures),
        "failures": failures,
    }


def find_stale_references(
    paths: list[Path] | None = None,
    *,
    extra_patterns: list[str] | None = None,
    max_failures: int = 30,
) -> dict:
    roots = paths if paths else DEFAULT_DOC_ROOTS
    patterns = [*STALE_REFERENCE_PATTERNS, *(extra_patterns or [])]
    files = iter_markdown_files(roots)
    failures = []
    total_hits = 0

    for file_path in files:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for pattern in patterns:
                if pattern not in line:
                    continue

                total_hits += 1
                if len(failures) < max_failures:
                    failures.append({
                        "file": display_path(file_path, root=WORKSPACE_ROOT),
                        "line": line_number,
                        "pattern": pattern,
                        "text": line.strip(),
                    })

    return {
        "check": "stale_refs",
        "passed": total_hits == 0,
        "files_scanned": len(files),
        "failure_count": total_hits,
        "truncated": total_hits > len(failures),
        "failures": failures,
    }


def run_all_docs_checks(*, max_failures_per_check: int = 30) -> dict:
    checks = [
        check_markdown_links(max_failures=max_failures_per_check),
        check_important_doc_index(max_failures=max_failures_per_check),
        find_stale_references(max_failures=max_failures_per_check),
    ]
    passed = all(check["passed"] for check in checks)

    if passed:
        return {
            "passed": True,
            "summary": "Docs checks passed: links, doc index, stale refs.",
        }

    return {
        "passed": False,
        "summary": "Docs checks failed. See failures for actionable details.",
        "checks": checks,
    }
