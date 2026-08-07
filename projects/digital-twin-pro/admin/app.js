/* 种植业数据管理系统 —— 管理页前端逻辑（原生 JS，无框架） */
"use strict";

const state = {
  page: 1,
  pageSize: 20,
  sort: "year",
  order: "asc",
  meta: null,          // /api/meta/dimensions 缓存
  chartYear: null,
  barChart: null,
  pieChart: null,
};

/* ---------- 工具 ---------- */
const TOKEN_KEY = "agri_admin_token";

function getToken() { try { return localStorage.getItem(TOKEN_KEY) || ""; } catch (e) { return ""; } }
function setToken(t) { try { localStorage.setItem(TOKEN_KEY, t); } catch (e) { /* ignore */ } }
function clearToken() { try { localStorage.removeItem(TOKEN_KEY); } catch (e) { /* ignore */ } }

function authHeaders(headers) {
  const h = headers || {};
  const t = getToken();
  if (t) h["Authorization"] = "Bearer " + t;
  return h;
}

async function api(url, options) {
  const opts = Object.assign({}, options);
  opts.headers = authHeaders(opts.headers);
  const resp = await fetch(url, opts);
  if (resp.status === 401) {
    // 写接口鉴权失败：清除 token 并重新弹出登录
    clearToken();
    updateAuthUI();
    showLogin();
    let detail = "登录已失效，请重新输入 Token";
    try {
      const body = await resp.json();
      if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch (e) { /* ignore */ }
    throw new Error(detail);
  }
  if (!resp.ok) {
    let detail = "HTTP " + resp.status;
    try {
      const body = await resp.json();
      if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch (e) { /* ignore */ }
    throw new Error(detail);
  }
  const ct = resp.headers.get("content-type") || "";
  return ct.includes("json") ? resp.json() : resp.text();
}

/* ---------- 登录 ---------- */
function showLogin() {
  document.getElementById("login-mask").style.display = "flex";
  document.getElementById("login-error").style.display = "none";
  const input = document.getElementById("login-token");
  if (!input.value) input.focus();
}

function hideLogin() {
  document.getElementById("login-mask").style.display = "none";
}

function updateAuthUI() {
  const on = !!getToken();
  const status = document.getElementById("auth-status");
  status.classList.toggle("on", on);
  document.getElementById("auth-status-text").textContent = on ? "已登录" : "未登录";
  document.getElementById("btn-logout").style.display = on ? "" : "none";
}

async function doLogin(ev) {
  ev.preventDefault();
  const token = document.getElementById("login-token").value.trim();
  const errEl = document.getElementById("login-error");
  if (!token) {
    errEl.textContent = "请输入管理 Token";
    errEl.style.display = "";
    return;
  }
  document.getElementById("btn-login").disabled = true;
  try {
    const r = await fetch("/api/auth/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
    });
    const body = await r.json().catch(() => ({}));
    if (r.ok && body.valid === true) {
      setToken(token);
      updateAuthUI();
      hideLogin();
      toast("登录成功");
      loadMeta().catch(e => toast("元数据加载失败：" + e.message, false));
      loadRecords();
    } else {
      errEl.textContent = "Token 无效，请检查后重试";
      errEl.style.display = "";
    }
  } catch (e) {
    errEl.textContent = "校验失败：" + e.message;
    errEl.style.display = "";
  } finally {
    document.getElementById("btn-login").disabled = false;
  }
}

function doLogout() {
  clearToken();
  updateAuthUI();
  showLogin();
  toast("已退出登录");
}

function toast(msg, ok = true) {
  const el = document.createElement("div");
  el.className = "toast " + (ok ? "ok" : "err");
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2600);
}

function fmtNum(v) {
  if (v == null) return "--";
  return Number(v).toLocaleString("zh-CN", { maximumFractionDigits: 2 });
}

function qs(name) {
  const p = new URLSearchParams();
  const v = document.getElementById(name);
  if (v && v.value) p.set(name, v.value);
  return p;
}

function collectFilters() {
  const p = new URLSearchParams();
  ["f-year", "f-region", "f-crop", "f-indicator", "f-keyword"].forEach(id => {
    const v = document.getElementById(id).value;
    if (v) p.set(id.replace("f-", ""), v);
  });
  p.set("page", state.page);
  p.set("page_size", state.pageSize);
  p.set("sort", state.sort);
  p.set("order", state.order);
  return p;
}

