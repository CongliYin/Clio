# Clio 本地开发环境 - 一键启动指南

## 前置要求
- Docker 24.0+（Mac 需 Docker Desktop）
- Docker Compose v2.20+
- Python 3.10+（仅首次初始化 Qdrant 需要）

## 快速启动
```bash
git pull origin main
cp .env.dev.example .env
docker compose -f docker-compose.dev.yml up -d
python3 scripts/init_qdrant.py    # 仅首次
```

## 验证
```bash
docker compose -f docker-compose.dev.yml ps
docker exec clio_pg psql -U clio -d clio_db -c "\\dt"   # 7张表
docker exec clio_redis redis-cli -a clio_dev_2026 ping  # PONG
curl http://localhost:6333/collections                   # 3个Collection
```

## 服务连接
| 服务 | 连接地址 |
|------|----------|
| PostgreSQL | `postgresql://clio:clio_dev_2026@localhost:5432/clio_db` |
| Redis | `redis://:clio_dev_2026@localhost:6379/0` |
| Qdrant | `http://localhost:6333` |

## 迁移到服务器
将 `.env` 中 `localhost` 改为服务器 IP，零代码改动。
