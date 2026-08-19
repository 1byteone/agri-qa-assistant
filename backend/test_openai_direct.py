import os
import httpx

proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
api_key = os.environ.get("AGNES_API_KEY", "")

print(f"Proxy: {proxy}")
print(f"API key length: {len(api_key)}")
print(f"API key: {api_key}")

from openai import OpenAI

# Try with /v1 suffix on api.agnes-ai.cn
client = OpenAI(
    api_key=api_key,
    base_url="https://api.agnes-ai.cn/v1",
    http_client=httpx.Client(proxy=proxy) if proxy else None,
)

try:
    response = client.chat.completions.create(
        model="agnes-2.5-flash",
        messages=[{"role": "user", "content": "你好，请用一句话回复"}],
        max_tokens=50,
    )
    print("Success!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Response status: {e.response.status_code}")
        print(f"Response body: {e.response.text[:500]}")