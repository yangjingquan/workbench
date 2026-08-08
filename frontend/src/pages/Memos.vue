<template>
  <div class="page-heading"><div><h1>备忘录</h1><p>把临时想法和重要资料集中保存，随时查阅。</p></div></div>

  <div class="panel memo-editor">
    <div class="panel-header"><div><div class="panel-title">{{ editingMemoId ? '编辑备忘录' : '录入信息' }}</div><div class="panel-subtitle">标题和内容都填写后才可以保存</div></div><el-button v-if="editingMemoId" @click="cancelEdit">取消编辑</el-button></div>
    <el-form label-position="top" @submit.prevent="saveMemo">
      <el-form-item label="标题"><el-input v-model="form.title" maxlength="200" show-word-limit placeholder="输入备忘录标题" /></el-form-item>
      <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :autosize="{ minRows: 5, maxRows: 12 }" placeholder="输入需要保存的文字内容" /></el-form-item>
      <el-button type="primary" :loading="saving" @click="saveMemo">{{ editingMemoId ? '保存修改' : '保存' }}</el-button>
    </el-form>
  </div>

  <div class="memo-layout">
    <div class="panel memo-list-panel">
      <div class="panel-header"><div><div class="panel-title">备忘录列表</div><div class="panel-subtitle">按添加时间倒序排列</div></div></div>
      <el-input v-model="keyword" clearable placeholder="根据标题搜索" class="memo-search" />
      <div v-if="memos.length" class="memo-list">
        <button v-for="item in memos" :key="item.id" class="memo-item" :class="{ active: selectedMemo?.id === item.id }" @click="selectedId = item.id">
          <strong>{{ item.title }}</strong><span>{{ formatDate(item.created_at) }}</span>
        </button>
      </div>
      <el-empty v-else description="暂无备忘录" :image-size="70" />
    </div>

    <div class="panel memo-detail-panel">
      <div v-if="selectedMemo" class="memo-detail">
        <div class="panel-header"><div><div class="panel-title">{{ selectedMemo.title }}</div><div class="panel-subtitle">添加于 {{ formatDate(selectedMemo.created_at) }}</div></div><div class="memo-detail-actions"><el-button @click="startEdit(selectedMemo)">编辑</el-button><el-button @click="copyMemo">一键复制</el-button><el-button type="danger" plain @click="removeMemo(selectedMemo)">删除</el-button></div></div>
        <div class="memo-content">{{ selectedMemo.content }}</div>
      </div>
      <el-empty v-else description="点击左侧标题查看内容" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api/http'

const form = reactive({ title: '', content: '' }); const keyword = ref(''); const memos = ref([]); const selectedId = ref(null); const saving = ref(false); const editingMemoId = ref(null)
const selectedMemo = computed(() => memos.value.find(item => item.id === selectedId.value) || null)
function formatDate(value) { return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '' }
async function loadMemos() {
  memos.value = (await api.memos({ keyword: keyword.value.trim() })).data || []
  if (!memos.value.some(item => item.id === selectedId.value)) selectedId.value = memos.value[0]?.id || null
}
async function saveMemo() {
  if (!form.title.trim() || !form.content.trim()) return ElMessage.warning('标题和内容都不能为空')
  saving.value = true
  try { if (editingMemoId.value) await api.updateMemo(editingMemoId.value, { title: form.title.trim(), content: form.content.trim() }); else await api.memo({ title: form.title.trim(), content: form.content.trim() }); form.title = ''; form.content = ''; editingMemoId.value = null; await loadMemos(); ElMessage.success('备忘录已保存') } finally { saving.value = false }
}
function startEdit(memo) { selectedId.value = memo.id; editingMemoId.value = memo.id; form.title = memo.title; form.content = memo.content }
function cancelEdit() { editingMemoId.value = null; form.title = ''; form.content = '' }
async function removeMemo(memo) { await ElMessageBox.confirm(`确定删除备忘录“${memo.title}”吗？`, '删除确认', { type: 'warning' }); await api.deleteMemo(memo.id); if (editingMemoId.value === memo.id) cancelEdit(); selectedId.value = null; await loadMemos(); ElMessage.success('备忘录已删除') }
async function copyMemo() {
  if (!selectedMemo.value) return
  await navigator.clipboard.writeText(selectedMemo.value.content)
  ElMessage.success('内容已复制')
}
let searchTimer
watch(keyword, () => { clearTimeout(searchTimer); searchTimer = setTimeout(loadMemos, 250) })
onMounted(loadMemos)
</script>
