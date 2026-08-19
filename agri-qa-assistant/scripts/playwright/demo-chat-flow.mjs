import { chromium } from 'playwright';
import path from 'path';
import fs from 'fs';

const BASE_URL = 'http://localhost:3001';
const VIDEO_DIR = 'docs/marketing-kit/videos';

async function main() {
  if (!fs.existsSync(VIDEO_DIR)) {
    fs.mkdirSync(VIDEO_DIR, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    recordVideo: { dir: VIDEO_DIR, size: { width: 1280, height: 800 } },
  });
  const page = await context.newPage();

  console.log('Step 1: Loading homepage...');
  await page.goto(BASE_URL);
  await page.waitForTimeout(3000);

  console.log('Step 2: Typing question...');
  await page.click('textarea');
  await page.fill('textarea', '水稻稻飞虱怎么防治？');
  await page.waitForTimeout(500);
  await page.click('button[type="submit"]');

  console.log('Step 3: Waiting for streaming response...');
  await page.waitForTimeout(12000);

  console.log('Step 4: Done recording chat flow');

  await browser.close();

  const videoFiles = fs.readdirSync(VIDEO_DIR).filter(f => f.endsWith('.webm'));
  if (videoFiles.length > 0) {
    console.log(`Video saved: ${VIDEO_DIR}/${videoFiles[0]}`);
  }
}

main().catch(console.error);
