<template>
  <div class="mcp-toolbar">
    <div class="section-header">
      <h4>
        <el-icon><Tools /></el-icon>
        MCP分析工具
      </h4>
      <el-button 
        size="small" 
        text 
        @click="refreshTools"
        :loading="loading"
        :icon="'Refresh'"
      >
        刷新
      </el-button>
    </div>
    
    <!-- 工具分类 -->
    <el-tabs v-model="activeCategory" class="tool-tabs">
      <el-tab-pane 
        v-for="category in toolCategories" 
        :key="category.id"
        :label="category.name" 
        :name="category.id"
      >
        <div class="tool-list">
          <div 
            v-for="tool in category.tools" 
            :key="tool.id"
            class="tool-item"
            :class="{ 
              disabled: !tool.available,
              active: selectedTool?.id === tool.id 
            }"
            @click="selectTool(tool)"
          >
            <div class="tool-icon">
              <el-icon :size="24">
                <component :is="tool.icon" />
              </el-icon>
            </div>
            
            <div class="tool-info">
              <div class="tool-name">{{ tool.name }}</div>
              <div class="tool-desc">{{ tool.description }}</div>
            </div>
            
            <div class="tool-status">
              <el-tag 
                v-if="!tool.available" 
                type="warning" 
                size="small"
              >
                不可用
              </el-tag>
              <el-tag 
                v-else-if="tool.experimental" 
                type="info" 
                size="small"
              >
                实验性
              </el-tag>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
    
    <!-- 工具参数面板 -->
    <div v-if="selectedTool" class="tool-params">
      <div class="params-header">
        <h5>{{ selectedTool.name }} - 参数设置</h5>
        <el-button 
          size="small" 
          text 
          @click="selectedTool = null"
          :icon="'Close'"
        />
      </div>
      
      <el-form 
        :model="toolParams" 
        :rules="paramRules"
        ref="paramsForm"
        label-position="top"
        size="small"
      >
        <!-- 动态参数表单 -->
        <div v-for="param in selectedTool.params" :key="param.name">
          <!-- 文本输入 -->
          <el-form-item 
            v-if="param.type === 'text'"
            :label="param.label"
            :prop="param.name"
            :required="param.required"
          >
            <el-input 
              v-model="toolParams[param.name]"
              :placeholder="param.placeholder"
              :disabled="param.disabled"
            />
            <div v-if="param.help" class="param-help">
              {{ param.help }}
            </div>
          </el-form-item>
          
          <!-- 数字输入 -->
          <el-form-item 
            v-else-if="param.type === 'number'"
            :label="param.label"
            :prop="param.name"
            :required="param.required"
          >
            <el-input-number 
              v-model="toolParams[param.name]"
              :min="param.min"
              :max="param.max"
              :step="param.step"
              :precision="param.precision"
              style="width: 100%"
            />
            <div v-if="param.help" class="param-help">
              {{ param.help }}
            </div>
          </el-form-item>
          
          <!-- 选择器 -->
          <el-form-item 
            v-else-if="param.type === 'select'"
            :label="param.label"
            :prop="param.name"
            :required="param.required"
          >
            <el-select 
              v-model="toolParams[param.name]"
              :placeholder="param.placeholder"
              style="width: 100%"
            >
              <el-option 
                v-for="option in param.options"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <div v-if="param.help" class="param-help">
              {{ param.help }}
            </div>
          </el-form-item>
          
          <!-- 坐标选择 -->
          <el-form-item 
            v-else-if="param.type === 'coordinate'"
            :label="param.label"
            :prop="param.name"
            :required="param.required"
          >
            <div class="coordinate-input">
              <el-input 
                v-model="toolParams[param.name + '_lng']"
                placeholder="经度"
                type="number"
                style="width: 48%"
              />
              <span style="margin: 0 2%">,</span>
              <el-input 
                v-model="toolParams[param.name + '_lat']"
                placeholder="纬度"
                type="number"
                style="width: 48%"
              />
            </div>
            <el-button 
              size="small" 
              text 
              @click="pickFromMap(param.name)"
              :icon="'MapLocation'"
            >
              从地图选择
            </el-button>
            <div v-if="param.help" class="param-help">
              {{ param.help }}
            </div>
          </el-form-item>
          
          <!-- 文件上传 -->
          <el-form-item 
            v-else-if="param.type === 'file'"
            :label="param.label"
            :prop="param.name"
            :required="param.required"
          >
            <el-upload
              :action="uploadUrl"
              :before-upload="beforeUpload"
              :on-success="(response) => handleUploadSuccess(response, param.name)"
              :show-file-list="false"
              :accept="param.accept"
              style="width: 100%"
            >
              <el-button type="primary" :icon="'Upload'">
                {{ toolParams[param.name] || '选择文件' }}
              </el-button>
            </el-upload>
            <div v-if="param.help" class="param-help">
              {{ param.help }}
            </div>
          </el-form-item>
          
          <!-- 区域选择 -->
          <el-form-item 
            v-else-if="param.type === 'bbox'"
            :label="param.label"
            :prop="param.name"
            :required="param.required"
          >
            <el-button 
              @click="drawBoundingBox(param.name)"
              :type="toolParams[param.name] ? 'success' : 'primary'"
              :icon="'Crop'"
              style="width: 100%"
            >
              {{ toolParams[param.name] ? '已选择区域' : '在地图上绘制区域' }}
            </el-button>
            <div v-if="param.help" class="param-help">
              {{ param.help }}
            </div>
          </el-form-item>
        </div>
        
        <!-- 执行按钮 -->
        <el-form-item class="execute-button">
          <el-button 
            type="primary" 
            @click="executeTool"
            :loading="executing"
            :disabled="!canExecute"
            style="width: 100%"
            size="default"
          >
            <el-icon><Play /></el-icon>
            执行 {{ selectedTool.name }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
    
    <!-- 工具说明 -->
    <div v-if="!selectedTool" class="tool-guide">
      <el-empty 
        description="选择一个分析工具开始使用" 
        :image-size="100"
      >
        <template #image>
          <el-icon size="100" color="#c0c4cc">
            <Tools />
          </el-icon>
        </template>
      </el-empty>
    </div>
    
    <!-- 最近使用的工具 -->
    <div v-if="recentTools.length > 0 && !selectedTool" class="recent-tools">
      <div class="section-title">
        <el-icon><Clock /></el-icon>
        最近使用
      </div>
      <div class="recent-list">
        <el-button 
          v-for="tool in recentTools"
          :key="tool.id"
          size="small"
          text
          @click="selectTool(tool)"
          class="recent-item"
        >
          <el-icon><component :is="tool.icon" /></el-icon>
          {{ tool.name }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { mcpService, uploadFile, showSuccess, showError } from '@/services/api'

const emit = defineEmits(['tool-execute'])
const appStore = useAppStore()

// 响应式数据
const loading = ref(false)
const executing = ref(false)
const selectedTool = ref(null)
const toolParams = reactive({})
const paramsForm = ref(null)
const activeCategory = ref('terrain')
const recentTools = ref([])

// 上传地址
const uploadUrl = '/api/upload'

// 工具分类配置
const toolCategories = reactive([
  {
    id: 'terrain',
    name: '地形分析',
    icon: 'Mountain',
    tools: [
      {
        id: 'slope_analysis',
        name: '坡度分析',
        description: '计算地形坡度信息',
        icon: 'TrendCharts',
        available: true,
        experimental: false,
        params: [
          {
            name: 'area',
            label: '分析区域',
            type: 'select',
            required: true,
            placeholder: '请选择分析区域',
            options: [
              { value: 'beijing', label: '北京市' },
              { value: 'shanghai', label: '上海市' },
              { value: 'guangzhou', label: '广州市' },
              { value: 'shenzhen', label: '深圳市' }
            ],
            help: '选择要进行坡度分析的地理区域'
          },
          {
            name: 'dem_resolution',
            label: 'DEM分辨率(米)',
            type: 'number',
            required: false,
            min: 1,
            max: 1000,
            step: 1,
            default: 30,
            help: '数字高程模型的空间分辨率'
          }
        ]
      }
    ]
  },
  {
    id: 'spatial',
    name: '空间分析',
    icon: 'MapLocation',
    tools: [
      {
        id: 'buffer_analysis',
        name: '缓冲区分析',
        description: '创建指定半径的缓冲区',
        icon: 'Position',
        available: true,
        experimental: false,
        params: [
          {
            name: 'center',
            label: '中心点坐标',
            type: 'coordinate',
            required: true,
            help: '缓冲区的中心点坐标（经度,纬度）'
          },
          {
            name: 'radius',
            label: '缓冲半径(米)',
            type: 'number',
            required: true,
            min: 1,
            max: 50000,
            step: 1,
            default: 1000,
            help: '缓冲区的半径，单位为米'
          },
          {
            name: 'segments',
            label: '分段数',
            type: 'number',
            required: false,
            min: 4,
            max: 64,
            step: 1,
            default: 16,
            help: '用于近似圆形的线段数量'
          }
        ]
      }
    ]
  },
  {
    id: 'agriculture',
    name: '农业分析',
    icon: 'Grape',
    tools: [
      {
        id: 'farmland_outflow',
        name: '耕地流出分析',
        description: '分析耕地利用变化情况',
        icon: 'Crop',
        available: true,
        experimental: false,
        params: [
          {
            name: 'region',
            label: '分析区域',
            type: 'select',
            required: true,
            options: [
              { value: 'shandong', label: '山东省' },
              { value: 'hebei', label: '河北省' },
              { value: 'henan', label: '河南省' },
              { value: 'jiangsu', label: '江苏省' }
            ],
            help: '选择要分析的省份或地区'
          },
          {
            name: 'year_start',
            label: '起始年份',
            type: 'number',
            required: true,
            min: 2000,
            max: 2023,
            step: 1,
            default: 2010,
            help: '分析的起始年份'
          },
          {
            name: 'year_end',
            label: '结束年份',
            type: 'number',
            required: true,
            min: 2000,
            max: 2023,
            step: 1,
            default: 2020,
            help: '分析的结束年份'
          }
        ]
      }
    ]
  },
  {
    id: 'extraction',
    name: '特征提取',
    icon: 'Search',
    tools: [
      {
        id: 'road_extraction',
        name: '道路提取',
        description: '从影像中提取道路网络',
        icon: 'Connection',
        available: true,
        experimental: true,
        params: [
          {
            name: 'image_file',
            label: '影像文件',
            type: 'file',
            required: true,
            accept: '.tif,.tiff,.jpg,.png',
            help: '上传要进行道路提取的影像文件'
          },
          {
            name: 'algorithm',
            label: '提取算法',
            type: 'select',
            required: true,
            options: [
              { value: 'canny', label: 'Canny边缘检测' },
              { value: 'morphology', label: '形态学处理' },
              { value: 'machine_learning', label: '机器学习' }
            ],
            default: 'canny',
            help: '选择道路提取使用的算法'
          }
        ]
      },
      {
        id: 'water_extraction',
        name: '水体提取',
        description: '提取水体分布信息',
        icon: 'Drizzling',
        available: true,
        experimental: false,
        params: [
          {
            name: 'bbox',
            label: '分析区域',
            type: 'bbox',
            required: true,
            help: '在地图上绘制要分析的区域范围'
          },
          {
            name: 'method',
            label: '提取方法',
            type: 'select',
            required: true,
            options: [
              { value: 'ndwi', label: 'NDWI水体指数' },
              { value: 'mndwi', label: 'MNDWI修正水体指数' },
              { value: 'threshold', label: '阈值分割' }
            ],
            default: 'ndwi',
            help: '选择水体提取的方法'
          }
        ]
      }
    ]
  },
  {
    id: 'classification',
    name: '影像分类',
    icon: 'Grid',
    tools: [
      {
        id: 'image_classification',
        name: '影像分类',
        description: '对遥感影像进行分类',
        icon: 'PictureRounded',
        available: true,
        experimental: true,
        params: [
          {
            name: 'image_file',
            label: '影像文件',
            type: 'file',
            required: true,
            accept: '.tif,.tiff',
            help: '上传要分类的遥感影像文件'
          },
          {
            name: 'class_num',
            label: '分类数量',
            type: 'number',
            required: true,
            min: 2,
            max: 20,
            step: 1,
            default: 5,
            help: '分类的类别数量'
          },
          {
            name: 'algorithm',
            label: '分类算法',
            type: 'select',
            required: true,
            options: [
              { value: 'kmeans', label: 'K-Means聚类' },
              { value: 'isodata', label: 'ISODATA算法' },
              { value: 'svm', label: '支持向量机' }
            ],
            default: 'kmeans',
            help: '选择影像分类算法'
          }
        ]
      }
    ]
  }
])

// 参数验证规则
const paramRules = reactive({})

// 计算属性
const canExecute = computed(() => {
  if (!selectedTool.value) return false
  
  // 检查必需参数是否已填写
  return selectedTool.value.params.every(param => {
    if (param.required) {
      const value = toolParams[param.name]
      return value !== undefined && value !== null && value !== ''
    }
    return true
  })
})

// 生命周期
onMounted(() => {
  refreshTools()
  loadRecentTools()
})

// 刷新工具列表
const refreshTools = async () => {
  loading.value = true
  try {
    // 检查工具可用性
    for (const category of toolCategories) {
      for (const tool of category.tools) {
        try {
          // 这里可以调用MCP服务检查工具状态
          tool.available = true
        } catch (error) {
          tool.available = false
        }
      }
    }
  } catch (error) {
    console.error('刷新工具列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 选择工具
const selectTool = (tool) => {
  if (!tool.available) {
    showError('该工具当前不可用，请稍后重试')
    return
  }
  
  selectedTool.value = tool
  
  // 初始化参数
  Object.keys(toolParams).forEach(key => delete toolParams[key])
  
  tool.params.forEach(param => {
    if (param.default !== undefined) {
      toolParams[param.name] = param.default
    } else if (param.type === 'coordinate') {
      toolParams[param.name + '_lng'] = ''
      toolParams[param.name + '_lat'] = ''
    }
  })
  
  // 设置验证规则
  Object.keys(paramRules).forEach(key => delete paramRules[key])
  
  tool.params.forEach(param => {
    if (param.required) {
      paramRules[param.name] = [
        { required: true, message: `请填写${param.label}`, trigger: 'blur' }
      ]
    }
  })
  
  console.log('选择工具:', tool.name)
}

// 从地图选择坐标
const pickFromMap = (paramName) => {
  console.log('从地图选择坐标:', paramName)
  showSuccess('请在地图上点击选择坐标')
  // 这里需要与地图组件交互
}

// 绘制边界框
const drawBoundingBox = (paramName) => {
  console.log('绘制边界框:', paramName)
  showSuccess('请在地图上绘制分析区域')
  // 这里需要与地图组件交互
}

// 文件上传前处理
const beforeUpload = (file) => {
  const isValidSize = file.size / 1024 / 1024 < 100 // 限制100MB
  if (!isValidSize) {
    showError('文件大小不能超过100MB')
    return false
  }
  return true
}

// 文件上传成功处理
const handleUploadSuccess = (response, paramName) => {
  toolParams[paramName] = response.filename
  showSuccess('文件上传成功')
}

// 执行工具
const executeTool = async () => {
  if (!paramsForm.value) return
  
  try {
    // 验证表单
    await paramsForm.value.validate()
    
    executing.value = true
    
    // 处理坐标参数
    const processedParams = { ...toolParams }
    selectedTool.value.params.forEach(param => {
      if (param.type === 'coordinate') {
        const lng = toolParams[param.name + '_lng']
        const lat = toolParams[param.name + '_lat']
        if (lng && lat) {
          processedParams[param.name] = [parseFloat(lng), parseFloat(lat)]
        }
        delete processedParams[param.name + '_lng']
        delete processedParams[param.name + '_lat']
      }
    })
    
    console.log('执行工具:', selectedTool.value.id, processedParams)
    
    // 发送工具执行事件
    emit('tool-execute', selectedTool.value.id, processedParams)
    
    // 添加到最近使用
    addToRecentTools(selectedTool.value)
    
    showSuccess(`正在执行${selectedTool.value.name}...`)
    
  } catch (error) {
    console.error('工具执行失败:', error)
    showError('参数验证失败，请检查输入')
  } finally {
    executing.value = false
  }
}

// 添加到最近使用
const addToRecentTools = (tool) => {
  const index = recentTools.value.findIndex(t => t.id === tool.id)
  if (index >= 0) {
    recentTools.value.splice(index, 1)
  }
  recentTools.value.unshift({ ...tool })
  
  // 限制数量
  if (recentTools.value.length > 5) {
    recentTools.value = recentTools.value.slice(0, 5)
  }
  
  // 保存到本地存储
  localStorage.setItem('oge_recent_tools', JSON.stringify(recentTools.value))
}

// 加载最近使用的工具
const loadRecentTools = () => {
  try {
    const stored = localStorage.getItem('oge_recent_tools')
    if (stored) {
      recentTools.value = JSON.parse(stored)
    }
  } catch (error) {
    console.error('加载最近使用工具失败:', error)
  }
}
</script>

<style lang="scss" scoped>
.mcp-toolbar {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
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

.tool-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  
  :deep(.el-tabs__content) {
    flex: 1;
    overflow-y: auto;
  }
}

.tool-list {
  .tool-item {
    display: flex;
    align-items: center;
    padding: 12px;
    margin-bottom: 8px;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover:not(.disabled) {
      border-color: #409eff;
      box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
    }
    
    &.active {
      border-color: #409eff;
      background-color: #ecf5ff;
    }
    
    &.disabled {
      opacity: 0.5;
      cursor: not-allowed;
      background-color: #f5f7fa;
    }
  }
  
  .tool-icon {
    margin-right: 12px;
    color: #409eff;
  }
  
  .tool-info {
    flex: 1;
    
    .tool-name {
      font-size: 14px;
      font-weight: 500;
      color: #303133;
      margin-bottom: 4px;
    }
    
    .tool-desc {
      font-size: 12px;
      color: #909399;
      line-height: 1.4;
    }
  }
  
  .tool-status {
    margin-left: 8px;
  }
}

.tool-params {
  margin-top: 16px;
  
  .params-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e4e7ed;
    
    h5 {
      margin: 0;
      font-size: 14px;
      color: #303133;
    }
  }
  
  .param-help {
    margin-top: 4px;
    font-size: 12px;
    color: #909399;
    line-height: 1.4;
  }
  
  .coordinate-input {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
  }
  
  .execute-button {
    margin-top: 20px;
    margin-bottom: 0;
  }
}

.tool-guide {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #909399;
}

.recent-tools {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
  
  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: #606266;
    margin-bottom: 12px;
  }
  
  .recent-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    
    .recent-item {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 4px 8px;
      font-size: 12px;
    }
  }
}

:deep(.el-form-item) {
  margin-bottom: 16px;
}

:deep(.el-tabs__item) {
  font-size: 13px;
}

:deep(.el-upload) {
  width: 100%;
  
  .el-upload-dragger {
    width: 100%;
  }
}
</style> 