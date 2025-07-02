<template>
  <div class="modern-tools-view">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-main">
          <div class="page-title-section">
            <h1 class="page-title">🛠️ 智能工具箱</h1>
            <p class="page-subtitle">强大的地理分析与数据处理工具集合</p>
          </div>
          
          <div class="header-actions">
            <button class="btn btn-secondary" @click="$router.push('/map')">
              <span>🗺️</span>
              <span>返回地图</span>
            </button>
          </div>
        </div>
        
        <!-- 搜索和筛选 -->
        <div class="search-filter-section">
          <div class="search-box">
            <div class="search-input-wrapper">
              <span class="search-icon">🔍</span>
              <input 
                v-model="searchQuery"
                type="text"
                placeholder="搜索工具名称或功能..."
                class="search-input"
              >
            </div>
          </div>
          
          <div class="filter-tabs">
            <button 
              v-for="category in categories"
              :key="category.id"
              :class="['filter-tab', { active: activeCategory === category.id }]"
              @click="setActiveCategory(category.id)"
            >
              <span class="tab-icon">{{ category.icon }}</span>
              <span class="tab-label">{{ category.name }}</span>
              <span class="tab-count">{{ category.count }}</span>
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- 工具网格 -->
    <main class="tools-content">
      <div class="tools-grid">
        <div 
          v-for="tool in filteredTools"
          :key="tool.id"
          class="tool-card animate-fadeInUp"
          @click="openTool(tool)"
        >
          <div class="tool-card-header">
            <div class="tool-icon">{{ tool.icon }}</div>
            <div class="tool-badge" :class="`badge-${tool.category}`">
              {{ getCategoryName(tool.category) }}
            </div>
          </div>
          
          <div class="tool-card-body">
            <h3 class="tool-title">{{ tool.name }}</h3>
            <p class="tool-description">{{ tool.description }}</p>
            
            <div class="tool-features">
              <div 
                v-for="feature in tool.features?.slice(0, 3)"
                :key="feature"
                class="feature-tag"
              >
                {{ feature }}
              </div>
            </div>
          </div>
          
          <div class="tool-card-footer">
            <div class="tool-meta">
              <span class="meta-item">
                <span class="meta-icon">⚡</span>
                <span>{{ tool.performance }}</span>
              </span>
              <span class="meta-item">
                <span class="meta-icon">🎯</span>
                <span>{{ tool.accuracy }}</span>
              </span>
            </div>
            
            <button class="launch-btn">
              <span>启动工具</span>
              <span class="btn-arrow">→</span>
            </button>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-if="filteredTools.length === 0" class="empty-state">
        <div class="empty-icon">🔍</div>
        <h3>未找到匹配的工具</h3>
        <p>尝试调整搜索条件或选择不同的分类</p>
        <button class="btn btn-primary" @click="resetFilters">
          <span>重置筛选</span>
        </button>
      </div>
    </main>

    <!-- 工具详情弹窗 -->
    <div v-if="selectedTool" class="tool-modal-overlay" @click="closeTool">
      <div class="tool-modal" @click.stop>
        <div class="modal-header">
          <div class="modal-title-section">
            <div class="modal-icon">{{ selectedTool.icon }}</div>
            <div>
              <h2 class="modal-title">{{ selectedTool.name }}</h2>
              <p class="modal-subtitle">{{ selectedTool.description }}</p>
            </div>
          </div>
          <button class="close-btn" @click="closeTool">✕</button>
        </div>
        
        <div class="modal-body">
          <div class="tool-info-grid">
            <div class="info-section">
              <h4>功能特性</h4>
              <ul class="feature-list">
                <li v-for="feature in selectedTool.features" :key="feature">
                  <span class="feature-bullet">✓</span>
                  <span>{{ feature }}</span>
                </li>
              </ul>
            </div>
            
            <div class="info-section">
              <h4>技术参数</h4>
              <div class="params-grid">
                <div class="param-item">
                  <span class="param-label">处理性能</span>
                  <span class="param-value">{{ selectedTool.performance }}</span>
                </div>
                <div class="param-item">
                  <span class="param-label">计算精度</span>
                  <span class="param-value">{{ selectedTool.accuracy }}</span>
                </div>
                <div class="param-item">
                  <span class="param-label">支持格式</span>
                  <span class="param-value">{{ selectedTool.formats?.join(', ') }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="usage-example" v-if="selectedTool.example">
            <h4>使用示例</h4>
            <div class="example-content">
              <p>{{ selectedTool.example }}</p>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeTool">
            取消
          </button>
          <button class="btn btn-primary" @click="executeTool(selectedTool)">
            <span>🚀</span>
            <span>立即使用</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const appStore = useAppStore()

// 响应式数据
const searchQuery = ref('')
const activeCategory = ref('all')
const selectedTool = ref(null)

// 工具分类
const categories = ref([
  { id: 'all', name: '全部', icon: '📦', count: 0 },
  { id: 'analysis', name: '空间分析', icon: '📊', count: 0 },
  { id: 'extraction', name: '信息提取', icon: '🔍', count: 0 },
  { id: 'processing', name: '数据处理', icon: '⚙️', count: 0 },
  { id: 'visualization', name: '可视化', icon: '🎨', count: 0 }
])

// 工具数据
const tools = ref([
  {
    id: 'slope_analysis',
    name: '坡度分析',
    description: '基于DEM数据进行地形坡度计算和分析',
    icon: '⛰️',
    category: 'analysis',
    performance: '高性能',
    accuracy: '精确',
    features: ['支持多种DEM格式', '可视化坡度分布', '批量处理', '统计分析'],
    formats: ['GeoTIFF', 'NetCDF', 'HDF'],
    example: '上传DEM数据，设置分析参数，自动计算坡度并生成可视化结果'
  },
  {
    id: 'buffer_analysis',
    name: '缓冲区分析',
    description: '对地理要素创建指定距离的缓冲区',
    icon: '🎯',
    category: 'analysis',
    performance: '快速',
    accuracy: '高精度',
    features: ['多种缓冲距离', '复杂几何处理', '属性保留', '拓扑检查'],
    formats: ['Shapefile', 'GeoJSON', 'KML'],
    example: '选择目标要素，设置缓冲距离，生成缓冲区多边形'
  },
  {
    id: 'road_extraction',
    name: '道路提取',
    description: '从遥感影像中智能提取道路网络',
    icon: '🛤️',
    category: 'extraction',
    performance: 'AI加速',
    accuracy: '智能',
    features: ['深度学习算法', '自动矢量化', '拓扑优化', '质量评估'],
    formats: ['GeoTIFF', 'JPEG', 'PNG'],
    example: '上传高分辨率影像，AI自动识别并提取道路网络'
  },
  {
    id: 'farmland_outflow',
    name: '耕地流出监测',
    description: '监测和分析耕地变化及流出情况',
    icon: '🌾',
    category: 'analysis',
    performance: '高效',
    accuracy: '专业',
    features: ['时序分析', '变化检测', '统计报告', '风险评估'],
    formats: ['Landsat', 'Sentinel', 'GaoFen'],
    example: '对比不同时期影像，自动检测耕地变化并生成分析报告'
  },
  {
    id: 'land_classification',
    name: '土地分类',
    description: '基于机器学习的智能土地利用分类',
    icon: '🗺️',
    category: 'extraction',
    performance: 'GPU加速',
    accuracy: '高精度',
    features: ['多光谱分析', '机器学习', '精度评估', '样本训练'],
    formats: ['多光谱影像', 'Shapefile'],
    example: '训练分类模型，对影像进行自动土地利用分类'
  },
  {
    id: 'water_extraction',
    name: '水体提取',
    description: '自动识别和提取各类水体要素',
    icon: '💧',
    category: 'extraction',
    performance: '实时',
    accuracy: '高精度',
    features: ['光谱指数', '阈值分割', '形态学处理', '噪声去除'],
    formats: ['Landsat', 'Sentinel', 'MODIS'],
    example: '基于NDWI指数自动提取水体边界和面积信息'
  },
  {
    id: 'data_fusion',
    name: '数据融合',
    description: '多源遥感数据的智能融合处理',
    icon: '🔄',
    category: 'processing',
    performance: '并行',
    accuracy: '优化',
    features: ['多源配准', '辐射校正', '几何校正', '质量提升'],
    formats: ['多种传感器数据'],
    example: '融合不同传感器数据，提高影像质量和信息量'
  },
  {
    id: 'visualization',
    name: '三维可视化',
    description: '创建震撼的三维地理场景展示',
    icon: '🎭',
    category: 'visualization',
    performance: '流畅',
    accuracy: '逼真',
    features: ['3D渲染', '纹理贴图', '动画效果', '交互控制'],
    formats: ['DEM', 'DOM', '矢量数据'],
    example: '基于DEM和影像创建真实感三维地形场景'
  }
])

// 计算属性
const filteredTools = computed(() => {
  let result = tools.value

  // 按分类筛选
  if (activeCategory.value !== 'all') {
    result = result.filter(tool => tool.category === activeCategory.value)
  }

  // 按搜索关键词筛选
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(tool => 
      tool.name.toLowerCase().includes(query) ||
      tool.description.toLowerCase().includes(query) ||
      tool.features.some(feature => feature.toLowerCase().includes(query))
    )
  }

  return result
})

