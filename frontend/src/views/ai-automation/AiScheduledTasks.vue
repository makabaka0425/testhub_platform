<template>
  <div class="page-container">
    <div class="page-titlebar">
      <h1 class="page-title">{{ $t('aiAutomation.scheduledTask.title') }}</h1>
      <div class="titlebar-actions">
        <el-button type="primary" size="small" @click="handleCreateClick">
          <el-icon><Plus /></el-icon>
          {{ $t('aiAutomation.scheduledTask.newTask') }}
        </el-button>
      </div>
    </div>

    <div class="workspace">
      <div class="list-column">
        <!-- 搜索区域卡片 -->
        <div class="filter-bar">
          <el-form :inline="true">
            <el-form-item :label="$t('aiAutomation.scheduledTask.taskName')">
              <el-input
                v-model="filters.search"
                :placeholder="$t('aiAutomation.scheduledTask.taskName')"
                clearable
                style="width: 180px"
                @keyup.enter="loadTasks"
              >
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item :label="$t('aiAutomation.scheduledTask.triggerType')">
              <el-select v-model="filters.trigger_type" :placeholder="$t('aiAutomation.common.all')" clearable style="width: 130px">
                <el-option :label="$t('aiAutomation.scheduledTask.triggerTypes.cron')" value="CRON" />
                <el-option :label="$t('aiAutomation.scheduledTask.triggerTypes.interval')" value="INTERVAL" />
                <el-option :label="$t('aiAutomation.scheduledTask.triggerTypes.once')" value="ONCE" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('aiAutomation.scheduledTask.status')">
              <el-select v-model="filters.status" :placeholder="$t('aiAutomation.common.all')" clearable style="width: 130px">
                <el-option :label="$t('aiAutomation.scheduledTask.statusTypes.active')" value="ACTIVE" />
                <el-option :label="$t('aiAutomation.scheduledTask.statusTypes.paused')" value="PAUSED" />
                <el-option :label="$t('aiAutomation.scheduledTask.statusTypes.completed')" value="COMPLETED" />
                <el-option :label="$t('aiAutomation.scheduledTask.statusTypes.failed')" value="FAILED" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadTasks">{{ $t('aiAutomation.common.search') }}</el-button>
              <el-button @click="resetFilters">{{ $t('aiAutomation.common.reset') }}</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 任务列表面板 -->
        <section class="panel list-panel">
          <div class="panel__header">
            <span class="panel__title">{{ $t('aiAutomation.scheduledTask.taskList') }}</span>
          </div>

          <div class="panel__body scheduled-task-table-wrapper">
            <el-table :data="tasks" v-loading="loading" height="100%">
              <el-table-column type="index" label="序号" width="50" align="center" />
              <el-table-column prop="name" :label="$t('aiAutomation.scheduledTask.taskName')" min-width="200" />
              <el-table-column prop="midscene_case_name" :label="$t('aiAutomation.scheduledTask.midsceneCase')" width="180">
                <template #default="scope">
                  {{ scope.row.midscene_case_name || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="trigger_type" :label="$t('aiAutomation.scheduledTask.triggerType')" width="120">
                <template #default="scope">
                  <el-tag>{{ getTriggerTypeText(scope.row.trigger_type) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" :label="$t('aiAutomation.scheduledTask.status')" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.status === 'ACTIVE' ? 'success' : scope.row.status === 'PAUSED' ? 'warning' : 'info'">
                    {{ getStatusText(scope.row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="next_run_time" :label="$t('aiAutomation.scheduledTask.nextRunTime')" width="180">
                <template #default="scope">
                  {{ formatDateTime(scope.row.next_run_time) }}
                </template>
              </el-table-column>
              <el-table-column prop="last_run_time" :label="$t('aiAutomation.scheduledTask.lastRunTime')" width="180">
                <template #default="scope">
                  {{ formatDateTime(scope.row.last_run_time) }}
                </template>
              </el-table-column>
              <el-table-column prop="total_runs" :label="$t('aiAutomation.scheduledTask.totalRuns')" width="90" />
              <el-table-column :label="$t('aiAutomation.common.operation')" width="180" fixed="right">
                <template #default="{ row }">
                  <ActionCell :actions="getTaskActions(row)" :row="row" :max-visible="3" />
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="pagination.current"
              v-model:page-size="pagination.size"
              :total="pagination.total"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="loadTasks"
              @current-change="loadTasks"
            />
          </div>
        </section>
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingTask ? $t('aiAutomation.scheduledTask.editTask') : $t('aiAutomation.scheduledTask.createTask')"
      width="720px"
      :close-on-click-modal="false"
      @close="resetTaskForm"
    >
      <el-form :model="taskForm" label-width="120px">
        <el-form-item :label="$t('aiAutomation.scheduledTask.taskName')" required>
          <el-input v-model="taskForm.name" :placeholder="$t('aiAutomation.scheduledTask.taskNamePlaceholder')" />
        </el-form-item>

        <el-form-item :label="$t('aiAutomation.scheduledTask.taskDesc')">
          <el-input v-model="taskForm.description" type="textarea" :placeholder="$t('aiAutomation.scheduledTask.taskDescPlaceholder')" />
        </el-form-item>

        <el-form-item :label="$t('aiAutomation.scheduledTask.relatedProject')" required>
          <el-select v-model="taskForm.project" :placeholder="$t('aiAutomation.scheduledTask.selectProject')" @change="onProjectChange">
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('aiAutomation.scheduledTask.midsceneCase')" required>
          <el-select v-model="taskForm.midscene_case" :placeholder="$t('aiAutomation.scheduledTask.selectCase')" filterable :disabled="!taskForm.project">
            <el-option
              v-for="c in midsceneCases"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('aiAutomation.scheduledTask.triggerType')" required>
          <el-radio-group v-model="taskForm.trigger_type">
            <el-radio value="CRON">{{ $t('aiAutomation.scheduledTask.triggerTypes.cron') }}</el-radio>
            <el-radio value="INTERVAL">{{ $t('aiAutomation.scheduledTask.triggerTypes.interval') }}</el-radio>
            <el-radio value="ONCE">{{ $t('aiAutomation.scheduledTask.triggerTypes.once') }}</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="taskForm.trigger_type === 'CRON'" :label="$t('aiAutomation.scheduledTask.cronExpression')" required>
          <el-input v-model="taskForm.cron_expression" :placeholder="$t('aiAutomation.scheduledTask.cronPlaceholder')" />
          <div class="cron-help">
            <el-tooltip raw-content placement="top">
              <template #content>
                <div style="line-height: 1.6; text-align: left;">
                  <div>{{ $t('aiAutomation.scheduledTask.cronHelp.format') }}</div>
                  <div>{{ $t('aiAutomation.scheduledTask.cronHelp.minute') }}</div>
                  <div>{{ $t('aiAutomation.scheduledTask.cronHelp.hour') }}</div>
                  <div>{{ $t('aiAutomation.scheduledTask.cronHelp.day') }}</div>
                  <div>{{ $t('aiAutomation.scheduledTask.cronHelp.month') }}</div>
                  <div>{{ $t('aiAutomation.scheduledTask.cronHelp.week') }}</div>
                  <div style="margin-top: 8px;">{{ $t('aiAutomation.scheduledTask.cronHelp.examples') }}</div>
                  <div>{{ $t('aiAutomation.scheduledTask.cronHelp.everyDay') }}</div>
                  <div>{{ $t('aiAutomation.scheduledTask.cronHelp.everyHour') }}</div>
                  <div>{{ $t('aiAutomation.scheduledTask.cronHelp.everyMonday') }}</div>
                  <div>{{ $t('aiAutomation.scheduledTask.cronHelp.everyMonth') }}</div>
                </div>
              </template>
              <span style="cursor: pointer; color: #409EFF;">{{ $t('aiAutomation.scheduledTask.cronHelpLink') }}</span>
            </el-tooltip>
          </div>
        </el-form-item>

        <el-form-item v-if="taskForm.trigger_type === 'INTERVAL'" :label="$t('aiAutomation.scheduledTask.intervalTime')" required>
          <el-input-number v-model="taskForm.interval_seconds" :min="60" :step="60" />
          <span class="unit">{{ $t('aiAutomation.scheduledTask.intervalUnit') }}</span>
        </el-form-item>

        <el-form-item v-if="taskForm.trigger_type === 'ONCE'" :label="$t('aiAutomation.scheduledTask.executeTime')" required>
          <el-date-picker
            v-model="taskForm.execute_at"
            type="datetime"
            :placeholder="$t('aiAutomation.scheduledTask.selectExecuteTime')"
          />
        </el-form-item>

        <el-form-item :label="$t('aiAutomation.scheduledTask.notificationSettings')">
          <el-checkbox v-model="taskForm.notify_on_success">{{ $t('aiAutomation.scheduledTask.notifyOnSuccess') }}</el-checkbox>
          <el-checkbox v-model="taskForm.notify_on_failure">{{ $t('aiAutomation.scheduledTask.notifyOnFailure') }}</el-checkbox>
        </el-form-item>

        <el-form-item v-if="taskForm.notify_on_success || taskForm.notify_on_failure" :label="$t('aiAutomation.scheduledTask.notificationType')">
          <el-select v-model="taskForm.notification_type" :placeholder="$t('aiAutomation.scheduledTask.selectNotificationType')">
            <el-option :label="$t('aiAutomation.scheduledTask.notificationTypes.email')" value="email" />
            <el-option :label="$t('aiAutomation.scheduledTask.notificationTypes.webhook')" value="webhook" />
            <el-option :label="$t('aiAutomation.scheduledTask.notificationTypes.both')" value="both" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="(taskForm.notify_on_success || taskForm.notify_on_failure) && (taskForm.notification_type === 'email' || taskForm.notification_type === 'both')" :label="$t('aiAutomation.scheduledTask.notifyEmails')">
          <el-select
            v-model="taskForm.notify_emails"
            multiple
            filterable
            :placeholder="$t('aiAutomation.scheduledTask.selectNotifyEmails')"
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.display_name"
              :value="user.email"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">{{ $t('aiAutomation.common.cancel') }}</el-button>
        <el-button type="primary" @click="submitTaskForm" :loading="submitting">
          {{ editingTask ? t('aiAutomation.scheduledTask.editTask') : t('aiAutomation.scheduledTask.createTask') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import ActionCell from '@/components/ActionCell.vue'
import {
  getAiScheduledTasks,
  createAiScheduledTask,
  updateAiScheduledTask,
  deleteAiScheduledTask,
  runAiScheduledTask,
  pauseAiScheduledTask,
  resumeAiScheduledTask,
  getAiProjects,
  getMidsceneCases,
  getAiUsers
} from '@/api/ui_automation.js'

const { t, locale } = useI18n()

// 数据状态
const tasks = ref([])
const projects = ref([])
const midsceneCases = ref([])
const users = ref([])
const loading = ref(false)
const submitting = ref(false)
const showCreateDialog = ref(false)
const editingTask = ref(null)

// 筛选条件
const filters = reactive({
  search: '',
  trigger_type: '',
  status: ''
})

// 分页配置
const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
})

// 表单数据
const taskForm = reactive({
  name: '',
  description: '',
  project: '',
  midscene_case: '',
  trigger_type: 'CRON',
  cron_expression: '0 0 * * *',
  interval_seconds: 3600,
  execute_at: '',
  notify_on_success: false,
  notify_on_failure: false,
  notification_type: '',
  notify_emails: []
})

// 文本转换
const getTriggerTypeText = (type) => {
  const typeMap = {
    'CRON': t('aiAutomation.scheduledTask.triggerTypes.cronShort'),
    'INTERVAL': t('aiAutomation.scheduledTask.triggerTypes.intervalShort'),
    'ONCE': t('aiAutomation.scheduledTask.triggerTypes.onceShort')
  }
  return typeMap[type] || type
}

const getStatusText = (status) => {
  const statusMap = {
    'ACTIVE': t('aiAutomation.scheduledTask.statusTypes.active'),
    'PAUSED': t('aiAutomation.scheduledTask.statusTypes.paused'),
    'COMPLETED': t('aiAutomation.scheduledTask.statusTypes.completedShort'),
    'FAILED': t('aiAutomation.scheduledTask.statusTypes.failed')
  }
  return statusMap[status] || status
}

// 操作列 actions
const getTaskActions = (row) => [
  { key: 'run', label: t('aiAutomation.scheduledTask.runNow'), loading: row.running, onClick: (r) => runTaskNow(r) },
  { key: 'edit', label: t('aiAutomation.scheduledTask.actions.edit'), onClick: (r) => handleTaskAction('edit', r) },
  { key: 'pause', label: t('aiAutomation.scheduledTask.actions.pause'), hidden: row.status !== 'ACTIVE', onClick: (r) => handleTaskAction('pause', r) },
  { key: 'resume', label: t('aiAutomation.scheduledTask.actions.resume'), hidden: row.status !== 'PAUSED', onClick: (r) => handleTaskAction('resume', r) },
  { key: 'delete', label: t('aiAutomation.scheduledTask.actions.delete'), danger: true, divided: true, onClick: (r) => handleTaskAction('delete', r) }
]

onMounted(() => {
  loadTasks()
  loadProjects()
  loadUsers()
})

// 加载任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.size,
      ...filters
    }
    const response = await getAiScheduledTasks(params)
    tasks.value = response.data.results
    pagination.total = response.data.count
  } catch (error) {
    ElMessage.error(t('aiAutomation.scheduledTask.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

// 加载项目列表
const loadProjects = async () => {
  try {
    const response = await getAiProjects()
    projects.value = response.data.results
  } catch (error) {
    console.error('Load projects failed:', error)
  }
}

// 加载用户列表
const loadUsers = async () => {
  try {
    const response = await getAiUsers()
    const usersData = response.data.results || response.data
    users.value = usersData.map(user => ({
      ...user,
      display_name: user.first_name ? `${user.first_name}（${user.email}）` : `${user.username}（${user.email}）`
    }))
  } catch (error) {
    console.error('Load users failed:', error)
  }
}

// 项目变化时加载对应的 Midscene 用例
const onProjectChange = async (projectId) => {
  taskForm.midscene_case = ''
  if (!projectId) {
    midsceneCases.value = []
    return
  }
  try {
    const response = await getMidsceneCases({ project: projectId, page_size: 200 })
    midsceneCases.value = response.data.results || response.data
  } catch (error) {
    console.error('Load midscene cases failed:', error)
    midsceneCases.value = []
  }
}

// 新建按钮点击
const handleCreateClick = () => {
  editingTask.value = null
  resetTaskForm()
  showCreateDialog.value = true
}

// 重置表单
const resetTaskForm = () => {
  Object.assign(taskForm, {
    name: '',
    description: '',
    project: '',
    midscene_case: '',
    trigger_type: 'CRON',
    cron_expression: '0 0 * * *',
    interval_seconds: 3600,
    execute_at: '',
    notify_on_success: false,
    notify_on_failure: false,
    notification_type: '',
    notify_emails: []
  })
}

// 重置筛选
const resetFilters = () => {
  Object.assign(filters, {
    search: '',
    trigger_type: '',
    status: ''
  })
  loadTasks()
}

// 提交任务表单
const submitTaskForm = async () => {
  submitting.value = true
  try {
    const submitData = {
      name: taskForm.name,
      description: taskForm.description,
      project: taskForm.project,
      task_type: 'MIDSCENE_CASE',
      midscene_case: taskForm.midscene_case,
      trigger_type: taskForm.trigger_type,
      notify_on_success: taskForm.notify_on_success,
      notify_on_failure: taskForm.notify_on_failure
    }

    if (taskForm.notify_on_success || taskForm.notify_on_failure) {
      if (taskForm.notification_type) {
        submitData.notification_type = taskForm.notification_type
      }
      if (taskForm.notify_emails && taskForm.notify_emails.length > 0) {
        submitData.notify_emails = taskForm.notify_emails
      }
    }

    if (taskForm.trigger_type === 'CRON') {
      submitData.cron_expression = taskForm.cron_expression
    } else if (taskForm.trigger_type === 'INTERVAL') {
      submitData.interval_seconds = taskForm.interval_seconds
    } else if (taskForm.trigger_type === 'ONCE') {
      submitData.execute_at = taskForm.execute_at
    }

    if (editingTask.value) {
      await updateAiScheduledTask(editingTask.value.id, submitData)
      ElMessage.success(t('aiAutomation.scheduledTask.messages.updateSuccess'))
    } else {
      await createAiScheduledTask(submitData)
      ElMessage.success(t('aiAutomation.scheduledTask.messages.createSuccess'))
    }
    showCreateDialog.value = false
    loadTasks()
  } catch (error) {
    console.error('Task operation failed:', error)
    ElMessage.error(error.response?.data?.error ||
                   error.response?.data?.detail ||
                   (editingTask.value ? t('aiAutomation.scheduledTask.messages.updateFailed') : t('aiAutomation.scheduledTask.messages.createFailed')))
  } finally {
    submitting.value = false
  }
}

// 立即执行任务
const runTaskNow = async (task) => {
  try {
    task.running = true
    await runAiScheduledTask(task.id)
    ElMessage.success(t('aiAutomation.scheduledTask.messages.runSuccess'))
    setTimeout(() => {
      loadTasks()
    }, 2000)
  } catch (error) {
    ElMessage.error(error.response?.data?.error || t('aiAutomation.scheduledTask.messages.runFailed'))
  } finally {
    task.running = false
  }
}

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  const localeStr = locale.value === 'en' ? 'en-US' : 'zh-CN'
  return date.toLocaleString(localeStr, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).replace(/\//g, '-')
}

// 处理任务操作
const handleTaskAction = (command, task) => {
  switch (command) {
    case 'pause':
      pauseTask(task)
      break
    case 'resume':
      resumeTask(task)
      break
    case 'edit':
      editTask(task)
      break
    case 'delete':
      deleteTask(task)
      break
  }
}

// 编辑任务
const editTask = async (task) => {
  editingTask.value = task

  // 先加载项目对应的用例列表
  if (task.project) {
    await onProjectChange(task.project)
  }

  Object.assign(taskForm, {
    name: task.name,
    description: task.description,
    project: task.project,
    midscene_case: task.midscene_case || '',
    trigger_type: task.trigger_type,
    cron_expression: task.cron_expression,
    interval_seconds: task.interval_seconds,
    execute_at: task.execute_at,
    notify_on_success: task.notify_on_success || false,
    notify_on_failure: task.notify_on_failure || false,
    notification_type: task.notification_type || '',
    notify_emails: task.notify_emails || []
  })

  showCreateDialog.value = true
}

// 暂停任务
const pauseTask = async (task) => {
  try {
    await pauseAiScheduledTask(task.id)
    ElMessage.success(t('aiAutomation.scheduledTask.messages.pauseSuccess'))
    loadTasks()
  } catch (error) {
    ElMessage.error(t('aiAutomation.scheduledTask.messages.pauseFailed'))
  }
}

// 恢复任务
const resumeTask = async (task) => {
  try {
    await resumeAiScheduledTask(task.id)
    ElMessage.success(t('aiAutomation.scheduledTask.messages.resumeSuccess'))
    loadTasks()
  } catch (error) {
    ElMessage.error(t('aiAutomation.scheduledTask.messages.resumeFailed'))
  }
}

// 删除任务
const deleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      t('aiAutomation.scheduledTask.messages.deleteConfirm'),
      t('aiAutomation.scheduledTask.messages.deleteConfirmTitle'),
      { confirmButtonText: t('aiAutomation.common.confirm'), cancelButtonText: t('aiAutomation.common.cancel'), type: 'warning' }
    )
    await deleteAiScheduledTask(task.id)
    ElMessage.success(t('aiAutomation.scheduledTask.messages.deleteSuccess'))
    loadTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('aiAutomation.scheduledTask.messages.deleteFailed'))
    }
  }
}
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

.scheduled-task-table-wrapper {
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

.list-panel :deep(.el-table .el-table__body tr:hover > td.el-table__cell) {
  background: var(--gray-50) !important;
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

.cron-help {
  margin-top: 8px;
  font-size: 12px;
}

.unit {
  margin-left: 8px;
  color: #606266;
}
</style>
