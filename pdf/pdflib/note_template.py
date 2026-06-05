from datetime import date
from pathlib import Path


def build_curated_note_template(title: str, metadata_path: Path, extracted_text_path: Path) -> str:
    today = date.today().isoformat()

    return f"""# {title} Notes

Date: {today}
Status: curated note from PDF; not source of truth until reviewed

## Source

- File:
- Extracted text: `{extracted_text_path.as_posix()}`
- Metadata: `{metadata_path.as_posix()}`

## Summary

-

## Relevant Ideas

-

## Trade-offs

-

## Decision Impact For IceBot

-

## Should This Enter Long-term Vault?

- Yes/No:
- Reason:

## Follow-up

-
"""
