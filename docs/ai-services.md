# Clio AI 服务接口文档

> Embedding + Reranker API，下游依赖：⑧向量化入库、⑩RAG检索、⑫语义缓存。
> 接口格式评审通过后即为合约，后续变更需双方确认。

---

## 一、Embedding 服务（端口 8001）

**模型**：BAAI/bge-large-zh-v1.5，向量维度 1024，Cosine 相似度

### GET /health

```json
{
  "status": "healthy",
  "model": "BAAI/bge-large-zh-v1.5",
  "device": "cpu",
  "model_loaded": true
}
```

### POST /embed — 单条向量化

**请求**：
```json
{
  "text": "贞观之治是唐太宗李世民在位期间的治世局面",
  "instruction": "为这段历史文本生成向量表示"
}
```

**响应**：
```json
{
  "vector": [0.0234, -0.0512, "..."],
  "dimension": 1024,
  "model": "BAAI/bge-large-zh-v1.5",
  "device": "cpu",
  "latency_ms": 82.3
}
```

### POST /embed/batch — 批量向量化

**请求**：
```json
{
  "texts": ["贞观之治是唐太宗...", "玄武门之变发生于..."],
  "instruction": "为这段历史文本生成向量表示",
  "batch_size": 32
}
```

**响应**：
```json
{
  "vectors": [[0.0234, ...], [0.0178, ...]],
  "dimension": 1024,
  "count": 2,
  "model": "BAAI/bge-large-zh-v1.5",
  "device": "cpu",
  "latency_ms": 125.6
}
```

---

## 二、Reranker 服务（端口 8002）

**模型**：BAAI/bge-reranker-v2-m3

### GET /health

```json
{
  "status": "healthy",
  "model": "BAAI/bge-reranker-v2-m3",
  "device": "cpu",
  "model_loaded": true
}
```

### POST /rerank — 文档重排序

**请求**：
```json
{
  "query": "唐太宗如何治理国家",
  "documents": [
    "贞观之治是唐太宗李世民在位期间...",
    "唐太宗推行均田制和租庸调制...",
    "安史之乱是唐朝由盛转衰的转折点..."
  ],
  "top_k": 5
}
```

**响应**：
```json
{
  "results": [
    {"index": 0, "score": 0.9823, "text": "贞观之治是唐太宗..."},
    {"index": 1, "score": 0.9156, "text": "唐太宗推行均田制..."},
    {"index": 2, "score": 0.2134, "text": "安史之乱是唐朝..."}
  ],
  "model": "BAAI/bge-reranker-v2-m3",
  "device": "cpu",
  "latency_ms": 285.4
}
```

---

## 三、一键启动（Mac M5 本地）

```bash
# Step 1: 启动数据层（任务③）
docker compose -f docker-compose.dev.yml up -d
python scripts/init_qdrant.py   # 仅首次

# Step 2: 启动 AI 服务
docker compose -f docker-compose.ai.yml up -d

# Step 3: 验证
curl http://localhost:8001/health   # Embedding
curl http://localhost:8002/health   # Reranker
```

## 四、性能参考（Mac M5 实测）

| 指标 | Mac M5 CPU | Linux GPU T4 |
|------|-----------|---------------|
| Embedding 单条 | ~80ms | ~12ms |
| Embedding batch=32 | ~600ms | ~50ms |
| Reranker 10 篇 | ~300ms | ~35ms |

全部使用 `DEVICE=cpu` 启动，迁移时改为 `DEVICE=cuda`，代码零改动。
