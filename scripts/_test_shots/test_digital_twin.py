# -*- coding: utf-8 -*-
import json, sys, io, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:8000/digital_twin_pro.html'
SHOT_DIR = r'd:\code\codeByCursor\AI_EXAM\_test_shots'
os.makedirs(SHOT_DIR, exist_ok=True)

errors = []
warnings = []
pageerrors = []
reqfail = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=[
        '--use-angle=swiftshader',
        '--enable-unsafe-swiftshader',
        '--no-sandbox',
    ])
    ctx = browser.new_context(viewport={'width': 1600, 'height': 900})
    page = ctx.new_page()

    page.on('console', lambda m: (
        errors.append(m.text) if m.type == 'error' else None,
        warnings.append(m.text) if m.type == 'warning' else None,
    ))
    page.on('pageerror', lambda e: pageerrors.append(str(e)))
    page.on('requestfailed', lambda r: reqfail.append(f"{r.url} -> {r.failure}"))

    page.goto(URL, wait_until='domcontentloaded', timeout=30000)
    # 等待 26s：加载 + echarts-gl WebGL 渲染 + 飞线动画
    time.sleep(26)

    state = page.evaluate('''() => {
      const q = s => document.querySelector(s);
      const g = id => document.getElementById(id);
      const txt = el => el ? (el.textContent || '').trim() : null;
      const canvases = [...document.querySelectorAll('#map-area canvas')].map(c => ({
        w: c.width, h: c.height, cw: c.clientWidth, ch: c.clientHeight
      }));
      return {
        loadingHidden: g('loading-overlay') ? g('loading-overlay').classList.contains('hidden') : null,
        loadingText: txt(g('loading-text')),
        loadingTextColor: g('loading-text') ? getComputedStyle(g('loading-text')).color : null,
        kpiText: txt(g('kpi-grid')),
        rankText: (txt(g('ranking-list')) || '').slice(0, 300),
        structureSvgs: document.querySelectorAll('#structure-panel svg, .structure-panel svg, #structure-chart svg').length,
        structureText: (txt(g('structure-panel')) || txt(g('structure-chart')) || '').slice(0, 200),
        mapCanvases: canvases,
        mapChartExists: !!g('map-chart'),
        flylineBtn: txt(g('flyline-toggle')),
        rotateBtn: txt(g('map-rotate-toggle')),
        webgl: (() => { try { const c = document.createElement('canvas'); return !!(c.getContext('webgl') || c.getContext('experimental-webgl')); } catch(e) { return false; } })(),
      };
    }''')

    page.screenshot(path=os.path.join(SHOT_DIR, 'digital_twin_full.png'), full_page=False)

    # 尝试读取地图 canvas 像素统计（WebGL canvas 需 preserveDrawingBuffer，可能为空，作为辅助）
    pixel = page.evaluate('''() => {
      const c = document.querySelector('#map-area canvas');
      if (!c) return null;
      try {
        const g = c.getContext('webgl') || c.getContext('experimental-webgl');
        const w = c.width, h = c.height;
        const buf = new Uint8Array(w * h * 4);
        g.readPixels(0, 0, w, h, g.RGBA, g.UNSIGNED_BYTE, buf);
        let nonBlank = 0, cyan = 0, amber = 0;
        for (let i = 0; i < buf.length; i += 4) {
          const r = buf[i], gg = buf[i+1], b = buf[i+2], a = buf[i+3];
          if (a > 0 && (r + gg + b) > 30) nonBlank++;
          if (gg > 120 && r < 120 && b > 60) cyan++;
          if (r > 150 && gg > 80 && b < 120) amber++;
        }
        return { w, h, nonBlank, cyan, amber, total: w * h };
      } catch (e) { return { err: String(e) }; }
    }''')

    browser.close()

result = {
    'console_errors': errors,
    'console_warnings': warnings,
    'page_errors': pageerrors,
    'request_failures': reqfail,
    'dom_state': state,
    'webgl_pixel_stats': pixel,
}
out = os.path.join(SHOT_DIR, 'result.json')
with open(out, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print('=== CONSOLE ERRORS (%d) ===' % len(errors))
for e in errors[:30]: print('  [err]', e[:300])
print('=== PAGE ERRORS (%d) ===' % len(pageerrors))
for e in pageerrors[:30]: print('  [pageerror]', e[:300])
print('=== WARNINGS (%d) ===' % len(warnings))
for w in warnings[:30]: print('  [warn]', w[:300])
print('=== REQUEST FAILURES (%d) ===' % len(reqfail))
for r in reqfail[:30]: print('  [reqfail]', r[:300])
print('=== DOM STATE ===')
print(json.dumps(state, ensure_ascii=False, indent=2))
print('=== WEBGL PIXEL ===')
print(json.dumps(pixel, ensure_ascii=False, indent=2))
print('RESULT_JSON:', out)