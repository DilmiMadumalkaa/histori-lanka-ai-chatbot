# Sri Lankan Historical Sites Tourism Chatbot

## Research Project
Developing a multilingual LLM-based chatbot for Sri Lankan historical tourism using fine-tuning and RAG.

## Project Structure
- Core code: `scripts/`
- Data artifacts: `data/`
- Technical documentation: `docs/`

## Quick Start
1. Create virtual environment: `python -m venv venv`
2. Activate: `venv\Scripts\activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Configure environment variables in `.env`
5. Run source-restricted Sri Lanka pipeline:
	`python scripts/rag_pipeline/sri_lanka_research_pipeline.py --step all --allow-mock-embeddings`

## Research Timeline
- Week 1-3: Data collection (155+ historical sites)
- Week 4-5: Fine-tuning dataset creation
- Week 6-8: Fine-tuning and RAG integration
- Week 9-10: Evaluation and deployment

## Documentation
See:
- `docs/project/` for project-level guides
- `docs/rag_pipeline/` for RAG implementation guides

running commands
uvicorn api.main:app --host 127.0.0.1 --port 8001
cd frontend
npm run dev