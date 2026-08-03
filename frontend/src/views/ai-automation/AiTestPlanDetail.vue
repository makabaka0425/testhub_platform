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
            <el-descriptions-item label="平台">
              <el-tag size="small" :type="plan.platform === 'web' ? '' : 'warning'">
                {{ plan.platform === 'web' ? 'Web端' : 'APP端' }}
              </el-tag>
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
      </div>

      <!-- 右侧：计划项管理 -->
      <div class="items-panel">
        <div class="panel-card items-card">
          <div class="panel-title-row">
            <div class="panel-title">计划项 ({{ planItems.length }})</div>
            <div class="panel-actions">
              <el-button type="primary" size="small" @click="showAddCaseDialog = true">
                <el-icon><Plus /></el-icon>
                添加用例
              </el-button>
            </div>
          </div>

          <div v-if="planItems.length === 0" class="empty-items">
            <el-empty description="暂无计划项，请添加用例" :image-size="80" />
          </div>

          <div v-else class="items-list">
            <div v-for="(item, index) in planItems" :key="item.id" class="plan-item-row">
              <div class="item-index">{{ index + 1 }}</div>
              <div class="item-name">{{ item.midscene_case_name }}</div>
              <el-tag size="small" :type="item.platform === 'web' ? '' : 'warning'" class="item-type-tag">
                {{ item.platform === 'web' ? 'Web端' : 'APP端' }}
              </el-tag>
              <el-button link type="danger" @click="removeItem(item)" class="remove-btn">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>
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
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加用例对话框 -->
    <el-dialog v-model="showAddCaseDialog" title="添加用例" width="600px">
      <div style="margin-bottom: 15px">
        <el-input v-model="addCaseSearch" placeholder="搜索用例名称" clearable>
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
      </div>
      <el-table :data="filteredAvailableCases" height="400" @selection-change="handleCaseSelectionChange">
        <el-table-column type="selection" width="55" :selectable="row => !isCaseAlreadyAdded(row.id)" />
        <el-table-column prop="name" label="用例名称" min-width="200" show-overflow-tooltip />
        <el-table-column label="平台" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.platform === 'web' ? '' : 'warning'">
              {{ row.platform === 'web' ? 'Web端' : 'APP端' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showAddCaseDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAddCases" :disabled="selectedCases.length === 0">
          添加 ({{ selectedCases.length }})
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行确认对话框 -->
    <el-dialog v-model="showRunDialog" title="执行测试计划" width="400px">
      <p>确定执行测试计划「{{ plan.name }}」？</p>
      <p style="color: #909399; font-size: 13px; margin-top: 8px">将按顺序逐个提交用例到Midscene微服务执行</p>
      <template #footer>
        <el-button @click="showRunDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmRun" :loading="runLoading">执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, Delete, VideoPlay, Plus, Search, Close } from '@element-plus/icons-vue'
import {
  getAiTestPlan, updateAiTestPlan, deleteAiTestPlan,
  getAiPlanItems, addAiPlanItemsBatch, removeAiPlanItem, runAiTestPlan,
  getMidsceneCases
} from '@/api/ui_automation'

const route = useRoute()
const router = useRouter()
const planId = computed(() => route.params.id)

// 数据
const plan = ref({})
const planItems = ref([])
const allMidsceneCases = ref([])
const loading = ref(false)

// 对话框
const showEditDialog = ref(false)
const showAddCaseDialog = ref(false)
const showRunDialog = ref(false)
const submitting = ref(false)
const runLoading = ref(false)

// 编辑表单
const editFormRef = ref(null)
const editForm = ref({
  name: '', description: ''
})
const formRules = {
  name: [{ required: true, message: '请输入计划名称', trigger: 'blur' }]
}

// 添加用例
const addCaseSearch = ref('')
const selectedCases = ref([])

// 计算属性
const filteredAvailableCases = computed(() => {
  if (!allMidsceneCases.value) return []
  let result = allMidsceneCases.value
  // 只显示与计划平台匹配的用例
  if (plan.value.platform) {
    result = result.filter(c => c.platform === plan.value.platform)
  }
  if (addCaseSearch.value) {
    const kw = addCaseSearch.value.toLowerCase()
    result = result.filter(c => c.name.toLowerCase().includes(kw))
  }
  return result
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
function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString('zh-CN')
}

function isCaseAlreadyAdded(caseId) {
  return planItems.value.some(i => i.midscene_case === caseId)
}

// 数据加载
async function loadPlan() {
  loading.value = true
  try {
    const res = await getAiTestPlan(planId.value)
    plan.value = res.data
  } catch (e) {
    ElMessage.error('加载计划详情失败')
    router.push({ name: 'AiTestPlans' })
  } finally {
    loading.value = false
  }
}

async function loadPlanItems() {
  try {
    const res = await getAiPlanItems(planId.value)
    planItems.value = res.data || []
  } catch (e) {
    console.error('加载计划项失败:', e)
    planItems.value = []
  }
}

async function loadMidsceneCases() {
  if (!plan.value.project) return
  try {
    const res = await getMidsceneCases({ project: plan.value.project, page_size: 500 })
    allMidsceneCases.value = res.data.results || res.data || []
  } catch (e) { console.error(e) }
}

// 操作
function goBack() {
  router.push({ name: 'AiTestPlans' })
}

// 监听编辑对话框打开
watch(showEditDialog, (val) => {
  if (val) {
    editForm.value = {
      name: plan.value.name,
      description: plan.value.description
    }
  }
})

async function submitEdit() {
  if (!editFormRef.value) return
  await editFormRef.value.validate()
  submitting.value = true
  try {
    await updateAiTestPlan(planId.value, editForm.value)
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
    await deleteAiTestPlan(planId.value)
    ElMessage.success('删除成功')
    router.push({ name: 'AiTestPlans' })
  } catch (e) { /* cancelled */ }
}

// 执行
async function confirmRun() {
  runLoading.value = true
  try {
    await runAiTestPlan(planId.value)
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
  const maxPolls = 600  // 最多10分钟
  const pollInterval = setInterval(async () => {
    pollCount++
    if (pollCount > maxPolls) {
      clearInterval(pollInterval)
      loadPlan()  // 超时后做一次最终刷新
      return
    }
    try {
      const res = await getAiTestPlan(planId.value)
      plan.value = res.data
      if (res.data.execution_status !== 'running') {
        clearInterval(pollInterval)
        loadPlan()  // 执行完成后刷新完整数据
        loadPlanItems()
      }
    } catch (e) {
      console.error('轮询计划状态失败:', e)
    }
  }, 3000)  // 3秒轮询一次
}

// 计划项操作
function handleCaseSelectionChange(val) {
  selectedCases.value = val
}

async function confirmAddCases() {
  try {
    const midscene_case_ids = selectedCases.value.map(c => c.id)
    await addAiPlanItemsBatch(planId.value, { midscene_case_ids })
    ElMessage.success('添加成功')
    showAddCaseDialog.value = false
    selectedCases.value = []
    loadPlanItems()
    loadPlan()
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function removeItem(item) {
  try {
    await ElMessageBox.confirm('确定移除该计划项吗？', '提示', { type: 'warning' })
    await removeAiPlanItem(planId.value, item.id)
    ElMessage.success('移除成功')
    loadPlanItems()
    loadPlan()
  } catch (e) { /* cancelled */ }
}

onMounted(async () => {
  await loadPlan()
  loadPlanItems()
  loadMidsceneCases()
})
</script>

<style scoped lang="scss">
.page-container {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 0;
}

.page-header {
  height: 64px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0;
}

.header-left {
  display: flex;
  align-items: center;
}

.back-btn {
  font-size: 14px;
  padding: 0;
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
  border: 1px solid #ebeef5;
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

// 计划项
.empty-items {
  padding: 40px 0;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.plan-item-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background: white;
  transition: all 0.2s;

  &:hover {
    border-color: #409eff;
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
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

.remove-btn {
  flex-shrink: 0;
}
</style>
