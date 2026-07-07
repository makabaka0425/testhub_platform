<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">登录配置</h1>
      <div style="display: flex; align-items: center; gap: 15px;">
        <el-select v-model="projectId" placeholder="请选择项目" style="width: 200px;" @change="onProjectChange">
          <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
        <el-button type="primary" @click="handleNewConfig">
          <el-icon><Plus /></el-icon>
          新建登录配置
        </el-button>
      </div>
    </div>

    <div class="card-container">
      <div class="filter-bar">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-input
              v-model="searchText"
              placeholder="搜索登录配置名称"
              clearable
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
        </el-row>
      </div>

      <el-table :data="loginConfigs" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="150">
          <template #default="{ row }">
            <el-link @click="editConfig(row.id)" type="primary">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
        <el-table-column prop="login_url" label="登录页URL" min-width="200" show-overflow-tooltip />
        <el-table-column label="验证方式" width="130">
          <template #default="{ row }">
            <el-tag size="small" :type="getVerifyTypeTag(row.verify_type)">
              {{ getVerifyTypeText(row.verify_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" :formatter="formatDate" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="editConfig(row.id)">编辑</el-button>
            <el-button link type="success" @click="handleTestLogin(row)">测试登录</el-button>
            <el-button link type="danger" @click="deleteConfig(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 创建/编辑登录配置对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="isEditing ? '编辑登录配置' : '新建登录配置'"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form ref="createFormRef" :model="createForm" :rules="formRules" label-width="120px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="createForm.description" type="textarea" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="登录页URL" prop="login_url">
          <el-input v-model="createForm.login_url" placeholder="请输入登录页URL，如 https://example.com/login" />
        </el-form-item>

        <el-divider content-position="left">用户名配置</el-divider>
        <el-form-item label="用户名元素" prop="username_element">
          <el-select v-model="createForm.username_element" placeholder="请选择用户名输入框元素" filterable clearable style="width: 100%">
            <el-option v-for="el in elements" :key="el.id" :label="el.name" :value="el.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户名值" prop="username_value">
          <el-input v-model="createForm.username_value" placeholder="请输入用户名" />
        </el-form-item>

        <el-divider content-position="left">密码配置</el-divider>
        <el-form-item label="密码元素" prop="password_element">
          <el-select v-model="createForm.password_element" placeholder="请选择密码输入框元素" filterable clearable style="width: 100%">
            <el-option v-for="el in elements" :key="el.id" :label="el.name" :value="el.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="密码值" prop="password_value">
          <el-input v-model="createForm.password_value" type="password" show-password placeholder="请输入密码" />
        </el-form-item>

        <el-divider content-position="left">登录按钮配置</el-divider>
        <el-form-item label="登录按钮元素" prop="login_button_element">
          <el-select v-model="createForm.login_button_element" placeholder="请选择登录按钮元素" filterable clearable style="width: 100%">
            <el-option v-for="el in elements" :key="el.id" :label="el.name" :value="el.id" />
          </el-select>
        </el-form-item>

        <el-divider content-position="left">登录验证配置</el-divider>
        <el-form-item label="验证方式" prop="verify_type">
          <el-select v-model="createForm.verify_type" placeholder="请选择验证方式" style="width: 100%">
            <el-option label="URL包含指定字符串" value="url_contains" />
            <el-option label="指定元素可见" value="element_visible" />
            <el-option label="指定元素存在" value="element_exists" />
            <el-option label="指定Cookie存在" value="cookie_exists" />
            <el-option label="仅等待固定时间" value="wait_time" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="needsVerifyElement" label="验证元素" prop="verify_element">
          <el-select v-model="createForm.verify_element" placeholder="请选择验证元素" filterable clearable style="width: 100%">
            <el-option v-for="el in elements" :key="el.id" :label="el.name" :value="el.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="needsVerifyValue" label="验证值" prop="verify_value">
          <el-input v-model="createForm.verify_value" :placeholder="getVerifyValuePlaceholder()" />
        </el-form-item>
        <el-form-item label="验证等待时间" prop="verify_wait_time">
          <el-input-number v-model="createForm.verify_wait_time" :min="0" :max="60" :step="1" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px;">秒</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cancelCreate">取消</el-button>
          <el-button type="primary" @click="handleCreate" :loading="saving">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import {
  getUiProjects,
  getElements,
  getLoginConfigs,
  createLoginConfig,
  getLoginConfigDetail,
  updateLoginConfig,
  deleteLoginConfig,
  testLoginConfig
} from '@/api/ui_automation'

// 响应式数据
const projects = ref([])
const projectId = ref('')
const loginConfigs = ref([])
const elements = ref([])
const loading = ref(false)
const searchText = ref('')
const total = ref(0)
const pagination = reactive({
  currentPage: 1,
  pageSize: 20
})

// 对话框控制
const showCreateDialog = ref(false)
const isEditing = ref(false)
const currentConfigId = ref(null)
const saving = ref(false)
const testing = ref(false)

// 表单数据 — 字段名与后端模型保持一致
const createFormRef = ref(null)
const createForm = reactive({
  name: '',
  description: '',
  login_url: '',
  username_element: null,
  username_value: '',
  password_element: null,
  password_value: '',
  login_button_element: null,
  verify_type: 'element_visible',
  verify_element: null,
  verify_value: '',
  verify_wait_time: 5  // 前端显示秒，提交时转为毫秒
})

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  login_url: [{ required: true, message: '请输入登录页URL', trigger: 'blur' }],
  username_element: [{ required: true, message: '请选择用户名元素', trigger: 'change' }],
  password_element: [{ required: true, message: '请选择密码元素', trigger: 'change' }],
  login_button_element: [{ required: true, message: '请选择登录按钮元素', trigger: 'change' }],
  verify_type: [{ required: true, message: '请选择验证方式', trigger: 'change' }]
}

// 计算属性 - 是否需要验证元素 (element_visible / element_exists)
const needsVerifyElement = computed(() => {
  return ['element_visible', 'element_exists'].includes(createForm.verify_type)
})

// 计算属性 - 是否需要验证值 (url_contains / cookie_exists)
const needsVerifyValue = computed(() => {
  return ['url_contains', 'cookie_exists'].includes(createForm.verify_type)
})

// 加载项目列表
const loadProjects = async () => {
  try {
    const response = await getUiProjects({ page_size: 100 })
    projects.value = response.data.results || response.data
  } catch (error) {
    console.error('获取项目列表失败:', error)
    ElMessage.error('获取项目列表失败')
  }
}

// 加载元素列表
const loadElements = async () => {
  if (!projectId.value) {
    elements.value = []
    return
  }
  try {
    const response = await getElements({
      project: projectId.value,
      page_size: 1000
    })
    elements.value = response.data.results || response.data
  } catch (error) {
    console.error('获取元素列表失败:', error)
    ElMessage.error('获取元素列表失败')
  }
}

// 加载登录配置列表
const loadLoginConfigs = async () => {
  if (!projectId.value) {
    loginConfigs.value = []
    total.value = 0
    return
  }

  loading.value = true
  try {
    const response = await getLoginConfigs({
      project: projectId.value,
      page: pagination.currentPage,
      page_size: pagination.pageSize,
      search: searchText.value
    })

    if (response.data.results) {
      loginConfigs.value = response.data.results
      total.value = response.data.count || 0
    } else {
      loginConfigs.value = response.data
      total.value = response.data.length
    }
  } catch (error) {
    console.error('获取登录配置列表失败:', error)
    ElMessage.error('获取登录配置列表失败')
  } finally {
    loading.value = false
  }
}

// 项目切换
const onProjectChange = async () => {
  pagination.currentPage = 1
  await Promise.all([loadElements(), loadLoginConfigs()])
}

// 搜索处理
const handleSearch = async () => {
  pagination.currentPage = 1
  await loadLoginConfigs()
}

// 分页处理
const handleSizeChange = async () => {
  pagination.currentPage = 1
  await loadLoginConfigs()
}

const handleCurrentChange = async () => {
  await loadLoginConfigs()
}

// 重置表单
const resetForm = () => {
  createForm.name = ''
  createForm.description = ''
  createForm.login_url = ''
  createForm.username_element = null
  createForm.username_value = ''
  createForm.password_element = null
  createForm.password_value = ''
  createForm.login_button_element = null
  createForm.verify_type = 'element_visible'
  createForm.verify_element = null
  createForm.verify_value = ''
  createForm.verify_wait_time = 5
  isEditing.value = false
  currentConfigId.value = null
}

// 新建登录配置
const handleNewConfig = async () => {
  if (!projectId.value) {
    ElMessage.warning('请先选择项目')
    return
  }
  resetForm()
  await loadElements()
  showCreateDialog.value = true
}

// 编辑登录配置
const editConfig = async (id) => {
  try {
    await loadElements()
    const response = await getLoginConfigDetail(id)
    const data = response.data
    currentConfigId.value = id
    isEditing.value = true
    createForm.name = data.name || ''
    createForm.description = data.description || ''
    createForm.login_url = data.login_url || ''
    createForm.username_element = data.username_element || null
    createForm.username_value = data.username_value || ''
    createForm.password_element = data.password_element || null
    createForm.password_value = data.password_value || ''
    createForm.login_button_element = data.login_button_element || null
    createForm.verify_type = data.verify_type || 'element_visible'
    createForm.verify_element = data.verify_element || null
    createForm.verify_value = data.verify_value || ''
    // 后端存毫秒，前端显示秒
    createForm.verify_wait_time = data.verify_wait_time ? Math.round(data.verify_wait_time / 1000) : 5
    showCreateDialog.value = true
  } catch (error) {
    console.error('加载登录配置详情失败:', error)
    ElMessage.error('加载登录配置详情失败')
  }
}

// 创建/更新登录配置
const handleCreate = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (!valid) return

    if (!projectId.value) {
      ElMessage.warning('请先选择项目')
      return
    }

    saving.value = true
    try {
      const configData = {
        project: projectId.value,
        name: createForm.name,
        description: createForm.description,
        login_url: createForm.login_url,
        username_element: createForm.username_element,
        username_value: createForm.username_value,
        password_element: createForm.password_element,
        password_value: createForm.password_value,
        login_button_element: createForm.login_button_element,
        verify_type: createForm.verify_type,
        verify_element: needsVerifyElement.value ? createForm.verify_element : null,
        verify_value: needsVerifyValue.value ? createForm.verify_value : '',
        // 前端秒 → 后端毫秒
        verify_wait_time: createForm.verify_wait_time * 1000
      }

      if (isEditing.value) {
        await updateLoginConfig(currentConfigId.value, configData)
        ElMessage.success('更新登录配置成功')
      } else {
        await createLoginConfig(configData)
        ElMessage.success('创建登录配置成功')
      }

      showCreateDialog.value = false
      await loadLoginConfigs()
      resetForm()
    } catch (error) {
      console.error('保存登录配置失败:', error)
      const errorMsg = error.response?.data?.detail || error.response?.data?.error || '保存登录配置失败'
      ElMessage.error(errorMsg)
    } finally {
      saving.value = false
    }
  })
}

