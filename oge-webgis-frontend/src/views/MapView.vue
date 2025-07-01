<template>
  <div class="map-view">
    <!-- 顶部导航栏 -->
    <div class="top-navbar">
      <div class="navbar-left">
        <div class="logo">
          <img src="/oge-logo.svg" alt="OGE" class="logo-img">
          <span class="logo-text">OGE</span>
        </div>
        
        <el-menu 
          mode="horizontal" 
          :default-active="activeMenu"
          class="navbar-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="map">地图分析</el-menu-item>
          <el-menu-item index="tools">工具箱</el-menu-item>
          <el-menu-item index="data">数据管理</el-menu-item>
          <el-menu-item index="task">任务中心</el-menu-item>
        </el-menu>
      </div>
      
      <div class="navbar-right">
        <!-- 环境状态指示器 -->
        <el-tooltip content="检查环境状态" placement="bottom">
          <el-button 
            :type="environmentStatus.healthy ? 'success' : 'danger'"
            :icon="environmentStatus.healthy ? 'Check' : 'Warning'"
            circle
            size="small"
            @click="checkEnvironment"
            :loading="environmentStatus.checking"
          />
        </el-tooltip>
        
        <!-- 用户信息 -->
        <el-dropdown v-if="user.isLoggedIn" trigger="click">
          <span class="user-dropdown">
            <el-avatar :size="32" :src="user.avatar">
              {{ user.username?.charAt(0).toUpperCase() }}
            </el-avatar>
            <span class="username">{{ user.username }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="$router.push('/dashboard')">
                <el-icon><User /></el-icon>
                个人中心
              </el-dropdown-item>
              <el-dropdown-item @click="$router.push('/settings')">
                <el-icon><Setting /></el-icon>
                设置
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        
        <el-button v-else type="primary" @click="$router.push('/login')">
          登录
        </el-button>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧面板 -->
      <div class="left-panel" :class="{ 'collapsed': leftPanelCollapsed }">
        <div class="panel-header">
          <h3 v-show="!leftPanelCollapsed">图层与工具</h3>
          <el-button 
            :icon="leftPanelCollapsed ? 'Expand' : 'Fold'"
            text
            @click="leftPanelCollapsed = !leftPanelCollapsed"
          />
        </div>
        
        <div class="panel-content" v-show="!leftPanelCollapsed">
          <!-- 图层控制 -->
          <LayerPanel @layer-toggle="handleLayerToggle" />
          
          <!-- MCP工具栏 -->
          <McpToolBar @tool-execute="handleToolExecute" />
        </div>
      </div>

      <!-- 地图容器 -->
      <div class="map-container">
        <div id="map" ref="mapContainer"></div>
        
        <!-- 地图工具栏 -->
        <div class="map-toolbar">
          <el-button-group>
            <el-tooltip content="放大" placement="top">
              <el-button :icon="'ZoomIn'" @click="zoomIn" />
            </el-tooltip>
            <el-tooltip content="缩小" placement="top">
              <el-button :icon="'ZoomOut'" @click="zoomOut" />
            </el-tooltip>
            <el-tooltip content="适合范围" placement="top">
              <el-button :icon="'FullScreen'" @click="fitBounds" />
            </el-tooltip>
            <el-tooltip content="定位" placement="top">
              <el-button :icon="'Location'" @click="locateUser" />
            </el-tooltip>
          </el-button-group>
        </div>
        
        <!-- 地图信息显示 -->
        <div class="map-info">
          <div class="coordinates">
            经度: {{ currentCoords.lng?.toFixed(6) }} | 
            纬度: {{ currentCoords.lat?.toFixed(6) }}
          </div>
          <div class="zoom-level">
            缩放级别: {{ currentZoom }}
          </div>
        </div>
      </div>

      <!-- 右侧面板（智能助手） -->
      <div class="right-panel" :class="{ 'collapsed': rightPanelCollapsed }">
        <div class="panel-header">
          <h3 v-show="!rightPanelCollapsed">OGE智能助手</h3>
          <el-button 
            :icon="rightPanelCollapsed ? 'Expand' : 'Fold'"
            text
            @click="rightPanelCollapsed = !rightPanelCollapsed"
          />
        </div>
        
        <div class="panel-content" v-show="!rightPanelCollapsed">
          <ChatBox @message-send="handleChatMessage" />
        </div>
      </div>
    </div>

    <!-- 任务状态弹窗 -->
    <el-dialog 
      v-model="taskDialog.visible"
      :title="taskDialog.title"
      width="600px"
      destroy-on-close
    >
      <TaskProgress 
        v-if="taskDialog.visible"
        :task-id="taskDialog.taskId"
        @task-complete="handleTaskComplete"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { mcpService, showSuccess, showError } from '@/services/api'
import mapboxgl from 'mapbox-gl'

// 导入组件
import LayerPanel from '@/components/LayerPanel.vue'
import McpToolBar from '@/components/McpToolBar.vue'
import ChatBox from '@/components/ChatBox.vue'
import TaskProgress from '@/components/TaskProgress.vue'

const router = useRouter()
const appStore = useAppStore()

// 响应式数据
const mapContainer = ref(null)
const map = ref(null)
const activeMenu = ref('map')
const leftPanelCollapsed = ref(false)
const rightPanelCollapsed = ref(false)

// 环境状态
const environmentStatus = reactive({
  healthy: false,
  checking: false,
  lastCheck: null
})

// 地图状态
const currentCoords = reactive({
  lng: 116.3974,
  lat: 39.9093
})
const currentZoom = ref(10)

// 任务对话框
const taskDialog = reactive({
  visible: false,
  title: '',
  taskId: null
})

// 用户信息
const { user, config } = appStore

// 生命周期钩子
onMounted(async () => {
  await nextTick()
  initMap()
  checkEnvironment()
})

onUnmounted(() => {
  if (map.value) {
    map.value.remove()
  }
})

// 初始化地图
const initMap = () => {
  try {
    // 设置 Mapbox access token
    mapboxgl.accessToken = config.mapbox.accessToken

    // 创建地图实例
    map.value = new mapboxgl.Map({
      container: mapContainer.value,
      style: config.mapbox.style,
      center: config.mapbox.center,
      zoom: config.mapbox.zoom,
      attributionControl: false
    })

    // 添加控件
    map.value.addControl(new mapboxgl.NavigationControl(), 'top-right')
    map.value.addControl(new mapboxgl.ScaleControl(), 'bottom-left')

    // 地图事件监听
    map.value.on('load', () => {
      console.log('🗺️ 地图加载完成')
      showSuccess('地图初始化成功')
    })

    map.value.on('mousemove', (e) => {
      currentCoords.lng = e.lngLat.lng
      currentCoords.lat = e.lngLat.lat
    })

    map.value.on('zoom', () => {
      currentZoom.value = Math.round(map.value.getZoom())
    })

    map.value.on('click', (e) => {
      console.log('地图点击:', e.lngLat)
      // 这里可以添加点击处理逻辑
    })

    // 右键菜单
    map.value.on('contextmenu', (e) => {
      e.preventDefault()
      showContextMenu(e.lngLat)
    })

  } catch (error) {
    console.error('地图初始化失败:', error)
    showError('地图初始化失败，请检查网络连接')
  }
}

// 检查环境状态
const checkEnvironment = async () => {
  environmentStatus.checking = true
  
  try {
    const result = await mcpService.checkEnvironment()
    environmentStatus.healthy = result.all_services_healthy || false
    environmentStatus.lastCheck = new Date()
    
    if (environmentStatus.healthy) {
      showSuccess('环境检查通过，所有服务运行正常')
    } else {
      showError('环境检查发现问题，部分服务可能不可用')
    }
  } catch (error) {
    console.error('环境检查失败:', error)
    environmentStatus.healthy = false
    showError('环境检查失败，请检查MCP服务状态')
  } finally {
    environmentStatus.checking = false
  }
}

// 菜单选择处理
const handleMenuSelect = (key) => {
  activeMenu.value = key
  
  switch (key) {
    case 'map':
      // 当前页面
      break
    case 'tools':
      router.push('/tools')
      break
    case 'data':
      router.push('/data')
      break
    case 'task':
      router.push('/task')
      break
  }
}

// 图层切换处理
const handleLayerToggle = (layerId, visible) => {
  console.log('图层切换:', layerId, visible)
  
  if (map.value.getLayer(layerId)) {
    map.value.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none')
  }
}

// 工具执行处理
const handleToolExecute = async (toolName, params) => {
  console.log('执行工具:', toolName, params)
  
  try {
    let result
    
    switch (toolName) {
      case 'slope_analysis':
        result = await mcpService.slopeAnalysis(params)
        break
      case 'buffer_analysis':
        result = await mcpService.bufferAnalysis(params)
        break
      case 'farmland_outflow':
        result = await mcpService.farmlandOutflow(params)
        break
      case 'road_extraction':
        result = await mcpService.roadExtraction(params)
        break
      default:
        throw new Error(`未知工具: ${toolName}`)
    }
    
    // 显示任务进度对话框
    if (result.task_id) {
      taskDialog.taskId = result.task_id
      taskDialog.title = `执行${toolName}`
      taskDialog.visible = true
    }
    
    // 如果有直接结果，添加到地图
    if (result.geojson) {
      addResultToMap(result.geojson, toolName)
    }
    
    showSuccess(`${toolName} 执行成功`)
  } catch (error) {
    console.error('工具执行失败:', error)
    showError(`${toolName} 执行失败: ${error.message}`)
  }
}

// 添加结果到地图
const addResultToMap = (geojson, layerName) => {
  const sourceId = `${layerName}-${Date.now()}`
  const layerId = `${layerName}-layer-${Date.now()}`
  
  // 添加数据源
  map.value.addSource(sourceId, {
    type: 'geojson',
    data: geojson
  })
  
  // 添加图层
  map.value.addLayer({
    id: layerId,
    type: 'fill',
    source: sourceId,
    paint: {
      'fill-color': '#ff0000',
      'fill-opacity': 0.5,
      'fill-outline-color': '#000000'
    }
  })
  
  // 适配到结果范围
  const bbox = turf.bbox(geojson)
  map.value.fitBounds(bbox, { padding: 50 })
  
  // 保存图层信息
  appStore.addLayer({
    id: layerId,
    name: layerName,
    type: 'result',
    sourceId,
    visible: true
  })
}

// 聊天消息处理
const handleChatMessage = async (message) => {
  console.log('用户消息:', message)
  // ChatBox组件会处理AI响应
}

// 任务完成处理
const handleTaskComplete = (taskResult) => {
  console.log('任务完成:', taskResult)
  
  if (taskResult.geojson) {
    addResultToMap(taskResult.geojson, taskResult.tool_name)
  }
  
  taskDialog.visible = false
  showSuccess('任务执行完成')
}

// 地图操作
const zoomIn = () => {
  map.value.zoomIn()
}

const zoomOut = () => {
  map.value.zoomOut()
}

const fitBounds = () => {
  map.value.fitBounds([
    [73.66, 3.86],   // 中国西南角
    [135.05, 53.55]  // 中国东北角
  ])
}

const locateUser = () => {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { longitude, latitude } = position.coords
        map.value.flyTo({
          center: [longitude, latitude],
          zoom: 15
        })
        showSuccess('定位成功')
      },
      (error) => {
        console.error('定位失败:', error)
        showError('定位失败，请检查位置权限')
      }
    )
  } else {
    showError('浏览器不支持地理定位')
  }
}

