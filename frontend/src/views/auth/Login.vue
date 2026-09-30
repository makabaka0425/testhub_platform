<template>
  <div class="login-page">
    <!-- ══════ 左侧 6/10 品牌展示区（亮色简洁商务风·原型 1:1） ══════ -->
    <section class="panel">
      <!-- 几何网格 + 圆环装饰 -->
      <div class="grid-bg"></div>
      <div class="rings">
        <span class="ring ring-1"></span>
        <span class="ring ring-2"></span>
        <span class="ring ring-3"></span>
      </div>

      <!-- 顶部品牌 + 语言切换 -->
      <header class="brand">
        <div class="mark">灵</div>
        <div class="nm">
          {{ t('auth.brandName') }}
          <small>{{ t('auth.brandSubname') }}</small>
        </div>
        <el-dropdown class="lang-sw" @command="handleLanguageChange" trigger="click">
          <span class="lang-trigger">
            <span class="lang-flag">{{ currentLanguage === 'zh-cn' ? '🇨🇳' : '🇺🇸' }}</span>
            <span class="lang-name">{{ currentLanguage === 'zh-cn' ? t('auth.languageZhCN') : t('auth.languageEn') }}</span>
            <el-icon class="caret"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="zh-cn" :disabled="currentLanguage === 'zh-cn'">{{ t('auth.languageZhCN') }}</el-dropdown-item>
              <el-dropdown-item command="en" :disabled="currentLanguage === 'en'">{{ t('auth.languageEn') }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </header>

      <!-- Hero 文案 -->
      <section class="hero">
        <span class="badge">
          {{ t('auth.badge') }}
        </span>
        <h1>
          {{ t('auth.heroLine1') }}<br />
          <span class="grad">{{ t('auth.heroLine2') }}</span>
        </h1>
        <p class="sub">{{ t('auth.heroSub') }}</p>
      </section>

      <!-- 4 张能力卡（2×2，带统计） -->
      <section class="cards">
        <div class="card">
          <div class="ic">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 20h9" />
              <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
            </svg>
          </div>
          <h3>{{ t('auth.f1Title') }}</h3>
          <p>{{ t('auth.f1Desc') }}</p>
          <div class="stat">
            {{ t('auth.f1Stat') }} <b>{{ t('auth.f1StatValue') }}</b> {{ t('auth.f1StatUnit') }}
            <span class="up">{{ t('auth.f1Trend') }}</span>
          </div>
        </div>
        <div class="card">
          <div class="ic">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2" />
            </svg>
          </div>
          <h3>{{ t('auth.f2Title') }}</h3>
          <p>{{ t('auth.f2Desc') }}</p>
          <div class="stat">
            {{ t('auth.f2Stat') }} <b>{{ t('auth.f2StatValue') }}</b> {{ t('auth.f2StatUnit') }}
            <span class="up">{{ t('auth.f2Trend') }}</span>
          </div>
        </div>
        <div class="card">
          <div class="ic">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" />
              <path d="M8 21h8M12 17v4" />
            </svg>
          </div>
          <h3>{{ t('auth.f3Title') }}</h3>
          <p>{{ t('auth.f3Desc') }}</p>
          <div class="stat">
            {{ t('auth.f3Stat') }} <b>{{ t('auth.f3StatValue') }}</b> {{ t('auth.f3StatUnit') }}
          </div>
        </div>
        <div class="card">
          <div class="ic">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 3v18h18" />
              <path d="M7 15l4-5 4 3 5-7" />
            </svg>
          </div>
          <h3>{{ t('auth.f4Title') }}</h3>
          <p>{{ t('auth.f4Desc') }}</p>
          <div class="stat">
            {{ t('auth.f4Stat') }} <b>{{ t('auth.f4StatValue') }}</b>
            <span class="up">{{ t('auth.f4Trend') }}</span>
          </div>
        </div>
      </section>

      <!-- 底部核心能力 tag + 版本号 -->
      <footer class="dock">
        <div class="lab">{{ t('auth.capabilitiesLabel') }}</div>
        <div class="tags">
          <span v-for="cap in capabilityList" :key="cap" class="tag">
            {{ cap }}
          </span>
        </div>
        <div class="cp">{{ t('auth.version') }}</div>
      </footer>
    </section>

    <!-- ══════ 右侧 4/10 登录表单区 ══════ -->
    <section class="form-panel">
      <div class="card-login">
        <div class="form-head">
          <div class="hello">{{ t('auth.welcomeBack') }} 👋</div>
          <div class="sub">
            {{ t('auth.loginSubtitle') }}
            <router-link to="/register" class="reg">{{ t('auth.signUp') }}</router-link>
          </div>
        </div>

        <!-- 登录方式 tab -->
        <div class="tabs" role="tablist">
          <button
            type="button"
            class="active"
            :class="{ active: loginMode === 'password' }"
            @click="loginMode = 'password'"
            role="tab"
          >{{ t('auth.passwordLogin') }}</button>
          <button
            type="button"
            :class="{ active: loginMode === 'sms' }"
            @click="loginMode = 'sms'; refreshCaptcha()"
            role="tab"
          >{{ t('auth.smsLogin') }}</button>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin" class="login-form" hide-required-asterisk>
          <!-- 密码登录 -->
          <template v-if="loginMode === 'password'">
            <div class="field">
              <label>{{ t('auth.accountLabel') }}</label>
              <div class="ctrl">
                <span class="pre">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="8" r="4" />
                    <path d="M4 21c0-4 3.6-6 8-6s8 2 8 6" />
                  </svg>
                </span>
                <input
                  v-model="form.username"
                  type="text"
                  :placeholder="t('auth.accountPlaceholder')"
                  autocomplete="username"
                  @keyup.enter="handleLogin"
                />
              </div>
            </div>
            <div class="field">
              <label>{{ t('auth.passwordLabel') }}</label>
              <div class="ctrl">
                <span class="pre">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="4" y="10" width="16" height="11" rx="2" />
                    <path d="M8 10V7a4 4 0 0 1 8 0v3" />
                  </svg>
                </span>
                <input
                  v-model="form.password"
                  :type="showPwd ? 'text' : 'password'"
                  :placeholder="t('auth.passwordPlaceholder')"
                  autocomplete="current-password"
                  @keyup.enter="handleLogin"
                />
                <button type="button" class="eye" :class="{ on: showPwd }" @click="showPwd = !showPwd">
                  <svg v-if="!showPwd" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 3l18 18" />
                    <path d="M10.6 10.6a3 3 0 0 0 4.2 4.2" />
                    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c6.5 0 10 8 10 8a13.5 13.5 0 0 1-1.7 2.6" />
                    <path d="M6.1 6.1A13.5 13.5 0 0 0 2 12s3.5 7 10 7a9.1 9.1 0 0 0 5.4-1.7" />
                  </svg>
                </button>
              </div>
            </div>
            <div class="row2">
              <label class="chk">
                <input type="checkbox" v-model="rememberMe" />
                <span class="box">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 6 9 17l-5-5" />
                  </svg>
                </span>
                {{ t('auth.rememberMe') }}
              </label>
              <a href="javascript:void(0)" class="forget" @click.prevent="onForgot">{{ t('auth.forgotPassword') }}</a>
            </div>
          </template>

          <!-- 短信登录 -->
          <template v-else>
            <div class="field">
              <label>{{ t('auth.phoneLabel') }}</label>
              <div class="ctrl">
                <span class="pre">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="7" y="2" width="10" height="20" rx="2.5" />
                    <path d="M11 18h2" />
                  </svg>
                </span>
                <input
                  v-model="form.phone"
                  type="tel"
                  :placeholder="t('auth.phonePlaceholder')"
                  autocomplete="tel"
                  maxlength="11"
                  @keyup.enter="handleLogin"
                />
              </div>
            </div>
            <div class="field">
              <label>{{ t('auth.captchaLabel') }}</label>
              <div class="ctrl code">
                <span class="pre">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="4" y="4" width="16" height="16" rx="3" />
                    <path d="M8 12h.01M12 12h.01M16 12h.01" />
                  </svg>
                </span>
                <input
                  v-model="form.captcha_code"
                  type="text"
                  :placeholder="t('auth.captchaLabel')"
                  inputmode="numeric"
                  maxlength="4"
                />
                <img
                  v-if="captchaImage"
                  :src="captchaImage"
                  alt="captcha"
                  class="captcha-img"
                  @click="refreshCaptcha"
                  :title="t('auth.captchaLabel')"
                />
              </div>
            </div>
            <div class="field">
              <label>{{ t('auth.smsCodeLabel') }}</label>
              <div class="ctrl code">
                <span class="pre">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="4" y="4" width="16" height="16" rx="3" />
                    <path d="M8 12h.01M12 12h.01M16 12h.01" />
                  </svg>
                </span>
                <input
                  v-model="form.verify_code"
                  type="text"
                  :placeholder="t('auth.smsCodeLabel')"
                  inputmode="numeric"
                  maxlength="6"
                  @keyup.enter="handleLogin"
                />
                <button
                  type="button"
                  class="send-btn"
                  :disabled="smsCountdown > 0 || !form.phone || !form.captcha_code"
                  @click="sendVerifyCode"
                >
                  <span v-if="sendingSms" class="sms-spinner"></span>
                  <template v-else-if="smsCountdown > 0">{{ smsCountdown }}{{ t('auth.smsResend') }}</template>
                  <template v-else>{{ t('auth.smsSend') }}</template>
                </button>
              </div>
            </div>
            <div class="row2" style="justify-content: flex-end">
              <label class="chk">
                <input type="checkbox" v-model="rememberMe" />
                <span class="box">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 6 9 17l-5-5" />
                  </svg>
                </span>
                {{ t('auth.rememberMe') }}
              </label>
            </div>
          </template>

          <!-- 登录按钮 -->
          <button type="submit" class="btn-login" :class="{ loading }" @click.prevent="handleLogin">
            <span class="spinner"></span>
            {{ loading ? t('auth.loggingIn') : t('auth.login') }}
          </button>

          <!-- 协议 -->
          <div class="foot">
            {{ t('auth.agreementPrefix') }}
            <a href="javascript:void(0)" @click.prevent="ElMessage.info('《用户协议》v2.4')">{{ t('auth.agreementTerms') }}</a>
            {{ t('auth.agreementAnd') }}
            <a href="javascript:void(0)" @click.prevent="ElMessage.info('《隐私政策》v2.4')">{{ t('auth.agreementPrivacy') }}</a>
          </div>
        </el-form>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import api from '@/utils/api'

const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()
const { t } = useI18n()

// 当前语言
const currentLanguage = computed(() => appStore.language)
const handleLanguageChange = (lang) => {
  appStore.setLanguage(lang)
}

// 能力标签（核心能力）
const capabilityList = computed(() => [
  t('auth.cap1'),
  t('auth.cap2'),
  t('auth.cap3'),
  t('auth.cap4')
])

const formRef = ref()
const loading = ref(false)
const loginMode = ref('password')

// 密码显示切换 + 记住我
const showPwd = ref(false)
const rememberMe = ref(true)

// 图形验证码
const captchaImage = ref('')
const captchaToken = ref('')

// 短信验证码
const sendingSms = ref(false)
const smsCountdown = ref(0)
let countdownTimer = null

const form = reactive({
  username: '',
  password: '',
  phone: '',
  captcha_code: '',
  verify_code: '',
  verify_code_token: ''
})

const validatePhone = (rule, value, callback) => {
  if (!value) {
    callback(new Error(t('auth.phoneInvalid')))
  } else if (!/^1[3-9]\d{9}$/.test(value)) {
    callback(new Error(t('auth.phoneInvalid')))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: computed(() => t('auth.usernameRequired')), trigger: 'blur' }
  ],
  password: [
    { required: true, message: computed(() => t('auth.passwordRequired')), trigger: 'blur' },
    { min: 6, message: computed(() => t('auth.passwordLength')), trigger: 'blur' }
  ],
  phone: [
    { required: true, validator: validatePhone, trigger: 'blur' }
  ],
  captcha_code: [
    { required: true, message: computed(() => t('auth.captchaRequired')), trigger: 'blur' }
  ],
  verify_code: [
    { required: true, message: computed(() => t('auth.smsCodeRequired')), trigger: 'blur' }
  ]
}

