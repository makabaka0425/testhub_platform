import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

// 静态导入常用组件来避免动态导入问题
import Login from '@/views/auth/Login.vue'
import Register from '@/views/auth/Register.vue'
import Layout from '@/layout/index.vue'
import ProjectList from '@/views/projects/ProjectList.vue'

/** @type {import('vue-router').RouteRecordRaw[]} */
const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresGuest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { requiresGuest: true }
  },
  {
    path: '/ai-generation/assistant',
    name: 'Assistant',
    component: () => import('@/views/assistant/AssistantView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ai-generation',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: 'requirement-analysis'
      },
      {
        path: 'requirement-analysis',
        name: 'RequirementAnalysis',
        component: () => import('@/views/requirement-analysis/RequirementAnalysisView.vue')
      },
      {
        path: 'projects',
        name: 'Projects',
        component: ProjectList
      },
      {
        path: 'projects/:id',
        name: 'ProjectDetail',
        component: () => import('@/views/projects/ProjectDetail.vue')
      },
      {
        path: 'testcases',
        name: 'TestCases',
        component: () => import('@/views/testcases/TestCaseList.vue')
      },
      {
        path: 'testcases/create',
        name: 'CreateTestCase',
        component: () => import('@/views/testcases/TestCaseForm.vue')
      },
      {
        path: 'testcases/:id',
        name: 'TestCaseDetail',
        component: () => import('@/views/testcases/TestCaseDetail.vue')
      },
      {
        path: 'testcases/:id/edit',
        name: 'EditTestCase',
        component: () => import('@/views/testcases/TestCaseEdit.vue')
      },
      {
        path: 'versions',
        name: 'Versions',
        component: () => import('@/views/versions/VersionList.vue')
      },
      {
        path: 'reviews',
        name: 'Reviews',
        component: () => import('@/views/reviews/ReviewList.vue')
      },
      {
        path: 'reviews/create',
        name: 'CreateReview',
        component: () => import('@/views/reviews/ReviewForm.vue')
      },
      {
        path: 'reviews/:id',
        name: 'ReviewDetail',
        component: () => import('@/views/reviews/ReviewDetail.vue')
      },
      {
        path: 'reviews/:id/edit',
        name: 'EditReview',
        component: () => import('@/views/reviews/ReviewForm.vue')
      },
      {
        path: 'review-templates',
        name: 'ReviewTemplates',
        component: () => import('@/views/reviews/ReviewTemplateList.vue')
      },
      {
        path: 'testsuites',
        name: 'TestSuites',
        component: () => import('@/views/testsuites/TestSuiteList.vue')
      },
      {
        path: 'executions',
        name: 'Executions',
        component: () => import('@/views/executions/ExecutionListView.vue')
      },
      {
        path: 'executions/:id',
        name: 'ExecutionDetail',
        component: () => import('@/views/executions/ExecutionDetailView.vue')
      },
      {
        path: 'reports',
        name: 'AiTestReport',
        component: () => import('@/views/reports/AiTestReport.vue')
      },
      {
        path: 'generated-testcases',
        name: 'GeneratedTestCases',
        component: () => import('@/views/requirement-analysis/GeneratedTestCaseList.vue')
      },
      {
        path: 'task-detail/:taskId',
        name: 'TaskDetail',
        component: () => import('@/views/requirement-analysis/TaskDetail.vue')
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/UserProfile.vue')
      }
    ]
  },
  {
    path: '/api-testing',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: 'dashboard'
      },
      {
        path: 'dashboard',
        name: 'ApiDashboard',
        component: () => import('@/views/api-testing/Dashboard.vue')
      },
      {
        path: 'projects',
        name: 'ApiProjects',
        component: () => import('@/views/api-testing/ProjectManagement.vue')
      },
      {
        path: 'interfaces',
        name: 'ApiInterfaces',
        component: () => import('@/views/api-testing/InterfaceManagement.vue')
      },
      {
        path: 'automation',
        name: 'ApiAutomation',
        component: () => import('@/views/api-testing/AutomationTesting.vue')
      },
      {
        path: 'history',
        name: 'ApiHistory',
        component: () => import('@/views/api-testing/RequestHistory.vue')
      },
      {
        path: 'environments',
        name: 'ApiEnvironments',
        component: () => import('@/views/api-testing/EnvironmentManagement.vue')
      },
      {
        path: 'reports',
        name: 'ApiReports',
        component: () => import('@/views/api-testing/ReportView.vue')
      },
      {
        path: 'scheduled-tasks',
        name: 'ApiScheduledTasks',
        component: () => import('@/views/api-testing/ScheduledTasks.vue')
      },
      {
        path: 'ai-service-config',
        name: 'ApiAIServiceConfig',
        component: () => import('@/views/api-testing/AIServiceConfig.vue')
      },
      {
        path: 'notification-logs',
        name: 'ApiNotificationLogs',
        component: () => import('@/views/notification/NotificationLogs.vue')
      }
    ]
  },
  {
    path: '/ui-automation',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: 'dashboard'
      },
      {
        path: 'dashboard',
        name: 'UiDashboard',
        component: () => import('@/views/ui-automation/dashboard/Dashboard.vue')
      },
      {
        path: 'projects',
        name: 'UiProjects',
        component: () => import('@/views/ui-automation/projects/ProjectList.vue')
      },
      {
        path: 'elements-enhanced',
        name: 'UiElementsEnhanced',
        component: () => import('@/views/ui-automation/elements/ElementManagerEnhanced.vue')
      },
      {
        path: 'test-cases',
        name: 'UiTestCases',
        component: () => import('@/views/ui-automation/test-cases/TestCaseManager.vue')
      },
      {
        path: 'scripts-enhanced',
        name: 'UiScriptsEnhanced',
        component: () => import('@/views/ui-automation/scripts/ScriptEditorEnhanced.vue')
      },
      {
        path: 'scripts/editor',
        name: 'UiScriptEditor',
        component: () => import('@/views/ui-automation/scripts/ScriptEditorEnhanced.vue')
      },
      {
        path: 'scripts',
        name: 'UiScripts',
        component: () => import('@/views/ui-automation/scripts/ScriptList.vue')
      },
      {
        path: 'suites',
        name: 'UiSuites',
        component: () => import('@/views/ui-automation/suites/SuiteList.vue')
      },
      {
        path: 'executions',
        name: 'UiExecutions',
        component: () => import('@/views/ui-automation/executions/ExecutionList.vue')
      },
      {
        path: 'reports',
        name: 'UiReports',
        component: () => import('@/views/ui-automation/reports/ReportList.vue')
      },
      {
        path: 'scheduled-tasks',
        name: 'UiScheduledTasks',
        component: () => import('@/views/ui-automation/scheduled-tasks/ScheduledTasks.vue')
      },
      {
        path: 'notification-logs',
        name: 'UiNotificationLogs',
        component: () => import('@/views/ui-automation/notification/NotificationLogs.vue')
      }
    ]
  },
  {
    path: '/ai-intelligent-mode',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: 'testing'
      },
      {
        path: 'testing',
        name: 'AITesting',
        component: () => import('@/views/ui-automation/ai/AITesting.vue')
      },
      {
        path: 'cases',
        name: 'AICaseList',
        component: () => import('@/views/ui-automation/ai/AICaseList.vue')
      },
      {
        path: 'execution-records',
        name: 'AIExecutionRecords',
        component: () => import('@/views/ui-automation/ai/AIExecutionRecords.vue')
      }
    ]
  },
  {
    path: '/data-factory',
    name: 'DataFactory',
    component: () => import('@/views/data-factory/DataFactory.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/configuration',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        component: () => import('@/views/configuration/ConfigurationCenter.vue'),
        children: [
          {
            path: '',
            redirect: 'ai-model'
          },
          {
            path: 'ai-model',
            name: 'ConfigAIModel',
            component: () => import('@/views/requirement-analysis/AIModelConfig.vue')
          },
          {
            path: 'prompt-config',
            name: 'ConfigPromptConfig',
            component: () => import('@/views/requirement-analysis/PromptConfig.vue')
          },
          {
            path: 'generation-config',
            name: 'ConfigGenerationConfig',
            component: () => import('@/views/requirement-analysis/GenerationConfigView.vue')
          },
          {
            path: 'ui-env',
            name: 'ConfigUIEnv',
            component: () => import('@/views/configuration/UIEnvironmentConfig.vue')
          },
          {
            path: 'app-env',
            name: 'ConfigAppEnv',
            component: () => import('@/views/app-automation/settings/AppSettings.vue')
          },
          {
            path: 'ai-mode',
            name: 'ConfigAIMode',
            component: () => import('@/views/configuration/AIIntelligentModeConfig.vue')
          },
          {
            path: 'scheduled-task',
            name: 'ConfigScheduledTask',
            component: () => import('@/views/ui-automation/notification/NotificationConfigs.vue')
          },
          {
            path: 'dify',
            name: 'DifyConfig',
            component: () => import('@/views/configuration/DifyConfig.vue')
          }
        ]
      }
    ]
  },
  // APP自动化测试路由
  {
    path: '/app-automation',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: 'dashboard'
      },
      {
        path: 'dashboard',
        name: 'AppAutomationDashboard',
        component: () => import('@/views/app-automation/dashboard/Dashboard.vue')
      },
      {
        path: 'projects',
        name: 'AppProjectList',
        component: () => import('@/views/app-automation/projects/ProjectList.vue')
      },
      {
        path: 'devices',
        name: 'AppDeviceList',
        component: () => import('@/views/app-automation/devices/DeviceList.vue')
      },
      {
        path: 'packages',
        name: 'AppPackageList',
        component: () => import('@/views/app-automation/packages/PackageList.vue')
      },
      {
        path: 'elements',
        name: 'AppElementList',
        component: () => import('@/views/app-automation/elements/ElementList.vue')
      },
      {
        path: 'scene-builder',
        name: 'AppSceneBuilder',
        component: () => import('@/views/app-automation/test-cases/SceneBuilder.vue'),
        meta: { title: '用例编排' }
      },
      {
        path: 'test-cases',
        name: 'AppTestCaseList',
        component: () => import('@/views/app-automation/test-cases/TestCaseList.vue')
      },
      {
        path: 'test-suites',
        name: 'AppTestSuiteList',
        component: () => import('@/views/app-automation/suites/SuiteList.vue')
      },
      {
        path: 'scheduled-tasks',
        name: 'AppScheduledTasks',
        component: () => import('@/views/app-automation/scheduled-tasks/ScheduledTasks.vue')
      },
      {
        path: 'notification-logs',
        name: 'AppNotificationLogs',
        component: () => import('@/views/app-automation/notification/NotificationLogs.vue')
      },
      {
        path: 'executions',
        name: 'AppExecutionList',
        component: () => import('@/views/app-automation/executions/ExecutionList.vue')
      },
      {
        path: 'reports',
        name: 'AppReportList',
        component: () => import('@/views/app-automation/reports/ReportList.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()

  console.log('路由守卫:', {
    to: to.path,
    from: from.path,
    hasToken: !!userStore.accessToken,
    hasUser: !!userStore.user,
    isAuthenticated: userStore.isAuthenticated
  })

  // 只在应用初始化或从登录页面导航时初始化认证
  if (!userStore.user && userStore.accessToken) {
    try {
      console.log('初始化认证...')
      await userStore.initAuth()
      console.log('认证初始化完成:', {
        hasUser: !!userStore.user,
        isAuthenticated: userStore.isAuthenticated
      })
    } catch (error) {
      console.error('认证初始化失败:', error)
    }
  }

  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    console.log('需要认证但未认证，跳转到登录页')
    next('/login')
  } else if (to.meta.requiresGuest && userStore.isAuthenticated) {
    console.log('访客页面但已认证，跳转到项目页')
    next('/home')
  } else {
    console.log('路由守卫通过，继续导航')
    next()
  }
})

router.afterEach((to, from) => {
  console.log(`Navigated from ${from.path} to ${to.path}`)
})

export default router