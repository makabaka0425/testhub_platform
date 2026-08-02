<template>
  <div class="page-container">
    <!-- 标题栏 -->
    <div class="page-titlebar">
      <h1 class="page-title">AI测试计划</h1>
      <div class="titlebar-actions">
        <el-select v-model="projectId" placeholder="选择项目" class="titlebar-select" @change="onProjectChange">
          <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
        <el-button type="primary" size="small" @click="handleCreate">新建计划</el-button>
      </div>
    </div>

    <div class="workspace">
      <div class="list-column">
        <!-- 搜索区域 -->
        <div class="filter-bar">
          <el-form :inline="true">
            <el-form-item label="计划名称">
              <el-input v-model="searchText" placeholder="搜索计划名称..." clearable style="width: 200px">
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item label="平台">
              <el-select v-model="filterPlatform" placeholder="全部" clearable style="width: 130px">
                <el-option label="Web端" value="web" />
                <el-option label="APP端" value="app" />
              </el-select>
            </el-form-item>
            <el-form-item label="执行状态">
              <el-select v-model="filterExecutionStatus" placeholder="全部" clearable style="width: 130px">
                <el-option label="未执行" value="not_run" />
                <el-option label="通过" value="passed" />
                <el-option label="失败" value="failed" />
                <el-option label="执行中" value="running" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- 计划列表面板 -->
        <section class="panel list-panel">
          <div class="panel__header">
            <span class="panel__title">计划列表</span>
          </div>

          <div class="panel__body plan-table-wrapper">
            <!-- 批量工具栏 -->
            <div class="batch-toolbar" v-if="selectedPlans.length > 0">
              <span class="batch-count">已选 {{ selectedPlans.length }} 项</span>
              <el-button size="small" type="success" @click="batchRunPlans" :loading="batchRunLoading">批量执行</el-button>
              <el-button size="small" type="danger" plain @click="batchDeletePlans">批量删除</el-button>
            </div>

            <el-table :data="filteredPlans" v-loading="loading" height="100%" row-key="id" @selection-change="handlePlanSelectionChange">
              <el-table-column type="selection" width="45" />
              <el-table-column type="index" label="序号" width="60" />
              <el-table-column prop="name" label="计划名称" min-width="180">
                <template #default="{ row }">
                  <el-link type="primary" @click="goToDetail(row.id)">{{ row.name }}</el-link>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="描述" min-width="150">
                <template #default="{ row }">
                  <span class="desc-text">{{ row.description || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="平台" width="90">
                <template #default="{ row }">
                  <el-tag size="small" :type="row.platform === 'web' ? '' : 'warning'">
                    {{ row.platform === 'web' ? 'Web端' : 'APP端' }}
                  </el-tag>
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
              <el-table-column prop="last_execution_time" label="执行时间" width="180" :formatter="formatDate" />
              <el-table-column prop="created_at" label="创建时间" width="180" :formatter="formatDate" />
              <el-table-column label="操作" width="160" fixed="right">
                <template #default="{ row }">
                  <ActionCell :actions="getPlanActions(row)" :row="row" :max-visible="3" />
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="pagination.currentPage"
              v-model:page-size="pagination.pageSize"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              :total="total"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </section>
      </div>
    </div>

    <!-- 创建/编辑计划对话框 -->
    <el-dialog v-model="showEditDialog" :title="isEditing ? '编辑测试计划' : '新建测试计划'" width="600px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="计划名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入计划名称" />
        </el-form-item>
        <el-form-item label="平台" prop="platform">
          <el-radio-group v-model="form.platform" :disabled="isEditing">
            <el-radio label="web">Web端</el-radio>
            <el-radio label="app">APP端</el-radio>
          </el-radio-group>
          <div class="mode-desc" v-if="!isEditing">选择平台后，只能添加该平台的用例</div>
        </el-form-item>
        <el-form-item label="计划描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请输入计划描述" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 执行确认对话框 -->
    <el-dialog v-model="showRunDialog" title="执行测试计划" width="400px">
      <p>确定执行测试计划「{{ currentRunPlan?.name }}」？</p>
      <p style="color: #909399; font-size: 13px; margin-top: 8px">将按顺序逐个提交用例到Midscene微服务执行</p>
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
import { Search } from '@element-plus/icons-vue'
import ActionCell from '@/components/ActionCell.vue'
import {
  getAiTestPlans, getAiTestPlan, createAiTestPlan, updateAiTestPlan, deleteAiTestPlan,
  runAiTestPlan,
  getAiProjects
} from '@/api/ui_automation'

const router = useRouter()

// 数据
const projects = ref([])
const projectId = ref(null)
const plans = ref([])
const loading = ref(false)
const total = ref(0)
const searchText = ref('')
const filterPlatform = ref('')
const filterExecutionStatus = ref('')
const pagination = ref({ currentPage: 1, pageSize: 20 })

// 对话框
const showEditDialog = ref(false)
const isEditing = ref(false)
const editingPlanId = ref(null)
const submitting = ref(false)

// 表单
const formRef = ref(null)
const form = ref({
  name: '', description: '', platform: 'web'
})
const formRules = {
  name: [{ required: true, message: '请输入计划名称', trigger: 'blur' }],
  platform: [{ required: true, message: '请选择平台', trigger: 'change' }]
}

// 批量操作
const selectedPlans = ref([])
const batchRunLoading = ref(false)

// 执行
const showRunDialog = ref(false)
const currentRunPlan = ref(null)
const runLoading = ref(false)

// 计算属性
const filteredPlans = computed(() => {
  let result = plans.value
  if (searchText.value) {
    const kw = searchText.value.toLowerCase()
    result = result.filter(p => p.name.toLowerCase().includes(kw))
  }
  if (filterPlatform.value) {
    result = result.filter(p => p.platform === filterPlatform.value)
  }
  if (filterExecutionStatus.value) {
    result = result.filter(p => p.execution_status === filterExecutionStatus.value)
  }
  return result
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

function goToDetail(planId) {
  router.push({ name: 'AiTestPlanDetail', params: { id: planId } })
}

function getPlanActions(row) {
  return [
    { key: 'run', label: '执行', onClick: (r) => runPlan(r) },
    { key: 'edit', label: '编辑', onClick: (r) => editPlan(r.id) },
    { key: 'delete', label: '删除', danger: true, onClick: (r) => deletePlan(r.id) }
  ]
}

function handlePlanSelectionChange(rows) {
  selectedPlans.value = rows
}

// ==================== 数据加载 ====================
async function loadProjects() {
  try {
    const res = await getAiProjects()
    projects.value = res.data.results || res.data || []
    if (projects.value.length > 0 && !projectId.value) {
      const savedProjectId = localStorage.getItem('lastAiProjectId')
      const exists = savedProjectId && projects.value.some(p => p.id === Number(savedProjectId) || p.id === savedProjectId)
      projectId.value = exists ? (typeof projects.value[0].id === 'number' ? Number(savedProjectId) : savedProjectId) : projects.value[0].id
    }
  } catch (e) { console.error(e) }
}

async function loadPlans() {
  if (!projectId.value) return
  loading.value = true
  try {
    const res = await getAiTestPlans({
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

function onProjectChange() {
  localStorage.setItem('lastAiProjectId', projectId.value)
  pagination.value.currentPage = 1
  loadPlans()
}

function handleSizeChange(val) {
  pagination.value.pageSize = val
  loadPlans()
}

function handleCurrentChange(val) {
  pagination.value.currentPage = val
  loadPlans()
}

// ==================== CRUD ====================
function handleCreate() {
  isEditing.value = false
  editingPlanId.value = null
  form.value = { name: '', description: '', platform: 'web' }
  showEditDialog.value = true
}

async function editPlan(planId) {
  isEditing.value = true
  editingPlanId.value = planId
  const found = plans.value.find(p => p.id === planId)
  form.value = {
    name: found?.name || '',
    description: found?.description || '',
    platform: found?.platform || 'web'
  }
  showEditDialog.value = true
}

async function submitForm() {
  if (!formRef.value) return
  await formRef.value.validate()
  submitting.value = true
  try {
    if (isEditing.value) {
      await updateAiTestPlan(editingPlanId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createAiTestPlan({ ...form.value, project: projectId.value })
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
    await deleteAiTestPlan(planId)
    ElMessage.success('删除成功')
    loadPlans()
  } catch (e) { /* cancelled */ }
}

// ==================== 执行 ====================
function runPlan(plan) {
  currentRunPlan.value = plan
  showRunDialog.value = true
}

async function confirmRun() {
  runLoading.value = true
  try {
    await runAiTestPlan(currentRunPlan.value.id)
    ElMessage.success('测试计划开始执行')
    showRunDialog.value = false
    pollPlanStatus(currentRunPlan.value.id)
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '执行失败')
  } finally {
    runLoading.value = false
  }
}

function pollPlanStatus(planId) {
  let pollCount = 0
  const maxPolls = 120
  const pollInterval = setInterval(async () => {
    pollCount++
    if (pollCount > maxPolls) {
      clearInterval(pollInterval)
      return
    }
    try {
      const res = await getAiTestPlan(planId)
      const plan = res.data
      const index = plans.value.findIndex(p => p.id === planId)
      if (index !== -1) {
        plans.value[index] = plan
      }
      if (plan.execution_status !== 'running') {
        clearInterval(pollInterval)
      }
    } catch (e) {
      console.error('轮询计划状态失败:', e)
    }
  }, 1000)
}

// ==================== 批量操作 ====================
async function batchDeletePlans() {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedPlans.value.length} 个计划？`, '提示', { type: 'warning' })
    let ok = 0, fail = 0
    for (const plan of selectedPlans.value) {
      try {
        await deleteAiTestPlan(plan.id)
        ok++
      } catch (e) { fail++; console.error(e) }
    }
    if (ok) ElMessage.success(`成功删除 ${ok} 个计划` + (fail ? `，${fail} 个失败` : ''))
    selectedPlans.value = []
    loadPlans()
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

async function batchRunPlans() {
  const valid = selectedPlans.value.filter(p => p.plan_item_count && p.plan_item_count > 0)
  const empty = selectedPlans.value.length - valid.length
  if (valid.length === 0) {
    ElMessage.warning('选中的计划均未包含计划项，无法执行')
    return
  }
  try {
    const tip = `确定批量执行 ${valid.length} 个计划？` + (empty ? `（${empty} 个计划无计划项，将跳过）` : '')
    await ElMessageBox.confirm(tip, '批量执行', { type: 'info' })
  } catch (e) { return }

  batchRunLoading.value = true
  let ok = 0, fail = 0
  for (const plan of valid) {
    try {
      await runAiTestPlan(plan.id)
      ok++
    } catch (e) {
      fail++
      console.error(e)
    }
  }
  if (ok) ElMessage.success(`已启动 ${ok} 个计划执行` + (fail ? `，${fail} 个失败` : ''))
  batchRunLoading.value = false
  selectedPlans.value = []
  loadPlans()
}

onMounted(async () => {
  await loadProjects()
  if (projectId.value) {
    loadPlans()
  }
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

.plan-table-wrapper {
  flex: 1;
  overflow: hidden;
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

/* 批量工具栏 */
.batch-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 6px;
  margin-bottom: 0;

  .batch-count {
    font-size: 13px;
    color: #409eff;
    font-weight: 500;
  }
}

.desc-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mode-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
</style>
