import type { AuditRuleResult, AuditIssue } from '../../ts/types'

export interface RuleContext {
  styleId: string
  computedStyles: Record<string, Record<string, string>>
  elements: Record<string, string[]>
}

export interface Rule {
  name: string
  category: 'visual' | 'accessibility' | 'code-quality' | 'performance'
  check: (ctx: RuleContext) => AuditRuleResult
}

/* ---- 辅助: 亮度计算 ---- */
function luminance(hex: string): number {
  const c = hex.replace('#', '')
  if (c.length < 6) return 0
  const r = parseInt(c.slice(0, 2), 16) / 255
  const g = parseInt(c.slice(2, 4), 16) / 255
  const b = parseInt(c.slice(4, 6), 16) / 255
  const [lr, lg, lb] = [r, g, b].map(v => {
    v = v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)
    return v
  })
  return 0.2126 * lr + 0.7152 * lg + 0.0722 * lb
}

function contrastRatio(a: string, b: string): number {
  const l1 = luminance(a)
  const l2 = luminance(b)
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)
}

/* ---- 规则: 对比度 ---- */
export const contrastCheck: Rule = {
  name: '文本对比度',
  category: 'visual',
  check: (ctx) => {
    const issues: AuditIssue[] = []
    const textMain = ctx.computedStyles['--pal-text-main']?.['--pal-text-main'] || '#111827'
    const bg = ctx.computedStyles['--pal-bg']?.['--pal-bg'] || '#f6f8fb'
    const ratio = contrastRatio(textMain, bg)
    if (ratio < 4.5) {
      issues.push({
        severity: 'error',
        message: `正文与背景对比度不足: ${ratio.toFixed(2)}:1（要求 >= 4.5:1）`,
        suggestion: '加深文本色或减淡背景色',
      })
    }
    const score = Math.min(5, Math.max(1, Math.round(ratio / 4.5 * 5)))
    return { name: '文本对比度', category: 'visual', score, maxScore: 5, issues }
  },
}

/* ---- 规则: 边框一致性 ---- */
export const borderConsistency: Rule = {
  name: '边框一致性',
  category: 'visual',
  check: (ctx) => {
    const issues: AuditIssue[] = []
    const borderWidth = ctx.computedStyles['--stl-border-width']?.['--stl-border-width'] || '1px'
    const sections = ctx.elements['.section'] || []
    if (sections.length > 0) {
      issues.push({
        severity: 'info',
        message: `边框宽度: ${borderWidth}`,
        suggestion: '确保同类元素使用相同的边框变量',
      })
    }
    return { name: '边框一致性', category: 'visual', score: 4, maxScore: 5, issues }
  },
}

/* ---- 规则: 投影可见性 ---- */
export const shadowVisibility: Rule = {
  name: '投影可见性',
  category: 'visual',
  check: (ctx) => {
    const issues: AuditIssue[] = []
    const shadow = ctx.computedStyles['--stl-shadow']?.['--stl-shadow'] || 'none'
    if (shadow === 'none' || shadow === '0') {
      issues.push({
        severity: 'info',
        message: '未使用投影（部分风格有意为之）',
      })
    }
    return { name: '投影可见性', category: 'visual', score: 4, maxScore: 5, issues }
  },
}

/* ---- 规则: 间距系统 ---- */
export const spacingUniformity: Rule = {
  name: '间距系统',
  category: 'visual',
  check: () => {
    return { name: '间距系统', category: 'visual', score: 5, maxScore: 5, issues: [] }
  },
}

export const visualRules: Rule[] = [
  contrastCheck,
  borderConsistency,
  shadowVisibility,
  spacingUniformity,
]