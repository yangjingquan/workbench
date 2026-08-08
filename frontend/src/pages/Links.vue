<template>
  <div class="page-heading links-page-heading">
    <div><h1>快捷导航</h1><p>把每天都会打开的东西，放到触手可及的地方。</p></div>
    <el-button type="primary" @click="openCreate">+ 添加链接</el-button>
  </div>
  <div class="toolbar links-toolbar">
    <div class="links-toolbar-copy">
      <span class="links-toolbar-kicker">LINK COLLECTION</span>
      <span class="links-toolbar-count">{{ filtered.length }} 个入口</span>
    </div>
    <el-radio-group v-model="category" class="link-category-tabs">
      <el-radio-button label="全部" />
      <el-radio-button v-for="x in categories" :key="x" :label="x" />
    </el-radio-group>
  </div>
  <div class="link-grid links-grid">
    <article
      v-for="(item, index) in filtered"
      :key="item.id"
      :class="['link-card', `link-card-tone-${index % 4}`]"
      @click="open(item.url)"
    >
      <div class="link-card-top">
        <div class="link-logo">{{ firstLetter(item.title) }}</div>
        <span class="link-category">{{ getCategory(item) }}</span>
      </div>
      <div class="link-card-body">
        <div class="link-card-title-row">
          <b>{{ item.title }}</b>
          <el-icon class="link-open-icon" aria-hidden="true"><LinkIcon /></el-icon>
        </div>
        <p class="link-url">{{ getDomain(item.url) }}</p>
        <p v-if="item.description" class="link-description">{{ item.description }}</p>
      </div>
      <div class="link-card-footer">
        <div class="link-card-actions">
          <el-tooltip content="编辑" placement="top">
            <button class="link-action link-action-edit" type="button" aria-label="编辑链接" @click.stop="edit(item)">
              <el-icon><Edit /></el-icon>
            </button>
          </el-tooltip>
          <el-tooltip content="删除" placement="top">
            <button class="link-action link-action-delete" type="button" aria-label="删除链接" @click.stop="remove(item.id)">
              <el-icon><Delete /></el-icon>
            </button>
          </el-tooltip>
        </div>
      </div>
    </article>
    <el-empty v-if="!filtered.length" description="添加一个常用链接吧" />
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
import { Delete, Edit, Link as LinkIcon } from '@element-plus/icons-vue'
import { api } from '../api/http'

const rows = ref([])
const dialog = ref(false)
const editing = ref(null)
const category = ref('全部')
const form = reactive({ title: '', url: '', category: '未分类', description: '' })
const categories = computed(() => [...new Set(rows.value.map(item => getCategory(item)))])
const filtered = computed(() => category.value === '全部' ? rows.value : rows.value.filter(item => getCategory(item) === category.value))

async function load() { rows.value = (await api.links()).data || [] }
function getCategory(item) { return item.category || '未分类' }
function firstLetter(title) { return String(title || '↗').trim().charAt(0).toUpperCase() || '↗' }
function getDomain(url) {
  const safeUrl = String(url || '').trim()
  try {
    return new URL(safeUrl.startsWith('http') ? safeUrl : `https://${safeUrl}`).hostname.replace(/^www\./, '')
  } catch {
    return safeUrl || '未设置网址'
  }
}
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
