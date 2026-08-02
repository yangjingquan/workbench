<template>
  <div class="page-heading">
    <div><h1>记账存钱</h1><p>记录每一笔收入与支出，让钱流向更清晰。</p></div>
    <div class="page-actions"><el-button @click="categoryDialog = true">管理分类</el-button></div>
  </div>

  <div class="account-entry-grid">
    <div class="panel account-entry-form">
      <div class="panel-header"><div><div class="panel-title">新增账目</div><div class="panel-subtitle">支出和进账都可以按自己的分类记录</div></div></div>
      <el-form label-position="top" @submit.prevent="saveEntry">
        <div class="two-col">
          <el-form-item label="账目类型">
            <el-radio-group v-model="form.entry_type" @change="syncCategory">
              <el-radio-button label="expense">支出</el-radio-button>
              <el-radio-button label="income">进账</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="金额">
            <el-input-number v-model="form.amount" :min="0.01" :precision="2" :step="10" controls-position="right" style="width:100%" />
          </el-form-item>
        </div>
        <div class="two-col">
          <el-form-item label="分类">
            <el-select v-model="form.category" filterable allow-create default-first-option placeholder="选择或直接输入分类" style="width:100%">
              <el-option v-for="item in currentCategories" :key="item.id" :label="item.name" :value="item.name" />
            </el-select>
          </el-form-item>
          <el-form-item label="发生日期">
            <el-date-picker v-model="form.entry_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
        </div>
        <el-form-item label="备注（可选）"><el-input v-model="form.note" placeholder="例如：午餐、项目奖金" /></el-form-item>
        <el-button type="primary" :loading="entryLoading" @click="saveEntry">保存账目</el-button>
      </el-form>
    </div>

    <div class="panel account-summary-panel">
      <div class="panel-header account-summary-header">
        <div><div class="panel-title">收支统计</div><div class="panel-subtitle">按日、月、年查看账目变化</div></div>
        <el-radio-group v-model="statPeriod" size="small">
          <el-radio-button label="day">日</el-radio-button><el-radio-button label="month">月</el-radio-button><el-radio-button label="year">年</el-radio-button>
        </el-radio-group>
      </div>
      <el-date-picker v-if="statPeriod === 'day'" v-model="statAnchor" type="date" value-format="YYYY-MM-DD" class="account-period-picker" />
      <el-date-picker v-else-if="statPeriod === 'month'" v-model="statAnchor" type="month" value-format="YYYY-MM" class="account-period-picker" />
      <el-date-picker v-else v-model="statAnchor" type="year" value-format="YYYY" class="account-period-picker" />
      <div class="account-stat-cards">
        <div class="account-stat-card"><span>收入</span><b class="income-text">¥ {{ formatMoney(summary.total_income) }}</b></div>
        <div class="account-stat-card"><span>支出</span><b class="expense-text">¥ {{ formatMoney(summary.total_expense) }}</b></div>
        <div class="account-stat-card"><span>结余</span><b :class="summary.balance >= 0 ? 'income-text' : 'expense-text'">¥ {{ formatMoney(summary.balance) }}</b></div>
      </div>
      <div class="account-trend">
        <div class="section-label">期间趋势</div>
        <div v-if="summary.trend.length" class="account-trend-list">
          <div v-for="item in summary.trend" :key="item.label" class="account-trend-item"><span>{{ item.label }}</span><span class="income-text">+¥{{ formatMoney(item.income) }}</span><span class="expense-text">-¥{{ formatMoney(item.expense) }}</span></div>
        </div>
        <el-empty v-else description="当前期间暂无账目" :image-size="58" />
      </div>
    </div>
  </div>

  <div class="panel account-category-panel">
    <div class="panel-header"><div><div class="panel-title">分类统计</div><div class="panel-subtitle">当前统计范围内各分类汇总</div></div></div>
    <div class="desktop-accounting-table"><el-table :data="summary.by_category" size="small">
      <el-table-column prop="category" label="分类" />
      <el-table-column label="类型" width="100"><template #default="scope"><span :class="scope.row.entry_type === 'income' ? 'income-text' : 'expense-text'">{{ scope.row.entry_type === 'income' ? '进账' : '支出' }}</span></template></el-table-column>
      <el-table-column label="金额" width="150"><template #default="scope"><span :class="scope.row.entry_type === 'income' ? 'income-text' : 'expense-text'">¥ {{ formatMoney(scope.row.total) }}</span></template></el-table-column>
      <el-table-column prop="count" label="笔数" width="100" />
    </el-table></div>
    <div class="mobile-accounting-list">
      <article v-for="item in summary.by_category" :key="`${item.category}-${item.entry_type}`" class="mobile-category-card mobile-accounting-card">
        <div class="mobile-accounting-card-header"><b>{{ item.category }}</b><span :class="item.entry_type === 'income' ? 'income-text' : 'expense-text'">{{ item.entry_type === 'income' ? '进账' : '支出' }}</span></div>
        <div class="mobile-accounting-card-stats"><div><span>金额</span><b :class="item.entry_type === 'income' ? 'income-text' : 'expense-text'">¥ {{ formatMoney(item.total) }}</b></div><div><span>笔数</span><b>{{ item.count }}</b></div></div>
      </article>
      <el-empty v-if="!summary.by_category.length" description="当前期间暂无分类统计" />
    </div>
  </div>

  <div class="panel account-records-panel">
    <div class="panel-header"><div><div class="panel-title">账目明细</div><div class="panel-subtitle">{{ summary.start }} 至 {{ summary.end }}</div></div></div>
    <div class="desktop-accounting-table"><el-table :data="entries" size="small">
      <el-table-column prop="entry_date" label="日期" width="130" />
      <el-table-column label="类型" width="100"><template #default="scope"><span :class="scope.row.entry_type === 'income' ? 'income-text' : 'expense-text'">{{ scope.row.entry_type === 'income' ? '进账' : '支出' }}</span></template></el-table-column>
      <el-table-column prop="category" label="分类" width="150" />
      <el-table-column prop="note" label="备注" min-width="180" show-overflow-tooltip />
      <el-table-column label="金额" width="150"><template #default="scope"><span :class="scope.row.entry_type === 'income' ? 'income-text' : 'expense-text'">{{ scope.row.entry_type === 'income' ? '+' : '-' }}¥ {{ formatMoney(scope.row.amount) }}</span></template></el-table-column>
      <el-table-column label="操作" width="80"><template #default="scope"><el-button link type="danger" @click="removeEntry(scope.row.id)">删除</el-button></template></el-table-column>
      <template #empty><el-empty description="当前期间暂无账目" /></template>
    </el-table></div>
    <div class="mobile-accounting-list">
      <article v-for="item in entries" :key="item.id" class="mobile-entry-card mobile-accounting-card">
        <div class="mobile-accounting-card-header"><span>{{ item.entry_date }}</span><span :class="item.entry_type === 'income' ? 'income-text' : 'expense-text'">{{ item.entry_type === 'income' ? '进账' : '支出' }}</span></div>
        <div class="mobile-entry-category"><span>分类</span><b>{{ item.category }}</b></div>
        <p v-if="item.note" class="mobile-entry-note">{{ item.note }}</p>
        <div class="mobile-entry-footer"><b :class="item.entry_type === 'income' ? 'income-text' : 'expense-text'">{{ item.entry_type === 'income' ? '+' : '-' }}¥ {{ formatMoney(item.amount) }}</b><el-button link type="danger" @click="removeEntry(item.id)">删除</el-button></div>
      </article>
      <el-empty v-if="!entries.length" description="当前期间暂无账目" />
    </div>
  </div>

  <el-dialog v-model="categoryDialog" title="管理记账分类" width="460px">
    <div class="category-create-row">
      <el-select v-model="categoryForm.entry_type" style="width:120px"><el-option label="支出" value="expense" /><el-option label="进账" value="income" /></el-select>
      <el-input v-model="categoryForm.name" placeholder="输入新分类名称" @keyup.enter="saveCategory" />
      <el-button type="primary" @click="saveCategory">添加</el-button>
    </div>
    <div class="category-chip-list"><el-tag v-for="item in categories" :key="item.id" :type="item.entry_type === 'income' ? 'success' : ''">{{ item.name }} · {{ item.entry_type === 'income' ? '进账' : '支出' }}</el-tag></div>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api/http'

