import re
from pathlib import Path

from raglib.config import RAG_CHUNK_OVERLAP, RAG_CHUNK_SIZE


SYMBOL_PATTERN = re.compile(
    r"^\s*(?:public|private|protected|internal|static|sealed|abstract|partial|async|\s)+"
    r"(?:class|record|struct|interface|enum|void|Task|ValueTask|IActionResult|ActionResult|[A-Za-z_][\w<>?,\[\]]*)\s+"
    r"(?P<name>[A-Za-z_]\w*)",
    re.MULTILINE,
)

NAMESPACE_PATTERN = re.compile(r"^\s*namespace\s+([A-Za-z_][\w.]*)", re.MULTILINE)
TYPE_PATTERN = re.compile(
    r"^\s*(?:public|private|protected|internal|static|sealed|abstract|partial|\s)*"
    r"(?P<kind>class|record|struct|interface|enum)\s+(?P<name>[A-Za-z_]\w*)",
    re.MULTILINE,
)


def is_empty_code_chunk(text: str) -> bool:
    normalized = text.strip()

    if not normalized:
        return True

    noise = normalized
    for marker in ("{", "}", "(", ")", "[", "]", ";", ",", ".", "/", "*", "#"):
        noise = noise.replace(marker, "")

    return not noise.strip()


def detect_namespace(text: str) -> str | None:
    match = NAMESPACE_PATTERN.search(text)
    return match.group(1) if match else None


def detect_primary_type(text: str) -> tuple[str | None, str | None]:
    match = TYPE_PATTERN.search(text)

    if not match:
        return None, None

    return match.group("kind"), match.group("name")


def line_number_at(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


class CodeChunker:
    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None) -> None:
        self.chunk_size = chunk_size or RAG_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else RAG_CHUNK_OVERLAP
        self.last_skipped_empty_chunks = 0

    def split(self, text: str, file_path: Path) -> list[dict]:
        self.last_skipped_empty_chunks = 0
        language = get_language(file_path)
        namespace = detect_namespace(text)
        symbol_kind, symbol_name = detect_primary_type(text)

        if language == "csharp":
            chunks = self.split_csharp(text, namespace, symbol_kind, symbol_name)
        else:
            chunks = self.split_plain_text(text, namespace, symbol_kind, symbol_name)

        filtered_chunks = []
        for chunk in chunks:
            if is_empty_code_chunk(chunk["text"]):
                self.last_skipped_empty_chunks += 1
                continue

            filtered_chunks.append(chunk)

        return filtered_chunks

    def split_csharp(
        self,
        text: str,
        namespace: str | None,
        symbol_kind: str | None,
        symbol_name: str | None,
    ) -> list[dict]:
        symbol_matches = list(SYMBOL_PATTERN.finditer(text))

        if not symbol_matches:
            return self.split_plain_text(text, namespace, symbol_kind, symbol_name)

        chunks = []
        boundaries = [match.start() for match in symbol_matches] + [len(text)]

        for index, match in enumerate(symbol_matches):
            start = boundaries[index]
            end = boundaries[index + 1]
            symbol_text = text[start:end].strip()
            chunks.extend(
                self.split_large_symbol(
                    symbol_text,
                    line_number_at(text, start),
                    namespace,
                    symbol_kind,
                    match.group("name"),
                )
            )

        return chunks

    def split_plain_text(
        self,
        text: str,
        namespace: str | None,
        symbol_kind: str | None,
        symbol_name: str | None,
    ) -> list[dict]:
        return self.split_large_symbol(text, 1, namespace, symbol_kind, symbol_name)

    def split_large_symbol(
        self,
        text: str,
        start_line: int,
        namespace: str | None,
        symbol_kind: str | None,
        symbol_name: str | None,
    ) -> list[dict]:
        lines = text.splitlines()
        chunks = []
        current_lines = []
        current_size = 0
        current_start_line = start_line

        for offset, line in enumerate(lines):
            line_size = len(line) + 1

            if current_lines and current_size + line_size > self.chunk_size:
                chunks.append(
                    build_code_chunk(
                        current_lines,
                        current_start_line,
                        namespace,
                        symbol_kind,
                        symbol_name,
                    )
                )

                overlap_lines = get_overlap_lines(current_lines, self.chunk_overlap)
                current_start_line = start_line + offset - len(overlap_lines)
                current_lines = overlap_lines
                current_size = sum(len(item) + 1 for item in current_lines)

            current_lines.append(line)
            current_size += line_size

        if current_lines:
            chunks.append(
                build_code_chunk(
                    current_lines,
                    current_start_line,
                    namespace,
                    symbol_kind,
                    symbol_name,
                )
            )

        return chunks


def build_code_chunk(
    lines: list[str],
    start_line: int,
    namespace: str | None,
    symbol_kind: str | None,
    symbol_name: str | None,
) -> dict:
    return {
        "text": "\n".join(lines).strip(),
        "start_line": start_line,
        "end_line": start_line + len(lines) - 1,
        "namespace": namespace,
        "symbol_kind": symbol_kind,
        "symbol_name": symbol_name,
    }


def get_overlap_lines(lines: list[str], overlap_chars: int) -> list[str]:
    if overlap_chars <= 0:
        return []

    overlap_lines = []
    total_size = 0

    for line in reversed(lines):
        line_size = len(line) + 1
        if total_size + line_size > overlap_chars:
            break
        overlap_lines.insert(0, line)
        total_size += line_size

    return overlap_lines


def get_language(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".cs":
        return "csharp"
    if suffix == ".json":
        return "json"
    if suffix in {".csproj", ".props", ".targets"}:
        return "xml"

    return suffix.lstrip(".") or "text"
