import assert from 'node:assert/strict'
import test from 'node:test'
import { closeMobileNav, createMobileNavState, toggleMobileNav } from './mobileNav.js'

test('mobile navigation starts closed and toggles without mutating the source state', () => {
  const closed = createMobileNavState()
  const opened = toggleMobileNav(closed)

  assert.deepEqual(closed, { open: false })
  assert.deepEqual(opened, { open: true })
  assert.deepEqual(toggleMobileNav(opened), { open: false })
})

test('mobile navigation can always be closed', () => {
  assert.deepEqual(closeMobileNav(), { open: false })
})
