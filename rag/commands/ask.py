import argparse
import os
import sys
from pathlib import Path

from openai import OpenAI

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[2]))

from raglib.config import (
    DEFAULT_LLM_MODEL,
    setup_cache_env,
)
from raglib.vector_store import retrieve_context

setup_cache_env()


def parse_args():
    parser = argparse.ArgumentParser(description="Ask questions over IceBot project knowledge.")
    parser.add_argument("question", nargs="?", help="Question. If omitted, input prompt is shown.")
    parser.add_argument(
        "--lane",
        choices=["docs", "code"],
        default="docs",
        help="Collection lane to retrieve from.",
    )
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of retrieved chunks.")
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=100,
        help="Number of vector search candidates to rerank before answering.",
    )
    parser.add_argument(
        "--no-rerank",
        action="store_true",
        help="Disable reranking and answer from vector search order.",
    )
    parser.add_argument(
        "--no-hybrid",
        action="store_true",
        help="Disable hybrid dense+sparse retrieval and use dense vector search only.",
    )
    parser.add_argument(
        "--include-vault",
        action="store_true",
        help="Include Vault draft notes. Default answers from official docs only.",
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
        help="Exclude overview chunks when answering from specific rules or APIs.",
    )
    parser.add_argument(
        "--path-contains",
        action="append",
        help="Filter by source_path text. Can be repeated, e.g. --path-contains IOT_CONTRACT.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", DEFAULT_LLM_MODEL),
        help="OpenAI model used to answer.",
    )
    return parser.parse_args()


def format_context(results) -> str:
    context_parts = []

    for index, result in enumerate(results, 1):
        payload = result.payload or {}
        context_parts.append(
            "\n".join(
                [
                    f"[Chunk {index}]",
                    f"source: {payload.get('source')}",
                    f"path: {payload.get('source_path')}",
                    f"type: {payload.get('source_type')}",
                    f"group: {payload.get('source_group')}",
                    f"doc_type: {payload.get('doc_type')}",
                    f"authority: {payload.get('authority')}",
                    f"status: {payload.get('status')}",
                    f"is_overview: {payload.get('is_overview')}",
                    f"section_index: {payload.get('section_index')}",
                    f"section_path: {payload.get('section_path')}",
                    f"language: {payload.get('language')}",
                    f"namespace: {payload.get('namespace')}",
                    f"symbol_kind: {payload.get('symbol_kind')}",
                    f"symbol_name: {payload.get('symbol_name')}",
                    f"start_line: {payload.get('start_line')}",
                    f"end_line: {payload.get('end_line')}",
                    f"vector_score: {payload.get('vector_score')}",
                    f"hybrid_score: {payload.get('hybrid_score')}",
                    f"rerank_score: {payload.get('rerank_score')}",
                    "text:",
                    payload.get("text") or "",
                ]
            )
        )

    return "\n\n".join(context_parts)



def main() -> None:
    args = parse_args()
    question = args.question or input("Question: ")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Missing OPENAI_API_KEY. Add it to IceBot-Tools/rag/.env or current environment.")

    llm = OpenAI(api_key=api_key)

    results = retrieve_context(
        question,
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

    if not results:
        raise SystemExit("No matching context found.")

    context = format_context(results)

    vault_instruction = (
        "Vault chunks are draft/personal notes. Use them only as supporting context and clearly mention when an answer depends on them."
        if args.include_vault
        else "Only official project/backend docs were retrieved. Do not infer from Vault notes."
    )

    prompt = f"""
You answer questions about the IceBot project using only the retrieved context.

Rules:
- If the context does not contain the answer, say you do not know.
- Prefer official/current sources over draft, future, raw, learning, or rejected notes.
- Treat rejected notes as designs that should not be recommended.
- Cite source paths in the answer when making a concrete claim.
- {vault_instruction}

Context:
{context}

Question:
{question}
"""

    response = llm.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "user", "content": prompt},
        ],
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
