<template>
  <div class="page-container">
    <!-- 顶部标题栏 -->
    <div class="page-titlebar">
      <h1 class="page-title">{{ routePlatform === 'web' ? 'Web端自动化' : routePlatform === 'app' ? 'APP端自动化' : 'AI自动化测试' }}</h1>
      <div class="titlebar-actions">
        <el-select v-model="projectId" placeholder="选择项目" class="titlebar-select" clearable @change="onProjectChange">
          <el-option v-for="p in projectList" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-button type="primary" size="small" @click="showImportDialog = true">
          <el-icon><Download /></el-icon>
          <span>从AI导入</span>
        </el-button>
        <el-button size="small" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          <span>新建用例</span>
        </el-button>
      </div>
    </div>

    <!-- 三栏工作区 -->
    <div class="workspace">
      <!-- 左侧：分组面板 -->
      <section class="panel group-panel">
        <div class="panel__header">
          <span class="panel__title">用例分组</span>
          <el-button text size="small" class="panel__action" @click="showGroupDialog = true">
            <el-icon><Plus /></el-icon>
            <span>添加</span>
          </el-button>
        </div>
        <div class="panel__body group-tree-wrapper">
          <div class="group-list">
            <div
              class="group-item"
              :class="{ active: !currentGroupId }"
              @click="selectGroup(null)"
            >全部</div>
            <div
              class="group-item"
              :class="{ active: currentGroupId === 'ungrouped' }"
              @click="selectGroup('ungrouped')"
            >未分组</div>
            <div
              v-for="g in groups" :key="g.id"
              class="group-item"
              :class="{ active: currentGroupId === g.id }"
              @click="selectGroup(g.id)"
            >
              <span class="group-node-label">{{ g.name }}</span>
              <span class="group-count">{{ g.case_count || 0 }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 中间列：搜索区域 + 用例列表 -->
      <div class="list-column">
        <!-- 搜索区域卡片 -->
        <div class="filter-bar">
          <el-form :inline="true">
            <el-form-item label="用例名称">
              <el-input v-model="searchText" placeholder="搜索用例名称" clearable style="width:220px" @input="onSearchInput">
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item v-if="!routePlatform" label="平台">
              <el-select v-model="filterPlatform" placeholder="全部" clearable style="width:120px" @change="loadCases">
                <el-option label="Web端" value="web" />
                <el-option label="APP端" value="app" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- 用例列表面板 -->
        <section class="panel list-panel">
          <div class="panel__header">
            <span class="panel__title">用例列表</span>
            <div class="panel__header-actions">
              <el-button size="small" @click="batchRun" :disabled="!selectedIds.length" :loading="batchRunning">
                <el-icon><VideoPlay /></el-icon>批量执行
              </el-button>
              <el-button size="small" type="danger" plain @click="handleBatchDelete" :disabled="!selectedIds.length">
                <el-icon><Delete /></el-icon>批量删除
              </el-button>
            </div>
          </div>

          <div class="panel__body table-wrapper">
            <!-- 批量操作浮动工具栏 -->
            <transition name="batch-bar-slide">
              <div v-if="selectedIds.length > 0" class="batch-toolbar">
                <span class="batch-toolbar__info">已选 {{ selectedIds.length }} 个用例</span>
                <div class="batch-toolbar__actions">
                  <el-button size="small" type="success" :icon="VideoPlay" @click="batchRun" :loading="batchRunning">批量执行</el-button>
                  <el-button size="small" type="danger" :icon="Delete" @click="handleBatchDelete">批量删除</el-button>
                  <el-button size="small" text @click="clearSelection">取消选择</el-button>
                </div>
              </div>
            </transition>

            <div class="table-area">
              <el-table
                :data="paginatedCases"
                height="100%"
                size="small"
                @selection-change="onSelectionChange"
                @current-change="handleRowClick"
                row-key="id"
              >
                <el-table-column type="selection" width="40" />
                <el-table-column type="index" label="序号" width="50" align="center" />
                <el-table-column prop="name" label="用例名称" min-width="200" show-overflow-tooltip />
                <el-table-column prop="platform" label="平台" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.platform === 'web' ? '' : 'warning'" size="small">
                      {{ row.platform === 'web' ? 'Web' : 'APP' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="step_count" label="步骤" width="60" align="center">
                  <template #default="{ row }">
                    <span class="step-count">{{ row.steps?.length || row.step_count || 0 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="source" label="来源" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.source === 'ai_import' ? 'success' : 'info'" size="small">
                      {{ row.source === 'ai_import' ? 'AI导入' : '手动' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="last_status" label="最近状态" width="90" align="center">
                  <template #default="{ row }">
                    <el-tag :type="statusTagType(row.last_status)" size="small">{{ statusLabel(row.last_status) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="last_executed_at" label="执行时间" width="160" align="center">
                  <template #default="{ row }">
                    <span v-if="row.last_executed_at">{{ formatDateTime(row.last_executed_at) }}</span>
                    <span v-else class="text-muted">-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="last_duration" label="时长" width="80" align="center">
                  <template #default="{ row }">
                    <span v-if="row.last_duration != null && row.last_duration > 0">{{ Math.round(row.last_duration) }}s</span>
                    <span v-else class="text-muted">-</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="180" fixed="right">
                  <template #default="{ row }">
                    <ActionCell :actions="getCaseActions(row)" :row="row" :max-visible="3" />
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50]"
              :total="filteredCases.length"
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
            <div v-if="selectedCase" class="detail-header-actions">
              <el-button size="small" type="primary" @click="saveCaseFromDrawer" :loading="saving">
                <el-icon><Check /></el-icon>保存
              </el-button>
              <el-button size="small" type="success" @click="runCase(selectedCase)" :loading="runningIds[selectedCase.id]">
                <el-icon><VideoPlay /></el-icon>执行
              </el-button>
              <el-button size="small" @click="closeDetailDrawer">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>
          <div class="panel__body detail-body">
            <div v-if="selectedCase" class="case-detail">
              <!-- 视图切换标签 -->
              <el-tabs v-model="detailActiveTab" class="detail-tabs">
                <el-tab-pane label="基本信息" name="info">
                  <el-form :model="drawerForm" label-width="100px" class="detail-form">
                    <el-form-item label="用例名称" required>
                      <el-input v-model="drawerForm.name" placeholder="请输入用例名称" />
                    </el-form-item>
                    <el-form-item label="平台" required>
                      <el-radio-group v-model="drawerForm.platform" :disabled="!!selectedCase">
                        <el-radio value="web">Web端</el-radio>
                        <el-radio value="app">APP端</el-radio>
                      </el-radio-group>
                    </el-form-item>
                    <el-form-item label="所属分组">
                      <el-select v-model="drawerForm.group_id" placeholder="无分组" clearable style="width:100%">
                        <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="描述">
                      <el-input v-model="drawerForm.description" type="textarea" :rows="2" />
                    </el-form-item>

                    <!-- Web端配置 -->
                    <template v-if="drawerForm.platform === 'web'">
                      <el-divider content-position="left">Web配置</el-divider>
                      <el-form-item label="目标URL" required>
                        <el-input v-model="drawerForm.url" placeholder="https://example.com" />
                      </el-form-item>
                      <el-form-item label="运行模式">
                        <el-radio-group v-model="drawerForm.headless">
                          <el-radio :value="false">有头模式</el-radio>
                          <el-radio :value="true">无头模式</el-radio>
                        </el-radio-group>
                      </el-form-item>
                      <el-form-item label="缓存策略">
                        <el-select v-model="drawerForm.cache_strategy">
                          <el-option label="默认" value="normal" />
                          <el-option label="每次清除" value="clear" />
                          <el-option label="全新会话" value="new" />
                        </el-select>
                      </el-form-item>
                      <el-form-item label="新开页签">
                        <el-switch v-model="drawerForm.new_tab" />
                      </el-form-item>
                      <el-form-item label="User-Agent">
                        <el-input v-model="drawerForm.user_agent" placeholder="留空使用默认UA" />
                      </el-form-item>
                      <el-form-item label="视口尺寸">
                        <div style="display:flex;gap:8px;align-items:center">
                          <el-input-number v-model="drawerForm.viewport_width" :min="320" :max="3840" :step="10" controls-position="right" style="width:120px" />
                          <span style="color:#999">×</span>
                          <el-input-number v-model="drawerForm.viewport_height" :min="240" :max="2160" :step="10" controls-position="right" style="width:120px" />
                        </div>
                      </el-form-item>
                      <el-form-item label="设备缩放比">
                        <el-input-number v-model="drawerForm.device_scale_factor" :min="0.5" :max="3" :step="0.25" :precision="2" controls-position="right" style="width:120px" />
                      </el-form-item>
                      <el-form-item label="Cookie文件">
                        <el-input v-model="drawerForm.cookie_file" placeholder="Cookie存储文件路径（可选）" />
                      </el-form-item>
                      <el-form-item label="网络空闲等待">
                        <div style="display:flex;gap:8px;align-items:center">
                          <el-input-number v-model="drawerForm.wait_for_network_idle_timeout" :min="0" :max="60000" :step="1000" controls-position="right" placeholder="ms" style="width:140px" />
                          <span style="color:#999;font-size:12px">ms (0=不等待)</span>
                          <el-checkbox v-model="drawerForm.continue_on_network_idle_error" style="margin-left:8px">超时时继续</el-checkbox>
                        </div>
                      </el-form-item>
                    </template>

                    <!-- APP端配置 -->
                    <template v-if="drawerForm.platform === 'app'">
                      <el-divider content-position="left">APP配置</el-divider>
                      <el-form-item label="设备ID">
                        <el-input v-model="drawerForm.device_id" placeholder="如：adb devices获取" />
                      </el-form-item>
                      <el-form-item label="包名">
                        <el-input v-model="drawerForm.package_name" placeholder="com.example.app" />
                      </el-form-item>
                      <el-form-item label="Activity">
                        <el-input v-model="drawerForm.app_activity" placeholder=".MainActivity" />
                      </el-form-item>
                    </template>
                  </el-form>
                </el-tab-pane>

                <el-tab-pane label="测试步骤" name="steps">
                  <div class="steps-editor-drawer">
                    <div v-for="(step, idx) in drawerForm.steps" :key="idx" class="step-row-block">
                      <div class="step-row-main">
                        <span class="step-order">{{ idx + 1 }}.</span>
                        <el-select v-model="step.type" style="width:90px" size="small">
                          <el-option label="操作" value="action" />
                          <el-option label="断言" value="assert" />
                        </el-select>
                        <el-input v-model="step.instruction" placeholder="步骤描述（支持${变量名}引用）" style="flex:1" size="small" />
                        <el-button link type="danger" size="small" @click="drawerForm.steps.splice(idx, 1)">
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </div>
                      <div class="step-row-params">
                        <el-input v-model="step.input_value" placeholder="输入值（支持${变量}和数据工厂函数）" style="flex:1" size="small">
                          <template #append>
                            <el-button size="small" @click="openVariableHelper(step, 'input_value')" title="变量助手">
                              <el-icon><MagicStick /></el-icon>
                            </el-button>
                          </template>
                        </el-input>
                        <el-input v-model="step.output_var" placeholder="输出变量名" style="width:120px" size="small" />
                      </div>
                    </div>
                    <el-button link type="primary" @click="addStepToDrawer" style="margin-top:4px">+ 添加步骤</el-button>
                  </div>
                </el-tab-pane>

                <el-tab-pane label="变量与SQL" name="variables">
                  <div style="margin-bottom:12px">
                    <div style="font-weight:600;margin-bottom:8px">前置数据SQL</div>
                    <el-input v-model="drawerForm.precondition_sql" type="textarea" :rows="3" placeholder="用例执行前的数据准备SQL，支持${变量名}引用，禁止DROP语句" />
                  </div>
                  <div style="margin-bottom:12px">
                    <div style="font-weight:600;margin-bottom:8px">后置清理SQL</div>
                    <el-input v-model="drawerForm.postcondition_sql" type="textarea" :rows="3" placeholder="用例执行后的数据清理SQL，只允许DELETE/UPDATE/TRUNCATE，支持${变量名}引用" />
                  </div>
                  <div>
                    <div style="font-weight:600;margin-bottom:8px">输出变量</div>
                    <div v-for="(v, idx) in drawerForm.output_variables" :key="idx" style="display:flex;gap:8px;margin-bottom:6px;align-items:center">
                      <el-input v-model="v.var_name" placeholder="变量名" style="width:120px" size="small" />
                      <el-select v-model="v.source" style="width:120px" size="small">
                        <el-option label="步骤输出" value="step" />
                        <el-option label="表达式" value="expression" />
                      </el-select>
                      <el-input-number v-model="v.step_index" placeholder="步骤序号" :min="1" size="small" style="width:100px" v-if="v.source === 'step'" />
                      <el-button link type="danger" size="small" @click="drawerForm.output_variables.splice(idx, 1)"><el-icon><Delete /></el-icon></el-button>
                    </div>
                    <el-button link type="primary" size="small" @click="drawerForm.output_variables.push({var_name:'',source:'step',step_index:1})">+ 添加变量</el-button>
                  </div>
                </el-tab-pane>

                <el-tab-pane label="执行结果" name="result">
                  <div v-if="drawerResultLoading" style="text-align:center;padding:40px">
                    <el-icon class="is-loading" style="font-size:24px"><Loading /></el-icon>
                    <div style="margin-top:8px">加载中...</div>
                  </div>
                  <template v-else-if="drawerResultData">
                    <el-descriptions :column="2" border size="small" style="margin-bottom:16px">
                      <el-descriptions-item label="状态">
                        <el-tag :type="statusTagType(drawerResultData.status)" size="small">{{ statusLabel(drawerResultData.status) }}</el-tag>
                      </el-descriptions-item>
                      <el-descriptions-item label="耗时">{{ drawerResultData.duration ? drawerResultData.duration.toFixed(1) + 's' : '-' }}</el-descriptions-item>
                    </el-descriptions>

                    <!-- 三页签：步骤结果 / 错误信息 / 回放报告 -->
                    <el-tabs v-model="drawerResultTab" class="result-tabs">
                      <el-tab-pane label="步骤结果" name="steps">
                        <div v-if="drawerResultData.step_results && drawerResultData.step_results.length">
                          <div v-for="(s, idx) in drawerResultData.step_results" :key="idx" class="step-result-row">
                            <el-tag :type="s.status === 'passed' ? 'success' : 'danger'" size="small">{{ s.status }}</el-tag>
                            <span style="margin-left:8px;flex:1">{{ s.instruction }}</span>
                            <el-tag v-if="s.output_var" type="warning" size="small" style="margin-left:6px">→ {{ s.output_var }}</el-tag>
                          </div>
                        </div>
                        <div v-else style="color:#999;text-align:center;padding:20px">暂无步骤结果</div>

                        <!-- 变量流转 -->
                        <div v-if="drawerResultData.variable_snapshot && Object.keys(drawerResultData.variable_snapshot).length" style="margin-top:16px">
                          <div style="font-weight:600;margin-bottom:8px">变量流转</div>
                          <el-table :data="Object.entries(drawerResultData.variable_snapshot).map(([k,v]) => ({var_name:k, value: typeof v === 'object' ? JSON.stringify(v) : v}))" border size="small" style="width:100%">
                            <el-table-column prop="var_name" label="变量名" width="160" />
                            <el-table-column prop="value" label="实际值" show-overflow-tooltip />
                          </el-table>
                        </div>

                        <!-- SQL执行结果 -->
                        <div v-if="drawerResultData.sql_results && drawerResultData.sql_results.length" style="margin-top:16px">
                          <div style="font-weight:600;margin-bottom:8px">SQL执行</div>
                          <div v-for="(sql, idx) in drawerResultData.sql_results" :key="idx" style="margin-bottom:8px;padding:8px;background:#f5f7fa;border-radius:4px;font-size:12px">
                            <div style="font-weight:500;color:#606266">{{ sql.type === 'pre' ? '前置SQL' : '后置SQL' }}</div>
                            <pre style="margin:4px 0;color:#303133;white-space:pre-wrap">{{ sql.sql }}</pre>
                            <el-tag :type="sql.success ? 'success' : 'danger'" size="small">{{ sql.success ? '成功' : '失败' }}</el-tag>
                            <span v-if="sql.rows_affected" style="margin-left:8px;color:#909399;font-size:12px">影响行数: {{ sql.rows_affected }}</span>
                            <div v-if="sql.error" style="color:#f56c6c;margin-top:4px">{{ sql.error }}</div>
                          </div>
                        </div>

                        <div v-if="drawerResultData.logs" style="margin-top:16px">
                          <div style="font-weight:600;margin-bottom:8px">执行日志</div>
                          <pre class="log-box">{{ drawerResultData.logs }}</pre>
                        </div>
                      </el-tab-pane>

                      <el-tab-pane label="错误信息" name="error">
                        <div v-if="drawerResultData.error_message">
                          <pre class="error-box">{{ drawerResultData.error_message }}</pre>
                        </div>
                        <div v-else style="color:#999;text-align:center;padding:40px">无错误信息</div>
                      </el-tab-pane>

                      <el-tab-pane label="回放报告" name="report">
                        <div v-if="drawerResultData.report_url" class="report-container">
                          <div class="report-toolbar">
                            <span class="report-hint">Midscene AI 操作回放</span>
                            <el-button link type="primary" @click="openReportNewTab(drawerResultData.report_url)">新窗口打开</el-button>
                          </div>
                          <iframe :src="getReportSrc(drawerResultData.report_url)" class="report-iframe" frameborder="0" allowfullscreen></iframe>
                        </div>
                        <div v-else style="color:#999;text-align:center;padding:40px">
                          <el-icon style="font-size:32px;margin-bottom:8px"><VideoPlay /></el-icon>
                          <div>暂无回放报告</div>
                          <div style="font-size:12px;margin-top:4px">执行完成后Midscene会自动生成操作回放报告</div>
                        </div>
                      </el-tab-pane>
                    </el-tabs>
                  </template>
                  <div v-else style="color:#999;text-align:center;padding:40px">暂无执行记录</div>
                </el-tab-pane>
              </el-tabs>
            </div>
          </div>
        </div>
      </el-drawer>
    </div>

    <!-- 新建用例弹窗（仅新建用） -->
    <el-dialog v-model="caseDialogVisible" title="新建用例" width="700px" :close-on-click-modal="false" destroy-on-close>
      <el-form :model="caseForm" label-width="100px">
        <el-form-item label="用例名称" required>
          <el-input v-model="caseForm.name" placeholder="请输入用例名称" />
        </el-form-item>
        <el-form-item label="平台" required>
          <el-radio-group v-model="caseForm.platform" :disabled="!!routePlatform">
            <el-radio value="web">Web端</el-radio>
            <el-radio value="app">APP端</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- Web端配置 -->
        <template v-if="caseForm.platform === 'web'">
          <el-form-item label="目标URL" required>
            <el-input v-model="caseForm.url" placeholder="https://example.com" />
          </el-form-item>
          <el-form-item label="运行模式">
            <el-radio-group v-model="caseForm.headless">
              <el-radio :value="false">有头模式</el-radio>
              <el-radio :value="true">无头模式</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="缓存策略">
            <el-select v-model="caseForm.cache_strategy">
              <el-option label="默认" value="normal" />
              <el-option label="每次清除" value="clear" />
              <el-option label="全新会话" value="new" />
            </el-select>
          </el-form-item>
          <el-form-item label="新开页签">
            <el-switch v-model="caseForm.new_tab" />
          </el-form-item>

          <el-divider content-position="left">高级配置</el-divider>
          <el-form-item label="User-Agent">
            <el-input v-model="caseForm.user_agent" placeholder="留空使用默认UA" />
          </el-form-item>
          <el-form-item label="视口尺寸">
            <div style="display:flex;gap:8px;align-items:center">
              <el-input-number v-model="caseForm.viewport_width" :min="320" :max="3840" :step="10" controls-position="right" style="width:120px" />
              <span style="color:#999">×</span>
              <el-input-number v-model="caseForm.viewport_height" :min="240" :max="2160" :step="10" controls-position="right" style="width:120px" />
            </div>
          </el-form-item>
          <el-form-item label="设备缩放比">
            <el-input-number v-model="caseForm.device_scale_factor" :min="0.5" :max="3" :step="0.25" :precision="2" controls-position="right" style="width:120px" />
          </el-form-item>
          <el-form-item label="Cookie文件">
            <el-input v-model="caseForm.cookie_file" placeholder="Cookie存储文件路径（可选）" />
          </el-form-item>
          <el-form-item label="网络空闲等待">
            <div style="display:flex;gap:8px;align-items:center">
              <el-input-number v-model="caseForm.wait_for_network_idle_timeout" :min="0" :max="60000" :step="1000" controls-position="right" placeholder="ms" style="width:140px" />
              <span style="color:#999;font-size:12px">ms (0=不等待)</span>
              <el-checkbox v-model="caseForm.continue_on_network_idle_error" style="margin-left:8px">超时时继续</el-checkbox>
            </div>
          </el-form-item>
        </template>

        <!-- APP端配置 -->
        <template v-if="caseForm.platform === 'app'">
          <el-form-item label="设备ID">
            <el-input v-model="caseForm.device_id" placeholder="如：adb devices获取" />
          </el-form-item>
          <el-form-item label="包名">
            <el-input v-model="caseForm.package_name" placeholder="com.example.app" />
          </el-form-item>
          <el-form-item label="Activity">
            <el-input v-model="caseForm.app_activity" placeholder=".MainActivity" />
          </el-form-item>
        </template>

        <el-form-item label="所属分组">
          <el-select v-model="caseForm.group_id" placeholder="无分组" clearable style="width:100%">
            <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="描述">
          <el-input v-model="caseForm.description" type="textarea" :rows="2" />
        </el-form-item>

        <!-- 步骤编辑 -->
        <el-form-item label="测试步骤">
          <div class="steps-editor">
            <div v-for="(step, idx) in caseForm.steps" :key="idx" class="step-row-block">
              <div class="step-row-main">
                <span class="step-order">{{ idx + 1 }}.</span>
                <el-select v-model="step.type" style="width:90px">
                  <el-option label="操作" value="action" />
                  <el-option label="断言" value="assert" />
                </el-select>
                <el-input v-model="step.instruction" placeholder="步骤描述（支持${变量名}引用）" style="flex:1" />
                <el-button link type="danger" @click="caseForm.steps.splice(idx, 1)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
              <div class="step-row-params">
                <el-input v-model="step.input_value" placeholder="输入值（支持${变量}和数据工厂函数）" style="flex:1">
                  <template #append>
                    <el-button size="small" @click="openVariableHelper(step, 'input_value')" title="变量助手">
                      <el-icon><MagicStick /></el-icon>
                    </el-button>
                  </template>
                </el-input>
                <el-input v-model="step.output_var" placeholder="输出变量名" style="width:120px" />
              </div>
            </div>
            <el-button link type="primary" @click="addStep">+ 添加步骤</el-button>
          </div>
        </el-form-item>

        <!-- 前置/后置SQL -->
        <el-form-item label="前置数据SQL">
          <el-input v-model="caseForm.precondition_sql" type="textarea" :rows="3" placeholder="用例执行前的数据准备SQL，支持${变量名}引用，禁止DROP语句" />
        </el-form-item>
        <el-form-item label="后置清理SQL">
          <el-input v-model="caseForm.postcondition_sql" type="textarea" :rows="3" placeholder="用例执行后的数据清理SQL，只允许DELETE/UPDATE/TRUNCATE，支持${变量名}引用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="caseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCase" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 从AI导入弹窗 -->
    <el-dialog v-model="showImportDialog" title="从AI生成用例导入" width="800px" destroy-on-close>
      <div style="margin-bottom:12px">
        <el-radio-group v-model="importPlatform">
          <el-radio value="web">导入为Web端用例</el-radio>
          <el-radio value="app">导入为APP端用例</el-radio>
        </el-radio-group>
      </div>
      <el-table :data="aiCases" @selection-change="onAISelection" height="350" v-loading="loadingAI">
        <el-table-column type="selection" width="40" />
        <el-table-column prop="case_id" label="编号" width="80" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="priority" label="优先级" width="70" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="doImport" :disabled="!selectedAICases.length" :loading="importing">
          导入选中 ({{ selectedAICases.length }})
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行结果弹窗（保留，用于从操作按钮直接查看） -->
    <el-dialog v-model="resultDialogVisible" title="执行结果" width="900px" destroy-on-close class="detail-dialog-680">
      <div v-if="resultLoading" style="text-align:center;padding:40px">
        <el-icon class="is-loading" style="font-size:24px"><Loading /></el-icon>
        <div style="margin-top:8px">加载中...</div>
      </div>
      <template v-else-if="resultData">
        <el-descriptions :column="3" border size="small" style="margin-bottom:16px">
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType(resultData.status)" size="small">{{ statusLabel(resultData.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="耗时">{{ resultData.duration ? resultData.duration.toFixed(1) + 's' : '-' }}</el-descriptions-item>
          <el-descriptions-item label="执行人">{{ resultData.executed_by || '-' }}</el-descriptions-item>
        </el-descriptions>

        <el-tabs v-model="resultActiveTab">
          <el-tab-pane label="步骤结果" name="steps">
            <div v-if="resultData.step_results && resultData.step_results.length">
              <div v-for="(s, idx) in resultData.step_results" :key="idx" class="step-result-row">
                <el-tag :type="s.status === 'passed' ? 'success' : 'danger'" size="small">{{ s.status }}</el-tag>
                <span style="margin-left:8px;flex:1">{{ s.instruction }}</span>
                <el-tag v-if="s.output_var" type="warning" size="small" style="margin-left:6px">→ {{ s.output_var }}</el-tag>
              </div>
            </div>
            <div v-else style="color:#999;text-align:center;padding:20px">暂无步骤结果</div>

            <!-- 变量流转 -->
            <div v-if="resultData.variable_snapshot && Object.keys(resultData.variable_snapshot).length" style="margin-top:16px">
              <div style="font-weight:600;margin-bottom:8px">变量流转</div>
              <el-table :data="Object.entries(resultData.variable_snapshot).map(([k,v]) => ({var_name:k, value: typeof v === 'object' ? JSON.stringify(v) : v}))" border size="small" style="width:100%">
                <el-table-column prop="var_name" label="变量名" width="160" />
                <el-table-column prop="value" label="实际值" show-overflow-tooltip />
              </el-table>
            </div>

            <!-- SQL执行结果 -->
            <div v-if="resultData.sql_results && resultData.sql_results.length" style="margin-top:16px">
              <div style="font-weight:600;margin-bottom:8px">SQL执行</div>
              <div v-for="(sql, idx) in resultData.sql_results" :key="idx" style="margin-bottom:8px;padding:8px;background:#f5f7fa;border-radius:4px;font-size:12px">
                <div style="font-weight:500;color:#606266">{{ sql.type === 'pre' ? '前置SQL' : '后置SQL' }}</div>
                <pre style="margin:4px 0;color:#303133;white-space:pre-wrap">{{ sql.sql }}</pre>
                <el-tag :type="sql.success ? 'success' : 'danger'" size="small">{{ sql.success ? '成功' : '失败' }}</el-tag>
                <span v-if="sql.rows_affected" style="margin-left:8px;color:#909399;font-size:12px">影响行数: {{ sql.rows_affected }}</span>
                <div v-if="sql.error" style="color:#f56c6c;margin-top:4px">{{ sql.error }}</div>
              </div>
            </div>

            <div v-if="resultData.logs" style="margin-top:16px">
              <div style="font-weight:600;margin-bottom:8px">执行日志</div>
              <pre class="log-box">{{ resultData.logs }}</pre>
            </div>
          </el-tab-pane>

          <el-tab-pane label="错误信息" name="error">
            <div v-if="resultData.error_message">
              <pre class="error-box">{{ resultData.error_message }}</pre>
            </div>
            <div v-else style="color:#999;text-align:center;padding:40px">无错误信息</div>
          </el-tab-pane>

          <el-tab-pane label="回放报告" name="report">
            <div v-if="resultData.report_url" class="report-container">
              <div class="report-toolbar">
                <span class="report-hint">Midscene AI 操作回放（支持截图+操作轨迹回放）</span>
                <el-button link type="primary" @click="openReportNewTab(resultData.report_url)">新窗口打开</el-button>
              </div>
              <iframe
                :src="getReportSrc(resultData.report_url)"
                class="report-iframe"
                frameborder="0"
                allowfullscreen
              ></iframe>
            </div>
            <div v-else style="color:#999;text-align:center;padding:40px">
              <el-icon style="font-size:32px;margin-bottom:8px"><VideoPlay /></el-icon>
              <div>暂无回放报告</div>
              <div style="font-size:12px;margin-top:4px">执行完成后Midscene会自动生成操作回放报告</div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-dialog>

    <!-- 新建分组弹窗 -->
    <!-- 变量助手弹窗 -->
    <el-dialog v-model="showVariableHelper" title="变量助手" width="900px" destroy-on-close>
      <div style="margin-bottom:12px;color:#606263;font-size:13px">
        点击行插入变量表达式到当前编辑的输入值字段。支持 <code>${变量名}</code> 引用上下文变量，<code>${函数()}</code> 调用数据工厂。
      </div>
      <el-tabs v-model="varHelperTab" tab-position="left" style="height:420px">
        <el-tab-pane v-for="cat in variableCategories" :key="cat.label" :label="cat.label" :name="cat.label">
          <el-table :data="cat.variables" size="small" @row-click="insertVariable" style="cursor:pointer">
            <el-table-column prop="name" label="函数名" width="180" />
            <el-table-column prop="desc" label="描述" />
            <el-table-column prop="syntax" label="语法" width="220" />
            <el-table-column prop="example" label="示例" width="200" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <el-dialog v-model="showGroupDialog" title="新建分组" width="400px" destroy-on-close>
      <el-form :model="groupForm" label-width="80px">
        <el-form-item label="分组名称" required>
          <el-input v-model="groupForm.name" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGroupDialog = false">取消</el-button>
        <el-button type="primary" @click="createGroup">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Plus, VideoPlay, Delete, Loading, Check, Close, Search, CaretRight, CaretLeft, Edit, MagicStick } from '@element-plus/icons-vue'
import ActionCell from '@/components/ActionCell.vue'
import {
  getMidsceneGroups, createMidsceneGroup,
  getMidsceneCases, createMidsceneCase, updateMidsceneCase, deleteMidsceneCase,
  batchDeleteMidsceneCases, importAIToMidscene, runMidsceneCase,
  getMidsceneExecutionDetail, getMidsceneExecutionStatus,
} from '@/api/ui_automation'
import { getAITaskList, getAITaskCases, getAiProjects } from '@/api/ui_automation'
import { getVariableFunctions } from '@/api/data-factory'

const route = useRoute()
const routePlatform = computed(() => route.meta?.platform || '')

// ---- 项目 ----
const projectList = ref([])
const projectId = ref(null)

async function loadProjects() {
  try {
    const res = await getAiProjects()
    projectList.value = res.data?.results || res.data || []
    // 从 localStorage 恢复上次选择
    const saved = localStorage.getItem('lastProjectId_ai_midscene')
    if (saved) projectId.value = parseInt(saved)
  } catch {}
}

function onProjectChange(val) {
  localStorage.setItem('lastProjectId_ai_midscene', val || '')
  loadCases()
}

// ---- 分组 ----
const groups = ref([])
const currentGroupId = ref(null)
const showGroupDialog = ref(false)
const groupForm = reactive({ name: '' })

async function loadGroups() {
  try {
    const res = await getMidsceneGroups()
    groups.value = res.data?.results || res.data || res
  } catch {}
}

function selectGroup(id) {
  currentGroupId.value = id
  currentPage.value = 1
  loadCases()
}

async function createGroup() {
  if (!groupForm.name) return ElMessage.warning('请输入分组名称')
  try {
    await createMidsceneGroup({ name: groupForm.name })
    showGroupDialog.value = false
    groupForm.name = ''
    loadGroups()
    ElMessage.success('分组已创建')
  } catch (e) {
    ElMessage.error('创建失败')
  }
}

// ---- 变量助手 ----
const showVariableHelper = ref(false)
const varHelperTab = ref('')
const variableCategories = ref([])
const currentEditingStep = ref(null)
const currentEditingField = ref('')

async function loadVariableFunctions() {
  try {
    const res = await getVariableFunctions()
    const functions = res.data || res
    // 按分类组织
    const catMap = {}
    const catOrder = ['随机工具', '测试数据', '字符工具', '编码工具', '加密工具', '时间日期', 'Crontab']
    for (const fn of functions) {
      const cat = fn.category || '其他'
      if (!catMap[cat]) catMap[cat] = { label: cat, variables: [] }
      catMap[cat].variables.push(fn)
    }
    variableCategories.value = catOrder
      .filter(c => catMap[c])
      .map(c => catMap[c])
      .concat(Object.values(catMap).filter(c => !catOrder.includes(c.label)))
    if (variableCategories.value.length) {
      varHelperTab.value = variableCategories.value[0].label
    }
  } catch {}
}

function openVariableHelper(step, field) {
  currentEditingStep.value = step
  currentEditingField.value = field
  if (!variableCategories.value.length) loadVariableFunctions()
  showVariableHelper.value = true
}

function insertVariable(variable) {
  if (!currentEditingStep.value || !currentEditingField.value) return
  const example = variable.example || `\${${variable.name}}`
  const current = currentEditingStep.value[currentEditingField.value] || ''
  currentEditingStep.value[currentEditingField.value] = current ? current + example : example
  showVariableHelper.value = false
}

// ---- 用例列表 ----
const cases = ref([])
const searchText = ref('')
const filterPlatform = computed({
  get: () => routePlatform.value || filterPlatformLocal.value,
  set: (v) => { filterPlatformLocal.value = v }
})
const filterPlatformLocal = ref('')
const selectedIds = ref([])
const runningIds = reactive({})
const batchRunning = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 过滤
const filteredCases = computed(() => {
  let list = cases.value
  if (searchText.value) {
    const kw = searchText.value.toLowerCase()
    list = list.filter(c => c.name?.toLowerCase().includes(kw))
  }
  if (filterPlatform.value) {
    list = list.filter(c => c.platform === filterPlatform.value)
  }
  return list
})

const paginatedCases = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredCases.value.slice(start, start + pageSize.value)
})

let searchTimer = null
function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadCases()
  }, 300)
}

async function loadCases() {
  try {
    const params = {}
    if (currentGroupId.value && currentGroupId.value !== 'ungrouped') {
      params.group_id = currentGroupId.value
    } else if (currentGroupId.value === 'ungrouped') {
      params.group_id = 'ungrouped'
    }
    if (searchText.value) params.search = searchText.value
    if (filterPlatform.value) params.platform = filterPlatform.value
    if (projectId.value) params.project_id = projectId.value

    const res = await getMidsceneCases(params)
    const data = res.data?.results || res.data || res
    cases.value = data.results || data
  } catch {}
}

function onSelectionChange(rows) {
  selectedIds.value = rows.map(r => r.id)
}

function clearSelection() {
  selectedIds.value = []
}

// ---- 状态工具 ----
function statusTagType(s) {
  return { passed: 'success', failed: 'danger', running: 'warning', pending: 'info' }[s] || 'info'
}
function statusLabel(s) {
  return { pending: '待执行', running: '执行中', passed: '通过', failed: '失败' }[s] || s || '-'
}

function formatDateTime(dt) {
  if (!dt) return '-'
  const d = new Date(dt)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

// ---- 操作按钮（ActionCell） ----
function getCaseActions(row) {
  return [
    {
      key: 'run',
      label: '执行',
      type: 'primary',
      loading: !!runningIds[row.id],
      onClick: (r) => runCase(r),
    },
    {
      key: 'edit',
      label: '编辑',
      type: 'primary',
      onClick: (r) => openDetailDrawer(r),
    },
    {
      key: 'result',
      label: '结果',
      type: 'primary',
      onClick: (r) => showResult(r),
    },
    {
      key: 'delete',
      label: '删除',
      danger: true,
      onClick: (r) => deleteCase(r),
    },
  ]
}

// ---- 新建用例弹窗 ----
const caseDialogVisible = ref(false)
const saving = ref(false)
const caseForm = reactive({
  name: '', platform: 'web', description: '', group_id: null,
  url: '', headless: false, cache_strategy: 'normal', new_tab: false,
  user_agent: '', viewport_width: 1280, viewport_height: 768, device_scale_factor: 1.0,
  cookie_file: '', wait_for_network_idle_timeout: null, continue_on_network_idle_error: true,
  device_id: '', package_name: '', app_activity: '',
  steps: [],
  output_variables: [],
  precondition_sql: '',
  postcondition_sql: '',
})

function openCreateDialog() {
  const defaultPlatform = routePlatform.value || 'web'
  Object.assign(caseForm, {
    name: '', platform: defaultPlatform, description: '', group_id: null,
    url: '', headless: false, cache_strategy: 'normal', new_tab: false,
    user_agent: '', viewport_width: 1280, viewport_height: 768, device_scale_factor: 1.0,
    cookie_file: '', wait_for_network_idle_timeout: null, continue_on_network_idle_error: true,
    device_id: '', package_name: '', app_activity: '',
    steps: [],
    output_variables: [],
    precondition_sql: '',
    postcondition_sql: '',
  })
  caseDialogVisible.value = true
}

function addStep() {
  caseForm.steps.push({ order: caseForm.steps.length + 1, type: 'action', instruction: '', input_value: '', output_var: '' })
}

async function saveCase() {
  if (!caseForm.name) return ElMessage.warning('请输入用例名称')
  saving.value = true
  try {
    const payload = { ...caseForm }
    payload.steps = payload.steps.map((s, i) => ({ ...s, order: i + 1 }))
    await createMidsceneCase(payload)
    ElMessage.success('已创建')
    caseDialogVisible.value = false
    loadCases()
    loadGroups()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '保存失败')
  } finally {
    saving.value = false
  }
}

async function deleteCase(row) {
  await ElMessageBox.confirm(`确定删除用例"${row.name}"？`, '删除确认')
  await deleteMidsceneCase(row.id)
  ElMessage.success('已删除')
  if (selectedCase.value?.id === row.id) closeDetailDrawer()
  loadCases()
  loadGroups()
}

async function handleBatchDelete() {
  await ElMessageBox.confirm(`确定删除选中的${selectedIds.value.length}条用例？`, '批量删除')
  await batchDeleteMidsceneCases({ ids: selectedIds.value })
  ElMessage.success('已删除')
  selectedIds.value = []
  loadCases()
  loadGroups()
}

// ---- 详情抽屉 ----
const detailDrawerVisible = ref(false)
const detailCollapsed = ref(false)
const detailDrawerWidth = ref(600)
const selectedCase = ref(null)
const detailActiveTab = ref('info')
const drawerResultData = ref(null)
const drawerResultLoading = ref(false)
const drawerResultTab = ref('steps')

const detailDrawerSize = computed(() => {
  if (detailCollapsed.value) return '20px'
  return `${detailDrawerWidth.value}px`
})

const drawerForm = reactive({
  name: '', platform: 'web', description: '', group_id: null,
  url: '', headless: false, cache_strategy: 'normal', new_tab: false,
  user_agent: '', viewport_width: 1280, viewport_height: 768, device_scale_factor: 1.0,
  cookie_file: '', wait_for_network_idle_timeout: null, continue_on_network_idle_error: true,
  device_id: '', package_name: '', app_activity: '',
  steps: [],
  output_variables: [],
  precondition_sql: '',
  postcondition_sql: '',
})

function openDetailDrawer(caseData) {
  selectedCase.value = caseData
  Object.assign(drawerForm, {
    name: caseData.name, platform: caseData.platform, description: caseData.description || '',
    group_id: caseData.group_id, url: caseData.url || '', headless: caseData.headless || false,
    cache_strategy: caseData.cache_strategy || 'normal', new_tab: caseData.new_tab || false,
    user_agent: caseData.user_agent || '',
    viewport_width: caseData.viewport_width || 1280, viewport_height: caseData.viewport_height || 768,
    device_scale_factor: caseData.device_scale_factor || 1.0,
    cookie_file: caseData.cookie_file || '',
    wait_for_network_idle_timeout: caseData.wait_for_network_idle_timeout ?? null,
    continue_on_network_idle_error: caseData.continue_on_network_idle_error ?? true,
    device_id: caseData.device_id || '', package_name: caseData.package_name || '',
    app_activity: caseData.app_activity || '',
    steps: (caseData.steps || []).map(s => ({ ...s, input_value: s.input_value || '', output_var: s.output_var || '' })),
    output_variables: caseData.output_variables || [],
    precondition_sql: caseData.precondition_sql || '',
    postcondition_sql: caseData.postcondition_sql || '',
  })
  detailActiveTab.value = 'info'
  drawerResultData.value = null
  detailDrawerVisible.value = true
  detailCollapsed.value = false
  // 加载执行结果
  loadDrawerResult(caseData)
}

function closeDetailDrawer() {
  detailDrawerVisible.value = false
  selectedCase.value = null
}

function toggleDetailCollapse() {
  detailCollapsed.value = !detailCollapsed.value
}

// 拖拽调宽
function startResize(e) {
  e.preventDefault()
  const startX = e.clientX
  const startW = detailDrawerWidth.value
  const onMove = (ev) => {
    const delta = startX - ev.clientX
    const newW = Math.max(400, Math.min(1200, startW + delta))
    detailDrawerWidth.value = newW
  }
  const onUp = () => {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

function addStepToDrawer() {
  drawerForm.steps.push({ order: drawerForm.steps.length + 1, type: 'action', instruction: '', input_value: '', output_var: '' })
}

async function saveCaseFromDrawer() {
  if (!drawerForm.name) return ElMessage.warning('请输入用例名称')
  saving.value = true
  try {
    const payload = { ...drawerForm }
    payload.steps = payload.steps.map((s, i) => ({ ...s, order: i + 1 }))
    await updateMidsceneCase(selectedCase.value.id, payload)
    ElMessage.success('已更新')
    // 更新列表中的数据
    Object.assign(selectedCase.value, payload)
    loadCases()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '保存失败')
  } finally {
    saving.value = false
  }
}

async function loadDrawerResult(caseData) {
  drawerResultLoading.value = true
  try {
    const { default: axios } = await import('@/utils/api')
    const res = await axios.get('/ui-automation/midscene-executions/', { params: { case_id: caseData.id } })
    const executions = res.data?.results || res.data || res
    if (executions.length > 0) {
      const detailRes = await getMidsceneExecutionDetail(executions[0].id)
      drawerResultData.value = detailRes.data || detailRes
    } else {
      drawerResultData.value = null
    }
  } catch {
    drawerResultData.value = null
  } finally {
    drawerResultLoading.value = false
  }
}

function handleRowClick(row) {
  if (row) openDetailDrawer(row)
}

// ---- 执行 ----
async function runCase(row) {
  runningIds[row.id] = true
  // 立即在列表中显示执行中
  row.last_status = 'running'
  try {
    const res = await runMidsceneCase(row.id)
    const data = res.data || res
    ElMessage.success(data.message || '任务已提交')
    pollStatus(row, data.execution_id)
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '执行失败')
    runningIds[row.id] = false
    row.last_status = 'failed'
  }
}

async function pollStatus(row, executionId) {
  let count = 0
  const poll = async () => {
    try {
      const res = await getMidsceneExecutionStatus({ execution_id: executionId })
      const data = res.data || res
      if (data.status === 'passed' || data.status === 'failed') {
        runningIds[row.id] = false
        loadCases()
        // 如果当前抽屉打开的是该用例，刷新结果
        if (selectedCase.value?.id === row.id) {
          loadDrawerResult(row)
        }
        return
      }
    } catch {}
    count++
    if (count < 120) setTimeout(poll, 2000)
    else runningIds[row.id] = false
  }
  poll()
}

async function batchRun() {
  batchRunning.value = true
  let submitted = 0
  for (const id of selectedIds.value) {
    try {
      runningIds[id] = true
      await runMidsceneCase(id)
      submitted++
    } catch {}
  }
  batchRunning.value = false
  ElMessage.success(`已提交${submitted}个用例`)
  setTimeout(loadCases, 5000)
}

// ---- 执行结果弹窗 ----
const resultDialogVisible = ref(false)
const resultData = ref(null)
const resultLoading = ref(false)
const resultActiveTab = ref('steps')

function getReportSrc(url) {
  if (!url) return ''
  const sep = url.includes('?') ? '&' : '?'
  return `${url}${sep}player-only=1&auto-play=0`
}

function openReportNewTab(url) {
  if (url) window.open(url, '_blank')
}

async function showResult(row) {
  resultDialogVisible.value = true
  resultLoading.value = true
  resultData.value = null
  resultActiveTab.value = 'steps'
  try {
    const { default: axios } = await import('@/utils/api')
    const res = await axios.get('/ui-automation/midscene-executions/', { params: { case_id: row.id } })
    const executions = res.data?.results || res.data || res
    if (executions.length > 0) {
      const detailRes = await getMidsceneExecutionDetail(executions[0].id)
      resultData.value = detailRes.data || detailRes
    } else {
      resultData.value = { status: 'pending', step_results: [], logs: '', error_message: '暂无执行记录' }
    }
  } catch {
    resultData.value = { status: 'pending', step_results: [], logs: '', error_message: '查询失败' }
  } finally {
    resultLoading.value = false
  }
}

// ---- 从AI导入 ----
const showImportDialog = ref(false)
const importPlatform = ref('web')
const aiCases = ref([])
const selectedAICases = ref([])
const loadingAI = ref(false)
const importing = ref(false)

async function loadAICases() {
  loadingAI.value = true
  try {
    const res = await getAITaskList()
    const tasks = res.data || res
    if (tasks.length > 0) {
      const detailRes = await getAITaskCases(tasks[0].id || tasks[0].task_id)
      aiCases.value = detailRes.data || detailRes
    }
  } catch {} finally {
    loadingAI.value = false
  }
}

function onAISelection(rows) {
  selectedAICases.value = rows
}

async function doImport() {
  importing.value = true
  try {
    const caseIds = selectedAICases.value.map(c => c.id)
    await importAIToMidscene({ case_ids: caseIds, platform: importPlatform.value })
    ElMessage.success(`成功导入${caseIds.length}条用例`)
    showImportDialog.value = false
    loadCases()
    loadGroups()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '导入失败')
  } finally {
    importing.value = false
  }
}

// ---- 初始化 ----
onMounted(() => {
  loadProjects()
  loadGroups()
  loadCases()
  loadAICases()
})

// 路由切换时重新加载（同组件不重建，需手动刷新）
watch(() => route.path, () => {
  loadCases()
})
</script>

<style lang="scss" scoped>
/* ============================================================
   页面容器
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

/* ============================================================
   三栏工作区
   ============================================================ */
.workspace {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 0;
  gap: var(--space-4);
  min-height: 0;
  position: relative;
}

/* 面板通用 */
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

.group-list {
  flex: 1;
  overflow-y: auto;
}

.group-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  color: var(--gray-600);
  border-radius: var(--radius-md);
  margin: 2px 0;
  transition: background 0.2s;
}

