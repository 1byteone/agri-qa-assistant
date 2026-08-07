# -*- coding: utf-8 -*-
"""鉴权 + 数据校验 端到端实测脚本（仅 stdlib）。"""
import csv
import io
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8001"
TOKEN = open("auth_token.txt", encoding="utf-8").read().strip()

results = []


def call(method, path, body=None, token=None, headers=None):
    url = BASE + path
    data = None
    hdrs = {"Content-Type": "application/json"} if body is not None else {}
    if headers:
        hdrs.update(headers)
    if token is not None:
        hdrs["Authorization"] = "Bearer " + token
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def t(name, method, path, body=None, token=None, expect=None, headers=None):
    code, resp = call(method, path, body, token, headers)
    ok = expect is None or code == expect
    results.append((name, code, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: HTTP {code}"
          + (f" (expect {expect})" if expect else ""))
    return code, resp


# 1. 读接口公开
t("GET /api/records 无token", "GET", "/api/records?page_size=1", expect=200)
t("GET /api/dashboard 无token", "GET", "/api/dashboard", expect=200)

# 2. 写接口必须带 token
t("POST /api/records 无token", "POST", "/api/records",
  {"year": 2024, "province": "测试省", "crop": "测试作物", "indicator": "产量",
   "unit": "吨", "value": 1}, expect=401)
t("POST /api/records 错误token", "POST", "/api/records",
  {"year": 2024, "province": "测试省", "crop": "测试作物", "indicator": "产量",
   "unit": "吨", "value": 1}, token="WRONG-TOKEN", expect=401)

# 3. 正确 token → 201，随后清理
code, resp = t("POST /api/records 正确token", "POST", "/api/records",
               {"year": 2024, "province": "测试省", "crop": "测试作物",
                "indicator": "产量", "unit": "吨", "value": 123.45,
                "source": "auth-test"}, token=TOKEN, expect=201)
fact_id = None
if code == 201:
    fact_id = json.loads(resp).get("fact_id")
    print(f"   created fact_id={fact_id}")

# 4. import/csv 无 token → 401（发送真实 CSV 文件体，验证鉴权先于入库）
_csv = ("年份,省份,品类,指标,数值,单位\n"
        "2024,测试省,测试作物,产量,100,吨\n").encode("utf-8")
_b = "----authTestBoundary"
_import_body = (f"--{_b}\r\nContent-Disposition: form-data; name=\"file\"; "
                f"filename=\"t.csv\"\r\nContent-Type: text/csv\r\n\r\n").encode() + \
    _csv + f"\r\n--{_b}--\r\n".encode()
t("POST /api/import/csv 无token(真实文件)", "POST", "/api/import/csv",
  headers={"Content-Type": f"multipart/form-data; boundary={_b}"}, expect=401)
# 注：call() 的 body 参数仅用于 JSON；此处需手工发 multipart
# （上方用 headers 构造，实际用下面的手工请求重测）
_req = urllib.request.Request(
    BASE + "/api/import/csv", data=_import_body, method="POST",
    headers={"Content-Type": f"multipart/form-data; boundary={_b}"})
try:
    with urllib.request.urlopen(_req, timeout=15) as r:
        _code, _ok = r.status, False
except urllib.error.HTTPError as e:
    _code, _ok = e.code, True
print(f"[{'PASS' if _ok and _code == 401 else 'FAIL'}] "
      f"POST /api/import/csv 无token(真实文件体): HTTP {_code} (expect 401)")

# 5. auth endpoints
t("GET /api/auth/status", "GET", "/api/auth/status", expect=200)
code, resp = call("POST", "/api/auth/verify", token=TOKEN)
print(f"[{'PASS' if code == 200 and json.loads(resp)['valid'] else 'FAIL'}] "
      f"POST /api/auth/verify 正确token: valid={json.loads(resp)['valid'] if code == 200 else resp}")
code, resp = call("POST", "/api/auth/verify", token="WRONG")
print(f"[{'PASS' if code == 200 and not json.loads(resp)['valid'] else 'FAIL'}] "
      f"POST /api/auth/verify 错误token: valid={json.loads(resp)['valid'] if code == 200 else resp}")

# 6. Pydantic 校验：value=-5 → 422；year 越界 → 422；NaN → 422
t("POST value=-5 → 422", "POST", "/api/records",
  {"year": 2024, "province": "测试省", "crop": "测试作物", "indicator": "产量",
   "unit": "吨", "value": -5}, token=TOKEN, expect=422)
t("POST year=1980 → 422", "POST", "/api/records",
  {"year": 1980, "province": "测试省", "crop": "测试作物", "indicator": "产量",
   "unit": "吨", "value": 5}, token=TOKEN, expect=422)
t("POST value=NaN → 422", "POST", "/api/records",
  {"year": 2024, "province": "测试省", "crop": "测试作物", "indicator": "产量",
   "unit": "吨", "value": float("nan")}, token=TOKEN, expect=422)

# 7. 导入行级校验：负值行 / 超限行 → failed 计入行号
buf = io.StringIO()
w = csv.writer(buf)
w.writerow(["年份", "省份", "品类", "指标", "数值", "单位"])
w.writerow([2024, "测试省", "测试作物", "产量", 100, "吨"])          # 合法
w.writerow([2024, "测试省", "测试作物", "产量", -50, "吨"])         # 负值
w.writerow([2024, "测试省", "测试作物", "面积", 99999999, "亩"])   # 超限
w.writerow([2024, "测试省", "测试作物", "产量", "abc", "吨"])      # 非数字
payload = buf.getvalue().encode("utf-8")
boundary = "----authTestBoundary"
body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"t.csv\"\r\nContent-Type: text/csv\r\n\r\n").encode() + payload + \
    f"\r\n--{boundary}--\r\n".encode()
req = urllib.request.Request(
    BASE + "/api/import/csv", data=body, method="POST",
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
             "Authorization": "Bearer " + TOKEN})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        report = json.loads(r.read().decode("utf-8"))
        print(f"[{'PASS' if report['failed_rows'] == 3 else 'FAIL'}] "
              f"导入行级校验: total={report['total_rows']} failed={report['failed_rows']} "
              f"(expect failed=3)")
        for d in report["failed_details"]:
            print("   ", d)
except urllib.error.HTTPError as e:
    print(f"[FAIL] 导入请求异常 HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}")

# 8. 清理测试记录
if fact_id:
    t(f"DELETE /api/records/{fact_id} 清理", "DELETE", f"/api/records/{fact_id}",
      token=TOKEN, expect=200)

print("\n===== SUMMARY =====")
fails = [r for r in results if not r[2]]
print(f"total={len(results)} pass={len(results) - len(fails)} fail={len(fails)}")
for name, code, ok in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {name} -> {code}")
if fails:
    raise SystemExit(1)