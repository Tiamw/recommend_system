import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 这里保留默认 5173 端口，和后端 CORS 配置保持一致。
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: '0.0.0.0',
  },
})
