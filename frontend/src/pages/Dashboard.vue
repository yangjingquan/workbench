<template>
  <div class="dashboard-page">
    <section class="dashboard-hero-zone">
      <div class="dashboard-main-column">
        <div class="dashboard-heading-row">
          <div>
            <h1>{{ greeting }}，{{ app.user?.display_name || '管理员' }} <span class="wave">✦</span></h1>
            <p>今天的工作节奏很棒，继续保持专注。</p>
          </div>
          <div class="page-actions">
            <el-button class="dashboard-secondary-action" @click="$router.push('/records')">＋ 记录工作</el-button>
            <el-button class="dashboard-primary-action" type="primary" @click="$router.push('/todos')">＋ 新建待办</el-button>
          </div>
        </div>

        <div class="dashboard-metric-grid">
          <article class="dashboard-metric-card metric-purple">
            <div class="dashboard-metric-label"><span>本月工时</span><span class="dashboard-metric-icon">◷</span></div>
            <div class="dashboard-metric-value"><strong>{{ stats.cards.hours }}</strong><span>h</span></div>
            <span class="dashboard-metric-foot positive">↗ ＋8.2%</span>
          </article>
          <article class="dashboard-metric-card metric-green">
            <div class="dashboard-metric-label"><span>待办完成率</span><span class="dashboard-metric-icon">✓</span></div>
            <div class="dashboard-metric-value"><strong>{{ stats.cards.completion_rate }}</strong><span>%</span></div>
            <span class="dashboard-metric-foot positive">✓ 超预期完成</span>
          </article>
          <article class="dashboard-metric-card metric-orange">
            <div class="dashboard-metric-label"><span>进行中任务</span><span class="dashboard-metric-icon">↗</span></div>
            <div class="dashboard-metric-value"><strong>{{ Math.max(0, stats.cards.todo_total - stats.cards.todo_done) }}</strong><span>项</span></div>
            <span class="dashboard-metric-foot neutral">◷ 稳步推进中</span>
          </article>
        </div>
      </div>

      <article class="panel dashboard-focus-card">
        <div class="dashboard-focus-orb" />
        <div class="dashboard-focus-visual"><span class="dashboard-focus-pulse" /><span class="focus-visual-icon">ϟ</span></div>
        <span class="focus-status">正在专注</span>
        <h2>{{ focusTasks.length ? focusTasks[0].title : '开始一个专注任务' }}</h2>
        <p>{{ focusTasks.length ? 'UI 空间感设计重构' : '打开 Todo 开始计时' }}</p>
        <strong class="dashboard-focus-time">{{ focusTasks.length ? formatDuration(focusTasks[0].elapsed_seconds) : '00:00:00' }}</strong><!-- formatDuration(task.elapsed_seconds) -->
        <el-button class="dashboard-focus-action" @click="$router.push('/todos')">{{ focusTasks.length ? '结束计时并记录' : '打开 Todo 看板' }}</el-button>
      </article>
    </section>

    <section class="dashboard-content-grid dashboard-middle-zone">
      <article class="panel dashboard-chart-card">
        <div class="dashboard-panel-header">
          <div><h2>工作量趋势</h2><p>本月每日投入时间分布</p></div>
          <div class="dashboard-panel-actions"><span class="chart-legend"><i />专注时长</span><el-button text @click="$router.push('/records')">详细分析 →</el-button></div>
        </div>
        <div ref="lineRef" class="dashboard-chart dashboard-line-chart" />
      </article>
      <article class="panel dashboard-chart-card dashboard-status-card">
        <div class="dashboard-panel-header"><h2>任务状态</h2><el-button text @click="$router.push('/todos')">看板 →</el-button></div>
        <div ref="pieRef" class="dashboard-chart dashboard-pie-chart" />
        <div class="dashboard-status-summary"><div><span>待推进</span><strong>{{ Math.max(0, stats.cards.todo_total - stats.cards.todo_done) }}</strong></div><div><span>已归档</span><strong>{{ stats.cards.todo_done }}</strong></div></div>
      </article>
    </section>

    <section class="dashboard-content-grid dashboard-bottom-zone">
      <article class="panel dashboard-records-card">
        <div class="dashboard-panel-header"><h2>今日执行记录</h2><el-button text @click="$router.push('/records')">所有记录 →</el-button></div>
        <div class="dashboard-record-list">
          <div v-for="(item, index) in recentRecords" :key="item.id" class="dashboard-record-item">
            <span :class="['dashboard-record-icon', `record-tone-${index % 3}`]">{{ index === 0 ? '✓' : index === 1 ? '⌁' : '‹›' }}</span>
            <div><strong>{{ item.title }}</strong><p>{{ item.work_date }} · {{ formatWorkHours(item.hours) }}</p></div>
            <span class="dashboard-record-tag">{{ item.tags?.[0] || '工作' }}</span>
          </div>
          <el-empty v-if="!recentRecords.length" description="还没有今日记录" :image-size="55" />
        </div>
      </article>
      <article class="panel dashboard-tools-card">
        <div class="dashboard-panel-header"><h2>常用工具频次</h2><el-button text @click="$router.push('/toolkit')">工具箱 →</el-button></div>
        <div ref="barRef" class="dashboard-chart dashboard-bar-chart" />
      </article>
    </section>
  </div>
