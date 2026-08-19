import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const SOCIAL_DIR = 'docs/marketing-kit/social';
const outputSizes = {
  'github-social-preview': { width: 1280, height: 640 },
  'twitter-card': { width: 1200, height: 600 },
  'linkedin-banner': { width: 1584, height: 396 },
};

async function main() {
  const browser = await chromium.launch({ headless: true });

  for (const [name, { width, height }] of Object.entries(outputSizes)) {
    // 1. Render HTML with viewport
    const page = await browser.newPage({ viewport: { width, height } });
    const htmlPath = path.resolve(`${SOCIAL_DIR}/${name}.html`);
    if (fs.existsSync(htmlPath)) {
      await page.goto(`file://${htmlPath}`);
      await page.waitForTimeout(1000);
      await page.screenshot({ path: `${SOCIAL_DIR}/${name}.png`, clip: { x: 0, y: 0, width, height } });
      console.log(`✅ Generated ${name}.png (${width}x${height})`);
    } else {
      console.log(`⚠️ Missing ${name}.html - creating blank template`);
      await page.setContent(`<div style="width:${width}px;height:${height}px;background:linear-gradient(135deg,#0b3d2e,#17613c,#2a8f5e);display:flex;align-items:center;justify-content:center;font-family:system-ui;color:white;font-size:${Math.floor(height/6)}px;font-weight:800;text-align:center;">🌾 AgriQA Assistant<br><span style="font-size:${Math.floor(height/12)}px;color:rgba(255,255,255,.8)">智慧农业智能问答系统</span></div>`);
      await page.screenshot({ path: `${SOCIAL_DIR}/${name}.png` });
      console.log(`✅ Generated ${name}.png (fallback template)`);
    }
    await page.close();
  }

  await browser.close();
  console.log('All social images generated!');
}

main().catch(console.error);