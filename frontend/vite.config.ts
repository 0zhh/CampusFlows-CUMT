import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  build: {
    // echarts 单独成块，首屏不必等它
    rollupOptions: {
      output: {
        manualChunks: {
          echarts: ['echarts/core', 'echarts/charts', 'echarts/components', 'echarts/renderers'],
          leaflet: ['leaflet']
        }
      }
    }
  },
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) }
  },
  server: {
    watch: {
      // Chrome 调试 profile、探针产物不参与热更新
      ignored: ['**/.probe/**', '**/node_modules/**', '**/dist/**']
    },
    port: 5173,
    strictPort: false,
    proxy: {
      // 第 3 段联调时启用；第 1 段后端未起，前端自动回落本地样例
      '/api': { target: 'http://127.0.0.1:8080', changeOrigin: true },
      '/ws': { target: 'ws://127.0.0.1:8080', ws: true }
    }
  }
})
