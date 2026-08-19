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

  // 1. Crop Diagnosis
  console.log('Step 1: Navigate to crop diagnosis...');
  await page.goto(`${BASE_URL}/crop-diagnosis`);
  await page.waitForTimeout(3000);

  // 2. Farming Calendar
  console.log('Step 2: Navigate to farming calendar...');
  await page.goto(`${BASE_URL}/farming-calendar`);
  await page.waitForTimeout(3000);

  // 3. Policy Consultation
  console.log('Step 3: Navigate to policy consultation...');
  await page.goto(`${BASE_URL}/policy`);
  await page.waitForTimeout(3000);

  console.log('Step 4: Done recording service workflows');

  await browser.close();

  const videoFiles = fs.readdirSync(VIDEO_DIR).filter(f => f.endsWith('.webm'));
  if (videoFiles.length > 0) {
    console.log(`Video saved: ${VIDEO_DIR}/${videoFiles[0]}`);
  }
}

main().catch(console.error);
