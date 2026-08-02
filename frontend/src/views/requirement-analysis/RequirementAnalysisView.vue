<template>
  <div class="requirement-analysis">
    <div class="page-header">
      <h1>{{ $t('requirementAnalysis.title') }}</h1>
    </div>

    <!-- 配置引导弹出窗口 -->
    <div v-if="showConfigGuide && !checkingConfig" class="modal-overlay" @click.self="showConfigGuide = false" :key="modalKey">
      <div class="guide-config-modal">
      <div class="guide-header">
        <svg class="guide-icon" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
          <path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z" fill="#f59e0b"/>
          <path d="M464 336a48 48 0 1 0 96 0 48 48 0 1 0-96 0zm72 112h-48c-4.4 0-8 3.6-8 8v272c0 4.4 3.6 8 8 8h48c4.4 0 8-3.6 8-8V456c0-4.4-3.6-8-8-8z" fill="#f59e0b"/>
        </svg>
        <div class="guide-title">
          <h2>{{ $t('configGuide.title') }}</h2>
          <p>{{ $t('configGuide.subtitle') }}</p>
        </div>
      </div>

      <div class="config-groups">
        <!-- 模型配置行 -->
        <div class="config-group">
          <div class="group-label">{{ $t('configGuide.modelConfig') }}</div>
          <div class="config-items-row">
            <div class="config-item-inline" :class="getConfigItemClass('writer_model')">
              <span class="status-symbol" v-html="getStatusSymbol('writer_model')"></span>
              <span class="config-label">{{ $t('configGuide.caseWriter') }}</span>
              <span class="config-name" v-if="configStatus.writer_model.name">{{ configStatus.writer_model.name }}</span>
              <span class="status-text" v-if="!configStatus.writer_model.configured">{{ $t('configGuide.unconfigured') }}</span>
              <span class="status-text warning" v-else-if="!configStatus.writer_model.enabled">{{ $t('configGuide.disabled') }}</span>
            </div>

            <div class="config-item-inline" :class="getConfigItemClass('reviewer_model')">
              <span class="status-symbol" v-html="getStatusSymbol('reviewer_model')"></span>
              <span class="config-label">{{ $t('configGuide.caseReviewer') }}</span>
              <span class="config-name" v-if="configStatus.reviewer_model.name">{{ configStatus.reviewer_model.name }}</span>
              <span class="status-text" v-if="!configStatus.reviewer_model.configured">{{ $t('configGuide.unconfigured') }}</span>
              <span class="status-text warning" v-else-if="!configStatus.reviewer_model.enabled">{{ $t('configGuide.disabled') }}</span>
            </div>
          </div>
        </div>

        <!-- 提示词配置行 -->
        <div class="config-group">
          <div class="group-label">{{ $t('configGuide.promptConfig') }}</div>
          <div class="config-items-row">
            <div class="config-item-inline" :class="getConfigItemClass('writer_prompt')">
              <span class="status-symbol" v-html="getStatusSymbol('writer_prompt')"></span>
              <span class="config-label">{{ $t('configGuide.caseWriter') }}</span>
              <span class="config-name" v-if="configStatus.writer_prompt.name">{{ configStatus.writer_prompt.name }}</span>
              <span class="status-text" v-if="!configStatus.writer_prompt.configured">{{ $t('configGuide.unconfigured') }}</span>
              <span class="status-text warning" v-else-if="!configStatus.writer_prompt.enabled">{{ $t('configGuide.disabled') }}</span>
            </div>

            <div class="config-item-inline" :class="getConfigItemClass('reviewer_prompt')">
              <span class="status-symbol" v-html="getStatusSymbol('reviewer_prompt')"></span>
              <span class="config-label">{{ $t('configGuide.caseReviewer') }}</span>
              <span class="config-name" v-if="configStatus.reviewer_prompt.name">{{ configStatus.reviewer_prompt.name }}</span>
              <span class="status-text" v-if="!configStatus.reviewer_prompt.configured">{{ $t('configGuide.unconfigured') }}</span>
              <span class="status-text warning" v-else-if="!configStatus.reviewer_prompt.enabled">{{ $t('configGuide.disabled') }}</span>
            </div>
          </div>
        </div>

        <!-- 生成行为配置行 -->
        <div class="config-group">
          <div class="group-label">{{ $t('configGuide.generationConfig') }}</div>
          <div class="config-items-row">
            <div class="config-item-inline" :class="getConfigItemClass('generation_config')">
              <span class="status-symbol" v-html="getStatusSymbol('generation_config')"></span>
              <span class="config-label">{{ $t('configGuide.generationSettings') }}</span>
              <span class="config-name" v-if="configStatus.generation_config && configStatus.generation_config.name">{{ configStatus.generation_config.name }}</span>
              <span class="status-text" v-if="!configStatus.generation_config || !configStatus.generation_config.configured">{{ $t('configGuide.unconfigured') }}</span>
            </div>
          </div>
        </div>
      </div>

        <div class="guide-actions">
          <button class="generate-manual-btn" @click="goToConfig">
            {{ $t('configGuide.goToConfig') }}
          </button>
          <div class="skip-action" @click="showConfigGuide = false">
            {{ $t('configGuide.configureLater') }}
          </div>
        </div>
      </div>
    </div>

    <!-- 输出模式选择弹窗 -->
    <div v-if="showOutputModeDialog" class="modal-overlay" @click.self="showOutputModeDialog = false">
      <div class="output-mode-dialog">
        <h3 class="dialog-title">{{ $t('requirementAnalysis.outputModeTitle') }}</h3>
        <p class="dialog-desc">{{ $t('requirementAnalysis.outputModeDesc') }}</p>
        <div class="mode-options">
          <label class="mode-option" :class="{ active: pendingOutputMode === 'stream' }" @click="pendingOutputMode = 'stream'">
            <input type="radio" v-model="pendingOutputMode" value="stream">
            <div class="mode-content">
              <div class="mode-title">{{ $t('requirementAnalysis.realtimeStream') }}</div>
              <div class="mode-desc">{{ $t('requirementAnalysis.realtimeStreamDesc') }}</div>
            </div>
          </label>
          <label class="mode-option" :class="{ active: pendingOutputMode === 'complete' }" @click="pendingOutputMode = 'complete'">
            <input type="radio" v-model="pendingOutputMode" value="complete">
            <div class="mode-content">
              <div class="mode-title">{{ $t('requirementAnalysis.completeOutput') }}</div>
              <div class="mode-desc">{{ $t('requirementAnalysis.completeOutputDesc') }}</div>
            </div>
          </label>
        </div>
        <div class="dialog-actions">
          <button class="dialog-cancel" @click="showOutputModeDialog = false">{{ $t('requirementAnalysis.cancelGeneration') || '取消' }}</button>
          <button class="dialog-confirm" @click="confirmGenerate">{{ $t('requirementAnalysis.generateButton') }}</button>
        </div>
      </div>
    </div>

    <!-- 评审确认弹窗 -->
    <div v-if="showReviewConfirmDialog" class="modal-overlay" @click.self="showReviewConfirmDialog = false">
      <div class="output-mode-dialog">
        <h3 class="dialog-title">AI评审确认</h3>
        <p class="dialog-desc">测试用例已生成完成，是否需要AI评审用例质量？</p>
        <div class="dialog-actions">
          <button class="dialog-cancel" @click="skipReview">跳过评审</button>
          <button class="dialog-confirm" @click="startReview">启动评审</button>
        </div>
      </div>
    </div>

    <!-- 主内容：左右分栏 -->
    <div class="workspace">
      <!-- 左栏：需求输入 -->
      <div class="left-panel" :style="{ width: leftPanelWidth + 'px' }">
        <div class="panel-section task-input-section">
          <div class="section-title">
            <span class="section-bar"></span>
            任务输入
          </div>
          <div class="form-group">
            <label class="form-label">* 任务描述</label>
            <input
              v-model="manualInput.title"
              type="text"
              class="form-input title-input"
              :placeholder="$t('requirementAnalysis.titlePlaceholder')">
          </div>
          <textarea
            v-model="manualInput.description"
            class="form-textarea main-textarea"
            :placeholder="$t('requirementAnalysis.descriptionPlaceholder')"
            @input="manualInput.description = manualInput.description.slice(0, 2000)"></textarea>
          <div class="char-count-bottom">{{ manualInput.description.length }}/2000</div>
        </div>

        <div class="left-toolbar">
          <div class="toolbar-left">
            <select v-model="manualInput.selectedProject" class="form-select project-select">
              <option value="">{{ $t('requirementAnalysis.selectProject') }}</option>
              <option v-for="project in projects" :key="project.id" :value="project.id">
                {{ project.name }}
              </option>
            </select>
            <div class="upload-inline">
              <input
                type="file"
                ref="fileInput"
                @change="handleFileSelect"
                accept=".pdf,.doc,.docx,.txt,.md"
                style="display: none;">
              <button class="upload-btn-inline" @click="$refs.fileInput.click()">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                <span v-if="!selectedFile">{{ $t('requirementAnalysis.selectFile') }}</span>
                <span v-else class="file-name-inline">{{ selectedFile.name }}</span>
              </button>
              <button v-if="selectedFile" class="remove-file-inline" @click="removeFile">✕</button>
            </div>
          </div>
          <button
            class="generate-btn"
            @click="showOutputModeDialog = true"
            :disabled="!canGenerateManual || isGenerating">
            {{ isGenerating ? '生成中...' : $t('requirementAnalysis.generateButton') }}
          </button>
        </div>

        <div class="left-tip">
          <div class="tip-title">提示</div>
          <div class="tip-text">AI模式使用"配置中心-AI智能模式配置"中的模型（如未添加模型，请前往添加）。支持中英文任务描述，任务描述越详细，生成效果越好。</div>
        </div>
      </div>

      <!-- 拖拽分隔条 -->
      <div
        class="resize-handle"
        @mousedown="onResizeStart"
      >
        <div class="resize-line"></div>
      </div>

      <!-- 右栏：输出展示（页签式三阶段） -->
      <div class="right-panel" :style="{ width: rightPanelWidth + 'px' }">
        <!-- 页签栏 -->
        <div class="stage-tabs">
          <div
            class="stage-tab"
            :class="{ active: activeTab === 'generate', completed: stagePhase === 'generated' || stagePhase === 'reviewing' || stagePhase === 'reviewed' || stagePhase === 'revising' || stagePhase === 'revised' || stagePhase === 'skip_review' }"
            @click="switchTab('generate')"
          >
            <span class="tab-step">1</span>
            <span class="tab-label">AI生成用例</span>
            <span v-if="isGenerating && stagePhase === 'generating'" class="streaming-tag">生成中...</span>
            <span v-else-if="stagePhase === 'generated' || stagePhase === 'reviewing' || stagePhase === 'reviewed' || stagePhase === 'revising' || stagePhase === 'revised' || stagePhase === 'skip_review'" class="tab-done">✓</span>
          </div>
          <div
            class="stage-tab"
            :class="{ active: activeTab === 'review', completed: stagePhase === 'reviewed' || stagePhase === 'revising' || stagePhase === 'revised', disabled: !tabData.review.visible }"
            @click="tabData.review.visible && switchTab('review')"
          >
            <span class="tab-step">2</span>
            <span class="tab-label">AI评审意见</span>
            <span v-if="isGenerating && stagePhase === 'reviewing'" class="streaming-tag">评审中...</span>
            <span v-else-if="stagePhase === 'reviewed' || stagePhase === 'revising' || stagePhase === 'revised'" class="tab-done">✓</span>
          </div>
          <div
            class="stage-tab"
            :class="{ active: activeTab === 'revise', completed: stagePhase === 'revised', disabled: !tabData.revise.visible }"
            @click="tabData.revise.visible && switchTab('revise')"
          >
            <span class="tab-step">3</span>
            <span class="tab-label">改进用例</span>
            <span v-if="isGenerating && stagePhase === 'revising'" class="streaming-tag">改进中...</span>
            <span v-else-if="stagePhase === 'revised'" class="tab-done">✓</span>
          </div>
        </div>

        <!-- 页签内容区 -->
        <div class="stage-content">
          <!-- 空态 -->
          <div v-if="activeTab === 'generate' && !isGenerating && !streamedContent && stagePhase === 'idle'" class="empty-state">
            请在左侧输入需求描述并点击生成
          </div>

          <!-- 页签1：AI生成用例 -->
          <div v-if="activeTab === 'generate'" class="stage-body">
            <div v-if="streamedContent" class="output-block">
              <div class="markdown-body" v-html="renderMarkdown(streamedContent)"></div>
            </div>
          </div>

          <!-- 页签2：AI评审意见 -->
          <div v-if="activeTab === 'review'" class="stage-body">
            <div v-if="streamedReviewContent" class="output-block review-block">
              <div class="markdown-body" v-html="renderMarkdown(streamedReviewContent)"></div>
            </div>
          </div>

          <!-- 页签3：改进后用例 -->
          <div v-if="activeTab === 'revise'" class="stage-body">
            <div v-if="finalTestCases" class="output-block final-block">
              <div class="markdown-body" v-html="renderMarkdown(finalTestCases)"></div>
            </div>
          </div>
        </div>

        <!-- 右栏底部操作 -->
        <div class="right-actions">
          <!-- 生成完成 → 确定（进入评审） -->
          <button v-if="activeTab === 'generate' && stagePhase === 'generated'" class="action-btn primary" @click="onGeneratedConfirm">
            确定
          </button>
          <!-- 跳过评审 -->
          <button v-if="activeTab === 'generate' && stagePhase === 'generated'" class="action-btn cancel" @click="skipReview">
            跳过评审
          </button>
          <!-- 评审完成 → 确定（进入改进） -->
          <button v-if="activeTab === 'review' && stagePhase === 'reviewed'" class="action-btn primary" @click="onReviewedConfirm">
            确定
          </button>
          <!-- 改进完成 → 采纳 -->
          <button v-if="activeTab === 'revise' && stagePhase === 'revised'" class="action-btn success" @click="onAdopt">
            采纳
          </button>
          <!-- 跳过评审后 → 采纳 -->
          <button v-if="activeTab === 'generate' && stagePhase === 'skip_review'" class="action-btn success" @click="onAdopt">
            采纳
          </button>
          <!-- 生成中/评审中/改进中 → 取消 -->
          <button v-if="isGenerating" class="action-btn cancel" @click="cancelGeneration">
            取消
          </button>
          <!-- 下载 -->
          <button v-if="stagePhase !== 'idle' && !isGenerating" class="action-btn download" @click="downloadTestCases">
            下载
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/utils/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as XLSX from 'xlsx'
import { useUserStore } from '@/stores/user'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (_) {}
    }
    try {
      return hljs.highlightAuto(str).value
    } catch (_) {}
    return ''
  }
})

