import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const pages = {
  records: readFileSync(new URL('../pages/Records.vue', import.meta.url), 'utf8'),
  plans: readFileSync(new URL('../pages/Plans.vue', import.meta.url), 'utf8'),
  reminders: readFileSync(new URL('../pages/Reminders.vue', import.meta.url), 'utf8')
}

test('mobile list pages expose desktop and mobile presentation hooks', () => {
  for (const source of Object.values(pages)) {
    assert.match(source, /class="desktop-table[^\"]*"/)
    assert.match(source, /class="mobile-card-list"/)
  }
})

test('mobile cards preserve each page primary fields and actions', () => {
  assert.match(pages.records, /mobile-record-card/)
  assert.match(pages.records, /openEdit\(row\)/)
  assert.match(pages.records, /remove\(row\.id\)/)
  assert.match(pages.plans, /mobile-plan-card/)
  assert.match(pages.plans, /edit\(row\)/)
  assert.match(pages.plans, /remove\(row\.id\)/)
  assert.match(pages.reminders, /mobile-reminder-card/)
  assert.match(pages.reminders, /action\(row\.id, 'delete'\)/)
})
