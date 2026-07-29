<template>
  <div class="page-container">
    <div class="page-titlebar">
      <h1 class="page-title">{{ $t('uiAutomation.execution.title') }}</h1>
      <div class="titlebar-actions">
        <el-select v-model="projectId" :placeholder="$t('uiAutomation.common.selectProject')" class="titlebar-select" @change="onProjectChange">
          <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
      </div>
    </div>

    <div class="workspace">
      <div class="list-column">
        <!-- 搜索区域卡片 -->
        <div class="filter-bar">
          <el-form :inline="true" :model="queryParams">
            <el-form-item :label="$t('uiAutomation.common.search')">
              <el-input
                v-model="queryParams.search"
                :placeholder="$t('uiAutomation.execution.searchPlaceholder')"
                clearable
                style="width: 200px"
                @keyup.enter="handleSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item :label="$t('uiAutomation.common.status')">
              <el-select v-model="queryParams.status" :placeholder="$t('uiAutomation.execution.statusFilter')" clearable style="width: 130px">
                <el-option :label="$t('uiAutomation.status.pending')" value="pending" />
                <el-option :label="$t('uiAutomation.status.running')" value="running" />
                <el-option :label="$t('uiAutomation.status.passed')" value="passed" />
                <el-option :label="$t('uiAutomation.status.failed')" value="failed" />
                <el-option :label="$t('uiAutomation.status.error')" value="error" />
                <el-option label="跳过" value="skipped" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('uiAutomation.execution.browserFilter')">
              <el-select v-model="queryParams.browser" :placeholder="$t('uiAutomation.execution.browserFilter')" clearable style="width: 130px">
                <el-option label="Chrome" value="chrome" />
                <el-option label="Firefox" value="firefox" />
                <el-option label="Safari" value="safari" />
                <el-option label="Edge" value="edge" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSearch">{{ $t('uiAutomation.common.query') }}</el-button>
              <el-button @click="resetQuery">{{ $t('uiAutomation.common.reset') }}</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 执行列表面板 -->
        <section class="panel list-panel">
          <div class="panel__header">
            <span class="panel__title">执行列表</span>
          </div>

          <div class="panel__body execution-table-wrapper">
              <el-table
                ref="tableRef"
                :data="executions"
                v-loading="loading"
                height="100%"
                row-key="id"
                :expand-row-keys="expandedKeys"
                :row-class-name="getRowClassName"
                @expand-change="handleExpandChange"
              >
              <!-- 展开列（仅计划/套件类型显示） -->
              <el-table-column type="expand" width="50">
                <template #default="{ row }">
                  <div v-if="row._loadingChildren" class="expand-loading">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    <span>加载中...</span>
                  </div>
                  <div v-else-if="row.item_type === 'plan'" class="expand-content" :style="{ '--grid-columns': gridColumns }">
                    <!-- 计划子项：套件+用例 -->
                    <template v-for="child in (row._children || [])" :key="child.id">
                      <!-- 套件子项 -->
                      <div v-if="child.item_type === 'suite'" class="child-suite">
                        <div class="child-grid-row" @click="toggleSuiteChildren(row, child)">
                          <div class="cg-name">
                            <el-icon class="expand-icon" :class="{ 'is-expanded': child._expanded }">
                              <ArrowRight />
                            </el-icon>
                            <span>{{ child.name }}</span>
                          </div>
                          <div class="cg-center"><el-tag type="warning" size="small">套件</el-tag></div>
                          <div class="cg-center"><el-tag :type="getStatusType(child.status)" size="small">{{ getStatusText(child.status) }}</el-tag></div>
                          <div class="cg-center">{{ formatDateTime(child.started_at) }}</div>
                          <div class="cg-center"><span v-if="child.duration != null">{{ formatDuration(child.duration) }}</span><span v-else>-</span></div>
                          <div class="cg-center"><span v-if="child.total_cases">{{ child.passed_cases || 0 }}/{{ child.total_cases }}</span><span v-else>-</span></div>
                          <div class="cg-center">-</div>
                          <div class="cg-op"><el-button type="primary" link size="small" @click.stop="viewPlanSuiteDetail(child)">详情</el-button></div>
                        </div>
                        <!-- 套件内用例（三级） -->
                        <div v-if="child._expanded && child.children" class="suite-children">
                          <div
                            v-for="subCase in child.children"
                            :key="subCase.id"
                            class="child-grid-row sub-case-row"
                          >
                            <div class="cg-name" style="padding-left: 28px;">{{ subCase.name }}</div>
                            <div class="cg-center"><el-tag type="info" size="small">用例</el-tag></div>
                            <div class="cg-center"><el-tag :type="getStatusType(subCase.status)" size="small">{{ getStatusText(subCase.status) }}</el-tag></div>
                            <div class="cg-center">{{ formatDateTime(subCase.started_at) }}</div>
                            <div class="cg-center"><span v-if="subCase.duration != null">{{ formatDuration(subCase.duration) }}</span><span v-else>-</span></div>
                            <div class="cg-center">-</div>
                            <div class="cg-center">-</div>
                            <div class="cg-op"><el-button type="primary" link size="small" @click="viewCaseDetail(subCase)">详情</el-button></div>
                          </div>
                        </div>
                      </div>
                      <!-- 独立用例子项 -->
                      <div v-else class="child-grid-row sub-case-row">
                        <div class="cg-name">{{ child.name }}</div>
                        <div class="cg-center"><el-tag type="info" size="small">用例</el-tag></div>
                        <div class="cg-center"><el-tag :type="getStatusType(child.status)" size="small">{{ getStatusText(child.status) }}</el-tag></div>
                        <div class="cg-center">{{ formatDateTime(child.started_at) }}</div>
                        <div class="cg-center"><span v-if="child.duration != null">{{ formatDuration(child.duration) }}</span><span v-else>-</span></div>
                        <div class="cg-center">-</div>
                        <div class="cg-center">-</div>
                        <div class="cg-op"><el-button type="primary" link size="small" @click="viewCaseDetail(child)">详情</el-button></div>
                      </div>
                    </template>
                  </div>
                  <div v-else-if="row.item_type === 'suite'" class="expand-content" :style="{ '--grid-columns': gridColumns }">
                    <!-- 套件子项：用例列表 -->
                    <div
                      v-for="child in (row._children || [])"
                      :key="child.id"
                      class="child-grid-row sub-case-row"
                    >
                      <div class="cg-name">{{ child.name }}</div>
                      <div class="cg-center"><el-tag type="info" size="small">用例</el-tag></div>
                      <div class="cg-center"><el-tag :type="getStatusType(child.status)" size="small">{{ getStatusText(child.status) }}</el-tag></div>
                      <div class="cg-center">{{ formatDateTime(child.started_at) }}</div>
                      <div class="cg-center"><span v-if="child.duration != null">{{ formatDuration(child.duration) }}</span><span v-else>-</span></div>
                      <div class="cg-center">-</div>
                      <div class="cg-center">-</div>
                      <div class="cg-op"><el-button type="primary" link size="small" @click="viewCaseDetail(child)">详情</el-button></div>
                    </div>
                  </div>
                </template>
              </el-table-column>

              <!-- 名称列 -->
              <el-table-column prop="name" label="名称" min-width="200">
                <template #default="{ row }">
                  <span class="name-text">{{ row.name }}</span>
                </template>
              </el-table-column>

              <!-- 类型列 -->
              <el-table-column label="类型" width="100" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.item_type === 'plan'" type="" size="small">计划</el-tag>
                  <el-tag v-else-if="row.item_type === 'suite'" type="warning" size="small">套件</el-tag>
                  <el-tag v-else type="info" size="small">用例</el-tag>
                </template>
              </el-table-column>

              <!-- 状态列 -->
              <el-table-column prop="status" label="状态" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
                </template>
              </el-table-column>

              <!-- 执行时间列 -->
              <el-table-column label="执行时间" width="180" align="center">
                <template #default="{ row }">
                  {{ formatDateTime(row.started_at) }}
                </template>
              </el-table-column>

              <!-- 耗时列 -->
              <el-table-column label="耗时" width="120" align="center">
                <template #default="{ row }">
                  <span v-if="row.duration != null">{{ formatDuration(row.duration) }}</span>
                  <span v-else>-</span>
                </template>
              </el-table-column>

              <!-- 通过率列（仅计划/套件） -->
              <el-table-column label="通过率" width="100" align="center">
                <template #default="{ row }">
                  <span v-if="row.total_cases != null && row.total_cases > 0">
                    {{ row.passed_cases || 0 }}/{{ row.total_cases }}
                  </span>
                  <span v-else>-</span>
                </template>
              </el-table-column>

              <!-- 执行人列 -->
              <el-table-column label="执行人" width="120" align="center">
                <template #default="{ row }">
                  <span>{{ row.executed_by || '-' }}</span>
                </template>
              </el-table-column>

              <!-- 操作列 -->
              <el-table-column label="操作" width="160">
                <template #default="{ row }">
                  <ActionCell :actions="getActions(row)" :row="row" :max-visible="3" />
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

    <!-- 执行详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="执行详情" width="900px">
      <div v-if="currentExecution" class="execution-detail">
        <!-- 基本信息 -->
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="currentExecution.item_type === 'plan' ? '计划名称' : currentExecution.item_type === 'suite' ? '套件名称' : '用例名称'">{{ currentExecution.name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentExecution.status)">{{ getStatusText(currentExecution.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="浏览器" v-if="!currentExecution.item_type || currentExecution.item_type === 'case'">{{ getBrowserText(currentExecution.browser) }}</el-descriptions-item>
          <el-descriptions-item label="执行人">{{ currentExecution.executed_by }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDateTime(currentExecution.started_at) }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ formatDateTime(currentExecution.finished_at) }}</el-descriptions-item>
          <el-descriptions-item label="耗时" :span="2">{{ formatDuration(currentExecution.duration) }}</el-descriptions-item>
          <!-- 计划/套件特有：通过率 -->
          <template v-if="currentExecution.item_type === 'plan' || currentExecution.item_type === 'suite'">
            <el-descriptions-item label="总用例数">{{ currentExecution.total_cases || 0 }}</el-descriptions-item>
            <el-descriptions-item label="通过/失败/跳过">
              {{ currentExecution.passed_cases || 0 }} / {{ currentExecution.failed_cases || 0 }} / {{ currentExecution.skipped_cases || 0 }}
            </el-descriptions-item>
          </template>
        </el-descriptions>

        <!-- 仅用例类型展示日志/截图/错误页签 -->
        <template v-if="!currentExecution.item_type || currentExecution.item_type === 'case'">
        <el-tabs v-model="activeTab" class="execution-tabs" style="margin-top: 20px;">
          <!-- 执行日志 -->
          <el-tab-pane label="执行日志" name="logs">
            <div class="logs-container">
              <div v-if="currentExecution.execution_logs">
                <div v-for="(step, index) in parseExecutionLogs(currentExecution.execution_logs)" :key="index" class="log-item">
                  <div class="log-header">
                    <el-tag :type="step.success ? 'success' : 'danger'" size="small">
                      步骤 {{ step.step_number }}
                    </el-tag>
                    <span class="log-action">{{ getActionText(step.action_type) }}</span>
                    <span class="log-desc">{{ step.description }}</span>
                  </div>
                  <div v-if="step.error" class="log-error">
                    <el-icon><WarningFilled /></el-icon>
                    <pre class="error-message">{{ step.error }}</pre>
                  </div>
                </div>
              </div>
              <el-empty v-else description="暂无执行日志" />
            </div>
          </el-tab-pane>

          <!-- 失败截图 -->
          <el-tab-pane label="失败截图" name="screenshots" v-if="currentExecution.status === 'failed' || currentExecution.status === 'error'">
            <div class="screenshots-container">
              <div v-if="currentExecution.screenshots && currentExecution.screenshots.length > 0">
                <div v-for="(screenshot, index) in currentExecution.screenshots" :key="index" class="screenshot-item">
                  <h5>{{ screenshot.description || `截图 ${index + 1}` }}</h5>
                  <div v-if="screenshot.url" class="screenshot-wrapper">
                    <img
                      :src="screenshot.url"
                      :alt="screenshot.description"
                      class="screenshot-img"
                      @error="handleImageError($event, screenshot)"
                    />
                  </div>
                  <div v-else class="screenshot-error">
                    <el-icon><WarningFilled /></el-icon>
                    <span>截图加载失败{{ screenshot.error || '未知原因' }}</span>
                  </div>
                  <p class="screenshot-time">{{ formatDateTime(screenshot.timestamp) }}</p>
                </div>
              </div>
              <el-empty v-else description="暂无截图" />
            </div>
          </el-tab-pane>

          <!-- 错误信息 -->
          <el-tab-pane label="错误信息" name="error" v-if="currentExecution.status === 'failed' || currentExecution.status === 'error'">
            <div class="errors-container">
              <div v-if="currentExecution.error_message" class="error-item">
                <div class="error-content">
                  <pre class="error-text">{{ currentExecution.error_message }}</pre>
                </div>
              </div>
              <el-empty v-else description="暂无错误信息" />
            </div>
          </el-tab-pane>
         </el-tabs>
        </template>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 重跑测试用例对话框 -->
    <el-dialog v-model="showRerunDialogVisible" title="重新运行" width="500px">
      <el-form :model="rerunFormData" label-width="100px">
        <el-form-item label="测试引擎">
          <el-radio-group v-model="rerunFormData.engine">
            <el-radio label="playwright">Playwright</el-radio>
            <el-radio label="selenium">Selenium</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="浏览器">
          <el-select v-model="rerunFormData.browser" style="width: 100%">
            <el-option label="Chrome" value="chrome" />
            <el-option label="Firefox" value="firefox" />
            <el-option label="Safari" value="safari" />
            <el-option label="Edge" value="edge" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行模式">
          <el-radio-group v-model="rerunFormData.headless">
            <el-radio :label="false">有头模式</el-radio>
            <el-radio :label="true">无头模式</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRerunDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleRerun" :loading="rerunning">确认重跑</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, WarningFilled, ArrowRight, Loading } from '@element-plus/icons-vue'