// 右键菜单
const showContextMenu = (lngLat) => {
  // 这里可以实现右键菜单功能
  console.log('右键点击:', lngLat)
}

// 退出登录
const handleLogout = () => {
  appStore.logout()
  router.push('/login')
}
</script>

<style lang="scss" scoped>
.map-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.top-navbar {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  z-index: 1000;
  
  .navbar-left {
    display: flex;
    align-items: center;
    
    .logo {
      display: flex;
      align-items: center;
      margin-right: 30px;
      
      .logo-img {
        width: 32px;
        height: 32px;
        margin-right: 8px;
      }
      
      .logo-text {
        font-size: 20px;
        font-weight: bold;
        color: #409eff;
      }
    }
    
    .navbar-menu {
      border: none;
      
      :deep(.el-menu-item) {
        border-bottom: none;
        
        &:hover {
          background-color: #ecf5ff;
        }
        
        &.is-active {
          color: #409eff;
          background-color: #ecf5ff;
        }
      }
    }
  }
  
  .navbar-right {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .user-dropdown {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 4px;
      transition: background-color 0.3s;
      
      &:hover {
        background-color: #f5f7fa;
      }
      
      .username {
        font-size: 14px;
        color: #606266;
      }
    }
  }
}

.main-content {
  flex: 1;
  display: flex;
  height: calc(100vh - 60px);
}

