<template>
  <div class="page-container">
    <div class="page-header" style="display: flex; align-items: center;">
      <h1 class="page-title" style="margin-right: 20px; margin-bottom: 0;">{{ $t('uiAutomation.element.title') }}</h1>
      <el-select v-model="projectId" :placeholder="$t('uiAutomation.common.selectProject')" style="width: 200px; margin-right: 15px" @change="onProjectChange">
        <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
      </el-select>
      <el-button type="primary" @click="handleShowCreateDialog">
        <el-icon><Plus /></el-icon>
        {{ $t('uiAutomation.element.newElement') }}
      </el-button>
      <el-button type="success" @click="showAiExtractDialog = true">
        AI 智能提取
      </el-button>
    </div>
    
    <div class="card-container">
      <div class="filter-bar">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-input
              v-model="searchText"
              :placeholder="$t('uiAutomation.element.searchPlaceholder')"
              clearable
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="4">
            <el-select v-model="strategyFilter" :placeholder="$t('uiAutomation.element.strategyFilter')" clearable @change="handleFilter">
              <el-option v-for="strategy in strategies" :key="strategy.id" :label="strategy.name" :value="strategy.id" />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select v-model="pageFilter" :placeholder="$t('uiAutomation.element.pageFilter')" clearable @change="handleFilter">
              <el-option v-for="page in pages" :key="page" :label="page" :value="page" />
            </el-select>
          </el-col>
        </el-row>
      </div>
      
      <el-table :data="elements" v-loading="loading" style="width: 100%">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" :label="$t('uiAutomation.element.elementName')" min-width="150">
          <template #default="{ row }">
            <el-link @click="showElementDetail(row.id)" type="primary">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="page" :label="$t('uiAutomation.element.page')" width="120" />
        <el-table-column prop="description" :label="$t('uiAutomation.common.description')" min-width="200" show-overflow-tooltip />
        <el-table-column :label="$t('uiAutomation.element.locatorStrategy')" width="100">
          <template #default="{ row }">
            {{ row.locator_strategy?.name || $t('uiAutomation.element.unknown') }}
          </template>
        </el-table-column>
        <el-table-column prop="locator_value" :label="$t('uiAutomation.element.locatorValue')" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" :label="$t('uiAutomation.common.createTime')" width="180" :formatter="formatDate" />
        <el-table-column prop="updated_at" :label="$t('uiAutomation.common.updateTime')" width="180" :formatter="formatDate" />
        <el-table-column :label="$t('uiAutomation.common.operation')" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="showElementDetail(row.id)">
              <el-icon><View /></el-icon>
              {{ $t('uiAutomation.common.view') }}
            </el-button>
            <el-button size="small" @click="editElement(row)">
              <el-icon><Edit /></el-icon>
              {{ $t('uiAutomation.common.edit') }}
            </el-button>
            <el-button size="small" type="danger" @click="handleDeleteElement(row.id)">
              <el-icon><Delete /></el-icon>
              {{ $t('uiAutomation.common.delete') }}
            </el-button>
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
    
    <!-- 创建元素对话框 -->
    <el-dialog v-model="showCreateDialog" :title="$t('uiAutomation.element.createElement')" width="600px" :close-on-click-modal="false">
      <el-form ref="createFormRef" :model="createForm" :rules="formRules" label-width="100px">
        <el-form-item :label="$t('uiAutomation.element.elementName')" prop="name">
          <el-input v-model="createForm.name" :placeholder="$t('uiAutomation.element.rules.nameRequired')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.element.page')" prop="page">
          <el-input v-model="createForm.page" :placeholder="$t('uiAutomation.element.rules.pageRequired')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.common.description')" prop="description">
          <el-input v-model="createForm.description" type="textarea" :placeholder="$t('uiAutomation.common.description')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.element.locatorStrategy')" prop="strategy">
          <el-select v-model="createForm.strategy" :placeholder="$t('uiAutomation.element.rules.strategyRequired')" @change="onStrategyChange">
            <el-option v-for="strategy in strategies" :key="strategy.id" :label="strategy.name" :value="strategy.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.element.locatorValue')" prop="locator_value">
          <el-input v-model="createForm.locator_value" :placeholder="$t('uiAutomation.element.rules.locatorRequired')" />
          <div class="el-form-item__help">
            <small style="color: #606266;">
              {{ $t('uiAutomation.element.locatorTip.title') }}<br>
              - {{ $t('uiAutomation.element.locatorTip.id') }}<br>
              - {{ $t('uiAutomation.element.locatorTip.css') }}<br>
              - {{ $t('uiAutomation.element.locatorTip.xpath') }}<br>
              - {{ $t('uiAutomation.element.locatorTip.other') }}
            </small>
          </div>
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.element.isUnique')" prop="is_unique">
          <el-switch v-model="createForm.is_unique" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.element.waitTimeout')" prop="wait_timeout">
          <el-input-number v-model="createForm.wait_timeout" :min="0" :max="30" :step="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">{{ $t('uiAutomation.common.cancel') }}</el-button>
          <el-button type="primary" @click="handleCreate">{{ $t('uiAutomation.common.confirm') }}</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 编辑元素对话框 -->
    <el-dialog v-model="showEditDialog" :title="$t('uiAutomation.element.editElement')" width="600px" :close-on-click-modal="false">
      <el-form ref="editFormRef" :model="editForm" :rules="formRules" label-width="100px">
        <el-form-item :label="$t('uiAutomation.element.elementName')" prop="name">
          <el-input v-model="editForm.name" :placeholder="$t('uiAutomation.element.rules.nameRequired')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.element.page')" prop="page">
          <el-input v-model="editForm.page" :placeholder="$t('uiAutomation.element.rules.pageRequired')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.common.description')" prop="description">
          <el-input v-model="editForm.description" type="textarea" :placeholder="$t('uiAutomation.common.description')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.element.locatorStrategy')" prop="strategy">
          <el-select v-model="editForm.strategy" :placeholder="$t('uiAutomation.element.rules.strategyRequired')" @change="onEditStrategyChange">
            <el-option v-for="strategy in strategies" :key="strategy.id" :label="strategy.name" :value="strategy.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.element.locatorValue')" prop="locator_value">
          <el-input v-model="editForm.locator_value" :placeholder="$t('uiAutomation.element.rules.locatorRequired')" />
          <div class="el-form-item__help">
            <small style="color: #606266;">
              {{ $t('uiAutomation.element.locatorTip.title') }}<br>
              - {{ $t('uiAutomation.element.locatorTip.id') }}<br>
              - {{ $t('uiAutomation.element.locatorTip.css') }}<br>
              - {{ $t('uiAutomation.element.locatorTip.xpath') }}<br>
              - {{ $t('uiAutomation.element.locatorTip.other') }}
            </small>
          </div>
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.element.isUnique')" prop="is_unique">
          <el-switch v-model="editForm.is_unique" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.element.waitTimeout')" prop="wait_timeout">
          <el-input-number v-model="editForm.wait_timeout" :min="0" :max="30" :step="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">{{ $t('uiAutomation.common.cancel') }}</el-button>
          <el-button type="primary" @click="handleEdit">{{ $t('uiAutomation.common.confirm') }}</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 元素详情对话框 -->
    <el-dialog v-model="showDetailDialog" :title="$t('uiAutomation.element.elementDetail')" width="600px">
      <div v-if="Object.keys(currentElementDetail).length > 0" class="element-detail">
        <el-descriptions border column="2" :column="{ xs: 1, sm: 2 }">
          <el-descriptions-item :label="$t('uiAutomation.element.elementName')">{{ currentElementDetail.name }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.element.page')">{{ currentElementDetail.page }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.element.project')">{{ currentElementDetail.project?.name || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.element.locatorStrategy')">{{ currentElementDetail.locator_strategy?.name || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.element.locatorValue')" :span="2">
            <el-tag type="info" style="word-break: break-all; display: block; text-align: left;">
              {{ currentElementDetail.locator_value }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.element.isUnique')">
            <el-tag :type="currentElementDetail.is_unique ? 'success' : 'warning'">
              {{ currentElementDetail.is_unique ? $t('uiAutomation.common.yes') : $t('uiAutomation.common.no') }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.element.waitTimeout')">{{ currentElementDetail.wait_timeout || 5 }}{{ $t('uiAutomation.element.waitTimeoutUnit') }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.common.description')" :span="2">{{ currentElementDetail.description === undefined ? '-' : currentElementDetail.description }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.common.createTime')">{{ formatDate(null, null, currentElementDetail.created_at) }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.common.updateTime')">{{ formatDate(null, null, currentElementDetail.updated_at) }}</el-descriptions-item>
          <el-descriptions-item :label="$t('uiAutomation.element.createdBy')" :span="2">{{ currentElementDetail.created_by?.username || '-' }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <div v-else class="text-center text-gray-500 py-10">
        {{ $t('uiAutomation.element.loadingDetail') }}
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showDetailDialog = false">{{ $t('uiAutomation.common.close') }}</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- AI智能提取 - 输入对话框 -->
    <el-dialog v-model="showAiExtractDialog" title="AI 智能提取元素" width="550px" :close-on-click-modal="false">
      <el-form label-width="100px">
        <el-form-item label="目标页面URL" required>
          <el-input v-model="aiExtractForm.url" placeholder="输入页面URL，如 https://example.com/user/list" />
        </el-form-item>
        <el-form-item label="登录配置">
          <el-select v-model="aiExtractForm.login_config_id" placeholder="可选，需登录的页面选择" clearable style="width: 100%">
            <el-option v-for="cfg in loginConfigs" :key="cfg.id" :label="cfg.name" :value="cfg.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="页面名称">
          <el-input v-model="aiExtractForm.page_name" placeholder="可选，如 用户管理页" />
        </el-form-item>
      </el-form>
      <div v-if="aiExtractLoading" style="text-align: center; padding: 20px 0;">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <p style="margin-top: 10px; color: #909399;">{{ aiExtractProgress }}</p>
      </div>
      <template #footer>
        <el-button @click="showAiExtractDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAiExtract" :loading="aiExtractLoading">开始提取</el-button>
      </template>
    </el-dialog>

    <!-- AI智能提取 - 结果预览对话框 -->
    <el-dialog v-model="showAiResultDialog" title="AI 提取结果预览" width="900px" :close-on-click-modal="false" top="5vh">
      <div style="margin-bottom: 12px; color: #606266;">
        页面: {{ aiResultInfo.url }}
        <span v-if="aiResultInfo.page_title" style="margin-left: 10px;">标题: {{ aiResultInfo.page_title }}</span>
        <span style="margin-left: 10px;">共 {{ aiExtractResults.length }} 个元素</span>
        <el-button size="small" type="primary" link @click="toggleSelectAll" style="margin-left: 10px;">
          {{ isAllSelected ? '取消全选' : '全选' }}
        </el-button>
      </div>
      <el-table :data="aiExtractResults" max-height="500" style="width: 100%"
        @selection-change="handleAiResultSelectionChange">
        <el-table-column type="selection" width="45" />
        <el-table-column label="元素名称" min-width="130">
          <template #default="{ row }">
            <el-input v-model="row.name" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="类型" width="110">
          <template #default="{ row }">
            <el-select v-model="row.element_type" size="small">
              <el-option label="输入框" value="INPUT" />
              <el-option label="按钮" value="BUTTON" />
              <el-option label="链接" value="LINK" />
              <el-option label="下拉框" value="DROPDOWN" />
              <el-option label="复选框" value="CHECKBOX" />
              <el-option label="单选框" value="RADIO" />
              <el-option label="文本" value="TEXT" />
              <el-option label="图片" value="IMAGE" />
              <el-option label="表格" value="TABLE" />
              <el-option label="容器" value="CONTAINER" />
              <el-option label="表单" value="FORM" />
              <el-option label="弹窗" value="MODAL" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="定位策略" width="100">
          <template #default="{ row }">
            <el-select v-model="row.locator_strategy" size="small">
              <el-option v-for="s in strategies" :key="s.name" :label="s.name" :value="s.name" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="定位表达式" min-width="180">
          <template #default="{ row }">
            <el-input v-model="row.locator_value" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="描述" min-width="130">
          <template #default="{ row }">
            <el-input v-model="row.description" size="small" />
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showAiResultDialog = false">取消</el-button>
        <el-button type="primary" @click="handleBatchImport" :loading="batchImportLoading">
          确认导入({{ selectedAiResults.length }}个元素)
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, View, Edit, Delete, Loading } from '@element-plus/icons-vue'
import {
  getUiProjects,
  getElements,
  createElement,
  updateElement,
  deleteElement,
  getElementDetail,
  getLocatorStrategies,
  aiExtractElements,
  getLoginConfigs
} from '@/api/ui_automation'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// 项目和元素数据
const projects = ref([])
const projectId = ref('')
const elements = ref([])

// 定位策略数据
const strategies = ref([])
const pages = ref([])
const loading = ref(false)
const total = ref(0)
const pagination = reactive({
  currentPage: 1,
  pageSize: 10
})

// 搜索和筛选
const searchText = ref('')
const strategyFilter = ref('')
const pageFilter = ref('')

// 表单相关
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showDetailDialog = ref(false)
const createFormRef = ref(null)
const editFormRef = ref(null)
const currentEditId = ref(null)
const currentElementDetail = ref({})

// AI智能提取相关
const showAiExtractDialog = ref(false)
const showAiResultDialog = ref(false)
const aiExtractLoading = ref(false)
const aiExtractProgress = ref('')
const aiExtractResults = ref([])
const selectedAiResults = ref([])
const batchImportLoading = ref(false)
const loginConfigs = ref([])
const aiResultInfo = reactive({ url: '', page_title: '' })
const aiExtractForm = reactive({
  url: '',
  login_config_id: null,
  page_name: ''
})
const isAllSelected = computed(() => {
  return aiExtractResults.value.length > 0 && selectedAiResults.value.length === aiExtractResults.value.length
})

// 表单数据
const createForm = reactive({
  project: '',
  name: '',
  page: '',
  description: '',
  strategy: '',
  locator_value: '',
  is_unique: false,
  wait_timeout: 5
})

const editForm = reactive({
  project: '',
  name: '',
  page: '',
  description: '',
  strategy: '',
  locator_value: '',
  is_unique: false,
  wait_timeout: 5
})

// 表单验证规则
const formRules = computed(() => ({
  name: [
    { required: true, message: t('uiAutomation.element.rules.nameRequired'), trigger: 'blur' },
    { min: 2, max: 100, message: t('uiAutomation.element.rules.nameLength'), trigger: 'blur' }
  ],
  page: [
    { required: true, message: t('uiAutomation.element.rules.pageRequired'), trigger: 'blur' }
  ],
  strategy: [
    { required: true, message: t('uiAutomation.element.rules.strategyRequired'), trigger: 'change' }
  ],
  locator_value: [
    { required: true, message: t('uiAutomation.element.rules.locatorRequired'), trigger: 'blur' }
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
    minute: '2-digit'
  })
}

// 加载项目列表
const loadProjects = async () => {
  try {
    const response = await getUiProjects({ page_size: 100 })
    projects.value = response.data.results || response.data
  } catch (error) {
    ElMessage.error(t('uiAutomation.project.messages.loadFailed'))
    console.error('获取项目列表失败:', error)
  }
}

// 加载定位策略
const loadStrategies = async () => {
  try {
    const response = await getLocatorStrategies()
    strategies.value = response.data.results || response.data
  } catch (error) {
    ElMessage.error(t('uiAutomation.element.messages.loadStrategiesFailed'))
    console.error('获取定位策略失败:', error)
  }
}

// 处理显示创建对话框
const handleShowCreateDialog = () => {
  showCreateDialog.value = true
}

// 加载元素列表
const loadElements = async () => {
  if (!projectId.value) {
    elements.value = []
    total.value = 0
    return
  }
  
  loading.value = true
  try {
    const params = {
      project: projectId.value,
      page: pagination.currentPage,
      page_size: pagination.pageSize
    }

    // 添加搜索条件
    if (searchText.value) {
      params.search = searchText.value
    }

    // 添加筛选条件
    if (strategyFilter.value) {
      params.locator_strategy = strategyFilter.value
    }

    // 页面筛选 - 使用page_name参数避免与分页page冲突
    if (pageFilter.value) {
      params.page_name = pageFilter.value
    }
    
    const response = await getElements(params)
    elements.value = response.data.results || response.data
    total.value = response.data.count || elements.value.length
    
    // 提取所有页面名称用于筛选
    const pageNames = [...new Set(elements.value.map(el => el.page))]
    pages.value = pageNames.filter(name => name)
  } catch (error) {
    ElMessage.error(t('uiAutomation.element.messages.loadFailed'))
    console.error('获取元素列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 项目变更处理
const onProjectChange = () => {
  // 清空搜索和筛选条件
  searchText.value = ''
  strategyFilter.value = ''
  pageFilter.value = ''
  pagination.currentPage = 1
  
  // 设置创建表单的项目
  createForm.project = projectId.value
  
  // 重新加载元素
  loadElements()
  loadLoginConfigs()
}

// 搜索处理
const handleSearch = () => {
  pagination.currentPage = 1
  loadElements()
}

// 筛选处理
const handleFilter = () => {
  pagination.currentPage = 1
  loadElements()
}

// 分页处理
const handleSizeChange = (size) => {
  pagination.pageSize = size
  loadElements()
}

const handleCurrentChange = (current) => {
  pagination.currentPage = current
  loadElements()
}

// 查看元素详情
const showElementDetail = async (id) => {
  try {
    // 清空之前的数据，避免缓存问题
    currentElementDetail.value = {}

    // 使用专门的详情API获取单个元素的完整信息
    const response = await getElementDetail(id)
    console.log('API返回的元素详情:', response.data)

    currentElementDetail.value = response.data
    showDetailDialog.value = true
  } catch (error) {
    ElMessage.error(t('uiAutomation.element.messages.loadDetailFailed'))
    console.error('获取元素详情失败:', error)
  }
}

// 编辑元素
const editElement = (element) => {
  currentEditId.value = element.id

  // 查找策略ID - 修正字段名
  const strategy = strategies.value.find(s => s.name === element.locator_strategy?.name)

  // 复制元素数据到编辑表单
  Object.assign(editForm, {
    project: element.project,
    name: element.name,
    page: element.page,
    description: element.description,
    strategy: strategy ? strategy.id : '',
    locator_value: element.locator_value,
    is_unique: element.is_unique,
    wait_timeout: element.wait_timeout || 5
  })

  showEditDialog.value = true
}

// 删除元素
const handleDeleteElement = async (id) => {
  try {
    await ElMessageBox.confirm(t('uiAutomation.element.messages.deleteConfirm'), t('uiAutomation.messages.confirm.delete'), {
      confirmButtonText: t('uiAutomation.common.confirm'),
      cancelButtonText: t('uiAutomation.common.cancel'),
      type: 'warning'
    })

    await deleteElement(id)
    ElMessage.success(t('uiAutomation.element.messages.deleteSuccess'))
    loadElements()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(t('uiAutomation.element.messages.deleteFailed'))
    console.error('删除元素失败:', error)
  }
}

// 定位策略变更处理
const onStrategyChange = () => {
  // 可以根据定位策略类型提供不同的输入提示或验证
}

const onEditStrategyChange = () => {
  // 可以根据定位策略类型提供不同的输入提示或验证
}

// ========== AI智能提取相关方法 ==========

// 加载登录配置列表
const loadLoginConfigs = async () => {
  if (!projectId.value) {
    loginConfigs.value = []
    return
  }
  try {
    const response = await getLoginConfigs({ project: projectId.value, page_size: 100 })
    loginConfigs.value = response.data.results || response.data
  } catch (error) {
    console.error('获取登录配置失败:', error)
    loginConfigs.value = []
  }
}

// 执行AI提取
const handleAiExtract = async () => {
  if (!aiExtractForm.url) {
    ElMessage.warning('请输入目标页面URL')
    return
  }
  if (!projectId.value) {
    ElMessage.warning('请先选择项目')
    return
  }

  aiExtractLoading.value = true
  aiExtractProgress.value = '正在打开页面...'

  try {
    const data = {
      project_id: projectId.value,
      url: aiExtractForm.url,
      login_config_id: aiExtractForm.login_config_id || undefined,
      page_name: aiExtractForm.page_name || undefined
    }

    aiExtractProgress.value = '正在分析DOM结构...'

    const response = await aiExtractElements(data)

    aiExtractProgress.value = '正在AI智能识别...'

    const result = response.data
    aiExtractResults.value = (result.elements || []).map((elem, index) => ({
      ...elem,
      _id: index,
      selected: true
    }))
    aiResultInfo.url = result.url || aiExtractForm.url
    aiResultInfo.page_title = result.page_title || ''

    if (aiExtractResults.value.length === 0) {
      ElMessage.warning('未提取到可交互元素')
      return
    }

    showAiExtractDialog.value = false
    showAiResultDialog.value = true
    ElMessage.success(`成功提取 ${aiExtractResults.value.length} 个元素`)
  } catch (error) {
    const errMsg = error.response?.data?.error || error.message || '提取失败'
    ElMessage.error(errMsg)
    console.error('AI提取失败:', error)
  } finally {
    aiExtractLoading.value = false
    aiExtractProgress.value = ''
  }
}

// 结果选择变更
const handleAiResultSelectionChange = (selection) => {
  selectedAiResults.value = selection
}

// 全选/取消全选
const toggleSelectAll = () => {
  const tableRef = document.querySelector('.ai-result-table')
  // 使用 Element Plus table toggleAllSelection 需要更复杂处理
  // 简化实现：直接标记
  if (isAllSelected.value) {
    selectedAiResults.value = []
  } else {
    selectedAiResults.value = [...aiExtractResults.value]
  }
}

// 批量导入元素
const handleBatchImport = async () => {
  if (selectedAiResults.value.length === 0) {
    ElMessage.warning('请至少选择一个元素')
    return
  }

  batchImportLoading.value = true
  let successCount = 0
  let failCount = 0

  try {
    for (const elem of selectedAiResults.value) {
      try {
        // 查找定位策略的ID
        const strategyObj = strategies.value.find(s => s.name === elem.locator_strategy)
        const apiData = {
          name: elem.name,
          page: elem.page || aiExtractForm.page_name || '',
          description: elem.description || '',
          locator_value: elem.locator_value,
          project_id: projectId.value,
          locator_strategy_id: strategyObj ? strategyObj.id : strategies.value[0]?.id,
          element_type: elem.element_type,
          is_unique: false,
          wait_timeout: 5
        }
        // 备用定位器
        if (elem.backup_locators && elem.backup_locators.length > 0) {
          apiData.backup_locators = elem.backup_locators
        }

        await createElement(apiData)
        successCount++
      } catch (err) {
        failCount++
        console.error(`导入元素"${elem.name}"失败:`, err)
      }
    }

    if (successCount > 0) {
      ElMessage.success(`成功导入 ${successCount} 个元素${failCount > 0 ? `，${failCount} 个失败` : ''}`)
      showAiResultDialog.value = false
      loadElements()
    } else {
      ElMessage.error('所有元素导入失败')
    }
  } finally {
    batchImportLoading.value = false
  }
}

// 处理创建元素
const handleCreate = async () => {
  const validate = await createFormRef.value.validate()
  if (!validate) return
  
  try {
    // 直接使用选择的策略ID，确保是整数类型
    const apiFormData = {
      name: createForm.name,
      page: createForm.page,
      description: createForm.description,
      locator_value: createForm.locator_value,
      project_id: projectId.value, // 使用当前选择的项目ID
      locator_strategy_id: createForm.strategy, // 直接使用整数ID，无需转换
      is_unique: createForm.is_unique, // 添加缺失的字段
      wait_timeout: createForm.wait_timeout // 添加缺失的字段
    }
    
    console.log('提交的API数据:', apiFormData)
    await createElement(apiFormData)
    ElMessage.success(t('uiAutomation.element.messages.createSuccess'))
    showCreateDialog.value = false
    
    // 重置表单
    Object.assign(createForm, {
      name: '',
      page: '',
      description: '',
      strategy: '',
      locator_value: '',
      is_unique: false,
      wait_timeout: 5
    })
    
    loadElements()
  } catch (error) {
    console.error('创建元素失败:', error)
    if (error.response && error.response.data) {
      const errorData = error.response.data
      if (errorData.locator_strategy_id) {
        ElMessage.error(errorData.locator_strategy_id[0])
      } else if (errorData.project_id) {
        ElMessage.error(errorData.project_id[0])
      } else {
        ElMessage.error(t('uiAutomation.element.messages.createFailed') + ': ' + JSON.stringify(errorData))
      }
    } else {
      ElMessage.error(t('uiAutomation.element.messages.createFailed'))
    }
  }
}

// 处理编辑元素
const handleEdit = async () => {
  const validate = await editFormRef.value.validate()
  if (!validate) return
  
  try {
    // 确保project_id是有效的整数值
    const projectIdInt = parseInt(editForm.project) || projectId.value;
    
    // 构建API请求数据
    const apiFormData = {
      name: editForm.name,
      page: editForm.page,
      description: editForm.description,
      locator_value: editForm.locator_value,
      project_id: projectIdInt, // 使用有效的整数项目ID
      locator_strategy_id: editForm.strategy,
      is_unique: editForm.is_unique, // 添加缺失的字段
      wait_timeout: editForm.wait_timeout // 添加缺失的字段
    }
    
    console.log('提交的API数据:', apiFormData)
    await updateElement(currentEditId.value, apiFormData)
    ElMessage.success(t('uiAutomation.element.messages.updateSuccess'))
    showEditDialog.value = false
    loadElements()
  } catch (error) {
    ElMessage.error(t('uiAutomation.element.messages.updateFailed'))
    console.error('更新元素失败:', error)
  }
}

// 监听项目选择变化
watch(projectId, (newValue) => {
  if (newValue) {
    createForm.project = newValue
  }
})

// 组件挂载时加载数据
onMounted(async () => {
  await Promise.all([
    loadProjects(),
    loadStrategies()
  ])

  // 如果有项目，默认选择第一个
  if (projects.value.length > 0) {
    projectId.value = projects.value[0].id
    createForm.project = projectId.value
    await loadElements()
    await loadLoginConfigs()
  }
})
</script>

<style scoped>
.page-container {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 24px;
}

.card-container {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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