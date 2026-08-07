import type { ExpenseRecord, FilterState, CategoryName, AnnualReport } from './types'
import { DEFAULT_FILTER, DEFAULT_SUB_CATEGORIES } from './types'
import { store } from './store'
import { escapeHtml, formatAmount, todayStr } from './utils'

/* ===== Toast ===== */
let toastTimer: ReturnType<typeof setTimeout> | null = null
export function showToast(msg: string, type: 'info' | 'success' | 'warning' = 'info'): void {
  const el = document.getElementById('toast')
  if (!el) return
  el.textContent = msg
  el.className = 'toast show ' + type
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { el.className = 'toast' }, 3000)
}
export function updateStatus(msg: string): void {
  const badge = document.getElementById('statusBadge')
  if (!badge) return
  badge.textContent = msg
  badge.classList.add('show')
  setTimeout(() => badge.classList.remove('show'), 2000)
}

/* ===== 分类图标 ===== */
const CATEGORY_ICONS: Record<string, string> = {
  餐饮: '<svg viewBox="0 0 24 24"><path d="M3 2l9 13 9-13A4 4 0 0 0 13 2H7a4 4 0 0 0-2 3.4"/><path d="M21 16v-2a8 8 0 0 0-8-8"/><circle cx="13" cy="19" r="2"/></svg>',
  交通: '<svg viewBox="0 0 24 24"><path d="M5 17h14M6 17V8l2-3h8l2 3v9"/><circle cx="8" cy="18" r="2"/><circle cx="16" cy="18" r="2"/><path d="M7 10h10"/></svg>',
  购物: '<svg viewBox="0 0 24 24"><path d="M6 8h12l-1 12H7L6 8Z"/><path d="M9 9V6a3 3 0 0 1 6 0v3"/></svg>',
  娱乐: '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m10 9 5 3-5 3Z"/></svg>',
  医疗: '<svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M12 8v8M8 12h8"/></svg>',
  固定账单: '<svg viewBox="0 0 24 24"><path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3Z"/><path d="M9 8h6M9 12h6"/></svg>',
  其他: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="8" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="16" cy="12" r="1"/></svg>',
}

/* ===== 当前筛选状态 ===== */
let currentFilter: FilterState = { ...DEFAULT_FILTER }
let isFilterActive = false
let filteredRecords: ExpenseRecord[] = []

/** 重置筛选状态（供外部调用，如清空数据时） */
export function resetFilterState(): void {
  isFilterActive = false
  currentFilter = { ...DEFAULT_FILTER }
  filteredRecords = []
}

/* ===== 趋势图绘制 (Canvas) ===== */
function drawTrendChart(month: string): void {
  const container = document.getElementById('trendChart')
  const canvas = document.getElementById('trendCanvas') as HTMLCanvasElement | null
  if (!container || !canvas) return

  const daily = store.getDailyTotals(month)
  const maxVal = Math.max(...daily.map(d => d.expense + d.income), 1)
  const width = container.clientWidth || 320
  const height = 140
  const dpr = window.devicePixelRatio || 1
  canvas.width = width * dpr
  canvas.height = height * dpr
  canvas.style.width = width + 'px'
  canvas.style.height = height + 'px'
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.scale(dpr, dpr)

  const style = getComputedStyle(document.documentElement)
  const colorExpense = style.getPropertyValue('--pal-primary').trim() || '#0066ff'
  const colorIncome = style.getPropertyValue('--pal-success').trim() || '#138a63'
  const colorGrid = style.getPropertyValue('--pal-border').trim() || '#e0e0e0'
  const colorText = style.getPropertyValue('--pal-text-muted').trim() || '#999'
  const pad = { top: 8, bottom: 16, left: 0, right: 0 }
  const chartW = width - pad.left - pad.right
  const chartH = height - pad.top - pad.bottom

  ctx.clearRect(0, 0, width, height)
  ctx.strokeStyle = colorGrid
  ctx.lineWidth = 0.5
  ctx.setLineDash([2, 3])
  for (let y = 0; y <= 4; y++) {
    const yy = pad.top + (chartH / 4) * y
    ctx.beginPath(); ctx.moveTo(pad.left, yy); ctx.lineTo(width - pad.right, yy); ctx.stroke()
  }
  ctx.setLineDash([])

  const stepX = chartW / Math.max(daily.length - 1, 1)
  const expensePoints = daily.map((d, i) => ({ x: pad.left + i * stepX, y: pad.top + chartH - (d.expense / maxVal) * chartH }))
  if (expensePoints.length > 0) {
    ctx.beginPath(); ctx.moveTo(expensePoints[0].x, pad.top + chartH)
    expensePoints.forEach(p => ctx.lineTo(p.x, p.y))
    ctx.lineTo(expensePoints[expensePoints.length - 1].x, pad.top + chartH); ctx.closePath()
    const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + chartH)
    grad.addColorStop(0, colorExpense + '40'); grad.addColorStop(1, colorExpense + '05')
    ctx.fillStyle = grad; ctx.fill()
    ctx.beginPath(); ctx.moveTo(expensePoints[0].x, expensePoints[0].y)
    expensePoints.forEach(p => ctx.lineTo(p.x, p.y))
    ctx.strokeStyle = colorExpense; ctx.lineWidth = 2; ctx.stroke()
  }

  const incomePoints = daily.map((d, i) => ({ x: pad.left + i * stepX, y: pad.top + chartH - (d.income / maxVal) * chartH }))
  if (incomePoints.some(p => p.y < pad.top + chartH)) {
    ctx.beginPath(); ctx.moveTo(incomePoints[0].x, pad.top + chartH)
    incomePoints.forEach(p => ctx.lineTo(p.x, p.y))
    ctx.lineTo(incomePoints[incomePoints.length - 1].x, pad.top + chartH); ctx.closePath()
    const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + chartH)
    grad.addColorStop(0, colorIncome + '40'); grad.addColorStop(1, colorIncome + '05')
    ctx.fillStyle = grad; ctx.fill()
    ctx.beginPath(); ctx.moveTo(incomePoints[0].x, incomePoints[0].y)
    incomePoints.forEach(p => ctx.lineTo(p.x, p.y))
    ctx.strokeStyle = colorIncome; ctx.lineWidth = 2; ctx.setLineDash([4, 3]); ctx.stroke(); ctx.setLineDash([])
  }
  ctx.font = '10px sans-serif'
  ctx.fillStyle = colorExpense; ctx.fillRect(8, 4, 8, 8); ctx.fillText('支出', 20, 12)
  ctx.fillStyle = colorIncome; ctx.fillRect(60, 4, 8, 8); ctx.fillText('收入', 72, 12)
}

