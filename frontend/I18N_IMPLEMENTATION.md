# 前端国际化实现说明

## 实现概述

本次更新为 TestHub 前端添加了中英文双语切换功能，使用 vue-i18n 实现国际化。

## 实现内容

### 1. 安装依赖

```bash
npm install vue-i18n@9
```

### 2. 创建国际化文件

```
frontend/src/locales/
├── index.js        # i18n 配置入口
├── zh-CN.js        # 简体中文翻译
└── en-US.js        # 英语翻译
```

**locales/index.js** - 创建 i18n 实例，从 localStorage 读取用户语言偏好，默认中文。

**locales/zh-CN.js** 和 **locales/en-US.js** - 包含所有菜单、按钮、提示信息的翻译文本。

### 3. 配置 main.js

修改 `frontend/src/main.js`：
- 引入 vue-i18n 和 Element Plus 英文语言包
- 注册 i18n 插件
- 根据当前语言动态设置 Element Plus 组件语言

### 4. 修改布局组件

修改 `frontend/src/layout/index.vue`：
- 在顶部导航栏的用户信息左侧添加语言切换下拉菜单
- 显示当前语言（中文/EN）
- 点击可切换中英文
- 切换后保存到 localStorage 并刷新页面

## 使用方法

### 基础用法

在 Vue 组件中使用国际化文本：

```vue
<template>
  <!-- 使用 $t 函数 -->
  <div>{{ $t('common.confirm') }}</div>

  <!-- 使用 v-bind -->
  <el-button :label="$t('common.save')">
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// 在 JS 中使用
console.log(t('common.success'))
</script>
```

### 切换语言

用户可以通过以下方式切换语言：
1. 点击顶部导航栏的语言切换按钮
2. 选择"简体中文"或"English"
3. 页面自动刷新应用新语言

### 添加新的翻译

1. 在 `locales/zh-CN.js` 添加中文翻译：
```javascript
export default {
  yourModule: {
    yourKey: '中文文本'
  }
}
```

2. 在 `locales/en-US.js` 添加英文翻译：
```javascript
export default {
  yourModule: {
    yourKey: 'English Text'
  }
}
```

3. 在组件中使用：
```vue
{{ $t('yourModule.yourKey') }}
```

## 已翻译的内容

### 通用文本 (common)
- 操作按钮：确定、取消、保存、删除、编辑、添加等
- 提示信息：加载中、操作成功、操作失败等

### 导航 (nav)
- 首页、退出登录、个人设置、语言切换

### 模块名称 (modules)
- AI用例生成
- 接口测试
- UI自动化测试
- AI 智能模式
- 配置中心

### 菜单项 (menu)
包含所有侧边栏菜单项的中英文翻译。

## 注意事项

1. **刷新机制**：切换语言后会刷新页面以正确应用 Element Plus 组件语言，这会导致页面状态重置。

2. **持久化**：用户选择的语言会保存到 localStorage，下次访问时自动加载。

3. **默认语言**：系统默认使用简体中文。

4. **扩展性**：如需添加更多语言（如日语、韩语），只需：
   - 在 `locales/` 目录添加对应的语言文件（如 `ja-JP.js`）
   - 在 `locales/index.js` 的 `messages` 对象中注册
   - 在布局组件的下拉菜单中添加选项

## 测试方法

### 功能测试

1. 登录系统后，在顶部导航栏找到语言切换按钮（用户头像左侧）
2. 点击按钮，选择"English"，页面刷新后界面变为英文
3. 再次切换回"简体中文"，界面恢复中文
4. 刷新浏览器，语言设置应该保持

### 浏览器控制台测试

```javascript
// 查看当前语言
localStorage.getItem('language')

// 手动切换语言
localStorage.setItem('language', 'en-US')
location.reload()

// 查看 i18n 配置
window.__VUE_I18N__.locale
```

## 未来改进

1. **无刷新切换**：改进 Element Plus 语言动态切换，避免页面刷新
2. **更多翻译**：逐步翻译所有页面文本
3. **自动检测**：根据浏览器语言自动选择默认语言
4. **RTL 支持**：支持阿拉伯语等从右到左的语言
5. **翻译管理**：引入在线翻译管理工具

## 相关文件

- `frontend/src/locales/` - 国际化配置和翻译文件
- `frontend/src/main.js` - i18n 初始化
- `frontend/src/layout/index.vue` - 语言切换按钮
- `frontend/package.json` - vue-i18n 依赖