import ActionCell from '@/components/ActionCell.vue'
import {
  getExecutionUnifiedList,
  getExecutionChildren,
  getUiProjects,
  getTestCaseExecutionDetail,
  deleteTestCaseExecution,
  deleteTestExecution,
  runTestCase
} from '@/api/ui_automation'

// 项目和执行数据
const projects = ref([])
const projectId = ref('')
const executions = ref([])
const loading = ref(false)
const total = ref(0)
const pagination = reactive({
  currentPage: 1,
  pageSize: 20
})

// 搜索和筛选
const queryParams = reactive({
  search: '',
  status: '',
  browser: ''
})

// 展开控制
const expandedKeys = ref([])

// 动态grid列宽（从el-table表头实时读取）
const gridColumns = ref('minmax(200px, 1fr) 100px 100px 180px 120px 100px 120px 160px')
const tableRef = ref(null)

/** 从el-table表头读取各列实际宽度，同步到展开区域的CSS Grid */
function syncGridColumns() {
  const tableEl = tableRef.value?.$el
  if (!tableEl) return

  // 只取主表头（排除 fixed 列的副本）
  const mainHeader = tableEl.querySelector('.el-table__header-wrapper:not(.is-hidden)')
  if (!mainHeader) return
  const headerCells = mainHeader.querySelectorAll('th')
  // 跳过第一列（expand列 width=50），取后续8列的实际宽度
  const widths = []
  for (let i = 1; i < headerCells.length; i++) {
    const rect = headerCells[i].getBoundingClientRect()
    if (rect.width > 0) {
      widths.push(Math.round(rect.width) + 'px')
    }
  }
  // 所有列宽都从表头精确读取，保证和el-table完全一致
  if (widths.length >= 8) {
    gridColumns.value = widths.join(' ')
  }

  // 同步操作列内容对齐：直接遍历所有展开区域中的 .cg-op，设置 inline paddingLeft
  const opPadLeft = getActionCellPadding(tableEl)
  const expandContents = document.querySelectorAll('.expand-content .cg-op')
  expandContents.forEach(el => {
    el.style.paddingLeft = opPadLeft + 'px'
  })
}

