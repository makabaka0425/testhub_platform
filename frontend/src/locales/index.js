import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'
import enUS from './en-US'

// 从 localStorage 获取语言设置，默认中文
const getLanguage = () => {
  const lang = localStorage.getItem('language')
  if (lang) {
    return lang
  }
  // 默认使用中文
  return 'zh-CN'
}

const i18n = createI18n({
  legacy: false, // 使用 Composition API 模式
  locale: getLanguage(), // 设置默认语言
  fallbackLocale: 'zh-CN', // 设置备用语言
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  }
})

export default i18n
