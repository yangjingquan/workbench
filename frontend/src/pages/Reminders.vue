<template>
  <div class="page-heading">
    <div><h1>事件提醒</h1><p>支持单次、每日、每周多天和每月多日周期提醒；通知右上角 X 表示已收到本周期提醒。</p></div>
    <div class="page-actions"><el-button @click="enableNotifications">开启桌面通知</el-button><el-button type="primary" @click="openCreate">+ 新建提醒</el-button></div>
  </div>

  <div class="desktop-table table-card">
    <el-table :data="rows" stripe>
      <el-table-column prop="title" label="提醒事项" min-width="190" />
      <el-table-column label="规则" min-width="280"><template #default="scope"><b>{{ scheduleText(scope.row) }}</b><div v-if="scope.row.content" class="muted-text"><a v-if="isUrl(scope.row.content)" class="reminder-link" :href="normalizeUrl(scope.row.content)" target="_blank" rel="noopener noreferrer" @click.stop>{{ scope.row.content }}</a><span v-else>{{ scope.row.content }}</span></div><div v-else class="muted-text">无备注</div></template></el-table-column>
      <el-table-column label="下一次执行" width="185"><template #default="scope">{{ scope.row.status === 'active' ? (scope.row.next_trigger_at || '已完成') : '—' }}</template></el-table-column>
      <el-table-column label="状态" width="100"><template #default="scope"><span :class="['status-tag', scope.row.status === 'closed' ? 'muted-status' : '']">{{ statusLabel(scope.row) }}</span></template></el-table-column>
      <el-table-column label="操作" width="245" fixed="right"><template #default="scope"><el-button link type="primary" @click="openEdit(scope.row)">编辑</el-button><el-button v-if="scope.row.status === 'active'" link type="warning" @click="action(scope.row.id, 'close')">关闭</el-button><el-button v-else link type="success" @click="action(scope.row.id, 'activate')">启用</el-button><el-button link type="danger" @click="action(scope.row.id, 'delete')">删除</el-button></template></el-table-column>
    </el-table>
    <el-empty v-if="!rows.length" description="还没有事件提醒" />
  </div>

  <div class="mobile-card-list">
    <article v-for="row in rows" :key="row.id" class="mobile-reminder-card mobile-content-card">
      <div class="mobile-card-header"><h3>{{ row.title }}</h3><span :class="['status-tag', row.status === 'closed' ? 'muted-status' : '']">{{ statusLabel(row) }}</span></div>
      <b class="mobile-card-rule">{{ scheduleText(row) }}</b>
      <p v-if="row.content" class="mobile-card-description"><a v-if="isUrl(row.content)" class="reminder-link" :href="normalizeUrl(row.content)" target="_blank" rel="noopener noreferrer">{{ row.content }}</a><span v-else>{{ row.content }}</span></p>
      <div class="mobile-card-actions"><el-button link type="primary" @click="openEdit(row)">编辑</el-button><el-button v-if="row.status === 'active'" link type="warning" @click="action(row.id, 'close')">关闭</el-button><el-button v-else link type="success" @click="action(row.id, 'activate')">启用</el-button><el-button link type="danger" @click="action(row.id, 'delete')">删除</el-button></div>
    </article>
    <el-empty v-if="!rows.length" description="还没有事件提醒" />
  </div>

  <el-dialog v-model="dialog" :title="editing ? '编辑事件提醒' : '新建事件提醒'" width="620px">
    <el-form :model="form" label-width="82px">
      <el-form-item label="提醒事项"><el-input v-model="form.title" placeholder="例如：每日复盘、周会、月度账单" /></el-form-item>
      <el-form-item label="备注"><el-input v-model="form.content" placeholder="可选" /></el-form-item>
      <el-form-item label="执行周期"><el-radio-group v-model="form.schedule_type"><el-radio-button label="once">固定日期</el-radio-button><el-radio-button label="daily">每天</el-radio-button><el-radio-button label="weekly">每周</el-radio-button><el-radio-button label="monthly">每月</el-radio-button></el-radio-group></el-form-item>
      <el-form-item v-if="form.schedule_type === 'once'" label="执行时间"><el-date-picker v-model="form.remind_at" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width:100%" /></el-form-item>
      <el-form-item v-else label="执行时间"><el-time-picker v-model="form.time_of_day" value-format="HH:mm:ss" format="HH:mm" style="width:100%" /></el-form-item>
      <el-form-item v-if="form.schedule_type === 'daily' || form.schedule_type === 'weekly'" :label="form.schedule_type === 'daily' ? '指定星期' : '每周日期'"><el-checkbox-group v-model="form.weekdays" class="weekday-options"><el-checkbox v-for="day in weekdayOptions" :key="day.value" :label="day.value" border>{{ day.label }}</el-checkbox></el-checkbox-group><div v-if="form.schedule_type === 'daily'" class="muted-text">不选择表示每天；选择后仅在指定星期提醒。</div></el-form-item>
      <el-form-item v-if="form.schedule_type === 'monthly'" label="每月日期"><el-select v-model="form.month_days" multiple filterable collapse-tags placeholder="选择日期，可多选" style="width:100%"><el-option v-for="day in 31" :key="day" :label="`${day} 日`" :value="day" /></el-select></el-form-item>
      <div class="muted-text schedule-help">示例：每天 00:05；每周选择周三、周五并设为 13:00；每月选择 1、3 日并设为 14:09。</div>
    </el-form>
    <template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" @click="save">保存提醒</el-button></template>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/http'

