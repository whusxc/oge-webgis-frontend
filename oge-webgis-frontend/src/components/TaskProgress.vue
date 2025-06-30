<template>
  <div class="task-progress">
    <div class="progress-header">
      <h4>{{ taskInfo.name || '执行任务' }}</h4>
      <el-tag :type="getStatusType(taskInfo.status)" size="small">
        {{ getStatusText(taskInfo.status) }}
      </el-tag>
    </div>
    
    <div class="progress-content">
      <!-- 进度条 -->
      <el-progress 
        :percentage="taskInfo.progress" 
        :status="getProgressStatus(taskInfo.status)"
        :show-text="true"
        :stroke-width="8"
      />
      
      <!-- 当前步骤 -->
      <div class="current-step" v-if="taskInfo.currentStep">
        <el-icon class="step-icon"><Loading /></el-icon>
        <span>{{ taskInfo.currentStep }}</span>
      </div>
      
      <!-- 详细信息 -->
      <div class="task-details">
        <div class="detail-item">
          <span class="label">任务ID:</span>
          <span class="value">{{ taskId }}</span>
        </div>
        <div class="detail-item">
          <span class="label">开始时间:</span>
          <span class="value">{{ formatTime(taskInfo.startTime) }}</span>
        </div>
        <div class="detail-item" v-if="taskInfo.estimatedTime">
          <span class="label">预估时间:</span>
          <span class="value">{{ taskInfo.estimatedTime }}秒</span>
        </div>
        <div class="detail-item" v-if="taskInfo.endTime">
          <span class="label">完成时间:</span>
          <span class="value">{{ formatTime(taskInfo.endTime) }}</span>
        </div>
      </div>
      
      <!-- 结果预览 -->
      <div v-if="taskInfo.status === 'completed' && taskInfo.result" class="task-result">
        <h5>执行结果</h5>
        
        <!-- 成功结果 -->
        <div v-if="taskInfo.result.success" class="result-success">
          <el-alert
            title="任务执行成功"
            :description="taskInfo.result.message"
            type="success"
            show-icon
            :closable="false"
          />
          
          <!-- 结果统计 -->
          <div v-if="taskInfo.result.statistics" class="result-stats">
            <div class="stat-item" v-for="(value, key) in taskInfo.result.statistics" :key="key">
              <span class="stat-label">{{ key }}:</span>
              <span class="stat-value">{{ value }}</span>
            </div>
          </div>
          
          <!-- 下载链接 -->
          <div v-if="taskInfo.result.downloadUrl" class="result-download">
            <el-button 
              type="primary" 
              @click="downloadResult"
              :icon="'Download'"
            >
              下载结果
            </el-button>
          </div>
        </div>
        
        <!-- 失败结果 -->
        <div v-else class="result-error">
          <el-alert
            title="任务执行失败"
            :description="taskInfo.result.error"
            type="error"
            show-icon
            :closable="false"
          />
        </div>
      </div>
      
      <!-- 日志信息 -->
      <div v-if="taskInfo.logs && taskInfo.logs.length > 0" class="task-logs">
        <h5>
          执行日志
          <el-button size="small" text @click="showLogs = !showLogs">
            {{ showLogs ? '隐藏' : '显示' }}
          </el-button>
        </h5>
        
        <div v-show="showLogs" class="log-content">
          <div 
            v-for="(log, index) in taskInfo.logs" 
            :key="index"
            class="log-item"
            :class="log.level"
          >
            <span class="log-time">{{ formatTime(log.timestamp) }}</span>
            <span class="log-level">{{ log.level.toUpperCase() }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="progress-actions">
      <el-button 
        v-if="taskInfo.status === 'running'"
        @click="cancelTask"
        type="danger"
        :icon="'Close'"
      >
        取消任务
      </el-button>
      
      <el-button 
        v-if="taskInfo.status === 'completed'"
        @click="handleComplete"
        type="primary"
        :icon="'Check'"
      >
        确认完成
      </el-button>
      
      <el-button 
        v-if="taskInfo.status === 'failed'"
        @click="retryTask"
        type="warning"
        :icon="'Refresh'"
      >
        重新执行
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { mcpService, showSuccess, showError } from '@/services/api'

const props = defineProps({
  taskId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['task-complete', 'task-cancel', 'task-retry'])

// 响应式数据
const taskInfo = reactive({
  id: props.taskId,
  name: '',
  status: 'pending', // pending, running, completed, failed, cancelled
  progress: 0,
  currentStep: '',
  startTime: null,
  endTime: null,
  estimatedTime: null,
  result: null,
  logs: []
})

const showLogs = ref(false)
const polling = ref(null)

// 生命周期
onMounted(() => {
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

// 开始轮询任务状态
const startPolling = () => {
  // 立即获取一次状态
  fetchTaskStatus()
  
  // 每秒轮询一次
  polling.value = setInterval(() => {
    if (taskInfo.status === 'running' || taskInfo.status === 'pending') {
      fetchTaskStatus()
    } else {
      stopPolling()
    }
  }, 1000)
}

// 停止轮询
const stopPolling = () => {
  if (polling.value) {
    clearInterval(polling.value)
    polling.value = null
  }
}

// 获取任务状态
const fetchTaskStatus = async () => {
  try {
    const status = await mcpService.getTaskStatus(props.taskId)
    
    // 更新任务信息
    Object.assign(taskInfo, {
      name: status.task_name || taskInfo.name,
      status: status.status || 'pending',
      progress: status.progress || 0,
      currentStep: status.current_step || '',
      startTime: status.start_time || taskInfo.startTime,
      endTime: status.end_time || null,
      estimatedTime: status.estimated_time || null,
      result: status.result || null,
      logs: status.logs || []
    })
    
    // 如果任务完成，触发完成事件
    if (status.status === 'completed' && status.result) {
      setTimeout(() => {
        emit('task-complete', status.result)
      }, 2000) // 延迟2秒让用户看到完成状态
    }
    
  } catch (error) {
    console.error('获取任务状态失败:', error)
    taskInfo.status = 'failed'
    taskInfo.result = {
      success: false,
      error: '无法获取任务状态'
    }
  }
}

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    pending: '等待中',
    running: '执行中',
    completed: '已完成',
    failed: '执行失败',
    cancelled: '已取消'
  }
  return textMap[status] || '未知状态'
}

// 获取进度条状态
const getProgressStatus = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return null
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

// 下载结果
const downloadResult = () => {
  if (taskInfo.result?.downloadUrl) {
    window.open(taskInfo.result.downloadUrl, '_blank')
    showSuccess('开始下载结果文件')
  }
}

// 取消任务
const cancelTask = async () => {
  try {
    await mcpService.cancelTask(props.taskId)
    taskInfo.status = 'cancelled'
    stopPolling()
    emit('task-cancel')
    showSuccess('任务已取消')
  } catch (error) {
    console.error('取消任务失败:', error)
    showError('取消任务失败')
  }
}

// 处理完成
const handleComplete = () => {
  emit('task-complete', taskInfo.result)
}

// 重试任务
const retryTask = () => {
  emit('task-retry', props.taskId)
}
</script>

<style lang="scss" scoped>
.task-progress {
  padding: 20px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h4 {
    margin: 0;
    color: #303133;
  }
}

.progress-content {
  .current-step {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 16px 0;
    color: #606266;
    font-size: 14px;
    
    .step-icon {
      animation: rotate 2s linear infinite;
    }
  }
  
  .task-details {
    margin: 20px 0;
    padding: 16px;
    background: #f5f7fa;
    border-radius: 6px;
    
    .detail-item {
      display: flex;
      margin-bottom: 8px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .label {
        width: 80px;
        color: #909399;
        font-size: 13px;
      }
      
      .value {
        flex: 1;
        color: #606266;
        font-size: 13px;
        font-family: 'Monaco', 'Consolas', monospace;
      }
    }
  }
  
  .task-result {
    margin: 20px 0;
    
    h5 {
      margin: 0 0 12px 0;
      color: #303133;
    }
    
    .result-stats {
      margin: 12px 0;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 8px;
      
      .stat-item {
        padding: 8px 12px;
        background: #f8f9fa;
        border-radius: 4px;
        font-size: 13px;
        
        .stat-label {
          color: #909399;
          margin-right: 8px;
        }
        
        .stat-value {
          color: #303133;
          font-weight: 500;
        }
      }
    }
    
    .result-download {
      margin-top: 12px;
    }
  }
  
  .task-logs {
    margin: 20px 0;
    
    h5 {
      margin: 0 0 12px 0;
      color: #303133;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .log-content {
      max-height: 200px;
      overflow-y: auto;
      background: #2d3748;
      border-radius: 6px;
      padding: 12px;
      
      .log-item {
        display: flex;
        gap: 12px;
        margin-bottom: 6px;
        font-size: 12px;
        font-family: 'Monaco', 'Consolas', monospace;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .log-time {
          color: #718096;
          white-space: nowrap;
        }
        
        .log-level {
          width: 50px;
          text-align: center;
          font-weight: bold;
        }
        
        .log-message {
          flex: 1;
          color: #e2e8f0;
        }
        
        &.info .log-level { color: #63b3ed; }
        &.warn .log-level { color: #f6ad55; }
        &.error .log-level { color: #f56565; }
        &.debug .log-level { color: #9f7aea; }
      }
    }
  }
}

.progress-actions {
  margin-top: 20px;
  text-align: center;
  
  .el-button {
    margin: 0 8px;
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style> 