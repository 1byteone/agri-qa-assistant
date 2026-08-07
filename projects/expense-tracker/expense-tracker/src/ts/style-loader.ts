import type { Style } from './types'
import { STYLES, STYLE_STORE_KEY, PALETTES, PALETTE_STORE_KEY } from './constants'
import { setStorage, getStorage } from './utils'

/**
 * 风格加载器 — 负责动态切换 data-palette / data-style
 * 以及注入 injectCSS 额外样式
 */
class StyleLoader {
  private _currentPalette: string
  private _currentStyle: string
  private _injectEl: HTMLStyleElement | null = null

  constructor() {
    this._currentPalette = getStorage(PALETTE_STORE_KEY, 'default')
    this._currentStyle = getStorage(STYLE_STORE_KEY, 'swiss')
    this._ensureInjectElement()
  }

  /* ---- 调色板 ---- */
  get palette(): string {
    return this._currentPalette
  }

  set palette(id: string) {
    this._currentPalette = id
    this._applyPalette(id)
    setStorage(PALETTE_STORE_KEY, id)
  }

  get paletteInfo() {
    return PALETTES.find(p => p.id === this._currentPalette) || PALETTES[0]
  }

  private _applyPalette(id: string): void {
    const el = document.documentElement
    el.removeAttribute('data-palette')
    if (id && id !== 'default') {
      el.setAttribute('data-palette', id)
    }
  }

  /* ---- 风格 ---- */
  get style(): string {
    return this._currentStyle
  }

  set style(id: string) {
    this._currentStyle = id
    this._applyStyle(id)
    setStorage(STYLE_STORE_KEY, id)
  }

  get styleInfo(): Style {
    return STYLES.find(s => s.id === this._currentStyle) || STYLES[0]
  }

  private _applyStyle(id: string): void {
    const style = STYLES.find(s => s.id === id)
    if (!style) return

    const root = document.documentElement
    root.setAttribute('data-style', id)

    // 应用 CSS 变量覆盖
    Object.entries(style.css).forEach(([key, val]) => {
      root.style.setProperty(key, val)
    })

    // 注入 injectCSS
    this._injectExtraCSS(style.injectCSS)
  }

  private _injectExtraCSS(css: string | null): void {
    if (!this._injectEl) this._ensureInjectElement()
    if (this._injectEl) {
      this._injectEl.textContent = css || ''
    }
  }

  private _ensureInjectElement(): void {
    let el = document.getElementById('styleInject')
    if (!el) {
      el = document.createElement('style')
      el.id = 'styleInject'
      document.head.appendChild(el)
    }
    this._injectEl = el as HTMLStyleElement
  }

  /* ---- 初始化 ---- */
  init(): void {
    this._applyPalette(this._currentPalette)
    this._applyStyle(this._currentStyle)
  }

  /* ---- 获取所有风格列表 ---- */
  get allStyles(): readonly Style[] {
    return STYLES
  }

  get allPalettes() {
    return PALETTES
  }
}

export const styleLoader = new StyleLoader()