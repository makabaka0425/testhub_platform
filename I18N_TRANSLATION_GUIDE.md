# TestHub 国际化翻译继续指南

## 📊 当前进度

**已完成：17/65 页面 (26.2%)**

### ✅ 已翻译模块
1. **Auth** (2 files) - Login.vue, Register.vue
2. **Projects** (2 files) - ProjectList.vue, ProjectDetail.vue
3. **Home** (1 file) - Home.vue
4. **Profile** (1 file) - UserProfile.vue
5. **Versions** (1 file) - VersionList.vue
6. **TestSuites** (1 file) - TestSuiteList.vue
7. **Reports** (2 files) - ReportList.vue, AiTestReport.vue
8. **TestCases** (4 files) - TestCaseList.vue, TestCaseForm.vue, TestCaseEdit.vue, TestCaseDetail.vue
9. **Executions** (3 files) - ExecutionList.vue, ExecutionListView.vue, ExecutionDetailView.vue

### 🎯 优先完成目标（用户指定）
**当前任务：翻译3个核心AI页面**
1. RequirementAnalysisView.vue (1267行) - AI用例生成
2. GeneratedTestCaseList.vue (1857行) - AI生成用例列表
3. PromptConfig.vue (1041行) - 提示词配置

### 📋 待翻译模块
- **Reviews** (4 files) - ReviewList.vue, ReviewForm.vue, ReviewDetail.vue, ReviewTemplateList.vue
- **Notification** (2 files)
- **Configuration** (4 files)
- **Assistant** (1 file)
- **Requirement Analysis** (2 more files) - AIModelConfig.vue, TaskDetail.vue
- **API Testing** (13 files)
- **UI Automation** (19 files)

---

## 🛠️ 翻译标准流程

### 步骤1：在locale文件中添加翻译keys

**文件位置：**
- `frontend/src/locales/zh-CN.js`
- `frontend/src/locales/en-US.js`

**标准结构：**
```javascript
// zh-CN.js中添加新模块
export default {
  // ... 现有模块

  moduleName: {
    // Page titles
    title: '页面标题',
    subtitle: '副标题',

    // Actions
    create: '创建',
    edit: '编辑',
    delete: '删除',
    save: '保存',
    cancel: '取消',

    // Form labels
    name: '名称',
    description: '描述',

    // Placeholders
    namePlaceholder: '请输入名称',

    // Table columns
    serialNumber: '序号',
    createdAt: '创建时间',

    // Status options
    active: '激活',
    inactive: '禁用',

    // Messages
    createSuccess: '创建成功',
    createFailed: '创建失败',
    deleteConfirm: '确定要删除吗？',

    // Validation
    nameRequired: '请输入名称'
  }
}
```

**命名规范：**
- 使用camelCase命名
- 按功能分组（titles, actions, labels, messages等）
- 支持变量插值：`'删除 {count} 个项目'`

### 步骤2：翻译Vue文件

#### 2.1 Script部分

**添加useI18n导入：**
```vue
<script setup>
import { useI18n } from 'vue-i18n'
import { computed } from 'vue'  // 如果需要响应式validation

const { t } = useI18n()
</script>
```

**翻译ElMessage调用：**
```javascript
// ❌ 旧代码
ElMessage.success('创建成功')
ElMessage.error('创建失败')

// ✅ 新代码
ElMessage.success(t('moduleName.createSuccess'))
ElMessage.error(t('moduleName.createFailed'))
```

**翻译ElMessageBox：**
```javascript
// ❌ 旧代码
await ElMessageBox.confirm('确定要删除吗？', '警告', {
  confirmButtonText: '确定',
  cancelButtonText: '取消',
  type: 'warning'
})

// ✅ 新代码
await ElMessageBox.confirm(
  t('moduleName.deleteConfirm'),
  t('common.warning'),
  {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }
)
```