// 忘记密码提示
const onForgot = () => {
  ElMessage.info(t('auth.forgotPasswordToast'))
}

// 获取图形验证码
const refreshCaptcha = async () => {
  try {
    const response = await api.get('/auth/captcha/')
    captchaImage.value = response.data.image
    captchaToken.value = response.data.token
    form.captcha_code = ''
  } catch (error) {
    // 静默失败
  }
}

// 发送短信验证码
const sendVerifyCode = async () => {
  if (!form.phone) {
    ElMessage.warning(t('auth.phoneInvalid'))
    return
  }
  if (!form.captcha_code) {
    ElMessage.warning(t('auth.captchaRequired'))
    return
  }

  sendingSms.value = true
  try {
    const response = await api.post('/auth/send-register-code/', {
      phone: form.phone,
      captcha_token: captchaToken.value,
      captcha_code: form.captcha_code,
      mode: 'login'
    })
    form.verify_code_token = response.data.verify_code_token
    ElMessage.success(t('auth.smsSent'))
    smsCountdown.value = 60
    countdownTimer = setInterval(() => {
      smsCountdown.value--
      if (smsCountdown.value <= 0) {
        clearInterval(countdownTimer)
        countdownTimer = null
      }
    }, 1000)
  } catch (error) {
    const errMsg = error.response?.data?.error || t('auth.smsSendFailed')
    ElMessage.error(errMsg)
    refreshCaptcha()
  } finally {
    sendingSms.value = false
  }
}

