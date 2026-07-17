<template>
  <div class="page-container">
    <!-- 顶部标题栏 -->
    <header class="page-titlebar">
      <h1 class="page-title">元素管理</h1>
      <div class="titlebar-actions">
        <el-select v-model="selectedProject" :placeholder="$t('common.selectProject')" @change="onProjectChange" class="titlebar-select">
          <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
        <el-button type="primary" size="small" @click="onCreateElement">
          <el-icon><Plus /></el-icon>
          <span>新增</span>
        </el-button>
        <el-button type="primary" size="small" @click="showAiExtractDialog = true">AI提取</el-button>
      </div>
    </header>

    <!-- 两栏工作区（Grid 布局，搜索卡片对齐右侧列） -->
    <div class="workspace">
      <!-- 左侧：页面分组面板（占第1列，跨2行） -->
      <section class="panel group-panel">
        <div class="panel__header">
          <span class="panel__title">页面分组</span>
          <el-button text size="small" class="panel__action" @click="showCreatePageDialog = true">
            <el-icon><Plus /></el-icon>
            <span>添加</span>
          </el-button>
        </div>
        <div class="panel__body group-tree-wrapper">
          <el-tree
            ref="pageTreeRef"
            :data="pageGroupTreeWithAll"
            :props="{ children: 'children', label: 'name' }"
            node-key="id"
            :current-node-key="selectedPageId === null ? '__all__' : selectedPageId"
            :expand-on-click-node="false"
            :default-expanded-keys="pageExpandedKeys"
            highlight-current
            @node-click="onPageGroupClick"
            @node-contextmenu="onPageGroupRightClick"
          >
            <template #default="{ node, data }">
              <div class="group-tree-node">
                <span class="group-node-label">{{ node.label }}</span>
                <span v-if="data.id !== '__all__'" class="group-count">{{ data.element_count || data.children?.length || 0 }}</span>
              </div>
            </template>
          </el-tree>
        </div>
      </section>

      <!-- 右侧上方：搜索区域卡片（对齐右侧列宽度） -->
      <div class="filter-bar">
        <el-form :inline="true">
          <el-form-item label="元素名称">
            <el-input v-model="searchName" placeholder="请输入元素名称" clearable style="width: 180px" />
          </el-form-item>
          <el-form-item label="元素类型">
            <el-select v-model="searchType" placeholder="全部" clearable style="width: 130px">
              <el-option label="按钮" value="BUTTON" />
              <el-option label="输入框" value="INPUT" />
              <el-option label="链接" value="LINK" />
              <el-option label="下拉框" value="DROPDOWN" />
              <el-option label="复选框" value="CHECKBOX" />
              <el-option label="单选框" value="RADIO" />
              <el-option label="文本" value="TEXT" />
              <el-option label="图片" value="IMAGE" />
              <el-option label="表格" value="TABLE" />
              <el-option label="表单" value="FORM" />
              <el-option label="弹窗" value="MODAL" />
            </el-select>
          </el-form-item>
          <el-form-item label="定位策略">
            <el-select v-model="searchStrategy" placeholder="全部" clearable style="width: 130px">
              <el-option v-for="strategy in locatorStrategies" :key="strategy.id" :label="strategy.name" :value="strategy.id" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <!-- 右侧下方：元素列表面板 -->
      <section class="panel list-panel">
        <div class="panel__header">
          <span class="panel__title">元素列表</span>
        </div>
        <div class="panel__body">
          <el-table :data="filteredElements" highlight-current-row size="small" :row-class-name="getElementRowClass">
            <el-table-column prop="name" label="元素名称" min-width="120" show-overflow-tooltip />
            <el-table-column prop="element_type" label="类型" width="80">
              <template #default="{ row }">
                <span class="element-type-tag" :class="(row.element_type || '').toLowerCase()">{{ getElementTypeLabel(row.element_type) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="定位策略" width="90">
              <template #default="{ row }">{{ getStrategyName(row.locator_strategy_id) }}</template>
            </el-table-column>
            <el-table-column prop="locator_value" label="定位表达式" min-width="160" show-overflow-tooltip />
            <el-table-column prop="wait_timeout" label="超时" width="65" align="center">
              <template #default="{ row }">{{ row.wait_timeout || 5 }}s</template>
            </el-table-column>
            <el-table-column label="强制" width="55" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.force_action" type="danger" size="small">是</el-tag>
                <span v-else style="color: var(--gray-400)">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="100" show-overflow-tooltip />
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <div class="op-btns">
                  <el-tooltip content="编辑" placement="top">
                    <el-button class="op-btn" type="primary" link size="small" @click.stop="onEditElement(row)"><el-icon><Edit /></el-icon></el-button>
                  </el-tooltip>
                  <el-tooltip content="复制" placement="top">
                    <el-button class="op-btn" type="primary" link size="small" @click.stop="copyElementFromList(row)"><el-icon><CopyDocument /></el-icon></el-button>
                  </el-tooltip>
                  <el-tooltip content="删除" placement="top">
                    <el-button class="op-btn op-btn--danger" link size="small" @click.stop="deleteElementFromList(row)"><el-icon><Delete /></el-icon></el-button>
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="filteredElements.length === 0" class="no-data-tip">暂无元素</div>
        </div>
      </section>
    </div>

    <!-- 新增/编辑元素弹窗 -->
    <el-dialog v-model="showElementDialog" :title="elementDialogTitle" width="620px" :close-on-click-modal="false" @closed="onElementDialogClosed">
      <el-form ref="elementFormRef" :key="formKey" :model="selectedElement" :rules="elementRules" label-width="100px" class="element-dialog-form">
        <el-form-item prop="name" label="元素名称" required>
          <el-input v-model="selectedElement.name" placeholder="输入元素名称" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="类型" prop="element_type">
              <el-select v-model="selectedElement.element_type" placeholder="元素类型" style="width: 100%">
                <el-option label="按钮" value="BUTTON" />
                <el-option label="输入框" value="INPUT" />
                <el-option label="链接" value="LINK" />
                <el-option label="下拉框" value="DROPDOWN" />
                <el-option label="复选框" value="CHECKBOX" />
                <el-option label="单选框" value="RADIO" />
                <el-option label="文本" value="TEXT" />
                <el-option label="图片" value="IMAGE" />
                <el-option label="表格" value="TABLE" />
                <el-option label="表单" value="FORM" />
                <el-option label="弹窗" value="MODAL" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属页面">
              <el-tree-select
                v-model="selectedElement.page"
                :data="pageOnlyTree"
                :props="{ label: 'name', value: 'name', children: 'children' }"
                placeholder="选择页面"
                check-strictly
                :render-after-expand="false"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="组件名称">
              <el-input v-model="selectedElement.component_name" placeholder="组件名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="超时(秒)">
              <el-input-number v-model="selectedElement.wait_timeout" :min="1" :max="60" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="定位策略" prop="locator_strategy_id" required>
              <el-select
                v-model="selectedElement.locator_strategy_id"
                :key="`strategy-${formKey}-${selectedElement.locator_strategy_id || 'null'}`"
                placeholder="选择定位策略"
                style="width: 100%"
              >
                <el-option v-for="strategy in locatorStrategies" :key="strategy.id" :label="strategy.name" :value="strategy.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="强制操作">
              <el-switch v-model="selectedElement.force_action" />
              <div class="form-help-text">跳过可见性检查，直接操作</div>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="定位表达式" prop="locator_value" required>
          <el-input v-model="selectedElement.locator_value" placeholder="输入定位表达式" />
          <div class="form-help-text">支持：ID / CSS / XPath / name / class / text / placeholder / role / label / title / test-id</div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="selectedElement.description" type="textarea" :rows="3" placeholder="元素描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showElementDialog = false">取消</el-button>
        <el-button type="primary" @click="saveElement" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 创建页面对话框 -->
    <el-dialog v-model="showCreatePageDialog" :title="$t('uiAutomation.element.createPageTitle')" width="500px" :close-on-click-modal="false">
      <el-form ref="pageFormRef" :model="pageForm" :rules="pageRules" label-width="80px">
        <el-form-item :label="$t('uiAutomation.element.pageName')" prop="name">
          <el-input v-model="pageForm.name" :placeholder="$t('uiAutomation.element.pageNamePlaceholder')" />
        </el-form-item>
        <el-form-item label="父页面">
          <el-select v-model="pageForm.parent_page" placeholder="选择父页面" clearable>
            <el-option v-for="page in getAllPages()" :key="page.id" :label="page.name" :value="page.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="pageForm.description" type="textarea" :rows="3" placeholder="页面描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreatePageDialog = false">取消</el-button>
        <el-button type="primary" @click="createPage">确认</el-button>
      </template>
    </el-dialog>

    <!-- 页面分组右键菜单 -->
    <ul v-show="showGroupContextMenu" class="group-context-menu" :style="{ left: groupContextMenuX + 'px', top: groupContextMenuY + 'px' }">
      <li @click="addContextElement">新增元素</li>
      <li v-if="rightClickedGroupNode && rightClickedGroupNode.type === 'page' && rightClickedGroupNode.id !== 'unassigned'" @click="addSubPage">新增子页面</li>
      <li v-if="rightClickedGroupNode && rightClickedGroupNode.id !== 'unassigned'" @click="editGroupNode">编辑</li>
      <li v-if="rightClickedGroupNode && rightClickedGroupNode.id !== 'unassigned'" @click="deleteGroupNode">删除</li>
      <li v-if="rightClickedGroupNode && rightClickedGroupNode.id === 'unassigned'" class="danger" @click="deleteUnassignedElements">清空未关联元素</li>
    </ul>

    <!-- 编辑页面对话框 -->
    <el-dialog v-model="showEditPageDialog" :title="$t('uiAutomation.element.editPageTitle')" width="500px" :close-on-click-modal="false">
      <el-form ref="editPageFormRef" :model="editPageForm" :rules="pageRules" label-width="80px">
        <el-form-item :label="$t('uiAutomation.element.pageName')" prop="name">
          <el-input v-model="editPageForm.name" :placeholder="$t('uiAutomation.element.pageNamePlaceholder')" />
        </el-form-item>
        <el-form-item label="父页面">
          <el-select v-model="editPageForm.parent_page" placeholder="选择父页面" clearable>
            <el-option v-for="page in getAllPagesExceptCurrent(editPageForm.id)" :key="page.id" :label="page.name" :value="page.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editPageForm.description" type="textarea" :rows="3" placeholder="页面描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditPageDialog = false">取消</el-button>
        <el-button type="primary" @click="updatePage">保存</el-button>
      </template>
    </el-dialog>

    <!-- AI智能提取输入对话框 -->
    <el-dialog v-model="showAiExtractDialog" title="AI 智能提取元素" width="550px" :close-on-click-modal="false">
      <el-form label-width="130px">
        <el-form-item label="目标页面URL" required>
          <el-input v-model="aiExtractForm.url" placeholder="输入页面URL，如 https://example.com/user/list" />
        </el-form-item>
        <el-form-item label="登录配置">
          <el-select v-model="aiExtractForm.login_config_id" placeholder="可选，需登录的页面选择" clearable style="width: 100%">
            <el-option v-for="cfg in loginConfigs" :key="cfg.id" :label="cfg.name" :value="cfg.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="页面名称">
          <el-input v-model="aiExtractForm.page_name" placeholder="可选，如 用户管理页" />
        </el-form-item>
      </el-form>
      <div v-if="aiExtractLoading" style="text-align: center; padding: 20px 0;">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <p style="margin-top: 10px; color: #909399;">{{ aiExtractProgress }}</p>
      </div>
      <template #footer>
        <el-button @click="showAiExtractDialog = false">取消</el-button>
        <el-button type="success" @click="handlePickStart" :loading="pickLoading">交互式选取</el-button>
        <el-button type="primary" @click="handleAiExtract" :loading="aiExtractLoading">开始提取</el-button>
      </template>
    </el-dialog>

    <!-- 交互式选取模式控制面板 -->
    <el-dialog v-model="showPickDialog" title="交互式选取模式" width="600px" :close-on-click-modal="false" :show-close="false" top="20vh">
      <el-alert type="success" :closable="false" show-icon style="margin-bottom: 16px;">
        <template #title>浏览器已打开，请在页面中点击要提取的元素。鼠标悬停会高亮显示，点击后AI自动识别定位器。</template>
      </el-alert>
      <div v-if="pickElements.length > 0" style="margin-bottom: 12px;">
        <div style="font-weight: 600; margin-bottom: 8px;">已选取元素（{{ pickElements.length }} 个）：</div>
        <el-table :data="pickElements" max-height="300" size="small">
          <el-table-column label="元素名称" min-width="120">
            <template #default="{ row }">{{ row.name || '未命名' }}</template>
          </el-table-column>
          <el-table-column label="类型" width="80">
            <template #default="{ row }"><el-tag size="small">{{ row.element_type || '-' }}</el-tag></template>
          </el-table-column>
          <el-table-column label="定位策略" width="80">
            <template #default="{ row }">{{ row.locator_strategy || '-' }}</template>
          </el-table-column>
          <el-table-column label="定位表达式" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ row.locator_value || '-' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="60">
            <template #default="{ $index }">
              <el-button type="danger" size="small" text @click="removePickElement($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else style="text-align: center; padding: 20px 0; color: #909399;">尚未选取任何元素，请在浏览器中点击页面元素</div>
      <template #footer>
        <el-button @click="handlePickFinish" type="success" :loading="pickLoading">完成选取</el-button>
      </template>
    </el-dialog>

    <!-- AI提取结果预览对话框 -->
    <el-dialog v-model="showAiResultDialog" title="AI 提取结果预览" width="900px" :close-on-click-modal="false" top="5vh">
      <div style="margin-bottom: 12px; color: #606266;">
        页面: {{ aiResultInfo.url }}
        <span v-if="aiResultInfo.final_url && aiResultInfo.final_url !== aiResultInfo.url" style="margin-left: 10px; color: #E6A23C;">(实际跳转: {{ aiResultInfo.final_url }})</span>
        <span v-if="aiResultInfo.page_title" style="margin-left: 10px;">标题: {{ aiResultInfo.page_title }}</span>
        <span style="margin-left: 10px;">共 {{ aiExtractResults.length }} 个元素</span>
      </div>
      <el-table ref="aiResultTableRef" :data="aiExtractResults" max-height="500" style="width: 100%" @selection-change="handleAiResultSelectionChange">
        <el-table-column type="selection" width="45" />
        <el-table-column label="元素名称" min-width="130">
          <template #default="{ row }"><el-input v-model="row.name" size="small" /></template>
        </el-table-column>
        <el-table-column label="类型" width="110">
          <template #default="{ row }">
            <el-select v-model="row.element_type" size="small">
              <el-option v-for="et in ['INPUT','BUTTON','LINK','DROPDOWN','CHECKBOX','RADIO','TEXT','IMAGE','TABLE','CONTAINER','FORM','MODAL']" :key="et" :label="et" :value="et" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="定位策略" width="100">
          <template #default="{ row }">
            <el-select v-model="row.locator_strategy" size="small">
              <el-option v-for="ls in ['ID','CSS','XPath','name','class','text','placeholder','role','label','title','test-id']" :key="ls" :label="ls" :value="ls" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="定位表达式" min-width="180">
          <template #default="{ row }"><el-input v-model="row.locator_value" size="small" /></template>
        </el-table-column>
        <el-table-column label="验证" width="80" align="center">
          <template #default="{ row }">
            <el-tooltip v-if="row.validation_status" :content="row.validation_details || ''" placement="top" :show-after="300">
              <el-tag v-if="row.validation_status === 'VALID'" type="success" size="small" effect="dark">有效</el-tag>
              <el-tag v-else-if="row.validation_status === 'PARTIAL'" type="warning" size="small" effect="dark">部分</el-tag>
              <el-tag v-else-if="row.validation_status === 'UNVALIDATED'" type="info" size="small" effect="dark">待验</el-tag>
              <el-tag v-else type="danger" size="small" effect="dark">无效</el-tag>
            </el-tooltip>
            <span v-else style="color: #c0c4cc; font-size: 12px;">-</span>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.source" type="info" size="small">{{ row.source }}</el-tag>
            <span v-else style="color: #c0c4cc; font-size: 12px;">主页面</span>
          </template>
        </el-table-column>
        <el-table-column label="描述" min-width="130">
          <template #default="{ row }"><el-input v-model="row.description" size="small" /></template>
        </el-table-column>
      </el-table>
      <template #footer>
        <div style="display: flex; justify-content: space-between; width: 100%;">
          <span></span>
          <div>
            <el-button @click="showAiResultDialog = false">取消</el-button>
            <el-button type="primary" @click="handleBatchImport" :loading="batchImportLoading">确认导入({{ selectedAiResults.length }}个元素)</el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 候选弹窗触发按钮选择对话框 -->
    <el-dialog v-model="showCandidateDialog" title="弹窗元素提取" width="700px" :close-on-click-modal="false" top="5vh">
      <div style="margin-bottom: 16px;">
        <el-alert type="info" :closable="false" show-icon>
          <template #title>检测到以下按钮可能触发弹窗，勾选后系统将自动点击并提取弹窗内元素</template>
        </el-alert>
      </div>
      <el-table :data="candidateButtons" @selection-change="handleCandidateSelectionChange" style="width: 100%" max-height="400">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="text" label="按钮文本" width="150" />
        <el-table-column prop="source" label="来源" width="120">
          <template #default="{ row }">
            <el-tag :type="row.source === '页面级按钮' ? 'primary' : 'warning'" size="small">{{ row.source }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="识别原因" />
      </el-table>
      <template #footer>
        <div style="display: flex; justify-content: space-between;">
          <el-button @click="handleManualModeStart" :loading="manualLoading" type="info">手动交互模式</el-button>
          <div>
            <el-button @click="showCandidateDialog = false">跳过</el-button>
            <el-button type="primary" @click="handleExtractDialogs" :loading="candidateLoading">自动提取勾选按钮的弹窗</el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 手动交互模式控制面板 -->
    <el-dialog v-model="showManualDialog" title="手动交互模式" width="500px" :close-on-click-modal="false" :show-close="false" top="30vh">
      <div style="margin-bottom: 16px;">
        <el-alert type="info" :closable="false" show-icon>
          <template #title>浏览器已打开，请手动操作到目标状态后，点击下方"提取当前页面"按钮</template>
        </el-alert>
      </div>
      <div v-if="manualCaptures.length > 0" style="margin-bottom: 16px;">
        <div style="font-weight: 600; margin-bottom: 8px;">已提取记录：</div>
        <div v-for="cap in manualCaptures" :key="cap.index" style="margin-bottom: 4px; color: #67c23a;">第{{ cap.index }}次 - {{ cap.page_name }}（{{ cap.element_count }} 个元素）</div>
      </div>
      <div style="margin-bottom: 12px;">
        <el-input v-model="aiExtractForm.page_name" placeholder="可选：为本次提取命名" size="small" clearable />
      </div>
      <template #footer>
        <el-button @click="handleManualCapture" :loading="manualLoading" type="primary">提取当前页面元素</el-button>
        <el-button @click="handleManualFinish" :loading="manualLoading" type="success">完成提取</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, FolderAdd, Document, Search, Edit, Delete,
  Folder, Document as DocumentIcon, Operation, DocumentCopy, ArrowDown,
  MagicStick, Loading, VideoPlay, CopyDocument
} from '@element-plus/icons-vue'
import {
  getUiProjects,
  getElements,
  createElement,
  getElementDetail,
  updateElement,
  deleteElement,
  getElementTree,
  getElementGroupTree,
  getElementGroups,
  createElementGroup,
  updateElementGroup,
  deleteElementGroup,
  getLocatorStrategies,
  validateElementLocator,
  generateElementSuggestions,
  aiExtractElements,
  aiExtractDialogs,
  aiExtractManualStart,
  aiExtractManualCapture,
  aiExtractManualFinish,
  aiPickStart,
  aiPickStatus,
  aiPickFinish,
  aiPickRemove,
  getLoginConfigs
} from '@/api/ui_automation'

// 国际化
const { t } = useI18n()

// 响应式数据
const projects = ref([])
const selectedProject = ref('')
const pages = ref([])
const locatorStrategies = ref([])
const treeData = ref([])

// 三栏布局相关
const selectedPageId = ref(null)   // 当前选中的页面分组ID（null=全部）
const pageExpandedKeys = ref([])
const searchName = ref('')
const searchType = ref('')
const searchStrategy = ref(null)
const pageTreeRef = ref(null)
const allElements = ref([])  // 扁平化的元素列表

// "全部"节点合并到页面分组树
const pageGroupTreeWithAll = computed(() => {
  const allNode = { id: '__all__', name: '全部', children: [] }
  // 从 treeData 提取仅页面节点（排除未关联页面的元素节点）
  const buildPageTree = (nodes) => {
    if (!nodes) return []
    return nodes
      .filter(n => n.type === 'page')
      .map(n => ({
        id: n.id,
        name: n.name,
        type: n.type,
        _originalId: n._originalId,
        element_count: n.children?.filter(c => c.type === 'element').length || 0,
        children: buildPageTree(n.children)
      }))
  }
  return [allNode, ...buildPageTree(treeData.value)]
})

// 根据选中页面和搜索关键词过滤元素
const filteredElements = computed(() => {
  let result = allElements.value
  // 按页面分组筛选
  if (selectedPageId.value !== null) {
    // 找到选中页面的原始ID
    const findOriginalId = (nodes) => {
      for (const n of nodes) {
        if (n.id === selectedPageId.value) return n._originalId || n.id
        if (n.children) {
          const found = findOriginalId(n.children)
          if (found) return found
        }
      }
      return null
    }
    const originalId = findOriginalId(treeData.value)
    // 特殊处理 unassigned
    if (selectedPageId.value === 'unassigned') {
      result = result.filter(e => !e.group_id && !e.group)
    } else if (originalId) {
      result = result.filter(e => {
        const gid = e.group_id ?? (e.group && e.group.id) ?? null
        return parseInt(gid) === parseInt(originalId)
      })
    }
  }
  // 按元素名称搜索
  if (searchName.value) {
    const kw = searchName.value.toLowerCase()
    result = result.filter(e => e.name && e.name.toLowerCase().includes(kw))
  }
  // 按元素类型筛选
  if (searchType.value) {
    result = result.filter(e => e.element_type === searchType.value)
  }
  // 按定位策略筛选
  if (searchStrategy.value) {
    result = result.filter(e => e.locator_strategy_id === searchStrategy.value)
  }
  return result
})

// 页面分组点击
const onPageGroupClick = (data) => {
  if (data.id === '__all__') {
    selectedPageId.value = null
  } else {
    selectedPageId.value = data.id
  }
}

// 页面分组右键
const showGroupContextMenu = ref(false)
const groupContextMenuX = ref(0)
const groupContextMenuY = ref(0)
const rightClickedGroupNode = ref(null)

const onPageGroupRightClick = (event, data) => {
  if (data.id === '__all__') return
  event.preventDefault()
  rightClickedGroupNode.value = data
  groupContextMenuX.value = event.clientX
  groupContextMenuY.value = event.clientY
  showGroupContextMenu.value = true
  const hideMenu = () => {
    showGroupContextMenu.value = false
    document.removeEventListener('click', hideMenu)
  }
  setTimeout(() => document.addEventListener('click', hideMenu), 100)
}

// 右键菜单操作（适配分组面板）
const addContextElement = () => {
  showGroupContextMenu.value = false
  elementDialogTitle.value = '新增元素'
  selectedElement.value = {
    name: '',
    element_type: 'BUTTON',
    page: '',
    component_name: '',
    locator_strategy_id: null,
    locator_value: '',
    wait_timeout: 5,
    force_action: false,
    description: ''
  }
  formKey.value += 1
  if (rightClickedGroupNode.value && rightClickedGroupNode.value.type === 'page') {
    if (rightClickedGroupNode.value.id === 'unassigned') {
      // 未关联页面不设置所属页面
    } else {
      const findPageNameById = (nodes, targetId) => {
        for (const n of nodes) {
          if ((n._originalId || n.id) === targetId || n.id === targetId) return n.name
          if (n.children) { const found = findPageNameById(n.children, targetId); if (found) return found }
        }
        return null
      }
      const origId = rightClickedGroupNode.value._originalId || rightClickedGroupNode.value.id
      selectedElement.value.page = findPageNameById(treeData.value, origId) || rightClickedGroupNode.value.name
      selectedElement.value.group_id = origId
    }
  }
  showElementDialog.value = true
}

const addSubPage = () => {
  showGroupContextMenu.value = false
  if (rightClickedGroupNode.value && rightClickedGroupNode.value.id === 'unassigned') {
    ElMessage.warning('未关联页面节点下不能创建子页面')
    return
  }
  showCreatePageDialog.value = true
  if (rightClickedGroupNode.value) {
    pageForm.parent_page = rightClickedGroupNode.value._originalId || rightClickedGroupNode.value.id
  }
}

const editGroupNode = async () => {
  showGroupContextMenu.value = false
  if (!rightClickedGroupNode.value) return
  if (rightClickedGroupNode.value.id === 'unassigned') {
    ElMessage.warning('未关联页面节点不能编辑')
    return
  }
  editPageForm.id = rightClickedGroupNode.value._originalId || rightClickedGroupNode.value.id
  editPageForm.name = rightClickedGroupNode.value.name
  editPageForm.description = rightClickedGroupNode.value.description || ''
  editPageForm.parent_page = rightClickedGroupNode.value.parent_group ?? null
  showEditPageDialog.value = true
}

const deleteGroupNode = async () => {
  showGroupContextMenu.value = false
  if (!rightClickedGroupNode.value) return
  if (rightClickedGroupNode.value.id === 'unassigned') {
    ElMessage.warning('未关联页面节点不能删除')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定删除页面「${rightClickedGroupNode.value.name}」？该页面下的元素将变为未关联。`,
      '删除页面',
      { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }
    )
    const originalId = rightClickedGroupNode.value._originalId || rightClickedGroupNode.value.id
    await deleteElementGroup(originalId)
    ElMessage.success('页面已删除')
    await Promise.all([loadPages(), loadElementTree()])
    treeKey.value += 1
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

// 元素列表行点击 - 双击编辑
const onElementRowClick = async (row) => {
  // 双击打开编辑弹窗
}

const getElementRowClass = ({ row }) => {
  return ''
}

// 获取定位策略名称
const getStrategyName = (strategyId) => {
  if (!strategyId) return '-'
  const strategy = locatorStrategies.value.find(s => s.id === strategyId)
  return strategy ? strategy.name : String(strategyId)
}

// 新增元素 - 打开弹窗
const onCreateElement = () => {
  elementDialogTitle.value = '新增元素'
  selectedElement.value = {
    name: '',
    element_type: 'BUTTON',
    page: '',
    component_name: '',
    locator_strategy_id: null,
    locator_value: '',
    wait_timeout: 5,
    force_action: false,
    description: ''
  }
  formKey.value += 1
  showElementDialog.value = true
}

// 编辑元素 - 打开弹窗
const onEditElement = async (row) => {
  elementDialogTitle.value = '编辑元素'
  try {
    const response = await getElementDetail(row.id)
    selectedElement.value = response.data
    formKey.value += 1
    showElementDialog.value = true
  } catch (error) {
    ElMessage.error('获取元素详情失败')
  }
}

// 弹窗关闭后清理
const onElementDialogClosed = () => {
  selectedElement.value = null
}

// 从列表复制元素
const copyElementFromList = async (row) => {
  elementDialogTitle.value = '复制元素'
  try {
    const response = await getElementDetail(row.id)
    const src = response.data
    selectedElement.value = {
      name: src.name + ' - 副本',
      element_type: src.element_type,
      page: src.page,
      component_name: src.component_name,
      locator_strategy_id: src.locator_strategy_id,
      locator_value: src.locator_value,
      wait_timeout: src.wait_timeout,
      force_action: src.force_action,
      description: src.description
    }
    formKey.value += 1
    showElementDialog.value = true
  } catch (error) {
    ElMessage.error('获取元素详情失败')
  }
}

// 从列表删除元素
const deleteElementFromList = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除元素「${row.name}」？`, '删除元素', { type: 'warning' })
    await deleteElement(row.id)
    ElMessage.success('元素已删除')
    await loadElementTree()
    treeKey.value += 1
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}
// 仅包含页面节点的树（过滤掉元素节点），用于所属页面树形下拉
const selectedElement = ref(null)
const treeKey = ref(0) // 用于强制重新渲染树组件
const formKey = ref(0) // 用于强制重新渲染表单组件

// 表单引用
const pageFormRef = ref(null)
const editPageFormRef = ref(null)
const elementFormRef = ref(null)

// 对话框控制
const showCreatePageDialog = ref(false)
const showEditPageDialog = ref(false)
const showElementDialog = ref(false)
const elementDialogTitle = ref('新增元素')

// AI智能提取相关
const showAiExtractDialog = ref(false)
const showAiResultDialog = ref(false)
const showCandidateDialog = ref(false)  // 候选按钮选择对话框
const aiExtractLoading = ref(false)
const aiExtractProgress = ref('')
const aiExtractResults = ref([])
const selectedAiResults = ref([])
const batchImportLoading = ref(false)
const loginConfigs = ref([])
const aiResultTableRef = ref(null)
const aiResultInfo = reactive({ url: '', page_title: '' })
const aiExtractForm = reactive({
  url: '',
  login_config_id: null,
  page_name: ''
})

// 候选弹窗触发按钮相关
const candidateButtons = ref([])       // 候选按钮列表
const selectedCandidates = ref([])     // 用户勾选的按钮
const candidateLoading = ref(false)    // 弹窗提取加载状态

// 手动交互模式相关
const showManualDialog = ref(false)        // 控制手动模式对话框显示
const manualSessionId = ref('')            // 手动模式session ID
const manualCaptures = ref([])             // 手动模式的多次提取结果
const manualCaptureIndex = ref(0)
const manualLoading = ref(false)

// 交互式选取模式相关
const showPickDialog = ref(false)          // 控制选取模式对话框显示
const pickSessionId = ref('')              // 选取模式session ID
const pickElements = ref([])               // 已选取的元素列表
const pickLoading = ref(false)             // 加载状态
let pickPollTimer = null                   // 轮询定时器

// 表单数据
const pageForm = reactive({
  name: '',
  description: '',
  parent_page: null
})

const editPageForm = reactive({
  id: null,
  name: '',
  description: '',
  parent_page: null
})

// 树形组件配置
const treeProps = {
  children: 'children',
  label: 'name'
}

// 表单验证规则
const pageRules = computed(() => ({
  name: [
    { required: true, message: t('uiAutomation.element.rules.pageNameRequired'), trigger: 'blur' }
  ]
}))

// 元素表单验证规则
const elementRules = computed(() => ({
  name: [
    { required: true, message: t('uiAutomation.element.rules.nameRequired'), trigger: 'blur' },
    { min: 1, max: 200, message: t('uiAutomation.element.rules.nameLength'), trigger: 'blur' }
  ],
  locator_strategy_id: [
    { required: true, message: t('uiAutomation.element.rules.strategyRequired'), trigger: 'change' }
  ],
  locator_value: [
    { required: true, message: t('uiAutomation.element.rules.locatorRequired'), trigger: 'blur' },
    { min: 1, max: 500, message: t('uiAutomation.element.rules.locatorLength'), trigger: 'blur' }
  ]
}))

// 获取元素类型标签
const getElementTypeLabel = (type) => {
  const typeKey = type?.toLowerCase()
  const typeMap = {
    'button': t('uiAutomation.element.elementTypes.button'),
    'input': t('uiAutomation.element.elementTypes.input'),
    'link': t('uiAutomation.element.elementTypes.link'),
    'dropdown': t('uiAutomation.element.elementTypes.dropdown'),
    'checkbox': t('uiAutomation.element.elementTypes.checkbox'),
    'radio': t('uiAutomation.element.elementTypes.radio'),
    'text': t('uiAutomation.element.elementTypes.text'),
    'image': t('uiAutomation.element.elementTypes.image'),
    'table': t('uiAutomation.element.elementTypes.table'),
    'form': t('uiAutomation.element.elementTypes.form'),
    'modal': t('uiAutomation.element.elementTypes.modal')
  }
  return typeMap[typeKey] || type
}

// 获取所有页面
const getAllPages = () => {
  const allPages = []

  const traverse = (nodes) => {
    nodes.forEach(node => {
      if (node.type === 'page') {
        allPages.push({
          id: node._originalId || node.id,
          name: node.name
        })
      }
      if (node.children) {
        traverse(node.children)
      }
    })
  }

  traverse(treeData.value)
  return allPages
}

// 获取所有页面（除了指定ID的页面）
const getAllPagesExceptCurrent = (currentId) => {
  const allPages = []

  const traverse = (nodes) => {
    nodes.forEach(node => {
      const nodeOriginalId = node._originalId || node.id
      if (node.type === 'page' && nodeOriginalId !== currentId) {
        allPages.push({
          id: nodeOriginalId,
          name: node.name
        })
      }
      if (node.children) {
        traverse(node.children)
      }
    })
  }

  traverse(treeData.value)
  return allPages
}

// 状态
const saving = ref(false)
const validating = ref(false)
const generating = ref(false)
const suggestions = ref([])


// 将关键变量暴露到window对象，方便在控制台调试
const exposeToWindow = () => {
  if (typeof window !== 'undefined') {
    window.ELEMENTS_DEBUG = {
      treeData,
      projects,
      selectedElement,
      loadElementTree,
      pageTreeRef,
      pageExpandedKeys,
      pages,
      $vm: { // 当前组件实例
        treeData: treeData.value,
        projects: projects.value,
        pages: pages.value,
        pageExpandedKeys: pageExpandedKeys.value
      }
    }
    console.log('=== Vue组件调试信息已暴露 ===')
    console.log('Window可用调试变量已设置')
    console.log('控制台可直接访问:')
    console.log('  window.ELEMENTS_DEBUG.treeData')
    console.log('  window.ELEMENTS_DEBUG.projects')
    console.log('  window.ELEMENTS_DEBUG.selectedElement')
    console.log('==============================')
  }
}

// 组件挂载
// ========== AI智能提取相关方法 ==========

const loadLoginConfigs = async () => {
  if (!selectedProject.value) {
    loginConfigs.value = []
    return
  }
  try {
    const response = await getLoginConfigs({ project: selectedProject.value, page_size: 100 })
    loginConfigs.value = response.data.results || response.data
  } catch (error) {
    console.error('获取登录配置失败:', error)
    loginConfigs.value = []
  }
}

const handleAiExtract = async () => {
  if (!aiExtractForm.url) {
    ElMessage.warning('请输入目标页面URL')
    return
  }
  if (!selectedProject.value) {
    ElMessage.warning('请先选择项目')
    return
  }

  aiExtractLoading.value = true
  aiExtractProgress.value = '正在打开页面...'

  try {
    const data = {
      project_id: selectedProject.value,
      url: aiExtractForm.url,
      login_config_id: aiExtractForm.login_config_id || undefined,
      page_name: aiExtractForm.page_name || undefined
    }

    aiExtractProgress.value = '正在分析DOM结构...'

    const response = await aiExtractElements(data)

    aiExtractProgress.value = '正在AI智能识别...'

    const result = response.data
    aiExtractResults.value = (result.elements || []).map((elem, index) => ({
      ...elem,
      _id: index
    }))
    aiResultInfo.url = result.url || aiExtractForm.url
    aiResultInfo.page_title = result.page_title || ''
    if (result.final_url) {
      aiResultInfo.final_url = result.final_url
    }

    // 检测重定向警告
    if (result.redirect_warning) {
      ElMessage.warning({ message: result.redirect_warning, duration: 5000 })
    }

    if (aiExtractResults.value.length === 0) {
      ElMessage.warning('未提取到可交互元素')
      return
    }

    // 展示主页面元素结果
    showAiExtractDialog.value = false
    showAiResultDialog.value = true

    // 构建候选弹窗按钮列表：
    // 1. 后端关键词匹配的候选按钮
    // 2. 主页面提取结果中的按钮类元素（BUTTON/LINK）
    // 按 css_selector 去重后合并
    const backendButtons = (result.candidate_buttons || []).map(btn => ({
      ...btn,
      source: btn.source || '页面级按钮',
      reason: btn.reason || '关键词匹配'
    }))

    // 从主页面提取结果中提取按钮类元素
    // 排除导航菜单：通过定位器中的menu/nav/sidebar等特征识别
    const navPatterns = /menu|nav|sidebar|breadcrumb|sider|aside/i
    const mainPageButtons = aiExtractResults.value
      .filter(elem => elem.element_type === 'BUTTON')
      .filter(elem => {
        // 检查定位器是否包含导航菜单特征
        const locatorStr = `${elem.auto_css || ''} ${elem.auto_xpath || ''} ${elem.locator_value || ''}`
        if (navPatterns.test(locatorStr)) return false
        return true
      })
      .map(elem => {
        let css_selector = elem.auto_css || ''
        let xpath = elem.auto_xpath || ''
        // 没有 auto_css 时从 locator_strategy/value 构建
        if (!css_selector && elem.locator_value) {
          if (elem.locator_strategy === 'CSS' || elem.locator_strategy === 'css') css_selector = elem.locator_value
          else if (elem.locator_strategy === 'ID' || elem.locator_strategy === 'id') css_selector = `#${elem.locator_value}`
          else if (elem.locator_strategy === 'name') css_selector = `[name="${elem.locator_value}"]`
          else if (elem.locator_strategy === 'class') css_selector = `.${elem.locator_value.split(' ')[0]}`
        }
        if (!xpath && elem.locator_value) {
          if (elem.locator_strategy === 'XPath' || elem.locator_strategy === 'xpath') xpath = elem.locator_value
        }
        return {
          text: elem.name || elem.text || '未命名按钮',
          css_selector,
          xpath,
          source: '主页面按钮',
          reason: '主页面提取的按钮元素'
        }
      })

    // 去重合并：按按钮名称(text)去重，先放后端关键词匹配的，再放主页面按钮
    const seenNames = new Set()
    const merged = []

    for (const btn of backendButtons) {
      const key = (btn.text || '').trim()
      if (key && !seenNames.has(key)) {
        seenNames.add(key)
        merged.push(btn)
      } else if (!key) {
        merged.push(btn)
      }
    }
    for (const btn of mainPageButtons) {
      const key = (btn.text || '').trim()
      if (key && !seenNames.has(key)) {
        seenNames.add(key)
        merged.push(btn)
      } else if (!key) {
        merged.push(btn)
      }
    }

    // 设置 _id 和默认选中状态
    candidateButtons.value = merged.map((btn, idx) => ({
      ...btn,
      _id: idx,
      selected: btn.source !== '表格行操作' && btn.source !== '主页面按钮'  // 页面级按钮默认选中，行操作和主页面按钮默认不选
    }))
    selectedCandidates.value = candidateButtons.value.filter(b => b.selected)

    const keywordCount = backendButtons.length
    const mainPageCount = mainPageButtons.length
    const totalCount = candidateButtons.value.length
    if (keywordCount > 0) {
      ElMessage.success(`主页面提取 ${aiExtractResults.value.length} 个元素，${totalCount} 个候选按钮（关键词匹配 ${keywordCount} 个 + 主页面按钮 ${mainPageCount} 个）`)
    } else {
      ElMessage.success(`主页面提取 ${aiExtractResults.value.length} 个元素，${totalCount} 个候选按钮可提取弹窗`)
    }

    // 默认全选所有提取的元素
    await nextTick()
    if (aiResultTableRef.value) {
      aiResultTableRef.value.toggleAllSelection()
    }
  } catch (error) {
    const errMsg = error.response?.data?.error || error.message || '提取失败'
    ElMessage.error(errMsg)
    console.error('AI提取失败:', error)
  } finally {
    aiExtractLoading.value = false
    aiExtractProgress.value = ''
  }
}

// 自动提取弹窗元素
const handleExtractDialogs = async () => {
  if (selectedCandidates.value.length === 0) {
    ElMessage.warning('请至少选择一个候选按钮')
    return
  }

  candidateLoading.value = true

  try {
    const data = {
      project_id: selectedProject.value,
      url: aiExtractForm.url,
      login_config_id: aiExtractForm.login_config_id || undefined,
      page_name: aiExtractForm.page_name || undefined,
      buttons: selectedCandidates.value.map(btn => ({
        text: btn.text,
        css_selector: btn.css_selector,
        xpath: btn.xpath,
        source: btn.source
      }))
    }

    const response = await aiExtractDialogs(data)
    const result = response.data

    // 将弹窗元素合并到结果中
    const dialogElements = (result.elements || []).map((elem, index) => ({
      ...elem,
      _id: aiExtractResults.value.length + index
    }))

    // 追加到现有结果
    aiExtractResults.value = [...aiExtractResults.value, ...dialogElements]

    // 关闭候选对话框，打开结果对话框
    showCandidateDialog.value = false
    showAiResultDialog.value = true

    // 显示失败信息
    const failures = result.failures || []
    if (failures.length > 0) {
      const failMsg = failures.map(f => `"${f.button}": ${f.reason}`).join('；')
      ElMessage.warning(`弹窗提取完成，新增 ${dialogElements.length} 个弹窗元素。以下按钮提取失败：${failMsg}`)
    } else {
      ElMessage.success(`弹窗提取完成，新增 ${dialogElements.length} 个弹窗元素`)
    }

    await nextTick()
    if (aiResultTableRef.value) {
      aiResultTableRef.value.toggleAllSelection()
    }
  } catch (error) {
    const errMsg = error.response?.data?.error || error.message || '弹窗提取失败'
    ElMessage.error(errMsg)
    console.error('弹窗提取失败:', error)
    // 出错时回到结果对话框
    showCandidateDialog.value = false
    showAiResultDialog.value = true
  } finally {
    candidateLoading.value = false
  }
}

// 候选按钮选择变化
const handleCandidateSelectionChange = (val) => {
  selectedCandidates.value = val
}

// 启动手动交互模式
const handleManualModeStart = async () => {
  if (!aiExtractForm.url) {
    ElMessage.warning('请输入目标页面URL')
    return
  }

  manualLoading.value = true
  try {
    const data = {
      project_id: selectedProject.value,
      url: aiExtractForm.url,
      login_config_id: aiExtractForm.login_config_id || undefined
    }

    const response = await aiExtractManualStart(data)
    const result = response.data

    manualSessionId.value = result.session_id
    manualCaptures.value = []
    manualCaptureIndex.value = 0
    showManualDialog.value = true

    ElMessage.success('浏览器已打开，请手动操作后提取元素')
    showAiExtractDialog.value = false
  } catch (error) {
    const errMsg = error.response?.data?.error || error.message || '启动浏览器失败'
    ElMessage.error(errMsg)
  } finally {
    manualLoading.value = false
  }
}

// 手动模式 - 提取当前页面
const handleManualCapture = async () => {
  if (!manualSessionId.value) {
    ElMessage.warning('请先启动手动模式')
    return
  }

  manualLoading.value = true
  try {
    const data = {
      session_id: manualSessionId.value,
      page_name: aiExtractForm.page_name || ''
    }

    const response = await aiExtractManualCapture(data)
    const result = response.data

    const capturedElements = (result.elements || []).map((elem, index) => ({
      ...elem,
      _id: manualCaptures.value.reduce((acc, c) => acc + c.elements.length, 0) + index
    }))

    manualCaptures.value.push({
      index: result.capture_index,
      page_name: result.page_name || `第${result.capture_index}次提取`,
      element_count: capturedElements.length,
      elements: capturedElements
    })
    manualCaptureIndex.value = result.capture_index

    ElMessage.success(`第${result.capture_index}次提取完成，获取 ${capturedElements.length} 个元素`)
  } catch (error) {
    const errMsg = error.response?.data?.error || error.message || '提取失败'
    ElMessage.error(errMsg)
  } finally {
    manualLoading.value = false
  }
}

// 手动模式 - 完成提取
const handleManualFinish = async () => {
  if (!manualSessionId.value) return

  manualLoading.value = true
  try {
    const response = await aiExtractManualFinish({ session_id: manualSessionId.value })
    const result = response.data

    // 将所有提取结果合并到主结果中
    const allElements = (result.elements || []).map((elem, index) => ({
      ...elem,
      _id: index
    }))

    aiExtractResults.value = allElements
    aiResultInfo.url = aiExtractForm.url
    manualSessionId.value = ''
    showManualDialog.value = false

    // 打开结果对话框
    showAiResultDialog.value = true
    await nextTick()
    if (aiResultTableRef.value) {
      aiResultTableRef.value.toggleAllSelection()
    }

    ElMessage.success(`手动提取完成，共 ${allElements.length} 个元素（${result.captures?.length || 0} 次提取）`)
  } catch (error) {
    const errMsg = error.response?.data?.error || error.message || '完成提取失败'
    ElMessage.error(errMsg)
  } finally {
    manualLoading.value = false
  }
}

// ==================== 交互式选取模式 ====================

// 启动交互式选取
const handlePickStart = async () => {
  if (!aiExtractForm.url) {
    ElMessage.warning('请输入目标页面URL')
    return
  }

  pickLoading.value = true
  try {
    const data = {
      project_id: selectedProject.value,
      url: aiExtractForm.url,
      login_config_id: aiExtractForm.login_config_id || undefined
    }

    const response = await aiPickStart(data)
    const result = response.data

    pickSessionId.value = result.session_id
    pickElements.value = []
    showPickDialog.value = true
    showAiExtractDialog.value = false

    ElMessage.success('浏览器已打开，请在页面中点击要提取的元素')

    // 开始轮询获取已选取的元素
    startPickPolling()
  } catch (error) {
    const errMsg = error.response?.data?.error || error.message || '启动失败'
    ElMessage.error(errMsg)
  } finally {
    pickLoading.value = false
  }
}

// 轮询获取已选取元素
const startPickPolling = () => {
  if (pickPollTimer) clearInterval(pickPollTimer)
  pickPollTimer = setInterval(async () => {
    if (!pickSessionId.value) {
      clearInterval(pickPollTimer)
      return
    }
    try {
      const response = await aiPickStatus({ session_id: pickSessionId.value })
      const result = response.data
      if (result.elements) {
        pickElements.value = result.elements.map((elem, index) => ({
          ...elem,
          _id: index
        }))
      }
    } catch (error) {
      // 静默处理轮询错误
    }
  }, 2000)
}

// 完成交互式选取
const handlePickFinish = async () => {
  if (!pickSessionId.value) return

  pickLoading.value = true
  try {
    // 停止轮询
    if (pickPollTimer) {
      clearInterval(pickPollTimer)
      pickPollTimer = null
    }

    const response = await aiPickFinish({ session_id: pickSessionId.value })
    const result = response.data

    // 将结果填充到预览表格
    const allElements = (result.elements || []).map((elem, index) => ({
      ...elem,
      _id: index
    }))

    aiExtractResults.value = allElements
    aiResultInfo.url = aiExtractForm.url
    pickSessionId.value = ''
    showPickDialog.value = false

    // 打开结果预览对话框
    showAiResultDialog.value = true
    await nextTick()
    if (aiResultTableRef.value) {
      aiResultTableRef.value.toggleAllSelection()
    }

    ElMessage.success(`选取完成，共 ${allElements.length} 个元素`)
  } catch (error) {
    const errMsg = error.response?.data?.error || error.message || '完成选取失败'
    ElMessage.error(errMsg)
  } finally {
    pickLoading.value = false
  }
}

// 交互式选取 — 删除指定元素（同步后端）
const removePickElement = async (index) => {
  try {
    await aiPickRemove({ session_id: pickSessionId.value, index })
    // 后端已删除，下一次轮询会自动同步，但先本地也删掉让UI即时响应
    pickElements.value.splice(index, 1)
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const handleAiResultSelectionChange = (selection) => {
  selectedAiResults.value = selection
}

const handleBatchImport = async () => {
  if (selectedAiResults.value.length === 0) {
    ElMessage.warning('请至少选择一个元素')
    return
  }

  batchImportLoading.value = true
  let successCount = 0
  let failCount = 0

  try {
    // 如果用户填了页面名称，先查找或创建对应的页面分组
    let targetGroupId = null
    const pageName = aiExtractForm.page_name?.trim()
    if (pageName) {
      try {
        // 查找当前项目下是否已有同名页面
        const groupsResponse = await getElementGroups({ project: selectedProject.value })
        const existingGroups = groupsResponse.data?.results || groupsResponse.data || []
        const match = existingGroups.find(g => g.name === pageName)
        if (match) {
          targetGroupId = match.id
          console.log(`[批量导入] 找到已有页面: ${pageName}, id=${targetGroupId}`)
        } else {
          // 创建新页面
          const createResponse = await createElementGroup({
            name: pageName,
            project: selectedProject.value
          })
          targetGroupId = createResponse.data?.id
          console.log(`[批量导入] 创建新页面: ${pageName}, id=${targetGroupId}`)
        }
      } catch (err) {
        console.error('[批量导入] 查找/创建页面失败:', err)
        ElMessage.warning(`页面"${pageName}"查找/创建失败，元素将导入到未关联页面`)
      }
    }

    for (const elem of selectedAiResults.value) {
      try {
        const strategyObj = locatorStrategies.value.find(s => s.name === elem.locator_strategy)
        const apiData = {
          name: elem.name,
          page: elem.page || pageName || '',
          description: elem.description || '',
          locator_value: elem.locator_value,
          project_id: selectedProject.value,
          locator_strategy_id: strategyObj ? strategyObj.id : locatorStrategies.value[0]?.id,
          element_type: elem.element_type,
          is_unique: false,
          wait_timeout: 5
        }
        // 设置页面分组ID
        if (targetGroupId) {
          apiData.group_id = targetGroupId
        }
        console.log(`[批量导入] 创建元素: name=${elem.name}, group_id=${apiData.group_id}, targetGroupId=${targetGroupId}, apiData=`, apiData)
        if (elem.backup_locators && elem.backup_locators.length > 0) {
          apiData.backup_locators = elem.backup_locators
        }

        await createElement(apiData)
        successCount++
      } catch (err) {
        failCount++
        console.error(`导入元素"${elem.name}"失败:`, err)
      }
    }

    if (successCount > 0) {
      ElMessage.success(`成功导入 ${successCount} 个元素${failCount > 0 ? `，${failCount} 个失败` : ''}${targetGroupId ? ` 到页面"${pageName}"` : ''}`)
      showAiResultDialog.value = false
      // 刷新元素树
      await onProjectChange()
    } else {
      ElMessage.error('所有元素导入失败')
    }
  } finally {
    batchImportLoading.value = false
  }
}

onMounted(async () => {
  console.log('=== 组件挂载开始 ===')

  await loadProjects()
  await loadLocatorStrategies()

  console.log('项目数量:', projects.value.length)
  console.log('定位策略:', locatorStrategies.value.length)

  if (projects.value.length > 0) {
    console.log('设置初始项目为:', projects.value[0].id)
    selectedProject.value = projects.value[0].id
    await onProjectChange()
    console.log('onProjectChange完成')
  }

  // 暴露调试信息
  exposeToWindow()

  console.log('=== 组件挂载完成 ===')
})

// 加载项目列表
const loadProjects = async () => {
  try {
    const response = await getUiProjects()
    projects.value = response.data?.results || response.data || []
  } catch (error) {
    console.error('获取项目列表失败:', error)
  }
}

// 提供控制台调试帮助函数
const debugTree = () => {
  if (typeof window !== 'undefined') {
    console.log('=== 树数据调试 ===')
    console.log('treeData:', treeData.value)
    console.log('页面对象:',
      treeData.value.map(p => ({
        id: p.id,
        name: p.name,
        type: p.type,
        children: p.children?.length || 0,
        elementChildren: p.children?.filter(c => c.type === 'element').map(e => e.name) || []
      }))
    )

    // 找出所有元素
    const allElements = []
    const findElements = (nodes, parent) => {
      nodes.forEach(node => {
        if (node.type === 'element') {
          allElements.push({
            name: node.name,
            id: node.id,
            parent: parent
          })
        } else if (node.type === 'page' && node.children) {
          findElements(node.children, node.name)
        }
      })
    }
    findElements(treeData.value, null)
    console.log('所有元素:', allElements)

    // 暴露到window
    window.debugTreeData = debugTree
    console.log('调试函数已挂载到 window.debugTreeData()')
    console.log('===============================')
  }
}

// 加载定位策略
const loadLocatorStrategies = async () => {
  try {
    const response = await getLocatorStrategies()
    locatorStrategies.value = response.data?.results || response.data || []
  } catch (error) {
    console.error('获取定位策略失败:', error)
  }
}

// 加载页面（分组）
const loadPages = async () => {
  if (!selectedProject.value) return

  try {
    const response = await getElementGroups({ project: selectedProject.value })
    pages.value = response.data?.results || response.data || []
  } catch (error) {
    console.error('获取页面失败:', error)
  }
}

// 加载页面树结构
const loadPageTree = async () => {
  if (!selectedProject.value) return

  try {
    const response = await getElementGroupTree({ project: selectedProject.value })
    // 构建完整的树形结构
    const buildTree = (groups) => {
      return groups.map(group => ({
        ...group,
        type: 'page',
        children: group.children ? buildTree(group.children) : []
      }))
    }

    treeData.value = buildTree(response.data || [])
  } catch (error) {
    console.error('获取页面树失败:', error)
    treeData.value = []
  }
}

// 加载元素树
const loadElementTree = async () => {
  if (!selectedProject.value) {
    treeData.value = []
    return
  }

  try {
    // 并行加载页面树和元素
    const [pageTreeResponse, elementsResponse] = await Promise.all([
      getElementGroupTree({ project: selectedProject.value }),
      getElementTree({ project: selectedProject.value })
    ])

    // 构建完整的树形结构 — 页面节点id加'page-'前缀，避免与元素id冲突
    const buildTree = (groups) => {
      return groups.map(group => ({
        ...group,
        id: `page-${group.id}`,
        _originalId: group.id,
        type: 'page',
        children: group.children ? buildTree(group.children) : []
      }))
    }

    const pageNodes = buildTree(pageTreeResponse.data || [])

    // 调试信息 - 检查API返回的完整响应结构
    console.log('=== 加载元素树调试 ===')
    console.log('页面树响应:', pageTreeResponse)
    console.log('元素响应:', elementsResponse)

    // 打印原始数据进行分析
    console.log('页面树原始数据:', JSON.parse(JSON.stringify(pageTreeResponse.data || []), null, 2))

    const elements = elementsResponse.data?.results || elementsResponse.data || []
    console.log('提取的元素列表:', elements)

    // 获取所有页面的ID，用于调试
    const pageIds = pageNodes.map(page => page.id)
    console.log('页面ID列表:', pageIds)

    // 将元素添加到对应页面下
    const attachedElementIds = new Set()

    const attachElementsToPages = (pages) => {
      pages.forEach(page => {
        // 找到属于当前页面的元素
        // 后端 tree 接口直接返回 group_id（整数），也兼容 list 接口返回的 group.id
        const pageOriginalId = page._originalId
        const pageElements = elements.filter(element => {
          const elemGroupId = element.group_id ?? (element.group && element.group.id) ?? null
          return parseInt(elemGroupId) === pageOriginalId
        })
        console.log(`页面 ${page.name} (ID: ${page.id}, originalId: ${pageOriginalId}) 找到 ${pageElements.length} 个关联元素`, pageElements.map(e => ({id: e.id, name: e.name, group_id: e.group_id})))

        const elementNodes = pageElements.map(element => {
          attachedElementIds.add(element.id)
          return {
            ...element,
            id: `elem-${element.id}`,
            _originalId: element.id,
            type: 'element'
          }
        })

        // 将元素添加到页面的子节点中
        page.children = page.children ? [...page.children, ...elementNodes] : [...elementNodes]
        console.log(`页面 ${page.name} 现在有 ${page.children.filter(c => c.type === 'element').length} 个子元素`)

        // 递归处理子页面
        if (page.children) {
          attachElementsToPages(page.children.filter(child => child.type === 'page'))
        }
      })
    }

    attachElementsToPages(pageNodes)

    // 添加未关联页面的元素到"未关联页面"节点
    // 包括：1. group 为 null 的元素
    //       2. group 指向的页面不存在的元素
    const unassignedElements = elements.filter(element => {
      // 从 group_id 或 group.id 获取分组ID
      const elemGroupId = element.group_id ?? (element.group && element.group.id) ?? null
      if (!elemGroupId) {
        return true
      }
      // 如果有分组ID但没有被添加到任何页面（页面不存在），也算未关联
      return !attachedElementIds.has(element.id)
    })

    console.log('未关联页面的元素:', unassignedElements)

    if (unassignedElements.length > 0) {
      const unassignedPage = {
        id: 'unassigned',
        _originalId: null,
        name: '未关联页面',
        type: 'page',
        children: unassignedElements.map(element => ({
          ...element,
          id: `elem-${element.id}`,
          _originalId: element.id,
          type: 'element'
        }))
      }
      pageNodes.unshift(unassignedPage) // 添加到列表最前面
      console.log(`已添加 ${unassignedElements.length} 个未关联元素到"未关联页面"节点`)
      // 默认展开未关联页面节点
      pageExpandedKeys.value.push('unassigned')
    }

    console.log('最终treeData:', pageNodes)
    treeData.value = pageNodes

    // 更新扁平化元素列表
    allElements.value = elements

    // 将treeData暴露到window，方便在控制台调试
    if (typeof window !== 'undefined') {
      window.vue_treeData = treeData.value
      console.log('treeData已挂载到window.vue_treeData，可在控制台查看')
      console.log('当前treeData结构:', JSON.parse(JSON.stringify(treeData.value)).map(p => ({
        name: p.name,
        id: p.id,
        children: p.children?.filter(c => c.type === 'element').length || 0
      })))
    }
  } catch (error) {
    console.error('获取元素树失败:', error)
    treeData.value = []
  }
}

// 项目切换
const onProjectChange = async () => {
  selectedElement.value = null
  suggestions.value = []

  console.log('=== 项目切换调试 ===')
  console.log('当前项目ID:', selectedProject.value)

  await Promise.all([
    loadPages(),
    loadElementTree(),
    loadLoginConfigs()
  ])

  console.log('项目切换完成，检查treeData:', treeData.value)
  console.log('treeData长度:', treeData.value.length)
  if (treeData.value.length > 0) {
    console.log('第一页信息:', {
      id: treeData.value[0].id,
      name: treeData.value[0].name,
      type: treeData.value[0].type,
      children: treeData.value[0].children?.length || 0
    })
  }

  // 项目切换时强制刷新树
  treeKey.value += 1
}

// 验证单个字段（用于失焦验证）
const validateField = async (field) => {
  if (!elementFormRef.value) return
  try {
    await elementFormRef.value.validateField(field)
  } catch (error) {
    // 验证失败，不需要做任何处理，错误会自动显示
  }
}

// 验证元素表单字段
const validateHeaderField = async (field) => {
  if (!elementFormRef.value) return
  try {
    await elementFormRef.value.validateField(field)
  } catch (error) {
    // 验证失败，错误会自动显示
  }
}

// 验证整个元素表单
const validateElementForm = async () => {
  if (!elementFormRef.value) return true
  try {
    await elementFormRef.value.validate()
    return true
  } catch {
    return false
  }
}

// 创建页面
const createPage = async () => {
  const validate = await pageFormRef.value.validate()
  if (!validate) return

  try {
    // 构建创建页面的参数，正确处理父页面参数
    const pageData = {
      name: pageForm.name,
      description: pageForm.description,
      project: selectedProject.value
    }

    // 只有当父页面ID存在且不为空时才添加parent_group字段
    if (pageForm.parent_page) {
      pageData.parent_group = pageForm.parent_page
    }

    await createElementGroup(pageData)

    ElMessage.success(t('uiAutomation.element.messages.pageCreateSuccess'))
    showCreatePageDialog.value = false

    // 重置表单
    Object.assign(pageForm, {
      name: '',
      description: '',
      parent_page: null
    })

    // 重新加载页面和树
    await Promise.all([
      loadPages(),
      loadElementTree()
    ])

    // 强制刷新树组件
    treeKey.value += 1
  } catch (error) {
    console.error('创建页面失败:', error)
    ElMessage.error(t('uiAutomation.element.messages.pageCreateFailed'))
  }
}

// 保存元素
const saveElement = async () => {
  if (!selectedElement.value) return

  // 验证表单
  const isValid = await validateElementForm()
  if (!isValid) {
    return
  }

  try {
    saving.value = true

    // 查找页面ID的辅助函数
    const findPageIdByName = (nodes, pageName) => {
      for (const node of nodes) {
        if (node.type === 'page' && node.name === pageName) {
          return node._originalId || node.id
        }
        if (node.children) {
          const foundId = findPageIdByName(node.children, pageName)
          if (foundId) return foundId
        }
      }
      return null
    }

    if (selectedElement.value.id) {
      // 更新元素
      const elementUpdateData = {
        name: selectedElement.value.name,
        element_type: selectedElement.value.element_type,
        page: selectedElement.value.page,
        component_name: selectedElement.value.component_name,
        description: selectedElement.value.description,
        locator_strategy_id: selectedElement.value.locator_strategy_id,
        locator_value: selectedElement.value.locator_value,
        wait_timeout: selectedElement.value.wait_timeout,
        force_action: selectedElement.value.force_action,
        project_id: selectedProject.value
      }

      if (selectedElement.value.page) {
        const pageId = findPageIdByName(treeData.value, selectedElement.value.page)
        if (pageId) elementUpdateData.group_id = pageId
      }

      await updateElement(selectedElement.value.id, elementUpdateData)
      ElMessage.success(t('uiAutomation.element.messages.saveSuccess'))
    } else {
      // 创建元素
      const elementData = {
        ...selectedElement.value,
        project_id: selectedProject.value
      }

      if (selectedElement.value.page) {
        const pageId = findPageIdByName(treeData.value, selectedElement.value.page)
        if (pageId) elementData.group_id = pageId
      }

      await createElement(elementData)
      ElMessage.success(t('uiAutomation.element.messages.createSuccess'))
    }

    // 关闭弹窗
    showElementDialog.value = false

    // 重新加载树
    await loadElementTree()
    treeKey.value += 1

    // 展开元素所在页面节点
    nextTick(() => {
      if (selectedElement.value && selectedElement.value.group_id) {
        const pageKey = `page-${selectedElement.value.group_id}`
        if (!pageExpandedKeys.value.includes(pageKey)) {
          pageExpandedKeys.value.push(pageKey)
        }
      }
    })
  } catch (error) {
    ElMessage.error(t('uiAutomation.element.messages.saveFailed') + ': ' + (error.response?.data?.message || error.message || t('uiAutomation.messages.error.unknown')))
  } finally {
    saving.value = false
  }
}

// 验证元素
const validateElement = async () => {
  if (!selectedElement.value) return

  try {
    validating.value = true
    const response = await validateElementLocator(selectedElement.value.id)
    const result = response.data

    if (result.is_valid) {
      ElMessage.success(t('uiAutomation.element.messages.validateSuccess'))
    } else {
      ElMessage.error(`${t('uiAutomation.element.messages.validateFailed')}: ${result.validation_message}`)
    }
  } catch (error) {
    ElMessage.error(t('uiAutomation.element.messages.validateFailed'))
    console.error('验证元素失败:', error)
  } finally {
    validating.value = false
  }
}

// 生成建议
const generateSuggestions = async () => {
  if (!selectedElement.value) return

  try {
    generating.value = true
    const response = await generateElementSuggestions(selectedElement.value.id)
    suggestions.value = response.data.suggestions
  } catch (error) {
    console.error('生成建议失败:', error)
  } finally {
    generating.value = false
  }
}

// 清空未关联页面下的所有元素
const deleteUnassignedElements = async () => {
  showGroupContextMenu.value = false

  // 从 treeData 中找未关联页面的元素
  const unassignedPage = treeData.value.find(n => n.id === 'unassigned')
  if (!unassignedPage) {
    ElMessage.info('当前没有未关联的元素')
    return
  }

  const children = unassignedPage.children?.filter(c => c.type === 'element') || []
  if (children.length === 0) {
    ElMessage.info('当前没有未关联的元素')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要清空所有未关联元素吗？共 ${children.length} 个元素将被删除，此操作不可恢复。`,
      '清空未关联元素',
      {
        type: 'warning',
        confirmButtonText: t('uiAutomation.common.confirm'),
        cancelButtonText: t('uiAutomation.common.cancel')
      }
    )

    // 逐个删除所有子元素（用原始ID调API）
    let successCount = 0
    let failCount = 0
    for (const child of children) {
      try {
        await deleteElement(child._originalId || child.id)
        successCount++
      } catch (err) {
        console.error(`删除元素 ${child._originalId || child.id} 失败:`, err)
        failCount++
      }
    }

    if (failCount === 0) {
      ElMessage.success(`已成功清空 ${successCount} 个未关联元素`)
    } else {
      ElMessage.warning(`已删除 ${successCount} 个元素，${failCount} 个删除失败`)
    }

    // 如果当前选中的元素在删除列表中，清空选中
    if (selectedElement.value) {
      const deletedIds = children.map(c => c._originalId || c.id)
      if (deletedIds.includes(selectedElement.value.id)) {
        selectedElement.value = null
      }
    }

    // 重新加载数据
    await Promise.all([
      loadPages(),
      loadElementTree()
    ])
    treeKey.value += 1
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空未关联元素失败:', error)
      ElMessage.error('清空未关联元素失败')
    }
  }
}

// 更新页面
const updatePage = async () => {
  console.log('Update page function called')
  console.log('Edit page form ref:', editPageFormRef.value)

  if (!editPageFormRef.value) {
    console.log('No edit page form ref')
    return
  }

  const validate = await editPageFormRef.value.validate()
  console.log('Validation result:', validate)
  if (!validate) {
    console.log('Validation failed')
    return
  }

  console.log('Updating page with data:', editPageForm)

  try {
    // 构建更新页面的参数，正确处理父页面参数
    const pageData = {
      name: editPageForm.name,
      description: editPageForm.description,
      project: selectedProject.value
    }

    // 始终包含parent_group字段，null表示取消父页面关联
    // 注意：el-select clearable清除时值可能变为undefined或''，需归一化为null
    pageData.parent_group = editPageForm.parent_page || null

    await updateElementGroup(editPageForm.id, pageData)

    ElMessage.success(t('uiAutomation.element.messages.pageUpdateSuccess'))
    showEditPageDialog.value = false

    // 重新加载页面和树
    await Promise.all([
      loadPages(),
      loadElementTree()
    ])

    // 强制刷新树组件
    treeKey.value += 1
  } catch (error) {
    console.error('更新页面失败:', error)
    ElMessage.error(t('uiAutomation.element.messages.pageUpdateFailed'))
  }
}
</script>

<style scoped>
/* 页面容器 */
.page-container {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}

/* 顶部标题栏 */
.page-titlebar {
  height: var(--title-h, 64px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6, 24px);
  flex-shrink: 0;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--gray-900, #0f172a);
  margin: 0;
}

.titlebar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3, 12px);
}

.titlebar-select {
  width: 200px;
}

/* 工作区：CSS Grid 两列两行，filter-bar 自然对齐右侧列 */
.workspace {
  flex: 1;
  display: grid;
  grid-template-columns: var(--group-w, 160px) 1fr;
  grid-template-rows: auto 1fr;
  gap: var(--space-4, 16px);
  padding: 0 var(--space-6, 24px) var(--space-6, 24px);
  overflow: hidden;
}

/* 分组面板跨两行 */
.group-panel {
  grid-row: 1 / 3;
  grid-column: 1;
}

/* 搜索区域占右侧第1行 */
.filter-bar {
  grid-row: 1;
  grid-column: 2;
  margin-bottom: 0; /* gap 替代 margin */
}

/* 元素列表面板占右侧第2行 */
.list-panel {
  grid-row: 2;
  grid-column: 2;
}

/* 分组面板宽度由 grid 列定义 */

.group-panel .panel__body {
  padding: var(--space-2, 8px);
}

.panel__action {
  --el-button-text-color: var(--brand-600, #3570e6);
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
  color: var(--gray-500, #64748b);
  background: var(--gray-100, #f1f5f9);
  border-radius: 10px;
  padding: 1px 7px;
  min-width: 18px;
  text-align: center;
  flex-shrink: 0;
}

.group-panel :deep(.el-tree) {
  background: transparent;
  --el-tree-node-hover-bg-color: transparent;
}

.group-panel :deep(.el-tree-node__content) {
  height: 36px;
  border-radius: var(--radius-md, 8px);
  padding-left: 4px !important;
  margin: 2px 0;
}

.group-panel :deep(.el-tree-node__content:hover) {
  background: var(--gray-100, #f1f5f9);
}

.group-panel :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: var(--brand-50, #edf5ff);
}

.group-panel :deep(.el-tree-node.is-current > .el-tree-node__content .group-node-label) {
  color: var(--brand-700, #2558bf);
  font-weight: 500;
}

.group-panel :deep(.el-tree-node__expand-icon) {
  font-size: 12px;
  color: var(--gray-500, #64748b);
}

.group-panel :deep(.el-tree-node__expand-icon.is-leaf) {
  color: transparent;
}

/* 列表面板宽高由 grid 定义 */

.no-data-tip {
  text-align: center;
  padding: 40px 0;
  color: var(--gray-500, #64748b);
  font-size: 13px;
}

/* 元素类型标签 */
.element-type-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--brand-50, #edf5ff);
  color: var(--brand-600, #3570e6);
}
.element-type-tag.button { background: #ecf5ff; color: #409eff; }
.element-type-tag.input { background: #f0f9eb; color: #67c23a; }
.element-type-tag.link { background: #fdf6ec; color: #e6a23c; }
.element-type-tag.dropdown { background: #fdf6ec; color: #e6a23c; }
.element-type-tag.checkbox { background: #f0f9eb; color: #67c23a; }
.element-type-tag.radio { background: #f0f9eb; color: #67c23a; }
.element-type-tag.text { background: #f4f4f5; color: #909399; }
.element-type-tag.image { background: #fdf6ec; color: #e6a23c; }
.element-type-tag.table { background: #ecf5ff; color: #409eff; }
.element-type-tag.form { background: #ecf5ff; color: #409eff; }
.element-type-tag.modal { background: #fef0f0; color: #f56c6c; }

/* 操作按钮 */
.op-btns {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-wrap: nowrap;
}

.op-btn {
  --el-button-text-color: var(--brand-500, #4f8cff);
  padding: 2px !important;
  border-radius: var(--radius-sm, 6px);
  font-size: 15px;
  transition: opacity 0.15s;
}

.op-btn .el-icon {
  font-size: 15px;
}

.op-btn:hover {
  opacity: 0.8;
  color: var(--brand-600, #3570e6) !important;
}

.op-btn--danger {
  --el-button-text-color: var(--error, #ef4444);
}

.op-btn--danger:hover {
  opacity: 0.8;
  color: var(--error, #ef4444) !important;
}

/* 选中行高亮已移除（不再需要编辑面板联动） */

/* 元素编辑弹窗表单 */
.element-dialog-form :deep(.el-form-item__label) {
  text-align: right;
  font-size: 13px;
  color: var(--gray-700, #334155);
}

.element-dialog-form :deep(.el-input__wrapper),
.element-dialog-form :deep(.el-textarea__inner),
.element-dialog-form :deep(.el-select__wrapper) {
  border-radius: var(--radius-md, 8px);
}

.element-dialog-form :deep(.el-input-number) {
  border-radius: var(--radius-md, 8px);
}

.element-dialog-form :deep(.el-input-number .el-input__wrapper) {
  border-radius: var(--radius-md, 8px);
}

.form-help-text {
  font-size: 12px;
  color: var(--gray-500, #64748b);
  margin-top: 4px;
}

/* 页面分组右键菜单 */
.group-context-menu {
  position: fixed;
  z-index: 9999;
  background: var(--gray-0, #fff);
  border: 1px solid var(--gray-200, #e2e8f0);
  border-radius: var(--radius-md, 8px);
  box-shadow: var(--shadow-md);
  padding: 4px 0;
  margin: 0;
  list-style: none;
  min-width: 140px;
}

.group-context-menu li {
  padding: 8px 16px;
  cursor: pointer;
  font-size: 13px;
  color: var(--gray-700, #334155);
  transition: background 0.15s;
}

.group-context-menu li:hover {
  background: var(--gray-50, #f8fafc);
  color: var(--brand-600, #3570e6);
}

.group-context-menu li.danger {
  color: var(--error, #ef4444);
}

.group-context-menu li.danger:hover {
  background: var(--error-bg, #fef2f2);
}
</style>