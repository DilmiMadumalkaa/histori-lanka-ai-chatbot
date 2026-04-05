# RAG Data Processing Pipeline
## Historical Sites Chatbot - 6-Step Research-Grade Pipeline

Complete implementation for preparing historical sites data for Retrieval-Augmented Generation (RAG).

---

## 🎯 Pipeline Overview

This pipeline implements the complete 6-step process for research-quality RAG preparation:

```
Raw Data (Multi-source scraped)
    ↓
[STEP 1] Merge & Clean
    ↓
[STEP 2] Deduplicate
    ↓
[STEP 3] Text Cleaning (LLM Quality)
    ↓
[STEP 4] Chunking (RAG Preparation)
    ↓
[STEP 5] Embeddings (Azure OpenAI)
    ↓
[STEP 6] Vector Database (FAISS/Azure Search)
    ↓
Production-Ready RAG System
```

---

## 📋 Step-by-Step Guide

### STEP 1: Merge & Clean All Scraped Data

**What it does:**
- Loads CSV files from multiple sources (Wikipedia, SLTDA, Archaeology)
- Removes Wikipedia metadata pages
- Filters non-English content (< 70% Latin characters)
- Removes very short descriptions (< 50 characters)
- Standardizes column format

**Key functions:**
```python
processor.load_and_merge_data(['*.csv'])
```

**Output:**
- Combined dataset with standardized format
- Metadata preserved (source, location, category)

---

### STEP 2: Deduplication Strategy

**What it does:**
- Finds exact duplicate records
- Uses fuzzy matching (85% similarity threshold) for similar site names
- Merges duplicates while keeping the longest description
- Consolidates sources in metadata

**Example:**
```
Before:  Sigiriya (Wikipedia) + Sigiriya (SLTDA) = 2 records
After:   Sigiriya (merged from Wikipedia | SLTDA) = 1 record
```

**Key functions:**
```python
processor.deduplicate_data(similarity_threshold=0.85)
```

**Why this matters:**
- Improves dataset quality → stronger thesis
- Prevents duplicate embeddings (wastes compute)
- Consolidates knowledge from multiple sources

---

### STEP 3: Text Cleaning (CRITICAL FOR LLM QUALITY)

**What it does:**
- **Removes citation brackets**: `[1]`, `[2]` → clean text
- **Removes HTML entities**: `&nbsp;` → space
- **Normalizes whitespace**: Multiple spaces → single space
- **Removes special characters**: HTML tags, excessive punctuation
- **Limits description**: Max 3000 characters (fits embedding window)

**Text cleaning flow:**
```
Raw: "This is [[an] ancient] site[1][2]...    with   extra   spaces"
Clean: "This is an ancient site with extra spaces"
```

**Key functions:**
```python
processor.clean_text()
```

**Why this matters:**
- LLMs perform better on clean text
- Improves embedding quality
- Ensures consistency across dataset

**Output:**
- Cleaned descriptions ready for chunking
- Original text preserved in backup column

---

### STEP 4: Chunk the Dataset (RAG PREPARATION)

**What it does:**
- Splits long descriptions into semantic chunks (512 chars default)
- Maintains overlap between chunks (100 chars default)
- Preserves metadata for each chunk
- Optimizes for retrieval relevance

**Chunking example:**
```
Site: Sigiriya
Description: "Long description (2000 chars)..."

Creates chunks:
  Chunk 1: Characters 0-512 (with context)
  Chunk 2: Characters 412-924 (with 100 char overlap)
  Chunk 3: Characters 824-1336
  ...
```

**Key functions:**
```python
processor.chunk_data(
    chunk_size=512,      # Target chunk size
    overlap=100          # Overlap between chunks
)
```

**Output:**
- ~2000-5000 chunks depending on dataset size
- Each chunk has metadata: site_id, site_name, category, source, etc.

**Why this matters:**
- Enables precise retrieval of relevant context
- Fits within LLM context windows
- Improves answer quality by providing focused context

---

### STEP 5: Generate Embeddings (AZURE OPENAI)

**What it does:**
- Uses Azure OpenAI `text-embedding-3-large` model
- Generates 1536-dimensional vectors for each chunk
- Captures semantic meaning of text
- Enables vector similarity search

**Model details:**
```
Model: text-embedding-3-large
Dimensions: 1536
Cost: ~$0.02 per 1M tokens
Speed: ~10,000 chunks per minute
```

**Key functions:**
```python
processor.generate_embeddings(
    api_key="sk-...",           # From environment
    endpoint="https://...",     # Azure endpoint
    model="text-embedding-3-large"
)
```

**Azure credentials (set in environment):**
```bash
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
```

**Fallback (mock embeddings for testing):**
```python
processor._generate_mock_embeddings()  # Uses numpy random
```

**Output:**
- Chunks with 1536-dimensional embeddings
- Ready for vector database storage

---

### STEP 6: Store in Vector Database

**What it does:**
- Saves embeddings to vector database (FAISS or Azure Search)
- Creates searchable index for retrieval
- Stores metadata with each embedding

**Database options:**

#### Option A: FAISS (Local, Development)
```python
processor.save_to_vector_db(db_type="faiss")
```

**Advantages:**
- ✓ Fast local search
- ✓ No external dependencies
- ✓ Good for prototyping

**Output files:**
- `historical_sites_faiss.index` - Vector index
- `historical_sites_metadata.json` - Chunk metadata

#### Option B: Azure AI Search (Production)
```python
processor.save_to_vector_db(db_type="azure-search")
```