const handleLogin = async () => {
  if (!formRef.value) return

  if (loginMode.value === 'sms') {
    await formRef.value.validate(async (valid) => {
      if (valid) {
        loading.value = true
        try {
          await userStore.smsLogin({
            phone: form.phone,
            verify_code: form.verify_code,
            verify_code_token: form.verify_code_token
          })
          ElMessage.success(t('auth.loginSuccess'))
          await router.replace('/home')
        } catch (error) {
          ElMessage.error(error.response?.data?.error || t('auth.loginFailed'))
          refreshCaptcha()
        } finally {
          loading.value = false
        }
      }
    })
    return
  }

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await userStore.login(form)
        ElMessage.success(t('auth.loginSuccess'))
        await router.replace('/home')
      } catch (error) {
        ElMessage.error(error.response?.data?.error || t('auth.loginFailed'))
      } finally {
        loading.value = false
      }
    }
  })
}

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
})
</script>

<style lang="scss" scoped>
/* ═══════════ 亮色简洁商务风 · 1:1 还原原型 ═══════════ */
.login-page {
  display: flex;
  min-height: 100vh;
  width: 100%;
  background: #f5f8fd;
  overflow: hidden;
  --blue: #2f6bff;
  --blue-h: #2455d6;
  --blue-deep: #1d47c0;
  --blue-50: #eef4ff;
  --blue-100: #dbe7ff;
  --blue-200: #c2d6ff;
  --ink-0: #f5f8fd;
  --ink-2: #e6eef8;
  --tx-1: #16233f;
  --tx-2: #5a6b8c;
  --tx-3: #8ea0bd;
  --tx-line: #e2e9f4;
  --green: #12a06b;
  --red: #e5484d;
  --r-md: 10px;
  --r-lg: 16px;
  --r-xl: 22px;
  --r-pill: 999px;
  --sh-sm: 0 1px 2px rgba(22, 41, 80, 0.05), 0 4px 14px rgba(22, 41, 80, 0.05);
  --sh-md: 0 6px 24px rgba(22, 41, 80, 0.08), 0 2px 6px rgba(22, 41, 80, 0.05);
  --grad-brand: linear-gradient(135deg, #3b82f6, #2f6bff 55%, #5a7cff);
}

/* ─────────── 左侧 60% 品牌区 ─────────── */
.panel {
  position: relative;
  flex: 0 0 60%;
  max-width: none;
  padding: 56px 72px 40px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(1200px 700px at -10% -10%, rgba(47, 107, 255, 0.14), transparent 55%),
    radial-gradient(900px 600px at 110% 115%, rgba(90, 124, 255, 0.12), transparent 55%),
    linear-gradient(160deg, #f8fbff 0%, #eef4ff 55%, #e7efff 100%);
  &::before {
    content: '';
    position: absolute;
    top: -120px; right: -120px;
    width: 360px; height: 360px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(47, 107, 255, 0.18), transparent 70%);
  }
  &::after {
    content: '';
    position: absolute;
    bottom: 8%; left: -90px;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.14), transparent 70%);
  }
}

