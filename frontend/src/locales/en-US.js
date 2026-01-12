export default {
  common: {
    confirm: 'Confirm',
    cancel: 'Cancel',
    save: 'Save',
    delete: 'Delete',
    edit: 'Edit',
    add: 'Add',
    search: 'Search',
    reset: 'Reset',
    submit: 'Submit',
    back: 'Back',
    view: 'View',
    export: 'Export',
    import: 'Import',
    download: 'Download',
    upload: 'Upload',
    refresh: 'Refresh',
    close: 'Close',
    loading: 'Loading...',
    success: 'Operation successful',
    error: 'Operation failed',
    tips: 'Tips',
    warning: 'Warning'
  },
  nav: {
    home: 'Home',
    logout: 'Logout',
    profile: 'Profile',
    language: 'Language'
  },
  modules: {
    aiGeneration: 'AI Test Case Generation',
    apiTesting: 'API Testing',
    uiAutomation: 'UI Automation Testing',
    aiIntelligentMode: 'AI Intelligent Mode',
    configuration: 'Configuration Center'
  },
  menu: {
    // AI Test Case Generation
    intelligentCaseGeneration: 'Intelligent Case Generation',
    aiCaseGeneration: 'AI Case Generation',
    aiGeneratedTestcases: 'AI Generated Test Cases',
    promptConfig: 'Prompt Configuration',
    projectManagement: 'Project Management',
    testCases: 'Test Cases',
    versionManagement: 'Version Management',
    reviewManagement: 'Review Management',
    reviewList: 'Review List',
    reviewTemplates: 'Review Templates',
    testPlan: 'Test Plan',
    testReport: 'Test Report',

    // API Testing
    dashboard: 'Dashboard',
    interfaceManagement: 'Interface Management',
    automationTesting: 'Automation Testing',
    requestHistory: 'Request History',
    environmentManagement: 'Environment Management',
    scheduledTasks: 'Scheduled Tasks',
    notificationList: 'Notification List',

    // UI Automation
    elementManagement: 'Element Management',
    caseManagement: 'Case Management',
    scriptGeneration: 'Script Generation',
    scriptList: 'Script List',
    suiteManagement: 'Suite Management',
    executionRecords: 'Execution Records',

    // AI Intelligent Mode
    aiIntelligentTesting: 'AI Intelligent Testing',
    aiCaseManagement: 'AI Case Management',
    aiExecutionRecords: 'AI Execution Records',

    // Configuration Center
    aiModelConfig: 'AI Model Configuration',
    uiEnvConfig: 'UI Environment Configuration',
    aiModeConfig: 'AI Mode Configuration',
    scheduledTaskConfig: 'Scheduled Task Configuration',
    difyConfig: 'Dify Configuration'
  },
  report: {
    // Page
    title: 'Test Report',
    inDevelopment: 'Test report feature under development...',

    // Filters
    selectProject: 'Select Project',
    timeRange: 'Time Range',
    recentDays: 'Last 7 Days',
    recent14Days: 'Last 14 Days',
    recent30Days: 'Last 30 Days',
    recent90Days: 'Last 90 Days',
    customRange: 'Custom Range',
    exportReport: 'Export Report',

    // Stats Cards
    testPlan: 'Test Plan',
    activePlans: 'Active Plans',
    progress: 'Progress',
    totalCases: 'Total Cases',
    passRate: 'Pass Rate',
    failedCases: 'Failed Cases',
    defectsFound: 'Defects Found',

    // Chart Titles
    executionStatusDistribution: 'Execution Status Distribution',
    dailyExecutionTrend: 'Daily Execution Trend',
    failureDistribution: 'Failed Cases Priority Distribution (Defect Distribution)',
    failureTop10: 'Failed Cases TOP 10',
    aiEffectivenessAnalysis: 'AI Generation Effectiveness Analysis',
    teamWorkload: 'Team Workload Statistics',

    // Status
    passed: 'Passed',
    failed: 'Failed',
    blocked: 'Blocked',
    retest: 'Retest',
    untested: 'Untested',
    executionStatus: 'Execution Status',

    // AI Effectiveness Metrics
    adoptionRate: 'Adoption Rate',
    requirementCoverage: 'Requirement Coverage',
    savedHours: 'Saved Hours',
    caseSource: 'Case Source',
    aiGenerated: 'AI Generated',
    manualCreated: 'Manual Created',

    // Team Workload
    executionCount: 'Execution Count',
    executedCases: 'Executed Cases',
    priorityDistribution: 'Priority Distribution',

    // Others
    noData: 'No Data',
    caseTitle: 'Case Title',
    failureCount: 'Failure Count',
    exportInDevelopment: 'Report export feature under development...',
    fetchProjectsFailed: 'Failed to fetch projects',
    fetchDashboardFailed: 'Failed to fetch dashboard data'
  },
  auth: {
    // Login page
    welcomeBack: 'Welcome Back',
    loginSubtitle: 'Sign in to continue with the all-in-one intelligent testing platform',
    usernamePlaceholder: 'Enter username',
    passwordPlaceholder: 'Enter password',
    login: 'Login',
    loggingIn: 'Logging in...',
    noAccount: "Don't have an account? ",
    signUpNow: 'Sign up now',
    loginSuccess: 'Login successful',
    loginFailed: 'Login failed',

    // Register page
    registerTitle: 'Register TestHub',
    registerSubtitle: 'Create your test management account',
    username: 'Username',
    email: 'Email',
    firstName: 'First Name',
    lastName: 'Last Name',
    password: 'Password',
    confirmPassword: 'Confirm Password',
    department: 'Department',
    position: 'Position',
    register: 'Register',
    hasAccount: 'Already have an account? Login now',
    registerSuccess: 'Registration successful, please login',
    registerFailed: 'Registration failed',

    // Features
    aiCaseGeneration: 'AI Case Generation',
    aiCaseGenerationDesc: 'Auto-generate test cases from natural language',
    aiIntelligentTesting: 'AI Intelligent Testing',
    aiIntelligentTestingDesc: 'Intelligently analyze requirements and automate testing',
    multiTypeTesting: 'Multi-Type Testing',
    multiTypeTestingDesc: 'Support API and UI automation testing',
    dataAnalysis: 'Data Analysis',
    dataAnalysisDesc: 'Real-time monitoring of test coverage and quality metrics',
    automatedExecution: 'Automated Execution',
    scheduledTasks: 'Scheduled Tasks',

    // Validation messages
    usernameRequired: 'Please enter username',
    usernameLength: 'Username length must be between 3 and 20 characters',
    emailRequired: 'Please enter email',
    emailFormat: 'Please enter a valid email',
    passwordRequired: 'Please enter password',
    passwordLength: 'Password must be at least 6 characters',
    confirmPasswordRequired: 'Please confirm password',
    passwordMismatch: 'Passwords do not match',

    // Copyright
    copyright: '© 2024 TestHub. All rights reserved.'
  },
  project: {
    // List page
    projectManagement: 'Project Management',
    newProject: 'New Project',
    searchPlaceholder: 'Search project name',
    statusFilter: 'Status Filter',
    projectName: 'Project Name',
    description: 'Description',
    status: 'Status',
    owner: 'Owner',
    createdAt: 'Created At',
    actions: 'Actions',

    // Status
    active: 'Active',
    paused: 'Paused',
    completed: 'Completed',
    archived: 'Archived',

    // Dialog
    editProject: 'Edit Project',
    createProject: 'New Project',
    projectNamePlaceholder: 'Enter project name',
    projectDescription: 'Project Description',
    projectDescriptionPlaceholder: 'Enter project description',
    selectStatus: 'Select status',
    update: 'Update',
    create: 'Create',

    // Validation
    projectNameRequired: 'Please enter project name',
    projectNameLength: 'Project name length must be between 2 and 200 characters',
    projectStatusRequired: 'Please select project status',

    // Messages
    fetchListFailed: 'Failed to fetch project list',
    updateSuccess: 'Project updated successfully',
    createSuccess: 'Project created successfully',
    updateFailed: 'Failed to update project',
    createFailed: 'Failed to create project',
    deleteConfirm: 'Are you sure to delete this project?',
    deleteSuccess: 'Project deleted successfully',
    deleteFailed: 'Failed to delete project',

    // Detail page
    projectDetail: 'Project Details',
    projectInfo: 'Project Info',
    noDescription: 'No description',
    projectMembers: 'Project Members',
    addMember: 'Add Member',
    username: 'Username',
    email: 'Email',
    role: 'Role',
    joinedAt: 'Joined At',
    removeMember: 'Remove',
    environments: 'Environments',
    addEnvironment: 'Add Environment',
    environmentName: 'Environment Name',
    baseUrl: 'Base URL',
    defaultEnvironment: 'Default Environment',
    yes: 'Yes',
    no: 'No',
    fetchDetailFailed: 'Failed to fetch project details',
    memberDeleteSuccess: 'Member deleted successfully',
    memberDeleteFailed: 'Failed to delete member'
  },
  home: {
    // Header
    user: 'User',
    logout: 'Logout',
    logoutConfirm: 'Are you sure to logout?',
    logoutSuccess: 'Logged out successfully',

    // Title
    title: 'TestHub Testing Platform',
    subtitle: 'All-in-One Intelligent Testing Solution',

    // Cards
    aiCaseGeneration: 'AI Case Generation',
    aiCaseGenerationDesc: 'Intelligently analyze requirements, auto-generate test cases',
    apiTesting: 'API Testing',
    apiTestingDesc: 'Efficient API automation testing and management',
    uiAutomation: 'UI Automation Testing',
    uiAutomationDesc: 'Visual Web/App UI automation testing',
    dataFactory: 'Data Factory',
    dataFactoryDesc: 'Flexible test data construction and management',
    aiIntelligentMode: 'AI Intelligent Mode',
    aiIntelligentModeDesc: 'Natural language-based intelligent test execution',
    aiEvaluator: 'AI Evaluator',
    aiEvaluatorDesc: 'Professional software testing Q&A based on evaluator knowledge base',
    configCenter: 'Configuration Center',
    configCenterDesc: 'System environment, AI model and notification configuration',

    // Messages
    featureInDevelopment: 'Feature is under development......'
  },
  profile: {
    // Page
    title: 'Profile Settings',
    basicInfo: 'Basic Information',
    changePassword: 'Change Password',

    // Basic Info
    username: 'Username',
    email: 'Email',
    name: 'Name',
    department: 'Department',
    position: 'Position',

    // Password
    currentPassword: 'Current Password',
    newPassword: 'New Password',
    confirmPassword: 'Confirm Password',
    changePasswordButton: 'Change Password'
  },
  version: {
    // Page
    title: 'Version Management',
    newVersion: 'New Version',
    batchDelete: 'Batch Delete',
    searchPlaceholder: 'Search version name',
    relatedProject: 'Related Project',
    versionType: 'Version Type',
    baselineVersion: 'Baseline Version',
    normalVersion: 'Normal Version',

    // Table
    serialNumber: 'No.',
    versionName: 'Version Name',
    baseline: 'Baseline',
    noProject: 'No Project',
    description: 'Description',
    testCaseCount: 'Test Cases',
    creator: 'Creator',
    createdAt: 'Created At',

    // Dialog
    editVersion: 'Edit Version',
    createVersion: 'Create Version',
    versionNamePlaceholder: 'Enter version name',
    selectProjects: 'Select projects (multiple)',
    versionDescription: 'Version Description',
    versionDescriptionPlaceholder: 'Enter version description',
    setAsBaseline: 'Set as baseline version',

    // Validation
    versionNameRequired: 'Please enter version name',
    projectRequired: 'Please select related project',

    // Messages
    fetchListFailed: 'Failed to fetch version list',
    fetchProjectsFailed: 'Failed to fetch project list',
    updateSuccess: 'Version updated successfully',
    createSuccess: 'Version created successfully',
    saveFailed: 'Failed to save',
    deleteConfirm: 'Are you sure to delete this version?',
    deleteSuccess: 'Version deleted successfully',
    deleteFailed: 'Failed to delete version',
    selectVersionsFirst: 'Please select versions to delete first',
    batchDeleteConfirm: 'Are you sure to delete selected {count} versions? This action cannot be undone.',
    batchDeleteSuccess: 'Successfully deleted {successCount} versions',
    batchDeleteFailed: 'Batch delete failed'
  },
  testSuite: {
    title: 'Test Suites',
    newSuite: 'New Suite',
    inDevelopment: 'Test suite feature is under development...'
  },
  testcase: {
    // Page titles
    title: 'Test Cases',
    detail: 'Test Case Details',
    edit: 'Edit Test Case',
    create: 'Create Test Case',

    // Actions
    newCase: 'New Case',
    batchDelete: 'Batch Delete',
    exportExcel: 'Export Excel',
    saveChanges: 'Save Changes',
    createCase: 'Create Case',

    // Field labels
    caseTitle: 'Case Title',
    caseDescription: 'Case Description',
    project: 'Project',
    relatedProject: 'Related Project',
    relatedVersions: 'Related Versions',
    priority: 'Priority',
    status: 'Status',
    testType: 'Test Type',
    preconditions: 'Preconditions',
    steps: 'Steps',
    expectedResult: 'Expected Result',
    author: 'Author',
    createdAt: 'Created At',
    serialNumber: 'No.',

    // Priority
    low: 'Low',
    medium: 'Medium',
    high: 'High',
    critical: 'Critical',

    // Status
    draft: 'Draft',
    active: 'Active',
    deprecated: 'Deprecated',

    // Test types
    functional: 'Functional Testing',
    integration: 'Integration Testing',
    api: 'API Testing',
    ui: 'UI Testing',
    performance: 'Performance Testing',
    security: 'Security Testing',

    // Placeholders
    searchPlaceholder: 'Search case title',
    caseTitlePlaceholder: 'Enter test case title',
    caseDescriptionPlaceholder: 'Enter case description',
    selectProject: 'Select project',
    selectPriority: 'Select priority',
    selectTestType: 'Select test type',
    selectStatus: 'Select status',
    selectVersions: 'Select versions (multiple)',
    preconditionsPlaceholder: 'Enter preconditions',
    stepsPlaceholder: 'Enter detailed steps, e.g.:\n1. Open login page\n2. Enter username and password\n3. Click login button\n4. Verify login result',
    expectedResultPlaceholder: 'Enter overall expected result',
    priorityFilter: 'Priority Filter',
    statusFilter: 'Status Filter',

    // Messages
    fetchListFailed: 'Failed to fetch test case list',
    fetchDetailFailed: 'Failed to fetch test case details',
    deleteConfirm: 'Are you sure to delete this test case?',
    deleteSuccess: 'Test case deleted successfully',
    deleteFailed: 'Failed to delete test case',
    selectFirst: 'Please select test cases to delete first',
    batchDeleteConfirm: 'Are you sure to delete selected {count} test cases? This action cannot be undone.',
    batchDeleteSuccess: 'Successfully deleted {successCount} test cases',
    batchDeletePartialSuccess: 'Successfully deleted {successCount} test cases, {failCount} failed',
    batchDeleteFailed: 'Delete failed',
    batchDeleteError: 'Batch delete failed',
    noDataToExport: 'No test case data to export',
    exportSuccess: 'Test cases exported successfully',
    exportFailed: 'Failed to export test cases',
    createSuccess: 'Test case created successfully',
    createFailed: 'Failed to create test case',
    updateSuccess: 'Test case updated successfully',
    updateFailed: 'Failed to update test case',
    fetchProjectsFailed: 'Failed to fetch project list',
    fetchVersionsFailed: 'Failed to fetch project versions',

    // Other
    noVersion: 'No version',
    noProject: 'No project',
    noDescription: 'No description',
    none: 'None',
    baseline: 'Baseline',

    // Validation
    titleRequired: 'Please enter case title',
    titleLength: 'Title length must be between 5 and 500 characters',
    expectedResultRequired: 'Please enter expected result',
    stepsMaxLength: 'Steps cannot exceed 1000 characters',

    // Excel export
    excelNumber: 'Test Case ID',
    excelTitle: 'Case Title',
    excelProject: 'Related Project',
    excelVersions: 'Related Versions',
    excelPreconditions: 'Preconditions',
    excelSteps: 'Steps',
    excelExpectedResult: 'Expected Result',
    excelPriority: 'Priority',
    excelStatus: 'Status',
    excelTestType: 'Test Type',
    excelAuthor: 'Author',
    excelCreatedAt: 'Created At',
    excelSheetName: 'Test Cases',
    excelFileName: 'TestCases_{date}.xlsx'
  },
  execution: {
    // Page titles
    title: 'Execution Records',
    testPlan: 'Test Plan',
    planDetail: 'Plan Details',
    executionHistory: 'Execution History',
    inDevelopment: 'Execution records feature under development...',

    // Actions
    newPlan: 'New Test Plan',
    batchDelete: 'Batch Delete',
    viewExecution: 'View Execution',
    createPlan: 'Create',
    updatePlan: 'Save',
    closePlan: 'Close',
    activatePlan: 'Activate',
    viewHistory: 'History',

    // Table columns
    serialNumber: 'No.',
    planName: 'Plan Name',
    project: 'Project',
    projects: 'Projects',
    version: 'Version',
    creator: 'Creator',
    status: 'Status',
    createdAt: 'Created At',
    actions: 'Actions',
    testCase: 'Test Case',
    executionStatus: 'Execution Status',
    comments: 'Comments',
    executedBy: 'Executed By',
    executedAt: 'Executed At',

    // Status
    active: 'Active',
    closed: 'Closed',
    untested: 'Untested',
    passed: 'Passed',
    failed: 'Failed',
    blocked: 'Blocked',
    retest: 'Retest',
    completed: 'Completed',
    notStarted: 'Not Started',
    inProgress: 'In Progress',

    // Statistics
    total: 'Total',
    progressRate: 'Progress',

    // Dialog titles
    createPlanDialog: 'New Test Plan',
    editPlanDialog: 'Edit Test Plan',

    // Form labels
    planName: 'Plan Name',
    planDescription: 'Plan Description',
    relatedProjects: 'Related Projects',
    relatedVersion: 'Related Version',
    testCases: 'Test Cases',
    assignees: 'Assignees',
    planStatus: 'Status',
    activeText: 'Active',
    inactiveText: 'Closed',

    // Placeholders
    planNamePlaceholder: 'Enter plan name',
    planDescriptionPlaceholder: 'Enter plan description',
    selectProjects: 'Select projects',
    selectVersion: 'Select version',
    selectTestcases: 'Select test cases',
    selectTestcasesDisabled: 'Please select project first',
    loadingTestcases: 'Loading...',
    selectAssignees: 'Select assignees',
    commentsPlaceholder: 'Enter comments',

    // Filters
    selectProject: 'Select Project',
    selectStatus: 'Select Status',
    filterActive: 'Active',
    filterClosed: 'Closed',

    // Messages
    fetchListFailed: 'Failed to fetch test plans',
    fetchDetailFailed: 'Failed to fetch test plan details',
    fetchBasicDataFailed: 'Failed to fetch basic data',
    fetchTestcasesFailed: 'Failed to fetch test cases',
    fetchHistoryFailed: 'Failed to fetch execution history',
    createSuccess: 'Test plan created successfully',
    createFailed: 'Failed to create test plan',
    updateSuccess: 'Test plan updated successfully',
    updateFailed: 'Failed to update test plan',
    statusUpdateSuccess: 'Status updated successfully',
    statusUpdateFailed: 'Failed to update status',
    detailsUpdateSuccess: 'Details updated successfully',
    detailsUpdateFailed: 'Failed to update details',
    selectFirst: 'Please select test plans to delete first',
    selectCasesFirst: 'Please select cases to delete first',
    selectProjectFirst: 'Please select project first',
    batchDeleteConfirm: 'Are you sure to delete selected {count} test plans? This action cannot be undone.',
    batchDeleteCasesConfirm: 'Are you sure to delete selected {count} cases? This action cannot be undone.',
    batchDeleteSuccess: 'Successfully deleted {successCount} test plans',
    batchDeleteCasesSuccess: 'Successfully deleted {successCount} cases',
    batchDeletePartialSuccess: 'Successfully deleted {successCount} test plans, {failCount} failed',
    batchDeleteCasesPartialSuccess: 'Successfully deleted {successCount} cases, {failCount} failed',
    batchDeleteFailed: 'Delete failed',
    toggleStatusConfirm: 'Are you sure to {action} this test plan?',
    toggleStatusSuccess: '{action} successful',
    toggleStatusFailed: 'Operation failed',

    // Other
    noProject: 'No Project',
    noData: '-',

    // Validation
    planNameRequired: 'Please enter plan name',
    projectsRequired: 'Please select project',
    testcasesRequired: 'Please select at least one test case',
    selectProjectBeforeTestcases: 'Please select project first'
  },
  requirementAnalysis: {
    // Page
    title: 'AI Test Case Generation',
    subtitle: 'AI will generate high-quality test cases based on requirement descriptions or documents',

    // Manual Input
    manualInputTitle: '✍️ Manual Input',
    requirementTitle: 'Requirement Title',
    requirementDescription: 'Requirement Description',
    relatedProject: 'Related Project (Optional)',
    titlePlaceholder: 'Enter requirement title, e.g.: User Login Feature',
    descriptionPlaceholder: 'Describe your requirement in detail, including features, scenarios, business flows, etc.',
    selectProject: 'Select Project',
    charCount: '{count}/2000',
    generating: '🔄 Generating...',
    generateBtn: '🚀 Generate Test Cases',

    // Document Upload
    uploadTitle: '📄 Upload Document',
    dragDropText: 'Drag file here or click to select',
    supportedFormats: 'Supports PDF, Word, TXT formats',
    selectFileBtn: 'Select File',
    removeFile: '❌',
    documentTitle: 'Document Title',
    documentTitlePlaceholder: 'Enter document title',
    fileSize: 'File Size',

    // Generation Options
    generationOptions: '⚙️ Generation Options',
    testCaseCount: 'Expected Number of Test Cases',
    detailLevel: 'Detail Level',
    detailSimple: 'Simple',
    detailNormal: 'Normal',
    detailDetailed: 'Detailed',
    includeEdgeCases: 'Include Edge Cases',
    includeNegativeCases: 'Include Negative Cases',
    submitGeneration: 'Submit Generation Task',

    // Divider
    dividerOr: 'or',

    // Messages
    titleRequired: 'Please enter requirement title',
    descriptionRequired: 'Please enter requirement description',
    descriptionTooShort: 'Description must be at least 10 characters',
    fileRequired: 'Please select a file',
    generateSuccess: 'Generation task submitted!',
    generateFailed: 'Generation failed',
    uploadSuccess: 'File uploaded successfully',
    uploadFailed: 'File upload failed',

    // Progress
    analyzingRequirement: '📖 Analyzing requirement...',
    generatingTestCases: '✍️ Writing test cases...',
    reviewingTestCases: '🔍 Reviewing test cases...',
    generationComplete: '✅ Generation Complete!',
    generationFailed: '❌ Generation Failed',

    // Results
    viewResultsBtn: 'View Results',
    generateAgainBtn: 'Generate Again',
    backBtn: 'Back',

    // Status
    pending: 'Pending',
    processing: 'Processing',
    completed: 'Completed',
    failed: 'Failed'
  },
  generatedTestCases: {
    // Page
    title: 'AI Generated Test Cases',

    // Filters
    statusFilter: 'Status Filter:',
    allStatus: 'All Status',
    pending: 'Analyzing',
    generating: 'Writing',
    reviewing: 'Reviewing',
    completed: 'Completed',
    failed: 'Failed',

    // Actions
    batchDelete: '🗑️ Batch Delete',
    deleting: '🗑️ Deleting...',
    refresh: '🔄 Refresh',
    loading: '🔄 Loading...',

    // Stats
    totalTasks: 'Total',
    completedTasks: 'Completed',
    runningTasks: 'Running',
    failedTasks: 'Failed',

    // Table Headers
    serialNumber: 'No.',
    taskId: 'Task ID',
    relatedRequirement: 'Requirement',
    status: 'Status',
    caseCount: 'Cases',
    generatedTime: 'Time',
    actions: 'Actions',

    // Actions
    viewDetail: 'View',
    adoptAll: 'Adopt All',
    exportExcel: 'Export',
    delete: 'Delete',

    // Empty State
    noTasks: 'No Tasks',
    noTasksHint: 'No AI generation tasks yet. Go to',
    noTasksLink: 'AI Generation',
    noTasksHint2: 'page to create one!',

    // Loading
    loadingTasks: '🔄 Loading task list...',

    // Messages
    deleteConfirm: 'Are you sure to delete this task?',
    batchDeleteConfirm: 'Are you sure to delete {count} selected tasks? This cannot be undone.',
    deleteSuccess: 'Deleted successfully',
    deleteFailed: 'Delete failed',
    batchDeleteSuccess: 'Successfully deleted {count} tasks',
    batchDeleteFailed: 'Batch delete failed',
    adoptAllSuccess: 'All cases adopted successfully',
    adoptAllFailed: 'Adopt failed',
    exportSuccess: 'Export successful',
    exportFailed: 'Export failed',
    loadFailed: 'Failed to load task list',

    // Selection
    selectAll: 'Select All',
    selectedCount: '{count} selected'
  },
  promptConfig: {
    // Page
    title: '📝 Prompt Configuration',
    subtitle: 'Configure AI prompts for test case writing and review',

    // Section
    configListTitle: 'Prompt Configuration List',
    loadDefaults: '📂 Load Defaults',
    addConfig: '➕ Add Config',

    // Config Card
    enabled: 'Enabled',
    disabled: 'Disabled',
    preview: '👁️ Preview',
    edit: '✏️ Edit',
    delete: '🗑️ Delete',

    // Config Details
    contentPreview: 'Content Preview:',
    createdAt: 'Created:',
    updatedAt: 'Updated:',
    creator: 'Creator:',
    unknown: 'Unknown',

    // Modal
    addTitle: 'Add Prompt Configuration',
    editTitle: 'Edit Prompt Configuration',
    configName: 'Config Name',
    configNamePlaceholder: 'e.g.: Test Case Writing Prompt v1.0',
    required: '*',
    promptType: 'Prompt Type',
    testCaseWriter: 'Test Case Writer',
    testCaseReviewer: 'Test Case Reviewer',
    selectType: 'Select Type',
    isActive: 'Enable',
    promptContent: 'Prompt Content',
    contentPlaceholder: 'Enter prompt content, supports variables...',
    contentHint: 'Tip: Use variables like {requirement} {project}',
    saveBtn: '💾 Save',
    cancelBtn: 'Cancel',
    saving: '💾 Saving...',

    // Preview Modal
    previewTitle: 'Preview Prompt',
    closeBtn: 'Close',

    // Empty State
    noConfigs: 'No Configurations',
    noConfigsHint: 'Add prompt configurations to customize AI behavior and output format',
    addFirstConfig: '➕ Add First Config',
    loadDefaultsFirst: '📂 Load Defaults',

    // Messages
    nameRequired: 'Please enter config name',
    typeRequired: 'Please select prompt type',
    contentRequired: 'Please enter prompt content',
    saveSuccess: 'Saved successfully',
    saveFailed: 'Save failed',
    deleteConfirm: 'Are you sure to delete this configuration?',
    deleteSuccess: 'Deleted successfully',
    deleteFailed: 'Delete failed',
    loadDefaultsSuccess: 'Default prompts loaded successfully',
    loadDefaultsFailed: 'Failed to load default prompts',
    loadConfigsFailed: 'Failed to load configurations'
  }
}
