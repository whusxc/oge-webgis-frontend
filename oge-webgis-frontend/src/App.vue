<template>
  <div id="app" class="oge-app">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAppStore } from './stores/app'

const appStore = useAppStore()

onMounted(() => {
  // 初始化应用配置
  appStore.initApp()
})
</script>

<style lang="scss">
.oge-app {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  
  * {
    box-sizing: border-box;
  }
}

// 全局滚动条样式
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
  
  &:hover {
    background: #a8abb2;
  }
}

// Element Plus 样式覆盖
.el-message {
  min-width: 300px;
  
  .el-message__content {
    font-size: 14px;
  }
}

.el-notification {
  .el-notification__content {
    font-size: 14px;
  }
}

// 地图相关样式
.mapboxgl-popup {
  .mapboxgl-popup-content {
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    padding: 16px;
    
    .mapboxgl-popup-close-button {
      font-size: 18px;
      color: #909399;
      
      &:hover {
        color: #606266;
      }
    }
  }
}

// 动画效果
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from {
  transform: translateX(-100%);
}

.slide-leave-to {
  transform: translateX(100%);
}
</style> 