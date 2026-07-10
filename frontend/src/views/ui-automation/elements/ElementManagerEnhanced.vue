<template>
  <div class="element-manager">
    <div class="element-layout">
      <!-- 左侧页面树 -->
      <div class="sidebar">
        <div class="sidebar-header">
          <el-select v-model="selectedProject" :placeholder="$t('common.selectProject')" @change="onProjectChange">
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
          <div class="header-actions">
            <el-button type="primary" size="small" @click="showCreatePageDialog = true" :title="$t('uiAutomation.element.createPage')">
              <el-icon><Folder /></el-icon>
            </el-button>
            <el-button type="success" size="small" @click="createEmptyElement" :title="$t('uiAutomation.element.addElement')">
              <el-icon><Plus /></el-icon>
            </el-button>
            <el-button type="warning" size="small" @click="showAiExtractDialog = true" title="AI智能提取">
              <el-icon><MagicStick /></el-icon>
            </el-button>
          </div>
        </div>

        <div class="page-tree">
          <el-tree
            ref="treeRef"
            :key="treeKey"
            :data="treeData"
            :props="treeProps"
            node-key="id"
            :expand-on-click-node="false"
            :default-expanded-keys="expandedKeys"
            @node-click="onNodeClick"
            @node-contextmenu="onNodeRightClick"
            @node-expand="onNodeExpand"
            @node-collapse="onNodeCollapse"
          >
            <template #default="{ node, data }">
              <div class="tree-node">
                <el-icon v-if="data.type === 'page'">
                  <Folder />
                </el-icon>
                <el-icon v-else>
                  <Document />
                </el-icon>

                <!-- 页面名称编辑 -->
                <div v-if="data.type === 'page' && editingNodeId === data.id" class="node-edit">
                  <el-input
                    v-model="editingNodeName"
                    size="small"
                    @blur="savePageName"
                    @keyup.enter="savePageName"
                    @keyup.esc="cancelEdit"
                    ref="editInputRef"
                  />
                </div>

                <!-- 普通显示模式 -->
                <span v-else class="node-label">{{ node.label }}</span>

                <span v-if="data.type === 'element'" class="element-type-tag" :class="data.element_type?.toLowerCase()">
                  {{ getElementTypeLabel(data.element_type) }}
                </span>
              </div>
            </template>
          </el-tree>
        </div>
      </div>

      <!-- 右侧元素详情 -->
      <div class="main-content">
        <div v-if="!selectedElement" class="empty-state">
          <el-empty :description="$t('uiAutomation.element.emptyElementTip')">
            <div style="display: flex; gap: 12px; justify-content: center;">
              <el-button type="primary" @click="createEmptyElement">{{ $t('uiAutomation.element.createNewElement') }}</el-button>
              <el-button type="warning" @click="showAiExtractDialog = true">
                <el-icon style="margin-right: 4px;"><MagicStick /></el-icon>AI 智能提取
              </el-button>
            </div>
          </el-empty>
        </div>

        <div v-else class="element-detail">
          <!-- 元素基本信息 -->
          <div class="element-header">
            <div class="element-info">
              <el-form ref="elementHeaderFormRef" :model="selectedElement" :rules="elementHeaderRules" inline>
                <el-form-item prop="name" :label="$t('uiAutomation.element.elementName')" required>
                  <el-input
                    v-model="selectedElement.name"
                    :placeholder="$t('uiAutomation.element.elementNamePlaceholder')"
                    style="width: 300px"
                    @blur="validateHeaderField('name')"
                  />
                </el-form-item>
                <el-form-item :label="$t('uiAutomation.element.elementType')">
                  <el-select v-model="selectedElement.element_type" :placeholder="$t('uiAutomation.element.elementType')" style="width: 120px;">
                    <el-option :label="$t('uiAutomation.element.elementTypes.button')" value="BUTTON" />
                    <el-option :label="$t('uiAutomation.element.elementTypes.input')" value="INPUT" />
                    <el-option :label="$t('uiAutomation.element.elementTypes.link')" value="LINK" />
                    <el-option :label="$t('uiAutomation.element.elementTypes.dropdown')" value="DROPDOWN" />
                    <el-option :label="$t('uiAutomation.element.elementTypes.checkbox')" value="CHECKBOX" />
                    <el-option :label="$t('uiAutomation.element.elementTypes.radio')" value="RADIO" />
                    <el-option :label="$t('uiAutomation.element.elementTypes.text')" value="TEXT" />
                    <el-option :label="$t('uiAutomation.element.elementTypes.image')" value="IMAGE" />
                    <el-option :label="$t('uiAutomation.element.elementTypes.table')" value="TABLE" />
                    <el-option :label="$t('uiAutomation.element.elementTypes.form')" value="FORM" />
                    <el-option :label="$t('uiAutomation.element.elementTypes.modal')" value="MODAL" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveElement" :loading="saving" ref="saveButtonRef">
                    {{ $t('uiAutomation.common.save') }}
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>

          <!-- 元素配置 -->
          <div class="element-form">
            <el-form ref="elementFormRef" :key="formKey" :model="selectedElement" :rules="elementRules" label-width="100px">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item :label="$t('uiAutomation.element.page')">
                    <el-select v-model="selectedElement.page" :placeholder="$t('uiAutomation.element.selectPage')">
                      <el-option
                        v-for="page in pages"
                        :key="page.id"
                        :label="page.name"
                        :value="page.name"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item :label="$t('uiAutomation.element.componentName')">
                    <el-input v-model="selectedElement.component_name" :placeholder="$t('uiAutomation.element.componentNamePlaceholder')" />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item :label="$t('uiAutomation.element.locatorStrategy')" prop="locator_strategy_id" required>
                    <el-select
                      v-model="selectedElement.locator_strategy_id"
                      :key="`strategy-${formKey}-${selectedElement.locator_strategy_id || 'null'}`"
                      :placeholder="$t('uiAutomation.element.rules.strategyRequired')"
                      value-key="id"
                      @blur="validateField('locator_strategy_id')"
                    >
                      <el-option
                        v-for="strategy in locatorStrategies"
                        :key="strategy.id"
                        :label="strategy.name"
                        :value="strategy.id"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item :label="$t('uiAutomation.element.waitTimeout') + '(' + $t('uiAutomation.element.waitTimeoutUnit') + ')'">
                    <el-input-number v-model="selectedElement.wait_timeout" :min="1" :max="60" style="width: 100%" />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item :label="$t('uiAutomation.element.forceAction')">
                    <el-switch
                      v-model="selectedElement.force_action"
                      :active-text="$t('uiAutomation.element.forceActionEnabled')"
                      :inactive-text="$t('uiAutomation.element.forceActionDisabled')"
                    />
                    <div class="form-help-text" style="margin-top: 5px;">
                      {{ $t('uiAutomation.element.forceActionTip') }}
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item :label="$t('uiAutomation.element.locatorExpression')" prop="locator_value" required>
                <el-input v-model="selectedElement.locator_value" :placeholder="$t('uiAutomation.element.locatorExpressionPlaceholder')" @blur="validateField('locator_value')" />
                <div class="form-help-text">
                  {{ $t('uiAutomation.element.locatorTip.title') }}<br>
                  - {{ $t('uiAutomation.element.locatorTip.id') }}<br>
                  - {{ $t('uiAutomation.element.locatorTip.css') }}<br>
                  - {{ $t('uiAutomation.element.locatorTip.xpath') }}<br>
                  - {{ $t('uiAutomation.element.locatorTip.other') }}
                </div>
              </el-form-item>

              <el-form-item :label="$t('uiAutomation.common.description')">
                <el-input v-model="selectedElement.description" type="textarea" :rows="3" :placeholder="$t('uiAutomation.element.descriptionPlaceholder')" />
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建页面对话框 -->
    <el-dialog v-model="showCreatePageDialog" :title="$t('uiAutomation.element.createPageTitle')" width="500px" :close-on-click-modal="false">
      <el-form ref="pageFormRef" :model="pageForm" :rules="pageRules" label-width="100px">
        <el-form-item :label="$t('uiAutomation.element.pageName')" prop="name">
          <el-input v-model="pageForm.name" :placeholder="$t('uiAutomation.element.pageNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.element.parentPage')">
          <el-select v-model="pageForm.parent_page" :placeholder="$t('uiAutomation.element.selectParentPage')" clearable>
            <el-option
              v-for="page in getAllPages()"
              :key="page.id"
              :label="page.name"
              :value="page.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.common.description')" prop="description">
          <el-input v-model="pageForm.description" type="textarea" :rows="3" :placeholder="$t('uiAutomation.element.descriptionPlaceholder')" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreatePageDialog = false">{{ $t('uiAutomation.common.cancel') }}</el-button>
        <el-button type="primary" @click="createPage">{{ $t('uiAutomation.common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 右键菜单 -->
    <ul v-show="showContextMenu" class="context-menu" :style="{ left: contextMenuX + 'px', top: contextMenuY + 'px' }">
      <li @click="addContextElement">{{ $t('uiAutomation.element.contextMenu.addElement') }}</li>
      <!-- 只有在普通页面节点下才显示"新增子页面"选项 -->
      <li v-if="rightClickedNode && rightClickedNode.type === 'page' && rightClickedNode.id !== 'unassigned'" @click="addSubPage">
        {{ $t('uiAutomation.element.contextMenu.addSubPage') }}
      </li>
      <!-- "未关联页面"节点不显示编辑选项 -->
      <li v-if="rightClickedNode && rightClickedNode.id !== 'unassigned'" @click="editNode">
        {{ $t('uiAutomation.element.contextMenu.edit') }}
      </li>
      <!-- 普通节点删除 -->
      <li v-if="rightClickedNode && rightClickedNode.id !== 'unassigned'" @click="deleteNode">
        {{ $t('uiAutomation.element.contextMenu.delete') }}
      </li>
      <!-- "未关联页面"节点：清空所有未关联元素 -->
      <li v-if="rightClickedNode && rightClickedNode.id === 'unassigned'" @click="deleteUnassignedElements" style="color: #f56c6c;">
        清空未关联元素
      </li>
    </ul>

    <!-- 编辑页面对话框 -->
    <el-dialog v-model="showEditPageDialog" :title="$t('uiAutomation.element.editPageTitle')" width="500px" :close-on-click-modal="false">
      <el-form ref="editPageFormRef" :model="editPageForm" :rules="pageRules" label-width="100px">
        <el-form-item :label="$t('uiAutomation.element.pageName')" prop="name">
          <el-input v-model="editPageForm.name" :placeholder="$t('uiAutomation.element.pageNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.element.parentPage')">
          <el-select v-model="editPageForm.parent_page" :placeholder="$t('uiAutomation.element.selectParentPage')" clearable>
            <el-option
              v-for="page in getAllPagesExceptCurrent(editPageForm.id)"
              :key="page.id"
              :label="page.name"
              :value="page.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('uiAutomation.common.description')" prop="description">
          <el-input v-model="editPageForm.description" type="textarea" :rows="3" :placeholder="$t('uiAutomation.element.descriptionPlaceholder')" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showEditPageDialog = false">{{ $t('uiAutomation.common.cancel') }}</el-button>
        <el-button type="primary" @click="updatePage">{{ $t('uiAutomation.common.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- AI智能提取 - 输入对话框 -->
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
        <el-button type="primary" @click="handleAiExtract" :loading="aiExtractLoading">开始提取</el-button>
      </template>
    </el-dialog>

    <!-- AI智能提取 - 结果预览对话框 -->
    <el-dialog v-model="showAiResultDialog" title="AI 提取结果预览" width="900px" :close-on-click-modal="false" top="5vh">
      <div style="margin-bottom: 12px; color: #606266;">
        页面: {{ aiResultInfo.url }}
        <span v-if="aiResultInfo.final_url && aiResultInfo.final_url !== aiResultInfo.url" style="margin-left: 10px; color: #E6A23C;">
          (实际跳转: {{ aiResultInfo.final_url }})
        </span>
        <span v-if="aiResultInfo.page_title" style="margin-left: 10px;">标题: {{ aiResultInfo.page_title }}</span>
        <span style="margin-left: 10px;">共 {{ aiExtractResults.length }} 个元素</span>
      </div>
      <el-table ref="aiResultTableRef" :data="aiExtractResults" max-height="500" style="width: 100%"
        @selection-change="handleAiResultSelectionChange">
        <el-table-column type="selection" width="45" />
        <el-table-column label="元素名称" min-width="130">
          <template #default="{ row }">
            <el-input v-model="row.name" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="类型" width="110">
          <template #default="{ row }">
            <el-select v-model="row.element_type" size="small">
              <el-option label="输入框" value="INPUT" />
              <el-option label="按钮" value="BUTTON" />
              <el-option label="链接" value="LINK" />
              <el-option label="下拉框" value="DROPDOWN" />
              <el-option label="复选框" value="CHECKBOX" />
              <el-option label="单选框" value="RADIO" />
              <el-option label="文本" value="TEXT" />
              <el-option label="图片" value="IMAGE" />
              <el-option label="表格" value="TABLE" />
              <el-option label="容器" value="CONTAINER" />
              <el-option label="表单" value="FORM" />
              <el-option label="弹窗" value="MODAL" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="定位策略" width="100">
          <template #default="{ row }">
            <el-select v-model="row.locator_strategy" size="small">
              <el-option label="ID" value="ID" />
              <el-option label="CSS" value="CSS" />
              <el-option label="XPath" value="XPath" />
              <el-option label="name" value="name" />
              <el-option label="class" value="class" />
              <el-option label="text" value="text" />
              <el-option label="placeholder" value="placeholder" />
              <el-option label="role" value="role" />
              <el-option label="label" value="label" />
              <el-option label="title" value="title" />
              <el-option label="test-id" value="test-id" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="定位表达式" min-width="180">
          <template #default="{ row }">
            <el-input v-model="row.locator_value" size="small" />
          </template>
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
          <template #default="{ row }">
            <el-input v-model="row.description" size="small" />
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <div style="display: flex; justify-content: space-between; width: 100%;">
          <el-button v-if="candidateButtons.length > 0" type="warning" @click="showAiResultDialog = false; showCandidateDialog = true">
            提取弹窗元素({{ candidateButtons.length }}个候选)
          </el-button>
          <span v-else></span>
          <div>
            <el-button @click="showAiResultDialog = false">取消</el-button>
            <el-button type="primary" @click="handleBatchImport" :loading="batchImportLoading">
              确认导入({{ selectedAiResults.length }}个元素)
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 候选弹窗触发按钮选择对话框 -->
    <el-dialog v-model="showCandidateDialog" title="弹窗元素提取" width="700px" :close-on-click-modal="false" top="5vh">
      <div style="margin-bottom: 16px;">
        <el-alert type="info" :closable="false" show-icon>
          <template #title>
            检测到以下按钮可能触发弹窗，勾选后系统将自动点击并提取弹窗内元素
          </template>
        </el-alert>
      </div>

      <el-table :data="candidateButtons" @selection-change="handleCandidateSelectionChange"
                style="width: 100%" max-height="400">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="text" label="按钮文本" width="150" />
        <el-table-column prop="source" label="来源" width="120">
          <template #default="{ row }">
            <el-tag :type="row.source === '页面级按钮' ? 'primary' : 'warning'" size="small">
              {{ row.source }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="识别原因" />
      </el-table>

      <template #footer>
        <div style="display: flex; justify-content: space-between;">
          <el-button @click="handleManualModeStart" :loading="manualLoading" type="info">
            手动交互模式
          </el-button>
          <div>
            <el-button @click="showCandidateDialog = false">跳过</el-button>
            <el-button type="primary" @click="handleExtractDialogs" :loading="candidateLoading">
              自动提取勾选按钮的弹窗
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 手动交互模式控制面板 -->
    <el-dialog v-model="showManualDialog" title="手动交互模式" width="500px" :close-on-click-modal="false"
               :show-close="false" top="30vh">
      <div style="margin-bottom: 16px;">
        <el-alert type="info" :closable="false" show-icon>
          <template #title>
            浏览器已打开，请手动操作到目标状态后，点击下方"提取当前页面"按钮
          </template>
        </el-alert>
      </div>

      <div v-if="manualCaptures.length > 0" style="margin-bottom: 16px;">
        <div style="font-weight: 600; margin-bottom: 8px;">已提取记录：</div>
        <div v-for="cap in manualCaptures" :key="cap.index" style="margin-bottom: 4px; color: #67c23a;">
          第{{ cap.index }}次 - {{ cap.page_name }}（{{ cap.element_count }} 个元素）
        </div>
      </div>

      <div style="margin-bottom: 12px;">
        <el-input v-model="aiExtractForm.page_name" placeholder="可选：为本次提取命名（如'新增用户弹窗'）"
                  size="small" clearable />
      </div>

      <template #footer>
        <el-button @click="handleManualCapture" :loading="manualLoading" type="primary">
          提取当前页面元素
        </el-button>
        <el-button @click="handleManualFinish" :loading="manualLoading" type="success">
          完成提取
        </el-button>
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
  MagicStick, Loading
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
const selectedElement = ref(null)
const expandedKeys = ref([])
const treeKey = ref(0) // 用于强制重新渲染树组件
const formKey = ref(0) // 用于强制重新渲染表单组件

// 表单引用
const treeRef = ref(null)
const pageFormRef = ref(null)
const editPageFormRef = ref(null)
const elementFormRef = ref(null)
const elementHeaderFormRef = ref(null)

// 对话框控制
const showCreatePageDialog = ref(false)
const showEditPageDialog = ref(false)

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

// 右键菜单
const showContextMenu = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const rightClickedNode = ref(null)

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

// 元素表单头部验证规则（元素名称）
const elementHeaderRules = computed(() => ({
  name: [
    { required: true, message: t('uiAutomation.element.rules.nameRequired'), trigger: 'blur' },
    { min: 1, max: 200, message: t('uiAutomation.element.rules.nameLength'), trigger: 'blur' }
  ]
}))

// 元素表单验证规则
const elementRules = computed(() => ({
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

// 页面名称编辑相关
const editingNodeId = ref(null)
const editingNodeName = ref('')
const editInputRef = ref(null)

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
      treeRef: typeof treeRef !== 'undefined' ? treeRef : null,
      expandedKeys,
      pages,
      $vm: { // 当前组件实例
        treeData: treeData.value,
        projects: projects.value,
        pages: pages.value,
        expandedKeys: expandedKeys.value
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

    // 检查是否有候选弹窗触发按钮
    const buttons = result.candidate_buttons || []
    if (buttons.length > 0) {
      // 先展示主页面元素结果
      showAiExtractDialog.value = false
      showAiResultDialog.value = true
      ElMessage.success(`主页面提取 ${aiExtractResults.value.length} 个元素，检测到 ${buttons.length} 个可能触发弹窗的按钮`)

      // 设置候选按钮数据，稍后用户可选择
      candidateButtons.value = buttons.map((btn, idx) => ({
        ...btn,
        _id: idx,
        selected: btn.source !== '表格行操作'  // 页面级按钮默认选中，行操作默认不选
      }))
      selectedCandidates.value = candidateButtons.value.filter(b => b.selected)

      // 默认全选所有提取的元素
      await nextTick()
      if (aiResultTableRef.value) {
        aiResultTableRef.value.toggleAllSelection()
      }
    } else {
      showAiExtractDialog.value = false
      showAiResultDialog.value = true
      ElMessage.success(`成功提取 ${aiExtractResults.value.length} 个元素`)

      // 默认全选所有提取的元素
      await nextTick()
      if (aiResultTableRef.value) {
        aiResultTableRef.value.toggleAllSelection()
      }
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
  showCandidateDialog.value = false

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

    ElMessage.success(`弹窗提取完成，新增 ${dialogElements.length} 个弹窗元素`)

    // 重新打开结果对话框
    showAiResultDialog.value = true
    await nextTick()
    if (aiResultTableRef.value) {
      aiResultTableRef.value.toggleAllSelection()
    }
  } catch (error) {
    const errMsg = error.response?.data?.error || error.message || '弹窗提取失败'
    ElMessage.error(errMsg)
    console.error('弹窗提取失败:', error)
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
      expandedKeys.value.push('unassigned')
    }

    console.log('最终treeData:', pageNodes)
    treeData.value = pageNodes

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

// 创建空元素
const createEmptyElement = () => {
  selectedElement.value = {
    name: '',
    element_type: 'BUTTON',
    page: '',
    component_name: '',
    locator_strategy_id: null, // 使用null而不是空字符串
    locator_value: '',
    wait_timeout: 5,
    force_action: false,  // 强制操作选项，默认禁用
    description: ''
  }
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

// 验证头部表单字段（元素名称）
const validateHeaderField = async (field) => {
  if (!elementHeaderFormRef.value) return
  try {
    await elementHeaderFormRef.value.validateField(field)
  } catch (error) {
    // 验证失败，不需要做任何处理，错误会自动显示
  }
}

// 验证整个元素表单
const validateElementForm = async () => {
  const results = await Promise.allSettled([
    elementHeaderFormRef.value?.validate() ?? Promise.resolve(),
    elementFormRef.value?.validate() ?? Promise.resolve()
  ])

  // 检查是否有验证失败的情况
  const hasFailed = results.some(result => result.status === 'rejected')
  return !hasFailed
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

// 节点点击
const onNodeClick = async (data) => {
  if (data.type === 'element') {
    try {
      const response = await getElementDetail(data._originalId || data.id)
      selectedElement.value = response.data

      // 强制刷新表单，确保下拉框正确显示
      formKey.value += 1
      console.log('点击节点时formKey更新为:', formKey.value)
    } catch (error) {
      console.error('获取元素详情失败:', error)
    }
  }
}

// 节点右键点击
const onNodeRightClick = (event, data) => {
  console.log('Node right click event:', event, 'Data:', data)
  event.preventDefault()

  // 隐藏现有菜单
  showContextMenu.value = false

  // 设置右键点击的节点
  rightClickedNode.value = data
  console.log('Set right clicked node:', data)

  // 设置菜单位置
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY

  // 显示菜单
  showContextMenu.value = true
  console.log('Show context menu at:', contextMenuX.value, contextMenuY.value)

  // 添加全局点击监听器以隐藏菜单
  const hideMenu = () => {
    console.log('Hide context menu')
    showContextMenu.value = false
    document.removeEventListener('click', hideMenu)
  }

  // 延迟添加监听器，避免立即触发
  setTimeout(() => {
    document.addEventListener('click', hideMenu)
  }, 100)
}

// 节点展开
const onNodeExpand = (data) => {
  if (!expandedKeys.value.includes(data.id)) {
    expandedKeys.value.push(data.id)
  }
}

// 节点收起
const onNodeCollapse = (data) => {
  const index = expandedKeys.value.indexOf(data.id)
  if (index > -1) {
    expandedKeys.value.splice(index, 1)
  }
}

// 保存元素
const saveElement = async () => {
  if (!selectedElement.value) return

  // 验证表单
  const isValid = await validateElementForm()
  if (!isValid) {
    ElMessage.error(t('uiAutomation.element.messages.saveFailed'))
    return
  }

  try {
    saving.value = true
    console.log('=== 保存元素调试 ===')
    console.log('当前选中的元素:', selectedElement.value)

    if (selectedElement.value.id) {
      // 更新元素 - 构建正确的API数据格式
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

      // 如果元素有分组（页面），确保传递正确的 group_id
      if (selectedElement.value.page) {
        console.log('更新元素 - 元素关联页面名称:', selectedElement.value.page)

        // 通过遍历树形结构查找对应的页面ID（返回原始ID用于API）
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

        const pageId = findPageIdByName(treeData.value, selectedElement.value.page)
        if (pageId) {
          elementUpdateData.group_id = pageId
        }
      }

      console.log('更新元素数据:', elementUpdateData)
      await updateElement(selectedElement.value.id, elementUpdateData)

      // 重新获取完整的元素详情以确保所有关联字段正确显示
      const detailResponse = await getElementDetail(selectedElement.value.id)
      selectedElement.value = detailResponse.data
      console.log('更新后获取到完整元素详情:', selectedElement.value)
      console.log('locator_strategy_id值:', selectedElement.value.locator_strategy_id, '类型:', typeof selectedElement.value.locator_strategy_id)
      console.log('locator_strategy对象:', selectedElement.value.locator_strategy)
      console.log('当前locatorStrategies:', locatorStrategies.value)
      console.log('locatorStrategies中是否包含id=' + selectedElement.value.locator_strategy_id + ':',
        locatorStrategies.value.find(s => s.id === selectedElement.value.locator_strategy_id))

      // 强制刷新表单，确保下拉框正确显示
      formKey.value += 1
      console.log('formKey更新为:', formKey.value)

      // 使用nextTick确保DOM更新
      await nextTick()
      console.log('DOM已更新，当前下拉框绑定值:', selectedElement.value.locator_strategy_id)

      ElMessage.success(t('uiAutomation.element.messages.saveSuccess'))
    } else {
      // 创建元素
      // 确保传递正确的字段名 project_id 而不是 project
      const elementData = {
        ...selectedElement.value,
        project_id: selectedProject.value
      }

      // 如果元素有分组（页面），确保传递 group_id
      if (selectedElement.value.page) {
        console.log('元素关联页面名称:', selectedElement.value.page)
        console.log('当前treeData结构:', treeData.value)

        // 通过遍历树形结构查找对应的页面ID（返回原始ID用于API）
        const findPageIdByName = (nodes, pageName) => {
          console.log(`在 ${nodes.length} 个节点中查找页面名称: ${pageName}`)
          for (const node of nodes) {
            console.log(`检查节点: ${node.name} (ID: ${node.id}, originalId: ${node._originalId}, type: ${node.type})`)
            if (node.type === 'page' && node.name === pageName) {
              const originalId = node._originalId || node.id
              console.log(`找到页面! 原始ID: ${originalId}`)
              return originalId
            }
            if (node.children) {
              console.log(`检查子节点:`, node.children.map(c => c.name))
              const foundId = findPageIdByName(node.children, pageName)
              if (foundId) return foundId
            }
          }
          console.log('未找到页面')
          return null
        }

        const pageId = findPageIdByName(treeData.value, selectedElement.value.page)
        console.log('找到的页面ID:', pageId)

        if (pageId) {
          elementData.group_id = pageId
          console.log('设置group_id为:', pageId)
        }
      }

      console.log('创建元素的数据:', elementData)
      const response = await createElement(elementData)
      console.log('创建响应:', response)

      // 重新获取完整的元素详情以确保所有关联字段正确显示
      const detailResponse = await getElementDetail(response.data.id)
      selectedElement.value = detailResponse.data
      console.log('获取到完整元素详情:', selectedElement.value)
      console.log('locator_strategy_id值:', selectedElement.value.locator_strategy_id, '类型:', typeof selectedElement.value.locator_strategy_id)
      console.log('locator_strategy对象:', selectedElement.value.locator_strategy)
      console.log('当前locatorStrategies:', locatorStrategies.value)
      console.log('locatorStrategies中是否包含id=' + selectedElement.value.locator_strategy_id + ':',
        locatorStrategies.value.find(s => s.id === selectedElement.value.locator_strategy_id))
      console.log('el-select绑定的值:', selectedElement.value.locator_strategy_id)

      // 强制刷新表单，确保下拉框正确显示
      formKey.value += 1
      console.log('formKey更新为:', formKey.value)

      // 使用nextTick确保DOM更新
      await nextTick()
      console.log('DOM已更新，当前下拉框绑定值:', selectedElement.value.locator_strategy_id)

      ElMessage.success(t('uiAutomation.element.messages.createSuccess'))
    }

    // 重新加载树
    console.log('开始重新加载元素树...')
    await loadElementTree()
    console.log('元素树重新加载完成')

    // 强制重新渲染树组件
    treeKey.value += 1
    console.log('树组件key更新为:', treeKey.value)

    // 强制触发Vue更新和树组件刷新
    nextTick(() => {
      console.log('nextTick - 检查treeData:', treeData.value)
      console.log('treeRef:', treeRef.value)

      // 展开新创建元素所在的页面节点（group_id需加page-前缀匹配树节点id）
      if (selectedElement.value && selectedElement.value.group_id) {
        const pageKey = `page-${selectedElement.value.group_id}`
        console.log('展开元素所在页面:', pageKey)
        if (!expandedKeys.value.includes(pageKey)) {
          expandedKeys.value.push(pageKey)
        }
      }

      console.log('树数据更新完成，当前expandedKeys:', expandedKeys.value)
    })
  } catch (error) {
    console.error('保存元素失败:', error)
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

// 保存页面名称
const savePageName = () => {
  // TODO: 实现页面名称保存
  editingNodeId.value = null
}

// 取消编辑
const cancelEdit = () => {
  editingNodeId.value = null
}

// 右键菜单操作函数
// 新增元素
const addContextElement = () => {
  console.log('Add context element clicked')
  showContextMenu.value = false
  createEmptyElement()

  // 如果右键点击的是页面节点，设置元素的页面
  if (rightClickedNode.value && rightClickedNode.value.type === 'page') {
    // 特殊处理：如果是"未关联页面"节点，不设置page和group_id
    if (rightClickedNode.value.id === 'unassigned') {
      console.log('在未关联页面节点下添加元素，不设置page和group_id')
      return
    }

    if (selectedElement.value) {
      selectedElement.value.page = rightClickedNode.value.name
      // 同时设置group_id，确保元素能正确关联到页面（用原始ID）
      selectedElement.value.group_id = rightClickedNode.value._originalId || rightClickedNode.value.id
    }
  }
}

// 新增子页面
const addSubPage = () => {
  console.log('Add sub page clicked')
  showContextMenu.value = false

  // 禁止在"未关联页面"节点下创建子页面
  if (rightClickedNode.value && rightClickedNode.value.id === 'unassigned') {
    ElMessage.warning('未关联页面节点下不能创建子页面')
    return
  }

  showCreatePageDialog.value = true

  // 如果右键点击的是页面节点，设置父页面（用原始ID）
  if (rightClickedNode.value && rightClickedNode.value.type === 'page') {
    pageForm.parent_page = rightClickedNode.value._originalId || rightClickedNode.value.id
  }
}

// 编辑节点
const editNode = async () => {
  console.log('Edit node clicked, rightClickedNode:', rightClickedNode.value)
  showContextMenu.value = false

  if (!rightClickedNode.value) {
    console.log('No right clicked node')
    return
  }

  console.log('Editing node:', rightClickedNode.value)
  console.log('Node type:', rightClickedNode.value.type)

  // 禁止编辑"未关联页面"节点
  if (rightClickedNode.value.id === 'unassigned') {
    ElMessage.warning('未关联页面节点不能编辑')
    return
  }

  if (rightClickedNode.value.type === 'page') {
    // 编辑页面
    console.log('Editing page node')
    editPageForm.id = rightClickedNode.value._originalId || rightClickedNode.value.id
    editPageForm.name = rightClickedNode.value.name
    editPageForm.description = rightClickedNode.value.description || ''
    editPageForm.parent_page = rightClickedNode.value.parent_group ?? null
    console.log('Set edit page form data:', editPageForm)
    console.log('Setting showEditPageDialog to true')
    showEditPageDialog.value = true
    console.log('showEditPageDialog value:', showEditPageDialog.value)
  } else if (rightClickedNode.value.type === 'element') {
    console.log('Editing element node')
    // 编辑元素 - 通过API获取完整的元素详情，避免使用树节点的复杂数据
    try {
      const response = await getElementDetail(rightClickedNode.value._originalId || rightClickedNode.value.id)
      selectedElement.value = response.data
      console.log('Set selected element for editing via API:', selectedElement.value)

      // 强制刷新表单，确保下拉框正确显示
      formKey.value += 1
      console.log('编辑时formKey更新为:', formKey.value)
    } catch (error) {
      console.error('获取元素详情失败:', error)
      ElMessage.error(t('uiAutomation.element.messages.getDetailFailed'))
    }
  } else {
    console.log('Unknown node type:', rightClickedNode.value.type)
  }
}

// 删除节点
const deleteNode = async () => {
  console.log('Delete node clicked, rightClickedNode:', rightClickedNode.value)
  showContextMenu.value = false

  if (!rightClickedNode.value) return

  // 禁止删除"未关联页面"节点
  if (rightClickedNode.value.id === 'unassigned') {
    ElMessage.warning('未关联页面节点不能删除')
    return
  }

  try {
    await ElMessageBox.confirm(
      t('uiAutomation.element.messages.confirmDeleteNode', { name: rightClickedNode.value.name }),
      t('uiAutomation.common.confirmDelete'),
      {
        type: 'warning',
        confirmButtonText: t('uiAutomation.common.confirm'),
        cancelButtonText: t('uiAutomation.common.cancel')
      }
    )

    console.log('Deleting node:', rightClickedNode.value)

    if (rightClickedNode.value.type === 'page') {
      // 删除页面（分组）— 用原始ID
      const originalId = rightClickedNode.value._originalId || rightClickedNode.value.id
      console.log('Calling deleteElementGroup with id:', originalId)
      await deleteElementGroup(originalId)
      ElMessage.success(t('uiAutomation.element.messages.pageDeleteSuccess'))
    } else if (rightClickedNode.value.type === 'element') {
      // 删除元素 — 用原始ID
      const originalId = rightClickedNode.value._originalId || rightClickedNode.value.id
      console.log('Calling deleteElement with id:', originalId)
      await deleteElement(originalId)
      ElMessage.success(t('uiAutomation.element.messages.deleteSuccess'))
      // 如果当前选中的是被删除的元素，清空选中
      if (selectedElement.value && selectedElement.value.id === originalId) {
        selectedElement.value = null
      }
    }

    console.log('Reload data after deletion')

    // 重新加载数据
    await Promise.all([
      loadPages(),
      loadElementTree()
    ])

    // 强制刷新树组件
    treeKey.value += 1
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(t('uiAutomation.element.messages.deleteFailed'))
    }
  }
}

// 清空未关联页面下的所有元素
const deleteUnassignedElements = async () => {
  showContextMenu.value = false

  if (!rightClickedNode.value || rightClickedNode.value.id !== 'unassigned') return

  const children = rightClickedNode.value.children || []
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
.element-manager {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.element-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 300px;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.sidebar-header {
  padding: 15px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-actions {
  display: flex;
  gap: 5px;
  margin-left: auto;
}

.page-tree {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 0;
}

.node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.element-type-tag {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  background-color: #ecf5ff;
  color: #409eff;
}

.main-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.element-header {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.element-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.element-form {
  margin-top: 20px;
}

.form-help-text {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

/* 右键菜单样式 */
.context-menu {
  position: fixed;
  z-index: 9999;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 5px 0;
  margin: 0;
  list-style: none;
  min-width: 120px;
}

.context-menu li {
  padding: 8px 15px;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
}

.context-menu li:hover {
  background-color: #f5f7fa;
  color: #409eff;
}
</style>