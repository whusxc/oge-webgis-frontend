<template>
  <div class="modern-map-view">
    <!-- 现代化顶部导航栏 -->
    <header class="top-header">
      <div class="header-left">
        <div class="brand-section">
          <div class="brand-logo">
            <div class="logo-icon">🌍</div>
            <span class="brand-name">OGE</span>
          </div>
          <div class="brand-tagline">智能地理分析平台</div>
        </div>
        
        <nav class="main-navigation">
          <button 
            v-for="tab in navigationTabs" 
            :key="tab.id"
            :class="['nav-tab', { active: activeTab === tab.id }]"
            @click="setActiveTab(tab.id)"
          >
            <span class="tab-icon">{{ tab.icon }}</span>
            <span class="tab-label">{{ tab.label }}</span>
          </button>
        </nav>
      </div>
      
      <div class="header-right">
        <div class="header-controls">
          <!-- 系统状态 -->
          <div class="status-indicator" :class="systemStatus.type">
            <div class="status-dot"></div>
            <span class="status-text">{{ systemStatus.text }}</span>
          </div>
          
          <!-- 快捷操作 -->
          <div class="quick-actions">
            <button class="action-btn" @click="toggleFullscreen" title="全屏模式">
              <span>⛶</span>
            </button>
            <button class="action-btn" @click="showSettings" title="设置">
              <span>⚙️</span>
            </button>
          </div>
          
          <!-- 用户区域 -->
          <div class="user-section">
            <div class="user-avatar" @click="showUserMenu">
              <span>{{ userInitial }}</span>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- 主内容区域 -->
    <main class="main-content">
      <!-- 左侧工具面板 -->
      <aside class="left-sidebar" :class="{ collapsed: leftSidebarCollapsed }">
        <div class="sidebar-header">
          <h3 v-show="!leftSidebarCollapsed">{{ leftPanelTitle }}</h3>
          <button 
            class="collapse-btn"
            @click="toggleLeftSidebar"
            :title="leftSidebarCollapsed ? '展开面板' : '收起面板'"
          >
            <span>{{ leftSidebarCollapsed ? '▶' : '◀' }}</span>
          </button>
        </div>
        
        <div class="sidebar-content" v-show="!leftSidebarCollapsed">
          <!-- 工具选项卡 -->
          <div class="tool-tabs">
            <button 
              v-for="tool in toolTabs"
              :key="tool.id"
              :class="['tool-tab', { active: activeTool === tool.id }]"
              @click="setActiveTool(tool.id)"
            >
              <span class="tool-icon">{{ tool.icon }}</span>
              <span class="tool-label">{{ tool.label }}</span>
            </button>
          </div>
          
          <!-- 工具内容 -->
          <div class="tool-content">
            <component :is="currentToolComponent" />
          </div>
        </div>
      </aside>

      <!-- 地图容器 -->
      <section class="map-section">
        <div class="map-container" ref="mapContainer">
          <!-- 地图工具栏 -->
          <div class="map-toolbar">
            <div class="toolbar-group">
              <button class="map-tool-btn" @click="zoomIn" title="放大">
                <span>🔍</span>
              </button>
              <button class="map-tool-btn" @click="zoomOut" title="缩小">
                <span>🔍</span>
              </button>
              <button class="map-tool-btn" @click="fitBounds" title="适合视图">
                <span>⌂</span>
              </button>
            </div>
            
            <div class="toolbar-group">
              <button class="map-tool-btn" @click="toggleMeasure" title="测量工具">
                <span>📏</span>
              </button>
              <button class="map-tool-btn" @click="toggleDraw" title="绘制工具">
                <span>✏️</span>
              </button>
            </div>
          </div>
          
          <!-- 地图信息面板 -->
          <div class="map-info-panel">
            <div class="coordinate-display">
              <span class="coord-label">坐标:</span>
              <span class="coord-value">
                {{ currentCoords.lng?.toFixed(6) }}, {{ currentCoords.lat?.toFixed(6) }}
              </span>
            </div>
            <div class="zoom-display">
              <span class="zoom-label">缩放:</span>
              <span class="zoom-value">{{ currentZoom }}</span>
            </div>
          </div>
          
          <!-- 地图加载状态 -->
          <div v-if="mapLoading" class="map-loading">
            <div class="loading-spinner"></div>
            <p>正在加载地图...</p>
          </div>
          
          <!-- 离线模式提示 -->
          <div class="offline-notice">
            <div class="notice-content">
              <span class="notice-icon">📱</span>
              <span class="notice-text">离线演示模式</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 右侧AI助手面板 -->
      <aside class="right-sidebar" :class="{ collapsed: rightSidebarCollapsed }">
        <div class="sidebar-header">
          <div class="ai-header" v-show="!rightSidebarCollapsed">
            <div class="ai-avatar">🤖</div>
            <div class="ai-info">
              <h3>OGE智能助手</h3>
              <p class="ai-status">{{ aiStatus }}</p>
            </div>
          </div>
          <button 
            class="collapse-btn"
            @click="toggleRightSidebar"
            :title="rightSidebarCollapsed ? '展开AI助手' : '收起AI助手'"
          >
            <span>{{ rightSidebarCollapsed ? '◀' : '▶' }}</span>
          </button>
        </div>
        
        <div class="sidebar-content" v-show="!rightSidebarCollapsed">
          <ChatInterface />
        </div>
      </aside>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'

