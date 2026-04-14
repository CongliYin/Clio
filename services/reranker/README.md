# Clio Reranker 服务
模型：`BAAI/bge-reranker-v2-m3`

## 启动
```bash
# 本地
pip install -r requirements.txt && DEVICE=cpu uvicorn main:app --reload --port 8002
# Docker
docker build -t clio-reranker . && docker run -p 8002:8002 -e DEVICE=cpu clio-reranker
```

## API
- `GET /health`
- `POST /rerank` 文档重排序
