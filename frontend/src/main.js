import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles.css'
import App from './App.vue'
import router from './router'
import { useAppStore } from './stores'

const pinia = createPinia()
const appStore = useAppStore(pinia)
appStore.initTheme()
window.addEventListener('workbench:auth-expired', () => {
  appStore.clearSession()
  if (router.currentRoute.value.path !== '/login') router.replace('/login')
})

createApp(App).use(pinia).use(router).use(ElementPlus).mount('#app')
