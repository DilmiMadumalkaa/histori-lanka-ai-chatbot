# Setup Instructions for Windows

## Prerequisites
- Python 3.9 or higher
- Git for version control
- 10GB free disk space

## Step-by-Step Setup

### 1. Clone Repository
```bash
git clone <your_repo_url>
cd historical-sites-chatbot
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Create .env and add your keys if available:
# AZURE_OPENAI_API_KEY=...
# AZURE_OPENAI_ENDPOINT=...
# AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
# PINECONE_API_KEY=...
```

### 5. Collect and Prepare Data (Sri Lanka Sources)
```bash
python scripts/rag_pipeline/sri_lanka_research_pipeline.py --step collect
python scripts/rag_pipeline/sri_lanka_research_pipeline.py --step review
python scripts/rag_pipeline/sri_lanka_research_pipeline.py --step chunk
python scripts/rag_pipeline/sri_lanka_research_pipeline.py --step embed --allow-mock-embeddings
```

### 6. Run Chat Interface (Mock)
```bash
python scripts/rag_pipeline/chat_interface.py --mock
```

### 7. Optional Live Vector Search (Requires Azure + Pinecone keys)
```bash
python scripts/rag_pipeline/sri_lanka_research_pipeline.py --step all --index-name historical-sites-sl
python scripts/rag_pipeline/sri_lanka_research_pipeline.py --step test --index-name historical-sites-sl
```