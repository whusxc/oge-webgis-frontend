<template>
  <div class="tools-page">
    <div class="tools-header">
      <h1>MCP工具箱</h1>
      <p>地理空间分析和处理工具集</p>
    </div>
    
    <div class="tools-container">
      <!-- 工具分类选项卡 -->
      <el-tabs v-model="activeTab" type="border-card" class="tools-tabs">
        <el-tab-pane 
          v-for="category in toolCategories" 
          :key="category.key"
          :label="category.name" 
          :name="category.key"
        >
          <div class="tools-grid">
            <el-card 
              v-for="tool in category.tools" 
              :key="tool.key"
              class="tool-card"
              :class="{ 'disabled': !tool.available }"
              @click="handleToolClick(tool)"
              shadow="hover"
            >
              <div class="tool-content">
                <div class="tool-icon" :style="{ color: tool.color }">
                  <el-icon size="32"><component :is="tool.icon" /></el-icon>
                </div>
                <div class="tool-info">
                  <h3>{{ tool.name }}</h3>
                  <p>{{ tool.description }}</p>
                  <div class="tool-status">
                    <el-tag 
                      :type="tool.available ? 'success' : 'info'" 
                      size="small"
                      effect="plain"
                    >
                      {{ tool.available ? '可用' : '需要内网' }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
      
      <!-- 工具说明 -->
      <el-card class="tool-description" v-if="selectedTool">
        <template #header>
          <h3>{{ selectedTool.name }}</h3>
        </template>
        <div class="description-content">
          <p>{{ selectedTool.detailedDescription }}</p>
          <div class="tool-params">
            <h4>参数说明：</h4>
            <ul>
              <li v-for="param in selectedTool.parameters" :key="param.name">
                <strong>{{ param.name }}</strong>: {{ param.description }}
              </li>
            </ul>
          </div>
          <div class="tool-actions">
            <el-button 
              type="primary" 
              :disabled="!selectedTool.available"
              @click="openMapWithTool"
            >
              在地图中使用
            </el-button>
            <el-button @click="selectedTool = null">关闭</el-button>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showWarning, showInfo } from '@/services/api'

const router = useRouter()
const activeTab = ref('terrain')
const selectedTool = ref(null)

// 工具分类和工具定义
const toolCategories = ref([
  {
    key: 'terrain',
    name: '地形分析',
    tools: [
      {
        key: 'slope',
        name: '坡度分析',
        description: '计算数字高程模型的坡度',
        detailedDescription: '基于DEM数据计算地表坡度，支持度数和百分比两种输出格式。',
        icon: 'TrendCharts',
        color: '#409EFF',
        available: false, // 需要内网
        parameters: [
          { name: 'DEM数据', description: '数字高程模型输入' },
          { name: '输出格式', description: '度数或百分比' },
          { name: '分析范围', description: '指定分析区域' }
        ]
      },
      {
        key: 'aspect',
        name: '坡向分析',
        description: '计算地形的坡向信息',
        detailedDescription: '分析地形表面的朝向，输出8个主要方向的坡向分布。',
        icon: 'Compass',
        color: '#67C23A',
        available: false,
        parameters: [
          { name: 'DEM数据', description: '数字高程模型输入' },
          { name: '方向分类', description: '8方向或16方向' }
        ]
      },
      {
        key: 'hillshade',
        name: '山体阴影',
        description: '生成地形阴影效果',
        detailedDescription: '根据光照角度和地形起伏生成逼真的山体阴影图。',
        icon: 'Sunny',
        color: '#E6A23C',
        available: false,
        parameters: [
          { name: 'DEM数据', description: '数字高程模型输入' },
          { name: '太阳高度角', description: '光源高度角度' },
          { name: '太阳方位角', description: '光源方位角度' }
        ]
      }
    ]
  },
  {
    key: 'spatial',
    name: '空间分析',
    tools: [
      {
        key: 'buffer',
        name: '缓冲区分析',
        description: '创建要素周围的缓冲区',
        detailedDescription: '在点、线、面要素周围创建指定距离的缓冲区域。',
        icon: 'Location',
        color: '#F56C6C',
        available: false,
        parameters: [
          { name: '输入要素', description: '点、线或面要素' },
          { name: '缓冲距离', description: '缓冲区半径' },
          { name: '单位', description: '米、千米等' }
        ]
      },
      {
        key: 'overlay',
        name: '叠加分析',
        description: '进行图层叠加运算',
        detailedDescription: '对多个图层进行交集、并集、差集等空间叠加运算。',
        icon: 'Grid',
        color: '#909399',
        available: false,
        parameters: [
          { name: '输入图层1', description: '第一个输入图层' },
          { name: '输入图层2', description: '第二个输入图层' },
          { name: '运算类型', description: '交集、并集、差集' }
        ]
      }
    ]
  },
  {
    key: 'agriculture',
    name: '农业分析',
    tools: [
      {
        key: 'ndvi',
        name: 'NDVI计算',
        description: '归一化植被指数计算',
        detailedDescription: '基于红光和近红外波段计算植被健康状况指数。',
        icon: 'GrassPlant',
        color: '#95d475',
        available: false,
        parameters: [
          { name: '红光波段', description: 'Red波段数据' },
          { name: '近红外波段', description: 'NIR波段数据' },
          { name: '输出范围', description: '-1到1的NDVI值' }
        ]
      },
      {
        key: 'crop_classification',
        name: '作物分类',
        description: '农作物自动分类识别',
        detailedDescription: '基于遥感影像自动识别和分类不同的农作物类型。',
        icon: 'Cherry',
        color: '#ff6b6b',
        available: false,
        parameters: [
          { name: '多光谱影像', description: '多波段遥感数据' },
          { name: '训练样本', description: '已知作物类型样本' },
          { name: '分类算法', description: '机器学习分类方法' }
        ]
      }
    ]
  },
  {
    key: 'feature',
    name: '特征提取',
    tools: [
      {
        key: 'road_extraction',
        name: '道路提取',
        description: '自动提取遥感影像中的道路',
        detailedDescription: '使用深度学习算法从高分辨率遥感影像中自动识别和提取道路网络。',
        icon: 'Position',
        color: '#74c0fc',
        available: false,
        parameters: [
          { name: '高分影像', description: '高分辨率遥感影像' },
          { name: '模型类型', description: 'U-Net或DeepLab模型' },
          { name: '后处理', description: '道路网络优化' }
        ]
      },
      {
        key: 'building_detection',
        name: '建筑物检测',
        description: '检测和识别建筑物',
        detailedDescription: '自动检测遥感影像中的建筑物并生成建筑物轮廓。',
        icon: 'House',
        color: '#845ec2',
        available: false,
        parameters: [
          { name: '输入影像', description: '遥感影像数据' },
          { name: '检测阈值', description: '建筑物检测阈值' },
          { name: '最小面积', description: '最小建筑物面积' }
        ]
      }
    ]
  },
  {
    key: 'classification',
    name: '影像分类',
    tools: [
      {
        key: 'supervised_classification',
        name: '监督分类',
        description: '基于训练样本的分类',
        detailedDescription: '使用已知样本训练分类器，对整幅影像进行自动分类。',
        icon: 'Document',
        color: '#4ecdc4',
        available: false,
        parameters: [
          { name: '多光谱影像', description: '待分类影像' },
          { name: '训练样本', description: '各类别训练数据' },
          { name: '分类器', description: '最大似然、支持向量机等' }
        ]
      },
      {
        key: 'unsupervised_classification',
        name: '非监督分类',
        description: '无需训练样本的自动分类',
        detailedDescription: '基于像元光谱特征的相似性进行自动聚类分类。',
        icon: 'DataBoard',
        color: '#ffbe0b',
        available: false,
        parameters: [
          { name: '输入影像', description: '多光谱影像数据' },
          { name: '聚类数量', description: '期望的分类类别数' },
          { name: '算法类型', description: 'K-means或ISODATA' }
        ]
      }
    ]
  }
])

