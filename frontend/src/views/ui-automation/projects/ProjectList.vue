<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">{{ $t('uiAutomation.project.title') }}</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        {{ $t('uiAutomation.project.newProject') }}
      </el-button>
    </div>
    
    <div class="filter-bar">
      <el-form :inline="true">
        <el-form-item>
          <el-input
            v-model="searchText"
            :placeholder="$t('uiAutomation.project.searchPlaceholder')"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-select v-model="statusFilter" :placeholder="$t('uiAutomation.project.statusFilter')" clearable @change="handleFilter">
            <el-option :label="$t('uiAutomation.status.notStarted')" value="NOT_STARTED" />
            <el-option :label="$t('uiAutomation.status.inProgress')" value="IN_PROGRESS" />
            <el-option :label="$t('uiAutomation.status.completed')" value="COMPLETED" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>
      
    <div class="table-scroll-area">
      <el-table :data="projects" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" :label="$t('uiAutomation.project.projectName')" min-width="200">
          <template #default="{ row }">
            <el-link @click="goToProjectDetail(row.id)" type="primary">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="description" :label="$t('uiAutomation.common.description')" min-width="300" show-overflow-tooltip />
        <el-table-column prop="status" :label="$t('uiAutomation.common.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="base_url" :label="$t('uiAutomation.project.baseUrl')" min-width="200" show-overflow-tooltip />
        <el-table-column prop="owner.username" :label="$t('uiAutomation.project.owner')" width="100" />
        <el-table-column prop="created_at" :label="$t('uiAutomation.common.createTime')" width="180" :formatter="formatDate" />
        <el-table-column prop="updated_at" :label="$t('uiAutomation.common.updateTime')" width="180" :formatter="formatDate" />
        <el-table-column :label="$t('uiAutomation.common.operation')" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goToProjectDetail(row.id)">{{ $t('uiAutomation.common.view') }}</el-button>
            <el-button link type="primary" @click="editProject(row)">{{ $t('uiAutomation.common.edit') }}</el-button>
            <el-button link type="danger" @click="showCleanDialog(row)">清理数据</el-button>
            <el-button link type="danger" @click="deleteProject(row.id)">{{ $t('uiAutomation.common.delete') }}</el-button>
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
    
    <!-- 创建项目对话框 -->
    <el-dialog v-model="showCreateDialog" :title="$t('uiAutomation.project.createProject')" width="500px" :close-on-click-modal="false">
      <el-form ref="createFormRef" :model="createForm" :rules="formRules" label-width="80px">
        <el-form-item :label="$t('uiAutomation.project.projectName')" prop="name">
          <el-input v-model="createForm.name" :placeholder="$t('uiAutomation.project.rules.nameRequired')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.project.projectDesc')" prop="description">
          <el-input v-model="createForm.description" type="textarea" :placeholder="$t('uiAutomation.project.projectDesc')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.common.status')" prop="status">
          <el-select v-model="createForm.status" :placeholder="$t('uiAutomation.project.rules.selectStatus')">
            <el-option :label="$t('uiAutomation.status.notStarted')" value="NOT_STARTED" />
            <el-option :label="$t('uiAutomation.status.inProgress')" value="IN_PROGRESS" />
            <el-option :label="$t('uiAutomation.status.completed')" value="COMPLETED" />
          </el-select>
        </el-form-item>
        <el-form-item label="基础URL" prop="base_url">
          <el-input 
            v-model="createForm.base_url" 
            placeholder="请输入基础URL（如：https://www.example.com）"
          >
            <template #prepend>
              <el-select v-model="urlProtocol" placeholder="协议" style="width: 100px">
                <el-option label="https://" value="https://" />
                <el-option label="http://" value="http://" />
              </el-select>
            </template>
          </el-input>
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            提示：请输入完整的URL地址，包含协议（http:// 或 https://）
          </div>
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.project.startDate')" prop="start_date">
          <el-date-picker v-model="createForm.start_date" type="date" :placeholder="$t('uiAutomation.project.selectDate')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.project.endDate')" prop="end_date">
          <el-date-picker v-model="createForm.end_date" type="date" :placeholder="$t('uiAutomation.project.selectDate')" />
        </el-form-item>
      </el-form>
      <!-- 被测数据库连接配置（可折叠） -->
      <el-divider content-position="left">被测系统数据库连接</el-divider>
      <el-form label-width="80px">
        <el-form-item label="数据库类型">
          <el-select v-model="createForm.target_db_type" placeholder="请选择" clearable style="width: 100%">
            <el-option label="MySQL" value="mysql" />
            <el-option label="PostgreSQL" value="postgresql" />
            <el-option label="SQLite" value="sqlite" />
            <el-option label="Oracle" value="oracle" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.target_db_type !== 'sqlite'" label="主机地址">
          <el-input v-model="createForm.target_db_host" placeholder="如：192.168.1.100" />
        </el-form-item>
        <el-form-item v-if="createForm.target_db_type !== 'sqlite'" label="端口">
          <el-input v-model="createForm.target_db_port" placeholder="如：3306" />
        </el-form-item>
        <el-form-item label="数据库名">
          <el-input v-model="createForm.target_db_name" :placeholder="createForm.target_db_type === 'sqlite' ? 'SQLite文件路径' : '数据库名'" />
        </el-form-item>
        <el-form-item v-if="createForm.target_db_type !== 'sqlite'" label="用户名">
          <el-input v-model="createForm.target_db_user" placeholder="数据库用户名" />
        </el-form-item>
        <el-form-item v-if="createForm.target_db_type !== 'sqlite'" label="密码">
          <el-input v-model="createForm.target_db_password" type="password" show-password placeholder="数据库密码" />
        </el-form-item>
        <div style="color: #909399; font-size: 12px; margin-top: -10px; margin-bottom: 10px; padding-left: 10px;">
          配置被测系统的数据库连接后，可在测试套件中配置清理SQL，执行测试后直接连接数据库清理测试数据。<br/>
          保存项目后可测试数据库连接。
        </div>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">{{ $t('uiAutomation.common.cancel') }}</el-button>
          <el-button type="primary" @click="handleCreate">{{ $t('uiAutomation.common.confirm') }}</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑项目对话框 -->
    <el-dialog v-model="showEditDialog" :title="$t('uiAutomation.project.editProject')" width="500px" :close-on-click-modal="false">
      <el-form ref="editFormRef" :model="editForm" :rules="formRules" label-width="80px">
        <el-form-item :label="$t('uiAutomation.project.projectName')" prop="name">
          <el-input v-model="editForm.name" :placeholder="$t('uiAutomation.project.rules.nameRequired')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.project.projectDesc')" prop="description">
          <el-input v-model="editForm.description" type="textarea" :placeholder="$t('uiAutomation.project.projectDesc')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.common.status')" prop="status">
          <el-select v-model="editForm.status" :placeholder="$t('uiAutomation.project.rules.selectStatus')">
            <el-option :label="$t('uiAutomation.status.notStarted')" value="NOT_STARTED" />
            <el-option :label="$t('uiAutomation.status.inProgress')" value="IN_PROGRESS" />
            <el-option :label="$t('uiAutomation.status.completed')" value="COMPLETED" />
          </el-select>
        </el-form-item>
        <el-form-item label="基础URL" prop="base_url">
          <el-input 
            v-model="editForm.base_url" 
            placeholder="请输入基础URL（如：https://www.example.com）"
          >
            <template #prepend>
              <el-select v-model="editUrlProtocol" placeholder="协议" style="width: 100px">
                <el-option label="https://" value="https://" />
                <el-option label="http://" value="http://" />
              </el-select>
            </template>
          </el-input>
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            提示：请输入完整的URL地址，包含协议（http:// 或 https://）
          </div>
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.project.startDate')" prop="start_date">
          <el-date-picker v-model="editForm.start_date" type="date" :placeholder="$t('uiAutomation.project.selectDate')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.project.endDate')" prop="end_date">
          <el-date-picker v-model="editForm.end_date" type="date" :placeholder="$t('uiAutomation.project.selectDate')" />
        </el-form-item>
      </el-form>
      <!-- 被测数据库连接配置（可折叠） -->
      <el-divider content-position="left">被测系统数据库连接</el-divider>
      <el-form label-width="80px">
        <el-form-item label="数据库类型">
          <el-select v-model="editForm.target_db_type" placeholder="请选择" clearable style="width: 100%">
            <el-option label="MySQL" value="mysql" />
            <el-option label="PostgreSQL" value="postgresql" />
            <el-option label="SQLite" value="sqlite" />
            <el-option label="Oracle" value="oracle" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editForm.target_db_type !== 'sqlite'" label="主机地址">
          <el-input v-model="editForm.target_db_host" placeholder="如：192.168.1.100" />
        </el-form-item>
        <el-form-item v-if="editForm.target_db_type !== 'sqlite'" label="端口">
          <el-input v-model="editForm.target_db_port" placeholder="如：3306" />
        </el-form-item>
        <el-form-item label="数据库名">
          <el-input v-model="editForm.target_db_name" :placeholder="editForm.target_db_type === 'sqlite' ? 'SQLite文件路径' : '数据库名'" />
        </el-form-item>
        <el-form-item v-if="editForm.target_db_type !== 'sqlite'" label="用户名">
          <el-input v-model="editForm.target_db_user" placeholder="数据库用户名" />
        </el-form-item>
        <el-form-item v-if="editForm.target_db_type !== 'sqlite'" label="密码">
          <el-input v-model="editForm.target_db_password" type="password" show-password placeholder="数据库密码" />
        </el-form-item>
        <div style="color: #909399; font-size: 12px; margin-top: -10px; margin-bottom: 10px; padding-left: 10px;">
          配置被测系统的数据库连接后，可在测试套件中配置清理SQL，执行测试后直接连接数据库清理测试数据
        </div>
        <div style="text-align: right; margin-top: -4px;">
          <el-button type="success" size="small" :loading="testDbLoading" :disabled="!editForm.target_db_type" @click="handleTestDbConnection">测试连接</el-button>
          <span v-if="testDbResult" :style="{ color: testDbResult.success ? '#67c23a' : '#f56c6c', fontSize: '12px', marginLeft: '8px' }">
            {{ testDbResult.success ? `连接成功 (${testDbResult.elapsed_ms}ms)` : `连接失败: ${testDbResult.error}` }}
          </span>
          <span v-if="testDbResult && testDbResult.success && testDbResult.db_version" style="color: #909399; font-size: 12px; margin-left: 8px;">
            {{ testDbResult.db_version }}
          </span>
        </div>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">{{ $t('uiAutomation.common.cancel') }}</el-button>
          <el-button type="primary" @click="handleEdit">{{ $t('uiAutomation.common.confirm') }}</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 项目详情弹框 -->
    <el-dialog v-model="showDetailDialog" :title="$t('uiAutomation.project.projectDetail')" width="600px">
      <div v-if="currentProjectDetail" class="project-detail">
        <el-descriptions bordered column="1">
          <el-descriptions-item :label="$t('uiAutomation.project.projectName')">{{ currentProjectDetail.name }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.project.projectDesc')" :span="2">{{ currentProjectDetail.description || $t('uiAutomation.project.noDescription') }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.common.status')">
            <el-tag :type="getStatusType(currentProjectDetail.status)">
              {{ getStatusText(currentProjectDetail.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.project.baseUrl')">{{ currentProjectDetail.base_url }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.project.owner')">{{ currentProjectDetail.owner?.username || $t('uiAutomation.project.none') }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.project.startDate')">{{ currentProjectDetail.start_date ? formatDate(null, null, currentProjectDetail.start_date) : $t('uiAutomation.project.notSet') }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.project.endDate')">{{ currentProjectDetail.end_date ? formatDate(null, null, currentProjectDetail.end_date) : $t('uiAutomation.project.notSet') }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.common.createTime')">{{ formatDate(null, null, currentProjectDetail.created_at) }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.common.updateTime')">{{ formatDate(null, null, currentProjectDetail.updated_at) }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <div v-else class="text-center text-gray-500">
        {{ $t('uiAutomation.common.loading') }}
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showDetailDialog = false">{{ $t('uiAutomation.common.close') }}</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 清理测试数据对话框 -->
    <el-dialog v-model="showCleanDataDialog" title="清理测试数据" width="520px" :close-on-click-modal="false">
      <div v-if="cleanTargetProject" style="margin-bottom: 16px;">
        <span style="font-weight: 500;">项目：</span>{{ cleanTargetProject.name }}
      </div>
      <el-alert type="warning" :closable="false" style="margin-bottom: 16px;">
        此操作将删除选中的执行数据，<b>不可恢复</b>。用例定义、元素库和操作审计记录不会被删除。
      </el-alert>
      <el-form label-width="100px">
        <el-form-item label="时间范围">
          <el-radio-group v-model="cleanForm.timeMode">
            <el-radio value="all">全部数据</el-radio>
            <el-radio value="before">指定时间之前</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="cleanForm.timeMode === 'before'" label="截止日期">
          <el-date-picker
            v-model="cleanForm.beforeDate"
            type="date"
            placeholder="选择截止日期"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            将清理该日期之前（不含当天）的执行数据
          </div>
        </el-form-item>
        <el-form-item label="数据类型">
          <el-checkbox-group v-model="cleanForm.dataTypes">
            <el-checkbox value="case_executions">用例执行记录</el-checkbox>
            <el-checkbox value="suite_executions">套件执行记录</el-checkbox>
            <el-checkbox value="ai_executions">AI执行记录</el-checkbox>
            <el-checkbox value="screenshots">截图文件</el-checkbox>
            <el-checkbox value="notification_logs">通知日志</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCleanDataDialog = false">取消</el-button>
          <el-button type="danger" :loading="cleanLoading" @click="handleCleanData">确认清理</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, View, Edit, Delete } from '@element-plus/icons-vue'
import { getUiProjects, createUiProject, updateUiProject, deleteUiProject, cleanProjectTestData, testDbConnection } from '@/api/ui_automation'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

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

// URL 协议选择
const urlProtocol = ref('https://')
const editUrlProtocol = ref('https://')

// 表单相关
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const createFormRef = ref(null)
const editFormRef = ref(null)
const currentEditId = ref(null)

// 表单数据
const createForm = reactive({
  name: '',
  description: '',
  status: 'IN_PROGRESS',
  base_url: '',
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
  base_url: '',
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
const formRules = computed(() => ({
  name: [
    { required: true, message: t('uiAutomation.project.rules.nameRequired'), trigger: 'blur' },
    { min: 2, max: 200, message: t('uiAutomation.project.rules.nameLength'), trigger: 'blur' }
  ],
  base_url: [
    { required: true, message: '请输入基础URL', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (!value) {
          callback(new Error('请输入基础URL'))
        } else if (!value.startsWith('http://') && !value.startsWith('https://')) {
          callback(new Error('URL必须以 http:// 或 https:// 开头'))
        } else {
          // 简单的URL格式验证
          try {
            new URL(value)
            callback()
          } catch (e) {
            callback(new Error('请输入有效的URL格式'))
          }
        }
      }, 
      trigger: 'blur' 
    }
  ]
}))

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
  const statusKey = {
    'NOT_STARTED': 'notStarted',
    'IN_PROGRESS': 'inProgress',
    'COMPLETED': 'completed'
  }[status]
  return statusKey ? t(`uiAutomation.status.${statusKey}`) : status
}

// 加载项目列表
const loadProjects = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      page_size: pagination.pageSize
    }
    
    // 添加搜索条件
    if (searchText.value) {
      params.search = searchText.value
    }
    
    // 添加筛选条件
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    
    const response = await getUiProjects(params)
    projects.value = response.data.results || response.data
    total.value = response.data.count || projects.value.length
  } catch (error) {
    ElMessage.error(t('uiAutomation.project.messages.loadFailed'))
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
const handleSizeChange = (size) => {
  pagination.pageSize = size
  loadProjects()
}

const handleCurrentChange = (current) => {
  pagination.currentPage = current
  loadProjects()
}

// 详情相关
const showDetailDialog = ref(false)
const currentProjectDetail = ref(null)

// 清理数据相关
const showCleanDataDialog = ref(false)
const cleanTargetProject = ref(null)
const cleanLoading = ref(false)
const cleanForm = reactive({
  timeMode: 'all',
  beforeDate: null,
  dataTypes: ['case_executions', 'suite_executions', 'ai_executions', 'screenshots', 'notification_logs']
})

// 测试数据库连接相关
const testDbLoading = ref(false)
const testDbResult = ref(null)

// 查看项目详情
const goToProjectDetail = (id) => {
  // 查找当前项目
  const project = projects.value.find(p => p.id === id)
  if (project) {
    currentProjectDetail.value = project
    showDetailDialog.value = true
  } else {
    ElMessage.error(t('uiAutomation.project.messages.notFound'))
  }
}

// 显示清理数据对话框
const showCleanDialog = (project) => {
  cleanTargetProject.value = project
  cleanForm.timeMode = 'all'
  cleanForm.beforeDate = null
  cleanForm.dataTypes = ['case_executions', 'suite_executions', 'ai_executions', 'screenshots', 'notification_logs']
  showCleanDataDialog.value = true
}

// 执行清理数据
const handleCleanData = async () => {
  if (cleanForm.dataTypes.length === 0) {
    ElMessage.warning('请至少选择一种数据类型')
    return
  }

  if (cleanForm.timeMode === 'before' && !cleanForm.beforeDate) {
    ElMessage.warning('请选择截止日期')
    return
  }

  const typeNames = {
    case_executions: '用例执行记录',
    suite_executions: '套件执行记录',
    ai_executions: 'AI执行记录',
    screenshots: '截图文件',
    notification_logs: '通知日志'
  }
  const selectedNames = cleanForm.dataTypes.map(t => typeNames[t]).join('、')
  const timeDesc = cleanForm.timeMode === 'before' ? `${cleanForm.beforeDate} 之前的` : '所有'

  try {
    await ElMessageBox.confirm(
      `确定要清理项目「${cleanTargetProject.value.name}」${timeDesc}${selectedNames}吗？此操作不可恢复！`,
      '确认清理',
      { confirmButtonText: '确认清理', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }

  cleanLoading.value = true
  try {
    const data = { data_types: cleanForm.dataTypes }
    if (cleanForm.timeMode === 'before' && cleanForm.beforeDate) {
      data.before_date = cleanForm.beforeDate
    }
    const res = await cleanProjectTestData(cleanTargetProject.value.id, data)
    ElMessage.success(res.data.message || '清理完成')
    showCleanDataDialog.value = false
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '清理失败')
    console.error('清理测试数据失败:', error)
  } finally {
    cleanLoading.value = false
  }
}

// 测试数据库连接
const handleTestDbConnection = async () => {
  if (!currentEditId.value) {
    ElMessage.warning('请先保存项目后再测试连接')
    return
  }
  if (!editForm.target_db_type) {
    ElMessage.warning('请先选择数据库类型')
    return
  }

  testDbLoading.value = true
  testDbResult.value = null
  try {
    // 将当前表单中的数据库配置传入，优先使用表单值
    const data = {
      target_db_type: editForm.target_db_type,
      target_db_host: editForm.target_db_host,
      target_db_port: editForm.target_db_port ? Number(editForm.target_db_port) : null,
      target_db_name: editForm.target_db_name,
      target_db_user: editForm.target_db_user,
      target_db_password: editForm.target_db_password
    }
    const res = await testDbConnection(currentEditId.value, data)
    testDbResult.value = res.data
    if (res.data.success) {
      ElMessage.success(`数据库连接成功 (${res.data.elapsed_ms}ms)`)
    } else {
      ElMessage.error(res.data.error || '连接失败')
    }
  } catch (error) {
    const result = { success: false, error: error.response?.data?.error || '连接测试失败' }
    testDbResult.value = result
    ElMessage.error(result.error)
  } finally {
    testDbLoading.value = false
  }
}

// 编辑项目
const editProject = (project) => {
  currentEditId.value = project.id
  // 复制项目数据到编辑表单
  Object.assign(editForm, {
    name: project.name,
    description: project.description,
    status: project.status,
    base_url: project.base_url,
    start_date: project.start_date ? new Date(project.start_date) : null,
    end_date: project.end_date ? new Date(project.end_date) : null,
    target_db_type: project.target_db_type || '',
    target_db_host: project.target_db_host || '',
    target_db_port: project.target_db_port || '',
    target_db_name: project.target_db_name || '',
    target_db_user: project.target_db_user || '',
    target_db_password: project.target_db_password || ''
  })
  testDbResult.value = null
  showEditDialog.value = true
}

// 删除项目
const deleteProject = async (id) => {
  try {
    await ElMessageBox.confirm(t('uiAutomation.project.messages.deleteConfirm'), t('uiAutomation.messages.confirm.delete'), {
      confirmButtonText: t('uiAutomation.common.confirm'),
      cancelButtonText: t('uiAutomation.common.cancel'),
      type: 'warning'
    })

    await deleteUiProject(id)
    ElMessage.success(t('uiAutomation.project.messages.deleteSuccess'))
    loadProjects()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(t('uiAutomation.project.messages.deleteFailed'))
    console.error('删除项目失败:', error)
  }
}

// 导入用户store
import { useUserStore } from '@/stores/user'

// 日期格式化辅助函数
const formatDateToISO = (date) => {
  if (!date) return null
  // 确保是Date对象
  const d = new Date(date)
  // 格式化为YYYY-MM-DD格式
  return d.toISOString().split('T')[0]
}

// 处理创建项目
const handleCreate = async () => {
  const validate = await createFormRef.value.validate()
  if (!validate) return
  
  try {
    const userStore = useUserStore()
    // 确保用户信息已加载
    if (!userStore.user?.id) {
      await userStore.fetchProfile()
    }
    
    // 确保 base_url 包含协议
    let baseUrl = createForm.base_url.trim()
    if (baseUrl && !baseUrl.startsWith('http://') && !baseUrl.startsWith('https://')) {
      baseUrl = urlProtocol.value + baseUrl
    }
    
    // 创建包含owner字段的项目数据，并格式化日期字段
    const projectData = {
      ...createForm,
      base_url: baseUrl,
      owner: userStore.user.id,  // 添加owner字段，值为当前登录用户ID
      // 格式化日期为YYYY-MM-DD格式
      start_date: formatDateToISO(createForm.start_date),
      end_date: formatDateToISO(createForm.end_date)
    }
    
    await createUiProject(projectData)
    ElMessage.success(t('uiAutomation.project.messages.createSuccess'))
    showCreateDialog.value = false
    
    // 重置表单
    Object.keys(createForm).forEach(key => {
      createForm[key] = ''
    })
    createForm.status = 'IN_PROGRESS'
    createForm.target_db_type = ''
    createForm.target_db_host = ''
    createForm.target_db_port = ''
    createForm.target_db_name = ''
    createForm.target_db_user = ''
    createForm.target_db_password = ''
    urlProtocol.value = 'https://'
    
    loadProjects()
  } catch (error) {
    ElMessage.error(error.response?.data?.base_url?.[0] || error.response?.data?.detail || '项目创建失败')
    console.error('创建项目失败:', error)
  }
}

// 处理编辑项目
const handleEdit = async () => {
  const validate = await editFormRef.value.validate()
  if (!validate) return
  
  try {
    // 确保 base_url 包含协议
    let baseUrl = editForm.base_url.trim()
    if (baseUrl && !baseUrl.startsWith('http://') && !baseUrl.startsWith('https://')) {
      baseUrl = editUrlProtocol.value + baseUrl
    }
    
    // 创建包含格式化日期字段的项目数据
    const projectData = {
      ...editForm,
      base_url: baseUrl,
      // 格式化日期为YYYY-MM-DD格式
      start_date: formatDateToISO(editForm.start_date),
      end_date: formatDateToISO(editForm.end_date)
    }
    
    await updateUiProject(currentEditId.value, projectData)
    ElMessage.success(t('uiAutomation.project.messages.updateSuccess'))
    showEditDialog.value = false
    loadProjects()
  } catch (error) {
    ElMessage.error(error.response?.data?.base_url?.[0] || error.response?.data?.detail || '项目更新失败')
    console.error('更新项目失败:', error)
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadProjects()
})
</script>

