import urllib.request
import json

# 模拟前端 fetch 调用
payload = json.dumps({
    "message": "水稻稻飞虱怎么防治？",
    "thread_id": "verify-thread"
}).encode()

req = urllib.request.Request(
    "http://localhost:8001/chat",
    data=payload,
    headers={"Content-Type": "application/json"}
)

try:
    resp = urllib.request.urlopen(req, timeout=60)
    print("Status:", resp.status)
    print("Body:", resp.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP Status:", e.code)
    print("Body:", e.read().decode())
except Exception as e:
    print("Network Error:", type(e).__name__, e)