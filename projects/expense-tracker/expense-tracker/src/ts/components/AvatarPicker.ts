import { AVATAR_LIBRARY } from '../constants'
import { escapeHtml } from '../utils'

const AVATAR_STORE_KEY = 'swiss_expenses_avatar'

export function renderAvatarPicker(): void {
  const avatarId = (() => {
    try { return localStorage.getItem(AVATAR_STORE_KEY) || AVATAR_LIBRARY[0].id }
    catch { return AVATAR_LIBRARY[0].id }
  })()
  const avatar = AVATAR_LIBRARY.find(a => a.id === avatarId) || AVATAR_LIBRARY[0]

  const preview = document.getElementById('avatarPreview')
  const profileName = document.getElementById('profileName')
  const grid = document.getElementById('avatarGrid')
  const trigger = document.getElementById('avatarTrigger')
  const panel = document.getElementById('avatarPanel')
  const closeBtn = document.getElementById('avatarClose')

  if (preview) preview.innerHTML = avatarMarkup(avatar)
  if (profileName) profileName.textContent = `${avatar.name}的账本`
  try { localStorage.setItem(AVATAR_STORE_KEY, avatar.id) } catch { /* ignore */ }

  if (grid) {
    grid.innerHTML = AVATAR_LIBRARY.map(a =>
      `<button class="avatar-option${a.id === avatar.id ? ' selected' : ''}" type="button" role="option" aria-label="选择${escapeHtml(a.name)}头像" aria-selected="${a.id === avatar.id}" data-avatar-id="${a.id}">${avatarMarkup(a)}</button>`
    ).join('')
  }

  // Events
  trigger?.addEventListener('click', () => {
    if (panel) panel.hidden = !panel.hidden
    trigger.setAttribute('aria-expanded', String(!panel?.hidden))
  })
  closeBtn?.addEventListener('click', () => {
    if (panel) panel.hidden = true
    trigger?.setAttribute('aria-expanded', 'false')
  })
  grid?.addEventListener('click', (e) => {
    const option = (e.target as HTMLElement).closest('[data-avatar-id]') as HTMLElement | null
    if (option) selectAvatar(option.dataset.avatarId!)
  })
  document.addEventListener('click', (e) => {
    if (panel && !panel.hidden && !(e.target as HTMLElement).closest('.profile-bar')) {
      panel.hidden = true
      trigger?.setAttribute('aria-expanded', 'false')
    }
  })
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && panel && !panel.hidden) {
      panel.hidden = true
      trigger?.setAttribute('aria-expanded', 'false')
    }
  })
}

function avatarMarkup(avatar: { id: string; name: string; fallback: string }): string {
  return `<span class="avatar-image" role="img" aria-label="${escapeHtml(avatar.name)}头像">${avatar.fallback}</span>`
}

function selectAvatar(id: string): void {
  const avatar = AVATAR_LIBRARY.find(a => a.id === id)
  if (!avatar) return
  try { localStorage.setItem(AVATAR_STORE_KEY, id) } catch { /* ignore */ }
  const preview = document.getElementById('avatarPreview')
  const profileName = document.getElementById('profileName')
  if (preview) preview.innerHTML = avatarMarkup(avatar)
  if (profileName) profileName.textContent = `${avatar.name}的账本`
  const panel = document.getElementById('avatarPanel')
  if (panel) panel.hidden = true
  document.getElementById('avatarTrigger')?.setAttribute('aria-expanded', 'false')
  // Update grid selection
  document.querySelectorAll('.avatar-option').forEach(el => {
    el.classList.toggle('selected', (el as HTMLElement).dataset.avatarId === id)
  })
}