/* ---------- 元数据加载 ---------- */
async function loadMeta() {
  state.meta = await api("/api/meta/dimensions");
  const fill = (id, items, label) => {
    const sel = document.getElementById(id);
    sel.innerHTML = `<option value="">${label}</option>` +
      items.map(i => `<option value="${i}">${i}</option>`).join("");
  };
  fill("f-year", state.meta.years, "全部年份");
  fill("f-region", state.meta.regions.map(r => r.province).filter(Boolean), "全部省份");
  fill("f-crop", state.meta.crops.map(c => c.name), "全部作物");
  fill("f-indicator", state.meta.indicators.map(i => i.name), "全部指标");
  document.getElementById("region-list").innerHTML =
    state.meta.regions.map(r => `<option value="${r.province}">`).join("");
  document.getElementById("chart-year").innerHTML =
    state.meta.years.map(y => `<option value="${y}">${y} 年</option>`).join("");

  document.getElementById("stat-records").textContent = fmtNum(state.meta.counts.fact_production);
  document.getElementById("stat-years").textContent = state.meta.years.length;
  document.getElementById("stat-regions").textContent = state.meta.regions.length;
  document.getElementById("stat-crops").textContent = state.meta.crops.length;

  state.chartYear = state.meta.years.length ? state.meta.years[state.meta.years.length - 1] : null;
  if (state.meta.years.length && window.echarts) {
    document.getElementById("chart-panel").style.display = "";
    document.getElementById("chart-year").value = state.chartYear;
    renderCharts();
  }
}

/* ---------- 记录列表 ---------- */
async function loadRecords() {
  const url = "/api/records?" + collectFilters().toString();
  try {
    const data = await api(url);
    const tbody = document.getElementById("records-tbody");
    if (!data.items.length) {
      tbody.innerHTML = '<tr><td colspan="10" class="empty">暂无数据</td></tr>';
    } else {
      tbody.innerHTML = data.items.map(r => `
        <tr>
          <td class="mono num">${r.year}</td>
          <td>${r.province}</td>
          <td>${r.crop}</td>
          <td class="${catClass(r.crop_category)}">${r.crop_category || "--"}</td>
          <td>${r.indicator}</td>
          <td class="mono num">${fmtNum(r.value)}</td>
          <td>${r.unit}</td>
          <td>${r.source || "--"}</td>
          <td class="ts">${r.updated_at || "--"}</td>
          <td class="td-ops">
            <button class="btn sm" onclick="openEdit(${r.fact_id})">编辑</button>
            <button class="btn sm danger" onclick="delRecord(${r.fact_id})">删除</button>
          </td>
        </tr>`).join("");
    }
    const totalPages = Math.max(1, Math.ceil(data.total / state.pageSize));
    document.getElementById("page-info").textContent =
      `共 ${data.total} 条 · 第 ${data.page}/${totalPages} 页`;
    document.getElementById("table-info").textContent =
      `（筛选后 ${data.total} 条）`;
    document.getElementById("btn-prev").disabled = data.page <= 1;
    document.getElementById("btn-next").disabled = data.page >= totalPages;
    state.page = data.page;
    applySortMark();
  } catch (e) {
    document.getElementById("records-tbody").innerHTML =
      `<tr><td colspan="10" class="empty">加载失败：${e.message}</td></tr>`;
  }
}

function catClass(cat) {
  if (cat === "粮食作物") return "cat-food";
  if (cat === "经济作物") return "cat-eco";
  return "cat-other";
}

function applySortMark() {
  document.querySelectorAll("th.sortable").forEach(th => {
    th.classList.remove("sorted-asc", "sorted-desc");
    if (th.dataset.sort === state.sort) {
      th.classList.add(state.order === "asc" ? "sorted-asc" : "sorted-desc");
    }
  });
}

/* ---------- 图表 ---------- */
function renderCharts() {
  if (!window.echarts || !state.chartYear) return;
  const year = state.chartYear;
  api(`/api/analytics/ranking?year=${year}&by=crop`).then(rank => {
    const top = rank.slice(0, 10).reverse();
    if (!state.barChart) state.barChart = echarts.init(document.getElementById("chart-bar"));
    state.barChart.setOption({
      backgroundColor: "transparent",
      grid: { left: 90, right: 30, top: 10, bottom: 25 },
      tooltip: { trigger: "axis" },
      xAxis: { type: "value", axisLabel: { color: "#94a3b8" }, splitLine: { lineStyle: { color: "#334155" } } },
      yAxis: { type: "category", data: top.map(d => d.name), axisLabel: { color: "#f8fafc", fontSize: 11 } },
      series: [{
        type: "bar", data: top.map(d => d.production),
        itemStyle: { color: "#10B981", borderRadius: [0, 3, 3, 0] },
        barWidth: "55%",
      }],
    });
  });
  api(`/api/analytics/structure?year=${year}`).then(st => {
    if (!state.pieChart) state.pieChart = echarts.init(document.getElementById("chart-pie"));
    state.pieChart.setOption({
      backgroundColor: "transparent",
      tooltip: { trigger: "item" },
      legend: { bottom: 0, textStyle: { color: "#94a3b8", fontSize: 11 } },
      series: [{
        type: "pie", radius: ["42%", "68%"],
        label: { color: "#f8fafc", fontSize: 11, formatter: "{b}\n{d}%" },
        data: st.map(d => ({ name: d.name, value: d.production, itemStyle: { color: d.color } })),
      }],
    });
  });
}