// 删除登录配置
const deleteConfig = async (id) => {
  try {
    await ElMessageBox.confirm('确认删除该登录配置吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await deleteLoginConfig(id)
    ElMessage.success('删除登录配置成功')
    await loadLoginConfigs()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除登录配置失败:', error)
      ElMessage.error('删除登录配置失败')
    }
  }
}

// 测试登录配置
const handleTestLogin = async (row) => {
  testing.value = true
  try {
    ElMessage.info(`正在测试登录配置「${row.name}」，请稍候...`)
    const response = await testLoginConfig(row.id)
    if (response.data.success) {
      ElMessage.success('登录测试成功')
    } else {
      ElMessage.error(response.data.message || '登录测试失败')
    }
  } catch (error) {
    console.error('测试登录配置失败:', error)
    const errorMsg = error.response?.data?.detail || error.response?.data?.error || error.response?.data?.message || '测试登录配置失败'
    ElMessage.error(errorMsg)
  } finally {
    testing.value = false
  }
}

// 取消创建
const cancelCreate = () => {
  showCreateDialog.value = false
  resetForm()
}

// 辅助方法
const formatDate = (row, column, cellValue) => {
  if (!cellValue) return ''
  return new Date(cellValue).toLocaleString()
}

const getVerifyTypeText = (type) => {
  const typeMap = {
    'url_contains': 'URL包含',
    'element_visible': '元素可见',
    'element_exists': '元素存在',
    'cookie_exists': 'Cookie存在',
    'wait_time': '等待时间'
  }
  return typeMap[type] || type || '未知'
}

const getVerifyTypeTag = (type) => {
  const tagMap = {
    'url_contains': 'primary',
    'element_visible': 'success',
    'element_exists': 'warning',
    'cookie_exists': 'info',
    'wait_time': 'info'
  }
  return tagMap[type] || 'info'
}

const getVerifyValuePlaceholder = () => {
  const placeholderMap = {
    'url_contains': '请输入期望包含的URL片段',
    'cookie_exists': '请输入Cookie名称'
  }
  return placeholderMap[createForm.verify_type] || '请输入验证值'
}

// 初始化
onMounted(async () => {
  await loadProjects()
  if (projects.value.length > 0) {
    projectId.value = projects.value[0].id
    await Promise.all([loadElements(), loadLoginConfigs()])
  }
})
</script>

<style scoped lang="scss">
.page-container {
  padding: 20px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: white;
  padding: 20px;
  border-radius: 4px;
}

.page-title {
  margin: 0;
  font-size: 24px;
}

.card-container {
  background: white;
  padding: 20px;
  border-radius: 4px;
}

.filter-bar {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
