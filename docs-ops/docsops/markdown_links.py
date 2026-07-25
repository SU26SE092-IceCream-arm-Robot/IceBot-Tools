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


def _heading_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    occurrences: dict[str, int] = {}

    for line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue

        heading = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", match.group(1))
        heading = re.sub(r"<[^>]+>", "", heading)
        heading = heading.replace("`", "").replace("*", "").replace("_", "")
        slug = "".join(character for character in heading.lower()
                       if character.isalnum() or character.isspace() or character == "-")
        slug = re.sub(r"\s+", "-", slug.strip())

        duplicate_index = occurrences.get(slug, 0)
        occurrences[slug] = duplicate_index + 1
        anchors.add(slug if duplicate_index == 0 else f"{slug}-{duplicate_index}")

    return anchors


def check_link(link: MarkdownLink) -> BrokenLink | None:
    target = link.target.strip()
    anchor_only = target.startswith("#")
    if is_external_or_anchor_only(target) and not anchor_only:
        return None

    target_path = normalize_target_path(target)
    resolved = link.source_file.resolve() if anchor_only else (link.source_file.parent / target_path).resolve()

    if not resolved.exists():
        return BrokenLink(
            source_file=link.source_file,
            target=link.target,
            resolved_path=resolved,
            line_number=link.line_number,
            reason="target does not exist",
        )

    fragment = unquote(target.split("#", 1)[1]).strip().lower() if "#" in target else ""
    if fragment and resolved.is_file() and resolved.suffix.lower() == ".md":
        if fragment not in _heading_anchors(resolved):
            return BrokenLink(
                source_file=link.source_file,
                target=link.target,
                resolved_path=resolved,
                line_number=link.line_number,
                reason=f"heading anchor '#{fragment}' does not exist",
            )

    return None
