<template>
  <div class="layer-panel">
    <div class="section-header">
      <h4>
        <el-icon><MapLocation /></el-icon>
        地图图层
      </h4>
      <el-button 
        size="small" 
        text 
        @click="refreshLayers"
        :loading="loading"
        :icon="'Refresh'"
      >
        刷新
      </el-button>
    </div>
    
    <!-- 基础底图 -->
    <div class="layer-group">
      <div class="group-title">
        <el-icon><Picture /></el-icon>
        底图样式
      </div>
      <div class="layer-list">
        <div 
          v-for="basemap in basemaps" 
          :key="basemap.id"
          class="layer-item basemap-item"
          :class="{ active: currentBasemap === basemap.id }"
          @click="changeBasemap(basemap.id)"
        >
          <div class="layer-preview">
            <img :src="basemap.thumbnail" :alt="basemap.name" />
          </div>
          <div class="layer-info">
            <span class="layer-name">{{ basemap.name }}</span>
            <span class="layer-desc">{{ basemap.description }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 数据图层 -->
    <div class="layer-group">
      <div class="group-title">
        <el-icon><Files /></el-icon>
        数据图层
        <el-button 
          size="small" 
          type="primary" 
          text 
          @click="showAddLayerDialog = true"
          :icon="'Plus'"
        >
          添加
        </el-button>
      </div>
      
      <div class="layer-list" v-if="dataLayers.length > 0">
        <div 
          v-for="layer in dataLayers" 
          :key="layer.id"
          class="layer-item"
          :class="{ disabled: !layer.visible }"
        >
          <div class="layer-checkbox">
            <el-checkbox 
              v-model="layer.visible"
              @change="toggleLayer(layer.id, layer.visible)"
            />
          </div>
          
          <div class="layer-info">
            <div class="layer-main">
              <span class="layer-name">{{ layer.name }}</span>
              <span class="layer-type">{{ layer.type }}</span>
            </div>
            <div class="layer-meta">
              <span class="layer-source">{{ layer.source }}</span>
              <span class="layer-time" v-if="layer.updateTime">
                {{ formatTime(layer.updateTime) }}
              </span>
            </div>
          </div>
          
          <div class="layer-actions">
            <el-dropdown trigger="click" placement="bottom-end">
              <el-icon class="action-icon"><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="zoomToLayer(layer)">
                    <el-icon><ZoomIn /></el-icon>
                    缩放到图层
                  </el-dropdown-item>
                  <el-dropdown-item @click="showLayerInfo(layer)">
                    <el-icon><InfoFilled /></el-icon>
                    图层信息
                  </el-dropdown-item>
                  <el-dropdown-item @click="adjustOpacity(layer)">
                    <el-icon><View /></el-icon>
                    透明度
                  </el-dropdown-item>
                  <el-dropdown-item 
                    @click="removeLayer(layer.id)"
                    class="danger-item"
                  >
                    <el-icon><Delete /></el-icon>
                    移除图层
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
      
      <div v-else class="empty-state">
        <el-empty 
          description="暂无数据图层" 
          :image-size="80"
        >
          <el-button type="primary" @click="showAddLayerDialog = true">
            添加第一个图层
          </el-button>
        </el-empty>
      </div>
    </div>
    
    <!-- 分析结果图层 -->
    <div class="layer-group" v-if="resultLayers.length > 0">
      <div class="group-title">
        <el-icon><TrendCharts /></el-icon>
        分析结果
        <el-button 
          size="small" 
          text 
          @click="clearAllResults"
          :icon="'Delete'"
        >
          清空
        </el-button>
      </div>
      
      <div class="layer-list">
        <div 
          v-for="layer in resultLayers" 
          :key="layer.id"
          class="layer-item result-item"
          :class="{ disabled: !layer.visible }"
        >
          <div class="layer-checkbox">
            <el-checkbox 
              v-model="layer.visible"
              @change="toggleLayer(layer.id, layer.visible)"
            />
          </div>
          
          <div class="layer-info">
            <div class="layer-main">
              <span class="layer-name">{{ layer.name }}</span>
              <el-tag :type="getResultType(layer.toolName)" size="small">
                {{ layer.toolName }}
              </el-tag>
            </div>
            <div class="layer-meta">
              <span class="layer-time">{{ formatTime(layer.createTime) }}</span>
            </div>
          </div>
          
          <div class="layer-actions">
            <el-button 
              size="small" 
              text 
              @click="downloadResult(layer)"
              :icon="'Download'"
            />
            <el-button 
              size="small" 
              text 
              type="danger"
              @click="removeLayer(layer.id)"
              :icon="'Delete'"
            />
          </div>
        </div>
      </div>
    </div>
    
    <!-- 添加图层对话框 -->
    <el-dialog 
      v-model="showAddLayerDialog"
      title="添加图层"
      width="500px"
      destroy-on-close
    >
      <AddLayerForm @layer-added="handleLayerAdded" />
    </el-dialog>
    
    <!-- 图层信息对话框 -->
    <el-dialog 
      v-model="showLayerInfoDialog"
      :title="selectedLayer?.name"
      width="600px"
      destroy-on-close
    >
      <LayerInfo v-if="selectedLayer" :layer="selectedLayer" />
    </el-dialog>
    
    <!-- 透明度调节对话框 -->
    <el-dialog 
      v-model="showOpacityDialog"
      title="调整透明度"
      width="400px"
      destroy-on-close
    >
      <div class="opacity-control">
        <div class="opacity-label">
          透明度: {{ Math.round(currentOpacity * 100) }}%
        </div>
        <el-slider 
          v-model="currentOpacity"
          :min="0"
          :max="1"
          :step="0.1"
          @change="updateLayerOpacity"
          show-stops
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { mapService, showSuccess, showError } from '@/services/api'
import { ElMessageBox } from 'element-plus'

// 导入子组件
import AddLayerForm from './AddLayerForm.vue'
import LayerInfo from './LayerInfo.vue'

const emit = defineEmits(['layer-toggle'])
const appStore = useAppStore()

// 响应式数据
const loading = ref(false)
const showAddLayerDialog = ref(false)
const showLayerInfoDialog = ref(false)
const showOpacityDialog = ref(false)
const selectedLayer = ref(null)
const currentOpacity = ref(1)
const currentBasemap = ref('streets-v11')

// 底图配置
const basemaps = reactive([
  {
    id: 'streets-v11',
    name: '标准地图',
    description: '包含道路、建筑等详细信息',
    style: 'mapbox://styles/mapbox/streets-v11',
    thumbnail: '/images/basemap-streets.jpg'
  },
  {
    id: 'satellite-v9',
    name: '卫星影像',
    description: '高分辨率卫星图像',
    style: 'mapbox://styles/mapbox/satellite-v9',
    thumbnail: '/images/basemap-satellite.jpg'
  },
  {
    id: 'outdoors-v11',
    name: '户外地图',
    description: '适合户外活动的地形图',
    style: 'mapbox://styles/mapbox/outdoors-v11',
    thumbnail: '/images/basemap-outdoors.jpg'
  },
  {
    id: 'light-v10',
    name: '浅色模式',
    description: '简洁的浅色主题地图',
    style: 'mapbox://styles/mapbox/light-v10',
    thumbnail: '/images/basemap-light.jpg'
  },
  {
    id: 'dark-v10',
    name: '深色模式',
    description: '适合夜间使用的深色主题',
    style: 'mapbox://styles/mapbox/dark-v10',
    thumbnail: '/images/basemap-dark.jpg'
  }
])

// 计算属性
const dataLayers = computed(() => 
  appStore.mapState.layers.filter(layer => layer.type === 'data')
)

const resultLayers = computed(() => 
  appStore.mapState.layers.filter(layer => layer.type === 'result')
)

// 生命周期
onMounted(() => {
  refreshLayers()
})

// 刷新图层列表
const refreshLayers = async () => {
  loading.value = true
  try {
    const layers = await mapService.getLayers()
    console.log('获取图层列表:', layers)
    // 这里可以处理从服务器获取的图层配置
  } catch (error) {
    console.error('获取图层列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 切换底图
const changeBasemap = (basemapId) => {
  currentBasemap.value = basemapId
  const basemap = basemaps.find(b => b.id === basemapId)
  if (basemap) {
    // 这里需要向父组件发送底图切换事件
    console.log('切换底图:', basemap.style)
    showSuccess(`已切换到${basemap.name}`)
  }
}

// 切换图层显示
const toggleLayer = (layerId, visible) => {
  console.log('切换图层:', layerId, visible)
  emit('layer-toggle', layerId, visible)
  appStore.toggleLayer(layerId)
}

// 缩放到图层
const zoomToLayer = (layer) => {
  console.log('缩放到图层:', layer.name)
  // 这里需要根据图层边界进行缩放
  showSuccess(`正在缩放到${layer.name}`)
}

// 显示图层信息
const showLayerInfo = (layer) => {
  selectedLayer.value = layer
  showLayerInfoDialog.value = true
}

// 调整透明度
const adjustOpacity = (layer) => {
  selectedLayer.value = layer
  currentOpacity.value = layer.opacity || 1
  showOpacityDialog.value = true
}

// 更新图层透明度
const updateLayerOpacity = (opacity) => {
  if (selectedLayer.value) {
    selectedLayer.value.opacity = opacity
    console.log('更新图层透明度:', selectedLayer.value.id, opacity)
    // 这里需要向地图发送透明度更新事件
  }
}

// 移除图层
const removeLayer = async (layerId) => {
  try {
    await ElMessageBox.confirm(
      '确定要移除这个图层吗？',
      '确认删除',
      {
        type: 'warning'
      }
    )
    
    appStore.removeLayer(layerId)
    emit('layer-toggle', layerId, false)
    showSuccess('图层已移除')
  } catch {
    // 用户取消删除
  }
}

// 清空所有结果图层
const clearAllResults = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有分析结果吗？',
      '确认清空',
      {
        type: 'warning'
      }
    )
    
    resultLayers.value.forEach(layer => {
      appStore.removeLayer(layer.id)
      emit('layer-toggle', layer.id, false)
    })
    
    showSuccess('已清空所有分析结果')
  } catch {
    // 用户取消操作
  }
}

// 下载结果
const downloadResult = (layer) => {
  console.log('下载结果:', layer.name)
  // 这里实现结果下载逻辑
  showSuccess(`正在下载${layer.name}`)
}

// 获取结果类型标签类型
const getResultType = (toolName) => {
  const typeMap = {
    'slope_analysis': 'warning',
    'buffer_analysis': 'info',
    'farmland_outflow': 'success',
    'road_extraction': 'primary',
    'water_extraction': 'info'
  }
  return typeMap[toolName] || 'default'
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 处理图层添加
const handleLayerAdded = (layer) => {
  appStore.addLayer(layer)
  showAddLayerDialog.value = false
  showSuccess(`图层"${layer.name}"添加成功`)
}
</script>

<style lang="scss" scoped>
.layer-panel {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  h4 {
    margin: 0;
    font-size: 16px;
    color: #303133;
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.layer-group {
  margin-bottom: 24px;
  
  .group-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    font-size: 14px;
    font-weight: 500;
    color: #606266;
    border-bottom: 1px solid #e4e7ed;
    margin-bottom: 12px;
    gap: 8px;
  }
}

.layer-list {
  .layer-item {
    display: flex;
    align-items: center;
    padding: 8px;
    margin-bottom: 8px;
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    transition: all 0.3s ease;
    cursor: pointer;
    
    &:hover {
      border-color: #409eff;
      box-shadow: 0 2px 4px rgba(64, 158, 255, 0.1);
    }
    
    &.disabled {
      opacity: 0.6;
    }
    
    &.active {
      border-color: #409eff;
      background-color: #ecf5ff;
    }
  }
  
  .basemap-item {
    flex-direction: column;
    padding: 12px;
    
    .layer-preview {
      width: 100%;
      height: 60px;
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 8px;
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }
    
    .layer-info {
      width: 100%;
      text-align: center;
      
      .layer-name {
        display: block;
        font-size: 13px;
        font-weight: 500;
        color: #303133;
        margin-bottom: 2px;
      }
      
      .layer-desc {
        font-size: 12px;
        color: #909399;
      }
    }
  }
  
  .layer-checkbox {
    margin-right: 12px;
  }
  
  .layer-info {
    flex: 1;
    min-width: 0;
    
    .layer-main {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 4px;
      
      .layer-name {
        font-size: 14px;
        font-weight: 500;
        color: #303133;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      
      .layer-type {
        font-size: 12px;
        color: #909399;
        background: #f5f7fa;
        padding: 2px 6px;
        border-radius: 3px;
      }
    }
    
    .layer-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .layer-source, .layer-time {
        font-size: 12px;
        color: #909399;
      }
    }
  }
  
  .layer-actions {
    display: flex;
    align-items: center;
    gap: 4px;
    
    .action-icon {
      padding: 4px;
      cursor: pointer;
      color: #909399;
      transition: color 0.3s;
      
      &:hover {
        color: #409eff;
      }
    }
  }
  
  .result-item {
    border-left: 3px solid #67c23a;
  }
}

.empty-state {
  text-align: center;
  padding: 20px;
}

.opacity-control {
  padding: 20px;
  
  .opacity-label {
    margin-bottom: 16px;
    font-size: 14px;
    color: #606266;
    text-align: center;
  }
}

:deep(.el-dropdown-menu__item.danger-item) {
  color: #f56c6c;
  
  &:hover {
    background-color: #fef0f0;
    color: #f56c6c;
  }
}
</style> 