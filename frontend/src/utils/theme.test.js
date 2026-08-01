import assert from 'node:assert/strict'
import test from 'node:test'
import { normalizeAccentTheme, nextAccentTheme } from './theme.js'

test('normalizeAccentTheme falls back to indigo for missing or unsupported values', () => {
  assert.equal(normalizeAccentTheme(null), 'indigo')
  assert.equal(normalizeAccentTheme('unknown'), 'indigo')
  assert.equal(normalizeAccentTheme('ocean'), 'ocean')
})

test('nextAccentTheme switches between the two supported themes', () => {
  assert.equal(nextAccentTheme('indigo'), 'ocean')
  assert.equal(nextAccentTheme('ocean'), 'indigo')
  assert.equal(nextAccentTheme('unknown'), 'ocean')
})
