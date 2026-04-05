"""Generate synthetic fine-tuning data for Sri Lankan historical sites.

Outputs Azure OpenAI chat fine-tuning JSONL files and a QA pair CSV.
Supports:
- basic profile (single-turn)
- advanced profile (higher linguistic variation + multi-turn dialogues)
"""

import argparse
import csv
import json
import random
import re
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


SYSTEM_PROMPT = (
    "You are a factual assistant for Sri Lankan historical places. "
    "Answer using only verified details from the provided training context. "
    "If a detail is not available, clearly state that it is not available in the source data. "
    "Do not invent dates, locations, or claims."
)

INTENT_TEMPLATES: Dict[str, List[str]] = {
    "overview": [
        "Tell me about {site_name}.",
        "Give me an overview of {site_name}.",
        "What is {site_name} known for?",
        "Can you describe {site_name}?",
        "Why is {site_name} important in Sri Lanka?",
    ],
    "historical_period": [
        "Which historical period is {site_name} associated with?",
        "What era does {site_name} belong to?",
        "When was {site_name} historically significant?",
        "Is {site_name} linked to an ancient, medieval, or modern period?",
        "What does the data say about the historical period of {site_name}?",
    ],
    "archaeological_significance": [
        "What is the archaeological significance of {site_name}?",
        "Why do archaeologists care about {site_name}?",
        "What archaeological value does {site_name} have?",
        "Explain the archaeological importance of {site_name}.",
        "What evidence makes {site_name} historically meaningful?",
    ],
    "location": [
        "Where is {site_name} located?",
        "Which area of Sri Lanka is {site_name} in?",
        "Can you tell me the location details of {site_name}?",
        "What region is connected to {site_name}?",
        "Do we have location information for {site_name}?",
    ],
    "unesco": [
        "Is {site_name} a UNESCO World Heritage Site?",
        "What is the UNESCO status of {site_name}?",
        "Does {site_name} have UNESCO recognition?",
        "How is {site_name} classified in UNESCO terms?",
        "What does the dataset say about UNESCO status for {site_name}?",
    ],
    "travel_context": [
        "Why should someone interested in heritage visit {site_name}?",
        "What makes {site_name} culturally valuable for visitors?",
        "How can {site_name} be described for educational tourism?",
        "What heritage aspects of {site_name} should visitors know?",
        "What are the key cultural highlights of {site_name}?",
    ],
    "source_confidence": [
        "What source information is available for {site_name}?",
        "Which reference URL is recorded for {site_name}?",
        "How well is {site_name} covered by sources in this dataset?",
        "Do we have a preferred source for {site_name}?",
        "What is the source confidence context for {site_name}?",
    ],
    "quick_facts": [
        "Give me quick facts about {site_name}.",
        "Summarize {site_name} in a few factual points.",
        "What are the most important facts about {site_name}?",
        "Provide a concise factual summary of {site_name}.",
        "List essential details about {site_name}.",
    ],
    "missing_info": [
        "What key information is missing for {site_name}?",
        "Are there any data gaps for {site_name}?",
        "Which fields are unavailable for {site_name}?",
        "What can we not confirm about {site_name} from this dataset?",
        "Does {site_name} have incomplete records?",
    ],
    "comparative_context": [
        "How can {site_name} be positioned among Sri Lankan heritage places?",
        "In dataset terms, how is {site_name} categorized?",
        "What category context is available for {site_name}?",
        "How does {site_name} fit into historical-site records?",
        "What structured metadata describes {site_name}?",
    ],
}

STYLE_PREFIXES = [
    "In a research tone, ",
    "For a travel-education audience, ",
    "Using concise factual language, ",
    "For a student assignment, ",
    "From a heritage documentation perspective, ",
]

STYLE_SUFFIXES = [
    " Please keep it factual.",
    " Keep the answer grounded in available data.",
    " Mention missing details explicitly if needed.",
    " Do not speculate.",
]

