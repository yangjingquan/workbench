<template>
  <div class="page-heading">
    <div><h1>快捷导航</h1><p>把每天都会打开的东西，放到触手可及的地方。</p></div>
    <el-button type="primary" @click="openCreate">+ 添加链接</el-button>
  </div>
  <div class="toolbar"><el-radio-group v-model="category" size="small"><el-radio-button label="全部"/><el-radio-button v-for="x in categories" :key="x" :label="x"/></el-radio-group></div>
  <div class="link-grid">
    <div v-for="item in filtered" :key="item.id" class="link-card" @click="open(item.url)">
      <div class="link-logo">{{ item.title?.[0] || '↗' }}</div><b>{{ item.title }}</b><p>{{ item.description || item.url }}</p>
      <div class="link-card-actions"><el-button link type="primary" @click.stop="edit(item)">编辑</el-button><el-button link type="danger" @click.stop="remove(item.id)">删除</el-button></div>
    </div>
    <el-empty v-if="!filtered.length" description="添加一个常用链接吧"/>
  </div>
  <el-dialog v-model="dialog" :title="editing ? '编辑链接' : '添加链接'" width="500px">
    <el-form :model="form" label-width="65px">
      <el-form-item label="名称"><el-input v-model="form.title"/></el-form-item>
      <el-form-item label="网址"><el-input v-model="form.url" placeholder="https://"/></el-form-item>
      <el-form-item label="分类"><el-input v-model="form.category" placeholder="例如：开发、设计、阅读"/></el-form-item>
      <el-form-item label="简介"><el-input v-model="form.description"/></el-form-item>
    </el-form>
    <template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/http'

const rows = ref([])
const dialog = ref(false)
const editing = ref(null)
const category = ref('全部')
const form = reactive({ title: '', url: '', category: '未分类', description: '' })
const categories = computed(() => [...new Set(rows.value.map(item => item.category))])
const filtered = computed(() => category.value === '全部' ? rows.value : rows.value.filter(item => item.category === category.value))

async function load() { rows.value = (await api.links()).data || [] }
function openCreate() { editing.value = null; Object.assign(form, { title: '', url: '', category: '未分类', description: '' }); dialog.value = true }
function edit(item) { editing.value = item.id; Object.assign(form, item); dialog.value = true }
async function save() {
  if (!form.title || !form.url) return ElMessage.warning('请填写名称和网址')
  if (editing.value) await api.updateLink(editing.value, form)
  else await api.link(form)
  dialog.value = false
  await load()
}
function open(url) { window.open(url.startsWith('http') ? url : `https://${url}`, '_blank') }
async function remove(id) { await api.deleteLink(id); await load() }
onMounted(load)
</script>