/* 几何网格 */
.grid-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0.5;
  background-image:
    linear-gradient(to right, var(--blue-100) 1px, transparent 1px),
    linear-gradient(to bottom, var(--blue-100) 1px, transparent 1px);
  background-size: 52px 52px;
  mask-image: radial-gradient(ellipse at 30% 30%, #000 20%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse at 30% 30%, #000 20%, transparent 70%);
}

/* 圆环 */
.rings {
  position: absolute;
  inset: 0;
  pointer-events: none;
  .ring {
    position: absolute;
    border: 1px solid rgba(47, 107, 255, 0.16);
    border-radius: 50%;
    &.ring-1 { width: 520px; height: 520px; top: -160px; right: -160px; }
    &.ring-2 { width: 340px; height: 340px; top: -40px; right: -40px; border-color: rgba(47, 107, 255, 0.22); }
    &.ring-3 { width: 180px; height: 180px; top: 120px; right: -60px; border-color: rgba(47, 107, 255, 0.18); }
  }
}

/* 品牌头部 */
.brand {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 12px;
  .mark {
    width: 38px; height: 38px;
    border-radius: 11px;
    background: var(--grad-brand);
    display: flex; align-items: center; justify-content: center;
    color: #fff;
    font-weight: 800;
    font-size: 19px;
    box-shadow: 0 8px 20px rgba(47, 107, 255, 0.35);
  }
  .nm {
    font-size: 19px;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: #10244d;
    small {
      font-weight: 500;
      color: var(--tx-2);
      font-size: 12.5px;
      margin-left: 6px;
      letter-spacing: 0;
    }
  }
  .lang-sw {
    margin-left: auto;
    :deep(.lang-trigger) {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: var(--tx-2);
      padding: 6px 11px;
      border: 1px solid var(--tx-line);
      border-radius: var(--r-pill);
      background: rgba(255, 255, 255, 0.7);
      cursor: pointer;
      transition: all 0.15s;
      &:hover {
        border-color: var(--blue-200);
        color: var(--blue);
      }
      .lang-flag { font-size: 14px; line-height: 1; }
      .caret { font-size: 11px; }
    }
  }
}

