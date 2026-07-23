<template>
  <div class="page-container">
    <!-- 顶部标题栏 -->
    <div class="page-titlebar">
      <h1 class="page-title">{{ t('uiAutomation.testCase.title') }}</h1>
      <div class="titlebar-actions">
        <el-select v-model="selectedEngine" :placeholder="t('uiAutomation.testCase.selectEngine')" size="small" class="toolbar-select">
          <el-option label="Playwright" value="playwright" />
          <el-option label="Selenium" value="selenium" />
        </el-select>
        <el-select v-model="selectedBrowser" :placeholder="t('uiAutomation.testCase.selectBrowser')" size="small" class="toolbar-select">
          <el-option label="Chrome" value="chrome" />
          <el-option label="Firefox" value="firefox" />
          <el-option label="Safari" value="safari" />
          <el-option label="Edge" value="edge" />
        </el-select>
        <el-select v-model="headlessMode" :placeholder="t('uiAutomation.testCase.runModeLabel')" size="small" class="toolbar-select">
          <el-option :label="t('uiAutomation.testCase.headedMode')" :value="false" />
          <el-option :label="t('uiAutomation.testCase.headlessMode')" :value="true" />
        </el-select>
        <el-select v-model="projectId" :placeholder="t('uiAutomation.project.selectProject')" class="titlebar-select" @change="onProjectChange">
          <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
        <el-button type="primary" size="small" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          <span>新增</span>
        </el-button>
      </div>
    </div>

    <!-- 三栏工作区 -->
    <div class="workspace">
      <!-- 左侧：用例分组面板 -->
      <section class="panel group-panel">
        <div class="panel__header">
          <span class="panel__title">用例分组</span>
          <el-button text size="small" class="panel__action" @click="showCreateGroupDialog = true">
            <el-icon><Plus /></el-icon>
            <span>添加</span>
          </el-button>
        </div>
        <div class="panel__body group-tree-wrapper">
          <el-tree
            ref="groupTreeRef"
            :data="groupTreeWithAll"
            :props="{ children: 'children', label: 'name' }"
            node-key="id"
            :current-node-key="selectedGroupId === null ? '__all__' : selectedGroupId"
            :expand-on-click-node="false"
            :default-expanded-keys="groupExpandedKeys"
            highlight-current
            draggable
            :allow-drag="allowGroupDrag"
            :allow-drop="allowGroupDrop"
            @node-click="onGroupNodeClick"
            @node-contextmenu="onGroupRightClick"
            @node-drop="onGroupNodeDrop"
          >
            <template #default="{ node, data }">
              <div class="group-tree-node">
                <span class="group-node-label">{{ node.label }}</span>
                <span v-if="data.id !== '__all__'" class="group-count">{{ data.test_cases_count || 0 }}</span>
              </div>
            </template>
          </el-tree>
        </div>
      </section>

      <!-- 中间列：搜索区域 + 用例列表 -->
      <div class="list-column">
        <!-- 搜索区域卡片（参照元素管理页） -->
        <div class="filter-bar">
          <el-form :inline="true">
            <el-form-item label="用例名称">
              <el-input
                v-model="searchKeyword"
                :placeholder="t('uiAutomation.testCase.searchPlaceholder')"
                clearable
                style="width: 220px"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="searchStatus" placeholder="全部" clearable style="width: 130px">
                <el-option label="正常" value="normal" />
                <el-option label="通过" value="passed" />
                <el-option label="失败" value="failed" />
                <el-option label="跳过" value="skipped" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- 用例列表面板 -->
        <section class="panel list-panel">
          <div class="panel__header">
            <span class="panel__title">用例列表</span>
          </div>

        <div class="panel__body test-case-table-wrapper">
          <!-- 批量操作浮动工具栏 -->
          <transition name="batch-bar-slide">
            <div v-if="selectedCases.length > 0 && !batchEditMode" class="batch-toolbar">
              <span class="batch-toolbar__info">已选 {{ selectedCases.length }} 个用例</span>
              <div class="batch-toolbar__actions">
                <el-button size="small" :icon="Edit" @click="enterBatchEditMode">批量编辑名称</el-button>
                <el-button size="small" type="success" :icon="VideoPlay" @click="handleBatchRun" :loading="batchRunLoading">批量执行</el-button>
                <el-button size="small" :icon="FolderOpened" @click="openBatchUpdateGroupDialog">批量改分组</el-button>
                <el-button size="small" type="danger" :icon="DeleteFilled" @click="handleBatchDelete">批量删除</el-button>
                <el-button size="small" text @click="clearCaseSelection">取消选择</el-button>
              </div>
            </div>
          </transition>
          <!-- 批量编辑名称时的保存/取消条 -->
          <transition name="batch-bar-slide">
            <div v-if="batchEditMode" class="batch-edit-bar">
              <span class="batch-toolbar__info">正在批量编辑 {{ batchEditIds.length }} 个用例的名称，修改后点击保存</span>
              <div class="batch-toolbar__actions">
                <el-button size="small" type="primary" :icon="Check" @click="saveBatchEdit" :loading="batchEditLoading">保存修改</el-button>
                <el-button size="small" text @click="cancelBatchEdit">取消</el-button>
              </div>
            </div>
          </transition>
          <el-table
            ref="testCaseTableRef"
            :data="paginatedTestCases"
            size="small"
            @current-change="handleTableCurrentChange"
            @selection-change="handleCaseSelectionChange"
            :row-class-name="tableRowClassName"
            row-key="id"
          >
            <el-table-column type="selection" width="40" />
            <el-table-column prop="name" label="用例名称" min-width="280" show-overflow-tooltip>
              <template #default="{ row }">
                <el-input
                  v-if="batchEditMode && isCaseSelected(row)"
                  v-model="row.name"
                  size="small"
                  class="batch-name-input"
                  placeholder="用例名称"
                  @click.stop
                />
                <span v-else>{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column label="前置条件" min-width="180" align="left">
              <template #default="{ row }">
                <span v-if="!row.preconditions_data || row.preconditions_data.length === 0" class="precondition-empty">-</span>
                <el-tooltip v-else placement="top" :show-after="300">
                  <template #content>
                    <div v-for="pc in row.preconditions_data" :key="pc.id">{{ pc.order }}. {{ pc.name }}</div>
                  </template>
                  <span class="precondition-text">{{ row.preconditions_data.map(pc => pc.name).join(' · ') }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="步骤" width="100" align="center">
              <template #default="{ row }">
                <span class="step-count">{{ row.steps?.length || 0 }}</span>
              </template>
            </el-table-column>
            <el-table-column label="更新时间" width="150" align="left">
              <template #default="{ row }">
                <span class="update-time">{{ formatTime(row.updated_at) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="执行时间" width="150" align="left">
              <template #default="{ row }">
                <span v-if="row.last_execution_time" class="execution-time">{{ formatTime(row.last_execution_time) }}</span>
                <span v-else class="precondition-empty">-</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <span class="status-tag" :class="`status-${row.status || 'normal'}`">{{ getStatusText(row.status) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <ActionCell :actions="getCaseActions(row)" :row="row" :max-visible="3" />
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50]"
            :total="filteredTestCases.length"
            layout="total, sizes, prev, pager, next"
          />
        </div>
        </section>
      </div>

      <!-- 右侧：用例详情抽屉 -->
      <el-drawer
        v-model="detailDrawerVisible"
        :with-header="false"
        :size="detailDrawerSize"
        direction="rtl"
        :modal="false"
        :append-to-body="false"
        modal-class="detail-drawer-overlay"
        :class="['detail-drawer', { 'detail-drawer--collapsed': detailCollapsed }]"
      >
        <div class="detail-toggle" @click="toggleDetailCollapse" :title="detailCollapsed ? '展开详情' : '收起详情'">
          <span class="detail-toggle__btn">
            <el-icon><component :is="detailCollapsed ? 'CaretLeft' : 'CaretRight'" /></el-icon>
          </span>
        </div>
        <div class="detail-resizer" v-show="!detailCollapsed" @mousedown="startResize"></div>
        <div class="detail-drawer-body" v-show="!detailCollapsed">
          <div class="panel__header">
            <span class="panel__title">用例详情</span>
            <div v-if="selectedTestCase" class="detail-header-actions">
              <el-button size="small" @click="(executionResult && !showSteps) ? toggleView() : addStep()">
                <el-icon><Plus v-if="!executionResult || showSteps" /><Edit v-else /></el-icon>
                {{ (executionResult && !showSteps) ? '编辑步骤' : t('uiAutomation.testCase.addStep') }}
              </el-button>
              <el-button size="small" type="primary" @click="saveTestCase">
                <el-icon><Check /></el-icon>
                {{ t('uiAutomation.testCase.saveTestCase') }}
              </el-button>
              <el-button size="small" type="success" @click="runTestCase(selectedTestCase)">
                <el-icon><VideoPlay /></el-icon>
                {{ lastRunCaseId === selectedTestCase.id ? '重新运行' : '运行' }}
              </el-button>
              <el-button size="small" @click="closeDetailDrawer">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>
          <div class="panel__body detail-body">
            <div v-if="selectedTestCase" class="test-case-detail">

            <!-- 测试步骤编辑 -->
            <div class="steps-container" v-show="showSteps">
              <!-- 前置条件 -->
              <div class="condition-section precondition-section">
                <div class="section-header" @click="showPreconditions = !showPreconditions">
                  <h4>前置条件</h4>
                  <el-icon><component :is="showPreconditions ? 'ArrowUp' : 'ArrowDown'" /></el-icon>
                </div>
                <div v-if="showPreconditions" class="section-content">
                  <el-tree-select
                    v-model="selectedPreconditions"
                    multiple
                    filterable
                    :data="preconditionTreeData"
                    :props="{ children: 'children', label: 'name', value: 'id', disabled: 'disabled' }"
                    node-key="id"
                    placeholder="选择前置条件用例（按选择顺序执行）"
                    style="width: 100%"
                    size="small"
                    check-strictly
                    :render-after-expand="false"
                  />
                  <div class="section-tip">单用例执行时自动先执行，套件执行时忽略</div>
                </div>
              </div>

              <div class="steps-header" @click="showTestSteps = !showTestSteps">
                <h4>{{ t('uiAutomation.testCase.testSteps') }}</h4>
                <div class="steps-header-actions">
                  <el-button size="small" text @click.stop="expandAllSteps">
                    {{ allStepsExpanded ? t('uiAutomation.testCase.foldAll') : t('uiAutomation.testCase.expandAll') }}
                  </el-button>
                  <el-icon><component :is="showTestSteps ? 'ArrowUp' : 'ArrowDown'" /></el-icon>
                </div>
              </div>

              <div class="steps-scroll-container" v-show="showTestSteps">
                <div class="steps-list">
                  <draggable
                    v-model="currentSteps"
                    item-key="id"
                    handle=".drag-handle"
                    @change="onStepsReorder"
                  >
                    <template #item="{ element, index }">
                      <div class="step-card" :class="{ expanded: element.expanded }">
                        <div class="step-header">
                          <div class="step-left">
                            <el-icon class="drag-handle"><Rank /></el-icon>
                            <span class="step-number">{{ index + 1 }}.</span>
                            <span
                              class="step-desc-text"
                              @click="element.expanded = !element.expanded"
                            >{{ element.description || getStepPlaceholder(element) }}</span>
                          </div>
                          <div class="step-right">
                            <el-button
                              size="small"
                              text
                              @click="element.expanded = !element.expanded"
                            >
                              <el-icon>
                                <component :is="element.expanded ? 'ArrowUp' : 'ArrowDown'" />
                              </el-icon>
                            </el-button>
                            <el-button size="small" text type="danger" @click="removeStep(index)">
                              <el-icon><Delete /></el-icon>
                            </el-button>
                          </div>
                        </div>

                        <div v-if="element.expanded" class="step-content">
                          <!-- 操作类型 -->
                          <div class="step-param">
                            <label>操作类型</label>
                            <el-select
                              v-model="element.action_type"
                              :placeholder="t('uiAutomation.testCase.selectAction')"
                              size="small"
                              class="step-input"
                              @change="onActionTypeChange(element)"
                            >
                              <el-option :label="t('uiAutomation.testCase.actionClick')" value="click" />
                              <el-option :label="t('uiAutomation.testCase.actionFill')" value="fill" />
                              <el-option label="选择下拉选项" value="select" />
                              <el-option :label="t('uiAutomation.testCase.actionGetText')" value="getText" />
                              <el-option :label="t('uiAutomation.testCase.actionWaitFor')" value="waitFor" />
                              <el-option :label="t('uiAutomation.testCase.actionHover')" value="hover" />
                              <el-option :label="t('uiAutomation.testCase.actionScroll')" value="scroll" />
                              <el-option :label="t('uiAutomation.testCase.actionScreenshot')" value="screenshot" />
                              <el-option :label="t('uiAutomation.testCase.actionAssert')" value="assert" />
                              <el-option :label="t('uiAutomation.testCase.actionWait')" value="wait" />
                              <el-option :label="t('uiAutomation.testCase.actionSwitchTab')" value="switchTab" />
                              <el-option label="路由跳转" value="navigate" />
                            </el-select>
                          </div>

                          <!-- 元素选择 -->
                          <div v-if="needsElement(element.action_type, element.assert_type)" class="step-param">
                            <label>操作元素</label>
                            <div class="step-input-group">
                              <el-tree-select
                                v-model="element.element_id"
                                :data="elementTreeData"
                                :props="elementTreeProps"
                                node-key="id"
                                :placeholder="t('uiAutomation.testCase.selectElement')"
                                size="small"
                                class="step-input"
                                check-strictly
                                :render-after-expand="false"
                                @change="onElementChange(element)"
                              >
                                <template #default="{ node, data }">
                                  <div class="element-tree-node">
                                    <span class="element-tree-node-label">{{ node.label }}</span>
                                    <span v-if="data.type === 'element'" class="element-type-tag" :class="data.element_type?.toLowerCase()">
                                      {{ getElementTypeLabel(data.element_type) }}
                                    </span>
                                  </div>
                                </template>
                              </el-tree-select>
                              <el-input
                                :model-value="getElementDescription(element.element_id)"
                                placeholder="元素描述"
                                size="small"
                                class="step-input"
                                readonly
                              />
                            </div>
                          </div>

                          <!-- 输入参数 -->
                          <div v-if="needsInputValue(element.action_type)" class="step-param">
                            <label>{{ t('uiAutomation.testCase.inputValue') }}</label>
                            <div class="step-input-group">
                              <el-input
                                v-model="element.input_value"
                                :placeholder="element.action_type === 'select' ? '选项文本，多个用逗号分隔' : element.action_type === 'switchTab' ? t('uiAutomation.testCase.switchTabPlaceholder') : element.action_type === 'navigate' ? '输入路由路径，如 /user/list' : t('uiAutomation.testCase.inputPlaceholder')"
                                size="small"
                                class="step-input"
                              >
                                <template #append>
                                  <el-button
                                    size="small"
                                    :icon="MagicStick"
                                    @click="openDataFactorySelector(element, 'input_value')"
                                    :title="t('uiAutomation.testCase.referenceDataFactory')"
                                    class="data-factory-btn"
                                  />
                                </template>
                              </el-input>
                              <el-tooltip :content="t('uiAutomation.testCase.insertVariable')" placement="top" v-if="!['switchTab', 'navigate'].includes(element.action_type)">
                                <el-button size="small" @click="openVariableHelper(element, 'input_value')" class="variable-helper-btn">
                                  <el-icon><MagicStick /></el-icon>
                                </el-button>
                              </el-tooltip>
                            </div>
                          </div>

                          <!-- 输出变量名 -->
                          <div v-if="['fill', 'getText', 'select'].includes(element.action_type)" class="step-param">
                            <label>输出变量</label>
                            <el-input
                              v-model="element.output_var"
                              placeholder="输出变量名"
                              size="small"
                              class="step-input"
                            />
                          </div>

                          <!-- 等待时间 -->
                          <div v-if="needsWaitTime(element.action_type)" class="step-param">
                            <label>{{ t('uiAutomation.testCase.waitTime') }}</label>
                            <el-input-number
                              v-model="element.wait_time"
                              :min="100"
                              :max="30000"
                              :step="100"
                              size="small"
                            />
                          </div>

                          <!-- 操作后等待 -->
                          <div v-if="needsActionWait(element.action_type)" class="step-param">
                            <label>操作后等待(秒)</label>
                            <el-input-number
                              v-model="element.action_wait"
                              :min="0"
                              :max="60"
                              :step="1"
                              size="small"
                              placeholder="0"
                            />
                          </div>

                          <!-- 断言参数 -->
                          <div v-if="element.action_type === 'assert'" class="step-param">
                            <label>{{ t('uiAutomation.testCase.assertType') }}</label>
                            <div class="step-input-group step-input-group--col">
                              <el-select v-model="element.assert_type" size="small" class="step-input">
                                <el-option :label="t('uiAutomation.testCase.assertTextContains')" value="textContains" />
                                <el-option :label="t('uiAutomation.testCase.assertTextEquals')" value="textEquals" />
                                <el-option :label="t('uiAutomation.testCase.assertIsVisible')" value="isVisible" />
                                <el-option :label="t('uiAutomation.testCase.assertExists')" value="exists" />
                                <el-option :label="t('uiAutomation.testCase.assertHasAttribute')" value="hasAttribute" />
                                <el-option label="表格包含文本" value="tableContains" />
                                <el-option label="表格不包含文本" value="tableNotContains" />
                                <el-option label="表格为空" value="tableEmpty" />
                              </el-select>
                              <div v-if="element.assert_type !== 'tableEmpty'" class="assert-value-row">
                                <el-input
                                  v-model="element.assert_value"
                                  :placeholder="t('uiAutomation.testCase.expectedValue')"
                                  size="small"
                                  class="step-input"
                                >
                                  <template #append>
                                    <el-button
                                      size="small"
                                      :icon="MagicStick"
                                      @click="openDataFactorySelector(element, 'assert_value')"
                                      :title="t('uiAutomation.testCase.referenceDataFactory')"
                                      class="data-factory-btn"
                                    />
                                  </template>
                                </el-input>
                                <el-tooltip :content="t('uiAutomation.testCase.insertVariable')" placement="top">
                                  <el-button size="small" @click="openVariableHelper(element, 'assert_value')" class="variable-helper-btn">
                                    <el-icon><MagicStick /></el-icon>
                                  </el-button>
                                </el-tooltip>
                              </div>
                            </div>
                          </div>

                          <!-- 步骤描述 -->
                          <div class="step-param">
                            <label>{{ t('uiAutomation.testCase.stepDescription') }}</label>
                            <el-input
                              v-model="element.description"
                              :placeholder="getStepPlaceholder(element)"
                              size="small"
                              class="step-input"
                            />
                          </div>
                        </div>
                      </div>
                    </template>
                  </draggable>
                </div>
              </div>

              <!-- 前置数据SQL -->
              <div class="condition-section precondition-sql-section">
                <div class="section-header" @click="showPreconditionSql = !showPreconditionSql">
                  <h4>前置数据SQL</h4>
                  <el-icon><component :is="showPreconditionSql ? 'ArrowUp' : 'ArrowDown'" /></el-icon>
                </div>
                <div v-if="showPreconditionSql" class="section-content">
                  <el-input
                    v-model="preconditionSql"
                    type="textarea"
                    :rows="3"
                    size="small"
                    placeholder="用例执行前自动执行的数据准备SQL，多条用分号分隔&#10;例如：INSERT INTO users (username, password) VALUES ('${username}', '123456');&#10;支持 INSERT/UPDATE/DELETE，仅禁止 DROP，可用 ${变量名} 引用变量"
                  />
                  <div class="section-tip">在登录和步骤执行前执行，始终运行（套件/计划中也不例外）；需先在项目配置中设置数据库连接</div>
                </div>
              </div>

              <!-- 后置清理SQL -->
              <div class="condition-section postcondition-section">
                <div class="section-header" @click="showPostcondition = !showPostcondition">
                  <h4>后置清理SQL</h4>
                  <el-icon><component :is="showPostcondition ? 'ArrowUp' : 'ArrowDown'" /></el-icon>
                </div>
                <div v-if="showPostcondition" class="section-content">
                  <el-input
                    v-model="postconditionSql"
                    type="textarea"
                    :rows="3"
                    size="small"
                    placeholder="用例执行完自动执行的清理SQL，多条用分号分隔&#10;例如：DELETE FROM users WHERE username='${username}';&#10;仅支持 DELETE/UPDATE/TRUNCATE，可用 ${变量名} 引用步骤输出变量"
                  />
                  <div class="section-tip">需先在项目配置中设置数据库连接</div>
                </div>
              </div>
            </div>

            <!-- 执行结果 -->
            <div v-if="executionResult" class="execution-result" v-show="!showSteps">
              <div class="result-header">
                <h4>{{ t('uiAutomation.testCase.executionResult') }}</h4>
                <el-tag :type="executionResult.status === 'passed' ? 'success' : executionResult.status === 'skipped' ? 'warning' : 'danger'">
                  {{ executionResult.status === 'passed' ? t('uiAutomation.testCase.executionSuccess') : executionResult.status === 'skipped' ? '跳过' : t('uiAutomation.testCase.executionFailed') }}
                </el-tag>
              </div>
              <div class="result-content">
                <el-tabs v-model="resultActiveTab">
                  <el-tab-pane :label="t('uiAutomation.testCase.executionLogs')" name="logs">
                    <div class="logs-container">
                      <div v-if="parsedExecutionLogs.length > 0">
                        <div v-for="(step, index) in parsedExecutionLogs" :key="index" class="log-item">
                          <div class="log-header">
                            <el-tag :type="step.success ? 'success' : 'danger'" size="small">
                                <template v-if="step.step_number === 'sql'">
                                 <span style="display: inline-flex; align-items: center; gap: 4px;"><el-icon style="font-size: 14px;"><Coin /></el-icon> SQL</span>
                               </template>
                              <template v-else>
                                {{ t('uiAutomation.testCase.step') }} {{ step.step_number }}
                              </template>
                            </el-tag>
                            <span class="log-action">{{ step.action_type === 'precondition_sql' ? '前置数据SQL' : step.action_type === 'postcondition_sql' ? '后置清理SQL' : getActionText(step.action_type) }}</span>
                            <span class="log-desc">{{ step.description }}</span>
                            <span v-if="step.input_value" class="log-value">"{{ step.input_value }}"</span>
                          </div>
                          <div v-if="step.error" class="log-error">
                            <el-icon><WarningFilled /></el-icon>
                            <pre class="error-message">{{ step.error }}</pre>
                          </div>
                        </div>
                      </div>
                      <el-empty v-if="!parsedExecutionLogs.length" :description="t('uiAutomation.testCase.noLogs')" />
                    </div>
                  </el-tab-pane>
                  <el-tab-pane :label="t('uiAutomation.testCase.failedScreenshots')" name="screenshots" v-if="executionResult.screenshots && executionResult.screenshots.length > 0">
                    <div class="screenshots-container">
                      <div
                        v-for="(screenshot, index) in executionResult.screenshots"
                        :key="index"
                        class="screenshot-item"
                        @click="previewScreenshot(screenshot)"
                      >
                        <div class="screenshot-wrapper">
                          <img
                            :src="screenshot.url"
                            :alt="`${t('uiAutomation.testCase.screenshot')} ${index + 1}`"
                            :data-index="index"
                            @error="handleImageError"
                            @load="handleImageLoad"
                          />
                          <div class="screenshot-placeholder" v-if="!screenshot.loaded">
                            <el-icon><Picture /></el-icon>
                            <span>{{ t('uiAutomation.testCase.loadingImage') }}</span>
                          </div>
                          <div class="screenshot-error" v-if="screenshot.error">
                            <el-icon><Warning /></el-icon>
                            <span>{{ t('uiAutomation.testCase.imageLoadFailed') }}</span>
                          </div>
                          <div class="screenshot-overlay">
                            <el-icon class="zoom-icon"><ZoomIn /></el-icon>
                          </div>
                        </div>
                        <div class="screenshot-info">
                          <p class="screenshot-description">{{ screenshot.description || t('uiAutomation.testCase.screenshot') + ' ' + (index + 1) }}</p>
                          <p class="screenshot-meta" v-if="screenshot.step_number">{{ t('uiAutomation.testCase.step') }} {{ screenshot.step_number }}</p>
                          <p class="screenshot-time" v-if="screenshot.timestamp">{{ formatTime(screenshot.timestamp) }}</p>
                        </div>
                      </div>
                    </div>
                  </el-tab-pane>
                  <el-tab-pane :label="t('uiAutomation.testCase.errorInfo')" name="errors" v-if="executionResult.errors && executionResult.errors.length > 0">
                    <div class="errors-container">
                      <div
                        v-for="(error, index) in executionResult.errors"
                        :key="index"
                        class="error-item"
                      >
                        <div class="error-header">
                          <el-tag type="danger" size="large">
                            <span class="error-tag-inner">
                              <el-icon><WarningFilled /></el-icon>
                              <span>{{ error.message || error }}</span>
                            </span>
                          </el-tag>
                          <span v-if="error.step_number" class="error-step">
                            {{ t('uiAutomation.testCase.step') }} {{ error.step_number }}
                          </span>
                        </div>

                        <div v-if="error.action_type || error.element || error.description" class="error-meta">
                          <div v-if="error.action_type" class="meta-item">
                            <span class="meta-label">{{ t('uiAutomation.testCase.operationType') }}</span>
                            <span class="meta-value">{{ error.action_type }}</span>
                          </div>
                          <div v-if="error.element" class="meta-item">
                            <span class="meta-label">{{ t('uiAutomation.testCase.targetElement') }}</span>
                            <span class="meta-value">{{ error.element }}</span>
                          </div>
                          <div v-if="error.description" class="meta-item">
                            <span class="meta-label">{{ t('uiAutomation.testCase.stepDesc') }}</span>
                            <span class="meta-value">{{ error.description }}</span>
                          </div>
                        </div>

                        <div v-if="error.details || error.stack" class="error-details">
                          <div class="details-header">{{ t('uiAutomation.testCase.detailErrorInfo') }}</div>
                          <pre class="details-content">{{ error.details || error.stack }}</pre>
                        </div>
                      </div>
                    </div>
                  </el-tab-pane>
                </el-tabs>
              </div>
            </div>
          </div>

          <div v-else class="no-selection">
            <el-empty :description="t('uiAutomation.testCase.selectTestCase')" />
          </div>
          </div>
        </div>
      </el-drawer>
    </div>

    <!-- 新建/编辑测试用例对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingTestCase ? t('uiAutomation.testCase.editTestCase') : t('uiAutomation.testCase.createTestCase')"
      :close-on-click-modal="false"
      width="650px"
    >
      <el-form :model="testCaseForm" label-width="100px">
        <el-form-item :label="t('uiAutomation.testCase.caseName')" required>
          <el-input v-model="testCaseForm.name" :placeholder="t('uiAutomation.testCase.caseNamePlaceholder')" />
        </el-form-item>
        <el-form-item label="所属分组">
          <el-tree-select
            v-model="testCaseForm.group"
            :data="groupTreeSelectData"
            :props="{ children: 'children', label: 'name', value: 'id' }"
            placeholder="不选择则为未分组"
            clearable
            check-strictly
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('uiAutomation.testCase.caseDescription')">
          <el-input
            v-model="testCaseForm.description"
            type="textarea"
            :rows="3"
            :placeholder="t('uiAutomation.testCase.caseDescPlaceholder')"
          />
        </el-form-item>
        <el-form-item :label="t('uiAutomation.testCase.priority')">
          <el-select v-model="testCaseForm.priority" style="width: 100%">
            <el-option :label="t('uiAutomation.testCase.priorityHigh')" value="high" />
            <el-option :label="t('uiAutomation.testCase.priorityMedium')" value="medium" />
            <el-option :label="t('uiAutomation.testCase.priorityLow')" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="前置条件">
          <el-tree-select
            v-model="testCaseForm.preconditions"
            multiple
            filterable
            :data="preconditionTreeData"
            :props="{ children: 'children', label: 'name', value: 'id', disabled: 'disabled' }"
            node-key="id"
            placeholder="选择前置条件用例（按选择顺序执行）"
            style="width: 100%"
            check-strictly
            :render-after-expand="false"
          />
          <div style="color: var(--gray-500); font-size: 12px; margin-top: 4px;">
            前置条件在单用例执行时自动先执行，套件执行时忽略
          </div>
        </el-form-item>
        <el-form-item label="前置数据SQL">
          <el-input
            v-model="testCaseForm.precondition_sql"
            type="textarea"
            :rows="4"
            placeholder="用例执行前自动执行的数据准备SQL，多条用分号分隔&#10;例如：INSERT INTO users (username, password) VALUES ('${username}', '123456');&#10;支持 INSERT/UPDATE/DELETE，仅禁止 DROP，可用 ${变量名} 引用变量"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            在登录和步骤执行前执行，始终运行；需先在项目配置中设置数据库连接
          </div>
        </el-form-item>
        <el-form-item label="后置清理SQL">
          <el-input
            v-model="testCaseForm.postcondition_sql"
            type="textarea"
            :rows="4"
            placeholder="用例执行后自动执行的清理SQL，多条用分号分隔&#10;例如：DELETE FROM users WHERE username='${username}';&#10;仅支持 DELETE/UPDATE/TRUNCATE 语句，可用 ${变量名} 引用步骤输出变量"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            需先在项目配置中设置数据库连接，支持 ${变量名} 引用步骤输出变量
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">{{ t('uiAutomation.common.cancel') }}</el-button>
          <el-button type="primary" @click="saveTestCaseForm">{{ t('uiAutomation.common.confirm') }}</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 分组创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateGroupDialog"
      :title="editingGroup ? '编辑分组' : '新增分组'"
      width="450px"
      :close-on-click-modal="false"
    >
      <el-form :model="groupForm" label-width="80px">
        <el-form-item label="分组名称" required>
          <el-input v-model="groupForm.name" placeholder="请输入分组名称" />
        </el-form-item>
        <el-form-item label="父分组">
          <el-tree-select
            v-model="groupForm.parent_group"
            :data="groupTreeSelectData"
            :props="{ children: 'children', label: 'name', value: 'id' }"
            placeholder="无（顶级分组）"
            clearable
            check-strictly
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="groupForm.description" type="textarea" :rows="2" placeholder="分组描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateGroupDialog = false">取消</el-button>
        <el-button type="primary" @click="saveGroupForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量修改分组弹窗 -->
    <el-dialog
      v-model="showBatchGroupDialog"
      title="批量修改分组"
      width="420px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-alert
        v-if="selectedCases.length > 0"
        :title="`将以下 ${selectedCases.length} 个用例移动到新的分组`"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />
      <el-form label-position="right" label-width="80px">
        <el-form-item label="目标分组">
          <el-tree-select
            v-model="batchTargetGroupId"
            :data="groupTreeSelectData"
            :props="{ children: 'children', label: 'name', value: 'id' }"
            node-key="id"
            placeholder="选择分组（留空移到未分组）"
            check-strictly
            :render-after-expand="false"
            clearable
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchGroupDialog = false">取消</el-button>
        <el-button type="primary" :loading="batchLoading" @click="handleBatchUpdateGroup">确认修改</el-button>
      </template>
    </el-dialog>

    <!-- 分组右键菜单 -->
    <div v-if="showGroupContextMenu" class="group-context-menu" :style="{ left: groupContextMenuX + 'px', top: groupContextMenuY + 'px' }">
      <div class="context-menu-item" @click="editGroupNode">编辑</div>
      <div class="context-menu-item" @click="addSubGroup">新增子分组</div>
      <div class="context-menu-item danger" @click="deleteGroupNode">删除</div>
    </div>

    <!-- 截图预览对话框 -->
    <el-dialog
      v-model="showScreenshotPreview"
      :title="t('uiAutomation.testCase.screenshotPreview')"
      width="80%"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :modal="true"
      :destroy-on-close="false"
    >
      <div v-if="currentScreenshot" class="screenshot-preview">
        <div class="preview-info">
          <h4>{{ currentScreenshot.description }}</h4>
          <p v-if="currentScreenshot.step_number">{{ t('uiAutomation.testCase.failedStep') }}: {{ t('uiAutomation.testCase.step') }} {{ currentScreenshot.step_number }}</p>
          <p v-if="currentScreenshot.timestamp">{{ t('uiAutomation.testCase.screenshotTime') }}: {{ formatTime(currentScreenshot.timestamp) }}</p>
        </div>
        <div class="preview-image">
          <img :src="currentScreenshot.url" :alt="currentScreenshot.description" />
        </div>
      </div>
    </el-dialog>

    <!-- 变量助手对话框 -->
    <el-dialog
      :close-on-press-escape="false"
      :modal="true"
      :destroy-on-close="false"
      v-model="showVariableHelper"
      :title="t('uiAutomation.testCase.variableHelper')"
      :close-on-click-modal="false"
      width="900px"
    >
      <el-tabs tab-position="left" style="height: 450px">
        <el-tab-pane
          v-for="(category, index) in variableCategoriesComputed"
          :key="index"
          :label="category.label"
        >
          <div style="height: 450px; overflow-y: auto; padding: 10px;">
            <el-table :data="category.variables" style="width: 100%" @row-click="insertVariable" highlight-current-row>
              <el-table-column prop="name" :label="t('uiAutomation.testCase.functionName')" width="150" show-overflow-tooltip>
                <template #default="{ row }">
                  <el-tag size="small">{{ row.name }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="desc" :label="t('uiAutomation.testCase.description')" min-width="150" />
              <el-table-column prop="syntax" :label="t('uiAutomation.testCase.syntax')" min-width="200" show-overflow-tooltip />
              <el-table-column prop="example" :label="t('uiAutomation.testCase.example')" min-width="200" show-overflow-tooltip />
              <el-table-column :label="t('uiAutomation.testCase.operation')" width="80" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" size="small">{{ t('uiAutomation.testCase.insert') }}</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
    
    <DataFactorySelector
      v-model="showDataFactorySelector"
      @select="handleDataFactorySelect"
    />

    <!-- 执行记录列表弹窗 -->
    <el-dialog
      v-model="historyDialogVisible"
      :title="`执行记录 - ${historyCaseName}`"
      width="700px"
      destroy-on-close
      append-to-body
    >
      <div v-loading="historyLoading">
        <el-table :data="historyRecords" style="width: 100%" size="small" v-if="historyRecords.length > 0">
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="getHistoryStatusType(row.status)" size="small">{{ getHistoryStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column label="时长" width="80" align="center">
            <template #default="{ row }">
              {{ formatDuration(row.execution_time) }}
            </template>
          </el-table-column>
          <el-table-column label="执行时间" min-width="160">
            <template #default="{ row }">
              {{ row.started_at ? formatTime(row.started_at) : formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="执行人" width="80" align="center">
            <template #default="{ row }">
              {{ row.created_by?.username || row.created_by || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="70" align="center">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="viewHistoryDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无执行记录" />
        <div class="pagination-container" v-if="historyTotal > 0" style="margin-top: 12px;">
          <el-pagination
            v-model:current-page="historyPage"
            v-model:page-size="historyPageSize"
            :total="historyTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @current-change="handleHistoryPageChange"
            @size-change="handleHistorySizeChange"
            small
          />
        </div>
      </div>
    </el-dialog>

    <!-- 执行记录详情弹窗 -->
    <el-dialog
      v-model="historyDetailVisible"
      title="执行记录详情"
      width="680px"
      destroy-on-close
      append-to-body
    >
      <template v-if="historyDetailData">
        <div class="history-detail-header">
          <el-descriptions :column="3" size="small" border>
            <el-descriptions-item label="状态">
              <el-tag :type="getHistoryStatusType(historyDetailData.status)" size="small">{{ getHistoryStatusText(historyDetailData.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="时长">{{ formatDuration(historyDetailData.execution_time) }}</el-descriptions-item>
            <el-descriptions-item label="浏览器">{{ historyDetailData.browser || '-' }}</el-descriptions-item>
            <el-descriptions-item label="开始时间">{{ historyDetailData.started_at ? formatTime(historyDetailData.started_at) : '-' }}</el-descriptions-item>
            <el-descriptions-item label="结束时间">{{ historyDetailData.finished_at ? formatTime(historyDetailData.finished_at) : '-' }}</el-descriptions-item>
            <el-descriptions-item label="执行人">{{ historyDetailData.created_by?.username || historyDetailData.created_by || '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>
        <div class="history-detail-logs" v-if="historyDetailData.parsedLogs">
          <h4 style="margin: 12px 0 8px; font-size: 14px; color: var(--gray-700);">执行日志</h4>
          <div v-for="(step, index) in (Array.isArray(historyDetailData.parsedLogs) ? historyDetailData.parsedLogs : historyDetailData.parsedLogs.steps || [])" :key="index" class="log-item">
            <div class="log-header">
              <el-tag :type="step.success ? 'success' : 'danger'" size="small">
                <template v-if="step.step_number === 'sql'">
                  <span style="display: inline-flex; align-items: center; gap: 4px;"><el-icon style="font-size: 14px;"><Coin /></el-icon> SQL</span>
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
              <el-icon><WarningFilled /></el-icon>
              <pre class="error-message">{{ step.error }}</pre>
            </div>
          </div>
        </div>
        <div v-if="historyDetailData.error_message" class="history-detail-error">
          <h4 style="margin: 12px 0 8px; font-size: 14px; color: var(--gray-700);">错误信息</h4>
          <div class="errors-container">
            <div
              v-for="(error, idx) in historyDetailErrors"
              :key="idx"
              class="error-item"
            >
              <div class="error-header">
                <el-tag type="danger" size="large">
                  <span class="error-tag-inner">
                    <el-icon><WarningFilled /></el-icon>
                    <span>{{ error.message }}</span>
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
            <!-- 兜底：无结构化错误时显示 error_message -->
            <div v-if="historyDetailErrors.length === 0" class="error-item">
              <div class="error-header">
                <el-tag type="danger" size="large">
                  <span class="error-tag-inner">
                    <el-icon><WarningFilled /></el-icon>
                    <span>{{ historyDetailData.error_message }}</span>
                  </span>
                </el-tag>
              </div>
            </div>
          </div>
        </div>
        <div v-if="historyDetailData.screenshots && historyDetailData.screenshots.length > 0" class="history-detail-screenshots">
          <h4 style="margin: 12px 0 8px; font-size: 14px; color: var(--gray-700);">失败截图</h4>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <el-image v-for="(img, idx) in historyDetailData.screenshots" :key="idx" :src="img.url || img" style="width: 120px; height: 80px; border-radius: 4px; border: 1px solid var(--gray-200);" fit="cover" :preview-src-list="historyDetailData.screenshots.map(s => s.url || s)" :initial-index="idx" />
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, Plus, Edit, Delete, Check, CaretRight, CaretLeft, ArrowUp, ArrowDown, Rank, Picture, Warning, View, ZoomIn, Refresh, WarningFilled, MagicStick, Folder, VideoPlay, CopyDocument, Close, FolderOpened, DeleteFilled, Coin
} from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import Sortable from 'sortablejs'
import DataFactorySelector from '@/components/DataFactorySelector.vue'
import ActionCell from '@/components/ActionCell.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

import {
  getUiProjects,
  getElements,
  getElementGroupTree,
  getElementTree,
  createTestCase,
  updateTestCase,
  deleteTestCase as deleteTestCaseApi,
  getTestCases,
  runTestCase as runTestCaseApi,
  copyTestCase as copyTestCaseApi,
  getLocatorStrategies,
  getTestCaseGroupTree,
  createTestCaseGroup,
  updateTestCaseGroup,
  deleteTestCaseGroup,
  batchReorderTestCases,
  batchDeleteTestCases,
  batchUpdateTestCaseGroup,
  batchUpdateTestCases,
  getTestCaseExecutions,
  batchReorderTestCaseGroups
} from '@/api/ui_automation'
import { getVariableFunctions } from '@/api/data-factory'

// 响应式数据
const projects = ref([])
const projectId = ref('')
const testCases = ref([])
const selectedTestCase = ref(null)
const detailDrawerVisible = ref(false)
const detailDrawerWidth = ref(600)
const detailCollapsed = ref(false)
const detailDrawerSize = computed(() => detailCollapsed.value ? '20px' : `${detailDrawerWidth.value}px`)
const currentSteps = ref([])
const availableElements = ref([])
const elementTreeData = ref([])
const searchKeyword = ref('')
const searchStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const showCreateDialog = ref(false)
const editingTestCase = ref(null)
const executionResult = ref(null)
const lastRunCaseId = ref(null)  // 记录最近运行的用例ID

// 从执行记录详情的步骤日志中提取错误列表
const historyDetailErrors = computed(() => {
  if (!historyDetailData.value) return []
  const steps = Array.isArray(historyDetailData.value.parsedLogs)
    ? historyDetailData.value.parsedLogs
    : (historyDetailData.value.parsedLogs?.steps || [])
  const errors = []
  for (const step of steps) {
    if (step.error && !step.success) {
      errors.push({
        message: step.step_number === 'sql'
          ? `${step.action_type === 'postcondition_sql' ? '后置清理SQL' : '前置数据SQL'}执行失败`
          : `步骤${step.step_number}执行失败`,
        step_number: step.step_number === 'sql' ? null : step.step_number,
        action_type: step.action_type || '',
        element: '',
        description: step.description || '',
        details: step.error || ''
      })
    }
  }
  return errors
})
const resultActiveTab = ref('logs')
const allStepsExpanded = ref(false)
const showSteps = ref(true)
const showScreenshotPreview = ref(false)
const currentScreenshot = ref(null)
const isRunning = ref(false)
const selectedEngine = ref('playwright')  // 默认使用Playwright
const selectedBrowser = ref('chrome')  // 默认使用Chrome
const headlessMode = ref(false)  // 默认使用有头模式
const showVariableHelper = ref(false)
const currentEditingStep = ref(null)
const currentEditingField = ref('')
const showDataFactorySelector = ref(false)
const currentStepForDataFactory = ref(null)
const currentFieldForDataFactory = ref('')
const variableCategories = ref([])
const loading = ref(false)
const testCaseTableRef = ref(null)
const sortableInstance = ref(null)
const isDragging = ref(false)
let _dragSelectedCases = []  // 拖拽期间暂存选中行

// ========== 执行记录弹窗相关 ==========
const historyDialogVisible = ref(false)
const historyLoading = ref(false)
const historyRecords = ref([])
const historyCaseName = ref('')
const historyCurrentCaseId = ref(null)
const historyPage = ref(1)
const historyPageSize = ref(10)
const historyTotal = ref(0)
const historyDetailVisible = ref(false)
const historyDetailData = ref(null)

// ========== 批量操作相关 ==========
const selectedCases = ref([])                  // 选中的用例行（由 el-table selection-change 维护）
const batchEditMode = ref(false)               // 批量编辑名称模式
const batchEditIds = ref([])                   // 批量编辑期间冻结的用例ID列表（脱离 el-table selection，避免抖动）
const batchEditBackup = ref({})                // 批量编辑前的名称备份 { id: oldName }
const batchEditLoading = ref(false)
const batchRunLoading = ref(false)
const batchLoading = ref(false)
const showBatchGroupDialog = ref(false)        // 批量改分组弹窗
const batchTargetGroupId = ref(null)           // 批量目标分组ID

// 表格选择变化
const handleCaseSelectionChange = (rows) => {
  // 批量编辑期间忽略 el-table selection 抖动，保持冻结的编辑集合不变
  if (batchEditMode.value) return
  selectedCases.value = rows
}

// 判断某行是否在批量编辑集合中（批量编辑模式下用）
const isCaseSelected = (row) => {
  return batchEditIds.value.includes(row.id)
}

// 清空选择
const clearCaseSelection = () => {
  testCaseTableRef.value?.clearSelection()
}

// 进入批量编辑名称模式：冻结选中ID集合，备份当前名称
const enterBatchEditMode = () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择要编辑的用例')
    return
  }
  batchEditIds.value = selectedCases.value.map(c => c.id)
  batchEditBackup.value = {}
  batchEditIds.value.forEach(id => {
    const tc = testCases.value.find(t => t.id === id)
    if (tc) batchEditBackup.value[id] = tc.name
  })
  batchEditMode.value = true
}

// 取消批量编辑：恢复名称到备份值
const cancelBatchEdit = () => {
  Object.keys(batchEditBackup.value).forEach(id => {
    const tc = testCases.value.find(t => String(t.id) === String(id))
    if (tc) tc.name = batchEditBackup.value[id]
  })
  batchEditBackup.value = {}
  batchEditIds.value = []
  batchEditMode.value = false
  // 强制清空选中状态，避免退出编辑后顶部批量工具栏再次出现
  selectedCases.value = []
  clearCaseSelection()
}

// 保存批量编辑：按 batchEditIds 收集改动过的用例
const saveBatchEdit = async () => {
  const updates = []
  batchEditIds.value.forEach(id => {
    const tc = testCases.value.find(t => t.id === id)
    if (!tc) return
    const oldName = batchEditBackup.value[id]
    const newName = (tc.name || '').trim()
    if (!newName) {
      ElMessage.warning('用例名称不能为空')
      return
    }
    if (newName !== oldName) {
      updates.push({ id, name: newName })
    }
  })
  if (updates.length === 0) {
    ElMessage.info('没有修改需要保存')
    batchEditMode.value = false
    batchEditBackup.value = {}
    batchEditIds.value = []
    return
  }
  batchEditLoading.value = true
  try {
    const res = await batchUpdateTestCases({ updates })
    ElMessage.success(res.data.message || `成功更新 ${updates.length} 个用例`)
    batchEditMode.value = false
    batchEditBackup.value = {}
    batchEditIds.value = []
    // 强制清空选中状态，避免退出编辑后顶部批量工具栏再次出现
    selectedCases.value = []
    clearCaseSelection()
  } catch (error) {
    const msg = error.response?.data?.error || error.message || '批量保存失败'
    ElMessage.error(msg)
  } finally {
    batchEditLoading.value = false
  }
}

// 批量执行：按 filteredTestCases 的列表顺序执行选中的用例
const handleBatchRun = async () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择要执行的用例')
    return
  }
  try {
    await ElMessageBox.confirm(
      `将按列表顺序执行选中的 ${selectedCases.value.length} 个用例，可能需要较长时间。是否继续？`,
      '批量执行',
      { type: 'warning', confirmButtonText: '开始执行', cancelButtonText: '取消' }
    )
  } catch (e) {
    return  // 用户取消
  }

  // 按 filteredTestCases 当前顺序排序选中的用例
  const orderedIds = filteredTestCases.value.map(tc => tc.id)
  const orderedSelected = [...selectedCases.value].sort(
    (a, b) => orderedIds.indexOf(a.id) - orderedIds.indexOf(b.id)
  )

  batchRunLoading.value = true
  let passCount = 0, failCount = 0, skipCount = 0
  ElMessage.info(`开始批量执行，共 ${orderedSelected.length} 个用例`)

  for (const tc of orderedSelected) {
    try {
      const response = await runTestCaseApi(tc.id, {
        project_id: projectId.value,
        engine: selectedEngine.value,
        browser: selectedBrowser.value,
        headless: headlessMode.value
      })
      if (response.data.success) {
        passCount++
      } else if (response.data.status === 'skipped') {
        skipCount++
      } else {
        failCount++
      }
    } catch (error) {
      failCount++
    }
  }

  batchRunLoading.value = false
  // 刷新列表与状态
  await loadTestCases()
  if (selectedTestCase.value) {
    const updated = testCases.value.find(tc => tc.id === selectedTestCase.value.id)
    if (updated) selectedTestCase.value = updated
  }
  ElMessage.success(`批量执行完成：通过 ${passCount}，失败 ${failCount}，跳过 ${skipCount}`)
}

// 打开批量改分组弹窗
const openBatchUpdateGroupDialog = () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择要操作的用例')
    return
  }
  batchTargetGroupId.value = null
  showBatchGroupDialog.value = true
}

// 执行批量改分组
const handleBatchUpdateGroup = async () => {
  batchLoading.value = true
  try {
    const ids = selectedCases.value.map(c => c.id)
    const groupId = batchTargetGroupId.value || null
    const res = await batchUpdateTestCaseGroup({ ids, group_id: groupId })
    ElMessage.success(res.data.message || `成功更新 ${ids.length} 个用例的分组`)
    showBatchGroupDialog.value = false
    clearCaseSelection()
    await loadTestCases()
    await loadTestCaseGroups()
  } catch (error) {
    const msg = error.response?.data?.error || error.message || '批量修改分组失败'
    ElMessage.error(msg)
  } finally {
    batchLoading.value = false
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择要删除的用例')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedCases.value.length} 个用例？此操作不可恢复`,
      '批量删除',
      { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }
    )
  } catch (e) {
    return  // 用户取消
  }
  batchLoading.value = true
  try {
    const ids = selectedCases.value.map(c => c.id)
    const res = await batchDeleteTestCases({ ids })
    ElMessage.success(res.data.message || `成功删除 ${ids.length} 个用例`)
    // 如果删除集中包含当前选中的用例，清空详情
    if (selectedTestCase.value && ids.includes(selectedTestCase.value.id)) {
      selectedTestCase.value = null
      currentSteps.value = []
      executionResult.value = null
    }
    clearCaseSelection()
    await loadTestCases()
    await loadTestCaseGroups()
  } catch (error) {
    const msg = error.response?.data?.error || error.message || '批量删除失败'
    ElMessage.error(msg)
  } finally {
    batchLoading.value = false
  }
}


// 分组相关
const testCaseGroupTree = ref([])
const selectedGroupId = ref(null)
const groupExpandedKeys = ref([])

// 将"全部"节点合并到分组树中，保持同级对齐
const groupTreeWithAll = computed(() => {
  const allNode = { id: '__all__', name: '全部', children: [] }
  return [allNode, ...testCaseGroupTree.value]
})
const groupTreeRef = ref(null)
const showCreateGroupDialog = ref(false)
const editingGroup = ref(null)
const groupForm = reactive({
  name: '',
  description: '',
  parent_group: null
})
const showGroupContextMenu = ref(false)
const groupContextMenuX = ref(0)
const groupContextMenuY = ref(0)
const rightClickedGroupNode = ref(null)

// 分组树select数据（过滤掉当前编辑的分组，防止循环引用）
const groupTreeSelectData = computed(() => {
  const filterNode = (nodes) => {
    if (!nodes) return []
    return nodes
      .filter(n => !editingGroup.value || n.id !== editingGroup.value.id)
      .map(n => ({ ...n, children: filterNode(n.children) }))
  }
  return filterNode(testCaseGroupTree.value)
})

// 前置条件/后置条件（详情面板编辑）
const selectedPreconditions = ref([])
const postconditionSql = ref('')
const preconditionSql = ref('')
const showPreconditions = ref(false)
const showPostcondition = ref(false)
const showPreconditionSql = ref(false)
const showTestSteps = ref(true)

const getTestCaseName = (id) => {
  const tc = testCases.value.find(t => t.id === id)
  return tc ? tc.name : `用例#${id}`
}

const removePrecondition = (index) => {
  selectedPreconditions.value.splice(index, 1)
}



// 表单数据
const testCaseForm = reactive({
  name: '',
  description: '',
  priority: 'medium',
  preconditions: [],
  postcondition_sql: '',
  precondition_sql: '',
  group: null
})

// 可选的前置条件用例列表（同项目下的其他用例）
// 前置条件用例树数据：分组 + 用例
const preconditionTreeData = computed(() => {
  const groups = testCaseGroupTree.value || []
  const cases = testCases.value || []
  const currentId = editingTestCase.value?.id

  // 递归构建分组节点，挂载用例
  const buildGroupNode = (group) => {
    const groupCases = cases.filter(tc => tc.group === group.id && tc.id !== currentId)
    const caseNodes = groupCases.map(tc => ({
      id: tc.id,
      name: tc.name,
      type: 'case',
      disabled: false
    }))
    const childGroups = (group.children || []).map(buildGroupNode)
    return {
      id: `group-${group.id}`,
      name: group.name,
      type: 'group',
      disabled: true,
      children: [...childGroups, ...caseNodes]
    }
  }

  const tree = groups.map(buildGroupNode)

  // 未分组用例
  const ungroupedCases = cases.filter(tc => !tc.group && tc.id !== currentId)
  if (ungroupedCases.length > 0) {
    tree.unshift({
      id: 'group-unassigned',
      name: '未分组',
      type: 'group',
      disabled: true,
      children: ungroupedCases.map(tc => ({
        id: tc.id,
        name: tc.name,
        type: 'case',
        disabled: false
      }))
    })
  }
  return tree
})

// 计算属性
const filteredTestCases = computed(() => {
  let result = testCases.value
  // 按分组筛选
  if (selectedGroupId.value) {
    result = result.filter(tc => tc.group === selectedGroupId.value)
  }
  // 按关键词筛选
  if (searchKeyword.value) {
    result = result.filter(tc =>
      tc.name.includes(searchKeyword.value) ||
      tc.description?.includes(searchKeyword.value)
    )
  }
  // 按状态筛选
  if (searchStatus.value) {
    result = result.filter(tc => (tc.status || 'normal') === searchStatus.value)
  }
  // 按 order 字段排序（拖拽排序后 order 会更新）
  result = [...result].sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
  return result
})

// 分页后的用例列表
const paginatedTestCases = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredTestCases.value.slice(start, start + pageSize.value)
})

// 搜索时重置到第一页
watch([searchKeyword, searchStatus], () => {
  currentPage.value = 1
})

// selectedTestCase 被外部置空时同步关闭抽屉
watch(selectedTestCase, (val) => {
  if (!val) detailDrawerVisible.value = false
})

// 抽屉关闭时（ESC/外部触发）同步清空选中用例
watch(detailDrawerVisible, (val) => {
  if (!val && selectedTestCase.value) {
    selectedTestCase.value = null
    currentSteps.value = []
    executionResult.value = null
  }
})

// 表格行点击选中
const handleTableCurrentChange = (row) => {
  if (isDragging.value) return
  // 批量编辑模式下禁止点击行打开步骤抽屉，避免干扰名称编辑
  if (batchEditMode.value) return
  // 编辑弹窗打开期间（包括保存过程中数据刷新导致的 current-change）不打开抽屉
  if (showCreateDialog.value) return
  if (row) selectTestCase(row)
}

// 表格行高亮样式
const tableRowClassName = ({ row }) => {
  return selectedTestCase.value?.id === row.id ? 'active-row' : ''
}

// 解析执行日志
const parsedExecutionLogs = computed(() => {
  if (!executionResult.value || !executionResult.value.logs) return []
  try {
    const raw = typeof executionResult.value.logs === 'string'
      ? JSON.parse(executionResult.value.logs)
      : executionResult.value.logs
    // 兼容新旧格式：新格式 {steps: [...], text_logs: '...'}，旧格式纯数组
    if (Array.isArray(raw)) {
      return raw
    }
    if (raw && raw.steps && Array.isArray(raw.steps)) {
      return raw.steps
    }
    return []
  } catch (e) {
    console.error('解析执行日志失败:', e)
    return []
  }
})

// 方法定义
const loadProjects = async () => {
  try {
    const response = await getUiProjects({ page_size: 100 })
    projects.value = response.data.results || response.data
  } catch (error) {
    ElMessage.error('获取项目列表失败')
    console.error('获取项目列表失败:', error)
  }
}

const loadTestCases = async () => {
  if (!projectId.value) {
    testCases.value = []
    return
  }

  try {
    const response = await getTestCases({ project: projectId.value })
    testCases.value = response.data.results || response.data
  } catch (error) {
    console.error('获取测试用例失败:', error)
  }
}

const loadElements = async () => {
  if (!projectId.value) {
    availableElements.value = []
    elementTreeData.value = []
    return
  }

  try {
    // 并行加载：平铺列表（用于onElementChange查找）+ 树形数据
    const [elementsResponse, pageTreeResponse, treeElementsResponse] = await Promise.all([
      getElements({ project: projectId.value, page_size: 500 }),
      getElementGroupTree({ project: projectId.value }),
      getElementTree({ project: projectId.value })
    ])

    // 平铺列表保留，供 onElementChange 等逻辑使用
    availableElements.value = elementsResponse.data.results || elementsResponse.data

    // 构建树形结构
    const buildTree = (groups) => {
      return groups.map(group => ({
        ...group,
        type: 'page',
        children: group.children ? buildTree(group.children) : []
      }))
    }
    const pageNodes = buildTree(pageTreeResponse.data || [])
    const treeElements = treeElementsResponse.data?.results || treeElementsResponse.data || []

    // 将元素挂载到对应页面节点下
    const attachedElementIds = new Set()
    const attachElementsToPages = (pages) => {
      pages.forEach(page => {
        const pageElements = treeElements.filter(element => element.group_id === page.id)
        const elementNodes = pageElements.map(element => {
          attachedElementIds.add(element.id)
          return { ...element, type: 'element' }
        })
        page.children = page.children ? [...page.children, ...elementNodes] : [...elementNodes]
        if (page.children) {
          attachElementsToPages(page.children.filter(child => child.type === 'page'))
        }
      })
    }
    attachElementsToPages(pageNodes)

    // 未关联页面元素
    const unassignedElements = treeElements.filter(element => {
      if (!element.group_id) return true
      return !attachedElementIds.has(element.id)
    })
    if (unassignedElements.length > 0) {
      pageNodes.unshift({
        id: 'unassigned',
        name: '未关联页面',
        type: 'page',
        children: unassignedElements.map(element => ({ ...element, type: 'element' }))
      })
    }

    elementTreeData.value = pageNodes
  } catch (error) {
    console.error('获取元素列表失败:', error)
  }
}

const onProjectChange = async () => {
  selectedTestCase.value = null
  currentSteps.value = []
  executionResult.value = null
  selectedGroupId.value = null

  await Promise.all([
    loadTestCases(),
    loadElements(),
    loadTestCaseGroups()
  ])
}

// 根据前置条件 ID 列表，从当前用例集合中构造 preconditions_data（[{id,name,order}]）
// 用于保存后实时更新列表/抽屉里展示的前置条件，避免刷新页面
const buildPreconditionsData = (idList) => {
  if (!idList || idList.length === 0) return []
  return idList.map((pid, idx) => {
    const tc = testCases.value.find(t => t.id === pid)
    return { id: pid, name: tc?.name || `用例#${pid}`, order: idx + 1 }
  })
}

const selectTestCase = (testCase) => {
  // 如果点击的是同一个用例
  if (selectedTestCase.value && selectedTestCase.value.id === testCase.id) {
    // 抽屉处于收起状态时，再次点击同一用例应展开抽屉
    if (detailCollapsed.value) {
      detailCollapsed.value = false
      detailDrawerVisible.value = true
    }
    return
  }

  selectedTestCase.value = testCase
  // 确保步骤数据格式正确，添加前端需要的字段
  if (testCase.steps && testCase.steps.length > 0) {
    currentSteps.value = testCase.steps.map(step => ({
      ...step,
      element_id: step.element || '',
      expanded: false
    }))
  } else {
    currentSteps.value = []
  }
  // 加载前置条件和后置条件
  selectedPreconditions.value = (testCase.preconditions_data || []).map(pc => pc.id)
  postconditionSql.value = testCase.postcondition_sql || ''
  preconditionSql.value = testCase.precondition_sql || ''
  showPreconditions.value = selectedPreconditions.value.length > 0
  showPostcondition.value = !!testCase.postcondition_sql
  showPreconditionSql.value = !!testCase.precondition_sql
  // 只有在切换到不同用例时才清空执行结果  executionResult.value = null
  showSteps.value = true
  // 打开详情抽屉
  detailDrawerVisible.value = true
  // 切换用例时若抽屉处于收起状态，自动展开
  if (detailCollapsed.value) detailCollapsed.value = false
}

// 关闭详情抽屉
const closeDetailDrawer = () => {
  detailDrawerVisible.value = false
  detailCollapsed.value = false
  selectedTestCase.value = null
  currentSteps.value = []
  executionResult.value = null
  // 清空 el-table 当前选中行，避免再次点击同一行时 current-change 不触发导致抽屉无法打开
  testCaseTableRef.value?.setCurrentRow(null)
}

// 切换抽屉收起/展开（保留用例数据不清空）
const toggleDetailCollapse = () => {
  detailCollapsed.value = !detailCollapsed.value
  // 收起抽屉时清空 el-table 当前选中行，以便再次点击同一行时能触发 current-change
  if (detailCollapsed.value) {
    testCaseTableRef.value?.setCurrentRow(null)
  }
}

// 拖拽调整抽屉宽度
const startResize = (e) => {
  e.preventDefault()
  const startX = e.clientX
  const startWidth = detailDrawerWidth.value
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  const onMove = (ev) => {
    const delta = startX - ev.clientX
    const newWidth = Math.max(400, Math.min(window.innerWidth - 320, startWidth + delta))
    detailDrawerWidth.value = newWidth
  }
  const onUp = () => {
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

const addStep = () => {
  const newStep = {
    id: Date.now(),
    action_type: 'click',
    element_id: '',
    input_value: '',
    wait_time: 1000,
    action_wait: 0,
    assert_type: 'textContains',
    assert_value: '',
    description: '',
    output_var: '',
    expanded: true
  }
  currentSteps.value.push(newStep)
}

const removeStep = (index) => {
  currentSteps.value.splice(index, 1)
}

const onStepsReorder = () => {
  // 步骤重新排序后的处理
  console.log('步骤已重新排序')
}

const onActionTypeChange = (step) => {
  // 根据操作类型重置相关参数
  if (!['fill', 'select', 'navigate'].includes(step.action_type)) {
    step.input_value = ''
  }
  if (step.action_type !== 'wait') {
    step.wait_time = 1000
  }
  if (step.action_type !== 'assert') {
    step.assert_type = 'textContains'
    step.assert_value = ''
  }
  // navigate 不需要元素
  if (step.action_type === 'navigate') {
    step.element_id = null
  }
}

const onElementChange = (step) => {
  // 元素变化时始终更新步骤描述：优先使用元素描述，否则回退到"操作类型+元素名"
  const element = availableElements.value.find(e => e.id === step.element_id)
  if (element) {
    step.description = element.description || `${getActionTypeText(step.action_type)}${element.name}`
  }
}

// 获取元素描述
const getElementDescription = (elementId) => {
  if (!elementId) return ''
  const element = availableElements.value.find(e => String(e.id) === String(elementId))
  return element?.description || ''
}

// 步骤描述为空时，显示操作类型+元素名作为兜底placeholder
const getStepPlaceholder = (step) => {
  const actionText = getActionTypeText(step.action_type)
  const element = availableElements.value.find(e => e.id === step.element_id)
  const elementName = element ? element.name : ''
  return elementName ? `${actionText}${elementName}` : actionText || '步骤描述'
}

const needsInputValue = (actionType) => {
  return ['fill', 'select', 'switchTab', 'navigate'].includes(actionType)
}

const needsWaitTime = (actionType) => {
  return ['wait', 'waitFor'].includes(actionType)
}

const needsActionWait = (actionType) => {
  // 操作后等待适用于除wait/waitFor/assert之外的所有操作类型
  return !['wait', 'waitFor', 'assert'].includes(actionType)
}

const needsElement = (actionType, assertType) => {
  if (['wait', 'switchTab', 'screenshot', 'navigate'].includes(actionType)) return false
  // 表格断言类型自动查找表格，不需要用户选择元素
  if (actionType === 'assert' && ['tableContains', 'tableNotContains', 'tableEmpty'].includes(assertType)) return false
  return true
}

// 元素树形下拉 props
const elementTreeProps = {
  children: 'children',
  label: 'name',
  value: 'id',
  isLeaf: (data) => data.type === 'element'
}

// 元素类型标签映射
const getElementTypeLabel = (type) => {
  const typeMap = {
    'button': '按钮', 'input': '输入框', 'link': '链接',
    'dropdown': '下拉框', 'checkbox': '复选框', 'radio': '单选框',
    'text': '文本', 'image': '图片', 'table': '表格',
    'form': '表单', 'modal': '弹窗'
  }
  return typeMap[type?.toLowerCase()] || type
}

const expandAllSteps = () => {
  allStepsExpanded.value = !allStepsExpanded.value
  currentSteps.value.forEach(step => {
    step.expanded = allStepsExpanded.value
  })
}

// 判断步骤是否发生了变化（用于保存后将用例状态重置为 normal）
// 比较步骤数组长度以及每个步骤的关键字段
const isStepsChanged = (oldSteps, newSteps) => {
  const a = oldSteps || []
  const b = newSteps || []
  if (a.length !== b.length) return true
  const keys = ['action_type', 'element', 'element_id', 'input_value', 'wait_time', 'action_wait', 'assert_type', 'assert_value', 'description', 'output_var']
  for (let i = 0; i < b.length; i++) {
    for (const k of keys) {
      const av = a[i]?.[k] ?? null
      const bv = b[i]?.[k] ?? null
      if (String(av) !== String(bv)) return true
    }
  }
  return false
}

const saveTestCase = async () => {
  if (!selectedTestCase.value) return

  try {
    const oldSteps = selectedTestCase.value.steps || []
    const updateData = {
      ...selectedTestCase.value,
      steps: currentSteps.value,
      preconditions: selectedPreconditions.value,
      postcondition_sql: postconditionSql.value,
      precondition_sql: preconditionSql.value
    }

    // 如果步骤发生了变化，将用例状态重置为 normal（修改步骤后需要重新执行才能得到新的状态）
    if (isStepsChanged(oldSteps, currentSteps.value)) {
      updateData.status = 'normal'
    }

    await updateTestCase(selectedTestCase.value.id, updateData)
    ElMessage.success(t('uiAutomation.testCase.save.success'))

    // 保存后实时更新 preconditions_data，让列表展示的前置条件立即生效
    const newPreconditionsData = buildPreconditionsData(selectedPreconditions.value)
    updateData.preconditions_data = newPreconditionsData

    // 更新本地数据
    const index = testCases.value.findIndex(tc => tc.id === selectedTestCase.value.id)
    if (index !== -1) {
      testCases.value[index] = { ...updateData }
      selectedTestCase.value = { ...updateData }
    }
  } catch (error) {
      console.error('保存测试用例失败:', error)
      if (error.response?.data?.preconditions) {
        const msg = error.response.data.preconditions
        ElMessage.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
      } else {
        ElMessage.error(t('uiAutomation.testCase.save.failed'))
      }
    }
}

const runTestCase = async (testCase) => {
  isRunning.value = true
  try {
    const modeText = headlessMode.value ? t('uiAutomation.testCase.runMode.headless') : t('uiAutomation.testCase.runMode.headed')
    ElMessage.info(t('uiAutomation.testCase.run.start', { engine: selectedEngine.value.toUpperCase(), browser: selectedBrowser.value.toUpperCase(), mode: modeText }))

    const response = await runTestCaseApi(testCase.id, {
      project_id: projectId.value,
      engine: selectedEngine.value,
      browser: selectedBrowser.value,
      headless: headlessMode.value
    })

    executionResult.value = response.data
    lastRunCaseId.value = testCase.id
    resultActiveTab.value = 'logs'
    showSteps.value = false  // 自动切换到结果视图

    if (response.data.success) {
      ElMessage.success(t('uiAutomation.testCase.run.success'))
    } else if (response.data.status === 'skipped') {
      ElMessage.warning('用例已跳过')
    } else {
      ElMessage.error(t('uiAutomation.testCase.run.failed'))
      // 如果有截图，自动切换到截图标签页
      if (response.data.screenshots && response.data.screenshots.length > 0) {
        resultActiveTab.value = 'screenshots'
      }
    }

    // 刷新用例列表以更新状态
    await loadTestCases()
    // 刷新后更新当前选中用例的状态
    if (selectedTestCase.value) {
      const updated = testCases.value.find(tc => tc.id === selectedTestCase.value.id)
      if (updated) {
        selectedTestCase.value = updated
      }
    }
  } catch (error) {
    console.error('执行测试用例失败:', error)

    // 即使出错也要设置执行结果,显示错误信息
    const errorMessage = error.response?.data?.message || error.message || '执行失败'
    const errorLogs = error.response?.data?.logs || `测试用例执行出错\n\n错误信息: ${errorMessage}`

    // 格式化错误信息为统一的对象格式
    const errors = error.response?.data?.errors || [{
      message: errorMessage,
      details: error.stack || '',
      step_number: null,
      action_type: '',
      element: '',
      description: ''
    }]

    executionResult.value = {
      success: false,
      logs: errorLogs,
      screenshots: error.response?.data?.screenshots || [],
      execution_time: 0,
      errors: errors
    }
    lastRunCaseId.value = testCase.id
    resultActiveTab.value = 'logs'
    showSteps.value = false  // 切换到结果视图显示错误

    ElMessage.error(t('uiAutomation.testCase.run.failedWithMessage', { message: errorMessage }))
  } finally {
    isRunning.value = false
  }
}

const toggleView = () => {
  showSteps.value = !showSteps.value
}

const editTestCase = (testCase) => {
  editingTestCase.value = testCase
  testCaseForm.name = testCase.name
  testCaseForm.description = testCase.description || ''
  testCaseForm.priority = testCase.priority || 'medium'
  testCaseForm.group = testCase.group || null
  // 加载前置条件（preconditions_data 是 [{id, name, order}] 格式，转为 id 列表）
  testCaseForm.preconditions = (testCase.preconditions_data || []).map(pc => pc.id)
  testCaseForm.postcondition_sql = testCase.postcondition_sql || ''
  testCaseForm.precondition_sql = testCase.precondition_sql || ''
  showCreateDialog.value = true
}

// ========== 查看执行记录 ==========
const loadHistoryRecords = async () => {
  historyLoading.value = true
  try {
    const res = await getTestCaseExecutions({ test_case: historyCurrentCaseId.value, execution_source: 'manual', page: historyPage.value, page_size: historyPageSize.value })
    historyRecords.value = res.data?.results || []
    historyTotal.value = res.data?.count || 0
  } catch (error) {
    console.error('获取执行记录失败:', error)
    ElMessage.error('获取执行记录失败')
  } finally {
    historyLoading.value = false
  }
}

const viewExecutionHistory = async (testCase) => {
  historyCaseName.value = testCase.name
  historyCurrentCaseId.value = testCase.id
  historyPage.value = 1
  historyRecords.value = []
  historyDialogVisible.value = true
  await loadHistoryRecords()
}

const handleHistoryPageChange = (page) => {
  historyPage.value = page
  loadHistoryRecords()
}

const handleHistorySizeChange = (size) => {
  historyPageSize.value = size
  historyPage.value = 1
  loadHistoryRecords()
}

const getHistoryStatusText = (status) => {
  const map = { pending: '待执行', running: '执行中', passed: '通过', failed: '失败', error: '错误', skipped: '跳过' }
  return map[status] || status
}

const getHistoryStatusType = (status) => {
  const map = { pending: 'info', running: 'warning', passed: 'success', failed: 'danger', error: 'danger', skipped: 'warning' }
  return map[status] || 'info'
}

const getHistorySourceType = (source) => {
  const map = { manual: '单用例', suite: '套件', scheduled: '定时' }
  return map[source] || source
}

const viewHistoryDetail = (record) => {
  let logs = record.execution_logs
  if (typeof logs === 'string') {
    try { logs = JSON.parse(logs) } catch { logs = null }
  }
  historyDetailData.value = {
    ...record,
    parsedLogs: logs
  }
  historyDetailVisible.value = true
}

const formatDuration = (seconds) => {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const min = Math.floor(seconds / 60)
  const sec = (seconds % 60).toFixed(1)
  return `${min}m${sec}s`
}

const deleteTestCase = async (testCase) => {
  try {
    await ElMessageBox.confirm(
      t('uiAutomation.testCase.delete.confirm', { name: testCase.name }),
      t('uiAutomation.testCase.delete.title'),
      {
        confirmButtonText: t('uiAutomation.common.confirm'),
        cancelButtonText: t('uiAutomation.common.cancel'),
        type: 'warning'
      }
    )

    await deleteTestCaseApi(testCase.id)
    ElMessage.success(t('uiAutomation.testCase.delete.success'))

    // 从列表中移除
    const index = testCases.value.findIndex(tc => tc.id === testCase.id)
    if (index !== -1) {
      testCases.value.splice(index, 1)
    }

    // 如果删除的是当前选中的用例，清空选择
    if (selectedTestCase.value?.id === testCase.id) {
      selectedTestCase.value = null
      currentSteps.value = []
      executionResult.value = null
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除测试用例失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const copyTestCase = async (testCase) => {
  try {
    await ElMessageBox.confirm(
      t('uiAutomation.testCase.copy.confirm', { name: testCase.name }),
      t('uiAutomation.testCase.copy.title'),
      {
        confirmButtonText: t('uiAutomation.common.confirm'),
        cancelButtonText: t('uiAutomation.common.cancel'),
        type: 'info'
      }
    )

    const response = await copyTestCaseApi(testCase.id)
    ElMessage.success(t('uiAutomation.testCase.copy.success'))

    // 复制的用例插入到列表头部
    testCases.value.unshift(response.data)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('复制测试用例失败:', error)
      ElMessage.error('复制失败')
    }
  }
}

// 加载变量函数
const loadVariableFunctions = async () => {
  try {
    loading.value = true
    console.log('开始加载变量函数...')
    const apiResponse = await getVariableFunctions()
    console.log('变量函数响应:', apiResponse)
    console.log('变量函数响应.data:', apiResponse.data)
    
    // 检查不同可能的数据结构
    let functionsData = []
    if (apiResponse && apiResponse.data) {
      if (Array.isArray(apiResponse.data)) {
        // 后端返回的是数组，直接使用
        functionsData = apiResponse.data
      } else if (apiResponse.data.functions) {
        // 如果data中有functions字段，使用它
        functionsData = apiResponse.data.functions
      } else if (typeof apiResponse.data === 'object') {
        // 如果data是对象但没有functions字段，假设整个对象就是按分类组织的函数
        functionsData = apiResponse.data
      }
    }
    
    console.log('处理后的函数数据:', functionsData)
    
    // 处理函数数据，按分类组织
    const grouped = {}
    
    if (Array.isArray(functionsData)) {
      // 如果是数组格式
      functionsData.forEach(func => {
        const category = func.category || '未分类'
        if (!grouped[category]) {
          grouped[category] = []
        }
        grouped[category].push({
          name: func.name,
          syntax: func.syntax,
          desc: func.description || func.desc || '',
          example: func.example
        })
      })
    } else if (typeof functionsData === 'object') {
      // 如果是按分类组织的对象格式
      for (const [category, funcs] of Object.entries(functionsData)) {
        if (Array.isArray(funcs)) {
          grouped[category] = funcs.map(func => ({
            name: func.name,
            syntax: func.syntax,
            desc: func.description || func.desc || '',
            example: func.example
          }))
        }
      }
    }
    
    console.log('按分类组织后的函数:', grouped)
    
    // 定义固定的分类顺序
    const categoryOrder = ['随机数', '测试数据', '字符串', '编码转换', '加密', '时间日期', 'Crontab', '未分类']
    
    // 按固定顺序构建分类列表
    const orderedCategories = []
    categoryOrder.forEach(category => {
      if (grouped[category]) {
        orderedCategories.push({
          label: category,
          variables: grouped[category]
        })
        delete grouped[category]
      }
    })
    
    // 添加剩余的分类
    for (const [category, funcs] of Object.entries(grouped)) {
      orderedCategories.push({
        label: category,
        variables: funcs
      })
    }
    
    console.log('最终的分类列表:', orderedCategories)
    variableCategories.value = orderedCategories
  } catch (error) {
    console.error('加载变量函数失败:', error)
    ElMessage.error('加载变量函数失败，使用本地数据')
    useLocalVariableCategories()
  } finally {
    loading.value = false
  }
}

// 使用本地变量分类数据作为 fallback
const useLocalVariableCategories = () => {
  variableCategories.value = [
    {
      label: t('uiAutomation.testCase.variableCategory.randomNumber'),
      variables: [
        { name: 'random_int', syntax: '${random_int(min, max, count)}', desc: t('uiAutomation.testCase.variable.randomInt.desc'), example: '${random_int(100, 999, 1)}' },
        { name: 'random_float', syntax: '${random_float(min, max, precision, count)}', desc: t('uiAutomation.testCase.variable.randomFloat.desc'), example: '${random_float(0, 1, 2, 1)}' }
      ]
    },
    {
      label: t('uiAutomation.testCase.variableCategory.randomString'),
      variables: [
        { name: 'random_string', syntax: '${random_string(length, char_type, count)}', desc: t('uiAutomation.testCase.variable.randomString.desc'), example: '${random_string(8, "all", 1)}' }
      ]
    }
  ]
}

// 计算属性提供变量分类数据
const variableCategoriesComputed = computed(() => {
  return variableCategories.value.length > 0 ? variableCategories.value : [
    {
      label: t('uiAutomation.testCase.variableCategory.randomNumber'),
      variables: []
    }
  ]
})

const openVariableHelper = (step, field) => {
  console.log('TestCaseManager openVariableHelper 被调用, step:', step, 'field:', field)
  console.log('variableCategories.value:', variableCategories.value)
  console.log('variableCategories.value.length:', variableCategories.value.length)
  currentEditingStep.value = step
  currentEditingField.value = field
  showVariableHelper.value = true
  console.log('showVariableHelper.value:', showVariableHelper.value)
}

const openDataFactorySelector = (step, field) => {
  currentStepForDataFactory.value = step
  currentFieldForDataFactory.value = field
  showDataFactorySelector.value = true
}

const handleDataFactorySelect = (record) => {
  const step = currentStepForDataFactory.value
  const field = currentFieldForDataFactory.value
  
  if (record && record.output_data && step && field) {
    let valueToSet = ''
    
    if (typeof record.output_data === 'string') {
      valueToSet = record.output_data
    } else if (record.output_data.result) {
      valueToSet = record.output_data.result
    } else if (record.output_data.output_data) {
      valueToSet = record.output_data.output_data
    } else {
      valueToSet = JSON.stringify(record.output_data)
    }
    
    step[field] = valueToSet
    ElMessage.success(t('uiAutomation.testCase.messages.dataFactorySelected', { toolName: record.tool_name }))
  }
  
  showDataFactorySelector.value = false
}

const insertVariable = (variable) => {
  if (currentEditingStep.value && currentEditingField.value) {
    const example = variable.example
    const currentValue = currentEditingStep.value[currentEditingField.value] || ''
    
    // 简单起见，这里直接追加到末尾，或者如果为空则替换
    if (!currentValue) {
      currentEditingStep.value[currentEditingField.value] = example
    } else {
      currentEditingStep.value[currentEditingField.value] = currentValue + example
    }
    
    ElMessage.success(t('uiAutomation.testCase.messages.variableInserted', { name: variable.name }))
    showVariableHelper.value = false
  }
}

const saveTestCaseForm = async () => {
  if (!testCaseForm.name.trim()) {
    ElMessage.warning(t('uiAutomation.testCase.form.nameRequired'))
    return
  }

  try {
    const data = {
      name: testCaseForm.name,
      description: testCaseForm.description,
      priority: testCaseForm.priority,
      preconditions: testCaseForm.preconditions,
      postcondition_sql: testCaseForm.postcondition_sql,
      precondition_sql: testCaseForm.precondition_sql,
      group: testCaseForm.group || null,
      project: projectId.value,
    }

    if (editingTestCase.value) {
      // 编辑现有用例
      await updateTestCase(editingTestCase.value.id, data)
      ElMessage.success(t('uiAutomation.testCase.update.success'))

      // 保存成功后实时更新 preconditions_data，列表/抽屉展示不受影响
      const newPreconditionsData = buildPreconditionsData(testCaseForm.preconditions)

      // 更新本地数据（保留原有的 steps，不覆盖）
      const index = testCases.value.findIndex(tc => tc.id === editingTestCase.value.id)
      if (index !== -1) {
        testCases.value[index] = {
          ...testCases.value[index],
          ...data,
          preconditions_data: newPreconditionsData
        }
        // 如果当前选中的就是这个用例，也更新选中状态
        if (selectedTestCase.value?.id === editingTestCase.value.id) {
          selectedTestCase.value = {
            ...selectedTestCase.value,
            ...data,
            preconditions_data: newPreconditionsData
          }
        }
      }
    } else {
      // 创建新用例
      const response = await createTestCase(data)
      ElMessage.success(t('uiAutomation.testCase.create.success'))
      // 新增用例插入到列表头部，刷新前即可见且排在第一个
      testCases.value.unshift(response.data)
    }

    showCreateDialog.value = false
    editingTestCase.value = null
    resetForm()
    await loadTestCaseGroups()  // 刷新分组用例计数
  } catch (error) {
    console.error('保存测试用例失败:', error)
    if (error.response?.data?.preconditions) {
      ElMessage.error(error.response.data.preconditions.join ? error.response.data.preconditions.join('; ') : error.response.data.preconditions)
    } else {
      ElMessage.error(t('uiAutomation.testCase.save.failed'))
    }
  }
}

const resetForm = () => {
  testCaseForm.name = ''
  testCaseForm.description = ''
  testCaseForm.priority = 'medium'
  testCaseForm.preconditions = []
  testCaseForm.postcondition_sql = ''
  testCaseForm.precondition_sql = ''
  testCaseForm.group = null
}

// 辅助方法
const getStatusTag = (status) => {
  const tagMap = {
    'normal': 'info',
    'passed': 'success',
    'failed': 'danger',
    'skipped': 'warning'
  }
  return tagMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    'normal': '正常',
    'passed': '通过',
    'failed': '失败',
    'skipped': '跳过'
  }
  return textMap[status] || '未知'
}

const getActionTypeText = (actionType) => {
  const textMap = {
    'click': t('uiAutomation.testCase.actionType.click'),
    'fill': t('uiAutomation.testCase.actionType.fill'),
    'select': '选择下拉选项',
    'getText': t('uiAutomation.testCase.actionType.getText'),
    'waitFor': t('uiAutomation.testCase.actionType.waitFor'),
    'hover': t('uiAutomation.testCase.actionType.hover'),
    'scroll': t('uiAutomation.testCase.actionType.scroll'),
    'screenshot': t('uiAutomation.testCase.actionType.screenshot'),
    'assert': t('uiAutomation.testCase.actionType.assert'),
    'wait': t('uiAutomation.testCase.actionType.wait'),
    'navigate': '路由跳转'
  }
  return textMap[actionType] || actionType
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString()
}

// 获取操作类型文本
const getActionText = (actionType) => {
  const actionMap = {
    'click': t('uiAutomation.testCase.actionText.click'),
    'fill': t('uiAutomation.testCase.actionText.fill'),
    'select': '选择',
    'getText': t('uiAutomation.testCase.actionText.getText'),
    'waitFor': t('uiAutomation.testCase.actionText.waitFor'),
    'hover': t('uiAutomation.testCase.actionText.hover'),
    'scroll': t('uiAutomation.testCase.actionText.scroll'),
    'screenshot': t('uiAutomation.testCase.actionText.screenshot'),
    'assert': t('uiAutomation.testCase.actionText.assert'),
    'wait': t('uiAutomation.testCase.actionText.wait'),
    'navigate': '跳转到'
  }
  return actionMap[actionType] || actionType
}

// 图片处理方法
const handleImageError = (event) => {
  const img = event.target
  const screenshotIndex = parseInt(img.dataset.index)
  if (executionResult.value && executionResult.value.screenshots) {
    executionResult.value.screenshots[screenshotIndex].error = true
    executionResult.value.screenshots[screenshotIndex].loaded = true
  }
}

const handleImageLoad = (event) => {
  const img = event.target
  const screenshotIndex = parseInt(img.dataset.index)
  if (executionResult.value && executionResult.value.screenshots) {
    executionResult.value.screenshots[screenshotIndex].loaded = true
    executionResult.value.screenshots[screenshotIndex].error = false
  }
}

const previewScreenshot = (screenshot) => {
  currentScreenshot.value = screenshot
  showScreenshotPreview.value = true
}

// ====== 分组相关方法 ======
const loadTestCaseGroups = async () => {
  if (!projectId.value) {
    testCaseGroupTree.value = []
    return
  }
  try {
    const response = await getTestCaseGroupTree({ project: projectId.value })
    testCaseGroupTree.value = response.data || []
  } catch (error) {
    console.error('获取用例分组树失败:', error)
  }
}

const onGroupNodeClick = (data) => {
  if (data.id === '__all__') {
    selectedGroupId.value = null
  } else {
    selectedGroupId.value = data.id
  }
  currentPage.value = 1
}

const onGroupRightClick = (event, data) => {
  if (data.id === '__all__') return  // "全部"节点不弹右键菜单
  event.preventDefault()
  rightClickedGroupNode.value = data
  groupContextMenuX.value = event.clientX
  groupContextMenuY.value = event.clientY
  showGroupContextMenu.value = true
}

// 分组拖拽排序：禁止拖拽"全部"节点
const allowGroupDrag = (draggingNode) => {
  return draggingNode.data.id !== '__all__'
}

// 分组拖拽排序：禁止拖入"全部"节点内部
const allowGroupDrop = (draggingNode, dropNode, type) => {
  if (dropNode.data.id === '__all__' && type !== 'before' && type !== 'after') return false
  return true
}

// 分组拖拽完成后，收集同级节点的顺序并提交后端
const onGroupNodeDrop = async (draggingNode, dropNode, type) => {
  // type: 'before' | 'after' | 'inner' 表示拖拽放置位置
  // 拖拽完成后，draggingNode 已移动到新位置，从 el-tree 实例获取完整节点结构
  const tree = groupTreeRef.value
  if (!tree) return

  // 根据拖放类型确定新的父节点和同级节点
  let parentNode
  if (type === 'inner') {
    // 拖入某个节点内部，该节点就是新父节点
    parentNode = dropNode
  } else {
    // before/after：和 dropNode 同级，取 dropNode 的父节点
    parentNode = dropNode.parent
  }

  // 获取同级子节点列表
  const siblings = parentNode ? parentNode.childNodes : tree.store.root.childNodes
  // 判断新的 parent_group：根节点（"全部"或无父）下为 null
  const newParentId = parentNode?.data?.id === '__all__' ? null : (parentNode?.data?.id ?? null)

  const orders = siblings
    .filter(node => node.data && node.data.id !== '__all__')
    .map((node, index) => ({
      id: node.data.id,
      order: index,
      parent_group: newParentId
    }))
  if (orders.length === 0) return
  try {
    await batchReorderTestCaseGroups({ orders })
    ElMessage.success('分组排序已保存')
  } catch (e) {
    console.error('分组排序保存失败:', e)
    ElMessage.error('分组排序保存失败')
  }
}

// 点击其他地方关闭右键菜单
watch(showGroupContextMenu, (val) => {
  if (val) {
    const closeMenu = () => {
      showGroupContextMenu.value = false
      document.removeEventListener('click', closeMenu)
    }
    setTimeout(() => document.addEventListener('click', closeMenu), 0)
  }
})

const editGroupNode = () => {
  showGroupContextMenu.value = false
  const node = rightClickedGroupNode.value
  editingGroup.value = node
  groupForm.name = node.name
  groupForm.description = node.description || ''
  groupForm.parent_group = node.parent_group || null
  showCreateGroupDialog.value = true
}

const addSubGroup = () => {
  showGroupContextMenu.value = false
  const node = rightClickedGroupNode.value
  editingGroup.value = null
  groupForm.name = ''
  groupForm.description = ''
  groupForm.parent_group = node.id
  showCreateGroupDialog.value = true
}

const deleteGroupNode = async () => {
  showGroupContextMenu.value = false
  const node = rightClickedGroupNode.value
  try {
    await ElMessageBox.confirm(`确定删除分组「${node.name}」？该分组下的用例将变为未分组。`, '删除分组', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteTestCaseGroup(node.id)
    ElMessage.success('分组已删除')
    if (selectedGroupId.value === node.id) {
      selectedGroupId.value = null
    }
    await loadTestCaseGroups()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除分组失败:', error)
      ElMessage.error('删除分组失败')
    }
  }
}

const saveGroupForm = async () => {
  if (!groupForm.name.trim()) {
    ElMessage.warning('请输入分组名称')
    return
  }
  try {
    const data = {
      name: groupForm.name,
      description: groupForm.description,
      parent_group: groupForm.parent_group || null,
      project: projectId.value
    }
    if (editingGroup.value) {
      await updateTestCaseGroup(editingGroup.value.id, data)
      ElMessage.success('分组已更新')
    } else {
      await createTestCaseGroup(data)
      ElMessage.success('分组已创建')
    }
    showCreateGroupDialog.value = false
    editingGroup.value = null
    groupForm.name = ''
    groupForm.description = ''
    groupForm.parent_group = null
    await loadTestCaseGroups()
  } catch (error) {
    console.error('保存分组失败:', error)
    ElMessage.error('保存分组失败')
  }
}

// 初始化表格行拖拽排序
const initSortable = () => {
  // 批量编辑或批量执行期间禁用拖拽，避免与行内输入冲突
  if (batchEditMode.value || batchRunLoading.value) return
  nextTick(() => {
    const tableEl = testCaseTableRef.value?.$el
    if (!tableEl) return
    const tbody = tableEl.querySelector('.el-table__body-wrapper tbody')
    if (!tbody) return

    // 销毁旧实例
    if (sortableInstance.value) {
      sortableInstance.value.destroy()
      sortableInstance.value = null
    }

    sortableInstance.value = Sortable.create(tbody, {
      animation: 150,
      onStart: () => {
        isDragging.value = true
        // 暂存选中状态
        _dragSelectedCases = selectedTestCases.value.slice()
      },
      onEnd: async (evt) => {
        isDragging.value = false
        const { oldIndex, newIndex } = evt
        if (oldIndex === newIndex) return

        // 还原 Sortable 的 DOM 操作，让 Vue 通过数据变化自行渲染
        const parent = evt.from
        const item = evt.item
        if (oldIndex < newIndex) {
          // 向下拖：插回 oldIndex 位置
          parent.insertBefore(item, parent.children[oldIndex])
        } else {
          // 向上拖：插到 oldIndex+1 之前（或末尾）
          parent.insertBefore(item, parent.children[oldIndex + 1] || null)
        }

        // el-table 绑定的是 paginatedTestCases（分页数据），索引需要加偏移
        const pageOffset = (currentPage.value - 1) * pageSize.value
        const globalOldIndex = pageOffset + oldIndex
        const globalNewIndex = pageOffset + newIndex

        // 更新 filteredTestCases 的顺序
        const list = [...filteredTestCases.value]
        const [moved] = list.splice(globalOldIndex, 1)
        list.splice(globalNewIndex, 0, moved)

        // 同步更新 testCases 数组中对应元素的 order
        const orders = list.map((tc, index) => ({ id: tc.id, order: index }))
        
        // 更新本地 testCases 数组的 order
        orders.forEach(item => {
          const tc = testCases.value.find(t => t.id === item.id)
          if (tc) tc.order = item.order
        })

        // 恢复选中状态
        nextTick(() => {
          if (_dragSelectedCases.length > 0 && testCaseTableRef.value) {
            testCaseTableRef.value.clearSelection()
            _dragSelectedCases.forEach(row => {
              testCaseTableRef.value.toggleRowSelection(row, true)
            })
          }
        })

        // 调用后端批量排序API持久化
        try {
          await batchReorderTestCases(orders)
        } catch (error) {
          console.error('保存用例排序失败:', error)
          ElMessage.error('保存排序失败')
          // 回滚：重新加载
          await loadTestCases()
        }
      }
    })
  })
}

// 监听 filteredTestCases 变化重新初始化拖拽
watch(filteredTestCases, () => {
  initSortable()
}, { deep: false })

// 组件挂载
// 操作列 actions
const getCaseActions = (row) => [
  { key: 'run', label: '执行', onClick: (r) => runTestCase(r) },
  { key: 'edit', label: '编辑', onClick: (r) => editTestCase(r) },
  { key: 'copy', label: '复制', onClick: (r) => copyTestCase(r) },
  { key: 'history', label: '记录', onClick: (r) => viewExecutionHistory(r) },
  { key: 'delete', label: '删除', danger: true, onClick: (r) => deleteTestCase(r) }
]

onMounted(async () => {
  console.log('TestCaseManager onMounted 开始执行...')
  await loadProjects()
  console.log('loadProjects 完成，准备加载变量函数...')
  await loadVariableFunctions()
  console.log('loadVariableFunctions 完成')

  if (projects.value.length > 0) {
    projectId.value = projects.value[0].id
    await onProjectChange()
  }
  initSortable()
})
</script>

<style scoped>
/* ============================================================
   元素树形下拉节点样式
   ============================================================ */
.element-tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  overflow: hidden;
}
.element-tree-node-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.element-type-tag {
  font-size: 11px;
  padding: 1px 5px;
  border-radius: 3px;
  background-color: var(--brand-50);
  color: var(--brand-600);
  white-space: nowrap;
  flex-shrink: 0;
}

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
  position: relative; /* 为右侧 el-drawer 的 absolute 定位提供参照，确保抽屉高度被 workspace 约束 */
}

/* ============================================================
   面板通用
   ============================================================ */
.workspace .panel {
  min-height: 0;
}

.workspace .panel__header {
  flex-shrink: 0;
}

.workspace .panel__body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

/* ============================================================
   左侧：分组面板
   ============================================================ */
.group-panel {
  width: var(--group-w);
  flex-shrink: 0;
}

.group-panel .panel__body {
  padding: var(--space-2);
}

.panel__action {
  --el-button-text-color: var(--brand-600);
  font-weight: 500;
}

.group-tree-wrapper {
  display: flex;
  flex-direction: column;
}

.group-tree-node {
  display: flex;
  align-items: center;
  gap: 0;
  font-size: 13px;
  flex: 1;
  overflow: hidden;
  padding-left: 2px;
}

.group-node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-count {
  font-size: 11px;
  color: var(--gray-500);
  background: var(--gray-100);
  border-radius: 10px;
  padding: 1px 7px;
  min-width: 18px;
  text-align: center;
  flex-shrink: 0;
}

/* el-tree 节点样式 */
.group-panel :deep(.el-tree) {
  background: transparent;
  --el-tree-node-hover-bg-color: transparent;
}

.group-panel :deep(.el-tree-node__content) {
  height: 36px;
  border-radius: var(--radius-md);
  padding-left: 4px !important;
  margin: 2px 0;
  gap: 4px;
}

.group-panel :deep(.el-tree-node__content:hover) {
  background: var(--gray-100);
}

.group-panel :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: var(--brand-50);
}

.group-panel :deep(.el-tree-node.is-current > .el-tree-node__content .group-node-label) {
  color: var(--brand-700);
  font-weight: 500;
}

.group-panel :deep(.el-tree-node__expand-icon) {
  font-size: 12px;
  color: var(--gray-500);
}

.group-panel :deep(.el-tree-node__expand-icon.is-leaf) {
  color: transparent;
}

/* 分组右键菜单 */
.group-context-menu {
  position: fixed;
  z-index: 2000;
  background: var(--gray-0);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-lg);
  padding: 4px 0;
  min-width: 120px;
}

.group-context-menu .context-menu-item {
  padding: 6px 16px;
  cursor: pointer;
  font-size: 13px;
  color: var(--gray-700);
}

.group-context-menu .context-menu-item:hover {
  background: var(--gray-50);
}

.group-context-menu .context-menu-item.danger {
  color: var(--error);
}

.group-context-menu .context-menu-item.danger:hover {
  background: var(--error-bg);
}

/* ============================================================
   中间列：搜索区域 + 用例列表面板
   ============================================================ */
.list-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* 搜索区域卡片：覆盖 global 默认 margin-bottom，由 list-column 的 gap 接管间距 */
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

.test-case-table-wrapper {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

/* ===== 批量操作工具栏 ===== */
.batch-toolbar,
.batch-edit-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  margin-bottom: 8px;
  border-radius: 6px;
  font-size: 13px;
}
.batch-toolbar {
  background: var(--brand-50, #ebf3fe);
  border: 1px solid var(--brand-200, #b3d8ff);
  color: var(--gray-700, #334155);
}
.batch-edit-bar {
  background: #fff7e6;
  border: 1px solid #ffd591;
  color: #874d00;
}
.batch-toolbar__info {
  font-weight: 600;
  color: var(--brand-600, #1890ff);
}
.batch-edit-bar .batch-toolbar__info {
  color: #d46b08;
}
.batch-toolbar__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.batch-name-input {
  width: 100%;
}
/* 批量工具栏进入/退出过渡 */
.batch-bar-slide-enter-active,
.batch-bar-slide-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.batch-bar-slide-enter-from,
.batch-bar-slide-leave-to {
  opacity: 0;
  max-height: 0;
  margin-bottom: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.batch-bar-slide-enter-to,
.batch-bar-slide-leave-from {
  opacity: 1;
  max-height: 60px;
}

.step-count {
  color: var(--brand-600);
  font-weight: 600;
  font-size: 13px;
}

.update-time {
  font-size: 12px;
  color: var(--gray-500);
  white-space: nowrap;
}

.precondition-text {
  font-size: 12px;
  color: var(--gray-700);
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

.precondition-empty {
  color: var(--gray-400);
}

.execution-time {
  font-size: 12px;
  color: var(--gray-500);
  white-space: nowrap;
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

.list-panel :deep(.el-table .active-row > td.el-table__cell) {
  background: var(--brand-50) !important;
}

.list-panel :deep(.el-table .active-row:hover > td.el-table__cell) {
  background: var(--brand-50) !important;
}

.list-panel :deep(.el-table .active-row td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 0 var(--brand-500);
}

.list-panel :deep(.el-table .el-table__body-wrapper td:first-child .cell),
.list-panel :deep(.el-table .el-table__header-wrapper th:first-child .cell) {
  padding-left: 12px;
}

/* 状态标签 */
.status-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  line-height: 20px;
  font-weight: 500;
}

.status-tag.status-normal {
  background: var(--info-bg);
  color: var(--brand-700);
}

.status-tag.status-passed {
  background: var(--success-bg);
  color: #059669;
}

.status-tag.status-failed {
  background: var(--error-bg);
  color: #dc2626;
}

.status-tag.status-skipped {
  background: var(--warning-bg, #fef3c7);
  color: #d97706;
}

/* 操作按钮 */
.op-btns {
  display: flex;
  align-items: center;
  gap: 0;
  flex-wrap: nowrap;
}

.op-btn {
  padding: 2px !important;
  border-radius: var(--radius-sm);
  font-size: 13px;
  transition: opacity 0.15s;
}

.op-btn--text {
  --el-button-text-color: var(--brand-500);
  font-size: 13px;
  padding: 0 4px !important;
}

.op-btn--text:hover {
  opacity: 0.8;
  color: var(--brand-600) !important;
}

.op-btn--danger {
  --el-button-text-color: var(--error);
}

.op-btn--danger:hover {
  opacity: 0.8;
  color: var(--error) !important;
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
   右侧：用例详情抽屉
   ============================================================ */
/* 让 overlay 不拦截底层点击，抽屉本身仍可交互 */
:deep(.detail-drawer) {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.08);
  pointer-events: auto;
  transition: width 0.2s ease;
  overflow: visible !important;
}

/* 收起状态下阴影减弱 */
:deep(.detail-drawer--collapsed) {
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.05);
}

/* 让 __body 不裁剪浮在外侧的 toggle 按钮 */
:deep(.detail-drawer .el-drawer__body) {
  padding: 0;
  display: flex;
  flex-direction: row;
  overflow: visible !important;
  height: 100%;
  min-height: 0;
}

/* 左边缘三角切换按钮 - 浮动胶囊样式 */
.detail-toggle {
  position: absolute;
  left: -10px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  cursor: pointer;
}

.detail-toggle__btn {
  width: 20px;
  height: 40px;
  border-radius: 6px;
  background: var(--gray-0);
  border: 1px solid var(--gray-200);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gray-500);
  transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
}

.detail-toggle:hover .detail-toggle__btn {
  background: var(--brand-50);
  border-color: var(--brand-300);
  color: var(--brand-600);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
}

/* 关闭按钮样式 */
.detail-close-btn {
  margin-left: var(--space-2);
}

.detail-resizer {
  width: 4px;
  cursor: col-resize;
  background: var(--gray-200);
  flex-shrink: 0;
  transition: background 0.2s;
}

.detail-resizer:hover {
  background: var(--brand-400);
}

.detail-drawer-body {
  flex: 1;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--gray-0);
}

.detail-body {
  padding: 0 !important;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.test-case-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

/* 详情工具栏 */
.detail-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--gray-100);
  flex-shrink: 0;
}

.detail-toolbar .el-button {
  margin: 0;
}

.toolbar-select {
  width: 110px;
}

/* 步骤容器 */
.steps-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  padding: var(--space-2) var(--space-2) 0;
  gap: var(--space-2);
}

/* 可折叠条件区块 */
.condition-section {
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  background: var(--gray-0);
  overflow: hidden;
  margin-bottom: var(--space-2);
  flex-shrink: 0;
}

.condition-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px var(--space-3);
  cursor: pointer;
  user-select: none;
  background: var(--gray-50);
  transition: background 0.15s;
}

.condition-section .section-header:hover {
  background: var(--gray-100);
}

.condition-section .section-header h4 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-700);
}

.condition-section .section-content {
  padding: var(--space-3);
}

.section-tip {
  color: var(--gray-500);
  font-size: 12px;
  margin-top: var(--space-3);
}

/* 步骤列表标题 */
.steps-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px var(--space-3);
  cursor: pointer;
  user-select: none;
  background: var(--gray-50);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  flex-shrink: 0;
  transition: background 0.15s;
}

.steps-header:hover {
  background: var(--gray-100);
}

.steps-header:hover {
  background: var(--gray-50);
}

.steps-header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.steps-header h4 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-700);
}

/* 步骤滚动区 */
.steps-scroll-container {
  overflow-y: auto;
  flex: 1;
  min-height: 0;
  padding: var(--space-1) var(--space-2);
}

.steps-scroll-container::-webkit-scrollbar {
  width: 6px;
}
.steps-scroll-container::-webkit-scrollbar-track {
  background: var(--gray-50);
  border-radius: 3px;
}
.steps-scroll-container::-webkit-scrollbar-thumb {
  background: var(--gray-300);
  border-radius: 3px;
}
.steps-scroll-container::-webkit-scrollbar-thumb:hover {
  background: var(--gray-500);
}

.steps-list {
  padding: 2px 0 var(--space-3);
}

/* 步骤卡片 */
.step-card {
  border: 1px solid var(--brand-200);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-2);
  background: var(--gray-0);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.step-card:hover {
  border-color: var(--brand-300);
  box-shadow: var(--shadow-sm);
}

.step-card.expanded {
  border-color: var(--brand-300);
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px var(--space-3);
  cursor: pointer;
  transition: background 0.12s;
}

.step-header:hover {
  background: var(--gray-50);
}

.step-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.drag-handle {
  cursor: move;
  color: var(--gray-300);
  flex-shrink: 0;
}

.drag-handle:hover {
  color: var(--gray-500);
}

.step-number {
  font-size: 13px;
  font-weight: 500;
  color: var(--gray-900);
  flex-shrink: 0;
  min-width: 20px;
}

.step-desc-text {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: var(--gray-900);
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.step-desc-text:hover {
  color: var(--brand-600);
}

.step-right {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}

.step-right :deep(.el-button--danger) {
  --el-button-text-color: var(--gray-300);
}

.step-right :deep(.el-button--danger:hover) {
  --el-button-text-color: var(--error);
  background: var(--error-bg);
}

.step-content {
  padding: var(--space-3);
  border-top: 1px solid var(--gray-100);
}

/* 步骤表单（标签和控件同行） */
.step-param {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.step-param:last-child {
  margin-bottom: 0;
}

.step-param label {
  font-size: 12px;
  font-weight: 500;
  color: var(--gray-700);
  flex-shrink: 0;
  width: 90px;
  text-align: left;
}

.step-input {
  width: 100% !important;
}

.step-param :deep(.el-input__wrapper),
.step-param :deep(.el-select .el-input__wrapper),
.step-param :deep(.el-textarea__inner) {
  border-radius: var(--radius-md);
}

.step-input-group {
  display: flex;
  flex-direction: row;
  gap: var(--space-2);
  flex: 1;
  min-width: 0;
}

.step-input-group--col {
  flex-direction: column;
  gap: var(--space-2);
}

.assert-value-row {
  display: flex;
  gap: 5px;
  align-items: center;
}

.assert-value-row .step-input {
  flex: 1;
}

.step-param :deep(.el-input-number) {
  width: 100%;
}

/* ============================================================
   空状态
   ============================================================ */
.no-selection {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  flex: 1;
}

/* ============================================================
   执行结果区
   ============================================================ */
.execution-result {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  margin: var(--space-2);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  background: var(--gray-0);
  overflow: hidden;
}

.execution-result .result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--gray-100);
  background: var(--gray-50);
  flex-shrink: 0;
}

.result-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-900);
}

