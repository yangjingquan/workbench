import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({ baseURL: import.meta.env.VITE_API_BASE || '', timeout: 12000 })
let authExpiredHandled = false

function contextParams(params = {}) {
  const workspaceId = Number(localStorage.getItem('workbench_workspace_id')) || undefined
  return { ...params, workspace_id: params.workspace_id ?? workspaceId }
}

function forceLogout() {
  if (authExpiredHandled) return
  authExpiredHandled = true
  localStorage.removeItem('workbench_token')
  localStorage.removeItem('workbench_user')
  window.dispatchEvent(new Event('workbench:auth-expired'))
}

export function resetAuthExpiredGuard() { authExpiredHandled = false }

http.interceptors.request.use(config => {
  const token = localStorage.getItem('workbench_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
http.interceptors.response.use(response => response.data, error => {
  const requestUrl = error.config?.url || ''
  const isLoginRequest = /\/api\/auth\/(login|public-key)$/.test(requestUrl)
  if (error.response?.status === 401 && localStorage.getItem('workbench_token') && !isLoginRequest) {
    forceLogout()
    ElMessage.warning('登录状态已失效，请重新登录')
  } else {
    ElMessage.error(error.response?.data?.msg || error.response?.data?.detail || '网络请求失败')
  }
  return Promise.reject(error)
})

export const api = {
  loginPublicKey: () => http.get('/api/auth/public-key'), login: data => http.post('/api/auth/login', data), me: () => http.get('/api/auth/me'),
  logoutAll: () => http.post('/api/auth/logout-all'), changePassword: data => http.post('/api/auth/change-password', data), resetPassword: data => http.post('/api/auth/reset-password', data), profile: data => http.put('/api/auth/profile', data),
  workspaces: () => http.get('/api/workspaces'), createWorkspace: data => http.post('/api/workspaces', data), updateWorkspace: (id, data) => http.put(`/api/workspaces/${id}`, data), archiveWorkspace: id => http.delete(`/api/workspaces/${id}`),
  projects: params => http.get('/api/projects', { params }), project: id => http.get(`/api/projects/${id}`), createProject: data => http.post('/api/projects', data), updateProject: (id, data) => http.put(`/api/projects/${id}`, data), archiveProject: id => http.delete(`/api/projects/${id}`), deleteProject: id => http.delete(`/api/projects/${id}/permanent`), projectDashboard: id => http.get(`/api/projects/${id}/dashboard`),
  milestones: id => http.get(`/api/projects/${id}/milestones`), createMilestone: (id, data) => http.post(`/api/projects/${id}/milestones`, data), updateMilestone: (projectId, id, data) => http.put(`/api/projects/${projectId}/milestones/${id}`, data), deleteMilestone: (projectId, id) => http.delete(`/api/projects/${projectId}/milestones/${id}`),
  versions: id => http.get(`/api/projects/${id}/versions`), createVersion: (id, data) => http.post(`/api/projects/${id}/versions`, data), updateVersion: (projectId, id, data) => http.put(`/api/projects/${projectId}/versions/${id}`, data), deleteVersion: (projectId, id) => http.delete(`/api/projects/${projectId}/versions/${id}`),
  commits: id => http.get(`/api/projects/${id}/commits`), createCommit: (id, data) => http.post(`/api/projects/${id}/commits`, data), deleteCommit: (projectId, id) => http.delete(`/api/projects/${projectId}/commits/${id}`),
  records: params => http.get('/api/work-records', { params: contextParams(params) }), record: data => http.post('/api/work-records', data), updateRecord: (id, data) => http.put(`/api/work-records/${id}`, data), deleteRecord: id => http.delete(`/api/work-records/${id}`),
  plans: params => http.get('/api/work-plans', { params: contextParams(params) }), plan: data => http.post('/api/work-plans', data), updatePlan: (id, data) => http.put(`/api/work-plans/${id}`, data), deletePlan: id => http.delete(`/api/work-plans/${id}`),
  reminders: params => http.get('/api/reminders', { params }), reminder: data => http.post('/api/reminders', data), updateReminder: (id, data) => http.put(`/api/reminders/${id}`, data), reminderAction: (id, action) => http.post(`/api/reminders/${id}/action`, null, { params: { action } }),
  todos: params => http.get('/api/todos', { params: contextParams(params) }), todo: data => http.post('/api/todos', data), updateTodo: (id, data) => http.put(`/api/todos/${id}`, data), statusTodo: (id, status) => http.patch(`/api/todos/${id}/status`, { status }), timerTodo: (id, action) => http.post(`/api/todos/${id}/timer`, null, { params: { action } }), deleteTodo: id => http.delete(`/api/todos/${id}`), addSubtask: (id, data) => http.post(`/api/todos/${id}/subtasks`, data), updateSubtask: (taskId, subtaskId, data) => http.patch(`/api/todos/${taskId}/subtasks/${subtaskId}`, data), deleteSubtask: (taskId, subtaskId) => http.delete(`/api/todos/${taskId}/subtasks/${subtaskId}`), archiveTodo: id => http.patch(`/api/todos/${id}/archive`), restoreTodo: id => http.patch(`/api/todos/${id}/restore`), batchTodos: (action, ids) => http.post('/api/todos/batch', ids, { params: { action } }),
  links: params => http.get('/api/quick-links', { params }), link: data => http.post('/api/quick-links', data), updateLink: (id, data) => http.put(`/api/quick-links/${id}`, data), deleteLink: id => http.delete(`/api/quick-links/${id}`),
  accountCategories: () => http.get('/api/accounts/categories'), accountCategory: data => http.post('/api/accounts/categories', data),
  accountEntries: params => http.get('/api/accounts/entries', { params }), accountEntry: data => http.post('/api/accounts/entries', data), updateAccountEntry: (id, data) => http.put(`/api/accounts/entries/${id}`, data), deleteAccountEntry: id => http.delete(`/api/accounts/entries/${id}`), accountSummary: params => http.get('/api/accounts/summary', { params }),
  memos: params => { const values = typeof params === 'string' ? (params ? { keyword: params } : {}) : params; return http.get('/api/memos', { params: contextParams(values) }) }, memo: data => http.post('/api/memos', data), updateMemo: (id, data) => http.put(`/api/memos/${id}`, data), deleteMemo: id => http.delete(`/api/memos/${id}`),
  usage: data => http.post('/api/tools/usage', data), config: () => http.get('/api/config'), saveConfig: values => http.put('/api/config', { values }), dashboard: params => http.get('/api/dashboard', { params: contextParams(params) }), search: (keyword, params = {}) => http.get('/api/search', { params: contextParams({ keyword, ...params }) })
}