/* Hero */
.hero {
  position: relative;
  z-index: 2;
  margin-top: 9vh;
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 6px 13px;
    border-radius: var(--r-pill);
    background: rgba(47, 107, 255, 0.1);
    border: 1px solid var(--blue-100);
    font-size: 12px;
    color: var(--blue);
    font-weight: 600;
    margin-bottom: 22px;
  }
  h1 {
    font-size: clamp(34px, 3.6vw, 50px);
    font-weight: 800;
    line-height: 1.12;
    letter-spacing: -0.02em;
    color: #10244d;
    margin: 0;
    .grad {
      background: var(--grad-brand);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }
  }
  .sub {
    font-size: 15.5px;
    color: var(--tx-2);
    line-height: 1.8;
    margin: 16px 0 0;
    max-width: 460px;
  }
}

/* 能力卡 2×2 */
.cards {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 44px;
}
.card {
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid var(--tx-line);
  border-radius: var(--r-lg);
  padding: 18px 18px 16px;
  backdrop-filter: blur(8px);
  transition: transform 0.18s, box-shadow 0.18s, border-color 0.18s;
  &:hover {
    transform: translateY(-3px);
    box-shadow: var(--sh-md);
    border-color: var(--blue-200);
  }
  .ic {
    width: 34px; height: 34px;
    border-radius: 9px;
    background: var(--blue-50);
    color: var(--blue);
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 12px;
    svg { width: 19px; height: 19px; }
  }
  h3 {
    font-size: 14.5px;
    font-weight: 700;
    color: #10244d;
    margin: 0;
  }
  p {
    font-size: 12.3px;
    color: var(--tx-2);
    line-height: 1.65;
    margin: 6px 0 0;
  }
  .stat {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 11px;
    font-size: 11.5px;
    color: var(--tx-3);
    b {
      color: var(--blue);
      font-size: 13px;
      font-family: 'JetBrains Mono', ui-monospace, monospace;
    }
    .up { color: var(--green); margin-left: 2px; }
  }
}

