import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const source = readFileSync(new URL('./AppLayout.vue', import.meta.url), 'utf8')

test('AppLayout exposes a mobile menu trigger and dismissible drawer', () => {
  assert.match(source, /class="mobile-menu-button"/)
  assert.match(source, /aria-label="打开移动端导航"/)
  assert.match(source, /class="mobile-nav-layer"/)
  assert.match(source, /class="mobile-nav-panel"/)
  assert.match(source, /class="mobile-nav-close"/)
  assert.match(source, /@click="closeMobileMenu"/)
  assert.match(source, /watch\(\(\) => route\.fullPath, closeMobileMenu\)/)
})
