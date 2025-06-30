<template>
  <div class="dashboard-page">
    <div class="dashboard-header">
      <h1>OGE 控制台</h1>
      <p>系统状态和统计信息</p>
    </div>
    
    <div class="dashboard-grid">
      <!-- 系统状态卡片 -->
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6" v-for="stat in systemStats" :key="stat.key">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" :style="{ backgroundColor: stat.color + '20', color: stat.color }">
                <el-icon><component :is="stat.icon" /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ stat.value }}</h3>
                <p>{{ stat.label }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 服务状态 -->
      <el-row :gutter="20" class="mt-20">
        <el-col :xs="24" :lg="12">
          <el-card class="service-card">
            <template #header>
              <h3>服务状态</h3>
            </template>
            <div class="service-list">
              <div 
                v-for="service in services" 
                :key="service.name"
                class="service-item"
              >
                <div class="service-info">
                  <h4>{{ service.name }}</h4>
                  <p>{{ service.description }}</p>
                </div>
                <el-tag 
                  :type="service.status === 'online' ? 'success' : 'danger'"
                  effect="dark"
                >
                  {{ service.status === 'online' ? '在线' : '离线' }}
                </el-tag>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :lg="12">
          <el-card class="activity-card">
            <template #header>
              <h3>最近活动</h3>
            </template>
            <el-timeline>
              <el-timeline-item
                v-for="activity in recentActivities"
                :key="activity.id"
                :timestamp="activity.time"
                :type="activity.type"
              >
                {{ activity.description }}
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 快速操作 -->
      <el-row :gutter="20" class="mt-20">
        <el-col :span="24">
          <el-card class="quick-actions">
            <template #header>
              <h3>快速操作</h3>
            </template>
            <div class="action-buttons">
              <el-button 
                v-for="action in quickActions"
                :key="action.key"
                :type="action.type"
                :icon="action.icon"
                @click="handleQuickAction(action.key)"
                size="large"
              >
                {{ action.label }}
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { showSuccess, showWarning } from '@/services/api'

const router = useRouter()
const appStore = useAppStore()

// 系统统计数据
const systemStats = ref([
  {
    key: 'tasks',
    label: '处理任务',
    value: '156',
    icon: 'DataAnalysis',
    color: '#409EFF'
  },
  {
    key: 'layers',
    label: '图层数量',
    value: '24',
    icon: 'MapLocation',
    color: '#67C23A'
  },
  {
    key: 'storage',
    label: '存储使用',
    value: '2.3TB',
    icon: 'FolderOpened',
    color: '#E6A23C'
  },
  {
    key: 'users',
    label: '在线用户',
    value: '8',
    icon: 'User',
    color: '#F56C6C'
  }
])

// 服务状态
const services = ref([
  {
    name: 'MCP服务器',
    description: '模型-控制-处理服务',
    status: 'offline' // 因为内网问题设为离线
  },
  {
    name: 'OGE计算集群',
    description: '地理空间计算服务',
    status: 'offline' // 因为内网问题设为离线
  },
  {
    name: 'MinIO存储',
    description: '对象存储服务',
    status: 'offline' // 因为内网问题设为离线
  },
  {
    name: '前端应用',
    description: 'WebGIS用户界面',
    status: 'online'
  }
])

// 最近活动
const recentActivities = ref([
  {
    id: 1,
    description: '启动前端应用',
    time: new Date().toLocaleString(),
    type: 'success'
  },
  {
    id: 2,
    description: '检测到网络连接问题',
    time: new Date(Date.now() - 60000).toLocaleString(),
    type: 'warning'
  },
  {
    id: 3,
    description: '系统初始化完成',
    time: new Date(Date.now() - 120000).toLocaleString(),
    type: 'success'
  }
])

// 快速操作
const quickActions = ref([
  {
    key: 'map',
    label: '打开地图',
    type: 'primary',
    icon: 'MapLocation'
  },
  {
    key: 'tools',
    label: '工具箱',
    type: 'success',
    icon: 'Tools'
  },
  {
    key: 'settings',
    label: '系统设置',
    type: 'info',
    icon: 'Setting'
  },
  {
    key: 'help',
    label: '帮助文档',
    type: 'warning',
    icon: 'QuestionFilled'
  }
])

const handleQuickAction = (actionKey) => {
  switch (actionKey) {
    case 'map':
      router.push('/map')
      break
    case 'tools':
      router.push('/tools')
      break
    case 'settings':
      showWarning('设置功能开发中...')
      break
    case 'help':
      showSuccess('帮助文档即将推出')
      break
  }
}

onMounted(() => {
  // 模拟数据更新
  const updateStats = () => {
    systemStats.value.forEach(stat => {
      if (stat.key === 'tasks') {
        stat.value = (parseInt(stat.value) + Math.floor(Math.random() * 5)).toString()
      }
    })
  }
  
  setInterval(updateStats, 30000) // 30秒更新一次
})
</script>

<style lang="scss" scoped>
.dashboard-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.dashboard-header {
  margin-bottom: 30px;
  text-align: center;
  
  h1 {
    color: #303133;
    margin: 0 0 8px 0;
    font-size: 28px;
    font-weight: 300;
  }
  
  p {
    color: #909399;
    margin: 0;
    font-size: 16px;
  }
}

.dashboard-grid {
  max-width: 1200px;
  margin: 0 auto;
}

.stat-card {
  margin-bottom: 20px;
  
  :deep(.el-card__body) {
    padding: 20px;
  }
}

.stat-content {
  display: flex;
  align-items: center;
  
  .stat-icon {
    width: 50px;
    height: 50px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 15px;
    font-size: 24px;
  }
  
  .stat-info {
    h3 {
      margin: 0 0 4px 0;
      font-size: 24px;
      font-weight: bold;
      color: #303133;
    }
    
    p {
      margin: 0;
      color: #909399;
      font-size: 14px;
    }
  }
}

.service-card, .activity-card, .quick-actions {
  :deep(.el-card__header) {
    padding: 18px 20px;
    border-bottom: 1px solid #ebeef5;
    
    h3 {
      margin: 0;
      color: #303133;
      font-size: 16px;
      font-weight: 500;
    }
  }
}

.service-list {
  .service-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #f0f2f6;
    
    &:last-child {
      border-bottom: none;
    }
    
    .service-info {
      h4 {
        margin: 0 0 4px 0;
        color: #303133;
        font-size: 14px;
        font-weight: 500;
      }
      
      p {
        margin: 0;
        color: #909399;
        font-size: 12px;
      }
    }
  }
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.mt-20 {
  margin-top: 20px;
}

@media (max-width: 768px) {
  .dashboard-page {
    padding: 15px;
  }
  
  .action-buttons {
    .el-button {
      flex: 1;
      min-width: calc(50% - 6px);
    }
  }
}
</style> 