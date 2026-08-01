import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles.css'
import App from './App.vue'
import router from './router'
import { useAppStore } from './stores'

const pinia = createPinia()
useAppStore(pinia).initTheme()

createApp(App).use(pinia).use(router).use(ElementPlus).mount('#app')
