from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from raglib.source_metadata import build_section_path


def is_empty_chunk(text: str) -> bool:
    normalized = text.strip()

    if not normalized:
        return True

    markdown_noise = normalized

    for marker in ("-", "_", "*", "`", "#", ">", "|", ":", ";"):
        markdown_noise = markdown_noise.replace(marker, "")

    return not markdown_noise.strip()


def get_section_text(section) -> str:
    if hasattr(section, "page_content"):
        return section.page_content

    return section.get("page_content", "")


def get_section_metadata(section) -> dict:
    if hasattr(section, "metadata"):
        return section.metadata

    return section.get("metadata", {})


class MarkdownChunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
                ("####", "h4"),
            ],
            strip_headers=False,
        )
        self.chunk_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self.last_skipped_empty_chunks = 0

    def split(self, text: str) -> list[dict]:
        chunks = []
        self.last_skipped_empty_chunks = 0
        sections = self.markdown_splitter.split_text(text)

        if not sections:
            sections = [{"page_content": text, "metadata": {}}]

        for section_index, section in enumerate(sections):
            section_text = get_section_text(section)
            section_metadata = get_section_metadata(section)
            section_path = build_section_path(section_metadata)

            for chunk in self.chunk_splitter.split_text(section_text):
                chunk_text = chunk.strip()

                if is_empty_chunk(chunk_text):
                    self.last_skipped_empty_chunks += 1
                    continue

                chunks.append(
                    {
                        "text": chunk_text,
                        "section_index": section_index,
                        "section_path": section_path,
                    }
                )

        return chunks
