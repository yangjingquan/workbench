<template>
  <div class="todo-page">
    <div class="todo-mobile-heading">
      <div><h1>Todo看板</h1><p>高效管理，清晰规划。</p></div>
      <button type="button" class="todo-archive-button" @click="toggleArchiveView"><el-icon><FolderOpened /></el-icon><span>{{ showArchive ? '隐藏归档' : '查看归档' }}</span></button>
    </div>

    <div class="todo-toolbar">
      <div class="todo-toolbar-main">
        <el-input class="todo-search" v-model="keyword" clearable placeholder="搜索任务、备注" @keyup.enter="load" />
        <div class="todo-board-help"><el-icon><InfoFilled /></el-icon><span>拖拽卡片即可快速调整状态</span></div>
        <el-checkbox class="todo-archive-check" v-model="showArchive" @change="load">查看归档任务</el-checkbox>
      </div>
      <div class="todo-toolbar-actions">
        <el-button class="todo-batch-button" @click="batch('complete')" :disabled="!selected.length">批量完成</el-button>
        <el-button type="primary" @click="openCreate"><span class="todo-plus">+</span> 新建任务</el-button>
      </div>
    </div>

    <div class="todo-mobile-tabs" role="tablist" aria-label="Todo 状态定位">
      <button v-for="col in columns" :key="col.key" type="button" :class="{ active: mobileColumn === col.key }" :aria-selected="mobileColumn === col.key" @click="focusColumn(col.key)"><span>{{ col.label }}</span><b>{{ grouped[col.key].length }}</b></button>
    </div>

    <div class="todo-board">
      <div v-for="col in columns" :key="col.key" :ref="element => setColumnRef(col.key, element)" class="todo-column" :data-status="col.key" @dragover.prevent @drop="drop(col.key)">
        <div class="column-head"><div class="column-label"><span class="column-dot" aria-hidden="true" /><b>{{ col.label }}</b><span class="column-count">{{ grouped[col.key].length }}</span></div></div>
      <div
        v-for="task in grouped[col.key]"
        :key="task.id"
        class="todo-card"
        :class="{ overdue: isOverdue(task), 'is-dragging': pointerDragging && dragging?.id === task.id }"
        draggable="true"
        @dragstart="dragging = task"
        @dragend="dragging = null"
      >
        <div class="todo-card-top">
          <div class="todo-title"><input type="checkbox" :checked="selected.includes(task.id)" @change="toggleSelect(task.id)" /><span>{{ task.title }}</span></div>
          <div class="todo-card-tools">
            <button type="button" class="todo-timer-button" :class="{ active: task.timer_started_at }" :aria-label="task.timer_started_at ? '暂停计时' : '开始计时'" @click.stop="toggleTimer(task)">
              <el-icon><VideoPause v-if="task.timer_started_at" /><VideoPlay v-else /></el-icon><span>{{ task.timer_started_at ? '暂停' : '计时' }}</span>
            </button>
            <button type="button" class="todo-drag-handle" aria-label="拖动任务" @pointerdown="startPointerDrag(task, $event)" @pointerup="finishPointerDrag" @pointercancel="cancelPointerDrag"><el-icon><MoreFilled /></el-icon></button>
          </div>
        </div>
        <div v-if="task.description" class="todo-description">{{ task.description }}</div>
        <div class="todo-meta"><span :class="['status-tag', task.priority === 'high' ? 'high' : '']">{{ priorityMap[task.priority] }}</span><span v-for="tag in task.tags || []" :key="tag" class="status-tag">{{ tag }}</span></div>
        <div class="todo-footer">
          <div class="todo-time-stack">
            <span class="todo-elapsed" :class="{ active: task.timer_started_at }"><el-icon><Timer /></el-icon>{{ formatDuration(taskElapsedSeconds(task)) }}</span>
            <span class="todo-due"><el-icon><Calendar /></el-icon>{{ formatDueAt(task.due_at) }}</span>
          </div>
          <el-dropdown><button type="button" class="todo-more-button" aria-label="更多任务操作"><el-icon><MoreFilled /></el-icon></button><template #dropdown><el-dropdown-menu><el-dropdown-item @click="edit(task)">编辑</el-dropdown-item><el-dropdown-item @click="addSub(task)">添加子任务</el-dropdown-item><el-dropdown-item @click="archiveOrRestore(task)">{{ task.archived ? '恢复到看板' : '归档' }}</el-dropdown-item><el-dropdown-item divided @click="remove(task.id)">删除</el-dropdown-item></el-dropdown-menu></template></el-dropdown>
        </div>
        <div class="todo-mobile-move"><span>移动到</span><el-select :model-value="task.status" size="small" @change="moveTask(task, $event)"><el-option v-for="option in columns" :key="option.key" :label="option.label" :value="option.key" /></el-select></div>
        <div v-if="task.subtasks?.length" class="subtasks">
          <div class="subtasks-header"><span>{{ task.subtasks.filter(x => x.completed).length }}/{{ task.subtasks.length }} 个子任务</span><span class="muted-text">可直接勾选完成</span></div>
          <div v-for="subtask in task.subtasks" :key="subtask.id" class="subtask-item">
            <input type="checkbox" :checked="subtask.completed" :aria-label="`完成子任务：${subtask.title}`" @change="toggleSubtask(task, subtask, $event.target.checked)" />
            <span :class="{ 'subtask-done': subtask.completed }">{{ subtask.title }}</span>
            <button type="button" class="subtask-action" @click.stop="editSubtask(task, subtask)">编辑</button>
            <button type="button" class="subtask-action danger" @click.stop="removeSubtask(task, subtask)">删除</button>
          </div>
        </div>
      </div>
      <el-empty v-if="!grouped[col.key].length" description="拖任务到这里" :image-size="45" />
    </div>
    </div>

    <el-dialog v-model="dialog" class="todo-create-dialog" :title="editing ? '编辑任务' : '新建任务'" width="580px">
    <el-form class="todo-dialog-form" :model="form" label-width="78px">
      <el-form-item class="todo-dialog-inline-item" label="归属项目"><el-select v-model="form.project_id" clearable placeholder="未归属项目" style="width:100%"><el-option v-for="project in app.projects" :key="project.id" :label="project.name" :value="project.id" /></el-select></el-form-item>
      <el-form-item class="todo-dialog-inline-item" label="任务标题"><el-input v-model="form.title" /></el-form-item>
      <el-form-item label="任务描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
      <el-form-item label="临时笔记"><el-input v-model="form.notes" type="textarea" :rows="2" placeholder="粘贴临时文字笔记" /></el-form-item>
      <div class="two-col todo-dialog-two-col"><el-form-item label="优先级"><el-select v-model="form.priority" style="width:100%"><el-option label="高优先级" value="high" /><el-option label="中优先级" value="medium" /><el-option label="低优先级" value="low" /></el-select></el-form-item><el-form-item label="截止时间"><el-date-picker v-model="form.due_at" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width:100%" /></el-form-item></div>
      <div class="two-col todo-dialog-two-col"><el-form-item label="任务标签"><el-select v-model="form.tags" multiple allow-create filterable style="width:100%"><el-option v-for="x in tagOptions" :key="x" :label="x" :value="x" /></el-select></el-form-item><el-form-item label="分组"><el-input v-model="form.group_name" /></el-form-item></div>
    </el-form>
    <template #footer><el-button class="todo-dialog-cancel" @click="dialog = false">取消</el-button><el-button class="todo-dialog-submit" type="primary" @click="save">保存任务</el-button></template>
  </el-dialog>

    <el-dialog v-model="subDialog" :title="subEditing ? '编辑子任务' : '添加子任务'" width="420px"><el-input v-model="subTitle" placeholder="例如：补充单元测试" @keyup.enter="saveSub" /><template #footer><el-button @click="subDialog = false">取消</el-button><el-button type="primary" @click="saveSub">保存</el-button></template></el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Calendar, FolderOpened, InfoFilled, MoreFilled, Timer, VideoPause, VideoPlay } from '@element-plus/icons-vue'
