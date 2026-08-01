<template>
  <div class="page-container">
    <!-- 顶部标题栏 -->
    <div class="page-titlebar">
      <h1 class="page-title">AI视觉自动化</h1>
      <div class="titlebar-actions">
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
            <el-form-item label="平台">
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
                    <div v-for="(step, idx) in drawerForm.steps" :key="idx" class="step-row">
                      <span class="step-order">{{ idx + 1 }}.</span>
                      <el-select v-model="step.type" style="width:100px" size="small">
                        <el-option label="操作" value="action" />
                        <el-option label="断言" value="assert" />
                      </el-select>
                      <el-input v-model="step.instruction" placeholder="输入步骤描述" style="flex:1" size="small" />
                      <el-button link type="danger" size="small" @click="drawerForm.steps.splice(idx, 1)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                    <el-button link type="primary" @click="addStepToDrawer" style="margin-top:4px">+ 添加步骤</el-button>
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

                    <div v-if="drawerResultData.step_results && drawerResultData.step_results.length">
                      <div v-for="(s, idx) in drawerResultData.step_results" :key="idx" class="step-result-row">
                        <el-tag :type="s.status === 'passed' ? 'success' : 'danger'" size="small">{{ s.status }}</el-tag>
                        <span style="margin-left:8px">{{ s.instruction }}</span>
                      </div>
                    </div>
                    <div v-else style="color:#999;text-align:center;padding:20px">暂无步骤结果</div>

                    <div v-if="drawerResultData.error_message" style="margin-top:16px">
                      <div style="font-weight:600;margin-bottom:8px">错误信息</div>
                      <pre class="error-box">{{ drawerResultData.error_message }}</pre>
                    </div>
                    <div v-if="drawerResultData.logs" style="margin-top:16px">
                      <div style="font-weight:600;margin-bottom:8px">执行日志</div>
                      <pre class="log-box">{{ drawerResultData.logs }}</pre>
                    </div>

                    <!-- 回放报告 -->
                    <div v-if="drawerResultData.report_url" style="margin-top:16px">
                      <div style="font-weight:600;margin-bottom:8px">回放报告</div>
                      <div class="report-container">
                        <div class="report-toolbar">
                          <span class="report-hint">Midscene AI 操作回放</span>
                          <el-button link type="primary" @click="openReportNewTab(drawerResultData.report_url)">新窗口打开</el-button>
                        </div>
                        <iframe :src="getReportSrc(drawerResultData.report_url)" class="report-iframe" frameborder="0" allowfullscreen></iframe>
                      </div>
                    </div>
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
          <el-radio-group v-model="caseForm.platform">
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
            <div v-for="(step, idx) in caseForm.steps" :key="idx" class="step-row">
              <span class="step-order">{{ idx + 1 }}.</span>
              <el-select v-model="step.type" style="width:100px">
                <el-option label="操作" value="action" />
                <el-option label="断言" value="assert" />
              </el-select>
              <el-input v-model="step.instruction" placeholder="输入步骤描述" style="flex:1" />
              <el-button link type="danger" @click="caseForm.steps.splice(idx, 1)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <el-button link type="primary" @click="addStep">+ 添加步骤</el-button>
          </div>
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
    <el-dialog v-model="resultDialogVisible" title="执行结果" width="900px" destroy-on-close class="result-dialog">
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
                <span style="margin-left:8px">{{ s.instruction }}</span>
              </div>
            </div>
            <div v-else style="color:#999;text-align:center;padding:20px">暂无步骤结果</div>

            <div v-if="resultData.error_message" style="margin-top:16px">
              <div style="font-weight:600;margin-bottom:8px">错误信息</div>
              <pre class="error-box">{{ resultData.error_message }}</pre>
            </div>

            <div v-if="resultData.logs" style="margin-top:16px">
              <div style="font-weight:600;margin-bottom:8px">执行日志</div>
              <pre class="log-box">{{ resultData.logs }}</pre>
            </div>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Plus, VideoPlay, Delete, Loading, Check, Close, Search, CaretRight, CaretLeft, Edit } from '@element-plus/icons-vue'
import ActionCell from '@/components/ActionCell.vue'
import {
  getMidsceneGroups, createMidsceneGroup,
  getMidsceneCases, createMidsceneCase, updateMidsceneCase, deleteMidsceneCase,
  batchDeleteMidsceneCases, importAIToMidscene, runMidsceneCase,
  getMidsceneExecutionDetail, getMidsceneExecutionStatus,
} from '@/api/ui_automation'
import { getAITaskList, getAITaskCases } from '@/api/ui_automation'

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

// ---- 用例列表 ----
const cases = ref([])
const searchText = ref('')
const filterPlatform = ref('')
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

// ---- 操作按钮（ActionCell） ----
function getCaseActions(row) {
  return [
    {
      key: 'run',
      label: '执行',
      type: 'primary',
      icon: VideoPlay,
      loading: !!runningIds[row.id],
      onClick: (r) => runCase(r),
    },
    {
      key: 'edit',
      label: '编辑',
      type: 'primary',
      icon: Edit,
      onClick: (r) => openDetailDrawer(r),
    },
    {
      key: 'result',
      label: '结果',
      type: 'primary',
      icon: CaretRight,
      onClick: (r) => showResult(r),
    },
    {
      key: 'delete',
      label: '删除',
      danger: true,
      icon: Delete,
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
})

function openCreateDialog() {
  Object.assign(caseForm, {
    name: '', platform: 'web', description: '', group_id: null,
    url: '', headless: false, cache_strategy: 'normal', new_tab: false,
    user_agent: '', viewport_width: 1280, viewport_height: 768, device_scale_factor: 1.0,
    cookie_file: '', wait_for_network_idle_timeout: null, continue_on_network_idle_error: true,
    device_id: '', package_name: '', app_activity: '',
    steps: [],
  })
  caseDialogVisible.value = true
}

function addStep() {
  caseForm.steps.push({ order: caseForm.steps.length + 1, type: 'action', instruction: '' })
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
    steps: (caseData.steps || []).map(s => ({ ...s })),
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
  drawerForm.steps.push({ order: drawerForm.steps.length + 1, type: 'action', instruction: '' })
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
  try {
    const res = await runMidsceneCase(row.id)
    const data = res.data || res
    ElMessage.success(data.message || '任务已提交')
    pollStatus(row, data.execution_id)
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '执行失败')
    runningIds[row.id] = false
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
  loadGroups()
  loadCases()
  loadAICases()
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