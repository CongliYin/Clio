#!/usr/bin/env python3
"""
Clio M1 Qdrant 初始化脚本
创建 Collection + 别名（historical_sources_blue / historical_sources_green / qa_cache）
"""

import httpx
import time
import os

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

COLLECTIONS = {
    "historical_sources_blue": {
        "vectors": {"size": 1024, "distance": "Cosine"},
        "payload_schema": {
            "source_name":   {"type": "keyword", "description": "史料名称，如《史记》"},
            "volume":        {"type": "keyword", "description": "卷目，如本纪·五帝本纪"},
            "dynasty":       {"type": "keyword", "description": "朝代，如上古、西汉"},
            "content_type":  {"type": "keyword", "description": "文体类型，如纪传体"},
            "chunk_text":    {"type": "text",    "description": "原文片段"},
            "chunk_index":   {"type": "integer", "description": "片段索引"},
            "metadata":       {"type": "struct",  "description": "其他元数据"},
        },
    },
    "historical_sources_green": {
        "vectors": {"size": 1024, "distance": "Cosine"},
        "payload_schema": {
            "source_name":   {"type": "keyword"},
            "volume":        {"type": "keyword"},
            "dynasty":       {"type": "keyword"},
            "content_type":  {"type": "keyword"},
            "chunk_text":    {"type": "text"},
            "chunk_index":   {"type": "integer"},
            "metadata":       {"type": "struct"},
        },
    },
    "qa_cache": {
        "vectors": {"size": 1024, "distance": "Cosine"},
        "payload_schema": {
            "question":  {"type": "text",    "description": "用户问题"},
            "answer":    {"type": "text",    "description": "标准答案"},
            "source":    {"type": "keyword", "description": "来源"},
            "created_at":{"type": "datetime"},
        },
    },
}


def wait_for_qdrant(timeout: int = 30) -> bool:
    client = httpx.Client(timeout=5.0)
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = client.get(f"{QDRANT_URL}/readyz")
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def collection_exists(name: str) -> bool:
    r = httpx.get(f"{QDRANT_URL}/collections/{name}", timeout=10.0)
    return r.status_code == 200


def create_collection(name: str, config: dict) -> None:
    payload = {"vectors": config["vectors"]}
    if "payload_schema" in config:
        payload["payload_schema"] = config["payload_schema"]

    r = httpx.put(
        f"{QDRANT_URL}/collections/{name}",
        json=payload,
        timeout=30.0,
    )
    if r.status_code in (200, 201):
        print(f"  ✅ Created collection: {name}")
    else:
        print(f"  ❌ Failed to create {name}: {r.text}")
        r.raise_for_status()


def set_alias(alias: str, collection: str) -> None:
    # Qdrant 1.8+ requires POST /collections/aliases
    r = httpx.post(
        f"{QDRANT_URL}/collections/aliases",
        json={
            "actions": [
                {
                    "create_alias": {
                        "alias_name": alias,
                        "collection_name": collection,
                    }
                }
            ]
        },
        timeout=10.0,
    )
    if r.status_code == 200:
        print(f"  ✅ Alias set: {alias} → {collection}")
    else:
        print(f"  ❌ Failed to set alias {alias}: {r.text}")


def main():
    print("🚀 等待 Qdrant 启动...")
    if not wait_for_qdrant():
        print("❌ Qdrant 启动超时")
        raise SystemExit(1)
    print("✅ Qdrant 已就绪\n")

    for name, config in COLLECTIONS.items():
        if collection_exists(name):
            print(f"  ⏭️  Collection 已存在: {name}，跳过")
        else:
            create_collection(name, config)

    set_alias("historical_sources", "historical_sources_blue")

    print("\n📋 验证 Collections:")
    r = httpx.get(f"{QDRANT_URL}/collections", timeout=10.0)
    data = r.json()
    for coll in data.get("result", {}).get("collections", []):
        print(f"  - {coll['name']}")

    print("\n📋 验证 Aliases:")
    r = httpx.get(f"{QDRANT_URL}/aliases", timeout=10.0)
    aliases = r.json().get("result", {}).get("aliases", [])
    for a in aliases:
        print(f"  - {a['alias_name']} → {a['collection_name']}")

    print("\n✅ Qdrant 初始化完成！")


if __name__ == "__main__":
    main()
