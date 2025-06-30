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
    // 注释掉代理配置，支持离线模式运行
    // proxy: {
    //   '/api/mcp': {
    //     target: 'http://localhost:8000',  // MCP服务器地址（需要内网）
    //     changeOrigin: true,
    //     rewrite: (path) => path.replace(/^\/api\/mcp/, '')
    //   },
    //   '/api/oge': {
    //     target: 'http://10.101.240.20',  // OGE后端地址（需要内网）
    //     changeOrigin: true,
    //     rewrite: (path) => path.replace(/^\/api\/oge/, '')
    //   }
    // }
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