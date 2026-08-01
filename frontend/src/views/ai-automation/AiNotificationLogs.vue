<template>
  <div class="page-container">
    <div class="page-titlebar">
      <h1 class="page-title">{{ $t('aiAutomation.notification.title') }}</h1>
    </div>

    <div class="workspace">
      <div class="list-column">
        <!-- 搜索区域卡片 -->
        <div class="filter-bar">
          <el-form :inline="true">
            <el-form-item :label="$t('aiAutomation.notification.taskName')">
              <el-input
                  v-model="searchForm.taskName"
                  :placeholder="$t('aiAutomation.notification.searchTaskName')"
                  clearable
                  @clear="handleSearch"
                  @keyup.enter="handleSearch"
                  style="width: 200px"
              >
                <template #prefix>
                  <el-icon>
                    <Search/>
                  </el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item :label="$t('aiAutomation.notification.dateRange')">
              <el-date-picker
                  v-model="searchForm.dateRange"
                  type="daterange"
                  :range-separator="$t('aiAutomation.notification.dateRangeTo')"
                  :start-placeholder="$t('aiAutomation.notification.startDate')"
                  :end-placeholder="$t('aiAutomation.notification.endDate')"
                  value-format="YYYY-MM-DD"
                  @change="handleSearch"
              />
            </el-form-item>
            <el-form-item :label="$t('aiAutomation.notification.notificationStatus')">
              <el-select
                  v-model="searchForm.status"
                  :placeholder="$t('aiAutomation.common.all')"
                  clearable
                  style="width: 130px"
                  @change="handleSearch"
              >
                <el-option :label="$t('aiAutomation.notification.statusSuccess')" value="success"/>
                <el-option :label="$t('aiAutomation.notification.statusFailed')" value="failed"/>
                <el-option :label="$t('aiAutomation.notification.statusPending')" value="pending"/>
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSearch">{{ $t('aiAutomation.common.search') }}</el-button>
              <el-button @click="handleReset">{{ $t('aiAutomation.common.reset') }}</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 通知列表面板 -->
        <section class="panel list-panel">
          <div class="panel__header">
            <span class="panel__title">{{ $t('aiAutomation.notification.logList') }}</span>
          </div>

          <div class="panel__body notification-log-table-wrapper">
            <el-table
                :data="logsData"
                v-loading="loading"
                :element-loading-text="$t('aiAutomation.notification.loading')"
                height="100%"
                @sort-change="handleSortChange"
            >
              <el-table-column type="index" label="序号" width="50" align="center" />
              <el-table-column
                   prop="task_name"
                  :label="$t('aiAutomation.notification.taskName')"
                  min-width="150"
                  sortable="custom"
              />
              <el-table-column
                  prop="task_type_display"
                  :label="$t('aiAutomation.notification.taskType')"
                  min-width="100"
              >
                <template #default="{ row }">
                  <el-tag type="info" size="small">
                    {{ row.task_type_display }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                  prop="actual_notification_type_display"
                  :label="$t('aiAutomation.notification.notificationType')"
                  min-width="120"
              >
                <template #default="{ row }">
                  <el-tag
                      :type="getNotificationTypeTagType(row.actual_notification_type_display)"
                      size="small"
                  >
                    {{ row.actual_notification_type_display }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                  prop="created_at"
                  :label="$t('aiAutomation.notification.notificationTime')"
                  min-width="180"
                  sortable="custom"
              >
                <template #default="{ row }">
                  {{ formatDate(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column
                  prop="status_display"
                  :label="$t('aiAutomation.common.status')"
                  min-width="100"
                  sortable="custom"
              >
                <template #default="{ row }">
                  <el-tag
                      :type="getStatusTagType(row.status_display)"
                      size="small"
                  >
                    {{ row.status_display }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                  :label="$t('aiAutomation.common.operation')"
                  width="100"
                  fixed="right"
              >
                <template #default="{ row }">
                  <ActionCell :actions="getNotificationActions(row)" :row="row" :max-visible="3" />
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div class="pagination-container">
            <el-pagination
                v-model:current-page="pagination.currentPage"
                v-model:page-size="pagination.pageSize"
                :page-sizes="[10, 20, 50, 100]"
                :total="pagination.total"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="handleSizeChange"
                @current-change="handleCurrentChange"
            />
          </div>
        </section>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog
        v-model="detailDialogVisible"
        :title="$t('aiAutomation.notification.detailTitle')"
        width="600px"
        :before-close="handleDetailDialogClose"
    >
      <el-form
          v-if="selectedLog"
          label-position="top"
          class="notification-detail-form"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('aiAutomation.notification.taskName')">
              <span>{{ selectedLog.task_name }}</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('aiAutomation.notification.taskType')">
              <span>{{ selectedLog.task_type_display }}</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('aiAutomation.notification.notificationType')">
              <el-tag :type="getNotificationTypeTagType(selectedLog.actual_notification_type_display)">
                {{ selectedLog.actual_notification_type_display }}
              </el-tag>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('aiAutomation.common.status')">
              <el-tag :type="getStatusTagType(selectedLog.status_display)">
                {{ selectedLog.status_display }}
              </el-tag>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('aiAutomation.notification.notificationTime')">
              <span>{{ formatDate(selectedLog.created_at) }}</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('aiAutomation.notification.sentTime')">
              <span>{{ selectedLog.sent_at ? formatDate(selectedLog.sent_at) : '-' }}</span>
            </el-form-item>
          </el-col>
          <el-col :span="24" v-if="selectedLog.webhook_bot_info && (selectedLog.webhook_bot_info.bot_type || selectedLog.webhook_bot_info.type)">
            <el-form-item :label="$t('aiAutomation.notification.webhookBot')">
              <div class="webhook-info">
                <el-tag
                    class="webhook-tag"
                    size="small"
                    type="info"
                >
                  {{ selectedLog.webhook_bot_info.name || selectedLog.webhook_bot_info.bot_name || $t('aiAutomation.notification.defaultBotName') }}
                </el-tag>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item :label="$t('aiAutomation.notification.content')">
              <div class="notification-content">
                <div v-if="parsedNotificationContent" class="notification-content-parsed">
                  <div class="content-item" v-for="(item, index) in parsedNotificationContent" :key="index">
                    <span class="content-label">{{ item.label }}:</span>
                    <span class="content-value">{{ item.value }}</span>
                  </div>
                </div>
                <div v-else class="notification-content-raw">
                  <pre>{{ selectedLog.notification_content || '-' }}</pre>
                </div>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="24" v-if="selectedLog.error_message">
            <el-form-item :label="$t('aiAutomation.notification.errorMessage')">
              <div class="error-message">
                <el-alert
                    :title="selectedLog.error_message"
                    type="error"
                    show-icon
                    :closable="false"
                />
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailDialogVisible = false">{{ $t('aiAutomation.common.cancel') }}</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import {Search} from '@element-plus/icons-vue'
import {ref, reactive, onMounted, computed} from 'vue'
import {ElMessage} from 'element-plus'
import { getAiNotificationLogs } from '@/api/ui_automation.js'
import { useI18n } from 'vue-i18n'
import ActionCell from '@/components/ActionCell.vue'

export default {
  name: 'AiNotificationLogs',
  components: {
    Search,
    ActionCell
  },
  setup() {
    const { t, locale } = useI18n()

    // 数据状态
    const loading = ref(false)
    const logsData = ref([])
    const detailDialogVisible = ref(false)
    const selectedLog = ref(null)

    // 搜索表单
    const searchForm = reactive({
      taskName: '',
      dateRange: [],
      status: ''
    })

    // 分页配置
    const pagination = reactive({
      currentPage: 1,
      pageSize: 10,
      total: 0
    })

    // 排序参数
    const sortParams = reactive({
      prop: 'created_at',
      order: 'descending'
    })

    // 获取通知日志数据
    const fetchLogsData = async () => {
      loading.value = true
      try {
        const params = {
          page: pagination.currentPage,
          page_size: pagination.pageSize,
          ordering: sortParams.order === 'ascending' ? sortParams.prop : `-${sortParams.prop}`
        }

        // 添加搜索条件
        if (searchForm.taskName) {
          params.search = searchForm.taskName
        }
        if (searchForm.dateRange && searchForm.dateRange.length === 2) {
          params.start_date = searchForm.dateRange[0]
          params.end_date = searchForm.dateRange[1]
        }
        if (searchForm.status) {
          params.status = searchForm.status
        }

        const response = await getAiNotificationLogs(params)
        logsData.value = response.data.results || []
        pagination.total = response.data.count || 0
      } catch (error) {
        console.error('Failed to fetch AI notification logs:', error)
        ElMessage.error(t('aiAutomation.notification.loadFailed'))
      } finally {
        loading.value = false
      }
    }

    // 处理搜索
    const handleSearch = () => {
      pagination.currentPage = 1
      fetchLogsData()
    }

    // 重置搜索
    const handleReset = () => {
      searchForm.taskName = ''
      searchForm.dateRange = []
      searchForm.status = ''
      pagination.currentPage = 1
      fetchLogsData()
    }

    // 处理分页变化
    const handleSizeChange = (val) => {
      pagination.pageSize = val
      pagination.currentPage = 1
      fetchLogsData()
    }

    const handleCurrentChange = (val) => {
      pagination.currentPage = val
      fetchLogsData()
    }

    // 处理排序
    const handleSortChange = ({prop, order}) => {
      sortParams.prop = prop
      sortParams.order = order || 'descending'
      fetchLogsData()
    }

    // 查看详情
    const viewDetail = (row) => {
      selectedLog.value = row
      detailDialogVisible.value = true
    }

    // 关闭详情弹窗
    const handleDetailDialogClose = (done) => {
      selectedLog.value = null
      done()
    }

    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return date.toLocaleString(locale.value === 'zh-cn' ? 'zh-CN' : 'en-US')
    }

    // 获取状态标签类型
    const getStatusTagType = (status) => {
      const typeMap = {
        '发送成功': 'success', 'Success': 'success', 'success': 'success',
        '发送失败': 'danger', 'Failed': 'danger', 'failed': 'danger',
        '待发送': 'info', 'Pending': 'info', 'pending': 'info',
        '发送中': 'warning', 'Sending': 'warning', 'sending': 'warning'
      }
      return typeMap[status] || 'info'
    }

    // 获取通知类型标签类型
    const getNotificationTypeTagType = (typeDisplay) => {
      const typeMap = {
        '邮箱通知': '', 'Email': '',
        'Webhook机器人': 'primary', 'Webhook Bot': 'primary',
        '两种都发送': 'warning', 'Both': 'warning'
      }
      return typeMap[typeDisplay] || 'info'
    }

    // 解析通知内容为结构化数据
    const parsedNotificationContent = computed(() => {
      if (!selectedLog.value || !selectedLog.value.notification_content) {
        return null
      }

      const content = selectedLog.value.notification_content

      try {
        const jsonContent = JSON.parse(content)
        const result = []
        let contentText = ''

        if (jsonContent.msgtype === 'markdown' && jsonContent.markdown) {
          contentText = jsonContent.markdown.text || jsonContent.markdown.content || ''
        } else if (jsonContent.msg_type === 'interactive' && jsonContent.card) {
          if (jsonContent.card.elements && jsonContent.card.elements[0] && jsonContent.card.elements[0].text) {
            contentText = jsonContent.card.elements[0].text.content
          }
        }

        if (contentText) {
          const lines = contentText.split('\n').filter(line => line.trim())
          lines.forEach(line => {
            if (line.includes('**') || line.trim() === '') return
            const colonIndex = line.indexOf(':')
            if (colonIndex > 0) {
              const label = line.substring(0, colonIndex).trim()
              const value = line.substring(colonIndex + 1).trim()
              if (label && value) {
                result.push({ label, value })
              }
            }
          })
          return result.length > 0 ? result : null
        }
      } catch (e) {
        // JSON解析失败，尝试纯文本
      }

      try {
        const result = []
        const lines = content.split('\n').filter(line => line.trim())
        lines.forEach(line => {
          if (!line.trim()) return
          const colonIndex = line.indexOf(':')
          if (colonIndex > 0) {
            const label = line.substring(0, colonIndex).trim()
            const value = line.substring(colonIndex + 1).trim()
            if (label && value && !value.includes("'results':") && !value.includes('"results":')) {
              result.push({ label, value })
            }
          }
        })
        return result.length > 0 ? result : null
      } catch (e) {
        return null
      }
    })

    // 操作列 actions
    const getNotificationActions = (row) => [
      { key: 'detail', label: t('aiAutomation.notification.viewDetail'), onClick: (r) => viewDetail(r) }
    ]

    // 组件挂载时获取数据
    onMounted(() => {
      fetchLogsData()
    })

    return {
      loading,
      logsData,
      detailDialogVisible,
      selectedLog,
      searchForm,
      pagination,
      sortParams,
      parsedNotificationContent,
      handleSearch,
      handleReset,
      handleSizeChange,
      handleCurrentChange,
      handleSortChange,
      viewDetail,
      getNotificationActions,
      handleDetailDialogClose,
      formatDate,
      getStatusTagType,
      getNotificationTypeTagType
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

.notification-log-table-wrapper {
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

.notification-detail-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.notification-content {
  width: 100%;
}

.notification-content-parsed {
  background: #ffffff;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.content-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 0;
  border-bottom: 1px solid #f0f2f5;
}

.content-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.content-item:first-child {
  padding-top: 0;
}

.content-label {
  font-weight: 600;
  color: #606266;
  min-width: 100px;
  flex-shrink: 0;
  margin-right: 16px;
  font-size: 14px;
  line-height: 1.8;
}

.content-value {
  color: #303133;
  flex: 1;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.8;
}

.notification-content-raw pre {
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
  max-height: 400px;
  overflow-y: auto;
}

.webhook-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.webhook-tag {
  margin: 0;
}

.error-message {
  margin-top: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
