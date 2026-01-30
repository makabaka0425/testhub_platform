<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">{{ $t('import.title') }}</h1>
      <el-button @click="$router.back()">{{ $t('common.back') }}</el-button>
    </div>

    <div class="card-container">
      <div class="filter-bar">
        <el-row :gutter="20">
          <el-col :span="4">
            <el-select v-model="statusFilter" :placeholder="$t('import.statusFilter')" clearable @change="handleFilter">
              <el-option :label="$t('import.pending')" value="pending" />
              <el-option :label="$t('import.processing')" value="processing" />
              <el-option :label="$t('import.success')" value="success" />
              <el-option :label="$t('import.failed')" value="failed" />
              <el-option :label="$t('import.partialSuccess')" value="partial_success" />
            </el-select>
          </el-col>
        </el-row>
      </div>

      <div class="table-container">
        <el-table
          :data="tasks"
          v-loading="loading"
          style="width: 100%"
          @row-click="showTaskDetail"
          class="clickable-rows"
        >
          <el-table-column prop="file_name" :label="$t('import.fileName')" min-width="200" />
          <el-table-column prop="status_display" :label="$t('import.status')" width="120">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ row.status_display }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="progress" :label="$t('import.progress')" width="150">
            <template #default="{ row }">
              <el-progress
                :percentage="row.progress"
                :status="getProgressStatus(row.status)"
                :stroke-width="12"
              />
            </template>
          </el-table-column>
          <el-table-column :label="$t('import.result')" width="200">
            <template #default="{ row }">
              <span v-if="row.status === 'pending'">-</span>
              <span v-else>
                {{ $t('import.successCount', { count: row.success_count }) }},
                {{ $t('import.failedCount', { count: row.failed_count }) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="project.name" :label="$t('testcase.project')" width="150">
            <template #default="{ row }">
              {{ row.project?.name || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="created_by.username" :label="$t('import.creator')" width="120" />
          <el-table-column prop="created_at" :label="$t('import.createdAt')" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>

    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="$t('import.taskDetail')"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="currentTask">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('import.fileName')">{{ currentTask.file_name }}</el-descriptions-item>
          <el-descriptions-item :label="$t('import.status')">
            <el-tag :type="getStatusType(currentTask.status)">
              {{ currentTask.status_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('import.progress')">
            <el-progress
              :percentage="currentTask.progress"
              :status="getProgressStatus(currentTask.status)"
              :stroke-width="12"
            />
          </el-descriptions-item>
          <el-descriptions-item :label="$t('testcase.project')">
            {{ currentTask.project?.name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('import.totalCount')">{{ currentTask.total_count }}</el-descriptions-item>
          <el-descriptions-item :label="$t('import.successCount', { count: currentTask.success_count })">
            {{ currentTask.success_count }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('import.failedCount', { count: currentTask.failed_count })">
            {{ currentTask.failed_count }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('import.createdAt')" :span="2">
            {{ formatDate(currentTask.created_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="currentTask.error_details && currentTask.error_details.length > 0" class="error-section">
          <h4>{{ $t('import.errorDetails') }}</h4>
          <el-table :data="currentTask.error_details" max-height="300" size="small">
            <el-table-column prop="row" :label="$t('import.rowNumber')" width="100" />
            <el-table-column prop="error" :label="$t('import.error')" min-width="300" />
          </el-table>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'
import dayjs from 'dayjs'

const { t } = useI18n()
const router = useRouter()
const loading = ref(false)
const tasks = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const statusFilter = ref('')
const detailDialogVisible = ref(false)
const currentTask = ref(null)

let pollingTimer = null

const fetchTasks = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      status: statusFilter.value
    }
    const response = await api.get('/testcases/import-tasks/', { params })
    tasks.value = response.data.results || []
    total.value = response.data.count || 0

    // 如果有进行中的任务，启动轮询
    const hasProcessingTasks = tasks.value.some(task =>
      task.status === 'pending' || task.status === 'processing'
    )
    if (hasProcessingTasks && !pollingTimer) {
      startPolling()
    }
  } catch (error) {
    ElMessage.error(t('import.fetchFailed'))
  } finally {
    loading.value = false
  }
}

const startPolling = () => {
  pollingTimer = setInterval(() => {
    fetchTasks()
  }, 5000) // 每5秒刷新一次
}

const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

const handleFilter = () => {
  currentPage.value = 1
  fetchTasks()
}

const handlePageChange = () => {
  fetchTasks()
}

const handleSizeChange = () => {
  currentPage.value = 1
  fetchTasks()
}

const getStatusType = (status) => {
  const typeMap = {
    pending: 'info',
    processing: 'warning',
    success: 'success',
    failed: 'danger',
    partial_success: 'warning'
  }
  return typeMap[status] || 'info'
}

const getProgressStatus = (status) => {
  const statusMap = {
    success: 'success',
    failed: 'exception',
    partial_success: 'warning'
  }
  return statusMap[status] || undefined
}

const formatDate = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm')
}

const showTaskDetail = (row) => {
  currentTask.value = row
  detailDialogVisible.value = true
}

onMounted(() => {
  fetchTasks()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style lang="scss" scoped>
.page-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px;
  box-sizing: border-box;
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.card-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.filter-bar {
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
}

.table-container {
  flex: 1;
  overflow: hidden;
  padding: 0 20px;

  :deep(.el-table) {
    height: 100% !important;
  }

  :deep(.el-table__body-wrapper) {
    overflow-y: auto !important;
  }
}

.clickable-rows {
  :deep(.el-table__body tr) {
    cursor: pointer;

    &:hover {
      background-color: #f5f7fa;
    }
  }
}

.pagination-container {
  padding: 20px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: center;
  flex-shrink: 0;
}

.error-section {
  margin-top: 20px;

  h4 {
    margin-bottom: 10px;
    color: #f56c6c;
  }
}
</style>
