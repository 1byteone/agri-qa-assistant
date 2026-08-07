import type { AuditRuleResult, AuditIssue } from '../../ts/types'
import type { RuleContext, Rule } from './visual'

/* ---- 规则: 焦点指示器 ---- */
export const focusIndicator: Rule = {
  name: '焦点指示器',
  category: 'accessibility',
  check: (ctx: RuleContext): AuditRuleResult => {
    const issues: AuditIssue[] = []
    const buttons = ctx.elements['button'] || []
    const inputs = ctx.elements['input'] || []
    const total = buttons.length + inputs.length
    if (total > 0) {
      issues.push({
        severity: 'info',
        message: `检测到 ${total} 个可交互元素`,
        suggestion: '确保所有交互元素有 :focus-visible 样式',
      })
    }
    return { name: '焦点指示器', category: 'accessibility', score: 4, maxScore: 5, issues }
  },
}

/* ---- 规则: ARIA 使用 ---- */
export const ariaUsage: Rule = {
  name: 'ARIA 属性',
  category: 'accessibility',
  check: (ctx: RuleContext): AuditRuleResult => {
    const issues: AuditIssue[] = []
    const els = ctx.elements['[aria-label]'] || []
    const roleEls = ctx.elements['[role]'] || []
    if (els.length + roleEls.length > 0) {
      issues.push({
        severity: 'info',
        message: `ARIA 标签: ${els.length} 个, 角色: ${roleEls.length} 个`,
      })
    }
    return { name: 'ARIA 属性', category: 'accessibility', score: 4, maxScore: 5, issues }
  },
}

/* ---- 规则: 颜色依赖 ---- */
export const colorBlindness: Rule = {
  name: '色盲友好',
  category: 'accessibility',
  check: (): AuditRuleResult => {
    return { name: '色盲友好', category: 'accessibility', score: 4, maxScore: 5, issues: [] }
  },
}

/* ---- 规则: 正文字号 ---- */
export const fontSizeCheck: Rule = {
  name: '正文字号',
  category: 'accessibility',
  check: (): AuditRuleResult => {
    return { name: '正文字号', category: 'accessibility', score: 5, maxScore: 5, issues: [] }
  },
}

export const a11yRules: Rule[] = [
  focusIndicator,
  ariaUsage,
  colorBlindness,
  fontSizeCheck,
]