"""Generate final synthetic travel QA dataset for Sri Lankan historical sites.

Uses:
- place dataset: data/processed/historical_sites_rag_ready.csv
- question templates: data/fine_tuning/sri_lanka_chatbot_travel_request_templates.csv

Outputs in data/fine_tuning/final/:
- final_sri_lanka_travel_qa_pairs.csv
- final_sri_lanka_travel_finetune_all.jsonl
- final_sri_lanka_travel_finetune_train.jsonl
- final_sri_lanka_travel_finetune_validation.jsonl
- final_sri_lanka_travel_finetune_summary.json
"""

from __future__ import annotations

import csv
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd


SYSTEM_PROMPT = (
    "You are a factual Sri Lanka historical travel assistant. "
    "Answer using only details available in the provided source context. "
    "If a detail is unavailable, clearly say it is not available in the dataset. "
    "Do not invent distances, timings, ticket prices, or weather claims."
)


@dataclass
class Place:
    site_name: str
    description: str
    archaeological_significance: str
    historical_period: str
    region_specific: str
    unesco_status: str
    url: str
    source: str
    location: str
    category: str
    inscription_year: str
    authority: str


def clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    text = re.sub(r"\s+", " ", text)
    return text


def first_sentence(text: str, max_chars: int = 360) -> str:
    text = clean_text(text)
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    sentence = parts[0].strip()
    if len(sentence) > max_chars:
        sentence = sentence[: max_chars - 3].rstrip() + "..."
    return sentence


def parse_admin(location: str, region_specific: str) -> Dict[str, str]:
    # Best-effort extraction from noisy fields.
    raw = " | ".join([x for x in [location, region_specific] if x])
    if not raw:
        return {"province": "", "district": "", "city": ""}

    tokens = [clean_text(x) for x in re.split(r"[|,;/]", raw) if clean_text(x)]
    province = ""
    district = ""
    city = ""

    for tok in tokens:
        low = tok.lower()
        if not province and "province" in low:
            province = tok
        elif not district and "district" in low:
            district = tok
        elif not city:
            city = tok

    if not city and tokens:
        city = tokens[0]

    return {"province": province, "district": district, "city": city}


def build_nearby_lookup(places: List[Place]) -> Dict[str, List[str]]:
    by_region: Dict[str, List[str]] = {}
    for p in places:
        key = clean_text(p.region_specific) or clean_text(p.location) or "unknown"
        by_region.setdefault(key.lower(), []).append(p.site_name)

    result: Dict[str, List[str]] = {}
    all_names = [p.site_name for p in places]
    for p in places:
        key = clean_text(p.region_specific) or clean_text(p.location) or "unknown"
        candidates = [x for x in by_region.get(key.lower(), []) if x != p.site_name]
        if len(candidates) < 3:
            fallback = [x for x in all_names if x != p.site_name and x not in candidates]
            candidates.extend(fallback[: 3 - len(candidates)])
        result[p.site_name] = candidates[:3]
    return result


def answer_for(category: str, place: Place, nearby: List[str], global_names: List[str]) -> str:
    desc = first_sentence(place.description)
    admin = parse_admin(place.location, place.region_specific)

    if category == "general_trip_planning":
        return (
            "Top historical places commonly listed in this dataset include: "
            + ", ".join(global_names[:8])
            + ". For the best season, exact monthly travel climate guidance is not consistently available in the dataset. "
            "A practical plan is 4 to 7 days for major cultural sites, depending on travel pace."
        )

    if category == "colombo_route":
        city = admin["city"] or place.location or "the site area"
        return (
            f"For {place.site_name}, transport can typically be planned from Colombo by private car, taxi, or public transport toward {city}. "
            "Exact km distance and exact travel time from Colombo are not available in the current dataset fields."
        )

    if category == "place_details":
        parts = []
        if desc:
            parts.append(desc)
        if place.historical_period:
            parts.append(f"Historical period: {place.historical_period}.")
        if place.archaeological_significance:
            parts.append(f"Significance: {place.archaeological_significance}.")
        if place.inscription_year:
            parts.append(f"Built/inscription year data: {place.inscription_year}.")
        if place.authority:
            parts.append(f"Associated authority/builder reference: {place.authority}.")
        if not parts:
            return (
                f"{place.site_name} is listed in the dataset, but detailed historical significance and builder/year details are limited."
            )
        return " ".join(parts)

    if category == "location_admin":
        province = admin["province"] or "Not available in dataset"
        district = admin["district"] or "Not available in dataset"
        city = admin["city"] or "Not available in dataset"
        return (
            f"Location details for {place.site_name}: Province: {province}; District: {district}; City/Town: {city}."
        )

    if category == "nearby_places":
        if nearby:
            return (
                f"Nearest/related places for planning around {place.site_name}: "
                + ", ".join(nearby)
                + ". Exact inter-site distance in km is not available in the dataset."
            )
        return f"Nearby place details for {place.site_name} are not available in the current dataset."

    if category == "timings_access":
        return (
            f"For {place.site_name}, opening/closing times, ticket requirements, and crowd levels are not consistently available in this dataset. "
            "You should verify current timings and entry rules with official tourism or site authorities before visiting."
        )

    if category == "season_weather":
        return (
            f"Seasonal weather details specific to {place.site_name} are not fully provided in this dataset. "
            "In general, travel suitability depends on regional monsoon patterns, so check a current weather forecast before travel."
        )

    if category == "logistics":
        city = admin["city"] or place.location or "the nearest town"
        return (
            f"For {place.site_name}, accommodation and transport are usually planned via {city}. "
            "Specific hotel lists and real-time transport schedules are not included in this dataset."
        )

    if category == "multi_site_planning":
        if nearby:
            return (
                f"A practical combined trip for {place.site_name} is to pair it with: "
                + ", ".join(nearby)
                + ". Start early from Colombo and confirm travel duration locally because exact times are not provided in the dataset."
            )
        return (
            f"A combined itinerary can include {place.site_name} with other nearby historical sites, "
            "but exact route optimization data is limited in this dataset."
        )

    return f"{place.site_name} is available in the Sri Lankan historical sites dataset."