FOLLOW_UP_TEMPLATES = [
    "Can you also mention its historical period?",
    "Do we have UNESCO status information as well?",
    "Can you add location details if available?",
    "What source confidence details do we have for this site?",
    "Can you summarize key missing fields too?",
]


def clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    if text.lower() == "nan":
        return ""
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def first_sentences(text: str, max_sentences: int = 2, max_chars: int = 480) -> str:
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    picked = " ".join(parts[:max_sentences]).strip()
    if len(picked) > max_chars:
        picked = picked[: max_chars - 1].rstrip() + "..."
    return picked


def build_context(row: Dict[str, object]) -> Dict[str, str]:
    site_name = clean_text(row.get("site_name")) or "Unknown Site"
    preferred_desc = clean_text(row.get("preferred_description"))
    description = clean_text(row.get("description"))
    archaeological_significance = clean_text(row.get("archaeological_significance"))
    historical_period = clean_text(row.get("historical_period"))
    region_specific = clean_text(row.get("region_specific"))
    location = clean_text(row.get("location"))
    unesco_status = clean_text(row.get("unesco_status"))
    category = clean_text(row.get("category"))
    source = clean_text(row.get("source"))
    preferred_url = clean_text(row.get("preferred_source_url"))
    sources_found = clean_text(row.get("sources_found"))
    source_coverage_count = clean_text(row.get("source_coverage_count"))

    overview_source = preferred_desc or description
    overview = first_sentences(overview_source, max_sentences=2)

    return {
        "site_name": site_name,
        "overview": overview,
        "archaeological_significance": archaeological_significance,
        "historical_period": historical_period,
        "region_specific": region_specific,
        "location": location,
        "unesco_status": unesco_status,
        "category": category,
        "source": source,
        "preferred_url": preferred_url,
        "sources_found": sources_found,
        "source_coverage_count": source_coverage_count,
    }


def answer_for_intent(intent: str, context: Dict[str, str]) -> str:
    site = context["site_name"]

    if intent == "overview":
        if context["overview"]:
            return f"{site}: {context['overview']}"
        return f"The dataset lists {site}, but a descriptive overview is not available in the current records."

    if intent == "historical_period":
        if context["historical_period"]:
            return f"{site} is associated with the historical period: {context['historical_period']}."
        return f"The historical period for {site} is not explicitly available in the dataset."

    if intent == "archaeological_significance":
        if context["archaeological_significance"]:
            return f"Archaeological significance of {site}: {context['archaeological_significance']}"
        return f"The dataset does not provide a specific archaeological-significance note for {site}."

    if intent == "location":
        location_bits = [x for x in [context["location"], context["region_specific"]] if x]
        if location_bits:
            return f"Location context for {site}: " + " | ".join(location_bits)
        return f"Precise location details for {site} are not available in the current dataset fields."

    if intent == "unesco":
        if context["unesco_status"]:
            return f"UNESCO status for {site}: {context['unesco_status']}."
        return f"UNESCO status for {site} is not recorded in the dataset."

    if intent == "travel_context":
        base = context["overview"] or "It is listed as a historical place in Sri Lanka."
        return (
            f"For heritage-focused visitors, {site} is relevant because {base} "
            "Visitors should treat this as a factual summary from dataset records and verify travel logistics separately."
        )

    if intent == "source_confidence":
        parts = []
        if context["source"]:
            parts.append(f"source label: {context['source']}")
        if context["sources_found"]:
            parts.append(f"sources found: {context['sources_found']}")
        if context["source_coverage_count"]:
            parts.append(f"source coverage count: {context['source_coverage_count']}")
        if context["preferred_url"]:
            parts.append(f"preferred URL: {context['preferred_url']}")
        if parts:
            return f"Source context for {site}: " + "; ".join(parts) + "."
        return f"Detailed source-confidence metadata is limited for {site} in the dataset."

    if intent == "quick_facts":
        facts = [
            f"Site: {site}",
            f"Historical period: {context['historical_period'] or 'Not specified'}",
            f"UNESCO status: {context['unesco_status'] or 'Not specified'}",
            f"Category: {context['category'] or 'Not specified'}",
        ]
        if context["location"] or context["region_specific"]:
            facts.append(f"Location: {context['location'] or context['region_specific']}")
        return " | ".join(facts)

    if intent == "missing_info":
        missing = []
        for field in ["historical_period", "archaeological_significance", "location", "region_specific", "category"]:
            if not context[field]:
                missing.append(field)
        if missing:
            return f"For {site}, the dataset is missing or sparse in these fields: {', '.join(missing)}."
        return f"For {site}, key structured fields are largely populated in the current dataset."

    if intent == "comparative_context":
        parts = []
        if context["category"]:
            parts.append(f"category: {context['category']}")
        if context["historical_period"]:
            parts.append(f"period: {context['historical_period']}")
        if context["unesco_status"]:
            parts.append(f"UNESCO: {context['unesco_status']}")
        if context["source"]:
            parts.append(f"source label: {context['source']}")
        if parts:
            return f"Dataset positioning for {site}: " + "; ".join(parts) + "."
        return f"{site} is present in the dataset, but comparative metadata is limited."

    return f"{site} is present in the Sri Lankan historical places dataset."


