/* 探针：定位 scatter3D 散点真实屏幕坐标并验证 hover tooltip
   运行: node hover_probe.js */
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

  // 在页面内提取散点 mesh、NDC、renderer/viewport 运行时信息
  const info = await page.evaluate(() => {
    const chart = echarts.getInstanceByDom(document.getElementById('map-chart'));
    const zr = chart.getZr();
    const layers = zr.painter.getLayers();
    let mesh = null, viewGL = null, layerGL = null;
    for (const k in layers) {
      const L = layers[k];
      if (!L.views) continue;
      for (const v of L.views) {
        if (!v.scene || !v.scene.traverse) continue;
        let m = null;
        v.scene.traverse((x) => { if (x && x._positionNDC) m = x; });
        if (m) { mesh = m; viewGL = v; layerGL = L; }
      }
    }
    if (!mesh) return { error: 'mesh not found' };
    const ndc = mesh._positionNDC;
    const vp = viewGL.viewport;
    const rend = layerGL.renderer;
    const sizeAttr = mesh.geometry.attributes.size;
    const sizeScale = mesh.sizeScale;
    return {
      vp: { x: vp.x, y: vp.y, width: vp.width, height: vp.height },
      renderer: { width: rend.getWidth(), height: rend.getHeight(), dpr: rend.getDevicePixelRatio ? rend.getDevicePixelRatio() : null },
      canvasCss: { w: layerGL.domElement ? layerGL.domElement.width : null, h: layerGL.domElement ? layerGL.domElement.height : null },
      ndc0: [ndc[0], ndc[1]],
      size0: sizeAttr.get(0),
      sizeScale,
      vertexCount: mesh.geometry.vertexCount,
      seriesIndex: mesh.seriesIndex,
    };
  });
  console.log('INFO', JSON.stringify(info, null, 2));
  if (info.error) { await browser.close(); process.exit(1); }

  // 用各种候选公式计算第一个散点的屏幕坐标
  const { vp, ndc0, renderer } = info;
  const [d, f] = ndc0;
  const H = renderer.height;
  const cand = [
    { name: 'A-noflip', x: Math.round((d + 1) / 2 * vp.width + vp.x), y: Math.round((1 - f) / 2 * vp.height + vp.y) },
    { name: 'B-rendererFlip', x: Math.round((d + 1) / 2 * vp.width + vp.x), y: Math.round(H - vp.y - (f + 1) / 2 * vp.height) },
    { name: 'C-noflip2', x: Math.round((d + 1) / 2 * vp.width + vp.x), y: Math.round((1 - f) / 2 * vp.height) },
    { name: 'D-rendererFlip2', x: Math.round((d + 1) / 2 * vp.width + vp.x), y: Math.round(H - (f + 1) / 2 * vp.height) },
  ];
  const readTip = () => page.evaluate(() => {
    const divs = document.querySelectorAll('#map-chart div');
    for (const el of divs) {
      if ((el.style && el.style.position === 'absolute') && (el.textContent || '').trim()) {
        return (el.textContent || '').trim().slice(0, 100);
      }
    }
    return null;
  });
  let hit = null;
  for (const c of cand) {
    await page.mouse.move(c.x, c.y);
    await page.waitForTimeout(250);
    const tip = await readTip();
    console.log('CAND', c.name, JSON.stringify(c), '->', tip);
    if (tip) { hit = { c, tip }; break; }
  }
  // 若候选全 miss：在第一候选位置附近做 5px 步长小范围扫描
  if (!hit && cand.length) {
    const base = cand[0];
    outer:
    for (let dy = -25; dy <= 25; dy += 5) {
      for (let dx = -25; dx <= 25; dx += 5) {
        await page.mouse.move(base.x + dx, base.y + dy);
        await page.waitForTimeout(40);
        const tip = await readTip();
        if (tip) { hit = { c: { name: 'scan', x: base.x + dx, y: base.y + dy }, tip }; break outer; }
      }
    }
  }
  if (hit) await page.screenshot({ path: 'tooltip_shots/probe_hit.png' });
  console.log('FINAL', JSON.stringify(hit));
  console.log('ERRORS', JSON.stringify({ errs, pageErrors }));
  await browser.close();
})().catch((e) => { console.error('FATAL', e); process.exit(1); });