.left-panel, .right-panel {
  background: #fff;
  border-right: 1px solid #e4e7ed;
  transition: width 0.3s ease;
  
  &.collapsed {
    width: 50px;
    
    .panel-content {
      display: none;
    }
  }
  
  .panel-header {
    height: 50px;
    border-bottom: 1px solid #e4e7ed;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 16px;
    
    h3 {
      margin: 0;
      font-size: 14px;
      color: #303133;
    }
  }
  
  .panel-content {
    height: calc(100% - 50px);
    overflow-y: auto;
  }
}

.left-panel {
  width: 320px;
}

.right-panel {
  width: 400px;
  border-right: none;
  border-left: 1px solid #e4e7ed;
}

.map-container {
  flex: 1;
  position: relative;
  
  #map {
    width: 100%;
    height: 100%;
  }
  
  .map-toolbar {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 100;
  }
  
  .map-info {
    position: absolute;
    bottom: 20px;
    left: 20px;
    background: rgba(255, 255, 255, 0.9);
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 12px;
    color: #606266;
    backdrop-filter: blur(8px);
    
    .coordinates, .zoom-level {
      margin: 2px 0;
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .left-panel {
    width: 280px;
  }
  
  .right-panel {
    width: 350px;
  }
}

@media (max-width: 768px) {
  .left-panel, .right-panel {
    position: absolute;
    top: 0;
    height: 100%;
    z-index: 200;
    
    &.collapsed {
      transform: translateX(-100%);
    }
  }
  
  .navbar-menu {
    display: none;
  }
}
</style> 