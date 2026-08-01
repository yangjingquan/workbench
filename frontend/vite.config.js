import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => ({
  plugins: [vue()],
  base: mode === 'desktop' ? './' : '/',
  server: { port: 5173, host: '0.0.0.0', proxy: { '/api': 'http://localhost:8100' } }
}))
