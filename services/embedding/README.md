# Clio Embedding 服务

模型：`BAAI/bge-large-zh-v1.5`，向量维度 1024，Cosine 相似度。

## 快速启动

```bash
# 本地开发
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DEVICE=cpu uvicorn main:app --reload --port 8001

# Docker
docker build -t clio-embedding .
docker run --rm -p 8001:8001 -e DEVICE=cpu clio-embedding
```

## API

| 端点 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `POST /embed` | 单条向量化 |
| `POST /embed/batch` | 批量向量化（最大 128 条）|

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEVICE` | cpu | 推理设备（cpu / cuda / mps）|
| `MODEL_NAME` | BAAI/bge-large-zh-v1.5 | 模型名称 |

## 设备迁移

本地开发用 `DEVICE=cpu`，迁移到 GPU 服务器时改为 `DEVICE=cuda`，**服务代码零改动**。
