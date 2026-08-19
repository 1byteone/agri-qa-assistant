import requests

url = "https://apihub.agnes-ai.cn/v1/embeddings"
headers = {
    "Authorization": "Bearer sk-H2xBJlVMLMLiM9tplNS4zeBchkmVa87ZyAZjZWJVfkLLYWHq",
    "Content-Type": "application/json",
}

models_to_try = [
    "text-embedding-ada-002",
    "text-embedding-3-small",
    "text-embedding-3-large",
    "agnes-2.0-flash",
    "embedding-2.0-flash",
    "embedding-2-small",
]

for model in models_to_try:
    payload = {"model": model, "input": ["test"]}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Model: {model} -> Status: {r.status_code}")
        if r.status_code == 200:
            print(f"  SUCCESS! Response: {r.text[:200]}")
            break
        else:
            print(f"  Error: {r.text[:200]}")
    except Exception as e:
        print(f"Model: {model} -> Error: {e}")