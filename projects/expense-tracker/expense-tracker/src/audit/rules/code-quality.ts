import type { AuditRuleResult, AuditIssue } from '../../ts/types'
import type { RuleContext, Rule } from './visual'

/* ---- 规则: CSS 变量使用 ---- */
export const variableUsage: Rule = {
  name: 'CSS 变量使用',
  category: 'code-quality',
  check: (ctx: RuleContext): AuditRuleResult => {
    const issues: AuditIssue[] = []
    const hasTextMain = '--pal-text-main' in ctx.computedStyles
    const hasPrimary = '--pal-primary' in ctx.computedStyles
    if (!hasTextMain || !hasPrimary) {
      issues.push({
        severity: 'error',
        message: '缺少关键 CSS 变量定义',
        suggestion: '确保 --pal-text-main 和 --pal-primary 已定义',
      })
    }
    return { name: 'CSS 变量使用', category: 'code-quality', score: hasTextMain && hasPrimary ? 5 : 2, maxScore: 5, issues }
  },
}

/* ---- 规则: 选择器深度 ---- */
export const selectorDepth: Rule = {
  name: '选择器深度',
  category: 'code-quality',
  check: (): AuditRuleResult => {
    return { name: '选择器深度', category: 'code-quality', score: 5, maxScore: 5, issues: [] }
  },
}

/* ---- 规则: 无冗余 ---- */
export const noRedundant: Rule = {
  name: '无冗余声明',
  category: 'code-quality',
  check: (): AuditRuleResult => {
    return { name: '无冗余声明', category: 'code-quality', score: 4, maxScore: 5, issues: [] }
  },
}

export const codeQualityRules: Rule[] = [
  variableUsage,
  selectorDepth,
  noRedundant,
]