// 组件导入（简化版本）
const LayerTools = { template: '<div class="layer-tools"><h4>🗺️ 图层管理</h4><p>图层控制功能</p></div>' }
const AnalysisTools = { template: '<div class="analysis-tools"><h4>📊 空间分析</h4><p>分析工具集合</p></div>' }
const DataTools = { template: '<div class="data-tools"><h4>💾 数据管理</h4><p>数据导入导出</p></div>' }
const ChatInterface = { template: '<div class="chat-interface"><div class="chat-messages"><div class="message ai-message">您好！我是OGE智能助手，很高兴为您服务！</div></div><div class="chat-input"><input placeholder="请输入您的问题..." /><button>发送</button></div></div>' }

const router = useRouter()
const appStore = useAppStore()

// 响应式数据
const leftSidebarCollapsed = ref(false)
const rightSidebarCollapsed = ref(false)
const activeTab = ref('map')
const activeTool = ref('layers')
const mapLoading = ref(false)

// 导航标签页
const navigationTabs = [
  { id: 'map', label: '地图分析', icon: '🗺️' },
  { id: 'tools', label: '工具箱', icon: '🛠️' },
  { id: 'data', label: '数据中心', icon: '💾' },
  { id: 'reports', label: '分析报告', icon: '📋' }
]

// 工具标签页
const toolTabs = [
  { id: 'layers', label: '图层', icon: '🗂️' },
  { id: 'analysis', label: '分析', icon: '📊' },
  { id: 'data', label: '数据', icon: '💾' }
]

// 当前坐标和缩放
const currentCoords = reactive({ lng: 116.3974, lat: 39.9093 })
const currentZoom = ref(10)

// 计算属性
const leftPanelTitle = computed(() => {
  const tool = toolTabs.find(t => t.id === activeTool.value)
  return tool ? `${tool.icon} ${tool.label}` : '工具面板'
})

const currentToolComponent = computed(() => {
  switch (activeTool.value) {
    case 'layers': return LayerTools
    case 'analysis': return AnalysisTools
    case 'data': return DataTools
    default: return LayerTools
  }
})

const systemStatus = computed(() => {
  return appStore.config?.system?.offlineMode 
    ? { type: 'offline', text: '离线模式' }
    : { type: 'online', text: '在线模式' }
})

const aiStatus = computed(() => {
  return appStore.config?.system?.offlineMode ? '离线演示' : '智能分析中'
})

const userInitial = computed(() => {
  return appStore.user?.username?.charAt(0).toUpperCase() || 'G'
})

// 方法
const setActiveTab = (tabId) => {
  activeTab.value = tabId
  if (tabId !== 'map') {
    router.push(`/${tabId}`)
  }
}

const setActiveTool = (toolId) => {
  activeTool.value = toolId
}

const toggleLeftSidebar = () => {
  leftSidebarCollapsed.value = !leftSidebarCollapsed.value
}

const toggleRightSidebar = () => {
  rightSidebarCollapsed.value = !rightSidebarCollapsed.value
}

