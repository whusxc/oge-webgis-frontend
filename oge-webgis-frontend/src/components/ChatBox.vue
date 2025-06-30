<template>
  <div class="chat-box">
    <!-- 头部 -->
    <div class="chat-header">
      <div class="header-info">
        <el-icon class="assistant-icon"><ChatDotRound /></el-icon>
        <div>
          <h4>GA+智能助手</h4>
          <span class="status online">在线</span>
        </div>
      </div>
      <el-button size="small" text @click="clearChat">
        <el-icon><Delete /></el-icon>
      </el-button>
    </div>
    
    <!-- 消息区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0" class="welcome-message">
        <el-icon size="48" color="#409eff"><Robot /></el-icon>
        <h3>您好！我是GA+智能助手</h3>
        <p>我可以帮助您进行地理分析、数据查询和问题解答</p>
        
        <div class="quick-actions">
          <el-button 
            v-for="action in quickActions" 
            :key="action.id"
            size="small" 
            @click="sendQuickMessage(action.message)"
          >
            {{ action.label }}
          </el-button>
        </div>
      </div>
      
      <!-- 消息列表 -->
      <div 
        v-for="(message, index) in messages" 
        :key="index"
        class="message-item"
        :class="{ 'user-message': message.type === 'user' }"
      >
        <div class="message-avatar">
          <el-avatar v-if="message.type === 'user'" :size="32">
            {{ username?.charAt(0).toUpperCase() }}
          </el-avatar>
          <el-icon v-else size="32" class="ai-avatar"><Robot /></el-icon>
        </div>
        
        <div class="message-content">
          <div class="message-header">
            <span class="sender">{{ message.type === 'user' ? username || '用户' : 'GA+助手' }}</span>
            <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
          </div>
          
          <div class="message-body">
            {{ message.content }}
          </div>
          
          <!-- AI消息操作 -->
          <div v-if="message.type === 'ai'" class="message-actions">
            <el-button size="small" text @click="copyMessage(message.content)">
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
          </div>
        </div>
      </div>
      
      <!-- 正在输入 -->
      <div v-if="isTyping" class="typing-indicator">
        <div class="message-avatar">
          <el-icon size="32" class="ai-avatar"><Robot /></el-icon>
        </div>
        <div class="typing-content">
          <div class="typing-dots">
            <span></span><span></span><span></span>
          </div>
          <span class="typing-text">正在思考...</span>
        </div>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="chat-input">
      <div class="input-area">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          placeholder="输入您的问题..."
          @keydown.enter.prevent="handleEnterKey"
          @keydown.ctrl.enter="sendMessage"
          :disabled="isTyping"
          resize="none"
        />
        
        <div class="input-actions">
          <span class="char-count">{{ inputMessage.length }}/2000</span>
          <el-button 
            type="primary" 
            @click="sendMessage"
            :loading="isTyping"
            :disabled="!canSend"
            size="small"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { useAppStore } from '@/stores/app'
import { aiService, showSuccess, showError } from '@/services/api'

const emit = defineEmits(['message-send'])
const appStore = useAppStore()

// 响应式数据
const inputMessage = ref('')
const messages = ref([])
const isTyping = ref(false)
const messagesContainer = ref(null)
const sessionId = ref(null)

// 用户信息
const { user } = appStore
const username = computed(() => user.username)

// 快速操作
const quickActions = reactive([
  { id: 'analysis', label: '地理分析', message: '我想进行地理分析，有哪些工具可以使用？' },
  { id: 'data', label: '数据查询', message: '帮我查询北京市的数据' },
  { id: 'tutorial', label: '使用教程', message: '如何使用OGE-GA+平台？' },
  { id: 'examples', label: '示例案例', message: '给我展示一些分析案例' }
])

// 计算属性
const canSend = computed(() => {
  return inputMessage.value.trim().length > 0 && 
         inputMessage.value.length <= 2000 && 
         !isTyping.value
})

// 生命周期
onMounted(async () => {
  await createSession()
})

// 监听消息变化
watch(messages, () => {
  nextTick(() => scrollToBottom())
}, { deep: true })

// 创建会话
const createSession = async () => {
  try {
    const result = await aiService.createSession()
    sessionId.value = result.session_id
  } catch (error) {
    console.error('创建AI会话失败:', error)
  }
}

