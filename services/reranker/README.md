# Clio Reranker 服务

模型：`BAAI/bge-reranker-v2-m3`

## 快速启动

```bash
# 本地开发
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DEVICE=cpu uvicorn main:app --reload --port 8002

# Docker
docker build -t clio-reranker .
docker run --rm -p 8002:8002 -e DEVICE=cpu clio-reranker
```

## API

| 端点 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `POST /rerank` | 文档重排序 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEVICE` | cpu | 推理设备（cpu / cuda / mps）|
| `MODEL_NAME` | BAAI/bge-reranker-v2-m3 | 模型名称 |

## 设备迁移

本地开发用 `DEVICE=cpu`，迁移到 GPU 服务器时改为 `DEVICE=cuda`，**服务代码零改动**。