const zoomIn = () => {
  currentZoom.value = Math.min(currentZoom.value + 1, 20)
}

const zoomOut = () => {
  currentZoom.value = Math.max(currentZoom.value - 1, 1)
}

const fitBounds = () => {
  console.log('适合视图')
}

const toggleMeasure = () => {
  console.log('测量工具')
}

const toggleDraw = () => {
  console.log('绘制工具')
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

const showSettings = () => {
  console.log('显示设置')
}

const showUserMenu = () => {
  console.log('显示用户菜单')
}

onMounted(() => {
  console.log('🗺️ 现代化地图界面已加载')
})
</script>

<style lang="scss" scoped>
.modern-map-view {
  height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
  background: var(--surface-alt);
  overflow: hidden;
}

// 顶部导航栏
.top-header {
  height: 64px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
  box-shadow: var(--shadow);
  z-index: 100;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 2rem;
    
    .brand-section {
      display: flex;
      align-items: center;
      gap: 1rem;
      
      .brand-logo {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        
        .logo-icon {
          width: 32px;
          height: 32px;
          background: linear-gradient(135deg, var(--primary), var(--secondary));
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.2rem;
        }
        
        .brand-name {
          font-size: 1.25rem;
          font-weight: 700;
          color: var(--text-primary);
          letter-spacing: -0.02em;
        }
      }
      
      .brand-tagline {
        font-size: 0.875rem;
        color: var(--text-secondary);
        font-weight: 500;
      }
    }
    
    .main-navigation {
      display: flex;
      gap: 0.5rem;
      
      .nav-tab {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border: none;
        background: transparent;
        border-radius: var(--radius);
        cursor: pointer;
        transition: var(--transition);
        font-weight: 500;
        color: var(--text-secondary);
        
        &:hover {
          background: var(--surface-alt);
          color: var(--text-primary);
        }
        
        &.active {
          background: var(--primary);
          color: white;
        }
        
        .tab-icon {
          font-size: 1rem;
        }
      }
    }
  }
  
  .header-right {
    .header-controls {
      display: flex;
      align-items: center;
      gap: 1rem;
      
      .status-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.375rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        
        &.online {
          background: rgba(16, 185, 129, 0.1);
          color: var(--secondary);
          
          .status-dot {
            background: var(--secondary);
          }
        }
        
        &.offline {
          background: rgba(245, 158, 11, 0.1);
          color: var(--accent);
          
          .status-dot {
            background: var(--accent);
          }
        }
      }
      
      .quick-actions {
        display: flex;
        gap: 0.25rem;
        
        .action-btn {
          width: 36px;
          height: 36px;
          border: none;
          background: transparent;
          border-radius: 8px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: var(--transition);
          
          &:hover {
            background: var(--surface-alt);
          }
        }
      }
      
      .user-section {
        .user-avatar {
          width: 36px;
          height: 36px;
          background: linear-gradient(135deg, var(--primary), var(--secondary));
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 600;
          cursor: pointer;
          transition: var(--transition);
          
          &:hover {
            transform: scale(1.05);
          }
        }
      }
    }
  }
}

// 主内容区域
.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  
  // 侧边栏通用样式
  .left-sidebar,
  .right-sidebar {
    background: var(--surface);
    border-right: 1px solid var(--border);
    transition: var(--transition);
    overflow: hidden;
    
    .sidebar-header {
      height: 56px;
      padding: 1rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      
      h3 {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
      }
      
      .collapse-btn {
        width: 24px;
        height: 24px;
        border: none;
        background: var(--surface-alt);
        border-radius: 4px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: var(--transition);
        
        &:hover {
          background: var(--border);
        }
      }
    }
    
    .sidebar-content {
      height: calc(100% - 56px);
      overflow-y: auto;
    }
    
    &.collapsed {
      width: 48px !important;
    }
  }
  
  .left-sidebar {
    width: 320px;
    
    .tool-tabs {
      display: flex;
      padding: 0.5rem;
      gap: 0.25rem;
      border-bottom: 1px solid var(--border);
      
      .tool-tab {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.25rem;
        padding: 0.75rem 0.5rem;
        border: none;
        background: transparent;
        border-radius: 8px;
        cursor: pointer;
        transition: var(--transition);
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--text-secondary);
        
        &:hover {
          background: var(--surface-alt);
        }
        
        &.active {
          background: var(--primary);
          color: white;
        }
        
        .tool-icon {
          font-size: 1.25rem;
        }
      }
    }
    
    .tool-content {
      padding: 1rem;
    }
  }
  
  .right-sidebar {
    width: 320px;
    border-right: none;
    border-left: 1px solid var(--border);
    
    .ai-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      
      .ai-avatar {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, var(--secondary), var(--primary));
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
      }
      
      .ai-info {
        h3 {
          font-size: 0.875rem;
          margin-bottom: 0.125rem;
        }
        
        .ai-status {
          font-size: 0.75rem;
          color: var(--text-secondary);
          margin: 0;
        }
      }
    }
  }
}

