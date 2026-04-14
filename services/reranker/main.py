"""Clio Reranker 服务 — BAAI/bge-reranker-v2-m3"""
import os, time
from contextlib import asynccontextmanager
from typing import List, Optional
import torch, uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import AutoModelForSequenceClassification, AutoTokenizer

DEVICE = os.getenv("DEVICE", "cpu")
MODEL_NAME = os.getenv("MODEL_NAME", "BAAI/bge-reranker-v2-m3")

if DEVICE == "cuda" and torch.cuda.is_available():
    device = "cuda"
elif DEVICE == "mps" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

reranker_model: Optional[AutoModelForSequenceClassification] = None
reranker_tokenizer: Optional[AutoTokenizer] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global reranker_model, reranker_tokenizer
    print(f"📦 Loading {MODEL_NAME} on {device}...")
    reranker_tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    reranker_model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    reranker_model.to(device)
    reranker_model.eval()
    yield
    reranker_model = None
    reranker_tokenizer = None

app = FastAPI(title="Clio Reranker API", lifespan=lifespan)

class RerankRequest(BaseModel):
    query: str = Field(..., description="查询文本")
    documents: List[str] = Field(..., description="待重排序的文档列表")
    top_k: int = Field(default=5, ge=1)

class RerankResultItem(BaseModel):
    index: int; score: float; text: str

class RerankResponse(BaseModel):
    results: List[RerankResultItem]; model: str; device: str; latency_ms: float

class HealthResponse(BaseModel):
    status: str; model: str; device: str; model_loaded: bool

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="healthy", model=MODEL_NAME, device=device, model_loaded=reranker_model is not None)

@app.post("/rerank", response_model=RerankResponse)
def rerank(req: RerankRequest):
    if reranker_model is None or reranker_tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    if not req.documents:
        raise HTTPException(status_code=400, detail="documents cannot be empty")
    start = time.perf_counter()
    inputs = reranker_tokenizer([req.query]*len(req.documents), req.documents, return_tensors="pt", padding=True, truncation=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        scores = reranker_model(**inputs).logits.squeeze().tolist()
    if isinstance(scores, float): scores = [scores]
    results = sorted([RerankResultItem(index=i, score=round(float(s), 4), text=doc) for i,(s,doc) in enumerate(zip(scores, req.documents))], key=lambda x: x.score, reverse=True)[:req.top_k]
    return RerankResponse(results=results, model=MODEL_NAME, device=device, latency_ms=round((time.perf_counter()-start)*1000, 2))

if __name__ == "__main__": uvicorn.run("main:app", host="0.0.0.0", port=8002)