// 发送消息
const sendMessage = async () => {
  if (!canSend.value) return
  
  const message = inputMessage.value.trim()
  
  // 添加用户消息
  addMessage({
    type: 'user',
    content: message,
    timestamp: new Date().toISOString()
  })
  
  inputMessage.value = ''
  isTyping.value = true
  
  try {
    // 模拟AI响应
    setTimeout(() => {
      const responses = [
        '我理解您的需求。OGE-GA+平台提供了多种地理分析工具，包括坡度分析、缓冲区分析、耕地流出分析等。',
        '根据您的问题，我建议您使用坡度分析工具。这个工具可以帮助您分析地形的坡度信息。',
        '北京市面积约16410平方公里，人口约2188万人。您还需要了解其他数据吗？',
        '很高兴为您介绍OGE-GA+平台的使用方法。首先，您可以从左侧的工具面板选择分析工具...',
        '这里有几个典型的地理分析案例：1.城市热岛效应分析 2.农业用地变化监测 3.水体污染评估'
      ]
      
      const randomResponse = responses[Math.floor(Math.random() * responses.length)]
      
      addMessage({
        type: 'ai',
        content: randomResponse,
        timestamp: new Date().toISOString()
      })
      
      isTyping.value = false
    }, 1000 + Math.random() * 2000)
    
    emit('message-send', message)
    
  } catch (error) {
    console.error('AI响应失败:', error)
    addMessage({
      type: 'ai',
      content: '抱歉，AI助手暂时无法响应，请稍后重试。',
      timestamp: new Date().toISOString()
    })
    isTyping.value = false
  }
}

// 添加消息
const addMessage = (message) => {
  messages.value.push(message)
}

// 处理Enter键
const handleEnterKey = (event) => {
  if (event.ctrlKey) {
    sendMessage()
  }
}

// 发送快速消息
const sendQuickMessage = (message) => {
  inputMessage.value = message
  sendMessage()
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 复制消息
const copyMessage = async (content) => {
  try {
    await navigator.clipboard.writeText(content)
    showSuccess('已复制到剪贴板')
  } catch (error) {
    showError('复制失败')
  }
}

// 清空对话
const clearChat = () => {
  messages.value = []
  showSuccess('对话已清空')
}
</script>

<style lang="scss" scoped>
.chat-box {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.chat-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .header-info {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .assistant-icon {
      font-size: 24px;
      color: #409eff;
    }
    
    h4 {
      margin: 0 0 2px 0;
      font-size: 16px;
      color: #303133;
    }
    
    .status {
      font-size: 12px;
      
      &.online {
        color: #67c23a;
      }
    }
  }
}

.chat-messages {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  
  .welcome-message {
    text-align: center;
    padding: 40px 20px;
    color: #606266;
    
    h3 {
      margin: 16px 0 8px 0;
      color: #303133;
    }
    
    p {
      margin-bottom: 24px;
      line-height: 1.6;
    }
    
    .quick-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: center;
    }
  }
  
  .message-item {
    display: flex;
    margin-bottom: 20px;
    align-items: flex-start;
    
    &.user-message {
      flex-direction: row-reverse;
      
      .message-content {
        margin-right: 12px;
        margin-left: 0;
        
        .message-body {
          background: #409eff;
          color: white;
        }
      }
    }
    
    .message-content {
      margin-left: 12px;
      
      .message-body {
        background: #f5f7fa;
        color: #303133;
      }
    }
  }
  
  .message-avatar {
    flex-shrink: 0;
    
    .ai-avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: #409eff;
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
  
  .message-content {
    flex: 1;
    max-width: calc(100% - 50px);
    
    .message-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 6px;
      
      .sender {
        font-size: 13px;
        font-weight: 500;
        color: #606266;
      }
      
      .timestamp {
        font-size: 12px;
        color: #c0c4cc;
      }
    }
    
    .message-body {
      padding: 12px 16px;
      border-radius: 12px;
      line-height: 1.6;
      word-wrap: break-word;
    }
    
    .message-actions {
      margin-top: 8px;
    }
  }
  
  .typing-indicator {
    display: flex;
    align-items: flex-start;
    
    .typing-content {
      margin-left: 12px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      
      .typing-dots {
        display: flex;
        gap: 4px;
        
        span {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #c0c4cc;
          animation: typing 1.4s infinite ease-in-out;
          
          &:nth-child(1) { animation-delay: -0.32s; }
          &:nth-child(2) { animation-delay: -0.16s; }
        }
      }
      
      .typing-text {
        font-size: 12px;
        color: #909399;
      }
    }
  }
}

.chat-input {
  border-top: 1px solid #e4e7ed;
  padding: 16px;
  
  .input-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 8px;
    
    .char-count {
      font-size: 12px;
      color: #909399;
    }
  }
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
</style> 