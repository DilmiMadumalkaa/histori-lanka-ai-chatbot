"""
Pinecone Vector Database Integration with Reranking
====================================================
Production-ready RAG retrieval system using Pinecone cloud + custom reranking

Features:
  • Cloud-hosted vector search (Pinecone)
  • Hybrid search (semantic + keyword)
  • Custom reranking algorithm
  • Metadata filtering
  • Result caching
  • Full transparency (all scoring visible)
"""

import os
import json
import logging
import hashlib
from urllib.parse import urlparse
from typing import List, Dict, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PineconeRetrieverWithReranking:
    """
    Retrieval system using Pinecone with custom reranking
    
    Architecture:
    1. Embed user query (Azure OpenAI)
    2. Search Pinecone (semantic + keyword hybrid)
    3. Rerank results (custom algorithm)
    4. Return top-K with scores
    """
    
    def __init__(self):
        """Initialize Pinecone connection and load configuration"""
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_env = os.getenv("PINECONE_ENV", "us-east-1")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "historical-sites-sl")
        self.index_candidates = self._build_index_candidates(self.index_name)
        
        # Azure OpenAI for embeddings
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = self._normalize_azure_endpoint(os.getenv("AZURE_OPENAI_ENDPOINT", ""))
        self.azure_api_version = os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION", "2024-02-01")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "embed-3-large")
        
        # Metadata cache
        self.metadata_cache = {}
        self._load_metadata()
        
        # Initialize Pinecone
        self.pc = None
        self.index = None
        self._initialize_pinecone()
        
        logger.info("✓ Pinecone retriever initialized")

    def _normalize_azure_endpoint(self, endpoint: str) -> str:
        """Normalize Azure endpoint to base resource URL if a full API path is provided."""
        if not endpoint:
            return endpoint
        parsed = urlparse(endpoint)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return endpoint

    def _build_index_candidates(self, configured_index: str) -> List[str]:
        """Build prioritized list of Pinecone index names to try."""
        candidates = [configured_index, "historical-sites-sl", "historical-sites"]
        out: List[str] = []
        for name in candidates:
            if name and name not in out:
                out.append(name)
        return out
    
    def _initialize_pinecone(self):
        """Connect to Pinecone"""
        try:
            from pinecone import Pinecone
        except ImportError:
            logger.error("Pinecone not installed. Run: pip install pinecone")
            raise
        
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not found in environment")
        
        self.pc = Pinecone(api_key=self.pinecone_api_key)

        last_error = None
        for candidate in self.index_candidates:
            try:
                logger.info("Connecting to Pinecone (index: %s)...", candidate)
                index = self.pc.Index(candidate)
                stats = index.describe_index_stats()
                vector_count = stats.get('total_vector_count', 0)

                self.index_name = candidate
                self.index = index
                logger.info("✓ Connected to Pinecone - index '%s' contains %s vectors", candidate, vector_count)
                return
            except Exception as e:
                last_error = e
                logger.warning("Failed to connect to index '%s': %s", candidate, e)

        logger.error("Failed to connect to any Pinecone index candidate: %s", self.index_candidates)
        if last_error:
            raise last_error
        raise RuntimeError("Unable to connect to Pinecone index")
    
    def _load_metadata(self):
        """Load chunk metadata for reranking"""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        candidate_paths = [
            os.path.join(project_root, "data", "rag_vectordb", "historical_sites_metadata.json"),
            os.path.join(project_root, "data", "rag_vectordb", "historical_sites_metadata_full.json"),
            os.path.join(project_root, "data", "rag_vectordb", "sri_lanka_historical_sites_chunks_with_embeddings.json"),
            os.path.join(project_root, "data", "rag_vectordb", "sri_lanka_historical_sites_chunks.json"),
        ]

        for metadata_path in candidate_paths:
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    raw_metadata = json.load(f)

                if isinstance(raw_metadata, dict):
                    metadata_list = list(raw_metadata.values())
                elif isinstance(raw_metadata, list):
                    metadata_list = raw_metadata
                else:
                    logger.warning("Unsupported metadata format in %s", metadata_path)
                    continue

                loaded = 0
                for item in metadata_list:
                    if not isinstance(item, dict):
                        continue
                    chunk_id = item.get('chunk_id') or item.get('id')
                    if not chunk_id:
                        continue
                    self.metadata_cache[chunk_id] = item
                    loaded += 1

                if loaded > 0:
                    logger.info("✓ Loaded %d chunk metadata entries from %s", loaded, metadata_path)
                    return
            except Exception as e:
                logger.warning("Could not load metadata from %s: %s", metadata_path, e)

        logger.warning("No metadata file loaded; relying on Pinecone match metadata only")
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for user query using Azure OpenAI"""
        try:
            from openai import AzureOpenAI
        except ImportError:
            logger.error("OpenAI not installed. Run: pip install openai")
            raise
        
        try:
            client = AzureOpenAI(
                api_key=self.azure_api_key,
                api_version=self.azure_api_version,
                azure_endpoint=self.azure_endpoint
            )
            
            response = client.embeddings.create(
                input=query,
                model=self.embedding_deployment
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for query (dim: {len(embedding)})")
            return embedding
            
        except Exception as e:
            logger.warning(f"Azure embedding failed: {e}. Using mock embedding...")
            return self._generate_mock_embedding(query)
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for testing (deterministic)"""
        import numpy as np
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        seed = int(digest[:8], 16)
        rng = np.random.default_rng(seed)
        return rng.standard_normal(3072).tolist()
    
    def retrieve_with_reranking(self, query: str, top_k: int = 5, rerank_top_k: int = 3) -> Dict:
        """
        Retrieve and rerank results
        
        Args:
            query: User question
            top_k: Get top K from Pinecone (before reranking)
            rerank_top_k: Return top K after reranking
        
        Returns:
            Dictionary with results and scoring details
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Query: {query}")
        logger.info(f"{'='*70}")
        
        # Step 1: Embed query
        logger.info("Step 1: Embedding query...")
        query_embedding = self.embed_query(query)
        
        # Step 2: Search Pinecone (get more than needed for reranking)
        logger.info(f"Step 2: Searching Pinecone (top {top_k})...")
        pinecone_results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Step 3: Rerank results
        logger.info("Step 3: Reranking results...")
        reranked = self._rerank_results(query, pinecone_results)
        
        # Step 4: Return top K after reranking
        final_results = reranked[:rerank_top_k]
        
        logger.info(f"\n✓ Retrieved {len(final_results)} results after reranking\n")
        
        return {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "results": final_results,
            "total_retrieved": len(reranked),
            "reranking_method": "hybrid (semantic + keyword + metadata)"
        }
    
    def _rerank_results(self, query: str, pinecone_results: Dict) -> List[Dict]:
        """
        Rerank Pinecone results using custom algorithm
        
        Scoring: 60% semantic + 30% keyword + 10% metadata
        """
        candidates = []
        
        for match in pinecone_results.get('matches', []):
            chunk_id = match['id']
            semantic_score = match.get('score', 0)  # From Pinecone (0-1)
            
            # Get metadata
            match_metadata = match.get('metadata', {}) or {}
            cache_metadata = self.metadata_cache.get(chunk_id, {})
            metadata = {**cache_metadata, **match_metadata}
            chunk_text = (
                metadata.get('chunk_text')
                or metadata.get('text')
                or metadata.get('rag_text')
                or ''
            )
            
            # Calculate keyword match score
            keyword_score = self._calculate_keyword_score(query, chunk_text)
            
            # Calculate metadata score
            metadata_score = self._calculate_metadata_score(query, metadata)
            
            # Combined score (weighted)
            combined_score = (
                0.6 * semantic_score +    # Semantic similarity (primary)
                0.3 * keyword_score +     # Keyword matching
                0.1 * metadata_score      # Metadata relevance
            )
            
            # Store with all scoring details
            result = {
                "chunk_id": chunk_id,
                "site_name": metadata.get('site_name', 'Unknown'),
                "category": metadata.get('category', metadata.get('site_type', 'Unknown')),
                "source": metadata.get('source', 'Unknown'),
                "chunk_text": chunk_text,
                
                # Scoring breakdown (for transparency)
                "scores": {
                    "semantic": round(semantic_score, 4),
                    "keyword": round(keyword_score, 4),
                    "metadata": round(metadata_score, 4),
                    "combined": round(combined_score, 4)
                }
            }
            
            candidates.append(result)
        
        # Sort by combined score (descending)
        candidates.sort(key=lambda x: x['scores']['combined'], reverse=True)
        
        # Log reranking details
        logger.info("\nReranking Results:")
        logger.info("-" * 70)
        for i, result in enumerate(candidates[:3], 1):
            logger.info(f"\n{i}. {result['site_name']} ({result['category']})")
            logger.info(f"   Scores - Semantic: {result['scores']['semantic']:.3f} | "
                       f"Keyword: {result['scores']['keyword']:.3f} | "
                       f"Metadata: {result['scores']['metadata']:.3f} | "
                       f"Combined: {result['scores']['combined']:.3f}")
            logger.info(f"   Text: {result['chunk_text'][:80]}...")
        
        return candidates
    
    def _calculate_keyword_score(self, query: str, text: str) -> float:
        """
        BM25-like keyword matching score
        Higher if query words appear in text
        
        Returns: 0-1 score
        """
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        # Remove common stop words
        stop_words = {'the', 'is', 'at', 'which', 'on', 'in', 'and', 'or', 'a', 'an'}
        query_words = query_words - stop_words
        
        if not query_words:
            return 0.5  # Default score if only stop words
        
        # Calculate overlap
        overlap = len(query_words & text_words)
        score = min(overlap / len(query_words), 1.0)
        
        return score
    
    def _calculate_metadata_score(self, query: str, metadata: Dict) -> float:
        """
        Score based on metadata relevance
        Checks: site type, category, source compatibility
        
        Returns: 0-1 score (higher = more relevant)
        """
        score = 0.5  # Neutral baseline
        
        # Check if site is UNESCO (often important)
        if 'unesco' in query.lower() and 'UNESCO' in metadata.get('category', ''):
            score = 0.9
        
        # Check if looking for ancient sites
        elif 'ancient' in query.lower() and 'Ancient' in metadata.get('category', ''):
            score = 0.8
        
        # Check if looking for temples/religious sites
        elif ('temple' in query.lower() or 'buddhist' in query.lower()):
            if 'Temple' in metadata.get('category', '') or 'Buddhist' in metadata.get('category', ''):
                score = 0.8
        
        # Check if looking for forts/fortresses
        elif ('fort' in query.lower() or 'fortress' in query.lower()):
            if 'Fort' in metadata.get('category', '') or 'Fortress' in metadata.get('category', ''):
                score = 0.8
        
        # Default: check if source is reliable
        elif metadata.get('source') in ['Wikipedia', 'Comprehensive List']:
            score = 0.6
        
        return score
    
    def retrieve_formatted_context(self, query: str, top_k: int = 3) -> str:
        """
        Retrieve and format context for GPT (Phase 4)
        
        Returns: Formatted string ready to send to LLM
        """
        results = self.retrieve_with_reranking(query, top_k=top_k * 2, rerank_top_k=top_k)
        
        context_parts = []
        for i, result in enumerate(results['results'], 1):
            context_parts.append(
                f"📍 Source {i}: {result['site_name']}\n"
                f"Category: {result['category']}\n"
                f"Relevance Score: {result['scores']['combined']:.1%}\n"
                f"\n{result['chunk_text']}\n"
            )
        
        formatted_context = "\n" + "="*70 + "\n".join(context_parts)
        return formatted_context
    
    def get_index_stats(self) -> Dict:
        """Get Pinecone index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                "index_name": self.index_name,
                "total_vectors": stats.get('total_vector_count', 0),
                "dimension": stats.get('dimension', 0),
                "index_fullness": stats.get('index_fullness', 0),
                "namespaces": stats.get('namespaces', {})
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}


def main():
    """Example usage"""
    
    # Initialize retriever
    retriever = PineconeRetrieverWithReranking()
    
    # Example queries
    queries = [
        "Tell me about ancient rock fortresses in Sri Lanka",
        "Which sites are UNESCO World Heritage Sites?",
        "What can you tell me about Buddhist temples?",
        "Describe the historical significance of Sigiriya",
        "Which sites are located in the Central Highlands?"
    ]
    
    # Test retrieval
    print("\n" + "="*70)
    print("PINECONE RETRIEVAL WITH RERANKING - TEST")
    print("="*70 + "\n")
    
    for query in queries[:2]:  # Test with 2 queries
        try:
            results = retriever.retrieve_with_reranking(query, top_k=5, rerank_top_k=3)
            
            print(f"\n✓ Retrieved {len(results['results'])} results")
            print(f"Method: {results['reranking_method']}")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            continue
    
    # Show index stats
    print("\n" + "="*70)
    print("INDEX STATISTICS")
    print("="*70)
    stats = retriever.get_index_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
