import { store } from '../store'
import { showToast, render } from '../render'
import { genId } from '../utils'
import type { CategoryName } from '../types'
import { DEFAULT_SUB_CATEGORIES } from '../types'

/* ===== 标签输入管理 ===== */
let currentTags: string[] = []

function initTagInput(): void {
  const input = document.getElementById('tagInput') as HTMLInputElement | null
  const list = document.getElementById('tagList')
  const suggestions = document.getElementById('tagSuggestions')
  if (!input || !list || !suggestions) return

  currentTags = []

  function renderTags(): void {
    list.innerHTML = currentTags.map(t =>
      `<span class="tag-chip">#${t} <button class="tag-remove" data-tag="${t}" type="button">&times;</button></span>`
    ).join('')
  }

  function showSuggestions(filter: string): void {
    const all = store.allTags.filter(t => t.includes(filter) && !currentTags.includes(t))
    if (all.length === 0 || !filter) {
      suggestions.hidden = true
      return
    }
    suggestions.innerHTML = all.map(t =>
      `<div class="tag-suggestion" data-tag="${t}">#${t}</div>`
    ).join('')
    suggestions.hidden = false
  }

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      const val = input.value.trim()
      if (val && !currentTags.includes(val)) {
        currentTags.push(val)
        renderTags()
      }
      input.value = ''
      suggestions.hidden = true
    }
    if (e.key === 'Backspace' && !input.value && currentTags.length > 0) {
      currentTags.pop()
      renderTags()
    }
  })

  input.addEventListener('input', () => {
    showSuggestions(input.value.trim())
  })

  // 事件委托: 点击标签移除按钮
  list.addEventListener('click', (e) => {
    const btn = (e.target as HTMLElement).closest('.tag-remove') as HTMLElement | null
    if (btn) {
      const tag = btn.dataset.tag
      if (tag) {
        currentTags = currentTags.filter(t => t !== tag)
        renderTags()
      }
    }
  })

  // 事件委托: 点击建议项
  suggestions.addEventListener('click', (e) => {
    const el = (e.target as HTMLElement).closest('.tag-suggestion') as HTMLElement | null
    if (el) {
      const tag = el.dataset.tag
      if (tag && !currentTags.includes(tag)) {
        currentTags.push(tag)
        renderTags()
        input.value = ''
        suggestions.hidden = true
      }
    }
  })

  // 点击外部关闭
  document.addEventListener('click', (e) => {
    const wrap = document.getElementById('tagInputWrap')
    if (wrap && !wrap.contains(e.target as Node)) {
      suggestions.hidden = true
    }
  })
}

/* ===== 子分类 ===== */
const DEFAULT_SUB_MAP: Record<string, string[]> = {}
DEFAULT_SUB_CATEGORIES.forEach(s => { DEFAULT_SUB_MAP[s.category] = s.subCategories })

function updateSubCategoryOptions(category: string): void {
  const sel = document.getElementById('subCatSelect') as HTMLSelectElement | null
  if (!sel) return
  const subs = store.getSubCategories(category as CategoryName)
  const defaults = DEFAULT_SUB_MAP[category] || []
  const allSubs = [...new Set([...subs, ...defaults])]
  sel.innerHTML = '<option value="">子分类</option>' + allSubs.map(s => `<option value="${s}">${s}</option>`).join('')
}