// 方法
const setActiveCategory = (categoryId) => {
  activeCategory.value = categoryId
}

const getCategoryName = (categoryId) => {
  const category = categories.value.find(cat => cat.id === categoryId)
  return category?.name || categoryId
}

const openTool = (tool) => {
  selectedTool.value = tool
}

const closeTool = () => {
  selectedTool.value = null
}

const executeTool = (tool) => {
  console.log('执行工具:', tool.name)
  // 这里可以添加工具执行逻辑
  router.push('/map')
  closeTool()
}

const resetFilters = () => {
  searchQuery.value = ''
  activeCategory.value = 'all'
}

// 更新分类计数
const updateCategoryCounts = () => {
  categories.value.forEach(category => {
    if (category.id === 'all') {
      category.count = tools.value.length
    } else {
      category.count = tools.value.filter(tool => tool.category === category.id).length
    }
  })
}

onMounted(() => {
  updateCategoryCounts()
  console.log('🛠️ 现代化工具箱页面已加载')
})
</script>

<style lang="scss" scoped>
.modern-tools-view {
  min-height: 100vh;
  background: var(--surface-alt);
}

// 页面头部
.page-header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: var(--spacing-6) 0;
  
  .header-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 var(--spacing-6);
    
    .header-main {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: var(--spacing-6);
      
      .page-title-section {
        .page-title {
          font-size: var(--text-3xl);
          font-weight: var(--font-bold);
          color: var(--text-primary);
          margin-bottom: var(--spacing-2);
        }
        
        .page-subtitle {
          font-size: var(--text-lg);
          color: var(--text-secondary);
          margin: 0;
        }
      }
    }
    
    .search-filter-section {
      display: flex;
      gap: var(--spacing-6);
      align-items: center;
      flex-wrap: wrap;
      
      .search-box {
        flex: 1;
        min-width: 300px;
        
        .search-input-wrapper {
          position: relative;
          
          .search-icon {
            position: absolute;
            left: var(--spacing-3);
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
          }
          
          .search-input {
            width: 100%;
            padding: var(--spacing-3) var(--spacing-3) var(--spacing-3) var(--spacing-10);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            font-size: var(--text-base);
            background: var(--surface);
            transition: var(--transition);
            
            &:focus {
              outline: none;
              border-color: var(--primary);
              box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
            }
          }
        }
      }
      
      .filter-tabs {
        display: flex;
        gap: var(--spacing-1);
        
        .filter-tab {
          display: flex;
          align-items: center;
          gap: var(--spacing-2);
          padding: var(--spacing-2) var(--spacing-4);
          border: 1px solid var(--border);
          background: var(--surface);
          border-radius: var(--radius-lg);
          cursor: pointer;
          transition: var(--transition);
          font-size: var(--text-sm);
          
          &:hover {
            background: var(--surface-hover);
            border-color: var(--border-hover);
          }
          
          &.active {
            background: var(--primary);
            border-color: var(--primary);
            color: var(--text-inverse);
          }
          
          .tab-count {
            background: rgba(255, 255, 255, 0.2);
            padding: 0.125rem 0.375rem;
            border-radius: var(--radius-full);
            font-size: var(--text-xs);
            font-weight: var(--font-semibold);
          }
        }
      }
    }
  }
}