/* 底部 tag 区 */
.dock {
  position: relative;
  z-index: 2;
  margin-top: auto;
  padding-top: 40px;
  .lab {
    font-size: 11.5px;
    color: var(--tx-3);
    letter-spacing: 1px;
    margin-bottom: 14px;
  }
  .tags {
    display: flex;
    gap: 9px;
    flex-wrap: wrap;
  }
  .tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 14px;
    border-radius: var(--r-pill);
    background: rgba(255, 255, 255, 0.85);
    border: 1px solid var(--tx-line);
    font-size: 12.5px;
    color: var(--tx-2);
    font-weight: 500;
  }
  .cp {
    margin-top: 22px;
    font-size: 11.5px;
    color: var(--tx-3);
  }
}

/* ─────────── 右侧 40% 登录区 ─────────── */
.form-panel {
  flex: 0 0 40%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
  background: var(--ink-0);
}
.card-login {
  width: 100%;
  max-width: 424px;
}
.form-head {
  .hello {
    font-size: 26px;
    font-weight: 800;
    color: #10244d;
    letter-spacing: -0.01em;
  }
  .sub {
    font-size: 13.5px;
    color: var(--tx-2);
    margin-top: 6px;
    .reg {
      color: var(--blue);
      font-weight: 600;
      margin-left: 4px;
      text-decoration: none;
      &:hover { text-decoration: underline; }
    }
  }
}

/* tab */
.tabs {
  display: flex;
  gap: 4px;
  margin: 26px 0 22px;
  background: var(--ink-2);
  padding: 4px;
  border-radius: var(--r-md);
  width: 100%;
  button {
    flex: 1;
    height: 38px;
    border: 0;
    background: transparent;
    border-radius: 8px;
    font-size: 13.5px;
    font-weight: 600;
    color: var(--tx-2);
    transition: all 0.18s;
    cursor: pointer;
    &.active {
      background: #fff;
      color: var(--blue);
      box-shadow: var(--sh-sm);
    }
  }
}

/* 表单字段 */
.field {
  margin-bottom: 16px;
  label {
    display: block;
    font-size: 12.5px;
    font-weight: 600;
    color: var(--tx-1);
    margin-bottom: 7px;
  }
}
.ctrl {
  position: relative;
  .pre {
    position: absolute;
    left: 13px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--tx-3);
    display: flex;
    pointer-events: none;
    svg { width: 17px; height: 17px; }
  }
  input {
    width: 100%;
    height: 44px;
    padding: 0 42px;
    border: 1px solid var(--tx-line);
    border-radius: var(--r-md);
    background: #fff;
    color: var(--tx-1);
    font-size: 14px;
    font-family: inherit;
    transition: border-color 0.15s, box-shadow 0.15s;
    &::placeholder { color: var(--tx-3); }
    &:focus {
      outline: none;
      border-color: var(--blue);
      box-shadow: 0 0 0 3px rgba(47, 107, 255, 0.13);
    }
  }
  .eye {
    position: absolute;
    right: 5px;
    top: 50%;
    transform: translateY(-50%);
    border: 0;
    background: transparent;
    color: var(--tx-3);
    width: 34px;
    height: 34px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.15s;
    cursor: pointer;
    &:hover { color: var(--blue); }
    svg { width: 18px; height: 18px; }
  }
  .send-btn {
    position: absolute;
    right: 6px;
    top: 50%;
    transform: translateY(-50%);
    height: 34px;
    padding: 0 12px;
    border: 0;
    border-radius: 8px;
    background: var(--blue-50);
    color: var(--blue);
    font-size: 12.5px;
    font-weight: 600;
    transition: all 0.15s;
    white-space: nowrap;
    cursor: pointer;
    &:not(:disabled):hover {
      background: var(--blue-100);
      color: var(--blue-h);
    }
    &:disabled {
      color: var(--tx-3);
      background: var(--ink-2);
      cursor: not-allowed;
    }
    .sms-spinner {
      display: inline-block;
      width: 12px;
      height: 12px;
      border: 2px solid var(--blue-100);
      border-top-color: var(--blue);
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      vertical-align: middle;
    }
  }
}

