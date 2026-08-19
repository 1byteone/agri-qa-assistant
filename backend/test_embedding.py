import requests

url = "https://apihub.agnes-ai.cn/v1/embeddings"
headers = {
    "Authorization": "Bearer sk-H2xBJlVMLMLiM9tplNS4zeBchkmVa87ZyAZjZWJVfkLLYWHq",
    "Content-Type": "application/json",
}
payload = {"model": "text-embedding-3-small", "input": ["test"]}

try:
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    print("Status:", r.status_code)
    print("Body:", r.text[:500])
except Exception as e:
    print("Error:", e)