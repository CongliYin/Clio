# Clio 本地开发环境 - 一键启动指南

> 5 分钟内完成本地数据层启动，适用于 CongliYin 本地开发。

## 前置要求

- Docker 24.0+（Mac 需 Docker Desktop）
- Docker Compose v2.20+
- Python 3.10+（仅首次初始化 Qdrant 需要）

## 快速启动

```bash
# Step 1：拉取最新代码
git pull origin main

# Step 2：配置环境变量
cp .env.dev.example .env
# .env 内容已默认适配本地开发，无需修改

# Step 3：启动数据层服务
docker compose -f docker-compose.dev.yml up -d

# Step 4：初始化 Qdrant Collection（仅首次）
python3 scripts/init_qdrant.py

# Step 5：验证
docker compose -f docker-compose.dev.yml ps
```

## 验证命令

```bash
# 验证 PostgreSQL 7 张表
docker exec clio_pg psql -U clio -d clio_db -c "\dt"

# 验证索引
docker exec clio_pg psql -U clio -d clio_db -c "\di"

# 验证 Redis（密码：clio_dev_2026）
docker exec clio_redis redis-cli -a clio_dev_2026 ping

# 验证 Qdrant
curl http://localhost:6333/collections
# 期望：historical_sources_blue, historical_sources_green, qa_cache
```

## 服务连接信息

| 服务 | 连接地址 |
|------|----------|
| PostgreSQL | `postgresql://clio:clio_dev_2026@localhost:5432/clio_db` |
| Redis | `redis://:clio_dev_2026@localhost:6379/0` |
| Qdrant | `http://localhost:6333` |

## 常见问题

**Q：PostgreSQL 连接报错？**
确认 `.env` 里 `DATABASE_URL` 正确，且 `docker compose ps` 中 clio_pg 状态为 running。

**Q：Redis 认证失败？**
确认密码为 `clio_dev_2026`（`.env` 中 `REDIS_PASSWORD`）。

**Q：Qdrant Collection 创建失败？**
确认 6333/6334 端口未被占用，首次需运行 `python3 scripts/init_qdrant.py`。

**Q：想停止服务？**
```bash
docker compose -f docker-compose.dev.yml down
```

**Q：想清空数据重新开始？**
```bash
docker compose -f docker-compose.dev.yml down -v  # -v 会删除数据卷
```

## 环境变量（可选）

`.env.dev.example` 中所有值均有默认值，可按需覆盖：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PG_PORT` | 5432 | PostgreSQL 端口 |
| `REDIS_PORT` | 6379 | Redis 端口 |
| `QDRANT_HTTP_PORT` | 6333 | Qdrant HTTP 端口 |
| `DEVICE` | cpu | 推理设备（cpu/cuda/mps）|

## 迁移到服务器

将 `.env` 中的 `localhost` 替换为服务器 IP，Docker Compose 配置零改动。