/* ===== 预算渲染 ===== */
function renderBudgets(month: string): void {
  const el = document.getElementById('budgetStats')
  if (!el) return
  if (isFilterActive) {
    el.innerHTML = '<div class="empty-text" style="font-size:12px;padding:4px 0;color:var(--warning);">筛选模式下预算数据不反映当前筛选结果</div>'
    return
  }
  const usage = store.getBudgetUsage(month)
  if (usage.length === 0) {
    el.innerHTML = '<div class="empty-text" style="font-size:12px;padding:4px 0;">点击「设置」为分类添加月度预算</div>'
    return
  }
  el.innerHTML = usage.map(u => {
    const cls = u.pct >= 90 ? 'danger' : u.pct >= 70 ? 'warn' : 'safe'
    return `<div class="budget-item">
      <span class="budget-label">${escapeHtml(u.category)}</span>
      <span class="budget-value">${formatAmount(u.spent)} / ${formatAmount(u.budget)}</span>
      <div class="budget-bar"><div class="budget-bar-fill ${cls}" style="width:${u.pct}%"></div></div>
    </div>`
  }).join('')
}

/* ===== 分类统计 ===== */
function renderCategoryStats(records: ExpenseRecord[], total: number): string {
  const catMap: Record<string, number> = {}
  records.filter(r => r.type === 'expense').forEach(r => {
    catMap[r.category] = (catMap[r.category] || 0) + r.amount
  })
  const sorted = Object.entries(catMap).sort(([, a], [, b]) => b - a)
  if (sorted.length === 0) {
    return '<div class="empty"><div class="empty-text">暂无分类数据</div></div>'
  }
  return sorted.map(([cat, amt]) => {
    const pct = ((amt / total) * 100).toFixed(1)
    const isMajor = parseFloat(pct) > 20
    const style = isMajor ? 'font-weight:600;background:var(--primary-soft);padding:4px;border-radius:var(--radius);' : ''
    return `<div class="stat-item" style="${style}"><span class="stat-label">${escapeHtml(cat)} (${pct}%)</span><span class="stat-value">${formatAmount(amt)}</span></div>`
  }).join('')
}

/* ===== 消费洞察 ===== */
function generateInsights(records: ExpenseRecord[], total: number, sortedCats: [string, number][]): string {
  if (records.length === 0) return '添加记录后生成消费洞察'
  const [topCat, topAmt] = sortedCats[0] || ['其他', 0]
  const topPct = ((topAmt / total) * 100).toFixed(1)
  const weekendDays = records.filter(r => { const d = new Date(r.date); return d.getDay() === 0 || d.getDay() === 6 }).length
  const weekendRatio = ((weekendDays / records.length) * 100).toFixed(0)
  let insight = `本月共支出 ¥${formatAmount(total)}，其中${topCat}支出最高（¥${formatAmount(topAmt)}，占 ${topPct}%）。`
  if (parseFloat(topPct) > 35) insight += `${topCat}已超过本月支出的三分之一，建议重点检查。`
  else if (Number(weekendRatio) > 50) insight += `周末消费记录占 ${weekendRatio}%，可以留意临时性消费。`
  else insight += '当前消费分布较为均衡，请继续保持理性记录。'
  return insight
}

