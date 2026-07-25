import argparse
from pathlib import Path

from _bootstrap import bootstrap_imports

bootstrap_imports()

from docsops.api_inventory import extract_rest_endpoints, render_markdown_inventory


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the current ASP.NET controller route inventory as Markdown."
    )
    parser.add_argument("--output", type=Path, required=True, help="Markdown output path")
    args = parser.parse_args()

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    endpoints = extract_rest_endpoints()
    output.write_text(render_markdown_inventory(endpoints), encoding="utf-8", newline="\n")
    print(f"Wrote {len(endpoints)} REST endpoints to {output}")


if __name__ == "__main__":
    main()
