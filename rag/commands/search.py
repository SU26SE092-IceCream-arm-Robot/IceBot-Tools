import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[2]))

from raglib.config import setup_cache_env
from raglib.vector_store import retrieve_context

setup_cache_env()


def parse_args():
    parser = argparse.ArgumentParser(description="Search IceBot project knowledge in Qdrant.")
    parser.add_argument("query", nargs="?", help="Search question. If omitted, input prompt is shown.")
    parser.add_argument(
        "--lane",
        choices=["docs", "code"],
        default="docs",
        help="Collection lane to search.",
    )
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of results.")
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
        help="Include Vault draft notes in results. Default searches official docs only.",
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
        help="Exclude overview chunks when searching for specific rules or APIs.",
    )
    parser.add_argument(
        "--path-contains",
        action="append",
        help="Filter by source_path text. Can be repeated, e.g. --path-contains IOT_CONTRACT.",
    )
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    query = args.query or input("Question: ")

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

    for i, result in enumerate(results, 1):
        payload = result.payload or {}

        print("=" * 80)
        print(f"Result {i}")
        print("Vector score:", payload.get("vector_score"))
        print("Hybrid score:", payload.get("hybrid_score"))
        print("Rerank score:", payload.get("rerank_score"))
        print("Source:", payload.get("source"))
        print("Path:", payload.get("source_path"))
        print("Type:", payload.get("source_type"))
        print("Group:", payload.get("source_group"))
        print("Doc type:", payload.get("doc_type"))
        print("Authority:", payload.get("authority"))
        print("Status:", payload.get("status"))
        print("Overview:", payload.get("is_overview"))
        print("Section index:", payload.get("section_index"))
        print("Section path:", payload.get("section_path"))
        print("Language:", payload.get("language"))
        print("Namespace:", payload.get("namespace"))
        print("Symbol:", payload.get("symbol_kind"), payload.get("symbol_name"))
        print("Lines:", payload.get("start_line"), "-", payload.get("end_line"))
        print("-" * 80)
        print(payload.get("text"))


if __name__ == "__main__":
    main()
