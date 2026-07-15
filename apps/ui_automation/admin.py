from django.contrib import admin
from .models import UiTestPlan, UiTestPlanItem


@admin.register(UiTestPlan)
class UiTestPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'execution_status', 'execution_mode', 'total_cases', 'passed_count', 'failed_count', 'created_by', 'created_at']
    list_filter = ['execution_status', 'execution_mode', 'project']
    search_fields = ['name', 'description']
    date_hierarchy = 'created_at'


@admin.register(UiTestPlanItem)
class UiTestPlanItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'test_plan', 'item_type', 'test_case', 'test_suite', 'order']
    list_filter = ['item_type']
    search_fields = ['test_plan__name']
    raw_id_fields = ['test_plan', 'test_case', 'test_suite']
