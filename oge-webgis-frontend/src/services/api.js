import axios from 'axios'
import { ElMessage, ElNotification } from 'element-plus'
import { deepseekService } from './deepseek'

// 离线模式配置
const OFFLINE_MODE = true // 启用离线模式，适合非内网环境

// AI服务配置
const AI_CONFIG = {
  provider: 'deepseek', // 可选: 'deepseek', 'mcp', 'mock'
  enableMCPTools: true   // 是否启用MCP工具调用
}

// 模拟数据
const mockData = {
  health: { status: 'ok', message: '模拟服务运行正常' },
  environment: { 
    status: 'offline', 
    message: '需要内网环境连接遥感大楼服务器',
    services: {
      mcp: 'offline',
      oge: 'offline', 
      minio: 'offline'
    }
  },
  taskHistory: [
    { id: 1, name: '坡度分析示例', status: 'completed', time: '2024-01-15 14:30:00' },
    { id: 2, name: '缓冲区分析示例', status: 'completed', time: '2024-01-15 15:20:00' },
    { id: 3, name: '道路提取示例', status: 'running', time: '2024-01-15 16:10:00' }
  ],
  layers: [
    { id: 1, name: '底图图层', type: 'base', visible: true },
    { id: 2, name: '卫星影像', type: 'raster', visible: false },
    { id: 3, name: '道路网络', type: 'vector', visible: true },
    { id: 4, name: '行政边界', type: 'vector', visible: false }
  ]
}

// 创建 axios 实例
const createApiInstance = (baseURL, timeout = 30000) => {
  const instance = axios.create({
    baseURL,
    timeout,
    headers: {
      'Content-Type': 'application/json'
    }
  })

  // 请求拦截器
  instance.interceptors.request.use(
    (config) => {
      // 添加认证token
      const token = localStorage.getItem('oge_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      
      console.log(`🚀 发送请求: ${config.method?.toUpperCase()} ${config.url}`)
      return config
    },
    (error) => {
      console.error('请求拦截器错误:', error)
      return Promise.reject(error)
    }
  )

  // 响应拦截器
  instance.interceptors.response.use(
    (response) => {
      console.log(`✅ 请求成功: ${response.config.url}`, response.data)
      return response.data
    },
    (error) => {
      console.error(`❌ 请求失败: ${error.config?.url}`, error)
      
      // 处理不同类型的错误
      let message = '请求失败'
      
      if (error.response) {
        const { status, data } = error.response
        
        switch (status) {
          case 400:
            message = data?.message || '请求参数错误'
            break
          case 401:
            message = '认证失败，请重新登录'
            // 清除token并跳转到登录页
            localStorage.removeItem('oge_token')
            window.location.href = '/login'
            break
          case 403:
            message = '权限不足'
            break
          case 404:
            message = '服务未找到'
            break
          case 500:
            message = '服务器内部错误'
            break
          default:
            message = data?.message || `请求失败 (${status})`
        }
      } else if (error.request) {
        message = '网络连接失败，请检查网络设置'
      } else {
        message = error.message || '请求配置错误'
      }
      
      ElMessage.error(message)
      return Promise.reject(error)
    }
  )

  return instance
}

// MCP服务API
const mcpApi = createApiInstance(
  import.meta.env.DEV ? '/api/mcp' : 'http://localhost:8000'
)

// OGE服务API - 使用可用的外网穿透服务器
const ogeApi = createApiInstance(
  import.meta.env.DEV ? '/api/oge' : 'http://111.37.195.111:7002'
)

// =================== MCP服务接口 ===================

export const mcpService = {
  // 健康检查
  async health() {
    if (OFFLINE_MODE) {
      return new Promise(resolve => {
        setTimeout(() => resolve(mockData.health), 500)
      })
    }
    return await mcpApi.get('/health')
  },

  // 检查遥感大楼环境
  async checkEnvironment() {
    if (OFFLINE_MODE) {
      return new Promise(resolve => {
        setTimeout(() => resolve(mockData.environment), 800)
      })
    }
    return await mcpApi.post('/check_yaogan_environment')
  },

  // 坡度分析
  async slopeAnalysis(params) {
    if (OFFLINE_MODE) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          reject(new Error('需要连接内网MCP服务器才能使用坡度分析功能'))
        }, 1000)
      })
    }
    return await mcpApi.post('/slope_analysis', params)
  },

  // 缓冲区分析
  async bufferAnalysis(params) {
    if (OFFLINE_MODE) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          reject(new Error('需要连接内网MCP服务器才能使用缓冲区分析功能'))
        }, 1000)
      })
    }
    return await mcpApi.post('/buffer_analysis', params)
  },

  // 耕地流出分析
  async farmlandOutflow(params) {
    if (OFFLINE_MODE) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          reject(new Error('需要连接内网MCP服务器才能使用耕地流出分析功能'))
        }, 1000)
      })
    }
    return await mcpApi.post('/farmland_outflow', params)
  },

  // 道路提取
  async roadExtraction(params) {
    if (OFFLINE_MODE) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          reject(new Error('需要连接内网MCP服务器才能使用道路提取功能'))
        }, 1000)
      })
    }
    return await mcpApi.post('/road_extraction', params)
  },

  // 影像分类
  async imageClassification(params) {
    if (OFFLINE_MODE) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          reject(new Error('需要连接内网MCP服务器才能使用影像分类功能'))
        }, 1000)
      })
    }
    return await mcpApi.post('/image_classification', params)
  },

  // 植被指数计算
  async vegetationIndex(params) {
    if (OFFLINE_MODE) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          reject(new Error('需要连接内网MCP服务器才能使用植被指数计算功能'))
        }, 1000)
      })
    }
    return await mcpApi.post('/vegetation_index', params)
  },

  // 水体提取
  async waterExtraction(params) {
    if (OFFLINE_MODE) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          reject(new Error('需要连接内网MCP服务器才能使用水体提取功能'))
        }, 1000)
      })
    }
    return await mcpApi.post('/water_extraction', params)
  },

  // 获取任务状态
  async getTaskStatus(taskId) {
    if (OFFLINE_MODE) {
      return new Promise(resolve => {
        setTimeout(() => {
          const task = mockData.taskHistory.find(t => t.id === taskId)
          resolve(task || { id: taskId, status: 'not_found' })
        }, 300)
      })
    }
    return await mcpApi.get(`/task_status/${taskId}`)
  },

  // 获取任务历史
  async getTaskHistory() {
    if (OFFLINE_MODE) {
      return new Promise(resolve => {
        setTimeout(() => resolve(mockData.taskHistory), 500)
      })
    }
    return await mcpApi.get('/task_history')
  }
}

