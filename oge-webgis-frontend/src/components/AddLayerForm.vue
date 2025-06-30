<template>
  <div class="add-layer-form">
    <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
      <el-form-item label="图层名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入图层名称" />
      </el-form-item>
      
      <el-form-item label="图层类型" prop="type">
        <el-select v-model="form.type" placeholder="请选择图层类型" style="width: 100%">
          <el-option label="GeoJSON" value="geojson" />
          <el-option label="WMS服务" value="wms" />
          <el-option label="瓦片服务" value="tiles" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="数据源" prop="source">
        <el-input 
          v-model="form.source" 
          type="textarea" 
          :rows="3"
          placeholder="请输入数据源URL或上传文件"
        />
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          添加图层
        </el-button>
        <el-button @click="handleCancel">
          取消
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const emit = defineEmits(['layer-added', 'cancel'])

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  name: '',
  type: '',
  source: ''
})

const rules = {
  name: [{ required: true, message: '请输入图层名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择图层类型', trigger: 'change' }],
  source: [{ required: true, message: '请输入数据源', trigger: 'blur' }]
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    // 模拟添加图层
    setTimeout(() => {
      const layer = {
        id: `layer_${Date.now()}`,
        name: form.name,
        type: 'data',
        source: form.source,
        visible: true,
        createTime: new Date().toISOString()
      }
      
      emit('layer-added', layer)
      loading.value = false
    }, 1000)
    
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

const handleCancel = () => {
  emit('cancel')
}
</script>

<style lang="scss" scoped>
.add-layer-form {
  padding: 20px;
}
</style> 