/* ---------- 新增/编辑 ---------- */
function openAdd() {
  document.getElementById("record-form").reset();
  document.getElementById("f-fact-id").value = "";
  document.getElementById("modal-title").textContent = "新增记录";
  document.getElementById("modal-mask").style.display = "flex";
}

function openEdit(id) {
  api(`/api/records/${id}`)
    .then(rec => {
      document.getElementById("record-form").reset();
      document.getElementById("f-fact-id").value = rec.fact_id;
      document.getElementById("form-year").value = rec.year;
      document.getElementById("f-province").value = rec.province;
      document.getElementById("form-crop").value = rec.crop;
      document.getElementById("f-crop-category").value = rec.crop_category || "其他作物";
      document.getElementById("form-indicator").value = rec.indicator;
      document.getElementById("f-unit").value = rec.unit || "吨";
      document.getElementById("f-value").value = rec.value;
      document.getElementById("f-source").value = rec.source || "";
      document.getElementById("f-quality").value = rec.data_quality || "normal";
      document.getElementById("modal-title").textContent = "编辑记录 #" + rec.fact_id;
      document.getElementById("modal-mask").style.display = "flex";
    })
    .catch(e => toast("加载记录失败：" + e.message, false));
}

async function delRecord(id) {
  if (!confirm("确定删除该记录？")) return;
  try {
    await api("/api/records/" + id, { method: "DELETE" });
    toast("删除成功");
    loadRecords();
    loadMeta();
  } catch (e) {
    toast("删除失败：" + e.message, false);
  }
}