**翻译validation rules（使用computed包装）：**
```javascript
// ❌ 旧代码
const rules = {
  name: [
    { required: true, message: '请输入名称', trigger: 'blur' }
  ]
}

// ✅ 新代码
const rules = {
  name: [
    { required: true, message: computed(() => t('moduleName.nameRequired')), trigger: 'blur' }
  ]
}
```

**翻译状态映射函数：**
```javascript
// ❌ 旧代码
const getStatusText = (status) => {
  const map = {
    active: '激活',
    inactive: '禁用'
  }
  return map[status] || status
}

// ✅ 新代码
const getStatusText = (status) => {
  const map = {
    active: t('moduleName.active'),
    inactive: t('moduleName.inactive')
  }
  return map[status] || status
}
```

#### 2.2 Template部分

**页面标题和按钮：**
```vue
<!-- ❌ 旧代码 -->
<h1 class="page-title">用户列表</h1>
<el-button type="primary">新建用户</el-button>

<!-- ✅ 新代码 -->
<h1 class="page-title">{{ $t('moduleName.title') }}</h1>
<el-button type="primary">{{ $t('moduleName.create') }}</el-button>
```

**表格列：**
```vue
<!-- ❌ 旧代码 -->
<el-table-column prop="name" label="名称" width="200" />

<!-- ✅ 新代码 -->
<el-table-column prop="name" :label="$t('moduleName.name')" width="200" />
```

**表单项：**
```vue
<!-- ❌ 旧代码 -->
<el-form-item label="用户名" prop="username">
  <el-input v-model="form.username" placeholder="请输入用户名" />
</el-form-item>

<!-- ✅ 新代码 -->
<el-form-item :label="$t('moduleName.username')" prop="username">
  <el-input v-model="form.username" :placeholder="$t('moduleName.usernamePlaceholder')" />
</el-form-item>
```

**下拉选项：**
```vue
<!-- ❌ 旧代码 -->
<el-option label="激活" value="active" />
<el-option label="禁用" value="inactive" />

<!-- ✅ 新代码 -->
<el-option :label="$t('moduleName.active')" value="active" />
<el-option :label="$t('moduleName.inactive')" value="inactive" />
```

**对话框：**
```vue
<!-- ❌ 旧代码 -->
<el-dialog title="编辑用户" v-model="visible">

<!-- ✅ 新代码 -->
<el-dialog :title="$t('moduleName.editDialog')" v-model="visible">
```

**变量插值：**
```vue
<!-- ❌ 旧代码 -->
<span>已选择 {{ count }} 项</span>

<!-- ✅ 新代码 -->
<span>{{ $t('moduleName.selectedCount', { count }) }}</span>

<!-- 对应locale配置 -->
selectedCount: '已选择 {count} 项'  // zh-CN
selectedCount: 'Selected {count} items'  // en-US
```

---

## 📝 具体翻译任务清单

### 当前优先任务：3个AI核心页面

#### 1. RequirementAnalysisView.vue (AI用例生成)

**需要添加的locale keys (requirementAnalysis模块)：**
```javascript
requirementAnalysis: {
  // Page
  title: '智能测试用例生成',
  subtitle: '基于需求描述或文档，AI将直接为您生成高质量的测试用例',

  // Manual Input Section
  manualInputTitle: '✍️ 手动输入需求描述',
  requirementTitle: '需求标题',
  requirementDescription: '需求描述',
  relatedProject: '关联项目（可选）',
  titlePlaceholder: '请输入需求标题，如：用户登录功能需求',
  descriptionPlaceholder: '请详细描述您的需求...',
  selectProject: '请选择项目',
  generating: '🔄 生成中...',
  generateBtn: '🚀 生成测试用例',

  // Document Upload Section
  uploadTitle: '📄 上传需求文档',
  dragDropText: '拖拽文件到此处或点击选择文件',
  supportedFormats: '支持 PDF、Word、TXT 格式',
  selectFileBtn: '选择文件',
  documentTitle: '文档标题',

  // Generation Options
  generationOptions: '生成选项',
  testCaseCount: '期望生成测试用例数量',
  detailLevel: '详细程度',
  detailSimple: '简要',
  detailNormal: '正常',
  detailDetailed: '详细',
  includeEdgeCases: '包含边界场景',
  includeNegativeCases: '包含异常场景',

  // Messages
  titleRequired: '请输入需求标题',
  descriptionRequired: '请输入需求描述',
  fileRequired: '请选择文件',
  generateSuccess: '生成任务已提交',
  generateFailed: '生成失败',

  // Results
  generatingProgress: '正在生成测试用例，请稍候...',
  generationComplete: '生成完成',
  viewResults: '查看结果'
}
```