.execution-result .result-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: var(--space-3);
  overflow: hidden;
}

.result-content :deep(.el-tabs) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.result-content :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.result-content :deep(.el-tab-pane) {
  height: 100%;
  overflow: auto;
}

/* 执行日志 */
.logs-container {
  max-height: 100%;
  overflow-y: auto;
  background: var(--gray-50);
  padding: 8px;
  border-radius: var(--radius-sm);
}

.log-item {
  margin-bottom: 6px;
  padding: 8px 12px;
  background: var(--gray-0);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--brand-500);
}

.log-item:last-child {
  margin-bottom: 0;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 0;
  flex-wrap: wrap;
}

.log-action {
  font-weight: 500;
  color: var(--gray-700);
  font-size: 13px;
}

.log-desc {
  color: var(--gray-500);
  font-size: 13px;
}

.log-value {
  color: var(--brand-600);
  font-size: 12px;
  font-weight: 500;
  background: var(--brand-50);
  padding: 1px 6px;
  border-radius: 3px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-value--output {
  color: #10b981;
  background: #ecfdf5;
}

.log-error {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--error);
  background: var(--error-bg);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  margin-top: var(--space-2);
  font-size: 13px;
}

.log-error .error-message {
  margin: 0;
  padding: 0;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  flex: 1;
}

