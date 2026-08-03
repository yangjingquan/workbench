import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const pages = {
  records: readFileSync(new URL('../pages/Records.vue', import.meta.url), 'utf8'),
  plans: readFileSync(new URL('../pages/Plans.vue', import.meta.url), 'utf8'),
  reminders: readFileSync(new URL('../pages/Reminders.vue', import.meta.url), 'utf8'),
  todos: readFileSync(new URL('../pages/Todos.vue', import.meta.url), 'utf8')
}

const reminderTime = readFileSync(new URL('../utils/reminderTime.js', import.meta.url), 'utf8')

test('mobile list pages expose desktop and mobile presentation hooks', () => {
  for (const source of Object.values({ records: pages.records, plans: pages.plans, reminders: pages.reminders })) {
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

test('Todo mobile interactions support touch movement and archive recovery', () => {
  assert.match(pages.todos, /class="todo-drag-handle"[^>]*@pointerdown="startPointerDrag\(task, \$event\)"/)
  assert.match(pages.todos, /@pointerup="finishPointerDrag"/)
  assert.match(pages.todos, /todo-mobile-move/)
  assert.match(pages.todos, /archiveOrRestore\(task\)/)
  assert.match(pages.todos, /restoreTodo/)
})

test('reminder times carry a browser timezone and render UTC instants locally', () => {
  assert.match(pages.reminders, /timezone: browserTimezone\(\)/)
  assert.match(pages.reminders, /remind_at: form\.schedule_type === 'once' \? toUtcIso\(form\.remind_at\) : null/)
  assert.match(pages.reminders, /formatLocalDateTime\(row\.remind_at\)/)
  assert.match(reminderTime, /toISOString\(\)/)
  assert.match(reminderTime, /resolvedOptions\(\)\.timeZone/)
})

test('mobile reminder dialog wraps schedule controls and centers picker poppers', () => {
  assert.match(pages.reminders, /popper-class="reminder-picker-popper"/)
  assert.match(readFileSync(new URL('../styles.css', import.meta.url), 'utf8'), /\.reminder-picker-popper[\s\S]*left: 50% !important/)
})
