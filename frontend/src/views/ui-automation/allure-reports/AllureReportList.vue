<template>
  <div class="page-container">
    <div class="page-titlebar">
      <h1 class="page-title">Allure报告</h1>
      <div class="titlebar-actions">
        <el-select v-model="projectId" placeholder="选择项目" class="titlebar-select" @change="onProjectChange">
          <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
        <el-button type="primary" @click="showCreateDrawer = true">新建报告</el-button>
      </div>
    </div>

    <div class="workspace">
      <div class="list-column">
        <section class="panel list-panel">
          <div class="panel__body">
            <el-table :data="reports" v-loading="loading" height="100%">
              <el-table-column prop="name" label="报告名称" min-width="200">
                <template #default="{ row }">
                  <span class="name-text">{{ row.name }}</span>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="120" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.status === 'generating'" type="warning" size="small">
                    <el-icon class="is-loading"><Loading /></el-icon> 生成中
                  </el-tag>
                  <el-tag v-else-if="row.status === 'completed'" type="success" size="small">已完成</el-tag>
                  <el-tag v-else-if="row.status === 'failed'" type="danger" size="small">生成失败</el-tag>
                  <el-tag v-else type="info" size="small">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="通过率" width="120" align="center">
                <template #default="{ row }">
                  <template v-if="row.status === 'completed'">
                    <span :class="getPassRateClass(row.pass_rate)">{{ row.pass_rate }}%</span>
                    <span class="pass-detail">({{ row.passed_cases }}/{{ row.total_cases }})</span>
                  </template>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="总/通过/失败/跳过" width="180" align="center">
                <template #default="{ row }">
                  <template v-if="row.status === 'completed'">
                    <span>{{ row.total_cases }}</span> /
                    <span class="text-success">{{ row.passed_cases }}</span> /
                    <span class="text-danger">{{ row.failed_cases }}</span> /
                    <span class="text-warning">{{ row.skipped_cases }}</span>
                  </template>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="平均耗时" width="100" align="center">
                <template #default="{ row }">
                  <span v-if="row.status === 'completed' && row.avg_duration">{{ row.avg_duration }}s</span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="浏览器" width="100" align="center">
                <template #default="{ row }">
                  <span>{{ row.browser || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="创建人" width="100" align="center">
                <template #default="{ row }">
                  {{ row.created_by_name || '-' }}
                </template>
              </el-table-column>
              <el-table-column label="创建时间" width="180" align="center">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="180">
                <template #default="{ row }">
                  <el-button v-if="row.status === 'completed'" type="primary" link size="small" @click="viewReport(row)">查看</el-button>
                  <el-button v-if="row.status === 'failed'" type="warning" link size="small" @click="regenerate(row)">重新生成</el-button>
                  <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
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

    <!-- 新建报告抽屉 -->
    <el-drawer v-model="showCreateDrawer" title="新建Allure报告" size="480px" :before-close="handleDrawerClose">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="项目" prop="project">
          <el-select v-model="createForm.project" placeholder="选择项目" filterable style="width: 100%" @change="onFormProjectChange">
            <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="测试计划" prop="test_plan">
          <el-select v-model="createForm.test_plan" placeholder="选择测试计划" filterable style="width: 100%" :loading="plansLoading" @change="onPlanChange">
            <el-option v-for="plan in plans" :key="plan.id" :label="plan.name" :value="plan.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行批次" prop="test_execution">
          <el-select v-model="createForm.test_execution" placeholder="选择执行批次" style="width: 100%" :loading="batchesLoading" :disabled="!createForm.test_plan">
            <el-option v-for="batch in batches" :key="batch.id" :label="batch.label" :value="batch.id" :disabled="!batch.has_executed" />
          </el-select>
        </el-form-item>
        <el-form-item label="报告名称" prop="name">
          <el-input v-model="createForm.name" placeholder="输入报告名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleDrawerClose">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">生成报告</el-button>
      </template>
    </el-drawer>

    <!-- 失败详情弹窗 -->
    <el-dialog v-model="showErrorDialog" title="生成失败详情" width="600px">
      <div class="error-content">
        <pre class="error-text">{{ errorDetail }}</pre>
      </div>
      <template #footer>
        <el-button @click="showErrorDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import {
  getAllureReports,
  createAllureReport,
  deleteAllureReport,
  regenerateAllureReport,
  getPlanExecutionBatches,
} from '@/api/ui_automation'
import { getUiProjects } from '@/api/ui_automation'
import { getTestPlans } from '@/api/ui_automation'

// 数据
const projects = ref([])
const projectId = ref('')
const reports = ref([])
const loading = ref(false)
const total = ref(0)
const pagination = reactive({ currentPage: 1, pageSize: 20 })

// 新建报告
const showCreateDrawer = ref(false)
const creating = ref(false)
const createFormRef = ref(null)
const plans = ref([])
const plansLoading = ref(false)
const batches = ref([])
const batchesLoading = ref(false)
const createForm = reactive({
  project: '',
  test_plan: '',
  test_execution: '',
  name: '',
})
const createRules = {
  project: [{ required: true, message: '请选择项目', trigger: 'change' }],
  test_plan: [{ required: true, message: '请选择测试计划', trigger: 'change' }],
  test_execution: [{ required: true, message: '请选择执行批次', trigger: 'change' }],
  name: [{ required: true, message: '请输入报告名称', trigger: 'blur' }],
}

// 错误详情
const showErrorDialog = ref(false)
const errorDetail = ref('')

// 轮询定时器
let pollTimer = null

// 格式化日期
const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '-'
  return date.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

// 通过率样式
const getPassRateClass = (rate) => {
  if (rate >= 80) return 'text-success'
  if (rate >= 50) return 'text-warning'
  return 'text-danger'
}

// 加载项目
const loadProjects = async () => {
  try {
    const response = await getUiProjects({ page_size: 100 })
    projects.value = response.data.results || response.data
  } catch (error) {
    console.error('获取项目列表失败:', error)
  }
}

// 加载报告列表
const loadReports = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      page_size: pagination.pageSize,
    }
    if (projectId.value) params.project = projectId.value
    const response = await getAllureReports(params)
    reports.value = response.data.results || []
    total.value = response.data.count || 0
  } catch (error) {
    console.error('获取报告列表失败:', error)
    ElMessage.error('获取报告列表失败')
  } finally {
    loading.value = false
  }
}

