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
