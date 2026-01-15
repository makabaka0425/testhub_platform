# 🚀 国际化翻译快速上手

## 5分钟入门教程

### 步骤 1: 查看现有翻译结构

```bash
# 查看已有的翻译key
cat frontend/src/locales/zh-CN.js
```

你会看到类似结构：
```javascript
export default {
  common: { /* 通用文本 */ },
  nav: { /* 导航 */ },
  menu: { /* 菜单 */ },
  report: { /* 测试报告 - 已添加 */ }
}
```

### 步骤 2: 找一个简单页面开始

推荐从项目列表页面开始，找到文件：
```bash
# 查找项目相关的 Vue 文件
find frontend/src/views -name "*project*" -o -name "*Project*" | grep -v node_modules
```

### 步骤 3: 识别需要翻译的文本

打开页面文件，找到所有硬编码的中文：
```vue
<!-- 这些需要翻译 ⬇️ -->
<el-button>创建项目</el-button>
<h2>项目列表</h2>
<el-table-column label="项目名称" />
```

### 步骤 4: 添加翻译 key

**在 `frontend/src/locales/zh-CN.js` 添加：**
```javascript
export default {
  // ... 其他内容
  project: {
    projectList: '项目列表',
    createProject: '创建项目',
    projectName: '项目名称',
    projectDesc: '项目描述',
    createdTime: '创建时间'
  }
}
```

**在 `frontend/src/locales/en-US.js` 添加：**
```javascript
export default {
  // ... 其他内容
  project: {
    projectList: 'Project List',
    createProject: 'Create Project',
    projectName: 'Project Name',
    projectDesc: 'Project Description',
    createdTime: 'Created Time'
  }
}
```

### 步骤 5: 修改 Vue 组件

```vue
<template>
  <div>
    <!-- 修改前 -->
    <h2>项目列表</h2>
    <el-button>创建项目</el-button>

    <!-- 修改后 ✅ -->
    <h2>{{ $t('project.projectList') }}</h2>
    <el-button>{{ $t('project.createProject') }}</el-button>

    <el-table :data="projects">
      <!-- 修改前 -->
      <el-table-column label="项目名称" prop="name" />

      <!-- 修改后 ✅ -->
      <el-table-column :label="$t('project.projectName')" prop="name" />
    </el-table>
  </div>
</template>

<script setup>
// 不需要额外导入，$t 在模板中全局可用

// 如果在 script 中使用，需要导入
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// 在代码中使用
const showMessage = () => {
  ElMessage.success(t('common.success'))
}
</script>
```

### 步骤 6: 测试

1. **保存文件** - Vite 会自动热更新
2. **刷新浏览器** - 打开 http://localhost:3000
3. **点击语言切换按钮**，切换到英文
4. **检查页面** - 文本是否变成英文

---

## 📝 常见模式

### 模式 1: 简单文本
```vue
<div>{{ $t('module.key') }}</div>
```

### 模式 2: 按钮文本
```vue
<el-button>{{ $t('module.buttonText') }}</el-button>
```

### 模式 3: 表格列名
```vue
<el-table-column :label="$t('module.columnName')" prop="field" />
```

### 模式 4: 表单标签
```vue
<el-form-item :label="$t('module.fieldName')">
  <el-input v-model="form.field" />
</el-form-item>
```

### 模式 5: 对话框
```vue
<el-dialog :title="$t('module.dialogTitle')">
  <p>{{ $t('module.dialogContent') }}</p>
  <template #footer>
    <el-button @click="close">{{ $t('common.cancel') }}</el-button>
    <el-button type="primary" @click="confirm">{{ $t('common.confirm') }}</el-button>
  </template>
</el-dialog>
```

### 模式 6: 消息提示
```vue
<script setup>
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'

const { t } = useI18n()

const deleteProject = async () => {
  try {
    await ElMessageBox.confirm(
      t('project.deleteConfirm'),
      t('common.warning'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
    // 删除逻辑
    ElMessage.success(t('common.success'))
  } catch {
    ElMessage.info(t('common.cancel'))
  }
}
</script>
```

### 模式 7: 动态文本（带变量）
```javascript
// 翻译文件
{
  project: {
    memberCount: '共 {count} 个成员',
    deleteConfirm: '确定要删除项目 {name} 吗？'
  }
}
```

```vue
<template>
  <div>{{ $t('project.memberCount', { count: members.length }) }}</div>
</template>

<script setup>
const { t } = useI18n()

const confirmDelete = () => {
  const message = t('project.deleteConfirm', { name: project.name })
  ElMessageBox.confirm(message, ...)
}
</script>
```

---

## 🔍 实用工具命令

