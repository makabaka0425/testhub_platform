<template>
  <div class="page-container">
    <!-- 页面说明 -->
    <div class="page-info">
      <h1 class="page-title">{{ $t('uiAutomation.notification.configs.pageTitle') }}</h1>
      <p class="page-desc">{{ $t('uiAutomation.notification.configs.pageDesc') }}</p>
    </div>

    <!-- Tab切换 -->
    <div class="card-container">
      <el-tabs v-model="activeTab" class="notification-tabs">

        <!-- 飞书机器人Tab -->
        <el-tab-pane :label="$t('uiAutomation.notification.configs.feishuBot')" name="feishu">
          <div class="tab-content">
            <div class="config-section">
              <el-form
                  ref="feishuFormRef"
                  :model="webhookBots.feishu"
                  label-position="top"
                  class="config-form"
              >
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item :label="$t('uiAutomation.notification.configs.botName')">
                      <el-input
                          v-model="webhookBots.feishu.name"
                          :placeholder="$t('uiAutomation.notification.configs.feishuBotNamePlaceholder')"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item :label="$t('uiAutomation.notification.configs.enable')">
                      <el-switch v-model="webhookBots.feishu.enabled"/>
                    </el-form-item>
                  </el-col>
                  <el-col :span="24">
                    <el-form-item :label="$t('uiAutomation.notification.configs.webhookUrl')">
                      <el-input
                          v-model="webhookBots.feishu.webhook_url"
                          :placeholder="$t('uiAutomation.notification.configs.webhookPlaceholder')"
                      />
                      <div class="form-item-hint">
                        {{ $t('uiAutomation.notification.configs.feishuUrlHint') }}
                      </div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="24">
                    <el-form-item :label="$t('uiAutomation.notification.configs.businessType')">
                      <el-checkbox v-model="webhookBots.feishu.enable_ui_automation">{{ $t('uiAutomation.notification.configs.uiAutomationTest') }}</el-checkbox>
                      <el-checkbox v-model="webhookBots.feishu.enable_api_testing">{{ $t('uiAutomation.notification.configs.apiTest') }}</el-checkbox>
                    </el-form-item>
                  </el-col>
                </el-row>

                <div class="form-actions">
                  <el-button type="primary" @click="saveWebhookBot('feishu')">
                    {{ $t('uiAutomation.notification.configs.saveFeishuConfig') }}
                  </el-button>
                </div>
              </el-form>
            </div>
          </div>
        </el-tab-pane>

        <!-- 企业微信机器人Tab -->
        <el-tab-pane :label="$t('uiAutomation.notification.configs.wechatBot')" name="wechat">
          <div class="tab-content">
            <div class="config-section">
              <el-form
                  ref="wechatFormRef"
                  :model="webhookBots.wechat"
                  label-position="top"
                  class="config-form"
              >
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item :label="$t('uiAutomation.notification.configs.botName')">
                      <el-input
                          v-model="webhookBots.wechat.name"
                          :placeholder="$t('uiAutomation.notification.configs.wechatBotNamePlaceholder')"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item :label="$t('uiAutomation.notification.configs.enable')">
                      <el-switch v-model="webhookBots.wechat.enabled"/>
                    </el-form-item>
                  </el-col>
                  <el-col :span="24">
                    <el-form-item :label="$t('uiAutomation.notification.configs.webhookUrl')">
                      <el-input
                          v-model="webhookBots.wechat.webhook_url"
                          :placeholder="$t('uiAutomation.notification.configs.webhookPlaceholder')"
                      />
                      <div class="form-item-hint">
                        {{ $t('uiAutomation.notification.configs.wechatUrlHint') }}
                      </div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="24">
                    <el-form-item :label="$t('uiAutomation.notification.configs.businessType')">
                      <el-checkbox v-model="webhookBots.wechat.enable_ui_automation">{{ $t('uiAutomation.notification.configs.uiAutomationTest') }}</el-checkbox>
                      <el-checkbox v-model="webhookBots.wechat.enable_api_testing">{{ $t('uiAutomation.notification.configs.apiTest') }}</el-checkbox>
                    </el-form-item>
                  </el-col>
                </el-row>

                <div class="form-actions">
                  <el-button type="primary" @click="saveWebhookBot('wechat')">
                    {{ $t('uiAutomation.notification.configs.saveWechatConfig') }}
                  </el-button>
                </div>
              </el-form>
            </div>
          </div>
        </el-tab-pane>

        <!-- 钉钉机器人Tab -->
        <el-tab-pane :label="$t('uiAutomation.notification.configs.dingtalkBot')" name="dingtalk">
          <div class="tab-content">
            <div class="config-section">
              <el-form
                  ref="dingtalkFormRef"
                  :model="webhookBots.dingtalk"
                  label-position="top"
                  class="config-form"
              >
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item :label="$t('uiAutomation.notification.configs.botName')">
                      <el-input
                          v-model="webhookBots.dingtalk.name"
                          :placeholder="$t('uiAutomation.notification.configs.dingtalkBotNamePlaceholder')"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item :label="$t('uiAutomation.notification.configs.enable')">
                      <el-switch v-model="webhookBots.dingtalk.enabled"/>
                    </el-form-item>
                  </el-col>
                  <el-col :span="24">
                    <el-form-item :label="$t('uiAutomation.notification.configs.webhookUrl')">
                      <el-input
                          v-model="webhookBots.dingtalk.webhook_url"
                          :placeholder="$t('uiAutomation.notification.configs.webhookPlaceholder')"
                      />
                      <div class="form-item-hint">
                        {{ $t('uiAutomation.notification.configs.dingtalkUrlHint') }}
                      </div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="24">
                    <el-form-item :label="$t('uiAutomation.notification.configs.signatureSecret')">
                      <el-input
                          v-model="webhookBots.dingtalk.secret"
                          :placeholder="$t('uiAutomation.notification.configs.signatureSecretPlaceholder')"
                          type="password"
                          show-password
                      />
                      <div class="form-item-hint">
                        {{ $t('uiAutomation.notification.configs.signatureSecretHint') }}
                      </div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="24">
                    <el-form-item :label="$t('uiAutomation.notification.configs.businessType')">
                      <el-checkbox v-model="webhookBots.dingtalk.enable_ui_automation">{{ $t('uiAutomation.notification.configs.uiAutomationTest') }}</el-checkbox>
                      <el-checkbox v-model="webhookBots.dingtalk.enable_api_testing">{{ $t('uiAutomation.notification.configs.apiTest') }}</el-checkbox>
                    </el-form-item>
                  </el-col>
                </el-row>

                <div class="form-actions">
                  <el-button type="primary" @click="saveWebhookBot('dingtalk')">
                    {{ $t('uiAutomation.notification.configs.saveDingtalkConfig') }}
                  </el-button>
                </div>
              </el-form>
            </div>
          </div>
        </el-tab-pane>
        <!-- 邮箱通知Tab -->
        <el-tab-pane label="邮箱通知" name="email">
          <div class="tab-content">
            <div class="config-section">
              <el-form
                  ref="emailFormRef"
                  :model="emailConfig"
                  label-position="top"
                  class="config-form"
              >
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="SMTP服务器">
                      <el-input v-model="emailConfig.smtp_host" placeholder="如 smtp.qq.com" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="SMTP端口">
                      <el-input-number v-model="emailConfig.smtp_port" :min="1" :max="65535" style="width: 100%" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="发件邮箱账号">
                      <el-input v-model="emailConfig.host_user" placeholder="如 your@qq.com" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="邮箱授权码">
                      <el-input v-model="emailConfig.host_password" type="password" show-password placeholder="不是登录密码，是SMTP授权码" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="发件人地址">
                      <el-input v-model="emailConfig.from_email" placeholder="通常与发件邮箱相同" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="加密方式">
                      <el-radio-group v-model="emailConfig.encrypt_type">
                        <el-radio value="ssl">SSL（端口465）</el-radio>
                        <el-radio value="tls">TLS（端口587）</el-radio>
                      </el-radio-group>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="是否启用">
                      <el-switch v-model="emailConfig.is_active" />
                    </el-form-item>
                  </el-col>
                </el-row>

                <div class="form-actions">
                  <el-button type="primary" @click="saveEmailConfig">保存邮箱配置</el-button>
                  <el-button @click="handleTestEmail" :loading="testEmailLoading">发送测试邮件</el-button>
                </div>
              </el-form>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script>
