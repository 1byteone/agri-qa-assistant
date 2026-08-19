import urllib.request, json

def test(method, url, data=None):
    try:
        req = urllib.request.Request(url, method=method,
            data=json.dumps(data).encode() if data else None,
            headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        body = resp.read().decode()
        print(f"[{method}] {url} -> {resp.status}")
        print(f"  Body: {body[:300]}")
        return True
    except urllib.error.HTTPError as e:
        print(f"[{method}] {url} -> {e.code}")
        print(f"  Body: {e.read().decode()[:500]}")
        return False
    except Exception as e:
        print(f"[{method}] {url} -> ERROR: {e}")
        return False

test("GET", "http://localhost:8001/health")
test("POST", "http://localhost:8001/chat", {"message": "你好", "thread_id": "debug_conn"})