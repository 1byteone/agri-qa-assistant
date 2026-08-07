/* 诊断：鼠标事件是否到达 LayerGL.onmousemove + picking 是否命中散点
   运行: node diag_gl_events.js */
const { chromium } = require('C:/Users/FFY/node_modules/playwright-core');
const CHROME = 'C:/Users/FFY/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe';
const DASH_URL = 'http://127.0.0.1:8000/digital_twin_pro.html';

(async () => {
  const browser = await chromium.launch({
    executablePath: CHROME, headless: true,
    args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--force-color-profile=srgb'],
  });
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 } });
  const page = await ctx.newPage();
  const errs = [], pageErrors = [];
  page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('pageerror', (e) => pageErrors.push(String(e)));
  await page.goto(DASH_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForFunction(() => document.querySelector('#map-chart canvas'), { timeout: 25000 });
  await page.waitForTimeout(4000);

  // 打桩：统计 LayerGL.onmousemove / pickObject 调用，以及 tooltip 是否出现
  await page.evaluate(() => {
    const chart = echarts.getInstanceByDom(document.getElementById('map-chart'));
    const zr = chart.getZr();
    const layers = zr.painter.getLayers();
    window.__stats = { layerMoves: 0, pickHits: 0, geo3dDots: 0 };
    for (const k in layers) {
      const L = layers[k];
      if (!L.views) continue;
      const origMove = L.onmousemove.bind(L);
      const origPick = L.pickObject.bind(L);
      L.onmousemove = (e) => { window.__stats.layerMoves++; return origMove(e); };
      L.pickObject = (x, y) => {
        const r = origPick(x, y);
        if (r && r.target) {
          window.__stats.pickHits++;
          window.__stats.hitMesh = { seriesIndex: r.target.seriesIndex, dataIndex: r.target.dataIndex, isPoints: !!r.target._positionNDC };
        }
        return r;
      };
    }
    // 同时统计散点 mesh 数量
    window.__stats.dotsMesh = 0;
    for (const k in layers) {
      const L = layers[k];
      if (!L.views) continue;
      for (const v of L.views) {
        if (!v.scene || !v.scene.traverse) continue;
        v.scene.traverse((m) => { if (m && m._positionNDC) window.__stats.dotsMesh++; });
      }
    }
  });

  // 读取第一个散点坐标
  const dots = await page.evaluate(() => {
    const chart = echarts.getInstanceByDom(document.getElementById('map-chart'));
    const zr = chart.getZr();
    const layers = zr.painter.getLayers();
    const out = [];
    for (const k in layers) {
      const L = layers[k];
      if (!L.views) continue;
      for (const v of L.views) {
        if (!v.scene || !v.scene.traverse) continue;
        let mesh = null;
        v.scene.traverse((m) => { if (m && m._positionNDC) mesh = m; });
        if (!mesh) continue;
        const vp = v.viewport;
        const ndc = mesh._positionNDC;
        for (let i = 0; i < ndc.length / 2; i++) {
          const x = Math.round((ndc[2 * i] + 1) / 2 * vp.width + vp.x);
          const y = Math.round((1 - ndc[2 * i + 1]) / 2 * vp.height + vp.y);
          out.push({ x, y });
        }
      }
    }
    return out;
  });
  console.log('DOTS', JSON.stringify(dots.slice(0, 5)));

  const readTip = () => page.evaluate(() => {
    const divs = document.querySelectorAll('#map-chart div');
    for (const el of divs) {
      if (el.style && el.style.position === 'absolute' && (el.textContent || '').trim()) return (el.textContent || '').trim().slice(0, 80);
    }
    return null;
  });

  // 1) 移动到第一个散点
  if (dots.length) {
    await page.mouse.move(dots[0].x, dots[0].y);
    await page.waitForTimeout(400);
    console.log('AFTER MOVE1 stats', JSON.stringify(await page.evaluate(() => window.__stats)), 'tip:', JSON.stringify(await readTip()));
    // 2) 再快速扫过一片区域
    for (let i = 0; i < 30; i++) {
      await page.mouse.move(200 + (i % 10) * 90, 200 + Math.floor(i / 10) * 150);
    }
    await page.waitForTimeout(400);
    console.log('AFTER SCAN stats', JSON.stringify(await page.evaluate(() => window.__stats)), 'tip:', JSON.stringify(await readTip()));
  }
  console.log('ERRORS', JSON.stringify({ errs, pageErrors }));
  await browser.close();
})().catch((e) => { console.error('FATAL', e); process.exit(1); });