// 项目切换
const onProjectChange = () => {
  localStorage.setItem('lastProjectId', projectId.value)
  pagination.currentPage = 1
  loadReports()
}

// 表单项目切换 → 加载计划
const onFormProjectChange = async (val) => {
  createForm.test_plan = ''
  createForm.test_execution = ''
  createForm.name = ''
  batches.value = []
  if (!val) { plans.value = []; return }
  plansLoading.value = true
  try {
    const response = await getTestPlans({ project: val, page_size: 100 })
    plans.value = response.data.results || []
  } catch (error) {
    console.error('获取计划列表失败:', error)
    plans.value = []
  } finally {
    plansLoading.value = false
  }
}

// 计划切换 → 加载执行批次
const onPlanChange = async (planId) => {
  createForm.test_execution = ''
  batches.value = []
  if (!planId) return

  // 自动生成报告名称
  const plan = plans.value.find(p => p.id === planId)
  if (plan) {
    const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    createForm.name = `${plan.name}_UI报告_${ts}`
  }

  batchesLoading.value = true
  try {
    const response = await getPlanExecutionBatches(planId)
    batches.value = response.data || []
  } catch (error) {
    console.error('获取执行批次失败:', error)
    batches.value = []
  } finally {
    batchesLoading.value = false
  }
}

// 创建报告
const handleCreate = async () => {
  if (!createFormRef.value) return
  await createFormRef.value.validate()

  creating.value = true
  try {
    await createAllureReport({
      name: createForm.name,
      project: createForm.project,
      test_plan: createForm.test_plan,
      test_execution: createForm.test_execution,
    })
    ElMessage.success('报告已开始生成')
    showCreateDrawer.value = false
    resetCreateForm()
    loadReports()
  } catch (error) {
    const msg = error.response?.data?.error || error.response?.data?.name?.[0] || '创建失败'
    ElMessage.error(msg)
  } finally {
    creating.value = false
  }
}

// 重置表单
const resetCreateForm = () => {
  createForm.project = ''
  createForm.test_plan = ''
  createForm.test_execution = ''
  createForm.name = ''
  plans.value = []
  batches.value = []
}

const handleDrawerClose = () => {
  showCreateDrawer.value = false
  resetCreateForm()
}

// 查看报告
const viewReport = (row) => {
  const url = `/ui-automation/allure-report-static/${row.id}/index.html`
  window.open(url, '_blank')
}

// 重新生成
const regenerate = async (row) => {
  try {
    await ElMessageBox.confirm('确认重新生成此报告？', '提示', { type: 'warning' })
    await regenerateAllureReport(row.id)
    ElMessage.success('已启动重新生成')
    loadReports()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确认删除此报告？报告文件将一并删除。', '提示', { type: 'warning' })
    await deleteAllureReport(row.id)
    ElMessage.success('删除成功')
    loadReports()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 分页
const handleSizeChange = (val) => {
  pagination.pageSize = val
  pagination.currentPage = 1
  loadReports()
}
const handleCurrentChange = (val) => {
  pagination.currentPage = val
  loadReports()
}

// 轮询：如果有生成中的报告则刷新
const startPolling = () => {
  pollTimer = setInterval(() => {
    const hasGenerating = reports.value.some(r => r.status === 'generating')
    if (hasGenerating) loadReports()
  }, 5000)
}

onMounted(async () => {
  await loadProjects()
  if (projects.value.length > 0) {
    const savedProjectId = localStorage.getItem('lastProjectId')
    const exists = savedProjectId && projects.value.some(p => p.id === Number(savedProjectId) || p.id === savedProjectId)
    projectId.value = exists ? (typeof projects.value[0].id === 'number' ? Number(savedProjectId) : savedProjectId) : projects.value[0].id
  }
  await loadReports()
  startPolling()
})

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
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

.list-panel {
  flex: 1;
  min-width: 0;
}

.list-panel .panel__body {
  padding: 0;
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

.name-text {
  font-size: 13px;
  color: var(--gray-800);
}

.text-success { color: #67c23a; }
.text-warning { color: #e6a23c; }
.text-danger { color: #f56c6c; }

.pass-detail {
  font-size: 12px;
  color: var(--gray-400);
  margin-left: 4px;
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

.error-content {
  max-height: 400px;
  overflow-y: auto;
}

.error-text {
  margin: 0;
  padding: 15px;
  background: #2d2d2d;
  color: #ff6b6b;
  border-radius: 4px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 生成中旋转动画 */
.is-loading {
  animation: rotating 1.5s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
