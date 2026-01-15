export default {
  requirementAnalysis: {
    // Page
    title: '智能测试用例生成',
    subtitle: '基于需求描述或文档，AI将直接为您生成高质量的测试用例',

    // Manual Input
    manualInputTitle: '✍️ 手动输入需求描述',
    requirementTitle: '需求标题',
    requirementDescription: '需求描述',
    relatedProject: '关联项目（可选）',
    titlePlaceholder: '请输入需求标题，如：用户登录功能需求',
    descriptionPlaceholder: '请详细描述您的需求，包括功能描述、使用场景、业务流程等',
    selectProject: '请选择项目',
    charCount: '{count}/2000',
    generating: '🔄 生成中...',
    generateBtn: '🚀 生成测试用例',

    // Document Upload
    uploadTitle: '📄 上传需求文档',
    dragDropText: '拖拽文件到此处或点击选择文件',
    supportedFormats: '支持 PDF、Word、TXT 格式',
    selectFileBtn: '选择文件',
    removeFile: '❌',
    documentTitle: '文档标题',
    documentTitlePlaceholder: '请输入文档标题',
    fileSize: '文件大小',

    // Generation Options
    generationOptions: '⚙️ 生成选项',
    testCaseCount: '期望生成测试用例数量',
    detailLevel: '详细程度',
    detailSimple: '简要',
    detailNormal: '正常',
    detailDetailed: '详细',
    includeEdgeCases: '包含边界场景',
    includeNegativeCases: '包含异常场景',
    submitGeneration: '提交生成任务',

    // Divider
    dividerOr: '或',

    // Messages
    titleRequired: '请输入需求标题',
    descriptionRequired: '请输入需求描述',
    descriptionTooShort: '需求描述至少需要10个字符',
    fileRequired: '请选择文件',
    generateSuccess: '生成任务已提交！',
    generateFailed: '生成失败',
    uploadSuccess: '文件上传成功',
    uploadFailed: '文件上传失败',

    // Progress
    analyzingRequirement: '📖 分析需求文档中...',
    generatingTestCases: '✍️ 编写测试用例中...',
    reviewingTestCases: '🔍 评审测试用例中...',
    generationComplete: '✅ 生成完成！',
    generationFailed: '❌ 生成失败',

    // Results
    viewResultsBtn: '查看生成结果',
    generateAgainBtn: '重新生成',
    backBtn: '返回',

    // Status
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  },
  generatedTestCases: {
    // Page
    title: 'AI生成用例记录',

    // Filters
    statusFilter: '状态筛选:',
    allStatus: '全部状态',
    pending: '需求分析中',
    generating: '用例编写中',
    reviewing: '用例评审中',
    completed: '已完成',
    failed: '失败',

    // Actions
    batchDelete: '🗑️ 批量删除',
    deleting: '🗑️ 删除中...',
    refresh: '🔄 刷新',
    loading: '🔄 加载中...',

    // Stats
    totalTasks: '任务总数',
    completedTasks: '已完成',
    runningTasks: '进行中',
    failedTasks: '失败',

    // Table Headers
    serialNumber: '序号',
    taskId: '任务ID',
    relatedRequirement: '关联需求',
    status: '状态',
    caseCount: '用例条数',
    generatedTime: '生成时间',
    actions: '操作',

    // Actions
    viewDetail: '查看详情',
    adoptAll: '全部采纳',
    exportExcel: '导出Excel',
    delete: '删除',

    // Empty State
    noTasks: '暂无生成任务',
    noTasksHint: '还没有AI生成用例任务，去',
    noTasksLink: 'AI用例生成',
    noTasksHint2: '页面创建一个任务吧！',

    // Loading
    loadingTasks: '🔄 正在加载任务列表...',

    // Messages
    deleteConfirm: '确定要删除这个任务吗？',
    batchDeleteConfirm: '确定要删除选中的 {count} 个任务吗？此操作不可恢复。',
    deleteSuccess: '删除成功',
    deleteFailed: '删除失败',
    batchDeleteSuccess: '成功删除 {count} 个任务',
    batchDeleteFailed: '批量删除失败',
    adoptAllSuccess: '全部采纳成功',
    adoptAllFailed: '采纳失败',
    exportSuccess: '导出成功',
    exportFailed: '导出失败',
    loadFailed: '加载任务列表失败',

    // Selection
    selectAll: '全选',
    selectedCount: '已选择 {count} 项'
  },
  promptConfig: {
    // Page
    title: '📝 提示词配置',
    subtitle: '配置用于测试用例编写和评审的AI提示词',

    // Section
    configListTitle: '提示词配置列表',
    loadDefaults: '📂 加载默认提示词',
    addConfig: '➕ 添加配置',

    // Config Card
    enabled: '启用',
    disabled: '禁用',
    preview: '👁️ 预览',
    edit: '✏️ 编辑',
    delete: '🗑️ 删除',

    // Config Details
    contentPreview: '提示词内容预览:',
    createdAt: '创建时间:',
    updatedAt: '更新时间:',
    creator: '创建者:',
    unknown: '未知',

    // Modal
    addTitle: '添加提示词配置',
    editTitle: '编辑提示词配置',
    configName: '配置名称',
    configNamePlaceholder: '例如：测试用例编写提示词 v1.0',
    required: '*',
    promptType: '提示词类型',
    testCaseWriter: '测试用例编写',
    testCaseReviewer: '测试用例评审',
    selectType: '请选择类型',
    isActive: '是否启用',
    promptContent: '提示词内容',
    contentPlaceholder: '请输入提示词内容，支持使用变量占位符...',
    contentHint: '提示：可使用 {requirement} {project} 等变量',
    saveBtn: '💾 保存',
    cancelBtn: '取消',
    saving: '💾 保存中...',

    // Preview Modal
    previewTitle: '预览提示词',
    closeBtn: '关闭',

    // Empty State
    noConfigs: '暂无提示词配置',
    noConfigsHint: '请添加提示词配置以自定义AI的行为和输出格式',
    addFirstConfig: '➕ 添加第一个配置',
    loadDefaultsFirst: '📂 加载默认提示词',

    // Messages
    nameRequired: '请输入配置名称',
    typeRequired: '请选择提示词类型',
    contentRequired: '请输入提示词内容',
    saveSuccess: '保存成功',
    saveFailed: '保存失败',
    deleteConfirm: '确定要删除这个配置吗？',
    deleteSuccess: '删除成功',
    deleteFailed: '删除失败',
    loadDefaultsSuccess: '默认提示词加载成功',
    loadDefaultsFailed: '加载默认提示词失败',
    loadConfigsFailed: '加载配置失败'
  }
}
