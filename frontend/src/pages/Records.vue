<template>
  <div class="records-page">
    <section class="records-page-heading">
      <div>
        <h1>专注记录</h1>
        <p>沉淀每一份努力，复盘每一次成长。</p>
      </div>
      <div class="records-heading-actions">
        <el-input v-model="keyword" class="records-search" clearable placeholder="搜索记录内容..." @keyup.enter="load"><template #prefix><el-icon><Search /></el-icon></template></el-input>
        <div class="records-period-toggle">
          <button type="button" :class="{ active: period === 'week' }" @click="setPeriod('week')">本周</button>
          <button type="button" :class="{ active: period === 'month' }" @click="setPeriod('month')">本月</button>
          <button type="button" :class="{ active: period === 'custom' }" aria-label="选择日期" @click="setPeriod('custom')">◫</button>
        </div>
        <el-button class="records-new-button" type="primary" @click="openCreate">＋ 新增记录</el-button>
      </div>
    </section>

    <section class="records-toolbar">
      <div class="records-toolbar-left">
        <el-date-picker v-model="dateRange" class="records-date-picker" type="daterange" value-format="YYYY-MM-DD" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" @change="onDateRangeChange" />
      </div>
      <el-button class="records-export-button" @click="exportText">⇩ 导出日报</el-button>
    </section>

    <div class="records-layout">
      <main class="records-main">
        <div v-if="view === 'list'" class="records-list-view">
          <div class="desktop-table table-card records-table-shell">
            <el-table :data="rows" stripe class="records-table">
              <el-table-column prop="work_date" label="日期 / 时间" width="150" />
              <el-table-column prop="title" label="工作内容" min-width="180" />
              <el-table-column prop="content" label="复盘备注" min-width="220" show-overflow-tooltip />
              <el-table-column label="标签" width="160"><template #default="scope"><div class="records-table-tags"><el-tag v-for="tag in scope.row.tags || []" :key="tag" size="small" effect="plain">{{ tag }}</el-tag></div></template></el-table-column>
              <el-table-column prop="hours" label="工时" width="150" align="center" header-align="center"><template #default="scope"><span class="records-hours"><el-icon class="records-hours-icon"><Clock /></el-icon><span>{{ formatHours(scope.row.hours) }}</span></span></template></el-table-column>
              <el-table-column label="操作" width="128" align="center" header-align="center"><template #default="scope"><div class="records-row-actions"><el-button class="records-action-button records-action-edit" link type="primary" title="编辑记录" aria-label="编辑记录" @click="openEdit(scope.row)"><el-icon><EditPen /></el-icon></el-button><el-popconfirm title="确认删除这条记录？" @confirm="remove(scope.row.id)"><template #reference><el-button class="records-action-button records-action-delete" link type="danger" title="删除记录" aria-label="删除记录"><el-icon><Delete /></el-icon></el-button></template></el-popconfirm></div></template></el-table-column>
            </el-table>
            <el-empty v-if="!rows.length" description="还没有工作记录，今天就从一条开始" />
            <div v-else class="records-table-footer"><span>当前筛选共 {{ rows.length }} 条记录</span><span>按日期持续沉淀你的工作资产</span></div>
          </div>

          <div class="mobile-card-list">
            <article v-for="row in rows" :key="row.id" class="mobile-record-card mobile-content-card">
              <div class="mobile-record-card-header"><span>{{ row.work_date }}</span><strong>◷ {{ formatHours(row.hours) }}</strong></div>
              <div class="mobile-record-card-title"><h3>{{ row.title }}</h3><div class="mobile-record-card-actions"><el-button class="records-action-button records-action-edit" link type="primary" title="编辑记录" aria-label="编辑记录" @click="openEdit(row)"><el-icon><EditPen /></el-icon></el-button><el-popconfirm title="确认删除这条记录？" @confirm="remove(row.id)"><template #reference><el-button class="records-action-button records-action-delete" link type="danger" title="删除记录" aria-label="删除记录"><el-icon><Delete /></el-icon></el-button></template></el-popconfirm></div></div>
              <p v-if="row.content" class="mobile-card-description">{{ row.content }}</p>
              <div v-if="row.tags?.length" class="mobile-card-tags"><el-tag v-for="tag in row.tags" :key="tag" size="small" effect="plain">{{ tag }}</el-tag></div>
            </article>
            <el-empty v-if="!rows.length" description="还没有工作记录，今天就从一条开始" />
          </div>
        </div>
        <div v-else class="panel calendar-placeholder records-calendar-shell"><el-calendar v-model="calendarDate"><template #date-cell="{ data }"><div class="calendar-day"><span>{{ data.day.split('-').slice(2).join('') }}</span><i v-if="rows.some(x => x.work_date === data.day)"></i></div></template></el-calendar></div>
      </main>

      <aside class="records-sidebar">
        <div class="panel records-month-card">
          <div class="records-sidebar-heading"><div><h2>月度概览</h2><p>{{ calendarDate.getFullYear ? `${calendarDate.getFullYear()}年${calendarDate.getMonth() + 1}月` : '本月' }}</p></div><span class="records-sidebar-mark">✦</span></div>
          <el-calendar v-model="calendarDate" class="records-mini-calendar"><template #date-cell="{ data }"><div class="calendar-day"><span>{{ data.day.split('-').slice(2).join('') }}</span><i v-if="rows.some(x => x.work_date === data.day)"></i></div></template></el-calendar>
          <div class="records-summary"><div><span>累计打卡</span><b>{{ recordStats.days }} 天</b></div><div><span>平均工时</span><b>{{ recordStats.average }} h/天</b></div></div>
        </div>
        <div class="panel records-tags-card"><h2>高频标签</h2><div class="record-tag-cloud"><el-tag v-for="item in recordStats.tags" :key="item.name" size="small" effect="plain">{{ item.name }} ({{ item.count }})</el-tag><span v-if="!recordStats.tags.length" class="muted-text">暂无标签</span></div></div>
      </aside>
    </div>
  </div>

  <el-dialog v-model="dialog" class="records-dialog" :title="editing ? '编辑工作记录' : '新增工作记录'" width="560px">
    <el-form :model="form" label-width="75px">
      <el-form-item class="records-dialog-field" label="归属项目"><el-select v-model="form.project_id" clearable placeholder="未归属项目" style="width:100%"><el-option v-for="project in app.projects" :key="project.id" :label="project.name" :value="project.id" /></el-select></el-form-item>
      <el-form-item class="records-dialog-field" label="工作日期"><el-date-picker v-model="form.work_date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
      <el-form-item class="records-dialog-field" label="工作标题"><el-input v-model="form.title" placeholder="例如：完成登录鉴权模块" /></el-form-item>
      <el-form-item class="records-dialog-field records-dialog-field-textarea" label="工作内容"><el-input v-model="form.content" type="textarea" :rows="4" placeholder="记录关键产出、遇到的问题与下一步" /></el-form-item>
      <div class="two-col"><el-form-item class="records-dialog-field" label="工时"><el-input-number v-model="form.hours" :min="0" :max="24" :step="0.5" /></el-form-item><el-form-item class="records-dialog-field" label="标签"><el-select v-model="form.tags" multiple allow-create filterable style="width:100%"><el-option v-for="tag in ['开发','会议','复盘','学习']" :key="tag" :label="tag" :value="tag" /></el-select></el-form-item></div>
    </el-form>
    <template #footer><el-button class="records-dialog-cancel" @click="dialog=false">取消</el-button><el-button class="records-dialog-submit" type="primary" @click="save">保存记录</el-button></template>
  </el-dialog>
