import type { ExpenseRecord } from './types'

/* ===== 真实场景数据池 ===== */

const CATS = ['餐饮', '交通', '购物', '娱乐', '医疗', '固定账单', '其他'] as const

/** 餐饮 — 真实场景备注 + 标签 + 子分类 */
const DINING = {
  notes: ['公司楼下快餐', '外卖午餐', '周末聚餐', '朋友请客回请', '商务宴请', '食堂', '火锅', '日料', '烧烤', '奶茶', '星巴克', '便利店早餐', '面包店', '水果店', '超市零食'],
  tags: ['工作餐', '外卖', '社交', '零食', '咖啡', '早餐'],
  subs: ['早餐', '午餐', '晚餐', '外卖', '零食', '咖啡', '聚餐'],
}
/** 交通 */
const TRANSIT = {
  notes: ['地铁通勤', '公交上班', '打车去车站', '周末打车', '加油', 'ETC充值', '停车费', '共享单车月卡', '高铁票', '机场大巴'],
  tags: ['通勤', '出差', '旅行', '打车'],
  subs: ['地铁', '公交', '打车', '加油', '停车', '共享单车'],
}
/** 购物 */
const SHOPPING = {
  notes: ['超市采购', '网购日用品', '衣服', '鞋子', '数码配件', '家居用品', '书店', '文具', '化妆品', '母婴用品'],
  tags: ['日用', '网购', '服饰', '数码', '家居'],
  subs: ['超市', '网购', '日用品', '衣服', '数码', '家居'],
}
/** 娱乐 */
const ENTERTAIN = {
  notes: ['电影票', '游戏充值', 'KTV', '健身房月卡', '游泳', '旅游门票', '酒店住宿', '剧本杀', '桌游', '宠物零食'],
  tags: ['电影', '游戏', '运动', '旅游', '社交', '宠物'],
  subs: ['电影', '游戏', '运动', '旅游', '社交', '宠物'],
}
/** 医疗 */
const MEDICAL = {
  notes: ['挂号费', '药房买药', '体检套餐', '牙科治疗', '眼科检查', '中医调理', '疫苗', '按摩理疗'],
  tags: ['药品', '体检', '牙科', '眼科', '中医'],
  subs: ['挂号', '药品', '体检', '牙科', '眼科'],
}
/** 固定账单 */
const BILLS = {
  notes: ['房租', '电费', '水费', '燃气费', '宽带费', '手机话费', '物业费', '停车月卡'],
  tags: ['住房', '水电', '通信', '物业'],
  subs: ['房租', '水电', '燃气', '网费', '话费', '物业'],
}
/** 其他 */
const OTHER = {
  notes: ['礼物', '快递费', '公益捐款', '红包', '维修费', '快递', '打印', '证件照'],
  tags: ['礼物', '快递', '公益', '其他'],
  subs: ['礼物', '快递', '公益', '其他'],
}

const CATEGORY_DATA: Record<string, typeof DINING> = {
  '餐饮': DINING, '交通': TRANSIT, '购物': SHOPPING,
  '娱乐': ENTERTAIN, '医疗': MEDICAL, '固定账单': BILLS, '其他': OTHER,
}

/** 收入备注池 */
const INCOME_DATA = {
  notes: ['1月工资', '2月工资', '3月工资', '4月工资', '5月工资', '6月工资',
    '项目奖金', '年终奖', '兼职收入', '理财收益', '基金分红', '红包收入',
    '二手出售', '稿费', '咨询费', '返现'],
  tags: ['工资', '奖金', '兼职', '理财', '红包', '其他收入'],
}

/* ===== 工具函数 ===== */
const rng = (min: number, max: number) => Math.random() * (max - min) + min
const rInt = (min: number, max: number) => Math.floor(rng(min, max))
const pick = <T>(arr: readonly T[] | T[]): T => arr[rInt(0, arr.length)]
const pickN = <T>(arr: readonly T[] | T[], n: number): T[] => {
  const shuffled = [...arr].sort(() => Math.random() - 0.5)
  return shuffled.slice(0, Math.min(n, arr.length))
}
const round2 = (n: number) => parseFloat(n.toFixed(2))

/* ===== 按分类生成单条支出 ===== */
function generateExpense(date: string, id: string): ExpenseRecord {
  const cat = pick(CATS)
  const data = CATEGORY_DATA[cat]

  // 金额范围按分类真实分布
  const ranges: Record<string, [number, number]> = {
    '餐饮': [5, 200], '交通': [1, 100], '购物': [10, 800],
    '娱乐': [10, 500], '医疗': [15, 1500], '固定账单': [50, 3000], '其他': [5, 300],
  }
  const [min, max] = ranges[cat] || [5, 200]
  const amount = round2(rng(min, max))

  return {
    id,
    type: 'expense',
    amount,
    category: cat,
    subCategory: pick(data.subs),
    tags: pickN(data.tags, rInt(0, 2)),
    date,
    note: pick(data.notes),
  }
}

/* ===== 生成单条收入 ===== */
function generateIncome(date: string, id: string): ExpenseRecord {
  // 用真实感分布：工资类固定较高，其他随机
  const isSalary = Math.random() < 0.4
  const amount = isSalary
    ? round2(rng(5000, 25000))
    : round2(rng(100, 5000))
  const tags = isSalary ? ['工资'] : pickN(['奖金', '兼职', '理财', '红包', '其他收入'], rInt(0, 1))
  return {
    id,
    type: 'income',
    amount,
    category: '其他',
    subCategory: '',
    tags,
    date,
    note: pick(INCOME_DATA.notes),
  }
}

/* ===== 公开生成函数：每次调用返回全新随机数据 ===== */
export function generateSampleData(): ExpenseRecord[] {
  const records: ExpenseRecord[] = []
  let idCounter = Date.now() * 1000

  const now = new Date()
  const baseYear = now.getFullYear()
  const baseMonth = now.getMonth()

  // 生成过去 6 个月的数据
  for (let mOffset = 0; mOffset < 6; mOffset++) {
    const targetMonth = new Date(baseYear, baseMonth - mOffset, 1)
    const year = targetMonth.getFullYear()
    const month = targetMonth.getMonth()
    const daysInMonth = new Date(year, month + 1, 0).getDate()

    // 每月 25-50 条支出
    const entriesPerMonth = rInt(25, 50)
    for (let i = 0; i < entriesPerMonth; i++) {
      const day = rInt(1, daysInMonth)
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
      records.push(generateExpense(dateStr, String(idCounter++)))
    }

    // 每月 1-3 条收入
    const incCount = rInt(1, 3)
    for (let i = 0; i < incCount; i++) {
      const day = rInt(1, 28)
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
      records.push(generateIncome(dateStr, String(idCounter++)))
    }
  }

  return records.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
}

/* ===== 默认预算（每次 demo 加载时调用） ===== */
export function getDefaultBudgets(): { category: string; budget: number }[] {
  return [
    { category: '餐饮', budget: 2000 },
    { category: '交通', budget: 500 },
    { category: '购物', budget: 1500 },
    { category: '娱乐', budget: 800 },
    { category: '医疗', budget: 500 },
    { category: '固定账单', budget: 3000 },
    { category: '其他', budget: 500 },
  ]
}