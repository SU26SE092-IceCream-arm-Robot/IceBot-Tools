import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .note_template import build_curated_note_template


@dataclass(frozen=True)
class PdfExtractionResult:
    output_dir: Path
    extracted_text_path: Path
    metadata_path: Path
    note_template_path: Path
    page_count: int


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "pdf-document"


def calculate_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def extract_pdf_text(
    pdf_path: Path,
    output_root: Path,
    slug: str | None = None,
    overwrite: bool = False,
    copy_source: bool = False,
) -> PdfExtractionResult:
    try:
        import fitz
    except ImportError as ex:
        raise RuntimeError("PyMuPDF is required. Run: pip install -r requirements.txt") from ex

    source_path = pdf_path.resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"PDF file not found: {source_path}")

    if source_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file: {source_path}")

    document_slug = slugify(slug or source_path.stem)
    output_dir = output_root.resolve() / document_slug
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(f"Output folder already exists. Use --overwrite: {output_dir}")
    if output_dir.exists() and overwrite:
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    extracted_text_path = output_dir / "extracted.txt"
    metadata_path = output_dir / "metadata.json"
    note_template_path = output_dir / "curated_note_template.md"

    page_texts: list[str] = []
    with fitz.open(source_path) as document:
        page_count = document.page_count
        for page_index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            page_texts.append(f"--- Page {page_index} ---\n\n{text}")

    extracted_text_path.write_text("\n\n".join(page_texts).strip() + "\n", encoding="utf-8")

    copied_source_path = None
    if copy_source:
        copied_source_path = output_dir / source_path.name
        shutil.copy2(source_path, copied_source_path)

    metadata = {
        "source_path": str(source_path),
        "source_name": source_path.name,
        "source_sha256": calculate_sha256(source_path),
        "page_count": page_count,
        "extractor": "PyMuPDF",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(output_dir),
        "output_files": {
            "extracted_text": str(extracted_text_path),
            "metadata": str(metadata_path),
            "curated_note_template": str(note_template_path),
            "copied_source": str(copied_source_path) if copied_source_path else None,
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    note_template = build_curated_note_template(source_path.stem, metadata_path, extracted_text_path)
    note_template_path.write_text(note_template, encoding="utf-8")

    return PdfExtractionResult(
        output_dir=output_dir,
        extracted_text_path=extracted_text_path,
        metadata_path=metadata_path,
        note_template_path=note_template_path,
        page_count=page_count,
    )
