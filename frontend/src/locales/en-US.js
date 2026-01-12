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
    // Filters
    selectProject: 'Select Project',
    recentDays: 'Last 7 Days',
    recent30Days: 'Last 30 Days',
    recent90Days: 'Last 90 Days',
    customRange: 'Custom Range',
    exportReport: 'Export Report',

    // Stats Cards
    testPlan: 'Test Plan',
    progress: 'Progress',
    totalCases: 'Total Cases',
    passRate: 'Pass Rate',
    failedCases: 'Failed Cases',

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

    // Others
    noData: 'No Data',
    caseTitle: 'Case Title',
    failureCount: 'Failure Count'
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
  }
}
