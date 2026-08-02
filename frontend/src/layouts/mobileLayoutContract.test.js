import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const source = readFileSync(new URL('./AppLayout.vue', import.meta.url), 'utf8')

test('AppLayout exposes a mobile menu trigger and dismissible drawer', () => {
  assert.match(source, /class="mobile-menu-button"/)
  assert.match(source, /aria-label="打开移动端导航"/)
  assert.match(source, /:aria-expanded="mobileNav\.open"/)
  assert.match(source, /aria-controls="mobile-nav-panel"/)
  assert.match(source, /class="mobile-nav-layer"/)
  assert.match(source, /id="mobile-nav-panel"/)
  assert.match(source, /role="dialog"/)
  assert.match(source, /aria-modal="true"/)
  assert.match(source, /@keydown="handleMobileNavKeydown"/)
  assert.match(source, /class="mobile-nav-close"/)
  assert.match(source, /@click="closeMobileMenu"/)
  assert.match(source, /watch\(\(\) => route\.fullPath, closeMobileMenu\)/)
})

test('AppLayout manages focus for the keyboard-modal mobile drawer', () => {
  assert.match(source, /ref="mobileMenuTrigger"/)
  assert.match(source, /ref="mobileNavClose"/)
  assert.match(source, /ref="mobileNavPanel"/)
  assert.match(source, /import \{[^}]*nextTick[^}]*\} from 'vue'/)
  assert.match(source, /function getMobileNavFocusableElements\(/)
  assert.match(source, /async function focusMobileNav\(/)
  assert.match(source, /function restoreMobileMenuTriggerFocus\(/)
  assert.match(source, /function handleMobileNavKeydown\(/)
  assert.match(source, /mobileNavClose\.value\?\.focus\(\)/)
  assert.match(source, /mobileMenuTrigger\.value\?\.focus\(\)/)
})