/* ===== 趋势环比 ===== */
function renderTrend(currentMonth: string): string {
  if (currentMonth === todayStr().slice(0, 7)) return ''
  const prevMonthDate = new Date(parseInt(currentMonth.slice(0, 4)), parseInt(currentMonth.slice(5)) - 2, 1)
  const prevMonth = prevMonthDate.toISOString().slice(0, 7)
  const currentTotal = store.getExpense(store.getByMonth(currentMonth))
  const prevTotal = store.getExpense(store.getByMonth(prevMonth))
  let changePct: number | string = 0
  if (prevTotal > 0) {
    changePct = (((currentTotal - prevTotal) / prevTotal) * 100).toFixed(1)
  } else if (currentTotal > 0) {
    changePct = '+∞'
  }
  const cls = typeof changePct === 'number' ? (Number(changePct) > 0 ? 'trend-up' : 'trend-down') : 'trend-up'
  const label = typeof changePct === 'number' ? `${Number(changePct) > 0 ? '+' : ''}${changePct}%` : changePct
  return `<span class="trend-indicator ${cls}">${label}</span>`
}

/* ===== 筛选标签下拉 ===== */
function updateFilterTagOptions(): void {
  const sel = document.getElementById('filterTag') as HTMLSelectElement | null
  if (!sel) return
  const tags = store.allTags
  sel.innerHTML = '<option value="">全部标签</option>' + tags.map(t => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('')
}

/* ===== 获取当前筛选状态 ===== */
function readFilterFromUI(): FilterState {
  const keyword = (document.getElementById('filterKeyword') as HTMLInputElement)?.value || ''
  const catVal = (document.getElementById('filterCategory') as HTMLSelectElement)?.value || ''
  const typeVal = (document.getElementById('filterType') as HTMLSelectElement)?.value || ''
  const minVal = parseFloat((document.getElementById('filterMinAmount') as HTMLInputElement)?.value || '') || 0
  const maxVal = parseFloat((document.getElementById('filterMaxAmount') as HTMLInputElement)?.value || '') || 0
  const tagVal = (document.getElementById('filterTag') as HTMLSelectElement)?.value || ''
  return {
    keyword,
    categories: catVal ? [catVal as CategoryName] : [],
    minAmount: minVal,
    maxAmount: maxVal,
    dateRange: ['', ''],
    types: typeVal ? [typeVal as 'expense' | 'income'] : [],
    tags: tagVal ? [tagVal] : [],
  }
}

/* ===== 应用筛选 ===== */
function applyFilter(): void {
  currentFilter = readFilterFromUI()
  const hasFilter = !!(currentFilter.keyword || currentFilter.categories.length || currentFilter.minAmount || currentFilter.maxAmount || currentFilter.types.length || currentFilter.tags.length)
  isFilterActive = hasFilter
  filteredRecords = hasFilter ? store.filter(currentFilter) : store.records

  const clearBtn = document.getElementById('filterClear')
  if (clearBtn) clearBtn.hidden = !hasFilter

  render() // 重新渲染全量
}

/* ===== 全量渲染 ===== */
export function render(): void {
  const monthEl = document.getElementById('monthFilter') as HTMLInputElement | null
  const currentMonth = monthEl?.value || todayStr().slice(0, 7)

  // 决定使用哪组记录: 筛选态 vs 月份
  const recordsToRender = isFilterActive ? filteredRecords : store.getByMonth(currentMonth)
  const monthExp = recordsToRender.filter(r => r.type === 'expense')
  const monthInc = recordsToRender.filter(r => r.type === 'income')

  const today = todayStr()
  const todayExp = store.getByDate(today).filter(r => r.type === 'expense')
  const total = store.getTotal(monthExp)
  const incomeTotal = store.getTotal(monthInc)
  const balance = incomeTotal - total
  const todaySum = store.getTotal(todayExp)
  const daysWithExp = new Set(monthExp.map(r => r.date)).size
  const avgDays = daysWithExp > 0 ? (total / daysWithExp).toFixed(2) : '0.00'

  setText('monthIncome', formatAmount(incomeTotal))
  setText('monthTotalVal', formatAmount(total))
  setHtml('monthTrend', renderTrend(currentMonth))
  setText('todayTotal', formatAmount(todaySum))
  setText('avgDaily', avgDays)
  setText('recordCount', String(recordsToRender.length))

  const balanceEl = document.getElementById('monthBalance')
  if (balanceEl) {
    balanceEl.textContent = formatAmount(balance)
    balanceEl.className = 'stat-value ' + (balance >= 0 ? 'stat-balance-positive' : 'stat-balance-negative')
  }

  const catMap: Record<string, number> = {}
  monthExp.forEach(r => { catMap[r.category] = (catMap[r.category] || 0) + r.amount })
  const sortedCats = Object.entries(catMap).sort(([, a], [, b]) => b - a)
  setHtml('catStats', renderCategoryStats(monthExp, total))
  setHtml('insightText', generateInsights(monthExp, total, sortedCats))
  renderBudgets(currentMonth)
  drawTrendChart(currentMonth)

  // 记录列表
  renderRecordList(recordsToRender)
  checkDataStatus()
  updateFilterTagOptions()
}

function setText(id: string, val: string): void {
  const el = document.getElementById(id)
  if (el) el.textContent = val
}
function setHtml(id: string, html: string): void {
  const el = document.getElementById(id)
  if (el) el.innerHTML = html
}

/* ===== 记录列表渲染（含标签、子分类） ===== */
function renderRecordList(allRecords: ExpenseRecord[]): void {
  const list = document.getElementById('recordList')
  if (!list) return
  const sorted = [...allRecords].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())

  const badge = document.getElementById('recordCountBadge')
  if (badge) badge.textContent = `共 ${sorted.length} 条`

  if (sorted.length === 0) {
    list.innerHTML = `<li class="empty"><svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg><div class="empty-text">${isFilterActive ? '没有匹配筛选条件的记录' : '本月暂无记录，添加第一笔开销吧'}</div></li>`
    return
  }

  list.innerHTML = sorted.map(r => {
    const iconSVG = CATEGORY_ICONS[r.category] || CATEGORY_ICONS['其他']
    const noteMarkup = r.note ? ` <span class="record-note">(${escapeHtml(r.note)})</span>` : ''
    const typeTag = r.type === 'income' ? '<span class="record-type-tag income">收入</span>' : ''
    const amountClass = r.type === 'income' ? 'record-amount income' : 'record-amount'
    const sign = r.type === 'income' ? '+' : '-'

    // 子分类
    const subCatMarkup = r.subCategory ? `<span class="record-subcat">${escapeHtml(r.subCategory)}</span>` : ''
    // 标签
    const tagsMarkup = r.tags?.length
      ? `<span class="record-tags">${r.tags.map(t => `<span class="record-tag">#${escapeHtml(t)}</span>`).join(' ')}</span>`
      : ''

    return `<li class="record" data-id="${escapeHtml(r.id)}">
      <div class="record-icon">${iconSVG}</div>
      <div>
        <div class="record-cat">${escapeHtml(r.category)}${typeTag}${subCatMarkup}${noteMarkup}</div>
        <div class="record-meta">${escapeHtml(r.date)}${tagsMarkup}</div>
      </div>
      <div class="${amountClass}">${sign}${formatAmount(r.amount)}</div>
      <div class="record-actions">
        <button class="btn-edit" type="button" aria-label="编辑记录" onclick="window.editRecord('${escapeHtml(r.id)}')">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L8 18l-4 1 1-4Z"/></svg>
        </button>
        <button class="btn-del" type="button" aria-label="删除记录" onclick="window.deleteRecord('${escapeHtml(r.id)}')">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>
        </button>
      </div>
    </li>`
  }).join('')
}

