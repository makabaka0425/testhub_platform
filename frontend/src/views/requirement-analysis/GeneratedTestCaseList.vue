<template>
  <div class="page-container">
    <!-- 顶部标题栏 -->
    <div class="page-titlebar">
      <h1 class="page-title">{{ $t('generatedTestCases.title') }}</h1>
      <div class="titlebar-actions">
        <el-select
          v-model="selectedProjectId"
          :placeholder="$t('generatedTestCases.selectProject')"
          class="titlebar-select"
          clearable
          @change="onProjectChange"
        >
          <el-option v-for="p in projectList" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-button
          v-if="selectedTasks.length > 0"
          type="danger"
          plain
          size="small"
          @click="batchDeleteTasks"
          :loading="isDeleting"
        >
          {{ $t('generatedTestCases.batchDelete', { count: selectedTasks.length }) }}
        </el-button>
        <el-button size="small" @click="loadTasks" :loading="isLoading">
          {{ $t('generatedTestCases.refresh') }}
        </el-button>
      </div>
    </div>

    <!-- 筛选条件 -->
    <div class="card-container">
      <div class="filter-bar">
        <el-select
          v-model="selectedStatus"
          :placeholder="$t('generatedTestCases.allStatus')"
          clearable
          style="width: 180px;"
          @change="onStatusChange"
        >
          <el-option
            v-for="s in statusOptions"
            :key="s.value"
            :label="s.label"
            :value="s.value"
          />
        </el-select>
      </div>

      <!-- 列表 -->
      <div class="table-scroll-area">
        <el-table
          :data="tasks"
          v-loading="isLoading"
          @selection-change="onSelectionChange"
          style="width: 100%"
          height="100%"
        >
          <el-table-column type="selection" width="45" />
          <el-table-column type="index" :label="$t('generatedTestCases.serialNumber')" width="60" :index="indexMethod" />
          <el-table-column prop="task_id" :label="$t('generatedTestCases.taskId')" min-width="160" show-overflow-tooltip />
          <el-table-column prop="title" :label="$t('generatedTestCases.requirement')" min-width="240" show-overflow-tooltip />
          <el-table-column :label="$t('generatedTestCases.status')" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small" effect="light">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="$t('generatedTestCases.caseCount')" width="100" align="center">
            <template #default="{ row }">
              <span class="case-count">{{ getTestCaseCount(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('generatedTestCases.generationTime')" width="170" align="center">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column :label="$t('generatedTestCases.actions')" width="180" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="viewTaskDetail(row)">
                {{ $t('generatedTestCases.viewDetail') }}
              </el-button>
              <el-button v-if="row.status === 'completed'" type="primary" link size="small" @click="batchAdoptTask(row)">
                {{ $t('generatedTestCases.batchAdopt') }}
              </el-button>
              <el-button v-if="row.status === 'completed'" type="danger" link size="small" @click="batchDiscardTask(row)">
                {{ $t('generatedTestCases.batchDiscard') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="onPageSizeChange"
          @current-change="onPageChange"
        />
      </div>
    </div>

    <!-- 采纳用例编辑弹框 -->
    <el-dialog v-model="showAdoptModal" :title="$t('generatedTestCases.adoptModalTitle')" width="680px" :close-on-click-modal="false">
      <el-form :model="adoptForm" label-width="100px" label-position="left">
        <el-form-item :label="$t('generatedTestCases.caseTitle')">
          <el-input v-model="adoptForm.title" />
        </el-form-item>
        <el-form-item :label="$t('generatedTestCases.caseDescription')">
          <el-input v-model="adoptForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="$t('generatedTestCases.belongsToProject')" required>
          <el-select v-model="adoptForm.project_id" @change="onAdoptProjectChange" style="width: 100%;">
            <el-option value="" :label="$t('generatedTestCases.selectProject')" disabled />
            <el-option v-for="project in projectList" :key="project.id" :label="project.name" :value="project.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('generatedTestCases.relatedVersion')" required>
          <el-select v-model="adoptForm.version_id" style="width: 100%;">
            <el-option value="" :label="$t('generatedTestCases.selectVersion')" disabled />
            <el-option v-for="ver in availableVersions" :key="ver.id" :label="ver.name + (ver.is_baseline ? $t('generatedTestCases.baseline') : '')" :value="ver.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('generatedTestCases.priority')">
          <el-select v-model="adoptForm.priority" style="width: 100%;">
            <el-option value="low" :label="$t('generatedTestCases.priorityLow')" />
            <el-option value="medium" :label="$t('generatedTestCases.priorityMedium')" />
            <el-option value="high" :label="$t('generatedTestCases.priorityHigh')" />
            <el-option value="critical" :label="$t('generatedTestCases.priorityCritical')" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('generatedTestCases.testType')">
          <el-select v-model="adoptForm.test_type" style="width: 100%;">
            <el-option value="functional" :label="$t('generatedTestCases.testTypeFunctional')" />
            <el-option value="integration" :label="$t('generatedTestCases.testTypeIntegration')" />
            <el-option value="api" :label="$t('generatedTestCases.testTypeAPI')" />
            <el-option value="ui" :label="$t('generatedTestCases.testTypeUI')" />
            <el-option value="performance" :label="$t('generatedTestCases.testTypePerformance')" />
            <el-option value="security" :label="$t('generatedTestCases.testTypeSecurity')" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('generatedTestCases.preconditions')">
          <el-input v-model="adoptForm.preconditions" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item :label="$t('generatedTestCases.operationSteps')">
          <el-input v-model="adoptForm.steps" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item :label="$t('generatedTestCases.expectedResult')">
          <el-input v-model="adoptForm.expected_result" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdoptModal = false">{{ $t('generatedTestCases.cancel') }}</el-button>
        <el-button type="primary" @click="confirmAdopt" :loading="isAdopting">{{ $t('generatedTestCases.confirmAdopt') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

export default {
  name: 'GeneratedTestCaseList',
  setup() {
    const { t } = useI18n()
    const router = useRouter()

    // === 数据 ===
    const isLoading = ref(false)
    const tasks = ref([])
    const selectedStatus = ref('')
    const selectedProjectId = ref('')
    const projectList = ref([])
    const projectVersions = ref([])
    const allVersions = ref([])
    const selectedTasks = ref([])
    const isDeleting = ref(false)
    const showAdoptModal = ref(false)
    const isAdopting = ref(false)
    const currentAdoptingTask = ref(null)

    const pagination = reactive({
      currentPage: 1,
      pageSize: 10,
      total: 0
    })

    const adoptForm = reactive({
      title: '',
      description: '',
      project_id: null,
      priority: 'low',
      test_type: 'functional',
      status: 'draft',
      preconditions: '',
      steps: '',
      expected_result: '',
      version_id: null
    })

    const availableVersions = computed(() => {
      if (adoptForm.project_id) {
        return projectVersions.value
      }
      return allVersions.value
    })

    // === 状态选项（完整覆盖后端所有可能值）===
    const statusOptions = computed(() => [
      { value: 'pending', label: t('generatedTestCases.statusPending') },
      { value: 'generating', label: t('generatedTestCases.statusGenerating') },
      { value: 'reviewing', label: t('generatedTestCases.statusReviewing') },
      { value: 'completed', label: t('generatedTestCases.statusCompleted') },
      { value: 'failed', label: t('generatedTestCases.statusFailed') },
    ])

    // === 状态中文映射 ===
    const STATUS_MAP = {
      'pending': 'generatedTestCases.statusPending',
      'generating': 'generatedTestCases.statusGenerating',
      'reviewing': 'generatedTestCases.statusReviewing',
      'revising': 'generatedTestCases.statusReviewing', // 改进中复用评审中
      'completed': 'generatedTestCases.statusCompleted',
      'failed': 'generatedTestCases.statusFailed',
      'cancelled': 'generatedTestCases.statusFailed', // 已取消复用失败
      'reviewed': 'generatedTestCases.statusReviewing', // 已评审
      'review_failed': 'generatedTestCases.statusFailed', // 评审失败
    }

    const getStatusText = (status) => {
      const key = STATUS_MAP[status]
      return key ? t(key) : status
    }

    // === 状态标签类型 ===
    const getStatusTagType = (status) => {
      const map = {
        'pending': 'info',
        'generating': '',
        'reviewing': '',
        'revising': '',
        'completed': 'success',
        'failed': 'danger',
        'cancelled': 'info',
        'reviewed': 'success',
        'review_failed': 'danger',
      }
      return map[status] || 'info'
    }

    // === 加载任务列表 ===
    const loadTasks = async () => {
      isLoading.value = true
      try {
        const params = new URLSearchParams()
        params.append('page', String(pagination.currentPage))
        params.append('page_size', String(pagination.pageSize))
        if (selectedStatus.value) {
          params.append('status', selectedStatus.value)
        }
        if (selectedProjectId.value) {
          params.append('project_id', selectedProjectId.value)
        }

        const response = await api.get(`/requirement-analysis/testcase-generation/?${params.toString()}`)
        if (response.data.results) {
          tasks.value = response.data.results
          pagination.total = response.data.count || 0
        } else {
          tasks.value = response.data || []
          pagination.total = tasks.value.length
        }
      } catch (error) {
        console.error('加载任务失败:', error)
        tasks.value = []
        pagination.total = 0
      } finally {
        isLoading.value = false
      }
    }

    // === 获取项目列表 ===
    const fetchProjects = async () => {
      try {
        const response = await api.get('/projects/list/')
        projectList.value = response.data.results || []
        // 恢复上次选择的项目
        const saved = localStorage.getItem('lastProjectId_generated')
        if (saved && projectList.value.some(p => p.id === parseInt(saved))) {
          selectedProjectId.value = parseInt(saved)
        }
      } catch (error) {
        console.error('获取项目列表失败:', error)
      }
    }

    // === 获取版本列表 ===
    const fetchAllVersions = async () => {
      try {
        const response = await api.get('/versions/')
        allVersions.value = response.data.results || response.data || []
      } catch (error) {
        console.error('获取版本列表失败:', error)
        allVersions.value = []
      }
    }

    const fetchProjectVersions = async (projectId) => {
      if (!projectId) {
        projectVersions.value = []
        return
      }
      try {
        const response = await api.get(`/versions/projects/${projectId}/versions/`)
        projectVersions.value = response.data || []
      } catch (error) {
        console.error('获取项目版本失败:', error)
        projectVersions.value = []
      }
    }

    // === 事件处理 ===
    const onProjectChange = () => {
      localStorage.setItem('lastProjectId_generated', selectedProjectId.value || '')
      pagination.currentPage = 1
      loadTasks()
    }

    const onStatusChange = () => {
      pagination.currentPage = 1
      loadTasks()
    }

    const onPageSizeChange = () => {
      pagination.currentPage = 1
      loadTasks()
    }

    const onPageChange = () => {
      loadTasks()
    }

    const onSelectionChange = (selection) => {
      selectedTasks.value = selection.map(s => s.task_id)
    }

    const indexMethod = (index) => {
      return (pagination.currentPage - 1) * pagination.pageSize + index + 1
    }

    // === 操作 ===
    const viewTaskDetail = (task) => {
      if (['pending', 'generating', 'reviewing'].includes(task.status)) {
        ElMessage.info(t('generatedTestCases.generatingWait'))
        return
      }
      // 在新标签页打开任务详情
      const resolved = router.resolve({ name: 'TaskDetail', params: { taskId: task.task_id } })
      window.open(resolved.href, '_blank')
    }

    const batchAdoptTask = async (task) => {
      try {
        await ElMessageBox.confirm(
          t('generatedTestCases.adoptConfirm', { title: task.title }),
          t('generatedTestCases.batchAdopt'),
          { type: 'info' }
        )
        await api.post(`/requirement-analysis/testcase-generation/${task.task_id}/batch_adopt/`)
        ElMessage.success(t('generatedTestCases.adoptSuccess'))
        loadTasks()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('采纳失败:', error)
          ElMessage.error(t('generatedTestCases.adoptFailed') + ': ' + (error.response?.data?.message || error.message))
        }
      }
    }

    const batchDiscardTask = async (task) => {
      try {
        await ElMessageBox.confirm(
          t('generatedTestCases.discardConfirm', { title: task.title }),
          t('generatedTestCases.batchDiscard'),
          { type: 'warning' }
        )
        await api.post(`/requirement-analysis/testcase-generation/${task.task_id}/batch_discard/`)
        ElMessage.success(t('generatedTestCases.discardSuccess'))
        loadTasks()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('弃用失败:', error)
          ElMessage.error(t('generatedTestCases.discardFailed') + ': ' + (error.response?.data?.message || error.message))
        }
      }
    }

    const batchDeleteTasks = async () => {
      if (selectedTasks.value.length === 0) {
        ElMessage.warning(t('generatedTestCases.selectTasksFirst'))
        return
      }
      try {
        await ElMessageBox.confirm(
          t('generatedTestCases.batchDeleteConfirm', { count: selectedTasks.value.length }),
          t('generatedTestCases.delete'),
          { type: 'warning' }
        )
        isDeleting.value = true
        let successCount = 0
        let failCount = 0
        for (const taskId of selectedTasks.value) {
          try {
            await api.delete(`/requirement-analysis/testcase-generation/${taskId}/`)
            successCount++
          } catch (error) {
            console.error(`删除任务 ${taskId} 失败:`, error)
            failCount++
          }
        }
        if (successCount > 0) {
          ElMessage.success(t('generatedTestCases.deleteSuccess', { success: successCount, failed: failCount }))
        } else {
          ElMessage.error(t('generatedTestCases.deleteFailed'))
        }
        selectedTasks.value = []
        loadTasks()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('批量删除失败:', error)
        }
      } finally {
        isDeleting.value = false
      }
    }

    // === 采纳弹框 ===
    const onAdoptProjectChange = async () => {
      if (adoptForm.project_id) {
        await fetchProjectVersions(adoptForm.project_id)
        if (adoptForm.version_id) {
          const versionExists = projectVersions.value.some(v => v.id === adoptForm.version_id)
          if (!versionExists) adoptForm.version_id = null
        }
      } else {
        projectVersions.value = []
      }
    }

    const confirmAdopt = async () => {
      if (!adoptForm.project_id) {
        ElMessage.warning(t('generatedTestCases.selectProjectRequired'))
        return
      }
      if (!adoptForm.version_id) {
        ElMessage.warning(t('generatedTestCases.selectVersionRequired'))
        return
      }
      if (!adoptForm.title.trim()) {
        ElMessage.warning(t('generatedTestCases.enterCaseTitle'))
        return
      }

      isAdopting.value = true
      try {
        const submitData = {
          title: adoptForm.title,
          description: adoptForm.description,
          project_id: adoptForm.project_id,
          priority: adoptForm.priority || 'low',
          test_type: adoptForm.test_type,
          status: adoptForm.status,
          preconditions: adoptForm.preconditions,
          steps: adoptForm.steps,
          expected_result: adoptForm.expected_result,
          version_ids: adoptForm.version_id ? [adoptForm.version_id] : []
        }

        await api.post('/testcases/', submitData)

        // 更新AI生成的用例状态为"已采纳"
        try {
          await api.patch(`/requirement-analysis/test-cases/${currentAdoptingTask.value.id}/`, {
            status: 'adopted'
          })
        } catch (updateError) {
          console.warn('更新状态失败:', updateError)
        }

        ElMessage.success(t('generatedTestCases.adoptModalSuccess'))
        showAdoptModal.value = false
        loadTasks()
      } catch (error) {
        console.error('采纳用例失败:', error)
        ElMessage.error(t('generatedTestCases.adoptCaseFailed'))
      } finally {
        isAdopting.value = false
      }
    }

    // === 辅助方法 ===
    const getTestCaseCount = (task) => {
      if (!task.final_test_cases) return 0
      const lines = task.final_test_cases.split('\n').filter(line => line.trim())
      let tableRows = 0
      let isFirstRow = true
      let isTableFormat = false

      for (const line of lines) {
        if (line.includes('|') && !line.includes('--------')) {
          const cells = line.split('|').map(cell => cell.trim()).filter(cell => cell)
          if (cells.length > 1) {
            if (isFirstRow) {
              isFirstRow = false
              if (line.includes('测试用例编号') || line.includes('ID') || line.includes('用例ID') ||
                  line.includes('场景') || line.includes('步骤')) {
                isTableFormat = true
                continue
              }
            }
            tableRows++
            if (tableRows >= 1) isTableFormat = true
          }
        }
      }

      if (isTableFormat && tableRows > 0) return tableRows

      let caseCount = 0
      for (const line of lines) {
        if (line.includes('测试用例') || line.includes('Test Case') || line.match(/^(\d+\.|测试场景)/)) {
          caseCount++
        }
      }
      return caseCount || 0
    }

    const formatDateTime = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    onMounted(() => {
      fetchProjects()
      fetchAllVersions()
      loadTasks()
    })

    return {
      isLoading, tasks, selectedStatus, selectedProjectId, projectList,
      selectedTasks, isDeleting, showAdoptModal, isAdopting, currentAdoptingTask,
      pagination, adoptForm, availableVersions, statusOptions,
      getStatusText, getStatusTagType,
      loadTasks, onProjectChange, onStatusChange, onPageSizeChange, onPageChange,
      onSelectionChange, indexMethod,
      viewTaskDetail, batchAdoptTask, batchDiscardTask, batchDeleteTasks,
      onAdoptProjectChange, confirmAdopt,
      getTestCaseCount, formatDateTime
    }
  }
}
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

  .page-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0;
  }

  .titlebar-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .titlebar-select {
    width: 180px;
  }
}

.card-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin: 0 20px 20px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.table-scroll-area {
  flex: 1;
  overflow: hidden;
}

.case-count {
  font-weight: 600;
  color: var(--el-color-primary);
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  padding: 12px 20px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
