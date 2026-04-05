# 🤖 RAG CHATBOT IMPLEMENTATION GUIDE

## Quick Start

```python
import pandas as pd

# Load the RAG-ready dataset
df = pd.read_csv('data/processed/historical_sites_rag_ready.csv')

print(f"Loaded {len(df)} historical sites")
print(f"Columns: {list(df.columns)}")
```

---

## Usage Examples

### 1. Search for UNESCO Sites
```python
unesco_sites = df[df['unesco_status'] == 'UNESCO World Heritage Site']
print(f"Found {len(unesco_sites)} UNESCO sites")
# Returns: 31 sites
```

### 2. Query by Region
```python
# Find all sites in Central Highlands
central_sites = df[df['region_specific'].str.contains('Central', na=False)]
print(central_sites[['site_name', 'historical_period']])
```

### 3. Filter by Historical Period
```python
# Find Ancient Kingdom sites
ancient = df[df['historical_period'] == 'Ancient Kingdom']
print(f"Ancient sites: {len(ancient)}")
# Returns sites like Anuradhapura, Polonnaruwa, Sigiriya
```

### 4. Get Site Details
```python
# Get comprehensive information about a specific site
site = df[df['site_name'] == 'Anuradhapura'].iloc[0]

print(f"Site: {site['site_name']}")
print(f"Period: {site['historical_period']}")
print(f"UNESCO: {site['unesco_status']}")
print(f"Region: {site['region_specific']}")
print(f"Significance: {site['archaeological_significance']}")
print(f"RAG Content:\n{site['rag_content']}")
```

### 5. Extract RAG Content for Embeddings
```python
# Prepare text for vector embeddings
rag_texts = df['rag_content'].tolist()
# Use these with your embedding model (e.g., OpenAI, Hugging Face)
```

---

## Integration with RAG Pipeline

### Minimal Example
```python
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np

# Load dataset
df = pd.read_csv('data/processed/historical_sites_rag_ready.csv')

# Generate embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(df['rag_content'].tolist())

# Store in vector database (e.g., Pinecone, Weaviate, Milvus)
# Then use for retrieval-augmented generation
```

### Question-Answer Example
```python
def answer_about_sites(question, df, embeddings, model, top_k=3):
    # Embed the question
    question_embedding = model.encode(question)
    
    # Find most similar sites
    similarities = np.dot(embeddings, question_embedding)
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    # Get context from top results
    context = "\n\n".join([
        df.iloc[idx]['rag_content'] 
        for idx in top_indices
    ])
    
    return context

# Example queries
queries = [
    "What are the UNESCO World Heritage Sites in Sri Lanka?",
    "Tell me about ancient Buddhist temples",
    "Where are the colonial forts located?"
]

for query in queries:
    context = answer_about_sites(query, df, embeddings, model)
    # Pass context to LLM for answer generation
```

---

## Sample Chatbot Queries & Expected Results

### Query 1: "What is Anuradhapura?"
**Expected Response Fields**:
- `site_name`: Anuradhapura
- `description`: [Comprehensive Wikipedia description]
- `archaeological_significance`: UNESCO World Heritage Site. Ancient capital...
- `historical_period`: Ancient Kingdom
- `region_specific`: North Central Province

### Query 2: "Show me all UNESCO sites"
**Expected Response**:
- 31 UNESCO World Heritage Sites returned
- Includes: Anuradhapura, Polonnaruwa, Sigiriya, Dambulla, Kandy, Galle Fort, etc.

### Query 3: "What historical sites are in the Central Highlands?"
**Expected Response**:
- 30 sites in Central Highlands region
- Mix of temples, mountains, archaeological sites

### Query 4: "Tell me about colonial heritage"
**Expected Response**:
- 8 sites with Colonial Period classification
- Includes forts and administrative buildings

---

## Dataset Statistics for Chatbot Training

Use these statistics to understand your knowledge base:

```
Total Coverage: 197 sites
- Buddhist Temples: 41
- Natural/Sacred Sites: 28
- Forts/Fortresses: 27
- Archaeological Sites: 18
- Colonial Heritage: 8
- Museums: 3
- National Parks: 2

Geographic Coverage:
- Central Highlands: 30 sites
- Western Province: 24 sites
- Other/General: 96 sites
- Southern Province: 16 sites

Historical Periods:
- General Historical: 152
- Ancient Kingdom: 18
- Medieval Kingdom: 16
- Colonial Period: 8

Data Quality:
- Description completeness: 100%
- URL availability: 100%
- Archaeological context: 100%
```

