import requests

url = "https://apihub.agnes-ai.cn/v1/models"
headers = {
    "Authorization": "Bearer sk-H2xBJlVMLMLiM9tplNS4zeBchkmVa87ZyAZjZWJVfkLLYWHq",
}

try:
    r = requests.get(url, headers=headers, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:2000]}")
except Exception as e:
    print(f"Error: {e}")