.log-error .el-icon {
  flex-shrink: 0;
}

/* 截图网格 */
.screenshots-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-4);
  padding: var(--space-2);
}

.screenshot-item {
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.screenshot-item:hover {
  transform: translateY(-4px);
}

.screenshot-wrapper {
  position: relative;
  width: 100%;
  min-height: 180px;
  background: var(--gray-100);
  border-radius: var(--radius-md);
  border: 2px solid var(--gray-200);
  overflow: hidden;
  transition: border-color 0.3s ease;
}

.screenshot-item:hover .screenshot-wrapper {
  border-color: var(--brand-500);
}

.screenshot-wrapper img {
  width: 100%;
  height: auto;
  display: block;
  transition: opacity 0.3s ease;
}

.screenshot-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.screenshot-item:hover .screenshot-overlay {
  opacity: 1;
}

.zoom-icon {
  font-size: 40px;
  color: #fff;
}

.screenshot-placeholder,
.screenshot-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  color: var(--gray-500);
  font-size: 13px;
}

.screenshot-placeholder .el-icon,
.screenshot-error .el-icon {
  font-size: 30px;
  margin-bottom: var(--space-2);
}

.screenshot-error {
  color: var(--error);
}

.screenshot-info {
  margin-top: var(--space-2);
}

.screenshot-description {
  margin: 0 0 4px 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--gray-900);
  text-align: left;
}