</template>
<script setup>
import { computed, reactive, ref, onMounted, onUnmounted, watch } from 'vue'; import { ElMessage } from 'element-plus'; import { Search, EditPen, Delete, Clock } from '@element-plus/icons-vue'; import { api } from '../api/http'; import { useAppStore } from '../stores'
const app=useAppStore(); const rows=ref([]), dateRange=ref([]), keyword=ref(''), period=ref('week'), view=ref('list'), dialog=ref(false), editing=ref(null), calendarDate=ref(new Date()); const form=reactive({ title:'',content:'',work_date:new Date().toISOString().slice(0,10),hours:1,tags:[],project_id:null })
const recordStats = computed(() => { const tagCounts = new Map(); const dates = new Set(); let hours = 0; rows.value.forEach(row => { dates.add(row.work_date); hours += Number(row.hours || 0); (row.tags || []).forEach(tag => tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1)) }); return { days: dates.size, average: dates.size ? (hours / dates.size).toFixed(1) : '0.0', tags: [...tagCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5).map(([name, count]) => ({ name, count })) } })
async function load(){ const res=await api.records({ start:dateRange.value?.[0], end:dateRange.value?.[1], keyword:keyword.value, project_id:app.currentProjectId || undefined }); rows.value=res.data }
function isoDate(value){ return value.toISOString().slice(0,10) }
function setPeriod(value){ period.value=value; if(value === 'custom'){ dateRange.value=[]; return load() } const end=new Date(); const start=new Date(end); if(value === 'week'){ const mondayOffset=(end.getDay() + 6) % 7; start.setDate(end.getDate() - mondayOffset) } else start.setDate(1); dateRange.value=[isoDate(start), isoDate(end)]; load() }
function onDateRangeChange(){ period.value='custom'; load() }
function openCreate(){ editing.value=null; Object.assign(form,{title:'',content:'',work_date:new Date().toISOString().slice(0,10),hours:1,tags:[],project_id:app.currentProjectId || null}); dialog.value=true } function openEdit(row){ editing.value=row.id; Object.assign(form,{...row,tags:row.tags||[]}); dialog.value=true }
async function save(){ if(!form.title) return ElMessage.warning('请填写工作标题'); editing.value ? await api.updateRecord(editing.value,form) : await api.record(form); dialog.value=false; ElMessage.success('已保存'); load() } async function remove(id){ await api.deleteRecord(id); ElMessage.success('已删除'); load() }
function formatHours(value){ const totalMinutes=Math.max(0,Math.round(Number(value||0)*60)); const hours=Math.floor(totalMinutes/60); const minutes=totalMinutes%60; if(hours) return minutes ? `${hours}小时${minutes}分` : `${hours}小时`; return `${minutes}分` }
function exportText(){ const text=rows.value.map(x=>`## ${x.work_date} ${x.title}\n${x.content}\n工时：${formatHours(x.hours)}`).join('\n\n'); const blob=new Blob([text],{type:'text/plain;charset=utf-8'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='工作日报.md'; a.click(); URL.revokeObjectURL(a.href) }
function handleMobileExport(){ exportText() }
watch(() => app.currentProjectId, load); onMounted(() => { window.addEventListener('workbench:records-export', handleMobileExport); app.loadProjectContext().then(() => setPeriod('week')).catch(() => setPeriod('week')) }); onUnmounted(() => window.removeEventListener('workbench:records-export', handleMobileExport))
</script>