**翻译要点：**
1. 有大量emoji表情符号，需要保留
2. 文件上传区域有拖拽功能文案
3. 生成选项有多个配置项需翻译
4. 进度显示和结果展示部分

#### 2. GeneratedTestCaseList.vue (AI生成用例列表)

**需要添加的locale keys：**
```javascript
generatedTestCases: {
  // Page
  title: 'AI生成用例记录',

  // Filters
  statusFilter: '状态筛选',
  allStatus: '全部状态',
  pending: '需求分析中',
  generating: '用例编写中',
  reviewing: '用例评审中',
  completed: '已完成',
  failed: '失败',

  // Actions
  batchDelete: '🗑️ 批量删除',
  refresh: '🔄 刷新',
  loading: '🔄 加载中...',
  deleting: '🗑️ 删除中...',

  // Stats
  totalTasks: '任务总数',
  completedTasks: '已完成',
  runningTasks: '进行中',
  failedTasks: '失败',

  // Table
  serialNumber: '序号',
  taskId: '任务ID',
  relatedRequirement: '关联需求',
  status: '状态',
  caseCount: '用例条数',
  generatedTime: '生成时间',
  actions: '操作',

  // Empty state
  noTasks: '暂无生成任务',
  noTasksHint: '还没有AI生成用例任务，去AI用例生成页面创建一个任务吧！',

  // Messages
  deleteConfirm: '确定要删除这个任务吗？',
  batchDeleteConfirm: '确定要删除选中的 {count} 个任务吗？',
  deleteSuccess: '删除成功',
  deleteFailed: '删除失败'
}
```

**翻译要点：**
1. 有统计卡片展示任务数量
2. 表格有复选框支持批量操作
3. 状态筛选器有多个选项
4. 空状态页面有引导文案

#### 3. PromptConfig.vue (提示词配置)

**需要添加的locale keys：**
```javascript
promptConfig: {
  // Page
  title: '📝 提示词配置',
  subtitle: '配置用于测试用例编写和评审的AI提示词',

  // Section headers
  configList: '提示词配置列表',
  loadDefaults: '📂 加载默认提示词',
  addConfig: '➕ 添加配置',

  // Config card
  enabled: '启用',
  disabled: '禁用',
  preview: '👁️ 预览',
  edit: '✏️ 编辑',
  delete: '🗑️ 删除',
  contentPreview: '提示词内容预览',
  createdAt: '创建时间',
  updatedAt: '更新时间',
  creator: '创建者',

  // Modal
  addConfigTitle: '添加提示词配置',
  editConfigTitle: '编辑提示词配置',
  configName: '配置名称',
  configNamePlaceholder: '例如：测试用例编写提示词 v1.0',
  promptType: '提示词类型',
  testCaseWriter: '测试用例编写',
  testCaseReviewer: '测试用例评审',
  isActive: '是否启用',
  promptContent: '提示词内容',
  contentPlaceholder: '请输入提示词内容...',

  // Empty state
  noConfigs: '暂无提示词配置',
  noConfigsHint: '请添加提示词配置以自定义AI的行为和输出格式',
  addFirstConfig: '➕ 添加第一个配置',

  // Messages
  nameRequired: '请输入配置名称',
  typeRequired: '请选择提示词类型',
  contentRequired: '请输入提示词内容',
  saveSuccess: '保存成功',
  saveFailed: '保存失败',
  deleteConfirm: '确定要删除这个配置吗？',
  deleteSuccess: '删除成功',
  loadDefaultsSuccess: '默认提示词加载成功',
  loadDefaultsFailed: '加载默认提示词失败'
}
```

