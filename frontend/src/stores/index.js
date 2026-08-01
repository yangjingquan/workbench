import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/http'
import { nextAccentTheme, normalizeAccentTheme } from '../utils/theme'

export const useAppStore = defineStore('app', () => {
  const token = ref(localStorage.getItem('workbench_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('workbench_user') || 'null'))
  const collapsed = ref(localStorage.getItem('workbench_collapsed') === 'true')
  const theme = ref(localStorage.getItem('workbench_theme') || 'light')
  const accentTheme = ref(normalizeAccentTheme(localStorage.getItem('workbench_accent_theme')))
  const loading = ref(false)
  const isLoggedIn = computed(() => Boolean(token.value))
  function setSession(payload) { token.value = payload.token; user.value = payload.user; localStorage.setItem('workbench_token', payload.token); localStorage.setItem('workbench_user', JSON.stringify(payload.user)) }
  function clearSession() { token.value = ''; user.value = null; localStorage.removeItem('workbench_token'); localStorage.removeItem('workbench_user') }
  async function toggleTheme() { theme.value = theme.value === 'light' ? 'dark' : 'light'; localStorage.setItem('workbench_theme', theme.value); document.documentElement.classList.toggle('dark', theme.value === 'dark'); if (isLoggedIn.value) await api.saveConfig({ theme: theme.value }).catch(() => {}) }
  function applyAccentTheme(value) { const normalized = normalizeAccentTheme(value); accentTheme.value = normalized; document.documentElement.dataset.accentTheme = normalized; return normalized }
  function setAccentTheme(value) { const normalized = applyAccentTheme(value); localStorage.setItem('workbench_accent_theme', normalized); return normalized }
  function toggleAccentTheme() { return setAccentTheme(nextAccentTheme(accentTheme.value)) }
  function initTheme() { document.documentElement.classList.toggle('dark', theme.value === 'dark'); applyAccentTheme(accentTheme.value) }
  async function saveCollapsed(value) { collapsed.value = value; localStorage.setItem('workbench_collapsed', String(value)); if (isLoggedIn.value) await api.saveConfig({ sidebar_collapsed: value }).catch(() => {}) }
  async function logoutAll() { await api.logoutAll(); clearSession() }
  return { token, user, collapsed, theme, accentTheme, loading, isLoggedIn, setSession, clearSession, toggleTheme, setAccentTheme, toggleAccentTheme, initTheme, saveCollapsed, logoutAll }
})
