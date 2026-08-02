export function createMobileNavState(open = false) {
  return { open: Boolean(open) }
}

export function toggleMobileNav(state) {
  return { open: !state.open }
}

export function closeMobileNav() {
  return { open: false }
}
