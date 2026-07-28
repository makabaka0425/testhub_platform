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
          <div class="panel-title-row">
            <div class="panel-title">执行历史</div>
            <el-button v-if="executionHistory.length > 0" link type="primary" size="small" @click="openRecordsDialog">查看全部</el-button>
          </div>
          <div v-if="executionHistory.length === 0" class="empty-text">暂无执行记录</div>
          <div v-else class="history-list">
            <div v-for="record in executionHistory.slice(0, 5)" :key="record.id" class="history-item" @click="openRecordsDialog">
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

    <!-- ==================== 执行记录弹窗 ==================== -->
    <el-dialog v-model="showRecordsDialog" :title="`执行记录 - ${plan.name}`" width="860px" :close-on-click-modal="false" class="plan-records-dialog">
      <div v-loading="recordsLoading" class="plan-records-body">
        <el-empty v-if="!recordsLoading && planExecutionRecords.length === 0" description="暂无执行记录" :image-size="60" />
        <el-collapse v-model="expandedRecords" v-if="planExecutionRecords.length > 0">
          <el-collapse-item v-for="record in planExecutionRecords" :key="record.id" :name="record.id">
            <template #title>
              <div class="record-header">
                <span class="record-status" :class="`status-${record.status?.toLowerCase()}`">{{ getExecStatusText(record.status) }}</span>
                <span class="record-time">{{ formatRecordTime(record.started_at) }}</span>
                <span class="record-duration" v-if="record.duration">{{ record.duration.toFixed(1) }}s</span>
                <span class="record-stats">
                  <span class="stat-passed" v-if="record.passed_cases">通过{{ record.passed_cases }}</span>
                  <span class="stat-failed" v-if="record.failed_cases">失败{{ record.failed_cases }}</span>
                  <span class="stat-skipped" v-if="record.skipped_cases">跳过{{ record.skipped_cases }}</span>
                </span>
                <span class="record-executor">{{ record.executed_by }}</span>
              </div>
            </template>

            <!-- 按计划项组织：套件可折叠，单用例平铺 -->
            <div class="record-items">
              <template v-for="(item, idx) in record.items" :key="idx">
                <!-- 套件项 -->
                <div v-if="item.item_type === 'test_suite'" class="record-item-block">
                  <div class="record-item-row is-suite" @click="toggleSuiteExpand(record.id, item.suite_id)">
                    <el-tag size="small" type="warning">套件</el-tag>
                    <span class="record-item-name">{{ item.suite_name }}</span>
                    <span class="status-tag" :class="`status-${getSuiteStatus(item)}`">{{ getCaseExecStatusText(getSuiteStatus(item)) }}</span>
                    <span class="record-item-time" v-if="getSuiteDuration(item)">{{ getSuiteDuration(item).toFixed(2) }}s</span>
                    <el-icon class="suite-expand-icon" :class="{ 'is-expanded': isSuiteExpanded(record.id, item.suite_id) }"><ArrowRight /></el-icon>
                  </div>
                  <div v-show="isSuiteExpanded(record.id, item.suite_id)" class="record-suite-cases">
                    <div v-for="(c, ci) in item.cases" :key="ci" class="record-item-row is-sub">
                      <el-tag size="small" type="info">用例</el-tag>
                      <span class="record-item-name">{{ c.test_case_name }}</span>
                      <span class="status-tag" :class="`status-${c.status}`">{{ getCaseExecStatusText(c.status) }}</span>
                      <span class="record-item-time" v-if="c.execution_time">{{ c.execution_time.toFixed(2) }}s</span>
                      <el-button link type="primary" size="small" @click="viewCaseExecDetail(c)">详情</el-button>
                    </div>
                  </div>
                </div>

                <!-- 单用例项 -->
                <div v-else class="record-item-row">
                  <el-tag size="small" type="info">用例</el-tag>
                  <span class="record-item-name">{{ item.test_case_name }}</span>
                  <span class="status-tag" :class="`status-${item.status}`">{{ getCaseExecStatusText(item.status) }}</span>
                  <span class="record-item-time" v-if="item.execution_time">{{ item.execution_time.toFixed(2) }}s</span>
                  <el-button link type="primary" size="small" @click="viewCaseExecDetail(item)">详情</el-button>
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
                        <template v-if="step.step_number === 'sql'">
                          <span style="display: inline-flex; align-items: center; gap: 4px;">SQL</span>
                        </template>
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
                    <div v-if="sqlExec.error" class="sql-exec-error">
                      <pre class="error-message">{{ sqlExec.error }}</pre>
                    </div>
                    <div v-if="sqlExec.original_sql" class="sql-block">
                      <div class="sql-block-label">原始SQL{{ sqlExec.original_sql !== sqlExec.resolved_sql ? '（含变量）' : '' }}：</div>
                      <pre class="sql-code">{{ sqlExec.original_sql }}</pre>
                    </div>
                    <div v-if="sqlExec.resolved_sql && sqlExec.resolved_sql !== sqlExec.original_sql" class="sql-block">
                      <div class="sql-block-label">解析后SQL：</div>
                      <pre class="sql-code sql-resolved">{{ sqlExec.resolved_sql }}</pre>
                    </div>
                    <div v-if="sqlExec.details && sqlExec.details.length > 0" class="sql-details">
                      <div class="sql-details-label">执行明细：</div>
                      <div v-for="(detail, di) in sqlExec.details" :key="di" class="sql-detail-row">
                        <span :class="['sql-detail-status', detail.error ? 'fail' : 'ok']">{{ detail.error ? '✗' : '✓' }}</span>
                        <pre class="sql-detail-code">{{ detail.sql }}</pre>
                        <span v-if="detail.affected !== undefined" class="sql-detail-affected">影响 {{ detail.affected }} 行</span>
                        <span v-if="detail.error" class="sql-detail-error">{{ detail.error }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="失败截图" name="screenshots" v-if="caseDetailData.screenshots && caseDetailData.screenshots.length > 0">
              <div class="history-detail-scroll">
                <div class="history-detail-screenshots">
                  <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <el-image v-for="(img, idx) in caseDetailData.screenshots" :key="idx" :src="img.url || img" style="width: 120px; height: 80px; border-radius: 4px; border: 1px solid #e4e7ed;" fit="cover" :preview-src-list="caseDetailData.screenshots.map(s => s.url || s)" :initial-index="idx" />
                  </div>
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="错误信息" name="errors" v-if="caseDetailErrors.length > 0">
              <div class="history-detail-scroll">
                <div class="errors-container">
                  <div v-for="(error, idx) in caseDetailErrors" :key="idx" class="error-item">
                    <div class="error-header">
                      <el-tag type="danger" size="large">
                        <span class="error-tag-inner"><span>✕ {{ error.message }}</span></span>
                      </el-tag>
                      <span v-if="error.step_number" class="error-step">步骤 {{ error.step_number }}</span>
                    </div>
                    <div v-if="error.action_type || error.element || error.description" class="error-meta">
                      <div v-if="error.action_type" class="meta-item">
                        <span class="meta-label">操作类型:</span>
                        <span class="meta-value">{{ error.action_type }}</span>
                      </div>
                      <div v-if="error.element" class="meta-item">
                        <span class="meta-label">目标元素:</span>
                        <span class="meta-value">{{ error.element }}</span>
                      </div>
                      <div v-if="error.description" class="meta-item">
                        <span class="meta-label">步骤描述:</span>
                        <span class="meta-value">{{ error.description }}</span>
                      </div>
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
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, Delete, VideoPlay, Plus, Search, Rank, Close, ArrowRight } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import {
  getTestPlan, updateTestPlan, deleteTestPlan,
  getPlanItems, addPlanItemsBatch, removePlanItem, updatePlanItemOrder, runTestPlan,
  getPlanExecutionHistory, getTestCasesAll, getTestSuites, getLoginConfigs, getTestCaseGroupTree,
  getTestCaseExecutionDetail
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

// ==================== 执行记录弹窗 ====================
const showRecordsDialog = ref(false)
const planExecutionRecords = ref([])
const recordsLoading = ref(false)
const expandedRecords = ref([])
const expandedSuites = ref({})  // `${recordId}-${suiteId}` -> boolean
let recordsPollTimer = null

const isSuiteExpanded = (recordId, suiteId) => {
  return expandedSuites.value[`${recordId}-${suiteId}`] || false
}
const toggleSuiteExpand = (recordId, suiteId) => {
  const key = `${recordId}-${suiteId}`
  expandedSuites.value[key] = !expandedSuites.value[key]
}

const refreshExecutionRecords = async () => {
  try {
    const res = await getPlanExecutionHistory(planId.value)
    planExecutionRecords.value = res.data.results || res.data || []
  } catch (e) {
    // 静默失败
  }
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
  if (recordsPollTimer) {
    clearInterval(recordsPollTimer)
    recordsPollTimer = null
  }
}

const openRecordsDialog = async () => {
  showRecordsDialog.value = true
  recordsLoading.value = true
  planExecutionRecords.value = []
  expandedRecords.value = []
  expandedSuites.value = {}
  stopRecordsPoll()
  try {
    const res = await getPlanExecutionHistory(planId.value)
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
    ? caseDetailData.value.parsedLogs
    : (caseDetailData.value.parsedLogs?.steps || [])
  const errors = []
  for (const step of steps) {
    if (step.error && !step.success) {
      errors.push({
        message: step.step_number === 'sql'
          ? `${step.action_type === 'postcondition_sql' ? '后置清理SQL' : '前置数据SQL'}执行失败`
          : `步骤${step.step_number}执行失败`,
        step_number: step.step_number === 'sql' ? null : step.step_number,
        action_type: step.action_type === 'precondition_sql' ? '前置数据SQL' : step.action_type === 'postcondition_sql' ? '后置清理SQL' : getActionText(step.action_type || ''),
        element: '',
        description: step.description || '',
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

  // 格式1：套件执行 - 独立的 precondition_sql / postcondition 对象
  if (!Array.isArray(logs)) {
    if (logs.precondition_cases_sql && Array.isArray(logs.precondition_cases_sql)) {
      for (const preCase of logs.precondition_cases_sql) {
        if (preCase.precondition_sql) {
          result.push({
            type: 'precondition_case',
            label: `前置用例「${preCase.case_name}」- 前置数据SQL`,
            success: preCase.precondition_sql.executed !== false && !preCase.precondition_sql.has_error,
            executed: preCase.precondition_sql.executed !== false,
            original_sql: preCase.precondition_sql.original_sql || '',
            resolved_sql: preCase.precondition_sql.resolved_sql || '',
            total_affected: preCase.precondition_sql.total_affected || 0,
            details: preCase.precondition_sql.details || [],
            error: preCase.precondition_sql.error || null
          })
        }
      }
    }
    if (logs.precondition_sql) {
      const pre = logs.precondition_sql
      result.push({
        type: 'precondition',
        label: '前置数据SQL',
        success: pre.executed !== false && !pre.has_error,
        executed: pre.executed !== false,
        original_sql: pre.original_sql || '',
        resolved_sql: pre.resolved_sql || '',
        total_affected: pre.total_affected || 0,
        details: pre.details || [],
        error: pre.error || null
      })
    }
    if (logs.postcondition) {
      const post = logs.postcondition
      result.push({
        type: 'postcondition',
        label: '后置清理SQL',
        success: post.executed !== false,
        executed: post.executed !== false,
        original_sql: post.original_sql || '',
        resolved_sql: post.resolved_sql || '',
        total_affected: post.total_affected || 0,
        details: post.details || [],
        error: post.error || null
      })
    }
  }

  // 格式2：单用例执行 - SQL信息嵌入在 steps 数组中
  const steps = Array.isArray(logs) ? logs : (logs.steps || [])
  for (const step of steps) {
    if (step.step_number === 'sql' && (step.original_sql || step.resolved_sql || step.details)) {
      result.push({
        type: step.action_type === 'postcondition_sql' ? 'postcondition' : 'precondition',
        label: step.description || (step.action_type === 'postcondition_sql' ? '后置清理SQL' : '前置数据SQL'),
        success: step.success,
        executed: true,
        original_sql: step.original_sql || '',
        resolved_sql: step.resolved_sql || '',
        total_affected: step.total_affected || 0,
        details: step.details || [],
        error: step.error || null
      })
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

// 监听编辑对话框打开
watch(showEditDialog, (val) => {
  if (val) openEditDialog()
})

// 弹窗关闭时停止轮询
watch(showRecordsDialog, (val) => {
  if (!val) stopRecordsPoll()
})

onBeforeUnmount(() => {
  stopRecordsPoll()
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
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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

// ==================== 执行记录弹窗 ====================
.record-header {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  width: 100%;

  .record-status {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;

    &.status-success { background: #ecfdf5; color: #059669; }
    &.status-running { background: #fef3c7; color: #d97706; }
    &.status-failed, &.status-aborted { background: #fef2f2; color: #dc2626; }
    &.status-pending { background: #f3f4f6; color: #9ca3af; }
  }

  .record-time { color: #606266; }
  .record-duration { color: #909399; font-size: 12px; }

  .record-stats {
    display: flex;
    gap: 8px;
    font-size: 12px;
    .stat-passed { color: #059669; }
    .stat-failed { color: #dc2626; }
    .stat-skipped { color: #d97706; }
  }

  .record-executor { color: #909399; font-size: 12px; margin-left: auto; }
}

.record-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.record-item-block {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  overflow: hidden;
}

.record-item-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 13px;
  border-bottom: 1px solid #f5f7fa;

  &:last-child { border-bottom: none; }

  &.is-suite {
    cursor: pointer;
    user-select: none;
    background: #fafbfc;
    &:hover { background: #f0f2f5; }
  }

  &.is-sub {
    padding-left: 24px;
    background: #fafbfc;
  }

  .record-item-name {
    color: #303133;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 500;
  }

  .record-item-time {
    color: #909399;
    font-size: 12px;
    min-width: 50px;
    text-align: right;
  }
}

.suite-expand-icon {
  margin-left: auto;
  transition: transform 0.2s;
  color: #909399;
  flex-shrink: 0;

  &.is-expanded { transform: rotate(90deg); }
}

.record-suite-cases {
  border-top: 1px solid #ebeef5;
}

.status-tag {
  font-size: 12px;
  &.status-passed { color: #059669; }
  &.status-failed { color: #dc2626; }
  &.status-running { color: #d97706; }
  &.status-pending, &.status-skipped { color: #d97706; }
  &.status-error { color: #dc2626; }
}

// ==================== 用例执行详情弹窗 ====================
.history-detail-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
.history-detail-header { flex-shrink: 0; margin-bottom: 16px; }
.history-detail-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.history-detail-tabs :deep(.el-tabs) { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.history-detail-tabs :deep(.el-tabs__header) { flex-shrink: 0; margin-bottom: 8px; }
.history-detail-tabs :deep(.el-tabs__content) { flex: 1; min-height: 0; overflow: hidden; }
.history-detail-tabs :deep(.el-tab-pane) { height: 100%; }
.history-detail-scroll { height: 100%; overflow-y: auto; padding-right: 8px; }

.log-item {
  margin-bottom: 8px;
  padding: 8px 10px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 13px;

  .log-header { display: flex; align-items: center; gap: 8px; }
  .log-action { color: #606266; font-weight: 500; }
  .log-desc { color: #909399; }
  .log-value { color: var(--brand-600, #409eff); font-size: 12px; font-weight: 500; background: var(--brand-50, #ecf5ff); padding: 1px 6px; border-radius: 3px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  .log-error {
    margin-top: 6px;
    padding: 6px 8px;
    background: #fef2f2;
    border-radius: 4px;
    .error-message { margin: 0; font-size: 12px; color: #dc2626; white-space: pre-wrap; word-break: break-all; }
  }
}

// SQL执行
.sql-exec-item { margin-bottom: 12px; padding: 12px; background: #f8f9fa; border-radius: 6px; }
.sql-exec-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.sql-affected { font-size: 12px; color: #909399; }
.sql-exec-error { margin-bottom: 8px; }
.sql-block { margin-bottom: 8px; }
.sql-block-label { font-size: 12px; color: #909399; margin-bottom: 4px; }
.sql-code { margin: 0; padding: 8px; background: #2d2d2d; color: #e5e5e5; border-radius: 4px; font-size: 12px; white-space: pre-wrap; word-break: break-all; }
.sql-resolved { border: 1px dashed #67c23a; }
.sql-details-label { font-size: 12px; color: #909399; margin-bottom: 4px; }
.sql-detail-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.sql-detail-status { font-weight: 600; &.ok { color: #059669; } &.fail { color: #dc2626; } }
.sql-detail-code { margin: 0; font-size: 12px; background: #2d2d2d; color: #e5e5e5; padding: 4px 8px; border-radius: 3px; flex: 1; white-space: pre-wrap; word-break: break-all; }
.sql-detail-affected { font-size: 12px; color: #909399; }
.sql-detail-error { font-size: 12px; color: #dc2626; }

// 错误信息
.errors-container { display: flex; flex-direction: column; gap: 12px; }
.error-item {
  background: #fff;
  border: 2px solid #dc2626;
  border-radius: 8px;
  padding: 16px;

  .error-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #f3f4f6; gap: 8px;
    .el-tag { font-size: 14px; padding: 8px 12px; font-weight: 600; }
  }
  .error-tag-inner { display: inline-flex; align-items: center; gap: 6px; }
  .error-step { background: #fef2f2; color: #dc2626; padding: 4px 12px; border-radius: 4px; font-weight: 600; font-size: 13px; }
  .error-meta { background: #f9fafb; padding: 12px; border-radius: 8px; margin-bottom: 12px; }
  .meta-item { display: flex; align-items: flex-start; margin-bottom: 8px; &:last-child { margin-bottom: 0; } }
  .meta-label { font-weight: 600; color: #6b7280; min-width: 80px; margin-right: 8px; font-size: 13px; }
  .meta-value { color: #111827; flex: 1; font-size: 13px; word-break: break-word; }
  .error-details { background: #2d2d2d; border-radius: 8px; overflow: hidden; }
  .details-header { color: #e5e5e5; font-size: 13px; padding: 12px 16px 6px; font-weight: 600; }
  .details-content { margin: 0; padding: 0 16px 12px; color: #f87171; font-size: 12px; white-space: pre-wrap; word-break: break-all; font-family: 'Cascadia Code', Consolas, monospace; }
}

// 截图
.history-detail-screenshots { padding: 8px 0; }
</style>
