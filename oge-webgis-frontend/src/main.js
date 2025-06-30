import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

// 导入全局样式
import './assets/styles/global.scss'

// 导入 Mapbox GL JS
import 'mapbox-gl/dist/mapbox-gl.css'

const app = createApp(App)

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局配置
app.config.globalProperties.$ELEMENT = {
  size: 'default',
  zIndex: 3000
}

// 使用插件
app.use(createPinia())
app.use(router)
app.use(ElementPlus, {
  locale: {
    name: 'zh-cn'
  }
})

// 挂载应用
app.mount('#app')

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('全局错误:', err, info)
}

// 开发环境配置
if (import.meta.env.DEV) {
  console.log('🌍 OGE-GA+ 开发模式启动')
  console.log('📍 地图服务: Mapbox GL JS')
  console.log('🔧 MCP服务: localhost:8000')
  console.log('🤖 智能助手: 已集成')
} 