/** 测量 el-table 操作列 .cell 的 padding-left，即操作按钮相对于 td 左边界的偏移 */
function getActionCellPadding(tableEl) {
  // 优先从已有行中测量
  const actionCell = tableEl.querySelector('.action-cell')
  const opTd = actionCell?.closest('td')
  if (actionCell && opTd) {
    const tdLeft = opTd.getBoundingClientRect().left
    const btnLeft = actionCell.getBoundingClientRect().left
    return Math.round(btnLeft - tdLeft)
  }
  // 回退：Element Plus el-table .cell 默认 padding 为 12px
  return 12
}

let resizeObserver = null

// 详情对话框相关
const showDetailDialog = ref(false)
const activeTab = ref('logs')
const currentExecution = ref(null)

// 重跑对话框相关
const showRerunDialogVisible = ref(false)
const rerunning = ref(false)
const rerunFormData = reactive({
  testCaseId: null,
  engine: 'playwright',
  browser: 'chrome',
  headless: false
})

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '-'
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 格式化持续时间
const formatDuration = (seconds) => {
  if (seconds == null) return '-'
  const totalSeconds = Math.floor(seconds)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const secs = totalSeconds % 60

  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`
  } else {
    return `${secs}s`
  }
}

// 获取状态样式
const getStatusType = (status) => {
  const statusMap = {
    'pending': 'info',
    'running': 'warning',
    'passed': 'success',
    'failed': 'danger',
    'error': 'danger',
    'skipped': 'warning'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    'pending': '待执行',
    'running': '执行中',
    'passed': '通过',
    'failed': '失败',
    'error': '错误',
    'skipped': '跳过'
  }
  return statusMap[status] || status
}

// 获取浏览器文本
const getBrowserText = (browser) => {
  const browserMap = {
    'chrome': 'Chrome',
    'firefox': 'Firefox',
    'safari': 'Safari',
    'edge': 'Edge'
  }
  return browserMap[browser] || browser || 'Chrome'
}

// 获取操作类型文本
const getActionText = (actionType) => {
  const actionMap = {
    'click': '点击',
    'fill': '输入',
    'select': '选择',
    'getText': '获取文本',
    'waitFor': '等待元素',
    'hover': '悬停',
    'scroll': '滚动',
    'screenshot': '截图',
    'assert': '断言',
    'wait': '等待',
    'navigate': '路由跳转'
  }
  return actionMap[actionType] || actionType
}

// 解析执行日志
const parseExecutionLogs = (logs) => {
  if (!logs) return []
  try {
    return typeof logs === 'string' ? JSON.parse(logs) : logs
  } catch (e) {
    console.error('解析执行日志失败:', e)
    return []
  }
}

// 处理图片加载错误
const handleImageError = (event) => {
  const img = event.target
  img.style.display = 'none'
}

// 加载项目列表
const loadProjects = async () => {
  try {
    const response = await getUiProjects({ page_size: 100 })
    projects.value = response.data.results || response.data
  } catch (error) {
    ElMessage.error('获取项目列表失败')
    console.error('获取项目列表失败:', error)
  }
}

// 加载执行列表
const loadExecutions = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      page_size: pagination.pageSize,
      ...queryParams
    }

    if (projectId.value) {
      params.project = projectId.value
    }

    const response = await getExecutionUnifiedList(params)
    const results = response.data.results || []
    // 为每条记录添加内部状态
    executions.value = results.map(item => ({
      ...item,
      _children: null,
      _loadingChildren: false,
    }))
    total.value = response.data.count || 0
    // 清空展开状态
    expandedKeys.value = []
  } catch (error) {
    ElMessage.error('获取执行列表失败')
    console.error('获取执行列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 处理展开/收起
const handleExpandChange = async (row, expandedRows) => {
  if (!row.has_children) return

  const isExpanding = expandedRows.some(r => r.id === row.id)
  if (isExpanding) {
    // 展开时加载子项
    expandedKeys.value = [row.id]
    await loadChildren(row)
    // 展开后同步列宽
    await nextTick()
    syncGridColumns()
  } else {
    expandedKeys.value = expandedKeys.value.filter(id => id !== row.id)
  }
}

// 行类名（用于隐藏用例行的展开图标）
const getRowClassName = ({ row }) => {
  return row.item_type === 'case' ? 'row-case' : ''
}

// 加载子项数据
const loadChildren = async (row) => {
  if (row._children) return // 已加载过

  row._loadingChildren = true
  try {
    const response = await getExecutionChildren(row.raw_id)
    const items = response.data.items || []
    // 为子项添加内部状态
    row._children = items.map(item => ({
      ...item,
      _expanded: false,
    }))
  } catch (error) {
    console.error('加载子项失败:', error)
    ElMessage.error('加载子项失败')
    row._children = []
  } finally {
    row._loadingChildren = false
  }
}

// 切换套件子项展开
const toggleSuiteChildren = (parentRow, suiteChild) => {
  suiteChild._expanded = !suiteChild._expanded
}

// 查看用例执行详情
const viewCaseDetail = async (child) => {
  // 子项数据来自children API，需要加载完整详情
  try {
    const rawId = child.raw_id
    if (!rawId) return
    const response = await getTestCaseExecutionDetail(rawId)
    currentExecution.value = response.data
    activeTab.value = 'logs'
    showDetailDialog.value = true
  } catch (error) {
    console.error('获取执行详情失败:', error)
    ElMessage.error('获取执行详情失败')
  }
}

// 项目变更处理
const onProjectChange = () => {
  localStorage.setItem('lastProjectId', projectId.value)
  queryParams.search = ''
  queryParams.status = ''
  queryParams.browser = ''
  pagination.currentPage = 1
  loadExecutions()
}

// 搜索处理
const handleSearch = () => {
  pagination.currentPage = 1
  loadExecutions()
}

// 重置查询
const resetQuery = () => {
  queryParams.search = ''
  queryParams.status = ''
  queryParams.browser = ''
  pagination.currentPage = 1
  loadExecutions()
}

// 分页处理
const handleSizeChange = (val) => {
  pagination.pageSize = val
  pagination.currentPage = 1
  loadExecutions()
}

const handleCurrentChange = (val) => {
  pagination.currentPage = val
  loadExecutions()
}

// 查看计划/套件执行详情（展示基本信息弹窗）
const viewPlanSuiteDetail = (row) => {
  currentExecution.value = {
    name: row.name,
    item_type: row.item_type,
    status: row.status,
    browser: row.browser,
    executed_by: row.executed_by,
    started_at: row.started_at,
    finished_at: row.finished_at,
    duration: row.duration,
    total_cases: row.total_cases,
    passed_cases: row.passed_cases,
    failed_cases: row.failed_cases,
    skipped_cases: row.skipped_cases,
  }
  activeTab.value = 'logs'
  showDetailDialog.value = true
}

// 重跑计划/套件
const handleRerunPlanSuite = (row) => {
  ElMessage.info(`${row.item_type === 'plan' ? '计划' : '套件'}重跑功能开发中`)
}

// 删除执行记录
const handleDelete = (row) => {
  ElMessageBox.confirm('确认删除此执行记录？', '提示', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      if (row.item_type === 'plan' || row.item_type === 'suite') {
        await deleteTestExecution(row.raw_id)
      } else if (row.item_type === 'case') {
        await deleteTestCaseExecution(row.raw_id)
      }
      ElMessage.success('删除成功')
      loadExecutions()
    } catch (error) {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  })
}

// 显示重跑对话框
const showRerunDialog = (execution) => {
  // 从统一列表中的用例行，或从子项用例
  if (execution.item_type === 'case') {
    // 需要获取test_case_id
    const testCaseId = execution.raw_id // 对于case类型，raw_id是TestCaseExecution的id
    // 但runTestCase需要的是test_case的id，从详情中获取
    getTestCaseExecutionDetail(execution.raw_id).then(res => {
      rerunFormData.testCaseId = res.data.test_case
      rerunFormData.engine = res.data.engine || 'playwright'
      rerunFormData.browser = res.data.browser || 'chrome'
      rerunFormData.headless = res.data.headless || false
      showRerunDialogVisible.value = true
    })
  }
}

// 执行重跑
const handleRerun = async () => {
  if (!rerunFormData.testCaseId) {
    ElMessage.error('无效的用例ID')
    return
  }

  rerunning.value = true
  try {
    const response = await runTestCase(rerunFormData.testCaseId, {
      engine: rerunFormData.engine,
      browser: rerunFormData.browser,
      headless: rerunFormData.headless
    })

    showRerunDialogVisible.value = false

    setTimeout(async () => {
      await loadExecutions()
    }, 500)

    if (response.data.success) {
      ElMessage.success('重跑成功')
    } else {
      ElMessage.warning('重跑完成，但有失败')
    }
  } catch (error) {
    showRerunDialogVisible.value = false
    ElMessage.error('重跑失败: ' + (error.response?.data?.message || error.message || '未知错误'))
    console.error('重跑失败:', error)
    setTimeout(async () => {
      await loadExecutions()
    }, 500)
  } finally {
    rerunning.value = false
  }
}

// 操作列按钮（仅父级列表行展示，子级不展示）
const getActions = (row) => {
  const actions = []
  if (row.item_type === 'plan' || row.item_type === 'suite') {
    actions.push({ key: 'detail', label: '详情', onClick: (r) => viewPlanSuiteDetail(r) })
    actions.push({
      key: 'rerun', label: '重跑',
      hidden: row.status !== 'failed' && row.status !== 'error',
      onClick: (r) => handleRerunPlanSuite(r)
    })
    actions.push({ key: 'delete', label: '删除', danger: true, onClick: (r) => handleDelete(r) })
  } else if (row.item_type === 'case') {
    actions.push({ key: 'detail', label: '详情', onClick: (r) => viewCaseDetail(r) })
    actions.push({
      key: 'rerun', label: '重跑',
      hidden: row.status !== 'failed' && row.status !== 'error',
      onClick: (r) => showRerunDialog(r)
    })
    actions.push({ key: 'delete', label: '删除', danger: true, onClick: (r) => handleDelete(r) })
  }
  return actions
}

onMounted(async () => {
  await loadProjects()
  if (projects.value.length > 0) {
    const savedProjectId = localStorage.getItem('lastProjectId')
    const exists = savedProjectId && projects.value.some(p => p.id === Number(savedProjectId) || p.id === savedProjectId)
    projectId.value = exists ? (typeof projects.value[0].id === 'number' ? Number(savedProjectId) : savedProjectId) : projects.value[0].id
  }
  await loadExecutions()
  // 初始同步列宽，并监听窗口resize
  await nextTick()
  syncGridColumns()
  resizeObserver = new ResizeObserver(() => syncGridColumns())
  const tableEl = tableRef.value?.$el
  if (tableEl) resizeObserver.observe(tableEl)
})

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})
</script>

<style scoped lang="scss">
/* ============================================================
   页面容器 / 标题栏 / 工作区
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

.execution-table-wrapper {
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

/* 展开区域样式 — CSS Grid 对齐表头列 */
.expand-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  color: var(--gray-400);
  font-size: 13px;
}

/* 展开行的 .cell 去掉默认 padding，避免整体右偏 */
:deep(.el-table__expanded-row .cell) {
  padding: 0 !important;
}

.expand-content {
  padding: 0;
  padding-left: 50px; /* 偏移展开列宽度，使子项名称与父级名称列对齐 */
  overflow: hidden;
}

.child-grid-row {
  display: grid;
  /* 8列宽度由JS动态同步自el-table表头 */
  grid-template-columns: var(--grid-columns, minmax(200px, 1fr) 100px 100px 180px 120px 100px 120px 160px);
  align-items: center;
  padding: 6px 0;
  cursor: default;
  min-height: 38px;
  border-bottom: 1px solid var(--gray-100);
}

.child-grid-row:last-child {
  border-bottom: none;
}

/* 套件行 — 左侧蓝色竖条标记层级 */
.child-suite > .child-grid-row {
  border-left: 3px solid #409eff;
  cursor: pointer;
  &:hover {
    background: #f5f7fa;
  }
}

/* 计划下的独立用例行 — 左侧灰色竖条 */
.expand-content > .sub-case-row {
  border-left: 3px solid var(--gray-300, #d0d0d0);
}

.sub-case-row {
  cursor: pointer;
  &:hover {
    background: var(--gray-50);
  }
}

/* 套件内三级用例行 — 浅灰背景 + 左侧虚线竖条 */
.suite-children .sub-case-row {
  background: #fafbfc;
  border-left: 3px dashed var(--gray-300, #d0d0d0);
  &:hover {
    background: #f3f5f7;
  }
}

.cg-name {
  display: flex;
  align-items: center;
  gap: 4px;
  padding-left: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 13px;
  color: var(--gray-800);
}

.cg-center {
  text-align: center;
}

.cg-op {
  display: flex;
  align-items: center;
  gap: 0;
  padding-left: 12px;
  padding-right: 8px;
}

.child-suite {
  display: flex;
  flex-direction: column;
  margin: 4px 0;
}

.suite-children {
  margin-left: 3px;  /* 与套件行左侧蓝色竖条对齐 */
  border-left: none;
  background: #fafbfc;
}

.expand-icon {
  transition: transform 0.2s;
  font-size: 12px;
  color: var(--gray-400);
  flex-shrink: 0;

  &.is-expanded {
    transform: rotate(90deg);
  }
}

.name-text {
  font-size: 13px;
  color: var(--gray-800);
}

/* 隐藏用例行的展开图标 */
.list-panel :deep(.el-table .el-table__expanded-cell) {
  padding: 0;
}

.list-panel :deep(.el-table .row-case .el-table__expand-icon) {
  visibility: hidden;
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

/* 执行详情弹窗样式 */
.execution-detail {
  .execution-tabs {
    margin-top: 20px;
  }

  .logs-container {
    max-height: 500px;
    overflow-y: auto;
    background: #f5f7fa;
    padding: 15px;
    border-radius: 4px;

    .log-item {
      margin-bottom: 15px;
      padding: 12px;
      background: white;
      border-radius: 4px;
      border-left: 3px solid #409eff;

      &:last-child {
        margin-bottom: 0;
      }

      .log-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;

        .log-action {
          font-weight: 500;
          color: #606266;
        }

        .log-desc {
          color: #909399;
          font-size: 14px;
        }
      }

      .log-error {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        color: #f56c6c;
        background: #fef0f0;
        padding: 8px 12px;
        border-radius: 4px;
        margin-top: 8px;
        font-size: 14px;

        .error-message {
          margin: 0;
          padding: 0;
          font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
          font-size: 13px;
          line-height: 1.6;
          white-space: pre-wrap;
          word-break: break-word;
          flex: 1;
        }

        .el-icon {
          margin-top: 2px;
          flex-shrink: 0;
        }
      }
    }
  }

  .screenshots-container {
    max-height: 600px;
    overflow-y: auto;
    padding: 10px;

    .screenshot-item {
      margin-bottom: 30px;
      text-align: center;

      h5 {
        margin: 0 0 15px 0;
        color: #303133;
        font-size: 14px;
      }

      .screenshot-wrapper {
        position: relative;
      }

      .screenshot-img {
        max-width: 100%;
        border: 1px solid #dcdfe6;
        border-radius: 4px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
      }

      .screenshot-error {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 12px 20px;
        background: #fef0f0;
        color: #f56c6c;
        border: 1px solid #fbc4c4;
        border-radius: 4px;
        font-size: 14px;

        .el-icon {
          font-size: 16px;
        }
      }

      .screenshot-time {
        margin: 10px 0 0 0;
        color: #909399;
        font-size: 12px;
      }
    }
  }

  .errors-container {
    padding: 10px;
    height: 100%;
    overflow-y: auto;
  }

  .error-item {
    background: #fff;
    border: 2px solid #f56c6c;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 15px;
  }

  .error-item:last-child {
    margin-bottom: 0;
  }

  .error-content {
    display: flex;
    flex-direction: column;
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
    overflow-x: auto;
  }
}
</style>
