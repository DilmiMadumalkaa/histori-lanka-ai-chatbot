# Phase 4: Quick Reference Guide
## GPT Integration - Common Tasks & Commands

---

## One-Liner Cheat Sheet

```python
# Single response generation
from gpt_response_generator import ResponseGenerator
gen = ResponseGenerator()
r = gen.generate_response("What is Sigiriya?", "Context here...")
print(r["response"])

# Interactive chat
python chat_interface.py --mock

# Run all tests
python phase4_integration_tests.py --mock --export

# Quality evaluation
from response_evaluator import ResponseEvaluator
evaluator = ResponseEvaluator()
eval = evaluator.evaluate_response(query, response, context)
print(f"Score: {eval['overall_score']}/1.0")

# Change response style
# Options: historian, guide, educator, researcher, child
python chat_interface.py --mock --query "Tell me about Sigiriya"
```

---

## Common Tasks

### Task 1: Generate Single Response

```python
from gpt_response_generator import ResponseGenerator

gen = ResponseGenerator()
result = gen.generate_response(
    user_query="Tell me about Sigiriya",
    context="Sigiriya is a rock fortress...",
    style="historian"  # or: guide, educator, researcher, child
)

print(result["response"])
print(f"Quality: {result['quality']['rating']}")
```

### Task 2: End-to-End with Retrieval

```python
from gpt_response_generator import ResponseGenerator
from rag_evaluation_simulator import MockRetriever  # or real retriever

retriever = MockRetriever()
gen = ResponseGenerator()

query = "Tell me about ancient Buddhist kingdoms"
context = retriever.retrieve_formatted_context(query, top_k=3)
result = gen.generate_response(query, context, style="educator")

print(result["response"])
```

### Task 3: Evaluate Response Quality

```python
from response_evaluator import ResponseEvaluator

evaluator = ResponseEvaluator()
eval = evaluator.evaluate_response(
    user_query="When was Sigiriya built?",
    response="Sigiriya was built in 5th century...",
    context="Context here..."
)

print(f"Overall: {eval['overall_score']}/1.0 ({eval['quality_rating']})")
print(f"Relevance: {eval['metrics']['relevance']['score']}")
print(f"Hallucination Risk: {eval['metrics']['hallucination_risk']['risk_level']}")
```

### Task 4: Interactive Chat Session

```bash
# Start chat
python chat_interface.py --mock

# In chat:
# 1. Type question: "Tell me about Anuradhapura"
# 2. Change style: "style educator"
# 3. Show history: "history"
# 4. Export: "export"
# 5. Exit: "quit"
```

### Task 5: Batch Process Multiple Queries

```python
from gpt_response_generator import ResponseGenerator
from rag_evaluation_simulator import MockRetriever

queries = [
    "Sigiriya fortress",
    "Temple of the Tooth",
    "Anuradhapura kingdom"
]

gen = ResponseGenerator()
retriever = MockRetriever()

for q in queries:
    print(f"\nQuery: {q}")
    context = retriever.retrieve_formatted_context(q, top_k=2)
    result = gen.generate_response(q, context, style="guide")
    print(f"Response: {result['response'][:100]}...")
    print(f"Quality: {result['quality']['rating']}")
```

### Task 6: Compare Response Styles

```python
from gpt_response_generator import ResponseGenerator

gen = ResponseGenerator()
query = "What is the significance of the Temple of the Tooth?"
context = "Temple context here..."

styles = ["historian", "guide", "educator", "researcher"]

for style in styles:
    result = gen.generate_response(query, context, style=style)
    print(f"\n{style.upper()}:")
    print(result["response"][:150] + "...")
```

### Task 7: Test Error Handling

```python
from gpt_response_generator import ResponseGenerator

gen = ResponseGenerator()

# Empty query
r1 = gen.generate_response("", "context")
print(f"Empty query: {r1.get('success', 'handled')}")

# Very long query (5000 chars)
long_q = "test " * 1000
r2 = gen.generate_response(long_q, "context")
print(f"Long query: {r2.get('success', 'handled')}")

# No context
r3 = gen.generate_response("question", "")
print(f"No context: {r3.get('success', 'handled')}")
```

### Task 8: Run Comprehensive Tests

