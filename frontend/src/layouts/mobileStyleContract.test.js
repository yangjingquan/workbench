import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const styles = readFileSync(new URL('../styles.css', import.meta.url), 'utf8')

test('mobile styles provide navigation, table, dialog, and stacked layout rules', () => {
  assert.match(styles, /\.mobile-menu-button\s*\{[^}]*display:\s*none/)
  assert.match(styles, /\.mobile-nav-layer\s*\{[^}]*display:\s*none/)
  assert.match(styles, /@media \(max-width:\s*760px\)/)
  assert.match(styles, /\.sidebar\s*\{\s*display:\s*none/)
  assert.match(styles, /\.mobile-menu-button\s*\{[^}]*display:\s*grid/)
  assert.match(styles, /\.table-card\s*\{[^}]*overflow-x:\s*auto/)
  assert.match(styles, /\.page-heading\s*\{[^}]*flex-direction:\s*column/)
  assert.match(styles, /\.setting-row\s*\{[^}]*flex-direction:\s*column/)
  assert.match(styles, /\.el-dialog\s*\{[^}]*width:\s*calc\(100vw - 32px\)/)
})
