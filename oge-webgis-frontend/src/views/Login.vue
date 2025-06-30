<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <img src="/oge-logo.svg" alt="OGE" class="logo" />
        <h1>OGE 平台</h1>
        <p>智能地理分析系统</p>
      </div>
      
      <el-card class="login-card">
        <el-form 
          ref="loginForm" 
          :model="form" 
          :rules="rules" 
          label-position="top"
          @submit.prevent="handleLogin"
        >
          <el-form-item label="用户名" prop="username">
            <el-input 
              v-model="form.username" 
              placeholder="请输入用户名"
              :prefix-icon="'User'"
              size="large"
            />
          </el-form-item>
          
          <el-form-item label="密码" prop="password">
            <el-input 
              v-model="form.password" 
              type="password" 
              placeholder="请输入密码"
              :prefix-icon="'Lock'"
              size="large"
              show-password
            />
          </el-form-item>
          
          <el-form-item>
            <el-checkbox v-model="form.remember">记住我</el-checkbox>
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              @click="handleLogin"
              :loading="loading"
              size="large"
              style="width: 100%"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="login-footer">
          <p>演示账号: admin / 123456</p>
          <p>访客模式: <el-button text type="primary" @click="guestLogin">直接进入</el-button></p>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { showSuccess, showError } from '@/services/api'

const router = useRouter()
const appStore = useAppStore()

const loginForm = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  remember: false
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginForm.value) return
  
  try {
    await loginForm.value.validate()
    loading.value = true
    
    // 模拟登录验证
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    if (form.username === 'admin' && form.password === '123456') {
      // 登录成功
      appStore.user.username = form.username
      appStore.user.isLoggedIn = true
      appStore.user.token = 'mock-token-' + Date.now()
      
      if (form.remember) {
        localStorage.setItem('oge_token', appStore.user.token)
        localStorage.setItem('oge_username', form.username)
      }
      
      showSuccess('登录成功')
      router.push('/map')
      
    } else {
      showError('用户名或密码错误')
    }
    
  } catch (error) {
    console.error('登录失败:', error)
  } finally {
    loading.value = false
  }
}

const guestLogin = () => {
  appStore.user.username = '访客用户'
  appStore.user.isLoggedIn = true
  showSuccess('以访客身份进入')
  router.push('/map')
}
</script>

<style lang="scss" scoped>
.login-page {
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-container {
  text-align: center;
  max-width: 400px;
  width: 100%;
}

.login-header {
  margin-bottom: 30px;
  color: white;
  
  .logo {
    width: 80px;
    height: 80px;
    margin-bottom: 20px;
  }
  
  h1 {
    font-size: 28px;
    margin: 0 0 8px 0;
    font-weight: 300;
  }
  
  p {
    margin: 0;
    opacity: 0.9;
    font-size: 16px;
  }
}

.login-card {
  :deep(.el-card__body) {
    padding: 40px;
  }
}

.login-footer {
  margin-top: 20px;
  text-align: center;
  color: #909399;
  font-size: 14px;
  
  p {
    margin: 8px 0;
  }
}

@media (max-width: 480px) {
  .login-card {
    :deep(.el-card__body) {
      padding: 30px 20px;
    }
  }
}
</style> 