<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">测试计划</h1>
      <div class="header-actions">
        <el-select v-model="projectId" placeholder="选择项目" style="width: 200px; margin-right: 15px" @change="onProjectChange">
          <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建计划
        </el-button>
      </div>
    </div>

    <div class="card-container">
      <div class="filter-bar">
        <el-form :inline="true">
          <el-form-item>
            <el-input v-model="searchText" placeholder="搜索计划名称" clearable @input="handleSearch">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
          </el-form-item>
        </el-form>
      </div>

      <div class="table-scroll-area">
        <el-table :data="filteredPlans" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="计划名称" min-width="200">
          <template #default="{ row }">
            <el-link @click="goToDetail(row.id)" type="primary">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
        <el-table-column label="执行模式" width="130">
          <template #default="{ row }">
            <el-tag size="small" :type="row.execution_mode === 'shared_session' ? 'success' : 'info'">
              {{ row.execution_mode === 'shared_session' ? '共享会话' : '独立模式' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="登录配置" width="150">
          <template #default="{ row }">
            <span v-if="row.login_config_name">{{ row.login_config_name }}</span>
            <span v-else style="color: #909399">未配置</span>
          </template>
        </el-table-column>
        <el-table-column label="计划项" width="80">
          <template #default="{ row }">{{ row.plan_item_count || 0 }}</template>
        </el-table-column>
        <el-table-column label="总用例" width="80">
          <template #default="{ row }">{{ row.total_cases || 0 }}</template>
        </el-table-column>
        <el-table-column label="执行状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.execution_status)">{{ getStatusText(row.execution_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="通过" width="70">
          <template #default="{ row }">
            <span style="color: #67c23a; font-weight: bold">{{ row.passed_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="失败" width="70">
          <template #default="{ row }">
            <span style="color: #f56c6c; font-weight: bold">{{ row.failed_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="跳过" width="70">
          <template #default="{ row }">
            <span style="color: #e6a23c; font-weight: bold">{{ row.skipped_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" :formatter="formatDate" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="editPlan(row.id)">编辑</el-button>
            <el-button link type="success" @click="runPlan(row)">执行</el-button>
            <el-button link type="danger" @click="deletePlan(row.id)">删除</el-button>
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
    </div>

    <!-- 创建/编辑计划对话框 -->
    <el-dialog v-model="showEditDialog" :title="isEditing ? '编辑测试计划' : '新建测试计划'" width="1000px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="计划名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入计划名称" />
        </el-form-item>
        <el-form-item label="计划描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请输入计划描述" />
        </el-form-item>
        <el-form-item label="执行模式" prop="execution_mode">
          <el-radio-group v-model="form.execution_mode">
            <el-radio label="per_case">独立模式</el-radio>
            <el-radio label="shared_session">共享会话模式</el-radio>
          </el-radio-group>
          <div class="mode-desc">
            <span v-if="form.execution_mode === 'per_case'">每个计划项独立启动浏览器，互不影响</span>
            <span v-else>所有计划项共享同一浏览器会话，计划级配置登录，项内登录自动跳过</span>
          </div>
        </el-form-item>
        <el-form-item v-if="form.execution_mode === 'shared_session'" label="登录配置" prop="login_config">
          <el-select v-model="form.login_config" placeholder="请选择登录配置" clearable filterable style="width: 100%">
            <el-option v-for="cfg in loginConfigs" :key="cfg.id" :label="cfg.name" :value="cfg.id" />
          </el-select>
          <div class="mode-desc">共享会话模式下，执行前先按登录配置自动登录，计划内套件/用例的登录步骤将被跳过</div>
        </el-form-item>
        <el-form-item label="清理SQL">
          <el-input v-model="form.cleanup_sql" type="textarea" :rows="3" placeholder="计划执行完毕后执行的清理SQL，多条用分号分隔" />
        </el-form-item>

      </el-form>

      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加用例对话框 -->
    <el-dialog v-model="showAddCaseDialog" title="添加用例" width="600px">
      <div style="display: flex; margin-bottom: 15px">
        <el-tree-select
          v-model="planGroupFilter"
          :data="planGroupTree"
          :props="{ children: 'children', label: 'name', value: 'id' }"
          placeholder="全部分组"
          clearable
          check-strictly
          size="small"
          style="width: 140px; margin-right: 8px;"
        />
        <el-input v-model="addCaseSearch" placeholder="搜索用例名称" clearable>
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
      </div>
      <el-table :data="filteredAvailableCases" height="400" @selection-change="handleCaseSelectionChange">
        <el-table-column type="selection" width="55" :selectable="row => !isCaseAlreadyAdded(row.id)" />
        <el-table-column prop="name" label="用例名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="priority" label="优先级" width="80" />
      </el-table>
      <template #footer>
        <el-button @click="showAddCaseDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAddCases" :disabled="selectedCases.length === 0">
          添加 ({{ selectedCases.length }})
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加套件对话框 -->
    <el-dialog v-model="showAddSuiteDialog" title="添加套件" width="600px">
      <el-input v-model="addSuiteSearch" placeholder="搜索套件名称" clearable style="margin-bottom: 15px">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-table :data="filteredAvailableSuites" height="400" @selection-change="handleSuiteSelectionChange">
        <el-table-column type="selection" width="55" :selectable="row => !isSuiteAlreadyAdded(row.id)" />
        <el-table-column prop="name" label="套件名称" min-width="200" show-overflow-tooltip />
        <el-table-column label="用例数" width="80">
          <template #default="{ row }">{{ row.test_case_count || 0 }}</template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showAddSuiteDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAddSuites" :disabled="selectedSuites.length === 0">
          添加 ({{ selectedSuites.length }})
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行对话框 -->
    <el-dialog v-model="showRunDialog" title="执行测试计划" width="500px">
      <el-form label-width="100px">
        <el-form-item label="测试引擎">
          <el-select v-model="runConfig.engine" style="width: 100%">
            <el-option label="Playwright" value="playwright" />
            <el-option label="Selenium" value="selenium" />
          </el-select>
        </el-form-item>
        <el-form-item label="浏览器">
          <el-select v-model="runConfig.browser" style="width: 100%">
            <el-option label="Chrome" value="chrome" />
            <el-option label="Firefox" value="firefox" />
            <el-option label="Edge" value="edge" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行模式">
          <el-radio-group v-model="runConfig.headless">
            <el-radio :label="false">有头模式</el-radio>
            <el-radio :label="true">无头模式</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRunDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmRun" :loading="runLoading">执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import {
  getTestPlans, getTestPlan, createTestPlan, updateTestPlan, deleteTestPlan,
  getPlanItems, addPlanItem, addPlanItemsBatch, removePlanItem, runTestPlan,
  getUiProjects, getTestCasesAll, getTestSuites, getLoginConfigs, getTestCaseGroupTree
} from '@/api/ui_automation'

const router = useRouter()

// 数据
const projects = ref([])
const projectId = ref(null)
const plans = ref([])
const planItems = ref([])
const loginConfigs = ref([])
const allTestCases = ref([])
const allSuites = ref([])
const loading = ref(false)
const total = ref(0)
const searchText = ref('')
const pagination = ref({ currentPage: 1, pageSize: 20 })

// 对话框
const showEditDialog = ref(false)
const showAddCaseDialog = ref(false)
const showAddSuiteDialog = ref(false)
const showRunDialog = ref(false)
const isEditing = ref(false)
const editingPlanId = ref(null)
const submitting = ref(false)
const runLoading = ref(false)

// 表单
const formRef = ref(null)
const form = ref({
  name: '', description: '', execution_mode: 'per_case',
  login_config: null, cleanup_sql: ''
})
const formRules = {
  name: [{ required: true, message: '请输入计划名称', trigger: 'blur' }],
  execution_mode: [{ required: true, message: '请选择执行模式', trigger: 'change' }]
}

// 执行配置
const runConfig = ref({ engine: 'playwright', browser: 'chrome', headless: false })
const currentRunPlan = ref(null)

// 添加用例
const addCaseSearch = ref('')
const selectedCases = ref([])
const planGroupFilter = ref(null)
const planGroupTree = ref([])
const addSuiteSearch = ref('')
const selectedSuites = ref([])

// 计算属性
const filteredPlans = computed(() => {
  if (!searchText.value) return plans.value
  const kw = searchText.value.toLowerCase()
  return plans.value.filter(p => p.name.toLowerCase().includes(kw))
})

const filteredAvailableCases = computed(() => {
  let result = allTestCases.value
  // 按分组筛选
  if (planGroupFilter.value) {
    result = result.filter(tc => tc.group === planGroupFilter.value)
  }
  // 文本搜索
  if (!addCaseSearch.value) return result
  const kw = addCaseSearch.value.toLowerCase()
  return result.filter(c => c.name.toLowerCase().includes(kw))
})

const filteredAvailableSuites = computed(() => {
  if (!addSuiteSearch.value) return allSuites.value
  const kw = addSuiteSearch.value.toLowerCase()
  return allSuites.value.filter(s => s.name.toLowerCase().includes(kw))
})

// 方法
function getStatusTag(status) {
  const map = { not_run: 'info', passed: 'success', failed: 'danger', running: 'warning' }
  return map[status] || 'info'
}
function getStatusText(status) {
  const map = { not_run: '未执行', passed: '通过', failed: '失败', running: '执行中' }
  return map[status] || '未知'
}
function formatDate(row, col, value) {
  if (!value) return ''
  return new Date(value).toLocaleString('zh-CN')
}

function isCaseAlreadyAdded(caseId) {
  return planItems.value.some(i => i.item_type === 'test_case' && i.test_case === caseId)
}
function isSuiteAlreadyAdded(suiteId) {
  return planItems.value.some(i => i.item_type === 'test_suite' && i.test_suite === suiteId)
}

async function loadProjects() {
  try {
    const res = await getUiProjects()
    projects.value = res.data.results || res.data || []
    if (projects.value.length > 0 && !projectId.value) {
      projectId.value = projects.value[0].id
    }
  } catch (e) { console.error(e) }
}

async function loadPlans() {
  if (!projectId.value) return
  loading.value = true
  try {
    const res = await getTestPlans({
      project: projectId.value,
      page: pagination.value.currentPage,
      page_size: pagination.value.pageSize
    })
    plans.value = res.data.results || res.data || []
    total.value = res.data.count || plans.value.length
  } catch (e) {
    ElMessage.error('加载计划列表失败')
  } finally {
    loading.value = false
  }
}

async function loadLoginConfigs() {
  if (!projectId.value) return
  try {
    const res = await getLoginConfigs({ project: projectId.value })
    loginConfigs.value = res.data.results || res.data || []
  } catch (e) { console.error(e) }
}

async function loadTestCases() {
  if (!projectId.value) return
  try {
    const res = await getTestCasesAll({ project: projectId.value, page_size: 500 })
    allTestCases.value = res.data.results || res.data || []
  } catch (e) { console.error(e) }
}

async function loadSuites() {
  if (!projectId.value) return
  try {
    const res = await getTestSuites({ project: projectId.value })
    allSuites.value = res.data.results || res.data || []
  } catch (e) { console.error(e) }
}

const loadPlanGroupTree = async () => {
  if (!projectId.value) { planGroupTree.value = []; return }
  try {
    const response = await getTestCaseGroupTree({ project: projectId.value })
    planGroupTree.value = response.data || []
  } catch (error) { console.error('获取用例分组树失败:', error) }
}

async function loadPlanItems(planId) {
  try {
    const res = await getPlanItems(planId)
    planItems.value = res.data || []
  } catch (e) {
    console.error('加载计划项失败:', e)
    planItems.value = []
  }
}

function onProjectChange() {
  pagination.value.currentPage = 1
  loadPlans()
  loadLoginConfigs()
  loadTestCases()
  loadSuites()
}

function handleSearch() {
  // 前端过滤，不需要重新请求
}

function handleSizeChange(val) {
  pagination.value.pageSize = val
  loadPlans()
}

function handleCurrentChange(val) {
  pagination.value.currentPage = val
  loadPlans()
}

function goToDetail(planId) {
  router.push({ name: 'UiTestPlanDetail', params: { id: planId } })
}

function handleCreate() {
  isEditing.value = false
  editingPlanId.value = null
  form.value = { name: '', description: '', execution_mode: 'per_case', login_config: null, cleanup_sql: '' }
  planItems.value = []
  showEditDialog.value = true
}

async function editPlan(planId) {
  isEditing.value = true
  editingPlanId.value = planId
  try {
    const res = await getTestPlan(planId)
    const data = res.data
    form.value = {
      name: data.name,
      description: data.description,
      execution_mode: data.execution_mode,
      login_config: data.login_config,
      cleanup_sql: data.cleanup_sql || ''
    }
    await loadPlanItems(planId)
    showEditDialog.value = true
  } catch (e) {
    console.error('加载计划详情失败:', e)
    const msg = e?.response?.data?.detail || e?.response?.data?.error || e?.message || '未知错误'
    ElMessage.error(`加载计划详情失败: ${msg}`)
    isEditing.value = false
    editingPlanId.value = null
  }
}

async function submitForm() {
  if (!formRef.value) return
  await formRef.value.validate()
  submitting.value = true
  try {
    if (isEditing.value) {
      await updateTestPlan(editingPlanId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createTestPlan({ ...form.value, project: projectId.value })
      ElMessage.success('创建成功')
    }
    showEditDialog.value = false
    loadPlans()
  } catch (e) {
    ElMessage.error(isEditing.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

async function deletePlan(planId) {
  try {
    await ElMessageBox.confirm('确定删除该测试计划吗？', '提示', { type: 'warning' })
    await deleteTestPlan(planId)
    ElMessage.success('删除成功')
    loadPlans()
  } catch (e) { /* cancelled */ }
}

function runPlan(plan) {
  currentRunPlan.value = plan
  runConfig.value = { engine: 'playwright', browser: 'chrome', headless: false }
  showRunDialog.value = true
}

async function confirmRun() {
  runLoading.value = true
  try {
    await runTestPlan(currentRunPlan.value.id, runConfig.value)
    ElMessage.success('测试计划开始执行')
    showRunDialog.value = false
    // 轮询刷新执行状态，直到不再是 RUNNING
    pollPlanStatus(currentRunPlan.value.id)
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '执行失败')
  } finally {
    runLoading.value = false
  }
}

function pollPlanStatus(planId) {
  let pollCount = 0
  const maxPolls = 120 // 最多轮询2分钟（每次间隔1秒）
  const pollInterval = setInterval(async () => {
    pollCount++
    if (pollCount > maxPolls) {
      clearInterval(pollInterval)
      return
    }
    try {
      const res = await getTestPlan(planId)
      const plan = res.data
      // 更新列表中对应计划的状态
      const index = plans.value.findIndex(p => p.id === planId)
      if (index !== -1) {
        plans.value[index] = plan
      }
      // 执行完成，停止轮询
      if (plan.execution_status !== 'running') {
        clearInterval(pollInterval)
      }
    } catch (e) {
      console.error('轮询计划状态失败:', e)
    }
  }, 1000)
}

// 计划项操作
function handleCaseSelectionChange(val) {
  selectedCases.value = val
}

function handleSuiteSelectionChange(val) {
  selectedSuites.value = val
}

async function confirmAddCases() {
  if (!editingPlanId.value) return
  try {
    const items = selectedCases.value.map(c => ({
      item_type: 'test_case',
      test_case_id: c.id
    }))
    await addPlanItemsBatch(editingPlanId.value, { items })
    ElMessage.success('添加成功')
    showAddCaseDialog.value = false
    selectedCases.value = []
    loadPlanItems(editingPlanId.value)
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function confirmAddSuites() {
  if (!editingPlanId.value) return
  try {
    const items = selectedSuites.value.map(s => ({
      item_type: 'test_suite',
      test_suite_id: s.id
    }))
    await addPlanItemsBatch(editingPlanId.value, { items })
    ElMessage.success('添加成功')
    showAddSuiteDialog.value = false
    selectedSuites.value = []
    loadPlanItems(editingPlanId.value)
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function removeItem(item) {
  try {
    await removePlanItem(editingPlanId.value, item.id)
    ElMessage.success('移除成功')
    loadPlanItems(editingPlanId.value)
  } catch (e) {
    ElMessage.error('移除失败')
  }
}

onMounted(async () => {
  await loadProjects()
  if (projectId.value) {
    loadPlans()
    loadLoginConfigs()
    loadTestCases()
    loadSuites()
  }
})
</script>

<style scoped lang="scss">
.page-container {
  height: calc(100vh - 100px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.card-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.mode-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.plan-items-container {
  width: 100%;
}

.plan-items-toolbar {
  margin-bottom: 10px;
}
</style>