.group-item:hover {
  background: var(--gray-100);
}

.group-item.active {
  background: var(--brand-50);
  color: var(--brand-700);
  font-weight: 500;
}

.group-node-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
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

.list-column .filter-bar {
  margin-bottom: 0;
}

.list-panel {
  flex: 1;
  min-width: 0;
}

.panel__header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.list-panel .panel__body {
  padding: 0;
}

.table-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.table-area {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.step-count {
  font-weight: 600;
  color: var(--brand-600);
}
.text-muted {
  color: #999;
}

/* 批量操作工具栏 */
.batch-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  margin-bottom: 8px;
  border-radius: 6px;
  background: var(--brand-50, #ebf3fe);
  border: 1px solid var(--brand-200, #b3d8ff);
  font-size: 13px;
}

.batch-toolbar__info {
  font-weight: 600;
  color: var(--brand-600, #1890ff);
}

.batch-toolbar__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.batch-bar-slide-enter-active,
.batch-bar-slide-leave-active {
  transition: all 0.3s ease;
}

.batch-bar-slide-enter-from,
.batch-bar-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
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

:deep(.detail-drawer--collapsed) {
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.05);
}

:deep(.detail-drawer .el-drawer__body) {
  padding: 0;
  display: flex;
  flex-direction: row;
  overflow: visible !important;
  height: 100%;
  min-height: 0;
}

/* 左边缘三角切换按钮 */
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

.case-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.detail-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 详情页签 */
.detail-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.detail-tabs :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px 16px 16px;
}

.detail-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 0 16px;
}

