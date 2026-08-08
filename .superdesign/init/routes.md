# Route map

Router: `frontend/src/router/index.js`; history is hash-based in desktop mode and browser history otherwise. All routes under `/` use `frontend/src/layouts/AppLayout.vue`; `/login` is public.

```js
import { createRouter, createWebHashHistory, createWebHistory } from 'vue-router'
import { useAppStore } from '../stores'

const routes = [
  { path: '/login', component: () => import('../pages/Login.vue'), meta: { public: true } },
  { path: '/', component: () => import('../layouts/AppLayout.vue'), children: [
    { path: '', redirect: '/dashboard' },
    { path: 'dashboard', component: () => import('../pages/Dashboard.vue'), meta: { title: '总览看板' } },
    { path: 'projects', component: () => import('../pages/Projects.vue'), meta: { title: '项目管理' } },
    { path: 'projects/:id', component: () => import('../pages/ProjectDetail.vue'), meta: { title: '项目详情' } },
    { path: 'records', component: () => import('../pages/Records.vue'), meta: { title: '工作记录' } },
    { path: 'plans', component: () => import('../pages/Plans.vue'), meta: { title: '工作计划' } },
    { path: 'reminders', component: () => import('../pages/Reminders.vue'), meta: { title: '事件提醒' } },
    { path: 'todos', component: () => import('../pages/Todos.vue'), meta: { title: 'Todo 看板' } },
    { path: 'links', component: () => import('../pages/Links.vue'), meta: { title: '快捷导航' } },
    { path: 'toolkit', component: () => import('../pages/Toolkit.vue'), meta: { title: '开发工具箱' } },
    { path: 'accounting', component: () => import('../pages/Accounting.vue'), meta: { title: '记账存钱' } },
    { path: 'memos', component: () => import('../pages/Memos.vue'), meta: { title: '备忘录' } },
    { path: 'profile', component: () => import('../pages/Profile.vue'), meta: { title: '个人中心' } },
    { path: 'settings', component: () => import('../pages/Settings.vue'), meta: { title: '系统设置' } }
  ]}
]
const router = createRouter({ history: import.meta.env.VITE_DESKTOP === 'true' ? createWebHashHistory() : createWebHistory(), routes })
router.beforeEach(to => { const store = useAppStore(); store.initTheme(); if (!to.meta.public && !store.isLoggedIn) return '/login'; if (to.path === '/login' && store.isLoggedIn) return '/dashboard' })
export default router
```

## Target routes

- `/dashboard` — `Dashboard.vue`; greeting, four metric cards, focus tasks, work trend, Todo completion, recent records, tool usage charts.
- `/records` — `Records.vue`; date range and keyword filters, list/calendar switch, work-record table/cards, create/edit dialog, export action.
- `/todos` — `Todos.vue`; search/archive filter, three status columns, draggable task cards, timers, subtasks, create/edit dialogs.
- `/projects` — project workspace list and project creation.
- `/plans` — monthly work plan list.
- `/reminders` — recurring reminder list.
- `/links` — quick-link card grid.
- `/toolkit` — developer utility tools.
- `/accounting` — accounting dashboard.
- `/memos` — memo list/detail editor.
- `/profile`, `/settings` — account and system settings.
