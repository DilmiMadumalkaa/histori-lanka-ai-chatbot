# PHASE 3: RAG TESTING & EVALUATION
## Comprehensive Guide to Retrieval Quality Assessment

**Status:** ✅ Complete & Ready  
**Components:** 4 modules + 1 simulator  
**Test Coverage:** 50 Q&A pairs across 10 categories  
**Metrics:** Precision, Recall, MRR, NDCG, MAP  

---

## Overview

Phase 3 measures how well your RAG system retrieves relevant historical sites for user queries.

### Why Test Retrieval?

```
Good Retrieval = Good Chatbot

If retrieval fails:
  User Query → Wrong contexts → GPT gives wrong answer → Useless chatbot
  
If retrieval succeeds:
  User Query → Right contexts → GPT gives great answer → Useful chatbot
```

**Goal:** Achieve >80% Precision@3 and >70% Recall@10

---

## Components

### 1. Test Dataset: `rag_test_dataset.py`

**Contains:** 50 historical sites Q&A pairs

**Structure:**
```python
{
  "id": "q001",
  "question": "Tell me about ancient rock fortresses",
  "relevant_sites": ["Sigiriya", "Polonnaruwa", "Yapahuwa"],
  "category": "Ancient Sites",
  "difficulty": "easy"
}
```

**Categories (10):**
- Ancient Sites & Kingdoms (10 questions)
- Buddhist Temples & Religious (10 questions)
- Forts & Colonial Architecture (5 questions)
- Sacred & Pilgrimage Sites (5 questions)
- Archaeology & Historical (5 questions)

**Difficulty Levels:**
- Easy: 16 questions (straightforward queries)
- Medium: 17 questions (multi-site queries)
- Hard: 17 questions (complex/synthesis queries)

**Quick Access:**
```python
from rag_test_dataset import get_test_dataset

dataset = get_test_dataset()  # All 50 questions
# dataset[0]['question']
# "Tell me about ancient rock fortresses in Sri Lanka"
```

---

### 2. Evaluation Metrics: `rag_evaluation_metrics.py`

**Metrics Computed:**

#### Precision Metrics (Accuracy)
```
Precision@3 = "How many of top 3 results are relevant?"
Precision@5 = "How many of top 5 results are relevant?"
Precision@10 = "How many of top 10 results are relevant?"

Example:
Query: "Buddhist temples"
Retrieved: [Kandy Temple ✓, Museum ✗, Kelaniya ✓, Theater ✗, Random ✗]
P@3 = 2/3 = 0.667
P@5 = 2/5 = 0.400
```

#### Recall Metrics (Completeness)
```
Recall@5 = "What fraction of ALL relevant sites appear in top 5?"
Recall@10 = "What fraction of ALL relevant sites appear in top 10?"

Example:
Query: "Buddhist temples"
Relevant: [Kandy Temple, Kelaniya, Polonnaruwa, Anuradhapura]
Retrieved@10: [Kandy ✓, Museum, Kelaniya ✓, Other, Polonnaruwa ✓, ...]
R@10 = 3/4 = 0.75
```

#### Ranking Quality Metrics
```
MRR = Mean Reciprocal Rank
"What's the average position of the FIRST relevant result?"
  If first relevant at position 1: 1/1 = 1.0    (perfect)
  If first relevant at position 2: 1/2 = 0.5    (good)
  If first relevant at position 5: 1/5 = 0.2    (poor)

NDCG@10 = Normalized Discounted Cumulative Gain
"Quality of ranking considering position matters"
  Ideally, all relevant results at top → NDCG = 1.0
  Relevant results scattered → NDCG < 1.0

MAP@10 = Mean Average Precision
"Average precision at each position where relevant item appears"
  Higher = better ranking quality
```

---

### 3. Benchmarking: `rag_benchmark.py`

**Run Complete Benchmark:**

```bash
# Test on all 50 questions (may take 5+ minutes)
python rag_benchmark.py

# Test on subset (faster for development)
python rag_benchmark.py --sample-size 10

# Skip reranking (baseline only)
python rag_benchmark.py --skip-reranking

# Analyze by category
python rag_benchmark.py --category-analysis

# Analyze by difficulty
python rag_benchmark.py --difficulty-analysis

# Custom output file
python rag_benchmark.py --output results.json
```

