from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from raglib.source_metadata import build_section_path


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

    def split(self, text: str) -> list[dict]:
        chunks = []
        sections = self.markdown_splitter.split_text(text)

        if not sections:
            sections = [{"page_content": text, "metadata": {}}]

        for section_index, section in enumerate(sections):
            section_text = getattr(section, "page_content", None) or section.get("page_content", "")
            section_metadata = getattr(section, "metadata", None) or section.get("metadata", {})
            section_path = build_section_path(section_metadata)

            for chunk in self.chunk_splitter.split_text(section_text):
                chunks.append(
                    {
                        "text": chunk,
                        "section_index": section_index,
                        "section_path": section_path,
                    }
                )

        return chunks
