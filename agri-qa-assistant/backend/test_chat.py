import json
import urllib.request
from urllib.error import HTTPError

payload = json.dumps({
    "message": "How do I grow tomatoes?",
    "thread_id": "test-thread-1",
    "user_id": "test-user"
}).encode()

req = urllib.request.Request(
    "http://localhost:8000/chat",
    data=payload,
    headers={"Content-Type": "application/json"}
)

try:
    resp = urllib.request.urlopen(req)
    print("Status:", resp.status)
    print("Body:", resp.read().decode())
except HTTPError as e:
    print("Status:", e.code)
    print("Body:", e.read().decode())