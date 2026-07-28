<template>
  <div class="page-container">
    <!-- ==================== 计划列表视图 ==================== -->
    <div class="page-titlebar">
      <h1 class="page-title">测试计划</h1>
      <div class="titlebar-actions">
        <el-select v-model="projectId" placeholder="选择项目" class="titlebar-select" @change="onProjectChange">
          <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
        <el-button type="primary" size="small" @click="handleCreate">新建计划</el-button>
      </div>
    </div>

    <div class="workspace">
      <div class="list-column">
        <!-- 搜索区域卡片 -->
        <div class="filter-bar">
          <el-form :inline="true">
            <el-form-item label="计划名称">
              <el-input v-model="searchText" placeholder="搜索计划名称..." clearable @input="handleSearch" style="width: 200px">
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item label="执行模式">
              <el-select v-model="filterExecutionMode" placeholder="全部" clearable style="width: 130px">
                <el-option label="共享会话" value="shared_session" />
                <el-option label="独立模式" value="per_case" />
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
            <el-table :data="filteredPlans" v-loading="loading" height="100%">
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

    <!-- ==================== 执行记录弹窗 ==================== -->
    <el-dialog v-model="showRecordsDialog" :title="`执行记录 - ${recordsPlanName}`" width="860px" :close-on-click-modal="false" class="plan-records-dialog">
      <div v-loading="recordsLoading" class="plan-records-body">
        <el-empty v-if="!recordsLoading && planExecutionRecords.length === 0" description="暂无执行记录" :image-size="60" />
        <el-collapse v-model="expandedRecords" v-if="planExecutionRecords.length > 0">
          <el-collapse-item v-for="record in planExecutionRecords" :key="record.id" :name="record.id">
            <template #title>
              <div class="record-header">
                <span class="record-status" :class="`status-${record.status?.toLowerCase()}`">{{ getExecStatusText(record.status) }}</span>
                <span class="record-time">{{ formatRecordTime(record.started_at) }}</span>
                <span class="record-duration" v-if="record.duration != null">耗时 {{ record.duration.toFixed(1) }}s</span>
                <span class="record-stats">
                  <span class="stat-passed" v-if="record.passed_cases">通过{{ record.passed_cases }}</span>
                  <span class="stat-failed" v-if="record.failed_cases">失败{{ record.failed_cases }}</span>
                  <span class="stat-skipped" v-if="record.skipped_cases">跳过{{ record.skipped_cases }}</span>
                </span>
                <span class="record-executor">{{ record.executed_by }}</span>
              </div>
            </template>

            <div class="record-items">
              <!-- 列头 -->
              <div class="record-item-header">
                <span class="col-type">类型</span>
                <span class="col-name">名称</span>
                <span class="col-status">状态</span>
                <span class="col-time">执行时间</span>
                <span class="col-duration">耗时</span>
                <span class="col-action">操作</span>
              </div>
              <template v-for="(item, idx) in record.items" :key="idx">
                <!-- 套件项 -->
                <div v-if="item.item_type === 'test_suite'" class="record-item-block">
                  <div class="record-item-row is-suite" @click="toggleSuiteExpand(record.id, item.suite_id)">
                    <span class="col-type"><el-tag size="small" type="warning">套件</el-tag></span>
                    <span class="col-name">{{ item.suite_name }}</span>
                    <span class="col-status"><span class="status-tag" :class="`status-${getSuiteStatus(item)}`">{{ getCaseExecStatusText(getSuiteStatus(item)) }}</span></span>
                    <span class="col-time">{{ formatRecordTime(item.started_at || item.cases?.[0]?.started_at) }}</span>
                    <span class="col-duration" v-if="getSuiteDuration(item)">{{ getSuiteDuration(item).toFixed(1) }}s</span>
                    <span class="col-action">
                      <el-icon class="suite-expand-icon" :class="{ 'is-expanded': isSuiteExpanded(record.id, item.suite_id) }"><ArrowRight /></el-icon>
                    </span>
                  </div>
                  <div v-show="isSuiteExpanded(record.id, item.suite_id)" class="record-suite-cases">
                    <div v-for="(c, ci) in item.cases" :key="ci" class="record-item-row is-sub">
                      <span class="col-type"><el-tag size="small" type="info">用例</el-tag></span>
                      <span class="col-name">{{ c.test_case_name }}</span>
                      <span class="col-status"><span class="status-tag" :class="`status-${c.status}`">{{ getCaseExecStatusText(c.status) }}</span></span>
                      <span class="col-time">{{ formatRecordTime(c.started_at) }}</span>
                      <span class="col-duration" v-if="c.execution_time">{{ c.execution_time.toFixed(1) }}s</span>
                      <span class="col-action"><el-button link type="primary" size="small" @click="viewCaseExecDetail(c)">详情</el-button></span>
                    </div>
                  </div>
                </div>

                <!-- 单用例项 -->
                <div v-else class="record-item-row">
                  <span class="col-type"><el-tag size="small" type="info">用例</el-tag></span>
                  <span class="col-name">{{ item.test_case_name }}</span>
                  <span class="col-status"><span class="status-tag" :class="`status-${item.status}`">{{ getCaseExecStatusText(item.status) }}</span></span>
                  <span class="col-time">{{ formatRecordTime(item.started_at) }}</span>
                  <span class="col-duration" v-if="item.execution_time">{{ item.execution_time.toFixed(1) }}s</span>
                  <span class="col-action"><el-button link type="primary" size="small" @click="viewCaseExecDetail(item)">详情</el-button></span>
                </div>
              </template>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-dialog>

    <!-- ==================== 用例执行详情弹窗 ==================== -->
    <el-dialog v-model="caseDetailVisible" title="执行记录详情" width="680px" destroy-on-close append-to-body class="history-detail-dialog">
      <div v-if="caseDetailData" v-loading="caseDetailLoading" class="history-detail-inner">
        <div class="history-detail-header">
          <el-descriptions :column="3" size="small" border>
            <el-descriptions-item label="状态">
              <el-tag :type="getCaseExecTagType(caseDetailData.status)" size="small">{{ getCaseExecStatusText(caseDetailData.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="时长">{{ caseDetailData.execution_time ? caseDetailData.execution_time.toFixed(1) + 's' : '-' }}</el-descriptions-item>
            <el-descriptions-item label="测试引擎">{{ getEngineText(caseDetailData.engine) }}</el-descriptions-item>
            <el-descriptions-item label="浏览器">{{ caseDetailData.browser || '-' }}</el-descriptions-item>
            <el-descriptions-item label="开始时间">{{ formatRecordTime(caseDetailData.started_at) }}</el-descriptions-item>
            <el-descriptions-item label="结束时间">{{ formatRecordTime(caseDetailData.finished_at) }}</el-descriptions-item>
          </el-descriptions>
        </div>
        <div class="history-detail-tabs">
          <el-tabs v-model="caseDetailActiveTab">
            <el-tab-pane label="执行日志" name="logs">
              <div class="history-detail-scroll">
                <div class="history-detail-logs" v-if="caseDetailData.parsedLogs">
                  <div v-for="(step, index) in (Array.isArray(caseDetailData.parsedLogs) ? caseDetailData.parsedLogs : caseDetailData.parsedLogs.steps || [])" :key="index" class="log-item">
                    <div class="log-header">
                      <el-tag :type="step.success ? 'success' : 'danger'" size="small">
                        <template v-if="step.step_number === 'sql'">SQL</template>
                        <template v-else>步骤 {{ step.step_number }}</template>
                      </el-tag>
                      <span class="log-action">{{ step.action_type === 'precondition_sql' ? '前置数据SQL' : step.action_type === 'postcondition_sql' ? '后置清理SQL' : getActionText(step.action_type) }}</span>
                      <span class="log-desc">{{ step.description }}</span>
                      <span v-if="step.input_value" class="log-value">"{{ step.input_value }}"</span>
                    </div>
                    <div v-if="step.error" class="log-error">
                      <pre class="error-message">{{ step.error }}</pre>
                    </div>
                  </div>
                </div>
                <el-empty v-else description="暂无执行日志" />
              </div>
            </el-tab-pane>
            <el-tab-pane label="SQL执行" name="sql" v-if="caseDetailSqlExecs.length > 0">
              <div class="history-detail-scroll">
                <div class="sql-exec-list">
                  <div v-for="(sqlExec, idx) in caseDetailSqlExecs" :key="idx" class="sql-exec-item">
                    <div class="sql-exec-header">
                      <el-tag :type="sqlExec.type === 'precondition' ? 'warning' : sqlExec.type === 'precondition_case' ? 'success' : 'info'" size="small">{{ sqlExec.label }}</el-tag>
                      <el-tag :type="sqlExec.success ? 'success' : 'danger'" size="small">{{ sqlExec.success ? '执行成功' : '执行失败' }}</el-tag>
                      <span v-if="sqlExec.executed && sqlExec.total_affected !== undefined" class="sql-affected">影响 {{ sqlExec.total_affected }} 行</span>
                    </div>
                    <div v-if="sqlExec.original_sql" class="sql-block">
                      <div class="sql-block-label">原始SQL{{ sqlExec.original_sql !== sqlExec.resolved_sql ? '（含变量）' : '' }}：</div>
                      <pre class="sql-code">{{ sqlExec.original_sql }}</pre>
                    </div>
                    <div v-if="sqlExec.resolved_sql && sqlExec.resolved_sql !== sqlExec.original_sql" class="sql-block">
                      <div class="sql-block-label">解析后SQL：</div>
                      <pre class="sql-code sql-resolved">{{ sqlExec.resolved_sql }}</pre>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="失败截图" name="screenshots" v-if="caseDetailData.screenshots && caseDetailData.screenshots.length > 0">
              <div class="history-detail-scroll">
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                  <el-image v-for="(img, idx) in caseDetailData.screenshots" :key="idx" :src="img.url || img" style="width: 120px; height: 80px; border-radius: 4px; border: 1px solid #e4e7ed;" fit="cover" :preview-src-list="caseDetailData.screenshots.map(s => s.url || s)" :initial-index="idx" />
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="错误信息" name="errors" v-if="caseDetailErrors.length > 0">
              <div class="history-detail-scroll">
                <div class="errors-container">
                  <div v-for="(error, idx) in caseDetailErrors" :key="idx" class="error-item">
                    <div class="error-header">
                      <el-tag type="danger" size="large"><span class="error-tag-inner">✕ {{ error.message }}</span></el-tag>
                      <span v-if="error.step_number" class="error-step">步骤 {{ error.step_number }}</span>
                    </div>
                    <div v-if="error.details" class="error-details">
                      <div class="details-header">详细错误信息:</div>
                      <pre class="details-content">{{ error.details }}</pre>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, ArrowRight } from '@element-plus/icons-vue'
import ActionCell from '@/components/ActionCell.vue'
import {
  getTestPlans, getTestPlan, createTestPlan, updateTestPlan, deleteTestPlan,
  getPlanItems, addPlanItem, addPlanItemsBatch, removePlanItem, runTestPlan,
  getUiProjects, getTestCasesAll, getTestSuites, getLoginConfigs, getTestCaseGroupTree,
  getPlanExecutionHistory, getTestCaseExecutionDetail
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
const filterExecutionMode = ref('')
const filterExecutionStatus = ref('')
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
  let result = plans.value
  if (searchText.value) {
    const kw = searchText.value.toLowerCase()
    result = result.filter(p => p.name.toLowerCase().includes(kw))
  }
  if (filterExecutionMode.value) {
    result = result.filter(p => p.execution_mode === filterExecutionMode.value)
  }
  if (filterExecutionStatus.value) {
    result = result.filter(p => p.execution_status === filterExecutionStatus.value)
  }
  return result
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
// 操作列 actions
function getPlanActions(row) {
  return [
    { key: 'run', label: '执行', onClick: (r) => runPlan(r) },
    { key: 'records', label: '记录', onClick: (r) => openRecordsDialog(r) },
    { key: 'edit', label: '编辑', onClick: (r) => editPlan(r.id) },
    { key: 'delete', label: '删除', danger: true, onClick: (r) => deletePlan(r.id) }
  ]
}

// ==================== 执行记录弹窗 ====================
const showRecordsDialog = ref(false)
const recordsPlanName = ref('')
const recordsPlanId = ref(null)
const planExecutionRecords = ref([])
const recordsLoading = ref(false)
const expandedRecords = ref([])
const expandedSuites = ref({})
let recordsPollTimer = null

const isSuiteExpanded = (recordId, suiteId) => expandedSuites.value[`${recordId}-${suiteId}`] || false
const toggleSuiteExpand = (recordId, suiteId) => {
  const key = `${recordId}-${suiteId}`
  expandedSuites.value[key] = !expandedSuites.value[key]
}

const refreshExecutionRecords = async () => {
  if (!recordsPlanId.value) return
  try {
    const res = await getPlanExecutionHistory(recordsPlanId.value)
    planExecutionRecords.value = res.data.results || res.data || []
  } catch (e) { /* 静默 */ }
}

const startRecordsPoll = () => {
  stopRecordsPoll()
  recordsPollTimer = setInterval(async () => {
    await refreshExecutionRecords()
    const hasRunning = planExecutionRecords.value.some(r => r.status === 'RUNNING' || r.status === 'PENDING')
    if (!hasRunning) stopRecordsPoll()
  }, 3000)
}

const stopRecordsPoll = () => {
  if (recordsPollTimer) { clearInterval(recordsPollTimer); recordsPollTimer = null }
}

const openRecordsDialog = async (plan) => {
  recordsPlanName.value = plan.name
  recordsPlanId.value = plan.id
  showRecordsDialog.value = true
  recordsLoading.value = true
  planExecutionRecords.value = []
  expandedRecords.value = []
  expandedSuites.value = {}
  stopRecordsPoll()
  try {
    const res = await getPlanExecutionHistory(plan.id)
    planExecutionRecords.value = res.data.results || res.data || []
    const hasRunning = planExecutionRecords.value.some(r => r.status === 'RUNNING' || r.status === 'PENDING')
    if (hasRunning) startRecordsPoll()
  } catch (e) {
    console.error('获取执行记录失败:', e)
    ElMessage.error('获取执行记录失败')
  } finally {
    recordsLoading.value = false
  }
}

const getExecStatusText = (s) => ({ PENDING: '待执行', RUNNING: '运行中', SUCCESS: '成功', FAILED: '失败', ABORTED: '中止' }[s] || '未知')
const getCaseExecStatusText = (s) => ({ pending: '待执行', running: '执行中', passed: '通过', failed: '失败', skipped: '跳过', error: '错误' }[s] || '未知')
const getCaseExecTagType = (s) => ({ pending: 'info', running: 'warning', passed: 'success', failed: 'danger', skipped: 'warning', error: 'danger' }[s] || 'info')
// 套件聚合状态：任一失败则失败，否则任一跳过则跳过，否则通过
const getSuiteStatus = (item) => {
  const cases = item.cases || []
  if (cases.some(c => c.status === 'failed' || c.status === 'error')) return 'failed'
  if (cases.some(c => c.status === 'skipped')) return 'skipped'
  if (cases.every(c => c.status === 'passed')) return 'passed'
  if (cases.some(c => c.status === 'running')) return 'running'
  return 'pending'
}
// 套件聚合时长：累加用例时长
const getSuiteDuration = (item) => {
  const cases = item.cases || []
  const total = cases.reduce((sum, c) => sum + (c.execution_time || 0), 0)
  return total > 0 ? total : null
}
const formatRecordTime = (val) => val ? new Date(val).toLocaleString() : '-'
const getActionText = (action) => ({
  click: '点击', fill: '输入', select: '选择', navigate: '导航',
  assert: '断言', wait: '等待', hover: '悬停', getText: '获取文本',
  screenshot: '截图', scroll: '滚动', keyboard: '键盘操作',
  precondition_sql: '前置数据SQL', postcondition_sql: '后置清理SQL'
}[action] || action)
const getEngineText = (engine) => ({ playwright: 'Playwright', selenium: 'Selenium' }[engine] || engine || '-')

// ==================== 用例执行详情弹窗 ====================
const caseDetailVisible = ref(false)
const caseDetailData = ref(null)
const caseDetailLoading = ref(false)
const caseDetailActiveTab = ref('logs')

const caseDetailErrors = computed(() => {
  if (!caseDetailData.value) return []
  const steps = Array.isArray(caseDetailData.value.parsedLogs)
    ? caseDetailData.value.parsedLogs : (caseDetailData.value.parsedLogs?.steps || [])
  const errors = []
  for (const step of steps) {
    if (step.error && !step.success) {
      errors.push({
        message: step.step_number === 'sql' ? `${step.action_type === 'postcondition_sql' ? '后置清理SQL' : '前置数据SQL'}执行失败` : `步骤${step.step_number}执行失败`,
        step_number: step.step_number === 'sql' ? null : step.step_number,
        details: step.error || ''
      })
    }
  }
  return errors
})

const caseDetailSqlExecs = computed(() => {
  if (!caseDetailData.value || !caseDetailData.value.parsedLogs) return []
  const logs = caseDetailData.value.parsedLogs
  const result = []
  if (!Array.isArray(logs)) {
    if (logs.precondition_cases_sql && Array.isArray(logs.precondition_cases_sql)) {
      for (const preCase of logs.precondition_cases_sql) {
        if (preCase.precondition_sql) {
          result.push({
            type: 'precondition_case', label: `前置用例「${preCase.case_name}」- 前置数据SQL`,
            success: preCase.precondition_sql.executed !== false && !preCase.precondition_sql.has_error,
            executed: preCase.precondition_sql.executed !== false,
            original_sql: preCase.precondition_sql.original_sql || '', resolved_sql: preCase.precondition_sql.resolved_sql || '',
            total_affected: preCase.precondition_sql.total_affected || 0
          })
        }
      }
    }
    if (logs.precondition_sql) {
      const pre = logs.precondition_sql
      result.push({ type: 'precondition', label: '前置数据SQL', success: pre.executed !== false && !pre.has_error, executed: pre.executed !== false, original_sql: pre.original_sql || '', resolved_sql: pre.resolved_sql || '', total_affected: pre.total_affected || 0 })
    }
    if (logs.postcondition) {
      const post = logs.postcondition
      result.push({ type: 'postcondition', label: '后置清理SQL', success: post.executed !== false, executed: post.executed !== false, original_sql: post.original_sql || '', resolved_sql: post.resolved_sql || '', total_affected: post.total_affected || 0 })
    }
  }
  const steps = Array.isArray(logs) ? logs : (logs.steps || [])
  for (const step of steps) {
    if (step.step_number === 'sql' && (step.original_sql || step.resolved_sql || step.details)) {
      result.push({ type: step.action_type === 'postcondition_sql' ? 'postcondition' : 'precondition', label: step.description || (step.action_type === 'postcondition_sql' ? '后置清理SQL' : '前置数据SQL'), success: step.success, executed: true, original_sql: step.original_sql || '', resolved_sql: step.resolved_sql || '', total_affected: step.total_affected || 0 })
    }
  }
  return result
})

const viewCaseExecDetail = async (row) => {
  caseDetailVisible.value = true
  caseDetailLoading.value = true
  caseDetailData.value = null
  caseDetailActiveTab.value = 'logs'
  try {
    const res = await getTestCaseExecutionDetail(row.id)
    const record = res.data
    let logs = record.execution_logs
    if (typeof logs === 'string') {
      try { logs = JSON.parse(logs) } catch {
        // 纯文本格式：转换为步骤列表
        logs = { steps: logs.split('\n').filter(Boolean).map((line, i) => ({
          step_number: i + 1, action_type: '', description: '', success: !line.includes('失败'), error: line.includes('失败') ? line : null, input_value: ''
        })) }
      }
    }
    caseDetailData.value = { ...record, parsedLogs: logs }
  } catch (e) {
    console.error('获取执行详情失败:', e)
    ElMessage.error('获取执行详情失败')
  } finally {
    caseDetailLoading.value = false
  }
}

watch(showRecordsDialog, (val) => { if (!val) stopRecordsPoll() })
onBeforeUnmount(() => { stopRecordsPoll() })

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
    const savedProjectId = localStorage.getItem('lastProjectId')
    const exists = savedProjectId && projects.value.some(p => p.id === Number(savedProjectId) || p.id === savedProjectId)
    projectId.value = exists ? (typeof projects.value[0].id === 'number' ? Number(savedProjectId) : savedProjectId) : projects.value[0].id
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
  localStorage.setItem('lastProjectId', projectId.value)
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
/* ============================================================
   页面容器 / 标题栏 / 工作区（参照套件管理）
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

/* ============================================================
   操作按钮
   ============================================================ */
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

.mode-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

// ==================== 执行记录弹窗 ====================
.plan-records-body {
  height: 580px;
  overflow-y: auto;
}
.record-header {
  display: flex; align-items: center; gap: 16px; font-size: 13px; width: 100%;
  .record-status {
    padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 500;
    &.status-success { background: #ecfdf5; color: #059669; }
    &.status-running { background: #fef3c7; color: #d97706; }
    &.status-failed, &.status-aborted { background: #fef2f2; color: #dc2626; }
    &.status-pending { background: #f3f4f6; color: #9ca3af; }
  }
  .record-time { color: #606266; }
  .record-duration { color: #909399; font-size: 12px; }
  .record-stats { display: flex; gap: 8px; font-size: 12px; .stat-passed { color: #059669; } .stat-failed { color: #dc2626; } .stat-skipped { color: #d97706; } }
  .record-executor { color: #909399; font-size: 12px; margin-left: auto; }
}
.record-items { display: flex; flex-direction: column; gap: 0; }
.record-item-header {
  display: grid;
  grid-template-columns: 56px 1fr 60px 150px 60px 60px;
  gap: 8px;
  padding: 6px 12px;
  font-size: 12px;
  color: #909399;
  font-weight: 500;
  border-bottom: 1px solid #ebeef5;
  background: #fafbfc;
  align-items: center;
}
.record-item-block { border-bottom: 1px solid #ebeef5; overflow: hidden; }
.record-item-row {
  display: grid;
  grid-template-columns: 56px 1fr 60px 150px 60px 60px;
  gap: 8px;
  padding: 8px 12px;
  font-size: 13px;
  align-items: center;
  border-bottom: 1px solid #f5f7fa;
  &:last-child { border-bottom: none; }
  &.is-suite { cursor: pointer; user-select: none; background: #fafbfc; &:hover { background: #f0f2f5; } }
  &.is-sub { background: #fafbfc; }
}
.col-type { text-align: center; }
.col-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #303133; font-weight: 500; }
.col-time { color: #909399; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.col-status { text-align: center; }
.col-duration { color: #909399; font-size: 12px; text-align: right; }
.col-action { text-align: center; }
.suite-expand-icon { transition: transform 0.2s; color: #909399; &.is-expanded { transform: rotate(90deg); } }
.record-suite-cases { border-top: 1px solid #ebeef5; }
.status-tag {
  font-size: 12px;
  &.status-passed { color: #059669; } &.status-failed { color: #dc2626; } &.status-running { color: #d97706; }
  &.status-pending, &.status-skipped { color: #d97706; } &.status-error { color: #dc2626; }
}

// ==================== 用例执行详情弹窗 ====================
.history-detail-inner { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.history-detail-header { flex-shrink: 0; margin-bottom: 16px; }
.history-detail-tabs { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.history-detail-tabs :deep(.el-tabs) { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.history-detail-tabs :deep(.el-tabs__header) { flex-shrink: 0; margin-bottom: 8px; }
.history-detail-tabs :deep(.el-tabs__content) { flex: 1; min-height: 0; overflow: hidden; }
.history-detail-tabs :deep(.el-tab-pane) { height: 100%; }
.history-detail-scroll { height: 100%; overflow-y: auto; padding-right: 8px; }
.log-item {
  margin-bottom: 8px; padding: 8px 10px; background: #f8f9fa; border-radius: 4px; font-size: 13px;
  .log-header { display: flex; align-items: center; gap: 8px; }
  .log-action { color: #606266; font-weight: 500; }
  .log-desc { color: #909399; }
  .log-value { color: var(--brand-600, #409eff); font-size: 12px; font-weight: 500; background: var(--brand-50, #ecf5ff); padding: 1px 6px; border-radius: 3px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .log-error { margin-top: 6px; padding: 6px 8px; background: #fef2f2; border-radius: 4px; .error-message { margin: 0; font-size: 12px; color: #dc2626; white-space: pre-wrap; word-break: break-all; } }
}
.sql-exec-item { margin-bottom: 12px; padding: 12px; background: #f8f9fa; border-radius: 6px; }
.sql-exec-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.sql-affected { font-size: 12px; color: #909399; }
.sql-block { margin-bottom: 8px; }
.sql-block-label { font-size: 12px; color: #909399; margin-bottom: 4px; }
.sql-code { margin: 0; padding: 8px; background: #2d2d2d; color: #e5e5e5; border-radius: 4px; font-size: 12px; white-space: pre-wrap; word-break: break-all; }
.sql-resolved { border: 1px dashed #67c23a; }
.errors-container { display: flex; flex-direction: column; gap: 12px; }
.error-item {
  background: #fff; border: 2px solid #dc2626; border-radius: 8px; padding: 16px;
  .error-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #f3f4f6; gap: 8px; .el-tag { font-size: 14px; padding: 8px 12px; font-weight: 600; } }
  .error-step { background: #fef2f2; color: #dc2626; padding: 4px 12px; border-radius: 4px; font-weight: 600; font-size: 13px; }
  .error-details { background: #2d2d2d; border-radius: 8px; overflow: hidden; .details-header { color: #e5e5e5; font-size: 13px; padding: 12px 16px 6px; font-weight: 600; } .details-content { margin: 0; padding: 0 16px 12px; color: #f87171; font-size: 12px; white-space: pre-wrap; word-break: break-all; } }
}
</style>

<style lang="scss">
.plan-records-dialog .el-dialog__body {
  max-height: 680px;
  overflow: hidden;
  padding-bottom: 0;
}
</style>