def build_single_turn_examples(context: Dict[str, str], advanced: bool) -> List[Dict[str, object]]:
    site_name = context["site_name"]
    examples: List[Dict[str, object]] = []

    for intent, templates in INTENT_TEMPLATES.items():
        answer = answer_for_intent(intent, context)
        for q in templates:
            variants = [q.format(site_name=site_name)]
            if advanced:
                for prefix in STYLE_PREFIXES:
                    variants.append((prefix + q).format(site_name=site_name))
                for suffix in STYLE_SUFFIXES:
                    variants.append((q + suffix).format(site_name=site_name))

            for user_q in variants:
                examples.append(
                    {
                        "site_name": site_name,
                        "intent": intent,
                        "dialogue_type": "single_turn",
                        "question": user_q,
                        "answer": answer,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_q},
                            {"role": "assistant", "content": answer},
                        ],
                    }
                )

    return examples


def build_multi_turn_examples(context: Dict[str, str], count: int, seed: int) -> List[Dict[str, object]]:
    site_name = context["site_name"]
    rnd = random.Random(seed)
    intents = list(INTENT_TEMPLATES.keys())
    examples: List[Dict[str, object]] = []

    for _ in range(count):
        first_intent = rnd.choice(intents)
        second_intent = rnd.choice([i for i in intents if i != first_intent])

        first_q = rnd.choice(INTENT_TEMPLATES[first_intent]).format(site_name=site_name)
        first_a = answer_for_intent(first_intent, context)

        follow_up_q = rnd.choice(FOLLOW_UP_TEMPLATES)
        second_a = answer_for_intent(second_intent, context)

        examples.append(
            {
                "site_name": site_name,
                "intent": f"{first_intent}_to_{second_intent}",
                "dialogue_type": "multi_turn",
                "question": first_q,
                "answer": second_a,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": first_q},
                    {"role": "assistant", "content": first_a},
                    {"role": "user", "content": follow_up_q},
                    {"role": "assistant", "content": second_a},
                ],
            }
        )

    return examples


