*我已经修复了 AI 用例生成任务详情页面的白屏问题。*

### *问题分析*

* ***现象**: 访问* *`/ai-generation/task-detail/:id`* *页面时显示空白。*

* ***原因**: 页面在数据加载完成前渲染了状态信息。`getStatusText`* *方法被调用时传入了* *`undefined`（因为* *`task`* *数据尚未返回），而该方法直接对输入执行了* *`status.charAt(0)`* *操作，导致 JavaScript 抛出* *`TypeError`，从而导致整个 Vue 组件渲染失败。*

### *修复内容*

1. ***修复*** ***`frontend/src/views/requirement-analysis/TaskDetail.vue`**:*

   * *修改* *`getStatusText`* *方法，增加了空值检查* *`if (!status) return ''`，防止运行时错误。*

   * *优化了标题显示逻辑，在任务标题加载前不显示多余的连字符。*

2. ***代码清理**:*

   * *清理了* *`frontend/src/locales/lang/zh-cn/requirement.js`* *中重复定义的国际化键值对。*

### 验证

* 修复后，即使在数据加载期间，`getStatusText` 也会安全返回空字符串，页面将正常渲染加载状态，待数据返回后自动更新显示内容。

* 检查了列表页 `GeneratedTestCaseList.vue`，确认其实现方式安全，不受此问题影响。

