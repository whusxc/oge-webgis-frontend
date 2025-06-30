<template>
  <div class="not-found-page">
    <div class="not-found-container">
      <div class="error-animation">
        <div class="error-number">4</div>
        <div class="error-icon">
          <el-icon size="120"><QuestionFilled /></el-icon>
        </div>
        <div class="error-number">4</div>
      </div>
      
      <div class="error-content">
        <h1>页面未找到</h1>
        <p>抱歉，您访问的页面不存在或已被移动。</p>
        <p class="error-detail">
          请检查URL是否正确，或者使用下面的按钮返回。
        </p>
        
        <div class="action-buttons">
          <el-button 
            type="primary" 
            size="large"
            @click="goHome"
            :icon="'House'"
          >
            返回首页
          </el-button>
          
          <el-button 
            size="large"
            @click="goBack"
            :icon="'ArrowLeft'"
          >
            返回上页
          </el-button>
          
          <el-button 
            type="success"
            size="large"
            @click="goMap"
            :icon="'MapLocation'"
          >
            打开地图
          </el-button>
        </div>
        
        <div class="help-links">
          <h3>您可以尝试：</h3>
          <ul>
            <li>
              <el-link 
                type="primary" 
                @click="goMap"
                :icon="'MapLocation'"
              >
                查看地图界面
              </el-link>
            </li>
            <li>
              <el-link 
                type="primary" 
                @click="goTools"
                :icon="'Tools'"
              >
                浏览工具箱
              </el-link>
            </li>
            <li>
              <el-link 
                type="primary" 
                @click="goDashboard"
                :icon="'DataBoard'"
              >
                访问控制台
              </el-link>
            </li>
            <li>
              <el-link 
                type="primary" 
                @click="contactSupport"
                :icon="'Service'"
              >
                联系技术支持
              </el-link>
            </li>
          </ul>
        </div>
      </div>
    </div>
    
    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="floating-shape shape-1"></div>
      <div class="floating-shape shape-2"></div>
      <div class="floating-shape shape-3"></div>
      <div class="floating-shape shape-4"></div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { showSuccess, showInfo } from '@/services/api'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  // 如果有历史记录就返回，否则去首页
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    goHome()
  }
}

const goMap = () => {
  router.push('/map')
}

const goTools = () => {
  router.push('/tools')
}

const goDashboard = () => {
  router.push('/dashboard')
}

const contactSupport = () => {
  showInfo('技术支持: support@oge.example.com')
}
</script>

<style lang="scss" scoped>
.not-found-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.not-found-container {
  text-align: center;
  max-width: 600px;
  width: 100%;
  z-index: 10;
  position: relative;
}

.error-animation {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 40px;
  
  .error-number {
    font-size: 150px;
    font-weight: bold;
    color: rgba(255, 255, 255, 0.9);
    text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    animation: bounce 2s infinite;
    
    &:first-child {
      animation-delay: 0s;
    }
    
    &:last-child {
      animation-delay: 0.4s;
    }
  }
  
  .error-icon {
    margin: 0 20px;
    color: rgba(255, 255, 255, 0.8);
    animation: wobble 3s infinite;
  }
}

.error-content {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  
  h1 {
    color: #303133;
    font-size: 32px;
    margin: 0 0 16px 0;
    font-weight: 300;
  }
  
  p {
    color: #606266;
    font-size: 16px;
    line-height: 1.6;
    margin: 0 0 12px 0;
    
    &.error-detail {
      font-size: 14px;
      color: #909399;
      margin-bottom: 30px;
    }
  }
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  margin-bottom: 30px;
}

.help-links {
  text-align: left;
  
  h3 {
    color: #303133;
    font-size: 18px;
    margin: 0 0 16px 0;
    font-weight: 500;
  }
  
  ul {
    list-style: none;
    padding: 0;
    margin: 0;
    
    li {
      margin-bottom: 8px;
      
      .el-link {
        font-size: 14px;
      }
    }
  }
}

.background-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.floating-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 6s ease-in-out infinite;
  
  &.shape-1 {
    width: 80px;
    height: 80px;
    top: 10%;
    left: 10%;
    animation-delay: 0s;
  }
  
  &.shape-2 {
    width: 120px;
    height: 120px;
    top: 20%;
    right: 15%;
    animation-delay: 1s;
  }
  
  &.shape-3 {
    width: 60px;
    height: 60px;
    bottom: 20%;
    left: 15%;
    animation-delay: 2s;
  }
  
  &.shape-4 {
    width: 100px;
    height: 100px;
    bottom: 15%;
    right: 10%;
    animation-delay: 3s;
  }
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

@keyframes wobble {
  0% { transform: rotate(0deg); }
  15% { transform: rotate(5deg); }
  30% { transform: rotate(-5deg); }
  45% { transform: rotate(3deg); }
  60% { transform: rotate(-3deg); }
  75% { transform: rotate(1deg); }
  100% { transform: rotate(0deg); }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  33% {
    transform: translateY(-20px) rotate(120deg);
  }
  66% {
    transform: translateY(20px) rotate(240deg);
  }
}

@media (max-width: 768px) {
  .not-found-page {
    padding: 15px;
  }
  
  .error-animation {
    .error-number {
      font-size: 100px;
    }
    
    .error-icon {
      margin: 0 10px;
      
      :deep(.el-icon) {
        font-size: 80px !important;
      }
    }
  }
  
  .error-content {
    padding: 30px 20px;
    
    h1 {
      font-size: 24px;
    }
  }
  
  .action-buttons {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
  
  .floating-shape {
    display: none; // 在小屏幕上隐藏装饰元素
  }
}
</style> 