// =================== OGE服务接口 ===================

export const ogeService = {
  // 用户认证
  async login(credentials) {
    return await ogeApi.post('/auth/login', credentials)
  },

  async logout() {
    return await ogeApi.post('/auth/logout')
  },

  async refreshToken() {
    return await ogeApi.post('/auth/refresh')
  },

  // 用户信息
  async getUserInfo() {
    return await ogeApi.get('/user/info')
  },

  // 数据管理
  async getDatasets() {
    return await ogeApi.get('/datasets')
  },

  async uploadDataset(formData) {
    return await ogeApi.post('/datasets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 计算服务
  async submitJob(jobConfig) {
    return await ogeApi.post('/compute/submit', jobConfig)
  },

  async getJobStatus(jobId) {
    return await ogeApi.get(`/compute/status/${jobId}`)
  }
}

// =================== 智能助手服务 ===================

export const aiService = {
  // 聊天对话
  async chat(message, sessionId = null, conversationHistory = []) {
    if (OFFLINE_MODE) {
      return new Promise(resolve => {
        setTimeout(() => {
          // 模拟AI回复
          const responses = [
            '您好！我是OGE智能助手。由于当前处于离线模式，我无法连接到后台AI服务，但可以为您提供基本的功能指导。',
            '很抱歉，AI智能分析功能需要连接到遥感大楼的内网服务器才能正常工作。',
            '您可以尝试使用工具箱中的各种分析功能，虽然在离线模式下无法执行真实计算，但可以了解功能界面。',
            '建议您在内网环境下使用本系统，以获得完整的AI智能分析体验。',
            '如需技术支持，请联系系统管理员配置网络连接。'
          ]
          
          const randomResponse = responses[Math.floor(Math.random() * responses.length)]
          
          resolve({
            response: randomResponse,
            session_id: sessionId || 'offline-session',
            timestamp: new Date().toISOString(),
            mode: 'offline'
          })
        }, 1000 + Math.random() * 1000) // 1-2秒随机延迟
      })
    }

    // 根据配置选择AI服务提供商
    try {
      switch (AI_CONFIG.provider) {
        case 'deepseek':
          console.log('🤖 使用DeepSeek AI服务')
          return await deepseekService.chat(message, sessionId, conversationHistory)
        
        case 'mcp':
          console.log('🔧 使用MCP AI服务')
          const payload = {
            message,
            session_id: sessionId,
            timestamp: new Date().toISOString()
          }
          return await mcpApi.post('/ai/chat', payload)
        
        default:
          // 备用模拟回复
          return {
            response: '智能助手暂时不可用，请稍后重试。',
            session_id: sessionId || `fallback-${Date.now()}`,
            timestamp: new Date().toISOString(),
            mode: 'fallback'
          }
      }
    } catch (error) {
      console.error('AI服务调用失败:', error)
      
      // 如果DeepSeek失败，尝试备用MCP服务
      if (AI_CONFIG.provider === 'deepseek') {
        try {
          console.log('🔄 DeepSeek失败，尝试MCP备用服务')
          const payload = {
            message,
            session_id: sessionId,
            timestamp: new Date().toISOString()
          }
          return await mcpApi.post('/ai/chat', payload)
        } catch (mcpError) {
          console.error('MCP备用服务也失败:', mcpError)
        }
      }
      
      throw error
    }
  },

  // 获取对话历史
  async getChatHistory(sessionId) {
    if (OFFLINE_MODE) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve([
            {
              id: 1,
              message: '欢迎使用OGE平台',
              response: '您好！我是智能助手，当前为离线演示模式。',
              timestamp: new Date(Date.now() - 300000).toISOString()
            }
          ])
        }, 300)
      })
    }
    return await mcpApi.get(`/ai/history/${sessionId}`)
  },

  // 创建新会话
  async createSession() {
    if (OFFLINE_MODE) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            session_id: 'offline-session-' + Date.now(),
            created_at: new Date().toISOString(),
            mode: 'offline'
          })
        }, 200)
      })
    }
    return await mcpApi.post('/ai/session')
  },

  // 删除会话
  async deleteSession(sessionId) {
    if (OFFLINE_MODE) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({ success: true, message: '会话已删除（离线模式）' })
        }, 200)
      })
    }
    return await mcpApi.delete(`/ai/session/${sessionId}`)
  }
}

