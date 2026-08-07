import { PALETTES, PALETTE_STORE_KEY } from '../constants'
import { styleLoader } from '../style-loader'
import { updateStatus } from '../render'

export function initPaletteBar(): void {
  const container = document.getElementById('paletteSwatches')
  const nameDisplay = document.getElementById('paletteNameDisplay')
  if (!container) return

  const current = (() => {
    try { return localStorage.getItem(PALETTE_STORE_KEY) || 'default' }
    catch { return 'default' }
  })()

  container.innerHTML = PALETTES.map(p =>
    `<button class="palette-swatch${p.id === current ? ' active' : ''}" type="button" data-palette-id="${p.id}"
      style="background:${p.primary};" aria-label="切换到${p.name}调色板" aria-pressed="${p.id === current}" role="radio"></button>`
  ).join('')

  container.addEventListener('click', (e) => {
    const sw = (e.target as HTMLElement).closest('.palette-swatch') as HTMLElement | null
    if (sw) applyPalette(sw.dataset.paletteId!)
  })

  container.addEventListener('keydown', (e) => {
    const sws = [...container.querySelectorAll('.palette-swatch')] as HTMLElement[]
    const idx = sws.indexOf(document.activeElement as HTMLElement)
    if (idx === -1) return
    let next = -1
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = (idx + 1) % sws.length
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = (idx - 1 + sws.length) % sws.length
    if (next >= 0) { sws[next].focus(); e.preventDefault() }
    if (e.key === 'Enter' || e.key === ' ') {
      const active = document.activeElement as HTMLElement
      if (active?.dataset.paletteId) { applyPalette(active.dataset.paletteId); e.preventDefault() }
    }
  })

  // 初始显示
  const p = PALETTES.find(p => p.id === current) || PALETTES[0]
  if (nameDisplay) nameDisplay.textContent = `调色板：${p.name}`
}

function applyPalette(id: string): void {
  styleLoader.palette = id
  const p = PALETTES.find(p => p.id === id) || PALETTES[0]
  const nameDisplay = document.getElementById('paletteNameDisplay')
  if (nameDisplay) nameDisplay.textContent = `调色板：${p.name}`
  document.querySelectorAll('.palette-swatch').forEach(sw =>
    sw.classList.toggle('active', (sw as HTMLElement).dataset.paletteId === id)
  )
  updateStatus(`调色板已切换为「${p.name}」`)
}