---

## Best Practices for RAG Implementation

### 1. **Text Chunking** (if needed)
```python
def chunk_text(text, max_length=512):
    """Split long descriptions into chunks"""
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_length:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk)
            current_chunk = sentence + ". "
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

# Apply to dataset
df['chunks'] = df['description'].apply(chunk_text)
```

### 2. **Semantic Search**
```python
def semantic_search(query, embeddings, df, model, top_k=5):
    query_embedding = model.encode(query)
    similarities = np.dot(embeddings, query_embedding)
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    results = df.iloc[top_indices][['site_name', 'description', 'region_specific']]
    return results
```

### 3. **Filtering & Re-ranking**
```python
# Filter by region then rank by relevance
central = df[df['region_specific'].str.contains('Central', na=False)]
central_embeddings = embeddings[central.index]
# Then perform semantic search on filtered set
```

### 4. **Context Window Management**
Use `rag_content` column which is pre-formatted for:
- Site information
- Archaeological context
- Historical details
- All in one optimized text block

---

## Testing Your Setup

### Verification Script
```python
import pandas as pd

df = pd.read_csv('data/processed/historical_sites_rag_ready.csv')

# Verify dataset integrity
assert len(df) == 197, "Should have 197 sites"
assert all(df['description'].notna()), "All sites should have descriptions"
assert 'rag_content' in df.columns, "RAG content column required"
assert (df['unesco_status'] == 'UNESCO World Heritage Site').sum() == 31, "31 UNESCO sites"

print("✅ Dataset verification passed!")
print(f"   - Sites: {len(df)}")
print(f"   - UNESCO: {(df['unesco_status'] == 'UNESCO World Heritage Site').sum()}")
print(f"   - Avg description: {df['description'].str.len().mean():.0f} chars")
print(f"   - Columns: {len(df.columns)}")
```

---

## Performance Optimization

### Embeddings Model Selection
- **Lightweight**: `all-MiniLM-L6-v2` (22MB, 384 dims)
- **Balanced**: `all-mpnet-base-v2` (440MB, 768 dims)
- **High-performance**: `all-roberta-large-v1` (740MB, 1024 dims)

### Recommended Configuration
```python
from sentence_transformers import SentenceTransformer

# Load model once and reuse
model = SentenceTransformer('all-mpnet-base-v2')

# Batch encoding for efficiency
embeddings = model.encode(
    df['rag_content'].tolist(),
    batch_size=32,
    show_progress_bar=True
)
```

---

## Troubleshooting

### Issue: Memory Error with Embeddings
**Solution**: Use batch processing
```python
batch_size = 32
embeddings_list = []
for i in range(0, len(df), batch_size):
    batch_text = df['rag_content'].iloc[i:i+batch_size].tolist()
    batch_embeddings = model.encode(batch_text)
    embeddings_list.append(batch_embeddings)

embeddings = np.vstack(embeddings_list)
```

### Issue: Slow Semantic Search
**Solution**: Pre-compute and cache embeddings, use GPU

### Issue: Low Retrieval Accuracy
**Solution**: 
- Use larger embedding model
- Implement re-ranking
- Combine multiple retrieval strategies
- Add metadata filters

---

## Deployment Checklist

- [ ] Load and verify dataset: `historical_sites_rag_ready.csv`
- [ ] Generate and cache embeddings
- [ ] Set up vector database (if using external store)
- [ ] Test semantic search functionality
- [ ] Configure LLM prompt template with context
- [ ] Deploy with proper error handling
- [ ] Monitor query performance
- [ ] Collect feedback for fine-tuning

---

## File Reference

**Primary Dataset**: `data/processed/historical_sites_rag_ready.csv`

**Key Columns for RAG**:
- `rag_content` - Use for embeddings
- `description` - Use as primary context
- `archaeological_significance` - Add for authority
- `historical_period` - Use for filtering
- `region_specific` - Use for location-based queries

---

Generated: 2024 | Ready for RAG Chatbot Implementation ✅
