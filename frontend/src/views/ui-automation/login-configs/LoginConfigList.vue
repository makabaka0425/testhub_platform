<template>
  <div class="page-container">
    <div class="page-titlebar">
      <h1 class="page-title">登录配置</h1>
      <div class="titlebar-actions">
        <el-select v-model="projectId" placeholder="请选择项目" class="titlebar-select" @change="onProjectChange">
          <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
        <el-button type="primary" size="small" @click="handleNewConfig">新建登录配置</el-button>
      </div>
    </div>

    <div class="workspace">
      <div class="list-column">
        <!-- 搜索区域卡片 -->
        <div class="filter-bar">
          <el-form :inline="true">
            <el-form-item label="名称">
              <el-input
                v-model="searchText"
                placeholder="搜索登录配置名称"
                clearable
                style="width: 200px"
                @input="handleSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-form>
        </div>

        <!-- 列表面板 -->
        <section class="panel list-panel">
          <div class="panel__header">
            <span class="panel__title">配置列表</span>
          </div>

          <div class="panel__body login-config-table-wrapper">
            <el-table :data="loginConfigs" v-loading="loading" style="width: 100%">
              <el-table-column prop="name" label="名称" min-width="150">
                <template #default="{ row }">
                  <el-link @click="editConfig(row.id)" type="primary">
                    {{ row.name }}
                  </el-link>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
              <el-table-column prop="login_url" label="登录页URL" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">
                  {{ row.login_url || '使用项目默认URL' }}
                </template>
              </el-table-column>
              <el-table-column label="登录用例" min-width="150">
                <template #default="{ row }">
                  <el-tag v-if="row.login_test_case_name" size="small" type="success">
                    {{ row.login_test_case_name }}
                  </el-tag>
                  <span v-else style="color: #909399;">未关联</span>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="创建时间" width="180" :formatter="formatDate" />
              <el-table-column label="操作" width="220">
                <template #default="{ row }">
                  <div class="op-btns">
                    <el-button class="op-btn" link type="primary" size="small" @click="editConfig(row.id)">编辑</el-button>
                    <el-button class="op-btn" link type="success" size="small" @click="handleTestLogin(row)">测试登录</el-button>
                    <el-button class="op-btn op-btn--danger" link size="small" @click="deleteConfig(row.id)">删除</el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>

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
        </section>
      </div>
    </div>

    <!-- 创建/编辑登录配置对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="isEditing ? '编辑登录配置' : '新建登录配置'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="createFormRef" :model="createForm" :rules="formRules" label-width="120px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="createForm.description" type="textarea" placeholder="请输入描述" />
        </el-form-item>

        <el-divider content-position="left">登录页配置</el-divider>
        <el-form-item label="登录页URL" prop="login_url">
          <el-input v-model="createForm.login_url" placeholder="可选，留空则使用项目基础URL" />
        </el-form-item>

        <el-divider content-position="left">登录用例</el-divider>
        <el-form-item label="登录测试用例" prop="login_test_case">
          <el-select
            v-model="createForm.login_test_case"
            placeholder="请选择登录测试用例"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="tc in testCases"
              :key="tc.id"
              :label="tc.name"
              :value="tc.id"
            >
              <span>{{ tc.name }}</span>
              <el-tag size="small" :type="getStatusTag(tc.status)" style="margin-left: 8px;">
                {{ getStatusText(tc.status) }}
              </el-tag>
            </el-option>
          </el-select>
          <div v-if="!testCases.length" style="color: #909399; font-size: 12px; margin-top: 4px;">
            当前项目暂无测试用例，请先在用例管理中创建登录用例
          </div>
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import {
  getUiProjects,
  getLoginConfigs,
  createLoginConfig,
  getLoginConfigDetail,
  updateLoginConfig,
  deleteLoginConfig,
  testLoginConfig,
  getTestCases
} from '@/api/ui_automation'