import { api } from '../api/http'
import { useAppStore } from '../stores'

const app = useAppStore(); const rows = ref([]); const selected = ref([]); const keyword = ref(''); const showArchive = ref(false); const dragging = ref(null); const pointerId = ref(null); const pointerDragging = ref(false); const dialog = ref(false); const editing = ref(null); const subDialog = ref(false); const subTitle = ref(''); const subTask = ref(null); const subEditing = ref(null); const mobileColumn = ref('todo'); const timerTick = ref(Date.now()); const columnRefs = {}; let timerInterval
const columns = [{ key: 'todo', label: '待处理' }, { key: 'doing', label: '进行中' }, { key: 'done', label: '已完成' }]
const priorityMap = { high: '高优先级', medium: '中优先级', low: '低优先级' }; const tagOptions = ['开发需求', 'BUG 修复', '学习任务', '日常琐事']; const form = reactive({ title: '', description: '', notes: '', status: 'todo', priority: 'medium', due_at: null, group_name: '默认分组', tags: [], project_id: null }); const priorityWeight = { high: 3, medium: 2, low: 1 }

const grouped = computed(() => Object.fromEntries(columns.map(column => {
  let list = rows.value.filter(item => item.status === column.key)
  if (column.key === 'todo') list = list.slice().sort((a, b) => { const priorityA = priorityWeight[a.priority] || 0; const priorityB = priorityWeight[b.priority] || 0; if (priorityA !== priorityB) return priorityB - priorityA; const dueA = a.due_at ? new Date(a.due_at).getTime() : Infinity; const dueB = b.due_at ? new Date(b.due_at).getTime() : Infinity; return dueA - dueB })
  return [column.key, list]
})))

