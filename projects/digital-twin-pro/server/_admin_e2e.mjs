/* 管理页登录 + 校验 Puppeteer 实测
 * 用法: node admin_auth_e2e.mjs  (NODE_PATH 指向全局 node_modules 以解析 puppeteer)
 */
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const fs = require("fs");

// 全局 node_modules（puppeteer 全局安装位置）
const GLOBAL_MODULES = "C:/Users/FFY/AppData/Roaming/npm/node_modules";
const puppeteerPath = GLOBAL_MODULES + "/puppeteer";
if (!fs.existsSync(puppeteerPath + "/package.json")) {
  console.error("FATAL: puppeteer not found at", puppeteerPath);
  process.exit(2);
}
const puppeteer = require(puppeteerPath);

const BASE = "http://127.0.0.1:8001";
const SHOT_DIR = "D:/code/codeByCursor/AI_EXAM/e2e_shots";
const TOKEN = fs.readFileSync("D:/code/codeByCursor/AI_EXAM/server/auth_token.txt", "utf8").trim();

const results = [];
let consoleErrors = [];
let dialogs = [];

function report(name, ok, extra = "") {
  results.push({ name, ok });
  console.log(`[${ok ? "PASS" : "FAIL"}] ${name}${extra ? "  " + extra : ""}`);
}

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--disable-gpu"],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (err) => consoleErrors.push("PAGEERROR: " + err.message));
  page.on("dialog", async (d) => {
    dialogs.push(d.message());
    await d.dismiss();
  });

  // ---------- 1. 打开管理页 → 出现登录遮罩 ----------
  await page.goto(BASE + "/admin/", { waitUntil: "networkidle0", timeout: 30000 });
  await sleep(500);
  const maskVisible = await page.$eval("#login-mask", el => getComputedStyle(el).display !== "none").catch(() => false);
  report("打开 /admin/ 出现登录遮罩", maskVisible);
  await page.screenshot({ path: SHOT_DIR + "/auth_01_login_mask.png" });

  // 未登录状态下表格不应加载数据
  const tbody = await page.$eval("#records-tbody", el => el.textContent).catch(() => "?");
  report("未登录时表格未加载(只显示遮罩)", tbody.includes("加载中") || tbody.includes("暂无") || tbody === "?");

  // ---------- 2. 输入错误 token → 提示失败 ----------
  await page.type("#login-token", "WRONG-TOKEN-12345");
  await page.click("#btn-login");
  await sleep(1200);
  const errVisible = await page.$eval("#login-error", el => getComputedStyle(el).display !== "none" && el.textContent.length > 0).catch(() => false);
  const errText = await page.$eval("#login-error", el => el.textContent).catch(() => "");
  report("错误 token 提示失败", errVisible, "msg=" + errText);
  await page.screenshot({ path: SHOT_DIR + "/auth_02_wrong_token.png" });
  // 清除错误输入
  await page.evaluate(() => document.getElementById("login-token").value = "");

  // ---------- 3. 输入正确 token → 进入管理页，表格加载 20 行 ----------
  await page.type("#login-token", TOKEN);
  await page.click("#btn-login");
  await sleep(1500);
  const maskGone = await page.$eval("#login-mask", el => getComputedStyle(el).display === "none").catch(() => false);
  report("正确 token 登录成功(遮罩关闭)", maskGone);
  const authText = await page.$eval("#auth-status-text", el => el.textContent).catch(() => "?");
  report("右上角显示 已登录", authText === "已登录", "text=" + authText);
  const rowCount = await page.$$eval("#records-tbody tr", trs => trs.length).catch(() => 0);
  report("表格加载 20 行数据", rowCount === 20, "rows=" + rowCount);
  await page.screenshot({ path: SHOT_DIR + "/auth_03_logged_in.png" });

  // ---------- 4. 新增非法记录（负值）→ 前端校验拦截 ----------
  await page.click("#btn-add");
  await sleep(400);
  const modalOpen = await page.$eval("#modal-mask", el => getComputedStyle(el).display !== "none").catch(() => false);
  report("新增弹窗打开", modalOpen);

  // 填写非法负值
  await page.type("#f-year", "2024");
  await page.type("#f-province", "测试省");
  await page.type("#f-crop", "测试作物");
  await page.select("#f-indicator", "产量");
  await page.type("#f-value", "-5");
  await page.click("#btn-save");
  await sleep(800);

  // 前端校验：toast 应提示数值必须为正数，且弹窗不关闭、无网络写请求
  const toastText = await page.$eval(".toast", el => el.textContent).catch(() => "");
  const modalStillOpen = await page.$eval("#modal-mask", el => getComputedStyle(el).display !== "none").catch(() => false);
  report("负值被前端拦截并提示", toastText.includes("正数"), "toast=" + toastText);
  report("拦截后弹窗未关闭(未提交)", modalStillOpen);
  await page.screenshot({ path: SHOT_DIR + "/auth_04_invalid_value_blocked.png" });

  // ---------- 5. 超限预警（产量 60000 ≥ 50000）：confirm 弹窗，取消则不提交 ----------
  await page.evaluate(() => document.getElementById("f-value").value = "60000");
  dialogs = [];
  await page.click("#btn-save");
  await sleep(800);
  report("超限出现 confirm 预警", dialogs.length >= 1 && dialogs[0].includes("50000"), "dialog=" + (dialogs[0] || ""));
  const modalStillOpen2 = await page.$eval("#modal-mask", el => getComputedStyle(el).display !== "none").catch(() => false);
  report("取消 confirm 后未提交(弹窗仍开)", modalStillOpen2);
  await page.screenshot({ path: SHOT_DIR + "/auth_05_overlimit_warn.png" });

  // 关闭弹窗
  await page.click("#btn-cancel");

  // ---------- 6. 退出登录 ----------
  await page.click("#btn-logout");
  await sleep(600);
  const loginMaskBack = await page.$eval("#login-mask", el => getComputedStyle(el).display !== "none").catch(() => false);
  const authText2 = await page.$eval("#auth-status-text", el => el.textContent).catch(() => "?");
  report("退出后重新出现登录遮罩", loginMaskBack && authText2 === "未登录");
  await page.screenshot({ path: SHOT_DIR + "/auth_06_logout.png" });

  await browser.close();

  console.log("\n===== CONSOLE ERRORS (" + consoleErrors.length + ") =====");
  consoleErrors.forEach(e => console.log("  ERR: " + e));

  const fails = results.filter(r => !r.ok);
  console.log("\n===== SUMMARY: " + (results.length - fails.length) + "/" + results.length + " PASS =====");
  if (consoleErrors.length > 0) { console.log("!! 存在 console 错误"); process.exit(1); }
  if (fails.length) { console.log("!! 存在失败项"); process.exit(1); }
})().catch(err => { console.error("E2E ERROR:", err); process.exit(1); });