<template>
  <div class="page-container">
    <!-- 顶部标题栏 -->
    <div class="page-titlebar">
      <h1 class="page-title">AI测试报告</h1>
      <div class="titlebar-actions">
        <el-button type="danger" size="small" :disabled="selectedRows.length === 0" @click="batchDelete">
          <el-icon><Delete /></el-icon>
          <span>批量删除</span>
        </el-button>
      </div>
    </div>

    <!-- 筛选条件 -->
    <div class="filter-bar">
      <el-select v-model="filters.project_id" placeholder="所属项目" clearable size="small" style="width:180px" @change="onFilterChange">
        <el-option v-for="p in projectList" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-select v-model="filters.platform" placeholder="平台" clearable size="small" style="width:120px" @change="onFilterChange">
        <el-option label="Web端" value="web" />
        <el-option label="APP端" value="app" />
      </el-select>
      <el-select v-model="filters.status" placeholder="执行状态" clearable size="small" style="width:120px" @change="onFilterChange">
        <el-option label="通过" value="passed" />
        <el-option label="失败" value="failed" />
        <el-option label="执行中" value="running" />
      </el-select>
      <el-select v-model="filters.report_only" placeholder="有报告" clearable size="small" style="width:120px" @change="onFilterChange">
        <el-option label="仅显示有报告" value="true" />
      </el-select>
    </div>

    <!-- 表格 -->
    <div class="card-container">
      <div class="table-scroll-area">
        <el-table
          :data="records"
          v-loading="loading"
          style="width:100%"
          height="100%"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="45" />
          <el-table-column label="#" width="60">
            <template #default="{ $index }">{{ (pagination.currentPage - 1) * pagination.pageSize + $index + 1 }}</template>
          </el-table-column>
          <el-table-column prop="case_name" label="用例名称" min-width="180" show-overflow-tooltip />
          <el-table-column prop="project_name" label="所属项目" width="140" show-overflow-tooltip />
          <el-table-column prop="platform" label="平台" width="80" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.platform === 'web'" size="small" type="">Web</el-tag>
              <el-tag v-else-if="row.platform === 'app'" size="small" type="warning">APP</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="statusTagMap[row.status] || 'info'" size="small">{{ statusTextMap[row.status] || row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="耗时(秒)" width="90" align="center">
            <template #default="{ row }">{{ row.duration ? row.duration.toFixed(2) : '-' }}</template>
          </el-table-column>
          <el-table-column prop="executed_by" label="执行人" width="90" align="center" />
          <el-table-column prop="started_at" label="执行时间" width="170">
            <template #default="{ row }">{{ formatDate(row.started_at) }}</template>
          </el-table-column>
          <el-table-column label="报告" width="100" align="center">
            <template #default="{ row }">
              <el-button v-if="row.report_url" type="primary" link size="small" @click="openReport(row)">查看</el-button>
              <span v-else class="text-muted">无</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="viewDetail(row)">详情</el-button>
              <el-button v-if="row.report_url" type="success" link size="small" @click="openReportNewTab(row)">新窗口</el-button>
              <el-button type="danger" link size="small" @click="deleteRecord(row)">删除</el-button>
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

    <!-- 详情弹窗 -->
    <el-dialog v-model="showDetailDialog" title="执行详情" width="800px" destroy-on-close>
      <div v-if="detailData" class="detail-body">
        <div class="detail-row">
          <span class="detail-label">用例名称：</span>
          <span>{{ detailData.case_name }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">执行状态：</span>
          <el-tag :type="statusTagMap[detailData.status] || 'info'" size="small">{{ statusTextMap[detailData.status] || detailData.status }}</el-tag>
        </div>
        <div class="detail-row">
          <span class="detail-label">执行时长：</span>
          <span>{{ detailData.duration ? detailData.duration.toFixed(2) + '秒' : '-' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">执行人：</span>
          <span>{{ detailData.executed_by || '-' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">执行时间：</span>
          <span>{{ formatDate(detailData.started_at) }}</span>
        </div>

        <!-- 步骤结果 -->
        <div v-if="detailData.step_results && detailData.step_results.length" class="detail-section">
          <h4>步骤结果</h4>
          <div class="steps-list">
            <div v-for="(step, idx) in detailData.step_results" :key="idx" class="step-item" :class="'step-item--' + step.status">
              <span class="step-order">{{ step.order || idx + 1 }}</span>
              <span class="step-type">[{{ step.type || 'action' }}]</span>
              <span class="step-instruction">{{ step.instruction || '-' }}</span>
              <el-tag :type="step.status === 'passed' ? 'success' : 'danger'" size="small">{{ step.status }}</el-tag>
            </div>
          </div>
        </div>

        <!-- 错误信息 -->
        <div v-if="detailData.error_message" class="detail-section">
          <h4>错误信息</h4>
          <pre class="error-box">{{ detailData.error_message }}</pre>
        </div>

        <!-- 回放报告 -->
        <div v-if="detailData.report_url" class="detail-section">
          <h4>回放报告</h4>
          <div class="report-container">
            <div class="report-toolbar">
              <span class="report-hint">Midscene AI 操作回放</span>
              <el-button link type="primary" @click="openReportNewTab(detailData)">新窗口打开</el-button>
            </div>
            <iframe :src="getReportSrc(detailData.report_url)" class="report-iframe" frameborder="0" allowfullscreen></iframe>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 报告弹窗（纯查看报告） -->
    <el-dialog v-model="showReportDialog" title="Midscene AI 操作回放" width="1000px" destroy-on-close>
      <div v-if="reportRow" class="report-container" style="height:600px">
        <div class="report-toolbar">
          <span class="report-hint">Midscene AI 操作回放（支持截图+操作轨迹回放）</span>
          <el-button link type="primary" @click="openReportNewTab(reportRow)">新窗口打开</el-button>
        </div>
        <iframe :src="getReportSrc(reportRow.report_url)" class="report-iframe" frameborder="0" allowfullscreen></iframe>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { getMidsceneExecutions, getMidsceneExecutionDetail, deleteMidsceneExecution, getAiProjects } from '@/api/ui_automation'

const records = ref([])
const loading = ref(false)
const total = ref(0)
const pagination = reactive({ currentPage: 1, pageSize: 20 })
const projectList = ref([])

const filters = reactive({
  project_id: null,
  platform: '',
  status: '',
  report_only: '',
})

const selectedRows = ref([])

// 详情弹窗
const showDetailDialog = ref(false)
const detailData = ref(null)

// 报告弹窗
const showReportDialog = ref(false)
const reportRow = ref(null)

const statusTagMap = { running: 'warning', passed: 'success', failed: 'danger' }
const statusTextMap = { running: '执行中', passed: '通过', failed: '失败' }

let pollTimer = null

// 加载项目列表
const loadProjects = async () => {
  try {
    const res = await getAiProjects()
    projectList.value = res.data?.results || res.data || []
  } catch (e) {
    console.error('加载项目列表失败', e)
  }
}

// 加载执行记录
const loadRecords = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      page_size: pagination.pageSize,
    }
    if (filters.project_id) params.project_id = filters.project_id
    if (filters.platform) params.platform = filters.platform
    if (filters.status) params.status = filters.status
    if (filters.report_only) params.report_only = filters.report_only

    const res = await getMidsceneExecutions(params)
    const data = res.data
    if (data.results) {
      records.value = data.results
      total.value = data.count || 0
    } else if (Array.isArray(data)) {
      records.value = data
      total.value = data.length
    }
  } catch (e) {
    console.error('加载报告列表失败', e)
    ElMessage.error('加载报告列表失败')
  } finally {
    loading.value = false
  }
}

const onFilterChange = () => {
  pagination.currentPage = 1
  loadRecords()
}

const handleSizeChange = () => {
  pagination.currentPage = 1
  loadRecords()
}

const handleCurrentChange = () => {
  loadRecords()
}

const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}

const formatDate = (val) => {
  if (!val) return '-'
  return new Date(val).toLocaleString('zh-CN', { hour12: false })
}

const getReportSrc = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return url.startsWith('/') ? url : '/' + url
}

// 查看详情
const viewDetail = async (row) => {
  try {
    const res = await getMidsceneExecutionDetail(row.id)
    detailData.value = res.data
    showDetailDialog.value = true
  } catch (e) {
    console.error('加载详情失败', e)
    ElMessage.error('加载详情失败')
  }
}

// 查看报告（弹窗）
const openReport = (row) => {
  reportRow.value = row
  showReportDialog.value = true
}

// 新窗口打开报告
const openReportNewTab = (row) => {
  const url = row.report_url
  if (url) window.open(getReportSrc(url), '_blank')
}

// 删除单条
const deleteRecord = async (row) => {
  try {
    await ElMessageBox.confirm('确认删除该执行记录？', '删除确认', { type: 'warning' })
    await deleteMidsceneExecution(row.id)
    ElMessage.success('删除成功')
    loadRecords()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除失败', e)
      ElMessage.error('删除失败')
    }
  }
}

// 批量删除
const batchDelete = async () => {
  if (selectedRows.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确认删除选中的 ${selectedRows.value.length} 条记录？`, '批量删除确认', { type: 'warning' })
    const ids = selectedRows.value.map(r => r.id)
    for (const id of ids) {
      await deleteMidsceneExecution(id)
    }
    ElMessage.success('批量删除成功')
    loadRecords()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('批量删除失败', e)
      ElMessage.error('批量删除失败')
    }
  }
}

// 轮询（仅在第一页且有执行中记录时）
const startPolling = () => {
  pollTimer = setInterval(() => {
    if (pagination.currentPage === 1 && !loading.value && !showDetailDialog.value && !showReportDialog.value) {
      const hasRunning = records.value.some(r => r.status === 'running')
      if (hasRunning) {
        getMidsceneExecutions({
          page: 1,
          page_size: pagination.pageSize,
          ...buildFilterParams()
        }).then(res => {
          const data = res.data
          if (data.results) {
            records.value = data.results
            total.value = data.count || 0
          }
        }).catch(() => {})
      }
    }
  }, 5000)
}

const buildFilterParams = () => {
  const params = {}
  if (filters.project_id) params.project_id = filters.project_id
  if (filters.platform) params.platform = filters.platform
  if (filters.status) params.status = filters.status
  if (filters.report_only) params.report_only = filters.report_only
  return params
}

onMounted(() => {
  loadProjects()
  loadRecords()
  startPolling()
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style lang="scss" scoped>
.page-container {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-titlebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 20px;
  flex-shrink: 0;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.titlebar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px 12px;
  flex-shrink: 0;
}

.card-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 0 20px;
}

.table-scroll-area {
  flex: 1;
  overflow: hidden;
}

.pagination-container {
  padding: 12px 0;
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

.text-muted {
  color: #c0c4cc;
  font-size: 12px;
}

/* 详情弹窗 */
.detail-body {
  max-height: 600px;
  overflow-y: auto;
}

.detail-row {
  margin-bottom: 12px;
}

.detail-label {
  font-weight: 600;
  color: #606266;
  margin-right: 8px;
}

.detail-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;

  h4 {
    font-size: 15px;
    color: #303133;
    margin-bottom: 12px;
  }
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  background: #f5f7fa;
  font-size: 13px;

  &--passed {
    border-left: 3px solid #67c23a;
  }
  &--failed {
    border-left: 3px solid #f56c6c;
  }
}

.step-order {
  font-weight: 700;
  color: #409eff;
  min-width: 20px;
}

.step-type {
  color: #909399;
  min-width: 60px;
}

.step-instruction {
  flex: 1;
  color: #303133;
}

.error-box {
  background: #fef0f0;
  color: #f56c6c;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

/* 报告容器 */
.report-container {
  display: flex;
  flex-direction: column;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  height: 500px;
}

.report-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.report-hint {
  font-size: 13px;
  color: #909399;
}

.report-iframe {
  flex: 1;
  width: 100%;
  border: none;
}
</style>
