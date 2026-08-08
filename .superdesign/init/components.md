# Frontend component inventory

## Stack

- Framework: Vue 3 with `<script setup>`
- Build: Vite
- Component library: Element Plus and `@element-plus/icons-vue`
- State: Pinia
- Styling: shared vanilla CSS in `frontend/src/styles.css`, CSS variables, Element Plus overrides

## `frontend/src/components/StatCard.vue`

Reusable metric card used by the overview dashboard. Props: `label`, `value`, `foot`, `trend`, `icon`, `tone`.

```vue
<template><div class="stat-card"><div class="stat-label">{{ label }}<span :class="['stat-icon', tone]">{{ icon }}</span></div><div class="stat-value">{{ value }}</div><div class="stat-foot"><span :class="trend > 0 ? 'up' : 'muted'">{{ trend ? `${trend > 0 ? '+' : ''}${trend}%` : '—' }}</span><span>{{ foot }}</span></div></div></template>
<script setup>defineProps({ label: String, value: [String, Number], foot: String, trend: Number, icon: String, tone: String })</script>
```

## `frontend/src/components/StatusTag.vue`

Small status/priority pill. Props: `text`, `label`, `tone`.

```vue
<template><span :class="['status-tag', tone]">{{ label || text }}</span></template>
<script setup>defineProps({ text: String, label: String, tone: { type: String, default: '' } })</script>
```

## `frontend/src/components/BaseDialog.vue`

Thin Element Plus dialog wrapper with a named footer slot.

```vue
<template><el-dialog v-bind="$attrs" :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)"><slot/><template #footer><slot name="footer"/></template></el-dialog></template>
<script setup>defineProps({ modelValue: Boolean }); defineEmits(['update:modelValue'])</script>
```

## `frontend/src/components/BaseSelect.vue`

Thin Element Plus select wrapper. Prop: `options` array of strings or `{ label, value }` objects.

```vue
<template><el-select v-bind="$attrs"><el-option v-for="item in options" :key="item.value ?? item" :label="item.label ?? item" :value="item.value ?? item"/></el-select></template>
<script setup>defineProps({ options: { type: Array, default: () => [] } })</script>
```

## `frontend/src/components/ReminderPoll.vue`

Shared background reminder poller; it renders no visible layout but can trigger Element Plus notifications.

```vue
<script setup>
import { onMounted, onUnmounted } from 'vue'
import { ElNotification } from 'element-plus'
import { api } from '../api/http'
let timer; const notified = new Set()
function notify(item) { const occurrenceKey = `${item.id}:${item.next_trigger_at || item.remind_at || ''}`; if (notified.has(occurrenceKey)) return; notified.add(occurrenceKey); ElNotification({ title: item.title, message: item.content || '有一条提醒到期了', type: 'warning', duration: 0, onClose: async () => { try { await api.reminderAction(item.id, 'ack'); window.location.reload() } finally { notified.delete(occurrenceKey) } } }); if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'granted') new Notification(item.title, { body: item.content || '有一条提醒到期了' }) }
async function checkReminders() { try { const res = await api.reminders({ due: true }); (res.data || []).forEach(notify) } catch (error) { console.warn('提醒检查失败', error) } }
function onVisible() { if (document.visibilityState === 'visible') checkReminders() }
onMounted(() => { checkReminders(); timer = setInterval(checkReminders, 10000); window.addEventListener('focus', checkReminders); document.addEventListener('visibilitychange', onVisible) })
onUnmounted(() => { clearInterval(timer); window.removeEventListener('focus', checkReminders); document.removeEventListener('visibilitychange', onVisible) })
</script>
```
