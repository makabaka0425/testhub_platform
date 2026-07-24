<template>
  <div class="page-container">
    <!-- ==================== 套件列表视图 ==================== -->
    <template v-if="!currentSuite">
      <div class="page-titlebar">
        <h1 class="page-title">套件管理</h1>
        <div class="titlebar-actions">
          <el-select v-model="projectId" placeholder="选择项目" class="titlebar-select" @change="onProjectChange">
            <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
          </el-select>
          <el-button type="primary" size="small" @click="handleNewSuite">新增</el-button>
        </div>
      </div>

      <div class="workspace">
        <div class="list-column">
          <!-- 搜索区域卡片 -->
          <div class="filter-bar">
            <el-form :inline="true">
              <el-form-item label="套件名称">
                <el-input v-model="searchText" placeholder="搜索套件名称..." clearable @input="handleSearch" style="width: 200px">
                  <template #prefix><el-icon><Search /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item label="执行模式">
                <el-select v-model="filterExecutionMode" placeholder="全部" clearable style="width: 130px">
                  <el-option label="共享会话" value="shared_session" />
                  <el-option label="用例独立" value="per_case" />
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

          <!-- 套件列表面板 -->
          <section class="panel list-panel">
            <div class="panel__header">
              <span class="panel__title">套件列表</span>
            </div>

            <div class="panel__body suite-table-wrapper">
              <!-- 批量工具栏（选中状态） -->
              <div class="batch-toolbar" v-if="!batchEditMode && selectedSuites.length > 0">
                <span class="batch-count">已选 {{ selectedSuites.length }} 项</span>
                <el-button size="small" type="primary" @click="enterBatchEditMode">批量编辑</el-button>
                <el-button size="small" type="success" @click="batchRunSuites" :loading="batchRunLoading">批量运行</el-button>
                <el-button size="small" type="danger" plain @click="batchDeleteSuites">批量删除</el-button>
              </div>

              <!-- 批量编辑操作栏 -->
              <div class="batch-edit-bar" v-if="batchEditMode">
                <span class="batch-count">批量编辑模式：已选 {{ batchEditIds.length }} 项</span>
                <div class="batch-edit-actions">
                  <el-button size="small" @click="cancelBatchEdit">取消</el-button>
                  <el-button size="small" type="primary" @click="saveBatchEdit" :loading="batchEditLoading">保存</el-button>
                </div>
              </div>

              <div class="table-area">
              <el-table :data="filteredSuites" v-loading="loading" height="100%"
                row-key="id" ref="suiteTableRef" @selection-change="handleSuiteSelectionChange">
                <el-table-column v-if="!batchEditMode" type="selection" width="45" />
                <el-table-column prop="name" label="套件名称" min-width="200">
                  <template #default="{ row }">
                    <el-input v-if="isSuiteInBatchEdit(row)" v-model="row.name" size="small" placeholder="套件名称" />
                    <el-link v-else @click="enterSuiteDetail(row)" type="primary">{{ row.name }}</el-link>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="描述" min-width="160">
                  <template #default="{ row }">
                    <el-input v-if="isSuiteInBatchEdit(row)" v-model="row.description" size="small" placeholder="描述" />
                    <span v-else class="desc-text">{{ row.description || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="执行模式" width="150">
                  <template #default="{ row }">
                    <el-select v-if="isSuiteInBatchEdit(row)" v-model="row.execution_mode" size="small" style="width: 100%">
                      <el-option label="共享会话" value="shared_session" />
                      <el-option label="用例独立" value="per_case" />
                    </el-select>
                    <el-tag v-else size="small" :type="row.execution_mode === 'shared_session' ? 'success' : 'info'">
                      {{ row.execution_mode === 'shared_session' ? '共享会话' : '用例独立' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="登录配置" width="160">
                  <template #default="{ row }">
                    <el-select v-if="isSuiteInBatchEdit(row) && row.execution_mode === 'shared_session'"
                      v-model="row.login_config" size="small" clearable filterable placeholder="选择配置" style="width: 100%">
                      <el-option v-for="cfg in loginConfigs" :key="cfg.id" :label="cfg.name" :value="cfg.id" />
                    </el-select>
                    <span v-else-if="isSuiteInBatchEdit(row)" style="color: #909399; font-size: 12px">无需配置</span>
                    <span v-else-if="row.login_config_name">{{ row.login_config_name }}</span>
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
                <el-table-column prop="last_execution_time" label="执行时间" width="170" :formatter="formatDate" />
                <el-table-column prop="updated_at" label="更新时间" width="170" :formatter="formatDate" />
                <el-table-column label="操作" width="160" fixed="right" v-if="!batchEditMode">
                  <template #default="{ row }">
                    <ActionCell :actions="getSuiteActions(row)" :row="row" :max-visible="3" />
                  </template>
                </el-table-column>
              </el-table>
              </div>
            </div>

            <div class="pagination-container">
              <el-pagination v-model:current-page="pagination.currentPage" v-model:page-size="pagination.pageSize"
                :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next" :total="total"
                @size-change="handleSizeChange" @current-change="handleCurrentChange" />
            </div>
          </section>
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
        <span class="info-item" v-if="currentSuite.execution_mode === 'shared_session'"><label>登录配置：</label>{{ currentSuite.login_config_name || '未配置' }}</span>
        <span class="info-item" v-if="currentSuite.execution_mode === 'shared_session'"><label>执行后动作：</label>{{ currentSuite.default_post_action_display || '保持并刷新' }}</span>
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
        <el-table ref="suiteCasesTableRef" :data="filteredSuiteCases" height="100%" @selection-change="handleCaseSelectionChange" row-key="id">
          <el-table-column type="selection" width="45" />
          <el-table-column label="#" width="50" align="center">
            <template #default="{ $index }">
              <span class="drag-handle"><el-icon style="cursor: grab"><Rank /></el-icon></span>
            </template>
          </el-table-column>
          <el-table-column prop="test_case.name" label="用例名称" min-width="240" show-overflow-tooltip />
          <el-table-column label="优先级" width="80" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="getPriorityTag(row.test_case.priority)">{{ getPriorityText(row.test_case.priority) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <span class="status-tag" :class="`status-${row.test_case.suite_status || 'not_executed'}`">{{ getSuiteStatusText(row.test_case.suite_status) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="执行时长" width="100" align="center">
            <template #default="{ row }">
              <span v-if="row.test_case.suite_last_duration != null">{{ row.test_case.suite_last_duration.toFixed(2) }}s</span>
              <span v-else style="color: var(--gray-400)">-</span>
            </template>
          </el-table-column>
          <el-table-column label="执行时间" width="170" align="center">
            <template #default="{ row }">
              <span v-if="row.test_case.suite_last_finished">{{ formatDate(null, null, row.test_case.suite_last_finished) }}</span>
              <span v-else style="color: var(--gray-400)">-</span>
            </template>
          </el-table-column>
          <el-table-column v-if="currentSuite.execution_mode === 'shared_session'" label="执行后动作" width="150" align="center">
            <template #default="{ row }">
              <el-select v-model="row.post_action" size="small" placeholder="默认" clearable style="width: 120px" @change="handlePostActionChange(row)">
                <el-option label="默认" value="" />
                <el-option label="保持并刷新" value="refresh_page" />
                <el-option label="关闭页面" value="close_page" />
                <el-option label="维持当前状态" value="keep_state" />
              </el-select>
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
        <el-form-item v-if="editForm.execution_mode === 'shared_session'" label="执行后动作" prop="default_post_action">
          <el-select v-model="editForm.default_post_action" placeholder="请选择默认执行后动作" style="width: 100%">
            <el-option label="保持并刷新" value="refresh_page" />
            <el-option label="关闭页面" value="close_page" />
            <el-option label="维持当前状态" value="keep_state" />
          </el-select>
          <div class="mode-tip">用例执行完后的默认页面操作，用例级可单独覆盖</div>
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
            <el-table :data="filteredAssocCases" height="360" @select="handleAssocSelect" @select-all="handleAssocSelectAll"
              ref="assocTableRef" :row-class-name="getAssocRowClass">
              <el-table-column type="selection" width="40" :selectable="isCaseAlreadyAdded" />
              <el-table-column prop="name" label="用例名称" min-width="160" show-overflow-tooltip />
              <el-table-column label="状态" width="70" align="center">
                <template #default="{ row }">
                  <span class="status-tag" :class="`status-${row.status || 'normal'}`">{{ getStatusText(row.status) }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

          <div class="associate-right">
          <div class="panel-title">
            <span>已选 ({{ selectedAssocCases.length }})</span>
            <el-button size="small" text type="danger" @click="selectedAssocCases = []" :disabled="selectedAssocCases.length === 0">清空</el-button>
          </div>
          <div class="panel-body">
            <draggable
              v-model="selectedAssocCases"
              item-key="id"
              handle=".drag-handle"
              animation="200"
            >
              <template #item="{ element, index }">
                <div class="assoc-case-item">
                  <span class="drag-handle"><el-icon><Rank /></el-icon></span>
                  <span class="case-order">{{ index + 1 }}</span>
                  <span class="case-name">{{ element.name }}</span>
                  <el-icon class="remove-icon" @click="selectedAssocCases.splice(index, 1)"><Close /></el-icon>
                </div>
              </template>
            </draggable>
            <el-empty v-if="selectedAssocCases.length === 0" description="从左侧勾选用例" :image-size="50" />
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

    <!-- ==================== 执行记录弹窗 ==================== -->
    <el-dialog v-model="showRecordsDialog" :title="`执行记录 - ${recordsSuiteName}`" width="800px" :close-on-click-modal="false" class="suite-records-dialog">
      <div v-loading="recordsLoading" class="suite-records-body">
        <el-empty v-if="!recordsLoading && executionRecords.length === 0" description="暂无执行记录" :image-size="60" />
        <el-collapse v-model="expandedRecords" v-if="executionRecords.length > 0">
          <el-collapse-item v-for="record in executionRecords" :key="record.id" :name="record.id">
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
            <el-table :data="record.cases" size="small" style="width: 100%">
              <el-table-column type="index" label="#" width="45" />
              <el-table-column prop="test_case_name" label="用例名称" min-width="180" show-overflow-tooltip />
              <el-table-column label="状态" width="70" align="center">
                <template #default="{ row }">
                  <span class="status-tag" :class="`status-${row.status}`">{{ getCaseExecStatusText(row.status) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="时长" width="80" align="center">
                <template #default="{ row }">
                  <span v-if="row.execution_time">{{ row.execution_time.toFixed(2) }}s</span>
                  <span v-else style="color: #9ca3af">-</span>
                </template>
              </el-table-column>
              <el-table-column label="执行时间" width="160">
                <template #default="{ row }">
                  {{ formatRecordTime(row.started_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ row }">
                  <el-button link type="primary" size="small" @click="viewCaseExecDetail(row)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>
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
                        <template v-else>
                          步骤 {{ step.step_number }}
                        </template>
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
                        <span class="error-tag-inner">
                          <span>✕ {{ error.message }}</span>
                        </span>
                      </el-tag>
                      <span v-if="error.step_number" class="error-step">
                        步骤 {{ error.step_number }}
                      </span>
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
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, ArrowLeft, Close, Rank } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import Sortable from 'sortablejs'
import ActionCell from '@/components/ActionCell.vue'
import {
  getUiProjects, getTestSuites, createTestSuite, updateTestSuite, deleteTestSuite,
  getTestCases, getTestSuiteTestCases, addTestCasesToTestSuite,
  removeTestCaseFromTestSuite, removeTestCasesFromTestSuite,
  updateTestCaseOrder, runTestSuite, getLoginConfigs, getTestCaseGroupTree,
  batchUpdateTestSuites, getSuiteExecutionRecords, getTestCaseExecutionDetail,
  updateTestCasePostAction
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
const filterExecutionMode = ref('')
const filterExecutionStatus = ref('')
const total = ref(0)
const pagination = reactive({ currentPage: 1, pageSize: 20 })

// 前端过滤当前页数据（执行模式/执行状态）
const filteredSuites = computed(() => {
  let result = suites.value
  if (filterExecutionMode.value) {
    result = result.filter(s => s.execution_mode === filterExecutionMode.value)
  }
  if (filterExecutionStatus.value) {
    result = result.filter(s => s.execution_status === filterExecutionStatus.value)
  }
  return result
})

// ==================== 批量编辑 ====================
const selectedSuites = ref([])
const batchEditMode = ref(false)
const batchEditIds = ref([])
const batchEditBackup = ref({})
const batchEditLoading = ref(false)
const suiteTableRef = ref(null)

const loadProjects = async () => {
  try {
    const res = await getUiProjects({ page_size: 100 })
    projects.value = res.data.results || res.data
  } catch (e) { console.error(e) }
}

const loadSuites = async ({ silent = false } = {}) => {
  if (!projectId.value) { suites.value = []; total.value = 0; return }
  if (!silent) loading.value = true
  try {
    const res = await getTestSuites({
      project: projectId.value, page: pagination.currentPage,
      page_size: pagination.pageSize, search: searchText.value
    })
    suites.value = res.data.results || res.data
    total.value = res.data.count || res.data.length
  } catch (e) { console.error(e) } finally { if (!silent) loading.value = false }
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

const onProjectChange = async () => { if (batchEditMode.value) return; localStorage.setItem('lastProjectId', projectId.value); pagination.currentPage = 1; await loadSuites() }
const handleSearch = async () => { if (batchEditMode.value) return; pagination.currentPage = 1; await loadSuites() }
const handleSizeChange = async () => { if (batchEditMode.value) return; pagination.currentPage = 1; await loadSuites() }
const handleCurrentChange = async () => { if (batchEditMode.value) return; await loadSuites() }

// ==================== 批量编辑方法 ====================
const handleSuiteSelectionChange = (rows) => {
  if (batchEditMode.value) return
  selectedSuites.value = rows
}

const isSuiteInBatchEdit = (row) => {
  return batchEditMode.value && batchEditIds.value.includes(row.id)
}

const enterBatchEditMode = async () => {
  if (selectedSuites.value.length === 0) return
  batchEditIds.value = selectedSuites.value.map(s => s.id)
  const backup = {}
  for (const suite of suites.value) {
    if (batchEditIds.value.includes(suite.id)) {
      backup[suite.id] = {
        name: suite.name,
        description: suite.description,
        execution_mode: suite.execution_mode,
        login_config: suite.login_config
      }
    }
  }
  batchEditBackup.value = backup
  batchEditMode.value = true
  await loadLoginConfigs()
  nextTick(() => {
    if (suiteTableRef.value) suiteTableRef.value.clearSelection()
  })
}

const cancelBatchEdit = () => {
  for (const suite of suites.value) {
    if (batchEditIds.value.includes(suite.id)) {
      const bk = batchEditBackup.value[suite.id]
      if (bk) {
        suite.name = bk.name
        suite.description = bk.description
        suite.execution_mode = bk.execution_mode
        suite.login_config = bk.login_config
      }
    }
  }
  batchEditMode.value = false
  batchEditIds.value = []
  batchEditBackup.value = {}
  selectedSuites.value = []
}

const saveBatchEdit = async () => {
  for (const id of batchEditIds.value) {
    const suite = suites.value.find(s => s.id === id)
    if (!suite || !suite.name || !suite.name.trim()) {
      ElMessage.warning('套件名称不能为空')
      return
    }
  }

  const updates = []
  for (const id of batchEditIds.value) {
    const suite = suites.value.find(s => s.id === id)
    const bk = batchEditBackup.value[id]
    if (!suite || !bk) continue

    const item = { id }
    if (suite.name !== bk.name) item.name = suite.name
    if (suite.description !== bk.description) item.description = suite.description
    if (suite.execution_mode !== bk.execution_mode) {
      item.execution_mode = suite.execution_mode
      if (suite.execution_mode === 'per_case') item.login_config = null
    }
    if (suite.login_config !== bk.login_config) {
      item.login_config = suite.execution_mode === 'shared_session' ? suite.login_config : null
    }

    if (Object.keys(item).length > 1) updates.push(item)
  }

  if (updates.length === 0) {
    ElMessage.info('没有变更')
    batchEditMode.value = false
    batchEditIds.value = []
    batchEditBackup.value = {}
    selectedSuites.value = []
    return
  }

  batchEditLoading.value = true
  try {
    const res = await batchUpdateTestSuites({ updates })
    ElMessage.success(res.data.message || `成功更新 ${updates.length} 个套件`)
    batchEditMode.value = false
    batchEditIds.value = []
    batchEditBackup.value = {}
    selectedSuites.value = []
    await loadSuites()
  } catch (e) {
    console.error(e)
    ElMessage.error('批量更新失败')
  } finally {
    batchEditLoading.value = false
  }
}

// ==================== 新增/编辑套件（仅基础信息） ====================
const showEditDialog = ref(false)
const isEditing = ref(false)
const editingSuiteId = ref(null)
const saving = ref(false)
const editFormRef = ref(null)
const editForm = reactive({ name: '', description: '', execution_mode: 'per_case', login_config: null, default_post_action: 'refresh_page' })
const editFormRules = { name: [{ required: true, message: '请输入套件名称', trigger: 'blur' }] }

const handleNewSuite = async () => {
  isEditing.value = false
  editingSuiteId.value = null
  Object.assign(editForm, { name: '', description: '', execution_mode: 'per_case', login_config: null, default_post_action: 'refresh_page' })
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
    login_config: row.login_config || null,
    default_post_action: row.default_post_action || 'refresh_page'
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
      login_config: editForm.execution_mode === 'shared_session' ? editForm.login_config : null,
      default_post_action: editForm.execution_mode === 'shared_session' ? editForm.default_post_action : 'refresh_page'
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
const suiteCasesTableRef = ref(null)
let sortableInstance = null

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
  if (sortableInstance) { sortableInstance.destroy(); sortableInstance = null }
  currentSuite.value = null
  suiteCases.value = []
  suiteCaseSearch.value = ''
  selectedCaseIds.value = []
  loadSuites()
}

const loadSuiteCases = async ({ silent = false } = {}) => {
  if (!currentSuite.value) return
  try {
    const res = await getTestSuiteTestCases(currentSuite.value.id)
    suiteCases.value = res.data || []
    if (!silent) { await nextTick(); initSortable() }
  } catch (e) { console.error(e) }
}

// ==================== 套件用例拖拽排序 ====================
const initSortable = () => {
  if (sortableInstance) { sortableInstance.destroy(); sortableInstance = null }
  // 搜索状态下禁止拖拽（索引不对应原始数组）
  if (suiteCaseSearch.value) return
  const tableRef = suiteCasesTableRef.value
  if (!tableRef || !tableRef.$el) return
  const el = tableRef.$el.querySelector('.el-table__body-wrapper tbody')
  if (!el) return
  sortableInstance = Sortable.create(el, {
    handle: '.drag-handle',
    animation: 200,
    onEnd: async ({ oldIndex, newIndex }) => {
      if (oldIndex === newIndex) return
      // 更新本地数组顺序
      const list = [...suiteCases.value]
      const [moved] = list.splice(oldIndex, 1)
      list.splice(newIndex, 0, moved)
      suiteCases.value = list
      // 保存排序到后端
      await saveCaseOrder()
    }
  })
}

const saveCaseOrder = async () => {
  if (!currentSuite.value) return
  try {
    const orderData = suiteCases.value.map((c, idx) => ({
      test_case_id: c.test_case.id,
      order: idx
    }))
    await updateTestCaseOrder(currentSuite.value.id, orderData)
    ElMessage.success('顺序已保存')
  } catch (e) {
    console.error('保存排序失败:', e)
    ElMessage.error('保存排序失败')
  }
}

// 搜索关键词变化时重新初始化拖拽（搜索状态下禁用拖拽）
watch(suiteCaseSearch, () => {
  nextTick(() => initSortable())
})

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

// ==================== 执行后动作 ====================
const handlePostActionChange = async (row) => {
  try {
    await updateTestCasePostAction(currentSuite.value.id, row.id, row.post_action || '')
    ElMessage.success('执行后动作已更新')
  } catch (e) {
    console.error(e)
    ElMessage.error('更新失败')
  }
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

// 切换分组/搜索时回勾已选用例
watch(filteredAssocCases, () => {
  nextTick(() => restoreAssocSelection())
})

// 已在套件中的用例ID集合
const existingCaseIds = computed(() => new Set(suiteCases.value.map(c => c.test_case.id)))

const isCaseAlreadyAdded = (row) => {
  // 不可选：已在套件中且不在右侧选中列表中（右侧选中的行需要能回勾）
  return !(existingCaseIds.value.has(row.id) && !selectedAssocCases.value.some(c => c.id === row.id))
}

const getAssocRowClass = ({ row }) => {
  if (existingCaseIds.value.has(row.id)) return 'already-added-row'
  return ''
}

const handleGroupNodeClick = (data) => {
  assocGroupFilter.value = data.id
}

// 回勾中侧表格中已在右侧选中的行
const restoreAssocSelection = () => {
  const table = assocTableRef.value
  if (!table) return
  // 先清空所有勾选
  table.clearSelection()
  // 遍历当前可见行，勾选已在右侧的
  const selectedIds = new Set(selectedAssocCases.value.map(c => c.id))
  filteredAssocCases.value.forEach(row => {
    if (selectedIds.has(row.id)) {
      table.toggleRowSelection(row, true)
    }
  })
}

const handleAssocSelect = (selection, row) => {
  // 单行勾选/取消：判断该行是否在 selection 中
  const checked = selection.some(r => r.id === row.id)
  if (checked) {
    // 勾选：追加到右侧（如不存在）
    if (!selectedAssocCases.value.some(c => c.id === row.id)) {
      selectedAssocCases.value.push({ id: row.id, name: row.name, priority: row.priority, status: row.status })
    }
  } else {
    // 取消勾选：从右侧移除
    selectedAssocCases.value = selectedAssocCases.value.filter(c => c.id !== row.id)
  }
}

const handleAssocSelectAll = (selection) => {
  // 全选/全不选：对比当前可见的可选用例
  const visibleIds = filteredAssocCases.value.filter(r => isCaseAlreadyAdded(r)).map(r => r.id)
  if (selection.length > 0) {
    // 全选：追加所有可见且可选的用例
    for (const row of selection) {
      if (!selectedAssocCases.value.some(c => c.id === row.id)) {
        selectedAssocCases.value.push({ id: row.id, name: row.name, priority: row.priority, status: row.status })
      }
    }
  } else {
    // 全不选：移除当前可见的所有可选行
    selectedAssocCases.value = selectedAssocCases.value.filter(c => !visibleIds.includes(c.id))
  }
}

const confirmAssociate = async () => {
  if (selectedAssocCases.value.length === 0) return
  assocSaving.value = true
  try {
    await addTestCasesToTestSuite(currentSuite.value.id, {
      test_case_ids: selectedAssocCases.value.map(c => c.id)
    })
    // 保存关联时的排序顺序
    const orderData = selectedAssocCases.value.map((c, idx) => ({
      test_case_id: c.id,
      order: idx
    }))
    // 关联后重新加载，新用例会追加到末尾
    ElMessage.success(`成功关联 ${selectedAssocCases.value.length} 个用例`)
    showAssociateDialog.value = false
    selectedAssocCases.value = []
    await loadSuiteCases()
    // 同步更新 currentSuite 的用例计数，避免运行时仍判断为 0
    if (currentSuite.value) {
      currentSuite.value.test_case_count = suiteCases.value.length
    }
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
watch(showAssociateDialog, (val) => { if (val) onAssociateDialogOpen() })

// ==================== 批量删除套件 ====================
const batchDeleteSuites = async () => {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedSuites.value.length} 个套件？`, '提示', { type: 'warning' })
    let ok = 0, fail = 0
    for (const suite of selectedSuites.value) {
      try {
        await deleteTestSuite(suite.id)
        ok++
      } catch (e) { fail++; console.error(e) }
    }
    if (ok) ElMessage.success(`成功删除 ${ok} 个套件` + (fail ? `，${fail} 个失败` : ''))
    selectedSuites.value = []
    await loadSuites()
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

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

// ==================== 批量运行套件 ====================
const batchRunLoading = ref(false)

const batchRunSuites = async () => {
  const valid = selectedSuites.value.filter(s => s.test_case_count && s.test_case_count > 0)
  const empty = selectedSuites.value.length - valid.length
  if (valid.length === 0) {
    ElMessage.warning('选中的套件均未包含用例，无法执行')
    return
  }
  try {
    const tip = `确定批量运行 ${valid.length} 个套件？` + (empty ? `（${empty} 个套件无用例，将跳过）` : '')
    await ElMessageBox.confirm(tip, '批量运行', { type: 'info' })
  } catch (e) { return }

  batchRunLoading.value = true
  let ok = 0, fail = 0
  const runningIds = []
  for (const suite of valid) {
    try {
      await runTestSuite(suite.id, {
        use_ai: false, engine: 'playwright', browser: 'chrome', headless: false
      })
      runningIds.push(suite.id)
      ok++
    } catch (e) {
      fail++
      console.error(e)
    }
  }
  if (ok) ElMessage.success(`已启动 ${ok} 个套件执行` + (fail ? `，${fail} 个失败` : ''))
  batchRunLoading.value = false
  selectedSuites.value = []
  await loadSuites()
  if (runningIds.length > 0) pollBatchSuiteStatus(runningIds)
}

const pollSuiteStatus = (suiteId) => {
  let count = 0
  const iv = setInterval(async () => {
    count++
    try {
      await loadSuites({ silent: true })
      // 轮询期间持续刷新套件内用例列表（实时更新状态/时长/时间）
      if (currentSuite.value && currentSuite.value.id === suiteId) {
        await loadSuiteCases({ silent: true })
      }
      const s = suites.value.find(s => s.id === suiteId)
      if (s && s.execution_status !== 'running') {
        clearInterval(iv)
        if (s.execution_status === 'passed') ElMessage.success(`执行完成：全部通过 (${s.passed_count})`)
        else if (s.execution_status === 'failed') ElMessage.warning(`执行完成：通过${s.passed_count}，失败${s.failed_count}`)
        // 执行完成后最终刷新一次（静默，避免闪烁）
        if (currentSuite.value && currentSuite.value.id === suiteId) {
          await loadSuiteCases({ silent: true })
          await nextTick()
          initSortable()
        }
      }
      if (count >= 120) { clearInterval(iv); ElMessage.info('执行时间较长，请稍后查看') }
    } catch (e) { clearInterval(iv) }
  }, 3000)
}

// 批量轮询多个套件状态
const pollBatchSuiteStatus = (suiteIds) => {
  const pendingIds = new Set(suiteIds)
  let count = 0
  const iv = setInterval(async () => {
    count++
    try {
      await loadSuites({ silent: true })
      // 轮询期间持续刷新当前套件内用例列表
      if (currentSuite.value && pendingIds.has(currentSuite.value.id)) {
        await loadSuiteCases({ silent: true })
      }
      for (const id of [...pendingIds]) {
        const s = suites.value.find(s => s.id === id)
        if (s && s.execution_status !== 'running') {
          pendingIds.delete(id)
          if (s.execution_status === 'passed') ElMessage.success(`「${s.name}」执行完成：全部通过 (${s.passed_count})`)
          else if (s.execution_status === 'failed') ElMessage.warning(`「${s.name}」执行完成：通过${s.passed_count}，失败${s.failed_count}`)
          if (currentSuite.value && currentSuite.value.id === id) {
            await loadSuiteCases({ silent: true })
          }
        }
      }
      if (pendingIds.size === 0) {
        clearInterval(iv)
        ElMessage.success('全部套件执行完成')
        // 轮询结束后重新初始化拖拽排序
        await nextTick()
        initSortable()
      }
      if (count >= 120) { clearInterval(iv); ElMessage.info('执行时间较长，请稍后查看') }
    } catch (e) { clearInterval(iv) }
  }, 3000)
}

// ==================== 操作列 actions ====================
const getSuiteActions = (row) => [
  { key: 'edit', label: '编辑', onClick: (r) => editSuiteInfo(r) },
  { key: 'run', label: '运行', onClick: (r) => runSuite(r) },
  { key: 'records', label: '记录', onClick: (r) => viewSuiteRecords(r) },
  { key: 'delete', label: '删除', danger: true, onClick: (r) => deleteSuite(r.id) }
]

// ==================== 辅助方法 ====================
const formatDate = (row, col, val) => val ? new Date(val).toLocaleString() : ''
const getExecutionStatusTag = (s) => ({ not_run: 'info', passed: 'success', failed: 'danger', running: 'warning' }[s] || 'info')
const getExecutionStatusText = (s) => ({ not_run: '未执行', passed: '通过', failed: '失败', running: '执行中' }[s] || '未知')
const getPriorityTag = (p) => ({ high: 'danger', medium: 'warning', low: 'info' }[p] || 'info')
const getPriorityText = (p) => ({ high: '高', medium: '中', low: '低' }[p] || '未知')
const getStatusText = (s) => ({ normal: '正常', passed: '通过', failed: '失败', skipped: '跳过' }[s] || '未知')
const getSuiteStatusText = (s) => ({ not_executed: '未执行', passed: '通过', failed: '失败', skipped: '跳过' }[s] || '未执行')

// ==================== 执行记录弹窗 ====================
const showRecordsDialog = ref(false)
const recordsSuiteName = ref('')
const recordsSuiteId = ref(null)
const executionRecords = ref([])
const recordsLoading = ref(false)
const expandedRecords = ref([])
let recordsPollTimer = null

const refreshExecutionRecords = async () => {
  if (!recordsSuiteId.value) return
  try {
    const res = await getSuiteExecutionRecords(recordsSuiteId.value)
    executionRecords.value = res.data || []
  } catch (e) {
    // 静默失败，避免轮询期间弹错误提示
  }
}

const startRecordsPoll = () => {
  stopRecordsPoll()
  recordsPollTimer = setInterval(async () => {
    await refreshExecutionRecords()
    // 检查是否还有运行中的记录，没有则停止轮询
    const hasRunning = executionRecords.value.some(r => r.status === 'RUNNING' || r.status === 'PENDING')
    if (!hasRunning) {
      stopRecordsPoll()
    }
  }, 3000)
}

const stopRecordsPoll = () => {
  if (recordsPollTimer) {
    clearInterval(recordsPollTimer)
    recordsPollTimer = null
  }
}

const viewSuiteRecords = async (row) => {
  recordsSuiteName.value = row.name
  recordsSuiteId.value = row.id
  showRecordsDialog.value = true
  recordsLoading.value = true
  executionRecords.value = []
  expandedRecords.value = []
  stopRecordsPoll()
  try {
    const res = await getSuiteExecutionRecords(row.id)
    executionRecords.value = res.data || []
    // 如果有运行中的记录，启动轮询
    const hasRunning = executionRecords.value.some(r => r.status === 'RUNNING' || r.status === 'PENDING')
    if (hasRunning) {
      startRecordsPoll()
    }
  } catch (e) {
    console.error('获取执行记录失败:', e)
    ElMessage.error('获取执行记录失败')
  } finally {
    recordsLoading.value = false
  }
}

const getExecStatusText = (s) => ({ PENDING: '待执行', RUNNING: '运行中', SUCCESS: '成功', FAILED: '失败', ABORTED: '中止' }[s] || '未知')
const getCaseExecStatusText = (s) => ({ pending: '待执行', running: '运行中', passed: '通过', failed: '失败', skipped: '跳过', error: '错误' }[s] || '未知')
const getCaseExecTagType = (s) => ({ pending: 'info', running: 'warning', passed: 'success', failed: 'danger', skipped: 'warning', error: 'danger' }[s] || 'info')
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

// 从执行记录步骤日志中提取错误列表
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

// 从执行记录中提取SQL执行信息（统一处理套件和单用例两种格式）
const caseDetailSqlExecs = computed(() => {
  if (!caseDetailData.value || !caseDetailData.value.parsedLogs) return []
  const logs = caseDetailData.value.parsedLogs
  const result = []

  // 格式1：套件执行 - 独立的 precondition_sql / postcondition 对象
  if (!Array.isArray(logs)) {
    // 前置条件用例的SQL信息（独立模式下前置条件用例的SQL合并到了主用例日志中）
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
      try { logs = JSON.parse(logs) } catch { logs = null }
    }
    caseDetailData.value = {
      ...record,
      parsedLogs: logs
    }
  } catch (e) {
    console.error('获取执行详情失败:', e)
    ElMessage.error('获取执行详情失败')
  } finally {
    caseDetailLoading.value = false
  }
}

// ==================== 初始化 ====================
onMounted(async () => {
  await loadProjects()
  if (projects.value.length > 0) {
    const savedProjectId = localStorage.getItem('lastProjectId')
    const exists = savedProjectId && projects.value.some(p => p.id === Number(savedProjectId) || p.id === savedProjectId)
    projectId.value = exists ? (typeof projects.value[0].id === 'number' ? Number(savedProjectId) : savedProjectId) : projects.value[0].id
    await loadSuites()
  }
})

// 弹窗关闭时停止轮询
watch(showRecordsDialog, (val) => {
  if (!val) stopRecordsPoll()
})

onBeforeUnmount(() => {
  stopRecordsPoll()
})
</script>

<style scoped lang="scss">
/* ============================================================
   页面容器 / 标题栏 / 工作区（参照用例列表）
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

.suite-table-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.suite-table-wrapper .table-area {
  flex: 1;
  min-height: 0;
  overflow: hidden;
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
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    flex-shrink: 0;
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
.status-tag.status-not_executed { background: #f3f4f6; color: #9ca3af; }

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
  width: 240px;
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
    overflow-y: auto;
  }
}

.assoc-case-item {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  margin-bottom: 4px;
  border-radius: 4px;
  background: #f0f9eb;
  cursor: grab;
  font-size: 13px;
  transition: background 0.2s;

  &:hover { background: #e1f3d8; }

  .drag-handle {
    color: #c0c4cc;
    margin-right: 4px;
    flex-shrink: 0;
    cursor: grab;
    display: inline-flex;
    align-items: center;
  }

  .case-order {
    color: #909399;
    font-size: 12px;
    min-width: 20px;
    text-align: center;
    margin-right: 6px;
  }

  .case-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .remove-icon {
    color: #f56c6c;
    cursor: pointer;
    flex-shrink: 0;
    margin-left: 4px;

    &:hover { color: #dd2020; }
  }
}

/* 已添加行样式 */
:deep(.already-added-row) {
  background-color: #f5f5f5 !important;
  color: #c0c4cc;

  td { color: #c0c4cc; }
}

/* ==================== 批量编辑 ==================== */
.batch-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 6px;
  margin-bottom: 12px;

  .batch-count {
    font-size: 13px;
    color: #409eff;
    font-weight: 500;
  }
}

.batch-edit-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #fef0f0;
  border: 1px solid #fde2e2;
  border-radius: 6px;
  margin-bottom: 12px;

  .batch-count {
    font-size: 13px;
    color: #f56c6c;
    font-weight: 500;
  }

  .batch-edit-actions {
    display: flex;
    gap: 8px;
  }
}

/* 描述文本省略 */
.desc-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ==================== 执行记录弹窗 ==================== */
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

  .record-time {
    color: #606266;
  }

  .record-duration {
    color: #909399;
    font-size: 12px;
  }

  .record-stats {
    display: flex;
    gap: 8px;
    font-size: 12px;

    .stat-passed { color: #059669; }
    .stat-failed { color: #dc2626; }
    .stat-skipped { color: #d97706; }
  }

  .record-executor {
    color: #909399;
    font-size: 12px;
    margin-left: auto;
  }
}

/* ==================== 执行详情弹窗 ==================== */
.history-detail-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
.history-detail-header {
  flex-shrink: 0;
  margin-bottom: 16px;
}
.history-detail-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.history-detail-tabs :deep(.el-tabs) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.history-detail-tabs :deep(.el-tabs__header) {
  flex-shrink: 0;
  margin-bottom: 8px;
}
.history-detail-tabs :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
.history-detail-tabs :deep(.el-tab-pane) {
  height: 100%;
}
.history-detail-scroll {
  height: 100%;
  overflow-y: auto;
  padding-right: 8px;
}

.log-item {
  margin-bottom: 8px;
  padding: 8px 10px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 13px;

  .log-header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .log-action { color: #606266; font-weight: 500; }
  .log-desc { color: #909399; }
  .log-value { color: var(--brand-600, #409eff); font-size: 12px; font-weight: 500; background: var(--brand-50, #ecf5ff); padding: 1px 6px; border-radius: 3px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  .log-error {
    margin-top: 6px;
    padding: 6px 8px;
    background: #fef2f2;
    border-radius: 4px;

    .error-message {
      margin: 0;
      font-size: 12px;
      color: #dc2626;
      white-space: pre-wrap;
      word-break: break-all;
    }
  }
}

/* ==================== 错误信息页签样式 ==================== */
.errors-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.error-item {
  background: #fff;
  border: 2px solid #dc2626;
  border-radius: 8px;
  padding: 16px;

  .error-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f3f4f6;
    gap: 8px;

    .el-tag {
      font-size: 14px;
      padding: 8px 12px;
      font-weight: 600;
    }
  }

  .error-tag-inner {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .error-step {
    background: #fef2f2;
    color: #dc2626;
    padding: 4px 12px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 13px;
  }

  .error-meta {
    background: #f9fafb;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 12px;
  }

  .meta-item {
    display: flex;
    align-items: flex-start;
    margin-bottom: 8px;

    &:last-child { margin-bottom: 0; }
  }

  .meta-label {
    font-weight: 600;
    color: #6b7280;
    min-width: 80px;
    margin-right: 8px;
    font-size: 13px;
  }

  .meta-value {
    color: #111827;
    flex: 1;
    font-size: 13px;
    word-break: break-word;
  }

  .error-details {
    background: #2d2d2d;
    border-radius: 8px;
    overflow: hidden;

    .details-header {
      background: #1e1e1e;
      color: #fff;
      padding: 8px 12px;
      font-weight: 600;
      font-size: 13px;
      border-bottom: 1px solid #3d3d3d;
    }

    .details-content {
      color: #ff6b6b;
      padding: 12px;
      margin: 0;
      font-family: 'Courier New', Courier, monospace;
      font-size: 12px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-wrap: break-word;
      max-height: 400px;
      overflow-y: auto;

      &::-webkit-scrollbar { width: 6px; }
      &::-webkit-scrollbar-track { background: #1e1e1e; }
      &::-webkit-scrollbar-thumb { background: #555; border-radius: 3px; }
      &::-webkit-scrollbar-thumb:hover { background: #777; }
    }
  }
}

/* ==================== SQL执行页签样式 ==================== */
.sql-exec-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sql-exec-item {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px 16px;
}

.sql-exec-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.sql-affected {
  font-size: 12px;
  color: #6b7280;
}

.sql-exec-error {
  margin-bottom: 10px;

  .error-message {
    color: #dc2626;
    font-size: 12px;
    margin: 0;
    font-family: 'Courier New', Courier, monospace;
    white-space: pre-wrap;
    word-break: break-word;
  }
}

.sql-block {
  margin-bottom: 10px;
}

.sql-block-label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 4px;
}

.sql-code {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 10px 12px;
  border-radius: 6px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  max-height: 200px;
  overflow-y: auto;
}

.sql-code.sql-resolved {
  border-left: 3px solid #10b981;
}

.sql-details {
  margin-top: 8px;
}

.sql-details-label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 6px;
}

.sql-detail-row {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-bottom: 6px;
  padding: 6px 8px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #f3f4f6;
}

.sql-detail-status {
  font-weight: 700;
  flex-shrink: 0;

  &.ok { color: #10b981; }
  &.fail { color: #ef4444; }
}

.sql-detail-code {
  flex: 1;
  font-family: 'Courier New', Courier, monospace;
  font-size: 11px;
  color: #374151;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.sql-detail-affected {
  font-size: 11px;
  color: #6b7280;
  flex-shrink: 0;
  white-space: nowrap;
}

.sql-detail-error {
  font-size: 11px;
  color: #ef4444;
  flex-shrink: 0;
  max-width: 200px;
}
</style>

<style>
/* ==================== 执行记录弹窗 ==================== */
.el-dialog.suite-records-dialog {
  height: 680px !important;
  max-height: 680px !important;
  display: flex !important;
  flex-direction: column !important;
  box-sizing: border-box !important;
  margin-top: calc((100vh - 680px) / 2) !important;
}
.el-dialog.suite-records-dialog .el-dialog__header {
  flex-shrink: 0;
  margin: 0;
  padding-bottom: 12px;
}
.el-dialog.suite-records-dialog .el-dialog__body {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  padding-top: 0;
}
.el-dialog.suite-records-dialog .suite-records-body {
  height: 100%;
  overflow-y: auto;
}

/* ==================== 执行详情弹窗 ==================== */
.el-dialog.history-detail-dialog {
  height: 680px !important;
  max-height: 680px !important;
  display: flex !important;
  flex-direction: column !important;
  box-sizing: border-box !important;
  margin-top: calc((100vh - 680px) / 2) !important;
}
.el-dialog.history-detail-dialog .el-dialog__header {
  flex-shrink: 0;
  margin: 0;
  padding-bottom: 12px;
}
.el-dialog.history-detail-dialog .el-dialog__body {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  padding-top: 0;
  display: flex;
  flex-direction: column;
}
.el-dialog.history-detail-dialog .el-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.el-dialog.history-detail-dialog .el-tabs__header {
  flex-shrink: 0;
  margin-bottom: 8px;
}
.el-dialog.history-detail-dialog .el-tabs__content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
.el-dialog.history-detail-dialog .el-tab-pane {
  height: 100%;
}
</style>
