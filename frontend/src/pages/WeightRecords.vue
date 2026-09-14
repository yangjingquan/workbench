<template>
  <div class="weight-page">
    <section class="page-heading weight-page-heading">
      <div>
        <h1>体重记录</h1>
        <p>每天记下早晚体重，看看变化趋势。</p>
      </div>
      <div class="weight-range-note"><span class="weight-range-dot" />近 30 天</div>
    </section>

    <section class="weight-top-grid">
      <article class="panel weight-entry-panel">
        <div class="weight-panel-header">
          <div>
            <div class="panel-title">{{ editingId ? '更新体重记录' : '记录今天的体重' }}</div>
            <div class="panel-subtitle">{{ selectedDateLabel }} · {{ periodLabel(form.period) }}</div>
          </div>
          <span class="weight-unit-badge">市斤</span>
        </div>

        <el-form class="weight-entry-form" label-position="top" @submit.prevent="saveRecord">
          <el-form-item label="记录日期">
            <el-date-picker
              v-model="form.record_date"
              type="date"
              value-format="YYYY-MM-DD"
              format="YYYY年MM月DD日"
              :disabled-date="disableFutureDate"
              :clearable="false"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="记录时段">
            <div class="weight-period-toggle" role="group" aria-label="选择记录时段">
              <button type="button" :class="{ active: form.period === 'morning' }" @click="form.period = 'morning'">早上</button>
              <button type="button" :class="{ active: form.period === 'evening' }" @click="form.period = 'evening'">晚上</button>
            </div>
          </el-form-item>

          <el-form-item label="体重">
            <div class="weight-input-wrap">
              <el-input-number
                v-model="form.weight"
                class="weight-input"
                :min="0.1"
                :max="1000"
                :step="0.1"
                :precision="1"
                controls-position="right"
                placeholder="请输入体重"
              />
              <span>斤</span>
            </div>
          </el-form-item>

          <div v-if="editingId" class="weight-edit-hint">当天的{{ periodLabel(form.period) }}已有记录，保存将更新它。</div>
          <div class="weight-form-actions">
            <el-button type="primary" :loading="saving" @click="saveRecord">{{ editingId ? '保存修改' : '保存记录' }}</el-button>
            <el-button v-if="editingId" text @click="resetForm">取消编辑</el-button>
          </div>
        </el-form>
      </article>

      <article class="panel weight-chart-panel">
        <div class="weight-panel-header weight-chart-header">
          <div>
            <div class="panel-title">近 30 天趋势</div>
            <div class="panel-subtitle">早晚体重放在同一张图里对比</div>
          </div>
          <div class="weight-legend" aria-label="图例">
            <span><i class="weight-legend-dot morning" />早上</span>
            <span><i class="weight-legend-dot evening" />晚上</span>
          </div>
        </div>
        <div v-if="records.length" ref="chartRef" class="weight-chart" />
        <div v-else class="weight-empty-state">
          <el-empty description="还没有体重记录" :image-size="72" />
          <p>从今天开始，记录你的第一笔体重。</p>
        </div>
      </article>
    </section>

    <section class="panel weight-history-panel">
      <div class="weight-panel-header weight-history-header">
        <div>
          <div class="panel-title">记录明细</div>
          <div class="panel-subtitle">近 30 天共 {{ records.length }} 条记录</div>
        </div>
        <span class="weight-history-tip">单位：市斤</span>
      </div>

      <div v-if="records.length" class="weight-desktop-table">
        <el-table :data="records" stripe>
          <el-table-column prop="record_date" label="日期" width="180" />
          <el-table-column label="时段" width="180">
            <template #default="scope">
              <span :class="['weight-period-tag', scope.row.period]">{{ periodLabel(scope.row.period) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="体重">
            <template #default="scope"><strong class="weight-table-value">{{ formatWeight(scope.row.weight) }} <small>斤</small></strong></template>
          </el-table-column>
          <el-table-column label="操作" width="140" align="right">
            <template #default="scope">
              <div class="weight-row-actions">
                <el-button link type="primary" title="编辑记录" aria-label="编辑记录" @click="editRecord(scope.row)"><el-icon><EditPen /></el-icon></el-button>
                <el-button link type="danger" title="删除记录" aria-label="删除记录" @click="removeRecord(scope.row)"><el-icon><Delete /></el-icon></el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-if="records.length" class="weight-mobile-list">
        <article v-for="row in records" :key="row.id" class="weight-mobile-item">
          <div class="weight-mobile-item-main">
            <div><strong>{{ row.record_date }}</strong><span :class="['weight-period-tag', row.period]">{{ periodLabel(row.period) }}</span></div>
            <strong class="weight-mobile-value">{{ formatWeight(row.weight) }}<small>斤</small></strong>
          </div>
          <div class="weight-row-actions">
            <el-button link type="primary" title="编辑记录" aria-label="编辑记录" @click="editRecord(row)"><el-icon><EditPen /></el-icon></el-button>
            <el-button link type="danger" title="删除记录" aria-label="删除记录" @click="removeRecord(row)"><el-icon><Delete /></el-icon></el-button>
          </div>
        </article>
      </div>

      <el-empty v-if="!records.length" description="暂无记录明细" :image-size="72" />
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, EditPen } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { api } from '../api/http'
import { useAppStore } from '../stores'

const app = useAppStore()
const chartRef = ref(null)
const records = ref([])
const editingId = ref(null)
const saving = ref(false)
const form = reactive({ record_date: formatDate(new Date()), period: 'morning', weight: null })
let chart = null
let formSyncToken = 0

const today = () => formatDate(new Date())
const chartStart = () => formatDate(addDays(new Date(), -29))
const selectedDateLabel = computed(() => {
  const [year, month, day] = form.record_date.split('-')
  return `${year}年${month}月${day}日`
})
const periodLabel = period => period === 'evening' ? '晚上' : '早上'

function formatDate(value) {
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`
}

function addDays(value, amount) {
  const result = new Date(value)
  result.setDate(result.getDate() + amount)
  return result
}

function parseDate(value) {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function formatWeight(value) {
  return Number(value || 0).toFixed(1)
}

function disableFutureDate(value) {
  const current = new Date()
  current.setHours(23, 59, 59, 999)
  return value > current
}

function findLocalRecord() {
  return records.value.find(row => row.record_date === form.record_date && row.period === form.period)
}

async function syncFormWithExisting() {
  const token = ++formSyncToken
  let row = findLocalRecord()
  if (!row && (form.record_date < chartStart() || form.record_date > today())) {
    const response = await api.weightRecords({ start: form.record_date, end: form.record_date })
    row = response.data?.find(item => item.record_date === form.record_date && item.period === form.period)
  }
  if (token !== formSyncToken) return
  editingId.value = row?.id || null
  form.weight = row ? Number(row.weight) : null
}

async function loadRecords() {
  const response = await api.weightRecords({ start: chartStart(), end: today() })
  records.value = response.data || []
  await nextTick()
  await syncFormWithExisting()
  renderChart()
}

async function saveRecord() {
  if (!form.weight || Number(form.weight) <= 0) return ElMessage.warning('请输入有效体重')
  saving.value = true
  const payload = { record_date: form.record_date, period: form.period, weight: Number(Number(form.weight).toFixed(1)) }
  try {
    if (editingId.value) await api.updateWeightRecord(editingId.value, payload)
    else await api.weightRecord(payload)
    ElMessage.success(editingId.value ? '体重记录已更新' : '体重记录已保存')
    await loadRecords()
  } finally {
    saving.value = false
  }
}

function resetForm() {
  form.record_date = today()
  form.period = 'morning'
  void syncFormWithExisting()
}

function editRecord(row) {
  form.record_date = row.record_date
  form.period = row.period
  form.weight = Number(row.weight)
  editingId.value = row.id
  document.querySelector('.weight-entry-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function removeRecord(row) {
  try {
    await ElMessageBox.confirm(`确定删除 ${row.record_date} 的${periodLabel(row.period)}体重记录吗？`, '删除记录', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    await api.deleteWeightRecord(row.id)
    ElMessage.success('体重记录已删除')
    await loadRecords()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') throw error
  }
}

function chartColors() {
  const style = getComputedStyle(document.documentElement)
  return {
    text: style.getPropertyValue('--muted').trim(),
    line: style.getPropertyValue('--line').trim(),
    morning: style.getPropertyValue('--primary').trim(),
    evening: style.getPropertyValue('--orange').trim(),
    surface: style.getPropertyValue('--surface').trim(),
  }
}

function renderChart() {
  if (!chartRef.value || !records.value.length) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)
  const colors = chartColors()
  const dates = Array.from({ length: 30 }, (_, index) => formatDate(addDays(parseDate(chartStart()), index)))
  const byKey = new Map(records.value.map(row => [`${row.record_date}-${row.period}`, Number(row.weight)]))
  const values = records.value.map(row => Number(row.weight)).filter(Number.isFinite)
  const min = values.length ? Math.floor(Math.min(...values) - 1) : 'dataMin'
  const max = values.length ? Math.ceil(Math.max(...values) + 1) : 'dataMax'
  chart.setOption({
    animation: false,
    grid: { left: 8, right: 10, top: 16, bottom: 8, containLabel: true },
    tooltip: {
      trigger: 'axis',
      backgroundColor: colors.surface,
      borderColor: colors.line,
      textStyle: { color: getComputedStyle(document.documentElement).getPropertyValue('--text').trim(), fontSize: 12 },
      formatter(params) {
        const date = params[0]?.axisValue || ''
        const rows = params.filter(item => item.value !== null && item.value !== undefined)
        return `${date}<br/>${rows.map(item => `${item.marker}${item.seriesName}：<strong>${formatWeight(item.value)} 斤</strong>`).join('<br/>') || '暂无记录'}`
      },
    },
    xAxis: {
      type: 'category', boundaryGap: false, data: dates,
      axisLabel: { color: colors.text, fontSize: 10, interval: 4, formatter: value => value.slice(5) },
      axisLine: { lineStyle: { color: colors.line } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value', min, max, splitNumber: 4,
      axisLabel: { color: colors.text, fontSize: 10, formatter: value => `${value}` },
      axisLine: { show: false }, splitLine: { lineStyle: { color: colors.line } },
    },
    series: [
      { name: '早上', type: 'line', data: dates.map(date => byKey.get(`${date}-morning`) ?? null), connectNulls: false, smooth: 0.2, symbol: 'circle', symbolSize: 6, itemStyle: { color: colors.morning }, lineStyle: { color: colors.morning, width: 2.5 } },
      { name: '晚上', type: 'line', data: dates.map(date => byKey.get(`${date}-evening`) ?? null), connectNulls: false, smooth: 0.2, symbol: 'circle', symbolSize: 6, itemStyle: { color: colors.evening }, lineStyle: { color: colors.evening, width: 2.5 } },
    ],
  })
}

function handleResize() { chart?.resize() }

watch(() => [form.record_date, form.period], () => { void syncFormWithExisting() })
watch(() => [app.theme, app.accentTheme], async () => { await nextTick(); renderChart() })
onMounted(async () => { await loadRecords(); window.addEventListener('resize', handleResize) })
onUnmounted(() => { window.removeEventListener('resize', handleResize); chart?.dispose() })
</script>
