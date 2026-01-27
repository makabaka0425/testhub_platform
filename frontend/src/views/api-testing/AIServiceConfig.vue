<template>
  <div class="ai-service-config">
    <div class="page-header">
      <h2>AI服务配置</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        添加配置
      </el-button>
    </div>

    <div class="config-list">
      <el-table :data="configs" v-loading="loading" stripe>
        <el-table-column prop="name" label="配置名称" width="200" />
        <el-table-column prop="service_type_display" label="服务类型" width="120" />
        <el-table-column prop="role_display" label="角色类型" width="150" />
        <el-table-column prop="model_name" label="模型名称" width="200" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_by_name" label="创建者" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="testConnection(row)" :loading="testing[row.id]">
              测试连接
            </el-button>
            <el-button size="small" @click="editConfig(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteConfig(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="showCreateDialog"
      :title="editingConfig ? '编辑配置' : '添加配置'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入配置名称" />
        </el-form-item>
        <el-form-item label="服务类型" prop="service_type">
          <el-select v-model="form.service_type" placeholder="选择服务类型" style="width: 100%">
            <el-option label="OpenAI" value="openai" />
            <el-option label="Azure OpenAI" value="azure" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="通义千问" value="qwen" />
            <el-option label="硅基流动" value="siliconflow" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色类型" prop="role">
          <el-select v-model="form.role" placeholder="选择角色类型" style="width: 100%">
            <el-option label="API文档提取" value="doc_extractor" />
            <el-option label="参数命名规范化" value="naming" />
            <el-option label="模拟数据生成" value="mock_data" />
            <el-option label="参数描述补全" value="description" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input v-model="form.api_key" type="password" placeholder="请输入API Key" show-password />
        </el-form-item>
        <el-form-item label="API Base URL" prop="base_url">
          <el-input v-model="form.base_url" placeholder="请输入API Base URL，例如：https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="模型名称" prop="model_name">
          <el-input v-model="form.model_name" placeholder="请输入模型名称，例如：gpt-4" />
        </el-form-item>
        <el-form-item label="最大Token数" prop="max_tokens">
          <el-input-number v-model="form.max_tokens" :min="100" :max="32000" :step="100" />
        </el-form-item>
        <el-form-item label="温度参数" prop="temperature">
          <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-input />
        </el-form-item>
        <el-form-item label="是否启用" prop="is_active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveConfig" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'

const loading = ref(false)
const configs = ref([])
const showCreateDialog = ref(false)
const editingConfig = ref(null)
const saving = ref(false)
const testing = ref({})
const formRef = ref(null)

const form = reactive({
  name: '',
  service_type: '',
  role: '',
  api_key: '',
  base_url: '',
  model_name: '',
  max_tokens: 4096,
  temperature: 0.7,
  is_active: true
})

const rules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  service_type: [{ required: true, message: '请选择服务类型', trigger: 'change' }],
  role: [{ required: true, message: '请选择角色类型', trigger: 'change' }],
  api_key: [{ required: true, message: '请输入API Key', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入API Base URL', trigger: 'blur' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }]
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadConfigs = async () => {
  loading.value = true
  try {
    const res = await api.get('/api-testing/ai-service-configs/')
    configs.value = res.data.results || res.data
  } catch (error) {
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

const editConfig = (config) => {
  editingConfig.value = config
  Object.assign(form, {
    name: config.name,
    service_type: config.service_type,
    role: config.role,
    api_key: config.api_key,
    base_url: config.base_url,
    model_name: config.model_name,
    max_tokens: config.max_tokens,
    temperature: config.temperature,
    is_active: config.is_active
  })
  showCreateDialog.value = true
}

const saveConfig = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch (error) {
    return
  }

  saving.value = true
  try {
    if (editingConfig.value) {
      await api.put(`/api-testing/ai-service-configs/${editingConfig.value.id}/`, form)
      ElMessage.success('更新成功')
    } else {
      await api.post('/api-testing/ai-service-configs/', form)
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    resetForm()
    await loadConfigs()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const deleteConfig = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除此配置吗？', '提示', {
      type: 'warning'
    })
    await api.delete(`/api-testing/ai-service-configs/${id}/`)
    ElMessage.success('删除成功')
    await loadConfigs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const testConnection = async (config) => {
  testing.value[config.id] = true
  try {
    await api.post('/api-testing/ai-service-configs/test_connection/', {
      config_id: config.id
    })
    ElMessage.success('连接测试成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '连接测试失败')
  } finally {
    testing.value[config.id] = false
  }
}

const resetForm = () => {
  editingConfig.value = null
  Object.assign(form, {
    name: '',
    service_type: '',
    role: '',
    api_key: '',
    base_url: '',
    model_name: '',
    max_tokens: 4096,
    temperature: 0.7,
    is_active: true
  })
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.ai-service-config {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.config-list {
  flex: 1;
  overflow: auto;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table .cell) {
  padding: 8px 0;
}
</style>
