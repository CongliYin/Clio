"""Clio Embedding 服务 — BAAI/bge-large-zh-v1.5，维度1024"""
import os, time
from contextlib import asynccontextmanager
from typing import List, Optional
import torch, uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

DEVICE = os.getenv("DEVICE", "cpu")
MODEL_NAME = os.getenv("MODEL_NAME", "BAAI/bge-large-zh-v1.5")

if DEVICE == "cuda" and torch.cuda.is_available():
    device = "cuda"
elif DEVICE == "mps" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

model: Optional[SentenceTransformer] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    print(f"📦 Loading {MODEL_NAME} on {device}...")
    model = SentenceTransformer(MODEL_NAME, device=device)
    yield
    model = None

app = FastAPI(title="Clio Embedding API", lifespan=lifespan)

class EmbedRequest(BaseModel):
    text: str = Field(..., description="待向量化的文本")
    instruction: str = Field(default="为这段历史文本生成向量表示", description="可选指令")

class EmbedResponse(BaseModel):
    vector: List[float]; dimension: int; model: str; device: str; latency_ms: float

class BatchEmbedRequest(BaseModel):
    texts: List[str] = Field(...); instruction: str = Field(default="为这段历史文本生成向量表示"); batch_size: int = Field(default=32, ge=1, le=128)

class BatchEmbedResponse(BaseModel):
    vectors: List[List[float]]; dimension: int; count: int; model: str; device: str; latency_ms: float

class HealthResponse(BaseModel):
    status: str; model: str; device: str; model_loaded: bool

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="healthy", model=MODEL_NAME, device=str(model.device) if model else device, model_loaded=model is not None)

@app.post("/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest):
    if model is None: raise HTTPException(status_code=503, detail="Model not loaded yet")
    text = f"{req.instruction} {req.text}" if req.instruction else req.text
    start = time.perf_counter()
    emb = model.encode(text, normalize_embeddings=True)
    return EmbedResponse(vector=emb.tolist(), dimension=len(emb), model=MODEL_NAME, device=str(model.device), latency_ms=round((time.perf_counter()-start)*1000, 2))

@app.post("/embed/batch", response_model=BatchEmbedResponse)
def embed_batch(req: BatchEmbedRequest):
    if model is None: raise HTTPException(status_code=503, detail="Model not loaded yet")
    texts = [f"{req.instruction} {t}" for t in req.texts] if req.instruction else req.texts
    start = time.perf_counter()
    embs = model.encode(texts, batch_size=req.batch_size, normalize_embeddings=True, show_progress_bar=False)
    return BatchEmbedResponse(vectors=[e.tolist() for e in embs], dimension=embs.shape[1], count=len(embs), model=MODEL_NAME, device=str(model.device), latency_ms=round((time.perf_counter()-start)*1000, 2))

if __name__ == "__main__": uvicorn.run("main:app", host="0.0.0.0", port=8001)
