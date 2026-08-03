<template>
  <div class="midscene-config">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>Midscene 配置</h1>
      <p>管理 Midscene AI视觉自动化引擎的全局配置，支持 Web / Android / iOS / HarmonyOS 多端配置</p>
    </div>

    <!-- 配置列表区 -->
    <div class="config-section">
      <div class="section-header">
        <h2>配置列表</h2>
        <div class="header-actions">
          <el-select
            v-model="filterDeviceType"
            placeholder="设备类型筛选"
            clearable
            size="default"
            style="width: 160px"
            @change="loadConfigs"
          >
            <el-option label="Web端" value="web" />
            <el-option label="Android" value="android" />
            <el-option label="iOS" value="ios" />
            <el-option label="HarmonyOS" value="harmony" />
          </el-select>
          <el-button type="primary" @click="openAddModal">
            <el-icon><Plus /></el-icon>添加
          </el-button>
        </div>
      </div>

      <!-- 配置卡片网格 -->
      <div v-if="configs.length > 0" class="configs-grid">
        <div v-for="config in configs" :key="config.id" class="config-card">
          <div class="config-card__header">
            <div class="config-card__title-row">
              <h3 class="config-card__name">{{ config.name || '未命名配置' }}</h3>
              <div class="config-card__badges">
                <span class="device-badge" :class="'device-badge--' + config.device_type">
                  {{ deviceTypeLabel(config.device_type) }}
                </span>
                <span class="status-badge" :class="{ 'status-badge--active': config.is_active }">
                  {{ config.is_active ? '启用' : '禁用' }}
                </span>
              </div>
            </div>
            <div class="config-card__actions">
              <el-switch v-model="config.is_active" @change="toggleActive(config)" />
              <el-button text type="primary" size="small" @click="editConfig(config)">编辑</el-button>
              <el-button text type="danger" size="small" @click="deleteConfig(config.id)">删除</el-button>
            </div>
          </div>
          <div class="config-card__body">
            <div v-if="config.ai_model_config && summarizeModelConfig(config.ai_model_config) !== '-'" class="detail-row">
              <span class="detail-label">AI模型</span>
              <span class="detail-value">{{ summarizeModelConfig(config.ai_model_config) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">创建时间</span>
              <span class="detail-value">{{ formatDateTime(config.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="configs.length === 0 && !loading" class="empty-state">
        <el-icon :size="48" color="#c0c4cc"><Document /></el-icon>
        <h3>暂无 Midscene 配置</h3>
        <p>请添加 Midscene 全局配置以启用 AI 视觉自动化引擎</p>
        <el-button type="primary" @click="openAddModal">添加第一个配置</el-button>
      </div>
    </div>

    <!-- 添加/编辑配置弹窗 -->
    <el-dialog
      v-model="showModal"
      :title="isEditing ? '编辑 Midscene 配置' : '添加 Midscene 配置'"
      width="720px"
      :close-on-click-modal="false"
      destroy-on-close
      class="midscene-config-dialog"
    >
      <el-form ref="formRef" :model="form" label-width="130px" label-position="left">
        <!-- 基础配置 -->
        <el-form-item label="配置名称" required>
          <el-input v-model="form.name" placeholder="例如：Web端默认配置" />
        </el-form-item>
        <el-form-item label="设备类型" required>
          <el-select v-model="form.device_type" placeholder="选择设备类型" style="width: 100%">
            <el-option label="Web端" value="web" />
            <el-option label="Android" value="android" />
            <el-option label="iOS" value="ios" />
            <el-option label="HarmonyOS" value="harmony" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>

        <!-- AI 模型配置 -->
        <el-divider content-position="left">AI 模型配置</el-divider>
        <p class="section-tip">三级意图模型：Default（默认）、Insight（定位）、Planning（规划）。留空表示使用 Midscene 内置默认。</p>

        <el-form-item label="Default 模型">
          <div class="model-row">
            <el-input v-model="form.ai_model_config.default.modelProvider" placeholder="modelProvider (如 openai)" style="flex:1" />
            <el-input v-model="form.ai_model_config.default.modelName" placeholder="modelName (如 gpt-4o)" style="flex:1" />
          </div>
        </el-form-item>
        <el-form-item label="Insight 模型">
          <div class="model-row">
            <el-input v-model="form.ai_model_config.insight.modelProvider" placeholder="modelProvider" style="flex:1" />
            <el-input v-model="form.ai_model_config.insight.modelName" placeholder="modelName" style="flex:1" />
          </div>
        </el-form-item>
        <el-form-item label="Planning 模型">
          <div class="model-row">
            <el-input v-model="form.ai_model_config.planning.modelProvider" placeholder="modelProvider" style="flex:1" />
            <el-input v-model="form.ai_model_config.planning.modelName" placeholder="modelName" style="flex:1" />
          </div>
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.ai_model_config.default.apiKey" type="password" show-password placeholder="AI模型 API Key（必填）" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="form.ai_model_config.default.baseURL" placeholder="AI模型 API 地址（如 https://api.openai.com/v1）" />
        </el-form-item>

        <!-- 执行配置 -->
        <el-divider content-position="left">执行配置</el-divider>
        <el-form-item label="操作后等待(ms)">
          <el-input-number v-model="form.execution_config.waitAfterAction" :min="0" :max="30000" :step="100" />
        </el-form-item>
        <el-form-item label="截图缩放因子">
          <el-input-number v-model="form.execution_config.screenshotShrinkFactor" :min="0.1" :max="1" :step="0.1" :precision="1" />
        </el-form-item>
        <el-form-item label="重规划限制">
          <el-input-number v-model="form.execution_config.replanningCycleLimit" :min="1" :max="20" :step="1" />
        </el-form-item>

        <!-- 报告配置 -->
        <el-divider content-position="left">报告配置</el-divider>
        <el-form-item label="生成报告">
          <el-switch v-model="form.report_config.generateReport" />
        </el-form-item>
        <el-form-item label="自动打印报告">
          <el-switch v-model="form.report_config.autoPrintReportMsg" />
          <span class="form-item-hint">（截图截断）</span>
        </el-form-item>

        <!-- Web 端配置 -->
        <template v-if="form.device_type === 'web'">
          <el-divider content-position="left">Web 端配置</el-divider>
          <el-form-item label="浏览器路径">
            <el-input v-model="form.web_config.browserPath" placeholder="可选，指定浏览器可执行文件路径" />
          </el-form-item>
          <el-form-item label="视口宽度">
            <el-input-number v-model="form.web_config.viewportWidth" :min="800" :max="3840" :step="10" />
          </el-form-item>
          <el-form-item label="视口高度">
            <el-input-number v-model="form.web_config.viewportHeight" :min="600" :max="2160" :step="10" />
          </el-form-item>
          <el-form-item label="无头模式">
            <el-switch v-model="form.web_config.headless" />
          </el-form-item>
        </template>

        <!-- Android 配置 -->
        <template v-if="form.device_type === 'android'">
          <el-divider content-position="left">Android 配置</el-divider>
          <el-form-item label="ADB路径">
            <el-input v-model="form.android_config.androidAdbPath" placeholder="可选，默认使用系统 adb" />
          </el-form-item>
          <el-form-item label="远程ADB主机">
            <el-input v-model="form.android_config.remoteAdbHost" placeholder="可选" />
          </el-form-item>
          <el-form-item label="远程ADB端口">
            <el-input-number v-model="form.android_config.remoteAdbPort" :min="0" :max="65535" />
          </el-form-item>
          <el-form-item label="输入法策略">
            <el-select v-model="form.android_config.imeStrategy" placeholder="选择输入法策略">
              <el-option label="默认" value="" />
              <el-option label="ADB 输入法" value="adb" />
              <el-option label="YADB 输入法" value="yadb" />
            </el-select>
          </el-form-item>
        </template>

        <!-- iOS 配置 -->
        <template v-if="form.device_type === 'ios'">
          <el-divider content-position="left">iOS 配置</el-divider>
          <el-form-item label="WDA 端口">
            <el-input-number v-model="form.ios_config.wdaPort" :min="0" :max="65535" />
          </el-form-item>
          <el-form-item label="WDA 主机">
            <el-input v-model="form.ios_config.wdaHost" placeholder="可选" />
          </el-form-item>
          <el-form-item label="MJPEG 端口">
            <el-input-number v-model="form.ios_config.wdaMjpegPort" :min="0" :max="65535" />
          </el-form-item>
        </template>

        <!-- HarmonyOS 配置 -->
        <template v-if="form.device_type === 'harmony'">
          <el-divider content-position="left">HarmonyOS 配置</el-divider>
          <el-form-item label="HDC 路径">
            <el-input v-model="form.harmony_config.hdcPath" placeholder="可选，指定 hdc 工具路径" />
          </el-form-item>
          <el-form-item label="键盘收起策略">
            <el-select v-model="form.harmony_config.dismissKeyboardStrategy" placeholder="选择策略">
              <el-option label="ESC 优先" value="esc-first" />
              <el-option label="返回优先" value="back-first" />
            </el-select>
          </el-form-item>
        </template>

        <!-- App名称映射 -->
        <template v-if="['android', 'ios', 'harmony'].includes(form.device_type)">
          <el-divider content-position="left">App 名称映射</el-divider>
          <p class="section-tip">将应用中文名映射到包名/bundle名，如: {"微信": "com.tencent.mm"}</p>
          <el-form-item label="名称映射">
            <el-input v-model="form.app_name_mapping_text" type="textarea" :rows="3" placeholder='{"微信": "com.tencent.mm", "支付宝": "com.eg.android.AlipayGphone"}' />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="showModal = false">取消</el-button>
        <el-button type="primary" :loading="isSaving" @click="saveConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Plus } from '@element-plus/icons-vue'
import {
  getMidsceneConfigs,
  createMidsceneConfig,
  updateMidsceneConfig,
  deleteMidsceneConfig
} from '@/api/ui_automation'

const configs = ref([])
const loading = ref(false)
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const isSaving = ref(false)
const filterDeviceType = ref('')

const createEmptyForm = () => ({
  name: '',
  device_type: 'web',
  is_active: true,
  ai_model_config: {
    default: { modelProvider: '', modelName: '', apiKey: '', baseURL: '' },
    insight: { modelProvider: '', modelName: '', apiKey: '', baseURL: '' },
    planning: { modelProvider: '', modelName: '', apiKey: '', baseURL: '' }
  },
  execution_config: { waitAfterAction: 1000, screenshotShrinkFactor: 1, replanningCycleLimit: 5 },
  report_config: { generateReport: true, autoPrintReportMsg: true },
  web_config: { browserPath: '', viewportWidth: 1280, viewportHeight: 720, headless: true },
  android_config: { androidAdbPath: '', remoteAdbHost: '', remoteAdbPort: 0, imeStrategy: '' },
  ios_config: { wdaPort: 8100, wdaHost: '', wdaMjpegPort: 9100 },
  harmony_config: { hdcPath: '', dismissKeyboardStrategy: 'esc-first' },
  app_name_mapping_text: ''
})

const form = reactive(createEmptyForm())

const deviceTypeLabel = (type) => {
  const map = { web: 'Web端', android: 'Android', ios: 'iOS', harmony: 'HarmonyOS' }
  return map[type] || type
}

const formatDateTime = (dt) => {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN')
}

const summarizeModelConfig = (config) => {
  if (!config) return '-'
  const parts = []
  if (config.default?.modelName) parts.push(`默认: ${config.default.modelName}`)
  if (config.insight?.modelName) parts.push(`定位: ${config.insight.modelName}`)
  if (config.planning?.modelName) parts.push(`规划: ${config.planning.modelName}`)
  return parts.join(' / ') || '-'
}

const loadConfigs = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterDeviceType.value) params.device_type = filterDeviceType.value
    const response = await getMidsceneConfigs(params)
    configs.value = Array.isArray(response.data) ? response.data : []
  } catch (error) {
    console.error('加载 Midscene 配置失败:', error)
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

const openAddModal = () => {
  Object.assign(form, createEmptyForm())
  isEditing.value = false
  editingId.value = null
  showModal.value = true
}

const editConfig = (config) => {
  isEditing.value = true
  editingId.value = config.id

  const aiModel = config.ai_model_config || {}
  const exec = config.execution_config || {}
  const report = config.report_config || {}
  const web = config.web_config || {}
  const android = config.android_config || {}
  const ios = config.ios_config || {}
  const harmony = config.harmony_config || {}
  const appMapping = config.app_name_mapping || {}

  form.name = config.name || ''
  form.device_type = config.device_type || 'web'
  form.is_active = config.is_active ?? true

  form.ai_model_config = {
    default: { modelProvider: aiModel.default?.modelProvider || '', modelName: aiModel.default?.modelName || '', apiKey: '********', baseURL: aiModel.default?.baseURL || '' },
    insight: { modelProvider: aiModel.insight?.modelProvider || '', modelName: aiModel.insight?.modelName || '', apiKey: aiModel.insight?.apiKey || '', baseURL: aiModel.insight?.baseURL || '' },
    planning: { modelProvider: aiModel.planning?.modelProvider || '', modelName: aiModel.planning?.modelName || '', apiKey: aiModel.planning?.apiKey || '', baseURL: aiModel.planning?.baseURL || '' }
  }
  form.execution_config = { waitAfterAction: exec.waitAfterAction ?? 1000, screenshotShrinkFactor: exec.screenshotShrinkFactor ?? 1, replanningCycleLimit: exec.replanningCycleLimit ?? 5 }
  form.report_config = { generateReport: report.generateReport ?? true, autoPrintReportMsg: report.autoPrintReportMsg ?? true }
  form.web_config = { browserPath: web.browserPath || '', viewportWidth: web.viewportWidth || 1280, viewportHeight: web.viewportHeight || 720, headless: web.headless ?? true }
  form.android_config = { androidAdbPath: android.androidAdbPath || '', remoteAdbHost: android.remoteAdbHost || '', remoteAdbPort: android.remoteAdbPort || 0, imeStrategy: android.imeStrategy || '' }
  form.ios_config = { wdaPort: ios.wdaPort || 8100, wdaHost: ios.wdaHost || '', wdaMjpegPort: ios.wdaMjpegPort || 9100 }
  form.harmony_config = { hdcPath: harmony.hdcPath || '', dismissKeyboardStrategy: harmony.dismissKeyboardStrategy || 'esc-first' }
  form.app_name_mapping_text = Object.keys(appMapping).length ? JSON.stringify(appMapping, null, 2) : ''

  showModal.value = true
}

const saveConfig = async () => {
  if (!form.name.trim()) {
    ElMessage.error('请输入配置名称')
    return
  }

  isSaving.value = true
  try {
    const buildModelEntry = (entry) => {
      const result = {}
      if (entry.modelProvider) result.modelProvider = entry.modelProvider
      if (entry.modelName) result.modelName = entry.modelName
      if (entry.apiKey && !entry.apiKey.includes('*')) result.apiKey = entry.apiKey
      if (entry.baseURL) result.baseURL = entry.baseURL
      return result
    }

    const aiModelConfig = {}
    const defaultEntry = buildModelEntry(form.ai_model_config.default)
    if (Object.keys(defaultEntry).length) aiModelConfig.default = defaultEntry
    const insightEntry = buildModelEntry(form.ai_model_config.insight)
    if (Object.keys(insightEntry).length) aiModelConfig.insight = insightEntry
    const planningEntry = buildModelEntry(form.ai_model_config.planning)
    if (Object.keys(planningEntry).length) aiModelConfig.planning = planningEntry

    let appMapping = {}
    if (form.app_name_mapping_text?.trim()) {
      try {
        appMapping = JSON.parse(form.app_name_mapping_text)
      } catch {
        ElMessage.error('App名称映射格式不正确，请输入合法 JSON')
        isSaving.value = false
        return
      }
    }

    const data = {
      name: form.name,
      device_type: form.device_type,
      is_active: form.is_active,
      ai_model_config: aiModelConfig,
      execution_config: { waitAfterAction: form.execution_config.waitAfterAction, screenshotShrinkFactor: form.execution_config.screenshotShrinkFactor, replanningCycleLimit: form.execution_config.replanningCycleLimit },
      report_config: { generateReport: form.report_config.generateReport, autoPrintReportMsg: form.report_config.autoPrintReportMsg },
      web_config: form.device_type === 'web' ? { browserPath: form.web_config.browserPath, viewportWidth: form.web_config.viewportWidth, viewportHeight: form.web_config.viewportHeight, headless: form.web_config.headless } : {},
      android_config: form.device_type === 'android' ? form.android_config : {},
      ios_config: form.device_type === 'ios' ? form.ios_config : {},
      harmony_config: form.device_type === 'harmony' ? form.harmony_config : {},
      app_name_mapping: appMapping
    }

    if (isEditing.value) {
      await updateMidsceneConfig(editingId.value, data)
      ElMessage.success('配置更新成功')
    } else {
      await createMidsceneConfig(data)
      ElMessage.success('配置创建成功')
    }
    showModal.value = false
    await loadConfigs()
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error(error.response?.data?.error || '保存失败')
  } finally {
    isSaving.value = false
  }
}

const toggleActive = async (config) => {
  try {
    await updateMidsceneConfig(config.id, { is_active: config.is_active })
    ElMessage.success(config.is_active ? '已启用' : '已禁用')
  } catch (error) {
    console.error('切换状态失败:', error)
    config.is_active = !config.is_active
    ElMessage.error('操作失败')
  }
}

const deleteConfig = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除此配置吗？', '删除确认', { type: 'warning' })
    await deleteMidsceneConfig(id)
    ElMessage.success('删除成功')
    await loadConfigs()
  } catch {
    // 取消删除
  }
}

onMounted(() => {
  loadConfigs()
})
</script>

<style lang="scss" scoped>
.midscene-config {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 页面头部 */
.page-header {
  flex-shrink: 0;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 22px;
  font-weight: 600;
  color: var(--gray-900, #1f2937);
  margin: 0 0 6px 0;
}

.page-header p {
  font-size: 14px;
  color: var(--gray-500, #6b7280);
  margin: 0;
}

/* 配置列表区 */
.config-section {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-800, #374151);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 配置卡片网格 */
.configs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
  gap: 16px;
}

.config-card {
  background: var(--gray-0, #fff);
  border: 1px solid var(--gray-200, #e5e7eb);
  border-radius: 8px;
  padding: 16px 20px;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.config-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-color: var(--gray-300, #d1d5db);
}

.config-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.config-card__name {
  font-size: 15px;
  font-weight: 600;
  color: var(--gray-900, #1f2937);
  margin: 0 0 8px 0;
}

.config-card__badges {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* 设备类型 badge */
.device-badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 500;
  line-height: 1.6;
}

.device-badge--web {
  background: #e0f2fe;
  color: #0369a1;
}

.device-badge--android {
  background: #dcfce7;
  color: #16a34a;
}

.device-badge--ios {
  background: #f0f0ff;
  color: #6366f1;
}

.device-badge--harmony {
  background: #fef3c7;
  color: #d97706;
}

/* 启用/禁用 badge */
.status-badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 500;
  line-height: 1.6;
  background: #f3f4f6;
  color: #9ca3af;
}

.status-badge--active {
  background: #dcfce7;
  color: #16a34a;
}

.config-card__actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

/* 卡片详情区 */
.config-card__body {
  border-top: 1px solid var(--gray-100, #f3f4f6);
  padding-top: 10px;
}

.detail-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 13px;
  color: var(--gray-500, #6b7280);
  margin-bottom: 4px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-weight: 500;
  color: var(--gray-700, #374151);
  flex-shrink: 0;
}

.detail-value {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 48px 0;
  color: #9ca3af;
}

.empty-state h3 {
  font-size: 16px;
  color: var(--gray-600, #6b7280);
  margin: 16px 0 8px;
}

.empty-state p {
  font-size: 14px;
  margin: 0 0 20px;
}

/* 弹窗内样式 */
.section-tip {
  font-size: 12px;
  color: var(--gray-400, #9ca3af);
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.model-row {
  display: flex;
  gap: 8px;
  width: 100%;
}

.form-item-hint {
  margin-left: 8px;
  font-size: 12px;
  color: var(--gray-400, #9ca3af);
}

:deep(.el-divider__text) {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-700, #374151);
}

/* 弹窗自定义 */
:deep(.midscene-config-dialog .el-dialog__body) {
  padding: 16px 20px;
  max-height: 65vh;
  overflow-y: auto;
}
</style>
