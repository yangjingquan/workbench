import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({ baseURL: import.meta.env.VITE_API_BASE || '', timeout: 12000 })
http.interceptors.request.use(config => {
  const token = localStorage.getItem('workbench_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
http.interceptors.response.use(response => response.data, error => {
  if (error.response?.status === 401) {
    localStorage.removeItem('workbench_token')
    localStorage.removeItem('workbench_user')
    if (location.pathname !== '/login') location.href = '/login'
  }
  ElMessage.error(error.response?.data?.msg || '网络请求失败')
  return Promise.reject(error)
})

export const api = {
  loginPublicKey: () => http.get('/api/auth/public-key'), login: data => http.post('/api/auth/login', data), me: () => http.get('/api/auth/me'),
  logoutAll: () => http.post('/api/auth/logout-all'), changePassword: data => http.post('/api/auth/change-password', data), resetPassword: data => http.post('/api/auth/reset-password', data), profile: data => http.put('/api/auth/profile', data),
  records: params => http.get('/api/work-records', { params }), record: data => http.post('/api/work-records', data), updateRecord: (id, data) => http.put(`/api/work-records/${id}`, data), deleteRecord: id => http.delete(`/api/work-records/${id}`),
  plans: params => http.get('/api/work-plans', { params }), plan: data => http.post('/api/work-plans', data), updatePlan: (id, data) => http.put(`/api/work-plans/${id}`, data), deletePlan: id => http.delete(`/api/work-plans/${id}`),
  reminders: params => http.get('/api/reminders', { params }), reminder: data => http.post('/api/reminders', data), updateReminder: (id, data) => http.put(`/api/reminders/${id}`, data), reminderAction: (id, action) => http.post(`/api/reminders/${id}/action`, null, { params: { action } }),
  todos: params => http.get('/api/todos', { params }), todo: data => http.post('/api/todos', data), updateTodo: (id, data) => http.put(`/api/todos/${id}`, data), statusTodo: (id, status) => http.patch(`/api/todos/${id}/status`, { status }), timerTodo: (id, action) => http.post(`/api/todos/${id}/timer`, null, { params: { action } }), deleteTodo: id => http.delete(`/api/todos/${id}`), addSubtask: (id, data) => http.post(`/api/todos/${id}/subtasks`, data), archiveTodo: id => http.patch(`/api/todos/${id}/archive`), batchTodos: (action, ids) => http.post('/api/todos/batch', ids, { params: { action } }),
  links: () => http.get('/api/quick-links'), link: data => http.post('/api/quick-links', data), updateLink: (id, data) => http.put(`/api/quick-links/${id}`, data), deleteLink: id => http.delete(`/api/quick-links/${id}`),
  accountCategories: () => http.get('/api/accounts/categories'), accountCategory: data => http.post('/api/accounts/categories', data),
  accountEntries: params => http.get('/api/accounts/entries', { params }), accountEntry: data => http.post('/api/accounts/entries', data), updateAccountEntry: (id, data) => http.put(`/api/accounts/entries/${id}`, data), deleteAccountEntry: id => http.delete(`/api/accounts/entries/${id}`), accountSummary: params => http.get('/api/accounts/summary', { params }),
  memos: keyword => http.get('/api/memos', { params: keyword ? { keyword } : {} }), memo: data => http.post('/api/memos', data), updateMemo: (id, data) => http.put(`/api/memos/${id}`, data), deleteMemo: id => http.delete(`/api/memos/${id}`),
  usage: data => http.post('/api/tools/usage', data), config: () => http.get('/api/config'), saveConfig: values => http.put('/api/config', { values }), dashboard: params => http.get('/api/dashboard', { params }), search: keyword => http.get('/api/search', { params: { keyword } })
}
