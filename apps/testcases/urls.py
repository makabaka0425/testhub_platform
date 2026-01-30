from django.urls import path
from . import views

urlpatterns = [
    # 测试用例相关
    path('', views.TestCaseListCreateView.as_view(), name='testcase-list'),
    path('<int:pk>/', views.TestCaseDetailView.as_view(), name='testcase-detail'),

    # 导入任务相关
    path('import-tasks/', views.TestCaseImportTaskListCreateView.as_view(), name='import-task-list'),
    path('import-tasks/<str:task_id>/', views.TestCaseImportTaskDetailView.as_view(), name='import-task-detail'),
    path('import-template/', views.download_import_template, name='import-template'),
]