def load_places(path: Path) -> List[Place]:
    df = pd.read_csv(path).fillna("")
    places: List[Place] = []
    for _, row in df.iterrows():
        places.append(
            Place(
                site_name=clean_text(row.get("site_name")) or "Unknown Site",
                description=clean_text(row.get("description")),
                archaeological_significance=clean_text(row.get("archaeological_significance")),
                historical_period=clean_text(row.get("historical_period")),
                region_specific=clean_text(row.get("region_specific")),
                unesco_status=clean_text(row.get("unesco_status")),
                url=clean_text(row.get("url")),
                source=clean_text(row.get("source")),
                location=clean_text(row.get("location")),
                category=clean_text(row.get("category")),
                inscription_year=clean_text(row.get("inscription_year")),
                authority=clean_text(row.get("authority")),
            )
        )
    return places


def load_templates(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [
            {
                "id": clean_text(r.get("id")),
                "category": clean_text(r.get("category")),
                "query": clean_text(r.get("query")),
            }
            for r in reader
        ]


def write_jsonl(path: Path, rows: List[Dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps({"messages": row["messages"]}, ensure_ascii=False) + "\n")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    place_path = repo_root / "data" / "processed" / "historical_sites_rag_ready.csv"
    template_path = repo_root / "data" / "fine_tuning" / "sri_lanka_chatbot_travel_request_templates.csv"
    out_dir = repo_root / "data" / "fine_tuning" / "final"
    out_dir.mkdir(parents=True, exist_ok=True)

    places = load_places(place_path)
    templates = load_templates(template_path)

    nearby_lookup = build_nearby_lookup(places)
    global_names = [p.site_name for p in places]

    qa_rows: List[Dict[str, object]] = []

    for place in places:
        for t in templates:
            query = t["query"].replace("{place_name}", place.site_name)
            answer = answer_for(t["category"], place, nearby_lookup.get(place.site_name, []), global_names)

            qa_rows.append(
                {
                    "site_name": place.site_name,
                    "template_id": t["id"],
                    "category": t["category"],
                    "question": query,
                    "answer": answer,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": query},
                        {"role": "assistant", "content": answer},
                    ],
                }
            )

    random.seed(42)
    shuffled = qa_rows[:]
    random.shuffle(shuffled)
    val_size = int(len(shuffled) * 0.05)
    val = shuffled[:val_size]
    train = shuffled[val_size:]

    qa_csv = out_dir / "final_sri_lanka_travel_qa_pairs.csv"
    all_jsonl = out_dir / "final_sri_lanka_travel_finetune_all.jsonl"
    train_jsonl = out_dir / "final_sri_lanka_travel_finetune_train.jsonl"
    val_jsonl = out_dir / "final_sri_lanka_travel_finetune_validation.jsonl"
    summary_json = out_dir / "final_sri_lanka_travel_finetune_summary.json"

    with qa_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["site_name", "template_id", "category", "question", "answer"],
        )
        writer.writeheader()
        for row in qa_rows:
            writer.writerow({k: row[k] for k in ["site_name", "template_id", "category", "question", "answer"]})

    write_jsonl(all_jsonl, qa_rows)
    write_jsonl(train_jsonl, train)
    write_jsonl(val_jsonl, val)

    summary = {
        "places": len(places),
        "templates_per_place": len(templates),
        "total_examples": len(qa_rows),
        "train_examples": len(train),
        "validation_examples": len(val),
        "validation_ratio": 0.05,
        "outputs": {
            "qa_csv": str(qa_csv),
            "all_jsonl": str(all_jsonl),
            "train_jsonl": str(train_jsonl),
            "validation_jsonl": str(val_jsonl),
        },
    }

    with summary_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