function formatDueAt(dueAt) { if (!dueAt) return '无截止时间'; const date = new Date(dueAt); const days = ['日', '一', '二', '三', '四', '五', '六']; const pad = value => String(value).padStart(2, '0'); return `截止 ${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}(星期${days[date.getDay()]})` }
function parseTimerTimestamp(value) { if (!value) return NaN; const text = String(value); const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(text); const timestamp = Date.parse(hasTimezone ? text : `${text}Z`); return Number.isFinite(timestamp) ? timestamp : NaN }
function taskElapsedSeconds(task) { const stored = Math.max(0, Number(task.elapsed_seconds) || 0); const startedAt = parseTimerTimestamp(task.timer_started_at); const liveSeconds = Number.isFinite(startedAt) ? Math.max(0, Math.floor((timerTick.value - startedAt) / 1000)) : 0; return stored + liveSeconds }
function formatDuration(seconds) { const total = Math.max(0, Math.floor(Number(seconds) || 0)); const hours = Math.floor(total / 3600); const minutes = Math.floor((total % 3600) / 60); const secs = total % 60; return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}` }
function isOverdue(task) { return task.due_at && new Date(task.due_at) < new Date() && task.status !== 'done' }
async function load() { rows.value = (await api.todos({ include_archived: showArchive.value, keyword: keyword.value, project_id: app.currentProjectId || undefined })).data }
function openCreate() { editing.value = null; Object.assign(form, { title: '', description: '', notes: '', status: 'todo', priority: 'medium', due_at: null, group_name: '默认分组', tags: [], project_id: app.currentProjectId || null }); dialog.value = true }
function toggleArchiveView() { showArchive.value = !showArchive.value; load() }
function setColumnRef(key, element) { if (element) columnRefs[key] = element }
function focusColumn(key) { mobileColumn.value = key; nextTick(() => columnRefs[key]?.scrollIntoView({ behavior: 'smooth', block: 'start' })) }
function edit(task) { editing.value = task.id; Object.assign(form, { ...task, tags: task.tags || [] }); dialog.value = true }
async function save() { if (!form.title) return ElMessage.warning('请填写任务标题'); editing.value ? await api.updateTodo(editing.value, form) : await api.todo(form); dialog.value = false; ElMessage.success('已保存'); load() }
function toggleSelect(id) { selected.value = selected.value.includes(id) ? selected.value.filter(item => item !== id) : [...selected.value, id] }
async function moveTask(task, status) { if (!status || task.status === status) return; await api.statusTodo(task.id, status); await load() }
async function drop(status) { const task = dragging.value; dragging.value = null; if (task) await moveTask(task, status) }
function startPointerDrag(task, event) { const handle = event.target?.closest?.('.todo-drag-handle'); if (event.pointerType === 'mouse' || event.button !== 0 || (!handle && event.target?.closest?.('button,input,textarea,select,[role="button"],.el-dropdown,.el-select'))) return; dragging.value = task; pointerId.value = event.pointerId; pointerDragging.value = true; event.currentTarget?.setPointerCapture?.(event.pointerId) }
async function finishPointerDrag(event) { if (pointerId.value !== event.pointerId) return; const task = dragging.value; const target = document.elementFromPoint(event.clientX, event.clientY)?.closest('.todo-column'); try { event.currentTarget?.releasePointerCapture?.(event.pointerId) } catch {} pointerId.value = null; pointerDragging.value = false; dragging.value = null; if (task && target?.dataset.status) await moveTask(task, target.dataset.status) }
function cancelPointerDrag(event) { if (pointerId.value !== event.pointerId) return; try { event.currentTarget?.releasePointerCapture?.(event.pointerId) } catch {} pointerId.value = null; pointerDragging.value = false; dragging.value = null }
async function remove(id) { await api.deleteTodo(id); await load() }
async function archiveOrRestore(task) { if (task.archived) { await api.restoreTodo(task.id); ElMessage.success('已恢复到看板') } else { await api.archiveTodo(task.id); ElMessage.success('已归档') } await load() }
async function batch(action) { await api.batchTodos(action, selected.value); selected.value = []; await load() }
async function toggleTimer(task) { const active = Boolean(task.timer_started_at); await api.timerTodo(task.id, active ? 'pause' : 'start'); ElMessage.success(active ? '已暂停计时' : '已开始计时'); await load() }
function addSub(task) { subTask.value = task; subEditing.value = null; subTitle.value = ''; subDialog.value = true }
function editSubtask(task, subtask) { subTask.value = task; subEditing.value = subtask.id; subTitle.value = subtask.title; subDialog.value = true }
async function saveSub() { const title = subTitle.value.trim(); if (!title) return ElMessage.warning('请填写子任务标题'); if (subEditing.value) await api.updateSubtask(subTask.value.id, subEditing.value, { title }); else await api.addSubtask(subTask.value.id, { title }); subDialog.value = false; await load() }
async function toggleSubtask(task, subtask, completed) { await api.updateSubtask(task.id, subtask.id, { completed }); await load() }
async function removeSubtask(task, subtask) { await ElMessageBox.confirm(`确定删除子任务“${subtask.title}”吗？`, '删除确认', { type: 'warning' }); await api.deleteSubtask(task.id, subtask.id); await load() }
watch(() => app.currentProjectId, load); onMounted(() => { timerInterval = window.setInterval(() => { timerTick.value = Date.now() }, 1000); app.loadProjectContext().then(load).catch(load) }); onUnmounted(() => window.clearInterval(timerInterval))
</script>
