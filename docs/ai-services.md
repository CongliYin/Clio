# Clio AI 服务接口文档

> Embedding + Reranker API，下游依赖：⑧向量化入库、⑩RAG检索、⑫语义缓存。
> 接口格式评审通过后即为合约，后续变更需双方确认。

## 一、Embedding 服务（端口 8001）
**模型**：BAAI/bge-large-zh-v1.5，维度1024，Cosine相似度

### GET /health
```json
{"status": "healthy", "model": "BAAI/bge-large-zh-v1.5", "device": "cpu", "model_loaded": true}
```

### POST /embed
```json
// 请求
{"text": "贞观之治是唐太宗李世民在位期间的治世局面", "instruction": "为这段历史文本生成向量表示"}
// 响应
{"vector": [0.0234, -0.0512, "..."], "dimension": 1024, "model": "bge-large-zh-v1.5", "device": "cpu", "latency_ms": 82.3}
```

### POST /embed/batch
```json
// 请求
{"texts": ["贞观之治...", "玄武门之变..."], "instruction": "为这段历史文本生成向量表示", "batch_size": 32}
// 响应
{"vectors": [[0.0234,...], [0.0178,...]], "dimension": 1024, "count": 2, "model": "bge-large-zh-v1.5", "device": "cpu", "latency_ms": 125.6}
```

## 二、Reranker 服务（端口 8002）
**模型**：BAAI/bge-reranker-v2-m3

### GET /health
```json
{"status": "healthy", "model": "BAAI/bge-reranker-v2-m3", "device": "cpu", "model_loaded": true}
```

### POST /rerank
```json
// 请求
{"query": "唐太宗如何治理国家", "documents": ["贞观之治是唐太宗...", "唐太宗推行均田制...", "安史之乱是唐朝..."], "top_k": 5}
// 响应
{"results": [{"index": 0, "score": 0.9823, "text": "贞观之治..."}, {"index": 1, "score": 0.9156, "text": "唐太宗推行均田制..."}], "model": "bge-reranker-v2-m3", "device": "cpu", "latency_ms": 285.4}
```

## 三、一键启动（Mac M5 本地）
```bash
# 数据层（任务③）
docker compose -f docker-compose.dev.yml up -d
python scripts/init_qdrant.py

# AI服务
docker compose -f docker-compose.ai.yml up -d

# 验证
curl http://localhost:8001/health   # Embedding
curl http://localhost:8002/health   # Reranker
```

## 四、性能参考（Mac M5 实测）

| 指标 | Mac M5 CPU | Linux GPU T4 |
|------|-----------|------------|
| Embedding 单条 | ~80ms | ~12ms |
| Embedding batch=32 | ~600ms | ~50ms |
| Reranker 10篇 | ~300ms | ~35ms |

全部使用 `DEVICE=cpu` 启动，迁移时改为 `DEVICE=cuda`，代码零改动。
