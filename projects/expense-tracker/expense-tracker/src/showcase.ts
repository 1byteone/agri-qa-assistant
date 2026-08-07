import './styles/main.scss'
import './styles/styles/_index.scss'

import { STYLES, STYLE_SWATCH_COLORS, PALETTES, PALETTE_STORE_KEY, STYLE_STORE_KEY } from './ts/constants'
import { escapeHtml, getStorage, setStorage } from './ts/utils'

/* ===== 调色板切换 ===== */
function initPalettePicker(): void {
  const current = getStorage(PALETTE_STORE_KEY, 'default')
  const bar = document.createElement('div')
  bar.className = 'palette-bar'
  bar.style.cssText = 'display:flex;align-items:center;gap:6px;margin-bottom:16px;flex-wrap:wrap;'
  const label = document.createElement('span')
  label.className = 'palette-label'
  label.textContent = '调色板'
  bar.appendChild(label)
  PALETTES.forEach(p => {
    const sw = document.createElement('button')
    sw.className = 'palette-swatch' + (p.id === current ? ' active' : '')
    sw.style.cssText = `width:22px;height:22px;border-radius:50%;border:2px solid var(--border);cursor:pointer;background:${p.primary};${p.id === current ? 'border-color:var(--text-main);transform:scale(1.15);' : ''}`
    sw.dataset.paletteId = p.id
    sw.setAttribute('aria-label', `切换到${p.name}调色板`)
    sw.addEventListener('click', () => {
      document.documentElement.removeAttribute('data-palette')
      if (p.id !== 'default') document.documentElement.setAttribute('data-palette', p.id)
      setStorage(PALETTE_STORE_KEY, p.id)
      bar.querySelectorAll('.palette-swatch').forEach(s => s.classList.remove('active'))
      sw.classList.add('active')
      sw.style.borderColor = 'var(--text-main)'
      showToast(`调色板已切换为「${p.name}」`)
    })
    bar.appendChild(sw)
  })
  document.querySelector('.subtitle')?.after(bar)
}

/* ===== 风格切换 ===== */
let currentStyle = getStorage(STYLE_STORE_KEY, 'swiss')

function applyStyle(id: string): void {
  currentStyle = id
  const style = STYLES.find(s => s.id === id)
  if (!style) return
  const root = document.documentElement
  root.setAttribute('data-style', id)
  Object.entries(style.css).forEach(([key, val]) => root.style.setProperty(key, val))
  const injectEl = document.getElementById('styleInject') as HTMLStyleElement
  if (injectEl) injectEl.textContent = style.injectCSS || ''
  setStorage(STYLE_STORE_KEY, id)
  document.querySelectorAll('.style-pill').forEach(el => {
    el.classList.toggle('active', (el as HTMLElement).dataset.styleId === id)
  })
  document.getElementById('pageTitle')!.textContent = `设计风格展示 — ${style.name}`
  showToast(`已切换为「${style.name}」`)
}

function initStylePicker(): void {
  const container = document.getElementById('stylePicker')!
  STYLES.forEach(s => {
    const pill = document.createElement('button')
    pill.className = 'style-pill' + (s.id === currentStyle ? ' active' : '')
    pill.textContent = s.short
    pill.dataset.styleId = s.id
    pill.title = s.name
    pill.addEventListener('click', () => applyStyle(s.id))
    container.appendChild(pill)
  })
  // Apply initial style
  applyStyle(currentStyle)
}

