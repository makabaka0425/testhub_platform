<template>
  <div class="page-container">
    <div class="page-titlebar">
      <h1 class="page-title">{{ $t('version.title') }}</h1>
      <div class="titlebar-actions">
        <el-button v-if="selectedVersions.length > 0" type="danger" plain @click="batchDeleteVersions" :disabled="isDeleting">
          {{ $t('version.batchDelete') }} ({{ selectedVersions.length }})
        </el-button>
        <el-button type="primary" @click="createVersion">
          <el-icon><Plus /></el-icon>
          {{ $t('version.newVersion') }}
        </el-button>
      </div>
    </div>

    <div class="workspace">
      <div class="list-column">
        <!-- 搜索区域卡片 -->
        <div class="filter-bar">
          <el-form :inline="true">
            <el-form-item>
              <el-input v-model="searchText" :placeholder="$t('version.searchPlaceholder')" clearable style="width: 200px" @input="handleSearch">
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-select v-model="projectFilter" :placeholder="$t('version.relatedProject')" clearable style="width: 180px" @change="handleFilter">
                <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-select v-model="baselineFilter" :placeholder="$t('version.versionType')" clearable style="width: 130px" @change="handleFilter">
                <el-option :label="$t('version.baselineVersion')" :value="true" />
                <el-option :label="$t('version.normalVersion')" :value="false" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- 版本列表面板 -->
        <section class="panel list-panel">
          <div class="panel__body version-table-wrapper">
            <el-table :data="versions" v-loading="loading" height="100%" @selection-change="handleSelectionChange">
              <el-table-column type="selection" width="45" />
              <el-table-column type="index" :label="$t('version.serialNumber')" width="60" :index="getSerialNumber" />
              <el-table-column prop="name" :label="$t('version.versionName')" min-width="100">
                <template #default="{ row }">
                  <div class="version-name">
                    <span>{{ row.name }}</span>
                    <el-tag v-if="row.is_baseline" type="warning" size="small" class="baseline-tag">{{ $t('version.baseline') }}</el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="projects" :label="$t('version.relatedProject')" min-width="250">
                <template #default="{ row }">
                  <div v-if="row.projects && row.projects.length > 0" class="project-tags">
                    <el-tag v-for="project in row.projects.slice(0, 2)" :key="project.id" size="small" type="primary" class="project-tag">{{ project.name }}</el-tag>
                    <el-tooltip v-if="row.projects.length > 2" :content="getProjectsTooltip(row.projects)">
                      <el-tag size="small" type="info" class="project-tag">+{{ row.projects.length - 2 }}</el-tag>
                    </el-tooltip>
                  </div>
                  <span v-else class="no-project">{{ $t('version.noProject') }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="description" :label="$t('version.description')" min-width="200" show-overflow-tooltip />
              <el-table-column prop="testcases_count" :label="$t('version.testCaseCount')" width="100">
                <template #default="{ row }">
                  <el-tag type="info" size="small">{{ row.testcases_count }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_by.username" :label="$t('version.creator')" width="100" />
              <el-table-column prop="created_at" :label="$t('version.createdAt')" width="180" :formatter="formatDate" />
              <el-table-column :label="$t('project.actions')" width="150" fixed="right">
                <template #default="{ row }">
                  <el-button link class="op-btn" @click="editVersion(row)">{{ $t('common.edit') }}</el-button>
                  <el-button link class="op-btn op-btn--danger" @click="deleteVersion(row)">{{ $t('common.delete') }}</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="total"
              @size-change="() => { currentPage = 1; fetchVersions() }"
              @current-change="handlePageChange"
            />
          </div>
        </section>
      </div>
    </div>
    
    <!-- 版本表单对话框 -->
    <el-dialog
      v-model="versionDialogVisible"
      :title="isEdit ? $t('version.editVersion') : $t('version.newVersion')"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="versionForm" :rules="versionRules" ref="versionFormRef" label-width="120px">
        <el-form-item :label="$t('version.versionName')" prop="name">
          <el-input v-model="versionForm.name" :placeholder="$t('version.versionNamePlaceholder')" />
        </el-form-item>

        <el-form-item :label="$t('version.relatedProject')" prop="project_ids">
          <el-select
            v-model="versionForm.project_ids"
            :placeholder="$t('version.selectProjects')"
            multiple
            style="width: 100%"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('version.versionDescription')">
          <el-input
            v-model="versionForm.description"
            type="textarea"
            :rows="3"
            :placeholder="$t('version.versionDescriptionPlaceholder')"
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="versionForm.is_baseline">{{ $t('version.setAsBaseline') }}</el-checkbox>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="versionDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveVersion" :loading="saving">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import api from '@/utils/api'
import dayjs from 'dayjs'

const { t } = useI18n()
const loading = ref(false)
const versions = ref([])
const projects = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchText = ref('')
const projectFilter = ref('')
const baselineFilter = ref('')
const selectedVersions = ref([])
const isDeleting = ref(false)

const versionDialogVisible = ref(false)
const versionFormRef = ref()
const saving = ref(false)
const isEdit = ref(false)
const editingVersionId = ref(null)

const versionForm = reactive({
  name: '',
  description: '',
  project_ids: [],
  is_baseline: false
})

const versionRules = {
  name: [{ required: true, message: computed(() => t('version.versionNameRequired')), trigger: 'blur' }],
  project_ids: [{ required: true, message: computed(() => t('version.projectRequired')), trigger: 'change' }]
}

const fetchVersions = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      search: searchText.value,
      projects: projectFilter.value,
      is_baseline: baselineFilter.value
    }
    const response = await api.get('/versions/', { params })
    versions.value = response.data.results || []
    total.value = response.data.count || 0
  } catch (error) {
    ElMessage.error(t('version.fetchListFailed'))
  } finally {
    loading.value = false
  }
}

