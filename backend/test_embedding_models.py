import os
import pytest
import requests

API_KEY = os.environ.get("AGNES_AI_API_KEY", "")
BASE_URL = os.environ.get("AGNES_BASE_URL", "https://apihub.agnes-ai.cn/v1")

MODELS_TO_TRY = [
    "text-embedding-ada-002",
    "text-embedding-3-small",
    "text-embedding-3-large",
    "agnes-2.0-flash",
    "embedding-2.0-flash",
    "embedding-2-small",
]


@pytest.mark.skipif(not API_KEY, reason="需要设置 AGNES_AI_API_KEY 环境变量")
@pytest.mark.parametrize("model", MODELS_TO_TRY)
def test_embedding_model(model):
    url = f"{BASE_URL}/embeddings"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "input": ["test"]}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    # 至少部分模型应该可用，记录结果
    print(f"Model: {model} -> Status: {r.status_code}")