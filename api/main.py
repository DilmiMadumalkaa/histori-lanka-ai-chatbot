from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# Ensure imports resolve for the existing RAG pipeline modules.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAG_PIPELINE_DIR = PROJECT_ROOT / "scripts" / "rag_pipeline"
if str(RAG_PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_PIPELINE_DIR))

from chat_interface import ChatInterface  # noqa: E402


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query")
    style: str = Field(default="informative", description="Response style")


class ChatResponse(BaseModel):
    success: bool
    query: str
    response: Optional[str] = None
    model: Optional[str] = None
    retrieved_sites_count: Optional[int] = None
    retrieved_sites: Optional[List[str]] = None
    quality_score: Optional[float] = None
    quality_rating: Optional[str] = None
    raw: Dict[str, Any]


app = FastAPI(title="Historical Sites Chat API", version="1.0.0")


def _build_allowed_origins() -> List[str]:
    configured = os.getenv("ALLOWED_ORIGINS", "")
    configured_origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    local_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    # Keep deterministic order and remove duplicates.
    return list(dict.fromkeys(local_origins + configured_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_allowed_origins(),
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


chat_service: Optional[ChatInterface] = None


@app.on_event("startup")
def startup_event() -> None:
    global chat_service
    # Real mode uses fine-tuned GPT + Pinecone retriever.
    chat_service = ChatInterface(use_mock=False)


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if chat_service is None:
        raise HTTPException(status_code=500, detail="Chat service not initialized")

    result = chat_service.get_response(request.query, style=request.style)
    if not result.get("success", False):
        error_msg = result.get("error", "Unknown error")
        raise HTTPException(status_code=500, detail=error_msg)

    evaluation = result.get("evaluation", {})

    return ChatResponse(
        success=True,
        query=request.query,
        response=result.get("response"),
        model=result.get("model"),
        retrieved_sites_count=result.get("retrieved_sites_count"),
        retrieved_sites=result.get("retrieved_sites"),
        quality_score=evaluation.get("overall_score"),
        quality_rating=evaluation.get("quality_rating"),
        raw=result,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