**Output Example:**
```
BASELINE METRICS (Semantic Search Only)
=========================================
  precision@3........................... 0.6234
  precision@5........................... 0.5120
  recall@10............................ 0.7342
  mrr.................................. 0.6891
  ndcg@10.............................. 0.7125
  map@10............................... 0.6543

RERANKED METRICS (With Custom Reranking)
=========================================
  precision@3........................... 0.7856
  precision@5........................... 0.6234
  recall@10............................ 0.8123
  mrr.................................. 0.8234
  ndcg@10.............................. 0.8342
  map@10............................... 0.7891

IMPROVEMENTS FROM RERANKING
=========================================
  precision@3............. 0.6234 → 0.7856  (↑ 25.97%)
  recall@10............... 0.7342 → 0.8123  (↑ 10.63%)
  mrr..................... 0.6891 → 0.8234  (↑ 19.48%)
```

---

### 4. Evaluation Simulator: `rag_evaluation_simulator.py`

**For Testing Without Pinecone Live Connection**

Use this to:
- Test the evaluation system immediately
- Validate metrics calculations
- Demonstrate RAG testing without cloud dependency
- Create mock benchmarks for development

```bash
# Quick demo (10 questions, mock retrieval)
python rag_evaluation_simulator.py

# Larger test (30 questions)
python rag_evaluation_simulator.py --sample-size 30

# Generate HTML report
python rag_evaluation_simulator.py --html-report
```

**Output:**
```
RAG EVALUATION SIMULATION
Questions: 10
Mode: Mock Retrieval (No Pinecone Required)

[Progress bar: ████████████████████] 10/10

BASELINE METRICS (Semantic Search Only)
=========================================
  precision@3..................... 0.5667
  recall@10....................... 0.6234
  mrr............................. 0.5891

IMPROVEMENTS FROM RERANKING
=========================================
  precision@3.. 0.5667 → 0.7234  (↑ 27.61%)
  recall@10.... 0.6234 → 0.8125  (↑ 30.32%)
  mrr.......... 0.5891 → 0.7456  (↑ 26.53%)
```

---

## Quick Start

### Step 1: Verify Setup

```bash
cd scripts/rag_pipeline

# Check all test modules exist
python -c "from rag_test_dataset import get_test_dataset; print(f'Dataset: {len(get_test_dataset())} questions')"
python -c "from rag_evaluation_metrics import RankingEvaluator; print('Metrics: Ready')"
python -c "from rag_evaluation_simulator import RAGEvaluationSimulator; print('Simulator: Ready')"
```

### Step 2: Run Evaluation Simulator (No Pinecone Required)

```bash
# Quick test with mock data
python rag_evaluation_simulator.py --sample-size 10
```

### Step 3: Run Real Benchmark (With Pinecone)

```bash
# First ensure Pinecone is populated:
# 1. Create index via console
# 2. Upload data: python upload_to_pinecone.py --mock-embeddings
# 3. Then run benchmark:

python rag_benchmark.py --sample-size 5
```

### Step 4: Analyze Results

```bash
# All results saved to rag_benchmark_results.json
python -c "
import json
with open('rag_benchmark_results.json') as f:
    results = json.load(f)
    print(f'MRR Score: {results[\"baseline\"][\"mrr\"]:.4f}')
    print(f'P@3: {results[\"baseline\"][\"precision@3\"]:.4f}')
"
```

---

## Interpreting Metrics

### Precision@3 Interpretation

| Score | Meaning | Action |
|-------|---------|--------|
| > 0.80 | Excellent | Keep current system |
| 0.60-0.80 | Good | Minor tweaks needed |
| 0.40-0.60 | Fair | Improve reranking |
| < 0.40 | Poor | Debug retrieval |

### MRR Interpretation