export default {
  name: 'RequirementAnalysisView',
  data() {
    return {
      // 全局输出模式设置
      globalOutputMode: 'stream',  // 默认使用流式输出

      // 手动输入需求
      manualInput: {
        title: '',
        description: '',
        selectedProject: ''
      },

      // 文件上传
      selectedFile: null,
      documentTitle: '',
      selectedProject: '',
      projects: [],
      isDragOver: false,

      // 生成状态
      isGenerating: false,
      currentTaskId: null,
      progressText: '',
      currentStep: 0,
      pollInterval: null,
      eventSource: null,  // SSE连接
      streamedContent: '',  // 流式接收的内容
      streamedReviewContent: '',  // 流式接收的评审内容
      finalTestCases: '',  // 最终版用例
      hasShownCompletionMessage: false,  // 是否已经显示过完成消息
      showReviewStep: true,  // 是否显示评审步骤（根据生成配置决定）

      // 生成结果
      showResults: false,
      generationResult: null,

      // AI配置状态
      configStatus: {
        overall_status: 'unknown',
        message: '',
        writer_model: {
          configured: false,
          enabled: false,
          name: null,
          provider: null,
          id: null,
          required: true
        },
        writer_prompt: {
          configured: false,
          enabled: false,
          name: null,
          id: null,
          required: true
        },
        reviewer_model: {
          configured: false,
          enabled: false,
          name: null,
          id: null,
          required: true
        },
        reviewer_prompt: {
          configured: false,
          enabled: false,
          name: null,
          id: null,
          required: true
        },
        generation_config: {
          configured: false,
          enabled: false,
          name: null,
          id: null,
          required: true,
          default_output_mode: null
        }
      },
      showConfigGuide: false,
      checkingConfig: true,
      modalKey: 0,  // 用于强制重新渲染弹窗
      showOutputModeDialog: false,
      pendingOutputMode: 'stream',

      // 新版左右分栏
      leftPanelWidth: 0,  // 在 mounted 中初始化
      isResizing: false,

      // 新版流程阶段
      stagePhase: 'idle',  // idle | generating | generated | reviewing | reviewed | revising | revised | skip_review
      showReviewConfirmDialog: false,

      // 页签式阶段
      activeTab: 'generate',  // generate | review | revise
      tabData: {
        generate: { title: '', time: '' },
        review: { title: '', time: '', visible: false },
        revise: { title: '', time: '', visible: false }
      }
    }
  },

  computed: {
    canGenerateManual() {
      return this.manualInput.title.trim() &&
             this.manualInput.description.trim() &&
             this.manualInput.description.length <= 2000
    },
    rightPanelWidth() {
      const container = this.$el?.querySelector?.('.workspace')
      if (!container) return 0
      const total = container.clientWidth
      const handleWidth = 6
      return total - this.leftPanelWidth - handleWidth
    },
    rightPanelTitle() {
      if (this.stagePhase === 'generating' || this.stagePhase === 'generated') return 'AI生成用例'
      if (this.stagePhase === 'reviewing' || this.stagePhase === 'reviewed') return 'AI评审意见'
      if (this.stagePhase === 'revising' || this.stagePhase === 'revised') return '改进后用例'
      if (this.stagePhase === 'skip_review') return 'AI生成用例'
      return '输出结果'
    }
  },

  mounted() {
    this.progressText = this.$t('requirementAnalysis.preparing')
    this.loadProjects()
    this.checkConfigStatus()
    this.$nextTick(() => {
      this.initPanelWidths()
    })
    window.addEventListener('resize', this.onWindowResize)
  },

  activated() {
    // 当从其他页面返回时，重新检查配置状态
    // 立即隐藏弹窗和遮罩层，强制重新渲染
    this.showConfigGuide = false
    this.checkingConfig = true
    this.modalKey += 1  // 改变key值，强制重新渲染弹窗

    // 延迟检查配置，确保页面完全加载后再显示弹窗
    setTimeout(async () => {
      await this.checkConfigStatus()
    }, 200)
  },

  beforeUnmount() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval)
    }
    // 停止token自动刷新定时器
    const userStore = useUserStore()
    userStore.stopAutoRefresh()
    window.removeEventListener('resize', this.onWindowResize)
  },

  methods: {
    async loadProjects() {
      try {
        const response = await api.get('/projects/')
        this.projects = response.data.results || response.data
      } catch (error) {
        console.error(this.$t('requirementAnalysis.loadProjectsFailed'), error)
      }
    },

    async checkConfigStatus() {
      try {
        this.checkingConfig = true
        const response = await api.get('/requirement-analysis/config/check/')
        this.configStatus = response.data

        // 判断逻辑：只有当"用例编写模型"、"用例评审模型"、"用例编写提示词"和"用例评审提示词"都配置且启用时，才不显示弹框
        const writerModelReady = response.data.writer_model &&
                                response.data.writer_model.configured &&
                                response.data.writer_model.enabled

        const reviewerModelReady = response.data.reviewer_model &&
                                  response.data.reviewer_model.configured &&
                                  response.data.reviewer_model.enabled

        const writerPromptReady = response.data.writer_prompt &&
                                 response.data.writer_prompt.configured &&
                                 response.data.writer_prompt.enabled

        const reviewerPromptReady = response.data.reviewer_prompt &&
                                   response.data.reviewer_prompt.configured &&
                                   response.data.reviewer_prompt.enabled

        // 检查生成行为配置
        const generationConfigReady = response.data.generation_config &&
                                      response.data.generation_config.configured

        // 只有五项都准备好时才不显示引导弹框
        if (writerModelReady && reviewerModelReady && writerPromptReady && reviewerPromptReady && generationConfigReady) {
          this.showConfigGuide = false

          // 如果生成配置允许用户修改，则使用配置的默认输出模式
          if (response.data.generation_config && response.data.generation_config.default_output_mode) {
            this.globalOutputMode = response.data.generation_config.default_output_mode
          }

          // 根据生成配置的enable_auto_review决定是否显示评审步骤
          if (response.data.generation_config && response.data.generation_config.enable_auto_review !== null) {
            this.showReviewStep = response.data.generation_config.enable_auto_review
          } else {
            this.showReviewStep = true  // 默认显示
          }
        } else {
          this.showConfigGuide = true
        }
      } catch (error) {
        console.error('Failed to check config status:', error)
        // 如果检查失败，默认不显示引导，避免影响正常使用
        this.showConfigGuide = false
        this.checkingConfig = false
      } finally {
        this.checkingConfig = false
      }
    },

    goToConfig() {
      // 智能判断跳转目标：优先跳转到未配置/未启用的页面
      // 优先级：必需配置 > 可选配置，提示词 > 模型

      // 0. 首先检查生成行为配置（generation_config）
      if (!this.configStatus.generation_config || !this.configStatus.generation_config.configured) {
        this.$router.push('/configuration/generation-config')
        return
      }

      // 1. 优先检查必需的提示词配置（writer_prompt）
      if (!this.configStatus.writer_prompt.configured || !this.configStatus.writer_prompt.enabled) {
        this.$router.push('/configuration/prompt-config')
        return
      }

      // 2. 检查必需的模型配置（writer_model）
      if (!this.configStatus.writer_model.configured || !this.configStatus.writer_model.enabled) {
        this.$router.push('/configuration/ai-model')
        return
      }

      // 3. 检查可选的评审提示词（reviewer_prompt）
      if (!this.configStatus.reviewer_prompt.configured || !this.configStatus.reviewer_prompt.enabled) {
        this.$router.push('/configuration/prompt-config')
        return
      }

      // 4. 检查可选的评审模型（reviewer_model）
      if (!this.configStatus.reviewer_model.configured || !this.configStatus.reviewer_model.enabled) {
        this.$router.push('/configuration/ai-model')
        return
      }

      // 默认跳转到生成行为配置
      this.$router.push('/configuration/generation-config')
    },

    goToPromptConfig() {
      this.$router.push('/configuration/prompt-config')
    },

    getConfigItemClass(configKey) {
      const config = this.configStatus[configKey]
      if (config.enabled) {
        return 'status-enabled'
      } else if (config.configured) {
        return 'status-disabled'
      } else {
        return 'status-unconfigured'
      }
    },

    getStatusIcon(configKey) {
      const config = this.configStatus[configKey]
      if (config.enabled) {
        // 绿色对号
        return '<path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm193.5 301.7l-210.6 292c-12.7 17.7-39 17.7-51.7 0L318.5 484.9c-3.8-5.3 0-12.7 6.5-12.7h46.9c10.2 0 19.9 4.9 25.9 13.3l71.2 98.8 157.2-218c6-8.3 15.6-13.3 25.9-13.3H699c6.5 0 10.3 7.4 6.5 12.7z" fill="#27ae60"/>'
      } else if (config.configured) {
        // 禁用图标（灰色圆圈和斜线）
        return '<path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372zm128-412c0 4.4-3.6 8-8 8H392c-4.4 0-8-3.6-8-8v-48c0-4.4 3.6-8 8-8h240c4.4 0 8 3.6 8 8v48z" fill="#95a5a6"/>'
      } else {
        // 红色叉号
        return '<path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm165.4 618.2l-66-70.7c-10.6-10.1-28.1-10.1-38.8 0l-66.7 71.5-66.7-71.5c-10.6-10.1-28.1-10.1-38.8 0l-66 70.7c-9.9 10.6-9.9 27.4 0 38l66 70.7c10.6 10.1 28.1 10.1 38.8 0l66.7-71.5 66.7 71.5c10.6 10.1 28.1 10.1 38.8 0l66-70.7c9.9-10.6 9.9-27.4 0-38z" fill="#e74c3c"/>'
      }
    },

    getStatusSymbol(configKey) {
      const config = this.configStatus[configKey]
      if (config.enabled) {
        // 绿色对勾
        return '<span style="color: #27ae60; font-size: 18px;">✓</span>'
      } else if (config.configured) {
        // 禁用图标
        return '<span style="color: #95a5a6; font-size: 18px;">○</span>'
      } else {
        // 红色叉号
        return '<span style="color: #e74c3c; font-size: 18px;">✗</span>'
      }
    },

    handleDrop(event) {
      event.preventDefault()
      this.isDragOver = false
      const files = event.dataTransfer.files
      if (files.length > 0) {
        this.handleFileSelect({ target: { files } })
      }
    },

    handleFileSelect(event) {
      const file = event.target.files[0]
      if (file) {
        const allowedTypes = [
          'application/pdf',
          'application/msword',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          'text/plain',
          'text/markdown',
          'text/x-markdown'
        ]

        if (allowedTypes.includes(file.type) ||
            file.name.match(/\.(pdf|doc|docx|txt|md)$/i)) {
          this.selectedFile = file
          this.documentTitle = file.name.replace(/\.[^/.]+$/, "")
        } else {
          ElMessage.error(this.$t('requirementAnalysis.invalidFileFormatDetail'))
        }
      }
    },

    removeFile() {
      this.selectedFile = null
      this.documentTitle = ''
      this.$refs.fileInput.value = ''
    },

    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },

    confirmGenerate() {
      if (!this.canGenerateManual) {
        ElMessage.error(this.$t('requirementAnalysis.fillRequiredInfo'))
        return
      }
      this.globalOutputMode = this.pendingOutputMode
      this.showOutputModeDialog = false

      if (this.selectedFile) {
        this.generateFromDocument()
      } else {
        this.generateFromManualInput()
      }
    },

    async generateFromManualInput() {
      if (!this.canGenerateManual) {
        ElMessage.error(this.$t('requirementAnalysis.fillRequiredInfo'))
        return
      }

      const requirementText = `${this.$t('requirementAnalysis.requirementTitle')}: ${this.manualInput.title}\n\n${this.$t('requirementAnalysis.requirementDescription')}:\n${this.manualInput.description}`

      await this.startGeneration(
        this.manualInput.title,
        requirementText,
        this.manualInput.selectedProject,
        this.globalOutputMode  // 使用全局输出模式
      )
    },

    async generateFromDocument() {
      if (!this.selectedFile || !this.documentTitle) {
        ElMessage.error(this.$t('requirementAnalysis.selectFileAndTitle'))
        return
      }

      try {
        // 首先上传并提取文档内容
        const formData = new FormData()
        formData.append('title', this.documentTitle)
        formData.append('file', this.selectedFile)
        if (this.selectedProject) {
          formData.append('project', this.selectedProject)
        }

        ElMessage.info(this.$t('requirementAnalysis.extractingContent'))
        const uploadResponse = await api.post('/requirement-analysis/documents/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })

        // 提取文档内容
        const extractResponse = await api.get(`/requirement-analysis/documents/${uploadResponse.data.id}/extract_text/`)
        const extractedText = extractResponse.data.extracted_text

        if (!extractedText || extractedText.trim().length === 0) {
          ElMessage.error(this.$t('requirementAnalysis.extractionFailed'))
          return
        }

        const requirementText = `${this.$t('requirementAnalysis.documentTitle')}: ${this.documentTitle}\n\n${this.$t('requirementAnalysis.documentContent')}:\n${extractedText}`

        await this.startGeneration(
          this.documentTitle,
          requirementText,
          this.selectedProject,
          this.globalOutputMode  // 使用全局输出模式
        )

      } catch (error) {
        console.error(this.$t('requirementAnalysis.documentProcessingFailed'), error)
        ElMessage.error(this.$t('requirementAnalysis.documentProcessingFailed') + ': ' + (error.response?.data?.error || error.message))
      }
    },

    async startGeneration(title, requirementText, projectId, outputMode = 'stream') {
      // 在开始生成前，主动刷新token确保生成过程中不会过期
      try {
        const userStore = useUserStore()
        if (userStore.isTokenExpiringSoon && userStore.refreshToken) {
          console.log('Refreshing token before generation...')
          await userStore.refreshAccessToken()
          console.log('Token refreshed successfully, safe to start generation')
        } else if (userStore.accessToken) {
          console.log('Token status is good, no refresh needed')
        }
      } catch (error) {
        console.error('Token refresh failed:', error)
        ElMessage.error(this.$t('requirementAnalysis.tokenRefreshFailed'))
        return
      }

      this.isGenerating = true
      this.currentStep = 1
      this.progressText = this.$t('requirementAnalysis.creatingTask')
      this.streamedContent = ''  // 清空流式内容
      this.finalTestCases = ''  // 清空最终版用例
      this.streamedReviewContent = ''  // 清空评审内容
      this.hasShownCompletionMessage = false  // 重置完成消息标志位
      this.showResults = false  // 隐藏上一次的结果
      this.stagePhase = 'generating'  // 新版：设置阶段
      this.activeTab = 'generate'

      try {
        // 调用新的生成API
        const requestData = {
          title: title,
          requirement_text: requirementText,
          use_writer_model: true,
          use_reviewer_model: false,  // 不自动评审，由前端决定是否启动评审
          output_mode: outputMode  // 添加输出模式参数
        }

        // 如果选择了项目，添加到请求中
        if (projectId) {
          requestData.project = projectId
        }

        const response = await api.post('/requirement-analysis/testcase-generation/generate/', requestData)

        this.currentTaskId = response.data.task_id
        this.progressText = this.$t('requirementAnalysis.taskCreated')

        ElMessage.success(this.$t('requirementAnalysis.generateSuccess'))

        // 根据输出模式选择不同的进度获取方式
        if (outputMode === 'stream') {
          this.startStreamingProgress()
        } else {
          this.startPolling()
        }

      } catch (error) {
        console.error(this.$t('requirementAnalysis.createTaskFailed'), error)
        ElMessage.error(this.$t('requirementAnalysis.createTaskFailed') + ': ' + (error.response?.data?.error || error.message))
        this.isGenerating = false
      }
    },

    startStreamingProgress() {
      // 使用SSE进行流式进度获取
      // 注意：EventSource不使用axios代理，需要直接指向后端服务器
      // 完整的URL路径: /api/requirement-analysis/testcase-generation/{task_id}/stream_progress/

      // 动态获取后端URL：使用当前页面的协议和主机名
      // 在生产环境中(如Docker部署)，通常通过Nginx反向代理访问，端口应该是80或443(与当前页面一致)
      // 而不是直接访问后端端口8000
      const currentOrigin = window.location.origin
      const apiUrl = `${currentOrigin}/api/requirement-analysis/testcase-generation/${this.currentTaskId}/stream_progress/`

      console.log('SSE连接URL:', apiUrl)

      // 创建EventSource（不支持自定义headers，使用withCredentials发送cookie）
      this.eventSource = new EventSource(apiUrl, { withCredentials: true })

      // 监听连接打开事件
      this.eventSource.onopen = (event) => {
        console.log('✅ SSE连接已打开', event)
      }

      this.eventSource.onmessage = (event) => {
        console.log('📨 收到SSE消息:', event.data)

        try {
          const data = JSON.parse(event.data)
          console.log('📦 解析后的数据:', data)

          if (data.type === 'progress') {
            // Update progress status
            if (data.status === 'generating') {
              this.currentStep = 2
              this.progressText = `${this.$t('requirementAnalysis.statusGenerating')} ${data.progress}%`
              if (this.stagePhase === 'generating') this.stagePhase = 'generating'
            } else if (data.status === 'reviewing') {
              this.currentStep = 3
              this.progressText = `${this.$t('requirementAnalysis.statusReviewing')} ${data.progress}%`
              if (this.stagePhase === 'reviewing') this.stagePhase = 'reviewing'
            } else if (data.status === 'revising') {
              this.currentStep = 3
              this.progressText = `${this.$t('requirementAnalysis.statusRevising')} ${data.progress}%`
              if (this.stagePhase === 'revising') this.stagePhase = 'revising'
            }
          } else if (data.type === 'content') {
            // Real-time streaming content (case generation)
            console.log('✍️ Received streaming content:', data.content.length, 'characters')
            this.streamedContent += data.content
            this.currentStep = 2
            this.progressText = this.$t('requirementAnalysis.statusGenerating')
          } else if (data.type === 'review_content') {
            // Real-time review content
            console.log('📝 Received review content:', data.content.length, 'characters', 'Total length:', this.streamedReviewContent.length + data.content.length)
            this.streamedReviewContent += data.content
            this.currentStep = 3
            this.progressText = this.$t('requirementAnalysis.statusReviewing')
          } else if (data.type === 'final_content') {
            // Real-time final test cases content
            console.log('🎯 Received final cases content:', data.content.length, 'characters', 'Total length:', this.finalTestCases.length + data.content.length)
            this.finalTestCases += data.content
            this.currentStep = 3
            this.progressText = '🎯 ' + this.$t('requirementAnalysis.statusRevising')
          } else if (data.type === 'status') {
            // Final status
            console.log('📊 Received status update:', data.status)
            if (data.status === 'completed') {
              this.progressText = this.$t('requirementAnalysis.statusCompleted')
              // Fetch final result
              this.fetchFinalResult()
            } else if (data.status === 'failed') {
              this.progressText = this.$t('requirementAnalysis.statusFailed')
              this.handleGenerationError()
            }
          } else if (data.type === 'done') {
            // 流式结束，立即关闭EventSource，获取最终结果
            console.log('✅ 流式传输完成')
            if (this.eventSource) {
              console.log('🔒 关闭SSE连接')
              this.eventSource.close()
              this.eventSource = null
            }
            this.fetchFinalResult()
          }
        } catch (e) {
          console.error('❌ 解析SSE数据失败:', e, '原始数据:', event.data)
        }
      }

      this.eventSource.onerror = (error) => {
        console.log('⚠️ SSE连接事件:', error)

        // 如果EventSource已经被关闭（在onmessage中关闭的），不做任何处理
        if (!this.eventSource) {
          console.log('ℹ️ EventSource已关闭，忽略错误事件')
          return
        }

        console.log('EventSource状态:', {
          readyState: this.eventSource.readyState,
          url: this.eventSource.url
        })

        // 如果任务已经完成或不在生成中，不要降级
        if (this.showResults || !this.isGenerating) {
          console.log('ℹ️ 任务已完成或不在生成中，不降级到轮询')
          // 清理EventSource
          if (this.eventSource) {
            this.eventSource.close()
            this.eventSource = null
          }
          return
        }

        // readyState=2表示连接已关闭，readyState=0表示连接中断
        // EventSource会自动重连（readyState=0），除非是致命错误（readyState=2）
        if (this.eventSource.readyState === 2) {
          console.error('❌ SSE连接永久关闭，降级到轮询模式')
          this.eventSource.close()
          this.eventSource = null
          ElMessage.warning(this.$t('requirementAnalysis.streamConnectionInterrupted'))
          this.startPolling()
        } else if (this.eventSource.readyState === 0) {
          // EventSource正在重连，等待一段时间后检查
          console.log('🔄 SSE正在重连...')
          setTimeout(() => {
            // 如果5秒后还是断开状态，降级到轮询
            if (this.eventSource && this.eventSource.readyState === 0) {
              console.error('❌ SSE重连失败，降级到轮询模式')
              this.eventSource.close()
              this.eventSource = null
              ElMessage.warning(this.$t('requirementAnalysis.streamConnectionInterrupted'))
              this.startPolling()
            }
          }, 5000)
        }
      }
    },

    async fetchFinalResult() {
      try {
        // 修复URL：去掉多余的/api/前缀（axios baseURL已经包含/api）
        const response = await api.get(`/requirement-analysis/testcase-generation/${this.currentTaskId}/progress/`)
        const task = response.data

        this.generationResult = task
        this.showResults = true
        this.isGenerating = false

        // 设置第4步为完成状态
        this.currentStep = 4

        // 设置最终版用例（如果还没有通过流式接收完整）
        if (task.final_test_cases) {
          console.log('📝 Getting final cases from task object')
          this.finalTestCases = task.final_test_cases
        }

        // 如果评审内容为空，从task对象中获取
        if (!this.streamedReviewContent && task.review_feedback) {
          console.log('📝 Getting review content from task object')
          this.streamedReviewContent = task.review_feedback
        }

        // 如果生成内容为空，从task对象中获取
        if (!this.streamedContent && task.generated_test_cases) {
          console.log('✍️ Getting generated content from task object')
          this.streamedContent = task.generated_test_cases
        }

        if (this.eventSource) {
          this.eventSource.close()
          this.eventSource = null
        }

        // 根据当前阶段更新 stagePhase
        if (this.stagePhase === 'reviewing') {
          this.stagePhase = 'reviewed'
          this.updateTabData('review', this.manualInput.title)
          this.activeTab = 'review'
        } else if (this.stagePhase === 'revising') {
          this.stagePhase = 'revised'
          this.updateTabData('revise', this.manualInput.title)
          this.activeTab = 'revise'
        } else if (this.stagePhase === 'generating') {
          this.stagePhase = 'generated'
          this.updateTabData('generate', this.manualInput.title)
        }

        // Only show completion message once
        if (!this.hasShownCompletionMessage) {
          ElMessage.success(this.$t('requirementAnalysis.generateCompleteSuccess'))
          this.hasShownCompletionMessage = true
        }
      } catch (error) {
        console.error('Failed to fetch final result:', error)
        ElMessage.error(this.$t('requirementAnalysis.fetchResultFailed'))
        this.isGenerating = false
      }
    },

    handleGenerationError() {
      this.isGenerating = false
      if (this.eventSource) {
        this.eventSource.close()
        this.eventSource = null
      }
      if (this.pollInterval) {
        clearInterval(this.pollInterval)
        this.pollInterval = null
      }
    },

    startPolling() {
      this.pollInterval = setInterval(async () => {
        try {
          // 修复URL：去掉多余的/api/前缀（axios baseURL已经包含/api）
          const response = await api.get(`/requirement-analysis/testcase-generation/${this.currentTaskId}/progress/`)
          const task = response.data

          console.log(`${this.$t('requirementAnalysis.taskStatus')}: ${task.status}, ${this.$t('requirementAnalysis.progress')}: ${task.progress}%`)

          // 更新进度显示
          if (task.status === 'generating') {
            this.currentStep = 2
            this.progressText = this.$t('requirementAnalysis.statusGenerating')
          } else if (task.status === 'reviewing') {
            this.currentStep = 3
            this.progressText = this.$t('requirementAnalysis.statusReviewing')
          } else if (task.status === 'completed') {
            this.currentStep = 4
            this.progressText = this.$t('requirementAnalysis.statusCompleted')

            // 任务完成，显示结果
            this.generationResult = task
            this.showResults = true
            this.isGenerating = false

            // 设置显示内容（完整输出模式下需要）
            if (task.generated_test_cases) {
              console.log('✍️ Polling mode - Setting generated content')
              this.streamedContent = task.generated_test_cases
            }
            if (task.review_feedback) {
              console.log('📝 Polling mode - Setting review content')
              this.streamedReviewContent = task.review_feedback
            }
            if (task.final_test_cases) {
              console.log('🎯 Polling mode - Setting final test cases')
              this.finalTestCases = task.final_test_cases
            }

            clearInterval(this.pollInterval)
            this.pollInterval = null

            // 只显示一次完成消息
            if (!this.hasShownCompletionMessage) {
              ElMessage.success(this.$t('requirementAnalysis.generateCompleteSuccess'))
              this.hasShownCompletionMessage = true
            }
            return
          } else if (task.status === 'failed') {
            this.progressText = this.$t('requirementAnalysis.statusFailed')
            this.isGenerating = false

            clearInterval(this.pollInterval)
            this.pollInterval = null

            ElMessage.error(this.$t('requirementAnalysis.generateFailed') + ': ' + (task.error_message || this.$t('requirementAnalysis.unknownError')))
            return
          }

        } catch (error) {
          console.error(this.$t('requirementAnalysis.checkProgressFailed'), error)
          // 继续轮询，不中断
        }
      }, 3000) // 每3秒检查一次
    },

    cancelGeneration() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval)
        this.pollInterval = null
      }
      this.isGenerating = false
      this.currentTaskId = null
      ElMessage.info(this.$t('requirementAnalysis.generationCancelled'))
    },

    // 下载测试用例为xlsx文件
    async downloadTestCases() {
      try {
        // 解析最终测试用例内容
        const finalTestCases = this.generationResult.final_test_cases;
        const taskId = this.generationResult.task_id;

        // 创建工作簿
        const workbook = XLSX.utils.book_new();

        // 过滤掉总结和建议部分，只保留测试用例内容
        const filteredContent = this.filterTestCasesOnly(finalTestCases);

        // 尝试解析表格格式的测试用例（参考AutoGenTestCase的做法）
        const tableFormat = this.parseTableFormat(filteredContent);

        let worksheetData = [];

        if (tableFormat.length > 0) {
          // 如果解析到表格格式，直接使用，但要确保表头正确
          worksheetData = tableFormat;

          // 检查并修正表头
          if (worksheetData.length > 0) {
            const header = worksheetData[0];
            for (let i = 0; i < header.length; i++) {
              if (header[i] && header[i].includes('测试步骤')) {
                header[i] = header[i].replace('测试步骤', '操作步骤');
              }
              if (header[i] && header[i].includes('Test Steps')) {
                header[i] = header[i].replace('Test Steps', '操作步骤');
              }
            }
          }
        } else {
          // 否则尝试解析结构化格式
          worksheetData = this.parseStructuredFormat(filteredContent);
        }

        // 将所有单元格中的<br>标签转换为换行符
        worksheetData = worksheetData.map(row =>
          row.map(cell => this.convertBrToNewline(cell))
        );

        // 创建工作表
        const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);

        // 设置列宽
        const colWidths = [
          { wch: 15 }, // 测试用例编号
          { wch: 30 }, // 测试场景
          { wch: 25 }, // 前置条件
          { wch: 40 }, // 操作步骤
          { wch: 30 }, // 预期结果
          { wch: 10 }  // 优先级
        ];
        worksheet['!cols'] = colWidths;

        // 设置表头样式（加粗）
        if (worksheetData.length > 1) {
          for (let col = 0; col < Math.min(6, worksheetData[0].length); col++) {
            const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col });
            if (!worksheet[cellAddress]) continue;
            worksheet[cellAddress].s = {
              font: { bold: true },
              alignment: { horizontal: 'center', vertical: 'center', wrapText: true }
            };
          }

          // 设置自动换行
          for (let row = 1; row < worksheetData.length; row++) {
            for (let col = 0; col < Math.min(6, worksheetData[row].length); col++) {
              const cellAddress = XLSX.utils.encode_cell({ r: row, c: col });
              if (worksheet[cellAddress]) {
                worksheet[cellAddress].s = {
                  alignment: { vertical: 'top', wrapText: true }
                };
              }
            }
          }
        }

        // 将工作表添加到工作簿
        XLSX.utils.book_append_sheet(workbook, worksheet, this.$t('requirementAnalysis.testCaseSheetName'));

        // 生成文件名（包含任务ID和日期）
        const fileName = this.$t('requirementAnalysis.excelFileName', { taskId: taskId, date: new Date().toISOString().slice(0, 10) });

        // 导出文件
        XLSX.writeFile(workbook, fileName);

        ElMessage.success(this.$t('requirementAnalysis.downloadSuccess'));
      } catch (error) {
        console.error(this.$t('requirementAnalysis.downloadFailed'), error);
        ElMessage.error(this.$t('requirementAnalysis.downloadFailed') + ': ' + (error.message || this.$t('requirementAnalysis.unknownError')));
      }
    },

    // 保存到用例记录
    async saveToTestCaseRecords() {
      try {
        // 调用后端API保存到记录
        const response = await api.post(`/requirement-analysis/testcase-generation/${this.generationResult.task_id}/save_to_records/`)

        if (response.data.already_saved) {
          ElMessage.info(this.$t('requirementAnalysis.alreadySaved'))
        } else {
          const importedCount = response.data.imported_count || 0
          ElMessage.success(`测试用例已保存！已导入 ${importedCount} 条测试用例到测试用例管理系统`)
        }

        // 不跳转，留在当前页面
        // this.$router.push('/generated-testcases')
      } catch (error) {
        console.error(this.$t('requirementAnalysis.saveFailed'), error)
        ElMessage.error(this.$t('requirementAnalysis.saveFailed') + ': ' + (error.response?.data?.error || error.message))
      }
    },

    resetGeneration() {
      // 重置生成状态
      this.isGenerating = false;
      this.currentTaskId = null;
      this.progressText = this.$t('requirementAnalysis.preparing');
      this.currentStep = 0;
      this.showResults = false;
      this.generationResult = null;
      this.stagePhase = 'idle';

      // 清空流式内容和最终版用例
      this.streamedContent = '';
      this.streamedReviewContent = '';
      this.finalTestCases = '';

      if (this.pollInterval) {
        clearInterval(this.pollInterval);
        this.pollInterval = null;
      }

      // 刷新页面以获取最新的配置
      window.location.reload();
    },

    // 格式化日期时间
    // === 新版左右分栏方法 ===
    initPanelWidths() {
      const container = this.$el?.querySelector?.('.workspace')
      if (container) {
        this.leftPanelWidth = Math.floor(container.clientWidth / 2)
      } else {
        this.leftPanelWidth = Math.floor((window.innerWidth - 80) / 2) // fallback
      }
    },
    onWindowResize() {
      this.initPanelWidths()
    },
    onResizeStart(e) {
      e.preventDefault()
      this.isResizing = true
      const startX = e.clientX
      const startWidth = this.leftPanelWidth
      const container = this.$el.querySelector('.workspace')
      const maxWidth = container ? container.clientWidth - 200 : 800

      const onMouseMove = (ev) => {
        const diff = ev.clientX - startX
        const newWidth = Math.min(Math.max(startWidth + diff, 300), maxWidth)
        this.leftPanelWidth = newWidth
      }
      const onMouseUp = () => {
        this.isResizing = false
        document.removeEventListener('mousemove', onMouseMove)
        document.removeEventListener('mouseup', onMouseUp)
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
      }
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
      document.addEventListener('mousemove', onMouseMove)
      document.addEventListener('mouseup', onMouseUp)
    },

    // === 新版流程方法 ===
    switchTab(tab) {
      // 已完成的页签可以切换回去查看，但活跃中的不能切
      this.activeTab = tab
    },

    // 更新页签数据（标题+时间）
    updateTabData(tab, title) {
      this.tabData[tab] = {
        title: title,
        time: new Date().toLocaleString('zh-CN'),
        visible: true
      }
    },

    renderMarkdown(content) {
      if (!content) return ''
      // 去除"新增"标记
      let cleaned = content
        .replace(/\*\*新增\*\*-/g, '')
        .replace(/新增-/g, '')
      return md.render(cleaned)
    },

    // 生成完成 → 点击"确定"
    onGeneratedConfirm() {
      this.showReviewConfirmDialog = true
    },

    // 启动评审
    async startReview() {
      this.showReviewConfirmDialog = false
      this.stagePhase = 'reviewing'
      this.isGenerating = true
      this.streamedReviewContent = ''
      this.tabData.review.visible = true
      this.activeTab = 'review'

      try {
        const response = await api.post(`/requirement-analysis/testcase-generation/${this.currentTaskId}/start_review/`)
        if (response.data.status === 'reviewing' || response.data.status === 'ok') {
          // 重新开启SSE接收评审内容
          this.startStreamingProgress()
        } else {
          ElMessage.error('启动评审失败：' + (response.data.error || '未知错误'))
          this.isGenerating = false
          this.stagePhase = 'generated'
          this.tabData.review.visible = false
        }
      } catch (error) {
        console.error('启动评审失败:', error)
        ElMessage.error('启动评审失败：' + (error.response?.data?.error || error.message))
        this.isGenerating = false
        this.stagePhase = 'generated'
        this.tabData.review.visible = false
      }
    },

    // 跳过评审
    skipReview() {
      this.showReviewConfirmDialog = false
      this.stagePhase = 'skip_review'
    },

    // 评审完成 → 点击"确定" → 基于评审重新生成
    async onReviewedConfirm() {
      this.stagePhase = 'revising'
      this.isGenerating = true
      this.finalTestCases = ''
      this.tabData.revise.visible = true
      this.activeTab = 'revise'

      try {
        const response = await api.post(`/requirement-analysis/testcase-generation/${this.currentTaskId}/start_revise/`)
        if (response.data.status === 'revising' || response.data.status === 'ok') {
          this.startStreamingProgress()
        } else {
          ElMessage.error('启动改进失败：' + (response.data.error || '未知错误'))
          this.isGenerating = false
          this.stagePhase = 'reviewed'
          this.tabData.revise.visible = false
        }
      } catch (error) {
        console.error('启动改进失败:', error)
        ElMessage.error('启动改进失败：' + (error.response?.data?.error || error.message))
        this.isGenerating = false
        this.stagePhase = 'reviewed'
        this.tabData.revise.visible = false
      }
    },

    // 采纳
    async onAdopt() {
      try {
        await ElMessageBox.confirm('确认采纳生成的测试用例？用例将导入到用例管理菜单。', '采纳确认', {
          confirmButtonText: '确认',
          cancelButtonText: '取消',
          type: 'info'
        })
      } catch {
        return
      }
      try {
        const response = await api.post(`/requirement-analysis/testcase-generation/${this.currentTaskId}/batch_adopt/`)
        const importedCount = response.data.imported_count || response.data.count || 0
        ElMessage.success(`已采纳 ${importedCount} 条测试用例，已导入到用例管理`)
        this.resetGeneration()
      } catch (error) {
        console.error('采纳失败:', error)
        ElMessage.error('采纳失败：' + (error.response?.data?.error || error.message))
      }
    },

    // 格式化Markdown为HTML（简化版 - 保留兼容）
    formatMarkdown(content) {
      return this.renderMarkdown(content)
    },

    formatDateTime(dateTimeString) {
      if (!dateTimeString) return '';
      const date = new Date(dateTimeString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day} ${hours}:${minutes}`;
    },

    // 格式化Markdown为HTML（简化版）
    formatMarkdown(content) {
      if (!content) return '';

      // 先去除"新增"标记，在markdown转换之前处理
      // 这样可以避免markdown转换后无法匹配的问题
      let html = content
          .replace(/\*\*新增\*\*-/g, '')  // **新增**-xxx -> xxx (保留xxx的原有格式)
          .replace(/新增-/g, '');  // 新增-xxx -> xxx (保留xxx的原有格式)

      // 转义HTML特殊字符
      html = html
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;');

      // 转换Markdown语法
      // 标题 #
      html = html.replace(/^#{6}\s+(.+)$/gm, '<h6>$1</h6>');
      html = html.replace(/^#{5}\s+(.+)$/gm, '<h5>$1</h5>');
      html = html.replace(/^#{4}\s+(.+)$/gm, '<h4>$1</h4>');
      html = html.replace(/^#{3}\s+(.+)$/gm, '<h3>$1</h3>');
      html = html.replace(/^#{2}\s+(.+)$/gm, '<h2>$1</h2>');
      html = html.replace(/^#{1}\s+(.+)$/gm, '<h1>$1</h1>');

      // 粗体 **text** 或 __text__
      html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

      // 斜体 *text* 或 _text_
      html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
      html = html.replace(/_(.+?)_/g, '<em>$1</em>');

      // 代码块 ```code```
      html = html.replace(/```([\s\S]+?)```/g, '<pre><code>$1</code></pre>');

      // 行内代码 `code`
      html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

      // 换行符转换为<br>
      html = html.replace(/\n/g, '<br>');

      return html;
    },

    // 将HTML的<br>标签转换为换行符（用于Excel导出）
    convertBrToNewline(text) {
      if (!text) return '';
      return text.replace(/<br\s*\/?>/gi, '\n');
    },

    // 过滤掉总结和建议部分，只保留测试用例内容
    filterTestCasesOnly(content) {
      if (!content) return '';

      const lines = content.split('\n');
      const filteredLines = [];
      let inTestCaseSection = true;

      for (let line of lines) {
        const trimmedLine = line.trim();

        // 检查是否到了总结或建议部分
        if (trimmedLine.includes('总结') ||
            trimmedLine.includes('建议') ||
            trimmedLine.includes('Summary') ||
            trimmedLine.includes('Recommendation') ||
            trimmedLine.includes('最后') ||
            trimmedLine.includes('补充说明')) {
          inTestCaseSection = false;
          break;
        }

        if (inTestCaseSection) {
          filteredLines.push(line);
        }
      }

      return filteredLines.join('\n');
    },

    // 解析表格格式的测试用例（参考AutoGenTestCase的做法）
    parseTableFormat(content) {
      if (!content) return [];

      const lines = content.split('\n').filter(line => line.trim());
      const worksheetData = [];

      for (let line of lines) {
        const trimmedLine = line.trim();

        // 检查是否是表格行（包含|分隔符，且不是分隔线）
        if (trimmedLine.includes('|') && !trimmedLine.includes('--------')) {
          const cells = trimmedLine.split('|').map(cell => cell.trim()).filter(cell => cell);
          if (cells.length > 1) {
            worksheetData.push(cells);
          }
        }
      }

      return worksheetData;
    },

    // 解析结构化格式的测试用例
    parseStructuredFormat(content) {
      if (!content) return [];

      const lines = content.split('\n').filter(line => line.trim());
      const worksheetData = [];

      // 添加表头
      worksheetData.push([
        this.$t('requirementAnalysis.excelTestCaseNumber'),
        this.$t('requirementAnalysis.excelTestScenario'),
        this.$t('requirementAnalysis.excelPrecondition'),
        this.$t('requirementAnalysis.excelTestSteps'),
        this.$t('requirementAnalysis.excelExpectedResult'),
        this.$t('requirementAnalysis.excelPriority')
      ]);

      let currentTestCase = {};
      let testCaseNumber = 1;
      let i = 0;

      while (i < lines.length) {
        const line = lines[i].trim();

        // 识别测试用例开始标志
        if (line.includes('测试用例') || line.includes('Test Case') ||
            line.match(/^(\d+\.|\*|\-|\d+、)/)) {

          // 如果之前有测试用例数据，先保存
          if (Object.keys(currentTestCase).length > 0) {
            worksheetData.push([
              currentTestCase.number || `TC${testCaseNumber}`,
              currentTestCase.scenario || '',
              currentTestCase.precondition || '',
              currentTestCase.steps || '',
              currentTestCase.expected || '',
              currentTestCase.priority || '中'
            ]);
            testCaseNumber++;
          }

          // 开始新的测试用例
          currentTestCase = {
            number: `TC${testCaseNumber}`,
            scenario: line.replace(/^(\d+\.|\*|\-|\d+、)\s*/, '').replace(/测试用例\d*[:：]?\s*/, ''),
            precondition: '',
            steps: '',
            expected: '',
            priority: '中'
          };
          i++;
        }
        // 识别前置条件
        else if (line.includes('前置条件') || line.includes('前提') ||
            line.includes('Precondition')) {
          let precondition = line.replace(/.*?[:：]\s*/, '');
          // 收集后续的前置条件行
          i++;
          while (i < lines.length) {
            const nextLine = lines[i].trim();
            if (nextLine.includes('测试步骤') || nextLine.includes('操作步骤') ||
                nextLine.includes('Test Steps') || nextLine.includes('步骤') ||
                nextLine.includes('预期结果') || nextLine.includes('Expected') ||
                nextLine.includes('优先级') || nextLine.includes('Priority') ||
                nextLine.includes('测试用例') || nextLine.includes('Test Case') ||
                nextLine.match(/^(\d+\.|\*|\-|\d+、)/)) {
              break;
            }
            if (nextLine) {
              precondition += '\n' + nextLine;
            }
            i++;
          }
          currentTestCase.precondition = precondition;
        }
        // 识别测试步骤
        else if (line.includes('测试步骤') || line.includes('操作步骤') ||
            line.includes('Test Steps') || line.includes('步骤')) {
          let steps = line.replace(/.*?[:：]\s*/, '');
          // 收集后续的步骤行
          i++;
          while (i < lines.length) {
            const nextLine = lines[i].trim();
            if (nextLine.includes('预期结果') || nextLine.includes('Expected') ||
                nextLine.includes('优先级') || nextLine.includes('Priority') ||
                nextLine.includes('测试用例') || nextLine.includes('Test Case') ||
                nextLine.match(/^(\d+\.|\*|\-|\d+、)/)) {
              break;
            }
            if (nextLine) {
              steps += '\n' + nextLine;
            }
            i++;
          }
          currentTestCase.steps = steps;
        }
        // 识别预期结果
        else if (line.includes('预期结果') || line.includes('Expected') ||
            line.includes('期望')) {
          let expected = line.replace(/.*?[:：]\s*/, '');
          // 收集后续的结果行
          i++;
          while (i < lines.length) {
            const nextLine = lines[i].trim();
            if (nextLine.includes('优先级') || nextLine.includes('Priority') ||
                nextLine.includes('测试用例') || nextLine.includes('Test Case') ||
                nextLine.match(/^(\d+\.|\*|\-|\d+、)/)) {
              break;
            }
            if (nextLine) {
              expected += '\n' + nextLine;
            }
            i++;
          }
          currentTestCase.expected = expected;
        }
        // 识别优先级
        else if (line.includes('优先级') || line.includes('Priority')) {
          currentTestCase.priority = line.replace(/.*?[:：]\s*/, '');
          i++;
        }
        // 如果是没有明确标识的行，可能是场景描述的延续
        else if (Object.keys(currentTestCase).length > 0 &&
            !currentTestCase.steps && !currentTestCase.expected &&
            !currentTestCase.precondition) {
          if (currentTestCase.scenario && line.length > 5) {
            currentTestCase.scenario += '\n' + line;
          }
          i++;
        } else {
          i++;
        }
      }

      // 保存最后一个测试用例
      if (Object.keys(currentTestCase).length > 0) {
        worksheetData.push([
          currentTestCase.number || `TC${testCaseNumber}`,
          currentTestCase.scenario || '',
          currentTestCase.precondition || '',
          currentTestCase.steps || '',
          currentTestCase.expected || '',
          currentTestCase.priority || '中'
        ]);
      }

      // 如果没有解析到结构化数据，则按原格式输出
      if (worksheetData.length <= 1) {
        worksheetData.length = 0; // 清空
        worksheetData.push([this.$t('requirementAnalysis.testCaseContent')]);
        content.split('\n').forEach((line, index) => {
          if (line.trim()) {
            worksheetData.push([line.trim()]);
          }
        });
      }

      return worksheetData;
    }
  }
}
</script>

<style scoped>
.requirement-analysis {
  padding: 0;
  margin: 0;
  position: relative;
  height: 100%;
  overflow: hidden;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.page-header {
  padding: 16px 20px 0;
  flex-shrink: 0;
}

.page-header h1 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0;
}

/* === 工作区：左右分栏 === */
.workspace {
  flex: 1;
  min-height: 0;
  display: flex;
  padding: 12px;
  gap: 0;
  width: 100%;
}

/* === 左栏 === */
.left-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 300px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.task-input-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: auto;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 12px;
}

.section-bar {
  width: 3px;
  height: 16px;
  background: #4f6ef7;
  border-radius: 2px;
}

.form-label {
  display: block;
  font-size: 13px;
  color: #475569;
  margin-bottom: 6px;
  font-weight: 500;
}

.title-input {
  font-size: 14px !important;
  font-weight: 500;
  border: 1px solid #e2e8f0 !important;
  border-radius: 8px !important;
  padding: 10px 12px !important;
  background: #f8fafc !important;
  margin-bottom: 8px;
}

.title-input:focus {
  border-color: #4f6ef7 !important;
  box-shadow: 0 0 0 2px rgba(79, 110, 247, 0.1) !important;
}

.main-textarea {
  flex: 1;
  min-height: 120px;
  resize: none !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 8px !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  padding: 10px 12px !important;
  background: #f8fafc !important;
}

.main-textarea:focus {
  border-color: #4f6ef7 !important;
  box-shadow: 0 0 0 2px rgba(79, 110, 247, 0.1) !important;
}

.main-textarea::placeholder {
  color: #94a3b8;
}

.char-count-bottom {
  text-align: right;
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}

/* 左栏底部工具栏 */
.left-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid #f1f5f9;
  background: #fafbfc;
  flex-shrink: 0;
}

.left-toolbar .toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.project-select {
  width: 140px;
  height: 32px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 0 8px;
  font-size: 13px;
  color: #475569;
  background: white;
  cursor: pointer;
}

.upload-inline {
  display: flex;
  align-items: center;
  gap: 4px;
}

.upload-btn-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px dashed #cbd5e1;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 13px;
  color: #64748b;
  transition: all 0.2s;
}

.upload-btn-inline:hover {
  border-color: #4f6ef7;
  color: #4f6ef7;
}

.file-name-inline {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-file-inline {
  background: none;
  border: none;
  color: #ef4444;
  cursor: pointer;
  font-size: 14px;
  padding: 2px 4px;
}

.generate-btn {
  height: 32px;
  padding: 0 20px;
  background: #4f6ef7;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}

.generate-btn:hover:not(:disabled) {
  background: #3b5de7;
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 左栏提示 */
.left-tip {
  padding: 12px 16px;
  border-top: 1px solid #f1f5f9;
  background: #fafbfc;
  flex-shrink: 0;
}

.tip-title {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 4px;
}

.tip-text {
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.5;
}

/* === 拖拽分隔条 === */
.resize-handle {
  width: 6px;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s;
  position: relative;
  z-index: 5;
}

.resize-handle:hover {
  background: rgba(79, 110, 247, 0.08);
}

.resize-line {
  width: 2px;
  height: 40px;
  background: #cbd5e1;
  border-radius: 1px;
  transition: background 0.2s;
}

.resize-handle:hover .resize-line {
  background: #4f6ef7;
}

/* === 右栏 === */
.right-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 300px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

/* === 页签栏 === */
.stage-tabs {
  display: flex;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  padding: 0 8px;
}

.stage-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  font-size: 13px;
  color: #94a3b8;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  white-space: nowrap;
  user-select: none;
}

.stage-tab:hover:not(.disabled) {
  color: #475569;
}

.stage-tab.active {
  color: #4f6ef7;
  font-weight: 600;
  border-bottom-color: #4f6ef7;
}

.stage-tab.completed {
  color: #475569;
}

.stage-tab.disabled {
  color: #d1d5db;
  cursor: not-allowed;
}

.tab-step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 600;
  background: #e2e8f0;
  color: #94a3b8;
  flex-shrink: 0;
}

.stage-tab.active .tab-step {
  background: #4f6ef7;
  color: white;
}

.stage-tab.completed .tab-step {
  background: #10b981;
  color: white;
}

.stage-tab.disabled .tab-step {
  background: #f1f5f9;
  color: #d1d5db;
}

.tab-done {
  color: #10b981;
  font-size: 14px;
  font-weight: 700;
}

/* === 页签内容区 === */
.stage-content {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.stage-body {
  padding: 16px;
}

.output-section {
  flex: 1;
  min-height: 0;
  padding: 16px;
  overflow: auto;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #94a3b8;
  font-size: 14px;
}

.streaming-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: 12px;
  padding: 2px 10px;
  background: #ecfdf5;
  color: #059669;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  line-height: 20px;
  white-space: nowrap;
  animation: tag-pulse 1.5s ease-in-out infinite;
}

.streaming-tag::before {
  content: '';
  width: 6px;
  height: 6px;
  background: #10b981;
  border-radius: 50%;
  animation: dot-blink 1s ease-in-out infinite;
}

@keyframes dot-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes tag-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.85; }
}

/* 输出块 */
.output-block {
  margin-bottom: 16px;
}

.output-block-title {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #f1f5f9;
}

.review-block .output-block-title {
  color: #f59e0b;
}

.final-block .output-block-title {
  color: #10b981;
}

/* Markdown 渲染样式 */
.markdown-body {
  font-size: 14px;
  line-height: 1.7;
  color: #334155;
  word-wrap: break-word;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  margin-top: 16px;
  margin-bottom: 8px;
  font-weight: 600;
  color: #1a202c;
}

.markdown-body :deep(h1) { font-size: 1.4em; }
.markdown-body :deep(h2) { font-size: 1.25em; }
.markdown-body :deep(h3) { font-size: 1.1em; }
.markdown-body :deep(h4) { font-size: 1em; }

.markdown-body :deep(p) {
  margin: 0 0 8px 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0 0 8px 0;
  padding-left: 24px;
}

.markdown-body :deep(li) {
  margin-bottom: 4px;
}

.markdown-body :deep(strong) {
  font-weight: 600;
  color: #1a202c;
}

.markdown-body :deep(code) {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  color: #e11d48;
}

.markdown-body :deep(pre) {
  background: #1e293b;
  color: #e2e8f0;
  padding: 12px 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
  font-size: 13px;
  line-height: 1.5;
}

.markdown-body :deep(pre code) {
  background: none;
  color: inherit;
  padding: 0;
  font-size: inherit;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 13px;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #e2e8f0;
  padding: 8px 12px;
  text-align: left;
}

.markdown-body :deep(th) {
  background: #f8fafc;
  font-weight: 600;
  color: #1a202c;
}

.markdown-body :deep(blockquote) {
  margin: 8px 0;
  padding: 8px 16px;
  border-left: 3px solid #4f6ef7;
  background: #f8fafc;
  color: #475569;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 12px 0;
}

/* 右栏底部操作 */
.right-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #f1f5f9;
  background: #fafbfc;
  flex-shrink: 0;
}

.action-btn {
  height: 32px;
  padding: 0 20px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.primary {
  background: #4f6ef7;
  color: white;
}

.action-btn.primary:hover {
  background: #3b5de7;
}

.action-btn.success {
  background: #10b981;
  color: white;
}

.action-btn.success:hover {
  background: #059669;
}

.action-btn.cancel {
  background: white;
  color: #64748b;
  border: 1px solid #e2e8f0;
}

.action-btn.cancel:hover {
  background: #f8fafc;
}

.action-btn.download {
  background: white;
  color: #4f6ef7;
  border: 1px solid #4f6ef7;
}

.action-btn.download:hover {
  background: rgba(79, 110, 247, 0.05);
}

/* === 弹窗样式 === */
.output-mode-dialog {
  background: white;
  border-radius: 16px;
  padding: 24px;
  max-width: 480px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.dialog-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a202c;
  margin: 0 0 8px;
}

.dialog-desc {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 16px;
}

.mode-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.mode-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-option:hover {
  border-color: #4f6ef7;
}

.mode-option.active {
  border-color: #4f6ef7;
  background: rgba(79, 110, 247, 0.04);
}

.mode-option input[type="radio"] {
  margin-top: 2px;
  accent-color: #4f6ef7;
}

.mode-content {
  flex: 1;
}

.mode-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 2px;
}

.mode-desc {
  font-size: 12px;
  color: #64748b;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.dialog-cancel {
  height: 36px;
  padding: 0 20px;
  background: white;
  color: #64748b;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.dialog-confirm {
  height: 36px;
  padding: 0 20px;
  background: #4f6ef7;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.dialog-confirm:hover {
  background: #3b5de7;
}

/* === 配置引导弹窗 === */
.config-groups {
  margin-bottom: 16px;
}

.config-group {
  margin-bottom: 12px;
}

.group-label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
}

.config-items-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.config-item-inline {
  flex: 1;
  min-width: 200px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  font-size: 13px;
}

.config-item-inline.configured {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.04);
}

.config-item-inline.not-configured {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.04);
}

.config-label {
  font-weight: 500;
  color: #1a202c;
}

.config-name {
  color: #10b981;
  font-size: 12px;
}

.status-text {
  font-size: 12px;
  color: #f59e0b;
}

.status-text.warning {
  color: #ef4444;
}

.guide-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
}

.guide-actions button {
  width: 240px;
  height: 44px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.guide-actions .generate-manual-btn {
  background: #4f6ef7;
  color: white;
  border: none;
}

.skip-action {
  font-size: 13px;
  color: #94a3b8;
  cursor: pointer;
}

.skip-action:hover {
  color: #64748b;
}

.guide-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.guide-icon {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
}

.guide-title h2 {
  font-size: 16px;
  color: #1a202c;
  margin: 0 0 4px;
}

.guide-title p {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}

.status-symbol {
  font-size: 16px;
}
</style>

<style>
/* 全局样式：确保弹窗不受任何容器限制 */
.modal-overlay {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  max-width: none !important;
  max-height: none !important;
  background: rgba(15, 23, 42, 0.6) !important;
  backdrop-filter: blur(4px);
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 9999 !important;
  padding: 20px;
  margin: 0 !important;
  opacity: 1 !important;
  box-sizing: border-box !important;
}

.guide-config-modal {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
  border-radius: 24px;
  padding: 36px;
  max-width: 850px !important;
  width: 100% !important;
  min-width: 300px !important;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(226, 232, 240, 0.8);
  position: relative;
  flex-shrink: 0;
  margin: auto;
  opacity: 1 !important;
  box-sizing: border-box !important;
}

/* 全局按钮样式 */
.guide-actions {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  gap: 12px;
  margin-top: 30px;
  width: 100%;
}

.guide-actions button {
  flex: none !important;
  width: 240px !important;
  height: 50px !important;
  padding: 0 24px !important;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  text-align: center;
  white-space: nowrap;
  opacity: 1 !important;
  box-sizing: border-box !important;
  cursor: pointer;
}

.guide-actions .generate-manual-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white !important;
  border: 2px solid transparent !important;
  box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
}

.guide-actions .skip-action {
  font-size: 0.85rem;
  color: #94a3b8;
  cursor: pointer;
  text-decoration: none;
  padding: 4px 8px;
  transition: color 0.3s;
}

.guide-actions .skip-action:hover {
  color: #64748b;
  text-decoration: underline;
}
</style>