/* ===== 引导状态 ===== */
function checkDataStatus(): void {
  const demoBtn = document.getElementById('demoBtn')
  if (!demoBtn) return
  // 有数据时隐藏示例数据按钮
  demoBtn.hidden = store.records.length > 0
}

/* ===== 编辑记录 ===== */
(window as any).editRecord = function (id: string): void {
  const record = store.getById(id)
  if (!record) return
  ;(window as any).__editingId = id
  ;(window as any).__isEditing = true
  const amountEl = document.getElementById('amount') as HTMLInputElement
  const dateEl = document.getElementById('date') as HTMLInputElement
  const noteEl = document.getElementById('note') as HTMLInputElement
  if (amountEl) amountEl.value = String(record.amount)
  if (dateEl) dateEl.value = record.date
  if (noteEl) noteEl.value = record.note || ''

  // 恢复类型切换
  const typeBtns = document.querySelectorAll('.type-btn')
  typeBtns.forEach(b => b.classList.toggle('active', (b as HTMLElement).dataset.type === record.type))
  ;(window as any).__selectedType = record.type

  // 恢复分类下拉框
  const catSelect = document.getElementById('catSelect') as HTMLSelectElement | null
  if (catSelect) {
    catSelect.value = record.category
    // 触发子分类联动
    const subCatSelect = document.getElementById('subCatSelect') as HTMLSelectElement | null
    if (subCatSelect) {
      // 获取子分类选项
      const subs = store.getSubCategories(record.category as any)
      const defaults = (() => {
        const m: Record<string, string[]> = {}
        DEFAULT_SUB_CATEGORIES.forEach(s => { m[s.category] = s.subCategories })
        return m
      })()
      const allSubs = [...new Set([...subs, ...(defaults[record.category] || [])])]
      subCatSelect.innerHTML = '<option value="">子分类</option>' + allSubs.map(s => `<option value="${s}"${s === record.subCategory ? ' selected' : ''}>${s}</option>`).join('')
    }
  }

  // 恢复标签
  const tagList = document.getElementById('tagList')
  if (tagList) {
    const editTags = [...(record.tags || [])]
    ;(window as any).__currentEditTags = editTags
    tagList.innerHTML = editTags.map(t =>
      `<span class="tag-chip">#${t} <button class="tag-remove" data-tag="${t}" type="button">&times;</button></span>`
    ).join('')
  }

  const submitBtn = document.querySelector('.btn-submit')
  if (submitBtn) submitBtn.textContent = '更新记录'
  amountEl?.focus()
  updateStatus('正在编辑记录')
}

