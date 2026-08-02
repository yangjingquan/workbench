<template>
  <div class="app-shell">
    <aside class="sidebar" :class="{ collapsed: app.collapsed }">
      <div class="brand"><div class="brand-mark">⌘</div><div v-if="!app.collapsed" class="brand-copy"><b>Workbench</b><span>小胖的工作台</span></div></div>
      <nav class="nav-list">
        <div class="nav-section" v-if="!app.collapsed">WORKSPACE</div>
        <RouterLink v-for="item in mainNav" :key="item.path" :to="item.path" class="nav-item"><el-icon><component :is="item.icon" /></el-icon><span v-if="!app.collapsed">{{ item.label }}</span></RouterLink>
        <div class="nav-section" v-if="!app.collapsed">TOOLS</div>
        <RouterLink to="/toolkit" class="nav-item"><el-icon><Tools /></el-icon><span v-if="!app.collapsed">开发工具箱</span><span v-if="!app.collapsed" class="nav-badge">4</span></RouterLink>
        <RouterLink to="/accounting" class="nav-item"><el-icon><Wallet /></el-icon><span v-if="!app.collapsed">记账存钱</span></RouterLink>
        <RouterLink to="/memos" class="nav-item"><el-icon><Memo /></el-icon><span v-if="!app.collapsed">备忘录</span></RouterLink>
      </nav>
      <div class="sidebar-bottom">
        <RouterLink to="/settings" class="nav-item"><el-icon><Setting /></el-icon><span v-if="!app.collapsed">系统设置</span></RouterLink>
        <button class="collapse-btn" @click="app.saveCollapsed(!app.collapsed)"><el-icon><DArrowLeft v-if="!app.collapsed" /><DArrowRight v-else /></el-icon><span v-if="!app.collapsed">收起侧栏</span></button>
      </div>
    </aside>
    <main class="main-area">
      <header class="topbar">
        <button class="mobile-menu-button" type="button" aria-label="打开移动端导航" @click="toggleMobileMenu">
          <el-icon><Menu /></el-icon>
        </button>
        <div class="breadcrumb"><span class="eyebrow">PERSONAL OS</span><span class="slash">/</span><span>{{ route.meta.title || '总览看板' }}</span></div>
        <div class="top-actions">
          <button class="icon-button" title="全局检索" @click="searchOpen = true"><el-icon><Search /></el-icon></button>
          <button class="icon-button" title="切换主题模式" aria-label="切换浅色或暗黑模式" @click="app.toggleTheme()"><el-icon><Moon v-if="app.theme === 'light'" /><Sunny v-else /></el-icon></button>
          <button class="icon-button accent-toggle" :title="app.accentTheme === 'indigo' ? '切换到天蓝青绿' : '切换到蓝紫品牌'" :aria-label="app.accentTheme === 'indigo' ? '切换到天蓝青绿主题' : '切换到蓝紫品牌主题'" @click="app.toggleAccentTheme()"><span :class="['accent-swatch', app.accentTheme]" /></button>
          <el-dropdown trigger="click" @command="handleUserCommand"><div class="avatar-wrap"><el-avatar :size="34" :src="app.user?.avatar_url || ''">{{ (app.user?.display_name || '管')[0] }}</el-avatar><span class="online-dot" /></div><template #dropdown><el-dropdown-menu><el-dropdown-item command="profile">个人中心</el-dropdown-item><el-dropdown-item divided command="logout">退出登录</el-dropdown-item></el-dropdown-menu></template></el-dropdown>
        </div>
      </header>
      <section class="content-scroll"><RouterView /></section>
    </main>
    <Transition name="mobile-nav">
      <div v-if="mobileNav.open" class="mobile-nav-layer">
        <button class="mobile-nav-backdrop" type="button" aria-label="关闭移动端导航" @click="closeMobileMenu" />
        <aside class="mobile-nav-panel" aria-label="移动端导航">
          <div class="mobile-nav-header">
            <div class="brand"><div class="brand-mark">⌘</div><div class="brand-copy"><b>Workbench</b><span>小胖的工作台</span></div></div>
            <button class="mobile-nav-close" type="button" aria-label="关闭移动端导航" @click="closeMobileMenu"><el-icon><Close /></el-icon></button>
          </div>
          <nav class="mobile-nav-list">
            <RouterLink v-for="item in mainNav" :key="item.path" :to="item.path" class="nav-item" @click="closeMobileMenu"><el-icon><component :is="item.icon" /></el-icon><span>{{ item.label }}</span></RouterLink>
            <RouterLink to="/toolkit" class="nav-item" @click="closeMobileMenu"><el-icon><Tools /></el-icon><span>开发工具箱</span><span class="nav-badge">4</span></RouterLink>
            <RouterLink to="/accounting" class="nav-item" @click="closeMobileMenu"><el-icon><Wallet /></el-icon><span>记账存钱</span></RouterLink>
            <RouterLink to="/memos" class="nav-item" @click="closeMobileMenu"><el-icon><Memo /></el-icon><span>备忘录</span></RouterLink>
            <RouterLink to="/settings" class="nav-item" @click="closeMobileMenu"><el-icon><Setting /></el-icon><span>系统设置</span></RouterLink>
          </nav>
        </aside>
      </div>
    </Transition>
    <el-dialog v-model="searchOpen" title="全局检索" width="680px" class="search-dialog"><el-input v-model="keyword" autofocus placeholder="检索工作记录、计划、待办和链接" :prefix-icon="Search" @keyup.enter="doSearch" /><div v-if="results" class="search-results"><div v-for="(items, key) in results" :key="key" class="search-group"><div class="search-group-title">{{ groupNames[key] }} · {{ items.length }}</div><div v-for="item in items" :key="item.id" class="search-result"><span>{{ item.title || item.name }}</span><small>{{ item.content || item.description || item.url || '' }}</small></div></div><el-empty v-if="!Object.values(results).some(x => x.length)" description="没有找到匹配内容" /></div></el-dialog>
    <ReminderPoll />
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { useRoute, useRouter, RouterLink, RouterView } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAppStore } from '../stores'
import { api } from '../api/http'
import ReminderPoll from '../components/ReminderPoll.vue'
import { createMobileNavState, toggleMobileNav, closeMobileNav } from './mobileNav'
import { Odometer, Calendar, Bell, List, Link, Tools, Wallet, Memo, Setting, Search, Moon, Sunny, DArrowLeft, DArrowRight, Menu, Close } from '@element-plus/icons-vue'
const app = useAppStore(); const route = useRoute(); const router = useRouter(); const searchOpen = ref(false); const keyword = ref(''); const results = ref(null)
const mobileNav = reactive(createMobileNavState())
function toggleMobileMenu() { Object.assign(mobileNav, toggleMobileNav(mobileNav)) }
function closeMobileMenu() { Object.assign(mobileNav, closeMobileNav(mobileNav)) }
watch(() => route.fullPath, closeMobileMenu)
const mainNav = [{ path: '/dashboard', label: '总览看板', icon: Odometer }, { path: '/records', label: '工作记录', icon: List }, { path: '/plans', label: '工作计划', icon: Calendar }, { path: '/reminders', label: '事件提醒', icon: Bell }, { path: '/todos', label: 'Todo 看板', icon: List }, { path: '/links', label: '快捷导航', icon: Link }]
const groupNames = { records: '工作记录', plans: '计划', todos: '待办', links: '链接', memos: '备忘录' }
async function doSearch() { if (!keyword.value.trim()) return; results.value = (await api.search(keyword.value)).data }
async function handleUserCommand(command) { if (command === 'profile') return router.push('/profile'); app.clearSession(); await router.replace('/login'); ElMessage.success('已退出登录') }
</script>
