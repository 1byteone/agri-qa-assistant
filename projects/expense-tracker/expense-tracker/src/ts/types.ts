/* ===== 核心类型定义 ===== */

/** 记录类型 */
export type RecordType = 'expense' | 'income'

/** 单条记账记录 */
export interface ExpenseRecord {
  id: string
  type: RecordType
  amount: number
  category: CategoryName
  subCategory?: string    // 子分类 (如 餐饮→午餐)
  tags: string[]          // 自定义标签 (如 #出差 #报销)
  date: string            // YYYY-MM-DD
  note: string
}

/** 分类名称 */
export type CategoryName =
  | '餐饮' | '交通' | '购物' | '娱乐'
  | '医疗' | '固定账单' | '其他'

export const ALL_CATEGORIES: readonly CategoryName[] = Object.freeze([
  '餐饮', '交通', '购物', '娱乐', '医疗', '固定账单', '其他',
])

export const INCOME_CATEGORIES: readonly string[] = Object.freeze([
  '工资', '兼职', '理财', '红包', '其他收入',
])

/** 子分类配置 — 每个分类下可选的子分类列表 */
export interface SubCategoryConfig {
  category: CategoryName
  subCategories: string[]
}

/** 默认子分类提议 */
export const DEFAULT_SUB_CATEGORIES: readonly SubCategoryConfig[] = Object.freeze([
  { category: '餐饮', subCategories: ['早餐', '午餐', '晚餐', '外卖', '零食', '咖啡', '聚餐'] },
  { category: '交通', subCategories: ['地铁', '公交', '打车', '加油', '停车', '共享单车'] },
  { category: '购物', subCategories: ['超市', '网购', '日用品', '衣服', '数码', '家居'] },
  { category: '娱乐', subCategories: ['电影', '游戏', '运动', '旅游', '社交', '宠物'] },
  { category: '医疗', subCategories: ['挂号', '药品', '体检', '牙科', '眼科'] },
  { category: '固定账单', subCategories: ['房租', '水电', '燃气', '网费', '话费', '物业'] },
  { category: '其他', subCategories: ['礼物', '快递', '公益', '其他'] },
])

/** 分类预算 */
export interface CategoryBudget {
  category: CategoryName
  budget: number      // 月度预算上限
}

/** 筛选状态 */
export interface FilterState {
  keyword: string               // 搜索关键词 (匹配 note / tags / subCategory)
  categories: CategoryName[]    // 选中的分类 (空 = 全部)
  minAmount: number             // 最小金额 (0 = 不限)
  maxAmount: number             // 最大金额 (0 = 不限)
  dateRange: [string, string]   // 日期范围 [start, end] ('' = 不限)
  types: RecordType[]           // 记录类型 (空 = 全部)
  tags: string[]                // 标签筛选 (空 = 全部)
}

/** 默认筛选状态 */
export const DEFAULT_FILTER: FilterState = {
  keyword: '',
  categories: [],
  minAmount: 0,
  maxAmount: 0,
  dateRange: ['', ''],
  types: [],
  tags: [],
}

/** 年度报告数据 */
export interface AnnualReport {
  year: number
  totalIncome: number
  totalExpense: number
  balance: number
  monthlyBreakdown: { month: number; income: number; expense: number; balance: number }[]
  categoryRanking: { category: string; amount: number; pct: number }[]
  topExpenses: { amount: number; category: string; date: string; note: string }[]
  monthlyAvg: number
  maxExpenseMonth: number
  maxExpenseAmount: number
  weekendExpensePct: number
  budgetCompletion: { category: string; budget: number; spent: number; pct: number }[]
  tagCloud: { tag: string; count: number; amount: number }[]
  incomeExpenseRatio: number
}

/* ===== 以下为原有类型 (保持不变) ===== */

/** 调色板定义 */
export interface Palette {
  id: string
  name: string
  primary: string
}

/** 一个设计风格的所有 CSS 变量覆盖 */
export interface StyleCSS {
  '--stl-radius': string
  '--stl-border-width': string
  '--stl-border-style': string
  '--stl-font-ui': string
  '--stl-font-heading': string
  '--stl-letter-spacing': string
  '--stl-line-height': string
  '--stl-shadow': string
  '--stl-chip-style': string
  '--stl-btn-style': string
  '--stl-header-border': string
  '--stl-decoration': string
  [key: string]: string
}

/** 设计风格定义 */
export interface Style {
  id: string
  name: string
  short: string
  css: Partial<StyleCSS>
  injectCSS: string | null
}

/** 头像定义 */
export interface Avatar {
  id: string
  name: string
  fallback: string
}

/** 审计规则结果 */
export interface AuditResult {
  styleId: string
  styleName: string
  score: number
  maxScore: number
  rules: AuditRuleResult[]
  timestamp: string
}

/** 单条审计规则结果 */
export interface AuditRuleResult {
  name: string
  category: 'visual' | 'accessibility' | 'code-quality' | 'performance'
  score: number
  maxScore: number
  issues: AuditIssue[]
}

/** 审计问题 */
export interface AuditIssue {
  severity: 'error' | 'warning' | 'info'
  message: string
  selector?: string
  suggestion?: string
}

/** 应用状态 */
export interface AppState {
  records: ExpenseRecord[]
  currentMonth: string
  selectedCat: CategoryName
  selectedAvatarId: string
  selectedPalette: string
  selectedStyle: string
  isEditing: boolean
  editingId: string | null
}