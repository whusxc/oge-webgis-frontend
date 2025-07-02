import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 应用状态
  const loading = ref(false)
  const initialized = ref(false)
  
  // 用户信息
  const user = reactive({
    id: null,
    username: '',
    token: '',
    isLoggedIn: false
  })
  
  // 应用配置
  const config = reactive({
    // 系统状态
    system: {
      offlineMode: true, // 当前为离线模式
      networkStatus: 'offline',
      lastConnectAttempt: null
    },
    
    // Mapbox 配置
    mapbox: {
      accessToken: 'pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw',
      style: 'mapbox://styles/mapbox/streets-v11',
      center: [116.3974, 39.9093], // 北京坐标
      zoom: 10
    },
    
    // MCP服务配置（需要内网）
    mcp: {
      baseUrl: import.meta.env.DEV ? '/api/mcp' : 'http://localhost:8000',
      timeout: 30000,
      connected: false,
      lastHealthCheck: null
    },
    
    // OGE服务配置（使用可用的外网穿透服务器）
    oge: {
      baseUrl: import.meta.env.DEV ? '/api/oge' : 'http://111.37.195.111:7002',
      timeout: 30000,
      connected: false,
      lastHealthCheck: null
    },
    
    // 智能助手配置
    ai: {
      enabled: true,
      model: 'offline-demo',
      apiUrl: '/api/ai/chat',
      maxTokens: 2000,
      offlineMode: true
    }
  })
  
  // 地图状态
  const mapState = reactive({
    center: [116.3974, 39.9093],
    zoom: 10,
    bearing: 0,
    pitch: 0,
    layers: [],
    activeLayers: [],
    currentTask: null
  })
  
  // 工具状态
  const toolState = reactive({
    activeTools: [],
    taskHistory: [],
    currentSession: null
  })
  
  // 初始化应用
  const initApp = async () => {
    try {
      console.log('📱 开始初始化应用状态...')
      setLoading(true)
      
      // 检查用户登录状态
      console.log('🔐 检查认证状态...')
      await checkAuthStatus()
      
      // 设置默认配置（不调用可能失败的API）
      console.log('⚙️ 加载应用配置...')
      config.system.offlineMode = true
      config.system.networkStatus = 'offline'
      config.system.lastConnectAttempt = new Date()
      
      // 初始化完成
      initialized.value = true
      
      console.log('🎉 OGE 应用初始化完成')
    } catch (error) {
      console.error('应用初始化失败:', error)
      throw error // 重新抛出错误让上层处理
    } finally {
      setLoading(false)
    }
  }
  
  // 检查认证状态
  const checkAuthStatus = async () => {
    const token = localStorage.getItem('oge_token')
    const username = localStorage.getItem('oge_username')
    
    if (token) {
      user.token = token
      user.username = username || ''
      user.isLoggedIn = true
      
      // 这里可以添加token验证逻辑
      try {
        // await validateToken(token)
        console.log('用户已登录:', user.username)
      } catch (error) {
        console.warn('Token验证失败，清除本地认证信息')
        logout()
      }
    }
  }
  
  // 登录
  const login = (userData) => {
    user.id = userData.id
    user.username = userData.username
    user.token = userData.token
    user.isLoggedIn = true
    
    // 保存到本地存储
    localStorage.setItem('oge_token', userData.token)
    localStorage.setItem('oge_username', userData.username)
    localStorage.setItem('oge_user_id', userData.id)
    
    console.log('用户登录成功:', user.username)
  }
  
  // 登出
  const logout = () => {
    user.id = null
    user.username = ''
    user.token = ''
    user.isLoggedIn = false
    
    // 清除本地存储
    localStorage.removeItem('oge_token')
    localStorage.removeItem('oge_username')
    localStorage.removeItem('oge_user_id')
    
    console.log('用户已登出')
  }
  
  // 加载应用配置
  const loadAppConfig = async () => {
    try {
      // 这里可以从服务器加载配置
      // const response = await fetch('/api/config')
      // const serverConfig = await response.json()
      // Object.assign(config, serverConfig)
      
      console.log('应用配置加载完成')
    } catch (error) {
      console.warn('加载应用配置失败，使用默认配置:', error)
    }
  }
  
  // 设置加载状态
  const setLoading = (status) => {
    loading.value = status
  }
  
  // 更新地图状态
  const updateMapState = (newState) => {
    Object.assign(mapState, newState)
  }
  
  // 添加地图图层
  const addLayer = (layer) => {
    const existingIndex = mapState.layers.findIndex(l => l.id === layer.id)
    if (existingIndex >= 0) {
      mapState.layers[existingIndex] = layer
    } else {
      mapState.layers.push(layer)
    }
  }
  
  // 移除地图图层
  const removeLayer = (layerId) => {
    const index = mapState.layers.findIndex(l => l.id === layerId)
    if (index >= 0) {
      mapState.layers.splice(index, 1)
    }
    
    // 从激活图层中移除
    const activeIndex = mapState.activeLayers.indexOf(layerId)
    if (activeIndex >= 0) {
      mapState.activeLayers.splice(activeIndex, 1)
    }
  }
  
  // 切换图层显示
  const toggleLayer = (layerId) => {
    const index = mapState.activeLayers.indexOf(layerId)
    if (index >= 0) {
      mapState.activeLayers.splice(index, 1)
    } else {
      mapState.activeLayers.push(layerId)
    }
  }
  
  // 添加任务历史
  const addTaskHistory = (task) => {
    toolState.taskHistory.unshift({
      ...task,
      id: Date.now(),
      timestamp: new Date().toISOString()
    })
    
    // 限制历史记录数量
    if (toolState.taskHistory.length > 100) {
      toolState.taskHistory = toolState.taskHistory.slice(0, 100)
    }
  }
  
  return {
    // 状态
    loading,
    initialized,
    user,
    config,
    mapState,
    toolState,
    
    // 方法
    initApp,
    checkAuthStatus,
    login,
    logout,
    loadAppConfig,
    setLoading,
    updateMapState,
    addLayer,
    removeLayer,
    toggleLayer,
    addTaskHistory
  }
}) 