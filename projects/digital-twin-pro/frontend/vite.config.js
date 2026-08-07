import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 本地演示：/api 与 /vendor 均代理到 FastAPI(8001)，避免外网依赖
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/vendor': { target: 'http://127.0.0.1:8001', changeOrigin: true },
    },
  },
})