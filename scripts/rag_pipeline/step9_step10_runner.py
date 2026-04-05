#!/usr/bin/env python3
"""
Step 9 and Step 10 runner

Step 9:
- Call GPT with user query + retrieved RAG context + explicit instructions.

Step 10:
- Evaluate the generated response and print what should improve.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Ensure this script works when launched from project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Step 9 + Step 10 for RAG chatbot")
    parser.add_argument("--query", required=True, help="User question")
    parser.add_argument(
        "--style",
        default="informative",
        choices=["informative", "concise", "detailed", "academic"],
        help="Response style",
    )
    parser.add_argument("--mock", action="store_true", help="Use mock mode")
    parser.add_argument(
        "--save-json",
        default="",
        help="Optional output path to save full JSON result",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    import sys

    rag_dir = PROJECT_ROOT / "scripts" / "rag_pipeline"
    if str(rag_dir) not in sys.path:
        sys.path.insert(0, str(rag_dir))

    from chat_interface import ChatInterface  # noqa: E402

    print("=" * 72)
    print("STEP 9: CALL GPT WITH QUERY + RAG CONTEXT + INSTRUCTIONS")
    print("=" * 72)

    chat = ChatInterface(use_mock=args.mock)
    result = chat.get_response(args.query, style=args.style)

    if not result.get("success"):
        print("FAILED")
        print(result.get("error", "Unknown error"))
        return

    print("Query:", args.query)
    print("Model:", result.get("model", "N/A"))
    print("Retrieved sites:", ", ".join(result.get("retrieved_sites", [])) or "N/A")
    print("Response:\n")
    print(result.get("response", ""))

    print("\n" + "=" * 72)
    print("STEP 10: RESPONSE CHECK + IMPROVEMENT SUGGESTIONS")
    print("=" * 72)

    evaluation = result.get("evaluation", {})
    if not evaluation:
        print("No evaluation data available.")
    else:
        print("Quality score:", evaluation.get("overall_score", "N/A"))
        print("Quality rating:", evaluation.get("quality_rating", "N/A"))

        metrics = evaluation.get("metrics", {})
        print("Relevance:", metrics.get("relevance", {}).get("score", "N/A"))
        print("Grounding:", metrics.get("factual_grounding", {}).get("score", "N/A"))
        print("Completeness:", metrics.get("completeness", {}).get("score", "N/A"))

        recs = evaluation.get("recommendations", [])
        if recs:
            print("\nSuggested improvements:")
            for idx, rec in enumerate(recs[:5], start=1):
                print(f"{idx}. {rec}")
        else:
            print("\nNo improvements suggested. Response quality is acceptable.")

    if args.save_json:
        out_path = Path(args.save_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nSaved full result JSON to: {out_path}")


if __name__ == "__main__":
    main()