.screenshot-meta {
  margin: 0 0 2px 0;
  font-size: 12px;
  color: var(--gray-500);
  text-align: left;
}

.screenshot-time {
  margin: 0;
  font-size: 11px;
  color: var(--gray-500);
  text-align: left;
}

/* 错误信息 */
.errors-container {
  padding: var(--space-2);
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.error-item {
  background: var(--gray-0);
  border: 2px solid var(--error);
  border-radius: var(--radius-md);
  padding: var(--space-4);
}

.error-item:last-child {
  margin-bottom: 0;
}

.error-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--gray-100);
  flex-wrap: wrap;
  gap: var(--space-2);
}

.error-header .el-tag {
  font-size: 14px;
  padding: 8px var(--space-3);
  font-weight: 600;
  display: inline-flex;
  align-items: center;
}

.error-tag-inner {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.error-step {
  background: var(--error-bg);
  color: var(--error);
  padding: 4px var(--space-3);
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 13px;
}

.error-meta {
  background: var(--gray-50);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-3);
}

.meta-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: var(--space-2);
}

.meta-item:last-child {
  margin-bottom: 0;
}

.meta-label {
  font-weight: 600;
  color: var(--gray-500);
  min-width: 80px;
  margin-right: var(--space-2);
  font-size: 13px;
}

