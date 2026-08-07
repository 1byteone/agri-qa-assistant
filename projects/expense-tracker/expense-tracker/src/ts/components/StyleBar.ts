import { STYLES, STYLE_SWATCH_COLORS, STYLE_STORE_KEY } from '../constants'
import { styleLoader } from '../style-loader'
import { updateStatus } from '../render'

export function initStyleBar(): void {
  const container = document.getElementById('styleSwatches')
  const nameDisplay = document.getElementById('styleNameDisplay')
  if (!container) return

  const current = (() => {
    try { return localStorage.getItem(STYLE_STORE_KEY) || 'swiss' }
    catch { return 'swiss' }
  })()

  container.innerHTML = STYLES.map(s => {
    const bg = STYLE_SWATCH_COLORS[s.id] || '#666'
    return `<button class="style-swatch${s.id === current ? ' active' : ''}" type="button" data-style-id="${s.id}"
      style="background:${bg};" aria-label="切换到${s.name}" aria-pressed="${s.id === current}" role="radio">
      <span class="style-swatch-label">${s.short}</span></button>`
  }).join('')

  container.addEventListener('click', (e) => {
    const sw = (e.target as HTMLElement).closest('.style-swatch') as HTMLElement | null
    if (sw) applyStyle(sw.dataset.styleId!)
  })

  container.addEventListener('keydown', (e) => {
    const sws = [...container.querySelectorAll('.style-swatch')] as HTMLElement[]
    const idx = sws.indexOf(document.activeElement as HTMLElement)
    if (idx === -1) return
    let next = -1
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = (idx + 1) % sws.length
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = (idx - 1 + sws.length) % sws.length
    if (next >= 0) { sws[next].focus(); e.preventDefault() }
    if (e.key === 'Enter' || e.key === ' ') {
      const active = document.activeElement as HTMLElement
      if (active?.dataset.styleId) { applyStyle(active.dataset.styleId); e.preventDefault() }
    }
  })

  const s = STYLES.find(s => s.id === current) || STYLES[0]
  if (nameDisplay) nameDisplay.textContent = `设计风格：${s.name}`
}

function applyStyle(id: string): void {
  styleLoader.style = id
  const s = STYLES.find(s => s.id === id) || STYLES[0]
  const nameDisplay = document.getElementById('styleNameDisplay')
  if (nameDisplay) nameDisplay.textContent = `设计风格：${s.name}`
  document.querySelectorAll('.style-swatch').forEach(sw =>
    sw.classList.toggle('active', (sw as HTMLElement).dataset.styleId === id)
  )
  updateStatus(`设计风格已切换为「${s.name}」`)
}