function pad(value) { return String(value).padStart(2, '0') }
function dateValue(date) { return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` }
function monthValue(date) { return `${date.getFullYear()}-${pad(date.getMonth() + 1)}` }
function yearValue(date) { return String(date.getFullYear()) }
function formatMoney(value) { return Number(value || 0).toFixed(2) }

const now = new Date()
const form = reactive({ entry_type: 'expense', amount: 0, category: '', note: '', entry_date: dateValue(now) })
const categoryForm = reactive({ entry_type: 'expense', name: '' })
const categories = ref([]); const entries = ref([]); const categoryDialog = ref(false); const entryLoading = ref(false)
const statPeriod = ref('month'); const statAnchor = ref(monthValue(now))
const summary = ref({ start: '', end: '', total_income: 0, total_expense: 0, balance: 0, by_category: [], trend: [] })
const currentCategories = computed(() => categories.value.filter(item => item.entry_type === form.entry_type))

function syncCategory() { if (!currentCategories.value.some(item => item.name === form.category)) form.category = currentCategories.value[0]?.name || '' }
async function loadCategories() { categories.value = (await api.accountCategories()).data || []; syncCategory() }
async function loadSummary() {
  const data = (await api.accountSummary({ period: statPeriod.value, anchor: statAnchor.value })).data
  summary.value = data || summary.value
  entries.value = (await api.accountEntries({ start: summary.value.start, end: summary.value.end })).data || []
}
async function saveEntry() {
  if (!form.amount || form.amount <= 0 || !form.category || !form.entry_date) return ElMessage.warning('请填写金额、分类和日期')
  entryLoading.value = true
  try { await api.accountEntry({ ...form }); form.amount = 0; form.note = ''; await loadSummary(); ElMessage.success('账目已保存') } finally { entryLoading.value = false }
}
async function removeEntry(id) {
  await ElMessageBox.confirm('确定删除这笔账目吗？', '删除确认', { type: 'warning' })
  await api.deleteAccountEntry(id); await loadSummary(); ElMessage.success('账目已删除')
}
async function saveCategory() {
  if (!categoryForm.name.trim()) return ElMessage.warning('请输入分类名称')
  await api.accountCategory({ ...categoryForm, name: categoryForm.name.trim() }); categoryForm.name = ''; await loadCategories(); ElMessage.success('分类已添加')
}
watch(statPeriod, period => { statAnchor.value = period === 'day' ? dateValue(new Date()) : period === 'month' ? monthValue(new Date()) : yearValue(new Date()) })
watch(statAnchor, () => { if (statAnchor.value) loadSummary() })
watch(() => form.entry_type, syncCategory)
onMounted(async () => { await loadCategories(); await loadSummary() })
</script>
