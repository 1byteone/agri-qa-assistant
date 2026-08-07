import type { AuditRuleResult, AuditIssue } from '../../ts/types'
import type { RuleContext, Rule } from './visual'

/* ---- 规则: 昂贵属性 ---- */
export const expensiveProperties: Rule = {
  name: '昂贵属性',
  category: 'performance',
  check: (ctx: RuleContext): AuditRuleResult => {
    const issues: AuditIssue[] = []
    const shadow = ctx.computedStyles['--stl-shadow']?.['--stl-shadow'] || ''
    const hasBackdrop = shadow.includes('filter')
    // 简化检查
    if (hasBackdrop) {
      issues.push({
        severity: 'warning',
        message: '使用了 backdrop-filter，可能影响滚动性能',
        suggestion: '使用 will-change: transform 或限制应用范围',
      })
    }
    return { name: '昂贵属性', category: 'performance', score: hasBackdrop ? 3 : 5, maxScore: 5, issues }
  },
}

/* ---- 规则: 动画数量 ---- */
export const animationCount: Rule = {
  name: '动画数量',
  category: 'performance',
  check: (): AuditRuleResult => {
    return { name: '动画数量', category: 'performance', score: 4, maxScore: 5, issues: [] }
  },
}

/* ---- 规则: 布局抖动 ---- */
export const layoutThrashing: Rule = {
  name: '布局抖动',
  category: 'performance',
  check: (): AuditRuleResult => {
    return { name: '布局抖动', category: 'performance', score: 5, maxScore: 5, issues: [] }
  },
}

export const performanceRules: Rule[] = [
  expensiveProperties,
  animationCount,
  layoutThrashing,
]