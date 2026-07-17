<template>
  <div class="page-container">
    <!-- ==================== 套件列表视图 ==================== -->
    <template v-if="!currentSuite">
      <div class="page-header">
        <h1 class="page-title">套件管理</h1>
        <div class="header-actions">
          <el-select v-model="projectId" placeholder="选择项目" style="width: 200px" @change="onProjectChange">
            <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
          </el-select>
          <el-button type="primary" @click="handleNewSuite">新增</el-button>
        </div>
      </div>

      <div class="filter-bar">
        <el-input v-model="searchText" placeholder="搜索套件名称..." clearable @input="handleSearch" style="width: 240px">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
      </div>

      <div class="table-scroll-area">
        <el-table :data="suites" v-loading="loading" style="width: 100%">
          <el-table-column prop="name" label="套件名称" min-width="200">
            <template #default="{ row }">
              <el-link @click="enterSuiteDetail(row)" type="primary">{{ row.name }}</el-link>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
          <el-table-column label="执行模式" width="130">
            <template #default="{ row }">
              <el-tag size="small" :type="row.execution_mode === 'shared_session' ? 'success' : 'info'">
                {{ row.execution_mode === 'shared_session' ? '共享会话' : '用例独立' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="登录配置" width="150">
            <template #default="{ row }">
              <span v-if="row.login_config_name">{{ row.login_config_name }}</span>
              <span v-else style="color: #909399">未配置</span>
            </template>
          </el-table-column>
          <el-table-column label="用例数" width="80" align="center">
            <template #default="{ row }">{{ row.test_case_count || 0 }}</template>
          </el-table-column>
          <el-table-column label="执行状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="getExecutionStatusTag(row.execution_status)">
                {{ getExecutionStatusText(row.execution_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="通过" width="60" align="center">
            <template #default="{ row }">
              <span style="color: #67c23a; font-weight: bold">{{ row.passed_count || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column label="失败" width="60" align="center">
            <template #default="{ row }">
              <span style="color: #f56c6c; font-weight: bold">{{ row.failed_count || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column label="跳过" width="60" align="center">
            <template #default="{ row }">
              <span style="color: #e6a23c; font-weight: bold">{{ row.skipped_count || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" width="170" :formatter="formatDate" />
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <div class="op-btns">
                <el-button class="op-btn" type="primary" link size="small" @click="editSuiteInfo(row)">编辑</el-button>
                <el-button class="op-btn" type="primary" link size="small" @click="runSuite(row)">运行</el-button>
                <el-button class="op-btn op-btn--danger" link size="small" @click="deleteSuite(row.id)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-container">
          <el-pagination v-model:current-page="pagination.currentPage" v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next" :total="total"
            @size-change="handleSizeChange" @current-change="handleCurrentChange" />
        </div>
      </div>
    </template>

    <!-- ==================== 套件详情视图（内部关联用例） ==================== -->
    <template v-if="currentSuite">
      <div class="page-header">
        <h1 class="page-title">
          <el-button link @click="exitSuiteDetail" style="margin-right: 8px; font-size: 16px">
            <el-icon><ArrowLeft /></el-icon>
          </el-button>
          {{ currentSuite.name }}
        </h1>
        <div class="header-actions">
          <el-button type="primary" @click="showAssociateDialog = true">关联用例</el-button>
          <el-button @click="editSuiteInfo(currentSuite)">编辑</el-button>
          <el-button type="primary" @click="runSuite(currentSuite)">运行</el-button>
        </div>
      </div>

      <!-- 套件基本信息 -->
      <div class="suite-info-bar">
        <span class="info-item"><label>执行模式：</label>{{ currentSuite.execution_mode === 'shared_session' ? '共享会话' : '用例独立' }}</span>
        <span class="info-item"><label>登录配置：</label>{{ currentSuite.login_config_name || '未配置' }}</span>
        <span class="info-item"><label>描述：</label>{{ currentSuite.description || '无' }}</span>
      </div>

      <!-- 套件内用例列表 -->
      <div class="suite-cases-section">
        <div class="section-header">
          <span class="section-title">用例列表 ({{ suiteCases.length }})</span>
          <div class="section-actions">
            <el-input v-model="suiteCaseSearch" placeholder="搜索用例名称..." clearable size="small" style="width: 200px; margin-right: 8px">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button size="small" type="danger" plain :disabled="selectedCaseIds.length === 0" @click="batchRemoveCases">
              批量移除 ({{ selectedCaseIds.length }})
            </el-button>
          </div>
        </div>
        <el-table :data="filteredSuiteCases" style="width: 100%" @selection-change="handleCaseSelectionChange">
          <el-table-column type="selection" width="45" />
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="test_case.name" label="用例名称" min-width="240" show-overflow-tooltip />
          <el-table-column label="优先级" width="80" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="getPriorityTag(row.test_case.priority)">{{ getPriorityText(row.test_case.priority) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <span class="status-tag" :class="`status-${row.test_case.status || 'normal'}`">{{ getStatusText(row.test_case.status) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <div class="op-btns">
                <el-button class="op-btn op-btn--danger" link size="small" @click="removeSingleCase(row)">移除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </template>

    <!-- ==================== 新增/编辑套件对话框（仅基础信息） ==================== -->
    <el-dialog v-model="showEditDialog" :title="isEditing ? '编辑套件' : '新建套件'" width="520px" :close-on-click-modal="false">
      <el-form ref="editFormRef" :model="editForm" :rules="editFormRules" label-position="left" label-width="80px">
        <el-form-item label="套件名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入套件名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="请输入套件描述" />
        </el-form-item>
        <el-form-item label="执行模式" prop="execution_mode">
          <el-radio-group v-model="editForm.execution_mode">
            <el-radio label="per_case">用例独立模式</el-radio>
            <el-radio label="shared_session">共享会话模式</el-radio>
          </el-radio-group>
          <div class="mode-tip" v-if="editForm.execution_mode === 'per_case'">每个用例独立启动浏览器，互不影响</div>
          <div class="mode-tip" v-else>所有用例共享同一浏览器会话，仅需登录一次</div>
        </el-form-item>
        <el-form-item v-if="editForm.execution_mode === 'shared_session'" label="登录配置" prop="login_config">
          <el-select v-model="editForm.login_config" placeholder="请选择登录配置" clearable filterable style="width: 100%">
            <el-option v-for="cfg in loginConfigs" :key="cfg.id" :label="cfg.name" :value="cfg.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveSuiteInfo" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 关联用例弹窗（三栏布局） ==================== -->
    <el-dialog v-model="showAssociateDialog" title="关联用例" width="900px" :close-on-click-modal="false" top="5vh">
      <div class="associate-layout">
        <!-- 左侧：分组树 -->
        <div class="associate-left">
          <div class="panel-title">分组</div>
          <div class="tree-scroll">
            <div class="tree-item" :class="{ active: !assocGroupFilter }" @click="assocGroupFilter = null">全部</div>
            <el-tree :data="groupTree" :props="{ children: 'children', label: 'name', value: 'id' }"
              node-key="id" highlight-current check-strictly
              @node-click="handleGroupNodeClick" />
          </div>
        </div>

        <!-- 中侧：可选用例 -->
        <div class="associate-center">
          <div class="panel-title">
            <span>可选用例</span>
            <el-input v-model="assocCaseSearch" placeholder="搜索用例..." clearable size="small" style="width: 160px; margin-left: auto">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
          </div>
          <div class="panel-body">
            <el-table :data="filteredAssocCases" height="360" @selection-change="handleAssocSelectionChange"
              ref="assocTableRef" :row-class-name="getAssocRowClass">
              <el-table-column type="selection" width="40" :selectable="isCaseAlreadyAdded" />
              <el-table-column prop="name" label="用例名称" min-width="160" show-overflow-tooltip />
              <el-table-column label="优先级" width="70" align="center">
                <template #default="{ row }">
                  <el-tag size="small" :type="getPriorityTag(row.priority)">{{ getPriorityText(row.priority) }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- 右侧：已选用例 -->
        <div class="associate-right">
          <div class="panel-title">
            <span>已选 ({{ selectedAssocCases.length }})</span>
            <el-button size="small" text type="danger" @click="selectedAssocCases = []" :disabled="selectedAssocCases.length === 0">清空</el-button>
          </div>
          <div class="panel-body">
            <el-table :data="selectedAssocCases" height="360">
              <el-table-column prop="name" label="用例名称" min-width="120" show-overflow-tooltip />
              <el-table-column width="50">
                <template #default="{ $index }">
                  <el-button size="small" text type="danger" @click="selectedAssocCases.splice($index, 1)">
                    <el-icon><Close /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showAssociateDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAssociate" :loading="assocSaving" :disabled="selectedAssocCases.length === 0">
          确认关联 ({{ selectedAssocCases.length }})
        </el-button>
      </template>
    </el-dialog>

    <!-- ==================== 运行配置对话框 ==================== -->
    <el-dialog v-model="showRunDialog" title="运行配置" width="500px" :close-on-click-modal="false">
      <el-form :model="runConfig" label-position="left" label-width="80px">
        <el-form-item label="测试引擎">
          <el-select v-model="runConfig.engine">
            <el-option label="Playwright" value="playwright" />
            <el-option label="Selenium" value="selenium" />
          </el-select>
        </el-form-item>
        <el-form-item label="浏览器">
          <el-select v-model="runConfig.browser">
            <el-option label="Chrome" value="chrome" />
            <el-option label="Firefox" value="firefox" />
          </el-select>
        </el-form-item>
        <el-form-item label="运行模式">
          <el-radio-group v-model="runConfig.headless">
            <el-radio :label="false">有头模式</el-radio>
            <el-radio :label="true">无头模式</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRunDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmRunSuite" :loading="running">开始执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, ArrowLeft, Close } from '@element-plus/icons-vue'
import {
  getUiProjects, getTestSuites, createTestSuite, updateTestSuite, deleteTestSuite,
  getTestCases, getTestSuiteTestCases, addTestCasesToTestSuite,
  removeTestCaseFromTestSuite, removeTestCasesFromTestSuite,
  updateTestCaseOrder, runTestSuite, getLoginConfigs, getTestCaseGroupTree
} from '@/api/ui_automation'

// ==================== 通用数据 ====================
const projects = ref([])
const projectId = ref('')
const loginConfigs = ref([])
const groupTree = ref([])

// ==================== 套件列表 ====================
const suites = ref([])
const loading = ref(false)
const searchText = ref('')
const total = ref(0)
const pagination = reactive({ currentPage: 1, pageSize: 20 })

const loadProjects = async () => {
  try {
    const res = await getUiProjects({ page_size: 100 })
    projects.value = res.data.results || res.data
  } catch (e) { console.error(e) }
}

const loadSuites = async () => {
  if (!projectId.value) { suites.value = []; total.value = 0; return }
  loading.value = true
  try {
    const res = await getTestSuites({
      project: projectId.value, page: pagination.currentPage,
      page_size: pagination.pageSize, search: searchText.value
    })
    suites.value = res.data.results || res.data
    total.value = res.data.count || res.data.length
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const loadLoginConfigs = async () => {
  if (!projectId.value) { loginConfigs.value = []; return }
  try {
    const res = await getLoginConfigs({ project: projectId.value, page_size: 1000 })
    loginConfigs.value = res.data.results || res.data
  } catch (e) { console.error(e) }
}

const loadGroupTree = async () => {
  if (!projectId.value) { groupTree.value = []; return }
  try {
    const res = await getTestCaseGroupTree({ project: projectId.value })
    groupTree.value = res.data || []
  } catch (e) { console.error(e) }
}

const onProjectChange = async () => { pagination.currentPage = 1; await loadSuites() }
const handleSearch = async () => { pagination.currentPage = 1; await loadSuites() }
const handleSizeChange = async () => { pagination.currentPage = 1; await loadSuites() }
const handleCurrentChange = async () => { await loadSuites() }

// ==================== 新增/编辑套件（仅基础信息） ====================
const showEditDialog = ref(false)
const isEditing = ref(false)
const editingSuiteId = ref(null)
const saving = ref(false)
const editFormRef = ref(null)
const editForm = reactive({ name: '', description: '', execution_mode: 'per_case', login_config: null })
const editFormRules = { name: [{ required: true, message: '请输入套件名称', trigger: 'blur' }] }

const handleNewSuite = async () => {
  isEditing.value = false
  editingSuiteId.value = null
  Object.assign(editForm, { name: '', description: '', execution_mode: 'per_case', login_config: null })
  await loadLoginConfigs()
  showEditDialog.value = true
}

const editSuiteInfo = async (row) => {
  isEditing.value = true
  editingSuiteId.value = row.id
  Object.assign(editForm, {
    name: row.name,
    description: row.description || '',
    execution_mode: row.execution_mode || 'per_case',
    login_config: row.login_config || null
  })
  await loadLoginConfigs()
  showEditDialog.value = true
}

const saveSuiteInfo = async () => {
  if (!editFormRef.value) return
  await editFormRef.value.validate()
  if (!projectId.value) { ElMessage.warning('请先选择项目'); return }

  saving.value = true
  try {
    const data = {
      project: projectId.value,
      name: editForm.name,
      description: editForm.description,
      execution_mode: editForm.execution_mode,
      login_config: editForm.execution_mode === 'shared_session' ? editForm.login_config : null
    }
    if (isEditing.value) {
      await updateTestSuite(editingSuiteId.value, data)
      ElMessage.success('套件更新成功')
    } else {
      await createTestSuite(data)
      ElMessage.success('套件创建成功')
    }
    showEditDialog.value = false
    await loadSuites()
    // 如果当前在详情视图且编辑的是当前套件，刷新详情
    if (currentSuite.value && currentSuite.value.id === editingSuiteId.value) {
      await loadSuiteCases()
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('保存失败')
  } finally { saving.value = false }
}

// ==================== 套件详情（内部用例管理） ====================
const currentSuite = ref(null)
const suiteCases = ref([])
const suiteCaseSearch = ref('')
const selectedCaseIds = ref([])

const filteredSuiteCases = computed(() => {
  if (!suiteCaseSearch.value) return suiteCases.value
  const kw = suiteCaseSearch.value.toLowerCase()
  return suiteCases.value.filter(c => c.test_case.name.toLowerCase().includes(kw))
})

const enterSuiteDetail = (row) => {
  currentSuite.value = row
  loadSuiteCases()
}

const exitSuiteDetail = () => {
  currentSuite.value = null
  suiteCases.value = []
  suiteCaseSearch.value = ''
  selectedCaseIds.value = []
  loadSuites()
}

const loadSuiteCases = async () => {
  if (!currentSuite.value) return
  try {
    const res = await getTestSuiteTestCases(currentSuite.value.id)
    suiteCases.value = res.data || []
  } catch (e) { console.error(e) }
}

const handleCaseSelectionChange = (rows) => {
  selectedCaseIds.value = rows.map(r => r.test_case.id)
}

const removeSingleCase = async (row) => {
  try {
    await ElMessageBox.confirm(`确定移除用例「${row.test_case.name}」？`, '提示', { type: 'warning' })
    await removeTestCaseFromTestSuite(currentSuite.value.id, row.test_case.id)
    ElMessage.success('已移除')
    await loadSuiteCases()
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

const batchRemoveCases = async () => {
  try {
    await ElMessageBox.confirm(`确定批量移除 ${selectedCaseIds.value.length} 个用例？`, '提示', { type: 'warning' })
    await removeTestCasesFromTestSuite(currentSuite.value.id, selectedCaseIds.value)
    ElMessage.success(`已移除 ${selectedCaseIds.value.length} 个用例`)
    selectedCaseIds.value = []
    await loadSuiteCases()
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

// ==================== 关联用例弹窗 ====================
const showAssociateDialog = ref(false)
const assocGroupFilter = ref(null)
const assocCaseSearch = ref('')
const allTestCases = ref([])
const selectedAssocCases = ref([])
const assocSaving = ref(false)
const assocTableRef = ref(null)

const filteredAssocCases = computed(() => {
  let result = allTestCases.value
  if (assocGroupFilter.value) {
    result = result.filter(tc => tc.group === assocGroupFilter.value)
  }
  if (assocCaseSearch.value) {
    const kw = assocCaseSearch.value.toLowerCase()
    result = result.filter(tc => tc.name.toLowerCase().includes(kw))
  }
  return result
})

// 已在套件中的用例ID集合
const existingCaseIds = computed(() => new Set(suiteCases.value.map(c => c.test_case.id)))

const isCaseAlreadyAdded = (row) => {
  // 不可选：已在套件中 + 已在右侧选中列表中
  return !existingCaseIds.value.has(row.id) && !selectedAssocCases.value.some(c => c.id === row.id)
}

const getAssocRowClass = ({ row }) => {
  if (existingCaseIds.value.has(row.id)) return 'already-added-row'
  return ''
}

const handleGroupNodeClick = (data) => {
  assocGroupFilter.value = data.id
}

const handleAssocSelectionChange = (rows) => {
  // 只追加新增的（避免重复）
  const newIds = rows.map(r => r.id)
  // 移除取消勾选的
  selectedAssocCases.value = selectedAssocCases.value.filter(c => newIds.includes(c.id))
  // 添加新勾选的
  for (const row of rows) {
    if (!selectedAssocCases.value.some(c => c.id === row.id)) {
      selectedAssocCases.value.push({ id: row.id, name: row.name, priority: row.priority })
    }
  }
}

const confirmAssociate = async () => {
  if (selectedAssocCases.value.length === 0) return
  assocSaving.value = true
  try {
    await addTestCasesToTestSuite(currentSuite.value.id, {
      test_case_ids: selectedAssocCases.value.map(c => c.id)
    })
    ElMessage.success(`成功关联 ${selectedAssocCases.value.length} 个用例`)
    showAssociateDialog.value = false
    selectedAssocCases.value = []
    await loadSuiteCases()
  } catch (e) {
    console.error(e)
    ElMessage.error('关联失败')
  } finally { assocSaving.value = false }
}

// 弹窗打开时加载数据
const onAssociateDialogOpen = async () => {
  assocGroupFilter.value = null
  assocCaseSearch.value = ''
  selectedAssocCases.value = []
  await Promise.all([loadAllTestCases(), loadGroupTree()])
  // 下一个tick后设置已添加行不可选
  await nextTick()
}

const loadAllTestCases = async () => {
  if (!projectId.value) return
  try {
    const res = await getTestCases({ project: projectId.value, page_size: 1000 })
    allTestCases.value = res.data.results || res.data
  } catch (e) { console.error(e) }
}

// 监听弹窗打开
import { watch } from 'vue'
watch(showAssociateDialog, (val) => { if (val) onAssociateDialogOpen() })

// ==================== 删除套件 ====================
const deleteSuite = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该套件？', '提示', { type: 'warning' })
    await deleteTestSuite(id)
    ElMessage.success('删除成功')
    if (currentSuite.value && currentSuite.value.id === id) { exitSuiteDetail() }
    else { await loadSuites() }
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

// ==================== 运行套件 ====================
const showRunDialog = ref(false)
const running = ref(false)
const currentRunningSuite = ref(null)
const runConfig = reactive({ engine: 'playwright', browser: 'chrome', headless: false })

const runSuite = (suite) => {
  if (!suite.test_case_count || suite.test_case_count === 0) {
    ElMessage.warning('该套件未包含用例，无法执行'); return
  }
  currentRunningSuite.value = suite
  showRunDialog.value = true
}

const confirmRunSuite = async () => {
  running.value = true
  try {
    await runTestSuite(currentRunningSuite.value.id, {
      use_ai: false, engine: runConfig.engine, browser: runConfig.browser, headless: runConfig.headless
    })
    ElMessage.success('执行已启动')
    showRunDialog.value = false
    await loadSuites()
    pollSuiteStatus(currentRunningSuite.value.id)
  } catch (e) {
    const msg = e.response?.data?.error || '执行失败'
    ElMessage.error(msg)
  } finally { running.value = false }
}

const pollSuiteStatus = (suiteId) => {
  let count = 0
  const iv = setInterval(async () => {
    count++
    try {
      await loadSuites()
      const s = suites.value.find(s => s.id === suiteId)
      if (s && s.execution_status !== 'running') {
        clearInterval(iv)
        if (s.execution_status === 'passed') ElMessage.success(`执行完成：全部通过 (${s.passed_count})`)
        else if (s.execution_status === 'failed') ElMessage.warning(`执行完成：通过${s.passed_count}，失败${s.failed_count}`)
      }
      if (count >= 120) { clearInterval(iv); ElMessage.info('执行时间较长，请稍后查看') }
    } catch (e) { clearInterval(iv) }
  }, 3000)
}

// ==================== 辅助方法 ====================
const formatDate = (row, col, val) => val ? new Date(val).toLocaleString() : ''
const getExecutionStatusTag = (s) => ({ not_run: 'info', passed: 'success', failed: 'danger', running: 'warning' }[s] || 'info')
const getExecutionStatusText = (s) => ({ not_run: '未执行', passed: '通过', failed: '失败', running: '执行中' }[s] || '未知')
const getPriorityTag = (p) => ({ high: 'danger', medium: 'warning', low: 'info' }[p] || 'info')
const getPriorityText = (p) => ({ high: '高', medium: '中', low: '低' }[p] || '未知')
const getStatusText = (s) => ({ normal: '正常', passed: '通过', failed: '失败', skipped: '跳过' }[s] || '未知')

// ==================== 初始化 ====================
onMounted(async () => {
  await loadProjects()
  if (projects.value.length > 0) {
    projectId.value = projects.value[0].id
    await loadSuites()
  }
})
</script>

<style scoped lang="scss">
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

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

.mode-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
}

/* 套件信息栏 */
.suite-info-bar {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: var(--radius-md, 8px);
  margin-bottom: 16px;

  .info-item {
    font-size: 13px;
    color: #606266;

    label {
      color: #909399;
      margin-right: 4px;
    }
  }
}

/* 套件内用例区域 */
.suite-cases-section {
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .section-title {
    font-size: 15px;
    font-weight: 600;
    color: #303133;
  }

  .section-actions {
    display: flex;
    align-items: center;
    gap: 4px;
  }
}

/* 状态标签 */
.status-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-sm, 6px);
  font-size: 12px;
  line-height: 20px;
  font-weight: 500;
}

.status-tag.status-normal { background: var(--info-bg, #edf5ff); color: var(--brand-700, #2558bf); }
.status-tag.status-passed { background: var(--success-bg, #ecfdf5); color: #059669; }
.status-tag.status-failed { background: var(--error-bg, #fef2f2); color: #dc2626; }
.status-tag.status-skipped { background: var(--warning-bg, #fef3c7); color: #d97706; }

/* ==================== 关联用例弹窗三栏布局 ==================== */
.associate-layout {
  display: flex;
  gap: 0;
  height: 420px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.associate-left {
  width: 180px;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;

  .panel-title {
    padding: 12px 14px;
    font-size: 13px;
    font-weight: 600;
    color: #303133;
    border-bottom: 1px solid #e4e7ed;
    background: #f8f9fa;
  }

  .tree-scroll {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
  }

  .tree-item {
    padding: 6px 14px;
    cursor: pointer;
    font-size: 13px;
    color: #606266;

    &:hover { background: #f5f7fa; }
    &.active { color: var(--brand-500, #4f8cff); font-weight: 600; background: #edf5ff; }
  }
}

.associate-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e4e7ed;

  .panel-title {
    padding: 12px 14px;
    font-size: 13px;
    font-weight: 600;
    color: #303133;
    border-bottom: 1px solid #e4e7ed;
    background: #f8f9fa;
    display: flex;
    align-items: center;
  }

  .panel-body {
    flex: 1;
    padding: 8px;
  }
}

.associate-right {
  width: 220px;
  display: flex;
  flex-direction: column;

  .panel-title {
    padding: 12px 14px;
    font-size: 13px;
    font-weight: 600;
    color: #303133;
    border-bottom: 1px solid #e4e7ed;
    background: #f8f9fa;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .panel-body {
    flex: 1;
    padding: 8px;
  }
}

/* 已添加行样式 */
:deep(.already-added-row) {
  background-color: #f5f5f5 !important;
  color: #c0c4cc;

  td { color: #c0c4cc; }
}
</style>
