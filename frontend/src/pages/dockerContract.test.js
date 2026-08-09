import assert from 'node:assert/strict'
import test from 'node:test'
import { readFileSync } from 'node:fs'

test('router and AppLayout expose Docker management', () => {
  const routerSource = readFileSync(new URL('../router/index.js', import.meta.url), 'utf8')
  const layoutSource = readFileSync(new URL('../layouts/AppLayout.vue', import.meta.url), 'utf8')
  assert.match(routerSource, /path: 'docker'/)
  assert.match(routerSource, /Docker\.vue/)
  assert.match(layoutSource, /to="\/docker"/)
  assert.match(layoutSource, /Docker 管理/)
})

test('Docker API surface includes lifecycle and log methods', () => {
  const source = readFileSync(new URL('../api/http.js', import.meta.url), 'utf8')
  assert.match(source, /dockerOverview/)
  assert.match(source, /dockerAction/)
  assert.match(source, /dockerServiceAction/)
  assert.match(source, /dockerAuditLogs/)
  assert.match(source, /compactParams/)
  assert.match(source, /dockerLogs:.*compactParams\(params\)/)
})

test('Docker page exposes status, logs, actions, and protection guardrails', () => {
  const source = readFileSync(new URL('./Docker.vue', import.meta.url), 'utf8')
  assert.match(source, /Docker 管理/)
  assert.match(source, /dockerOverview/)
  assert.match(source, /实时跟随/)
  assert.match(source, /confirm_name/)
  assert.match(source, /streamDockerLogs/)
  assert.match(source, /受保护容器不可删除/)
})
