# Clio Embedding 服务
模型：`BAAI/bge-large-zh-v1.5`，维度1024，Cosine相似度

## 启动
```bash
# 本地
pip install -r requirements.txt && DEVICE=cpu uvicorn main:app --reload --port 8001
# Docker
docker build -t clio-embedding . && docker run -p 8001:8001 -e DEVICE=cpu clio-embedding
```

## API
- `GET /health`
- `POST /embed` 单条
- `POST /embed/batch` 批量（最大128条）
