import argparse
import sys
from pathlib import Path

PDF_DIR = Path(__file__).resolve().parents[1]
TOOLS_DIR = PDF_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

from pdf.pdflib.extraction import extract_pdf_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract raw text from a PDF and create a curated-note template."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file to extract.")
    parser.add_argument(
        "--out",
        default=str(TOOLS_DIR / "data" / "pdf_extracts"),
        help="Output root folder. Default: IceBot-Tools/data/pdf_extracts.",
    )
    parser.add_argument("--slug", help="Optional output folder slug.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing output folder for the same slug.",
    )
    parser.add_argument(
        "--copy-source",
        action="store_true",
        help="Copy the source PDF into the output folder. Off by default.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = extract_pdf_text(
        pdf_path=Path(args.pdf_path),
        output_root=Path(args.out),
        slug=args.slug,
        overwrite=args.overwrite,
        copy_source=args.copy_source,
    )

    print(f"Extracted {result.page_count} pages")
    print(f"Output: {result.output_dir}")
    print(f"Text: {result.extracted_text_path}")
    print(f"Metadata: {result.metadata_path}")
    print(f"Note template: {result.note_template_path}")


if __name__ == "__main__":
    main()