// 响应式数据
const projects = ref([])
const projectId = ref('')
const loginConfigs = ref([])
const testCases = ref([])
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
  login_test_case: null
})

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  login_test_case: [{ required: true, message: '请选择登录测试用例', trigger: 'change' }]
}

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

// 加载测试用例列表（当前项目下的）
const loadTestCases = async () => {
  if (!projectId.value) {
    testCases.value = []
    return
  }
  try {
    const response = await getTestCases({
      project: projectId.value,
      page_size: 200
    })
    testCases.value = response.data.results || response.data
  } catch (error) {
    console.error('获取测试用例列表失败:', error)
    ElMessage.error('获取测试用例列表失败')
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
  await Promise.all([loadTestCases(), loadLoginConfigs()])
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
  createForm.login_test_case = null
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
  await loadTestCases()
  showCreateDialog.value = true
}

// 编辑登录配置
const editConfig = async (id) => {
  try {
    await loadTestCases()
    const response = await getLoginConfigDetail(id)
    const data = response.data
    currentConfigId.value = id
    isEditing.value = true
    createForm.name = data.name || ''
    createForm.description = data.description || ''
    createForm.login_url = data.login_url || ''
    createForm.login_test_case = data.login_test_case || null
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
        project_id: projectId.value,
        name: createForm.name,
        description: createForm.description,
        login_url: createForm.login_url,
        login_test_case: createForm.login_test_case
      }

      if (isEditing.value) {
        // 更新时不发送 project_id
        delete configData.project_id
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

const getStatusText = (status) => {
  const map = { draft: '草稿', ready: '就绪', running: '执行中', passed: '通过', failed: '失败' }
  return map[status] || status
}

const getStatusTag = (status) => {
  const map = { draft: 'info', ready: 'success', running: 'warning', passed: 'success', failed: 'danger' }
  return map[status] || 'info'
}

// 初始化
onMounted(async () => {
  await loadProjects()
  if (projects.value.length > 0) {
    projectId.value = projects.value[0].id
    await Promise.all([loadTestCases(), loadLoginConfigs()])
  }
})
</script>

<style scoped lang="scss">
/* ============================================================
   页面容器 / 标题栏 / 工作区（参照套件管理）
   ============================================================ */
.page-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}

.page-titlebar {
  height: 64px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--gray-900);
  margin: 0;
  letter-spacing: -0.02em;
}

.titlebar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.titlebar-select {
  width: 200px;
}

.workspace {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 0;
  gap: var(--space-4);
  min-height: 0;
}

.list-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.list-column .filter-bar {
  margin-bottom: 0;
}

.list-panel {
  flex: 1;
  min-width: 0;
}

.list-panel .panel__body {
  padding: 0;
}

.login-config-table-wrapper {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

/* 表格样式 */
.list-panel :deep(.el-table) {
  --el-table-border-color: var(--gray-200);
  --el-table-header-bg-color: var(--gray-50);
  --el-table-tr-bg-color: var(--gray-0);
}

.list-panel :deep(.el-table th.el-table__cell) {
  background: var(--gray-100);
  color: var(--gray-500);
  font-size: 12px;
  font-weight: 500;
}

.list-panel :deep(.el-table .el-table__cell) {
  padding: 4px 0;
}

.list-panel :deep(.el-table .el-table__body tr) {
  height: 40px;
}

.list-panel :deep(.el-table .el-table__body tr:hover > td.el-table__cell) {
  background: var(--gray-50) !important;
}

/* 分页 */
.pagination-container {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid var(--gray-100);
  flex-shrink: 0;
  background: var(--gray-0);
}

/* 操作按钮 */
.op-btns {
  display: flex;
  align-items: center;
  gap: 0;
}

.op-btn {
  --el-button-text-color: var(--brand-500, #4f8cff);
  padding: 2px 4px !important;
  border-radius: var(--radius-sm, 6px);
}

.op-btn--danger {
  --el-button-text-color: #f56c6c;
}
</style>