async function saveRecord(ev) {
  ev.preventDefault();
  const id = document.getElementById("f-fact-id").value;
  const yearRaw = document.getElementById("form-year").value;
  const province = document.getElementById("f-province").value.trim();
  const crop = document.getElementById("form-crop").value.trim();
  const indicator = document.getElementById("form-indicator").value;
  const unit = document.getElementById("f-unit").value;
  const valueRaw = document.getElementById("f-value").value;

  // ---- 前端数据质量校验（与后端 Pydantic 双保险） ----
  const year = parseInt(yearRaw, 10);
  const value = parseFloat(valueRaw);

  if (yearRaw === "" || !province || !crop || !indicator || valueRaw === "") {
    toast("必填字段缺失：年份/省份/作物/指标/数值", false);
    return;
  }
  if (!Number.isFinite(year) || year < 1990 || year > 2099) {
    toast("年份必须在 1990-2099 范围内", false);
    return;
  }
  if (!Number.isFinite(value) || value <= 0) {
    toast("数值必须为正数（>0，且不能为 NaN/Infinity）", false);
    return;
  }
  // 超限预警：黄色警告，用户确认后仍可提交（不阻断）
  // 全国汇总级（省份为"全国"/空）量级远超省级，跳过超限确认（与后端全国级阈值一致）
  const isNational = (province === "全国" || province === "");
  if (!isNational && indicator === "产量" && value >= 50000) {
    if (!confirm(`⚠ 警告：产量 ${fmtNum(value)} 吨 ≥ 50000 吨上限，数据可能异常。\n\n仍要保存吗？`)) return;
  }
  if (!isNational && indicator === "面积" && value >= 500000) {
    if (!confirm(`⚠ 警告：面积 ${fmtNum(value)} 亩 ≥ 500000 亩上限，数据可能异常。\n\n仍要保存吗？`)) return;
  }

  const body = {
    year,
    province,
    crop,
    crop_category: document.getElementById("f-crop-category").value,
    indicator,
    unit,
    value,
    source: document.getElementById("f-source").value.trim(),
    data_quality: document.getElementById("f-quality").value,
  };
  try {
    if (id) {
      await api("/api/records/" + id, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      toast("更新成功");
    } else {
      await api("/api/records", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      toast("新增成功");
    }
    document.getElementById("modal-mask").style.display = "none";
    loadRecords();
    loadMeta();
  } catch (e) {
    toast("保存失败：" + e.message, false);
  }
}

/* ---------- CSV 导入 ---------- */
async function doImport() {
  const fileInput = document.getElementById("import-file");
  if (!fileInput.files.length) { toast("请先选择 CSV 文件", false); return; }
  const file = fileInput.files[0];
  const form = new FormData();
  form.append("file", file);
  try {
    const report = await api("/api/import/csv", { method: "POST", body: form });
    const el = document.getElementById("import-report");
    el.innerHTML = `
      <span style="color:var(--color-success)">✔ ${report.message}</span>
      ${report.warning_rows ? `<span style="color:var(--color-warning)"> · 警告明细：${(report.warning_details || []).join("；")}</span>` : ""}
      ${report.failed_rows ? `<span style="color:var(--color-danger)"> · 失败明细：${(report.failed_details || []).join("；")}</span>` : ""}
    `;
    toast(`导入完成：新增 ${report.inserted_rows} / 更新 ${report.updated_rows} / 失败 ${report.failed_rows}${report.warning_rows ? ` / 警告 ${report.warning_rows}` : ""}`);
    loadRecords();
    loadMeta();
  } catch (e) {
    toast("导入失败：" + e.message, false);
  }
}

/* ---------- 事件绑定 ---------- */
function bindEvents() {
  document.getElementById("btn-search").onclick = () => { state.page = 1; loadRecords(); };
  document.getElementById("btn-reset").onclick = () => {
    ["f-year", "f-region", "f-crop", "f-indicator", "f-keyword"].forEach(id =>
      document.getElementById(id).value = "");
    state.page = 1;
    loadRecords();
  };
  document.getElementById("btn-export").onclick = () => {
    const p = new URLSearchParams();
    ["f-year", "f-region", "f-crop", "f-indicator", "f-keyword"].forEach(id => {
      const v = document.getElementById(id).value;
      if (v) p.set(id.replace("f-", ""), v);
    });
    window.location.href = "/api/export/csv?" + p.toString();
  };
  document.getElementById("btn-add").onclick = openAdd;
  document.getElementById("btn-cancel").onclick = () =>
    document.getElementById("modal-mask").style.display = "none";
  document.getElementById("modal-mask").onclick = (e) => {
    if (e.target.id === "modal-mask") document.getElementById("modal-mask").style.display = "none";
  };
  document.getElementById("record-form").onsubmit = saveRecord;
  document.getElementById("login-form").onsubmit = doLogin;
  document.getElementById("btn-logout").onclick = doLogout;
  document.getElementById("btn-import").onclick = doImport;
  document.getElementById("btn-refresh").onclick = () => { loadMeta(); loadRecords(); };
  document.getElementById("btn-prev").onclick = () => { if (state.page > 1) { state.page--; loadRecords(); } };
  document.getElementById("btn-next").onclick = () => { state.page++; loadRecords(); };
  document.getElementById("page-size").onchange = (e) => {
    state.pageSize = parseInt(e.target.value, 10);
    state.page = 1;
    loadRecords();
  };
  document.getElementById("chart-year").onchange = (e) => {
    state.chartYear = parseInt(e.target.value, 10);
    renderCharts();
  };
  document.querySelectorAll("th.sortable").forEach(th => {
    th.onclick = () => {
      const key = th.dataset.sort;
      if (state.sort === key) state.order = state.order === "asc" ? "desc" : "asc";
      else { state.sort = key; state.order = "asc"; }
      state.page = 1;
      loadRecords();
    };
  });
}

/* ---------- 启动 ---------- */
(async function init() {
  bindEvents();
  updateAuthUI();

  // 读接口公开：先探测鉴权要求；localStorage 无 token 时先登录再加载数据
  let authRequired = true;
  try {
    const st = await api("/api/auth/status");
    authRequired = !!st.auth_required;
  } catch (e) { /* 探测失败时按需登录处理，不阻塞 */ }

  if (authRequired && !getToken()) {
    showLogin();
    return; // 未登录：等待登录成功后加载
  }
  hideLogin(); // 已登录（localStorage 有 token）或无需鉴权：确保遮罩隐藏（刷新场景）

  try {
    await loadMeta();
  } catch (e) {
    toast("元数据加载失败：" + e.message, false);
  }
  loadRecords();
})();