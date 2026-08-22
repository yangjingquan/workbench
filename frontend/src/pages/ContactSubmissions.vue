<template>
  <div class="contact-submissions-page">
    <div class="page-heading">
      <div>
        <h1>需求列表</h1>
        <p>查看官网联系表单提交的需求信息，按提交时间倒序排列。</p>
      </div>
    </div>

    <div class="desktop-table table-card contact-submissions-table-card">
      <el-table v-loading="loading" :data="rows" stripe>
        <el-table-column prop="name" label="联系人" min-width="140" />
        <el-table-column prop="contact" label="联系方式" min-width="220" show-overflow-tooltip />
        <el-table-column prop="project_type" label="项目类型" min-width="170" show-overflow-tooltip />
        <el-table-column prop="budget" label="预算" min-width="170" show-overflow-tooltip />
        <el-table-column prop="timeline" label="期望周期" min-width="160" show-overflow-tooltip />
        <el-table-column prop="materials" label="现有素材" min-width="160" show-overflow-tooltip />
        <el-table-column prop="message" label="需求描述" min-width="360" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" min-width="150" show-overflow-tooltip />
        <el-table-column label="提交时间" min-width="190">
          <template #default="scope">{{ formatDateTime(scope.row.created_at) }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !rows.length" description="暂时还没有需求提交" />
    </div>

    <div class="mobile-card-list contact-submissions-mobile-list">
      <article v-for="row in rows" :key="row.id" class="mobile-content-card contact-submission-card">
        <div class="contact-submission-card-header">
          <strong>{{ row.name }}</strong>
          <span>{{ row.contact }}</span>
        </div>
        <div class="contact-submission-tags">
          <el-tag v-if="row.project_type" size="small" effect="plain">{{ row.project_type }}</el-tag>
          <el-tag v-if="row.budget" size="small" effect="plain">预算：{{ row.budget }}</el-tag>
          <el-tag v-if="row.timeline" size="small" effect="plain">周期：{{ row.timeline }}</el-tag>
        </div>
        <p class="contact-submission-message">{{ row.message }}</p>
        <div v-if="row.materials" class="contact-submission-materials">现有素材：{{ row.materials }}</div>
        <div class="contact-submission-ip">IP：{{ row.ip || '-' }}</div>
        <div class="contact-submission-created-at">提交时间：{{ formatDateTime(row.created_at) }}</div>
      </article>
      <el-empty v-if="!loading && !rows.length" description="暂时还没有需求提交" />
    </div>

    <div class="contact-submissions-pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @current-change="load"
        @size-change="handlePageSizeChange"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api/http'

const rows = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function load() {
  loading.value = true
  try {
    const data = (await api.contactSubmissions({ page: page.value, page_size: pageSize.value })).data || {}
    rows.value = data.items || []
    total.value = data.total || 0
    if (!rows.value.length && page.value > 1 && total.value > 0) {
      page.value -= 1
      await load()
    }
  } finally {
    loading.value = false
  }
}

function handlePageSizeChange(size) {
  pageSize.value = size
  page.value = 1
  load()
}

onMounted(load)
</script>
