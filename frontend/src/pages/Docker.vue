<template>
  <div class="docker-page">
    <div class="page-heading">
      <div><h1>Docker 管理</h1><p>集中查看服务器容器、Compose 服务、日志和生命周期操作。</p></div>
      <div class="page-actions"><span class="docker-last-refresh">{{ lastRefreshLabel }}</span><el-button :icon="Refresh" :loading="loading" @click="loadData()">刷新</el-button></div>
    </div>

    <div class="docker-stat-grid">
      <div class="stat-card"><div class="stat-label">Docker Engine <span class="stat-icon green">●</span></div><div class="stat-value">{{ engineLabel }}</div><div class="stat-foot">{{ overview.engine?.version || '等待连接' }}</div></div>
      <div class="stat-card"><div class="stat-label">运行中容器 <span class="stat-icon purple">▶</span></div><div class="stat-value">{{ overview.running_count ?? '-' }}</div><div class="stat-foot">共 {{ overview.container_count ?? '-' }} 个容器</div></div>
      <div class="stat-card"><div class="stat-label">异常容器 <span class="stat-icon red">!</span></div><div class="stat-value">{{ overview.abnormal_count ?? '-' }}</div><div class="stat-foot">含 Health Check 异常</div></div>
      <div class="stat-card"><div class="stat-label">Compose 项目 <span class="stat-icon orange">◆</span></div><div class="stat-value">{{ overview.project_count ?? '-' }}</div><div class="stat-foot">服务分组实时读取</div></div>
    </div>

    <div class="docker-toolbar panel">
      <div class="docker-view-tabs"><button :class="['docker-view-tab', { active: activeView === 'services' }]" type="button" @click="activeView = 'services'">服务视图</button><button :class="['docker-view-tab', { active: activeView === 'containers' }]" type="button" @click="activeView = 'containers'">容器视图</button></div>
      <div class="docker-filter-row">
        <el-input v-model="filters.keyword" clearable placeholder="搜索容器或镜像" class="docker-keyword" />
        <el-select v-model="filters.project" clearable placeholder="全部项目" class="docker-filter"><el-option v-for="project in projects" :key="project.name" :label="project.name" :value="project.name" /></el-select>
        <el-select v-model="filters.state" clearable placeholder="全部状态" class="docker-filter"><el-option label="运行中" value="running" /><el-option label="已停止" value="exited" /><el-option label="暂停" value="paused" /><el-option label="重启中" value="restarting" /><el-option label="异常" value="dead" /></el-select>
        <el-select v-model="filters.health" clearable placeholder="健康状态" class="docker-filter"><el-option label="健康" value="healthy" /><el-option label="异常" value="unhealthy" /><el-option label="检查中" value="starting" /><el-option label="无检查" value="none" /></el-select>
      </div>
    </div>

    <div v-if="activeView === 'services'" class="docker-project-grid">
      <div v-for="project in visibleProjects" :key="project.name" class="panel docker-project-card">
        <div class="panel-header docker-project-header"><div><div class="panel-title">{{ project.name }}</div><div class="panel-subtitle">{{ project.container_count }} 个容器 · {{ project.services.length }} 个服务</div></div><el-tag size="small" effect="plain">Compose 项目</el-tag></div>
        <div v-if="project.services.length" class="docker-service-list">
          <div v-for="service in project.services" :key="service.name" class="docker-service-row">
            <div class="docker-service-title"><div><b>{{ service.name }}</b><span>{{ service.containers.length }} 个容器 · {{ service.running_count }} 个运行中</span></div><el-button size="small" plain @click="runServiceAction(project.name, service.name, 'restart')">重启服务</el-button></div>
            <div class="docker-mini-container-list"><button v-for="container in visibleServiceContainers(service.containers)" :key="container.id" type="button" class="docker-mini-container" @click="openContainer(container)"><span :class="['docker-state-dot', container.state]" /><span class="docker-mini-name">{{ container.name }}</span><StatusTag :label="stateLabel(container.state)" :tone="stateTone(container.state)" /><StatusTag v-if="container.health !== 'none'" :label="healthLabel(container.health)" :tone="healthTone(container.health)" /></button></div>
          </div>
        </div>
        <el-empty v-else description="没有可用服务" :image-size="54" />
      </div>
      <el-empty v-if="!visibleProjects.length" description="没有匹配的 Compose 项目" />
    </div>

    <div v-else class="panel docker-table-panel">
      <el-table :data="filteredContainers" row-key="id" class="docker-table" @row-click="openContainer">
        <el-table-column label="容器" min-width="210"><template #default="{ row }"><div class="docker-name-cell"><span :class="['docker-state-dot', row.state]" /><div><b>{{ row.name }}</b><small>{{ row.project || '独立容器' }}<span v-if="row.service"> / {{ row.service }}</span></small></div></div></template></el-table-column>
        <el-table-column label="状态" width="120"><template #default="{ row }"><StatusTag :label="stateLabel(row.state)" :tone="stateTone(row.state)" /></template></el-table-column>
        <el-table-column label="健康" width="110"><template #default="{ row }"><StatusTag :label="healthLabel(row.health)" :tone="healthTone(row.health)" /></template></el-table-column>
        <el-table-column label="镜像" min-width="220" show-overflow-tooltip prop="image" />
        <el-table-column label="资源" width="170"><template #default="{ row }"><small>{{ formatBytes(row.resources?.memory_usage_bytes) }} / {{ formatBytes(row.resources?.memory_limit_bytes) }}</small><br><small>{{ row.resources?.cpu_percent ?? 0 }}% CPU</small></template></el-table-column>
        <el-table-column label="操作" width="170" fixed="right"><template #default="{ row }"><el-button link type="primary" @click.stop="openContainer(row)">详情</el-button><el-button link type="warning" @click.stop="runContainerAction('restart', row)">重启</el-button></template></el-table-column>
      </el-table>
      <el-empty v-if="!filteredContainers.length" description="没有匹配的容器" />
    </div>

    <div class="panel docker-audit-panel"><div class="panel-header"><div><div class="panel-title">最近操作</div><div class="panel-subtitle">Docker 写操作会保留审计记录</div></div><el-button text @click="loadAuditLogs">刷新</el-button></div><el-table :data="auditLogs" class="docker-audit-table"><el-table-column label="时间" width="180"><template #default="{ row }">{{ formatDate(row.created_at) }}</template></el-table-column><el-table-column label="目标" min-width="200"><template #default="{ row }">{{ row.target_name }}</template></el-table-column><el-table-column label="动作" width="110"><template #default="{ row }">{{ actionLabel(row.action) }}</template></el-table-column><el-table-column label="结果" width="100"><template #default="{ row }"><StatusTag :label="resultLabel(row.result)" :tone="resultTone(row.result)" /></template></el-table-column><el-table-column label="错误" min-width="220" show-overflow-tooltip prop="error_message" /></el-table></div>

    <el-drawer v-model="drawerOpen" :title="selectedContainer?.name || '容器详情'" size="min(720px, 96vw)" @close="closeDrawer">
      <template v-if="selectedContainer">
        <div class="docker-detail-head"><div><StatusTag :label="stateLabel(selectedContainer.state)" :tone="stateTone(selectedContainer.state)" /><StatusTag :label="healthLabel(selectedContainer.health)" :tone="healthTone(selectedContainer.health)" /><span v-if="selectedContainer.protected" class="docker-protected-label">受保护容器</span></div><div class="docker-action-row"><el-button v-if="selectedContainer.state !== 'running'" size="small" type="success" plain @click="runContainerAction('start')">启动</el-button><el-button v-if="selectedContainer.state === 'running'" size="small" plain @click="runContainerAction('stop')">停止</el-button><el-button size="small" plain @click="runContainerAction('restart')">重启</el-button><el-button size="small" plain @click="runContainerAction(selectedContainer.state === 'paused' ? 'unpause' : 'pause')">{{ selectedContainer.state === 'paused' ? '恢复' : '暂停' }}</el-button><el-button size="small" type="danger" plain @click="runContainerAction('kill')">强制终止</el-button><el-button size="small" type="danger" plain :disabled="selectedContainer.protected" @click="runContainerAction('remove')">删除</el-button></div></div>
        <div class="docker-detail-grid"><div><span>镜像</span><b>{{ selectedContainer.image || '-' }}</b></div><div><span>重启次数</span><b>{{ selectedContainer.restart_count ?? 0 }}</b></div><div><span>启动时间</span><b>{{ formatDate(selectedContainer.started_at) }}</b></div><div><span>端口</span><b>{{ formatPorts(selectedContainer.ports) }}</b></div></div>
        <div class="docker-detail-section"><div class="docker-detail-section-title">日志 <div class="docker-log-actions"><el-select v-model="logTail" size="small" style="width:110px" @change="loadLogs"><el-option label="最近 100 行" :value="100" /><el-option label="最近 200 行" :value="200" /><el-option label="最近 1000 行" :value="1000" /></el-select><el-input v-model="logKeyword" size="small" clearable placeholder="筛选日志" style="width:140px" /><el-switch v-model="logFollowing" size="small" active-text="实时跟随" @change="toggleLogFollow" /></div></div><div class="docker-log-panel"><div v-for="(line, index) in visibleLogLines" :key="`${line.timestamp}-${index}`" :class="['docker-log-line', line.stream]"><span class="docker-log-time">{{ line.timestamp }}</span><span class="docker-log-stream">{{ line.stream }}</span><span>{{ line.message }}</span></div><span v-if="!visibleLogLines.length" class="docker-log-empty">暂无日志</span></div><el-button size="small" text @click="downloadLogs">下载当前日志</el-button></div>
        <div class="docker-detail-section"><div class="docker-detail-section-title">运行信息</div><div class="docker-meta-list"><div><span>命令</span><code>{{ selectedContainer.command?.join(' ') || '-' }}</code></div><div><span>网络</span><b>{{ selectedContainer.networks?.join(', ') || '-' }}</b></div><div><span>环境变量</span><b>{{ selectedContainer.environment_names?.join(', ') || '未提供' }}</b></div></div></div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import StatusTag from '../components/StatusTag.vue'
