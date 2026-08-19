import os
import pytest
import requests

API_KEY = os.environ.get("AGNES_AI_API_KEY", "")
BASE_URL = os.environ.get("AGNES_BASE_URL", "https://apihub.agnes-ai.cn/v1")


@pytest.mark.skipif(not API_KEY, reason="需要设置 AGNES_AI_API_KEY 环境变量")
def test_list_models():
    url = f"{BASE_URL}/models"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    r = requests.get(url, headers=headers, timeout=30)
    assert r.status_code == 200, f"模型列表返回非 200: {r.status_code}"
    data = r.json()
    assert "data" in data, "响应缺少 data 字段"
    print(f"可用模型数: {len(data['data'])}")