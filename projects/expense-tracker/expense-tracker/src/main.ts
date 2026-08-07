import './styles/main.scss'
import './styles/styles/_index.scss'

import { styleLoader } from './ts/style-loader'
import { render, initRenderer, resetFilterState } from './ts/render'
import { initEntryForm, initBudgetModal } from './ts/components/EntryForm'
import { renderAvatarPicker } from './ts/components/AvatarPicker'
import { initPaletteBar } from './ts/components/PaletteBar'
import { initStyleBar } from './ts/components/StyleBar'
import { store } from './ts/store'
import { showToast, updateStatus } from './ts/render'
import { initAuditPanel } from './audit/panel'
import { generateSampleData, getDefaultBudgets } from './ts/sample-data'

function initApp(): void {
  styleLoader.init()
  renderAvatarPicker()
  initPaletteBar()
  initStyleBar()
  initRenderer()
  initEntryForm()
  initBudgetModal()
  render()

  // 撤销快捷键
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
      e.preventDefault()
      if (store.undo()) { render(); showToast('已撤销上一步操作', 'info') }
      else { showToast('没有可撤销的操作') }
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
      e.preventDefault()
      if (store.redo()) { render(); showToast('已重做', 'info') }
      else { showToast('没有可重做的操作') }
    }
  })

  // 示例数据按钮 — 每次点击生成全新随机数据
  const demoBtn = document.getElementById('demoBtn')
  demoBtn?.addEventListener('click', () => {
    if (store.records.length > 0) { showToast('已有数据，如需重新加载请先清空', 'warning'); return }
    store.replaceAll(generateSampleData())
    // 加载默认预算
    getDefaultBudgets().forEach(b => store.setBudget(b.category as any, b.budget))
    render()
    showToast('已添加随机生成的示例数据，含标签/子分类/收入记录', 'success')
    updateStatus('示例数据已加载')
  })

  // 导出
  document.getElementById('exportBtn')?.addEventListener('click', () => {
    const blob = new Blob(
      [JSON.stringify({ records: store.records, budgets: store.budgets, exportedAt: new Date().toISOString() }, null, 2)],
      { type: 'application/json' },
    )
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `开销备份_${new Date().toISOString().split('T')[0]}.json`
    a.click(); URL.revokeObjectURL(url); showToast('数据已导出')
  })

  // 导入
  document.getElementById('importBtn')?.addEventListener('click', () => { document.getElementById('importFile')?.click() })
  document.getElementById('importFile')?.addEventListener('change', (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      try {
        const data = JSON.parse(ev.target?.result as string)
        const normalizedRecords = (
          Array.isArray(data?.records) ? data.records :
          Array.isArray(data) ? data : null
        )?.filter((r: unknown) => {
          const rec = r as any
          return rec && Number.isFinite(Number(rec.amount)) && Number(rec.amount) > 0 &&
            typeof rec.date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(rec.date) &&
            typeof rec.category === 'string'
        }) || null
        if (normalizedRecords && confirm('导入会替换当前全部记录，确定继续吗？')) {
          store.replaceAll(normalizedRecords)
          if (Array.isArray(data?.budgets)) {
            data.budgets.forEach((b: any) => {
              if (b.category && b.budget > 0) store.setBudget(b.category, b.budget)
            })
          }
          render()
          showToast('数据导入成功', 'success')
        } else if (!normalizedRecords) {
          alert('JSON 数据格式无效')
        }
      } catch (err) { alert(`文件解析失败：${(err as Error).message}`) }
    }
    reader.readAsText(file)
  })

  // 清空 — 同时重置筛选状态
  document.getElementById('clearBtn')?.addEventListener('click', () => {
    if (confirm('确定清空全部记录吗？此操作无法撤销。')) {
      store.clearAll()
      resetFilterState()
      render()
      showToast('全部记录已清空，筛选已重置', 'warning')
    }
  })

  initAuditPanel()
  updateStatus('就绪')
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp)
} else {
  initApp()
}