**翻译要点：**
1. 配置卡片有预览和操作按钮
2. 模态框表单有多个字段
3. 空状态页面有两个操作按钮
4. 加载默认提示词功能

---

## 🔧 Git提交规范

### 提交消息模板
```bash
feat: i18n translation for [Module Name]

Added comprehensive internationalization support for [module description]:

Frontend Changes:
- [File1.vue]: [Description]
- [File2.vue]: [Description]

Locale Files:
- Added [N]+ [module] translation keys to zh-CN.js and en-US.js
- Includes [key categories]

Features:
- [Feature 1]
- [Feature 2]

Progress: X/65 pages completed (Y%)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 提交命令示例
```bash
# Stage文件
git add frontend/src/locales/*.js frontend/src/views/[module]/*.vue

# 查看状态
git status

# 提交
git commit -m "$(cat <<'EOF'
[提交消息内容]
EOF
)"
```

---

## ✅ 质量检查清单

翻译每个文件后，检查：

- [ ] 所有硬编码中文/英文文本都已替换为 `$t()` 或 `t()`
- [ ] Script中导入了 `useI18n` 和必要的 `computed`
- [ ] Validation rules使用 `computed(() => t('key'))`
- [ ] ElMessage/ElMessageBox使用翻译key
- [ ] 表格列的label使用 `:label="$t('key')"`
- [ ] 表单项的label和placeholder都已翻译
- [ ] 下拉选项的label使用 `:label` 绑定
- [ ] 对话框title使用 `:title` 绑定
- [ ] 变量插值正确使用 `t('key', { var })`
- [ ] 中英文翻译keys数量一致且结构相同
- [ ] 运行`npm run dev`确保无语法错误
- [ ] 在浏览器中测试语言切换功能

---

## 🚀 快速开始命令

```bash
# 1. 进入前端目录
cd /Users/qudong/Code/testhub_platform/frontend

# 2. 启动开发服务器（如未运行）
npm run dev

# 3. 打开浏览器测试
# http://localhost:5173

# 4. 切换语言测试
# 点击顶部导航栏的语言切换按钮（中文/EN）

# 5. 提交更改
git add frontend/src/locales/*.js frontend/src/views/**/*.vue
git status
git commit -m "..."
```

---

## 📞 遇到问题？

### 常见问题

**Q: 翻译后页面显示 `moduleName.keyName` 而不是翻译文本？**
A: 检查locale文件中是否正确添加了对应的key，注意大小写和层级结构。

**Q: Validation消息没有实时切换语言？**
A: 确保使用了 `computed(() => t('key'))` 包装，而不是直接 `t('key')`。

**Q: 变量插值不显示？**
A: 检查locale中的占位符格式是否为 `{varName}`，调用时是否传递了对应变量。

**Q: 提交时出现冲突？**
A: 先 `git pull` 拉取最新代码，解决冲突后再提交。

---

## 📊 进度跟踪

使用以下命令查看翻译进度：

```bash
# 统计已翻译文件数
git log --oneline | grep "i18n translation" | wc -l

# 查看最近的翻译提交
git log --oneline --grep="i18n" -10

# 查看待翻译文件
find frontend/src/views -name "*.vue" -exec grep -l "label=\"[^:$]*\"" {} \; | wc -l
```

---

## 🎯 下一步行动

1. **完成3个优先AI页面**（当前任务）
   - RequirementAnalysisView.vue
   - GeneratedTestCaseList.vue
   - PromptConfig.vue

2. **继续Reviews模块**（4 files）
3. **继续其他requirement-analysis文件**（2 files）
4. **继续Configuration模块**（4 files）
5. **继续API Testing模块**（13 files）
6. **继续UI Automation模块**（19 files）

---

**文档创建时间：** 2026-01-12
**最后更新：** Session继续前
**当前进度：** 17/65 (26.2%)
**目标：** 完成全部65个页面的国际化翻译
