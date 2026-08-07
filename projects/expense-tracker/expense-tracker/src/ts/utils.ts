import type { Record } from './types'

/** HTML 转义 */
export function escapeHtml(v: unknown): string {
  return String(v ?? '').replace(
    /[\u0026\u003c\u003e"\u0027]/g,
    (c) =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[c] ?? c,
  )
}

/** 检查记录是否有效 — 保持宽松以兼容旧版数据，缺失字段由 normalizeRecord 兜底 */
export function isValidRecord(record: unknown): record is Record {
  if (!record || typeof record !== 'object') return false
  const r = record as Record
  return (
    Number.isFinite(Number(r.amount)) &&
    Number(r.amount) > 0 &&
    typeof r.date === 'string' &&
    /^\d{4}-\d{2}-\d{2}$/.test(r.date) &&
    typeof r.category === 'string'
  )
}

/** 获取今日日期字符串 YYYY-MM-DD */
export function todayStr(): string {
  return new Date().toISOString().slice(0, 10)
}

/** 获取当前月份 YYYY-MM */
export function currentMonthStr(): string {
  return new Date().toISOString().slice(0, 7)
}

/** 格式化金额 */
export function formatAmount(n: number): string {
  return n.toFixed(2)
}

/** 生成唯一 ID */
export function genId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
}

/** 读取 localStorage 安全包装 */
export function getStorage<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw !== null ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

/** 写入 localStorage 安全包装 */
export function setStorage(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (e) {
    console.warn('localStorage write failed:', e)
  }
}