const fetchProjects = async () => {
  try {
    const response = await api.get('/projects/')
    projects.value = response.data.results || response.data || []
  } catch (error) {
    ElMessage.error(t('version.fetchProjectsFailed'))
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchVersions()
}

const handleFilter = () => {
  currentPage.value = 1
  fetchVersions()
}

const handlePageChange = () => {
  fetchVersions()
}

const createVersion = () => {
  isEdit.value = false
  resetVersionForm()
  versionDialogVisible.value = true
}

const editVersion = (version) => {
  isEdit.value = true
  editingVersionId.value = version.id
  
  versionForm.name = version.name
  versionForm.description = version.description
  versionForm.project_ids = version.projects.map(p => p.id)
  versionForm.is_baseline = version.is_baseline
  
  versionDialogVisible.value = true
}

const saveVersion = async () => {
  if (!versionFormRef.value) return

  try {
    await versionFormRef.value.validate()
    saving.value = true

    if (isEdit.value) {
      await api.put(`/versions/${editingVersionId.value}/`, versionForm)
      ElMessage.success(t('version.updateSuccess'))
    } else {
      await api.post('/versions/', versionForm)
      ElMessage.success(t('version.createSuccess'))
    }

    versionDialogVisible.value = false
    fetchVersions()

  } catch (error) {
    if (error.response?.data) {
      const errors = Object.values(error.response.data).flat()
      ElMessage.error(errors[0] || t('version.saveFailed'))
    } else {
      ElMessage.error(t('version.saveFailed'))
    }
  } finally {
    saving.value = false
  }
}

const deleteVersion = async (version) => {
  try {
    await ElMessageBox.confirm(t('version.deleteConfirm'), t('common.warning'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })

    await api.delete(`/versions/${version.id}/`)
    ElMessage.success(t('version.deleteSuccess'))
    fetchVersions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('version.deleteFailed'))
    }
  }
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedVersions.value = selection
}

// 获取序号
const getSerialNumber = (index) => {
  return (currentPage.value - 1) * pageSize.value + index + 1
}

// 批量删除
const batchDeleteVersions = async () => {
  if (selectedVersions.value.length === 0) {
    ElMessage.warning(t('version.selectVersionsFirst'))
    return
  }

  try {
    await ElMessageBox.confirm(
      t('version.batchDeleteConfirm', { count: selectedVersions.value.length }),
      t('common.warning'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )

    isDeleting.value = true
    let successCount = 0
    let failCount = 0

    // 逐个删除选中的版本
    for (const version of selectedVersions.value) {
      try {
        await api.delete(`/versions/${version.id}/`)
        successCount++
      } catch (error) {
        console.error(`删除版本 ${version.id} 失败:`, error)
        failCount++
      }
    }

    // 显示删除结果
    if (successCount > 0) {
      ElMessage.success(t('version.batchDeleteSuccess', { successCount }) + (failCount > 0 ? `，${failCount} ${t('common.error')}` : ''))
    } else {
      ElMessage.error(t('version.batchDeleteFailed'))
    }

    // 清空选择并重新加载列表
    selectedVersions.value = []
    fetchVersions()

  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error(t('version.batchDeleteFailed') + ': ' + (error.message || t('common.error')))
    }
  } finally {
    isDeleting.value = false
  }
}

const resetVersionForm = () => {
  versionForm.name = ''
  versionForm.description = ''
  versionForm.project_ids = []
  versionForm.is_baseline = false
  editingVersionId.value = null
}

const formatDate = (row, column, cellValue) => {
  return dayjs(cellValue).format('YYYY-MM-DD HH:mm')
}

const getProjectsTooltip = (projects) => {
  return projects.map(p => p.name).join('、')
}

onMounted(() => {
  fetchProjects()
  fetchVersions()
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

.version-table-wrapper {
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

.version-name {
  display: flex;
  align-items: center;
  gap: 8px;
  .baseline-tag { font-size: 12px; }
}

.project-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  .project-tag { margin: 0; }
}

.no-project {
  color: #909399;
  font-size: 12px;
  font-style: italic;
}

.op-btn {
  --el-button-text-color: var(--brand-500, #4f8cff);
  padding: 2px 4px !important;
  border-radius: var(--radius-sm, 6px);
}

.op-btn--danger {
  --el-button-text-color: #f56c6c;
}
</style>