```
MRR Interpretation:
  ≥ 0.8  : Excellent - First relevant site usually in top 2
  0.5-0.8: Good - First relevant site usually in top 3
  0.33-0.5: Fair - First relevant site usually in top 4
  < 0.33: Poor - First relevant site often beyond top 5
```

### Recall Interpretation

```
Higher is better, but context matters:

High Recall (> 0.8) = Found most relevant sites
  ✓ Good for comprehensive search
  ✗ May sacrifice precision

Low Recall (< 0.4) = Missing many relevant sites
  ✗ Need better retrieval
  ✗ Need more diverse embeddings
```

---

## Example: Full Evaluation Workflow

### 1. Test Query: "Buddhist temples in Sri Lanka"

**Ground Truth (Relevant Sites):**
```
- Temple of the Tooth (Kandy)
- Kelaniya Rajamaha Viharaya
- Anuradhapura temples
```

### 2. Baseline Retrieval (Semantic only)

```
Retrieved Results:
1. Kandy City (0.87 score) ✓ RELEVANT
2. Random Museum (0.81 score) ✗ NOT RELEVANT
3. Temple of the Tooth (0.79 score) ✓ RELEVANT
4. Colombo (0.75 score) ✗ NOT RELEVANT
5. Kelaniya Temple (0.72 score) ✓ RELEVANT
...
10. Anuradhapura (0.45 score) ✓ RELEVANT

Baseline Metrics:
  P@3: 2/3 = 0.667
  P@5: 3/5 = 0.600
  Recall@5: 3/3 = 1.000
  MRR: 1/1 = 1.000
```

### 3. Reranked Retrieval (Semantic + Keyword + Metadata)

```
Reranked Results:
1. Temple of the Tooth (0.85 score) ✓ RELEVANT
   Scores: Semantic 0.79 → Keyword 0.90 → Metadata 0.95 = 0.85
2. Kelaniya Temple (0.82 score) ✓ RELEVANT
3. Anuradhapura (0.78 score) ✓ RELEVANT
4. Kandy City (0.65 score) ✓ RELEVANT (bonus)
5. Random Museum (0.42 score) ✗ NOT RELEVANT
...

Reranked Metrics:
  P@3: 3/3 = 1.000   (↑ 50% improvement!)
  P@5: 4/5 = 0.800   (↑ 33% improvement!)
  Recall@5: 4/3 = 1.000 (maintained)
  MRR: 1/1 = 1.000   (maintained)
```

### 4. Comparison

```
Metric        Baseline  Reranked  Improvement
─────────────────────────────────────────────
P@3           0.667     1.000     +50.0%
P@5           0.600     0.800     +33.3%
Recall@5      1.000     1.000     maintained
MRR           1.000     1.000     maintained
```

---

## Expected Performance Targets

### Achievable Benchmarks

**Quality Tier 1 (Current FAISS + Basic Retrieval):**
```
Precision@3: 70-75%
Recall@10:   65-70%
MRR:         0.65-0.70
Expected result: Good search, some irrelevant items
```

**Quality Tier 2 (Semantic + Keyword Reranking):**
```
Precision@3: 80-85%
Recall@10:   75-80%
MRR:         0.75-0.80
Expected result: Most results correct, good ranking
```

**Quality Tier 3 (Advanced - Semantic + Keyword + Metadata + Feedback):**
```
Precision@3: 85-90%
Recall@10:   85-90%
MRR:         0.85-0.90
Expected result: Near-perfect retrieval quality
```

---

## Category-Specific Analysis

### Top Categories by Expected Performance

1. **Ancient Sites** (Easy)
   - Expected P@3: 0.85+ (clear definitions)
   - Example: "ancient rock fortresses" → Sigiriya, Polonnaruwa

2. **Buddhist Temples** (Easy)
   - Expected P@3: 0.82+ (distinct category)
   - Example: "Buddhist temples" → Temple of Tooth, Kelaniya

3. **Forts & Colonial** (Medium)
   - Expected P@3: 0.75+ (clear but overlapping)
   - Example: "forts" → Galle, Matara (may retrieve random sites)

4. **UNESCO Sites** (Hard)
   - Expected P@3: 0.70+ (spans multiple types)
   - Example: "UNESCO" → Mix of ancient, temples, forts

