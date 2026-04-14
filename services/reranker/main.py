"""
Clio Reranker 服务
模型：BAAI/bge-reranker-v2-m3
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
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# ── 设备选择 ────────────────────────────────────────────
DEVICE = os.getenv("DEVICE", "cpu")
MODEL_NAME = os.getenv("MODEL_NAME", "BAAI/bge-reranker-v2-m3")

if DEVICE == "cuda" and torch.cuda.is_available():
    device = "cuda"
elif DEVICE == "mps" and torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

# ── 全局模型（启动时加载）────────────────────────────────
model: Optional[AutoModelForSequenceClassification] = None
tokenizer: Optional[AutoTokenizer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer
    print(f"📦 正在加载模型 {MODEL_NAME} 到 {device} ...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.to(device)
    model.eval()
    print(f"✅ 模型加载完成，当前设备: {device}")
    yield
    model = None
    tokenizer = None


app = FastAPI(title="Clio Reranker API", lifespan=lifespan)


# ── Schemas ──────────────────────────────────────────────
class RerankRequest(BaseModel):
    query: str = Field(..., description="查询文本")
    documents: List[str] = Field(..., description="待重排序的文档列表")
    top_k: int = Field(default=5, ge=1, description="返回 top_k 条结果")


class RerankResultItem(BaseModel):
    index: int
    score: float
    text: str


class RerankResponse(BaseModel):
    results: List[RerankResultItem]
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
        device=device,
        model_loaded=model is not None,
    )


@app.post("/rerank", response_model=RerankResponse)
def rerank(req: RerankRequest):
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    if not req.documents:
        raise HTTPException(status_code=400, detail="documents cannot be empty")

    start = time.perf_counter()

    # Tokenize all query-document pairs
    inputs = tokenizer(
        [req.query] * len(req.documents),
        req.documents,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        scores = model(**inputs).logits.squeeze().tolist()

    # 构建结果列表
    results = [
        RerankResultItem(index=i, score=round(float(s), 4), text=doc)
        for i, (s, doc) in enumerate(zip(scores, req.documents))
    ]

    # 按 score 降序排列
    results.sort(key=lambda x: x.score, reverse=True)
    top_results = results[: req.top_k]

    latency_ms = (time.perf_counter() - start) * 1000

    return RerankResponse(
        results=top_results,
        model=MODEL_NAME,
        device=device,
        latency_ms=round(latency_ms, 2),
    )


# ── 启动 ─────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002)