;(window as any).deleteRecord = function (id: string): void {
  if (!confirm('确定删除这条记录吗？')) return
  store.delete(id)
  render()
  showToast('记录已删除')
}

/* ===== 年度报告渲染 ===== */
export function renderAnnualReport(year: number): void {
  const report = store.getAnnualReport(year)
  const titleEl = document.getElementById('annualReportTitle')
  if (titleEl) titleEl.textContent = `${year} 年度报告`

  // 摘要
  const summaryEl = document.getElementById('arSummary')
  if (summaryEl) {
    const balanceClass = report.balance >= 0 ? 'stat-balance-positive' : 'stat-balance-negative'
    summaryEl.innerHTML = `
      <div class="ar-summary-grid">
        <div class="ar-summary-item"><span class="ar-summary-label">总收入</span><span class="ar-summary-value">¥${formatAmount(report.totalIncome)}</span></div>
        <div class="ar-summary-item"><span class="ar-summary-label">总支出</span><span class="ar-summary-value">¥${formatAmount(report.totalExpense)}</span></div>
        <div class="ar-summary-item"><span class="ar-summary-label">结余</span><span class="ar-summary-value ${balanceClass}">¥${formatAmount(report.balance)}</span></div>
        <div class="ar-summary-item"><span class="ar-summary-label">月均支出</span><span class="ar-summary-value">¥${formatAmount(report.monthlyAvg)}</span></div>
        <div class="ar-summary-item"><span class="ar-summary-label">支出最高月</span><span class="ar-summary-value">${report.maxExpenseMonth} 月 (¥${formatAmount(report.maxExpenseAmount)})</span></div>
        <div class="ar-summary-item"><span class="ar-summary-label">周末消费占比</span><span class="ar-summary-value">${report.weekendExpensePct.toFixed(1)}%</span></div>
        <div class="ar-summary-item"><span class="ar-summary-label">收支比</span><span class="ar-summary-value">${report.incomeExpenseRatio.toFixed(2)}</span></div>
      </div>
    `
  }

  // 月度趋势图
  drawAnnualTrendChart(report)

  // 分类排名
  const rankingEl = document.getElementById('arCategoryRanking')
  if (rankingEl) {
    if (report.categoryRanking.length === 0) {
      rankingEl.innerHTML = '<div class="empty-text">暂无分类数据</div>'
    } else {
      rankingEl.innerHTML = report.categoryRanking.map((c, i) => {
        const barW = Math.min(c.pct, 100)
        return `<div class="ar-ranking-item">
          <span class="ar-ranking-pos">#${i + 1}</span>
          <span class="ar-ranking-cat">${escapeHtml(c.category)}</span>
          <div class="ar-ranking-bar-wrap"><div class="ar-ranking-bar" style="width:${barW}%"></div></div>
          <span class="ar-ranking-amt">¥${formatAmount(c.amount)}</span>
          <span class="ar-ranking-pct">${c.pct.toFixed(1)}%</span>
        </div>`
      }).join('')
    }
  }

  // TOP10 单笔
  const topEl = document.getElementById('arTopList')
  if (topEl) {
    if (report.topExpenses.length === 0) {
      topEl.innerHTML = '<div class="empty-text">暂无数据</div>'
    } else {
      topEl.innerHTML = report.topExpenses.map((e, i) => `
        <div class="ar-top-item">
          <span class="ar-top-pos">#${i + 1}</span>
          <span class="ar-top-cat">${escapeHtml(e.category)}</span>
          <span class="ar-top-date">${e.date}</span>
          <span class="ar-top-note">${escapeHtml(e.note || '')}</span>
          <span class="ar-top-amt">¥${formatAmount(e.amount)}</span>
        </div>
      `).join('')
    }
  }

  // 预算完成率
  const budgetEl = document.getElementById('arBudget')
  if (budgetEl) {
    if (report.budgetCompletion.length === 0) {
      budgetEl.innerHTML = '<div class="empty-text">未设置年度预算</div>'
    } else {
      budgetEl.innerHTML = report.budgetCompletion.map(b => {
        const cls = b.pct >= 100 ? 'danger' : b.pct >= 70 ? 'warn' : 'safe'
        return `<div class="budget-item">
          <span class="budget-label">${escapeHtml(b.category)}</span>
          <span class="budget-value">¥${formatAmount(b.spent)} / ¥${formatAmount(b.budget)}</span>
          <div class="budget-bar"><div class="budget-bar-fill ${cls}" style="width:${Math.min(b.pct, 100)}%"></div></div>
        </div>`
      }).join('')
    }
  }

  // 标签云
  const tagCloudEl = document.getElementById('arTagCloud')
  if (tagCloudEl) {
    if (report.tagCloud.length === 0) {
      tagCloudEl.innerHTML = '<div class="empty-text">无标签数据</div>'
    } else {
      const maxCount = Math.max(...report.tagCloud.map(t => t.count), 1)
      tagCloudEl.innerHTML = report.tagCloud.map(t => {
        const size = 0.8 + (t.count / maxCount) * 1.2
        return `<span class="ar-tag" style="font-size:${size}em">#${escapeHtml(t.tag)}<small> (${t.count}次, ¥${formatAmount(t.amount)})</small></span>`
      }).join(' ')
    }
  }

  // 消费习惯
  const insightsEl = document.getElementById('arInsights')
  if (insightsEl) {
    const lines: string[] = []
    if (report.totalExpense > 0) {
      lines.push(`全年总支出 ¥${formatAmount(report.totalExpense)}，月均 ¥${formatAmount(report.monthlyAvg)}。`)
      if (report.monthlyAvg > 0) {
        lines.push(`支出最高月在 ${report.maxExpenseMonth} 月，支出 ¥${formatAmount(report.maxExpenseAmount)}。`)
      }
      if (report.weekendExpensePct > 40) {
        lines.push(`周末消费占比 ${report.weekendExpensePct.toFixed(1)}%，建议减少非必要周末消费。`)
      }
      if (report.incomeExpenseRatio < 1) {
        lines.push(`收支比 ${report.incomeExpenseRatio.toFixed(2)}，支出大于收入，需注意财务健康。`)
      } else {
        lines.push(`收支比 ${report.incomeExpenseRatio.toFixed(2)}，收支平衡良好。`)
      }
    }
    insightsEl.innerHTML = lines.length ? lines.map(l => `<p style="margin:4px 0;font-size:13px;">${l}</p>`).join('') : '暂无足够数据生成分析'
  }
}