// 工具网格
.tools-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-6);
  
  .tools-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: var(--spacing-6);
    
    .tool-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      overflow: hidden;
      transition: var(--transition);
      cursor: pointer;
      
      &:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-4px);
        border-color: var(--primary);
      }
      
      .tool-card-header {
        padding: var(--spacing-5);
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        background: linear-gradient(135deg, var(--surface-alt) 0%, var(--surface) 100%);
        
        .tool-icon {
          width: 60px;
          height: 60px;
          background: linear-gradient(135deg, var(--primary), var(--secondary));
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 2rem;
        }
        
        .tool-badge {
          padding: var(--spacing-1) var(--spacing-3);
          border-radius: var(--radius-full);
          font-size: var(--text-xs);
          font-weight: var(--font-semibold);
          
          &.badge-analysis {
            background: rgba(37, 99, 235, 0.1);
            color: var(--primary);
          }
          
          &.badge-extraction {
            background: rgba(16, 185, 129, 0.1);
            color: var(--secondary);
          }
          
          &.badge-processing {
            background: rgba(245, 158, 11, 0.1);
            color: var(--accent);
          }
          
          &.badge-visualization {
            background: rgba(139, 92, 246, 0.1);
            color: #8b5cf6;
          }
        }
      }
      
      .tool-card-body {
        padding: var(--spacing-5);
        
        .tool-title {
          font-size: var(--text-xl);
          font-weight: var(--font-semibold);
          color: var(--text-primary);
          margin-bottom: var(--spacing-2);
        }
        
        .tool-description {
          color: var(--text-secondary);
          line-height: var(--leading-relaxed);
          margin-bottom: var(--spacing-4);
        }
        
        .tool-features {
          display: flex;
          flex-wrap: wrap;
          gap: var(--spacing-2);
          
          .feature-tag {
            padding: var(--spacing-1) var(--spacing-2);
            background: var(--surface-alt);
            border-radius: var(--radius);
            font-size: var(--text-xs);
            color: var(--text-secondary);
          }
        }
      }
      
      .tool-card-footer {
        padding: var(--spacing-5);
        border-top: 1px solid var(--border);
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .tool-meta {
          display: flex;
          gap: var(--spacing-4);
          
          .meta-item {
            display: flex;
            align-items: center;
            gap: var(--spacing-1);
            font-size: var(--text-sm);
            color: var(--text-secondary);
            
            .meta-icon {
              opacity: 0.7;
            }
          }
        }
        
        .launch-btn {
          display: flex;
          align-items: center;
          gap: var(--spacing-2);
          padding: var(--spacing-2) var(--spacing-4);
          background: var(--primary);
          color: var(--text-inverse);
          border: none;
          border-radius: var(--radius);
          font-size: var(--text-sm);
          font-weight: var(--font-medium);
          cursor: pointer;
          transition: var(--transition);
          
          &:hover {
            background: var(--primary-dark);
            transform: translateX(2px);
          }
          
          .btn-arrow {
            transition: var(--transition);
          }
        }
      }
    }
  }
}

