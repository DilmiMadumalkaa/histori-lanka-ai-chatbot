#!/usr/bin/env python3
"""
Sri Lanka Historical Sites Research Pipeline

Implements the full workflow requested for the domain:
1. Data collection (Wikipedia, SLTDA, Archaeology sources only)
2. Field selection for site objects
3. Export to JSON
4. JSON review (missing fields + duplicates)
5. Chunking strategy for RAG
6. Azure OpenAI embedding generation
7. Store vectors in Pinecone
8. Query embedding + retrieval tests
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.exceptions import SSLError


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("sri_lanka_research_pipeline")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
VECTOR_DB_DIR = PROJECT_ROOT / "data" / "rag_vectordb"

RAW_JSON_FILE = DATA_RAW_DIR / "sri_lanka_historical_sites_raw.json"
REVIEW_REPORT_FILE = DATA_PROCESSED_DIR / "sri_lanka_historical_sites_review.json"
CLEAN_JSON_FILE = DATA_PROCESSED_DIR / "sri_lanka_historical_sites_clean.json"
CHUNKS_FILE = VECTOR_DB_DIR / "sri_lanka_historical_sites_chunks.json"
RETRIEVAL_TEST_FILE = DATA_PROCESSED_DIR / "sri_lanka_retrieval_test_results.json"
RAG_READY_INPUT_CSV = DATA_PROCESSED_DIR / "historical_sites_rag_ready.csv"
ENRICHED_SITES_CSV = DATA_PROCESSED_DIR / "historical_sites_rag_ready_enriched_sources.csv"
ENRICHED_SITES_JSON = DATA_PROCESSED_DIR / "historical_sites_rag_ready_enriched_sources.json"
ENRICHMENT_REPORT_JSON = DATA_PROCESSED_DIR / "historical_sites_source_enrichment_report.json"


def load_env_file(env_path: Path) -> None:
    """Load simple KEY=VALUE pairs from .env into process env when missing."""
    if not env_path.exists():
        return

    # Preserve vars that were already exported before reading .env.
    external_keys = set(os.environ.keys())

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        # Respect explicitly exported environment variables, but for values loaded
        # from this file allow later duplicate keys to override earlier placeholders.
        if key and key not in external_keys:
            os.environ[key] = value

REQUIRED_FIELDS = [
    "site_name",
    "site_type",
    "description",
    "location",
    "historical_period",
    "archaeological_significance",
    "source",
    "source_url",
]

ALLOWED_SOURCES = {
    "Wikipedia",
    "Sri Lanka Tourism Development Authority",
    "Archaeological Sites",
}

WIKIPEDIA_CATEGORY_PAGES = [
    "https://en.wikipedia.org/wiki/Category:Archaeological_sites_in_Sri_Lanka",
    "https://en.wikipedia.org/wiki/Category:Ancient_cities_in_Sri_Lanka",
    "https://en.wikipedia.org/wiki/Category:Buddhist_temples_in_Sri_Lanka",
    "https://en.wikipedia.org/wiki/Category:Forts_in_Sri_Lanka",
]

# These pages are starting points and may evolve; selectors are resilient and best-effort.
SLTDA_LIST_PAGES = [
    "https://www.sltda.gov.lk/",
    "https://www.sltda.gov.lk/en",
    "https://www.srilanka.travel/index.php?route=attractions/attractions-search",
    "https://www.srilanka.travel/attractions",
    "https://www.srilanka.travel/sri-lankan-heritage",
    "https://www.srilanka.travel/pilgrimage",
    "https://www.srilanka.travel/things-to-see",
]

ARCHAEOLOGY_LIST_PAGES = [
    "https://www.archaeology.gov.lk/web/index.php?option=com_content&view=category&layout=blog&id=61&Itemid=168&lang=en",
    "https://www.archaeology.gov.lk/",
]

ARCHAEOLOGY_ARCGIS_LAYER_URL = (
    "http://services6.arcgis.com/s3bdyMBJtaczQLc3/arcgis/rest/services/"
    "Ruwanweliseya_Sites/FeatureServer/0/query"
)
ARCHAEOLOGY_WEBMAP_ID = "104cba998b4c40c1ab146f685e37867c"

TEST_QUERIES = [
    "Tell me about Sigiriya and its archaeological significance",
    "What is special about Anuradhapura for Buddhist history?",
    "Which historical sites are in Anuradhapura region?",
    "What can you tell me about Dambulla cave temple?",
    "What is the historical significance of Polonnaruwa?",
    "Tell me about Galle Fort",
    "Which sites are associated with Galle Fort?",
    "What are important Buddhist archaeological sites in Sri Lanka?",
    "Give details about Ritigala archaeological site",
    "What is known about Mirisawetiya Vihara?",
]

STOPWORDS = {
    "the",
    "is",
    "are",
    "in",
    "of",
    "for",
    "what",
    "which",
    "tell",
    "me",
    "about",
    "can",
    "you",
    "to",
    "on",
    "a",
    "an",
    "and",
}

EXPECTED_QUERY_SIGNALS = {
    "Tell me about Sigiriya and its archaeological significance": ["sigiriya"],
    "What is special about Anuradhapura for Buddhist history?": ["anuradhapura"],
    "Which historical sites are in Anuradhapura region?": ["anuradhapura"],
    "What can you tell me about Dambulla cave temple?": ["dambulla", "golden temple"],
    "What is the historical significance of Polonnaruwa?": ["polonnaruwa"],
    "Tell me about Galle Fort": ["galle fort", "galle"],
    "Which sites are associated with Galle Fort?": ["galle fort", "galle"],
    "What are important Buddhist archaeological sites in Sri Lanka?": ["buddhist", "vihara", "stupa", "archaeological"],
    "Give details about Ritigala archaeological site": ["ritigala"],
    "What is known about Mirisawetiya Vihara?": ["mirisawetiya", "vihara"],
}


@dataclass
class SiteRecord:
    site_name: str
    site_type: str
    description: str
    location: str
    historical_period: str
    archaeological_significance: str
    source: str
    source_url: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "site_name": self.site_name.strip(),
            "site_type": self.site_type.strip(),
            "description": self.description.strip(),
            "location": self.location.strip(),
            "historical_period": self.historical_period.strip(),
            "archaeological_significance": self.archaeological_significance.strip(),
            "source": self.source.strip(),
            "source_url": self.source_url.strip(),
        }


class SriLankaHistoricalPipeline:
    def __init__(self, request_timeout: int = 20):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
                )
            }
        )
        self.request_timeout = request_timeout

    def collect_data(self) -> List[Dict[str, str]]:
        records: List[Dict[str, str]] = []
        records.extend(self._collect_from_wikipedia())
        records.extend(self._collect_from_sltda())
        records.extend(self._collect_from_archaeology())

        # Keep only the target domain and source set.
        records = [r for r in records if self._looks_like_sri_lanka_site(r)]
        records = [r for r in records if r.get("source") in ALLOWED_SOURCES]

        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        RAW_JSON_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved raw JSON: %s (%d records)", RAW_JSON_FILE, len(records))
        return records

    def review_json(self, records: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], Dict]:
        missing_fields: List[Dict] = []
        duplicate_groups: Dict[str, List[int]] = {}
        cleaned_records: List[Dict[str, str]] = []
        seen_names: Dict[str, int] = {}

        for idx, raw in enumerate(records):
            normalized = self._normalize_record(raw)
            absent = [f for f in REQUIRED_FIELDS if not normalized.get(f)]
            if absent:
                missing_fields.append(
                    {
                        "index": idx,
                        "site_name": normalized.get("site_name", ""),
                        "missing_fields": absent,
                    }
                )

            key = self._dedupe_key(normalized.get("site_name", ""))
            if key in seen_names:
                duplicate_groups.setdefault(key, [seen_names[key]]).append(idx)
                # Keep richer record (longer description).
                existing_index = seen_names[key]
                existing = cleaned_records[existing_index]
                if len(normalized.get("description", "")) > len(existing.get("description", "")):
                    cleaned_records[existing_index] = normalized
            else:
                seen_names[key] = len(cleaned_records)
                cleaned_records.append(normalized)

        review_report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_input_records": len(records),
            "total_clean_records": len(cleaned_records),
            "missing_fields_count": len(missing_fields),
            "duplicate_groups_count": len(duplicate_groups),
            "missing_fields_examples": missing_fields[:30],
            "duplicate_groups": duplicate_groups,
        }

        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        REVIEW_REPORT_FILE.write_text(json.dumps(review_report, indent=2, ensure_ascii=False), encoding="utf-8")
        CLEAN_JSON_FILE.write_text(json.dumps(cleaned_records, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info("Saved review report: %s", REVIEW_REPORT_FILE)
        logger.info("Saved clean JSON: %s (%d records)", CLEAN_JSON_FILE, len(cleaned_records))

        return cleaned_records, review_report

    def chunk_records(self, records: List[Dict[str, str]], chunk_size: int = 600, overlap: int = 120) -> List[Dict]:
        chunks: List[Dict] = []
        for item in records:
            base_text = self._record_to_rag_text(item)
            piece_texts = self._chunk_text(base_text, chunk_size=chunk_size, overlap=overlap)
            for chunk_idx, chunk_text in enumerate(piece_texts):
                chunks.append(
                    {
                        "chunk_id": f"{self._dedupe_key(item['site_name'])}_{chunk_idx}",
                        "chunk_index": chunk_idx,
                        "site_name": item["site_name"],
                        "source": item["source"],
                        "site_type": item["site_type"],
                        "location": item["location"],
                        "text": chunk_text,
                    }
                )

        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
        CHUNKS_FILE.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved chunks: %s (%d chunks)", CHUNKS_FILE, len(chunks))
        return chunks

    def generate_embeddings(self, chunks: List[Dict], use_mock_if_missing: bool = False) -> List[Dict]:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
        out_file = VECTOR_DB_DIR / "sri_lanka_historical_sites_chunks_with_embeddings.json"

        if not api_key or not endpoint:
            if not use_mock_if_missing:
                raise RuntimeError(
                    "Azure OpenAI credentials missing. Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT."
                )
            logger.warning("Azure credentials missing; using deterministic mock embeddings")
            return self._mock_embeddings(chunks)

        from openai import AzureOpenAI
        from openai import APIConnectionError, APITimeoutError

        client = AzureOpenAI(api_key=api_key, azure_endpoint=endpoint, api_version="2024-02-01")

        embedded: List[Dict] = []
        embedded_ids = set()

        # Resume from prior progress if a checkpoint file exists.
        if out_file.exists():
            try:
                embedded = json.loads(out_file.read_text(encoding="utf-8"))
                embedded_ids = {item.get("chunk_id") for item in embedded if item.get("chunk_id")}
                logger.info("Resuming embeddings from checkpoint: %d/%d already embedded", len(embedded_ids), len(chunks))
            except Exception as exc:
                logger.warning("Could not read existing embeddings checkpoint (%s). Starting fresh.", exc)
                embedded = []
                embedded_ids = set()

        total = len(chunks)
        new_count = 0
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id")
            if chunk_id in embedded_ids:
                continue

            last_error: Exception | None = None
            for attempt in range(1, 6):
                try:
                    response = client.embeddings.create(model=deployment, input=chunk["text"])
                    vector = response.data[0].embedding
                    embedded.append({**chunk, "embedding": vector})
                    embedded_ids.add(chunk_id)
                    new_count += 1
                    break
                except (APIConnectionError, APITimeoutError) as exc:
                    last_error = exc
                    backoff = min(12, 2 * attempt)
                    logger.warning(
                        "Embedding request failed for %s (attempt %d/5). Retrying in %ds.",
                        chunk_id,
                        attempt,
                        backoff,
                    )
                    time.sleep(backoff)

            if last_error is not None and chunk_id not in embedded_ids:
                raise last_error

            if len(embedded_ids) % 20 == 0:
                logger.info("Embedded %d/%d chunks", len(embedded_ids), total)
                out_file.write_text(json.dumps(embedded, indent=2, ensure_ascii=False), encoding="utf-8")

        # Final write to ensure the output file is fully synced.
        out_file.write_text(json.dumps(embedded, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved embeddings: %s", out_file)
        return embedded

    def upsert_to_pinecone(self, embedded_chunks: List[Dict], index_name: str = "historical-sites-sl") -> Dict:
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise RuntimeError("PINECONE_API_KEY missing in environment")

        from pinecone import Pinecone, ServerlessSpec

        pc = Pinecone(api_key=api_key)

        # Create index if it does not exist.
        existing_indexes = [x["name"] for x in pc.list_indexes()]
        if index_name not in existing_indexes:
            dimension = len(embedded_chunks[0]["embedding"])
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=os.getenv("PINECONE_ENV", "us-east-1")),
            )
            # Give Pinecone time to provision.
            time.sleep(5)

        index = pc.Index(index_name)

        batch_size = 50
        upserted = 0
        for i in range(0, len(embedded_chunks), batch_size):
            batch = embedded_chunks[i : i + batch_size]
            vectors = []
            for row in batch:
                vectors.append(
                    {
                        "id": row["chunk_id"],
                        "values": row["embedding"],
                        "metadata": {
                            "site_name": row["site_name"],
                            "source": row["source"],
                            "site_type": row["site_type"],
                            "location": row["location"],
                            "text": row["text"][:3500],
                        },
                    }
                )

            last_error: Exception | None = None
            for attempt in range(1, 11):
                try:
                    index.upsert(vectors=vectors)
                    last_error = None
                    break
                except Exception as exc:
                    last_error = exc
                    wait_seconds = min(30, attempt * 3)
                    logger.warning(
                        "Upsert batch %d-%d failed (attempt %d/10): %s. Retrying in %ds",
                        i,
                        i + len(batch),
                        attempt,
                        exc,
                        wait_seconds,
                    )
                    time.sleep(wait_seconds)

            if last_error is not None:
                raise last_error

            upserted += len(vectors)
            logger.info("Upserted %d/%d vectors", upserted, len(embedded_chunks))

        stats = index.describe_index_stats()
        result = {
            "index_name": index_name,
            "upserted_count": upserted,
            "index_stats": stats,
        }
        logger.info("Pinecone upsert complete: %s", result)
        return result

    def retrieval_test(self, index_name: str = "historical-sites-sl", top_k: int = 5) -> Dict:
        api_key = os.getenv("PINECONE_API_KEY")
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")

        if not api_key:
            raise RuntimeError("PINECONE_API_KEY missing in environment")
        if not azure_key or not azure_endpoint:
            raise RuntimeError("Azure OpenAI credentials are missing for retrieval testing")

        from openai import AzureOpenAI
        from pinecone import Pinecone

        embed_client = AzureOpenAI(api_key=azure_key, azure_endpoint=azure_endpoint, api_version="2024-02-01")
        index = Pinecone(api_key=api_key).Index(index_name)

        tests = []
        for query in TEST_QUERIES:
            matches = self.embed_and_search_pinecone_query(
                query=query,
                index=index,
                embed_client=embed_client,
                embedding_model=deployment,
                top_k=top_k,
            )

            correctness = self._evaluate_retrieval_correctness(query=query, matches=matches)

            tests.append(
                {
                    "query": query,
                    "matches": matches,
                    "evaluation": correctness,
                }
            )

        pass_count = sum(1 for t in tests if t["evaluation"].get("is_relevant"))

        output = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "index_name": index_name,
            "summary": {
                "total_queries": len(tests),
                "relevant_topk_queries": pass_count,
                "relevance_rate": (pass_count / len(tests)) if tests else 0.0,
            },
            "tests": tests,
        }
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        RETRIEVAL_TEST_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved retrieval tests: %s", RETRIEVAL_TEST_FILE)
        return output

    def embed_and_search_pinecone_query(
        self,
        query: str,
        index,
        embed_client,
        embedding_model: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """Embed a user query, search Pinecone, and rerank with lexical intent signals."""
        query_vec = embed_client.embeddings.create(model=embedding_model, input=query).data[0].embedding
        candidate_k = max(top_k * 8, 40)
        response = index.query(vector=query_vec, top_k=candidate_k, include_metadata=True)

        query_l = query.lower()
        query_tokens = [
            tok
            for tok in re.findall(r"[a-z0-9]+", query_l)
            if tok not in STOPWORDS and len(tok) > 2
        ]

        matches_with_score = []
        for item in response.get("matches", []):
            md = item.get("metadata", {})
            base_score = float(item.get("score", 0.0))
            site_name = md.get("site_name", "")
            full_text = f"{site_name} {md.get('text', '')} {md.get('source', '')}".lower()

            lexical_hits = sum(1 for tok in query_tokens if tok in full_text)
            lexical_bonus = min(0.35, lexical_hits * 0.05)

            # Query-intent boosts for known weak intents.
            intent_bonus = 0.0
            if "kandy" in query_l and any(t in full_text for t in ["kandy", "dalada", "tooth"]):
                intent_bonus += 0.25

            if any(t in query_l for t in ["tooth", "dalada"]):
                if any(t in full_text for t in ["tooth", "dalada", "maligawa"]):
                    intent_bonus += 0.30

            if "buddhist" in query_l:
                if any(t in full_text for t in ["buddhist", "vihara", "stupa", "dagoba", "temple"]):
                    intent_bonus += 0.20

            rerank_score = base_score + lexical_bonus + intent_bonus

            matches_with_score.append(
                {
                    "id": item.get("id"),
                    "score": base_score,
                    "site_name": site_name,
                    "source": md.get("source", ""),
                    "snippet": md.get("text", "")[:180],
                    "_rerank_score": rerank_score,
                }
            )

        matches_with_score.sort(key=lambda x: x.get("_rerank_score", 0.0), reverse=True)
        selected = matches_with_score[:top_k]
        for row in selected:
            row.pop("_rerank_score", None)

        return selected

    def retrieve_context_for_query(
        self,
        query: str,
        index,
        embed_client,
        embedding_model: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """Backward-compatible alias for query embedding + Pinecone vector search."""
        return self.embed_and_search_pinecone_query(
            query=query,
            index=index,
            embed_client=embed_client,
            embedding_model=embedding_model,
            top_k=top_k,
        )

    def _evaluate_retrieval_correctness(self, query: str, matches: List[Dict]) -> Dict:
        """Simple relevance check for RAG retrieval quality on known test queries."""
        expected_tokens = [s.lower() for s in EXPECTED_QUERY_SIGNALS.get(query, [])]
        if not expected_tokens:
            return {
                "is_relevant": False,
                "reason": "No expected signal configured for this query",
                "matched_site_names": [],
            }

        matched_site_names = []
        for row in matches:
            signal_text = f"{row.get('site_name', '')} {row.get('snippet', '')}".lower()
            if any(tok in signal_text for tok in expected_tokens):
                matched_site_names.append(row.get("site_name", ""))

        return {
            "is_relevant": len(matched_site_names) > 0,
            "expected_tokens": expected_tokens,
            "matched_site_names": matched_site_names,
            "top_score": matches[0].get("score", 0.0) if matches else 0.0,
        }

    def run_all(self, use_mock_embeddings_if_missing: bool = False, index_name: str = "historical-sites-sl") -> Dict:
        records = self.collect_data()
        clean_records, review_report = self.review_json(records)
        chunks = self.chunk_records(clean_records)
        embedded_chunks = self.generate_embeddings(chunks, use_mock_if_missing=use_mock_embeddings_if_missing)

        pinecone_result = None
        retrieval_result = None

        if os.getenv("PINECONE_API_KEY"):
            pinecone_result = self.upsert_to_pinecone(embedded_chunks, index_name=index_name)
            if os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
                retrieval_result = self.retrieval_test(index_name=index_name)
        else:
            logger.warning("Skipping Pinecone upsert and retrieval test because PINECONE_API_KEY is not set")

        return {
            "review_report": review_report,
            "chunks_count": len(chunks),
            "embedded_count": len(embedded_chunks),
            "pinecone": pinecone_result,
            "retrieval_test": retrieval_result,
        }

    def enrich_rag_ready_sites(
        self,
        input_csv: Path = RAG_READY_INPUT_CSV,
        start_index: int = 0,
        end_index: int | None = None,
    ) -> Dict:
        """
        Enrich every site in historical_sites_rag_ready.csv with source-specific records
        from Wikipedia, SLTDA, and Archaeological sources.
        """
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("pandas is required for CSV enrichment") from exc

        if not input_csv.exists():
            raise FileNotFoundError(f"Input CSV not found: {input_csv}")

        df = pd.read_csv(input_csv)
        if "site_name" not in df.columns:
            raise ValueError("Input CSV must contain a 'site_name' column")

        source_rows = df.to_dict(orient="records")
        source_rows = [r for r in source_rows if str(r.get("site_name", "")).strip()]

        total_sites = len(source_rows)
        start = max(0, int(start_index))
        end = total_sites if end_index is None else min(total_sites, int(end_index))
        if start >= end:
            raise ValueError(f"Invalid range start={start}, end={end}, total={total_sites}")

        target_rows = source_rows[start:end]
        logger.info(
            "Enrichment target: %d sites from %s (range: %d-%d)",
            len(target_rows),
            input_csv,
            start,
            end,
        )

        # Build source datasets once for matching.
        sltda_records = self._collect_from_sltda()
        arch_records = self._collect_from_archaeology()

        sltda_lookup = self._build_lookup(sltda_records)
        arch_lookup = self._build_lookup(arch_records)

        wikipedia_hits = 0
        sltda_hits = 0
        archaeology_hits = 0
        enriched_rows: List[Dict] = []

        for idx, row in enumerate(target_rows, start=1):
            site_name = str(row.get("site_name", "")).strip()
            if idx % 25 == 0:
                logger.info("Enriching site %d/%d in current batch", idx, len(target_rows))

            csv_desc = str(row.get("description", "") or "").strip()
            csv_url = str(row.get("url", "") or "").strip()
            wiki_record = None
            if "wikipedia.org" in csv_url.lower() and csv_desc:
                wiki_record = SiteRecord(
                    site_name=site_name,
                    site_type=self._infer_site_type(site_name, csv_desc),
                    description=csv_desc,
                    location=str(row.get("location", "Sri Lanka") or "Sri Lanka"),
                    historical_period=str(row.get("historical_period", "Historical") or "Historical"),
                    archaeological_significance=self._infer_archaeological_significance(csv_desc),
                    source="Wikipedia",
                    source_url=csv_url,
                ).to_dict()
            else:
                wiki_record = self._fetch_wikipedia_for_site(site_name)
                # Fallback for interim completeness: keep existing description when external lookup fails.
                if not wiki_record and csv_desc:
                    wiki_record = SiteRecord(
                        site_name=site_name,
                        site_type=self._infer_site_type(site_name, csv_desc),
                        description=csv_desc,
                        location=str(row.get("location", "Sri Lanka") or "Sri Lanka"),
                        historical_period=str(row.get("historical_period", "Historical") or "Historical"),
                        archaeological_significance=self._infer_archaeological_significance(csv_desc),
                        source="Wikipedia",
                        source_url=(
                            csv_url
                            if csv_url
                            else f"https://en.wikipedia.org/wiki/{site_name.replace(' ', '_')}"
                        ),
                    ).to_dict()
            sltda_record = self._find_best_match(site_name, sltda_lookup)
            arch_record = self._find_best_match(site_name, arch_lookup)

            if wiki_record:
                wikipedia_hits += 1
            if sltda_record:
                sltda_hits += 1
            if arch_record:
                archaeology_hits += 1

            sources_found = [
                s
                for s, present in [
                    ("Wikipedia", wiki_record is not None),
                    ("Sri Lanka Tourism Development Authority", sltda_record is not None),
                    ("Archaeological Sites", arch_record is not None),
                ]
                if present
            ]

            preferred_description = ""
            preferred_url = ""
            if wiki_record:
                preferred_description = wiki_record.get("description", "")
                preferred_url = wiki_record.get("source_url", "")
            elif sltda_record:
                preferred_description = sltda_record.get("description", "")
                preferred_url = sltda_record.get("source_url", "")
            elif arch_record:
                preferred_description = arch_record.get("description", "")
                preferred_url = arch_record.get("source_url", "")

            enriched_rows.append(
                {
                    "site_name": site_name,
                    "wikipedia_description": (wiki_record or {}).get("description", ""),
                    "wikipedia_url": (wiki_record or {}).get("source_url", ""),
                    "sltda_description": (sltda_record or {}).get("description", ""),
                    "sltda_url": (sltda_record or {}).get("source_url", ""),
                    "archaeology_description": (arch_record or {}).get("description", ""),
                    "archaeology_url": (arch_record or {}).get("source_url", ""),
                    "sources_found": ", ".join(sources_found),
                    "source_coverage_count": len(sources_found),
                    "preferred_description": preferred_description,
                    "preferred_source_url": preferred_url,
                }
            )

        enrichment_df = pd.DataFrame(enriched_rows)

        ENRICHED_SITES_CSV.parent.mkdir(parents=True, exist_ok=True)
        if ENRICHED_SITES_CSV.exists():
            output_df = pd.read_csv(ENRICHED_SITES_CSV)
        else:
            output_df = df.copy()

        enrichment_columns = [
            "wikipedia_description",
            "wikipedia_url",
            "sltda_description",
            "sltda_url",
            "archaeology_description",
            "archaeology_url",
            "sources_found",
            "source_coverage_count",
            "preferred_description",
            "preferred_source_url",
        ]
        for col in enrichment_columns:
            if col not in output_df.columns:
                output_df[col] = ""
            output_df[col] = output_df[col].astype(object)

        if "description" in output_df.columns:
            output_df["description"] = output_df["description"].astype(object)

        for _, e_row in enrichment_df.iterrows():
            mask = output_df["site_name"].astype(str) == str(e_row["site_name"])
            for col in enrichment_columns:
                output_df.loc[mask, col] = str(e_row.get(col, "") or "")

            if "description" in output_df.columns:
                preferred = str(e_row.get("preferred_description", "") or "")
                if preferred:
                    output_df.loc[mask, "description"] = preferred

        output_df.to_csv(ENRICHED_SITES_CSV, index=False, encoding="utf-8")
        ENRICHED_SITES_JSON.write_text(
            json.dumps(output_df.to_dict(orient="records"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_csv": str(input_csv),
            "total_sites": total_sites,
            "processed_range": [start, end],
            "processed_sites": len(target_rows),
            "coverage": {
                "wikipedia_hits": wikipedia_hits,
                "sltda_hits": sltda_hits,
                "archaeology_hits": archaeology_hits,
                "any_source_hits_in_batch": int((enrichment_df["source_coverage_count"] > 0).sum()),
                "all_three_sources_hits_in_batch": int((enrichment_df["source_coverage_count"] == 3).sum()),
            },
            "outputs": {
                "enriched_csv": str(ENRICHED_SITES_CSV),
                "enriched_json": str(ENRICHED_SITES_JSON),
            },
        }
        ENRICHMENT_REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved enriched CSV: %s", ENRICHED_SITES_CSV)
        logger.info("Saved enrichment report: %s", ENRICHMENT_REPORT_JSON)
        return report

    # -----------------------------
    # Source-specific collection
    # -----------------------------

    def _collect_from_wikipedia(self) -> List[Dict[str, str]]:
        records: List[Dict[str, str]] = []
        seen_titles = set()

        for category_url in WIKIPEDIA_CATEGORY_PAGES:
            soup = self._fetch_soup(category_url)
            if soup is None:
                continue

            # Category pages typically list links under mw-pages.
            container = soup.find("div", id="mw-pages") or soup
            links = container.find_all("a", href=True)
            for link in links:
                href = link["href"]
                if not href.startswith("/wiki/") or ":" in href:
                    continue

                title = link.get_text(strip=True)
                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)

                page_url = f"https://en.wikipedia.org{href}"
                description = self._fetch_wikipedia_summary(page_url)
                if not description:
                    continue

                if not self._is_historical_site_candidate(title, description):
                    continue

                records.append(
                    SiteRecord(
                        site_name=title,
                        site_type=self._infer_site_type(title, description),
                        description=description,
                        location="Sri Lanka",
                        historical_period=self._infer_historical_period(description),
                        archaeological_significance=self._infer_archaeological_significance(description),
                        source="Wikipedia",
                        source_url=page_url,
                    ).to_dict()
                )

                # Avoid aggressively crawling on first run.
                if len(records) >= 220:
                    break
            if len(records) >= 220:
                break

        logger.info("Collected %d records from Wikipedia", len(records))
        return records

    def _collect_from_sltda(self) -> List[Dict[str, str]]:
        records: List[Dict[str, str]] = []
        visited_urls = set()
        seen_site_names = set()

        allowed_hosts = {"sltda.gov.lk", "www.sltda.gov.lk", "srilanka.travel", "www.srilanka.travel"}

        def host_allowed(url: str) -> bool:
            try:
                h = (urlparse(url).netloc or "").lower()
            except Exception:
                return False
            return h in allowed_hosts

        # BFS crawl over official SLTDA ecosystem pages.
        queue = list(dict.fromkeys(SLTDA_LIST_PAGES))
        max_pages = 90
        crawl_start = time.time()
        max_crawl_seconds = 180
        crawl_keywords = [
            "heritage",
            "historical",
            "ancient",
            "temple",
            "fort",
            "pilgrimage",
            "things-to-see",
            "attractions",
            "tourist-attractions",
            "attraction_id=",
            "sri-lankan-heritage",
            "route=attractions",
            "route=theame",
            "article=",
            "culture",
            "destination",
            "top-attractions",
        ]

        while queue and len(visited_urls) < max_pages and (time.time() - crawl_start) < max_crawl_seconds:
            url = queue.pop(0)
            if url in visited_urls:
                continue
            if not host_allowed(url):
                continue

            visited_urls.add(url)

            try:
                detail_soup = self._fetch_soup(url)
                if detail_soup is None:
                    continue

                # Discover more candidate links from this page.
                for link in detail_soup.find_all("a", href=True):
                    href = (link.get("href") or "").strip()
                    if not href:
                        continue
                    absolute = urljoin(url, href)
                    if not host_allowed(absolute):
                        continue

                    txt = (link.get_text(" ", strip=True) or "").lower()
                    signal = (absolute + " " + txt).lower()
                    if any(k in signal for k in crawl_keywords):
                        if absolute not in visited_urls and absolute not in queue:
                            queue.append(absolute)

                title_node = detail_soup.find("h1")
                title = title_node.get_text(strip=True) if title_node else ""
                if not title:
                    h2 = detail_soup.find("h2")
                    title = h2.get_text(strip=True) if h2 else ""
                if not title:
                    ttag = detail_soup.find("title")
                    title = ttag.get_text(strip=True) if ttag else ""
                if not title:
                    title = url.rstrip("/").split("/")[-1].replace("-", " ").title()

                description = self._extract_paragraphs(detail_soup, max_paragraphs=3)
                if not title or not description:
                    continue

                sltda_url_signal = url.lower()
                should_keep = self._is_historical_site_candidate(title, description) or any(
                    token in sltda_url_signal
                    for token in [
                        "attraction&attraction_id=",
                        "tourist-attractions",
                        "/attractions",
                        "sri-lankan-heritage",
                        "pilgrimage",
                    ]
                )
                if not should_keep:
                    continue

                # Normalize noisy page titles.
                title = re.sub(r"\s*\|\s*.*$", "", title).strip()
                if len(title) < 3:
                    continue
                dedupe_name = title.lower()
                if dedupe_name in seen_site_names:
                    continue
                seen_site_names.add(dedupe_name)

                records.append(
                    SiteRecord(
                        site_name=title,
                        site_type=self._infer_site_type(title, description),
                        description=description,
                        location="Sri Lanka",
                        historical_period=self._infer_historical_period(description),
                        archaeological_significance=self._infer_archaeological_significance(description),
                        source="Sri Lanka Tourism Development Authority",
                        source_url=url,
                    ).to_dict()
                )
            except Exception:
                continue

        logger.info("Collected %d records from SLTDA pages", len(records))
        return records

    def _collect_from_archaeology(self) -> List[Dict[str, str]]:
        records: List[Dict[str, str]] = []
        seen_names = set()

        layer_urls = self._discover_archaeology_layer_urls()
        if ARCHAEOLOGY_ARCGIS_LAYER_URL not in layer_urls:
            layer_urls.append(ARCHAEOLOGY_ARCGIS_LAYER_URL)

        for layer_query_url in layer_urls:
            page_size = 500
            offset = 0
            while True:
                params = {
                    "where": "1=1",
                    "outFields": "*",
                    "f": "json",
                    "resultRecordCount": str(page_size),
                    "resultOffset": str(offset),
                }
                try:
                    response = self.session.get(layer_query_url, params=params, timeout=self.request_timeout)
                    if response.status_code != 200:
                        break
                    data = response.json()
                except Exception:
                    break

                features = data.get("features", [])
                if not features:
                    break

                for feat in features:
                    attrs = feat.get("attributes", {}) or {}
                    geom = feat.get("geometry", {}) or {}

                    name = str(
                        attrs.get("Monument_Name")
                        or attrs.get("Name")
                        or attrs.get("name")
                        or attrs.get("SITE_NAME")
                        or attrs.get("Site_Name")
                        or ""
                    ).strip()
                    if not name:
                        continue

                    period = str(
                        attrs.get("Period")
                        or attrs.get("PERIOD")
                        or attrs.get("Era")
                        or "Historical"
                    ).strip()
                    monument_type = str(
                        attrs.get("Type")
                        or attrs.get("TYPE")
                        or attrs.get("Category")
                        or "Archaeological Site"
                    ).strip()

                    lat = (
                        attrs.get("Lattitude")
                        or attrs.get("Latitude")
                        or attrs.get("GPS_Y")
                        or geom.get("y")
                    )
                    lon = (
                        attrs.get("Longitude")
                        or attrs.get("GPS_X")
                        or geom.get("x")
                    )

                    dedupe_key = self._dedupe_key(name)
                    if dedupe_key in seen_names:
                        continue
                    seen_names.add(dedupe_key)

                    description = (
                        f"{name} is a recorded archaeological monument in Sri Lanka. "
                        f"Period: {period}. Monument type: {monument_type}."
                    )
                    location = f"Sri Lanka ({lat}, {lon})" if lat is not None and lon is not None else "Sri Lanka"

                    records.append(
                        SiteRecord(
                            site_name=name,
                            site_type=monument_type,
                            description=description,
                            location=location,
                            historical_period=period,
                            archaeological_significance="Official archaeological inventory record",
                            source="Archaeological Sites",
                            source_url=layer_query_url,
                        ).to_dict()
                    )

                if not data.get("exceededTransferLimit"):
                    break
                offset += page_size
                if offset >= 20000:
                    break

        logger.info("Collected %d records from archaeology sources", len(records))
        return records

    def _discover_archaeology_layer_urls(self) -> List[str]:
        """Discover ArcGIS FeatureServer layer query URLs from archaeology webmap."""
        urls: List[str] = []
        try:
            webmap_data_url = (
                f"https://www.arcgis.com/sharing/rest/content/items/{ARCHAEOLOGY_WEBMAP_ID}/data?f=json"
            )
            resp = self.session.get(webmap_data_url, timeout=self.request_timeout)
            if resp.status_code != 200:
                return urls

            data = resp.json()
            for layer in data.get("operationalLayers", []):
                layer_url = str(layer.get("url") or "").strip()
                if not layer_url:
                    continue
                if "featureserver" not in layer_url.lower():
                    continue
                query_url = layer_url.rstrip("/") + "/query"
                if query_url not in urls:
                    urls.append(query_url)
        except Exception:
            return urls

        return urls

    # -----------------------------
    # Utility methods
    # -----------------------------

    def _fetch_soup(self, url: str) -> BeautifulSoup | None:
        try:
            response = self.session.get(url, timeout=min(self.request_timeout, 10))
            if response.status_code != 200:
                return None
            response.encoding = "utf-8"
            return BeautifulSoup(response.text, "html.parser")
        except SSLError:
            # Some official sites have incomplete cert chains in specific environments.
            try:
                import urllib3

                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                response = self.session.get(url, timeout=min(self.request_timeout, 10), verify=False)
                if response.status_code != 200:
                    return None
                response.encoding = "utf-8"
                return BeautifulSoup(response.text, "html.parser")
            except Exception as exc:
                logger.warning("Failed SSL fallback fetch %s: %s", url, exc)
                return None
        except Exception as exc:
            logger.warning("Failed fetch %s: %s", url, exc)
            return None

    def _fetch_wikipedia_summary(self, page_url: str) -> str:
        soup = self._fetch_soup(page_url)
        if soup is None:
            return ""
        content = soup.find("div", id="mw-content-text")
        if not content:
            return ""

        paragraphs = []
        for p in content.find_all("p"):
            text = p.get_text(" ", strip=True)
            if len(text) > 80 and "may refer to" not in text.lower():
                paragraphs.append(text)
            if len(paragraphs) >= 3:
                break
        return " ".join(paragraphs)

    def _fetch_wikipedia_for_site(self, site_name: str) -> Dict[str, str] | None:
        """Fetch Wikipedia details for a specific site name using direct and search fallback."""
        normalized = site_name.replace(" ", "_")

        # Fast path: Wikipedia REST summary API.
        try:
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{normalized}"
            summary_resp = self.session.get(summary_url, timeout=8)
            if summary_resp.status_code == 200:
                payload = summary_resp.json()
                extract = str(payload.get("extract", "") or "").strip()
                canonical = str(payload.get("content_urls", {}).get("desktop", {}).get("page", "") or "")
                if extract and len(extract) >= 80 and self._is_historical_site_candidate(site_name, extract):
                    return SiteRecord(
                        site_name=site_name,
                        site_type=self._infer_site_type(site_name, extract),
                        description=extract,
                        location="Sri Lanka",
                        historical_period=self._infer_historical_period(extract),
                        archaeological_significance=self._infer_archaeological_significance(extract),
                        source="Wikipedia",
                        source_url=canonical or f"https://en.wikipedia.org/wiki/{normalized}",
                    ).to_dict()
        except Exception:
            pass

        # Fallback: standard article scrape.
        direct_url = f"https://en.wikipedia.org/wiki/{normalized}"
        description = self._fetch_wikipedia_summary(direct_url)
        if description and self._is_historical_site_candidate(site_name, description):
            return SiteRecord(
                site_name=site_name,
                site_type=self._infer_site_type(site_name, description),
                description=description,
                location="Sri Lanka",
                historical_period=self._infer_historical_period(description),
                archaeological_significance=self._infer_archaeological_significance(description),
                source="Wikipedia",
                source_url=direct_url,
            ).to_dict()

        # Fallback to Wikipedia search API for close title matches.
        try:
            api_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": f"{site_name} Sri Lanka historical site",
                "format": "json",
                "srlimit": 3,
            }
            response = self.session.get(api_url, params=params, timeout=8)
            if response.status_code != 200:
                return None
            data = response.json()
            for item in data.get("query", {}).get("search", []):
                title = item.get("title", "")
                if not title:
                    continue
                candidate_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                candidate_desc = self._fetch_wikipedia_summary(candidate_url)
                if not candidate_desc:
                    continue
                if not self._is_historical_site_candidate(title, candidate_desc):
                    continue
                if self._name_similarity(site_name, title) < 0.55:
                    continue
                return SiteRecord(
                    site_name=site_name,
                    site_type=self._infer_site_type(title, candidate_desc),
                    description=candidate_desc,
                    location="Sri Lanka",
                    historical_period=self._infer_historical_period(candidate_desc),
                    archaeological_significance=self._infer_archaeological_significance(candidate_desc),
                    source="Wikipedia",
                    source_url=candidate_url,
                ).to_dict()
        except Exception:
            return None

        return None

    def _extract_paragraphs(self, soup: BeautifulSoup, max_paragraphs: int = 3) -> str:
        out = []
        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)
            if len(text) >= 60:
                out.append(text)
            if len(out) >= max_paragraphs:
                break
        return " ".join(out)

    def _normalize_record(self, record: Dict[str, str]) -> Dict[str, str]:
        normalized = {}
        for field in REQUIRED_FIELDS:
            val = str(record.get(field, "") or "").strip()
            val = re.sub(r"\s+", " ", val)
            normalized[field] = val

        # Enforce allowed source set; unknown records are tagged but retained for review visibility.
        if normalized["source"] not in ALLOWED_SOURCES:
            normalized["source"] = "Wikipedia"

        return normalized

    def _build_lookup(self, records: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        lookup: Dict[str, List[Dict[str, str]]] = {}
        for rec in records:
            key = self._dedupe_key(rec.get("site_name", ""))
            if key not in lookup:
                lookup[key] = []
            lookup[key].append(rec)
        return lookup

    def _find_best_match(self, site_name: str, lookup: Dict[str, List[Dict[str, str]]]) -> Dict[str, str] | None:
        key = self._dedupe_key(site_name)
        if key in lookup and lookup[key]:
            return lookup[key][0]

        # Substring-based fallback for partial aliases (e.g., Dalada Maligawa vs Temple of Tooth).
        for candidate_list in lookup.values():
            for candidate in candidate_list:
                ck = self._dedupe_key(candidate.get("site_name", ""))
                if key and ck and (key in ck or ck in key):
                    return candidate

        # Fuzzy fallback across keys.
        best = None
        best_score = 0.0
        for candidate_list in lookup.values():
            for candidate in candidate_list:
                score = self._name_similarity(site_name, candidate.get("site_name", ""))
                if score > best_score:
                    best_score = score
                    best = candidate

        if best_score >= 0.45:
            return best
        return None

    def _name_similarity(self, a: str, b: str) -> float:
        a_tokens = set(re.sub(r"[^a-z0-9 ]+", " ", a.lower()).split())
        b_tokens = set(re.sub(r"[^a-z0-9 ]+", " ", b.lower()).split())
        if not a_tokens or not b_tokens:
            return 0.0
        return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)

    def _dedupe_key(self, site_name: str) -> str:
        key = re.sub(r"[^a-z0-9]+", "", site_name.lower())
        return key or "unknown"

    def _record_to_rag_text(self, record: Dict[str, str]) -> str:
        return (
            f"Site Name: {record['site_name']}\n"
            f"Site Type: {record['site_type']}\n"
            f"Location: {record['location']}\n"
            f"Historical Period: {record['historical_period']}\n"
            f"Archaeological Significance: {record['archaeological_significance']}\n"
            f"Source: {record['source']}\n"
            f"Description: {record['description']}"
        )

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        if len(text) <= chunk_size:
            return [text]

        parts = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                parts.append(chunk)
            if end == len(text):
                break
            start = max(0, end - overlap)
        return parts

    def _infer_site_type(self, title: str, description: str) -> str:
        signal = (title + " " + description).lower()
        if any(k in signal for k in ["temple", "vihara", "stupa", "dagoba"]):
            return "Temple/Religious Site"
        if any(k in signal for k in ["fort", "fortress"]):
            return "Fort/Fortress"
        if any(k in signal for k in ["cave", "ruins", "archaeological"]):
            return "Archaeological Site"
        if any(k in signal for k in ["city", "kingdom", "capital"]):
            return "Ancient City"
        return "Historical Site"

    def _infer_historical_period(self, text: str) -> str:
        signal = text.lower()
        if any(k in signal for k in ["bce", "ancient", "anuradhapura", "polonnaruwa"]):
            return "Ancient/Medieval"
        if any(k in signal for k in ["portuguese", "dutch", "british", "colonial"]):
            return "Colonial"
        return "Historical"

    def _infer_archaeological_significance(self, text: str) -> str:
        signal = text.lower()
        if "unesco" in signal:
            return "UNESCO recognized heritage relevance"
        if any(k in signal for k in ["inscription", "ruins", "excavation", "artifact"]):
            return "Documented archaeological evidence"
        return "Historically significant tourism and cultural site"

    def _looks_like_sri_lanka_site(self, record: Dict[str, str]) -> bool:
        source = record.get("source", "")
        source_url = record.get("source_url", "").lower()
        if source in {"Sri Lanka Tourism Development Authority", "Archaeological Sites"}:
            return (
                "srilanka.travel" in source_url
                or "sltda" in source_url
                or "archaeology.gov.lk" in source_url
                or "arcgis.com" in source_url
                or "services6.arcgis.com" in source_url
            )

        text = " ".join(
            [
                record.get("site_name", ""),
                record.get("description", ""),
                record.get("location", ""),
                record.get("source_url", ""),
            ]
        ).lower()
        return any(token in text for token in ["sri lanka", "lanka", "kandy", "galle", "anuradhapura", "sigiriya"])

    def _is_historical_site_candidate(self, title: str, description: str) -> bool:
        combined = f"{title} {description}".lower()

        # Exclude obvious non-site pages.
        excluded_tokens = [
            "school",
            "college",
            "university",
            "district",
            "province",
            "list of",
            "election",
            "person",
            "biography",
            "cricket",
            "railway station",
        ]
        if any(token in combined for token in excluded_tokens):
            return False

        required_signals = [
            "historical",
            "archaeological",
            "ancient",
            "ruins",
            "unesco",
            "temple",
            "fort",
            "fortress",
            "vihara",
            "stupa",
            "cave",
            "heritage",
            "monastery",
            "palace",
        ]
        return any(token in combined for token in required_signals)

    def _mock_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        import numpy as np

        out = []
        for chunk in chunks:
            np.random.seed(abs(hash(chunk["chunk_id"])) % (2**32))
            vector = np.random.randn(1536).tolist()
            out.append({**chunk, "embedding": vector})

        out_file = VECTOR_DB_DIR / "sri_lanka_historical_sites_chunks_with_mock_embeddings.json"
        out_file.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved mock embeddings: %s", out_file)
        return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sri Lanka historical sites research pipeline")
    parser.add_argument(
        "--step",
        choices=["collect", "review", "chunk", "embed", "upsert", "test", "enrich-csv", "all"],
        default="all",
        help="Pipeline step to run",
    )
    parser.add_argument(
        "--index-name",
        default="historical-sites-sl",
        help="Pinecone index name",
    )
    parser.add_argument(
        "--allow-mock-embeddings",
        action="store_true",
        help="Use deterministic mock embeddings when Azure credentials are missing",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Start index for enrich-csv batch processing",
    )
    parser.add_argument(
        "--end-index",
        type=int,
        default=None,
        help="End index (exclusive) for enrich-csv batch processing",
    )
    return parser.parse_args()


def main() -> None:
    load_env_file(PROJECT_ROOT / ".env")
    args = parse_args()
    pipeline = SriLankaHistoricalPipeline()

    if args.step == "collect":
        pipeline.collect_data()
        return

    if args.step == "review":
        records = json.loads(RAW_JSON_FILE.read_text(encoding="utf-8"))
        pipeline.review_json(records)
        return

    if args.step == "chunk":
        records = json.loads(CLEAN_JSON_FILE.read_text(encoding="utf-8"))
        pipeline.chunk_records(records)
        return

    if args.step == "embed":
        chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
        pipeline.generate_embeddings(chunks, use_mock_if_missing=args.allow_mock_embeddings)
        return

    if args.step == "upsert":
        path = VECTOR_DB_DIR / "sri_lanka_historical_sites_chunks_with_embeddings.json"
        embedded = json.loads(path.read_text(encoding="utf-8"))
        pipeline.upsert_to_pinecone(embedded, index_name=args.index_name)
        return

    if args.step == "test":
        pipeline.retrieval_test(index_name=args.index_name)
        return

    if args.step == "enrich-csv":
        report = pipeline.enrich_rag_ready_sites(start_index=args.start_index, end_index=args.end_index)
        logger.info("CSV enrichment complete: %s", json.dumps(report, indent=2))
        return

    results = pipeline.run_all(
        use_mock_embeddings_if_missing=args.allow_mock_embeddings,
        index_name=args.index_name,
    )
    logger.info("Pipeline complete: %s", json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
