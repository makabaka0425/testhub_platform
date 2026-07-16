<template>
  <div class="page-container">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="goBack" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <el-divider direction="vertical" />
        <h1 class="page-title">{{ plan.name || '测试计划详情' }}</h1>
        <el-tag v-if="plan.execution_status" :type="getStatusTag(plan.execution_status)" style="margin-left: 12px">
          {{ getStatusText(plan.execution_status) }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button type="success" @click="showRunDialog = true" :disabled="planItems.length === 0">
          <el-icon><VideoPlay /></el-icon>
          执行
        </el-button>
        <el-button type="primary" @click="showEditDialog = true">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button type="danger" @click="handleDelete">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <div class="content-wrapper">
      <!-- 左侧：基本信息 -->
      <div class="info-panel">
        <div class="panel-card">
          <div class="panel-title">基本信息</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="计划名称">{{ plan.name }}</el-descriptions-item>
            <el-descriptions-item label="描述">{{ plan.description || '-' }}</el-descriptions-item>
            <el-descriptions-item label="执行模式">
              <el-tag size="small" :type="plan.execution_mode === 'shared_session' ? 'success' : 'info'">
                {{ plan.execution_mode === 'shared_session' ? '共享会话' : '独立模式' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="登录配置" v-if="plan.execution_mode === 'shared_session'">
              {{ plan.login_config_name || '未配置' }}
            </el-descriptions-item>
            <el-descriptions-item label="清理SQL">
              <span v-if="plan.cleanup_sql" class="sql-text">{{ plan.cleanup_sql }}</span>
              <span v-else style="color: #909399">无</span>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDate(plan.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ formatDate(plan.updated_at) }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 执行统计 -->
        <div class="panel-card">
          <div class="panel-title">执行统计</div>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value">{{ plan.total_cases || 0 }}</div>
              <div class="stat-label">总用例</div>
            </div>
            <div class="stat-item">
              <div class="stat-value" style="color: #67c23a">{{ plan.passed_count || 0 }}</div>
              <div class="stat-label">通过</div>
            </div>
            <div class="stat-item">
              <div class="stat-value" style="color: #f56c6c">{{ plan.failed_count || 0 }}</div>
              <div class="stat-label">失败</div>
            </div>
            <div class="stat-item">
              <div class="stat-value" style="color: #e6a23c">{{ plan.skipped_count || 0 }}</div>
              <div class="stat-label">跳过</div>
            </div>
          </div>
        </div>

        <!-- 最近执行历史 -->
        <div class="panel-card">
          <div class="panel-title">执行历史</div>
          <div v-if="executionHistory.length === 0" class="empty-text">暂无执行记录</div>
          <div v-else class="history-list">
            <div v-for="record in executionHistory.slice(0, 5)" :key="record.id" class="history-item">
              <el-tag size="small" :type="getHistoryStatusTag(record.status)">{{ getHistoryStatusText(record.status) }}</el-tag>
              <span class="history-time">{{ formatDate(record.started_at) }}</span>
              <span class="history-result">{{ record.passed_cases || 0 }}/{{ record.total_cases || 0 }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：计划项管理 -->
      <div class="items-panel">
        <div class="panel-card items-card">
          <div class="panel-title-row">
            <div class="panel-title">计划项 ({{ planItems.length }})</div>
            <div class="panel-actions">
              <el-button type="primary" size="small" @click="showAddCaseDialog = true; loadPlanGroupTree()">
                <el-icon><Plus /></el-icon>
                添加用例
              </el-button>
              <el-button type="success" size="small" @click="showAddSuiteDialog = true">
                <el-icon><Plus /></el-icon>
                添加套件
              </el-button>
            </div>
          </div>

          <div v-if="planItems.length === 0" class="empty-items">
            <el-empty description="暂无计划项，请添加用例或套件" :image-size="80" />
          </div>

          <draggable
            v-else
            v-model="planItems"
            item-key="id"
            handle=".drag-handle"
            @end="onDragEnd"
            ghost-class="ghost-item"
          >
            <template #item="{ element, index }">
              <div class="plan-item-row">
                <div class="drag-handle">
                  <el-icon><Rank /></el-icon>
                </div>
                <div class="item-index">{{ index + 1 }}</div>
                <el-tag size="small" :type="element.item_type === 'test_suite' ? 'warning' : ''" class="item-type-tag">
                  {{ element.item_type === 'test_suite' ? '套件' : '用例' }}
                </el-tag>
                <div class="item-name">
                  {{ element.item_type === 'test_suite' ? element.test_suite_name : element.test_case_name }}
                </div>
                <div class="item-info">
                  <span v-if="element.item_type === 'test_suite'" class="case-count">
                    {{ element.test_case_count || 0 }} 个用例
                  </span>
                </div>
                <el-button link type="danger" @click="removeItem(element)" class="remove-btn">
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
            </template>
          </draggable>
        </div>
      </div>
    </div>

    <!-- 编辑计划对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑测试计划" width="600px" :close-on-click-modal="false">
      <el-form ref="editFormRef" :model="editForm" :rules="formRules" label-width="100px">
        <el-form-item label="计划名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入计划名称" />
        </el-form-item>
        <el-form-item label="计划描述" prop="description">
          <el-input v-model="editForm.description" type="textarea" placeholder="请输入计划描述" />
        </el-form-item>
        <el-form-item label="执行模式" prop="execution_mode">
          <el-radio-group v-model="editForm.execution_mode">
            <el-radio label="per_case">独立模式</el-radio>
            <el-radio label="shared_session">共享会话模式</el-radio>
          </el-radio-group>
          <div class="mode-desc">
            <span v-if="editForm.execution_mode === 'per_case'">每个计划项独立启动浏览器，互不影响</span>
            <span v-else>所有计划项共享同一浏览器会话，计划级配置登录，项内登录自动跳过</span>
          </div>
        </el-form-item>
        <el-form-item v-if="editForm.execution_mode === 'shared_session'" label="登录配置" prop="login_config">
          <el-select v-model="editForm.login_config" placeholder="请选择登录配置" clearable filterable style="width: 100%">
            <el-option v-for="cfg in loginConfigs" :key="cfg.id" :label="cfg.name" :value="cfg.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="清理SQL">
          <el-input v-model="editForm.cleanup_sql" type="textarea" :rows="3" placeholder="计划执行完毕后执行的清理SQL，多条用分号分隔" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="submitting">保存</el-button>
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
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, Delete, VideoPlay, Plus, Search, Rank, Close } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import {
  getTestPlan, updateTestPlan, deleteTestPlan,
  getPlanItems, addPlanItemsBatch, removePlanItem, updatePlanItemOrder, runTestPlan,
  getPlanExecutionHistory, getTestCasesAll, getTestSuites, getLoginConfigs, getTestCaseGroupTree
} from '@/api/ui_automation'

const route = useRoute()
const router = useRouter()
const planId = computed(() => route.params.id)

// 数据
const plan = ref({})
const planItems = ref([])
const loginConfigs = ref([])
const allTestCases = ref([])
const allSuites = ref([])
const executionHistory = ref([])
const loading = ref(false)

// 对话框
const showEditDialog = ref(false)
const showAddCaseDialog = ref(false)
const showAddSuiteDialog = ref(false)
const showRunDialog = ref(false)
const submitting = ref(false)
const runLoading = ref(false)

// 编辑表单
const editFormRef = ref(null)
const editForm = ref({
  name: '', description: '', execution_mode: 'per_case',
  login_config: null, cleanup_sql: ''
})
const formRules = {
  name: [{ required: true, message: '请输入计划名称', trigger: 'blur' }],
  execution_mode: [{ required: true, message: '请选择执行模式', trigger: 'change' }]
}

// 执行配置
const runConfig = ref({ engine: 'playwright', browser: 'chrome', headless: false })

// 添加用例/套件
const addCaseSearch = ref('')
const selectedCases = ref([])
const addSuiteSearch = ref('')
const selectedSuites = ref([])
const planGroupFilter = ref(null)
const planGroupTree = ref([])

// 计算属性
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

// 状态映射
function getStatusTag(status) {
  const map = { not_run: 'info', passed: 'success', failed: 'danger', running: 'warning', skipped: 'warning' }
  return map[status] || 'info'
}
function getStatusText(status) {
  const map = { not_run: '未执行', passed: '通过', failed: '失败', running: '执行中', skipped: '跳过' }
  return map[status] || '未知'
}
function getHistoryStatusTag(status) {
  const map = { SUCCESS: 'success', FAILED: 'danger', RUNNING: 'warning', PENDING: 'info' }
  return map[status] || 'info'
}
function getHistoryStatusText(status) {
  const map = { SUCCESS: '通过', FAILED: '失败', RUNNING: '执行中', PENDING: '等待中' }
  return map[status] || status || '未知'
}
function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString('zh-CN')
}

function isCaseAlreadyAdded(caseId) {
  return planItems.value.some(i => i.item_type === 'test_case' && i.test_case === caseId)
}
function isSuiteAlreadyAdded(suiteId) {
  return planItems.value.some(i => i.item_type === 'test_suite' && i.test_suite === suiteId)
}

// 数据加载
async function loadPlan() {
  loading.value = true
  try {
    const res = await getTestPlan(planId.value)
    plan.value = res.data
  } catch (e) {
    ElMessage.error('加载计划详情失败')
    router.push({ name: 'UiTestPlans' })
  } finally {
    loading.value = false
  }
}

async function loadPlanItems() {
  try {
    const res = await getPlanItems(planId.value)
    planItems.value = res.data || []
  } catch (e) {
    console.error('加载计划项失败:', e)
    planItems.value = []
  }
}

async function loadLoginConfigs() {
  if (!plan.value.project) return
  try {
    const res = await getLoginConfigs({ project: plan.value.project })
    loginConfigs.value = res.data.results || res.data || []
  } catch (e) { console.error(e) }
}

async function loadTestCases() {
  if (!plan.value.project) return
  try {
    const res = await getTestCasesAll({ project: plan.value.project, page_size: 500 })
    allTestCases.value = res.data.results || res.data || []
  } catch (e) { console.error(e) }
}

async function loadSuites() {
  if (!plan.value.project) return
  try {
    const res = await getTestSuites({ project: plan.value.project })
    allSuites.value = res.data.results || res.data || []
  } catch (e) { console.error(e) }
}

const loadPlanGroupTree = async () => {
  if (!plan.value.project) { planGroupTree.value = []; return }
  try {
    const response = await getTestCaseGroupTree({ project: plan.value.project })
    planGroupTree.value = response.data || []
  } catch (error) { console.error('获取用例分组树失败:', error) }
}

async function loadExecutionHistory() {
  try {
    const res = await getPlanExecutionHistory(planId.value)
    executionHistory.value = res.data.results || res.data || []
  } catch (e) {
    console.error('加载执行历史失败:', e)
    executionHistory.value = []
  }
}

// 操作
function goBack() {
  router.push({ name: 'UiTestPlans' })
}

async function submitEdit() {
  if (!editFormRef.value) return
  await editFormRef.value.validate()
  submitting.value = true
  try {
    await updateTestPlan(planId.value, editForm.value)
    ElMessage.success('更新成功')
    showEditDialog.value = false
    loadPlan()
  } catch (e) {
    ElMessage.error('更新失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确定删除该测试计划吗？删除后不可恢复。', '提示', { type: 'warning' })
    await deleteTestPlan(planId.value)
    ElMessage.success('删除成功')
    router.push({ name: 'UiTestPlans' })
  } catch (e) { /* cancelled */ }
}

// 执行
async function confirmRun() {
  runLoading.value = true
  try {
    await runTestPlan(planId.value, runConfig.value)
    ElMessage.success('测试计划开始执行')
    showRunDialog.value = false
    pollPlanStatus()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '执行失败')
  } finally {
    runLoading.value = false
  }
}

function pollPlanStatus() {
  let pollCount = 0
  const maxPolls = 120
  const pollInterval = setInterval(async () => {
    pollCount++
    if (pollCount > maxPolls) {
      clearInterval(pollInterval)
      return
    }
    try {
      const res = await getTestPlan(planId.value)
      plan.value = res.data
      if (res.data.execution_status !== 'running') {
        clearInterval(pollInterval)
        loadExecutionHistory()
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
  try {
    const items = selectedCases.value.map(c => ({
      item_type: 'test_case',
      test_case_id: c.id
    }))
    await addPlanItemsBatch(planId.value, { items })
    ElMessage.success('添加成功')
    showAddCaseDialog.value = false
    selectedCases.value = []
    loadPlanItems()
    loadPlan() // 刷新统计
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function confirmAddSuites() {
  try {
    const items = selectedSuites.value.map(s => ({
      item_type: 'test_suite',
      test_suite_id: s.id
    }))
    await addPlanItemsBatch(planId.value, { items })
    ElMessage.success('添加成功')
    showAddSuiteDialog.value = false
    selectedSuites.value = []
    loadPlanItems()
    loadPlan() // 刷新统计
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function removeItem(item) {
  try {
    await ElMessageBox.confirm('确定移除该计划项吗？', '提示', { type: 'warning' })
    await removePlanItem(planId.value, item.id)
    ElMessage.success('移除成功')
    loadPlanItems()
    loadPlan()
  } catch (e) { /* cancelled */ }
}

// 拖拽排序
async function onDragEnd() {
  const itemOrders = planItems.value.map((item, index) => ({
    item_id: item.id,
    order: index + 1
  }))
  try {
    await updatePlanItemOrder(planId.value, itemOrders)
  } catch (e) {
    ElMessage.error('排序保存失败')
    loadPlanItems() // 回滚
  }
}

// 打开编辑对话框时填充表单
function openEditDialog() {
  editForm.value = {
    name: plan.value.name,
    description: plan.value.description,
    execution_mode: plan.value.execution_mode,
    login_config: plan.value.login_config,
    cleanup_sql: plan.value.cleanup_sql || ''
  }
  showEditDialog.value = true
}

// 监听编辑对话框打开
import { watch } from 'vue'
watch(showEditDialog, (val) => {
  if (val) openEditDialog()
})

onMounted(async () => {
  await loadPlan()
  if (plan.value.project) {
    loadLoginConfigs()
    loadTestCases()
    loadSuites()
  }
  loadPlanItems()
  loadExecutionHistory()
})
</script>

<style scoped lang="scss">
.page-container {
  padding: 20px;
  height: calc(100vh - 100px);
  overflow: hidden;
  background: #f5f5f5;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: white;
  padding: 16px 20px;
  border-radius: 4px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
}

.back-btn {
  font-size: 14px;
  padding: 0;
}

.page-title {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.content-wrapper {
  flex: 1;
  display: flex;
  gap: 20px;
  min-height: 0;
}

// 左侧信息面板
.info-panel {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

// 右侧计划项面板
.items-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.panel-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
}

.items-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.panel-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-shrink: 0;

  .panel-title {
    margin-bottom: 0;
  }
}

.panel-actions {
  display: flex;
  gap: 8px;
}

// 统计网格
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

// SQL文本
.sql-text {
  font-family: monospace;
  font-size: 12px;
  color: #606266;
  word-break: break-all;
}

// 执行历史
.empty-text {
  text-align: center;
  color: #909399;
  font-size: 13px;
  padding: 8px 0;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.history-time {
  color: #909399;
  font-size: 12px;
}

.history-result {
  color: #606266;
  margin-left: auto;
}

// 计划项
.empty-items {
  padding: 40px 0;
}

.plan-item-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 8px;
  background: white;
  transition: all 0.2s;

  &:hover {
    border-color: #409eff;
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  }
}

.drag-handle {
  cursor: grab;
  color: #c0c4cc;
  font-size: 16px;
  padding: 0 4px;

  &:hover {
    color: #409eff;
  }

  &:active {
    cursor: grabbing;
  }
}

.item-index {
  width: 28px;
  height: 28px;
  background: #f0f2f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #606266;
  flex-shrink: 0;
}

.item-type-tag {
  flex-shrink: 0;
}

.item-name {
  flex: 1;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-info {
  flex-shrink: 0;
  font-size: 12px;
  color: #909399;
}

.case-count {
  background: #fdf6ec;
  color: #e6a23c;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.remove-btn {
  flex-shrink: 0;
}

.ghost-item {
  opacity: 0.5;
  background: #ecf5ff;
}

.mode-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
</style>
