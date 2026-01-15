export default {
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
