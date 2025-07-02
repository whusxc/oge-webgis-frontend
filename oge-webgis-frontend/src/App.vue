<template>
  <div id="app" class="oge-app">
    <!-- 现代化启动屏幕 -->
    <div v-if="loading" class="loading-screen">
      <div class="loading-container">
        <div class="logo-section">
          <div class="logo-circle">
            <div class="earth-icon">🌍</div>
          </div>
          <h1 class="brand-title">OGE</h1>
          <p class="brand-subtitle">智能地理分析平台</p>
        </div>
        
        <div class="loading-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: loadingProgress + '%' }"></div>
          </div>
          <p class="loading-text">{{ loadingText }}</p>
        </div>
        
        <div class="feature-highlights">
          <div class="feature-item" v-for="feature in features" :key="feature.id">
            <div class="feature-icon">{{ feature.icon }}</div>
            <span>{{ feature.name }}</span>
          </div>
        </div>
      </div>
      
      <!-- 动态背景 -->
      <div class="animated-background">
        <div class="bg-shape shape-1"></div>
        <div class="bg-shape shape-2"></div>
        <div class="bg-shape shape-3"></div>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-screen">
      <div class="error-container">
        <div class="error-icon">⚠️</div>
        <h2>初始化遇到问题</h2>
        <p class="error-message">{{ error }}</p>
        <button @click="retry" class="retry-btn">
          <span class="btn-icon">🔄</span>
          重新尝试
        </button>
      </div>
    </div>

    <!-- 主应用界面 -->
    <div v-else class="main-app">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onErrorCaptured } from 'vue'
import { useAppStore } from './stores/app'

const appStore = useAppStore()
const loading = ref(true)
const error = ref(null)
const loadingProgress = ref(0)
const loadingText = ref('正在启动系统...')

const features = [
  { id: 1, icon: '🗺️', name: '智能地图分析' },
  { id: 2, icon: '🛰️', name: '遥感数据处理' },
  { id: 3, icon: '🤖', name: 'AI地理助手' },
  { id: 4, icon: '📊', name: '数据可视化' }
]

// 模拟加载进度
const simulateLoading = () => {
  const steps = [
    { progress: 20, text: '初始化核心模块...' },
    { progress: 40, text: '加载地图服务...' },
    { progress: 60, text: '连接AI助手...' },
    { progress: 80, text: '准备用户界面...' },
    { progress: 100, text: '启动完成！' }
  ]
  
  let currentStep = 0
  const interval = setInterval(() => {
    if (currentStep < steps.length) {
      loadingProgress.value = steps[currentStep].progress
      loadingText.value = steps[currentStep].text
      currentStep++
    } else {
      clearInterval(interval)
    }
  }, 800)
}

onMounted(async () => {
  try {
    console.log('🚀 OGE应用开始初始化...')
    
    // 启动加载动画
    simulateLoading()
    
    // 初始化应用
    await appStore.initApp()
    
    // 等待加载动画完成
    setTimeout(() => {
      loading.value = false
      console.log('✅ OGE应用初始化完成')
    }, 4000)
    
  } catch (err) {
    console.error('❌ 应用初始化失败:', err)
    error.value = err.message || '应用初始化失败'
    loading.value = false
  }
})

onErrorCaptured((err, vm, info) => {
  console.error('Vue组件错误:', err, info)
  error.value = `组件错误: ${err.message}`
  return false
})

const retry = () => {
  error.value = null
  loading.value = true
  loadingProgress.value = 0
  window.location.reload()
}
</script>

<style lang="scss">
// 全局重置和变量
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  // 现代化配色方案
  --primary: #2563eb;
  --primary-dark: #1d4ed8;
  --secondary: #10b981;
  --accent: #f59e0b;
  --background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --surface: #ffffff;
  --surface-alt: #f8fafc;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --border: #e2e8f0;
  --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --radius: 12px;
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.oge-app {
  height: 100vh;
  width: 100vw;
  font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;
}

// 加载屏幕
.loading-screen {
  height: 100vh;
  background: var(--background);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.loading-container {
  text-align: center;
  z-index: 2;
  position: relative;
}

.logo-section {
  margin-bottom: 3rem;
  
  .logo-circle {
    width: 120px;
    height: 120px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1.5rem;
    backdrop-filter: blur(10px);
    border: 2px solid rgba(255, 255, 255, 0.2);
    animation: pulse 2s ease-in-out infinite;
    
    .earth-icon {
      font-size: 3rem;
      animation: rotate 10s linear infinite;
    }
  }
  
  .brand-title {
    font-size: 3.5rem;
    font-weight: 700;
    color: white;
    margin-bottom: 0.5rem;
    letter-spacing: -0.02em;
  }
  
  .brand-subtitle {
    font-size: 1.25rem;
    color: rgba(255, 255, 255, 0.9);
    font-weight: 300;
  }
}

.loading-progress {
  margin-bottom: 2rem;
  
  .progress-bar {
    width: 300px;
    height: 4px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
    margin: 0 auto 1rem;
    overflow: hidden;
    
    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #10b981, #3b82f6);
      border-radius: 2px;
      transition: width 0.8s ease;
    }
  }
  
  .loading-text {
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.9rem;
    font-weight: 500;
  }
}

.feature-highlights {
  display: flex;
  gap: 2rem;
  justify-content: center;
  flex-wrap: wrap;
  
  .feature-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(255, 255, 255, 0.1);
    padding: 0.75rem 1.5rem;
    border-radius: var(--radius);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    font-size: 0.9rem;
    font-weight: 500;
    transition: var(--transition);
    
    &:hover {
      background: rgba(255, 255, 255, 0.15);
      transform: translateY(-2px);
    }
    
    .feature-icon {
      font-size: 1.2rem;
    }
  }
}

// 动态背景
.animated-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  
  .bg-shape {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    animation: float 6s ease-in-out infinite;
    
    &.shape-1 {
      width: 200px;
      height: 200px;
      top: 10%;
      left: 10%;
      animation-delay: 0s;
    }
    
    &.shape-2 {
      width: 150px;
      height: 150px;
      top: 60%;
      right: 15%;
      animation-delay: 2s;
    }
    
    &.shape-3 {
      width: 100px;
      height: 100px;
      bottom: 20%;
      left: 20%;
      animation-delay: 4s;
    }
  }
}

// 错误屏幕
.error-screen {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-alt);
  
  .error-container {
    text-align: center;
    padding: 2rem;
    
    .error-icon {
      font-size: 4rem;
      margin-bottom: 1rem;
    }
    
    h2 {
      color: var(--text-primary);
      margin-bottom: 1rem;
      font-weight: 600;
    }
    
    .error-message {
      color: var(--text-secondary);
      margin-bottom: 2rem;
      max-width: 400px;
    }
    
    .retry-btn {
      background: var(--primary);
      color: white;
      border: none;
      padding: 0.75rem 2rem;
      border-radius: var(--radius);
      font-weight: 500;
      cursor: pointer;
      transition: var(--transition);
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin: 0 auto;
      
      &:hover {
        background: var(--primary-dark);
        transform: translateY(-1px);
      }
      
      .btn-icon {
        animation: spin 2s linear infinite;
      }
    }
  }
}

// 动画定义
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// 主应用容器
.main-app {
  height: 100vh;
  width: 100vw;
}
</style> 