import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const source = readFileSync(new URL('../pages/Accounting.vue', import.meta.url), 'utf8')

test('accounting exposes desktop table wrappers and mobile card lists', () => {
  assert.equal((source.match(/desktop-accounting-table/g) || []).length, 2)
  assert.equal((source.match(/mobile-accounting-list/g) || []).length, 2)
  assert.match(source, /<div class="accounting-lower-grid">[\s\S]*account-category-panel[\s\S]*account-records-panel[\s\S]*<\/div>/)
  assert.match(source, /mobile-category-card/)
  assert.match(source, /mobile-entry-card/)
})

test('mobile accounting cards retain category data and entry deletion', () => {
  assert.match(source, /summary\.by_category/)
  assert.match(source, /formatMoney\(item\.total\)/)
  assert.match(source, /entries/)
  assert.match(source, /removeEntry\(item\.id\)/)
})