// =================== 地图数据服务 ===================

export const mapService = {
  // 获取图层配置
  async getLayers() {
    if (OFFLINE_MODE) {
      return new Promise(resolve => {
        setTimeout(() => resolve(mockData.layers), 400)
      })
    }
    return await mcpApi.get('/layers')
  },

  // 获取图层数据
  async getLayerData(layerId, params = {}) {
    if (OFFLINE_MODE) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          const layer = mockData.layers.find(l => l.id === layerId)
          if (layer) {
            resolve({ 
              layerId, 
              data: { 
                type: 'FeatureCollection', 
                features: [] 
              },
              message: '离线模式，无法加载真实数据' 
            })
          } else {
            reject(new Error('图层不存在'))
          }
        }, 600)
      })
    }
    return await mcpApi.get(`/layers/${layerId}/data`, { params })
  },

  // 地理编码
  async geocode(address) {
    if (OFFLINE_MODE) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          reject(new Error('地理编码服务需要网络连接'))
        }, 500)
      })
    }
    return await mcpApi.get('/geocode', { params: { address } })
  },

  // 逆地理编码
  async reverseGeocode(lng, lat) {
    if (OFFLINE_MODE) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          reject(new Error('逆地理编码服务需要网络连接'))
        }, 500)
      })
    }
    return await mcpApi.get('/reverse-geocode', { params: { lng, lat } })
  },

  // 获取地理统计数据
  async getGeoStats(bounds) {
    if (OFFLINE_MODE) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            area: '约 1000 平方公里',
            population: '模拟数据',
            features: 0,
            message: '离线模式，显示模拟统计信息'
          })
        }, 600)
      })
    }
    return await mcpApi.post('/geo-stats', { bounds })
  }
}

// =================== 工具函数 ===================

// 上传文件
export const uploadFile = async (file, type = 'dataset') => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('type', type)
  
  return await ogeApi.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      )
      console.log(`上传进度: ${percentCompleted}%`)
    }
  })
}

// 下载文件
export const downloadFile = async (url, filename) => {
  const response = await mcpApi.get(url, {
    responseType: 'blob'
  })
  
  const blob = new Blob([response])
  const downloadUrl = window.URL.createObjectURL(blob)
  
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  window.URL.revokeObjectURL(downloadUrl)
}

// 显示成功通知
export const showSuccess = (message, title = '操作成功') => {
  ElNotification.success({
    title,
    message,
    duration: 3000
  })
}

// 显示错误通知
export const showError = (message, title = '操作失败') => {
  ElNotification.error({
    title,
    message,
    duration: 5000
  })
}

// 显示信息通知
export const showInfo = (message, title = '提示') => {
  ElNotification.info({
    title,
    message,
    duration: 3000
  })
}

// 显示警告通知
export const showWarning = (message, title = '警告') => {
  ElNotification.warning({
    title,
    message,
    duration: 4000
  })
}

// 导出所有服务
export default {
  mcpService,
  ogeService,
  aiService,
  mapService,
  uploadFile,
  downloadFile,
  showSuccess,
  showError,
  showInfo,
  showWarning
} 