/* ===== 年度趋势折线图 ===== */
function drawAnnualTrendChart(report: AnnualReport): void {
  const container = document.getElementById('arTrendChart')
  const canvas = document.getElementById('arTrendCanvas') as HTMLCanvasElement | null
  if (!container || !canvas) return

  const width = container.clientWidth || 480
  const height = 200
  const dpr = window.devicePixelRatio || 1
  canvas.width = width * dpr
  canvas.height = height * dpr
  canvas.style.width = width + 'px'
  canvas.style.height = height + 'px'
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.scale(dpr, dpr)

  const style = getComputedStyle(document.documentElement)
  const colorExpense = style.getPropertyValue('--pal-primary').trim() || '#0066ff'
  const colorIncome = style.getPropertyValue('--pal-success').trim() || '#138a63'
  const colorGrid = style.getPropertyValue('--pal-border').trim() || '#e0e0e0'
  const pad = { top: 16, bottom: 20, left: 40, right: 16 }
  const chartW = width - pad.left - pad.right
  const chartH = height - pad.top - pad.bottom

  ctx.clearRect(0, 0, width, height)

  const maxVal = Math.max(...report.monthlyBreakdown.map(m => Math.max(m.expense, m.income)), 1)

  // 网格
  ctx.strokeStyle = colorGrid
  ctx.lineWidth = 0.5
  ctx.setLineDash([2, 3])
  for (let y = 0; y <= 4; y++) {
    const yy = pad.top + (chartH / 4) * y
    ctx.beginPath(); ctx.moveTo(pad.left, yy); ctx.lineTo(width - pad.right, yy); ctx.stroke()
    ctx.setLineDash([])
    ctx.fillStyle = style.getPropertyValue('--pal-text-muted').trim() || '#999'
    ctx.font = '9px sans-serif'
    ctx.textAlign = 'right'
    ctx.fillText('¥' + Math.round((maxVal / 4) * (4 - y)), pad.left - 4, yy + 3)
  }
  ctx.setLineDash([])

  const stepX = chartW / 11
  const months = report.monthlyBreakdown

  // 支出
  const expPoints = months.map((m, i) => ({ x: pad.left + i * stepX, y: pad.top + chartH - (m.expense / maxVal) * chartH }))
  ctx.beginPath(); ctx.moveTo(expPoints[0].x, pad.top + chartH)
  expPoints.forEach(p => ctx.lineTo(p.x, p.y))
  ctx.lineTo(expPoints[expPoints.length - 1].x, pad.top + chartH); ctx.closePath()
  const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + chartH)
  grad.addColorStop(0, colorExpense + '30'); grad.addColorStop(1, colorExpense + '05')
  ctx.fillStyle = grad; ctx.fill()
  ctx.beginPath(); ctx.moveTo(expPoints[0].x, expPoints[0].y)
  expPoints.forEach(p => ctx.lineTo(p.x, p.y))
  ctx.strokeStyle = colorExpense; ctx.lineWidth = 2; ctx.stroke()

  // 收入
  const incPoints = months.map((m, i) => ({ x: pad.left + i * stepX, y: pad.top + chartH - (m.income / maxVal) * chartH }))
  ctx.beginPath(); ctx.moveTo(incPoints[0].x, pad.top + chartH)
  incPoints.forEach(p => ctx.lineTo(p.x, p.y))
  ctx.lineTo(incPoints[incPoints.length - 1].x, pad.top + chartH); ctx.closePath()
  const grad2 = ctx.createLinearGradient(0, pad.top, 0, pad.top + chartH)
  grad2.addColorStop(0, colorIncome + '30'); grad2.addColorStop(1, colorIncome + '05')
  ctx.fillStyle = grad2; ctx.fill()
  ctx.beginPath(); ctx.moveTo(incPoints[0].x, incPoints[0].y)
  incPoints.forEach(p => ctx.lineTo(p.x, p.y))
  ctx.strokeStyle = colorIncome; ctx.lineWidth = 2; ctx.setLineDash([4, 3]); ctx.stroke(); ctx.setLineDash([])

  // X 轴标签
  ctx.fillStyle = style.getPropertyValue('--pal-text-muted').trim() || '#999'
  ctx.font = '9px sans-serif'
  ctx.textAlign = 'center'
  months.forEach(m => {
    const x = pad.left + (m.month - 1) * stepX
    ctx.fillText(String(m.month), x, height - 4)
  })

  // 图例
  ctx.fillStyle = colorExpense; ctx.fillRect(8, 4, 8, 8); ctx.fillText('支出', 20, 12)
  ctx.fillStyle = colorIncome; ctx.fillRect(60, 4, 8, 8); ctx.fillText('收入', 72, 12)
}

