import { chromium } from 'playwright';
import fs from 'fs';

const BASE_URL = 'http://localhost:3001';
const SCREENSHOT_DIR = 'docs/marketing-kit/screenshots';

async function main() {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });

  // 1. Chat with question - streaming response
  console.log('1. Capturing chat-streaming...');
  const page1 = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page1.goto(BASE_URL);
  await page1.waitForTimeout(2000);
  await page1.click('textarea');
  await page1.fill('textarea', '水稻稻飞虱怎么防治？');
  await page1.waitForTimeout(500);
  await page1.click('button[type="submit"]');
  console.log('Waiting for response... waiting 12s');
  await page1.waitForTimeout(12000);
  await page1.waitForTimeout(3000);
  await page1.screenshot({ path: `${SCREENSHOT_DIR}/chat-streaming.png`, fullPage: false });
  await page1.close();

  // 2. Chat with completed response - decision card
  console.log('2. Capturing chat-decision-card...');
  const page2 = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page2.goto(BASE_URL);
  await page2.waitForTimeout(2000);
  await page2.click('textarea');
  await page2.fill('textarea', '水稻稻飞虱怎么防治？');
  await page2.waitForTimeout(500);
  await page2.click('button[type="submit"]');
  console.log('Waiting for response... waiting 12s');
  await page2.waitForTimeout(12000);
  await page2.waitForTimeout(10000);
  await page2.screenshot({ path: `${SCREENSHOT_DIR}/chat-decision-card.png`, fullPage: false });
  await page2.close();

  // 3. Chat with knowledge trace
  console.log('3. Capturing chat-knowledge-trace...');
  const page3 = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page3.goto(BASE_URL);
  await page3.waitForTimeout(2000);
  await page3.click('textarea');
  await page3.fill('textarea', '小麦条锈病怎么识别？');
  await page3.waitForTimeout(500);
  await page3.click('button[type="submit"]');
  console.log('Waiting for response... waiting 12s');
  await page3.waitForTimeout(12000);
  await page3.waitForTimeout(10000);
  await page3.screenshot({ path: `${SCREENSHOT_DIR}/chat-knowledge-trace.png`, fullPage: false });
  await page3.close();

  // 4. Chat mobile view with response
  console.log('4. Capturing chat-mobile-with-response...');
  const page4 = await browser.newPage({ viewport: { width: 375, height: 812 } });
  await page4.goto(BASE_URL);
  await page4.waitForTimeout(2000);
  await page4.click('textarea');
  await page4.fill('textarea', '玉米种植密度多少合适？');
  await page4.waitForTimeout(500);
  await page4.click('button[type="submit"]');
  console.log('Waiting for response... waiting 12s');
  await page4.waitForTimeout(12000);
  await page4.waitForTimeout(8000);
  await page4.screenshot({ path: `${SCREENSHOT_DIR}/chat-mobile-response.png`, fullPage: false });
  await page4.close();

  await browser.close();
  console.log('All Playwright screenshots captured!');
}

main().catch(console.error);
