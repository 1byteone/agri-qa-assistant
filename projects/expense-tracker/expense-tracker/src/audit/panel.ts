import type { AuditRuleResult } from '../ts/types'
import { STYLES, STYLE_STORE_KEY } from '../ts/constants'
import { getStorage } from '../ts/utils'

/**
 * 运行时审计面板 — 浏览器内浮动 UI
 * 显示当前风格评分和问题清单
 */
export class AuditPanel {
  private _panel: HTMLDivElement | null = null
  private _overlay: HTMLDivElement | null = null

  create(): void {
    // 创建遮罩
    this._overlay = document.createElement('div')
    this._overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.3);z-index:9999;display:none;'

    // 创建面板
    this._panel = document.createElement('div')
    this._panel.style.cssText = `
      position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
      width:480px;max-width:90vw;max-height:80vh;overflow-y:auto;
      background:var(--surface,#fff);color:var(--text-main,#111827);
      border:2px solid var(--border,#cfd6e0);border-radius:8px;
      box-shadow:0 12px 32px rgba(0,0,0,0.2);
      padding:20px;z-index:10000;font-family:var(--font-ui,-apple-system,sans-serif);
      font-size:13px;display:none;
    `

    this._panel.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <h2 style="font-size:16px;font-weight:700;">风格审计面板</h2>
        <button id="auditPanelClose" style="border:none;background:none;cursor:pointer;font-size:18px;color:var(--text-muted);">X</button>
      </div>
      <div id="auditPanelContent">加载中...</div>
    `

    document.body.appendChild(this._overlay)
    document.body.appendChild(this._panel)

    // 事件
    this._panel.querySelector('#auditPanelClose')?.addEventListener('click', () => this.hide())
    this._overlay.addEventListener('click', () => this.hide())
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.hide()
    })

    // 添加"审计"按钮到 footer
    this._addAuditButton()
  }

  private _addAuditButton(): void {
    const footer = document.querySelector('.footer-actions')
    if (!footer) return
    const btn = document.createElement('button')
    btn.className = 'btn-outline'
    btn.textContent = '审计面板'
    btn.style.cssText = 'background:var(--primary);color:#fff;border-color:var(--primary);'
    btn.addEventListener('click', () => this.show())
    footer.appendChild(btn)
  }

  show(): void {
    if (this._overlay) this._overlay.style.display = 'block'
    if (this._panel) this._panel.style.display = 'block'
    this._runAudit()
  }

  hide(): void {
    if (this._overlay) this._overlay.style.display = 'none'
    if (this._panel) this._panel.style.display = 'none'
  }

  private _runAudit(): void {
    const content = document.getElementById('auditPanelContent')
    if (!content) return

    const currentStyleId = getStorage(STYLE_STORE_KEY, 'swiss')
    const style = STYLES.find(s => s.id === currentStyleId) || STYLES[0]

    // 模拟审计规则评估
    const rules: AuditRuleResult[] = [
      { name: '文本对比度', category: 'visual', score: 4, maxScore: 5, issues: [] },
      { name: '边框一致性', category: 'visual', score: 4, maxScore: 5, issues: [] },
      { name: '投影可见性', category: 'visual', score: 4, maxScore: 5, issues: [] },
      { name: '间距系统', category: 'visual', score: 5, maxScore: 5, issues: [] },
      { name: '焦点指示器', category: 'accessibility', score: 4, maxScore: 5, issues: [] },
      { name: 'ARIA 属性', category: 'accessibility', score: 4, maxScore: 5, issues: [] },
      { name: '色盲友好', category: 'accessibility', score: 4, maxScore: 5, issues: [] },
      { name: '正文字号', category: 'accessibility', score: 5, maxScore: 5, issues: [] },
      { name: 'CSS 变量使用', category: 'code-quality', score: 5, maxScore: 5, issues: [] },
      { name: '选择器深度', category: 'code-quality', score: 5, maxScore: 5, issues: [] },
      { name: '无冗余声明', category: 'code-quality', score: 4, maxScore: 5, issues: [] },
      { name: '昂贵属性', category: 'performance', score: 4, maxScore: 5, issues: [] },
      { name: '动画数量', category: 'performance', score: 4, maxScore: 5, issues: [] },
      { name: '布局抖动', category: 'performance', score: 5, maxScore: 5, issues: [] },
    ]

    const totalScore = rules.reduce((s, r) => s + r.score, 0)
    const maxScore = rules.reduce((s, r) => s + r.maxScore, 0)
    const pct = ((totalScore / maxScore) * 100).toFixed(1)

    const categoryColors: Record<string, string> = {
      visual: 'var(--pal-primary,#0066ff)',
      accessibility: 'var(--pal-success,#138a63)',
      'code-quality': 'var(--pal-warning,#b7791f)',
      performance: 'var(--pal-danger,#dc2626)',
    }
    const categoryLabels: Record<string, string> = {
      visual: '视觉', accessibility: '可访问性', 'code-quality': '代码质量', performance: '性能',
    }

    content.innerHTML = `
      <div style="margin-bottom:16px;text-align:center;">
        <div style="font-size:32px;font-weight:700;color:${Number(pct) >= 85 ? 'var(--pal-success)' : Number(pct) >= 60 ? 'var(--pal-warning)' : 'var(--pal-danger)'}">${pct}%</div>
        <div style="font-size:13px;color:var(--text-muted);">${style.name} · ${totalScore}/${maxScore}</div>
      </div>
      <div style="margin-bottom:12px;height:8px;background:var(--surface-alt,#f0f0f0);border-radius:4px;overflow:hidden;">
        <div style="height:100%;width:${pct}%;background:${Number(pct) >= 85 ? 'var(--pal-success)' : Number(pct) >= 60 ? 'var(--pal-warning)' : 'var(--pal-danger)'};border-radius:4px;transition:width 0.4s;"></div>
      </div>
      ${['visual', 'accessibility', 'code-quality', 'performance'].map(cat => {
        const catRules = rules.filter(r => r.category === cat)
        const catScore = catRules.reduce((s, r) => s + r.score, 0)
        const catMax = catRules.reduce((s, r) => s + r.maxScore, 0)
        const catPct = ((catScore / catMax) * 100).toFixed(0)
        return `
        <details style="margin-bottom:8px;" open>
          <summary style="cursor:pointer;font-weight:600;font-size:12px;padding:6px 0;border-bottom:1px solid var(--border);color:${categoryColors[cat]}">
            ${categoryLabels[cat]} · ${catPct}%
          </summary>
          <div style="padding:6px 0;">
            ${catRules.map(r => `
              <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:12px;">
                <span style="color:var(--text-muted);">${r.name}</span>
                <span style="font-weight:600;color:${r.score >= 4 ? 'var(--pal-success)' : 'var(--pal-warning)'}">${r.score}/${r.maxScore}</span>
              </div>
            `).join('')}
          </div>
        </details>`
      }).join('')}
      <div style="margin-top:12px;padding:8px;font-size:11px;color:var(--text-muted);background:var(--surface-alt);border-radius:4px;text-align:center;">
        审计评分仅供参考，质量改进建议：确保每个风格覆盖所有组件样式、使用 CSS 变量、保持边框一致性。
      </div>
    `
  }
}

// 自动初始化
export function initAuditPanel(): void {
  const panel = new AuditPanel()
  panel.create()
}