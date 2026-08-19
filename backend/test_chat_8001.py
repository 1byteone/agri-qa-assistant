import urllib.request
import json

payload = json.dumps({
    "message": "你好",
    "thread_id": "test-thread-1"
}).encode()

req = urllib.request.Request(
    "http://localhost:8001/chat",
    data=payload,
    headers={"Content-Type": "application/json"}
)

try:
    resp = urllib.request.urlopen(req)
    print("Status:", resp.status)
    print("Body:", resp.read().decode())
except urllib.error.HTTPError as e:
    print("Status:", e.code)
    print("Body:", e.read().decode())
except Exception as e:
    print("Error:", e)