/* 图形验证码 + 短信码：右侧附加按钮 */
.code {
  input {
    padding-right: 118px;
  }
  .captcha-img {
    position: absolute;
    right: 6px;
    top: 50%;
    transform: translateY(-50%);
    height: 34px;
    width: 100px;
    border-radius: 8px;
    border: 1px solid var(--tx-line);
    object-fit: cover;
    cursor: pointer;
    background: #fff;
  }
}

.row2 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 4px 0 20px;
}

.chk {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 12.5px;
  color: var(--tx-2);
  user-select: none;
  input { display: none; }
  .box {
    width: 16px;
    height: 16px;
    border-radius: 5px;
    border: 1.5px solid var(--tx-line);
    background: #fff;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
    flex-shrink: 0;
    svg { width: 11px; height: 11px; color: #fff; opacity: 0; transform: scale(0.5); transition: all 0.15s; }
  }
  input:checked + .box {
    background: var(--blue);
    border-color: var(--blue);
    svg { opacity: 1; transform: scale(1); }
  }
}

.forget {
  font-size: 12.5px;
  color: var(--tx-2);
  font-weight: 500;
  text-decoration: none;
  &:hover { color: var(--blue); }
}

/* 登录按钮 */
.btn-login {
  width: 100%;
  height: 46px;
  border: 0;
  border-radius: var(--r-md);
  background: var(--grad-brand);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 2px;
  box-shadow: 0 8px 22px rgba(47, 107, 255, 0.32);
  transition: all 0.18s;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 12px 28px rgba(47, 107, 255, 0.4);
    filter: brightness(1.03);
  }
  &:active { transform: translateY(0); }
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: -60%;
    width: 40%;
    height: 100%;
    background: linear-gradient(100deg, transparent, rgba(255, 255, 255, 0.35), transparent);
    transform: skewX(-20deg);
    animation: btn-sheen 2.8s infinite;
  }
  @keyframes btn-sheen {
    0% { left: -60%; }
    60%, 100% { left: 130%; }
  }
  &.loading {
    pointer-events: none;
    opacity: 0.85;
    .spinner { display: inline-block; }
  }
  .spinner {
    display: none;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.35);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    vertical-align: -3px;
    margin-right: 8px;
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
}

/* 底部协议 */
.foot {
  position: relative;
  z-index: 2;
  text-align: center;
  margin-top: 34px;
  font-size: 12px;
  color: var(--tx-3);
  a {
    color: var(--tx-3);
    text-decoration: none;
    &:hover { color: var(--blue); }
  }
}

/* ─────────── 响应式 ─────────── */
@media (max-width: 1180px) {
  .panel { padding: 48px 48px 32px; }
  .cards { gap: 12px; }
}
@media (max-width: 960px) {
  .login-page { flex-direction: column; overflow-y: auto; }
  .panel { flex-basis: 100%; padding: 32px 24px; }
  .hero { margin-top: 40px; }
  .form-panel { flex: none; padding: 36px 20px; }
}
</style>
