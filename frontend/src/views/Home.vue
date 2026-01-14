<template>
  <div class="home-container">
    <div class="content-wrapper">
      <div class="header-actions">
        <el-dropdown @command="handleLanguageChange" class="language-dropdown">
          <span class="el-dropdown-link">
            <span class="language-icon">{{ currentLanguage === 'zh-CN' ? '🇨🇳' : '🇺🇸' }}</span>
            <span class="language-text">{{ currentLanguage === 'zh-CN' ? '中文' : 'English' }}</span>
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="zh-CN" :disabled="currentLanguage === 'zh-CN'">
                <span class="dropdown-flag">🇨🇳</span> 简体中文
              </el-dropdown-item>
              <el-dropdown-item command="en-US" :disabled="currentLanguage === 'en-US'">
                <span class="dropdown-flag">🇺🇸</span> English
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
      <h1 class="main-title">{{ $t('home.title') }}</h1>
      <p class="subtitle">{{ $t('home.subtitle') }}</p>

      <div class="cards-container">
        <!-- AI用例生成 -->
        <div class="nav-card" @click="handleNavigate('ai')" role="button" tabindex="0">
          <div class="card-icon ai-icon">
            <el-icon><MagicStick /></el-icon>
          </div>
          <h3>{{ $t('home.aiCaseGeneration') }}</h3>
          <p>{{ $t('home.aiCaseGenerationDesc') }}</p>
        </div>

        <!-- 接口测试 -->
        <div class="nav-card" @click="handleNavigate('api')" role="button" tabindex="0">
          <div class="card-icon api-icon">
            <el-icon><Link /></el-icon>
          </div>
          <h3>{{ $t('home.apiTesting') }}</h3>
          <p>{{ $t('home.apiTestingDesc') }}</p>
        </div>

        <!-- UI自动化测试 -->
        <div class="nav-card" @click="handleNavigate('ui')" role="button" tabindex="0">
          <div class="card-icon ui-icon">
            <el-icon><Monitor /></el-icon>
          </div>
          <h3>{{ $t('home.uiAutomation') }}</h3>
          <p>{{ $t('home.uiAutomationDesc') }}</p>
        </div>

        <!-- 数据工厂 -->
        <div class="nav-card" @click="handleNavigate('data')" role="button" tabindex="0">
          <div class="card-icon data-icon">
            <el-icon><DataLine /></el-icon>
          </div>
          <h3>{{ $t('home.dataFactory') }}</h3>
          <p>{{ $t('home.dataFactoryDesc') }}</p>
        </div>
        <!-- AI 智能模式 -->
        <div class="nav-card" @click="handleNavigate('ai-intelligent')" role="button" tabindex="0">
          <div class="card-icon ai-intelligent-icon">
            <el-icon><Cpu /></el-icon>
          </div>
          <h3>{{ $t('home.aiIntelligentMode') }}</h3>
          <p>{{ $t('home.aiIntelligentModeDesc') }}</p>
        </div>
        <!-- AI评测师 -->
        <div class="nav-card" @click="handleNavigate('assistant')" role="button" tabindex="0">
          <div class="card-icon assistant-icon">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <h3>{{ $t('home.aiEvaluator') }}</h3>
          <p>{{ $t('home.aiEvaluatorDesc') }}</p>
        </div>
        <!-- 配置中心 -->
        <div class="nav-card" @click="handleNavigate('config')" role="button" tabindex="0">
          <div class="card-icon config-icon">
            <el-icon><Setting /></el-icon>
          </div>
          <h3>{{ $t('home.configCenter') }}</h3>
          <p>{{ $t('home.configCenterDesc') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Link, Monitor, DataLine, Cpu, Setting, ChatDotRound, UserFilled, ArrowDown } from '@element-plus/icons-vue'

const router = useRouter()
const { t, locale } = useI18n()
const userStore = useUserStore()

// 当前语言
const currentLanguage = computed(() => locale.value)

// 语言切换
const handleLanguageChange = (lang) => {
  locale.value = lang
  localStorage.setItem('language', lang)

  // 刷新页面以更新 Element Plus 的语言
  window.location.reload()
}

const handleCommand = (command) => {
  if (command === 'logout') {
    handleLogout()
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
    'ai-intelligent': '/ai-intelligent-mode/testing',
    'assistant': '/ai-generation/assistant',
    'config': '/configuration/ai-model'
  }

  if (type === 'data') {
    ElMessage.info(t('home.featureInDevelopment'))
    return
  }

  if (routes[type]) {
    const routeData = router.resolve({ path: routes[type] })
    window.open(routeData.href, '_blank')
  }
}
</script>

<style scoped lang="scss">
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.content-wrapper {
  text-align: center;
  max-width: 1200px;
  width: 100%;
  position: relative;
}

.header-actions {
  position: absolute;
  top: 0;
  right: 0;
  padding: 10px;
  display: flex;
  align-items: center;
  gap: 20px;

  .language-dropdown {
    .el-dropdown-link {
      display: flex;
      align-items: center;
      cursor: pointer;
      color: #5e6d82;
      transition: color 0.3s;
      outline: none;

      &:focus {
        outline: none;
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

      &:hover {
        color: #409eff;
      }
    }
  }

  .el-dropdown-link {
    display: flex;
    align-items: center;
    cursor: pointer;
    color: #5e6d82;
    transition: color 0.3s;
    outline: none;

    &:focus {
      outline: none;
    }

    .username {
      margin: 0 8px;
      font-size: 14px;
    }

    &:hover {
      color: #409eff;
    }
  }
}

.dropdown-flag {
  font-size: 16px;
  margin-right: 5px;
}

.main-title {
  font-size: 3.5rem;
  color: #2c3e50;
  margin-bottom: 1rem;
  font-weight: 700;
  letter-spacing: 2px;
}

.subtitle {
  font-size: 1.5rem;
  color: #5e6d82;
  margin-bottom: 4rem;
}

.cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 30px;
  padding: 20px;
}

.nav-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  padding: 40px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  align-items: center;

  &:hover {
    transform: translateY(-10px);
    box-shadow: 0 20px 30px rgba(0, 0, 0, 0.1);
    background: #fff;
  }

  h3 {
    font-size: 1.5rem;
    color: #2c3e50;
    margin: 20px 0 10px;
  }

  p {
    color: #7f8c8d;
    line-height: 1.5;
    margin: 0;
  }
}

.card-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  margin-bottom: 10px;
  transition: all 0.3s ease;

  &.ai-icon {
    background: #e8f4ff;
    color: #409eff;
  }

  &.api-icon {
    background: #f0f9eb;
    color: #67c23a;
  }

  &.ui-icon {
    background: #fdf6ec;
    color: #e6a23c;
  }

  &.data-icon {
    background: #f4f4f5;
    color: #909399;
  }

  &.ai-intelligent-icon {
    background: #f0f5ff;
    color: #2f54eb;
  }

  &.config-icon {
    background: #e6fffb;
    color: #13c2c2;
  }

  &.assistant-icon {
    background: #fff7e6;
    color: #fa8c16;
  }
}

.nav-card:hover .card-icon {
  transform: scale(1.1);
}
</style>
