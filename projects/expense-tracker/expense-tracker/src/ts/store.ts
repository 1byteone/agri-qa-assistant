import type { ExpenseRecord, CategoryName, CategoryBudget, FilterState, SubCategoryConfig, AnnualReport } from './types'
import { STORE_KEY, BUDGET_KEY, SUB_CATEGORY_KEY } from './constants'
import { isValidRecord, getStorage, setStorage } from './utils'

/* ===== 分类标准化 ===== */
const CATEGORY_NAMES: readonly CategoryName[] = Object.freeze([
  '餐饮', '交通', '购物', '娱乐', '医疗', '固定账单', '其他',
])

const CATEGORY_ALIASES: Record<string, CategoryName> = Object.freeze({
  food: '餐饮', transport: '交通', shop: '购物', shopping: '购物',
  entertainment: '娱乐', health: '医疗', medical: '医疗', bills: '固定账单', other: '其他',
})

export function normalizeCategory(category: string): CategoryName {
  const value = category.trim()
  if (CATEGORY_NAMES.includes(value as CategoryName)) return value as CategoryName
  return CATEGORY_ALIASES[value.toLowerCase()] || '其他'
}

export function normalizeRecord(record: ExpenseRecord): ExpenseRecord {
  return {
    ...record,
    type: record.type || 'expense',
    amount: Number(record.amount),
    category: normalizeCategory(record.category),
    tags: Array.isArray(record.tags) ? record.tags : [],
    subCategory: record.subCategory || '',
    note: String(record.note || ''),
  }
}

/* ===== Store ===== */
class Store {
  private _records: ExpenseRecord[] = []
  private _budgets: CategoryBudget[] = []
  private _subCategories: SubCategoryConfig[] = []
  /** 全局已使用过的标签列表 (自动收集) */
  private _allTags: string[] = []
  private _history: ExpenseRecord[][] = []
  private _redo: ExpenseRecord[][] = []

  constructor() {
    this._records = this._load()
    this._budgets = this._loadBudgets()
    this._subCategories = this._loadSubCategories()
    this._allTags = this._extractTags()
  }

  /* ---- 读取 ---- */
  get records(): ExpenseRecord[] { return this._records }
  get budgets(): CategoryBudget[] { return this._budgets }
  get allTags(): string[] { return this._allTags }
  get subCategories(): SubCategoryConfig[] { return this._subCategories }

  /* ---- 加载/持久化 ---- */
  private _load(): ExpenseRecord[] {
    return getStorage<ExpenseRecord[]>(STORE_KEY, []).filter(isValidRecord).map(normalizeRecord)
  }
  private _loadBudgets(): CategoryBudget[] {
    return getStorage<CategoryBudget[]>(BUDGET_KEY, [])
  }
  private _loadSubCategories(): SubCategoryConfig[] {
    return getStorage<SubCategoryConfig[]>(SUB_CATEGORY_KEY, [])
  }
  save(): void { setStorage(STORE_KEY, this._records); this._allTags = this._extractTags() }
  saveBudgets(): void { setStorage(BUDGET_KEY, this._budgets) }
  saveSubCategories(): void { setStorage(SUB_CATEGORY_KEY, this._subCategories) }

  private _extractTags(): string[] {
    const set = new Set<string>()
    this._records.forEach(r => r.tags?.forEach(t => set.add(t)))
    return [...set].sort()
  }

  /* ---- CRUD ---- */
  add(record: ExpenseRecord): void {
    this._pushHistory()
    this._records.unshift(normalizeRecord(record))
    this.save()
  }

  update(id: string, updates: Partial<ExpenseRecord>): void {
    this._pushHistory()
    const idx = this._records.findIndex(r => r.id === id)
    if (idx >= 0) {
      this._records[idx] = normalizeRecord({ ...this._records[idx], ...updates })
      this.save()
    }
  }

  delete(id: string): void {
    this._pushHistory()
    const idx = this._records.findIndex(r => r.id === id)
    if (idx >= 0) { this._records.splice(idx, 1); this.save() }
  }

  getById(id: string): ExpenseRecord | undefined {
    return this._records.find(r => r.id === id)
  }

  /* ---- 子分类配置 ---- */
  getSubCategories(category: CategoryName): string[] {
    return this._subCategories.find(s => s.category === category)?.subCategories || []
  }
  setSubCategories(category: CategoryName, subs: string[]): void {
    const idx = this._subCategories.findIndex(s => s.category === category)
    if (idx >= 0) this._subCategories[idx] = { category, subCategories: subs }
    else this._subCategories.push({ category, subCategories: subs })
    this.saveSubCategories()
  }
  resetSubCategories(): void {
    this._subCategories = []
    this.saveSubCategories()
  }

