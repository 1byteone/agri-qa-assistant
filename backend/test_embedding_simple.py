import os
import pytest
import requests

API_KEY = os.environ.get("AGNES_AI_API_KEY", "")
BASE_URL = os.environ.get("AGNES_BASE_URL", "https://apihub.agnes-ai.cn/v1")


@pytest.mark.skipif(not API_KEY, reason="需要设置 AGNES_AI_API_KEY 环境变量")
def test_embedding_simple():
    url = f"{BASE_URL}/embeddings"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    model = "text-embedding-ada-002"
    payload = {"model": model, "input": ["test"]}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    assert r.status_code == 200, f"模型 {model} 返回非 200: {r.status_code}"