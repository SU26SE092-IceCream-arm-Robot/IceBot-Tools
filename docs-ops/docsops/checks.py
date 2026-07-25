from pathlib import Path

from docsops.config import DEFAULT_DOC_ROOTS, IMPORTANT_DOC_PATHS, STALE_REFERENCE_PATTERNS
from docsops.files import display_path, iter_markdown_files
from docsops.markdown_links import check_link, extract_markdown_links
from docsops.api_inventory import check_policy_inventory
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


def check_backend_doc_structure(*, max_failures: int = 30) -> dict:
    docs_root = (WORKSPACE_ROOT / "IceBot-Backend" / "docs").resolve()
    files = iter_markdown_files([docs_root])
    failures = []
    total_issues = 0
    forbidden_name_prefixes = ("HISTORICAL_", "DEPRECATED_", "PROPOSAL_")

    def add_failure(file_path: Path, reason: str, line_number: int | None = None) -> None:
        nonlocal total_issues
        total_issues += 1
        if len(failures) < max_failures:
            failures.append({
                "file": display_path(file_path, root=WORKSPACE_ROOT),
                "line": line_number,
                "target": None,
                "reason": reason,
            })

    for file_path in files:
        text = file_path.read_text(encoding="utf-8-sig", errors="ignore")
        lines = text.splitlines()

        if len(lines) > 500:
            add_failure(file_path, f"active backend doc has {len(lines)} lines; split ownership before exceeding 500")

        section_starts = [
            index for index, line in enumerate(lines)
            if line.startswith("## ") or line.startswith("### ")
        ]
        for section_index, start in enumerate(section_starts):
            end = section_starts[section_index + 1] if section_index + 1 < len(section_starts) else len(lines)
            section_length = end - start
            if section_length > 120:
                add_failure(
                    file_path,
                    f"section '{lines[start]}' has {section_length} lines; split it at 120 lines or less",
                    start + 1,
                )

        if file_path.name.startswith(forbidden_name_prefixes):
            add_failure(file_path, "historical/deprecated/proposal material belongs in Vault, not active backend docs")

        if file_path.name == "README.md":
            continue

        if "## Search Keywords" not in lines:
            add_failure(file_path, "missing '## Search Keywords' section")
        if "## Related Docs" not in lines:
            add_failure(file_path, "missing '## Related Docs' section")

    return {
        "check": "backend_doc_structure",
        "passed": total_issues == 0,
        "files_scanned": len(files),
        "failure_count": total_issues,
        "truncated": total_issues > len(failures),
        "failures": failures,
    }


def run_all_docs_checks(*, max_failures_per_check: int = 30) -> dict:
    checks = [
        check_markdown_links(max_failures=max_failures_per_check),
        check_important_doc_index(max_failures=max_failures_per_check),
        find_stale_references(max_failures=max_failures_per_check),
        check_backend_doc_structure(max_failures=max_failures_per_check),
        check_policy_inventory(max_failures=max_failures_per_check),
    ]
    passed = all(check["passed"] for check in checks)

    if passed:
        return {
            "passed": True,
            "summary": "Docs checks passed: links, doc index, stale refs, backend doc structure, API policy inventory.",
        }

    return {
        "passed": False,
        "summary": "Docs checks failed. See failures for actionable details.",
        "checks": checks,
    }
