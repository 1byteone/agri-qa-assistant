import http.client, json

# 模拟浏览器跨域 preflight (OPTIONS)
conn = http.client.HTTPConnection("localhost", 8001, timeout=10)
conn.request("OPTIONS", "/chat",
    headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
resp = conn.getresponse()
print("=== PREFLIGHT ===")
print("Status:", resp.status)
for h, v in resp.getheaders():
    if "access-control" in h.lower() or "allow" in h.lower():
        print(f"  {h}: {v}")
conn.close()

# 模拟实际 POST（带 Origin）
conn = http.client.HTTPConnection("localhost", 8001, timeout=60)
body = json.dumps({"message": "水稻怎么种", "thread_id": "cors_test"}).encode()
conn.request("POST", "/chat", body=body,
    headers={
        "Origin": "http://localhost:3000",
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
    })
resp = conn.getresponse()
print("\n=== POST ===")
print("Status:", resp.status)
for h, v in resp.getheaders():
    if "access-control" in h.lower():
        print(f"  {h}: {v}")
print("  Body:", resp.read().decode()[:200])
conn.close()