/* ===== 表单初始化 ===== */
export function initEntryForm(): void {
  const form = document.getElementById('entryForm') as HTMLFormElement | null
  if (!form) return

  initTagInput()

  // 类型切换
  const typeBtns = document.querySelectorAll('.type-btn')
  typeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      typeBtns.forEach(b => b.classList.remove('active'))
      btn.classList.add('active')
      ;(window as any).__selectedType = (btn as HTMLElement).dataset.type
      updateChipsForType()
    })
  })
  ;(window as any).__selectedType = 'expense'

  // 分类 Chip 交互
  const chips = document.querySelectorAll('.chip')
  chips.forEach(chip => {
    chip.addEventListener('click', () => selectChip(chip as HTMLElement))
    chip.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectChip(chip as HTMLElement) }
    })
  })

  // 子分类联动
  const catSelect = document.getElementById('catSelect') as HTMLSelectElement | null
  const subCatSelect = document.getElementById('subCatSelect') as HTMLSelectElement | null
  catSelect?.addEventListener('change', () => {
    updateSubCategoryOptions(catSelect.value)
    ;(window as any).__selectedCat = catSelect.value
  })
  // 初始化子分类
  if (catSelect) updateSubCategoryOptions(catSelect.value)

  // 表单提交
  form.addEventListener('submit', (e) => {
    e.preventDefault()
    const amountEl = document.getElementById('amount') as HTMLInputElement
    const dateEl = document.getElementById('date') as HTMLInputElement
    const noteEl = document.getElementById('note') as HTMLInputElement
    const amount = parseFloat(amountEl.value)
    if (!amount || amount <= 0) { showToast('请输入大于 0 的有效金额'); return }

    const editingId = (window as any).__editingId as string | undefined
    const isEditing = (window as any).__isEditing as boolean | undefined
    const selectedCat = catSelect?.value || '餐饮'
    const selectedSubCat = subCatSelect?.value || ''
    const selectedType = (window as any).__selectedType as string || 'expense'

    // 编辑时使用 editRecord 缓存的标签，否则用当前输入标签
    const editTags = (window as any).__currentEditTags as string[] | undefined
    const tags = isEditing && editTags ? [...editTags] : [...currentTags]

    const recordData = {
      amount,
      type: selectedType as any,
      category: selectedCat as any,
      subCategory: selectedSubCat,
      tags,
      date: dateEl.value,
      note: noteEl.value.trim() || '',
    }

    if (isEditing && editingId) {
      store.update(editingId, recordData)
      showToast('记录已更新', 'success')
      ;(window as any).__editingId = null
      ;(window as any).__isEditing = false
      ;(window as any).__currentEditTags = undefined
    } else {
      store.add({ id: genId(), ...recordData })
      showToast('记录已添加', 'success')
    }

    render()
    form.reset()
    dateEl.valueAsDate = new Date()
    // 清空标签
    currentTags = []
    const tagList = document.getElementById('tagList')
    if (tagList) tagList.innerHTML = ''
    // 重置子分类
    if (catSelect) updateSubCategoryOptions(catSelect.value)
    const submitBtn = form.querySelector('.btn-submit')
    if (submitBtn) submitBtn.textContent = '保存记录'
    setTimeout(() => amountEl.focus(), 100)
  })
}

function updateChipsForType(): void {
  // 收入模式下 chip 视觉提示改为绿色，已通过 CSS 处理
}

function selectChip(chip: HTMLElement): void {
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'))
  chip.classList.add('active')
  ;(window as any).__selectedCat = chip.dataset.cat
  const cat = chip.dataset.cat
  if (cat) updateSubCategoryOptions(cat)
}

/* ===== 预算弹窗 ===== */
export function initBudgetModal(): void {
  const toggle = document.getElementById('budgetToggle')
  const overlay = document.getElementById('budgetModalOverlay')
  const closeBtn = document.getElementById('budgetModalClose')
  const saveBtn = document.getElementById('budgetSaveBtn')
  const formEl = document.getElementById('budgetForm')
  if (!toggle || !overlay || !closeBtn || !saveBtn || !formEl) return

  const CATEGORIES = ['餐饮', '交通', '购物', '娱乐', '医疗', '固定账单', '其他']

  function open(): void {
    overlay.hidden = false
    formEl.innerHTML = CATEGORIES.map(cat => {
      const val = store.getBudget(cat as any)
      return `<div class="budget-form-row">
        <span class="budget-form-label">${cat}</span>
        <input type="number" class="budget-form-input" data-cat="${cat}" min="0" step="50" value="${val || ''}" placeholder="0">
      </div>`
    }).join('')
  }

  function close(): void { overlay.hidden = true }

  toggle.addEventListener('click', open)
  closeBtn.addEventListener('click', close)
  overlay.addEventListener('click', (e) => { if (e.target === overlay) close() })
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !overlay.hidden) close() })

  saveBtn.addEventListener('click', () => {
    const inputs = formEl.querySelectorAll('.budget-form-input')
    inputs.forEach(input => {
      const cat = (input as HTMLElement).dataset.cat
      const val = parseFloat((input as HTMLInputElement).value) || 0
      if (cat) store.setBudget(cat as any, val)
    })
    close()
    render()
    showToast('预算已保存', 'success')
  })
}