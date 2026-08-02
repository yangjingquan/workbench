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

test('mobile styles provide 40px touch targets and reduced-motion drawer behavior', () => {
  assert.match(styles, /\.icon-button,[\s\S]*?\.mobile-menu-button,[\s\S]*?\.mobile-nav-close,[\s\S]*?\.top-actions\s+\.el-dropdown\s*\{[^}]*min-width:\s*40px[^}]*min-height:\s*40px/)
  assert.match(styles, /\.avatar-wrap\s*\{[^}]*min-width:\s*40px[^}]*min-height:\s*40px/)
  assert.match(styles, /\.el-button\s*\{[^}]*min-height:\s*40px/)
  assert.match(styles, /\.el-input__wrapper,[\s\S]*?\.el-select__wrapper,[\s\S]*?\.el-date-editor[^}]*\{[^}]*min-height:\s*40px/)
  assert.match(styles, /\.el-radio-button__inner,[\s\S]*?\.el-segmented,[\s\S]*?\.el-switch,[\s\S]*?\.memo-item\s*\{[^}]*min-height:\s*40px/)
  assert.match(styles, /@media \(prefers-reduced-motion:\s*reduce\)[\s\S]*?\.mobile-nav-enter-active,[\s\S]*?\.mobile-nav-leave-active/)
})

test('mobile content overrides remove list-page overflow and center controls', () => {
  assert.match(styles, /\.mobile-nav-panel\s*\{[^}]*width:\s*min\(300px,\s*50vw\)/)
  assert.match(styles, /\.desktop-table\s*\{[^}]*display:\s*none/)
  assert.match(styles, /\.mobile-card-list\s*\{[^}]*display:\s*flex/)
  assert.match(styles, /\.link-grid\s*\{[^}]*grid-template-columns:\s*1fr/)
  assert.match(styles, /\.el-radio-button__inner\s*\{[^}]*display:\s*inline-flex[^}]*align-items:\s*center[^}]*justify-content:\s*center/)
})

test('mobile dialogs are centered and accounting tables switch to cards', () => {
  assert.match(styles, /\.el-overlay-dialog\s*\{[^}]*display:\s*flex[^}]*align-items:\s*center[^}]*justify-content:\s*center/)
  assert.match(styles, /\.el-dialog\s*\{[^}]*max-height:\s*calc\(100vh - 32px\)/)
  assert.match(styles, /\.desktop-accounting-table\s*\{[^}]*display:\s*none/)
  assert.match(styles, /\.mobile-accounting-list\s*\{[^}]*display:\s*flex/)
  assert.match(styles, /\.account-category-panel,[\s\S]*?\.account-records-panel\s*\{[^}]*overflow-x:\s*hidden/)
})