import { api } from '../api/http'
import { streamDockerLogs } from '../api/dockerStream'

const loading = ref(false)
const overview = ref({})
const projects = ref([])
const containers = ref([])
const auditLogs = ref([])
const activeView = ref('services')
const drawerOpen = ref(false)
const selectedContainer = ref(null)
const filters = reactive({ keyword: '', project: '', state: '', health: '' })
const logTail = ref(200)
const logKeyword = ref('')
const logFollowing = ref(false)
const logLines = ref([])
const streamController = ref(null)
const lastRefresh = ref(null)
let refreshTimer

const engineLabel = computed(() => overview.value.engine?.status === 'online' ? '在线' : overview.value.engine ? '异常' : '未连接')
const lastRefreshLabel = computed(() => lastRefresh.value ? `更新于 ${lastRefresh.value.toLocaleTimeString()}` : '尚未刷新')
const filteredContainers = computed(() => containers.value.filter(matchesFilters))
const visibleProjects = computed(() => projects.value.map(project => ({ ...project, services: project.services.map(service => ({ ...service, containers: visibleServiceContainers(service.containers) })).filter(service => service.containers.length) })).filter(project => project.services.length))
const visibleLogLines = computed(() => { const keyword = logKeyword.value.trim().toLowerCase(); return keyword ? logLines.value.filter(line => `${line.stream} ${line.message}`.toLowerCase().includes(keyword)) : logLines.value })