const rows = ref([])
const dialog = ref(false)
const editing = ref(null)
const weekdayOptions = [{ value: 1, label: '周一' }, { value: 2, label: '周二' }, { value: 3, label: '周三' }, { value: 4, label: '周四' }, { value: 5, label: '周五' }, { value: 6, label: '周六' }, { value: 7, label: '周日' }]
const form = reactive({ title: '', content: '', schedule_type: 'once', remind_at: '', time_of_day: '00:05:00', weekdays: [], month_days: [] })

async function load() { rows.value = (await api.reminders()).data }
function resetForm() { Object.assign(form, { title: '', content: '', schedule_type: 'once', remind_at: '', time_of_day: '00:05:00', weekdays: [], month_days: [] }) }
function openCreate() { editing.value = null; resetForm(); dialog.value = true }
function openEdit(row) { editing.value = row.id; Object.assign(form, { title: row.title, content: row.content || '', schedule_type: row.schedule_type || 'once', remind_at: row.schedule_type === 'once' ? row.remind_at?.replace('T', ' ') : '', time_of_day: row.time_of_day || '00:05:00', weekdays: row.weekdays || [], month_days: row.month_days || [] }); dialog.value = true }
function statusLabel(row) { if (row.status === 'active') return '生效中'; if (row.schedule_type === 'once') return '已失效'; return '已关闭' }
function scheduleText(row) { const time = (row.time_of_day || '').slice(0, 5); if (row.schedule_type === 'daily') return row.weekdays?.length ? `每周 ${(row.weekdays || []).map(x => weekdayOptions.find(day => day.value === x)?.label).join('、')} ${time}` : `每天 ${time}`; if (row.schedule_type === 'weekly') return `每周 ${(row.weekdays || []).map(x => weekdayOptions.find(day => day.value === x)?.label).join('、')} ${time}`; if (row.schedule_type === 'monthly') return `每月 ${(row.month_days || []).join('、')} 日 ${time}`; return `固定 ${row.remind_at?.replace('T', ' ') || '未设置'}` }
function isUrl(value) { return /^(https?:\/\/|www\.)[^\s]+$/i.test(value.trim()) }
function normalizeUrl(value) { const url = value.trim(); return /^https?:\/\//i.test(url) ? url : `https://${url}` }
async function save() { if (!form.title) return ElMessage.warning('请填写提醒事项'); if (form.schedule_type === 'once' && !form.remind_at) return ElMessage.warning('请选择固定执行时间'); if (form.schedule_type === 'weekly' && !form.weekdays.length) return ElMessage.warning('至少选择一个星期'); if (form.schedule_type === 'monthly' && !form.month_days.length) return ElMessage.warning('至少选择一个月内日期'); const payload = { ...form, remind_at: form.schedule_type === 'once' ? form.remind_at : null }; if (editing.value) await api.updateReminder(editing.value, payload); else await api.reminder(payload); dialog.value = false; ElMessage.success('提醒已保存'); await load() }
async function action(id, type) { await api.reminderAction(id, type); ElMessage.success(type === 'delete' ? '提醒已删除' : type === 'activate' ? '提醒已启用' : '提醒状态已更新'); await load() }
async function enableNotifications() { if (!('Notification' in window)) return ElMessage.warning('当前浏览器不支持桌面通知'); const permission = await Notification.requestPermission(); ElMessage[permission === 'granted' ? 'success' : 'warning'](permission === 'granted' ? '桌面通知已开启' : '浏览器未允许桌面通知；页面内提醒仍会正常显示') }
onMounted(load)
</script>