import {Setting} from '@element-plus/icons-vue'
import {ref, reactive, onMounted} from 'vue'
import {ElMessage} from 'element-plus'
import {
  getUnifiedNotificationConfigs,
  createUnifiedNotificationConfig,
  updateUnifiedNotificationConfig,
  testEmailConfig
} from '@/api/core.js'
import { useI18n } from 'vue-i18n'

export default {
  name: 'NotificationConfigs',
  components: {
    Setting
  },
  setup() {
    const { t } = useI18n()

    // 数据状态
    const feishuFormRef = ref(null)
    const wechatFormRef = ref(null)
    const dingtalkFormRef = ref(null)
    const emailFormRef = ref(null)
    const testEmailLoading = ref(false)
    const activeTab = ref('feishu')

    // 邮箱配置
    const emailConfig = reactive({
      id: null,
      smtp_host: '',
      smtp_port: 465,
      host_user: '',
      host_password: '',
      from_email: '',
      encrypt_type: 'ssl',
      is_active: true
    })

    // Webhook机器人配置
    const webhookBots = reactive({
      feishu: {
        name: '',
        webhook_url: '',
        enabled: true,
        enable_ui_automation: true,
        enable_api_testing: true
      },
      wechat: {
        name: '',
        webhook_url: '',
        enabled: true,
        enable_ui_automation: true,
        enable_api_testing: true
      },
      dingtalk: {
        name: '',
        webhook_url: '',
        secret: '',
        enabled: true,
        enable_ui_automation: true,
        enable_api_testing: true
      }
    })

    // 获取config_type映射
    const getConfigType = (botType) => {
      const configTypeMap = {
        'feishu': 'webhook_feishu',
        'wechat': 'webhook_wechat',
        'dingtalk': 'webhook_dingtalk'
      }
      return configTypeMap[botType]
    }

    // 获取机器人显示名称
    const getBotDisplayName = (botType) => {
      const displayNameMap = {
        'feishu': t('uiAutomation.notification.configs.platforms.feishu'),
        'wechat': t('uiAutomation.notification.configs.platforms.wechatWork'),
        'dingtalk': t('uiAutomation.notification.configs.platforms.dingtalk')
      }
      return displayNameMap[botType] || botType
    }

    // 保存Webhook机器人配置
    const saveWebhookBot = async (botType) => {
      const formRef = botType === 'feishu' ? feishuFormRef.value :
          botType === 'wechat' ? wechatFormRef.value :
              dingtalkFormRef.value

      if (!formRef) return

      try {
        const configType = getConfigType(botType)
        const botDisplayName = getBotDisplayName(botType)

        // 检查是否已存在对应类型的机器人配置
        let webhookConfigId = null
        try {
          const response = await getUnifiedNotificationConfigs({ config_type: configType })
          if (response.data.results && response.data.results.length > 0) {
            webhookConfigId = response.data.results[0].id
          }
        } catch (error) {
          console.log(t('uiAutomation.notification.configs.messages.noExistingConfig'))
        }

        const botConfig = webhookBots[botType]
        let requestData

        if (webhookConfigId) {
          // 更新现有配置 - 需要先获取现有配置，然后更新webhook_bots
          const configResponse = await getUnifiedNotificationConfigs({ config_type: configType })
          const existingConfig = configResponse.data.results[0]

          // 合并现有的webhook_bots和其他字段
          const updatedWebhookBots = existingConfig.webhook_bots || {}
          const botData = {
            name: botConfig.name || `${botType}机器人`,
            webhook_url: botConfig.webhook_url,
            enabled: botConfig.enabled,
            enable_ui_automation: botConfig.enable_ui_automation,
            enable_api_testing: botConfig.enable_api_testing
          }

          // 钉钉机器人需要额外保存secret字段
          if (botType === 'dingtalk' && botConfig.secret) {
            botData.secret = botConfig.secret
          }

          updatedWebhookBots[botType] = botData

          requestData = {
            name: existingConfig.name || `${botDisplayName}${t('uiAutomation.notification.configs.title')}`,
            config_type: configType,
            webhook_bots: updatedWebhookBots,
            is_active: true
          }

          // 更新现有配置
          await updateUnifiedNotificationConfig(webhookConfigId, requestData)
          const successMsgKey = botType === 'feishu' ? 'feishuUpdateSuccess' :
              botType === 'wechat' ? 'wechatUpdateSuccess' : 'dingtalkUpdateSuccess'
          ElMessage.success(t(`uiAutomation.notification.configs.messages.${successMsgKey}`))
        } else {
          // 创建新配置
          const botData = {
            name: botConfig.name || `${botType}机器人`,
            webhook_url: botConfig.webhook_url,
            enabled: botConfig.enabled,
            enable_ui_automation: botConfig.enable_ui_automation,
            enable_api_testing: botConfig.enable_api_testing
          }

          // 钉钉机器人需要额外保存secret字段
          if (botType === 'dingtalk' && botConfig.secret) {
            botData.secret = botConfig.secret
          }

          requestData = {
            name: `${botDisplayName}${t('uiAutomation.notification.configs.title')}`,
            config_type: configType,
            webhook_bots: {
              [botType]: botData
            },
            is_active: true
          }

          await createUnifiedNotificationConfig(requestData)
          const successMsgKey = botType === 'feishu' ? 'feishuCreateSuccess' :
              botType === 'wechat' ? 'wechatCreateSuccess' : 'dingtalkCreateSuccess'
          ElMessage.success(t(`uiAutomation.notification.configs.messages.${successMsgKey}`))
        }

        // 重新加载数据以确保状态同步
        fetchWebhookConfig(botType)
      } catch (error) {
        console.error('保存Webhook机器人配置失败:', error)
        const failedMsgKey = botType === 'feishu' ? 'feishuSaveFailed' :
            botType === 'wechat' ? 'wechatSaveFailed' : 'dingtalkSaveFailed'
        ElMessage.error(t(`uiAutomation.notification.configs.messages.${failedMsgKey}`) + ': ' + (error.response?.data?.detail || error.message))
      }
    }

    // 获取Webhook机器人配置
    const fetchWebhookConfig = async (botType) => {
      try {
        const configType = getConfigType(botType)
        const response = await getUnifiedNotificationConfigs({ config_type: configType })
        if (response.data.results && response.data.results.length > 0) {
          const config = response.data.results[0]

          if (config.webhook_bots && config.webhook_bots[botType]) {
            const bot = config.webhook_bots[botType]
            webhookBots[botType].name = bot.name || ''
            webhookBots[botType].webhook_url = bot.webhook_url || ''
            webhookBots[botType].enabled = bot.enabled !== false
            webhookBots[botType].enable_ui_automation = bot.enable_ui_automation !== false
            webhookBots[botType].enable_api_testing = bot.enable_api_testing !== false
            // 钉钉机器人需要额外读取secret字段
            if (botType === 'dingtalk' && bot.secret) {
              webhookBots[botType].secret = bot.secret
            }
          }
        }
      } catch (error) {
        console.error(t('uiAutomation.notification.configs.messages.getConfigFailed'), error)
      }
    }

    // 获取邮箱配置
    const fetchEmailConfig = async () => {
      try {
        const response = await getUnifiedNotificationConfigs({ config_type: 'email' })
        if (response.data.results && response.data.results.length > 0) {
          const config = response.data.results[0]
          emailConfig.id = config.id
          emailConfig.smtp_host = config.email_smtp_host || ''
          emailConfig.smtp_port = config.email_smtp_port || 465
          emailConfig.host_user = config.email_host_user || ''
          emailConfig.host_password = '' // 密码不回填
          emailConfig.from_email = config.email_from || ''
          emailConfig.encrypt_type = config.email_use_ssl ? 'ssl' : 'tls'
          emailConfig.is_active = config.is_active
        }
      } catch (error) {
        console.error('获取邮箱配置失败:', error)
      }
    }

    // 保存邮箱配置
    const saveEmailConfig = async () => {
      try {
        const requestData = {
          name: '邮箱通知',
          config_type: 'email',
          email_smtp_host: emailConfig.smtp_host,
          email_smtp_port: emailConfig.smtp_port,
          email_use_ssl: emailConfig.encrypt_type === 'ssl',
          email_use_tls: emailConfig.encrypt_type === 'tls',
          email_host_user: emailConfig.host_user,
          email_from: emailConfig.from_email || emailConfig.host_user,
          is_active: emailConfig.is_active
        }
        // 只在用户填写了密码时才提交密码字段
        if (emailConfig.host_password) {
          requestData.email_host_password = emailConfig.host_password
        }

        if (emailConfig.id) {
          await updateUnifiedNotificationConfig(emailConfig.id, requestData)
          ElMessage.success('邮箱配置更新成功')
        } else {
          const response = await createUnifiedNotificationConfig(requestData)
          emailConfig.id = response.data.id
          ElMessage.success('邮箱配置保存成功')
        }
        fetchEmailConfig()
      } catch (error) {
        ElMessage.error('保存邮箱配置失败: ' + (error.response?.data?.detail || error.message))
      }
    }

    // 测试邮件发送
    const handleTestEmail = async () => {
      if (!emailConfig.smtp_host || !emailConfig.host_user) {
        ElMessage.warning('请先填写SMTP服务器和发件邮箱')
        return
      }
      if (!emailConfig.id) {
        ElMessage.warning('请先保存邮箱配置后再测试')
        return
      }
      testEmailLoading.value = true
      try {
        const response = await testEmailConfig(emailConfig.id, {
          email: emailConfig.host_user
        })
        ElMessage.success(response.data.message || '测试邮件已发送')
      } catch (error) {
        ElMessage.error('测试邮件发送失败: ' + (error.response?.data?.error || error.message))
      } finally {
        testEmailLoading.value = false
      }
    }

    // 获取所有Webhook机器人配置
    const fetchAllWebhookConfigs = async () => {
      try {
        for (const botType of Object.keys(webhookBots)) {
          await fetchWebhookConfig(botType)
        }
      } catch (error) {
        console.error(t('uiAutomation.notification.configs.messages.getAllConfigFailed'), error)
      }
    }

    // 组件挂载时获取数据
    onMounted(async () => {
      try {
        console.log('NotificationConfigs 组件开始初始化')
        await fetchAllWebhookConfigs()
        await fetchEmailConfig()
        console.log('NotificationConfigs 组件初始化完成')
      } catch (error) {
        console.error('NotificationConfigs 组件初始化失败:', error)
      }
    })

    return {
      feishuFormRef,
      wechatFormRef,
      dingtalkFormRef,
      emailFormRef,
      testEmailLoading,
      activeTab,
      webhookBots,
      emailConfig,
      saveWebhookBot,
      saveEmailConfig,
      handleTestEmail,
      fetchWebhookConfig,
      fetchAllWebhookConfigs
    }
  }
}
</script>

<style scoped>
.notification-tabs :deep(.el-tabs__nav-wrap) {
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.notification-tabs :deep(.el-tabs__item) {
  font-weight: 500;
}

.tab-content {
  min-height: 400px;
  padding: 20px 0;
}

.form-item-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.form-actions {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
  text-align: right;
}
</style>
