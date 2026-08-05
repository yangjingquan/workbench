<template>
  <div class="page-heading">
    <div><h1>项目</h1><p>用工作区隔离场景，用项目承载目标、任务和投入。</p></div>
    <el-button type="primary" @click="openCreate">+ 新建项目</el-button>
  </div>

  <div v-for="workspace in app.workspaces" :key="workspace.id" class="project-workspace-section">
    <div class="section-heading"><div><h2>{{ workspace.name }}</h2><span class="muted-text">{{ workspace.projects?.length || 0 }} 个项目</span></div><span class="workspace-dot" :style="{ background: workspace.color }" /></div>
    <div class="project-grid">
      <article v-for="project in workspace.projects" :key="project.id" class="project-card" @click="router.push(`/projects/${project.id}`)">
        <div class="project-card-top"><el-tag :type="statusType(project.status)" size="small">{{ statusMap[project.status] || project.status }}</el-tag><el-dropdown trigger="click" @click.stop><el-button link @click.stop><span class="more-dots">•••</span></el-button><template #dropdown><el-dropdown-menu><el-dropdown-item @click="openEdit(project)">编辑项目</el-dropdown-item><el-dropdown-item divided @click="archive(project)">归档项目</el-dropdown-item></el-dropdown-menu></template></el-dropdown></div>
        <h3>{{ project.name }}</h3><p>{{ project.description || '还没有项目简介' }}</p>
        <div v-if="project.tags?.length" class="tag-row"><el-tag v-for="tag in project.tags.slice(0, 4)" :key="tag" size="small" effect="plain">{{ tag }}</el-tag></div>
        <div class="project-card-footer"><span>{{ project.due_date ? `截止 ${project.due_date}` : '未设置截止日期' }}</span><span class="project-link">查看详情 →</span></div>
      </article>
      <el-empty v-if="!workspace.projects?.length" description="还没有项目" :image-size="64" />
    </div>
  </div>
  <el-empty v-if="!app.workspaces.length" description="正在加载工作区…" />

  <el-dialog v-model="dialog" :title="editing ? '编辑项目' : '新建项目'" width="680px">
    <el-form :model="form" label-width="90px">
      <div class="two-col"><el-form-item label="归属工作区"><el-select v-model="form.workspace_id" style="width:100%"><el-option v-for="workspace in app.workspaces" :key="workspace.id" :label="workspace.name" :value="workspace.id" /></el-select></el-form-item><el-form-item label="项目状态"><el-select v-model="form.status" style="width:100%"><el-option v-for="(label, value) in statusMap" :key="value" :label="label" :value="value" /></el-select></el-form-item></div>
      <el-form-item label="项目名称"><el-input v-model="form.name" placeholder="例如：个人知识库" /></el-form-item>
      <el-form-item label="项目简介"><el-input v-model="form.description" /></el-form-item>
      <el-form-item label="项目目标"><el-input v-model="form.goal" type="textarea" :rows="3" placeholder="希望通过这个项目达成什么？" /></el-form-item>
      <el-form-item label="技术栈"><el-select v-model="form.tech_stack" multiple filterable allow-create default-first-option style="width:100%" placeholder="输入后回车添加" /></el-form-item>
      <div class="two-col"><el-form-item label="仓库地址"><el-input v-model="form.repo_url" placeholder="https://github.com/..." /></el-form-item><el-form-item label="部署地址"><el-input v-model="form.deployment_url" placeholder="https://..." /></el-form-item></div>
      <div class="two-col"><el-form-item label="本地目录"><el-input v-model="form.local_path" placeholder="/Users/..." /></el-form-item><el-form-item label="截止日期"><el-date-picker v-model="form.due_date" value-format="YYYY-MM-DD" clearable style="width:100%" /></el-form-item></div>
      <el-form-item label="项目标签"><el-select v-model="form.tags" multiple filterable allow-create default-first-option style="width:100%" placeholder="输入后回车添加" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="dialog = false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { api } from '../api/http'
import { useAppStore } from '../stores'

const app = useAppStore(); const router = useRouter(); const dialog = ref(false); const editing = ref(null)
const statusMap = { planning: '规划中', active: '进行中', paused: '已暂停', completed: '已完成', archived: '已归档' }
const form = reactive({ workspace_id: null, name: '', description: '', goal: '', status: 'planning', tech_stack: [], repo_url: '', local_path: '', deployment_url: '', tags: [], due_date: null })
function statusType(status) { return { active: 'success', completed: 'success', paused: 'warning', archived: 'info' }[status] || '' }
function resetForm() { Object.assign(form, { workspace_id: app.currentWorkspaceId || app.workspaces[0]?.id || null, name: '', description: '', goal: '', status: 'planning', tech_stack: [], repo_url: '', local_path: '', deployment_url: '', tags: [], due_date: null }) }
function openCreate() { editing.value = null; resetForm(); dialog.value = true }
function openEdit(project) { editing.value = project.id; Object.assign(form, JSON.parse(JSON.stringify(project))); dialog.value = true }
async function save() { if (!form.name.trim()) return ElMessage.warning('请填写项目名称'); if (!form.workspace_id) return ElMessage.warning('请选择工作区'); if (editing.value) await api.updateProject(editing.value, form); else await api.createProject(form); dialog.value = false; await app.loadProjectContext(); ElMessage.success('项目已保存') }
async function archive(project) { await ElMessageBox.confirm(`确定归档项目“${project.name}”吗？`, '归档项目', { type: 'warning' }); await api.archiveProject(project.id); if (app.currentProjectId === project.id) app.selectProject(null); await app.loadProjectContext(); ElMessage.success('项目已归档') }
onMounted(() => app.loadProjectContext().catch(() => {}))
</script>
