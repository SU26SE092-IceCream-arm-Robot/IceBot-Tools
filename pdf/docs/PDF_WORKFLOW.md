# PDF Workflow

This workflow turns a PDF into raw extracted text and a reviewed curated note.

It is designed for Workflow 2:

```text
PDF
  -> Extract Text
  -> AI Summary / analysis
  -> Curated Note
  -> Vault, only after review
```

## Why This Workflow

- Raw PDF extraction is noisy and should not become project truth directly.
- AI summary is an intermediate aid, not a final decision.
- Curated notes keep `Vault` readable and reduce RAG noise.
- Generated extracts stay local and are ignored by git.

## Current Decision

PDF-to-Markdown is not a default step in this workflow.

Default:

```text
PDF
  -> Extract Text
  -> AI Summary / analysis
  -> Curated Note
```

Not default:

```text
PDF
  -> Converted Markdown
  -> Curated Note
```

Converted Markdown is useful only when the converted document itself becomes a searchable/readable artifact, such as for paper-scale RAG, full-text search across many papers, or batch processing. For normal reading and note-making, it becomes a duplicate intermediate copy between the original PDF and the curated note.

## Setup

Run from `IceBot-Tools`:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Extract Text

```powershell
python .\pdf\commands\extract_text.py "D:\path\to\document.pdf"
```

Default output:

```text
IceBot-Tools/data/pdf_extracts/<pdf-slug>/
  extracted.txt
  metadata.json
  curated_note_template.md
```

Use a custom slug:

```powershell
python .\pdf\commands\extract_text.py "D:\path\to\document.pdf" --slug robot-runtime-paper
```

Overwrite an existing extract:

```powershell
python .\pdf\commands\extract_text.py "D:\path\to\document.pdf" --overwrite
```

Copying the source PDF into output is off by default. Use it only when useful for local review:

```powershell
python .\pdf\commands\extract_text.py "D:\path\to\document.pdf" --copy-source
```

## Curated Note Process

1. Read `extracted.txt`.
2. Ask an LLM to summarize, extract decisions, and identify trade-offs.
3. Fill `curated_note_template.md`.
4. Move the reviewed note into the relevant `Vault` folder.
5. Do not treat the raw extract as source of truth.

## Boundaries

- Do not commit raw PDFs.
- Do not commit `data/pdf_extracts`.
- Do not ingest `data/pdf_extracts` into long-term RAG.
- Only reviewed curated notes should enter `Vault`.
- Workflow 3, polished PDF-to-Markdown conversion, is reserved for high-value long-lived references.
