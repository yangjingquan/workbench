<template>
  <div class="page-heading">
    <div><h1>Todo 看板</h1><p>把任务从脑内缓存移到看板，清晰地推进每一步。</p></div>
    <div class="page-actions"><el-button @click="batch('complete')" :disabled="!selected.length">批量完成</el-button><el-button type="primary" @click="openCreate">+ 新建任务</el-button></div>
  </div>

  <div class="toolbar">
    <div class="toolbar-left">
      <el-input v-model="keyword" clearable placeholder="搜索任务、备注" style="width:240px" @keyup.enter="load" />
      <el-checkbox v-model="showArchive" @change="load">查看归档任务</el-checkbox>
    </div>
    <div class="toolbar-right todo-toolbar-help">
      <span class="muted-text">拖拽卡片可改变状态</span>
      <el-tooltip content="归档会从当前看板隐藏任务，不会删除；勾选“查看归档任务”后可恢复。" placement="bottom-start"><span class="todo-archive-help">归档说明</span></el-tooltip>
    </div>
  </div>

  <div class="todo-board">
    <div v-for="col in columns" :key="col.key" class="todo-column" :data-status="col.key" @dragover.prevent @drop="drop(col.key)">
      <div class="column-head"><b>{{ col.label }}</b><span class="column-count">{{ grouped[col.key].length }}</span></div>
      <div
        v-for="task in grouped[col.key]"
        :key="task.id"
        class="todo-card"
        :class="{ overdue: isOverdue(task), 'is-dragging': pointerDragging && dragging?.id === task.id }"
        draggable="true"
        @dragstart="dragging = task"
        @dragend="dragging = null"
      >
        <div class="todo-card-top"><div class="todo-title"><input type="checkbox" :checked="selected.includes(task.id)" @change="toggleSelect(task.id)" /><span>{{ task.title }}</span></div><button type="button" class="todo-drag-handle" aria-label="拖动任务" @pointerdown="startPointerDrag(task, $event)" @pointerup="finishPointerDrag" @pointercancel="cancelPointerDrag">⋮⋮</button></div>
        <div v-if="task.description" class="muted-text" style="margin:10px 0 0 22px;line-height:1.5">{{ task.description }}</div>
        <div class="todo-meta"><span :class="['status-tag', task.priority === 'high' ? 'high' : '']">{{ priorityMap[task.priority] }}</span><span v-for="tag in task.tags || []" :key="tag" class="status-tag">{{ tag }}</span></div>
        <div class="todo-footer">
          <span>{{ formatDueAt(task.due_at) }}</span>
          <span class="timer-link" @click.stop="toggleTimer(task)">{{ task.timer_started_at ? '⏸ 计时中' : '⏱ 计时' }}</span>
          <el-dropdown><span style="cursor:pointer">···</span><template #dropdown><el-dropdown-menu><el-dropdown-item @click="edit(task)">编辑</el-dropdown-item><el-dropdown-item @click="addSub(task)">添加子任务</el-dropdown-item><el-dropdown-item @click="archiveOrRestore(task)">{{ task.archived ? '恢复到看板' : '归档' }}</el-dropdown-item><el-dropdown-item divided @click="remove(task.id)">删除</el-dropdown-item></el-dropdown-menu></template></el-dropdown>
        </div>
        <div class="todo-mobile-move"><span>移动到</span><el-select :model-value="task.status" size="small" @change="moveTask(task, $event)"><el-option v-for="option in columns" :key="option.key" :label="option.label" :value="option.key" /></el-select></div>
        <div v-if="task.subtasks?.length" class="subtasks">{{ task.subtasks.filter(x => x.completed).length }}/{{ task.subtasks.length }} 个子任务</div>
      </div>
      <el-empty v-if="!grouped[col.key].length" description="拖任务到这里" :image-size="45" />
    </div>
  </div>

  <el-dialog v-model="dialog" :title="editing ? '编辑任务' : '新建任务'" width="580px">
    <el-form :model="form" label-width="78px">
      <el-form-item label="任务标题"><el-input v-model="form.title" /></el-form-item>
      <el-form-item label="任务描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
      <el-form-item label="临时笔记"><el-input v-model="form.notes" type="textarea" :rows="2" placeholder="粘贴临时文字笔记" /></el-form-item>
      <div class="two-col"><el-form-item label="优先级"><el-select v-model="form.priority" style="width:100%"><el-option label="高优先级" value="high" /><el-option label="中优先级" value="medium" /><el-option label="低优先级" value="low" /></el-select></el-form-item><el-form-item label="截止时间"><el-date-picker v-model="form.due_at" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width:100%" /></el-form-item></div>
      <div class="two-col"><el-form-item label="任务标签"><el-select v-model="form.tags" multiple allow-create filterable style="width:100%"><el-option v-for="x in tagOptions" :key="x" :label="x" :value="x" /></el-select></el-form-item><el-form-item label="分组"><el-input v-model="form.group_name" /></el-form-item></div>
    </el-form>
    <template #footer><el-button @click="dialog = false">取消</el-button><el-button type="primary" @click="save">保存任务</el-button></template>
  </el-dialog>

  <el-dialog v-model="subDialog" title="添加子任务" width="420px"><el-input v-model="subTitle" placeholder="例如：补充单元测试" /><template #footer><el-button @click="subDialog = false">取消</el-button><el-button type="primary" @click="saveSub">添加</el-button></template></el-dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/http'