/* ===== 导出 CSV ===== */
export function exportCSV(records: ExpenseRecord[]): void {
  const header = '日期,类型,分类,子分类,金额,标签,备注\n'
  const rows = records.map(r => {
    const type = r.type === 'expense' ? '支出' : '收入'
    const tags = (r.tags || []).join(';')
    return `${r.date},${type},${r.category},${r.subCategory || ''},${r.amount},"${tags}","${r.note}"`
  }).join('\n')
  const blob = new Blob(['\uFEFF' + header + rows], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `开销报表_${todayStr()}.csv`
  a.click(); URL.revokeObjectURL(url)
}

/* ===== 导出 XLSX (HTML table 转 XLSX 近似) ===== */
export function exportXLSX(records: ExpenseRecord[]): void {
  // 生成 HTML table 格式，Excel 可打开
  const table = `<table>
    <thead><tr><th>日期</th><th>类型</th><th>分类</th><th>子分类</th><th>金额</th><th>标签</th><th>备注</th></tr></thead>
    <tbody>${records.map(r => {
      const type = r.type === 'expense' ? '支出' : '收入'
      const tags = (r.tags || []).join(';')
      return `<tr><td>${r.date}</td><td>${type}</td><td>${r.category}</td><td>${r.subCategory || ''}</td><td>${r.amount}</td><td>${tags}</td><td>${r.note}</td></tr>`
    }).join('')}</tbody></table>`
  const blob = new Blob(['\uFEFF' + table], { type: 'application/vnd.ms-excel;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `开销报表_${todayStr()}.xls`
  a.click(); URL.revokeObjectURL(url)
}

/* ===== 初始化入口 ===== */
export function initRenderer(): void {
  const monthFilter = document.getElementById('monthFilter') as HTMLInputElement | null
  if (monthFilter) {
    monthFilter.value = todayStr().slice(0, 7)
    monthFilter.addEventListener('change', () => {
      // 切换月份时清除筛选
      if (isFilterActive) {
        isFilterActive = false
        currentFilter = { ...DEFAULT_FILTER }
        resetFilterUI()
      }
      render()
      updateStatus(`正在查看 ${monthFilter.value}`)
    })
  }
  const dateInput = document.getElementById('date') as HTMLInputElement | null
  if (dateInput) dateInput.valueAsDate = new Date()
  const guideDismiss = document.getElementById('guideDismiss')
  guideDismiss?.addEventListener('click', () => {
    try { localStorage.setItem('swiss_expenses_guide', 'dismissed') } catch { /* ignore */ }
    const guide = document.getElementById('guideBanner')
    const demoBtn = document.getElementById('demoBtn')
    if (guide) guide.hidden = true
    if (demoBtn) demoBtn.hidden = true
  })
  window.addEventListener('resize', () => {
    const mf = document.getElementById('monthFilter') as HTMLInputElement | null
    if (mf) drawTrendChart(mf.value)
  })

  // --- 筛选事件 ---
  const filterApplyBtn = document.getElementById('filterApplyBtn')
  filterApplyBtn?.addEventListener('click', applyFilter)

  // 回车触发筛选
  const filterKeyword = document.getElementById('filterKeyword')
  filterKeyword?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') applyFilter()
  })

  // 清除筛选
  const filterClear = document.getElementById('filterClear')
  filterClear?.addEventListener('click', () => {
    isFilterActive = false
    currentFilter = { ...DEFAULT_FILTER }
    resetFilterUI()
    render()
  })

  // --- 年度报告 ---
  const annualReportBtn = document.getElementById('annualReportBtn')
  const annualReportOverlay = document.getElementById('annualReportOverlay')
  const annualReportClose = document.getElementById('annualReportClose')
  const annualReportYear = document.getElementById('annualReportYear') as HTMLSelectElement | null

  annualReportBtn?.addEventListener('click', () => {
    if (!annualReportOverlay || !annualReportYear) return
    // 填充年份选择
    const years = new Set<number>()
    store.records.forEach(r => {
      const y = parseInt(r.date.slice(0, 4))
      if (!isNaN(y)) years.add(y)
    })
    const currentYear = new Date().getFullYear()
    if (years.size === 0) years.add(currentYear)
    const sortedYears = [...years].sort((a, b) => b - a)
    annualReportYear.innerHTML = sortedYears.map(y => `<option value="${y}">${y} 年</option>`).join('')
    annualReportOverlay.hidden = false
    renderAnnualReport(sortedYears[0])
  })

  annualReportClose?.addEventListener('click', () => {
    if (annualReportOverlay) annualReportOverlay.hidden = true
  })
  annualReportOverlay?.addEventListener('click', (e) => {
    if (e.target === annualReportOverlay) annualReportOverlay.hidden = true
  })
  annualReportYear?.addEventListener('change', () => {
    if (annualReportYear) renderAnnualReport(parseInt(annualReportYear.value))
  })

  // --- 导出按钮 ---
  document.getElementById('arExportCsvBtn')?.addEventListener('click', () => {
    const year = annualReportYear ? parseInt(annualReportYear.value) : new Date().getFullYear()
    const report = store.getAnnualReport(year)
    // 导出全年记录
    const yearRecords = store.records.filter(r => r.date.startsWith(String(year)))
    exportCSV(yearRecords)
    showToast('CSV 已导出', 'success')
  })
  document.getElementById('arExportXlsxBtn')?.addEventListener('click', () => {
    const year = annualReportYear ? parseInt(annualReportYear.value) : new Date().getFullYear()
    const yearRecords = store.records.filter(r => r.date.startsWith(String(year)))
    exportXLSX(yearRecords)
    showToast('XLSX 已导出', 'success')
  })
}

function resetFilterUI(): void {
  const kw = document.getElementById('filterKeyword') as HTMLInputElement
  const cat = document.getElementById('filterCategory') as HTMLSelectElement
  const type = document.getElementById('filterType') as HTMLSelectElement
  const min = document.getElementById('filterMinAmount') as HTMLInputElement
  const max = document.getElementById('filterMaxAmount') as HTMLInputElement
  const tag = document.getElementById('filterTag') as HTMLSelectElement
  const clearBtn = document.getElementById('filterClear')
  if (kw) kw.value = ''
  if (cat) cat.value = ''
  if (type) type.value = ''
  if (min) min.value = ''
  if (max) max.value = ''
  if (tag) tag.value = ''
  if (clearBtn) clearBtn.hidden = true
}