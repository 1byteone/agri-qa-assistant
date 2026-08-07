/* E2E 验证脚本：大屏对接 API（模式C：API优先+静态兜底）+ 管理页
   运行: node verify_e2e.js
*/
const { chromium } = require('C:/Users/FFY/node_modules/playwright-core');

const CHROME = 'C:/Users/FFY/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe';
const DASH_URL = 'http://127.0.0.1:8000/digital_twin_pro.html';
const ADMIN_URL = 'http://127.0.0.1:8001/admin/';
const SHOT_DIR = 'e2e_shots';

const fs = require('fs');
if (!fs.existsSync(SHOT_DIR)) fs.mkdirSync(SHOT_DIR);

function summarize(page, tag) {
  return page.evaluate((tag) => {
    const q = (s) => document.querySelectorAll(s).length;
    const ds = document.getElementById('data-source-indicator');
    const mapCanvas = document.querySelector('#map-chart canvas');
    const kpiCards = q('.kpi-card');
    const rankItems = q('#rank-list li');
    const structBars = q('#structure-panel .struct-bar, #structure-panel li, #structure-panel > div');
    const loadingHidden = document.getElementById('loading-overlay')?.classList.contains('hidden');
    const loadingText = document.getElementById('loading-text')?.textContent;
    return {
      tag,
      dataSource: ds ? ds.textContent.trim() : '(无指示器)',
      dsTitle: ds ? ds.title : '',
      mapCanvas: !!mapCanvas,
      mapCanvasCount: mapCanvas ? q('#map-chart canvas') : 0,
      kpiCards,
      rankItems,
      structPanelChildren: q('#structure-panel *'),
      loadingHidden,
      loadingText,
      mapRotateBtn: !!document.getElementById('map-rotate-toggle'),
      ready: DataStore && DataStore.isReady && DataStore.isReady(),
    };
  }, tag);
}

(async () => {
  const browser = await chromium.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--force-color-profile=srgb'],
  });

  const results = {};

  // ========== 场景A: API 主路径（后端 8001 运行中） ==========
  {
    const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 } });
    const page = await ctx.newPage();
    const consoleErrors = [], pageErrors = [], failedReqs = [], logs = [];
    page.on('console', (m) => {
      const t = m.type();
      if (t === 'error' || t === 'warning') consoleErrors.push(`[${t}] ${m.text()}`);
      logs.push(`[${t}] ${m.text()}`);
    });
    page.on('pageerror', (e) => pageErrors.push(String(e)));
    page.on('requestfailed', (r) => failedReqs.push(`${r.url()} :: ${r.failure()?.errorText}`));

    await page.goto(DASH_URL, { waitUntil: 'networkidle', timeout: 30000 }).catch(e => pageErrors.push('goto: ' + e.message));
    await page.waitForFunction(() => document.getElementById('data-source-indicator')?.textContent, { timeout: 20000 }).catch(() => {});
    await page.waitForTimeout(2500); // 等地图渲染
    results.api = await summarize(page, 'api-mode');
    results.api.consoleErrors = consoleErrors;
    results.api.pageErrors = pageErrors;
    results.api.failedReqs = failedReqs;
    results.api.consoleLogs = logs.filter(l => l.includes('数据源') || l.includes('DigitalTwin'));
    await page.screenshot({ path: `${SHOT_DIR}/a_api_mode.png`, fullPage: false });
    await page.screenshot({ path: `${SHOT_DIR}/a_api_mode_small.png`, fullPage: false, clip: { x: 0, y: 0, width: 1200, height: 700 } });
    await ctx.close();
  }

  // ========== 场景B: 兜底路径（拦截 8001 请求，模拟后端不可达） ==========
  {
    const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 } });
    const page = await ctx.newPage();
    const consoleErrors = [], pageErrors = [], failedReqs = [], logs = [];
    await page.route('**://127.0.0.1:8001/**', (route) => route.abort('connectionrefused'));
    page.on('console', (m) => {
      const t = m.type();
      if (t === 'error') consoleErrors.push(`[${t}] ${m.text()}`);
      logs.push(`[${t}] ${m.text()}`);
    });
    page.on('pageerror', (e) => pageErrors.push(String(e)));
    page.on('requestfailed', (r) => {
      if (!r.url().includes('127.0.0.1:8001')) failedReqs.push(`${r.url()} :: ${r.failure()?.errorText}`);
    });
    await page.goto(DASH_URL, { waitUntil: 'networkidle', timeout: 30000 }).catch(e => pageErrors.push('goto: ' + e.message));
    await page.waitForFunction(() => document.getElementById('data-source-indicator')?.textContent, { timeout: 20000 }).catch(() => {});
    await page.waitForTimeout(2500);
    results.static = await summarize(page, 'static-fallback');
    results.static.consoleErrors = consoleErrors;
    results.static.pageErrors = pageErrors;
    results.static.failedReqs = failedReqs;
    results.static.fallbackLogs = logs.filter(l => l.includes('数据源') || l.includes('回退') || l.includes('API 不可用'));
    await page.screenshot({ path: `${SHOT_DIR}/b_static_fallback.png`, fullPage: false });
    await page.screenshot({ path: `${SHOT_DIR}/b_static_fallback_small.png`, fullPage: false, clip: { x: 0, y: 0, width: 1200, height: 700 } });
    await ctx.close();
  }

  // ========== 场景C: 管理页 ==========
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    const consoleErrors = [], pageErrors = [], failedReqs = [];
    page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(`[${m.type()}] ${m.text()}`); });
    page.on('pageerror', (e) => pageErrors.push(String(e)));
    page.on('requestfailed', (r) => failedReqs.push(`${r.url()} :: ${r.failure()?.errorText}`));
    await page.goto(ADMIN_URL, { waitUntil: 'networkidle', timeout: 30000 }).catch(e => pageErrors.push('goto: ' + e.message));
    await page.waitForTimeout(2500);
    results.admin = await page.evaluate(() => {
      const txt = (s) => document.querySelector(s)?.textContent?.trim();
      return {
        title: document.title,
        h1: txt('h1'),
        tables: document.querySelectorAll('table').length,
        tableRows: document.querySelectorAll('table tbody tr').length,
        statCards: document.querySelectorAll('.stat-card, .stat, [class*="stat"]').length,
        statTexts: Array.from(document.querySelectorAll('.stat-card, .stat, [class*="stat"]')).slice(0, 4).map(e => e.textContent.trim().slice(0, 40)),
        bodySnippet: document.body.innerText.slice(0, 300),
      };
    });
    results.admin.consoleErrors = consoleErrors;
    results.admin.pageErrors = pageErrors;
    results.admin.failedReqs = failedReqs;
    await page.screenshot({ path: `${SHOT_DIR}/c_admin.png`, fullPage: true });
    await page.screenshot({ path: `${SHOT_DIR}/c_admin_small.png`, fullPage: false, clip: { x: 0, y: 0, width: 1200, height: 700 } });
    await ctx.close();
  }

  await browser.close();
  console.log(JSON.stringify(results, null, 2));
})().catch((e) => { console.error('FATAL', e); process.exit(1); });