def build_examples_for_site(row: Dict[str, object], profile: str, examples_per_site: int, seed: int) -> List[Dict[str, object]]:
    context = build_context(row)
    site_name = context["site_name"]
    advanced = profile == "advanced"

    single_turn = build_single_turn_examples(context, advanced=advanced)
    if not advanced:
        if examples_per_site <= len(single_turn):
            return single_turn[:examples_per_site]
        needed = examples_per_site - len(single_turn)
        extension = single_turn * ((needed // len(single_turn)) + 1)
        return single_turn + extension[:needed]

    multi_turn_target = max(10, int(examples_per_site * 0.2))
    multi_turn = build_multi_turn_examples(context, count=multi_turn_target * 2, seed=seed + hash(site_name) % 100000)

    candidate_pool = single_turn + multi_turn
    rnd = random.Random(seed + len(site_name))
    rnd.shuffle(candidate_pool)

    if examples_per_site <= len(candidate_pool):
        return candidate_pool[:examples_per_site]

    # If user requests very high counts, cycle candidates deterministically.
    needed = examples_per_site - len(candidate_pool)
    extension = candidate_pool * ((needed // len(candidate_pool)) + 1)
    return candidate_pool + extension[:needed]


def write_jsonl(path: Path, records: List[Dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps({"messages": rec["messages"]}, ensure_ascii=False) + "\n")


def write_pairs_csv(path: Path, records: List[Dict[str, object]]) -> None:
    fieldnames = ["site_name", "intent", "dialogue_type", "question", "answer"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow({k: rec[k] for k in fieldnames})


def split_train_validation(records: List[Dict[str, object]], validation_ratio: float, seed: int) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    rnd = random.Random(seed)
    shuffled = records[:]
    rnd.shuffle(shuffled)
    val_size = int(len(shuffled) * validation_ratio)
    val = shuffled[:val_size]
    train = shuffled[val_size:]
    return train, val


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic fine-tuning dataset for Sri Lankan historical places")
    parser.add_argument(
        "--input-csv",
        default="data/final/cleaned_main_dataset.csv",
        help="Input cleaned dataset CSV",
    )
    parser.add_argument(
        "--output-dir",
        default="data/fine_tuning",
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--validation-ratio",
        type=float,
        default=0.05,
        help="Validation split ratio",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible split",
    )
    parser.add_argument(
        "--profile",
        choices=["basic", "advanced"],
        default="basic",
        help="Generation profile. 'advanced' adds richer linguistic variation and multi-turn dialogues.",
    )
    parser.add_argument(
        "--examples-per-site",
        type=int,
        default=50,
        choices=[50, 100, 200],
        help="Target examples per site.",
    )
    args = parser.parse_args()

    input_csv = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_csv)
    df = df.fillna("")

    all_records: List[Dict[str, object]] = []
    for _, row in df.iterrows():
        all_records.extend(
            build_examples_for_site(
                row.to_dict(),
                profile=args.profile,
                examples_per_site=args.examples_per_site,
                seed=args.seed,
            )
        )

    train_records, val_records = split_train_validation(all_records, args.validation_ratio, args.seed)

    profile_tag = f"{args.profile}_{args.examples_per_site}"
    all_jsonl = output_dir / f"sri_lanka_historical_sites_finetune_all_{profile_tag}.jsonl"
    train_jsonl = output_dir / f"sri_lanka_historical_sites_finetune_train_{profile_tag}.jsonl"
    val_jsonl = output_dir / f"sri_lanka_historical_sites_finetune_validation_{profile_tag}.jsonl"
    pairs_csv = output_dir / f"sri_lanka_historical_sites_qa_pairs_{profile_tag}.csv"
    summary_json = output_dir / f"sri_lanka_historical_sites_finetune_summary_{profile_tag}.json"

    write_jsonl(all_jsonl, all_records)
    write_jsonl(train_jsonl, train_records)
    write_jsonl(val_jsonl, val_records)
    write_pairs_csv(pairs_csv, all_records)

    unique_sites = len(set(rec["site_name"] for rec in all_records))
    multi_turn_count = sum(1 for rec in all_records if rec.get("dialogue_type") == "multi_turn")
    summary = {
        "input_csv": str(input_csv),
        "profile": args.profile,
        "unique_sites": unique_sites,
        "examples_per_site": args.examples_per_site,
        "total_examples": len(all_records),
        "train_examples": len(train_records),
        "validation_examples": len(val_records),
        "validation_ratio": args.validation_ratio,
        "intent_count": len(INTENT_TEMPLATES),
        "multi_turn_examples": multi_turn_count,
        "format": "Azure OpenAI chat fine-tuning JSONL",
        "files": {
            "all_jsonl": str(all_jsonl),
            "train_jsonl": str(train_jsonl),
            "validation_jsonl": str(val_jsonl),
            "qa_pairs_csv": str(pairs_csv),
        },
    }

    with summary_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