const rows = ref([]); const selected = ref([]); const keyword = ref(''); const showArchive = ref(false); const dragging = ref(null); const pointerId = ref(null); const pointerDragging = ref(false); const dialog = ref(false); const editing = ref(null); const subDialog = ref(false); const subTitle = ref(''); const subTask = ref(null)
const columns = [{ key: 'todo', label: '待处理' }, { key: 'doing', label: '进行中' }, { key: 'done', label: '已完成' }]
const priorityMap = { high: '高优先级', medium: '中优先级', low: '低优先级' }; const tagOptions = ['开发需求', 'BUG 修复', '学习任务', '日常琐事']; const form = reactive({ title: '', description: '', notes: '', status: 'todo', priority: 'medium', due_at: null, group_name: '默认分组', tags: [] }); const priorityWeight = { high: 3, medium: 2, low: 1 }

const grouped = computed(() => Object.fromEntries(columns.map(column => {
  let list = rows.value.filter(item => item.status === column.key)
  if (column.key === 'todo') list = list.slice().sort((a, b) => { const priorityA = priorityWeight[a.priority] || 0; const priorityB = priorityWeight[b.priority] || 0; if (priorityA !== priorityB) return priorityB - priorityA; const dueA = a.due_at ? new Date(a.due_at).getTime() : Infinity; const dueB = b.due_at ? new Date(b.due_at).getTime() : Infinity; return dueA - dueB })
  return [column.key, list]
})))

function formatDueAt(dueAt) { if (!dueAt) return '无截止时间'; const date = new Date(dueAt); const days = ['日', '一', '二', '三', '四', '五', '六']; const pad = value => String(value).padStart(2, '0'); return `截止 ${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}(星期${days[date.getDay()]})` }
function isOverdue(task) { return task.due_at && new Date(task.due_at) < new Date() && task.status !== 'done' }
async function load() { rows.value = (await api.todos({ include_archived: showArchive.value, keyword: keyword.value })).data }
function openCreate() { editing.value = null; Object.assign(form, { title: '', description: '', notes: '', status: 'todo', priority: 'medium', due_at: null, group_name: '默认分组', tags: [] }); dialog.value = true }
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
async function toggleTimer(task) { await api.timerTodo(task.id, task.timer_started_at ? 'stop' : 'start'); ElMessage.success(task.timer_started_at ? '计时已结束并生成工作记录' : '已开始计时'); await load() }
function addSub(task) { subTask.value = task; subTitle.value = ''; subDialog.value = true }
async function saveSub() { if (!subTitle.value) return; await api.addSubtask(subTask.value.id, { title: subTitle.value }); subDialog.value = false; await load() }
onMounted(load)
</script>