/* ===== 展示卡片 ===== */
function buildShowcaseCards(): void {
  const grid = document.getElementById('showcaseGrid')!
  grid.innerHTML = STYLES.map(s => {
    const bg = STYLE_SWATCH_COLORS[s.id] || '#666'
    return `
    <div class="showcase-card" data-style-id="${s.id}">
      <h3>${escapeHtml(s.name)} <span style="font-size:11px;font-weight:400;color:var(--text-muted);">(${s.short})</span></h3>
      <p>${getStyleDescription(s.id)}</p>
      <div>
        <button class="demo-btn" data-preview="${s.id}">按钮</button>
        <span class="demo-chip active">标签</span>
        <span class="demo-chip">次要</span>
      </div>
      <div style="margin-top:12px;">
        <div class="demo-stat"><span class="stat-label">分类</span><span class="stat-value">¥128.00</span></div>
        <div class="demo-stat"><span class="stat-label">分类</span><span class="stat-value">¥56.50</span></div>
      </div>
      <div style="margin-top:12px;">
        <input class="demo-input" type="text" placeholder="输入框示例" readonly value="示例文本">
      </div>
      <div style="margin-top:8px;">
        <div class="demo-record"><span>餐饮 · 午餐</span><span>¥35.00</span></div>
        <div class="demo-record"><span>交通 · 地铁</span><span>¥6.00</span></div>
      </div>
      <div style="margin-top:12px;display:flex;gap:6px;flex-wrap:wrap;">
        <button class="btn-outline" style="font-size:11px;padding:4px 10px;" onclick="document.documentElement.setAttribute('data-style','${s.id}');applyStyle('${s.id}')">预览此风格</button>
      </div>
    </div>`
  }).join('')

  // Preview button inside each card
  grid.addEventListener('click', (e) => {
    const btn = (e.target as HTMLElement).closest('[data-preview]') as HTMLElement | null
    if (btn) {
      applyStyle(btn.dataset.preview!)
      // Scroll to top to see full effect
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  })
}

function getStyleDescription(id: string): string {
  const descriptions: Record<string, string> = {
    swiss: '无衬线字体、严格网格、红色强调、无阴影、粗边框。源于 1950 年代瑞士国际主义风格。',
    neubrutalism: '粗边框 3px+、黑色投影 8px、Arial Black 字体、高对比。现代数字艺术的叛逆表达。',
    webbrutalism: 'Times New Roman 衬线体、蓝色链接、原始感、无装饰。回归早期 Web 的质朴美学。',
    skeuomorphism: '内阴影、纹理渐变、皮革质感、拟物按钮。模拟真实世界的物理质感。',
    neumorphism: '外阴影+内阴影组合、同色系、软 UI、无边框。极简的柔软立体感。',
    glassmorphism: 'backdrop-filter blur、半透明背景、渐变背景层、发光边框。毛玻璃效果。',
    flat20: '柔和阴影、圆角 6px、简洁图标、干净排版。扁平化设计的现代演进。',
    material: '海拔阴影系统、Z 轴层次、涟漪动效。Google Material Design 规范。',
    minimalism: '最大留白、细边框 1px、极淡色调、内容优先。少即是多的极致追求。',
    maximalism: '重复图案背景、双边框、丰富色彩、装饰性元素。更多才是更多。',
    vaporwave: '霓虹紫/粉/蓝配色、网格线背景、发光文字。80/90 年代复古未来主义。',
    y2k: '高光渐变、镀铬效果、圆角胶囊、天蓝/银配色。千禧年的科技乐观主义。',
    darkmode: '深色背景、浅色文字、低饱和强调色、减少蓝光。护眼暗色主题。',
    bauhaus: '红/黄/蓝三原色、几何形状、无装饰、粗体无衬线。形式追随功能。',
    memphis: '波点/之字形背景、鲜艳色彩、随机几何装饰。1980 年代意大利反叛设计。',
    claymorphism: '3D 粘土质感、圆润大圆角、柔和投影、暖色调。柔软可爱的立体触感。',
    organic: '圆角胶囊、自然绿/棕色调、柔和曲线、生态感。大自然的有机形态。',
    acid: '荧绿/紫配色、黑色背景、故障效果、高饱和对比。迷幻的酸性视觉冲击。',
    cyberpunk: '霓虹边框、故障文字动效、扫描线、深色背景+高亮色。反乌托邦未来世界。',
    pixel: '像素边框、块状阴影、8-bit 字体、阶梯边缘。复古游戏机美学。',
  }
  return descriptions[id] || '自定义设计风格'
}

/* ===== Toast ===== */
function showToast(msg: string): void {
  const el = document.getElementById('toast')!
  el.textContent = msg
  el.style.opacity = '1'
  el.style.transform = 'translateY(0)'
  setTimeout(() => {
    el.style.opacity = '0'
    el.style.transform = 'translateY(20px)'
  }, 2000)
}

/* ===== 初始化 ===== */
function init(): void {
  initPalettePicker()
  initStylePicker()
  buildShowcaseCards()
  showToast('已加载 20 种设计风格')
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init)
} else {
  init()
}

// 暴露给全局供 onclick 使用
;(window as any).applyStyle = applyStyle