</template>
<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'; import * as echarts from 'echarts'; import { useAppStore } from '../stores'; import { api } from '../api/http'
const app = useAppStore(); const greeting = ref(''); const focusTick = ref(Date.now()); const stats = ref({ cards: { hours: 0, completion_rate: 0, todo_total: 0, todo_done: 0 }, focus_tasks: [], work_trend: [], tool_usage: [] }); const recentRecords = ref([]); const lineRef = ref(); const pieRef = ref(); const barRef = ref(); let charts = []; let greetingTimer; let focusTimer
const statusMap = { todo: '待处理', doing: '进行中', done: '已完成' }
function parseTimerTimestamp(value) { if (!value) return NaN; const text = String(value); const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(text); const timestamp = Date.parse(hasTimezone ? text : `${text}Z`); return Number.isFinite(timestamp) ? timestamp : NaN }
const focusTasks = computed(() => { const now = focusTick.value; return (stats.value.focus_tasks || []).map(task => { const startedAt = parseTimerTimestamp(task.timer_started_at); const liveSeconds = Number.isFinite(startedAt) ? Math.max(0, Math.floor((now - startedAt) / 1000)) : 0; return { ...task, elapsed_seconds: Math.max(0, Number(task.elapsed_seconds) || 0) + liveSeconds } }) })
function formatDuration(seconds) { const total = Math.max(0, Math.floor(Number(seconds) || 0)); const hours = Math.floor(total / 3600); const minutes = Math.floor((total % 3600) / 60); const secs = total % 60; return hours ? `${hours}小时${String(minutes).padStart(2, '0')}分${String(secs).padStart(2, '0')}秒` : `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}` }
function formatWorkHours(value) { const totalMinutes = Math.max(0, Math.round(Number(value || 0) * 60)); const hours = Math.floor(totalMinutes / 60); const minutes = totalMinutes % 60; if (hours) return minutes ? `${hours}小时${minutes}分` : `${hours}小时`; return `${minutes}分` }
const colors = () => ({ text: getComputedStyle(document.documentElement).getPropertyValue('--muted'), line: getComputedStyle(document.documentElement).getPropertyValue('--line'), primary: getComputedStyle(document.documentElement).getPropertyValue('--primary'), primaryStrong: getComputedStyle(document.documentElement).getPropertyValue('--primary-strong'), primarySoft: getComputedStyle(document.documentElement).getPropertyValue('--primary-soft'), accent: getComputedStyle(document.documentElement).getPropertyValue('--accent'), green: getComputedStyle(document.documentElement).getPropertyValue('--green') })
function updateGreeting() { const hour = new Date().getHours(); greeting.value = hour < 6 || hour >= 22 ? '夜深了' : hour < 9 ? '早上好' : hour < 12 ? '上午好' : hour < 14 ? '中午好' : hour < 18 ? '下午好' : '晚上好' }
function render() { charts.forEach(c => c.dispose()); charts = []; const c = colors(); const line = echarts.init(lineRef.value); line.setOption({ grid:{left:8,right:8,top:20,bottom:8,containLabel:true}, xAxis:{type:'category',boundaryGap:false,data:stats.value.work_trend.map(x=>x.date.slice(5)),axisLabel:{color:c.text,fontSize:10},axisLine:{lineStyle:{color:c.line}}}, yAxis:{type:'value',axisLabel:{color:c.text,fontSize:10},splitLine:{lineStyle:{color:c.line}}}, series:[{data:stats.value.work_trend.map(x=>x.hours),type:'line',smooth:true,symbol:'none',lineStyle:{color:c.primary,width:3},areaStyle:{color:c.primarySoft}}] }); const pie = echarts.init(pieRef.value); pie.setOption({ tooltip:{trigger:'item'}, series:[{type:'pie',radius:['56%','76%'],center:['50%','50%'],label:{show:false},data:[{value:stats.value.cards.todo_done,name:'已完成',itemStyle:{color:c.green}},{value:Math.max(0,stats.value.cards.todo_total-stats.value.cards.todo_done),name:'待推进',itemStyle:{color:c.accent}}]}] }); const bar = echarts.init(barRef.value); bar.setOption({grid:{left:8,right:8,top:20,bottom:8,containLabel:true},xAxis:{type:'category',data:stats.value.tool_usage.map(x=>x.name),axisLabel:{color:c.text,fontSize:10},axisLine:{lineStyle:{color:c.line}}},yAxis:{type:'value',axisLabel:{color:c.text,fontSize:10},splitLine:{lineStyle:{color:c.line}}},series:[{type:'bar',barWidth:18,data:stats.value.tool_usage.map(x=>x.count),itemStyle:{borderRadius:[5,5,0,0],color:c.primaryStrong}}]}); charts=[line,pie,bar] }
onMounted(async () => { updateGreeting(); greetingTimer = window.setInterval(updateGreeting, 60000); focusTimer = window.setInterval(() => { focusTick.value = Date.now() }, 250); const project_id = app.currentProjectId || undefined; const today = new Date().toISOString().slice(0,10); const [dash, records] = await Promise.all([api.dashboard({ project_id }), api.records({ start: today, end: today, project_id })]); stats.value = dash.data; focusTick.value = Date.now(); recentRecords.value = records.data.slice(0, 4); await nextTick(); render(); window.addEventListener('resize', () => charts.forEach(c => c.resize())) })
onUnmounted(() => { window.clearInterval(greetingTimer); window.clearInterval(focusTimer) })
watch(() => [app.theme, app.accentTheme], async () => { await nextTick(); if (lineRef.value) render() })
</script>
