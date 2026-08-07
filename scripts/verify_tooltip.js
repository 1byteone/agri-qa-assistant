/* 验证脚本：任务1（API 配置化）+ 任务2（tooltip 覆盖层）
   运行: node verify_tooltip.js [scenario]
   scenario: geo3d-candidate | final
*/
const { chromium } = require('C:/Users/FFY/node_modules/playwright-core');
const CHROME = 'C:/Users/FFY/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe';
const DASH_URL = 'http://127.0.0.1:8000/digital_twin_pro.html';
const SHOT_DIR = 'tooltip_shots';
const fs = require('fs');
if (!fs.existsSync(SHOT_DIR)) fs.mkdirSync(SHOT_DIR);

const scenario = process.argv[2] || 'final';

// 在页面内提取 scatter3D 散点的屏幕像素坐标（借助 clay 预计算的 NDC 位置）
const extractDots = () => {
  const chart = echarts.getInstanceByDom(document.getElementById('map-chart'));
  if (!chart) return { error: 'no chart', dots: [] };
  const zr = chart.getZr();
  const layers = zr.painter && zr.painter.getLayers ? zr.painter.getLayers() : {};
  const dots = [];
  for (const k in layers) {
    const L = layers[k];
    if (!L.views) continue;
    for (const v of L.views) {
      if (!v.scene || !v.scene.traverse) continue;
      let mesh = null;
      v.scene.traverse((m) => { if (m && m._positionNDC) mesh = m; });
      if (!mesh || !mesh._positionNDC) continue;
      const vp = v.viewport || {};
      const ndc = mesh._positionNDC;
      for (let i = 0; i < ndc.length / 2; i++) {
        const x = Math.round((ndc[2 * i] + 1) / 2 * (vp.width || 0) + (vp.x || 0));
        const y = Math.round((1 - ndc[2 * i + 1]) / 2 * (vp.height || 0) + (vp.y || 0));
        dots.push({ x, y });
      }
    }
  }
  return { dots, layerKeys: Object.keys(layers) };
};

// 检查 #map-chart 内是否出现可见的 echarts tooltip 及内容
const readTooltip = () => {
  const chart = document.getElementById('map-chart');
  if (!chart) return null;
  const divs = chart.querySelectorAll('div');
  for (const d of divs) {
    const st = d.style || {};
    const isAbs = st.position === 'absolute';
    const txt = (d.textContent || '').trim();
    if (isAbs && txt && !d.querySelector('canvas')) {
      return { text: txt.slice(0, 120), display: st.display };
    }
  }
  return null;
};

async function newPage(browser, ctxOpts) {
  const ctx = await browser.newContext(ctxOpts || { viewport: { width: 1600, height: 900 } });
  const page = await ctx.newPage();
  const consoleErrors = [], pageErrors = [], failedReqs = [], logs = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); logs.push(`[${m.type()}] ${m.text()}`); });
  page.on('pageerror', (e) => pageErrors.push(String(e)));
  page.on('requestfailed', (r) => { if (!r.url().includes('geo.datav')) failedReqs.push(`${r.url()} :: ${r.failure()?.errorText}`); });
  return { ctx, page, consoleErrors, pageErrors, failedReqs, logs };
}

