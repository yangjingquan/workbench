import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const read = path => readFileSync(new URL(path, import.meta.url), 'utf8')
const dashboard = read('../pages/Dashboard.vue')
const records = read('../pages/Records.vue')
const memos = read('../pages/Memos.vue')
const accounting = read('../pages/Accounting.vue')
const todos = read('../pages/Todos.vue')
const layout = read('./AppLayout.vue')
const api = read('../api/http.js')

test('dashboard exposes live focus tasks and elapsed time', () => {
  assert.match(dashboard, /focus_tasks/)
  assert.match(dashboard, /formatDuration\(task\.elapsed_seconds\)/)
  assert.match(dashboard, /parseTimerTimestamp/)
  assert.match(dashboard, /focusTimer = window\.setInterval/)
  assert.match(dashboard, /}, 250\)/)
})

test('work records display hours as hours and minutes', () => {
  assert.match(records, /formatHours\(scope\.row\.hours\)/)
  assert.match(records, /formatHours\(row\.hours\)/)
  assert.match(records, /工时：\$\{formatHours\(x\.hours\)\}/)
})

test('memos and accounting expose edit and delete actions', () => {
  assert.match(memos, /startEdit\(selectedMemo\)/)
  assert.match(memos, /removeMemo\(selectedMemo\)/)
  assert.match(accounting, /startEditEntry\(scope\.row\)/)
  assert.match(accounting, /updateAccountEntry/)
  assert.match(accounting, /removeEntry\(item\.id\)/)
})

test('todo subtasks expose view, completion, edit, and delete flows', () => {
  assert.match(todos, /v-for="subtask in task\.subtasks"/)
  assert.match(todos, /toggleSubtask\(task, subtask/)
  assert.match(todos, /editSubtask\(task, subtask\)/)
  assert.match(todos, /removeSubtask\(task, subtask\)/)
  assert.match(api, /updateSubtask:/)
  assert.match(api, /deleteSubtask:/)
})

test('global search results navigate to their resource pages', () => {
  assert.match(layout, /@click="goToSearchResult\(key, item\)"/)
  assert.match(layout, /records: '\/records'/)
  assert.match(layout, /todos: '\/todos'/)
  assert.match(layout, /memos: '\/memos'/)
})