  /* ---- 预算 ---- */
  setBudget(category: CategoryName, budget: number): void {
    const idx = this._budgets.findIndex(b => b.category === category)
    if (idx >= 0) {
      if (budget <= 0) this._budgets.splice(idx, 1)
      else this._budgets[idx] = { category, budget }
    } else if (budget > 0) {
      this._budgets.push({ category, budget })
    }
    this.saveBudgets()
  }

  getBudget(category: CategoryName): number {
    return this._budgets.find(b => b.category === category)?.budget || 0
  }

  getBudgetUsage(month: string): { category: CategoryName; budget: number; spent: number; pct: number }[] {
    const monthExp = this.getByMonth(month).filter(r => r.type === 'expense')
    const spent: Record<string, number> = {}
    monthExp.forEach(r => { spent[r.category] = (spent[r.category] || 0) + r.amount })
    return this._budgets.map(b => ({
      category: b.category,
      budget: b.budget,
      spent: spent[b.category] || 0,
      pct: b.budget > 0 ? Math.min((spent[b.category] || 0) / b.budget * 100, 100) : 0,
    }))
  }

  /* ---- 筛选 ---- */
  filter(filter: FilterState): ExpenseRecord[] {
    return this._records.filter(r => {
      // 关键词: 匹配 note / tags / subCategory
      if (filter.keyword) {
        const kw = filter.keyword.toLowerCase()
        const matchNote = r.note.toLowerCase().includes(kw)
        const matchTags = r.tags?.some(t => t.toLowerCase().includes(kw))
        const matchSub = r.subCategory?.toLowerCase().includes(kw)
        if (!matchNote && !matchTags && !matchSub) return false
      }
      // 分类
      if (filter.categories.length > 0 && !filter.categories.includes(r.category)) return false
      // 金额范围
      if (filter.minAmount > 0 && r.amount < filter.minAmount) return false
      if (filter.maxAmount > 0 && r.amount > filter.maxAmount) return false
      // 日期范围
      if (filter.dateRange[0] && r.date < filter.dateRange[0]) return false
      if (filter.dateRange[1] && r.date > filter.dateRange[1]) return false
      // 类型
      if (filter.types.length > 0 && !filter.types.includes(r.type)) return false
      // 标签
      if (filter.tags.length > 0 && !filter.tags.some(t => r.tags?.includes(t))) return false
      return true
    })
  }

  /* ---- 财务汇总 ---- */
  getIncome(records: ExpenseRecord[]): number {
    return records.filter(r => r.type === 'income').reduce((s, r) => s + r.amount, 0)
  }
  getExpense(records: ExpenseRecord[]): number {
    return records.filter(r => r.type === 'expense').reduce((s, r) => s + r.amount, 0)
  }
  getBalance(records: ExpenseRecord[]): number {
    return this.getIncome(records) - this.getExpense(records)
  }

  /* ---- 趋势数据 ---- */
  getDailyTotals(month: string): { date: string; expense: number; income: number }[] {
    const records = this.getByMonth(month)
    const days = new Date(parseInt(month.slice(0, 4)), parseInt(month.slice(5)), 0).getDate()
    const map: Record<string, { expense: number; income: number }> = {}
    records.forEach(r => {
      if (!map[r.date]) map[r.date] = { expense: 0, income: 0 }
      if (r.type === 'expense') map[r.date].expense += r.amount
      else map[r.date].income += r.amount
    })
    const result: { date: string; expense: number; income: number }[] = []
    for (let d = 1; d <= days; d++) {
      const date = `${month}-${String(d).padStart(2, '0')}`
      result.push(map[date] || { date, expense: 0, income: 0 })
    }
    return result
  }

  /* ---- 分类统计 ---- */
  getCategoryTotals(records: ExpenseRecord[]): { category: string; amount: number }[] {
    const map: Record<string, number> = {}
    records.filter(r => r.type === 'expense').forEach(r => {
      map[r.category] = (map[r.category] || 0) + r.amount
    })
    return Object.entries(map).sort(([, a], [, b]) => b - a).map(([category, amount]) => ({ category, amount }))
  }