// 空状态
.empty-state {
  text-align: center;
  padding: var(--spacing-16) var(--spacing-6);
  
  .empty-icon {
    font-size: 4rem;
    margin-bottom: var(--spacing-4);
    opacity: 0.5;
  }
  
  h3 {
    color: var(--text-primary);
    margin-bottom: var(--spacing-2);
  }
  
  p {
    color: var(--text-secondary);
    margin-bottom: var(--spacing-4);
  }
}

// 工具详情弹窗
.tool-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-4);
  
  .tool-modal {
    background: var(--surface);
    border-radius: var(--radius-lg);
    max-width: 800px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: var(--shadow-xl);
    
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: var(--spacing-6);
      border-bottom: 1px solid var(--border);
      
      .modal-title-section {
        display: flex;
        gap: var(--spacing-4);
        align-items: center;
        
        .modal-icon {
          width: 60px;
          height: 60px;
          background: linear-gradient(135deg, var(--primary), var(--secondary));
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 2rem;
        }
        
        .modal-title {
          font-size: var(--text-2xl);
          font-weight: var(--font-bold);
          color: var(--text-primary);
          margin-bottom: var(--spacing-1);
        }
        
        .modal-subtitle {
          color: var(--text-secondary);
          margin: 0;
        }
      }
      
      .close-btn {
        width: 32px;
        height: 32px;
        border: none;
        background: var(--surface-alt);
        border-radius: var(--radius);
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
    
    .modal-body {
      padding: var(--spacing-6);
      
      .tool-info-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: var(--spacing-6);
        margin-bottom: var(--spacing-6);
        
        .info-section {
          h4 {
            font-size: var(--text-lg);
            font-weight: var(--font-semibold);
            color: var(--text-primary);
            margin-bottom: var(--spacing-3);
          }
          
          .feature-list {
            list-style: none;
            
            li {
              display: flex;
              align-items: center;
              gap: var(--spacing-2);
              margin-bottom: var(--spacing-2);
              
              .feature-bullet {
                color: var(--success);
                font-weight: var(--font-bold);
              }
            }
          }
          
          .params-grid {
            display: flex;
            flex-direction: column;
            gap: var(--spacing-3);
            
            .param-item {
              display: flex;
              justify-content: space-between;
              align-items: center;
              padding: var(--spacing-2) 0;
              border-bottom: 1px solid var(--border);
              
              .param-label {
                color: var(--text-secondary);
                font-size: var(--text-sm);
              }
              
              .param-value {
                color: var(--text-primary);
                font-weight: var(--font-medium);
              }
            }
          }
        }
      }
      
      .usage-example {
        h4 {
          font-size: var(--text-lg);
          font-weight: var(--font-semibold);
          color: var(--text-primary);
          margin-bottom: var(--spacing-3);
        }
        
        .example-content {
          background: var(--surface-alt);
          padding: var(--spacing-4);
          border-radius: var(--radius);
          border-left: 4px solid var(--primary);
          
          p {
            color: var(--text-secondary);
            line-height: var(--leading-relaxed);
            margin: 0;
          }
        }
      }
    }
    
    .modal-footer {
      padding: var(--spacing-6);
      border-top: 1px solid var(--border);
      display: flex;
      gap: var(--spacing-3);
      justify-content: flex-end;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .page-header .header-content .search-filter-section {
    flex-direction: column;
    align-items: stretch;
    
    .search-box {
      min-width: auto;
    }
    
    .filter-tabs {
      overflow-x: auto;
      padding-bottom: var(--spacing-2);
    }
  }
  
  .tools-grid {
    grid-template-columns: 1fr !important;
  }
  
  .tool-modal .modal-body .tool-info-grid {
    grid-template-columns: 1fr !important;
  }
}
</style> 