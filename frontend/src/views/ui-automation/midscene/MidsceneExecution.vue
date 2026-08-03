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
          <el-button text size="small" class="panel__action" @click="openAddGroup">
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
            :current-node-key="currentGroupId === null ? '__all__' : currentGroupId === 'ungrouped' ? '__ungrouped__' : currentGroupId"
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
              <span class="group-tree-node">
                <span class="group-tree-label">{{ data.name }}</span>
                <span v-if="data.case_count !== undefined" class="group-count">{{ data.case_count }}</span>
              </span>
            </template>
          </el-tree>
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
            <el-form-item label="状态">
              <el-select v-model="filterStatus" placeholder="全部" clearable style="width:120px" @change="onFilterChange">
                <el-option label="通过" value="passed" />
                <el-option label="失败" value="failed" />
                <el-option label="执行中" value="running" />
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
                    <el-form-item v-if="!routePlatform" label="平台" required>
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

                    <!-- Midscene 三级配置覆盖 -->
                    <el-divider content-position="left">Midscene 配置覆盖</el-divider>
                    <p style="font-size:12px;color:#909399;margin:0 0 12px 0">以下配置留空则继承全局Midscene配置，填写则覆盖全局</p>
                    <el-form-item label="设备类型">
                      <el-select v-model="drawerForm.device_type" placeholder="继承全局" clearable style="width:100%">
                        <el-option label="继承全局" value="" />
                        <el-option label="Web端" value="web" />
                        <el-option label="Android" value="android" />
                        <el-option label="iOS" value="ios" />
                        <el-option label="HarmonyOS" value="harmony" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="AI模型覆盖">
                      <el-button size="small" @click="openAiModelOverride">
                        {{ Object.keys(drawerForm.ai_model_config_override).length ? '已配置，点击编辑' : '点击配置' }}
                      </el-button>
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
                      <el-form-item label="启动URL">
                        <el-input v-model="drawerForm.url" placeholder="可选，留空则通过包名启动" />
                        <div style="font-size:12px;color:#909399;margin-top:4px">配置包名后优先使用包名启动，URL仅作为回退方式</div>
                      </el-form-item>
                      <el-form-item label="设备ID">
                        <el-input v-model="drawerForm.device_id" placeholder="如：adb devices获取，留空自动检测" />
                      </el-form-item>
                      <el-form-item label="包名" required>
                        <el-input v-model="drawerForm.package_name" placeholder="com.example.app" />
                      </el-form-item>
                      <el-form-item label="Activity">
                        <el-input v-model="drawerForm.app_activity" placeholder=".MainActivity（可选）" />
                      </el-form-item>
                    </template>
                  </el-form>
                </el-tab-pane>

                <el-tab-pane label="测试步骤" name="steps">
                  <div class="steps-editor-drawer">
                    <div v-for="(step, idx) in drawerForm.steps" :key="idx" class="step-row-block">
                      <!-- 主行：序号 + 模式标签 + 类型 + 描述 + 删除 -->
                      <div class="step-row-main" @click.self="toggleDrawerStep(idx)">
                        <el-icon class="step-toggle-icon" :class="{ 'is-expanded': drawerExpandedSteps.has(idx) }" @click.stop="toggleDrawerStep(idx)"><ArrowRight /></el-icon>
                        <span class="step-order">{{ idx + 1 }}.</span>
                        <el-tag
                          :type="step.mode === 'traditional' ? 'warning' : 'success'"
                          size="small"
                          class="step-mode-tag"
                          @click.stop="!(drawerForm.platform === 'app' && step.mode !== 'traditional') && toggleStepMode(step)"
                          :style="{ cursor: drawerForm.platform === 'app' && step.mode !== 'traditional' ? 'not-allowed' : 'pointer', opacity: drawerForm.platform === 'app' && step.mode !== 'traditional' ? 0.5 : 1, marginRight: '4px' }"
                          :title="drawerForm.platform === 'app' && step.mode !== 'traditional' ? 'APP端不支持传统模式' : (step.mode === 'traditional' ? '点击切换为AI模式' : '点击切换为传统模式')"
                        >{{ step.mode === 'traditional' ? '传统' : 'AI' }}</el-tag>
                        <el-select v-model="step.type" style="width:90px" size="small" @click.stop>
                          <el-option label="操作" value="action" />
                          <el-option label="断言" value="assert" />
                        </el-select>
                        <el-input
                          v-if="step.mode !== 'traditional'"
                          v-model="step.instruction"
                          placeholder="步骤描述（支持${变量名}引用）"
                          style="flex:1" size="small" @click.stop
                        />
                        <el-input
                          v-else
                          v-model="step.instruction"
                          placeholder="步骤描述"
                          style="flex:1" size="small" @click.stop
                        />
                        <el-button link type="danger" size="small" @click.stop="drawerForm.steps.splice(idx, 1)">
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </div>
                      <!-- 展开区 -->
                      <div v-if="drawerExpandedSteps.has(idx)" class="step-row-params">
                        <span class="step-params-indent-toggle"></span>
                        <span class="step-params-indent-order"></span>
                        <span class="step-params-indent-select"></span>

                        <!-- AI模式展开 -->
                        <template v-if="step.mode !== 'traditional'">
                          <el-input v-model="step.input_value" placeholder="输入值（支持${变量}和数据工厂函数）" style="flex:1" size="small">
                            <template #append>
                              <el-button size="small" @click="openVariableHelper(step, 'input_value')" title="变量助手">
                                <el-icon><MagicStick /></el-icon>
                              </el-button>
                            </template>
                          </el-input>
                          <el-input v-model="step.output_var" placeholder="输出变量名" style="width:120px" size="small" />
                          <el-input-number v-model="step.retry_count" :min="0" :max="5" controls-position="right" style="width:90px" size="small" title="失败后重试次数，0=不重试" />
                        </template>

                        <!-- 传统模式展开 -->
                        <template v-else>
                          <div style="display:flex;flex-direction:column;gap:6px;flex:1">
                            <div style="display:flex;gap:6px;align-items:center">
                              <el-select v-model="step.action_type" placeholder="操作类型" style="width:100px" size="small">
                                <el-option label="点击" value="click" />
                                <el-option label="输入" value="input" />
                                <el-option label="选择" value="select" />
                                <el-option label="悬停" value="hover" />
                                <el-option label="等待" value="wait" />
                                <el-option label="滚动" value="scroll" />
                              </el-select>
                              <el-input v-model="step.locator_value" placeholder="定位表达式（如 #btn-submit 或 //button[text()='登录']）" style="flex:1" size="small" />
                            </div>
                            <div style="display:flex;gap:6px;align-items:center">
                              <el-input v-model="step.input_value" placeholder="输入值（支持${变量}和数据工厂函数）" style="flex:1" size="small">
                                <template #append>
                                  <el-button size="small" @click="openVariableHelper(step, 'input_value')" title="变量助手">
                                    <el-icon><MagicStick /></el-icon>
                                  </el-button>
                                </template>
                              </el-input>
                              <el-input v-model="step.output_var" placeholder="输出变量名" style="width:120px" size="small" />
                            </div>
                            <template v-if="step.type === 'assert'">
                              <div style="display:flex;gap:6px;align-items:center">
                                <el-select v-model="step.assert_type" placeholder="断言类型" style="width:100px" size="small">
                                  <el-option label="等于" value="equals" />
                                  <el-option label="包含" value="contains" />
                                  <el-option label="不等于" value="not_equals" />
                                  <el-option label="存在" value="exists" />
                                </el-select>
                                <el-input v-model="step.assert_value" placeholder="期望值" style="flex:1" size="small" />
                              </div>
                            </template>
                            <div style="display:flex;gap:6px;align-items:center">
                              <el-input-number v-model="step.retry_count" :min="0" :max="5" controls-position="right" style="width:90px" size="small" title="失败后重试次数，0=不重试" />
                              <span style="font-size:12px;color:#909399">重试次数</span>
                            </div>
                          </div>
                        </template>

                        <span class="step-params-indent-delete"></span>
                      </div>
                    </div>
                    <div style="display:flex;gap:8px;margin-top:4px">
                      <el-button link type="primary" @click="addStepToDrawer('ai')">+ AI步骤</el-button>
                      <el-button link type="warning" @click="addStepToDrawer('traditional')">+ 传统步骤</el-button>
                    </div>
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
                          <div v-for="(s, idx) in drawerResultData.step_results" :key="idx" class="step-result-row" style="flex-wrap:wrap">
                            <el-tag :type="s.status === 'passed' ? 'success' : 'danger'" size="small">{{ s.status }}</el-tag>
                            <el-tag v-if="s.mode === 'traditional'" type="info" size="small" style="margin-left:6px">传统</el-tag>
                            <el-tag v-else type="" size="small" style="margin-left:6px">AI</el-tag>
                            <span style="margin-left:8px;flex:1">
                              <template v-if="s.mode === 'traditional'">
                                {{ s.action_type || 'click' }} <span style="color:#909399">{{ s.locator_value ? '(' + s.locator_value.substring(0, 60) + (s.locator_value.length > 60 ? '...' : '') + ')' : '' }}</span>
                              </template>
                              <template v-else>
                                {{ s.instruction }}
                              </template>
                            </span>
                            <el-tag v-if="s.type" size="small" style="margin-left:6px">{{ s.type }}</el-tag>
                            <el-tag v-if="s.output_var" type="warning" size="small" style="margin-left:6px">→ {{ s.output_var }}</el-tag>
                            <div v-if="s.screenshot && s.status === 'failed'" style="width:100%;margin-top:6px;margin-left:0">
                              <el-image :src="s.screenshot" fit="contain" style="max-width:360px;max-height:200px;border:1px solid #ebeef5;border-radius:4px" :preview-src-list="[s.screenshot]" preview-teleported />
                              <div style="margin-top:4px;display:flex;gap:6px">
                                <el-button size="small" text type="primary" @click="saveAsBaseline(s.screenshot)">设为基线</el-button>
                                <el-button size="small" text type="primary" @click="openVisualCompare(s.screenshot)">视觉对比</el-button>
                              </div>
                            </div>
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

                <!-- 执行历史 -->
                <el-tab-pane label="执行历史" name="history">
                  <div v-if="caseHistoryLoading" style="text-align:center;padding:40px">
                    <el-icon class="is-loading" style="font-size:24px"><Loading /></el-icon>
                    <div style="margin-top:8px">加载中...</div>
                  </div>
                  <div v-else-if="caseHistoryList.length === 0" style="color:#999;text-align:center;padding:40px">暂无执行记录</div>
                  <el-table v-else :data="caseHistoryList" size="small" stripe max-height="400">
                    <el-table-column prop="started_at" label="执行时间" width="160" align="center">
                      <template #default="{ row }">
                        {{ formatDateTime(row.started_at) }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="status" label="状态" width="80" align="center">
                      <template #default="{ row }">
                        <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="duration" label="耗时" width="80" align="center">
                      <template #default="{ row }">
                        {{ row.duration ? row.duration.toFixed(1) + 's' : '-' }}
                      </template>
                    </el-table-column>
                    <el-table-column label="操作" width="60" align="center">
                      <template #default="{ row }">
                        <el-button link type="primary" size="small" @click="viewHistoryDetail(row)">详情</el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </el-tab-pane>

              </el-tabs>
            </div>
          </div>
        </div>
      </el-drawer>

      <!-- AI模型覆盖配置弹窗 -->
      <el-dialog v-model="showAiModelOverrideDrawer" title="AI模型覆盖配置" width="600px" :close-on-click-modal="false" destroy-on-close>
        <p style="font-size:12px;color:#909399;margin:0 0 16px 0">三级意图模型覆盖：留空则继承全局配置，填写则覆盖。Default 为必填基础模型。</p>
        <el-form label-width="120px" label-position="left">
          <el-divider content-position="left">Default（默认模型）</el-divider>
          <el-form-item label="模型提供商">
            <el-input v-model="aiOverrideEdit.default.modelProvider" placeholder="如 openai" />
          </el-form-item>
          <el-form-item label="模型名称">
            <el-input v-model="aiOverrideEdit.default.modelName" placeholder="如 gpt-4o" />
          </el-form-item>
          <el-form-item label="API Key">
            <el-input v-model="aiOverrideEdit.default.apiKey" type="password" show-password placeholder="模型 API Key" />
          </el-form-item>
          <el-form-item label="Base URL">
            <el-input v-model="aiOverrideEdit.default.baseURL" placeholder="如 https://api.openai.com/v1" />
          </el-form-item>

          <el-divider content-position="left">Insight（定位模型，可选）</el-divider>
          <el-form-item label="模型提供商">
            <el-input v-model="aiOverrideEdit.insight.modelProvider" placeholder="留空继承 Default" />
          </el-form-item>
          <el-form-item label="模型名称">
            <el-input v-model="aiOverrideEdit.insight.modelName" placeholder="留空继承 Default" />
          </el-form-item>
          <el-form-item label="API Key">
            <el-input v-model="aiOverrideEdit.insight.apiKey" type="password" show-password placeholder="留空继承 Default" />
          </el-form-item>
          <el-form-item label="Base URL">
            <el-input v-model="aiOverrideEdit.insight.baseURL" placeholder="留空继承 Default" />
          </el-form-item>

          <el-divider content-position="left">Planning（规划模型，可选）</el-divider>
          <el-form-item label="模型提供商">
            <el-input v-model="aiOverrideEdit.planning.modelProvider" placeholder="留空继承 Default" />
          </el-form-item>
          <el-form-item label="模型名称">
            <el-input v-model="aiOverrideEdit.planning.modelName" placeholder="留空继承 Default" />
          </el-form-item>
          <el-form-item label="API Key">
            <el-input v-model="aiOverrideEdit.planning.apiKey" type="password" show-password placeholder="留空继承 Default" />
          </el-form-item>
          <el-form-item label="Base URL">
            <el-input v-model="aiOverrideEdit.planning.baseURL" placeholder="留空继承 Default" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAiModelOverrideDrawer = false">取消</el-button>
          <el-button type="danger" plain @click="drawerForm.ai_model_config_override = {}; showAiModelOverrideDrawer = false">清除覆盖</el-button>
          <el-button type="primary" @click="saveAiModelOverride">保存</el-button>
        </template>
      </el-dialog>

    <!-- 新建用例弹窗（仅新建用） -->
    <el-dialog v-model="caseDialogVisible" title="新建用例" width="700px" :close-on-click-modal="false" destroy-on-close>
      <el-form :model="caseForm" label-width="100px">
        <el-form-item label="用例名称" required>
          <el-input v-model="caseForm.name" placeholder="请输入用例名称" />
        </el-form-item>
        <el-form-item v-if="!routePlatform" label="平台" required>
          <el-radio-group v-model="caseForm.platform" :disabled="!!routePlatform">
            <el-radio value="web">Web端</el-radio>
            <el-radio value="app">APP端</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="caseForm.platform === 'app'" label="设备类型">
          <el-select v-model="caseForm.device_type" placeholder="请选择设备类型" style="width:100%">
            <el-option label="Android" value="android" />
            <el-option label="iOS" value="ios" disabled>
              <span>iOS</span>
              <span style="color:#909399;font-size:12px;margin-left:4px">（暂未实现）</span>
            </el-option>
            <el-option label="HarmonyOS" value="harmony" disabled>
              <span>HarmonyOS</span>
              <span style="color:#909399;font-size:12px;margin-left:4px">（暂未实现）</span>
            </el-option>
          </el-select>
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
          <el-form-item label="启动URL">
            <el-input v-model="caseForm.url" placeholder="可选，留空则通过包名启动" />
            <div style="font-size:12px;color:#909399;margin-top:4px">配置包名后优先使用包名启动，URL仅作为回退方式</div>
          </el-form-item>
          <el-form-item label="设备ID">
            <el-input v-model="caseForm.device_id" placeholder="如：adb devices获取，留空自动检测" />
          </el-form-item>
          <el-form-item label="包名" required>
            <el-input v-model="caseForm.package_name" placeholder="com.example.app" />
          </el-form-item>
          <el-form-item label="Activity">
            <el-input v-model="caseForm.app_activity" placeholder=".MainActivity（可选）" />
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
              <div class="step-row-main" @click.self="toggleCaseStep(idx)">
                <el-icon class="step-toggle-icon" :class="{ 'is-expanded': caseExpandedSteps.has(idx) }" @click.stop="toggleCaseStep(idx)"><ArrowRight /></el-icon>
                <span class="step-order">{{ idx + 1 }}.</span>
                <el-tag
                  :type="step.mode === 'traditional' ? 'warning' : 'success'"
                  size="small" class="step-mode-tag"
                  @click.stop="!(caseForm.platform === 'app' && step.mode !== 'traditional') && toggleStepMode(step)"
                  :style="{ cursor: caseForm.platform === 'app' && step.mode !== 'traditional' ? 'not-allowed' : 'pointer', opacity: caseForm.platform === 'app' && step.mode !== 'traditional' ? 0.5 : 1, marginRight: '4px' }"
                  :title="caseForm.platform === 'app' && step.mode !== 'traditional' ? 'APP端不支持传统模式' : (step.mode === 'traditional' ? '点击切换为AI模式' : '点击切换为传统模式')"
                >{{ step.mode === 'traditional' ? '传统' : 'AI' }}</el-tag>
                <el-select v-model="step.type" style="width:90px" @click.stop>
                  <el-option label="操作" value="action" />
                  <el-option label="断言" value="assert" />
                </el-select>
                <el-input v-model="step.instruction" placeholder="步骤描述" style="flex:1" @click.stop />
                <el-button link type="danger" @click.stop="caseForm.steps.splice(idx, 1)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
              <div v-if="caseExpandedSteps.has(idx)" class="step-row-params">
                <span class="step-params-indent-toggle"></span>
                <span class="step-params-indent-order"></span>
                <span class="step-params-indent-select"></span>
                <!-- AI模式 -->
                <template v-if="step.mode !== 'traditional'">
                  <el-input v-model="step.input_value" placeholder="输入值（支持${变量}和数据工厂函数）" style="flex:1">
                    <template #append>
                      <el-button size="small" @click="openVariableHelper(step, 'input_value')" title="变量助手">
                        <el-icon><MagicStick /></el-icon>
                      </el-button>
                    </template>
                  </el-input>
                  <el-input v-model="step.output_var" placeholder="输出变量名" style="width:120px" />
                  <el-input-number v-model="step.retry_count" :min="0" :max="5" controls-position="right" style="width:90px" title="失败后重试次数，0=不重试" />
                </template>
                <!-- 传统模式 -->
                <template v-else>
                  <div style="display:flex;flex-direction:column;gap:6px;flex:1">
                    <div style="display:flex;gap:6px;align-items:center">
                      <el-select v-model="step.action_type" placeholder="操作类型" style="width:100px" size="small">
                        <el-option label="点击" value="click" />
                        <el-option label="输入" value="input" />
                        <el-option label="选择" value="select" />
                        <el-option label="悬停" value="hover" />
                        <el-option label="等待" value="wait" />
                        <el-option label="滚动" value="scroll" />
                      </el-select>
                      <el-input v-model="step.locator_value" placeholder="定位表达式" style="flex:1" size="small" />
                    </div>
                    <div style="display:flex;gap:6px;align-items:center">
                      <el-input v-model="step.input_value" placeholder="输入值" style="flex:1" size="small">
                        <template #append>
                          <el-button size="small" @click="openVariableHelper(step, 'input_value')" title="变量助手">
                            <el-icon><MagicStick /></el-icon>
                          </el-button>
                        </template>
                      </el-input>
                      <el-input v-model="step.output_var" placeholder="输出变量名" style="width:120px" size="small" />
                    </div>
                    <template v-if="step.type === 'assert'">
                      <div style="display:flex;gap:6px;align-items:center">
                        <el-select v-model="step.assert_type" placeholder="断言类型" style="width:100px" size="small">
                          <el-option label="等于" value="equals" />
                          <el-option label="包含" value="contains" />
                          <el-option label="不等于" value="not_equals" />
                          <el-option label="存在" value="exists" />
                        </el-select>
                        <el-input v-model="step.assert_value" placeholder="期望值" style="flex:1" size="small" />
                      </div>
                    </template>
                    <div style="display:flex;gap:6px;align-items:center">
                      <el-input-number v-model="step.retry_count" :min="0" :max="5" controls-position="right" style="width:90px" size="small" title="失败后重试次数，0=不重试" />
                      <span style="font-size:12px;color:#909399">重试次数</span>
                    </div>
                  </div>
                </template>
                <span class="step-params-indent-delete"></span>
              </div>
            </div>
            <div style="display:flex;gap:8px">
              <el-button link type="primary" @click="addStep('ai')">+ AI步骤</el-button>
              <el-button link type="warning" @click="addStep('traditional')">+ 传统步骤</el-button>
            </div>
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
              <div v-for="(s, idx) in resultData.step_results" :key="idx" class="step-result-row" style="flex-wrap:wrap">
                <el-tag :type="s.status === 'passed' ? 'success' : 'danger'" size="small">{{ s.status }}</el-tag>
                <el-tag v-if="s.mode === 'traditional'" type="info" size="small" style="margin-left:6px">传统</el-tag>
                <el-tag v-else type="" size="small" style="margin-left:6px">AI</el-tag>
                <span style="margin-left:8px;flex:1">
                  <template v-if="s.mode === 'traditional'">
                    {{ s.action_type || 'click' }} <span style="color:#909399">{{ s.locator_value ? '(' + s.locator_value.substring(0, 60) + (s.locator_value.length > 60 ? '...' : '') + ')' : '' }}</span>
                  </template>
                  <template v-else>
                    {{ s.instruction }}
                  </template>
                </span>
                <el-tag v-if="s.type" size="small" style="margin-left:6px">{{ s.type }}</el-tag>
                <el-tag v-if="s.output_var" type="warning" size="small" style="margin-left:6px">→ {{ s.output_var }}</el-tag>
                <div v-if="s.screenshot && s.status === 'failed'" style="width:100%;margin-top:6px;margin-left:0">
                  <el-image :src="s.screenshot" fit="contain" style="max-width:360px;max-height:200px;border:1px solid #ebeef5;border-radius:4px" :preview-src-list="[s.screenshot]" preview-teleported />
                  <div style="margin-top:4px;display:flex;gap:6px">
                    <el-button size="small" text type="primary" @click="saveAsBaseline(s.screenshot)">设为基线</el-button>
                    <el-button size="small" text type="primary" @click="openVisualCompare(s.screenshot)">视觉对比</el-button>
                  </div>
                </div>
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

    <!-- 视觉对比弹窗 -->
    <el-dialog v-model="visualCompareVisible" title="视觉回归对比" width="860px" destroy-on-close>
      <div class="visual-compare-body">
        <!-- 基线选择 -->
        <div class="vc-section">
          <div class="vc-section__title">基线截图</div>
          <div v-if="baselineList.length === 0" style="color:#909399;font-size:13px;padding:8px 0">
            暂无基线，请先将某次失败截图设为基线
          </div>
          <el-radio-group v-else v-model="selectedBaselineUrl" style="display:flex;flex-direction:column;gap:8px">
            <el-radio v-for="b in baselineList" :key="b.url" :value="b.url" style="display:flex;align-items:center;gap:8px">
              <el-image :src="b.url" fit="contain" class="vc-thumb" />
              <span style="font-size:12px;color:#606266">{{ formatBaselineTime(b.saved_at) }}</span>
            </el-radio>
          </el-radio-group>
        </div>
        <!-- 当前截图 -->
        <div class="vc-section">
          <div class="vc-section__title">当前截图</div>
          <el-image v-if="visualCompareCurrentUrl" :src="visualCompareCurrentUrl" fit="contain" class="vc-current-img" />
        </div>
      </div>
      <!-- 对比结果 -->
      <div v-if="compareResult" class="vc-result">
        <div class="vc-result__header">
          <el-tag :type="compareResult.match ? 'success' : 'danger'" size="small">
            {{ compareResult.match ? '完全匹配' : '存在差异' }}
          </el-tag>
          <span style="margin-left:8px;font-size:13px;color:#606266">
            差异像素: {{ compareResult.diff_pixels }} / {{ compareResult.total_pixels }} ({{ compareResult.diff_percent }}%)
          </span>
        </div>
        <div class="vc-result__images">
          <div class="vc-result__img-box">
            <div class="vc-result__img-label">基线</div>
            <el-image :src="compareResult.baseline_url" fit="contain" class="vc-result__img" :preview-src-list="[compareResult.baseline_url]" preview-teleported />
          </div>
          <div class="vc-result__img-box">
            <div class="vc-result__img-label">差异</div>
            <el-image v-if="!compareResult.match" :src="compareResult.diff_url" fit="contain" class="vc-result__img" :preview-src-list="[compareResult.diff_url]" preview-teleported />
            <div v-else style="display:flex;align-items:center;justify-content:center;height:100%;color:#67c23a;font-size:14px">无差异</div>
          </div>
          <div class="vc-result__img-box">
            <div class="vc-result__img-label">当前</div>
            <el-image :src="compareResult.current_url" fit="contain" class="vc-result__img" :preview-src-list="[compareResult.current_url]" preview-teleported />
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="visualCompareVisible = false">关闭</el-button>
        <el-button type="primary" :loading="compareLoading" :disabled="!selectedBaselineUrl" @click="doVisualCompare">执行对比</el-button>
      </template>
    </el-dialog>

    <!-- 分组右键菜单 -->
    <div v-if="showGroupContextMenu" class="group-context-menu"
      :style="{ left: groupContextMenuX + 'px', top: groupContextMenuY + 'px' }">
      <div class="context-menu-item" @click="editGroupNode">编辑</div>
      <div class="context-menu-item" @click="addSubGroup">新增子分组</div>
      <div class="context-menu-item danger" @click="deleteGroupNode">删除</div>
    </div>

    <!-- 新建/编辑分组弹窗 -->
    <el-dialog v-model="showGroupDialog" :title="editingGroup ? '编辑分组' : '新增分组'" width="450px" destroy-on-close @close="resetGroupForm">
      <el-form :model="groupForm" label-width="80px">
        <el-form-item label="分组名称" required>
          <el-input v-model="groupForm.name" />
        </el-form-item>
        <el-form-item label="父分组">
          <el-tree-select
            v-model="groupForm.parent_id"
            :data="groupTreeSelectData"
            :props="{ children: 'children', label: 'name', value: 'id' }"
            placeholder="无（顶级分组）"
            clearable
            check-strictly
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="groupForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGroupDialog = false">取消</el-button>
        <el-button type="primary" @click="saveGroupForm">{{ editingGroup ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import { Download, Plus, VideoPlay, Delete, Loading, Check, Close, Search, CaretRight, CaretLeft, Edit, MagicStick, ArrowRight, ArrowDown, CopyDocument, PictureFilled } from '@element-plus/icons-vue'
import ActionCell from '@/components/ActionCell.vue'
import {
  getMidsceneGroups, getMidsceneGroupTree, createMidsceneGroup, updateMidsceneGroup, deleteMidsceneGroup, batchReorderMidsceneGroups,
  getMidsceneCases, createMidsceneCase, updateMidsceneCase, deleteMidsceneCase,
  batchDeleteMidsceneCases, importAIToMidscene, runMidsceneCase, copyMidsceneCase,
  getMidsceneExecutionDetail, getMidsceneExecutionStatus,
  midsceneVisualCompare, midsceneSaveBaseline, midsceneListBaselines,
  getMidsceneExecutions,
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
  loadGroups()
  loadCases()
}

// ---- 视觉回归 ----
const visualCompareVisible = ref(false)
const visualCompareCurrentUrl = ref('')
const baselineList = ref([])
const selectedBaselineUrl = ref('')
const compareResult = ref(null)
const compareLoading = ref(false)

function formatBaselineTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function saveAsBaseline(screenshotUrl) {
  // 用当前选中的用例或最近执行的用例获取case_id
  const caseId = selectedCase.value?.id || drawerResultData.value?.case_id || resultData.value?.case_id
  if (!caseId) {
    ElMessage.warning('无法确定用例ID，请先选中一个用例')
    return
  }
  try {
    const res = await midsceneSaveBaseline({ case_id: caseId, screenshot_url: screenshotUrl })
    ElMessage.success('基线已保存')
  } catch (e) {
    ElMessage.error('基线保存失败：' + (e.response?.data?.error || e.message))
  }
}

async function openVisualCompare(screenshotUrl) {
  visualCompareCurrentUrl.value = screenshotUrl
  compareResult.value = null
  selectedBaselineUrl.value = ''
  visualCompareVisible.value = true

  // 加载基线列表
  const caseId = selectedCase.value?.id || drawerResultData.value?.case_id || resultData.value?.case_id
  if (!caseId) {
    baselineList.value = []
    return
  }
  try {
    const res = await midsceneListBaselines({ case_id: caseId })
    baselineList.value = res.data?.baselines || []
  } catch {
    baselineList.value = []
  }
}

async function doVisualCompare() {
  if (!selectedBaselineUrl.value || !visualCompareCurrentUrl.value) return
  compareLoading.value = true
  compareResult.value = null
  try {
    const res = await midsceneVisualCompare({
      baseline: selectedBaselineUrl.value,
      current: visualCompareCurrentUrl.value,
    })
    compareResult.value = res.data || null
  } catch (e) {
    ElMessage.error('对比失败：' + (e.response?.data?.error || e.message))
  } finally {
    compareLoading.value = false
  }
}

// ---- 分组 ----
const groupTreeRef = ref(null)
const groups = ref([])
const currentGroupId = ref(null)
const showGroupDialog = ref(false)
const editingGroup = ref(null)           // null=新建, object=编辑
const groupForm = reactive({ name: '', parent_id: null, description: '' })
const groupExpandedKeys = ref([])
const showGroupContextMenu = ref(false)
const groupContextMenuX = ref(0)
const groupContextMenuY = ref(0)
const groupRightClickNode = ref(null)

// 组装 el-tree 数据：全部 + 未分组 + 用户分组树
const groupTreeWithAll = computed(() => {
  const allNode = { id: '__all__', name: '全部', case_count: 0, children: [] }
  const ungroupedNode = { id: '__ungrouped__', name: '未分组', case_count: 0, children: [] }
  // 统计全部和未分组的用例数
  const countAll = (list) => {
    let c = 0
    for (const g of list) {
      c += (g.case_count || 0)
      if (g.children?.length) c += countAll(g.children)
    }
    return c
  }
  allNode.case_count = countAll(groups.value)
  return [allNode, ungroupedNode, ...groups.value]
})

// 父分组选择数据（编辑时排除自身及子树）
const groupTreeSelectData = computed(() => {
  const filterSelf = (list, excludeId) => {
    return list.filter(item => {
      if (item.id === excludeId) return false
      if (item.children?.length) {
        item = { ...item, children: filterSelf(item.children, excludeId) }
      }
      return true
    })
  }
  if (editingGroup.value) {
    return filterSelf(JSON.parse(JSON.stringify(groups.value)), editingGroup.value.id)
  }
  return groups.value
})

async function loadGroups() {
  try {
    const params = {}
    if (projectId.value) params.project_id = projectId.value
    const res = await getMidsceneGroupTree(params)
    groups.value = res.data || []
  } catch {}
}

function onGroupNodeClick(data) {
  if (data.id === '__all__') {
    currentGroupId.value = null
  } else if (data.id === '__ungrouped__') {
    currentGroupId.value = 'ungrouped'
  } else {
    currentGroupId.value = data.id
  }
  currentPage.value = 1
  loadCases()
}

// 右键菜单
function onGroupRightClick(data, node, ev) {
  if (data.id === '__all__' || data.id === '__ungrouped__') return
  groupRightClickNode.value = { data, node }
  groupContextMenuX.value = ev.clientX
  groupContextMenuY.value = ev.clientY
  showGroupContextMenu.value = true
}

function editGroupNode() {
  showGroupContextMenu.value = false
  if (!groupRightClickNode.value) return
  const data = groupRightClickNode.value.data
  const node = groupRightClickNode.value.node
  // 优先从data取id，兜底从node.key取
  const groupId = data.id ?? node?.key ?? node?.id
  if (!groupId && groupId !== 0) {
    ElMessage.error('无法获取分组ID，请刷新页面后重试')
    return
  }
  editingGroup.value = { ...data, id: groupId }
  groupForm.name = data.name || ''
  groupForm.parent_id = data.parent_id ?? null
  groupForm.description = data.description || ''
  showGroupDialog.value = true
}

function addSubGroup() {
  showGroupContextMenu.value = false
  if (!groupRightClickNode.value) return
  const data = groupRightClickNode.value.data
  editingGroup.value = null
  groupForm.name = ''
  groupForm.parent_id = data.id
  groupForm.description = ''
  showGroupDialog.value = true
}

async function deleteGroupNode() {
  showGroupContextMenu.value = false
  if (!groupRightClickNode.value) return
  const data = groupRightClickNode.value.data
  try {
    await ElMessageBox.confirm(`确定要删除分组「${data.name}」吗？子分组将一并删除，用例将移至未分组。`, '确认删除', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteMidsceneGroup(data.id)
    if (currentGroupId.value === data.id) {
      currentGroupId.value = null
      loadCases()
    }
    loadGroups()
    ElMessage.success('分组已删除')
  } catch {}
}

// 拖拽排序
function allowGroupDrag() { return true }
function allowGroupDrop(draggingNode, dropNode, type) {
  // 不允许拖到"全部"和"未分组"上
  if (dropNode.data.id === '__all__' || dropNode.data.id === '__ungrouped__') return type !== 'inner'
  return true
}

async function onGroupNodeDrop(draggingNode, dropNode, dropType) {
  // 收集同级节点的新顺序
  const siblings = dropNode.parent.childNodes
  const parentId = dropNode.parent.data.id
  const orders = siblings
    .filter(n => n.data.id !== '__all__' && n.data.id !== '__ungrouped__')
    .map((n, i) => {
      const item = { id: n.data.id, order: i }
      if (dropType === 'inner') {
        item.parent = dropNode.data.id
      } else {
        item.parent = (parentId === '__all__' || parentId === '__ungrouped__' || !parentId) ? null : parentId
      }
      return item
    })
  try {
    await batchReorderMidsceneGroups({ orders })
  } catch {
    ElMessage.error('排序保存失败')
    loadGroups()
  }
}

async function saveGroupForm() {
  if (!groupForm.name) return ElMessage.warning('请输入分组名称')
  try {
    if (editingGroup.value) {
      const groupId = editingGroup.value.id
      if (!groupId && groupId !== 0) {
        console.error('编辑分组ID为空:', editingGroup.value)
        ElMessage.error('分组ID无效，请刷新页面后重试')
        return
      }
      await updateMidsceneGroup(groupId, {
        name: groupForm.name,
        parent_id: groupForm.parent_id,
      })
      ElMessage.success('分组已更新')
    } else {
      await createMidsceneGroup({
        name: groupForm.name,
        parent_id: groupForm.parent_id || null,
        project_id: projectId.value || null,
      })
      ElMessage.success('分组已创建')
    }
    showGroupDialog.value = false
    loadGroups()
  } catch {
    ElMessage.error(editingGroup.value ? '更新失败' : '创建失败')
  }
}

function resetGroupForm() {
  editingGroup.value = null
  groupForm.name = ''
  groupForm.parent_id = null
  groupForm.description = ''
}

// 点击空白处关闭右键菜单
function closeGroupContextMenu(e) {
  if (showGroupContextMenu.value && !e.target.closest('.group-context-menu')) {
    showGroupContextMenu.value = false
  }
}

// 分组面板顶部的"添加"按钮：新建顶级分组
function openAddGroup() {
  editingGroup.value = null
  groupForm.name = ''
  groupForm.parent_id = null
  groupForm.description = ''
  showGroupDialog.value = true
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
const filterStatus = ref('')
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
  if (filterStatus.value) {
    list = list.filter(c => c.last_status === filterStatus.value)
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
function onFilterChange() {
  currentPage.value = 1
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
    const data = res.data
    // 后端返回 { count, results }，直接取 results
    cases.value = Array.isArray(data) ? data : (data.results || [])

    // 刷新列表后，保持 selectedCase 与新数据同步
    if (selectedCase.value) {
      const updated = cases.value.find(c => c.id === selectedCase.value.id)
      if (updated) selectedCase.value = updated
    }
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
      key: 'copy',
      label: '复制',
      type: 'primary',
      onClick: (r) => copyCase(r),
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
const caseExpandedSteps = ref(new Set())

// ---- 抽屉步骤折叠 ----
const drawerExpandedSteps = ref(new Set())
// ---- AI模型覆盖弹窗 ----
const showAiModelOverrideDrawer = ref(false)
const aiOverrideEdit = reactive({
  default: { modelProvider: '', modelName: '', apiKey: '', baseURL: '' },
  insight: { modelProvider: '', modelName: '', apiKey: '', baseURL: '' },
  planning: { modelProvider: '', modelName: '', apiKey: '', baseURL: '' }
})

function openAiModelOverride() {
  const src = drawerForm.ai_model_config_override || {}
  aiOverrideEdit.default = { ...aiOverrideEdit.default, ...(src.default || {}) }
  aiOverrideEdit.insight = { ...aiOverrideEdit.insight, ...(src.insight || {}) }
  aiOverrideEdit.planning = { ...aiOverrideEdit.planning, ...(src.planning || {}) }
  showAiModelOverrideDrawer.value = true
}

function saveAiModelOverride() {
  const result = {}
  const build = (entry) => {
    const r = {}
    if (entry.modelProvider) r.modelProvider = entry.modelProvider
    if (entry.modelName) r.modelName = entry.modelName
    if (entry.apiKey && !entry.apiKey.includes('*')) r.apiKey = entry.apiKey
    if (entry.baseURL) r.baseURL = entry.baseURL
    return r
  }
  const d = build(aiOverrideEdit.default)
  const i = build(aiOverrideEdit.insight)
  const p = build(aiOverrideEdit.planning)
  if (Object.keys(d).length) result.default = d
  if (Object.keys(i).length) result.insight = i
  if (Object.keys(p).length) result.planning = p
  drawerForm.ai_model_config_override = result
  showAiModelOverrideDrawer.value = false
}

function toggleCaseStep(idx) {
  if (caseExpandedSteps.value.has(idx)) {
    caseExpandedSteps.value.delete(idx)
  } else {
    caseExpandedSteps.value.add(idx)
  }
}

function toggleDrawerStep(idx) {
  if (drawerExpandedSteps.value.has(idx)) {
    drawerExpandedSteps.value.delete(idx)
  } else {
    drawerExpandedSteps.value.add(idx)
  }
}
const caseForm = reactive({
  name: '', platform: 'web', device_type: '', description: '', group_id: null,
  url: '', headless: false, cache_strategy: 'normal', new_tab: false,
  user_agent: '', viewport_width: 1280, viewport_height: 768, device_scale_factor: 1.0,
  cookie_file: '', wait_for_network_idle_timeout: null, continue_on_network_idle_error: true,
  device_id: '', package_name: '', app_activity: '',
  steps: [],
  output_variables: [],
  precondition_sql: '',
  postcondition_sql: '',
})

// 平台切换联动device_type
watch(() => caseForm.platform, (val) => {
  if (val === 'app') {
    if (!caseForm.device_type) caseForm.device_type = 'android'
  } else {
    caseForm.device_type = ''
  }
})

function openCreateDialog() {
  const defaultPlatform = routePlatform.value || 'web'
  Object.assign(caseForm, {
    name: '', platform: defaultPlatform, device_type: defaultPlatform === 'app' ? 'android' : '', description: '', group_id: null,
    url: '', headless: false, cache_strategy: 'normal', new_tab: false,
    user_agent: '', viewport_width: 1280, viewport_height: 768, device_scale_factor: 1.0,
    cookie_file: '', wait_for_network_idle_timeout: null, continue_on_network_idle_error: true,
    device_id: '', package_name: '', app_activity: '',
    steps: [],
    output_variables: [],
    precondition_sql: '',
    postcondition_sql: '',
  })
  caseExpandedSteps.value = new Set()
  caseDialogVisible.value = true
}

function addStep(mode = 'ai') {
  const idx = caseForm.steps.length
  caseForm.steps.push({
    order: idx + 1, type: 'action', mode,
    instruction: '', input_value: '', output_var: '',
    locator_value: '', action_type: '', assert_type: '', assert_value: '',
    retry_count: 0
  })
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

async function copyCase(row) {
  try {
    await copyMidsceneCase(row.id)
    ElMessage.success('用例已复制')
    loadCases()
  } catch (e) {
    ElMessage.error('复制失败: ' + (e?.response?.data?.error || e.message))
  }
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

// ---- 执行历史 ----
const caseHistoryList = ref([])
const caseHistoryLoading = ref(false)

async function loadCaseHistory(caseId) {
  caseHistoryLoading.value = true
  try {
    const res = await getMidsceneExecutions({ case_id: caseId, page_size: 50 })
    caseHistoryList.value = res.data?.results || res.data || []
  } catch {
    caseHistoryList.value = []
  } finally {
    caseHistoryLoading.value = false
  }
}

function viewHistoryDetail(row) {
  // 将历史记录加载到执行结果弹窗中查看
  resultData.value = row
  resultActiveTab.value = 'steps'
  resultDialogVisible.value = true
}

// 监听detailActiveTab切换到执行历史时加载数据
watch(detailActiveTab, (val) => {
  if (val === 'history' && selectedCase.value) {
    loadCaseHistory(selectedCase.value.id)
  }
})

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
  device_type: '', // Midscene设备类型覆盖（web/android/ios/harmony）
  ai_model_config_override: {}, // AI模型覆盖（三级意图）
  device_config_override: {}, // 设备配置覆盖
  app_name_mapping: {}, // App名称映射覆盖
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
    device_type: caseData.device_type || '',
    ai_model_config_override: caseData.ai_model_config_override || {},
    device_config_override: caseData.device_config_override || {},
    app_name_mapping: caseData.app_name_mapping || {},
    steps: (caseData.steps || []).map(s => ({ ...s, mode: s.mode || 'ai', input_value: s.input_value || '', output_var: s.output_var || '', locator_value: s.locator_value || '', action_type: s.action_type || '', assert_type: s.assert_type || '', assert_value: s.assert_value || '', retry_count: s.retry_count ?? 0 })),
    output_variables: caseData.output_variables || [],
    precondition_sql: caseData.precondition_sql || '',
    postcondition_sql: caseData.postcondition_sql || '',
  })
  detailActiveTab.value = 'info'
  drawerResultData.value = null
  drawerExpandedSteps.value = new Set()
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

function addStepToDrawer(mode = 'ai') {
  const idx = drawerForm.steps.length
  drawerForm.steps.push({
    order: idx + 1, type: 'action', mode,
    instruction: '', input_value: '', output_var: '',
    // 传统模式字段（AI模式不使用）
    locator_value: '', action_type: '', assert_type: '', assert_value: '',
    retry_count: 0
  })
}

function toggleStepMode(step) {
  // 检查当前是否为APP端环境（通过抽屉或新建弹窗的platform判断）
  const currentPlatform = detailDrawerVisible.value ? drawerForm.platform : caseForm.platform
  if (step.mode !== 'traditional' && currentPlatform === 'app') {
    ElMessage.warning('APP端不支持传统模式步骤，请使用AI模式')
    return
  }
  if (step.mode === 'traditional') {
    step.mode = 'ai'
  } else {
    step.mode = 'traditional'
    // 切到传统时，如果缺少字段则补默认值
    if (!step.locator_value) step.locator_value = ''
    if (!step.action_type) step.action_type = 'click'
    if (!step.assert_type) step.assert_type = ''
    if (!step.assert_value) step.assert_value = ''
  }
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
        // 只更新行级状态，不重新加载整个列表（避免过滤条件导致用例消失）
        row.last_status = data.status
        row.last_executed_at = data.started_at || new Date().toISOString()
        row.last_duration = data.duration || null
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
  // 不再全量重载列表，pollStatus 会逐条行级更新状态
  // 如果需要兜底，10秒后仅刷新一次状态而非全量加载
  setTimeout(() => {
    cases.value.forEach(c => {
      if (runningIds[c.id]) runningIds[c.id] = false
    })
  }, 10000)
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
  document.addEventListener('click', closeGroupContextMenu)
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
  overflow-y: auto;
}

.group-tree-wrapper :deep(.el-tree) {
  background: transparent;
}

.group-tree-wrapper :deep(.el-tree-node__content) {
  height: 36px;
  padding-left: 8px !important;
}

.group-tree-wrapper :deep(.el-tree-node__content:hover) {
  background: var(--gray-100);
}

.group-tree-wrapper :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: var(--brand-50);
  color: var(--brand-700);
  font-weight: 500;
}

.group-tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
  overflow: hidden;
}

.group-tree-label {
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
  margin-left: 8px;
}

/* 右键菜单 */
.group-context-menu {
  position: fixed;
  z-index: 9999;
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
  padding: 4px 0;
  min-width: 120px;
}

.group-context-menu .context-menu-item {
  padding: 7px 16px;
  font-size: 13px;
  color: var(--gray-700);
  cursor: pointer;
  transition: background 0.15s;
}

.group-context-menu .context-menu-item:hover {
  background: var(--gray-100);
}

.group-context-menu .context-menu-item.danger {
  color: var(--red-600);
}

.group-context-menu .context-menu-item.danger:hover {
  background: var(--red-50);
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
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.15s;
}

.step-row-main:hover {
  background-color: #f0f2f5;
}

.step-mode-tag {
  flex-shrink: 0;
  user-select: none;
}

.step-toggle-icon {
  cursor: pointer;
  transition: transform 0.2s ease;
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}

.step-toggle-icon.is-expanded {
  transform: rotate(90deg);
}

.step-row-params {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

/* 参数行占位：和主行对应元素等宽，确保输入值/输出变量和 instruction 对齐 */
.step-params-indent-toggle {
  flex-shrink: 0;
  /* 和 .step-toggle-icon 同宽（icon font-size 12px + 自身无额外宽度） */
  width: 12px;
}

.step-params-indent-order {
  flex-shrink: 0;
  /* 和 .step-order 同宽 */
  width: 24px;
}

.step-params-indent-select {
  flex-shrink: 0;
  /* 和 el-select style=width:90px 同宽 */
  width: 90px;
}

.step-params-indent-delete {
  flex-shrink: 0;
  /* 和删除按钮（icon 16px + padding）同宽 */
  width: 24px;
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

/* ============================================================
   视觉回归对比
   ============================================================ */
.visual-compare-body {
  display: flex;
  gap: 20px;
  min-height: 200px;
}

.vc-section {
  flex: 1;
  min-width: 0;
}

.vc-section__title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  margin-bottom: 8px;
}

.vc-thumb {
  width: 80px;
  height: 50px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  vertical-align: middle;
}

.vc-current-img {
  max-width: 100%;
  max-height: 180px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.vc-result {
  margin-top: 16px;
  border-top: 1px solid #ebeef5;
  padding-top: 12px;
}

.vc-result__header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.vc-result__images {
  display: flex;
  gap: 12px;
}

.vc-result__img-box {
  flex: 1;
  min-width: 0;
}

.vc-result__img-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
  text-align: center;
}

.vc-result__img {
  width: 100%;
  max-height: 240px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
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