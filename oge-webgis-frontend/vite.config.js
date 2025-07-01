import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: ['vue', 'vue-router', 'pinia']
    }),
    Components({
      resolvers: [ElementPlusResolver()]
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    // 更新代理配置，连接可用的OGE服务器
    proxy: {
      '/api/mcp': {
        target: 'http://localhost:8000',  // 本地MCP服务器地址
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/mcp/, '')
      },
              '/api/oge': {
          target: 'http://111.37.195.111:7002',  // 志威哥提供的外网穿透地址
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/oge/, '')
        }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          ui: ['element-plus'],
          map: ['mapbox-gl', '@turf/turf']
        }
      }
    }
  }
}) 