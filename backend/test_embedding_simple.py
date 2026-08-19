import requests

url = "https://apihub.agnes-ai.cn/v1/embeddings"
headers = {
    "Authorization": "Bearer sk-H2xBJlVMLMLiM9tplNS4zeBchkmVa87ZyAZjZWJVfkLLYWHq",
    "Content-Type": "application/json",
}

model = "text-embedding-ada-002"
payload = {"model": model, "input": ["test"]}

try:
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Model: {model}")
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")