// 地图区域
.map-section {
  flex: 1;
  position: relative;
  
  .map-container {
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    
    &::before {
      content: '🗺️';
      font-size: 4rem;
      opacity: 0.3;
    }
  }
  
  .map-toolbar {
    position: absolute;
    top: 1rem;
    right: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    z-index: 10;
    
    .toolbar-group {
      background: var(--surface);
      border-radius: 8px;
      padding: 0.25rem;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      
      .map-tool-btn {
        width: 36px;
        height: 36px;
        border: none;
        background: transparent;
        border-radius: 6px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: var(--transition);
        
        &:hover {
          background: var(--surface-alt);
        }
      }
    }
  }
  
  .map-info-panel {
    position: absolute;
    bottom: 1rem;
    left: 1rem;
    background: var(--surface);
    padding: 0.75rem 1rem;
    border-radius: 8px;
    box-shadow: var(--shadow);
    display: flex;
    gap: 1rem;
    font-size: 0.875rem;
    
    .coord-label,
    .zoom-label {
      color: var(--text-secondary);
      font-weight: 500;
    }
    
    .coord-value,
    .zoom-value {
      color: var(--text-primary);
      font-family: 'Monaco', monospace;
    }
  }
  
  .offline-notice {
    position: absolute;
    top: 1rem;
    left: 1rem;
    z-index: 10;
    
    .notice-content {
      background: rgba(245, 158, 11, 0.1);
      border: 1px solid rgba(245, 158, 11, 0.3);
      padding: 0.5rem 1rem;
      border-radius: 20px;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.875rem;
      color: var(--accent);
      font-weight: 500;
    }
  }
  
  .map-loading {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    color: var(--text-secondary);
    
    .loading-spinner {
      width: 32px;
      height: 32px;
      border: 3px solid var(--border);
      border-top: 3px solid var(--primary);
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin: 0 auto 1rem;
    }
  }
}

// 工具组件样式
:deep(.layer-tools),
:deep(.analysis-tools),
:deep(.data-tools) {
  h4 {
    color: var(--text-primary);
    margin-bottom: 1rem;
    font-size: 1rem;
    font-weight: 600;
  }
  
  p {
    color: var(--text-secondary);
    font-size: 0.875rem;
  }
}

// AI聊天界面
:deep(.chat-interface) {
  height: 100%;
  display: flex;
  flex-direction: column;
  
  .chat-messages {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
    
    .message {
      margin-bottom: 1rem;
      padding: 0.75rem;
      border-radius: 12px;
      font-size: 0.875rem;
      line-height: 1.5;
      
      &.ai-message {
        background: var(--surface-alt);
        color: var(--text-primary);
      }
    }
  }
  
  .chat-input {
    padding: 1rem;
    border-top: 1px solid var(--border);
    display: flex;
    gap: 0.5rem;
    
    input {
      flex: 1;
      padding: 0.5rem 0.75rem;
      border: 1px solid var(--border);
      border-radius: 20px;
      font-size: 0.875rem;
      outline: none;
      
      &:focus {
        border-color: var(--primary);
      }
    }
    
    button {
      padding: 0.5rem 1rem;
      background: var(--primary);
      color: white;
      border: none;
      border-radius: 20px;
      font-size: 0.875rem;
      font-weight: 500;
      cursor: pointer;
      transition: var(--transition);
      
      &:hover {
        background: var(--primary-dark);
      }
    }
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style> 