.detail-form {
  max-width: 500px;
}

/* 抽屉内步骤编辑器 */
.steps-editor-drawer {
  padding: 4px 0;
}

.step-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.step-row-block {
  margin-bottom: 8px;
  padding: 8px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #ebeef5;
}

.step-row-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-row-params {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  padding-left: 32px;
}

.step-order {
  width: 24px;
  text-align: right;
  font-weight: 600;
  color: var(--gray-600);
  font-size: 13px;
}

/* ============================================================
   弹窗内样式
   ============================================================ */
.steps-editor {
  width: 100%;
}

.step-result-row {
  display: flex;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--gray-100);
  font-size: 13px;
}

.error-box, .log-box {
  background: var(--gray-50);
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

.error-box {
  background: #fef0f0;
  color: #f56c6c;
}

.report-container {
  display: flex;
  flex-direction: column;
  height: 500px;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  overflow: hidden;
}

.report-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--gray-50);
  border-bottom: 1px solid var(--gray-200);
  flex-shrink: 0;
}

.report-hint {
  font-size: 13px;
  color: var(--gray-600);
}

.report-iframe {
  flex: 1;
  width: 100%;
  border: none;
}
</style>

<!-- 全局样式：弹窗高度控制 -->
<style lang="scss">
.detail-dialog-680 .el-dialog__body {
  max-height: 580px;
  overflow-y: auto;
  padding: 16px;
}
</style>