async function waitReady(page) {
  await page.goto(DASH_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForFunction(() => document.getElementById('data-source-indicator')?.textContent, { timeout: 25000 }).catch(() => {});
  await page.waitForFunction(() => document.querySelector('#map-chart canvas'), { timeout: 25000 }).catch(() => {});
  await page.waitForTimeout(3500); // GL 渲染 + 动画
}

(async () => {
  const browser = await chromium.launch({
    executablePath: CHROME, headless: true,
    args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--force-color-profile=srgb'],
  });
  const out = { scenario, runs: {} };

  if (scenario === 'geo3d-candidate') {
    // 候选1实测：geo3D 组件级 tooltip 是否生效 —— hover 地图区域本体（非散点处）
    const { ctx, page, consoleErrors, pageErrors, failedReqs, logs } = await newPage(browser);
    await waitReady(page);
    const dotsInfo = await page.evaluate(extractDots);
    // 找一个远离散点的“地图本体”位置：以散点均值中心为中心，向旁偏移 120px
    const dots = dotsInfo.dots || [];
    const cx = Math.round(dots.reduce((s, d) => s + d.x, 0) / Math.max(dots.length, 1));
    const cy = Math.round(dots.reduce((s, d) => s + d.y, 0) / Math.max(dots.length, 1));
    const far = { x: Math.min(cx + 140, 1100), y: Math.min(cy + 110, 780) };
    const near = dots.filter(d => Math.hypot(d.x - far.x, d.y - far.y) < 30).length;
    await page.mouse.move(far.x, far.y);
    await page.waitForTimeout(600);
    const tip = await page.evaluate(readTooltip);
    await page.mouse.move(10, 10);
    await page.waitForTimeout(300);
    await page.screenshot({ path: `${SHOT_DIR}/geo3d_candidate_hover.png` });
    out.runs.geo3dCandidate = {
      hoverPoint: far, dotsCount: dots.length, nearDots: near,
      tooltipAfterHover: tip,
      consoleErrors, pageErrors, failedReqs,
      ds: await page.evaluate(() => document.getElementById('data-source-indicator')?.textContent),
    };
    await ctx.close();
  } else {
    // ===== A. 默认路径：API 数据源 + 散点 hover tooltip =====
    {
      const { ctx, page, consoleErrors, pageErrors, failedReqs, logs } = await newPage(browser);
      await waitReady(page);
      const ds = await page.evaluate(() => {
        const el = document.getElementById('data-source-indicator');
        return { text: el?.textContent, title: el?.title, color: el?.style?.color };
      });
      const dotsInfo = await page.evaluate(extractDots);
      const dots = dotsInfo.dots || [];
      // 依次 hover 各散点直到出现 tooltip
      let hit = null;
      for (const d of dots.slice(0, 40)) {
        await page.mouse.move(d.x, d.y);
        await page.waitForTimeout(120);
        const tip = await page.evaluate(readTooltip);
        if (tip && tip.text) { hit = { point: d, tip }; break; }
      }
      if (hit) {
        await page.waitForTimeout(200);
        await page.screenshot({ path: `${SHOT_DIR}/tooltip_hover.png` });
        // 再移开，确认 tooltip 消失（hide 正常）
        await page.mouse.move(20, 20);
        await page.waitForTimeout(350);
        hit.afterLeave = await page.evaluate(readTooltip);
      }
      out.runs.apiMode = {
        ds, dotsCount: dots.length, layerKeys: dotsInfo.layerKeys,
        hit, consoleErrors, pageErrors, failedReqs,
        dsLogs: logs.filter(l => l.includes('数据源') || l.includes('DigitalTwin') || l.includes('回退')),
      };
      await ctx.close();
    }
    // ===== B. URL 参数 ?apiBase= 覆盖 + 兜底 =====
    {
      const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 } });
      const page = await ctx.newPage();
      const consoleErrors = [], pageErrors = [], failedReqs = [], logs = [];
      page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); logs.push(`[${m.type()}] ${m.text()}`); });
      page.on('pageerror', (e) => pageErrors.push(String(e)));
      await page.goto(DASH_URL + '?apiBase=http://127.0.0.1:9999', { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForFunction(() => document.getElementById('data-source-indicator')?.textContent, { timeout: 25000 }).catch(() => {});
      await page.waitForTimeout(7000); // 等待 4s 超时 + 静态兜底
      out.runs.urlParamOverride = {
        ds: await page.evaluate(() => {
          const el = document.getElementById('data-source-indicator');
          return { text: el?.textContent, title: el?.title };
        }),
        logs: logs.filter(l => l.includes('数据源') || l.includes('回退') || l.includes('API 不可用')),
        consoleErrors, pageErrors,
      };
      await page.screenshot({ path: `${SHOT_DIR}/urlparam_static.png` });
      await ctx.close();
    }
    // ===== C. window.__AGRI_API_BASE__ 覆盖 + 兜底 =====
    {
      const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 } });
      const page = await ctx.newPage();
      await page.addInitScript(() => { window.__AGRI_API_BASE__ = 'http://127.0.0.1:9998'; });
      const consoleErrors = [], pageErrors = [], logs = [];
      page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); logs.push(`[${m.type()}] ${m.text()}`); });
      page.on('pageerror', (e) => pageErrors.push(String(e)));
      await page.goto(DASH_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForFunction(() => document.getElementById('data-source-indicator')?.textContent, { timeout: 25000 }).catch(() => {});
      await page.waitForTimeout(7000);
      out.runs.windowVarOverride = {
        ds: await page.evaluate(() => {
          const el = document.getElementById('data-source-indicator');
          return { text: el?.textContent, title: el?.title };
        }),
        logs: logs.filter(l => l.includes('数据源') || l.includes('回退') || l.includes('API 不可用')),
        consoleErrors, pageErrors,
      };
      await ctx.close();
    }
  }

  await browser.close();
  console.log(JSON.stringify(out, null, 2));
})().catch((e) => { console.error('FATAL', e); process.exit(1); });