from dataclasses import dataclass
from pathlib import Path
import re
from urllib.parse import unquote


INLINE_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
REFERENCE_DEF_RE = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.MULTILINE)

IGNORED_SCHEMES = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
    "file:",
    "vscode:",
)


@dataclass(frozen=True)
class MarkdownLink:
    source_file: Path
    target: str
    line_number: int


@dataclass(frozen=True)
class BrokenLink:
    source_file: Path
    target: str
    resolved_path: Path
    line_number: int
    reason: str


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def extract_markdown_links(path: Path) -> list[MarkdownLink]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    links: list[MarkdownLink] = []

    for match in INLINE_LINK_RE.finditer(text):
        links.append(MarkdownLink(path, match.group(1).strip(), _line_number(text, match.start())))

    for match in REFERENCE_DEF_RE.finditer(text):
        links.append(MarkdownLink(path, match.group(1).strip(), _line_number(text, match.start())))

    return links


def is_external_or_anchor_only(target: str) -> bool:
    normalized = target.strip().lower()
    return (
        not normalized
        or normalized.startswith("#")
        or normalized.startswith(IGNORED_SCHEMES)
    )


def normalize_target_path(target: str) -> str:
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    target = target.split("#", 1)[0]
    target = target.split("?", 1)[0]
    return unquote(target.strip())


def check_link(link: MarkdownLink) -> BrokenLink | None:
    if is_external_or_anchor_only(link.target):
        return None

    target_path = normalize_target_path(link.target)
    if not target_path:
        return None

    resolved = (link.source_file.parent / target_path).resolve()
    if resolved.exists():
        return None

    return BrokenLink(
        source_file=link.source_file,
        target=link.target,
        resolved_path=resolved,
        line_number=link.line_number,
        reason="target does not exist",
    )