---

## Debugging Poor Results

### If P@3 < 0.65

**Likely causes:**
1. Weak embeddings (using mock instead of real)
   - Solution: Upload with real Azure OpenAI embeddings

2. Reranking not working
   - Solution: Check metadata file exists and loads
   - Solution: Verify category field populated in metadata

3. Too few training examples
   - Solution: Expand historical sites dataset
   - Solution: Add more context per site

**Debug steps:**
```bash
# Check embeddings quality
python -c "
from pinecone_retrieval import PineconeRetrieverWithReranking
r = PineconeRetrieverWithReranking()
results = r.retrieve_with_reranking('ancient temple', top_k=5, rerank_top_k=3)
for result in results['results']:
    print(f\"{result['site_name']}: {result['scores']['combined']:.2%}\")
"

# Check metadata
python -c "
import json
with open('data/rag_vectordb/historical_sites_metadata.json') as f:
    metadata = json.load(f)
    print(f'Total chunks: {len(metadata)}')
    print(f'Sample: {metadata[0]}')
"
```

### If Recall@10 < 0.6

**Likely causes:**
1. Insufficient chunks per document
   - Solution: Reduce chunk size (256 instead of 512)
   - Solution: Reduce overlap (50 instead of 100)

2. Missing relevant sites entirely
   - Solution: Add more sites to CSV
   - Solution: Check data was uploaded to Pinecone

3. Embedding space doesn't capture semantic relationships
   - Solution: Use better embeddings (real Azure)
   - Solution: Fine-tune embedding model (Phase 5)

---

## Phase 3 Checklist

- [ ] Run test dataset loader: `python -c "from rag_test_dataset import get_test_dataset; print(len(get_test_dataset()))"`
- [ ] Run evaluation simulator: `python rag_evaluation_simulator.py --sample-size 5`
- [ ] Verify metrics calculation: `python -c "from rag_evaluation_metrics import RankingEvaluator; e = RankingEvaluator(); m = e.evaluate(['A', 'B', 'C'], ['A', 'B']); print(f'P@3: {m.precision_at_3}')"`
- [ ] Run benchmark on sample: `python rag_benchmark.py --sample-size 5`
- [ ] Check category performance: `python rag_benchmark.py --category-analysis`
- [ ] Save results: `python rag_benchmark.py --output phase3_results.json`
- [ ] Review metrics: `python -c "import json; print(json.load(open('phase3_results.json')))"`

---

## Moving to Phase 4

**Prerequisites for Phase 4 (GPT Integration):**
1. ✅ Retrieval P@3 > 0.70
2. ✅ Retrieval Recall@10 > 0.65
3. ✅ MRR > 0.65

**When ready:**
```bash
# Phase 4 will use the retriever for context
from pinecone_retrieval import PineconeRetrieverWithReranking
from openai import AzureOpenAI

retriever = PineconeRetrieverWithReranking()
context = retriever.retrieve_formatted_context(user_query, top_k=3)
# Use context with GPT → Phase 4 ✓
```

---

## Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `rag_test_dataset.py` | 50 Q&A test pairs | 250 |
| `rag_evaluation_metrics.py` | Metric calculations | 380 |
| `rag_benchmark.py` | Live benchmarking | 350 |
| `rag_evaluation_simulator.py` | Mock benchmarking | 320 |
| `PHASE3_RAG_TESTING.md` | This guide | - |

---

## Resources

- **Information Retrieval:** https://en.wikipedia.org/wiki/Precision_and_recall
- **NDCG:** https://en.wikipedia.org/wiki/Discounted_cumulative_gain
- **MRR:** https://en.wikipedia.org/wiki/Mean_reciprocal_rank
- **BM25:** https://en.wikipedia.org/wiki/Okapi_BM25
- **Pinecone Retrieval:** See PINECONE_RETRIEVAL_GUIDE.md

---

**Phase 3 Status:** ✅ COMPLETE & READY FOR TESTING

Next: Phase 4 - GPT Integration for Chatbot Responses
