import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from raglib.config import setup_cache_env
from raglib.result_formatting import result_to_dict
from raglib.vector_store import retrieve_context

setup_cache_env()


def parse_args():
    parser = argparse.ArgumentParser(description="Retrieve IceBot project context without calling an LLM.")
    parser.add_argument("query", nargs="?", help="Context query. If omitted, input prompt is shown.")
    parser.add_argument(
        "--lane",
        choices=["docs", "code"],
        default="docs",
        help="Collection lane to retrieve from.",
    )
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of context chunks.")
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=100,
        help="Number of vector search candidates to rerank.",
    )
    parser.add_argument(
        "--no-rerank",
        action="store_true",
        help="Disable reranking and return vector search order.",
    )
    parser.add_argument(
        "--no-hybrid",
        action="store_true",
        help="Disable hybrid dense+sparse retrieval and use dense vector search only.",
    )
    parser.add_argument(
        "--include-vault",
        action="store_true",
        help="Include Vault draft notes. Default retrieves official docs only.",
    )
    parser.add_argument(
        "--status",
        action="append",
        help="Filter by status. Can be repeated, e.g. --status current --status decision-note.",
    )
    parser.add_argument(
        "--authority",
        action="append",
        help="Filter by authority. Can be repeated, e.g. --authority implementation.",
    )
    parser.add_argument(
        "--source-type",
        action="append",
        help="Filter by source_type. Can be repeated, e.g. --source-type backend-doc.",
    )
    parser.add_argument(
        "--source-group",
        action="append",
        help="Filter by source_group. Can be repeated, e.g. --source-group docs.",
    )
    parser.add_argument(
        "--doc-type",
        action="append",
        help="Filter by doc_type. Can be repeated, e.g. --doc-type api.",
    )
    parser.add_argument(
        "--exclude-overview",
        action="store_true",
        help="Exclude overview chunks when retrieving specific rules or APIs.",
    )
    parser.add_argument(
        "--path-contains",
        action="append",
        help="Filter by source_path text. Can be repeated, e.g. --path-contains IOT_CONTRACT.",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format.",
    )
    return parser.parse_args()


def print_markdown_context(query: str, context_items: list[dict]) -> None:
    print("# Retrieved IceBot Context")
    print()
    print(f"Query: {query}")
    print()
    print("Use this context as supporting material. Prefer official/current sources over draft, future, raw, learning, or rejected notes.")
    print()

    for index, item in enumerate(context_items, 1):
        print(f"## Context {index}")
        print()
        print(f"- Source: `{item['source']}`")
        print(f"- Path: `{item['source_path']}`")
        print(f"- Type: `{item['source_type']}`")
        print(f"- Group: `{item['source_group']}`")
        print(f"- Doc type: `{item['doc_type']}`")
        print(f"- Authority: `{item['authority']}`")
        print(f"- Status: `{item['status']}`")
        print(f"- Overview: `{item['is_overview']}`")
        print(f"- Chunk: `{item['chunk_index']}`")
        print(f"- Section index: `{item['section_index']}`")
        print(f"- Section path: `{item['section_path']}`")
        print(f"- Language: `{item['language']}`")
        print(f"- Namespace: `{item['namespace']}`")
        print(f"- Symbol: `{item['symbol_kind']} {item['symbol_name']}`")
        print(f"- Lines: `{item['start_line']}-{item['end_line']}`")
        print(f"- Vector score: `{item['vector_score']}`")
        print(f"- Hybrid score: `{item['hybrid_score']}`")
        print(f"- Rerank score: `{item['rerank_score']}`")
        print()
        print(item["text"])
        print()



def main() -> None:
    args = parse_args()
    query = args.query or input("Context query: ")

    results = retrieve_context(
        query,
        lane=args.lane,
        include_vault=args.include_vault,
        authorities=args.authority,
        statuses=args.status,
        source_types=args.source_type,
        source_groups=args.source_group,
        doc_types=args.doc_type,
        path_contains=args.path_contains,
        include_overview=not args.exclude_overview,
        limit=args.limit,
        candidate_limit=args.candidate_limit,
        use_reranker=not args.no_rerank,
        use_hybrid=not args.no_hybrid,
    )
    context_items = [result_to_dict(result) for result in results]

    if args.format == "json":
        print(json.dumps({"query": query, "contexts": context_items}, ensure_ascii=False, indent=2))
    else:
        print_markdown_context(query, context_items)


if __name__ == "__main__":
    main()
