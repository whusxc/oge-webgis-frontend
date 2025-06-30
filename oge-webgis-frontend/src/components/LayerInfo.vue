<template>
  <div class="layer-info">
    <el-descriptions :column="1" border>
      <el-descriptions-item label="图层名称">
        {{ layer.name }}
      </el-descriptions-item>
      <el-descriptions-item label="图层类型">
        {{ layer.type }}
      </el-descriptions-item>
      <el-descriptions-item label="数据源">
        {{ layer.source }}
      </el-descriptions-item>
      <el-descriptions-item label="创建时间" v-if="layer.createTime">
        {{ formatTime(layer.createTime) }}
      </el-descriptions-item>
      <el-descriptions-item label="可见性">
        <el-tag :type="layer.visible ? 'success' : 'info'">
          {{ layer.visible ? '可见' : '隐藏' }}
        </el-tag>
      </el-descriptions-item>
    </el-descriptions>
    
    <div class="layer-stats" v-if="layer.statistics">
      <h4>图层统计</h4>
      <el-row :gutter="16">
        <el-col :span="8" v-for="(value, key) in layer.statistics" :key="key">
          <el-statistic :title="key" :value="value" />
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  layer: {
    type: Object,
    required: true
  }
})

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}
</script>

<style lang="scss" scoped>
.layer-info {
  padding: 20px;
}

.layer-stats {
  margin-top: 20px;
  
  h4 {
    margin-bottom: 16px;
    color: #303133;
  }
}
</style> 