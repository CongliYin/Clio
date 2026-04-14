"""
Clio Embedding 服务
模型：BAAI/bge-large-zh-v1.5
向量维度：1024
"""

import os
import time
from contextlib import asynccontextmanager
from typing import List, Optional

import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

# ── 设备选择 ────────────────────────────────────────────
DEVICE = os.getenv("DEVICE", "cpu")
MODEL_NAME = os.getenv("MODEL_NAME", "BAAI/bge-large-zh-v1.5")

if DEVICE == "cuda" and torch.cuda.is_available():
    device = "cuda"
elif DEVICE == "mps" and torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

# ── 全局模型（启动时加载）────────────────────────────────
model: Optional[SentenceTransformer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    print(f"📦 正在加载模型 {MODEL_NAME} 到 {device} ...")
    model = SentenceTransformer(MODEL_NAME, device=device)
    print(f"✅ 模型加载完成，当前设备: {model.device}")
    yield
    # shutdown 时不做特殊清理
    model = None


app = FastAPI(title="Clio Embedding API", lifespan=lifespan)


# ── Schemas ──────────────────────────────────────────────
class EmbedRequest(BaseModel):
    text: str = Field(..., description="待向量化的文本")
    instruction: str = Field(
        default="为这段历史文本生成向量表示",
        description="可选指令，用于优化向量质量",
    )


class EmbedResponse(BaseModel):
    vector: List[float]
    dimension: int
    model: str
    device: str
    latency_ms: float


class BatchEmbedRequest(BaseModel):
    texts: List[str] = Field(..., description="批量待向量化的文本")
    instruction: str = Field(
        default="为这段历史文本生成向量表示",
        description="可选指令",
    )
    batch_size: int = Field(default=32, ge=1, le=128, description="批大小")


class BatchEmbedResponse(BaseModel):
    vectors: List[List[float]]
    dimension: int
    count: int
    model: str
    device: str
    latency_ms: float


class HealthResponse(BaseModel):
    status: str
    model: str
    device: str
    model_loaded: bool


# ── Routes ───────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="healthy",
        model=MODEL_NAME,
        device=str(model.device) if model else device,
        model_loaded=model is not None,
    )


@app.post("/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    text = req.text
    if req.instruction:
        text = f"{req.instruction} {req.text}"

    start = time.perf_counter()
    embedding = model.encode(text, normalize_embeddings=True)
    latency_ms = (time.perf_counter() - start) * 1000

    return EmbedResponse(
        vector=embedding.tolist(),
        dimension=len(embedding),
        model=MODEL_NAME,
        device=str(model.device),
        latency_ms=round(latency_ms, 2),
    )


@app.post("/embed/batch", response_model=BatchEmbedResponse)
def embed_batch(req: BatchEmbedRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    texts = req.texts
    if req.instruction:
        texts = [f"{req.instruction} {t}" for t in texts]

    start = time.perf_counter()
    embeddings = model.encode(
        texts,
        batch_size=req.batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    return BatchEmbedResponse(
        vectors=[emb.tolist() for emb in embeddings],
        dimension=embeddings.shape[1],
        count=len(embeddings),
        model=MODEL_NAME,
        device=str(model.device),
        latency_ms=round(latency_ms, 2),
    )


# ── 启动 ─────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001)