function matchesFilters(container) { return (!filters.keyword || `${container.name} ${container.image}`.toLowerCase().includes(filters.keyword.toLowerCase())) && (!filters.project || container.project === filters.project) && (!filters.state || container.state === filters.state) && (!filters.health || container.health === filters.health) }
function visibleServiceContainers(items = []) { return items.filter(matchesFilters) }
function stateLabel(value) { return ({ running: '运行中', exited: '已停止', paused: '已暂停', restarting: '重启中', dead: '异常', created: '已创建' }[value] || '未知') }
function stateTone(value) { return value === 'running' ? 'done' : ['dead', 'restarting'].includes(value) ? 'high' : 'muted-status' }
function healthLabel(value) { return ({ healthy: '健康', unhealthy: '异常', starting: '检查中', none: '无检查' }[value] || '未知') }
function healthTone(value) { return value === 'healthy' ? 'done' : value === 'unhealthy' ? 'high' : 'muted-status' }
function resultLabel(value) { return ({ success: '成功', partial: '部分成功', rejected: '已拦截', failed: '失败' }[value] || value || '未知') }
function resultTone(value) { return value === 'success' ? 'done' : value === 'partial' ? '' : 'high' }
function actionLabel(value) { return ({ start: '启动', stop: '停止', restart: '重启', pause: '暂停', unpause: '恢复', kill: '强制终止', remove: '删除' }[value] || value) }
function formatBytes(value = 0) { if (!value) return '0 B'; const units = ['B', 'KB', 'MB', 'GB']; const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1); return `${(value / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}` }
function formatDate(value) { if (!value) return '-'; const date = new Date(value); return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN', { hour12: false }) }
function formatPorts(ports = []) { return ports.length ? ports.map(port => `${port.public || '*'}:${port.private || '-'}`).join(', ') : '无映射' }

async function loadData(options = {}) {
  if (!options.silent) loading.value = true
  try {
    const [overviewResponse, projectsResponse, containersResponse] = await Promise.all([api.dockerOverview(), api.dockerProjects(), api.dockerContainers(filters)])
    overview.value = overviewResponse.data || {}
    projects.value = projectsResponse.data?.projects || []
    containers.value = containersResponse.data?.containers || []
    lastRefresh.value = new Date()
    await loadAuditLogs()
  } finally {
    loading.value = false
  }
}

async function loadAuditLogs() { const response = await api.dockerAuditLogs({ limit: 20 }); auditLogs.value = response.data || [] }
async function openContainer(container) { stopLogStream(); const response = await api.dockerContainer(container.id); selectedContainer.value = response.data || container; drawerOpen.value = true; await loadLogs() }
function closeDrawer() { stopLogStream(); selectedContainer.value = null; logLines.value = []; logFollowing.value = false }
async function loadLogs() { if (!selectedContainer.value) return; const response = await api.dockerLogs(selectedContainer.value.id, { tail: logTail.value }); logLines.value = response.data?.lines || [] }
function stopLogStream() { streamController.value?.abort(); streamController.value = null }
async function toggleLogFollow(value) { if (!value) return stopLogStream(); stopLogStream(); streamController.value = new AbortController(); try { await streamDockerLogs(selectedContainer.value.id, { tail: logTail.value }, line => { logLines.value = [...logLines.value, line].slice(-5000) }, streamController.value.signal) } catch (error) { if (error.name !== 'AbortError') ElMessage.error(error.message || '日志流连接失败') } finally { if (streamController.value && streamController.value.signal.aborted) streamController.value = null; else logFollowing.value = false } }
async function runContainerAction(action, target = selectedContainer.value) {
  if (!target || target.protected && action === 'remove') return ElMessage.warning('受保护容器不可删除')
  let payload = {}
  if (['kill', 'remove'].includes(action)) { try { const result = await ElMessageBox.prompt(`请输入“${target.name}”确认${actionLabel(action)}`, `确认${actionLabel(action)}`, { inputPlaceholder: target.name, confirmButtonText: '确认执行', cancelButtonText: '取消', inputPattern: new RegExp(`^${target.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`), inputErrorMessage: '容器名称不匹配' }); payload = { confirm_name: result.value } } catch { return } }
  else if (['stop', 'restart', 'pause'].includes(action)) { try { await ElMessageBox.confirm(`确定对 ${target.name} 执行${actionLabel(action)}吗？`, '确认操作', { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }) } catch { return } }
  try { await api.dockerAction(target.id, action, payload); ElMessage.success(`${target.name}：${actionLabel(action)}已完成`); await loadData({ silent: true }); if (drawerOpen.value) await openContainer(target) } catch { /* Axios interceptor already presents the server error. */ }
}
async function runServiceAction(project, service, action) { try { await ElMessageBox.confirm(`确定重启 ${project}/${service} 吗？`, '确认服务操作', { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }); await api.dockerServiceAction(project, service, action); ElMessage.success(`${project}/${service}：操作已完成`); await loadData({ silent: true }) } catch { /* Cancellation and interceptor errors are intentionally quiet here. */ } }
function downloadLogs() { const body = visibleLogLines.value.map(line => `${line.timestamp} [${line.stream}] ${line.message}`).join('\n'); const url = URL.createObjectURL(new Blob([body], { type: 'text/plain;charset=utf-8' })); const link = document.createElement('a'); link.href = url; link.download = `${selectedContainer.value?.name || 'container'}-logs.txt`; link.click(); URL.revokeObjectURL(url) }
watch(() => ({ ...filters }), () => loadData({ silent: true }), { deep: true })
onMounted(() => { loadData(); refreshTimer = window.setInterval(() => loadData({ silent: true }), 5000) })
onUnmounted(() => { window.clearInterval(refreshTimer); stopLogStream() })
</script>