### 查找包含中文的文件
```bash
# 在 views 目录搜索中文
grep -rl "[\u4e00-\u9fa5]" frontend/src/views/

# 显示行号
grep -rn "[\u4e00-\u9fa5]" frontend/src/views/projects/

# 只看按钮文本
grep -rn "<el-button.*>.*[\u4e00-\u9fa5]" frontend/src/views/
```

### 查看某个文件的中文内容
```bash
# 提取所有中文文本
grep -o "[\u4e00-\u9fa5].*[\u4e00-\u9fa5]" frontend/src/views/projects/ProjectList.vue
```

### 统计翻译进度
```bash
# 统计还有多少文件包含中文
grep -rl "[\u4e00-\u9fa5]" frontend/src/views/ | wc -l
```

---

## ✅ 检查清单

翻译完一个页面后，检查：

- [ ] 所有按钮文本已翻译
- [ ] 所有表格列名已翻译
- [ ] 所有表单标签已翻译
- [ ] 所有提示消息已翻译
- [ ] 所有对话框标题和内容已翻译
- [ ] 在中文模式下测试功能正常
- [ ] 切换到英文模式测试显示正确
- [ ] 翻译文本没有截断或溢出
- [ ] 提交代码前运行 `npm run lint`

---

## 🐛 常见问题

### 问题 1: 页面没有变化
**原因**: 缓存问题或语法错误

**解决**:
```bash
# 1. 硬刷新浏览器 (Ctrl+Shift+R / Cmd+Shift+R)
# 2. 清除缓存重启开发服务器
cd frontend
rm -rf node_modules/.vite
npm run dev
# 3. 检查浏览器控制台是否有错误
```

### 问题 2: 显示 key 而不是翻译文本
**原因**: 翻译 key 不存在或路径错误

**检查**:
```vue
<!-- 错误 ❌ -->
<div>{{ $t('project.notExist') }}</div>

<!-- 正确 ✅ -->
<div>{{ $t('project.projectName') }}</div>
```

打开浏览器控制台查看警告信息。

### 问题 3: 部分文本没翻译
**原因**: 可能是动态生成的文本

**解决**: 使用 computed 属性
```vue
<script setup>
const statusText = computed(() => {
  const map = {
    pending: t('status.pending'),
    active: t('status.active'),
    completed: t('status.completed')
  }
  return map[status.value]
})
</script>

<template>
  <div>{{ statusText }}</div>
</template>
```

---

## 📦 提交规范

```bash
# 1. 查看修改
git status
git diff

# 2. 添加修改的文件
git add frontend/src/locales/
git add frontend/src/views/projects/

# 3. 提交
git commit -m "i18n: 翻译项目管理页面

- 添加 project 翻译 key
- 修改项目列表组件使用 i18n
- 修改项目详情组件使用 i18n
- 测试中英文切换正常"

# 4. 推送
git push
```

---

## 💡 进阶技巧

### 技巧 1: 使用 VS Code 插件

安装 **i18n Ally** 插件:
```bash
code --install-extension lokalise.i18n-ally
```

功能:
- 在代码中直接显示翻译文本
- 快速跳转到翻译文件
- 高亮未翻译的 key

### 技巧 2: 批量替换

使用 VS Code 的查找替换 (Cmd/Ctrl + H):

**查找**: `<el-button>(.*?)</el-button>`
**替换**: `<el-button>{{ $t('module.$1') }}</el-button>`

（需要手动调整 module 和 key）

### 技巧 3: 组件级翻译命名空间

```vue
<script setup>
import { useI18n } from 'vue-i18n'

// 使用命名空间
const { t } = useI18n({
  messages: {
    'zh-CN': {
      title: '项目列表',
      button: '创建'
    },
    'en-US': {
      title: 'Project List',
      button: 'Create'
    }
  }
})
</script>

<template>
  <h2>{{ t('title') }}</h2>
</template>
```

---

## 📞 需要帮助？

1. **查看完整文档**: `frontend/PAGE_I18N_GUIDE.md`
2. **参考示例**: `frontend/src/layout/index.vue`
3. **检查翻译文件**: `frontend/src/locales/`
4. **查看 vue-i18n 文档**: https://vue-i18n.intlify.dev/

---

## 🎯 建议的工作流程

1. **选一个页面** (从简单的开始)
2. **列出需要翻译的文本** (浏览页面记录)
3. **添加翻译 key** (先完成翻译文件)
4. **修改组件** (逐个替换)
5. **测试** (中英文都要测试)
6. **提交** (一个页面一次提交)
7. **重复** (继续下一个页面)

---

**预计时间**: 每个简单页面 15-30 分钟，复杂页面 30-60 分钟

**开始吧！Good luck! 🚀**