**Advantages:**
- ✓ Scalable, cloud-based
- ✓ Integrated with Azure ecosystem
- ✓ Advanced filtering capabilities
- ✓ Dedicated infrastructure

**Setup required:**
```python
export AZURE_SEARCH_SERVICE_NAME="your-service"
export AZURE_SEARCH_API_KEY="your-key"
```

---

## 🚀 Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
```
pandas>=1.5.0
numpy>=1.23.0
openai>=1.0.0
faiss-cpu>=1.7.4  # Or faiss-gpu for GPU support
```

### Run Full Pipeline

```bash
python scripts/rag_pipeline/run_rag_pipeline.py
```

**With custom options:**
```bash
python scripts/rag_pipeline/run_rag_pipeline.py \
  --data-dir data/processed \
  --output-dir data/rag_vectordb \
  --db-type faiss \
  --chunk-size 512 \
  --chunk-overlap 100 \
  --use-mock-embeddings  # For testing without Azure
```

### Validate Output

```bash
python scripts/rag_pipeline/validate_rag_pipeline.py data/rag_vectordb
```

Generates validation report with:
- Data quality statistics
- Chunk analysis
- Embedding validation
- Processing summary

---

## 📊 Configuration

Edit `scripts/rag_pipeline/config.py`:

```python
# Chunk configuration
CHUNKING_CONFIG = {
    "chunk_size_chars": 512,      # Larger = fewer chunks, less precise
    "chunk_overlap_chars": 100,   # Larger = more redundancy
    "split_by_sentence": True,    # Better semantic boundaries
}

# Deduplication
DEDUPLICATION_CONFIG = {
    "fuzzy_threshold": 0.85,      # 0.85 = 85% similarity required
}

# Embedding
EMBEDDING_CONFIG = {
    "model": "text-embedding-3-large",
    "batch_size": 10,
}
```

---

## 📈 Expected Results

For a typical historical sites dataset:

| Metric | Value |
|--------|-------|
| Raw records | 100-200 |
| After cleaning | 80-150 |
| After deduplication | 70-120 |
| Total chunks | 2,000-5,000 |
| Embedding dimension | 1536 |
| FAISS index size | 50-200 MB |
| Processing time | 5-15 minutes |

---

## 🔍 Quality Checks

### Data Quality Metrics

1. **Cleaned CSV**
   - No duplicate descriptions
   - All entries English-language
   - Descriptions 50-3000 chars
   - All required metadata present

2. **Chunks**
   - Average chunk length: 300-600 words
   - Chunks preserve semantic meaning
   - Metadata linked to source records

3. **Embeddings**
   - 1536-dimensional vectors
   - Normalized L2 distance
   - Ready for vector search

### Run Validation

```bash
python scripts/rag_pipeline/validate_rag_pipeline.py data/rag_vectordb
```

**Output includes:**
- Record count and statistics
- Missing value analysis
- Chunk quality metrics
- Embedding validation

---

## 🔗 Integration with RAG System

### Using FAISS Index

```python
import faiss
import json

# Load index and metadata
index = faiss.read_index("data/rag_vectordb/historical_sites_faiss.index")
with open("data/rag_vectordb/historical_sites_metadata.json") as f:
    metadata = json.load(f)

# Search for similar chunks
query_embedding = embed_query(user_query)
distances, indices = index.search(np.array([query_embedding]), k=5)

# Retrieve context
for idx in indices[0]:
    print(metadata[idx]['chunk_text'])
```

### Using Azure AI Search

```python
from azure.search.documents import SearchClient

client = SearchClient(
    endpoint="https://your-service.search.windows.net",
    index_name="historical-sites",
    credential=credential
)

results = client.search(
    search_text=query,
    vector=query_embedding,
    top=5
)
```

---

## 📚 Best Practices for Research

1. **Data Quality**
   - Always validate cleaned data
   - Check metadata preservation
   - Review random sample of chunks

2. **Chunking**
   - Adjust chunk size based on domain knowledge
   - Overlapping chunks prevent missed context
   - Validate chunk coherence

3. **Embeddings**
   - Don't regenerate unless necessary (cost/time)
   - Cache embeddings locally
   - Version your embeddings with timestamp

4. **Documentation**
   - Record all preprocessing decisions
   - Keep processing statistics
   - Document any manual corrections

5. **Reproducibility**
   - Use fixed random seeds
   - Document exact parameters used
   - Keep input data versioned

---

## 🐛 Troubleshooting

### Azure Credentials Missing
```
Error: Azure credentials not found
Solution: Set environment variables
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_ENDPOINT="..."
```

### FAISS Installation
```
Error: No module named 'faiss'
Solution for CPU: pip install faiss-cpu
Solution for GPU: pip install faiss-gpu
```

### Out of Memory
```
Error: Memory allocation failed
Solution: Reduce batch size in config or process in smaller batches
```

### Slow Processing
```
Tip: Use mock embeddings for testing (--use-mock-embeddings)
Tip: Multi-GPU support with faiss-gpu
Tip: Batch size tuning based on memory
```

---

## 📖 References

- [Azure OpenAI Embeddings](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/understand-embeddings)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [RAG Architecture Best Practices](https://docs.microsoft.com/en-us/azure/architecture/reference-architectures/ai-machine-learning/rag)

---

## 📝 Citation for Research

```bibtex
@software{historical_sites_rag,
  title={RAG Data Processing Pipeline for Historical Sites Chatbot},
  author={Your Name},
  year={2024},
  url={https://github.com/...}
}
```

---

**Status:** ✅ Production Ready for Research  
**Last Updated:** 2024  
**Version:** 1.0.0