  /* ---- 年度报告 ---- */
  getAnnualReport(year: number): AnnualReport {
    const yearRecords = this._records.filter(r => r.date.startsWith(String(year)))
    const expenses = yearRecords.filter(r => r.type === 'expense')
    const incomes = yearRecords.filter(r => r.type === 'income')
    const totalIncome = incomes.reduce((s, r) => s + r.amount, 0)
    const totalExpense = expenses.reduce((s, r) => s + r.amount, 0)

    // 月度分解
    const monthlyBreakdown: { month: number; income: number; expense: number; balance: number }[] = []
    for (let m = 1; m <= 12; m++) {
      const ms = String(m).padStart(2, '0')
      const mRecs = yearRecords.filter(r => r.date.startsWith(`${year}-${ms}`))
      const mInc = mRecs.filter(r => r.type === 'income').reduce((s, r) => s + r.amount, 0)
      const mExp = mRecs.filter(r => r.type === 'expense').reduce((s, r) => s + r.amount, 0)
      monthlyBreakdown.push({ month: m, income: mInc, expense: mExp, balance: mInc - mExp })
    }

    // 分类排名
    const catMap: Record<string, number> = {}
    expenses.forEach(r => { catMap[r.category] = (catMap[r.category] || 0) + r.amount })
    const total = totalExpense || 1
    const categoryRanking = Object.entries(catMap)
      .sort(([, a], [, b]) => b - a)
      .map(([category, amount]) => ({ category, amount, pct: (amount / total) * 100 }))

    // TOP10 单笔
    const topExpenses = [...expenses]
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 10)
      .map(r => ({ amount: r.amount, category: r.category, date: r.date, note: r.note }))

    // 月均支出
    const monthsWithExp = new Set(expenses.map(r => r.date.slice(0, 7))).size
    const monthlyAvg = monthsWithExp > 0 ? totalExpense / monthsWithExp : 0

    // 最大支出月
    let maxExpenseMonth = 1, maxExpenseAmount = 0
    monthlyBreakdown.forEach(m => {
      if (m.expense > maxExpenseAmount) { maxExpenseAmount = m.expense; maxExpenseMonth = m.month }
    })

    // 周末消费占比
    const weekendDays = expenses.filter(r => {
      const d = new Date(r.date); return d.getDay() === 0 || d.getDay() === 6
    }).length
    const weekendExpensePct = expenses.length > 0 ? (weekendDays / expenses.length) * 100 : 0

    // 预算完成率
    const budgetCompletion = this._budgets.map(b => {
      const spent = catMap[b.category] || 0
      return { category: b.category, budget: b.budget, spent, pct: b.budget > 0 ? (spent / b.budget) * 100 : 0 }
    })

    // 标签云
    const tagMap: Record<string, { count: number; amount: number }> = {}
    expenses.forEach(r => {
      r.tags?.forEach(t => {
        if (!tagMap[t]) tagMap[t] = { count: 0, amount: 0 }
        tagMap[t].count++
        tagMap[t].amount += r.amount
      })
    })
    const tagCloud = Object.entries(tagMap)
      .map(([tag, v]) => ({ tag, count: v.count, amount: v.amount }))
      .sort((a, b) => b.count - a.count)

    // 收支比
    const incomeExpenseRatio = totalExpense > 0 ? totalIncome / totalExpense : 0

    return {
      year, totalIncome, totalExpense, balance: totalIncome - totalExpense,
      monthlyBreakdown, categoryRanking, topExpenses,
      monthlyAvg, maxExpenseMonth, maxExpenseAmount,
      weekendExpensePct, budgetCompletion, tagCloud, incomeExpenseRatio,
    }
  }

  /* ---- 撤销/重做 ---- */
  private _pushHistory(): void {
    this._history.push(JSON.parse(JSON.stringify(this._records)))
    if (this._history.length > 20) this._history.shift()
    this._redo = []
  }
  undo(): boolean {
    if (this._history.length === 0) return false
    this._redo.push(JSON.parse(JSON.stringify(this._records)))
    this._records = this._history.pop()!
    this.save()
    return true
  }
  redo(): boolean {
    if (this._redo.length === 0) return false
    this._history.push(JSON.parse(JSON.stringify(this._records)))
    this._records = this._redo.pop()!
    this.save()
    return true
  }

  /* ---- 批量操作 ---- */
  replaceAll(records: ExpenseRecord[]): void {
    this._pushHistory()
    this._records = records.filter(isValidRecord).map(normalizeRecord)
    this.save()
  }
  clearAll(): void {
    this._pushHistory()                    // 保存清空前状态到历史栈，可撤销
    this._records = []
    this._redo = []                        // 只清空重做栈，保留历史栈
    this.save()
  }

  /* ---- 查询 ---- */
  getByMonth(month: string): ExpenseRecord[] {
    return this._records.filter(r => r.date.startsWith(month))
  }
  getByDate(date: string): ExpenseRecord[] {
    return this._records.filter(r => r.date === date)
  }
  getTotal(records: ExpenseRecord[]): number {
    return records.reduce((s, r) => s + r.amount, 0)
  }
}

export const store = new Store()