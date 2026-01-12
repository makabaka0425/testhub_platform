export default {
  common: {
    confirm: '确定',
    cancel: '取消',
    save: '保存',
    delete: '删除',
    edit: '编辑',
    add: '添加',
    search: '搜索',
    reset: '重置',
    submit: '提交',
    back: '返回',
    view: '查看',
    export: '导出',
    import: '导入',
    download: '下载',
    upload: '上传',
    refresh: '刷新',
    close: '关闭',
    loading: '加载中...',
    success: '操作成功',
    error: '操作失败',
    tips: '提示',
    warning: '警告'
  },
  nav: {
    home: '首页',
    logout: '退出登录',
    profile: '个人设置',
    language: '语言切换'
  },
  modules: {
    aiGeneration: 'AI用例生成',
    apiTesting: '接口测试',
    uiAutomation: 'UI自动化测试',
    aiIntelligentMode: 'AI 智能模式',
    configuration: '配置中心'
  },
  menu: {
    // AI用例生成
    intelligentCaseGeneration: '智能用例生成',
    aiCaseGeneration: 'AI用例生成',
    aiGeneratedTestcases: 'AI生成用例记录',
    promptConfig: '提示词配置',
    projectManagement: '项目管理',
    testCases: '测试用例',
    versionManagement: '版本管理',
    reviewManagement: '评审管理',
    reviewList: '评审列表',
    reviewTemplates: '评审模板',
    testPlan: '测试计划',
    testReport: '测试报告',

    // 接口测试
    dashboard: '数据看板',
    interfaceManagement: '接口管理',
    automationTesting: '自动化测试',
    requestHistory: '请求历史',
    environmentManagement: '环境管理',
    scheduledTasks: '定时任务',
    notificationList: '通知列表',

    // UI自动化
    elementManagement: '元素管理',
    caseManagement: '用例管理',
    scriptGeneration: '脚本生成',
    scriptList: '脚本列表',
    suiteManagement: '套件管理',
    executionRecords: '执行记录',

    // AI智能模式
    aiIntelligentTesting: 'AI 智能测试',
    aiCaseManagement: 'AI 用例管理',
    aiExecutionRecords: 'AI 执行记录',

    // 配置中心
    aiModelConfig: 'AI模型配置',
    uiEnvConfig: 'UI环境配置',
    aiModeConfig: 'AI智能模式配置',
    scheduledTaskConfig: '定时任务配置',
    difyConfig: 'AI评测师配置'
  },
  report: {
    // 页面
    title: '测试报告',
    inDevelopment: '测试报告功能开发中...',

    // 筛选
    selectProject: '选择项目',
    timeRange: '时间范围',
    recentDays: '最近7天',
    recent14Days: '最近14天',
    recent30Days: '最近30天',
    recent90Days: '最近90天',
    customRange: '自定义范围',
    exportReport: '导出报告',

    // 统计卡片
    testPlan: '测试计划',
    activePlans: '活跃计划',
    progress: '进度',
    totalCases: '用例总数',
    passRate: '通过率',
    failedCases: '失败用例',
    defectsFound: '发现缺陷',

    // 图表标题
    executionStatusDistribution: '执行状态分布',
    dailyExecutionTrend: '每日执行趋势',
    failureDistribution: '失败用例优先级分布（缺陷分布）',
    failureTop10: '失败用例 TOP 10',
    aiEffectivenessAnalysis: 'AI生成效能分析',
    teamWorkload: '团队工作量统计',

    // 状态
    passed: '通过',
    failed: '失败',
    blocked: '阻塞',
    retest: '重测',
    untested: '未测',
    executionStatus: '执行状态',

    // AI效能指标
    adoptionRate: '生成采纳率',
    requirementCoverage: '需求覆盖率',
    savedHours: '节省工时估算',
    caseSource: '用例来源',
    aiGenerated: 'AI生成',
    manualCreated: '人工创建',

    // 团队工作量
    executionCount: '执行数量',
    executedCases: '执行用例',
    priorityDistribution: '优先级分布',

    // 其他
    noData: 'No Data',
    caseTitle: '用例标题',
    failureCount: '失败次数',
    exportInDevelopment: '报告导出功能开发中...',
    fetchProjectsFailed: '获取项目失败',
    fetchDashboardFailed: '获取概览数据失败'
  },
  auth: {
    // Login page
    welcomeBack: '欢迎回来',
    loginSubtitle: '登录以继续使用一站式智能化测试平台',
    usernamePlaceholder: '请输入用户名',
    passwordPlaceholder: '请输入密码',
    login: '登录',
    loggingIn: '登录中...',
    noAccount: '还没有账号？',
    signUpNow: '立即注册',
    loginSuccess: '登录成功',
    loginFailed: '登录失败',

    // Register page
    registerTitle: '注册 TestHub',
    registerSubtitle: '创建您的测试管理账号',
    username: '用户名',
    email: '邮箱',
    firstName: '姓',
    lastName: '名',
    password: '密码',
    confirmPassword: '确认密码',
    department: '部门',
    position: '职位',
    register: '注册',
    hasAccount: '已有账号？立即登录',
    registerSuccess: '注册成功，请登录',
    registerFailed: '注册失败',

    // Features
    aiCaseGeneration: 'AI用例生成',
    aiCaseGenerationDesc: '基于自然语言自动生成测试用例',
    aiIntelligentTesting: 'AI智能测试',
    aiIntelligentTestingDesc: '智能分析需求，自动化执行测试',
    multiTypeTesting: '多类型测试',
    multiTypeTestingDesc: '支持接口、UI自动化测试',
    dataAnalysis: '数据分析',
    dataAnalysisDesc: '实时监控测试覆盖率与质量指标',
    automatedExecution: '自动化执行',
    scheduledTasks: '定时任务',

    // Validation messages
    usernameRequired: '请输入用户名',
    usernameLength: '用户名长度在 3 到 20 个字符',
    emailRequired: '请输入邮箱',
    emailFormat: '请输入正确的邮箱格式',
    passwordRequired: '请输入密码',
    passwordLength: '密码长度不能少于6位',
    confirmPasswordRequired: '请确认密码',
    passwordMismatch: '两次输入的密码不一致',

    // Copyright
    copyright: '© 2024 TestHub. All rights reserved.'
  },
  project: {
    // List page
    projectManagement: '项目管理',
    newProject: '新建项目',
    searchPlaceholder: '搜索项目名称',
    statusFilter: '状态筛选',
    projectName: '项目名称',
    description: '描述',
    status: '状态',
    owner: '负责人',
    createdAt: '创建时间',
    actions: '操作',

    // Status
    active: '进行中',
    paused: '已暂停',
    completed: '已完成',
    archived: '已归档',

    // Dialog
    editProject: '编辑项目',
    createProject: '新建项目',
    projectNamePlaceholder: '请输入项目名称',
    projectDescription: '项目描述',
    projectDescriptionPlaceholder: '请输入项目描述',
    selectStatus: '请选择状态',
    update: '更新',
    create: '创建',

    // Validation
    projectNameRequired: '请输入项目名称',
    projectNameLength: '项目名称长度在 2 到 200 个字符',
    projectStatusRequired: '请选择项目状态',

    // Messages
    fetchListFailed: '获取项目列表失败',
    updateSuccess: '项目更新成功',
    createSuccess: '项目创建成功',
    updateFailed: '项目更新失败',
    createFailed: '项目创建失败',
    deleteConfirm: '确定要删除这个项目吗？',
    deleteSuccess: '项目删除成功',
    deleteFailed: '项目删除失败',

    // Detail page
    projectDetail: '项目详情',
    projectInfo: '项目信息',
    noDescription: '暂无描述',
    projectMembers: '项目成员',
    addMember: '添加成员',
    username: '用户名',
    email: '邮箱',
    role: '角色',
    joinedAt: '加入时间',
    removeMember: '删除',
    environments: '环境配置',
    addEnvironment: '添加环境',
    environmentName: '环境名称',
    baseUrl: '基础URL',
    defaultEnvironment: '默认环境',
    yes: '是',
    no: '否',
    fetchDetailFailed: '获取项目详情失败',
    memberDeleteSuccess: '成员删除成功',
    memberDeleteFailed: '删除成员失败'
  },
  home: {
    // Header
    user: '用户',
    logout: '退出登录',
    logoutConfirm: '确定要退出登录吗？',
    logoutSuccess: '已退出登录',

    // Title
    title: 'TestHub 测试平台',
    subtitle: '一站式智能化测试解决方案',

    // Cards
    aiCaseGeneration: 'AI用例生成',
    aiCaseGenerationDesc: '智能分析需求，自动生成测试用例',
    apiTesting: '接口测试',
    apiTestingDesc: '高效的接口自动化测试与管理',
    uiAutomation: 'UI自动化测试',
    uiAutomationDesc: '可视化的Web/App UI自动化测试',
    dataFactory: '数据工厂',
    dataFactoryDesc: '灵活的测试数据构造与管理',
    aiIntelligentMode: 'AI 智能模式',
    aiIntelligentModeDesc: '基于自然语言的智能化测试执行',
    aiEvaluator: 'AI评测师',
    aiEvaluatorDesc: '基于评测师知识库，提供专业软件测试问答',
    configCenter: '配置中心',
    configCenterDesc: '系统环境、AI模型及通知配置',

    // Messages
    featureInDevelopment: '功能正在开发中......'
  },
  profile: {
    // Page
    title: '个人设置',
    basicInfo: '基本信息',
    changePassword: '修改密码',

    // Basic Info
    username: '用户名',
    email: '邮箱',
    name: '姓名',
    department: '部门',
    position: '职位',

    // Password
    currentPassword: '当前密码',
    newPassword: '新密码',
    confirmPassword: '确认密码',
    changePasswordButton: '修改密码'
  },
  version: {
    // Page
    title: '版本管理',
    newVersion: '新建版本',
    batchDelete: '批量删除',
    searchPlaceholder: '搜索版本名称',
    relatedProject: '关联项目',
    versionType: '版本类型',
    baselineVersion: '基线版本',
    normalVersion: '普通版本',

    // Table
    serialNumber: '序号',
    versionName: '版本名称',
    baseline: '基线',
    noProject: '未关联项目',
    description: '描述',
    testCaseCount: '用例数量',
    creator: '创建者',
    createdAt: '创建时间',

    // Dialog
    editVersion: '编辑版本',
    createVersion: '创建版本',
    versionNamePlaceholder: '请输入版本名称',
    selectProjects: '请选择项目（可多选）',
    versionDescription: '版本描述',
    versionDescriptionPlaceholder: '请输入版本描述',
    setAsBaseline: '设为基线版本',

    // Validation
    versionNameRequired: '请输入版本名称',
    projectRequired: '请选择关联项目',

    // Messages
    fetchListFailed: '获取版本列表失败',
    fetchProjectsFailed: '获取项目列表失败',
    updateSuccess: '版本更新成功',
    createSuccess: '版本创建成功',
    saveFailed: '保存失败',
    deleteConfirm: '确定要删除这个版本吗？',
    deleteSuccess: '版本删除成功',
    deleteFailed: '版本删除失败',
    selectVersionsFirst: '请先选择要删除的版本',
    batchDeleteConfirm: '确定要删除选中的 {count} 个版本吗？此操作不可恢复。',
    batchDeleteSuccess: '成功删除 {successCount} 个版本',
    batchDeleteFailed: '批量删除失败'
  },
  testSuite: {
    title: '测试套件',
    newSuite: '新建套件',
    inDevelopment: '测试套件功能开发中...'
  },
  testcase: {
    // Page titles
    title: '测试用例',
    detail: '用例详情',
    edit: '编辑测试用例',
    create: '创建测试用例',

    // Actions
    newCase: '新建用例',
    batchDelete: '批量删除',
    exportExcel: '导出Excel',
    saveChanges: '保存修改',
    createCase: '创建用例',

    // Field labels
    caseTitle: '用例标题',
    caseDescription: '用例描述',
    project: '归属项目',
    relatedProject: '关联项目',
    relatedVersions: '关联版本',
    priority: '优先级',
    status: '状态',
    testType: '测试类型',
    preconditions: '前置条件',
    steps: '操作步骤',
    expectedResult: '预期结果',
    author: '作者',
    createdAt: '创建时间',
    serialNumber: '序号',

    // Priority
    low: '低',
    medium: '中',
    high: '高',
    critical: '紧急',

    // Status
    draft: '草稿',
    active: '激活',
    deprecated: '废弃',

    // Test types
    functional: '功能测试',
    integration: '集成测试',
    api: 'API测试',
    ui: 'UI测试',
    performance: '性能测试',
    security: '安全测试',

    // Placeholders
    searchPlaceholder: '搜索用例标题',
    caseTitlePlaceholder: '请输入测试用例标题',
    caseDescriptionPlaceholder: '请输入用例描述',
    selectProject: '请选择项目',
    selectPriority: '请选择优先级',
    selectTestType: '请选择测试类型',
    selectStatus: '请选择状态',
    selectVersions: '请选择版本（可多选）',
    preconditionsPlaceholder: '请输入前置条件',
    stepsPlaceholder: '请输入详细的操作步骤，如：\n1. 打开登录页面\n2. 输入用户名和密码\n3. 点击登录按钮\n4. 验证登录结果',
    expectedResultPlaceholder: '请输入整体预期结果',
    priorityFilter: '优先级筛选',
    statusFilter: '状态筛选',

    // Messages
    fetchListFailed: '获取测试用例列表失败',
    fetchDetailFailed: '获取用例详情失败',
    deleteConfirm: '确定要删除这个测试用例吗？',
    deleteSuccess: '测试用例删除成功',
    deleteFailed: '测试用例删除失败',
    selectFirst: '请先选择要删除的测试用例',
    batchDeleteConfirm: '确定要删除选中的 {count} 个测试用例吗？此操作不可恢复。',
    batchDeleteSuccess: '成功删除 {successCount} 个测试用例',
    batchDeletePartialSuccess: '成功删除 {successCount} 个测试用例，{failCount} 个失败',
    batchDeleteFailed: '删除失败',
    batchDeleteError: '批量删除失败',
    noDataToExport: '没有测试用例数据可导出',
    exportSuccess: '测试用例导出成功',
    exportFailed: '导出测试用例失败',
    createSuccess: '测试用例创建成功',
    createFailed: '测试用例创建失败',
    updateSuccess: '测试用例修改成功',
    updateFailed: '测试用例修改失败',
    fetchProjectsFailed: '获取项目列表失败',
    fetchVersionsFailed: '获取项目版本失败',

    // Other
    noVersion: '未关联版本',
    noProject: '未关联项目',
    noDescription: '暂无描述',
    none: '无',
    baseline: '基线',

    // Validation
    titleRequired: '请输入用例标题',
    titleLength: '标题长度在 5 到 500 个字符',
    expectedResultRequired: '请输入预期结果',
    stepsMaxLength: '操作步骤不能超过1000个字符',

    // Excel export
    excelNumber: '测试用例编号',
    excelTitle: '用例标题',
    excelProject: '关联项目',
    excelVersions: '关联版本',
    excelPreconditions: '前置条件',
    excelSteps: '操作步骤',
    excelExpectedResult: '预期结果',
    excelPriority: '优先级',
    excelStatus: '状态',
    excelTestType: '测试类型',
    excelAuthor: '作者',
    excelCreatedAt: '创建时间',
    excelSheetName: '测试用例',
    excelFileName: '测试用例_{date}.xlsx'
  }
}
