from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from rest_framework.routers import DefaultRouter
import os
from django.http import FileResponse, HttpResponseNotFound


def allure_report_serve(request, report_id, path):
    """服务 Allure 报告静态文件"""
    report_dir = os.path.join(settings.BASE_DIR, 'allure_reports', f'report_{report_id}')
    file_path = os.path.normpath(os.path.join(report_dir, path))

    # 安全检查：防止路径穿越
    if not file_path.startswith(os.path.normpath(report_dir)):
        return HttpResponseNotFound('Invalid path')

    if not os.path.isfile(file_path):
        return HttpResponseNotFound('File not found')

    return FileResponse(open(file_path, 'rb'))
from .views import (
    UiProjectViewSet,
    LocatorStrategyViewSet,
    ElementGroupViewSet,
    ElementViewSet,
    TestScriptViewSet,
    PageObjectViewSet,
    ScriptStepViewSet,
    TestSuiteViewSet,
    TestExecutionViewSet,
    ScreenshotViewSet,
    TestCaseViewSet,
    TestCaseGroupViewSet,
    TestCaseStepViewSet,
    TestCaseExecutionViewSet,
    UiScheduledTaskViewSet,
    AIExecutionRecordViewSet,
    AICaseViewSet,
    UiNotificationLogViewSet,
    OperationRecordViewSet,
    UiDashboardViewSet,
    LoginConfigViewSet,
    UiTestPlanViewSet,
    AllureReportViewSet
)
from .views_config import EnvironmentConfigViewSet, AIIntelligentModeConfigViewSet

router = DefaultRouter()
router.register(r'dashboard', UiDashboardViewSet, basename='dashboard')
router.register(r'projects', UiProjectViewSet)
router.register(r'locator-strategies', LocatorStrategyViewSet)
router.register(r'element-groups', ElementGroupViewSet)
router.register(r'elements', ElementViewSet)
router.register(r'test-scripts', TestScriptViewSet)
router.register(r'page-objects', PageObjectViewSet)
router.register(r'steps', ScriptStepViewSet)
router.register(r'test-suites', TestSuiteViewSet)
router.register(r'test-plans', UiTestPlanViewSet)
router.register(r'test-executions', TestExecutionViewSet)
router.register(r'screenshots', ScreenshotViewSet)
router.register(r'test-cases', TestCaseViewSet)
router.register(r'test-case-groups', TestCaseGroupViewSet)
router.register(r'test-case-steps', TestCaseStepViewSet)
router.register(r'test-case-executions', TestCaseExecutionViewSet)
router.register(r'scheduled-tasks', UiScheduledTaskViewSet)
router.register(r'ai-execution-records', AIExecutionRecordViewSet)
router.register(r'ai-cases', AICaseViewSet, basename='ai-cases')
router.register(r'ai-case-generation', AICaseViewSet, basename='ai-case-generation')
router.register(r'notification-logs', UiNotificationLogViewSet)
router.register(r'operation-records', OperationRecordViewSet)
router.register(r'login-configs', LoginConfigViewSet, basename='login-configs')
router.register(r'allure-reports', AllureReportViewSet, basename='allure-reports')


# Configuration Center APIs
router.register(r'config/environment', EnvironmentConfigViewSet, basename='config-environment')
router.register(r'config/ai-mode', AIIntelligentModeConfigViewSet, basename='config-ai-mode')
router.register(r'ai-models', AIIntelligentModeConfigViewSet, basename='ai-models')

urlpatterns = [
    path('', include(router.urls)),
    # Allure 报告静态文件服务: /ui-automation/allure-report-static/{report_id}/{path}
    re_path(r'^allure-report-static/(?P<report_id>\d+)/(?P<path>.*)$', allure_report_serve, name='allure-report-static'),
]

# 添加媒体文件路由
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)