.meta-value {
  color: var(--gray-900);
  flex: 1;
  font-size: 13px;
  word-break: break-word;
}

.error-details {
  background: #2d2d2d;
  border-radius: var(--radius-md);
  overflow: hidden;
}

.details-header {
  background: #1e1e1e;
  color: #fff;
  padding: 8px var(--space-3);
  font-weight: 600;
  font-size: 13px;
  border-bottom: 1px solid #3d3d3d;
}

.details-content {
  color: #ff6b6b;
  padding: var(--space-3);
  margin: 0;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 400px;
  overflow-y: auto;
}

.details-content::-webkit-scrollbar {
  width: 6px;
}
.details-content::-webkit-scrollbar-track {
  background: #1e1e1e;
}
.details-content::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 3px;
}
.details-content::-webkit-scrollbar-thumb:hover {
  background: #777;
}

/* ============================================================
   截图预览对话框
   ============================================================ */
.screenshot-preview {
  display: flex;
  flex-direction: column;
}

.preview-info {
  margin-bottom: var(--space-4);
  padding: var(--space-3);
  background: var(--gray-50);
  border-radius: var(--radius-md);
}

.preview-info h4 {
  margin: 0 0 var(--space-2) 0;
  font-size: 16px;
  color: var(--gray-900);
}

