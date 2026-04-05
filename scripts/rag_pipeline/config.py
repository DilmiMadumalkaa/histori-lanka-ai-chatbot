"""
RAG Pipeline Configuration
Settings for data processing and embedding generation
"""

import os
from pathlib import Path

# ==========================================
# DATA PATHS
# ==========================================
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "rag_vectordb"
EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "embeddings"

# ==========================================
# DATA PROCESSING CONFIG
# ==========================================
CLEANING_CONFIG = {
    "remove_wikipedia_metadata": True,
    "min_description_length": 50,
    "max_description_length": 3000,
    "require_english_only": True,
    "latin_char_threshold": 0.7,  # 70% Latin characters
}

DEDUPLICATION_CONFIG = {
    "remove_exact_duplicates": True,
    "fuzzy_matching_enabled": True,
    "fuzzy_threshold": 0.85,  # 85% similarity
    "keep_longest_description": True,
}

CHUNKING_CONFIG = {
    "chunk_size_chars": 512,
    "chunk_overlap_chars": 100,
    "split_by_sentence": True,
    "preserve_metadata": True,
}

# ==========================================
# EMBEDDING CONFIG
# ==========================================
EMBEDDING_CONFIG = {
    "model": "text-embedding-3-large",
    "dimension": 1536,  # text-embedding-3-large produces 1536-dim vectors
    "batch_size": 10,
    "api_version": "2024-02-01",
    "use_mock_embeddings": False,  # Set to True if Azure credentials not available
}

# Azure OpenAI Credentials (from environment)
AZURE_OPENAI_CONFIG = {
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
    "api_version": "2024-02-01",
}

# ==========================================
# VECTOR DATABASE CONFIG
# ==========================================
VECTOR_DB_CONFIG = {
    "type": "faiss",  # Options: "faiss", "azure-search", "json"
    "faiss_index_file": "historical_sites_faiss.index",
    "metadata_file": "historical_sites_metadata.json",
}

# Azure AI Search Config (for production)
AZURE_SEARCH_CONFIG = {
    "service_name": os.getenv("AZURE_SEARCH_SERVICE_NAME"),
    "api_key": os.getenv("AZURE_SEARCH_API_KEY"),
    "api_version": "2024-05-01-preview",
    "index_name": "historical-sites",
}

# ==========================================
# LOGGING CONFIG
# ==========================================
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_file": PROJECT_ROOT / "logs" / "rag_pipeline.log",
}

# ==========================================
# RESEARCH SETTINGS
# ==========================================
RESEARCH_CONFIG = {
    "project_name": "Historical Sites Chatbot",
    "data_sources": ["Wikipedia", "SLTDA", "Archaeology Databases"],
    "target_language": "English",
    "min_sites_for_training": 50,
    "validation_split": 0.2,
    "test_split": 0.1,
}
