export const ACCENT_THEMES = ['indigo', 'ocean']

export function normalizeAccentTheme(value) {
  return ACCENT_THEMES.includes(value) ? value : 'indigo'
}

export function nextAccentTheme(value) {
  return normalizeAccentTheme(value) === 'indigo' ? 'ocean' : 'indigo'
}