.preview-info p {
  margin: 5px 0;
  font-size: 14px;
  color: var(--gray-700);
}

.preview-image {
  display: flex;
  justify-content: center;
  align-items: center;
  background: var(--gray-100);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  max-height: 70vh;
  overflow: auto;
}

.preview-image img {
  max-width: 100%;
  height: auto;
  border-radius: var(--radius-sm);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* ============================================================
   工具按钮（数据工厂 / 变量助手）
   ============================================================ */
.data-factory-btn {
  background-color: var(--brand-500) !important;
  border-color: var(--brand-500) !important;
  color: #fff !important;
}

.data-factory-btn:hover {
  background-color: var(--brand-600) !important;
  border-color: var(--brand-600) !important;
}

.variable-helper-btn {
  background-color: var(--success);
  border-color: var(--success);
  color: #fff;
  flex-shrink: 0;
}

.variable-helper-btn:hover {
  background-color: #0ea272;
  border-color: #0ea272;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}

/* 执行记录弹窗 */
.history-detail-header {
  margin-bottom: 8px;
}

.history-detail-logs .log-item {
  margin-bottom: 6px;
  padding: 8px 12px;
  background: var(--gray-0);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--brand-500);
}

.history-detail-logs .log-item:last-child {
  margin-bottom: 0;
}

.history-detail-logs .log-header {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.history-detail-logs .log-action {
  font-weight: 500;
  color: var(--gray-700);
  font-size: 13px;
}

.history-detail-logs .log-desc {
  color: var(--gray-500);
  font-size: 13px;
}

.history-detail-logs .log-error {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--error);
  background: var(--error-bg);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  margin-top: var(--space-2);
  font-size: 13px;
}

.history-detail-logs .log-error .error-message {
  margin: 0;
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 12px;
}
</style>
