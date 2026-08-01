<template>
  <div class="page-heading"><div><h1>系统设置</h1><p>把工作台调整成更贴合你节奏的样子。</p></div></div>
  <div class="settings-list">
    <div class="setting-row"><div><b>主题色系</b><p>保留蓝紫品牌，或切换到明快的天蓝青绿</p></div><el-segmented v-model="settings.accentTheme" :options="[{label:'蓝紫品牌',value:'indigo'},{label:'天蓝青绿',value:'ocean'}]" @change="app.setAccentTheme(settings.accentTheme)" /></div>
    <div class="setting-row"><div><b>主题模式</b><p>全站组件与图表会同步适配</p></div><el-segmented v-model="settings.theme" :options="[{label:'浅色',value:'light'},{label:'暗黑',value:'dark'}]" /></div>
    <div class="setting-row"><div><b>侧边栏默认状态</b><p>下次进入工作台时保持这个状态</p></div><el-switch v-model="settings.sidebar_collapsed" active-text="收起" inactive-text="展开" /></div>
    <div class="setting-row"><div><b>默认提醒提前时间</b><p>事件到期前提前弹窗提醒</p></div><el-select v-model="settings.remind_before" style="width:150px"><el-option label="不提前" :value="0"/><el-option label="提前 5 分钟" :value="5"/><el-option label="提前 15 分钟" :value="15"/><el-option label="提前 30 分钟" :value="30"/></el-select></div>
    <div class="setting-row"><div><b>工作台默认视图</b><p>工作记录与 Todo 的首选展示方式</p></div><el-radio-group v-model="settings.default_view"><el-radio label="list">列表</el-radio><el-radio label="calendar">日历</el-radio></el-radio-group></div>
    <div class="setting-row"><div><b>默认工作时段</b><p>用于工时统计与每日节奏参考</p></div><div class="two-col" style="width:280px"><el-time-select v-model="settings.work_start" start="06:00" step="00:30" end="12:00" placeholder="开始"/><el-time-select v-model="settings.work_end" start="13:00" step="00:30" end="23:00" placeholder="结束"/></div></div>
  </div>
  <div class="settings-actions"><el-button type="primary" @click="save">保存设置</el-button></div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from '../stores'
import { api } from '../api/http'

const app = useAppStore()
const settings = reactive({ accentTheme: app.accentTheme, theme: app.theme, sidebar_collapsed: app.collapsed, remind_before: 15, default_view: 'list', work_start: '09:00', work_end: '18:00' })

onMounted(async () => {
  const res = await api.config()
  Object.entries(res.data || {}).forEach(([key, value]) => { settings[key] = value })
  settings.accentTheme = app.accentTheme
})

async function save() {
  const { accentTheme, ...serverSettings } = settings
  await api.saveConfig(serverSettings)
  app.theme = settings.theme
  app.initTheme()
  localStorage.setItem('workbench_theme', settings.theme)
  app.setAccentTheme(settings.accentTheme)
  await app.saveCollapsed(settings.sidebar_collapsed)
  ElMessage.success('设置已保存')
}
</script>
