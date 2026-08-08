<template>
  <div class="plans-page">
    <div class="page-heading">
      <div>
        <h1>工作计划</h1>
        <p>把模糊的目标拆成有起止、有优先级的推进路径。</p>
      </div>
      <el-button class="plans-create-button" type="primary" @click="openCreate">
        <span class="button-plus">+</span> 新建计划
      </el-button>
    </div>

    <div class="toolbar plans-toolbar">
      <div class="plans-month-control">
        <el-date-picker
          v-model="month"
          class="plans-month-picker"
          type="month"
          value-format="YYYY-MM"
          :prefix-icon="Calendar"
          :clearable="false"
          @change="load"
        />
      </div>
      <span class="muted-text plans-summary">月度日历视图 · 共 {{ rows.length }} 项计划</span>
    </div>

    <div class="desktop-table table-card plans-table-card">
      <el-table v-loading="loading" :data="rows" stripe>
        <el-table-column prop="title" label="计划" min-width="240" />
        <el-table-column label="时间范围" width="220">
          <template #default="slotProps">{{ slotProps.row.start_date }} → {{ slotProps.row.end_date }}</template>
        </el-table-column>
        <el-table-column label="优先级" width="110">
          <template #default="slotProps">
            <span :class="['status-tag', slotProps.row.priority === 'high' ? 'high' : '']">
              {{ priorityMap[slotProps.row.priority] || slotProps.row.priority }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="slotProps">
            <el-tag :type="slotProps.row.status === 'done' ? 'success' : 'warning'" size="small">
              {{ slotProps.row.status === 'done' ? '已完成' : slotProps.row.status === 'pending' ? '待开始' : '进行中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="slotProps">
            <el-button class="plans-action-button plans-action-edit" link type="primary" title="编辑计划" aria-label="编辑计划" @click="edit(slotProps.row)">
              <el-icon><EditPen /></el-icon>
            </el-button>
            <el-button class="plans-action-button plans-action-delete" link type="danger" title="删除计划" aria-label="删除计划" @click="remove(slotProps.row.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !rows.length" description="这个月还没有计划" />
    </div>

    <div class="mobile-card-list">
      <article v-for="row in rows" :key="row.id" class="mobile-plan-card mobile-content-card">
        <div class="mobile-card-meta">
          <span>{{ row.start_date }} → {{ row.end_date }}</span>
          <span :class="['status-tag', row.priority === 'high' ? 'high' : '']">{{ priorityMap[row.priority] }}</span>
        </div>
        <h3>{{ row.title }}</h3>
        <p v-if="row.description" class="mobile-card-description">{{ row.description }}</p>
        <div class="mobile-card-footer">
          <el-tag :type="row.status === 'done' ? 'success' : 'warning'" size="small">
            {{ row.status === 'done' ? '已完成' : row.status === 'pending' ? '待开始' : '进行中' }}
          </el-tag>
          <div class="mobile-card-actions">
            <el-button class="plans-action-button plans-action-edit" link type="primary" title="编辑计划" aria-label="编辑计划" @click="edit(row)">
              <el-icon><EditPen /></el-icon>
            </el-button>
            <el-button class="plans-action-button plans-action-delete" link type="danger" title="删除计划" aria-label="删除计划" @click="remove(row.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </article>
      <el-empty v-if="!loading && !rows.length" description="这个月还没有计划" />
    </div>

    <el-dialog
      v-model="dialog"
      class="plans-dialog"
      :title="editing ? '编辑计划' : '新建计划'"
      width="560px"
    >
      <el-form class="plans-form" :model="form" label-width="88px">
        <el-form-item label="所属项目">
          <el-select v-model="form.project_id" placeholder="请选择项目" filterable style="width:100%">
            <el-option v-for="project in app.projects" :key="project.id" :label="project.name" :value="project.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划名称">
          <el-input v-model="form.title" placeholder="例如：完成季度复盘" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="补充计划目标或关键事项" />
        </el-form-item>
        <div class="two-col">
          <el-form-item label="开始日期">
            <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
          <el-form-item label="结束日期">
            <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
        </div>
        <div class="two-col">
          <el-form-item label="优先级">
            <el-select v-model="form.priority" style="width:100%">
              <el-option label="高优先级" value="high" />
              <el-option label="中优先级" value="medium" />
              <el-option label="低优先级" value="low" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status" style="width:100%">
              <el-option label="待开始" value="pending" />
              <el-option label="进行中" value="doing" />
              <el-option label="已完成" value="done" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button class="plans-dialog-cancel" @click="dialog = false">取消</el-button>
        <el-button class="plans-dialog-save" type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Calendar, Delete, EditPen } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/http'
import { useAppStore } from '../stores'

const app = useAppStore()
const rows = ref([])
const loading = ref(false)
const saving = ref(false)
const dialog = ref(false)
const editing = ref(null)
const priorityMap = { high: '高', medium: '中', low: '低' }

function localDate() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const month = ref(localDate().slice(0, 7))
const form = reactive({
  title: '',
  description: '',
  start_date: localDate(),
  end_date: localDate(),
  priority: 'medium',
  status: 'pending',
  project_id: null,
})

function responseData(response, fallback = null) {
  return response && Object.prototype.hasOwnProperty.call(response, 'data') ? response.data : (response ?? fallback)
}

function isVisibleInCurrentList(plan) {
  const sameMonth = plan?.start_date?.slice(0, 7) === month.value || plan?.end_date?.slice(0, 7) === month.value
  const sameProject = !app.currentProjectId || plan?.project_id === app.currentProjectId
  return sameMonth && sameProject
}

async function load() {
  loading.value = true
  try {
    const response = await api.plans({ month: month.value, project_id: app.currentProjectId || undefined })
    const data = responseData(response, [])
    rows.value = Array.isArray(data) ? data : []
    return rows.value
  } finally {
    loading.value = false
  }
}

function resetForm() {
  Object.assign(form, {
    title: '',
    description: '',
    start_date: localDate(),
    end_date: localDate(),
    priority: 'medium',
    status: 'pending',
    project_id: app.currentProjectId || null,
  })
}

function openCreate() {
  editing.value = null
  resetForm()
  dialog.value = true
}

function edit(plan) {
  editing.value = plan.id
  Object.assign(form, {
    title: plan.title || '',
    description: plan.description || '',
    start_date: plan.start_date,
    end_date: plan.end_date,
    priority: plan.priority || 'medium',
    status: plan.status || 'pending',
    project_id: plan.project_id || null,
  })
  dialog.value = true
}

async function save() {
  if (!form.title.trim()) {
    ElMessage.warning('请填写计划名称')
    return
  }
  saving.value = true
  try {
    const payload = { ...form, title: form.title.trim(), project_id: form.project_id || null }
    const response = editing.value ? await api.updatePlan(editing.value, payload) : await api.plan(payload)
    const savedPlan = responseData(response)
    dialog.value = false
    ElMessage.success('计划已保存')

    const loadedRows = await load()
    // Keep the just-created row visible even when the server's list query lags behind the write.
    if (savedPlan?.id && isVisibleInCurrentList(savedPlan) && !loadedRows.some(row => row.id === savedPlan.id)) {
      const hasExistingRow = rows.value.some(row => row.id === savedPlan.id)
      rows.value = hasExistingRow
        ? rows.value.map(row => row.id === savedPlan.id ? savedPlan : row)
        : [savedPlan, ...rows.value]
    }
  } finally {
    saving.value = false
  }
}

async function remove(id) {
  await api.deletePlan(id)
  rows.value = rows.value.filter(row => row.id !== id)
  ElMessage.success('计划已删除')
  await load()
}

onMounted(() => app.loadProjectContext().then(load, load))
</script>