```bash
# All tests with mock (no external deps)
python phase4_integration_tests.py --mock --export

# Results saved to: phase4_test_results_YYYYMMDD_HHMMSS.json

# View results
cat phase4_test_results_*.json | grep -A 20 "TEST SUMMARY"
```

---

## Response Styles Explained

| Style | Best For | Example |
|-------|----------|---------|
| **historian** | Research, detailed accuracy | "Archaeological evidence reveals..." |
| **guide** | Tourists, practical info | "It's 147 meters high! You can see..." |
| **educator** | Teaching, learning | "Sigiriya teaches us..., which was important because..." |
| **researcher** | Academic papers | "Methodologically, the dating analysis indicates..." |
| **child** | Young learners | "Imagine a giant rock standing tall..." |

---

## Quality Metrics Quick Guide

| Metric | What It Measures | Good Score |
|--------|------------------|-----------|
| **Relevance** | Does response answer the question? | > 0.7 |
| **Factual Grounding** | Are claims supported by context? | > 0.7 |
| **Completeness** | Is all important info included? | > 0.6 |
| **Coherence** | Is it well-written and organized? | > 0.7 |
| **Hallucination Risk** | Low/Medium/High - Likely to make up info? | Low |
| **Citation Quality** | Are sources properly indicated? | > 0.6 |
| **Specificity** | Concrete details vs generic language? | > 0.5 |
| **Length** | Appropriate for the question? | > 0.8 |

**Overall Score = Weighted average (target: > 0.70 = good quality)**

---

## Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| **"API key not found"** | `export AZURE_OPENAI_API_KEY="your_key"; export AZURE_OPENAI_ENDPOINT="https://..."` |
| **"Module not found"** | `pip install openai --upgrade` |
| **"Connection timeout"** | Check endpoint URL, verify firewall, try again |
| **"Low quality score"** | Increase context (`top_k=5`), lower temperature to 0.5 |
| **"Hallucination detected"** | Use "researcher" style, reduce `max_tokens`, increase context |
| **"Slow response"** | Use mock retriever, reduce `max_tokens`, set `temperature=0.3` |

---

## Performance Targets

| Operation | Target | Your Result |
|-----------|--------|------------|
| Single response generation | < 5 sec | _____ |
| Retrieval + generation | < 10 sec | _____ |
| Quality evaluation | < 2 sec | _____ |
| Batch 5 queries | < 50 sec | _____ |
| Quality score | > 0.70 | _____ |
| Hallucination risk | Low | _____ |

---

## File Organization

```
scripts/rag_pipeline/
├── gpt_response_generator.py      ← Main generator class
├── prompt_templates.py             ← Prompt engineering
├── response_evaluator.py           ← Quality metrics
├── chat_interface.py               ← Interactive interface
├── phase4_integration_tests.py     ← Test suite
└── PHASE4_GPT_INTEGRATION.md      ← Full documentation
```

---

## Development Checklist

```
[ ] Response generation works (demo runs)
[ ] Prompt templates available for all 5 roles
[ ] Quality evaluation returns 8 metrics
[ ] Chat interface responds to queries
[ ] Integration tests pass (6/7 categories minimum)
[ ] Error handling graceful
[ ] Performance < 10 seconds per query
[ ] Quality scores > 0.65 average
[ ] Documentation complete
[ ] Ready for production
```

---

## Useful Environment Variables

```bash
# Set temporarily
export AZURE_OPENAI_API_KEY="pksk_..."
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"

# Or in .env (permanent)
cat .env
AZURE_OPENAI_API_KEY=pksk_...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Verify loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(bool(os.getenv('AZURE_OPENAI_API_KEY')))"
```

---

## Additional Resources

```
Related Phases:
- Phase 2: scripts/rag_pipeline/RAG_PIPELINE_GUIDE.md
- Phase 3: PHASE3_RAG_TESTING.md
- Data: data/processed/comprehensive_historical_sites_merged.csv

Installation:
- pip install openai python-dotenv pinecone-client

Key Classes:
- ResponseGenerator - Generate responses using GPT
- PromptBuilder - Build optimized prompts
- ResponseEvaluator - Assess quality (8 metrics)
- ChatInterface - Interactive chat
- Phase4TestSuite - Comprehensive tests
```

---

**Last Updated:** 2024-01-15 | **Phase 4 Version:** 1.0
