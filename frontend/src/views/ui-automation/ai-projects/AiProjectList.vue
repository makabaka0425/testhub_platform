<template>
  <div class="page-container">
    <div class="page-titlebar">
      <h1 class="page-title">AI自动化项目管理</h1>
      <div class="titlebar-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建项目
        </el-button>
      </div>
    </div>

    <div class="workspace">
      <div class="list-column">
        <!-- 搜索区域卡片 -->
        <div class="filter-bar">
          <el-form :inline="true">
            <el-form-item>
              <el-input
                v-model="searchText"
                placeholder="搜索项目名称"
                clearable
                style="width: 200px"
                @input="handleSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-select v-model="statusFilter" placeholder="项目状态" clearable style="width: 130px" @change="handleFilter">
                <el-option label="未开始" value="NOT_STARTED" />
                <el-option label="进行中" value="IN_PROGRESS" />
                <el-option label="已结束" value="COMPLETED" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- 项目列表面板 -->
        <section class="panel list-panel">
          <div class="panel__header">
            <span class="panel__title">项目列表</span>
          </div>

          <div class="panel__body project-table-wrapper">
            <el-table :data="projects" v-loading="loading" height="100%">
              <el-table-column type="index" label="序号" width="50" align="center" />
              <el-table-column prop="name" label="项目名称" min-width="200">
                <template #default="{ row }">
                  <el-link @click="viewProject(row)" type="primary">
                    {{ row.name }}
                  </el-link>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="default_platform" label="默认平台" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.default_platform === 'web' ? 'primary' : 'success'" size="small">
                    {{ row.default_platform === 'web' ? 'Web' : 'APP' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="owner.username" label="负责人" width="100" />
              <el-table-column prop="created_at" label="创建时间" width="180" :formatter="formatDate" />
              <el-table-column prop="updated_at" label="更新时间" width="180" :formatter="formatDate" />
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="{ row }">
                  <ActionCell :actions="getProjectActions(row)" :row="row" :max-visible="3" />
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

    <!-- 创建项目对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建AI自动化项目" width="600px" :close-on-click-modal="false">
      <el-form ref="createFormRef" :model="createForm" :rules="formRules" label-width="80px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input v-model="createForm.description" type="textarea" placeholder="请输入项目描述" />
        </el-form-item>
        <el-form-item label="项目状态" prop="status">
          <el-select v-model="createForm.status" placeholder="请选择状态">
            <el-option label="未开始" value="NOT_STARTED" />
            <el-option label="进行中" value="IN_PROGRESS" />
            <el-option label="已结束" value="COMPLETED" />
          </el-select>
        </el-form-item>
        <el-form-item label="默认平台" prop="default_platform">
          <el-select v-model="createForm.default_platform" placeholder="请选择默认平台">
            <el-option label="Web端" value="web" />
            <el-option label="APP端" value="app" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker v-model="createForm.start_date" type="date" placeholder="选择开始日期" />
        </el-form-item>
        <el-form-item label="结束日期" prop="end_date">
          <el-date-picker v-model="createForm.end_date" type="date" placeholder="选择结束日期" />
        </el-form-item>
      </el-form>
      <el-divider content-position="left">数据库配置</el-divider>
      <el-form ref="createDbFormRef" :model="createForm" label-width="110px">
        <el-form-item label="数据库类型" prop="target_db_type">
          <el-select v-model="createForm.target_db_type" placeholder="请选择数据库类型" clearable style="width:100%">
            <el-option label="MySQL" value="mysql" />
            <el-option label="PostgreSQL" value="postgresql" />
            <el-option label="SQLite" value="sqlite" />
            <el-option label="Oracle" value="oracle" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.target_db_type && createForm.target_db_type !== 'sqlite'" label="数据库地址">
          <div style="display:flex;gap:8px;width:100%">
            <el-input v-model="createForm.target_db_host" placeholder="如 192.168.1.100" style="flex:1" />
            <el-input v-model="createForm.target_db_port" placeholder="端口" style="width:100px" />
          </div>
        </el-form-item>
        <el-form-item label="数据库名" prop="target_db_name">
          <el-input v-model="createForm.target_db_name" :placeholder="createForm.target_db_type === 'sqlite' ? 'SQLite文件路径' : '请输入数据库名'" />
        </el-form-item>
        <el-form-item v-if="createForm.target_db_type && createForm.target_db_type !== 'sqlite'" label="数据库用户">
          <div style="display:flex;gap:8px;width:100%">
            <el-input v-model="createForm.target_db_user" placeholder="用户名" style="flex:1" />
            <el-input v-model="createForm.target_db_password" type="password" placeholder="密码" show-password style="flex:1" />
          </div>
        </el-form-item>
        <el-form-item v-if="createForm.target_db_type" label="">
          <el-button type="success" size="small" :loading="createTestDbLoading" @click="handleCreateTestDbConnection">测试连接</el-button>
          <span v-if="createTestDbResult" :style="{ color: createTestDbResult.success ? '#67c23a' : '#f56c6c', marginLeft: '8px' }">
            {{ createTestDbResult.success ? `连接成功 (${createTestDbResult.elapsed_ms}ms)` : `连接失败: ${createTestDbResult.error}` }}
          </span>
          <span v-if="createTestDbResult && createTestDbResult.success && createTestDbResult.db_version" style="margin-left: 8px; color: #909399">
            {{ createTestDbResult.db_version }}
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="handleCreate">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑项目对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑AI自动化项目" width="600px" :close-on-click-modal="false">
      <el-form ref="editFormRef" :model="editForm" :rules="formRules" label-width="80px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input v-model="editForm.description" type="textarea" placeholder="请输入项目描述" />
        </el-form-item>
        <el-form-item label="项目状态" prop="status">
          <el-select v-model="editForm.status" placeholder="请选择状态">
            <el-option label="未开始" value="NOT_STARTED" />
            <el-option label="进行中" value="IN_PROGRESS" />
            <el-option label="已结束" value="COMPLETED" />
          </el-select>
        </el-form-item>
        <el-form-item label="默认平台" prop="default_platform">
          <el-select v-model="editForm.default_platform" placeholder="请选择默认平台">
            <el-option label="Web端" value="web" />
            <el-option label="APP端" value="app" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker v-model="editForm.start_date" type="date" placeholder="选择开始日期" />
        </el-form-item>
        <el-form-item label="结束日期" prop="end_date">
          <el-date-picker v-model="editForm.end_date" type="date" placeholder="选择结束日期" />
        </el-form-item>
      </el-form>
      <el-divider content-position="left">数据库配置</el-divider>
      <el-form :model="editForm" label-width="110px">
        <el-form-item label="数据库类型" prop="target_db_type">
          <el-select v-model="editForm.target_db_type" placeholder="请选择数据库类型" clearable style="width:100%">
            <el-option label="MySQL" value="mysql" />
            <el-option label="PostgreSQL" value="postgresql" />
            <el-option label="SQLite" value="sqlite" />
            <el-option label="Oracle" value="oracle" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editForm.target_db_type && editForm.target_db_type !== 'sqlite'" label="数据库地址">
          <div style="display:flex;gap:8px;width:100%">
            <el-input v-model="editForm.target_db_host" placeholder="如 192.168.1.100" style="flex:1" />
            <el-input v-model="editForm.target_db_port" placeholder="端口" style="width:100px" />
          </div>
        </el-form-item>
        <el-form-item label="数据库名" prop="target_db_name">
          <el-input v-model="editForm.target_db_name" :placeholder="editForm.target_db_type === 'sqlite' ? 'SQLite文件路径' : '请输入数据库名'" />
        </el-form-item>
        <el-form-item v-if="editForm.target_db_type && editForm.target_db_type !== 'sqlite'" label="数据库用户">
          <div style="display:flex;gap:8px;width:100%">
            <el-input v-model="editForm.target_db_user" placeholder="用户名" style="flex:1" />
            <el-input v-model="editForm.target_db_password" type="password" placeholder="密码" show-password style="flex:1" />
          </div>
        </el-form-item>
        <el-form-item v-if="editForm.target_db_type" label="">
          <el-button type="success" size="small" :loading="editTestDbLoading" @click="handleEditTestDbConnection">测试连接</el-button>
          <span v-if="editTestDbResult" :style="{ color: editTestDbResult.success ? '#67c23a' : '#f56c6c', marginLeft: '8px' }">
            {{ editTestDbResult.success ? `连接成功 (${editTestDbResult.elapsed_ms}ms)` : `连接失败: ${editTestDbResult.error}` }}
          </span>
          <span v-if="editTestDbResult && editTestDbResult.success && editTestDbResult.db_version" style="margin-left: 8px; color: #909399">
            {{ editTestDbResult.db_version }}
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="handleEdit">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 项目详情弹框 -->
    <el-dialog v-model="showDetailDialog" title="项目详情" width="600px">
      <div v-if="currentProject" class="project-detail">
        <el-descriptions bordered column="1">
          <el-descriptions-item label="项目名称">{{ currentProject.name }}</el-descriptions-item>
          <el-descriptions-item label="项目描述">{{ currentProject.description || '暂无描述' }}</el-descriptions-item>
          <el-descriptions-item label="项目状态">
            <el-tag :type="getStatusType(currentProject.status)">{{ getStatusText(currentProject.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="默认平台">
            <el-tag :type="currentProject.default_platform === 'web' ? 'primary' : 'success'" size="small">
              {{ currentProject.default_platform === 'web' ? 'Web端' : 'APP端' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="负责人">{{ currentProject.owner?.username || '无' }}</el-descriptions-item>
          <el-descriptions-item label="开始日期">{{ currentProject.start_date || '未设置' }}</el-descriptions-item>
          <el-descriptions-item label="结束日期">{{ currentProject.end_date || '未设置' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(null, null, currentProject.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDate(null, null, currentProject.updated_at) }}</el-descriptions-item>
          <el-descriptions-item label="数据库类型">{{ currentProject.target_db_type ? getDbTypeLabel(currentProject.target_db_type) : '未配置' }}</el-descriptions-item>
          <el-descriptions-item v-if="currentProject.target_db_type && currentProject.target_db_type !== 'sqlite'" label="数据库地址">{{ currentProject.target_db_host || '-' }}:{{ currentProject.target_db_port || '-' }}</el-descriptions-item>
          <el-descriptions-item v-if="currentProject.target_db_type" label="数据库名">{{ currentProject.target_db_name || '-' }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showDetailDialog = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { getAiProjects, createAiProject, updateAiProject, deleteAiProject, aiTestDbConnection } from '@/api/ui_automation'
import ActionCell from '@/components/ActionCell.vue'

// 项目数据
const projects = ref([])
const loading = ref(false)
const total = ref(0)
const pagination = reactive({
  currentPage: 1,
  pageSize: 10
})

// 搜索和筛选
const searchText = ref('')
const statusFilter = ref('')

// 表单相关
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showDetailDialog = ref(false)
const createFormRef = ref(null)
const editFormRef = ref(null)
const currentEditId = ref(null)
const currentProject = ref(null)

// 测试数据库连接相关（新建/编辑各自独立状态）
const createTestDbLoading = ref(false)
const createTestDbResult = ref(null)
const editTestDbLoading = ref(false)
const editTestDbResult = ref(null)

const getDbTypeLabel = (type) => {
  const map = { mysql: 'MySQL', postgresql: 'PostgreSQL', sqlite: 'SQLite', oracle: 'Oracle' }
  return map[type] || type
}

// 表单数据
const createForm = reactive({
  name: '',
  description: '',
  status: 'IN_PROGRESS',
  default_platform: 'web',
  start_date: null,
  end_date: null,
  target_db_type: '',
  target_db_host: '',
  target_db_port: '',
  target_db_name: '',
  target_db_user: '',
  target_db_password: ''
})

const editForm = reactive({
  name: '',
  description: '',
  status: 'IN_PROGRESS',
  default_platform: 'web',
  start_date: null,
  end_date: null,
  target_db_type: '',
  target_db_host: '',
  target_db_port: '',
  target_db_name: '',
  target_db_user: '',
  target_db_password: ''
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 200, message: '项目名称长度2-200个字符', trigger: 'blur' }
  ]
}

// 格式化日期
const formatDate = (row, column, cellValue) => {
  if (!cellValue) return ''
  return new Date(cellValue).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 获取状态样式
const getStatusType = (status) => {
  const statusMap = {
    'NOT_STARTED': 'warning',
    'IN_PROGRESS': 'primary',
    'COMPLETED': 'success'
  }
  return statusMap[status] || 'default'
}

// 获取状态文本
const getStatusText = (status) => {
  const map = {
    'NOT_STARTED': '未开始',
    'IN_PROGRESS': '进行中',
    'COMPLETED': '已结束'
  }
  return map[status] || status
}

// 日期格式化辅助函数
const formatDateToISO = (date) => {
  if (!date) return null
  const d = new Date(date)
  return d.toISOString().split('T')[0]
}

// 加载项目列表
const loadProjects = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      page_size: pagination.pageSize
    }
    if (searchText.value) {
      params.search = searchText.value
    }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    const response = await getAiProjects(params)
    projects.value = response.data.results || response.data
    total.value = response.data.count || projects.value.length
  } catch (error) {
    ElMessage.error('获取项目列表失败')
    console.error('获取项目列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.currentPage = 1
  loadProjects()
}

// 筛选处理
const handleFilter = () => {
  pagination.currentPage = 1
  loadProjects()
}

// 分页处理
const handleSizeChange = () => { loadProjects() }
const handleCurrentChange = () => { loadProjects() }

// 查看项目详情
const viewProject = (project) => {
  currentProject.value = project
  showDetailDialog.value = true
}

// 编辑项目
const editProject = (project) => {
  currentEditId.value = project.id
  Object.assign(editForm, {
    name: project.name,
    description: project.description,
    status: project.status,
    default_platform: project.default_platform || 'web',
    start_date: project.start_date ? new Date(project.start_date) : null,
    end_date: project.end_date ? new Date(project.end_date) : null,
    target_db_type: project.target_db_type || '',
    target_db_host: project.target_db_host || '',
    target_db_port: project.target_db_port || '',
    target_db_name: project.target_db_name || '',
    target_db_user: project.target_db_user || '',
    target_db_password: project.target_db_password || ''
  })
  editTestDbResult.value = null
  showEditDialog.value = true
}

// 删除项目
const deleteProject = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该项目吗？删除后不可恢复！', '确认删除', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteAiProject(id)
    ElMessage.success('项目删除成功')
    loadProjects()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error('删除项目失败')
    console.error('删除项目失败:', error)
  }
}

// 操作列 actions
const getProjectActions = (row) => [
  { key: 'view', label: '查看', onClick: () => viewProject(row) },
  { key: 'edit', label: '编辑', onClick: () => editProject(row) },
  { key: 'delete', label: '删除', danger: true, onClick: () => deleteProject(row.id) }
]

// 处理创建项目
const handleCreate = async () => {
  try {
    await createFormRef.value.validate()
  } catch { return }

  try {
    const { useUserStore } = await import('@/stores/user')
    const userStore = useUserStore()
    if (!userStore.user?.id) {
      await userStore.fetchProfile()
    }

    const projectData = {
      ...createForm,
      owner: userStore.user.id,
      start_date: formatDateToISO(createForm.start_date),
      end_date: formatDateToISO(createForm.end_date)
    }

    await createAiProject(projectData)
    ElMessage.success('项目创建成功')
    showCreateDialog.value = false

    // 重置表单
    Object.assign(createForm, {
      name: '',
      description: '',
      status: 'IN_PROGRESS',
      default_platform: 'web',
      start_date: null,
      end_date: null,
      target_db_type: '',
      target_db_host: '',
      target_db_port: '',
      target_db_name: '',
      target_db_user: '',
      target_db_password: ''
    })

    loadProjects()
  } catch (error) {
    const detail = error.response?.data?.detail || error.response?.data?.name?.[0] || '项目创建失败'
    ElMessage.error(detail)
    console.error('创建项目失败:', error)
  }
}

// 处理编辑项目
const handleEdit = async () => {
  try {
    await editFormRef.value.validate()
  } catch { return }

  try {
    const projectData = {
      ...editForm,
      start_date: formatDateToISO(editForm.start_date),
      end_date: formatDateToISO(editForm.end_date)
    }

    await updateAiProject(currentEditId.value, projectData)
    ElMessage.success('项目更新成功')
    showEditDialog.value = false
    loadProjects()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '项目更新失败')
    console.error('更新项目失败:', error)
  }
}

// 新建弹窗-测试数据库连接
const handleCreateTestDbConnection = async () => {
  if (!createForm.target_db_type) {
    ElMessage.warning('请先选择数据库类型')
    return
  }
  createTestDbLoading.value = true
  createTestDbResult.value = null
  try {
    const data = {
      target_db_type: createForm.target_db_type,
      target_db_host: createForm.target_db_host,
      target_db_port: createForm.target_db_port ? Number(createForm.target_db_port) : null,
      target_db_name: createForm.target_db_name,
      target_db_user: createForm.target_db_user,
      target_db_password: createForm.target_db_password
    }
    const res = await aiTestDbConnection(data)
    createTestDbResult.value = res.data
    if (res.data.success) {
      ElMessage.success(`数据库连接成功 (${res.data.elapsed_ms}ms)`)
    } else {
      ElMessage.error(res.data.error || '连接失败')
    }
  } catch (error) {
    createTestDbResult.value = { success: false, error: error.response?.data?.error || '连接测试失败' }
    ElMessage.error(createTestDbResult.value.error)
  } finally {
    createTestDbLoading.value = false
  }
}

// 编辑弹窗-测试数据库连接
const handleEditTestDbConnection = async () => {
  if (!editForm.target_db_type) {
    ElMessage.warning('请先选择数据库类型')
    return
  }
  editTestDbLoading.value = true
  editTestDbResult.value = null
  try {
    const data = {
      target_db_type: editForm.target_db_type,
      target_db_host: editForm.target_db_host,
      target_db_port: editForm.target_db_port ? Number(editForm.target_db_port) : null,
      target_db_name: editForm.target_db_name,
      target_db_user: editForm.target_db_user,
      target_db_password: editForm.target_db_password
    }
    const res = await aiTestDbConnection(data)
    editTestDbResult.value = res.data
    if (res.data.success) {
      ElMessage.success(`数据库连接成功 (${res.data.elapsed_ms}ms)`)
    } else {
      ElMessage.error(res.data.error || '连接失败')
    }
  } catch (error) {
    editTestDbResult.value = { success: false, error: error.response?.data?.error || '连接测试失败' }
    ElMessage.error(editTestDbResult.value.error)
  } finally {
    editTestDbLoading.value = false
  }
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped lang="scss">
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

.project-table-wrapper {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

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

.pagination-container {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid var(--gray-100);
  flex-shrink: 0;
  background: var(--gray-0);
}

.project-detail {
  max-height: 60vh;
  overflow-y: auto;
}
</style>
