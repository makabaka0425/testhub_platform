<template>
  <div class="home-container">
    <div class="content-wrapper">
      <div class="header-actions">
        <!-- PC：语言、用户分开 -->
        <div class="header-actions-pc">
          <el-dropdown @command="handleLanguageChange" class="language-dropdown">
            <span class="el-dropdown-link">
              <span class="language-icon">{{ currentLanguage === 'zh-cn' ? '🇨🇳' : '🇺🇸' }}</span>
              <span class="language-text">{{ $t('home.language.current') }}</span>
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="zh-cn" :disabled="currentLanguage === 'zh-cn'">
                  <span class="dropdown-flag">🇨🇳</span> {{ $t('home.language.zhCN') }}
                </el-dropdown-item>
                <el-dropdown-item command="en" :disabled="currentLanguage === 'en'">
                  <span class="dropdown-flag">🇺🇸</span> {{ $t('home.language.en') }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-dropdown @command="handleCommand">
            <span class="el-dropdown-link">
              <el-avatar :size="32" :icon="UserFilled" />
              <span class="username">{{ userStore.user?.username || $t('home.user') }}</span>
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">{{ $t('home.logout') }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <!-- 移动端：合并菜单 -->
        <div class="header-actions-mobile">
          <el-dropdown trigger="click" @command="handleHeaderCommand">
            <span class="user-menu-trigger">
              <span class="avatar-wrap">
                <el-avatar :size="28" :icon="UserFilled" />
                <span class="lang-badge">{{ currentLanguage === 'zh-cn' ? '🇨🇳' : '🇺🇸' }}</span>
              </span>
              <el-icon class="trigger-arrow"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="zh-cn" :disabled="currentLanguage === 'zh-cn'">
                  <span class="dropdown-flag">🇨🇳</span> {{ $t('home.language.zhCN') }}
                </el-dropdown-item>
                <el-dropdown-item command="en" :disabled="currentLanguage === 'en'">
                  <span class="dropdown-flag">🇺🇸</span> {{ $t('home.language.en') }}
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  {{ $t('home.logout') }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <h1 class="main-title">
        <span class="brand-name">
          <span class="brand-corner">
            <span class="brand-text">{{ $t('home.brandName') }}</span>
          </span>
        </span>
        {{ $t('home.titleSuffix') }}
      </h1>
      <p class="subtitle">{{ $t('home.subtitle') }}</p>

      <div class="cards-container">
        <!-- 1. AI用例生成 -->
        <div class="nav-card" @click="handleNavigate('ai')" role="button" tabindex="0">
          <div class="card-icon ai-icon">
            <el-icon><MagicStick /></el-icon>
          </div>
          <h3>{{ $t('home.aiCaseGeneration') }}<span class="ai-badge">AI</span></h3>
          <p>{{ $t('home.aiCaseGenerationDesc') }}</p>
        </div>

        <!-- 2. AI自动化测试 -->
        <div class="nav-card" @click="handleNavigate('ai-intelligent')" role="button" tabindex="0">
          <div class="card-icon ai-intelligent-icon">
            <el-icon><Cpu /></el-icon>
          </div>
          <h3>{{ $t('home.aiIntelligentMode') }}<span class="ai-badge">AI</span></h3>
          <p>{{ $t('home.aiIntelligentModeDesc') }}</p>
        </div>

        <!-- 3. UI自动化测试 -->
        <div class="nav-card" @click="handleNavigate('ui')" role="button" tabindex="0">
          <div class="card-icon ui-icon">
            <el-icon><Monitor /></el-icon>
          </div>
          <h3>{{ $t('home.uiAutomation') }}</h3>
          <p>{{ $t('home.uiAutomationDesc') }}</p>
        </div>

        <!-- 4. APP自动化测试 -->
        <div class="nav-card" @click="handleNavigate('app')" role="button" tabindex="0">
          <div class="card-icon app-icon">
            <el-icon><Cellphone /></el-icon>
          </div>
          <h3>{{ $t('home.appAutomation') }}</h3>
          <p>{{ $t('home.appAutomationDesc') }}</p>
        </div>

        <!-- 5. 接口测试 -->
        <div class="nav-card" @click="handleNavigate('api')" role="button" tabindex="0">
          <div class="card-icon api-icon">
            <el-icon><Link /></el-icon>
          </div>
          <h3>{{ $t('home.apiTesting') }}</h3>
          <p>{{ $t('home.apiTestingDesc') }}</p>
        </div>

        <!-- 6. Bug缺陷管理（暂时隐藏） -->
        <template v-if="false">
        <div class="nav-card" @click="handleNavigate('defects')" role="button" tabindex="0">
          <div class="card-icon defects-icon">
            <el-icon><Tickets /></el-icon>
          </div>
          <h3>{{ $t('home.defectManagement') }}</h3>
          <p>{{ $t('home.defectManagementDesc') }}</p>
        </div>
        </template>

        <!-- 7. 数据工厂 -->
        <div class="nav-card" @click="handleNavigate('data')" role="button" tabindex="0">
          <div class="card-icon data-icon">
            <el-icon><DataLine /></el-icon>
          </div>
          <h3>{{ $t('home.dataFactory') }}</h3>
          <p>{{ $t('home.dataFactoryDesc') }}</p>
        </div>

        <!-- 8. AI评测师（暂时隐藏） -->
        <template v-if="false">
        <div class="nav-card" @click="handleNavigate('assistant')" role="button" tabindex="0">
          <div class="card-icon assistant-icon">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <h3>{{ $t('home.aiEvaluator') }}</h3>
          <p>{{ $t('home.aiEvaluatorDesc') }}</p>
        </div>
        </template>

        <!-- 9. 配置中心 -->
        <div class="nav-card" @click="handleNavigate('config')" role="button" tabindex="0">
          <div class="card-icon config-icon">
            <el-icon><Setting /></el-icon>
          </div>
          <h3>{{ $t('home.configCenter') }}</h3>
          <p>{{ $t('home.configCenterDesc') }}</p>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="mobileDialogVisible"
      class="mobile-tip-dialog"
      :title="$t('home.mobileTipTitle')"
      width="88%"
      align-center
      :close-on-click-modal="true"
      append-to-body
    >
      <div class="mobile-tip-dialog-body">
        <div class="dialog-icon-wrap">
          <el-icon><Monitor /></el-icon>
        </div>
        <p class="dialog-desc">{{ $t('home.mobileTipDesc') }}</p>
      </div>
      <template #footer>
        <el-button type="primary" class="dialog-confirm-btn" @click="mobileDialogVisible = false">
          {{ $t('home.mobileTipOk') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { track } from '@/utils/tracker'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Link, Monitor, DataLine, Cpu, Setting, ChatDotRound, UserFilled, ArrowDown, Cellphone, Tickets } from '@element-plus/icons-vue'

const router = useRouter()
const { t } = useI18n()
const userStore = useUserStore()
const appStore = useAppStore()

// 当前语言
const currentLanguage = computed(() => appStore.language)
const isMobile = ref(false)
const mobileTipDismissed = ref(false)
const MOBILE_BREAKPOINT = 768
const MOBILE_TIP_STORAGE_KEY = 'lingce_ltest_home_mobile_tip_seen'

const dismissMobileTip = () => {
  mobileTipDismissed.value = true
  try {
    localStorage.setItem(MOBILE_TIP_STORAGE_KEY, '1')
  } catch {
    // ignore quota / private mode
  }
}

const mobileDialogVisible = computed({
  get: () => isMobile.value && !mobileTipDismissed.value,
  set: (val) => {
    if (!val) dismissMobileTip()
  }
})

const updateMobileTip = () => {
  isMobile.value = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`).matches
}

onMounted(() => {
  try {
    if (localStorage.getItem(MOBILE_TIP_STORAGE_KEY) === '1') {
      mobileTipDismissed.value = true
    }
  } catch {
    // ignore
  }
  updateMobileTip()
  window.addEventListener('resize', updateMobileTip)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateMobileTip)
})

const handleLanguageChange = (lang) => {
  appStore.setLanguage(lang)
}

const handleCommand = (command) => {
  if (command === 'logout') {
    handleLogout()
  }
}

const handleHeaderCommand = (command) => {
  if (command === 'logout') {
    handleLogout()
    return
  }
  if (command === 'zh-cn' || command === 'en') {
    appStore.setLanguage(command)
  }
}

const handleLogout = () => {
  ElMessageBox.confirm(t('home.logoutConfirm'), t('common.tips'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }).then(() => {
    userStore.logout()
    router.push('/login')
    ElMessage.success(t('home.logoutSuccess'))
  }).catch(() => {})
}

const handleNavigate = (type) => {
  const routes = {
    'ai': '/ai-generation/requirement-analysis',
    'api': '/api-testing/dashboard',
    'ui': '/ui-automation/dashboard',
    'defects': '/defects/dashboard',
    'app': '/app-automation/dashboard',
    'ai-intelligent': '/ai-intelligent-mode/dashboard',
    'assistant': '/ai-generation/assistant',
    'config': '/configuration/ai-model',
    'data': '/data-factory'
  }

  if (routes[type]) {
    track('module_card_click', {
      event_type: 'click',
      module: 'home',
      page_path: '/home',
      target_path: routes[type],
      metadata: {
        card_type: type
      }
    })
    const routeData = router.resolve({ path: routes[type] })
    window.open(routeData.href, '_blank')
  }
}
</script>

<style scoped lang="scss">
/* ========== 深邃科技蓝背景 + 微光粒子 ========== */
.home-container {
  min-height: calc(100vh - 100px);
  background: linear-gradient(135deg, #0B1120 0%, #162544 40%, #1E3A6E 70%, #0F172A 100%);
  background-size: 400% 400%;
  animation: bgShift 20s ease infinite;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  position: relative;
  overflow: hidden;

  /* 装饰光晕 */
  &::before {
    content: '';
    position: absolute;
    width: 600px;
    height: 600px;
    top: -150px;
    right: -100px;
    background: radial-gradient(circle, rgba(34, 211, 238, 0.08) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
  }
  &::after {
    content: '';
    position: absolute;
    width: 500px;
    height: 500px;
    bottom: -100px;
    left: -80px;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.07) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
  }
}

@keyframes bgShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.content-wrapper {
  text-align: center;
  max-width: 1200px;
  width: 100%;
  position: relative;
  z-index: 1;
}

/* ========== 顶部操作区 ========== */
.header-actions {
  position: absolute;
  top: 0;
  right: 0;
  padding: 10px;
}

.header-actions-pc {
  display: flex;
  align-items: center;
  gap: 20px;

  .language-dropdown {
    .el-dropdown-link {
      display: flex;
      align-items: center;
      cursor: pointer;
      color: rgba(255, 255, 255, 0.65);
      transition: color 0.3s;
      outline: none;

      &:hover {
        color: #22D3EE;
      }

      .language-icon {
        font-size: 18px;
        margin-right: 5px;
        line-height: 1;
      }

      .language-text {
        margin: 0 5px;
        font-size: 14px;
      }
    }
  }

  .el-dropdown-link {
    display: flex;
    align-items: center;
    cursor: pointer;
    color: rgba(255, 255, 255, 0.65);
    transition: color 0.3s;
    outline: none;

    .username {
      margin: 0 8px;
      font-size: 14px;
    }

    &:hover {
      color: #22D3EE;
    }
  }
}

.header-actions-mobile {
  display: none;
}

.user-menu-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.7);
  padding: 6px 10px 6px 6px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
  transition: all 0.3s;
  outline: none;

  &:focus {
    outline: none;
  }

  &:hover {
    color: #22D3EE;
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(34, 211, 238, 0.3);
  }

  .avatar-wrap {
    position: relative;
    display: inline-flex;
    flex-shrink: 0;
  }

  .lang-badge {
    position: absolute;
    right: -5px;
    bottom: -3px;
    font-size: 11px;
    line-height: 1;
    background: rgba(15, 23, 42, 0.8);
    border-radius: 50%;
    padding: 1px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  }

  .trigger-arrow {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
  }
}

.dropdown-flag {
  font-size: 16px;
  margin-right: 5px;
}

/* ========== 主标题：纯白+深蓝科技感 ========== */
.main-title {
  font-size: 3.5rem;
  color: #ffffff;
  margin-bottom: 1rem;
  font-weight: 800;
  letter-spacing: 3px;
  text-shadow: 0 2px 20px rgba(34, 211, 238, 0.15);
}

.brand-name {
  display: inline-block;
  margin-right: 8px;
  vertical-align: baseline;
}

.brand-corner {
  display: inline-block;
  position: relative;
  padding: 8px 14px 8px 10px;

  &::before,
  &::after {
    content: '';
    position: absolute;
    width: 20px;
    height: 20px;
    border-style: solid;
    border-width: 0;
  }

  /* 左上角 */
  &::before {
    top: 0;
    left: 0;
    border-top-width: 3px;
    border-left-width: 3px;
    border-top-left-radius: 4px;
    border-color: #22D3EE;
    box-shadow: -2px -2px 8px rgba(34, 211, 238, 0.25);
  }

  /* 右下角 */
  &::after {
    bottom: 0;
    right: 0;
    border-bottom-width: 3px;
    border-right-width: 3px;
    border-bottom-right-radius: 4px;
    border-color: #8B5CF6;
    box-shadow: 2px 2px 8px rgba(139, 92, 246, 0.25);
  }
}

.brand-text {
  display: inline;
}

.subtitle {
  font-size: 1.5rem;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 4rem;
  font-weight: 300;
  letter-spacing: 1px;
}

/* ========== 卡片网格 ========== */
.cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 30px;
  padding: 20px;
}

/* ========== Glassmorphism 玻璃拟态卡片 ========== */
.nav-card {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 20px;
  padding: 40px 20px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  align-items: center;
  /* 玻璃拟态核心属性 */
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.2),
    0 1px 0 rgba(255, 255, 255, 0.05) inset;
  position: relative;
  overflow: hidden;

  /* 卡片顶部高光线 */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 20%;
    right: 20%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent);
  }

  &:hover {
    transform: translateY(-8px);
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.15);
    box-shadow:
      0 20px 40px rgba(0, 0, 0, 0.3),
      0 1px 0 rgba(255, 255, 255, 0.08) inset;
  }

  h3 {
    font-size: 1.5rem;
    color: #ffffff;
    margin: 20px 0 10px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  p {
    color: rgba(255, 255, 255, 0.5);
    line-height: 1.6;
    margin: 0;
    font-size: 14px;
  }
}

/* ========== AI 流光渐变胶囊标签 ========== */
.ai-badge {
  display: inline-flex;
  align-items: center;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  padding: 2px 8px;
  border-radius: 999px;
  color: #fff;
  background: linear-gradient(135deg, #22D3EE, #8B5CF6);
  position: relative;
  flex-shrink: 0;

  /* 流光边框动画 */
  &::before {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: 999px;
    padding: 1px;
    background: linear-gradient(135deg, #22D3EE, #8B5CF6, #22D3EE);
    background-size: 300% 300%;
    animation: badgeGlow 3s ease infinite;
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
  }
}

@keyframes badgeGlow {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* ========== 图标色彩：科技感升级 ========== */
.card-icon {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  margin-bottom: 10px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);

  /* AI功能：亮青色/电光蓝 */
  &.ai-icon {
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.15) 0%, rgba(6, 182, 212, 0.08) 100%);
    color: #22D3EE;
    box-shadow: 0 0 20px rgba(34, 211, 238, 0.15);
  }

  /* AI智能：电光蓝 */
  &.ai-intelligent-icon {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(99, 102, 241, 0.08) 100%);
    color: #60A5FA;
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.15);
  }

  /* UI测试：活力紫 */
  &.ui-icon {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(168, 85, 247, 0.08) 100%);
    color: #A78BFA;
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.15);
  }

  /* APP测试：活力紫（偏粉） */
  &.app-icon {
    background: linear-gradient(135deg, rgba(192, 132, 252, 0.15) 0%, rgba(232, 121, 249, 0.08) 100%);
    color: #C084FC;
    box-shadow: 0 0 20px rgba(192, 132, 252, 0.15);
  }

  /* 接口测试：薄荷绿 */
  &.api-icon {
    background: linear-gradient(135deg, rgba(52, 211, 153, 0.15) 0%, rgba(16, 185, 129, 0.08) 100%);
    color: #34D399;
    box-shadow: 0 0 20px rgba(52, 211, 153, 0.15);
  }

  /* 数据工厂：橙色 */
  &.data-icon {
    background: linear-gradient(135deg, rgba(251, 146, 60, 0.15) 0%, rgba(245, 158, 11, 0.08) 100%);
    color: #FB923C;
    box-shadow: 0 0 20px rgba(251, 146, 60, 0.15);
  }

  /* 缺陷管理：玫瑰红 */
  &.defects-icon {
    background: linear-gradient(135deg, rgba(251, 113, 133, 0.15) 0%, rgba(244, 63, 94, 0.08) 100%);
    color: #FB7185;
    box-shadow: 0 0 20px rgba(251, 113, 133, 0.15);
  }

  /* 配置中心：琥珀金 */
  &.config-icon {
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, rgba(245, 158, 11, 0.08) 100%);
    color: #FBBF24;
    box-shadow: 0 0 20px rgba(251, 191, 36, 0.15);
  }

  /* AI评测师：橙色渐变 */
  &.assistant-icon {
    background: linear-gradient(135deg, rgba(251, 146, 60, 0.15) 0%, rgba(234, 88, 12, 0.08) 100%);
    color: #FB923C;
    box-shadow: 0 0 20px rgba(251, 146, 60, 0.15);
  }
}

/* 悬停时图标发光增强 */
.nav-card:hover .card-icon {
  transform: scale(1.08);
  filter: brightness(1.2);
}
.nav-card:hover .ai-icon { box-shadow: 0 0 30px rgba(34, 211, 238, 0.35); }
.nav-card:hover .ai-intelligent-icon { box-shadow: 0 0 30px rgba(59, 130, 246, 0.35); }
.nav-card:hover .ui-icon { box-shadow: 0 0 30px rgba(139, 92, 246, 0.35); }
.nav-card:hover .app-icon { box-shadow: 0 0 30px rgba(192, 132, 252, 0.35); }
.nav-card:hover .api-icon { box-shadow: 0 0 30px rgba(52, 211, 153, 0.35); }
.nav-card:hover .data-icon { box-shadow: 0 0 30px rgba(251, 146, 60, 0.35); }
.nav-card:hover .config-icon { box-shadow: 0 0 30px rgba(251, 191, 36, 0.35); }

/* ========== 响应式 ========== */
@media screen and (max-width: 1920px) {
  .main-title {
    font-size: 3.2rem;
  }

  .subtitle {
    font-size: 1.4rem;
  }

  .cards-container {
    gap: 28px;
    padding: 18px;
  }
}

@media screen and (max-width: 1600px) {
  .main-title {
    font-size: 3rem;
  }

  .subtitle {
    font-size: 1.3rem;
  }

  .cards-container {
    gap: 26px;
    padding: 16px;
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  }

  .nav-card {
    padding: 35px 18px;
  }
}

@media screen and (max-width: 1440px) {
  .main-title {
    font-size: 2.8rem;
  }

  .subtitle {
    font-size: 1.2rem;
  }

  .cards-container {
    gap: 24px;
    padding: 14px;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  .nav-card {
    padding: 30px 16px;

    h3 {
      font-size: 1.4rem;
    }
  }

  .card-icon {
    width: 70px;
    height: 70px;
    font-size: 35px;
    border-radius: 18px;
  }
}

@media screen and (max-width: 1366px) {
  .main-title {
    font-size: 2.6rem;
  }

  .subtitle {
    font-size: 1.1rem;
  }

  .cards-container {
    gap: 22px;
    padding: 12px;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }

  .nav-card {
    padding: 28px 14px;

    h3 {
      font-size: 1.3rem;
    }
  }

  .card-icon {
    width: 65px;
    height: 65px;
    font-size: 32px;
    border-radius: 16px;
  }
}

@media screen and (max-width: 1280px) {
  .main-title {
    font-size: 2.4rem;
  }

  .subtitle {
    font-size: 1rem;
  }

  .cards-container {
    gap: 20px;
    padding: 12px;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }

  .nav-card {
    padding: 25px 12px;

    h3 {
      font-size: 1.2rem;
    }
  }

  .card-icon {
    width: 60px;
    height: 60px;
    font-size: 30px;
  }
}

@media screen and (max-width: 1024px) {
  .home-container {
    padding: 15px;
  }

  .main-title {
    font-size: 2.2rem;
  }

  .subtitle {
    font-size: 1rem;
    margin-bottom: 3rem;
  }

  .cards-container {
    gap: 18px;
    padding: 10px;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  }

  .nav-card {
    padding: 20px 10px;

    h3 {
      font-size: 1.1rem;
    }

    p {
      font-size: 0.9rem;
    }
  }

  .card-icon {
    width: 55px;
    height: 55px;
    font-size: 28px;
  }

  .header-actions {
    padding: 8px;
  }
}

/* ========== 移动端 ========== */
@media screen and (max-width: 768px) {
  .home-container {
    position: relative;
    overflow: hidden;
    padding: 14px 14px 24px;
    padding-top: max(14px, env(safe-area-inset-top));

    &::before,
    &::after {
      content: '';
      position: absolute;
      border-radius: 50%;
      pointer-events: none;
      z-index: 0;
    }

    &::before {
      width: 260px;
      height: 260px;
      top: -70px;
      right: -50px;
      background: radial-gradient(circle, rgba(34, 211, 238, 0.1) 0%, transparent 68%);
    }

    &::after {
      width: 220px;
      height: 220px;
      bottom: 8%;
      left: -70px;
      background: radial-gradient(circle, rgba(139, 92, 246, 0.08) 0%, transparent 70%);
    }
  }

  .content-wrapper {
    position: relative;
    z-index: 1;
  }

  .header-actions {
    position: static;
    margin-bottom: 12px;
    padding: 0;
  }

  .header-actions-pc {
    display: none;
  }

  .header-actions-mobile {
    display: flex;
    justify-content: flex-end;
  }

  .main-title {
    font-size: 1.75rem;
    letter-spacing: 0.5px;
    color: #ffffff;
    margin-bottom: 8px;
  }

  .brand-corner {
    padding: 5px 8px 5px 6px;

    &::before,
    &::after {
      width: 14px;
      height: 14px;
      border-width: 2px;
    }
  }

  .subtitle {
    font-size: 0.9375rem;
    color: rgba(255, 255, 255, 0.5);
    margin: 0 auto 24px;
    max-width: 280px;
    line-height: 1.5;
  }

  .cards-container {
    grid-template-columns: repeat(2, 1fr);
    gap: 14px;
  }

  .nav-card {
    min-height: 148px;
    padding: 18px 12px 16px;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow:
      0 4px 14px rgba(0, 0, 0, 0.2),
      0 1px 0 rgba(255, 255, 255, 0.05) inset;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);

    &:hover {
      transform: none;
      box-shadow:
        0 6px 18px rgba(0, 0, 0, 0.25),
        0 1px 0 rgba(255, 255, 255, 0.08) inset;
    }

    &:active {
      transform: scale(0.98);
      background: rgba(255, 255, 255, 0.08);
    }

    h3 {
      font-size: 15px;
      margin: 12px 0 6px;
      color: #ffffff;
      line-height: 1.35;
    }

    p {
      font-size: 12px;
      line-height: 1.45;
      color: rgba(255, 255, 255, 0.45);
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
  }

  .card-icon {
    width: 48px;
    height: 48px;
    font-size: 24px;
    border-radius: 14px;
  }

  .nav-card:hover .card-icon {
    transform: none;
  }
}

@media screen and (max-width: 480px) {
  .home-container {
    padding: 12px 12px 20px;
    padding-top: max(12px, env(safe-area-inset-top));
  }

  .header-actions {
    margin-bottom: 16px;
  }

  .header-actions-mobile .user-menu-trigger {
    padding: 5px 8px 5px 5px;
    gap: 4px;
  }

  .main-title {
    font-size: 1.5rem;
  }

  .brand-corner {
    padding: 4px 6px 4px 5px;

    &::before,
    &::after {
      width: 12px;
      height: 12px;
      border-width: 2px;
    }
  }

  .subtitle {
    font-size: 0.875rem;
    margin-bottom: 20px;
  }

  .cards-container {
    gap: 12px;
  }

  .nav-card {
    min-height: 140px;
    padding: 16px 10px 14px;
    border-radius: 12px;

    h3 {
      font-size: 14px;
      margin: 10px 0 5px;
    }

    p {
      font-size: 11px;
      -webkit-line-clamp: 3;
    }
  }

  .card-icon {
    width: 44px;
    height: 44px;
    font-size: 22px;
    border-radius: 12px;
  }
}
</style>

<style lang="scss">
.mobile-tip-dialog.el-dialog {
  max-width: 340px;
  border-radius: 16px;
  overflow: hidden;
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(16px);

  .el-dialog__header {
    padding: 20px 20px 8px;
    margin-right: 0;
    text-align: center;

    .el-dialog__title {
      font-size: 17px;
      font-weight: 600;
      color: #ffffff;
      line-height: 1.4;
    }

    .el-dialog__headerbtn {
      top: 14px;
      right: 14px;

      .el-dialog__close {
        color: rgba(255, 255, 255, 0.5);
      }
    }
  }

  .el-dialog__body {
    padding: 4px 24px 8px;
  }

  .el-dialog__footer {
    padding: 8px 20px 20px;

    .dialog-confirm-btn {
      width: 100%;
      height: 40px;
      border-radius: 20px;
      font-size: 15px;
      background: linear-gradient(135deg, #22D3EE, #8B5CF6);
      border: none;
    }
  }
}

.mobile-tip-dialog-body {
  text-align: center;

  .dialog-icon-wrap {
    width: 56px;
    height: 56px;
    margin: 0 auto 14px;
    border-radius: 14px;
    background: linear-gradient(145deg, rgba(34, 211, 238, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
    color: #22D3EE;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
  }

  .dialog-desc {
    margin: 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.65);
    line-height: 1.6;
  }
}
</style>
