#!/usr/bin/env python3
"""Clio M1 Qdrant 初始化脚本"""
import httpx, time, os
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTIONS = {
    "historical_sources_blue": {"vectors": {"size": 1024, "distance": "Cosine"}, "payload_schema": {"source_name": {"type": "keyword", "description": "史料名称，如《史记》"}, "volume": {"type": "keyword", "description": "卷目"}, "dynasty": {"type": "keyword", "description": "朝代"}, "content_type": {"type": "keyword", "description": "文体类型"}, "chunk_text": {"type": "text", "description": "原文片段"}, "chunk_index": {"type": "integer", "description": "片段索引"}, "metadata": {"type": "struct", "description": "其他元数据"}}},
    "historical_sources_green": {"vectors": {"size": 1024, "distance": "Cosine"}, "payload_schema": {"source_name": {"type": "keyword"}, "volume": {"type": "keyword"}, "dynasty": {"type": "keyword"}, "content_type": {"type": "keyword"}, "chunk_text": {"type": "text"}, "chunk_index": {"type": "integer"}, "metadata": {"type": "struct"}}},
    "qa_cache": {"vectors": {"size": 1024, "distance": "Cosine"}, "payload_schema": {"question": {"type": "text", "description": "用户问题"}, "answer": {"type": "text", "description": "标准答案"}, "source": {"type": "keyword", "description": "来源"}, "created_at": {"type": "datetime"}}}
}
def wait_for_qdrant(timeout=30):
    client = httpx.Client(timeout=5.0)
    start = time.time()
    while time.time() - start < timeout:
        try:
            if client.get(f"{QDRANT_URL}/readyz").status_code == 200:
                return True
        except: pass
        time.sleep(1)
    return False
def collection_exists(name):
    return httpx.get(f"{QDRANT_URL}/collections/{name}", timeout=10.0).status_code == 200
def create_collection(name, config):
    payload = {"vectors": config["vectors"]}
    if "payload_schema" in config: payload["payload_schema"] = config["payload_schema"]
    r = httpx.put(f"{QDRANT_URL}/collections/{name}", json=payload, timeout=30.0)
    if r.status_code in (200, 201): print(f"  ✅ Created: {name}")
    else: print(f"  ❌ Failed {name}: {r.text}"); r.raise_for_status()
def set_alias(alias, collection):
    r = httpx.post(f"{QDRANT_URL}/collections/aliases", json={"actions": [{"create_alias": {"alias_name": alias, "collection_name": collection}}]}, timeout=10.0)
    if r.status_code == 200: print(f"  ✅ Alias: {alias} → {collection}")
    else: print(f"  ❌ Alias failed: {r.text}")
def main():
    print("🚀 等待 Qdrant..."); 
    if not wait_for_qdrant(): print("❌ 超时"); raise SystemExit(1)
    print("✅ Qdrant 就绪\n")
    for name, config in COLLECTIONS.items():
        if collection_exists(name): print(f"  ⏭️  已存在: {name}")
        else: create_collection(name, config)
    set_alias("historical_sources", "historical_sources_blue")
    print("\n📋 Collections:")
    for c in httpx.get(f"{QDRANT_URL}/collections", timeout=10.0).json()["result"]["collections"]: print(f"  - {c['name']}")
    print("\n✅ 完成！")
if __name__ == "__main__": main()