const handleToolClick = (tool) => {
  if (!tool.available) {
    showWarning('该工具需要连接到内网MCP服务器才能使用')
    return
  }
  selectedTool.value = tool
}

const openMapWithTool = () => {
  if (!selectedTool.value.available) {
    showWarning('工具不可用，需要内网连接')
    return
  }
  
  showInfo(`正在打开地图并加载${selectedTool.value.name}工具...`)
  router.push('/map')
}
</script>

<style lang="scss" scoped>
.tools-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.tools-header {
  text-align: center;
  margin-bottom: 30px;
  
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

.tools-container {
  max-width: 1200px;
  margin: 0 auto;
}

.tools-tabs {
  :deep(.el-tabs__content) {
    padding: 20px;
  }
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.tool-card {
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover:not(.disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  &.disabled {
    opacity: 0.6;
    cursor: not-allowed;
    
    :deep(.el-card__body) {
      background-color: #f9f9f9;
    }
  }
  
  :deep(.el-card__body) {
    padding: 20px;
  }
}

.tool-content {
  display: flex;
  align-items: center;
}

.tool-icon {
  margin-right: 15px;
  flex-shrink: 0;
}

.tool-info {
  flex: 1;
  
  h3 {
    margin: 0 0 8px 0;
    color: #303133;
    font-size: 16px;
    font-weight: 500;
  }
  
  p {
    margin: 0 0 10px 0;
    color: #606266;
    font-size: 14px;
    line-height: 1.4;
  }
}

.tool-status {
  margin-top: 8px;
}

.tool-description {
  margin-top: 20px;
  
  :deep(.el-card__header) {
    padding: 18px 20px;
    border-bottom: 1px solid #ebeef5;
    
    h3 {
      margin: 0;
      color: #303133;
      font-size: 18px;
      font-weight: 500;
    }
  }
}

.description-content {
  p {
    color: #606266;
    line-height: 1.6;
    margin-bottom: 20px;
  }
  
  .tool-params {
    margin-bottom: 20px;
    
    h4 {
      color: #303133;
      margin: 0 0 10px 0;
      font-size: 14px;
      font-weight: 500;
    }
    
    ul {
      margin: 0;
      padding-left: 20px;
      color: #606266;
      
      li {
        margin-bottom: 5px;
        line-height: 1.4;
      }
    }
  }
  
  .tool-actions {
    display: flex;
    gap: 10px;
  }
}

@media (max-width: 768px) {
  .tools-page {
    padding: 15px;
  }
  
  .tools-grid {
    grid-template-columns: 1fr;
  }
  
  .tool-content {
    flex-direction: column;
    text-align: center;
    
    .tool-icon {
      margin: 0 0 10px 0;
    }
  }
}
</style> 