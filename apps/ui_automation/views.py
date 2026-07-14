from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import models
from django.utils import timezone
import logging
import json
import re
import random
import time

from .models import (
    UiProject, LocatorStrategy, Element, TestScript, TestSuite,
    TestSuiteScript, TestExecution, Screenshot,
    ElementGroup, PageObject, PageObjectElement, ScriptStep, ScriptElementUsage,
    TestCase, TestCaseStep, TestCaseExecution, OperationRecord,
    TestCase, TestCaseStep, TestCaseExecution, OperationRecord,
    UiScheduledTask, UiNotificationLog, UiTaskNotificationSetting,
    AICase, AIExecutionRecord, LoginConfig
)
from .serializers import (
    UiProjectSerializer, UiProjectCreateSerializer, UiProjectUpdateSerializer,
    LocatorStrategySerializer,
    ElementSerializer, ElementEnhancedSerializer,
    TestScriptSerializer, TestScriptCreateSerializer, TestScriptUpdateSerializer,
    TestSuiteSerializer, TestSuiteCreateSerializer, TestSuiteUpdateSerializer, TestSuiteWithScriptsSerializer,
    TestSuiteScriptSerializer, TestSuiteTestCaseSerializer,
    TestExecutionSerializer, TestExecutionCreateSerializer,
    ScreenshotSerializer,
    ElementGroupSerializer, ElementGroupCreateSerializer,
    PageObjectSerializer, PageObjectCreateSerializer, PageObjectElementSerializer,
    ScriptStepSerializer, ScriptElementUsageSerializer,
    ScriptAnalysisSerializer, ElementValidationSerializer, CodeGenerationSerializer,
    TestCaseSerializer, TestCaseStepSerializer, TestCaseExecutionSerializer, TestCaseRunSerializer,
    OperationRecordSerializer,
    UiScheduledTaskSerializer, UiNotificationLogSerializer, UiTaskNotificationSettingSerializer,
    AICaseSerializer, AIExecutionRecordSerializer,
    LoginConfigSerializer, LoginConfigCreateSerializer, LoginConfigUpdateSerializer
)
from .operation_logger import log_operation

logger = logging.getLogger(__name__)
User = get_user_model()


def extract_step_info(s, step_index):
    """提取步骤信息的辅助函数，确保返回可读的步骤描述"""
    step_info = {'step': step_index}

    # 尝试多种方式提取可读信息
    if hasattr(s, 'action'):
        # 如果有action属性
        action_data = s.action
        if isinstance(action_data, str):
            step_info['action'] = action_data
        elif hasattr(action_data, '__dict__'):
            # 如果是对象，提取关键属性
            attrs = {}
            for key in ['type', 'description', 'goal', 'coordinate', 'text', 'output', 'result']:
                if hasattr(action_data, key):
                    value = getattr(action_data, key)
                    if isinstance(value, str):
                        attrs[key] = value
                    elif callable(value):
                        attrs[key] = getattr(value, '__name__', str(value))
                    else:
                        attrs[key] = str(value)
            if attrs:
                step_info['action'] = attrs
        else:
            step_info['action'] = str(action_data)
    elif hasattr(s, 'model_output'):
        # 如果有model_output属性
        output_data = s.model_output
        if isinstance(output_data, str):
            step_info['action'] = output_data
        elif hasattr(output_data, '__dict__'):
            # 提取model_output的关键信息
            attrs = {'type': 'model_output'}
            for key in ['action', 'description', 'goal', 'coordinate', 'text']:
                if hasattr(output_data, key):
                    value = getattr(output_data, key)
                    attrs[key] = str(value) if value else None
            step_info['action'] = attrs
        else:
            step_info['action'] = str(output_data)
    elif hasattr(s, '__dict__'):
        # 通用的对象提取
        attrs = {}
        for key in dir(s):
            if not key.startswith('_'):
                try:
                    value = getattr(s, key)
                    if not callable(value):
                        attrs[key] = str(value)
                except:
                    pass
        if attrs:
            step_info['action'] = attrs
    else:
        # 最后回退，但检查是否是函数对象
        if callable(s):
            step_info['action'] = f"<Action: {getattr(s, '__name__', 'unknown action')}>"
        else:
            step_info['action'] = str(s)

    return step_info


from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000


class UiProjectViewSet(viewsets.ModelViewSet):
    queryset = UiProject.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'owner', 'members']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return UiProjectCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UiProjectUpdateSerializer
        return UiProjectSerializer

    def get_queryset(self):
        # 只显示用户有权限访问的项目
        user = self.request.user
        return UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()

    def perform_create(self, serializer):
        # 创建项目时，当前用户自动成为负责人
        instance = serializer.save(owner=self.request.user)
        # 记录操作
        log_operation('create', 'project', instance.id, instance.name, self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        # 记录操作
        log_operation('edit', 'project', instance.id, instance.name, self.request.user)

    def perform_destroy(self, instance):
        # 记录操作（在删除前记录）
        log_operation('delete', 'project', instance.id, instance.name, self.request.user)
        instance.delete()

    @action(detail=True, methods=['post'], url_path='clean-test-data')
    def clean_test_data(self, request, pk=None):
        """清理项目的测试执行数据（保留用例定义、元素库、操作审计记录）"""
        import os
        from django.conf import settings

        project = self.get_object()

        # 可选的时间范围过滤
        before_date = request.data.get('before_date')  # ISO格式字符串，如 2025-01-01
        data_types = request.data.get('data_types')  # 指定要清理的数据类型，不传则默认全部

        # 默认清理所有类型的执行数据
        all_data_types = ['case_executions', 'suite_executions', 'ai_executions', 'screenshots', 'notification_logs']
        if data_types is None:
            data_types = all_data_types
        elif not data_types:
            return Response({'message': '未选择要清理的数据类型', 'details': {}, 'total_deleted': 0})

        stats = {}
        total_deleted = 0

        # 构建时间过滤条件
        time_filter = {}
        if before_date:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(before_date)
                time_filter['created_at__lt'] = dt
            except (ValueError, TypeError):
                return Response({'error': 'before_date 格式无效，请使用 ISO 格式（如 2025-01-01）'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. 清理 TestCaseExecution（用例执行记录）
        if 'case_executions' in data_types:
            qs = TestCaseExecution.objects.filter(project=project)
            if time_filter:
                qs = qs.filter(**time_filter)
            count = qs.count()
            # 删除关联的磁盘文件（如果有截图存在screenshots JSON中）
            if count > 0:
                qs.delete()
            stats['case_executions'] = count
            total_deleted += count

        # 2. 清理 TestExecution（套件执行记录）+ 关联的 Screenshot
        if 'suite_executions' in data_types:
            qs = TestExecution.objects.filter(project=project)
            if time_filter:
                qs = qs.filter(**time_filter)
            count = qs.count()
            if count > 0:
                # 先删除关联的截图文件
                screenshot_qs = Screenshot.objects.filter(execution__project=project)
                if time_filter:
                    screenshot_qs = screenshot_qs.filter(execution__created_at__lt=time_filter.get('created_at__lt', None))
                for screenshot in screenshot_qs:
                    try:
                        if screenshot.image and os.path.isfile(screenshot.image.path):
                            os.remove(screenshot.image.path)
                    except Exception:
                        pass
                qs.delete()  # 级联删除会处理Screenshot记录
            stats['suite_executions'] = count
            total_deleted += count

        # 3. 清理 AIExecutionRecord（AI执行记录）+ 关联的磁盘文件
        if 'ai_executions' in data_types:
            qs = AIExecutionRecord.objects.filter(project=project)
            if time_filter:
                qs = qs.filter(**time_filter)
            count = qs.count()
            if count > 0:
                for record in qs:
                    # 删除GIF录制文件
                    if record.gif_path:
                        try:
                            gif_full_path = os.path.join(settings.MEDIA_ROOT, record.gif_path.lstrip('/'))
                            if os.path.isfile(gif_full_path):
                                os.remove(gif_full_path)
                        except Exception:
                            pass
                qs.delete()
            stats['ai_executions'] = count
            total_deleted += count

        # 4. 清理孤立的截图文件（不属于任何执行记录的）
        if 'screenshots' in data_types and 'suite_executions' not in data_types:
            # 单独清理截图（如果上面没清理套件执行的话）
            orphan_screenshots = Screenshot.objects.filter(execution__project=project)
            deleted_screenshots = 0
            for screenshot in orphan_screenshots:
                try:
                    if screenshot.image and os.path.isfile(screenshot.image.path):
                        os.remove(screenshot.image.path)
                        deleted_screenshots += 1
                except Exception:
                    pass
            orphan_screenshots.delete()
            stats['orphan_screenshots'] = deleted_screenshots

        # 5. 清理通知日志
        if 'notification_logs' in data_types:
            qs = UiNotificationLog.objects.filter(task__project=project)
            if time_filter:
                qs = qs.filter(**time_filter)
            count = qs.count()
            if count > 0:
                qs.delete()
            stats['notification_logs'] = count
            total_deleted += count

        # 记录操作
        log_operation('delete', 'project', project.id,
                      f'清理测试数据: {project.name} (共{total_deleted}条)', request.user)

        return Response({
            'message': f'清理完成，共删除 {total_deleted} 条记录',
            'project': project.name,
            'details': stats,
            'total_deleted': total_deleted
        })

    @action(detail=True, methods=['post'], url_path='test-db-connection')
    def test_db_connection(self, request, pk=None):
        """测试被测系统数据库连接"""
        import time

        project = self.get_object()

        # 支持两种场景：
        # 1. 已保存的项目：使用项目上的数据库配置
        # 2. 请求体中传入配置：优先使用请求体中的值（创建/编辑时即时测试）
        db_type = request.data.get('target_db_type') or project.target_db_type
        db_host = request.data.get('target_db_host') or project.target_db_host
        db_port = request.data.get('target_db_port') or project.target_db_port
        db_name = request.data.get('target_db_name') or project.target_db_name
        db_user = request.data.get('target_db_user') or project.target_db_user
        db_password = request.data.get('target_db_password', None)
        if db_password is None:
            db_password = project.target_db_password or ''

        if not db_type:
            return Response({'success': False, 'error': '请先选择数据库类型'}, status=status.HTTP_400_BAD_REQUEST)
        if not db_name:
            return Response({'success': False, 'error': '请先填写数据库名'}, status=status.HTTP_400_BAD_REQUEST)

        db_type = db_type.lower()
        conn = None
        start = time.time()

        try:
            if db_type == 'mysql':
                import pymysql
                conn = pymysql.connect(
                    host=db_host or 'localhost',
                    port=int(db_port) if db_port else 3306,
                    user=db_user or '',
                    password=db_password,
                    database=db_name,
                    charset='utf8mb4',
                    connect_timeout=10
                )
            elif db_type in ('postgresql', 'postgres'):
                import psycopg2
                conn = psycopg2.connect(
                    host=db_host or 'localhost',
                    port=int(db_port) if db_port else 5432,
                    user=db_user or '',
                    password=db_password,
                    dbname=db_name,
                    connect_timeout=10
                )
            elif db_type == 'sqlite':
                import sqlite3
                conn = sqlite3.connect(db_name)
            elif db_type == 'oracle':
                import cx_Oracle
                dsn = cx_Oracle.makedsn(
                    db_host or 'localhost',
                    int(db_port) if db_port else 1521,
                    service_name=db_name
                )
                conn = cx_Oracle.connect(user=db_user or '', password=db_password, dsn=dsn)
            else:
                return Response({'success': False, 'error': f'不支持的数据库类型: {db_type}'}, status=status.HTTP_400_BAD_REQUEST)

            # 测试查询
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')

            elapsed = round((time.time() - start) * 1000)
            db_version = ''
            try:
                with conn.cursor() as cursor:
                    if db_type == 'mysql':
                        cursor.execute('SELECT VERSION()')
                    elif db_type in ('postgresql', 'postgres'):
                        cursor.execute('SELECT version()')
                    elif db_type == 'sqlite':
                        cursor.execute('SELECT sqlite_version()')
                    elif db_type == 'oracle':
                        cursor.execute('SELECT * FROM v$version WHERE rownum = 1')
                    row = cursor.fetchone()
                    if row:
                        db_version = str(row[0])
            except Exception:
                pass

            return Response({
                'success': True,
                'message': '数据库连接成功',
                'db_type': db_type,
                'db_version': db_version,
                'elapsed_ms': elapsed
            })

        except Exception as e:
            elapsed = round((time.time() - start) * 1000)
            return Response({
                'success': False,
                'error': str(e),
                'elapsed_ms': elapsed
            })
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class LocatorStrategyViewSet(viewsets.ModelViewSet):
    queryset = LocatorStrategy.objects.all()
    permission_classes = []
    serializer_class = LocatorStrategySerializer
    ordering = ['id']


class ElementViewSet(viewsets.ModelViewSet):
    queryset = Element.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['project', 'locator_strategy', 'element_type', 'validation_status', 'group']
    search_fields = ['name', 'description', 'page', 'component_name']

    # 手动交互模式会话管理（类变量，跨请求共享）
    _manual_sessions = {}  # session_id -> {playwright, browser, page, context, captures, created_at}
    # 交互式选取模式会话管理
    _pick_sessions = {}    # session_id -> {playwright, browser, page, context, picked_elements, created_at}

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ElementEnhancedSerializer
        return ElementSerializer

    def get_queryset(self):
        # 只显示用户有权限访问的项目的元素
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        return Element.objects.filter(project__in=accessible_projects).select_related(
            'project', 'group', 'locator_strategy', 'created_by', 'parent_element'
        ).prefetch_related('script_usages__script').order_by('page', 'order', 'name')

    def filter_queryset(self, queryset):
        # 先应用默认的过滤器
        queryset = super().filter_queryset(queryset)

        # 处理页面筛选（使用page_name参数避免与分页page冲突）
        page_name = self.request.query_params.get('page_name', None)
        if page_name:
            queryset = queryset.filter(page=page_name)

        return queryset

    def perform_create(self, serializer):
        # 创建元素时自动设置创建人
        instance = serializer.save(created_by=self.request.user)
        # 记录操作
        log_operation('create', 'element', instance.id, instance.name, self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        # 记录操作
        log_operation('edit', 'element', instance.id, instance.name, self.request.user)

    def perform_destroy(self, instance):
        # 记录操作（在删除前记录）
        log_operation('delete', 'element', instance.id, instance.name, self.request.user)
        instance.delete()

    @action(detail=True, methods=['post'])
    def validate_locator(self, request, pk=None):
        """验证元素定位器有效性"""
        element = self.get_object()

        # 这里可以集成实际的浏览器验证逻辑
        # 现在只是模拟验证
        validation_result = self._perform_element_validation(element)

        element.validation_status = 'VALID' if validation_result['is_valid'] else 'INVALID'
        element.validation_message = validation_result['validation_message']
        element.last_validated = timezone.now()
        element.save()

        serializer = ElementValidationSerializer(validation_result)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def usages(self, request, pk=None):
        """获取元素在脚本中的使用情况"""
        element = self.get_object()
        usages = ScriptElementUsage.objects.filter(element=element).select_related('script')
        serializer = ScriptElementUsageSerializer(usages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取元素树形结构"""
        project_id = request.query_params.get('project')
        if not project_id:
            return Response({'error': '需要指定项目ID'}, status=status.HTTP_400_BAD_REQUEST)

        elements = self.get_queryset().filter(project_id=project_id)
        tree_data = self._build_element_tree(elements)
        return Response(tree_data)

    @action(detail=True, methods=['post'])
    def add_backup_locator(self, request, pk=None):
        """添加备用定位器"""
        element = self.get_object()
        strategy = request.data.get('strategy')
        value = request.data.get('value')

        if not strategy or not value:
            return Response({'error': '策略和值都是必需的'}, status=status.HTTP_400_BAD_REQUEST)

        backup_locators = element.backup_locators or []
        backup_locators.append({'strategy': strategy, 'value': value})
        element.backup_locators = backup_locators
        element.save()

        return Response({'message': '备用定位器添加成功'})

    @action(detail=True, methods=['post'])
    def generate_suggestions(self, request, pk=None):
        """生成元素使用建议"""
        element = self.get_object()
        suggestions = self._generate_element_suggestions(element)
        return Response({'suggestions': suggestions})

    def _perform_element_validation(self, element):
        """执行元素验证（模拟实现）"""
        try:
            # 这里可以集成实际的浏览器自动化工具进行验证
            # 现在只是简单的语法检查
            is_valid = True
            message = "定位器验证通过"
            suggestions = []

            # 简单的语法检查
            if element.locator_strategy.name == 'css':
                if not element.locator_value.strip():
                    is_valid = False
                    message = "CSS选择器不能为空"
            elif element.locator_strategy.name == 'xpath':
                if not element.locator_value.strip():
                    is_valid = False
                    message = "XPath表达式不能为空"

            return {
                'is_valid': is_valid,
                'validation_message': message,
                'suggestions': suggestions
            }
        except Exception as e:
            return {
                'is_valid': False,
                'validation_message': f'验证过程中出现错误: {str(e)}',
                'suggestions': []
            }

    @action(detail=False, methods=['post'])
    def ai_extract(self, request):
        """AI智能提取页面元素 — Playwright DOM提取 + LLM分析"""
        import os
        os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'

        project_id = request.data.get('project_id')
        url = request.data.get('url', '').strip()
        login_config_id = request.data.get('login_config_id')
        page_name = request.data.get('page_name', '').strip()

        if not project_id or not url:
            return Response({'error': 'project_id 和 url 为必填项'}, status=status.HTTP_400_BAD_REQUEST)

        # 验证项目
        try:
            project = UiProject.objects.get(id=project_id)
        except UiProject.DoesNotExist:
            return Response({'error': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)

        # URL规范化：相对路径拼接 + 协议修正
        _base_url = (project.base_url or '').rstrip('/')
        if url and not url.startswith('http://') and not url.startswith('https://'):
            if _base_url:
                url = f"{_base_url}/{url.lstrip('/')}"
            else:
                return Response({'error': '相对路径需要项目配置base_url'}, status=status.HTTP_400_BAD_REQUEST)
        if _base_url.startswith('https://') and url.startswith('http://'):
            url = 'https://' + url[7:]
            print(f'[URL规范化] http→https: {url}')

        # 验证登录配置
        login_config = None
        if login_config_id:
            try:
                login_config = LoginConfig.objects.get(id=login_config_id, project=project)
            except LoginConfig.DoesNotExist:
                return Response({'error': '登录配置不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 预先获取登录配置数据，避免在Playwright上下文中访问ORM
        login_steps_data = None
        login_start_url = ''
        if login_config:
            login_start_url = login_config.login_url or ''
            if not login_start_url and login_config.project:
                login_start_url = login_config.project.base_url or ''
            test_case = login_config.login_test_case
            if test_case:
                steps = test_case.steps.select_related('element', 'element__locator_strategy').filter(is_cleanup=False).order_by('step_number')
                login_steps_data = []
                for step in steps:
                    step_data = {
                        'action_type': step.action_type,
                        'input_value': step.input_value or '',
                        'wait_time': step.wait_time or 1000,
                        'element': None
                    }
                    if step.element:
                        step_data['element'] = {
                            'locator_value': step.element.locator_value,
                            'locator_strategy': step.element.locator_strategy.name if step.element.locator_strategy else 'css'
                        }
                    login_steps_data.append(step_data)

        # Step 1: Playwright DOM 提取
        try:
            extract_result = self._playwright_extract_elements(url, login_start_url, login_steps_data)
            dom_elements = extract_result.get('elements', [])
            final_url = extract_result.get('final_url', url)
            redirect_warning = extract_result.get('redirect_warning', '')
            candidate_buttons = extract_result.get('candidate_buttons', [])
            table_row_count = extract_result.get('table_row_count', 0)
        except Exception as e:
            import traceback
            error_detail = f'{str(e)}\n{traceback.format_exc()}'
            print(f'[AI提取] DOM提取失败: {error_detail}')
            return Response({'error': f'页面DOM提取失败: {str(e) or type(e).__name__}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not dom_elements:
            return Response({'error': '未在页面上找到可交互元素'}, status=status.HTTP_404_NOT_FOUND)

        # Step 2: AI 分析与分类
        try:
            ai_elements = self._ai_analyze_elements(dom_elements)
        except Exception as e:
            # AI 分析失败时回退到规则引擎
            print(f'[AI提取] AI分析失败，回退到规则引擎: {str(e)}')
            ai_elements = self._rule_based_classify(dom_elements)

        # 填充 page_name
        for elem in ai_elements:
            if page_name:
                elem['page'] = page_name

        # 将 dom_elements 中的验证状态关联到 ai_elements
        # 构建验证状态索引：按 locator_value 和 auto_css/auto_xpath 匹配
        validation_map = {}
        # 同时记录所有DOM提取阶段验证过的定位值集合（仅这些值经过了浏览器验证）
        dom_validated_values = set()
        for dom_elem in dom_elements:
            v_status = dom_elem.get('validation_status', '')
            v_details = dom_elem.get('validation_details', '')
            if not v_status:
                continue
            # 用 auto_css 和 auto_xpath 作为 key 建立索引
            auto_css = dom_elem.get('auto_css', '')
            auto_xpath = dom_elem.get('auto_xpath', '')
            if auto_css:
                validation_map[auto_css] = (v_status, v_details)
                dom_validated_values.add(auto_css)
            if auto_xpath:
                validation_map[auto_xpath] = (v_status, v_details)
                dom_validated_values.add(auto_xpath)
        
        # 为 ai_elements 匹配验证状态
        # 关键修复：仅当 locator_value 在 dom_validated_values 中（即经过浏览器验证的）才信任 validation_map
        # LLM 可能修改了定位值，这些值未经浏览器验证，必须走二次验证
        # 同时，PARTIAL状态（匹配不唯一）的元素也需要二次验证，尝试找到更精确的定位
        for ai_elem in ai_elements:
            if ai_elem.get('validation_status'):
                continue  # 规则引擎已经设置了
            locator_value = ai_elem.get('locator_value', '')
            if locator_value and locator_value in dom_validated_values:
                # 该定位值确实在DOM提取阶段经过浏览器验证，可以信任
                ai_elem['validation_status'], ai_elem['validation_details'] = validation_map[locator_value]
            # 其他情况（LLM修改了值、值不在DOM验证集合中）留空，由 _revalidate_locators 二次验证

        # Step 2.5: 对LLM生成的locator_value进行二次验证
        # LLM可能修改了定位值（如去掉空格、改写选择器），需要重新在浏览器中验证
        # 同时，PARTIAL状态（匹配多个元素，不精确）的也需要二次验证以找到更精确的定位
        needs_revalidation = [
            e for e in ai_elements 
            if not e.get('validation_status') or e.get('validation_status') in ('', 'PARTIAL')
        ]
        if needs_revalidation:
            print(f'[AI提取] 有{len(needs_revalidation)}个元素需要二次验证（未验证或PARTIAL），开始二次验证...')
            self._revalidate_locators(url, login_start_url, login_steps_data, needs_revalidation)

        # Step 3: 去重定位值，确保每个元素的定位尽量唯一
        ai_elements = self._deduplicate_locators(ai_elements)

        # Step 3.5: 按元素名称去重，过滤列表行重复的操作按钮
        ai_elements = self._deduplicate_by_name(ai_elements)

        response_data = {
            'page_title': dom_elements[0].get('page_title', '') if dom_elements else '',
            'url': url,
            'final_url': final_url,
            'elements': ai_elements,
            'candidate_buttons': candidate_buttons,
            'table_row_count': table_row_count
        }
        if redirect_warning:
            response_data['redirect_warning'] = redirect_warning

        return Response(response_data)

    @action(detail=False, methods=['post'])
    def ai_extract_dialogs(self, request):
        """AI提取弹窗元素 — 自动点击候选按钮，提取弹窗内元素"""
        import os
        os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'

        project_id = request.data.get('project_id')
        url = request.data.get('url', '').strip()
        login_config_id = request.data.get('login_config_id')
        page_name = request.data.get('page_name', '').strip()
        buttons = request.data.get('buttons', [])  # 用户勾选的候选按钮列表

        if not project_id or not url:
            return Response({'error': 'project_id 和 url 为必填项'}, status=status.HTTP_400_BAD_REQUEST)
        if not buttons:
            return Response({'error': 'buttons 为必填项，请提供要点击的候选按钮列表'}, status=status.HTTP_400_BAD_REQUEST)

        # 验证项目
        try:
            project = UiProject.objects.get(id=project_id)
        except UiProject.DoesNotExist:
            return Response({'error': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 验证登录配置
        login_config = None
        if login_config_id:
            try:
                login_config = LoginConfig.objects.get(id=login_config_id, project=project)
            except LoginConfig.DoesNotExist:
                return Response({'error': '登录配置不存在'}, status=status.HTTP_404_NOT_FOUND)

        login_steps_data = None
        login_start_url = ''
        if login_config:
            login_start_url = login_config.login_url or ''
            if not login_start_url and login_config.project:
                login_start_url = login_config.project.base_url or ''
            test_case = login_config.login_test_case
            if test_case:
                steps = test_case.steps.select_related('element', 'element__locator_strategy').filter(is_cleanup=False).order_by('step_number')
                login_steps_data = []
                for step in steps:
                    step_data = {
                        'action_type': step.action_type,
                        'input_value': step.input_value or '',
                        'wait_time': step.wait_time or 1000,
                        'action_wait': step.action_wait or 0,
                        'element': None
                    }
                    if step.element:
                        step_data['element'] = {
                            'locator_value': step.element.locator_value,
                            'locator_strategy': step.element.locator_strategy.name if step.element.locator_strategy else 'css'
                        }
                    login_steps_data.append(step_data)

        # 使用Playwright自动点击按钮并提取弹窗元素
        try:
            extract_result = self._playwright_extract_dialog_elements(
                url, buttons, login_start_url, login_steps_data
            )
        except Exception as e:
            import traceback
            error_detail = f'{str(e)}\n{traceback.format_exc()}'
            print(f'[AI提取弹窗] 提取失败: {error_detail}')
            return Response({'error': f'弹窗元素提取失败: {str(e) or type(e).__name__}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        dialog_elements = extract_result.get('elements', [])
        dialog_sources = extract_result.get('dialog_sources', {})

        # AI 分析与分类
        if not dialog_elements:
            return Response({
                'elements': [],
                'dialog_sources': dialog_sources,
                'message': '未在弹窗中找到可交互元素'
            })

        try:
            ai_elements = self._ai_analyze_elements(dialog_elements)
        except Exception as e:
            print(f'[AI提取弹窗] AI分析失败，回退到规则引擎: {str(e)}')
            ai_elements = self._rule_based_classify(dialog_elements)

        # 填充 page_name 和 source
        for elem in ai_elements:
            if page_name:
                elem['page'] = page_name

        # 关联验证状态
        validation_map = {}
        dom_validated_values = set()
        for dom_elem in dialog_elements:
            v_status = dom_elem.get('validation_status', '')
            v_details = dom_elem.get('validation_details', '')
            if not v_status:
                continue
            auto_css = dom_elem.get('auto_css', '')
            auto_xpath = dom_elem.get('auto_xpath', '')
            if auto_css:
                validation_map[auto_css] = (v_status, v_details)
                dom_validated_values.add(auto_css)
            if auto_xpath:
                validation_map[auto_xpath] = (v_status, v_details)
                dom_validated_values.add(auto_xpath)

        for elem in ai_elements:
            locator_value = elem.get('locator_value', '')
            if locator_value in validation_map:
                v_status, v_details = validation_map[locator_value]
                elem['validation_status'] = v_status
                elem['validation_details'] = v_details
            else:
                elem['validation_status'] = 'UNVALIDATED'
                elem['validation_details'] = '未在DOM提取阶段验证'

            # 关联弹窗来源
            source = elem.get('source', '')
            if not source:
                for css in [elem.get('locator_value', ''), elem.get('auto_css', '')]:
                    if css:
                        for dialog_name, dialog_css_list in dialog_sources.items():
                            if css in dialog_css_list:
                                elem['source'] = dialog_name
                                break

        # 二次验证
        needs_revalidation = [
            e for e in ai_elements
            if not e.get('validation_status') or e.get('validation_status') in ('', 'PARTIAL')
        ]
        if needs_revalidation:
            print(f'[AI提取弹窗] 有{len(needs_revalidation)}个元素需要二次验证')
            self._revalidate_locators(url, login_start_url, login_steps_data, needs_revalidation)

        ai_elements = self._deduplicate_locators(ai_elements)

        # 按元素名称去重，过滤列表行重复的操作按钮
        ai_elements = self._deduplicate_by_name(ai_elements)

        return Response({
            'elements': ai_elements,
            'dialog_sources': dialog_sources
        })

    def _playwright_extract_dialog_elements(self, url, buttons, login_start_url='', login_steps_data=None):
        """使用Playwright打开页面，逐个点击候选按钮提取弹窗元素"""
        from playwright.sync_api import sync_playwright
        import time

        all_dialog_elements = []
        dialog_sources = {}  # 弹窗名 -> 元素CSS列表
        dialog_failures = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()

            # 登录（如有）
            if login_start_url and login_steps_data:
                page.goto(login_start_url, wait_until='networkidle', timeout=30000)
                time.sleep(2)
                for i, step_data in enumerate(login_steps_data):
                    self._execute_login_step(page, step_data)
                try:
                    page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    pass
                time.sleep(2)

            # 导航到目标页面
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(2)
            page_title = page.title()

            for btn_info in buttons:
                btn_text = btn_info.get('text', '')
                btn_css = btn_info.get('css_selector', '')
                btn_xpath = btn_info.get('xpath', '')
                btn_source = btn_info.get('source', '页面级按钮')

                print(f'[AI提取弹窗] 尝试点击按钮: "{btn_text}" (source={btn_source})')

                try:
                    # 点击按钮
                    clicked = False
                    if btn_css:
                        try:
                            locator = page.locator(btn_css).first
                            if locator.count() > 0:
                                locator.click(timeout=5000)
                                clicked = True
                        except:
                            pass
                    if not clicked and btn_xpath:
                        try:
                            locator = page.locator(f'xpath={btn_xpath}').first
                            if locator.count() > 0:
                                locator.click(timeout=5000)
                                clicked = True
                        except:
                            pass
                    if not clicked and btn_text:
                        # 尝试通过文本点击
                        try:
                            page.get_by_text(btn_text, exact=False).first.click(timeout=5000)
                            clicked = True
                        except:
                            pass

                    if not clicked:
                        dialog_failures.append({'button': btn_text, 'reason': '无法定位或点击按钮'})
                        continue

                    # 等待弹窗出现
                    dialog_appeared = False
                    dialog_selector = None
                    for sel in ['.ant-modal:visible', '.ant-drawer:visible', '.el-dialog:visible', '.el-drawer:visible',
                                '[role="dialog"]:visible', '.modal:visible']:
                        try:
                            page.wait_for_selector(sel, timeout=3000)
                            dialog_selector = sel
                            dialog_appeared = True
                            break
                        except:
                            continue

                    if not dialog_appeared:
                        dialog_failures.append({'button': btn_text, 'reason': '点击后未检测到弹窗'})
                        # 尝试恢复页面状态
                        time.sleep(1)
                        continue

                    time.sleep(1)  # 等待弹窗内容完全渲染

                    # 获取弹窗标题（用于来源标注）
                    dialog_title = btn_text
                    try:
                        title_el = page.locator(f'{dialog_selector} .ant-modal-title, {dialog_selector} .el-dialog__title, {dialog_selector} [role="dialog"] h3, {dialog_selector} h2, {dialog_selector} h3').first
                        if title_el.count() > 0:
                            dialog_title = f"{btn_text}弹窗({title_el.text_content().strip()[:20]})"
                        else:
                            dialog_title = f"{btn_text}弹窗"
                    except:
                        dialog_title = f"{btn_text}弹窗"

                    print(f'[AI提取弹窗] 检测到弹窗: {dialog_title}')

                    # 提取弹窗内部元素（scope限制在弹窗容器内）
                    dialog_js = """
                    (dialogSelector) => {
                        const results = [];
                        const interactiveSelectors = [
                            'input', 'button', 'a[href]', 'select', 'textarea',
                            '[role="button"]', '[role="link"]', '[role="tab"]',
                            '[role="menuitem"]', '[role="option"]', '[role="switch"]',
                            '[onclick]', '[contenteditable="true"]',
                            '.el-button', '.el-input__inner', '.el-select',
                            '.el-checkbox', '.el-radio', '.el-switch',
                            '.ant-btn', '.ant-input', '.ant-select', '.ant-checkbox',
                            '.ant-radio', '.ant-switch'
                        ];

                        const seen = new Set();
                        const container = document.querySelector(dialogSelector);
                        if (!container) return { elements: [] };

                        interactiveSelectors.forEach(selector => {
                            try {
                                container.querySelectorAll(selector).forEach(el => {
                                    const rect = el.getBoundingClientRect();
                                    if (rect.width === 0 && rect.height === 0) return;
                                    const style = window.getComputedStyle(el);
                                    if (style.display === 'none' || style.visibility === 'hidden') return;

                                    const key = el.tagName + '|' + (el.id||'') + '|' + el.className + '|' + rect.x + '|' + rect.y;
                                    if (seen.has(key)) return;
                                    seen.add(key);

                                    results.push({
                                        tag: el.tagName.toLowerCase(),
                                        id: el.id || '',
                                        name: el.getAttribute('name') || '',
                                        className: (typeof el.className === 'string') ? el.className.substring(0, 200) : '',
                                        type: el.type || '',
                                        placeholder: el.placeholder || '',
                                        value: (el.value || '').substring(0, 50),
                                        href: el.href || '',
                                        role: el.getAttribute('role') || '',
                                        ariaLabel: el.getAttribute('aria-label') || '',
                                        dataTestId: el.getAttribute('data-testid') || '',
                                        text: (el.textContent || '').trim().substring(0, 80),
                                        title: el.title || '',
                                        visible: true,
                                        rect: { x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height) },
                                        isInTableRow: false,
                                        tableRowIndex: -1
                                    });
                                });
                            } catch(e) {}
                        });
                        return { elements: results.slice(0, 80) };
                    }
                    """

                    dialog_result = page.evaluate(dialog_js, dialog_selector)
                    dialog_raw_elements = dialog_result.get('elements', [])

                    # 计算定位器 + 验证
                    dialog_css_list = []
                    for elem in dialog_raw_elements:
                        elem['page_title'] = page_title
                        elem['source'] = dialog_title
                        css_selector = self._compute_css_selector(elem)
                        xpath = self._compute_xpath(elem)
                        validation = self._validate_locators(page, elem, css_selector, xpath)
                        elem['auto_css'] = validation['css_selector']
                        elem['auto_xpath'] = validation['xpath']
                        elem['validation_status'] = validation['validation_status']
                        elem['validation_details'] = validation['validation_details']
                        all_dialog_elements.append(elem)
                        if validation['css_selector']:
                            dialog_css_list.append(validation['css_selector'])

                    dialog_sources[dialog_title] = dialog_css_list
                    print(f'[AI提取弹窗] 弹窗"{dialog_title}"提取到 {len(dialog_raw_elements)} 个元素')

                    # 关闭弹窗：遮罩层 → 取消按钮 → ESC
                    self._close_dialog(page)

                except Exception as e:
                    dialog_failures.append({'button': btn_text, 'reason': str(e)})
                    print(f'[AI提取弹窗] 点击"{btn_text}"时出错: {str(e)}')
                    # 尝试恢复
                    try:
                        self._close_dialog(page)
                    except:
                        pass

            browser.close()

        if dialog_failures:
            print(f'[AI提取弹窗] 失败的按钮: {dialog_failures}')

        return {
            'elements': all_dialog_elements,
            'dialog_sources': dialog_sources
        }

    def _close_dialog(self, page):
        """关闭弹窗：遮罩层优先 → 取消按钮 → ESC兜底"""
        import time

        # 1. 点击遮罩层
        try:
            # Ant Design: 点击modal-wrap的边缘区域
            mask = page.locator('.ant-modal-wrap:not(.ant-modal-wrap-hidden)').first
            if mask.count() > 0:
                # 点击左上角边缘（遮罩层区域，而非modal内容区域）
                mask_box = mask.bounding_box()
                if mask_box:
                    page.mouse.click(mask_box['x'] + 5, mask_box['y'] + 5)
                    time.sleep(500 / 1000)
                    if page.locator('.ant-modal:visible').count() == 0:
                        return True
        except:
            pass

        # 2. 找取消/关闭按钮
        try:
            for close_sel in ['.ant-modal-close', '.ant-modal:visible .ant-btn-default',
                              '.el-dialog__close', '.el-dialog .el-button--default',
                              '[role="dialog"] button:has-text("取消")',
                              '[role="dialog"] button:has-text("关闭")']:
                try:
                    close_btn = page.locator(close_sel).last
                    if close_btn.count() > 0:
                        close_btn.click(timeout=3000)
                        time.sleep(500 / 1000)
                        if page.locator('.ant-modal:visible, .el-dialog:visible, [role="dialog"]:visible').count() == 0:
                            return True
                except:
                    continue
        except:
            pass

        # 3. ESC兜底
        try:
            page.keyboard.press('Escape')
            time.sleep(500 / 1000)
        except:
            pass

        return page.locator('.ant-modal:visible, .el-dialog:visible, [role="dialog"]:visible').count() == 0

        return page.locator('.ant-modal:visible, .el-dialog:visible, [role="dialog"]:visible').count() == 0

    @action(detail=False, methods=['post'], url_path='ai_extract_manual/start')
    def ai_extract_manual_start(self, request):
        """手动交互模式 — 启动浏览器会话（在专用线程中运行Playwright）"""
        import os
        import uuid
        import time
        import threading
        import asyncio
        os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'

        url = request.data.get('url', '').strip()
        login_config_id = request.data.get('login_config_id')
        project_id = request.data.get('project_id')

        if not url:
            return Response({'error': 'url 为必填项'}, status=status.HTTP_400_BAD_REQUEST)

        # 登录配置
        login_steps_data = None
        login_start_url = ''
        login_config = None
        if login_config_id and project_id:
            try:
                project = UiProject.objects.get(id=project_id)
                login_config = LoginConfig.objects.get(id=login_config_id, project=project)
                login_start_url = login_config.login_url or ''
                if not login_start_url and login_config.project:
                    login_start_url = login_config.project.base_url or ''
                test_case = login_config.login_test_case
                if test_case:
                    steps = test_case.steps.select_related('element', 'element__locator_strategy').order_by('step_number')
                    login_steps_data = []
                    for step in steps:
                        step_data = {
                            'action_type': step.action_type,
                            'input_value': step.input_value or '',
                            'wait_time': step.wait_time or 1000,
                            'action_wait': step.action_wait or 0,
                            'element': None
                        }
                        if step.element:
                            step_data['element'] = {
                                'locator_value': step.element.locator_value,
                                'locator_strategy': step.element.locator_strategy.name if step.element.locator_strategy else 'css'
                            }
                        login_steps_data.append(step_data)
            except Exception as e:
                print(f'[手动提取] 登录配置加载失败: {str(e)}')

        # 启动Playwright有头浏览器，在专用线程的事件循环中运行
        try:
            session_id = str(uuid.uuid4())

            # 创建专用线程的事件循环
            loop = asyncio.new_event_loop()

            # 用于接收启动结果
            start_result = {'error': None, 'page': None, 'browser': None, 'context': None, 'pw': None}

            def run_playwright_in_thread():
                """在专用线程中运行Playwright"""
                asyncio.set_event_loop(loop)
                from playwright.async_api import async_playwright

                async def do_start():
                    try:
                        pw = await async_playwright().start()
                        browser = await pw.chromium.launch(headless=False, args=['--start-maximized'])
                        context = await browser.new_context(no_viewport=True)
                        page = await context.new_page()

                        # 登录（如有）
                        if login_start_url and login_steps_data:
                            await page.goto(login_start_url, wait_until='networkidle', timeout=30000)
                            await asyncio.sleep(2)
                            for step_data in login_steps_data:
                                await self._async_execute_login_step(page, step_data)
                            try:
                                await page.wait_for_load_state('networkidle', timeout=10000)
                            except:
                                pass
                            await asyncio.sleep(2)

                        # 导航到目标页面
                        await page.goto(url, wait_until='networkidle', timeout=30000)
                        await asyncio.sleep(2)

                        # 注入浮动按钮
                        await self._async_inject_fab_button(page, session_id)

                        start_result['pw'] = pw
                        start_result['browser'] = browser
                        start_result['context'] = context
                        start_result['page'] = page
                    except Exception as e:
                        start_result['error'] = str(e)

                loop.run_until_complete(do_start())
                # 保持事件循环运行，等待后续capture/finish任务
                loop.run_forever()

            # 启动专用线程
            thread = threading.Thread(target=run_playwright_in_thread, daemon=True)
            thread.start()

            # 等待启动完成（最多60秒）
            for _ in range(120):
                time.sleep(0.5)
                if start_result['error'] or start_result['page']:
                    break

            if start_result['error']:
                return Response({'error': f'启动浏览器失败: {start_result["error"]}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if not start_result['page']:
                return Response({'error': '启动浏览器超时'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 存储会话
            self._manual_sessions[session_id] = {
                'loop': loop,
                'thread': thread,
                'playwright': start_result['pw'],
                'browser': start_result['browser'],
                'context': start_result['context'],
                'page': start_result['page'],
                'captures': [],
                'created_at': time.time()
            }

            return Response({
                'session_id': session_id,
                'message': '浏览器已打开，请手动操作后点击"提取当前页面"按钮'
            })
        except Exception as e:
            import traceback
            return Response({'error': f'启动浏览器失败: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='ai_extract_manual/capture')
    def ai_extract_manual_capture(self, request):
        """手动交互模式 — 提取当前页面元素（通过专用线程事件循环执行）"""
        import time
        import asyncio

        session_id = request.data.get('session_id')
        page_name = request.data.get('page_name', '').strip()

        if not session_id or session_id not in self._manual_sessions:
            return Response({'error': '无效的会话ID，请重新启动'}, status=status.HTTP_400_BAD_REQUEST)

        session = self._manual_sessions[session_id]
        loop = session['loop']

        # 检查是否超时（5分钟）
        if time.time() - session['created_at'] > 300:
            self._cleanup_manual_session(session_id)
            return Response({'error': '会话已超时(5分钟)，请重新启动'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 在专用线程的事件循环中执行Playwright操作
            async def do_capture():
                page = session['page']
                page_title = await page.title()

                # 注入提取JS
                extract_js = """
                () => {
                    const results = [];
                    const interactiveSelectors = [
                        'input', 'button', 'a[href]', 'select', 'textarea',
                        '[role="button"]', '[role="link"]', '[role="tab"]',
                        '[role="menuitem"]', '[role="option"]', '[role="switch"]',
                        '[onclick]', '[contenteditable="true"]',
                        '.el-button', '.el-input__inner', '.el-select',
                        '.el-checkbox', '.el-radio', '.el-switch',
                        '.ant-btn', '.ant-input', '.ant-select', '.ant-checkbox',
                        '.ant-radio', '.ant-switch'
                    ];
                    const seen = new Set();
                    interactiveSelectors.forEach(selector => {
                        try {
                            document.querySelectorAll(selector).forEach(el => {
                                if (el.id === 'ai-extract-fab' || el.closest('#ai-extract-fab')) return;
                                const rect = el.getBoundingClientRect();
                                if (rect.width === 0 && rect.height === 0) return;
                                const style = window.getComputedStyle(el);
                                if (style.display === 'none' || style.visibility === 'hidden') return;
                                const key = el.tagName + '|' + (el.id||'') + '|' + el.className + '|' + rect.x + '|' + rect.y;
                                if (seen.has(key)) return;
                                seen.add(key);
                                results.push({
                                    tag: el.tagName.toLowerCase(),
                                    id: el.id || '',
                                    name: el.getAttribute('name') || '',
                                    className: (typeof el.className === 'string') ? el.className.substring(0, 200) : '',
                                    type: el.type || '',
                                    placeholder: el.placeholder || '',
                                    value: (el.value || '').substring(0, 50),
                                    href: el.href || '',
                                    role: el.getAttribute('role') || '',
                                    ariaLabel: el.getAttribute('aria-label') || '',
                                    dataTestId: el.getAttribute('data-testid') || '',
                                    text: (el.textContent || '').trim().substring(0, 80),
                                    title: el.title || '',
                                    visible: true,
                                    rect: { x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height) },
                                    isInTableRow: false,
                                    tableRowIndex: -1
                                });
                            });
                        } catch(e) {}
                    });
                    return { elements: results.slice(0, 80) };
                }
                """

                extract_result = await page.evaluate(extract_js)
                raw_elements = extract_result.get('elements', [])

                # 计算定位器 + 验证
                for elem in raw_elements:
                    elem['page_title'] = page_title
                    if page_name:
                        elem['source'] = page_name
                    css_selector = self._compute_css_selector(elem)
                    xpath = self._compute_xpath(elem)
                    validation = await self._async_validate_locators(page, elem, css_selector, xpath)
                    elem['auto_css'] = validation['css_selector']
                    elem['auto_xpath'] = validation['xpath']
                    elem['validation_status'] = validation['validation_status']
                    elem['validation_details'] = validation['validation_details']

                # AI分析
                try:
                    ai_elements = self._ai_analyze_elements(raw_elements)
                except Exception as e:
                    print(f'[手动提取] AI分析失败，回退规则引擎: {str(e)}')
                    ai_elements = self._rule_based_classify(raw_elements)

                for elem in ai_elements:
                    if page_name:
                        elem['page'] = page_name
                        elem['source'] = page_name

                # 记录这次提取
                capture_info = {
                    'index': len(session['captures']) + 1,
                    'page_name': page_name or page_title,
                    'element_count': len(ai_elements),
                    'elements': ai_elements
                }
                session['captures'].append(capture_info)

                # 重新注入浮动按钮
                await asyncio.sleep(0.5)
                await self._async_inject_fab_button(page, session_id)

                return capture_info

            # 提交到专用线程的事件循环并等待结果
            future = asyncio.run_coroutine_threadsafe(do_capture(), loop)
            capture_info = future.result(timeout=120)

            return Response({
                'elements': capture_info['elements'],
                'capture_index': capture_info['index'],
                'total_captures': len(session['captures'])
            })

        except Exception as e:
            import traceback
            print(f'[手动提取] 提取失败: {traceback.format_exc()}')
            return Response({'error': f'提取失败: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='ai_extract_manual/finish')
    def ai_extract_manual_finish(self, request):
        """手动交互模式 — 完成提取，汇总所有结果"""
        import asyncio

        session_id = request.data.get('session_id')

        if not session_id or session_id not in self._manual_sessions:
            return Response({'error': '无效的会话ID'}, status=status.HTTP_400_BAD_REQUEST)

        session = self._manual_sessions[session_id]
        captures = session['captures']

        # 汇总所有提取结果
        all_elements = []
        seen_keys = set()
        for capture in captures:
            for elem in capture['elements']:
                # 去重：按 元素名称+定位策略+定位值 去重，避免同名同定位的重复元素
                # 不同名称的元素即使定位器相同也保留（如多个button.ant-btn）
                dedup_key = (
                    elem.get('name', ''),
                    elem.get('locator_strategy', ''),
                    elem.get('locator_value', '')
                )
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)
                all_elements.append(elem)

        # 按元素名称去重，过滤列表行重复的操作按钮
        all_elements = self._deduplicate_by_name(all_elements)

        # 关闭浏览器（在专用线程的事件循环中执行）
        loop = session['loop']

        async def do_cleanup():
            try:
                await session['browser'].close()
            except:
                pass
            try:
                await session['playwright'].stop()
            except:
                pass

        future = asyncio.run_coroutine_threadsafe(do_cleanup(), loop)
        try:
            future.result(timeout=10)
        except:
            pass

        # 停止事件循环
        loop.call_soon_threadsafe(loop.stop)

        del self._manual_sessions[session_id]

        return Response({
            'elements': all_elements,
            'captures': [
                {'index': c['index'], 'page_name': c['page_name'], 'element_count': c['element_count']}
                for c in captures
            ]
        })

    def _inject_fab_button(self, page, session_id):
        """在页面中注入浮动操作按钮"""
        # 获取当前请求的host（后端地址）
        fab_js = """
        (sessionId) => {
            // 清除旧的浮动按钮
            const oldFab = document.getElementById('ai-extract-fab');
            if (oldFab) oldFab.remove();

            const fab = document.createElement('div');
            fab.id = 'ai-extract-fab';
            fab.innerHTML = `
                <div style="position: fixed; bottom: 30px; right: 30px; z-index: 999999;
                     display: flex; flex-direction: column; gap: 8px; font-family: sans-serif;">
                    <button id="ai-extract-btn" style="
                        width: 120px; padding: 10px 16px; border: none; border-radius: 8px;
                        background: #409 EFF; color: white; font-size: 13px; font-weight: 600;
                        cursor: pointer; box-shadow: 0 4px 12px rgba(64,158,255,0.4);
                        transition: all 0.2s;
                    " onmouseover="this.style.transform='scale(1.05)'"
                       onmouseout="this.style.transform='scale(1)'">
                        提取当前元素
                    </button>
                    <button id="ai-finish-btn" style="
                        width: 120px; padding: 10px 16px; border: none; border-radius: 8px;
                        background: #f56c6c; color: white; font-size: 13px; font-weight: 600;
                        cursor: pointer; box-shadow: 0 4px 12px rgba(245,108,108,0.4);
                        transition: all 0.2s;
                    " onmouseover="this.style.transform='scale(1.05)'"
                       onmouseout="this.style.transform='scale(1)'">
                        完成提取
                    </button>
                </div>
            `;
            document.body.appendChild(fab);
        }
        """
        try:
            page.evaluate(fab_js, session_id)
        except:
            pass

    def _cleanup_manual_session(self, session_id):
        """清理手动交互会话（仅用于外部清理，正常流程使用finish）"""
        if session_id not in self._manual_sessions:
            return
        session = self._manual_sessions[session_id]
        loop = session.get('loop')
        try:
            if loop and loop.is_running():
                import asyncio
                async def do_close():
                    try:
                        await session['browser'].close()
                    except:
                        pass
                    try:
                        await session['playwright'].stop()
                    except:
                        pass
                future = asyncio.run_coroutine_threadsafe(do_close(), loop)
                try:
                    future.result(timeout=5)
                except:
                    pass
                loop.call_soon_threadsafe(loop.stop)
            else:
                session['browser'].close()
                session['playwright'].stop()
        except:
            pass
        del self._manual_sessions[session_id]

    # ==================== 交互式选取模式 ====================

    @action(detail=False, methods=['post'], url_path='ai_pick/start')
    def ai_pick_start(self, request):
        """交互式选取模式 — 启动浏览器会话，用户点击元素后AI识别定位器"""
        import os
        import uuid
        import time
        import threading
        import asyncio
        os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'

        url = request.data.get('url', '').strip()
        login_config_id = request.data.get('login_config_id')
        project_id = request.data.get('project_id')

        if not url:
            return Response({'error': 'url 为必填项'}, status=status.HTTP_400_BAD_REQUEST)

        # URL规范化：如果URL是相对路径，用项目base_url拼接；如果协议不一致则修正
        if project_id:
            try:
                _proj = UiProject.objects.get(id=project_id)
                _base_url = (_proj.base_url or '').rstrip('/')
                # 相对路径拼接
                if url and not url.startswith('http://') and not url.startswith('https://'):
                    if _base_url:
                        url = f"{_base_url}/{url.lstrip('/')}"
                    else:
                        return Response({'error': '相对路径需要项目配置base_url'}, status=status.HTTP_400_BAD_REQUEST)
                # 协议修正：项目base_url是https但用户输入了http，自动修正以保持cookie
                if _base_url.startswith('https://') and url.startswith('http://'):
                    url = 'https://' + url[7:]
                    print(f'[URL规范化] http→https: {url}')
            except Exception as e:
                print(f'[URL规范化] 失败: {str(e)}')

        # 登录配置（复用手动模式的逻辑）
        login_steps_data = None
        login_start_url = ''
        if login_config_id and project_id:
            try:
                project = UiProject.objects.get(id=project_id)
                login_config = LoginConfig.objects.get(id=login_config_id, project=project)
                login_start_url = login_config.login_url or ''
                if not login_start_url and login_config.project:
                    login_start_url = login_config.project.base_url or ''
                test_case = login_config.login_test_case
                if test_case:
                    steps = test_case.steps.select_related('element', 'element__locator_strategy').order_by('step_number')
                    login_steps_data = []
                    for step in steps:
                        step_data = {
                            'action_type': step.action_type,
                            'input_value': step.input_value or '',
                            'wait_time': step.wait_time or 1000,
                            'action_wait': step.action_wait or 0,
                            'element': None
                        }
                        if step.element:
                            step_data['element'] = {
                                'locator_value': step.element.locator_value,
                                'locator_strategy': step.element.locator_strategy.name if step.element.locator_strategy else 'css'
                            }
                        login_steps_data.append(step_data)
            except Exception as e:
                print(f'[交互选取] 登录配置加载失败: {str(e)}')

        try:
            session_id = str(uuid.uuid4())
            loop = asyncio.new_event_loop()
            start_result = {'error': None, 'page': None, 'browser': None, 'context': None, 'pw': None}

            def run_playwright_in_thread():
                asyncio.set_event_loop(loop)
                from playwright.async_api import async_playwright

                async def do_start():
                    try:
                        pw = await async_playwright().start()
                        browser = await pw.chromium.launch(headless=False, args=['--start-maximized'])
                        context = await browser.new_context(no_viewport=True)
                        page = await context.new_page()

                        if login_start_url and login_steps_data:
                            await page.goto(login_start_url, wait_until='networkidle', timeout=30000)
                            await asyncio.sleep(2)
                            for step_data in login_steps_data:
                                await self._async_execute_login_step(page, step_data)
                            try:
                                await page.wait_for_load_state('networkidle', timeout=10000)
                            except:
                                pass
                            await asyncio.sleep(2)

                        await page.goto(url, wait_until='networkidle', timeout=30000)
                        await asyncio.sleep(2)

                        # 注入交互式选取脚本
                        await self._async_inject_pick_script(page, session_id)

                        start_result['pw'] = pw
                        start_result['browser'] = browser
                        start_result['context'] = context
                        start_result['page'] = page
                    except Exception as e:
                        start_result['error'] = str(e)

                loop.run_until_complete(do_start())
                loop.run_forever()

            thread = threading.Thread(target=run_playwright_in_thread, daemon=True)
            thread.start()

            for _ in range(120):
                time.sleep(0.5)
                if start_result['error'] or start_result['page']:
                    break

            if start_result['error']:
                return Response({'error': f'启动浏览器失败: {start_result["error"]}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            if not start_result['page']:
                return Response({'error': '启动浏览器超时'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            self._pick_sessions[session_id] = {
                'loop': loop,
                'thread': thread,
                'playwright': start_result['pw'],
                'browser': start_result['browser'],
                'context': start_result['context'],
                'page': start_result['page'],
                'picked_elements': [],
                'created_at': time.time()
            }

            return Response({
                'session_id': session_id,
                'message': '浏览器已打开，请在页面中点击要提取的元素'
            })
        except Exception as e:
            import traceback
            return Response({'error': f'启动失败: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='ai_pick/status')
    def ai_pick_status(self, request):
        """交互式选取模式 — 获取已选取的元素列表（供前端轮询）"""
        session_id = request.query_params.get('session_id')
        if not session_id or session_id not in self._pick_sessions:
            return Response({'error': '无效的会话ID'}, status=status.HTTP_400_BAD_REQUEST)

        session = self._pick_sessions[session_id]
        import time
        if time.time() - session['created_at'] > 600:
            self._cleanup_pick_session(session_id)
            return Response({'error': '会话已超时(10分钟)，请重新启动'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'elements': session['picked_elements'],
            'count': len(session['picked_elements'])
        })

    @action(detail=False, methods=['post'], url_path='ai_pick/remove')
    def ai_pick_remove(self, request):
        """交互式选取模式 — 删除指定元素"""
        session_id = request.data.get('session_id')
        element_index = request.data.get('index')
        if not session_id or session_id not in self._pick_sessions:
            return Response({'error': '无效的会话ID'}, status=status.HTTP_400_BAD_REQUEST)

        session = self._pick_sessions[session_id]
        if element_index is not None and 0 <= element_index < len(session['picked_elements']):
            removed = session['picked_elements'].pop(element_index)
            return Response({
                'success': True,
                'removed': removed,
                'count': len(session['picked_elements'])
            })
        return Response({'error': '无效的元素索引'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='ai_pick/finish')
    def ai_pick_finish(self, request):
        """交互式选取模式 — 完成选取，关闭浏览器，返回所有元素"""
        import asyncio

        session_id = request.data.get('session_id')
        if not session_id or session_id not in self._pick_sessions:
            return Response({'error': '无效的会话ID'}, status=status.HTTP_400_BAD_REQUEST)

        session = self._pick_sessions[session_id]
        all_elements = session['picked_elements']

        # 关闭浏览器
        loop = session['loop']

        async def do_cleanup():
            try:
                await session['browser'].close()
            except:
                pass
            try:
                await session['playwright'].stop()
            except:
                pass

        future = asyncio.run_coroutine_threadsafe(do_cleanup(), loop)
        try:
            future.result(timeout=10)
        except:
            pass

        loop.call_soon_threadsafe(loop.stop)
        del self._pick_sessions[session_id]

        return Response({
            'elements': all_elements,
            'count': len(all_elements)
        })

    def _cleanup_pick_session(self, session_id):
        """清理交互式选取会话"""
        if session_id not in self._pick_sessions:
            return
        session = self._pick_sessions[session_id]
        loop = session.get('loop')
        try:
            if loop and loop.is_running():
                import asyncio
                async def do_close():
                    try:
                        await session['browser'].close()
                    except:
                        pass
                    try:
                        await session['playwright'].stop()
                    except:
                        pass
                future = asyncio.run_coroutine_threadsafe(do_close(), loop)
                try:
                    future.result(timeout=5)
                except:
                    pass
                loop.call_soon_threadsafe(loop.stop)
        except:
            pass
        del self._pick_sessions[session_id]

    async def _async_inject_pick_script(self, page, session_id):
        """注入交互式选取脚本 — mouseover高亮 + click捕获 + 浮层面板"""
        # 先暴露 Python 函数，供 JS 在用户点击元素时调用
        async def on_element_clicked(element_data):
            """JS调用：用户点击元素后，计算定位器并AI分析"""
            try:
                # 计算CSS和XPath
                css_selector = self._compute_css_selector(element_data)
                xpath = self._compute_xpath(element_data)

                # 验证定位器
                validation = await self._async_validate_locators(page, element_data, css_selector, xpath)
                element_data['auto_css'] = validation['css_selector']
                element_data['auto_xpath'] = validation['xpath']
                element_data['validation_status'] = validation['validation_status']
                element_data['validation_details'] = validation['validation_details']

                # AI分析单个元素
                try:
                    ai_result = self._ai_analyze_single_element(element_data)
                except Exception as e:
                    print(f'[交互选取] AI分析失败，回退规则引擎: {str(e)}')
                    ai_result = self._rule_based_classify([element_data])[0] if self._rule_based_classify([element_data]) else None

                if ai_result:
                    ai_result['source'] = '交互选取'

                    # 验证AI返回的定位器，如果不唯一则尝试修正
                    ai_result = await self._validate_and_fix_locator(page, ai_result, element_data)

                    # 存入session（去重：相同 locator_strategy + locator_value 不重复添加）
                    session = self._pick_sessions.get(session_id)
                    if session:
                        new_key = (ai_result.get('locator_strategy', ''), ai_result.get('locator_value', ''))
                        existing_keys = {(e.get('locator_strategy', ''), e.get('locator_value', '')) for e in session['picked_elements']}
                        if new_key not in existing_keys:
                            session['picked_elements'].append(ai_result)
                    return ai_result
                return None
            except Exception as e:
                print(f'[交互选取] 元素处理失败: {str(e)}')
                return None

        await page.expose_function('__aiPickElement', on_element_clicked)

        # 暴露改名函数
        async def on_element_renamed(index, new_name):
            """JS调用：用户在浮窗中修改元素名称"""
            session = self._pick_sessions.get(session_id)
            if session and 0 <= index < len(session['picked_elements']):
                session['picked_elements'][index]['name'] = new_name
                return True
            return False

        await page.expose_function('__aiPickRename', on_element_renamed)

        # 注入选取模式UI脚本
        pick_js = """
        () => {
            // 清除旧面板
            const oldPanel = document.getElementById('ai-pick-panel');
            if (oldPanel) oldPanel.remove();

            // 创建样式
            const style = document.createElement('style');
            style.id = 'ai-pick-style';
            style.textContent = `
                .ai-pick-highlight {
                    outline: 2px solid #ff4d4f !important;
                    outline-offset: 1px !important;
                    cursor: crosshair !important;
                }
                #ai-pick-panel {
                    position: fixed; top: 16px; right: 16px; z-index: 999999;
                    width: 320px; max-height: 70vh; overflow-y: auto;
                    background: rgba(255,255,255,0.98); border-radius: 10px;
                    box-shadow: 0 6px 24px rgba(0,0,0,0.15);
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    font-size: 13px;
                }
                #ai-pick-panel .pick-header {
                    padding: 12px 16px; background: #409EFF; color: white;
                    border-radius: 10px 10px 0 0; font-weight: 600; font-size: 14px;
                    display: flex; justify-content: space-between; align-items: center;
                    cursor: move; user-select: none;
                }
                #ai-pick-panel .pick-body { padding: 8px 0; }
                #ai-pick-panel .pick-item {
                    padding: 8px 16px; border-bottom: 1px solid #f0f0f0;
                    display: flex; justify-content: space-between; align-items: center;
                }
                #ai-pick-panel .pick-item:last-child { border-bottom: none; }
                #ai-pick-panel .pick-item-name {
                    font-weight: 500; color: #333; flex: 1; min-width: 0;
                    padding: 2px 6px; border: 1px solid transparent; border-radius: 4px;
                    outline: none; background: transparent; cursor: text;
                    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
                }
                #ai-pick-panel .pick-item-name:hover {
                    border-color: #d9d9d9; background: #fafafa;
                }
                #ai-pick-panel .pick-item-name:focus {
                    border-color: #409EFF; background: white;
                    white-space: normal; overflow: visible;
                }
                #ai-pick-panel .pick-item-type {
                    font-size: 11px; padding: 2px 8px; border-radius: 10px;
                    background: #e6f7ff; color: #1890ff;
                }
                #ai-pick-panel .pick-loading {
                    padding: 12px 16px; text-align: center; color: #999;
                }
                #ai-pick-panel .pick-empty {
                    padding: 20px 16px; text-align: center; color: #999;
                }
                #ai-pick-panel .pick-footer {
                    padding: 10px 16px; border-top: 1px solid #f0f0f0;
                    display: flex; justify-content: center;
                }
                #ai-pick-panel .pick-hint {
                    padding: 6px 16px; font-size: 11px; color: #999; text-align: center;
                    background: #fafafa;
                }
                #ai-pick-panel .pick-toolbar {
                    padding: 6px 12px; display: flex; gap: 8px; border-bottom: 1px solid #f0f0f0;
                }
                #ai-pick-panel .pick-toolbar button {
                    flex: 1; padding: 5px 10px; border: 1px solid #d9d9d9; border-radius: 6px;
                    background: white; color: #666; font-size: 12px; cursor: pointer; transition: all 0.15s;
                }
                #ai-pick-panel .pick-toolbar button.active {
                    background: #409EFF; color: white; border-color: #409EFF;
                }
                #ai-pick-panel .pick-mode-badge {
                    display: inline-block; padding: 2px 8px; border-radius: 10px;
                    font-size: 11px; font-weight: 500;
                }
                #ai-pick-panel .pick-mode-badge.select {
                    background: #fff1f0; color: #ff4d4f;
                }
                #ai-pick-panel .pick-mode-badge.browse {
                    background: #f6ffed; color: #52c41a;
                }
            `;
            document.head.appendChild(style);

            // 创建面板
            const panel = document.createElement('div');
            panel.id = 'ai-pick-panel';
            panel.innerHTML = `
                <div class="pick-header">
                    <span>选取模式</span>
                    <span id="pick-count">0 个元素</span>
                </div>
                <div class="pick-toolbar">
                    <button id="pick-mode-select" class="active">选取元素</button>
                    <button id="pick-mode-browse">浏览操作</button>
                </div>
                <div class="pick-hint" id="pick-hint">
                    <span class="pick-mode-badge select">选取</span> 鼠标悬停高亮，点击选取元素
                </div>
                <div class="pick-body" id="pick-body">
                    <div class="pick-empty">尚未选取任何元素</div>
                </div>
            `;
            document.body.appendChild(panel);

            // 拖拽逻辑：按住 header 拖动面板
            const pickHeader = panel.querySelector('.pick-header');
            let isDragging = false;
            let dragOffsetX = 0;
            let dragOffsetY = 0;

            pickHeader.addEventListener('mousedown', (e) => {
                isDragging = true;
                const rect = panel.getBoundingClientRect();
                dragOffsetX = e.clientX - rect.left;
                dragOffsetY = e.clientY - rect.top;
                e.preventDefault();
            });

            document.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                let newX = e.clientX - dragOffsetX;
                let newY = e.clientY - dragOffsetY;
                // 限制不超出视口
                const maxX = window.innerWidth - panel.offsetWidth;
                const maxY = window.innerHeight - 40;
                newX = Math.max(0, Math.min(newX, maxX));
                newY = Math.max(0, Math.min(newY, maxY));
                panel.style.left = newX + 'px';
                panel.style.top = newY + 'px';
                panel.style.right = 'auto';
            });

            document.addEventListener('mouseup', () => {
                isDragging = false;
            });

            // 模式切换：选取模式 vs 浏览模式
            let pickMode = 'select'; // 'select' or 'browse'
            const btnSelect = document.getElementById('pick-mode-select');
            const btnBrowse = document.getElementById('pick-mode-browse');
            const hintEl = document.getElementById('pick-hint');

            btnSelect.addEventListener('click', () => {
                pickMode = 'select';
                btnSelect.classList.add('active');
                btnBrowse.classList.remove('active');
                hintEl.innerHTML = '<span class="pick-mode-badge select">选取</span> 鼠标悬停高亮，点击选取元素';
            });

            btnBrowse.addEventListener('click', () => {
                pickMode = 'browse';
                btnBrowse.classList.add('active');
                btnSelect.classList.remove('active');
                // 清除高亮
                if (highlightedEl) {
                    highlightedEl.classList.remove('ai-pick-highlight');
                    highlightedEl = null;
                }
                hintEl.innerHTML = '<span class="pick-mode-badge browse">浏览</span> 正常操作页面，可点击按钮打开弹窗';
            });

            let highlightedEl = null;
            let isProcessing = false;

            // mouseover 高亮（仅选取模式）
            document.addEventListener('mouseover', (e) => {
                if (isProcessing || pickMode !== 'select') return;
                const el = e.target;
                // 排除面板自身
                if (el.closest('#ai-pick-panel') || el.closest('#ai-pick-style')) return;
                if (highlightedEl && highlightedEl !== el) {
                    highlightedEl.classList.remove('ai-pick-highlight');
                }
                el.classList.add('ai-pick-highlight');
                highlightedEl = el;
            }, true);

            // mouseout 移除高亮
            document.addEventListener('mouseout', (e) => {
                if (highlightedEl) {
                    highlightedEl.classList.remove('ai-pick-highlight');
                }
            }, true);

            // click 捕获（仅选取模式拦截，浏览模式放行）
            document.addEventListener('click', async (e) => {
                // 浏览模式：不拦截，让页面正常响应
                if (pickMode !== 'select') return;

                let el = e.target;
                // 排除面板自身
                if (el.closest('#ai-pick-panel') || el.closest('#ai-pick-style')) return;

                // 拦截默认行为
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();

                if (isProcessing) return;
                isProcessing = true;

                // 移除高亮
                el.classList.remove('ai-pick-highlight');

                // 向上查找最近的交互元素（button, a, input, select, textarea, [role=button] 等）
                // 用户可能点击的是按钮内部的 span/icon，需要定位到真正的交互元素
                const interactiveSelectors = 'button, a[href], input, select, textarea, [role="button"], [role="link"], [role="switch"], [onclick], .ant-btn, .el-button';
                let interactiveEl = el.closest(interactiveSelectors);
                if (interactiveEl) {
                    el = interactiveEl;
                }

                // 收集元素DOM信息
                const rect = el.getBoundingClientRect();
                const parentEl = el.parentElement;
                const elementData = {
                    tag: el.tagName.toLowerCase(),
                    id: el.id || '',
                    name: el.getAttribute('name') || '',
                    className: (typeof el.className === 'string') ? el.className.substring(0, 200) : '',
                    type: el.type || '',
                    placeholder: el.placeholder || '',
                    value: (el.value || '').substring(0, 50),
                    href: el.href || '',
                    role: el.getAttribute('role') || '',
                    ariaLabel: el.getAttribute('aria-label') || '',
                    dataTestId: el.getAttribute('data-testid') || '',
                    text: (el.textContent || '').trim().substring(0, 80),
                    title: el.title || '',
                    visible: true,
                    rect: { x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height) },
                    isInTableRow: false,
                    tableRowIndex: -1,
                    outerHTML: el.outerHTML.substring(0, 500),
                    parentInfo: parentEl ? {
                        tag: parentEl.tagName.toLowerCase(),
                        className: (typeof parentEl.className === 'string') ? parentEl.className.substring(0, 100) : '',
                        text: (parentEl.textContent || '').trim().substring(0, 80)
                    } : null
                };

                // 显示加载状态
                const body = document.getElementById('pick-body');
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'pick-loading';
                loadingDiv.id = 'pick-loading';
                loadingDiv.textContent = '正在分析元素...';
                body.appendChild(loadingDiv);

                try {
                    const result = await window.__aiPickElement(elementData);
                    // 移除加载状态
                    const ld = document.getElementById('pick-loading');
                    if (ld) ld.remove();

                    if (result) {
                        // 移除空提示
                        const empty = body.querySelector('.pick-empty');
                        if (empty) empty.remove();

                        // 添加到列表
                        const item = document.createElement('div');
                        item.className = 'pick-item';
                        const typeMap = {
                            'INPUT': '输入框', 'BUTTON': '按钮', 'LINK': '链接',
                            'DROPDOWN': '下拉框', 'CHECKBOX': '复选框', 'RADIO': '单选框',
                            'TEXT': '文本', 'IMAGE': '图片', 'TABLE': '表格',
                            'CONTAINER': '容器', 'FORM': '表单', 'MODAL': '弹窗'
                        };
                        const typeText = typeMap[result.element_type] || result.element_type || '元素';
                        const itemName = result.name || '未命名';
                        const itemIndex = body.querySelectorAll('.pick-item').length;
                        item.innerHTML = `
                            <span class="pick-item-name" contenteditable="true" data-index="${itemIndex}" title="点击编辑名称">${itemName}</span>
                            <span class="pick-item-type">${typeText}</span>
                        `;
                        body.appendChild(item);

                        // 监听名称编辑，同步到后端 session
                        const nameSpan = item.querySelector('.pick-item-name');
                        nameSpan.addEventListener('blur', async () => {
                            const newName = nameSpan.textContent.trim();
                            const idx = parseInt(nameSpan.getAttribute('data-index'));
                            if (newName) {
                                try {
                                    await window.__aiPickRename(idx, newName);
                                } catch(e) {
                                    console.error('[交互选取] 改名失败:', e);
                                }
                            }
                        });
                        nameSpan.addEventListener('keydown', (e) => {
                            if (e.key === 'Enter') {
                                e.preventDefault();
                                nameSpan.blur();
                            }
                        });

                        // 更新计数
                        const countEl = document.getElementById('pick-count');
                        const items = body.querySelectorAll('.pick-item');
                        countEl.textContent = items.length + ' 个元素';
                    }
                } catch (err) {
                    const ld = document.getElementById('pick-loading');
                    if (ld) ld.remove();
                    console.error('[交互选取] 分析失败:', err);
                } finally {
                    isProcessing = false;
                }
            }, true);
        }
        """
        await page.evaluate(pick_js)

    async def _validate_and_fix_locator(self, page, ai_result, element_data):
        """验证AI返回的定位器，如果不唯一则尝试生成更精确的定位表达式"""
        strategy = ai_result.get('locator_strategy', '')
        value = ai_result.get('locator_value', '')
        text = (element_data.get('text', '') or '').strip()
        tag = element_data.get('tag', '')
        elem_id = element_data.get('id', '')
        aria_label = element_data.get('ariaLabel', '')
        placeholder = element_data.get('placeholder', '')
        name_attr = element_data.get('name', '')

        # 如果已有ID且唯一，直接用
        if elem_id:
            try:
                count = await page.locator(f'#{elem_id}').count()
                if count == 1:
                    ai_result['locator_strategy'] = 'ID'
                    ai_result['locator_value'] = elem_id
                    ai_result['validation_status'] = 'VALID'
                    ai_result['validation_details'] = 'ID唯一匹配'
                    return ai_result
            except:
                pass

        # 验证AI返回的定位器
        match_count = 0
        try:
            if strategy == 'XPath':
                match_count = await page.locator(f'xpath={value}').count()
            elif strategy == 'CSS':
                match_count = await page.locator(value).count()
        except:
            pass

        if match_count == 1:
            ai_result['validation_status'] = 'VALID'
            ai_result['validation_details'] = '定位器唯一匹配'
            return ai_result

        # 不唯一或无效，尝试生成基于文本的精确XPath
        if text and len(text) <= 30:
            # 尝试多种XPath文本定位方式
            candidates = []
            # 1. 文本在元素自身
            candidates.append(f'//{tag}[contains(text(),"{text}")]')
            # 2. 文本在直接子元素
            candidates.append(f'//{tag}[.//*[contains(text(),"{text}")]]')
            # 3. 文本在任意后代元素
            candidates.append(f'//{tag}[contains(.,"{text}")]')

            for xp in candidates:
                try:
                    count = await page.locator(f'xpath={xp}').count()
                    if count == 1:
                        ai_result['locator_strategy'] = 'XPath'
                        ai_result['locator_value'] = xp
                        ai_result['validation_status'] = 'VALID'
                        ai_result['validation_details'] = f'文本XPath唯一匹配: {xp}'
                        print(f'[交互选取] 定位器修正: {strategy}:{value} → XPath:{xp}')
                        return ai_result
                except:
                    continue

        # 尝试 aria-label
        if aria_label:
            xp = f'//{tag}[@aria-label="{aria_label}"]'
            try:
                count = await page.locator(f'xpath={xp}').count()
                if count == 1:
                    ai_result['locator_strategy'] = 'XPath'
                    ai_result['locator_value'] = xp
                    ai_result['validation_status'] = 'VALID'
                    ai_result['validation_details'] = f'aria-label唯一匹配'
                    return ai_result
            except:
                pass

        # 尝试 placeholder
        if placeholder:
            xp = f'//{tag}[@placeholder="{placeholder}"]'
            try:
                count = await page.locator(f'xpath={xp}').count()
                if count == 1:
                    ai_result['locator_strategy'] = 'XPath'
                    ai_result['locator_value'] = xp
                    ai_result['validation_status'] = 'VALID'
                    ai_result['validation_details'] = f'placeholder唯一匹配'
                    return ai_result
            except:
                pass

        # 尝试 name 属性
        if name_attr and ' ' not in name_attr:
            xp = f'//{tag}[@name="{name_attr}"]'
            try:
                count = await page.locator(f'xpath={xp}').count()
                if count == 1:
                    ai_result['locator_strategy'] = 'XPath'
                    ai_result['locator_value'] = xp
                    ai_result['validation_status'] = 'VALID'
                    ai_result['validation_details'] = f'name属性唯一匹配'
                    return ai_result
            except:
                pass

        # 所有策略都无法唯一定位，保留原值但标记状态
        if match_count > 1:
            ai_result['validation_status'] = 'PARTIAL'
            ai_result['validation_details'] = f'定位器匹配{match_count}个元素，不够精确'
        else:
            ai_result['validation_status'] = element_data.get('validation_status', 'UNVALIDATED')
            ai_result['validation_details'] = element_data.get('validation_details', '未验证')

        return ai_result

    def _ai_analyze_single_element(self, elem):
        """使用 LLM 分析单个元素，返回结构化元素信息"""
        from langchain_openai import ChatOpenAI
        from apps.requirement_analysis.models import AIModelConfig
        import asyncio
        import json
        import re

        config_obj = AIModelConfig.objects.filter(role='browser_use_text', is_active=True).first()
        if not config_obj:
            raise Exception('未找到可用的AI模型配置')

        api_key = config_obj.api_key
        base_url = config_obj.base_url
        model_name = config_obj.model_name

        if not api_key:
            raise Exception('AI模型API Key未配置')

        llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=0.1,
            max_tokens=1000
        )

        # 构造精简的元素数据
        elem_data = {
            'tag': elem.get('tag', ''),
            'id': elem.get('id', ''),
            'name': elem.get('name', ''),
            'type': elem.get('type', ''),
            'placeholder': elem.get('placeholder', ''),
            'text': elem.get('text', '')[:50],
            'role': elem.get('role', ''),
            'ariaLabel': elem.get('ariaLabel', ''),
            'className': elem.get('className', '')[:100],
            'auto_css': elem.get('auto_css', ''),
            'auto_xpath': elem.get('auto_xpath', ''),
            'outerHTML': elem.get('outerHTML', '')[:300],
        }

        prompt = f"""你是一个UI自动化测试元素定位专家。以下是用户点击选中的网页元素DOM数据，请分析并返回：
1. 元素的中文名称（简洁准确，如"用户名输入框"、"查询按钮"、"新增链接"）
2. 最佳定位策略和定位值
3. 元素类型，必须是以下之一：INPUT, BUTTON, LINK, DROPDOWN, CHECKBOX, RADIO, TEXT, IMAGE, CONTAINER, TABLE, FORM, MODAL

定位策略必须是以下之一：ID, CSS, XPath, name, class, text, placeholder, role, label, title, test-id

定位值生成规则（按优先级）：
- 有id属性：用 ID 策略，值如 username（不要加#前缀）
- 有data-testid：用 test-id 策略
- 有name属性（不含空格）：用 name 策略
- 有placeholder：用 placeholder 策略
- 有aria-label：用 label 策略
- 按钮类元素（button/a/[role=button]）且有文本内容：用 XPath 策略，值如 //button[contains(text(),"新增")] 或 //button[.//span[contains(text(),"新增")]]（根据文本在元素自身还是子元素中）
- 有唯一className组合：用 CSS 策略，如 button.ant-btn-primary
- 以上都不满足时，结合 tag + 文本生成 XPath

重要：定位值必须能唯一定位到该元素。不要返回简单的标签名（如 span、button），必须包含足够的限定条件。

请严格按以下JSON格式返回，不要添加任何其他文字：
{{"name": "元素名称", "element_type": "BUTTON", "locator_strategy": "XPath", "locator_value": "//button[contains(text(),\\"新增\\")]", "description": "简短描述"}}

元素DOM数据：
{json.dumps(elem_data, ensure_ascii=False)}"""

        # 同步调用 LLM
        import concurrent.futures
        def call_llm():
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(llm.ainvoke(prompt))
            finally:
                loop.close()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(call_llm)
            response = future.result(timeout=60)
        content = response.content

        # 解析JSON
        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(1))
                # 补充备份定位器和验证状态
                backup = []
                css_sel = elem.get('auto_css', '')
                xpath = elem.get('auto_xpath', '')
                if css_sel and css_sel != result.get('locator_value', ''):
                    backup.append({'strategy': 'CSS', 'value': css_sel})
                if xpath and xpath != result.get('locator_value', ''):
                    backup.append({'strategy': 'XPath', 'value': xpath})
                result['backup_locators'] = backup
                result['is_visible'] = True
                result['validation_status'] = elem.get('validation_status', '')
                result['validation_details'] = elem.get('validation_details', '')
                return result
            except json.JSONDecodeError:
                pass

        # 解析失败，回退规则引擎
        raise Exception(f'AI返回结果解析失败: {content[:200]}')

    async def _async_execute_login_step(self, page, step_data):
        """async版本 — 在页面上执行单个登录步骤"""
        import asyncio
        try:
            action = step_data.get('action_type')
            element_info = step_data.get('element')
            input_value = step_data.get('input_value', '')

            # 不需要元素定位器的操作类型
            _no_element_actions = ('navigate', 'wait', 'screenshot')

            if action in _no_element_actions:
                if action == 'navigate':
                    # navigate需要用项目的base_url拼接相对路径
                    await page.goto(input_value, wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(1)
                elif action == 'wait':
                    wait_ms = step_data.get('wait_time', 1000)
                    await asyncio.sleep(wait_ms / 1000)
                return

            if not element_info:
                return

            strategy = element_info.get('locator_strategy', 'css')
            locator_value = element_info.get('locator_value', '')

            if not locator_value:
                return

            if strategy in ['id', 'ID']:
                locator = locator_value if locator_value.startswith('#') else f'#{locator_value}'
            elif strategy in ['css', 'CSS']:
                locator = locator_value
            elif strategy in ['xpath', 'XPath']:
                locator = f'xpath={locator_value}'
            elif strategy == 'name':
                locator = f'[name="{locator_value}"]'
            else:
                locator = locator_value

            el = page.locator(locator).first
            if not await el.is_visible():
                try:
                    await el.wait_for(state='visible', timeout=5000)
                except:
                    return

            if action == 'click':
                await el.click()
                await asyncio.sleep(0.5)
            elif action == 'fill':
                await el.fill(input_value)
            elif action == 'select':
                # select操作：尝试原生select_option，失败则Ant Design/Element Plus点击模式
                try:
                    await el.select_option(label=input_value, timeout=5000)
                except Exception:
                    # 自定义下拉组件：点击触发器打开 → JS查找选项 → 点击选中
                    await el.click()
                    await asyncio.sleep(0.5)
                    try:
                        js_match = f"""
                            (() => {{
                                const dropdowns = document.querySelectorAll('.ant-select-dropdown, .el-select-dropdown');
                                for (const dd of dropdowns) {{
                                    if (dd.offsetParent !== null) {{
                                        const items = dd.querySelectorAll('.ant-select-item-option, .el-select-dropdown__item');
                                        for (const item of items) {{
                                            const text = (item.textContent || '').trim();
                                            if (text.includes({repr(input_value)})) {{
                                                item.click();
                                                return true;
                                            }}
                                        }}
                                    }}
                                }}
                                return false;
                            }})()
                        """
                        await page.evaluate(js_match)
                        await asyncio.sleep(0.3)
                    except:
                        pass
        except Exception as e:
            print(f'[登录步骤-async] 执行失败: {str(e)}')

    async def _async_inject_fab_button(self, page, session_id):
        """async版本 — 在页面中注入浮动操作按钮"""
        fab_js = """
        (sessionId) => {
            const oldFab = document.getElementById('ai-extract-fab');
            if (oldFab) oldFab.remove();

            const fab = document.createElement('div');
            fab.id = 'ai-extract-fab';
            fab.innerHTML = `
                <div style="position: fixed; bottom: 30px; right: 30px; z-index: 999999;
                     display: flex; flex-direction: column; gap: 8px; font-family: sans-serif;">
                    <button id="ai-extract-btn" style="
                        width: 120px; padding: 10px 16px; border: none; border-radius: 8px;
                        background: #409EFF; color: white; font-size: 13px; font-weight: 600;
                        cursor: pointer; box-shadow: 0 4px 12px rgba(64,158,255,0.4);
                        transition: all 0.2s;
                    " onmouseover="this.style.transform='scale(1.05)'"
                       onmouseout="this.style.transform='scale(1)'">
                        提取当前元素
                    </button>
                    <button id="ai-finish-btn" style="
                        width: 120px; padding: 10px 16px; border: none; border-radius: 8px;
                        background: #f56c6c; color: white; font-size: 13px; font-weight: 600;
                        cursor: pointer; box-shadow: 0 4px 12px rgba(245,108,108,0.4);
                        transition: all 0.2s;
                    " onmouseover="this.style.transform='scale(1.05)'"
                       onmouseout="this.style.transform='scale(1)'">
                        完成提取
                    </button>
                </div>
            `;
            document.body.appendChild(fab);
        }
        """
        try:
            await page.evaluate(fab_js, session_id)
        except:
            pass

    async def _async_validate_locators(self, page, elem, css_selector, xpath):
        """async版本 — 在浏览器页面上即时验证定位策略"""
        import re

        result = {
            'css_selector': css_selector,
            'xpath': xpath,
            'css_valid': False,
            'xpath_valid': False,
            'validation_status': 'INVALID',
            'validation_details': ''
        }

        details = []

        # 验证 CSS Selector
        css_count = 0
        try:
            css_count = await page.locator(css_selector).count()
        except Exception as e:
            details.append(f'CSS异常: {str(e)[:60]}')

        if css_count >= 1:
            result['css_valid'] = True
            if css_count == 1:
                details.append(f'CSS有效(1个匹配)')
            else:
                details.append(f'CSS有效但多个匹配({css_count}个)')
        else:
            details.append(f'CSS无效(0匹配)')
            fallback_css = await self._async_try_css_fallbacks(page, elem, css_selector)
            if fallback_css:
                result['css_selector'] = fallback_css
                result['css_valid'] = True
                details.append(f'CSS回退成功: {fallback_css}')
            else:
                details.append('CSS回退失败')

        # 验证 XPath
        xpath_count = 0
        try:
            xpath_count = await page.locator(f'xpath={xpath}').count()
        except Exception as e:
            details.append(f'XPath异常: {str(e)[:60]}')

        if xpath_count >= 1:
            result['xpath_valid'] = True
            if xpath_count == 1:
                details.append(f'XPath有效(1个匹配)')
            else:
                details.append(f'XPath有效但多个匹配({xpath_count}个)')
        else:
            details.append(f'XPath无效(0匹配)')
            fallback_xpath = await self._async_try_xpath_fallbacks(page, elem, xpath)
            if fallback_xpath:
                result['xpath'] = fallback_xpath
                result['xpath_valid'] = True
                details.append(f'XPath回退成功: {fallback_xpath}')
            else:
                details.append('XPath回退失败')

        if result['css_valid'] and result['xpath_valid']:
            result['validation_status'] = 'VALID'
        elif result['css_valid'] or result['xpath_valid']:
            result['validation_status'] = 'PARTIAL'
        result['validation_details'] = '; '.join(details)

        return result

    async def _async_try_css_fallbacks(self, page, elem, original_css):
        """async版本 — CSS回退策略"""
        import re

        # 策略1: 带tag的id选择器
        if elem.get('id'):
            tag = elem.get('tag', '')
            fallback = f'{tag}#{elem["id"]}' if tag else f'#{elem["id"]}'
            try:
                if await page.locator(fallback).count() >= 1:
                    return fallback
            except:
                pass

        # 策略2: name属性选择器
        if elem.get('name'):
            tag = elem.get('tag', 'input')
            fallback = f'{tag}[name="{elem["name"]}"]'
            try:
                if await page.locator(fallback).count() >= 1:
                    return fallback
            except:
                pass

        # 策略3: placeholder属性
        if elem.get('placeholder'):
            tag = elem.get('tag', 'input')
            fallback = f'{tag}[placeholder="{elem["placeholder"]}"]'
            try:
                if await page.locator(fallback).count() >= 1:
                    return fallback
            except:
                pass

        return None

    async def _async_try_xpath_fallbacks(self, page, elem, original_xpath):
        """async版本 — XPath回退策略"""
        import re

        # 策略1: 带text的XPath
        text = elem.get('text', '').strip()
        if text and len(text) <= 50:
            tag = elem.get('tag', '*')
            fallback = f'//{tag}[contains(text(), "{text[:30]}")]'
            try:
                if await page.locator(f'xpath={fallback}').count() >= 1:
                    return fallback
            except:
                pass

        # 策略2: 带id的XPath
        if elem.get('id'):
            tag = elem.get('tag', '*')
            fallback = f'//{tag}[@id="{elem["id"]}"]'
            try:
                if await page.locator(f'xpath={fallback}').count() >= 1:
                    return fallback
            except:
                pass

        return None

    def _playwright_extract_elements(self, url, login_start_url='', login_steps_data=None):
        """使用 Playwright 打开页面并提取 DOM 元素"""
        from playwright.sync_api import sync_playwright
        import time

        dom_elements = []
        final_url = url
        redirect_warning = ''

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()

            # 如有登录配置，先登录
            if login_start_url and login_steps_data:
                print(f'[AI提取] 开始登录流程: login_start_url={login_start_url}')
                page.goto(login_start_url, wait_until='networkidle', timeout=30000)
                time.sleep(2)
                print(f'[AI提取] 已打开登录页面: {page.url}')

                # 执行登录用例步骤
                for i, step_data in enumerate(login_steps_data):
                    print(f'[AI提取] 执行登录步骤 {i+1}/{len(login_steps_data)}: action={step_data.get("action_type")}, element={step_data.get("element")}, input_value={step_data.get("input_value", "")}')
                    self._execute_login_step(page, step_data)

                # 等待登录跳转
                try:
                    page.wait_for_load_state('networkidle', timeout=10000)
                except Exception:
                    pass
                time.sleep(2)
                print(f'[AI提取] 登录步骤执行完毕, 当前URL: {page.url}')

            # 导航到目标页面
            print(f'[AI提取] 导航到目标页面: {url}')
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(2)
            final_url = page.url
            print(f'[AI提取] 导航完成, 最终URL: {final_url}')

            # 检测是否被重定向到登录页（目标URL和最终URL差异过大时给出警告）
            redirect_warning = ''
            if login_start_url and final_url != url:
                redirect_warning = f'页面可能被重定向: 期望={url}, 实际={final_url}'
                print(f'[AI提取] ⚠ {redirect_warning}')

            # 获取页面标题
            page_title = page.title()

            # 注入 JS 脚本提取 DOM 元素（含列表行去重 + 候选弹窗触发按钮识别）
            js_script = """
            () => {
                const results = [];
                const candidateButtons = [];
                const interactiveSelectors = [
                    'input', 'button', 'a[href]', 'select', 'textarea',
                    '[role="button"]', '[role="link"]', '[role="tab"]',
                    '[role="menuitem"]', '[role="option"]', '[role="switch"]',
                    '[onclick]', '[contenteditable="true"]',
                    // Element Plus
                    '.el-button', '.el-input__inner', '.el-select',
                    '.el-checkbox', '.el-radio', '.el-switch',
                    '.el-pagination', '.el-table',
                    // Ant Design
                    '.ant-btn', '.ant-input', '.ant-select', '.ant-checkbox',
                    '.ant-radio', '.ant-switch', '.ant-pagination', '.ant-table'
                ];

                const seen = new Set();

                // ---- 列表行去重：识别表格/列表区域，行内元素只保留第一行 ----
                // 找出所有表格行
                const tableRows = [];
                const rowElementSets = []; // 每行的元素集合
                document.querySelectorAll('table tbody tr, .ant-table-tbody tr, .el-table__body tr').forEach(tr => {
                    const cells = Array.from(tr.querySelectorAll('td'));
                    if (cells.length > 0) tableRows.push({ tr, cells });
                });

                // 记录非首行中重复的按钮/链接（相同文本+相同class视为重复）
                const firstRowButtonKeys = new Set();
                const duplicateRowElementKeys = new Set();

                if (tableRows.length > 1) {
                    // 收集第一行中所有按钮/链接的签名
                    const firstRow = tableRows[0];
                    firstRow.tr.querySelectorAll('button, a, [role="button"], .ant-btn, .el-button').forEach(btn => {
                        const key = (btn.textContent || '').trim().substring(0, 30) + '|' +
                                    (btn.className || '').toString().substring(0, 100) + '|' +
                                    btn.tagName;
                        firstRowButtonKeys.add(key);
                    });
                    // 非首行中与第一行签名相同的元素标记为重复
                    for (let r = 1; r < tableRows.length; r++) {
                        tableRows[r].tr.querySelectorAll('button, a, [role="button"], .ant-btn, .el-button').forEach(btn => {
                            const key = (btn.textContent || '').trim().substring(0, 30) + '|' +
                                        (btn.className || '').toString().substring(0, 100) + '|' +
                                        btn.tagName;
                            if (firstRowButtonKeys.has(key)) {
                                duplicateRowElementKeys.add(btn);
                            }
                        });
                    }
                }

                // ---- 候选弹窗触发按钮关键词 ----
                const dialogKeywords = ['新增', '添加', '创建', '新建', '编辑', '修改', '查看', '详情',
                    '导入', '导出', '设置', '配置', '分配', '授权', '审核', '审批',
                    '新增用户', '新增角色', '新增岗位', '新增部门'];
                const dangerKeywords = ['删除', '移除', '清空', '注销', '退出', '提交', '保存', '确认', '禁用', '启用'];

                interactiveSelectors.forEach(selector => {
                    try {
                        document.querySelectorAll(selector).forEach(el => {
                            // 跳过不可见元素
                            const rect = el.getBoundingClientRect();
                            if (rect.width === 0 && rect.height === 0) return;
                            const style = window.getComputedStyle(el);
                            if (style.display === 'none' || style.visibility === 'hidden') return;

                            // 排除导航菜单区域元素（侧边栏、顶部导航、面包屑、标签页）
                            // 对所有标签生效，不限于<a>
                            {
                                const navPatterns = /menu|nav|sidebar|breadcrumb|sider|aside|tabbar|page-header/i;
                                // 精确匹配导航容器类名（避免模糊匹配误伤主内容区）
                                const navContainerSelectors = '.ant-menu, .el-menu, .ant-layout-sider, .el-aside, aside, nav, .breadcrumb, [class*="breadcrumb"], [class*="tabbar"]';
                                const parentNav = el.closest(navContainerSelectors);
                                if (parentNav) {
                                    // 排除表格内的元素（如下拉菜单在表格内时不排除）
                                    if (!el.closest('tr, .ant-table-tbody, .el-table__body')) return;
                                }
                                // <a>标签按原有逻辑过滤
                                if (el.tagName === 'A') {
                                    const elClassName = (typeof el.className === 'string') ? el.className : '';
                                    const parentClassName = (el.parentElement && typeof el.parentElement.className === 'string') ? el.parentElement.className : '';
                                    const grandParent = el.parentElement ? el.parentElement.parentElement : null;
                                    const grandParentClassName = (grandParent && typeof grandParent.className === 'string') ? grandParent.className : '';
                                    if (navPatterns.test(elClassName) || navPatterns.test(parentClassName) || navPatterns.test(grandParentClassName)) return;
                                }
                            }

                            // 列表行去重：跳过非首行的重复按钮
                            if (duplicateRowElementKeys.has(el)) return;

                            // 去重
                            const key = el.tagName + '|' + (el.id||'') + '|' + el.className + '|' + rect.x + '|' + rect.y;
                            if (seen.has(key)) return;
                            seen.add(key);

                            // 判断是否在表格行内
                            const tr = el.closest('tr');
                            const isInTableRow = tr !== null && tableRows.length > 0;
                            const rowIndex = isInTableRow ? tableRows.findIndex(r => r.tr === tr) : -1;

                            results.push({
                                tag: el.tagName.toLowerCase(),
                                id: el.id || '',
                                name: el.getAttribute('name') || '',
                                className: (typeof el.className === 'string') ? el.className.substring(0, 200) : '',
                                type: el.type || '',
                                placeholder: el.placeholder || '',
                                value: (el.value || '').substring(0, 50),
                                href: el.href || '',
                                role: el.getAttribute('role') || '',
                                ariaLabel: el.getAttribute('aria-label') || '',
                                dataTestId: el.getAttribute('data-testid') || '',
                                text: (el.textContent || '').trim().substring(0, 80),
                                title: el.title || '',
                                visible: true,
                                rect: { x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height) },
                                isInTableRow: isInTableRow,
                                tableRowIndex: rowIndex
                            });
                        });
                    } catch(e) {}
                });

                // ---- 识别候选弹窗触发按钮 ----
                // 收集页面级按钮（不在表格行内的）
                // 排除导航菜单链接（侧边栏菜单、顶部导航等），只收集真正的操作按钮
                const navKeywords = ['menu', 'nav', 'sidebar', 'breadcrumb', 'tab'];
                const btnElements = results.filter(e => {
                    // 必须是按钮类元素
                    const isButton = e.tag === 'button' || e.role === 'button' ||
                        e.className.includes('ant-btn') || e.className.includes('el-button');
                    const isLink = e.tag === 'a' && e.href && !e.href.startsWith('javascript');
                    if (!isButton && !isLink) return false;
                    // 排除导航菜单类元素
                    const cls = (e.className || '').toLowerCase();
                    if (navKeywords.some(kw => cls.includes(kw))) return false;
                    // <a>标签只保留不含导航class的
                    if (isLink && !isButton) return false;
                    return true;
                });

                // 页面级按钮候选
                btnElements.filter(e => !e.isInTableRow).forEach((btn, idx) => {
                    const text = btn.text.trim();
                    const isDanger = dangerKeywords.some(kw => text.includes(kw));
                    const isCandidate = !isDanger && (
                        dialogKeywords.some(kw => text.includes(kw)) ||
                        btn.className.includes('ant-btn-primary') ||
                        btn.className.includes('el-button--primary')
                    );
                    if (isCandidate) {
                        candidateButtons.push({
                            index: candidateButtons.length,
                            text: text,
                            tag: btn.tag,
                            className: btn.className,
                            id: btn.id,
                            source: '页面级按钮',
                            reason: dialogKeywords.some(kw => text.includes(kw)) ?
                                `文本"${text}"包含弹窗触发关键词` : '主要操作按钮（primary样式）'
                        });
                    }
                });

                // 表格行操作按钮候选（只用第一行的）
                if (tableRows.length > 0) {
                    const firstRow = tableRows[0];
                    firstRow.tr.querySelectorAll('button, a, [role="button"], .ant-btn, .el-button').forEach(el => {
                        const text = (el.textContent || '').trim();
                        if (!text) return;
                        const isDanger = dangerKeywords.some(kw => text.includes(kw));
                        const isCandidate = !isDanger && (
                            dialogKeywords.some(kw => text.includes(kw)) ||
                            el.className.includes('ant-btn-link') ||
                            el.className.includes('el-button--text')
                        );
                        if (isCandidate) {
                            // 找到这个元素在results中的索引，获取其定位信息
                            const rect = el.getBoundingClientRect();
                            candidateButtons.push({
                                index: candidateButtons.length,
                                text: text,
                                tag: el.tagName.toLowerCase(),
                                className: (typeof el.className === 'string') ? el.className.substring(0, 200) : '',
                                id: el.id || '',
                                source: '表格行操作',
                                reason: dialogKeywords.some(kw => text.includes(kw)) ?
                                    `表格行操作"${text}"可能触发弹窗` : '表格行链接按钮'
                            });
                        }
                    });
                }

                return {
                    elements: results.slice(0, 80),
                    candidateButtons: candidateButtons.slice(0, 20),
                    tableRowCount: tableRows.length
                };
            }
            """

            extract_result = page.evaluate(js_script)
            raw_elements = extract_result.get('elements', [])
            candidate_buttons_raw = extract_result.get('candidateButtons', [])
            table_row_count = extract_result.get('tableRowCount', 0)

            # 为候选按钮计算定位器（在浏览器仍打开时）
            candidate_buttons = []
            for cb in candidate_buttons_raw:
                try:
                    css_sel = self._compute_css_selector(cb)
                    xpath_sel = self._compute_xpath(cb)
                    # 验证定位器
                    try:
                        css_count = page.locator(css_sel).count() if css_sel else 0
                    except:
                        css_count = 0
                    cb['css_selector'] = css_sel if css_count > 0 else ''
                    cb['xpath'] = xpath_sel
                    cb['locator_valid'] = css_count == 1
                except Exception as e:
                    cb['css_selector'] = ''
                    cb['xpath'] = ''
                    cb['locator_valid'] = False
                candidate_buttons.append(cb)

            if table_row_count > 0:
                print(f'[AI提取] 检测到表格 {table_row_count} 行，已去重行内重复按钮')
            if candidate_buttons:
                print(f'[AI提取] 识别到 {len(candidate_buttons)} 个候选弹窗触发按钮: {[cb["text"] for cb in candidate_buttons]}')

            # 为每个元素计算 CSS Selector 和 XPath，并进行即时验证
            validation_stats = {'valid': 0, 'partial': 0, 'invalid': 0}
            for i, elem in enumerate(raw_elements):
                elem['page_title'] = page_title
                # 计算 CSS Selector
                css_selector = self._compute_css_selector(elem)
                xpath = self._compute_xpath(elem)
                
                # 即时验证：在浏览器仍然打开时，验证定位策略是否有效
                validation = self._validate_locators(page, elem, css_selector, xpath)
                
                # 使用验证后的（可能被回退替换的）选择器
                elem['auto_css'] = validation['css_selector']
                elem['auto_xpath'] = validation['xpath']
                elem['validation_status'] = validation['validation_status']
                elem['validation_details'] = validation['validation_details']
                
                # 统计验证结果
                status = validation['validation_status']
                if status == 'VALID':
                    validation_stats['valid'] += 1
                elif status == 'PARTIAL':
                    validation_stats['partial'] += 1
                else:
                    validation_stats['invalid'] += 1
                
                dom_elements.append(elem)
            
            print(f'[AI提取] 定位策略验证结果: 有效={validation_stats["valid"]}, 部分有效={validation_stats["partial"]}, 无效={validation_stats["invalid"]}')

            browser.close()

        return {
            'elements': dom_elements,
            'final_url': final_url,
            'redirect_warning': redirect_warning,
            'candidate_buttons': candidate_buttons,
            'table_row_count': table_row_count
        }

    def _execute_login_step(self, page, step_data):
        """在页面上执行单个登录步骤"""
        import time
        try:
            action = step_data.get('action_type')
            element_info = step_data.get('element')
            input_value = step_data.get('input_value', '')

            # 不需要元素定位器的操作类型
            _no_element_actions = ('navigate', 'wait', 'screenshot')

            if action in _no_element_actions:
                if action == 'navigate':
                    page.goto(input_value, wait_until='networkidle', timeout=30000)
                    time.sleep(1)
                elif action == 'wait':
                    wait_ms = step_data.get('wait_time', 1000)
                    time.sleep(wait_ms / 1000)
                return

            if not element_info:
                print(f'[登录步骤] 跳过: 无元素信息, action={action}')
                return

            strategy = element_info.get('locator_strategy', 'css')
            locator_value = element_info.get('locator_value', '')

            if not locator_value:
                print(f'[登录步骤] 跳过: 定位值为空, action={action}')
                return

            # 定位元素
            if strategy in ['id', 'ID']:
                locator = locator_value if locator_value.startswith('#') else f'#{locator_value}'
            elif strategy in ['css', 'CSS']:
                locator = locator_value
            elif strategy in ['xpath', 'XPath']:
                locator = f'xpath={locator_value}'
            elif strategy == 'name':
                locator = f'[name="{locator_value}"]'
            else:
                locator = locator_value

            el = page.locator(locator).first
            if not el.is_visible():
                print(f'[登录步骤] ⚠ 元素不可见, locator={locator}, action={action}')
                # 尝试等待元素出现
                try:
                    el.wait_for(state='visible', timeout=5000)
                except Exception:
                    print(f'[登录步骤] 元素等待超时仍未可见, 跳过此步骤')
                    return

            if action == 'click':
                el.click()
                time.sleep(0.5)
                print(f'[登录步骤] ✅ click 成功, locator={locator}')
            elif action == 'fill':
                el.fill(input_value)
                print(f'[登录步骤] ✅ fill 成功, locator={locator}, value={input_value}')
            elif action == 'select':
                try:
                    el.select_option(label=input_value, timeout=5000)
                    print(f'[登录步骤] ✅ select 成功, locator={locator}, value={input_value}')
                except Exception:
                    el.click()
                    time.sleep(0.5)
                    try:
                        js_match = f"""
                            (() => {{
                                const dropdowns = document.querySelectorAll('.ant-select-dropdown, .el-select-dropdown');
                                for (const dd of dropdowns) {{
                                    if (dd.offsetParent !== null) {{
                                        const items = dd.querySelectorAll('.ant-select-item-option, .el-select-dropdown__item');
                                        for (const item of items) {{
                                            const text = (item.textContent || '').trim();
                                            if (text.includes({repr(input_value)})) {{
                                                item.click();
                                                return true;
                                            }}
                                        }}
                                    }}
                                }}
                                return false;
                            }})()
                        """
                        page.evaluate(js_match)
                        time.sleep(0.3)
                        print(f'[登录步骤] ✅ select(自定义下拉) 成功, locator={locator}, value={input_value}')
                    except:
                        print(f'[登录步骤] ⚠ select自定义下拉失败, locator={locator}, value={input_value}')
            else:
                print(f'[登录步骤] 未知action类型: {action}')
        except Exception as e:
            print(f'[登录步骤] ❌ 执行失败: action={step_data.get("action_type")}, locator={locator_value}, 错误={str(e)}')

    def _revalidate_locators(self, url, login_start_url, login_steps_data, ai_elements):
        """重新打开页面，验证LLM生成的locator_value是否有效
        
        LLM可能会修改定位值（如去掉空格、改写选择器），这些值未经浏览器验证。
        此方法重新打开页面进行验证，对于无效的定位值尝试回退替换。
        """
        from playwright.sync_api import sync_playwright
        import time
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={'width': 1920, 'height': 1080})
                page = context.new_page()
                
                # 如有登录配置，先登录
                if login_start_url and login_steps_data:
                    page.goto(login_start_url, wait_until='networkidle', timeout=30000)
                    time.sleep(2)
                    for step_data in login_steps_data:
                        self._execute_login_step(page, step_data)
                    time.sleep(2)
                
                # 导航到目标页面
                page.goto(url, wait_until='networkidle', timeout=30000)
                time.sleep(2)
                
                # 逐个验证未验证的元素
                validated_count = 0
                replaced_count = 0
                for ai_elem in ai_elements:
                    locator_strategy = ai_elem.get('locator_strategy', '')
                    locator_value = ai_elem.get('locator_value', '')
                    
                    if not locator_value:
                        ai_elem['validation_status'] = 'INVALID'
                        ai_elem['validation_details'] = '定位值为空'
                        continue
                    
                    # 根据策略类型构造Playwright locator
                    locator = None
                    try:
                        if locator_strategy in ('CSS', 'css', 'name', 'class', 'placeholder', 'role', 'label', 'title', 'test-id'):
                            locator = page.locator(locator_value)
                        elif locator_strategy in ('XPath', 'xpath'):
                            locator = page.locator(f'xpath={locator_value}')
                        elif locator_strategy == 'ID':
                            locator = page.locator(locator_value)
                        else:
                            # 未知策略，尝试作为CSS
                            locator = page.locator(locator_value)
                    except Exception as e:
                        ai_elem['validation_status'] = 'INVALID'
                        ai_elem['validation_details'] = f'定位表达式异常: {str(e)[:60]}'
                        validated_count += 1
                        continue
                    
                    # 验证匹配数
                    try:
                        count = locator.count()
                    except Exception as e:
                        ai_elem['validation_status'] = 'INVALID'
                        ai_elem['validation_details'] = f'验证异常: {str(e)[:60]}'
                        validated_count += 1
                        continue
                    
                    if count == 1:
                        # 精确匹配1个，标记为VALID
                        ai_elem['validation_status'] = 'VALID'
                        ai_elem['validation_details'] = f'二次验证有效(1个匹配)'
                        validated_count += 1
                    elif count > 1:
                        # 匹配多个，不精确，尝试用backup_locators替换为更精确的定位
                        replaced = False
                        for bl in ai_elem.get('backup_locators', []):
                            bl_strategy = bl.get('strategy', '')
                            bl_value = bl.get('value', '')
                            if not bl_value:
                                continue
                            try:
                                if bl_strategy in ('XPath', 'xpath'):
                                    bl_count = page.locator(f'xpath={bl_value}').count()
                                else:
                                    bl_count = page.locator(bl_value).count()
                                if bl_count == 1:
                                    # 用精确匹配1个的backup替换
                                    ai_elem['locator_strategy'] = bl_strategy
                                    ai_elem['locator_value'] = bl_value
                                    ai_elem['validation_status'] = 'VALID'
                                    ai_elem['validation_details'] = f'原定位匹配{count}个不精确，替换为精确backup({bl_strategy}): {bl_value}'
                                    replaced = True
                                    replaced_count += 1
                                    validated_count += 1
                                    break
                            except Exception:
                                continue
                        if not replaced:
                            # backup也没有精确匹配的，尝试Ant Design按钮子span模式
                            # 如 <button><span>新增</span></button>，用 //button[.//span[contains(text(),"新增")]]
                            # 注意：Ant Design的letter-spacing会在文本中插入空格（"查 询"、"重 置"），
                            # 需要同时尝试带空格和不带空格的版本
                            elem_name = ai_elem.get('name', '')
                            elem_texts = []
                            if elem_name:
                                elem_texts.append(elem_name)  # 带空格的原始文本（如"查 询"）
                                compact = elem_name.replace(' ', '')
                                if compact != elem_name:
                                    elem_texts.append(compact)  # 去掉空格（如"查询"）
                            if not elem_texts:
                                desc = ai_elem.get('description', '')
                                if desc:
                                    elem_texts.append(desc)
                                    compact = desc.replace(' ', '')
                                    if compact != desc:
                                        elem_texts.append(compact)
                            for elem_text in elem_texts:
                                if not elem_text:
                                    continue
                                # 尝试多种Ant Design按钮XPath模式
                                ant_xpaths = [
                                    f'//button[.//span[text()="{elem_text}"]]',
                                    f'//button[.//span[contains(text(),"{elem_text}")]]',
                                ]
                                for ant_xpath in ant_xpaths:
                                    try:
                                        ant_count = page.locator(f'xpath={ant_xpath}').count()
                                        if ant_count == 1:
                                            ai_elem['locator_strategy'] = 'XPath'
                                            ai_elem['locator_value'] = ant_xpath
                                            ai_elem['validation_status'] = 'VALID'
                                            ai_elem['validation_details'] = f'原定位匹配{count}个不精确，Ant Design按钮XPath精确匹配(1个): {ant_xpath}'
                                            replaced = True
                                            replaced_count += 1
                                            validated_count += 1
                                            break
                                    except Exception:
                                        pass
                                if replaced:
                                    break
                            if not replaced:
                                ai_elem['validation_status'] = 'PARTIAL'
                                ai_elem['validation_details'] = f'二次验证匹配{count}个(不精确)，backup也无精确匹配'
                                validated_count += 1
                    else:
                        # 定位无效，尝试用backup_locators替换
                        replaced = False
                        for bl in ai_elem.get('backup_locators', []):
                            bl_strategy = bl.get('strategy', '')
                            bl_value = bl.get('value', '')
                            if not bl_value:
                                continue
                            try:
                                if bl_strategy in ('XPath', 'xpath'):
                                    bl_count = page.locator(f'xpath={bl_value}').count()
                                else:
                                    bl_count = page.locator(bl_value).count()
                                if bl_count >= 1:
                                    # 用有效的backup替换主定位
                                    ai_elem['locator_strategy'] = bl_strategy
                                    ai_elem['locator_value'] = bl_value
                                    ai_elem['validation_status'] = 'VALID'
                                    ai_elem['validation_details'] = f'原定位无效，已替换为backup({bl_strategy}): {bl_value}'
                                    replaced = True
                                    replaced_count += 1
                                    validated_count += 1
                                    break
                            except Exception:
                                continue
                        
                        if not replaced:
                            # 最后兜底：尝试 Ant Design 按钮子span模式
                            # 如 <button><span>新增</span></button>，用 //button[.//span[contains(text(),"新增")]]
                            # 注意：Ant Design的letter-spacing会在文本中插入空格（"查 询"、"重 置"），
                            # 需要同时尝试带空格和不带空格的版本
                            elem_name = ai_elem.get('name', '')
                            elem_texts = []
                            if elem_name:
                                elem_texts.append(elem_name)
                                compact = elem_name.replace(' ', '')
                                if compact != elem_name:
                                    elem_texts.append(compact)
                            if not elem_texts:
                                desc = ai_elem.get('description', '')
                                if desc:
                                    elem_texts.append(desc)
                                    compact = desc.replace(' ', '')
                                    if compact != desc:
                                        elem_texts.append(compact)
                            for elem_text in elem_texts:
                                if not elem_text:
                                    continue
                                ant_xpaths = [
                                    f'//button[.//span[text()="{elem_text}"]]',
                                    f'//button[.//span[contains(text(),"{elem_text}")]]',
                                ]
                                for ant_xpath in ant_xpaths:
                                    try:
                                        ant_count = page.locator(f'xpath={ant_xpath}').count()
                                        if ant_count >= 1:
                                            ai_elem['locator_strategy'] = 'XPath'
                                            ai_elem['locator_value'] = ant_xpath
                                            v_st = 'VALID' if ant_count == 1 else 'PARTIAL'
                                            ai_elem['validation_status'] = v_st
                                            ai_elem['validation_details'] = f'原定位无效，Ant Design按钮XPath回退({ant_count}个匹配): {ant_xpath}'
                                            replaced = True
                                            replaced_count += 1
                                            validated_count += 1
                                            break
                                    except Exception:
                                        pass
                                if replaced:
                                    break
                            
                            if not replaced:
                                ai_elem['validation_status'] = 'INVALID'
                                ai_elem['validation_details'] = f'二次验证无效(0匹配)，backup也无有效定位'
                                validated_count += 1
                
                browser.close()
                print(f'[AI提取] 二次验证完成: 验证{validated_count}个, 替换{replaced_count}个')
        
        except Exception as e:
            # 二次验证失败不应阻断整个流程，标记为UNVALIDATED
            print(f'[AI提取] 二次验证失败(不阻断): {str(e)[:100]}')
            for ai_elem in ai_elements:
                if not ai_elem.get('validation_status'):
                    ai_elem['validation_status'] = 'UNVALIDATED'
                    ai_elem['validation_details'] = '二次验证未执行'

    def _validate_locators(self, page, elem, css_selector, xpath):
        """在浏览器页面上即时验证定位策略是否有效，失败时尝试回退策略
        
        Args:
            page: Playwright page 对象（仍存活）
            elem: 元素字典（包含 tag, name, id, className, text, placeholder 等）
            css_selector: 计算出的 CSS 选择器
            xpath: 计算出的 XPath
        
        Returns:
            dict: {
                'css_selector': 最终CSS选择器（可能被替换）,
                'xpath': 最终XPath（可能被替换）,
                'css_valid': bool,
                'xpath_valid': bool,
                'validation_status': 'VALID'|'PARTIAL'|'INVALID',
                'validation_details': 验证详情字符串
            }
        """
        import re
        
        result = {
            'css_selector': css_selector,
            'xpath': xpath,
            'css_valid': False,
            'xpath_valid': False,
            'validation_status': 'INVALID',
            'validation_details': ''
        }
        
        details = []
        
        # === 1. 验证 CSS Selector ===
        css_count = 0
        try:
            css_count = page.locator(css_selector).count()
        except Exception as e:
            details.append(f'CSS异常: {str(e)[:60]}')
        
        if css_count >= 1:
            result['css_valid'] = True
            if css_count == 1:
                details.append(f'CSS有效(1个匹配)')
            else:
                details.append(f'CSS有效但多个匹配({css_count}个)')
        else:
            details.append(f'CSS无效(0匹配)')
            # 尝试 CSS 回退策略
            fallback_css = self._try_css_fallbacks(page, elem, css_selector)
            if fallback_css:
                result['css_selector'] = fallback_css
                result['css_valid'] = True
                details.append(f'CSS回退成功: {fallback_css}')
            else:
                details.append('CSS回退失败')
        
        # === 2. 验证 XPath ===
        xpath_count = 0
        try:
            xpath_count = page.locator(f'xpath={xpath}').count()
        except Exception as e:
            details.append(f'XPath异常: {str(e)[:60]}')
        
        if xpath_count >= 1:
            result['xpath_valid'] = True
            if xpath_count == 1:
                details.append(f'XPath有效(1个匹配)')
            else:
                details.append(f'XPath有效但多个匹配({xpath_count}个)')
        else:
            details.append(f'XPath无效(0匹配)')
            # 尝试 XPath 回退策略
            fallback_xpath = self._try_xpath_fallbacks(page, elem, xpath)
            if fallback_xpath:
                result['xpath'] = fallback_xpath
                result['xpath_valid'] = True
                details.append(f'XPath回退成功: {fallback_xpath}')
            else:
                details.append('XPath回退失败')
        
        # === 3. 综合判定 ===
        # VALID: CSS和XPath都精确匹配(仅1个)
        # PARTIAL: 匹配到元素但不精确(多个匹配)，或仅CSS/XPath之一有效
        # INVALID: CSS和XPath都无效
        css_precise = result['css_valid'] and css_count == 1
        xpath_precise = result['xpath_valid'] and xpath_count == 1
        
        if css_precise and xpath_precise:
            result['validation_status'] = 'VALID'
        elif result['css_valid'] or result['xpath_valid']:
            result['validation_status'] = 'PARTIAL'
        else:
            result['validation_status'] = 'INVALID'
        
        result['validation_details'] = '; '.join(details)
        return result

    def _try_css_fallbacks(self, page, elem, original_css):
        """CSS选择器验证失败时，尝试回退策略生成有效的选择器
        
        策略优先级：
        1. 跳过含空格的name属性，改用其他属性
        2. 使用 tag + aria-label
        3. 使用 tag + className组合
        4. 使用 tag + placeholder
        5. 使用 tag + title
        6. 使用 tag + text（通过CSS无法直接实现，跳过）
        """
        tag = elem.get('tag', '')
        name = elem.get('name', '')
        aria_label = elem.get('ariaLabel', '')
        class_name = elem.get('className', '')
        placeholder = elem.get('placeholder', '')
        title_attr = elem.get('title', '')
        elem_id = elem.get('id', '')
        data_testid = elem.get('dataTestId', '')
        
        candidates = []
        
        # 如果原始选择器基于 name 且含空格（如 [name="查 询"]），跳过name，用其他属性
        if name and ' ' in name:
            # name含空格不可靠，跳过name，尝试其他属性
            if elem_id:
                candidates.append(f'#{elem_id}')
            if data_testid:
                candidates.append(f'[data-testid="{data_testid}"]')
            if aria_label:
                base = f'{tag}[aria-label="{aria_label}"]' if tag else f'[aria-label="{aria_label}"]'
                candidates.append(base)
            if placeholder:
                base = f'{tag}[placeholder="{placeholder}"]' if tag else f'[placeholder="{placeholder}"]'
                candidates.append(base)
            if title_attr:
                base = f'{tag}[title="{title_attr}"]' if tag else f'[title="{title_attr}"]'
                candidates.append(base)
            # className组合
            if class_name:
                classes = [c for c in class_name.split() if c and not c.startswith('__') and not c.startswith('v-')]
                if len(classes) >= 1 and tag:
                    candidates.append(f'{tag}.{classes[0]}')
                if len(classes) >= 2 and tag:
                    candidates.append(f'{tag}.{classes[0]}.{classes[1]}')
        
        # 如果原始选择器不是基于name含空格的，仍尝试其他回退
        if not candidates:
            if aria_label and tag:
                candidates.append(f'{tag}[aria-label="{aria_label}"]')
            if class_name and tag:
                classes = [c for c in class_name.split() if c and not c.startswith('__') and not c.startswith('v-')]
                if len(classes) >= 1:
                    candidates.append(f'{tag}.{classes[0]}')
                if len(classes) >= 2:
                    candidates.append(f'{tag}.{classes[0]}.{classes[1]}')
            if placeholder and tag:
                candidates.append(f'{tag}[placeholder="{placeholder}"]')
        
        # 逐个验证候选选择器
        for candidate in candidates:
            if candidate == original_css:
                continue  # 跳过和原始相同的
            try:
                count = page.locator(candidate).count()
                if count >= 1:
                    return candidate
            except Exception:
                continue
        
        return None

    def _try_xpath_fallbacks(self, page, elem, original_xpath):
        """XPath验证失败时，尝试回退策略生成有效的XPath
        
        策略优先级：
        1. 使用 tag + text contains（短文本）
        2. 使用 tag + 含空格name的text回退
        3. 使用 tag + aria-label
        4. 使用 tag + placeholder
        5. 使用 tag + className
        """
        tag = elem.get('tag', '*')
        name = elem.get('name', '')
        text = elem.get('text', '').strip()
        aria_label = elem.get('ariaLabel', '')
        placeholder = elem.get('placeholder', '')
        class_name = elem.get('className', '')
        elem_id = elem.get('id', '')
        
        candidates = []
        
        # text-based XPath（最可靠，尤其是按钮）
        if text and len(text) <= 50:
            escaped_text = text.replace('"', "'")
            candidates.append(f'//{tag}[contains(text(),"{escaped_text}")]')
            # 也试试 normalize-space 处理空格
            if ' ' in text:
                candidates.append(f'//{tag}[contains(normalize-space(text()),"{escaped_text}")]')
            # Ant Design按钮模式：文本在子<span>中，如 <button><span>新增</span></button>
            # 使用 .//span[contains(text(),"新增")] 可以匹配到子元素中的文本
            if tag in ('button', 'a', 'div', 'span'):
                compact = text.replace(' ', '')
                if compact:
                    candidates.append(f'//{tag}[.//span[contains(text(),"{compact}")]]')
                    if compact != escaped_text:
                        candidates.append(f'//{tag}[.//span[text()="{compact}"]]')
        
        # name含空格时，用text代替
        if name and ' ' in name and text:
            escaped_text = text.replace('"', "'")
            candidates.append(f'//{tag}[contains(text(),"{escaped_text}")]')
        
        # aria-label
        if aria_label:
            candidates.append(f'//{tag}[@aria-label="{aria_label}"]')
        
        # placeholder
        if placeholder:
            candidates.append(f'//{tag}[@placeholder="{placeholder}"]')
        
        # id
        if elem_id:
            candidates.append(f'//*[@id="{elem_id}"]')
        
        # className-based XPath
        if class_name and tag != '*':
            classes = [c for c in class_name.split() if c and not c.startswith('__') and not c.startswith('v-')]
            if len(classes) >= 1:
                candidates.append(f'//{tag}[contains(@class,"{classes[0]}")]')
        
        # 逐个验证候选XPath
        for candidate in candidates:
            if candidate == original_xpath:
                continue
            try:
                count = page.locator(f'xpath={candidate}').count()
                if count >= 1:
                    return candidate
            except Exception:
                continue
        
        return None

    def _compute_css_selector(self, elem):
        """根据原始 DOM 信息计算最优 CSS Selector"""
        # 优先级：id > data-testid > name(无空格) > placeholder > class组合 > tag+text
        if elem.get('id'):
            return f'#{elem["id"]}'
        if elem.get('dataTestId'):
            return f'[data-testid="{elem["dataTestId"]}"]'
        # name属性：如果值含空格（Ant Design的letter-spacing导致的"查 询"、"新 增"等），
        # CSS选择器[name="查 询"]虽然语法合法但极易失效，跳过name改用其他策略
        name_val = elem.get('name', '')
        if name_val and ' ' not in name_val:
            return f'[name="{name_val}"]'
        if elem.get('type') and elem.get('tag') == 'input':
            type_val = elem['type']
            if elem.get('placeholder'):
                return f'input[type="{type_val}"][placeholder="{elem["placeholder"]}"]'
            return f'input[type="{type_val}"]'
        if elem.get('placeholder'):
            return f'[placeholder="{elem["placeholder"]}"]'
        if elem.get('role'):
            return f'[role="{elem["role"]}"]'
        if elem.get('ariaLabel'):
            return f'[aria-label="{elem["ariaLabel"]}"]'
        # 用 tag + class（取第一个有意义的 class）
        tag = elem.get('tag', 'div')
        if elem.get('className'):
            first_class = elem['className'].split()[0]
            if first_class and not first_class.startswith('__'):
                return f'{tag}.{first_class}'
        return tag

    def _compute_xpath(self, elem):
        """根据原始 DOM 信息计算 XPath"""
        if elem.get('id'):
            return f'//*[@id="{elem["id"]}"]'
        # name含空格时不可靠，跳过name改用text
        name_val = elem.get('name', '')
        if name_val and ' ' not in name_val:
            return f'//*[@name="{name_val}"]'
        tag = elem.get('tag', '*')
        text = elem.get('text', '')
        # name含空格时，优先用text（去掉空格后的文本更准确）
        if name_val and ' ' in name_val:
            compact_text = name_val.replace(' ', '')
            if compact_text:
                return f'//{tag}[contains(text(),"{compact_text}")]'
        if text and len(text) < 30:
            return f'//{tag}[contains(text(),"{text}")]'
        if elem.get('placeholder'):
            return f'//{tag}[@placeholder="{elem["placeholder"]}"]'
        return f'//{tag}'

    def _enhance_css_selector(self, elem):
        """当基础CSS选择器不唯一时，尝试生成更精确的选择器"""
        tag = elem.get('tag', '')
        text = elem.get('text', '').strip()
        class_name = elem.get('className', '')
        placeholder = elem.get('placeholder', '')
        aria_label = elem.get('ariaLabel', '')
        elem_type = elem.get('type', '')
        name = elem.get('name', '')
        title_attr = elem.get('title', '')
        elem_id = elem.get('id', '')

        # 1. id 一定唯一
        if elem_id:
            return 'CSS', f'#{elem_id}'

        # 2. name 属性（跳过含空格的name，不可靠）
        if name and ' ' not in name:
            return 'CSS', f'[name="{name}"]'

        # 3. aria-label
        if aria_label:
            base = f'{tag}[aria-label="{aria_label}"]' if tag else f'[aria-label="{aria_label}"]'
            return 'CSS', base

        # 4. placeholder
        if placeholder:
            if tag == 'input' and elem_type:
                return 'CSS', f'input[type="{elem_type}"][placeholder="{placeholder}"]'
            return 'CSS', f'[placeholder="{placeholder}"]'

        # 5. title 属性
        if title_attr:
            base = f'{tag}[title="{title_attr}"]' if tag else f'[title="{title_attr}"]'
            return 'CSS', base

        # 6. 有短文本的按钮/链接 → 用 tag + class + text 的 XPath
        if text and len(text) <= 30 and tag in ('button', 'a', 'span', 'label', 'div'):
            # 按钮等元素用 XPath text() 更可靠
            escaped_text = text.replace('"', "'")
            return 'XPath', f'//{tag}[contains(text(),"{escaped_text}")]'

        # 7. 多class组合：取前2个有意义的class
        if class_name:
            classes = [c for c in class_name.split() if c and not c.startswith('__') and not c.startswith('v-')]
            if len(classes) >= 2:
                combined = '.'.join(classes[:2])
                return 'CSS', f'{tag}.{combined}'

        # 8. type 属性
        if elem_type and tag == 'input':
            return 'CSS', f'input[type="{elem_type}"]'

        return None, None

    def _deduplicate_by_name(self, elements):
        """按元素名称去重，同一来源下同名元素只保留第一条。
        
        用于过滤列表中每行重复的操作按钮（如编辑、删除等）。
        不同来源（如不同弹窗）的同名元素不受影响。
        """
        seen_names = set()
        deduped = []
        removed_count = 0
        for elem in elements:
            name = (elem.get('name', '') or '').strip()
            source = (elem.get('source', '') or '').strip()
            dedup_key = (name, source)
            if name and dedup_key in seen_names:
                removed_count += 1
                continue
            if name:
                seen_names.add(dedup_key)
            deduped.append(elem)
        if removed_count > 0:
            print(f'[AI提取] 按名称去重: 移除了{removed_count}个同名重复元素')
        return deduped

    def _deduplicate_locators(self, elements):
        """检测并修复重复的定位值，确保每个元素的定位尽量唯一"""
        # 按 (locator_strategy, locator_value) 分组找重复
        from collections import defaultdict
        locator_groups = defaultdict(list)
        for i, elem in enumerate(elements):
            key = (elem.get('locator_strategy', ''), elem.get('locator_value', ''))
            locator_groups[key].append(i)

        # 找出有重复的组
        duplicates = {k: indices for k, indices in locator_groups.items() if len(indices) > 1}

        if not duplicates:
            return elements

        print(f'[AI提取] 发现 {len(duplicates)} 组重复定位值，正在去重...')

        for (strategy, value), indices in duplicates.items():
            print(f'[AI提取] 重复组: strategy={strategy}, value={value}, 共{len(indices)}个元素')

            enhanced_count = 0
            still_duplicate = []

            # 第一轮：尝试用 _enhance_css_selector 增强
            new_values = {}
            for idx in indices:
                elem = elements[idx]
                new_strategy, new_value = self._enhance_css_selector(elem)
                if new_strategy and new_value and (new_strategy, new_value) != (strategy, value):
                    new_values[idx] = (new_strategy, new_value)

            # 检查增强后的值之间是否还有重复
            enhanced_groups = defaultdict(list)
            for idx, (ns, nv) in new_values.items():
                enhanced_groups[(ns, nv)].append(idx)

            for idx in indices:
                if idx in new_values:
                    ns, nv = new_values[idx]
                    group = enhanced_groups[(ns, nv)]
                    if len(group) == 1:
                        # 增强后唯一，直接使用
                        elements[idx]['locator_strategy'] = ns
                        elements[idx]['locator_value'] = nv
                        enhanced_count += 1
                    else:
                        still_duplicate.append(idx)
                else:
                    still_duplicate.append(idx)

            # 第二轮：仍有重复的，追加 nth-child 或位置信息
            if still_duplicate:
                # 再按增强后的值分组
                sub_groups = defaultdict(list)
                for idx in still_duplicate:
                    key = (elements[idx].get('locator_strategy', ''), elements[idx].get('locator_value', ''))
                    sub_groups[key].append(idx)

                for (s, v), sub_indices in sub_groups.items():
                    if len(sub_indices) <= 1:
                        continue
                    # 尝试按文本区分
                    text_used = False
                    text_groups = defaultdict(list)
                    for idx in sub_indices:
                        t = elements[idx].get('name', '') or elements[idx].get('description', '') or ''
                        text_groups[t].append(idx)

                    if len(text_groups) > 1:
                        # 文本能区分部分，用XPath contains(text())
                        for t, t_indices in text_groups.items():
                            if len(t_indices) == 1 and t:
                                idx = t_indices[0]
                                tag = elements[idx].get('element_type', 'button')
                                tag_map = {'输入框': 'input', '按钮': 'button', '链接': 'a', '下拉框': 'select', '复选框': 'input', '文本域': 'textarea'}
                                html_tag = tag_map.get(tag, 'button')
                                escaped = t.replace('"', "'")
                                elements[idx]['locator_strategy'] = 'XPath'
                                elements[idx]['locator_value'] = f'//{html_tag}[contains(text(),"{escaped}")]'
                                enhanced_count += 1
                                text_used = True

                    # 最后兜底：用 nth-child
                    remaining = [idx for idx in sub_indices if
                                 (elements[idx].get('locator_strategy'), elements[idx].get('locator_value')) == (s, v)]
                    if len(remaining) > 1:
                        for seq, idx in enumerate(remaining, 1):
                            current_value = elements[idx]['locator_value']
                            if elements[idx]['locator_strategy'] == 'CSS':
                                elements[idx]['locator_value'] = f'{current_value}:nth-child({seq})'
                            else:
                                # XPath 用 position
                                elements[idx]['locator_value'] = f'({current_value})[{seq}]'
                            enhanced_count += 1

            print(f'[AI提取] 重复组处理完成: 增强了{enhanced_count}个元素的定位值')

        return elements

    def _ai_analyze_elements(self, dom_elements):
        """使用 LLM 分析 DOM 元素，返回结构化元素列表"""
        from langchain_openai import ChatOpenAI
        from apps.requirement_analysis.models import AIModelConfig
        import asyncio

        # 获取 AI 配置
        config_obj = AIModelConfig.objects.filter(role='browser_use_text', is_active=True).first()
        if not config_obj:
            raise Exception('未找到可用的AI模型配置')

        api_key = config_obj.api_key
        base_url = config_obj.base_url
        model_name = config_obj.model_name

        if not api_key:
            raise Exception('AI模型API Key未配置')

        llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=0.1,
            max_tokens=4000
        )

        # 精简 DOM 数据发给 LLM
        simplified = []
        for elem in dom_elements:
            simplified.append({
                'tag': elem.get('tag', ''),
                'id': elem.get('id', ''),
                'name': elem.get('name', ''),
                'type': elem.get('type', ''),
                'placeholder': elem.get('placeholder', ''),
                'text': elem.get('text', '')[:50],
                'role': elem.get('role', ''),
                'ariaLabel': elem.get('ariaLabel', ''),
                'auto_css': elem.get('auto_css', ''),
                'auto_xpath': elem.get('auto_xpath', ''),
            })

        prompt = f"""你是一个UI元素分析专家。以下是某个网页的可交互元素DOM数据，请为每个元素：
1. 生成简洁准确的中文名称（如"用户名输入框"、"查询按钮"、"新增链接"）
2. 推荐最佳定位策略（优先级：id > name > placeholder > CSS > XPath），选择最稳定、最不容易随页面改版而失效的方式
3. 分类元素类型，必须是以下之一：INPUT, BUTTON, LINK, DROPDOWN, CHECKBOX, RADIO, TEXT, IMAGE, CONTAINER, TABLE, FORM, MODAL
4. 去除无实际测试意义的元素（纯装饰性图标容器、空div等）
5. 合并功能相同的重复元素

元素类型映射规则：
- input/textarea → INPUT
- button/role=button → BUTTON
- a[href] → LINK
- select → DROPDOWN
- checkbox → CHECKBOX
- radio → RADIO
- 普通文本 → TEXT
- img → IMAGE
- 表格/container → TABLE 或 CONTAINER
- 弹窗 → MODAL

定位策略必须是以下之一：ID, CSS, XPath, name, class, text, placeholder, role, label, title, test-id

请严格按以下JSON数组格式返回，不要添加任何其他文字：
[{{"name": "元素名称", "element_type": "INPUT", "locator_strategy": "CSS", "locator_value": "#username", "backup_locators": [{{"strategy": "XPath", "value": "//*[@id='username']"}}], "description": "简短描述", "is_visible": true}}]

DOM数据：
{json.dumps(simplified, ensure_ascii=False)}"""

        # 同步调用 LLM（使用线程安全方式，兼容 Django 已有事件循环的情况）
        import concurrent.futures
        def call_llm():
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(llm.ainvoke(prompt))
            finally:
                loop.close()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(call_llm)
            response = future.result(timeout=120)
        content = response.content

        # 解析 LLM 返回的 JSON
        # 尝试提取 JSON 数组
        json_match = re.search(r'(\[.*\])', content, re.DOTALL)
        if json_match:
            try:
                ai_elements = json.loads(json_match.group(1))
                return ai_elements
            except json.JSONDecodeError:
                pass

        # 如果解析失败，尝试修复常见的 JSON 格式问题
        try:
            # 移除 markdown 代码块标记
            cleaned = content.replace('```json', '').replace('```', '').strip()
            ai_elements = json.loads(cleaned)
            return ai_elements
        except json.JSONDecodeError:
            raise Exception(f'AI返回结果解析失败: {content[:200]}')

    def _rule_based_classify(self, dom_elements):
        """规则引擎分类 — AI 分析失败时的兜底方案"""
        result = []
        for elem in dom_elements:
            tag = elem.get('tag', '')
            # 推断元素类型
            element_type = self._infer_element_type(elem)
            # 推断定位策略和值
            strategy, value = self._infer_best_locator(elem)
            # 推断名称
            name = self._infer_element_name(elem)

            if not name or not value:
                continue

            backup = []
            css_sel = elem.get('auto_css', '')
            xpath = elem.get('auto_xpath', '')
            if css_sel and css_sel != value:
                backup.append({'strategy': 'CSS', 'value': css_sel})
            if xpath and xpath != value:
                backup.append({'strategy': 'XPath', 'value': xpath})

            result.append({
                'name': name,
                'element_type': element_type,
                'locator_strategy': strategy,
                'locator_value': value,
                'backup_locators': backup,
                'description': name,
                'is_visible': elem.get('visible', True),
                'validation_status': elem.get('validation_status', ''),
                'validation_details': elem.get('validation_details', ''),
            })
        return result

    def _infer_element_type(self, elem):
        """根据 DOM 信息推断元素类型"""
        tag = elem.get('tag', '')
        role = elem.get('role', '')
        input_type = elem.get('type', '')

        if tag == 'input':
            if input_type in ['checkbox']:
                return 'CHECKBOX'
            if input_type in ['radio']:
                return 'RADIO'
            return 'INPUT'
        if tag == 'textarea':
            return 'INPUT'
        if tag == 'button' or role == 'button':
            return 'BUTTON'
        if tag == 'a':
            return 'LINK'
        if tag == 'select' or role == 'listbox':
            return 'DROPDOWN'
        if tag == 'img':
            return 'IMAGE'
        if 'table' in tag or 'el-table' in elem.get('className', ''):
            return 'TABLE'
        if role == 'dialog':
            return 'MODAL'
        return 'BUTTON'  # 默认

    def _infer_best_locator(self, elem):
        """推断最佳定位策略和值"""
        if elem.get('id'):
            return 'ID', elem["id"]
        # name含空格时不可靠，跳过
        name_val = elem.get('name', '')
        if name_val and ' ' not in name_val:
            return 'name', f'[name="{name_val}"]'
        # name含空格时，如果有text，用XPath text更可靠
        tag = elem.get('tag', 'button')
        if name_val and ' ' in name_val:
            compact_text = name_val.replace(' ', '')
            if compact_text:
                return 'XPath', f'//{tag}[contains(text(),"{compact_text}")]'
        if elem.get('dataTestId'):
            return 'test-id', f'[data-testid="{elem["dataTestId"]}"]'
        if elem.get('placeholder'):
            return 'placeholder', f'[placeholder="{elem["placeholder"]}"]'
        if elem.get('role') and elem.get('ariaLabel'):
            return 'role', f'[role="{elem["role"]}"]'
        if elem.get('ariaLabel'):
            return 'label', f'[aria-label="{elem["ariaLabel"]}"]'
        # 回退到 CSS
        css = elem.get('auto_css', '')
        if css:
            return 'CSS', css
        xpath = elem.get('auto_xpath', '')
        if xpath:
            return 'XPath', xpath
        return '', ''

    def _infer_element_name(self, elem):
        """推断元素名称"""
        # 优先使用 aria-label
        if elem.get('ariaLabel'):
            return elem['ariaLabel']
        # placeholder
        if elem.get('placeholder'):
            return elem['placeholder']
        # label 关联的文字
        if elem.get('title'):
            return elem['title']
        # 按钮文字
        text = elem.get('text', '').strip()
        if text and len(text) <= 20:
            return text
        # name 属性
        if elem.get('name'):
            return elem['name']
        # tag + type
        tag = elem.get('tag', '')
        input_type = elem.get('type', '')
        if tag == 'input' and input_type:
            return f'{input_type}输入框'
        if tag == 'button':
            return '按钮'
        if tag == 'a':
            return '链接'
        return ''

    def _build_element_tree(self, elements):
        """构建元素树形结构 - 返回元素列表而不是页面分组，因为前端会自己处理页面关联"""
        element_data_list = []
        for element in elements:
            element_data = {
                'id': element.id,
                'name': element.name,
                'type': 'element',
                'element_type': element.element_type,
                'locator_strategy': element.locator_strategy.name if element.locator_strategy else None,
                'locator_value': element.locator_value,
                'validation_status': element.validation_status,
                'usage_count': element.usage_count,
                'group_id': element.group_id,  # 用于前端关联到页面
                'page': element.page,  # 保留向后兼容
                'children': []
            }
            element_data_list.append(element_data)

        return element_data_list

    def _generate_element_suggestions(self, element):
        """生成元素使用建议"""
        suggestions = []

        # 基于元素类型生成建议
        if element.element_type == 'INPUT':
            suggestions.append("建议为输入框元素添加清空和输入验证操作")
        elif element.element_type == 'BUTTON':
            suggestions.append("建议验证按钮点击后的页面跳转或状态变化")
        elif element.element_type == 'DROPDOWN':
            suggestions.append("建议测试下拉框的所有选项")

        # 基于使用频率生成建议
        if element.usage_count == 0:
            suggestions.append("此元素尚未在任何脚本中使用，考虑是否需要删除")
        elif element.usage_count > 10:
            suggestions.append("此元素使用频率较高，建议添加到页面对象中以提高复用性")

        return suggestions


class ElementGroupViewSet(viewsets.ModelViewSet):
    queryset = ElementGroup.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['project', 'parent_group']
    search_fields = ['name', 'description']

    def get_serializer_class(self):
        if self.action == 'create':
            return ElementGroupCreateSerializer
        return ElementGroupSerializer

    def get_queryset(self):
        # 只显示用户有权限访问的项目的元素分组
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        return ElementGroup.objects.filter(project__in=accessible_projects).select_related('project',
                                                                                           'parent_group').order_by(
            'order', 'name')

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取分组树形结构"""
        project_id = request.query_params.get('project')
        if not project_id:
            return Response({'error': '需要指定项目ID'}, status=status.HTTP_400_BAD_REQUEST)

        groups = self.get_queryset().filter(project_id=project_id, parent_group__isnull=True)
        serializer = ElementGroupSerializer(groups, many=True)
        return Response(serializer.data)


class PageObjectViewSet(viewsets.ModelViewSet):
    queryset = PageObject.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['project']
    search_fields = ['name', 'class_name', 'description']

    def get_serializer_class(self):
        if self.action == 'create':
            return PageObjectCreateSerializer
        return PageObjectSerializer

    def get_queryset(self):
        # 只显示用户有权限访问的项目的页面对象
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        return PageObject.objects.filter(project__in=accessible_projects).select_related(
            'project', 'created_by'
        ).prefetch_related('page_object_elements__element').order_by('-created_at')

    @action(detail=True, methods=['post'])
    def generate_code(self, request, pk=None):
        """生成页面对象代码"""
        page_object = self.get_object()
        serializer = CodeGenerationSerializer(data=request.data)

        if serializer.is_valid():
            language = serializer.validated_data['language']
            framework = serializer.validated_data['framework']
            include_comments = serializer.validated_data['include_comments']

            try:
                generated_code = page_object.generate_code(language)

                # 保存生成的代码模板
                page_object.template_code = generated_code
                page_object.save()

                return Response({
                    'code': generated_code,
                    'language': language,
                    'framework': framework
                })
            except Exception as e:
                return Response({
                    'error': f'代码生成失败: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_element(self, request, pk=None):
        """向页面对象添加元素"""
        page_object = self.get_object()
        serializer = PageObjectElementSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(page_object=page_object)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def elements(self, request, pk=None):
        """获取页面对象的所有元素"""
        page_object = self.get_object()
        po_elements = page_object.page_object_elements.select_related('element').all()
        serializer = PageObjectElementSerializer(po_elements, many=True)
        return Response(serializer.data)


class PageObjectElementViewSet(viewsets.ModelViewSet):
    queryset = PageObjectElement.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = PageObjectElementSerializer

    def get_queryset(self):
        # 只显示用户有权限访问的页面对象元素
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        return PageObjectElement.objects.filter(
            page_object__project__in=accessible_projects
        ).select_related('page_object', 'element').order_by('id')


class ScriptStepViewSet(viewsets.ModelViewSet):
    queryset = ScriptStep.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ScriptStepSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['script', 'action_type', 'target_element', 'page_object']

    def get_queryset(self):
        # 只显示用户有权限访问的脚本步骤
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        return ScriptStep.objects.filter(
            script__project__in=accessible_projects
        ).select_related('script', 'target_element', 'page_object').order_by('step_order')

    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        """批量创建脚本步骤"""
        steps_data = request.data.get('steps', [])
        created_steps = []

        for step_data in steps_data:
            serializer = ScriptStepSerializer(data=step_data)
            if serializer.is_valid():
                step = serializer.save()
                created_steps.append(step)
            else:
                return Response({
                    'error': f'步骤创建失败: {serializer.errors}'
                }, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = ScriptStepSerializer(created_steps, many=True)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ScriptElementUsageViewSet(viewsets.ModelViewSet):
    queryset = ScriptElementUsage.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ScriptElementUsageSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['script', 'element', 'usage_type']

    def get_queryset(self):
        # 只显示用户有权限访问的脚本元素使用记录
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        return ScriptElementUsage.objects.filter(
            script__project__in=accessible_projects
        ).select_related('script', 'element').order_by('script', 'line_number')

    @action(detail=False, methods=['post'])
    def analyze_script(self, request):
        """分析脚本中的元素使用情况"""
        script_id = request.data.get('script_id')
        if not script_id:
            return Response({'error': '需要指定脚本ID'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            script = TestScript.objects.get(id=script_id)
            analysis_result = self._analyze_script_elements(script)

            serializer = ScriptAnalysisSerializer(analysis_result)
            return Response(serializer.data)
        except TestScript.DoesNotExist:
            return Response({'error': '脚本不存在'}, status=status.HTTP_404_NOT_FOUND)

    def _analyze_script_elements(self, script):
        """分析脚本中的元素使用"""
        # 解析脚本内容，查找元素使用情况
        content = script.content
        usages = []
        missing_elements = []
        recommendations = []

        # 简单的元素使用分析（实际实现会更复杂）
        if script.script_type == 'CODE':
            # 分析代码中的定位器使用
            locator_patterns = [
                r'locator\(["\']([^"\']+)["\']\)',
                r'findElement\(["\']([^"\']+)["\']\)',
                r'css\(["\']([^"\']+)["\']\)',
                r'xpath\(["\']([^"\']+)["\']\)'
            ]

            for pattern in locator_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # 查找对应的元素
                    try:
                        element = Element.objects.get(
                            project=script.project,
                            locator_value=match
                        )
                        usage, created = ScriptElementUsage.objects.get_or_create(
                            script=script,
                            element=element,
                            defaults={
                                'usage_type': 'CLICK',  # 默认类型
                                'line_number': 1,  # 需要实际解析
                                'frequency': 1
                            }
                        )
                        if not created:
                            usage.frequency += 1
                            usage.save()

                        element.increment_usage_count()
                        usages.append(usage)
                    except Element.DoesNotExist:
                        missing_elements.append(match)

        # 生成建议
        if missing_elements:
            recommendations.append(f"发现 {len(missing_elements)} 个未定义的元素定位器")

        if len(usages) > 20:
            recommendations.append("脚本复杂度较高，建议拆分为多个小脚本")

        complexity_score = min(100, len(usages) * 5)

        return {
            'element_usages': usages,
            'missing_elements': missing_elements,
            'recommendations': recommendations,
            'complexity_score': complexity_score
        }


class TestScriptViewSet(viewsets.ModelViewSet):
    queryset = TestScript.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['project', 'script_type']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return TestScriptCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TestScriptUpdateSerializer
        return TestScriptSerializer

    def get_queryset(self):
        # 只显示用户有权限访问的项目的测试脚本
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        return TestScript.objects.filter(project__in=accessible_projects)


class LoginConfigViewSet(viewsets.ModelViewSet):
    """登录配置视图集"""
    queryset = LoginConfig.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['project']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return LoginConfigCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return LoginConfigUpdateSerializer
        return LoginConfigSerializer

    def get_queryset(self):
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        return LoginConfig.objects.filter(
            project__in=accessible_projects
        ).select_related('project', 'login_test_case', 'created_by')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def test_login(self, request, pk=None):
        """测试登录配置是否可用 — 执行关联的登录测试用例"""
        login_config = self.get_object()

        if not login_config.login_test_case:
            return Response({
                'success': False,
                'message': '未关联登录测试用例'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            import os
            os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'

            from playwright.sync_api import sync_playwright

            test_case = login_config.login_test_case

            # 预先获取步骤数据，避免在Playwright上下文中访问ORM（跳过清理步骤）
            steps = test_case.steps.select_related('element', 'element__locator_strategy').filter(is_cleanup=False).order_by('step_number')
            case_data = {
                'id': test_case.id,
                'name': test_case.name,
                'steps': []
            }
            for step in steps:
                step_data = {
                    'id': step.id,
                    'step_number': step.step_number,
                    'action_type': step.action_type,
                    'description': step.description,
                    'input_value': step.input_value,
                    'wait_time': step.wait_time,
                    'action_wait': step.action_wait,
                    'assert_type': step.assert_type,
                    'assert_value': step.assert_value,
                    'output_var': step.output_var,
                    'element': None
                }
                if step.element:
                    step_data['element'] = {
                        'id': step.element.id,
                        'name': step.element.name,
                        'locator_value': step.element.locator_value,
                        'locator_strategy': step.element.locator_strategy.name if step.element.locator_strategy else 'css'
                    }
                case_data['steps'].append(step_data)

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False, args=['--start-maximized'])
                context = browser.new_context(no_viewport=True)
                page = context.new_page()

                # 导航到登录页（优先使用login_config的login_url，否则使用项目基础URL）
                start_url = login_config.login_url or login_config.project.base_url
                if start_url:
                    page.goto(start_url, wait_until='networkidle', timeout=30000)
                    time.sleep(2)

                # 执行登录用例的每个步骤
                step_errors = []
                for step_data in case_data['steps']:
                    try:
                        # 构造选择器
                        selector = None
                        element_info = step_data.get('element')
                        if element_info:
                            locator_value = element_info['locator_value']
                            locator_strategy = element_info['locator_strategy'].lower()
                            if locator_strategy in ['css', 'css selector']:
                                selector = locator_value
                            elif locator_strategy == 'xpath':
                                selector = f'xpath={locator_value}'
                            elif locator_strategy == 'id':
                                selector = locator_value if locator_value.startswith('#') else f'#{locator_value}'
                            elif locator_strategy == 'name':
                                selector = f'[name="{locator_value}"]'
                            elif locator_strategy == 'text':
                                selector = f'text={locator_value}'
                            else:
                                selector = locator_value

                        action = step_data['action_type']

                        if action == 'click' and selector:
                            page.click(selector, timeout=10000)
                        elif action == 'fill' and selector:
                            page.fill(selector, step_data['input_value'], timeout=10000)
                        elif action == 'wait':
                            time.sleep(step_data['wait_time'] / 1000)
                        elif action == 'waitFor' and selector:
                            page.wait_for_selector(selector, timeout=step_data['wait_time'])
                        elif action == 'hover' and selector:
                            page.hover(selector, timeout=10000)
                        elif action == 'assert':
                            if step_data['assert_type'] == 'isVisible' and selector:
                                if not page.is_visible(selector):
                                    step_errors.append(f"步骤{step_data['step_number']}: 元素不可见")
                            elif step_data['assert_type'] == 'textContains' and selector:
                                text = page.locator(selector).text_content(timeout=5000) or ''
                                if step_data['assert_value'] not in text:
                                    step_errors.append(f"步骤{step_data['step_number']}: 文本不包含'{step_data['assert_value']}'")
                        
                        time.sleep(0.5)
                        
                        # action_wait: 步骤操作成功后等待指定秒数再执行下一步
                        action_wait = step_data.get('action_wait', 0) or 0
                        if action_wait > 0:
                            time.sleep(action_wait)
                    except Exception as step_err:
                        step_errors.append(f"步骤{step_data['step_number']}执行失败: {str(step_err)}")
                        break

                browser.close()

            if step_errors:
                return Response({
                    'success': False,
                    'message': f'登录测试失败: {"; ".join(step_errors)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'success': True,
                'message': '登录测试成功'
            })

        except Exception as e:
            import traceback
            return Response({
                'success': False,
                'message': f'登录测试异常: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TestSuiteViewSet(viewsets.ModelViewSet):
    queryset = TestSuite.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['project']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return TestSuiteCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TestSuiteUpdateSerializer
        elif self.action == 'retrieve':
            return TestSuiteWithScriptsSerializer
        return TestSuiteSerializer

    def get_queryset(self):
        # 只显示用户有权限访问的项目的测试套件
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        return TestSuite.objects.filter(project__in=accessible_projects)

    def perform_create(self, serializer):
        instance = serializer.save()
        # 记录操作
        log_operation('create', 'suite', instance.id, instance.name, self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        # 记录操作
        log_operation('edit', 'suite', instance.id, instance.name, self.request.user)

    def perform_destroy(self, instance):
        # 记录操作（在删除前记录）
        log_operation('delete', 'suite', instance.id, instance.name, self.request.user)
        instance.delete()

    @action(detail=True, methods=['get'])
    def scripts(self, request, pk=None):
        """获取测试套件中的所有脚本"""
        test_suite = self.get_object()
        scripts = test_suite.suite_scripts.all()
        serializer = TestSuiteScriptSerializer(scripts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_script(self, request, pk=None):
        """向测试套件添加脚本"""
        test_suite = self.get_object()
        data = request.data
        data['test_suite'] = pk
        serializer = TestSuiteScriptSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove_script(self, request, pk=None, script_id=None):
        """从测试套件移除脚本"""
        test_suite = self.get_object()
        try:
            suite_script = TestSuiteScript.objects.get(test_suite=test_suite, id=script_id)
            suite_script.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TestSuiteScript.DoesNotExist:
            return Response({'error': '脚本不存在于该测试套件中'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def test_cases(self, request, pk=None):
        """获取测试套件中的所有测试用例"""
        test_suite = self.get_object()
        test_cases = test_suite.suite_test_cases.all()
        serializer = TestSuiteTestCaseSerializer(test_cases, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_test_case(self, request, pk=None):
        """向测试套件添加测试用例"""
        test_suite = self.get_object()
        test_case_id = request.data.get('test_case_id')
        order = request.data.get('order', 0)

        try:
            from .models import TestSuiteTestCase
            suite_test_case = TestSuiteTestCase.objects.create(
                test_suite=test_suite,
                test_case_id=test_case_id,
                order=order
            )
            serializer = TestSuiteTestCaseSerializer(suite_test_case)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove_test_case(self, request, pk=None):
        """从测试套件移除测试用例"""
        test_suite = self.get_object()
        test_case_id = request.data.get('test_case_id')

        try:
            from .models import TestSuiteTestCase
            suite_test_case = TestSuiteTestCase.objects.get(
                test_suite=test_suite,
                test_case_id=test_case_id
            )
            suite_test_case.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TestSuiteTestCase.DoesNotExist:
            return Response({'error': '测试用例不存在于该测试套件中'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def update_test_case_order(self, request, pk=None):
        """更新测试套件中测试用例的顺序"""
        test_suite = self.get_object()
        test_case_orders = request.data.get('test_case_orders', [])

        try:
            from .models import TestSuiteTestCase
            for item in test_case_orders:
                TestSuiteTestCase.objects.filter(
                    test_suite=test_suite,
                    test_case_id=item['test_case_id']
                ).update(order=item['order'])

            return Response({'message': '顺序更新成功'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def run_suite(self, request, pk=None):
        """执行测试套件"""
        test_suite = self.get_object()

        # 传统模式执行（Playwright/Selenium）
        # 检查是否包含测试用例
        test_case_count = test_suite.suite_test_cases.count()
        if test_case_count == 0:
            return Response({
                'error': '该测试套件未包含任何测试用例，无法执行'
            }, status=status.HTTP_400_BAD_REQUEST)

        engine = request.data.get('engine', 'playwright')
        browser = request.data.get('browser', 'chrome')
        headless = request.data.get('headless', False)

        if engine == 'selenium':
            from .selenium_engine import SeleniumTestEngine
            is_ready, error_msg = SeleniumTestEngine.check_execution_environment(browser)
            if not is_ready:
                return Response({
                    'error': error_msg,
                    'message': '浏览器驱动未就绪，请先安装后再执行测试套件'
                }, status=status.HTTP_400_BAD_REQUEST)
        elif engine == 'playwright':
            from .playwright_engine import PlaywrightTestEngine
            is_ready, error_msg = PlaywrightTestEngine.check_execution_environment_sync(browser)
            if not is_ready:
                return Response({
                    'error': error_msg,
                    'message': 'Playwright 浏览器未就绪，请先安装后再执行测试套件'
                }, status=status.HTTP_400_BAD_REQUEST)

        # 更新套件执行状态为运行中
        test_suite.execution_status = 'running'
        test_suite.save()

        # 记录运行操作
        log_operation('run', 'suite', test_suite.id, test_suite.name, request.user)

        # 在后台线程中执行测试
        import threading
        import traceback
        from .test_executor import TestExecutor

        def run_test():
            try:
                print(f"[测试套件] 开始执行: {test_suite.name} (ID: {test_suite.id})")
                print(f"[测试套件] 配置: engine={engine}, browser={browser}, headless={headless}")

                executor = TestExecutor(
                    test_suite=test_suite,
                    engine=engine,
                    browser=browser,
                    headless=headless,
                    executed_by=request.user
                )
                executor.run()

                print(f"[测试套件] 执行完成: {test_suite.name}")
            except Exception as e:
                print(f"[测试套件] 执行异常: {test_suite.name}")
                print(f"[测试套件] 错误: {str(e)}")
                traceback.print_exc()

                # 更新套件状态为失败
                try:
                    test_suite.execution_status = 'failed'
                    test_suite.save()
                    print(f"[测试套件] 已更新状态为失败")
                except Exception as save_error:
                    print(f"[测试套件] 更新状态失败: {save_error}")

        # 启动后台线程执行测试
        thread = threading.Thread(target=run_test, daemon=False)
        thread.start()

        return Response({
            'message': '测试套件开始执行',
            'suite_id': test_suite.id,
            'test_case_count': test_case_count,
            'engine': engine,
            'browser': browser,
            'headless': headless
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='run-cleanup')
    def run_cleanup(self, request, pk=None):
        """执行套件中所有用例的清理步骤"""
        test_suite = self.get_object()

        # 检查是否有用例
        test_cases = [stc.test_case for stc in test_suite.suite_test_cases.all().order_by('order')]
        if not test_cases:
            return Response({'error': '该测试套件未包含任何测试用例'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查是否有清理步骤
        has_cleanup = False
        for tc in test_cases:
            if tc.steps.filter(is_cleanup=True).exists():
                has_cleanup = True
                break
        if not has_cleanup:
            return Response({'error': '该套件的用例没有配置清理步骤'}, status=status.HTTP_400_BAD_REQUEST)

        engine = request.data.get('engine', getattr(test_suite, 'engine', None) or 'playwright')
        browser = request.data.get('browser', getattr(test_suite, 'browser', None) or 'chrome')
        headless = request.data.get('headless', False)

        import threading
        import traceback
        from .test_executor import TestExecutor

        def run_cleanup_task():
            try:
                print(f"[清理步骤] 开始执行: {test_suite.name}")
                executor = TestExecutor(
                    test_suite=test_suite,
                    engine=engine,
                    browser=browser,
                    headless=headless,
                    executed_by=request.user
                )
                executor.run_cleanup(test_cases)
                print(f"[清理步骤] 执行完成: {test_suite.name}")
            except Exception as e:
                print(f"[清理步骤] 执行异常: {str(e)}")
                traceback.print_exc()

        thread = threading.Thread(target=run_cleanup_task, daemon=False)
        thread.start()

        log_operation('run', 'suite', test_suite.id, f'{test_suite.name} - 清理测试数据', request.user)

        return Response({
            'message': '清理步骤开始执行',
            'suite_id': test_suite.id,
            'engine': engine,
            'browser': browser,
            'headless': headless
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='run-db-cleanup')
    def run_db_cleanup(self, request, pk=None):
        """通过直连被测数据库执行清理SQL"""
        test_suite = self.get_object()
        project = test_suite.project

        # 检查项目是否配置了被测数据库连接
        if not project.target_db_type:
            return Response({'error': '项目未配置被测数据库连接信息，请在项目设置中配置'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查套件是否配置了清理SQL
        cleanup_sql = test_suite.cleanup_sql.strip()
        if not cleanup_sql:
            return Response({'error': '该套件未配置清理SQL'}, status=status.HTTP_400_BAD_REQUEST)

        # 执行数据库清理
        try:
            result = self._execute_cleanup_sql(project, cleanup_sql)
            log_operation('run', 'suite', test_suite.id, f'{test_suite.name} - 数据库清理({result["total_affected"]}行)', request.user)
            return Response({
                'message': f'清理完成，共影响 {result["total_affected"]} 行',
                'suite_id': test_suite.id,
                'details': result['details'],
                'total_affected': result['total_affected']
            })
        except Exception as e:
            logger.error(f"数据库清理失败: {str(e)}", exc_info=True)
            return Response({'error': f'数据库清理失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _execute_cleanup_sql(self, project, cleanup_sql):
        """连接被测数据库执行清理SQL"""
        import re

        # 拆分多条SQL（按分号分隔，忽略注释和空行）
        sqls = [s.strip() for s in re.split(r';\s*\n', cleanup_sql) if s.strip() and not s.strip().startswith('--')]

        db_type = project.target_db_type.lower()
        details = []
        total_affected = 0

        if db_type == 'mysql':
            import pymysql
            conn = pymysql.connect(
                host=project.target_db_host,
                port=project.target_db_port or 3306,
                user=project.target_db_user,
                password=project.target_db_password,
                database=project.target_db_name,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.Cursor
            )
        elif db_type in ('postgresql', 'postgres'):
            import psycopg2
            conn = psycopg2.connect(
                host=project.target_db_host,
                port=project.target_db_port or 5432,
                user=project.target_db_user,
                password=project.target_db_password,
                dbname=project.target_db_name
            )
        elif db_type == 'sqlite':
            import sqlite3
            conn = sqlite3.connect(project.target_db_name)
        elif db_type == 'oracle':
            import cx_Oracle
            dsn = cx_Oracle.makedsn(project.target_db_host, project.target_db_port or 1521, service_name=project.target_db_name)
            conn = cx_Oracle.connect(user=project.target_db_user, password=project.target_db_password, dsn=dsn)
        else:
            raise ValueError(f'不支持的数据库类型: {db_type}')

        try:
            with conn.cursor() as cursor:
                for sql in sqls:
                    # 安全检查：只允许 DELETE / UPDATE / TRUNCATE 语句
                    sql_upper = sql.strip().upper()
                    if not any(sql_upper.startswith(kw) for kw in ['DELETE', 'UPDATE', 'TRUNCATE']):
                        details.append({'sql': sql, 'error': '只允许 DELETE/UPDATE/TRUNCATE 语句', 'affected': 0})
                        continue

                    try:
                        cursor.execute(sql)
                        affected = cursor.rowcount if cursor.rowcount >= 0 else 0
                        details.append({'sql': sql, 'affected': affected})
                        total_affected += affected
                    except Exception as e:
                        details.append({'sql': sql, 'error': str(e), 'affected': 0})
            conn.commit()
        finally:
            conn.close()

        return {'details': details, 'total_affected': total_affected}


class TestExecutionViewSet(viewsets.ModelViewSet):
    queryset = TestExecution.objects.all()
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['project', 'test_suite', 'test_script', 'status', 'environment', 'executed_by']
    search_fields = ['error_message']
    ordering = ['-created_at']
    pagination_class = StandardPagination

    def get_queryset(self):
        # 只显示用户有权限访问的项目的测试执行记录
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        return TestExecution.objects.filter(
            project__in=accessible_projects
        ).select_related('project', 'test_suite', 'test_script', 'executed_by')

    def get_serializer_class(self):
        if self.action == 'create':
            return TestExecutionCreateSerializer
        return TestExecutionSerializer

    def perform_destroy(self, instance):
        # 记录操作（删除测试报告）
        suite_name = instance.test_suite.name if instance.test_suite else f"执行记录#{instance.id}"
        log_operation('delete', 'report', instance.id, suite_name, self.request.user)
        instance.delete()


class ScreenshotViewSet(viewsets.ModelViewSet):
    queryset = Screenshot.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ScreenshotSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['execution']

    def get_queryset(self):
        # 只显示用户有权限访问的项目的截图
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        executions = TestExecution.objects.filter(project__in=accessible_projects)
        return Screenshot.objects.filter(execution__in=executions)


class TestCaseViewSet(viewsets.ModelViewSet):
    """测试用例视图集"""
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name', 'priority', 'status']
    ordering = ['-created_at']
    filterset_fields = ['project', 'status', 'priority', 'created_by']

    def get_queryset(self):
        # 只显示用户有权限访问的项目的测试用例
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()

    def get_queryset(self):
        # 只显示用户有权限访问的项目的测试用例
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        return TestCase.objects.filter(project__in=accessible_projects).select_related('project', 'created_by')

    def perform_create(self, serializer):
        # 创建测试用例
        instance = serializer.save(created_by=self.request.user)

        # 记录操作
        log_operation('create', 'test_case', instance.id, instance.name, self.request.user)

        # 处理步骤数据
        steps_data = self.request.data.get('steps', [])
        logger.info(f"创建测试用例 {instance.id} 的步骤数据: {len(steps_data)} 个步骤")

        if steps_data:
            # 创建新步骤
            created_count = 0
            for i, step_data in enumerate(steps_data):
                # 确保步骤数据结构正确
                step_data = dict(step_data)  # 创建副本避免修改原数据
                step_data['test_case'] = instance.id  # 使用测试用例ID
                step_data['step_number'] = i + 1  # 确保步骤序号正确

                # 处理元素ID
                if 'element_id' in step_data:
                    step_data['element'] = step_data.pop('element_id')

                # 移除只读字段
                step_data.pop('id', None)
                step_data.pop('element_name', None)
                step_data.pop('element_locator', None)
                step_data.pop('created_at', None)
                step_data.pop('expanded', None)  # 前端UI状态字段

                # 使用模型直接创建，避免序列化器的复杂性
                try:
                    TestCaseStep.objects.create(
                        test_case=instance,
                        step_number=step_data.get('step_number', i + 1),
                        action_type=step_data.get('action_type', 'click'),
                        element_id=step_data.get('element') if step_data.get('element') else None,
                        input_value=step_data.get('input_value', ''),
                        wait_time=step_data.get('wait_time', 1000),
                        action_wait=step_data.get('action_wait', 0),
                        assert_type=step_data.get('assert_type', ''),
                        assert_value=step_data.get('assert_value', ''),
                        description=step_data.get('description', ''),
                        output_var=step_data.get('output_var', ''),
                        is_cleanup=step_data.get('is_cleanup', False)
                    )
                    created_count += 1
                except Exception as e:
                    logger.error(f"创建步骤 {i + 1} 失败: {str(e)}")
                    logger.error(f"步骤数据: {step_data}")

            logger.info(f"成功创建了 {created_count} 个新步骤")

    @action(detail=True, methods=['post'])
    def copy_case(self, request, pk=None):
        """复制测试用例"""
        test_case = self.get_object()

        try:
            # 1. 复制测试用例基本信息
            new_case = TestCase.objects.create(
                project=test_case.project,
                name=f"{test_case.name}_copy",
                description=test_case.description,
                priority=test_case.priority,
                status=test_case.status,
                created_by=request.user
            )

            # 2. 复制测试步骤
            steps = test_case.steps.all().order_by('step_number')
            new_steps = []
            for step in steps:
                new_steps.append(TestCaseStep(
                    test_case=new_case,
                    step_number=step.step_number,
                    action_type=step.action_type,
                    element=step.element,
                    input_value=step.input_value,
                    wait_time=step.wait_time,
                    action_wait=step.action_wait,
                    assert_type=step.assert_type,
                    assert_value=step.assert_value,
                    description=step.description,
                    is_cleanup=step.is_cleanup
                ))

            if new_steps:
                TestCaseStep.objects.bulk_create(new_steps)

            # 记录操作
            log_operation('create', 'test_case', new_case.id, new_case.name, request.user)

            serializer = self.get_serializer(new_case)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"复制测试用例失败: {str(e)}")
            return Response({'error': f"复制失败: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_update(self, serializer):
        # 更新测试用例步骤
        instance = serializer.save()

        # 记录操作
        log_operation('edit', 'test_case', instance.id, instance.name, self.request.user)

        # 处理步骤数据
        steps_data = self.request.data.get('steps', [])
        logger.info(f"更新测试用例 {instance.id} 的步骤数据: {len(steps_data)} 个步骤")

        if steps_data:
            # 删除现有步骤
            existing_steps_count = instance.steps.count()
            instance.steps.all().delete()
            logger.info(f"删除了 {existing_steps_count} 个现有步骤")

            # 创建新步骤
            created_count = 0
            for i, step_data in enumerate(steps_data):
                # 确保步骤数据结构正确
                step_data = dict(step_data)  # 创建副本避免修改原数据
                step_data['test_case'] = instance.id  # 使用测试用例ID
                step_data['step_number'] = i + 1  # 确保步骤序号正确

                # 处理元素ID
                if 'element_id' in step_data:
                    step_data['element'] = step_data.pop('element_id')

                # 移除只读字段
                step_data.pop('id', None)
                step_data.pop('element_name', None)
                step_data.pop('element_locator', None)
                step_data.pop('created_at', None)
                step_data.pop('expanded', None)  # 前端UI状态字段

                # 使用模型直接创建，避免序列化器的复杂性
                try:
                    TestCaseStep.objects.create(
                        test_case=instance,
                        step_number=step_data.get('step_number', i + 1),
                        action_type=step_data.get('action_type', 'click'),
                        element_id=step_data.get('element') if step_data.get('element') else None,
                        input_value=step_data.get('input_value', ''),
                        wait_time=step_data.get('wait_time', 1000),
                        action_wait=step_data.get('action_wait', 0),
                        assert_type=step_data.get('assert_type', ''),
                        assert_value=step_data.get('assert_value', ''),
                        description=step_data.get('description', ''),
                        output_var=step_data.get('output_var', ''),
                        is_cleanup=step_data.get('is_cleanup', False)
                    )
                    created_count += 1
                except Exception as e:
                    logger.error(f"创建步骤 {i + 1} 失败: {str(e)}")
                    logger.error(f"步骤数据: {step_data}")

            logger.info(f"成功创建了 {created_count} 个新步骤")

    def _generate_step_log(self, step, step_result='success'):
        """根据测试步骤生成执行日志"""
        import time

        # 模拟执行时间（0.1秒到2秒之间）
        execution_time = round(random.uniform(0.1, 2.0), 2)

        # 构建基础日志
        log_parts = []

        # 步骤信息
        if step.element:
            element_name = step.element.name
            locator_info = f"{step.element.locator_strategy.name}={step.element.locator_value}"
        else:
            element_name = "页面"
            locator_info = "无"

        # 根据操作类型生成具体日志
        if step.action_type == 'click':
            log_parts.append(f"点击元素 '{element_name}'")
            log_parts.append(f"- 使用定位器: {locator_info}")
            if step_result == 'success':
                log_parts.append(f"- 元素点击成功 - 耗时 {execution_time}s")
            else:
                log_parts.append(f"- 元素点击失败 - 元素未找到或不可点击")

        elif step.action_type == 'fill':
            log_parts.append(f"在元素 '{element_name}' 中输入文本")
            log_parts.append(f"- 使用定位器: {locator_info}")
            log_parts.append(f"- 输入值: '{step.input_value}'")
            if step_result == 'success':
                log_parts.append(f"- 文本输入成功 - 耗时 {execution_time}s")
            else:
                log_parts.append(f"- 文本输入失败 - 元素未找到或不可编辑")

        elif step.action_type == 'getText':
            log_parts.append(f"获取元素 '{element_name}' 的文本内容")
            log_parts.append(f"- 使用定位器: {locator_info}")
            if step_result == 'success':
                # 模拟获取到的文本
                mock_text = f"示例文本内容_{step.id}" if step.id else "示例文本内容"
                log_parts.append(f"- 获取到文本: '{mock_text}' - 耗时 {execution_time}s")
            else:
                log_parts.append(f"- 获取文本失败 - 元素未找到")

        elif step.action_type == 'waitFor':
            log_parts.append(f"等待元素 '{element_name}' 出现")
            log_parts.append(f"- 使用定位器: {locator_info}")
            log_parts.append(f"- 超时时间: {step.wait_time / 1000}秒")
            if step_result == 'success':
                log_parts.append(f"- 元素在 {execution_time}s 后出现")
            else:
                log_parts.append(f"- 等待超时 - 元素未在指定时间内出现")

        elif step.action_type == 'hover':
            log_parts.append(f"在元素 '{element_name}' 上悬停")
            log_parts.append(f"- 使用定位器: {locator_info}")
            if step_result == 'success':
                log_parts.append(f"- 悬停操作成功 - 耗时 {execution_time}s")
            else:
                log_parts.append(f"- 悬停操作失败 - 元素未找到")

        elif step.action_type == 'scroll':
            log_parts.append(f"滚动到元素 '{element_name}'")
            log_parts.append(f"- 使用定位器: {locator_info}")
            if step_result == 'success':
                log_parts.append(f"- 滚动操作成功 - 耗时 {execution_time}s")
            else:
                log_parts.append(f"- 滚动操作失败 - 元素未找到")

        elif step.action_type == 'screenshot':
            log_parts.append(f"执行截图操作")
            if step.element:
                log_parts.append(f"- 截图范围: 元素 '{element_name}'")
            else:
                log_parts.append(f"- 截图范围: 整个页面")
            if step_result == 'success':
                screenshot_name = f"screenshot_{int(time.time())}.png"
                log_parts.append(f"- 截图保存成功: {screenshot_name} - 耗时 {execution_time}s")
            else:
                log_parts.append(f"- 截图保存失败")

        elif step.action_type == 'assert':
            log_parts.append(f"执行断言验证")
            log_parts.append(f"- 断言类型: {step.assert_type}")
            if step.assert_value:
                log_parts.append(f"- 期望值: '{step.assert_value}'")
            if step_result == 'success':
                log_parts.append(f"- 断言通过 - 耗时 {execution_time}s")
            else:
                log_parts.append(f"- 断言失败 - 实际值与期望值不匹配")

        elif step.action_type == 'wait':
            log_parts.append(f"固定等待")
            log_parts.append(f"- 等待时间: {step.wait_time / 1000}秒")
            log_parts.append(f"- 等待完成")

        else:
            # 默认处理其他操作类型
            log_parts.append(f"执行操作: {step.action_type}")
            if step.element:
                log_parts.append(f"- 目标元素: {element_name}")
            if step.input_value:
                log_parts.append(f"- 输入值: {step.input_value}")
            log_parts.append(f"- 操作{'成功' if step_result == 'success' else '失败'} - 耗时 {execution_time}s")

        # 如果步骤有描述，添加到日志中
        if step.description:
            log_parts.insert(0, f"说明: {step.description}")

        return '\n'.join(log_parts)

    def _generate_failure_screenshot(self, step_number, step_description):
        """生成失败截图的模拟数据（base64格式）"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            import base64

            # 创建一个模拟的失败截图
            # 实际应用中，这里应该是通过Playwright/Selenium捕获真实的页面截图
            width, height = 1280, 720
            img = Image.new('RGB', (width, height), color=(240, 240, 245))
            draw = ImageDraw.Draw(img)

            # 绘制标题区域
            draw.rectangle([0, 0, width, 80], fill=(220, 53, 69))

            # 添加文本信息（使用默认字体）
            try:
                # 尝试使用系统字体
                font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 40)
                font_text = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 24)
            except:
                # 如果系统字体不可用，使用默认字体
                font_title = ImageFont.load_default()
                font_text = ImageFont.load_default()

            # 标题
            draw.text((40, 20), "测试步骤执行失败", fill=(255, 255, 255), font=font_title)

            # 失败信息
            info_y = 120
            draw.text((40, info_y), f"失败步骤: 步骤 {step_number}", fill=(50, 50, 50), font=font_text)
            draw.text((40, info_y + 40), f"步骤说明: {step_description}", fill=(50, 50, 50), font=font_text)
            draw.text((40, info_y + 80), f"失败时间: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
                      fill=(50, 50, 50), font=font_text)

            # 绘制一个模拟的浏览器窗口
            browser_y = info_y + 140
            draw.rectangle([40, browser_y, width - 40, height - 40], outline=(200, 200, 200), width=2)
            draw.rectangle([40, browser_y, width - 40, browser_y + 40], fill=(200, 200, 200))
            draw.text((60, browser_y + 10), "模拟浏览器页面 - 失败截图", fill=(80, 80, 80), font=font_text)

            # 在浏览器窗口中绘制错误提示
            error_y = browser_y + 80
            draw.text((60, error_y), "× 元素定位失败或操作执行异常", fill=(220, 53, 69), font=font_text)
            draw.text((60, error_y + 40), "× 请检查元素定位器是否正确", fill=(220, 53, 69), font=font_text)
            draw.text((60, error_y + 80), "× 或页面加载是否完成", fill=(220, 53, 69), font=font_text)

            # 转换为base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            logger.error(f"生成失败截图时出错: {str(e)}")
            # 返回一个简单的错误占位符
            return None

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """运行单个测试用例 - 支持选择Playwright或Selenium执行引擎"""
        test_case = self.get_object()

        try:
            # 获取执行引擎选择，默认使用playwright
            engine_type = request.data.get('engine', 'playwright')

            # 创建执行记录
            execution = TestCaseExecution.objects.create(
                test_case=test_case,
                project=test_case.project,
                execution_source='manual',
                status='running',
                engine=engine_type,
                browser=request.data.get('browser', 'chrome'),
                headless=request.data.get('headless', False),
                created_by=request.user,
                started_at=timezone.now()
            )

            # 根据引擎类型导入对应的执行引擎
            if engine_type == 'selenium':
                from .selenium_engine import SeleniumTestEngine

                # Selenium 引擎需要预先检查浏览器和驱动是否可用
                browser_type = request.data.get('browser', 'chrome')
                is_ready, error_msg = SeleniumTestEngine.check_execution_environment(browser_type)
                if not is_ready:
                    # 浏览器环境不可用，立即返回错误
                    logger.error(f"Selenium 执行环境检查失败: {error_msg}")
                    execution.status = 'failed'
                    execution.error_message = error_msg
                    execution.execution_logs = (
                        f"浏览器环境检查失败\n\n{error_msg}\n\n建议：\n"
                        f"1. 请确认已安装 {browser_type.capitalize()} 浏览器\n"
                        f"2. 执行 `python manage.py download_webdrivers --browsers {browser_type}` 安装对应驱动\n"
                        f"3. 或者尝试使用其他浏览器（Chrome、Firefox、Edge）\n"
                        f"4. 或者使用 Playwright 引擎（支持自动下载浏览器）"
                    )
                    execution.finished_at = timezone.now()
                    execution.save()

                    return Response({
                        'success': False,
                        'logs': execution.execution_logs,
                        'screenshots': [],
                        'execution_time': 0,
                        'errors': [{
                            'message': f'{browser_type.capitalize()} 浏览器执行环境不可用',
                            'details': error_msg,
                            'step_number': None,
                            'action_type': '浏览器检查',
                            'element': '',
                            'description': '执行前浏览器与驱动环境检查'
                        }]
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                import asyncio
                import threading
                from .playwright_engine import PlaywrightTestEngine

                browser_type = request.data.get('browser', 'chrome')
                is_ready, error_msg = PlaywrightTestEngine.check_execution_environment_sync(browser_type)
                if not is_ready:
                    logger.error(f"Playwright 执行环境检查失败: {error_msg}")
                    execution.status = 'failed'
                    execution.error_message = error_msg
                    execution.execution_logs = (
                        f"Playwright 浏览器环境检查失败\n\n{error_msg}\n\n建议：\n"
                        f"1. 执行 `python -m playwright install` 或 `python -m playwright install {PlaywrightTestEngine.normalize_browser_type(browser_type)}` 安装浏览器\n"
                        f"2. 如果 Playwright 模块未安装，请先执行 `pip install playwright`\n"
                        f"3. 或者切换到 Selenium 引擎并安装对应浏览器驱动"
                    )
                    execution.finished_at = timezone.now()
                    execution.save()

                    return Response({
                        'success': False,
                        'logs': execution.execution_logs,
                        'screenshots': [],
                        'execution_time': 0,
                        'errors': [{
                            'message': f'{browser_type.capitalize()} Playwright 执行环境不可用',
                            'details': error_msg,
                            'step_number': None,
                            'action_type': '浏览器检查',
                            'element': '',
                            'description': '执行前 Playwright 浏览器环境检查'
                        }]
                    }, status=status.HTTP_400_BAD_REQUEST)

            start_time = time.time()

            # 获取测试用例的所有步骤（跳过清理步骤）
            test_steps = list(test_case.steps.filter(is_cleanup=False).all().order_by('step_number'))

            # 预先获取所有步骤的数据,避免在异步上下文中访问ORM
            steps_data = []
            for step in test_steps:
                step_data = {
                    'step': step,
                    'action_type': step.action_type,
                    'description': step.description,
                    'input_value': step.input_value,
                    'wait_time': step.wait_time,
                    'action_wait': step.action_wait,
                    'assert_type': step.assert_type,
                    'assert_value': step.assert_value,
                    'output_var': step.output_var,
                }

                # 获取元素数据
                if step.element:
                    step_data['element_data'] = {
                        'locator_strategy': step.element.locator_strategy.name if step.element.locator_strategy else 'css',
                        'locator_value': step.element.locator_value,
                        'name': step.element.name,
                        'wait_timeout': step.element.wait_timeout,  # 添加元素的等待超时设置（秒）
                        'force_action': step.element.force_action  # 添加强制操作选项
                    }
                else:
                    step_data['element_data'] = None

                steps_data.append(step_data)

            # 预取前置条件数据（避免在异步上下文中访问Django ORM触发SynchronousOnlyOperation）
            from .models import TestCasePrecondition
            preconditions_data = []
            precondition_rels = TestCasePrecondition.objects.filter(
                test_case=test_case
            ).select_related('precondition').order_by('order')
            for rel in precondition_rels:
                pre_case = rel.precondition
                pre_steps_qs = pre_case.steps.filter(is_cleanup=False).select_related('element__locator_strategy').order_by('step_number')
                pre_steps_list = []
                for ps in pre_steps_qs:
                    psd = {
                        'step_number': ps.step_number,
                        'action_type': ps.action_type,
                        'description': ps.description,
                        'input_value': ps.input_value,
                        'wait_time': ps.wait_time,
                        'action_wait': ps.action_wait,
                        'assert_type': ps.assert_type,
                        'assert_value': ps.assert_value,
                        'output_var': ps.output_var or '',
                    }
                    if ps.element:
                        psd['element_data'] = {
                            'locator_strategy': ps.element.locator_strategy.name if ps.element.locator_strategy else 'css',
                            'locator_value': ps.element.locator_value,
                            'name': ps.element.name,
                            'wait_timeout': ps.element.wait_timeout,
                            'force_action': ps.element.force_action
                        }
                    else:
                        psd['element_data'] = None
                    pre_steps_list.append(psd)
                preconditions_data.append({
                    'id': pre_case.id,
                    'name': pre_case.name,
                    'steps': pre_steps_list,
                })

            # 存储步骤执行结果（用于JSON格式的execution_logs）
            step_results = []

            # 生成执行日志（保留文本格式用于调试）
            execution_logs = []
            execution_logs.append(f"测试用例 '{test_case.name}' 开始执行")
            execution_logs.append(f"执行时间: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
            execution_logs.append(f"执行引擎: {engine_type.upper()}")
            execution_logs.append(f"浏览器: {request.data.get('browser', 'chrome').capitalize()}")
            headless_mode = request.data.get('headless', False)
            mode_text = "无头模式" if headless_mode else "有头模式"
            execution_logs.append(f"执行模式: {mode_text}")
            execution_logs.append(f"执行用户: {request.user.username}")
            execution_logs.append(f"项目基础URL: {test_case.project.base_url}")
            execution_logs.append("")

            # 截图列表
            screenshots = []
            # 详细错误信息列表
            detailed_errors = []
            execution_result = {'status': 'passed', 'error_message': None}

            # 根据引擎类型选择执行方式
            if engine_type == 'selenium':
                # Selenium同步执行
                def run_test_selenium():
                    """使用Selenium执行测试"""
                    browser_type = request.data.get('browser', 'chrome')
                    headless = request.data.get('headless', False)

                    # 创建Selenium引擎实例
                    engine = SeleniumTestEngine(browser_type=browser_type, headless=headless)

                    try:
                        # 启动浏览器
                        execution_logs.append("========== 初始化浏览器 ==========")
                        try:
                            engine.start()
                            mode_text = "无头模式" if headless else "有头模式"
                            execution_logs.append(
                                f"✓ {browser_type.capitalize()} 浏览器启动成功 (Selenium, {mode_text})")
                            execution_logs.append("")
                        except Exception as browser_error:
                            # 浏览器启动失败
                            execution_logs.append(f"✗ {browser_type.capitalize()} 浏览器启动失败")
                            execution_logs.append(f"  错误: {str(browser_error)}")
                            execution_logs.append("")
                            execution_result['status'] = 'failed'
                            execution_result[
                                'error_message'] = f"{browser_type.capitalize()} 浏览器启动失败: {str(browser_error)}"

                            # 添加详细错误信息
                            detailed_errors.append({
                                'step_number': None,
                                'action_type': '浏览器启动',
                                'element': '',
                                'message': f"{browser_type.capitalize()} 浏览器启动失败",
                                'details': str(browser_error),
                                'description': '执行前浏览器启动检查'
                            })

                            return False

                        # 导航到项目基础URL
                        if test_case.project.base_url:
                            execution_logs.append("========== 导航到测试页面 ==========")
                            success, nav_log = engine.navigate(test_case.project.base_url)
                            execution_logs.append(nav_log)
                            execution_logs.append("")

                            if not success:
                                execution_result['status'] = 'failed'
                                execution_result['error_message'] = "导航到测试页面失败"
                                return False

                        if steps_data:
                            execution_logs.append("========== 执行测试步骤 ==========")
                            step_count = len(steps_data)
                            execution_logs.append(f"共有 {step_count} 个步骤需要执行")
                            execution_logs.append("")

                            for i, step_info in enumerate(steps_data, 1):
                                execution_logs.append(f"========== 开始执行步骤 {i}/{step_count} ==========")
                                execution_logs.append(f"步骤 {i}/{step_count}:")

                                step = step_info['step']
                                action_type = step_info['action_type']
                                description = step_info['description']
                                element_data = step_info['element_data']

                                action_choices_dict = dict(TestCaseStep.ACTION_TYPE_CHOICES)
                                action_type_text = action_choices_dict.get(action_type, action_type)
                                execution_logs.append(f"  操作: {action_type_text}")

                                if description:
                                    execution_logs.append(f"  说明: {description}")

                                if element_data:
                                    execution_logs.append(f"  元素: {element_data['name']}")
                                    execution_logs.append(
                                        f"  定位器: {element_data['locator_strategy']}={element_data['locator_value']}")
                                else:
                                    execution_logs.append(f"  (此步骤不需要元素)")

                                try:
                                    success, step_log, screenshot_base64 = engine.execute_step(step, element_data or {})
                                    execution_logs.append(f"  {step_log}")
                                    execution_logs.append("")

                                    # 记录步骤执行结果（用于JSON格式）
                                    step_results.append({
                                        'step_number': i,
                                        'action_type': action_type,
                                        'description': description or '',
                                        'success': success,
                                        'error': None if success else step_log
                                    })

                                    # action_wait: 步骤操作成功后等待指定秒数再执行下一步
                                    if success and getattr(step, 'action_wait', 0) and step.action_wait > 0:
                                        execution_logs.append(f"  ⏱️  操作后等待 {step.action_wait} 秒 (action_wait)")
                                        time.sleep(step.action_wait)

                                    if not success:
                                        logger.info(f"[调试-Selenium] 步骤 {i} 执行失败，设置状态为 failed")
                                        execution_result['status'] = 'failed'
                                        element_info = element_data['name'] if element_data else "未知元素"
                                        execution_result['error_message'] = step_log  # 使用step_log作为错误信息
                                        logger.info(f"[调试-Selenium] execution_result = {execution_result}")

                                        detailed_errors.append({
                                            'step_number': i,
                                            'action_type': action_type_text,
                                            'element': element_info,
                                            'message': f"步骤 {i}/{step_count} 执行失败",
                                            'details': step_log,
                                            'description': description or ''
                                        })

                                        if not screenshot_base64:
                                            screenshot_base64 = engine.capture_screenshot()

                                        if screenshot_base64:
                                            screenshots.append({
                                                'url': screenshot_base64,
                                                'description': f'步骤 {i} 失败截图: {description or action_type_text}',
                                                'step_number': i,
                                                'timestamp': timezone.now().isoformat()
                                                # 移除 loaded 和 error 字段，让前端自行处理
                                            })
                                            execution_logs.append(f"  📸 失败截图已捕获")

                                        return False

                                    if action_type == 'screenshot' and screenshot_base64:
                                        screenshots.append({
                                            'url': screenshot_base64,
                                            'description': f'步骤 {i}: {description or "手动截图"}',
                                            'step_number': i,
                                            'timestamp': timezone.now().isoformat()
                                            # 移除 loaded 和 error 字段，让前端自行处理
                                        })

                                except Exception as e:
                                    execution_logs.append(f"  ✗ 步骤执行异常: {str(e)}")
                                    import traceback
                                    tb_str = traceback.format_exc()
                                    execution_logs.append(f"  [调试] 异常堆栈:\n{tb_str}")

                                    # 记录步骤执行结果（异常情况）
                                    step_results.append({
                                        'step_number': i,
                                        'action_type': action_type,
                                        'description': description or '',
                                        'success': False,
                                        'error': str(e)
                                    })

                                    execution_result['status'] = 'failed'
                                    execution_result['error_message'] = f"步骤 {i} 执行异常: {str(e)}"

                                    element_info = element_data['name'] if element_data else "未知元素"
                                    detailed_errors.append({
                                        'step_number': i,
                                        'action_type': action_type_text,
                                        'element': element_info,
                                        'message': f"步骤 {i}/{step_count} 执行异常",
                                        'details': f"异常: {str(e)}\n\n堆栈跟踪:\n{tb_str}",
                                        'description': description or ''
                                    })

                                    try:
                                        screenshot_base64 = engine.capture_screenshot()
                                        if screenshot_base64:
                                            screenshots.append({
                                                'url': screenshot_base64,
                                                'description': f'步骤 {i} 异常截图: {str(e)}',
                                                'step_number': i,
                                                'timestamp': timezone.now().isoformat()
                                                # 移除 loaded 和 error 字段，让前端自行处理
                                            })
                                    except:
                                        pass

                                    return False

                            execution_logs.append(f"========== 执行完成 ({step_count} 个步骤全部通过) ==========")
                            return True
                        else:
                            execution_logs.append("警告: 测试用例没有定义任何步骤")
                            return True

                    finally:
                        execution_logs.append("")
                        execution_logs.append("========== 清理资源 ==========")
                        engine.stop()
                        execution_logs.append("✓ 浏览器已关闭")

                # 在独立线程中运行Selenium测试
                import threading
                test_thread = threading.Thread(target=run_test_selenium)
                test_thread.start()
                test_thread.join()

            else:
                # Playwright异步执行
                def run_test_in_thread():
                    """在独立线程中运行异步测试"""

                    async def run_test():
                        """异步执行测试"""
                        # 用例级变量表，存储步骤输出变量
                        context_variables = {}

                        # 根据浏览器类型选择
                        browser_map = {
                            'chrome': 'chromium',
                            'firefox': 'firefox',
                            'safari': 'webkit',
                            'edge': 'chromium'
                        }
                        browser_type = browser_map.get(request.data.get('browser', 'chrome'), 'chromium')
                        headless = request.data.get('headless', False)

                        # 创建Playwright引擎实例
                        engine = PlaywrightTestEngine(browser_type=browser_type, headless=headless, base_url=test_case.project.base_url)

                        try:
                            # 启动浏览器
                            execution_logs.append("========== 初始化浏览器 ==========")
                            await engine.start()
                            mode_text = "无头模式" if headless else "有头模式"
                            execution_logs.append(
                                f"✓ {browser_type.capitalize()} 浏览器启动成功 (Playwright, {mode_text})")
                            execution_logs.append("")

                            # 导航到项目基础URL
                            if test_case.project.base_url:
                                execution_logs.append("========== 导航到测试页面 ==========")
                                success, nav_log = await engine.navigate(test_case.project.base_url)
                                execution_logs.append(nav_log)
                                execution_logs.append("")

                                if not success:
                                    execution_result['status'] = 'failed'
                                    execution_result['error_message'] = "导航到测试页面失败"
                                    return False

                            if steps_data:
                                # 执行前置条件（单条用例执行时，使用预取数据避免异步上下文中的ORM访问）
                                if preconditions_data:
                                    execution_logs.append("========== 执行前置条件 ==========")
                                    for pre_cond in preconditions_data:
                                        pre_case_name = pre_cond['name']
                                        execution_logs.append(f"执行前置用例: {pre_case_name}")
                                        pre_steps_data = pre_cond['steps']

                                        # 同引擎执行前置用例步骤
                                        pre_passed = True
                                        for psi, ps_info in enumerate(pre_steps_data, 1):
                                            try:
                                                # 使用预取的step字段数据构造一个简单的step-like对象
                                                # 避免在异步上下文中访问ORM对象
                                                from types import SimpleNamespace
                                                ps_obj = SimpleNamespace(
                                                    action_type=ps_info['action_type'],
                                                    input_value=ps_info.get('input_value', ''),
                                                    wait_time=ps_info.get('wait_time', 1000),
                                                    action_wait=ps_info.get('action_wait', 0),
                                                    assert_type=ps_info.get('assert_type', ''),
                                                    assert_value=ps_info.get('assert_value', ''),
                                                    output_var=ps_info.get('output_var', ''),
                                                )
                                                ps_success, ps_log, ps_screenshot = await engine.execute_step(
                                                    ps_obj,
                                                    ps_info.get('element_data') or {},
                                                    context_variables
                                                )
                                                if not ps_success:
                                                    pre_passed = False
                                                    execution_logs.append(f"  ✗ 前置步骤 {psi} 失败: {ps_log}")
                                                    break
                                                else:
                                                    execution_logs.append(f"  ✓ 前置步骤 {psi}: {ps_log.split(chr(10))[0]}")
                                            except Exception as e:
                                                pre_passed = False
                                                execution_logs.append(f"  ✗ 前置步骤 {psi} 异常: {str(e)}")
                                                break

                                        if not pre_passed:
                                            execution_result['status'] = 'failed'
                                            execution_result['error_message'] = f"前置用例「{pre_case_name}」执行失败"
                                            execution_logs.append(f"✗ 前置条件失败，跳过当前用例")
                                            # 清理退出
                                            try:
                                                if not headless:
                                                    try:
                                                        await engine.page.wait_for_load_state('networkidle', timeout=5000)
                                                    except:
                                                        pass
                                                    import asyncio
                                                    await asyncio.sleep(1)
                                                await engine.stop()
                                            except:
                                                pass
                                            return False
                                        execution_logs.append(f"✓ 前置用例「{pre_case_name}」执行通过")
                                    execution_logs.append("")

                                    # 前置条件执行完后，等待页面稳定再开始主用例步骤
                                    try:
                                        await engine.page.wait_for_load_state('networkidle', timeout=10000)
                                    except:
                                        pass
                                    await engine.page.wait_for_timeout(2000)
                                    execution_logs.append("✓ 前置条件执行完毕，页面已稳定")

                                execution_logs.append("========== 执行测试步骤 ==========")
                                step_count = len(steps_data)
                                execution_logs.append(f"共有 {step_count} 个步骤需要执行")
                                execution_logs.append("")

                                for i, step_info in enumerate(steps_data, 1):
                                    execution_logs.append(f"========== 开始执行步骤 {i}/{step_count} ==========")
                                    execution_logs.append(f"步骤 {i}/{step_count}:")

                                    # 从预先获取的数据中获取信息
                                    step = step_info['step']
                                    action_type = step_info['action_type']
                                    description = step_info['description']
                                    element_data = step_info['element_data']

                                    # 获取操作类型的中文显示
                                    action_choices_dict = dict(TestCaseStep.ACTION_TYPE_CHOICES)
                                    action_type_text = action_choices_dict.get(action_type, action_type)
                                    execution_logs.append(f"  操作: {action_type_text}")

                                    if description:
                                        execution_logs.append(f"  说明: {description}")

                                    if element_data:
                                        execution_logs.append(f"  元素: {element_data['name']}")
                                        execution_logs.append(
                                            f"  定位器: {element_data['locator_strategy']}={element_data['locator_value']}")
                                    else:
                                        execution_logs.append(f"  (此步骤不需要元素)")

                                    # 执行步骤
                                    try:
                                        execution_logs.append(f"  [调试] 准备执行步骤...")
                                        success, step_log, screenshot_base64 = await engine.execute_step(step,
                                                                                                           element_data or {},
                                                                                                           context_variables)
                                        execution_logs.append(f"  [调试] 步骤执行完成, success={success}")

                                        execution_logs.append(f"  {step_log}")
                                        execution_logs.append("")

                                        # 记录步骤执行结果（用于JSON格式）
                                        step_results.append({
                                            'step_number': i,
                                            'action_type': action_type,
                                            'description': description or '',
                                            'success': success,
                                            'error': None if success else step_log
                                        })

                                        # action_wait: 步骤操作成功后等待指定秒数再执行下一步
                                        if success and getattr(step, 'action_wait', 0) and step.action_wait > 0:
                                            execution_logs.append(f"  ⏱️  操作后等待 {step.action_wait} 秒 (action_wait)")
                                            await asyncio.sleep(step.action_wait)

                                        # 如果步骤失败,保存截图
                                        if not success:
                                            execution_logs.append(f"  [调试] 检测到步骤失败,准备处理...")
                                            execution_result['status'] = 'failed'

                                            # 获取失败的元素信息
                                            element_info = element_data['name'] if element_data else "未知元素"

                                            execution_result['error_message'] = step_log  # 使用step_log作为错误信息

                                            # 添加详细错误信息
                                            detailed_errors.append({
                                                'step_number': i,
                                                'action_type': action_type_text,
                                                'element': element_info,
                                                'message': f"步骤 {i}/{step_count} 执行失败",
                                                'details': step_log,  # 包含详细的错误日志
                                                'description': description or ''
                                            })

                                            # 如果没有截图,捕获一张
                                            if not screenshot_base64:
                                                screenshot_base64 = await engine.capture_screenshot()

                                        if screenshot_base64:
                                            screenshots.append({
                                                'url': screenshot_base64,
                                                'description': f'步骤 {i} 失败截图: {description or action_type_text}',
                                                'step_number': i,
                                                'timestamp': timezone.now().isoformat()
                                                # 移除 loaded 和 error 字段，让前端自行处理
                                            })
                                            execution_logs.append(f"  📸 失败截图已捕获")

                                            execution_logs.append(f"  [调试] 步骤失败,准备退出执行...")
                                            return False

                                        # 如果是截图步骤且成功,也保存截图
                                        if action_type == 'screenshot' and screenshot_base64:
                                            screenshots.append({
                                                'url': screenshot_base64,
                                                'description': f'步骤 {i}: {description or "手动截图"}',
                                                'step_number': i,
                                                'timestamp': timezone.now().isoformat()
                                                # 移除 loaded 和 error 字段，让前端自行处理
                                            })

                                        execution_logs.append(f"  [调试] 步骤 {i} 成功完成,准备执行下一步...")

                                    except Exception as e:
                                        execution_logs.append(f"  ✗ 步骤执行异常: {str(e)}")
                                        execution_logs.append(f"  [调试] 异常详情: {repr(e)}")
                                        import traceback
                                        tb_str = traceback.format_exc()
                                        execution_logs.append(f"  [调试] 异常堆栈:\n{tb_str}")

                                        # 记录步骤执行结果（异常情况）
                                        step_results.append({
                                            'step_number': i,
                                            'action_type': action_type,
                                            'description': description or '',
                                            'success': False,
                                            'error': str(e)
                                        })

                                        execution_result['status'] = 'failed'
                                        execution_result['error_message'] = f"步骤 {i} 执行异常: {str(e)}"

                                        # 添加详细错误信息
                                        element_info = element_data['name'] if element_data else "未知元素"
                                        detailed_errors.append({
                                            'step_number': i,
                                            'action_type': action_type_text,
                                            'element': element_info,
                                            'message': f"步骤 {i}/{step_count} 执行异常",
                                            'details': f"异常: {str(e)}\n\n堆栈跟踪:\n{tb_str}",
                                            'description': description or ''
                                        })

                                        # 捕获异常截图
                                        try:
                                            screenshot_base64 = await engine.capture_screenshot()
                                            if screenshot_base64:
                                                screenshots.append({
                                                    'url': screenshot_base64,
                                                    'description': f'步骤 {i} 异常截图: {str(e)}',
                                                    'step_number': i,
                                                    'timestamp': timezone.now().isoformat()
                                                    # 移除 loaded 和 error 字段，让前端自行处理
                                                })
                                        except:
                                            pass

                                        execution_logs.append(f"  [调试] 发生异常,准备退出执行...")
                                        return False

                                # 所有步骤都成功
                                execution_logs.append(f"========== 执行完成 ({step_count} 个步骤全部通过) ==========")

                                # 执行后置条件SQL（清理数据）
                                if test_case.postcondition_sql and test_case.postcondition_sql.strip():
                                    execution_logs.append("")
                                    execution_logs.append("========== 执行后置条件SQL ==========")
                                    try:
                                        from .variable_resolver import resolve_variables
                                        resolved_sql = resolve_variables(test_case.postcondition_sql, context_variables)
                                        execution_logs.append(f"  清理SQL: {resolved_sql[:200]}")

                                        # 获取项目的数据库连接配置
                                        project = test_case.project
                                        if project.target_db_engine:
                                            import sqlalchemy
                                            db_url = None
                                            if project.target_db_engine == 'mysql':
                                                db_url = f"mysql+pymysql://{project.target_db_user}:{project.target_db_password}@{project.target_db_host}:{project.target_db_port}/{project.target_db_name}"
                                            elif project.target_db_engine == 'postgresql':
                                                db_url = f"postgresql+psycopg2://{project.target_db_user}:{project.target_db_password}@{project.target_db_host}:{project.target_db_port}/{project.target_db_name}"
                                            elif project.target_db_engine == 'sqlite':
                                                db_url = f"sqlite:///{project.target_db_name}"
                                            elif project.target_db_engine == 'oracle':
                                                db_url = f"oracle+cx_oracle://{project.target_db_user}:{project.target_db_password}@{project.target_db_host}:{project.target_db_port}/{project.target_db_name}"

                                            if db_url:
                                                engine_db = sqlalchemy.create_engine(db_url)
                                                with engine_db.connect() as conn:
                                                    # 分割多条SQL语句
                                                    sql_statements = [s.strip() for s in resolved_sql.split(';') if s.strip()]
                                                    total_affected = 0
                                                    for sql_stmt in sql_statements:
                                                        # 安全检查：只允许 DELETE/UPDATE/TRUNCATE
                                                        sql_upper = sql_stmt.strip().upper()
                                                        if not any(sql_upper.startswith(kw) for kw in ['DELETE', 'UPDATE', 'TRUNCATE']):
                                                            execution_logs.append(f"  ✗ 跳过不安全的SQL: {sql_stmt[:50]}...")
                                                            continue
                                                        result = conn.execute(sqlalchemy.text(sql_stmt))
                                                        conn.commit()
                                                        affected = result.rowcount
                                                        total_affected += affected
                                                        execution_logs.append(f"  ✓ 执行: {sql_stmt[:80]}... (影响 {affected} 行)")
                                                engine_db.dispose()
                                                execution_logs.append(f"✓ 后置条件SQL执行完成，共影响 {total_affected} 行")
                                            else:
                                                execution_logs.append(f"  ✗ 不支持的数据库类型: {project.target_db_engine}")
                                        else:
                                            execution_logs.append("  ⚠ 未配置项目数据库连接，跳过后置条件SQL执行")
                                    except Exception as e:
                                        execution_logs.append(f"  ✗ 后置条件SQL执行失败: {str(e)}")
                                        # 后置条件失败不影响用例结果

                                return True

                            else:
                                execution_logs.append("警告: 测试用例没有定义任何步骤")
                                return True

                        finally:
                            # 关闭浏览器
                            execution_logs.append("")
                            execution_logs.append("========== 清理资源 ==========")
                            await engine.stop()
                            execution_logs.append("✓ 浏览器已关闭")

                    # 在新的事件循环中运行测试
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(run_test())
                    except Exception as thread_exc:
                        # 捕获异步测试中未处理的异常，避免线程静默失败
                        logger.error(f"[Playwright执行线程异常] {str(thread_exc)}", exc_info=True)
                        execution_logs.append(f"✗ 执行过程发生异常: {str(thread_exc)}")
                        execution_result['status'] = 'failed'
                        execution_result['error_message'] = f"执行过程发生异常: {str(thread_exc)}"
                    finally:
                        loop.close()

                # 在独立线程中运行Playwright测试
                import threading
                test_thread = threading.Thread(target=run_test_in_thread)
                test_thread.start()
                test_thread.join()  # 等待测试完成

            # 计算总执行时间
            total_time = round(time.time() - start_time, 2)
            execution_logs.append("")
            execution_logs.append("执行环境信息:")
            execution_logs.append(f"- 执行引擎: {engine_type.upper()}")
            execution_logs.append(f"- 浏览器: {request.data.get('browser', 'chrome').capitalize()}")
            execution_logs.append(f"- 屏幕分辨率: 1920x1080")
            execution_logs.append(f"- 总执行时间: {total_time}秒")

            if screenshots:
                execution_logs.append(f"- 截图数量: {len(screenshots)} 张")

            # 保存执行日志和截图
            logger.info(f"[调试] 准备保存执行结果: execution_result['status'] = {execution_result['status']}")
            execution.status = execution_result['status']

            # 保存error_message（step_log已经是简洁的错误信息）
            execution.error_message = execution_result['error_message'] or ''

            # 保存步骤执行结果为JSON格式
            execution.execution_logs = json.dumps(step_results, ensure_ascii=False)
            execution.execution_time = total_time
            execution.finished_at = timezone.now()
            execution.screenshots = screenshots
            execution.save()
            logger.info(f"[调试] 执行结果已保存: execution.status = {execution.status}")

            serializer = TestCaseExecutionSerializer(execution)
            # 格式化错误信息为统一的对象格式
            errors = []
            if detailed_errors:
                # 使用详细的错误信息
                for error in detailed_errors:
                    errors.append({
                        'message': error['message'],
                        'details': error['details'],
                        'step_number': error['step_number'],
                        'action_type': error['action_type'],
                        'element': error['element'],
                        'description': error['description']
                    })
            elif execution.error_message:
                # 如果没有详细错误信息，使用简单格式
                errors.append({
                    'message': execution.error_message,
                    'details': ''
                })

            # 记录运行操作
            log_operation('run', 'test_case', test_case.id, test_case.name, request.user)

            return Response({
                'success': execution.status == 'passed',
                'logs': execution.execution_logs,
                'screenshots': screenshots,
                'execution_time': execution.execution_time,
                'errors': errors
            })

        except Exception as e:
            logger.error(f"执行测试用例失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'logs': f"执行失败: {str(e)}\n\n{traceback.format_exc()}",
                'screenshots': [],
                'execution_time': 0,
                'errors': [{'message': str(e), 'stack': traceback.format_exc()}]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def batch_run(self, request):
        """批量运行测试用例"""
        test_case_ids = request.data.get('test_case_ids', [])
        project_id = request.data.get('project_id')

        if not test_case_ids:
            return Response({'error': '请选择要运行的测试用例'}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        for test_case_id in test_case_ids:
            try:
                test_case = TestCase.objects.get(id=test_case_id)
                # 这里调用单个运行逻辑
                # 简化处理，实际应该异步执行
                results.append({
                    'test_case_id': test_case_id,
                    'test_case_name': test_case.name,
                    'status': 'passed'
                })
            except TestCase.DoesNotExist:
                results.append({
                    'test_case_id': test_case_id,
                    'test_case_name': '未知',
                    'status': 'error',
                    'error': '测试用例不存在'
                })

        return Response({'results': results})

    def perform_destroy(self, instance):
        # 记录操作（在删除前记录）
        log_operation('delete', 'test_case', instance.id, instance.name, self.request.user)
        instance.delete()


class TestCaseStepViewSet(viewsets.ModelViewSet):
    """测试用例步骤视图集"""
    queryset = TestCaseStep.objects.all()
    serializer_class = TestCaseStepSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['step_number']
    ordering = ['step_number']
    filterset_fields = ['test_case', 'action_type']

    def get_queryset(self):
        # 只显示用户有权限访问的测试用例的步骤
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        accessible_test_cases = TestCase.objects.filter(project__in=accessible_projects)
        return TestCaseStep.objects.filter(test_case__in=accessible_projects)


class TestCaseExecutionViewSet(viewsets.ModelViewSet):
    """测试用例执行记录视图集"""
    queryset = TestCaseExecution.objects.all().select_related(
        'test_case', 'project', 'test_suite', 'executed_by'
    )
    serializer_class = TestCaseExecutionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['test_case__name', 'error_message']
    ordering_fields = ['created_at', 'started_at', 'finished_at', 'status']
    ordering = ['-created_at']
    filterset_fields = ['project', 'test_suite', 'test_case', 'status', 'execution_source']
    pagination_class = StandardPagination

    def get_queryset(self):
        # 只显示用户有权限访问的项目的执行记录
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        return TestCaseExecution.objects.filter(
            project__in=accessible_projects
        ).select_related(
            'test_case', 'project', 'test_suite', 'created_by'
        )

    def perform_destroy(self, instance):
        # 记录操作
        name = instance.test_case.name if instance.test_case else f"执行记录#{instance.id}"
        log_operation('delete', 'report', instance.id, name, self.request.user)
        instance.delete()

    @action(detail=False, methods=['post'], url_path='batch-delete')
    def batch_delete(self, request):
        """批量删除执行记录"""
        try:
            ids = request.data.get('ids', [])

            # 验证ids参数
            if not ids:
                return Response({'error': '未提供要删除的记录ID'}, status=status.HTTP_400_BAD_REQUEST)

            # 确保ids是列表
            if not isinstance(ids, list):
                return Response({'error': 'ids参数格式错误，应为数组'}, status=status.HTTP_400_BAD_REQUEST)

            # 确保只能删除有权限的记录
            queryset = self.get_queryset()
            records_to_delete = queryset.filter(id__in=ids)

            # 检查是否有记录可删除
            if not records_to_delete.exists():
                return Response({'error': '未找到可删除的记录或没有权限删除'}, status=status.HTTP_404_NOT_FOUND)

            # 获取可删除记录的ID列表，避免对带select_related的queryset调用delete()可能出现的问题
            deletable_ids = list(records_to_delete.values_list('id', flat=True))

            # 使用ID列表直接删除
            deleted_count = TestCaseExecution.objects.filter(id__in=deletable_ids).delete()[0]

            return Response({'message': f'成功删除 {deleted_count} 条记录', 'deleted_count': deleted_count})
        except Exception as e:
            logger.error(f"批量删除测试用例执行记录失败: {str(e)}", exc_info=True)
            return Response({'error': f'批量删除失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OperationRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """操作记录视图集（只读）"""
    queryset = OperationRecord.objects.all()
    serializer_class = OperationRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['operation_type', 'resource_type', 'user']

    def get_queryset(self):
        # 返回最近的操作记录，按创建时间倒序
        # 过滤掉AI智能模式相关的操作记录
        queryset = OperationRecord.objects.exclude(
            resource_type__in=['ai_case', 'ai_execution']
        ).order_by('-created_at')

        # 支持通过查询参数限制返回数量
        limit = self.request.query_params.get('limit', None)
        if limit:
            try:
                limit = int(limit)
                queryset = queryset[:limit]
            except ValueError:
                pass

        return queryset


# ==================== 定时任务和通知相关视图 ====================

class UiScheduledTaskViewSet(viewsets.ModelViewSet):
    """UI定时任务视图集"""
    queryset = UiScheduledTask.objects.all()
    serializer_class = UiScheduledTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['task_type', 'status', 'trigger_type', 'project']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'next_run_time', 'last_run_time']
    ordering = ['-created_at']

    def get_queryset(self):
        """只显示用户有权限访问的项目的定时任务"""
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        return UiScheduledTask.objects.filter(project__in=accessible_projects)

    def perform_create(self, serializer):
        """创建定时任务"""
        instance = serializer.save(created_by=self.request.user)
        log_operation('create', 'scheduled_task', instance.id, instance.name, self.request.user)

    def perform_update(self, serializer):
        """更新定时任务"""
        instance = serializer.save()
        log_operation('edit', 'scheduled_task', instance.id, instance.name, self.request.user)

    def perform_destroy(self, instance):
        """删除定时任务"""
        log_operation('delete', 'scheduled_task', instance.id, instance.name, self.request.user)
        instance.delete()

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """暂停定时任务"""
        task = self.get_object()
        task.status = 'PAUSED'
        task.save()
        return Response({'message': '任务已暂停', 'status': task.status})

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """恢复定时任务"""
        task = self.get_object()
        task.status = 'ACTIVE'
        task.next_run_time = task.calculate_next_run()
        task.save()
        return Response({'message': '任务已恢复', 'status': task.status})

    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """立即运行任务"""
        task = self.get_object()

        try:
            # 更新任务执行时间和次数
            task.last_run_time = timezone.now()
            task.total_runs += 1
            # 重新计算下次运行时间
            task.next_run_time = task.calculate_next_run()
            task.save()

            # 根据任务类型执行不同的逻辑
            if task.task_type == 'TEST_SUITE':
                # 执行测试套件
                if not task.test_suite:
                    return Response({
                        'error': '该任务未配置测试套件'
                    }, status=status.HTTP_400_BAD_REQUEST)

                test_suite = task.test_suite
                test_case_count = test_suite.suite_test_cases.count()

                if test_case_count == 0:
                    return Response({
                        'error': '该测试套件未包含任何测试用例，无法执行'
                    }, status=status.HTTP_400_BAD_REQUEST)

                if task.engine == 'playwright':
                    from .playwright_engine import PlaywrightTestEngine
                    is_ready, error_msg = PlaywrightTestEngine.check_execution_environment_sync(task.browser)
                    if not is_ready:
                        return Response({
                            'error': error_msg,
                            'message': 'Playwright 浏览器未就绪，请先安装后再执行测试套件任务'
                        }, status=status.HTTP_400_BAD_REQUEST)

                # 更新套件执行状态
                test_suite.execution_status = 'running'
                test_suite.save()

                # 在后台线程中执行测试
                import threading
                from .test_executor import TestExecutor

                def run_test():
                    try:
                        executor = TestExecutor(
                            test_suite=test_suite,
                            engine=task.engine,
                            browser=task.browser,
                            headless=task.headless,
                            executed_by=task.created_by
                        )
                        executor.run()

                        # 更新任务执行结果
                        task.successful_runs += 1
                        task.last_result = {'status': 'success', 'message': '测试套件执行成功'}
                        task.error_message = ''
                        task.save()

                        # 发送成功通知
                        self._send_task_notification(task, success=True)

                    except Exception as e:
                        task.failed_runs += 1
                        task.last_result = {'status': 'failed', 'message': str(e)}
                        task.error_message = str(e)
                        test_suite.execution_status = 'failed'
                        test_suite.save()
                        task.save()

                        # 发送失败通知
                        self._send_task_notification(task, success=False)

                # 启动后台线程执行测试
                thread = threading.Thread(target=run_test)
                thread.daemon = True
                thread.start()

                log_operation('run', 'scheduled_task', task.id, task.name, request.user)

                return Response({
                    'message': '测试套件开始执行',
                    'task_id': task.id,
                    'task_name': task.name,
                    'test_suite': test_suite.name,
                    'test_case_count': test_case_count,
                    'engine': task.engine,
                    'browser': task.browser,
                    'headless': task.headless
                }, status=status.HTTP_200_OK)

            elif task.task_type == 'TEST_CASE':
                # 执行测试用例
                if not task.test_cases or len(task.test_cases) == 0:
                    return Response({
                        'error': '该任务未配置测试用例'
                    }, status=status.HTTP_400_BAD_REQUEST)

                test_case_ids = task.test_cases
                test_cases = TestCase.objects.filter(id__in=test_case_ids)
                test_case_count = test_cases.count()

                if test_case_count == 0:
                    return Response({
                        'error': '找不到配置的测试用例'
                    }, status=status.HTTP_400_BAD_REQUEST)

                if task.engine == 'playwright':
                    from .playwright_engine import PlaywrightTestEngine
                    is_ready, error_msg = PlaywrightTestEngine.check_execution_environment_sync(task.browser)
                    if not is_ready:
                        return Response({
                            'error': error_msg,
                            'message': 'Playwright 浏览器未就绪，请先安装后再执行测试用例任务'
                        }, status=status.HTTP_400_BAD_REQUEST)

                # 在后台线程中执行测试用例
                import threading

                def run_test_cases():
                    """在后台线程中执行测试用例"""
                    success_count = 0
                    failed_count = 0

                    try:
                        for test_case in test_cases:
                            # 创建执行记录
                            execution = TestCaseExecution.objects.create(
                                test_case=test_case,
                                project=task.project,
                                execution_source='scheduled',
                                status='running',
                                engine=task.engine,
                                browser=task.browser,
                                headless=task.headless,
                                created_by=task.created_by,
                                started_at=timezone.now()
                            )

                            # 实际执行测试用例
                            try:
                                logger.info(f"开始执行定时任务的测试用例: {test_case.name} (ID: {test_case.id})")

                                start_time = time.time()

                                # 获取测试用例的所有步骤
                                test_steps = list(test_case.steps.all().order_by('step_number'))

                                # 预先获取所有步骤的数据
                                steps_data = []
                                for step in test_steps:
                                    step_data = {
                                        'step': step,
                                        'action_type': step.action_type,
                                        'description': step.description,
                                        'input_value': step.input_value,
                                        'wait_time': step.wait_time,
                                        'assert_type': step.assert_type,
                                        'assert_value': step.assert_value,
                                        'output_var': step.output_var,
                                    }

                                    if step.element:
                                        step_data['element_data'] = {
                                            'locator_strategy': step.element.locator_strategy.name if step.element.locator_strategy else 'css',
                                            'locator_value': step.element.locator_value,
                                            'name': step.element.name,
                                            'wait_timeout': step.element.wait_timeout,
                                            'force_action': step.element.force_action
                                        }
                                    else:
                                        step_data['element_data'] = None

                                    steps_data.append(step_data)

                                # 存储步骤执行结果和截图
                                step_results = []
                                screenshots = []
                                execution_logs = []
                                execution_result = {'status': 'passed', 'error_message': None}

                                # 根据引擎类型执行
                                if task.engine == 'selenium':
                                    from .selenium_engine import SeleniumTestEngine

                                    # 检查浏览器和驱动是否可用
                                    is_ready, error_msg = SeleniumTestEngine.check_execution_environment(task.browser)
                                    if not is_ready:
                                        execution.status = 'failed'
                                        execution.error_message = error_msg
                                        execution.execution_logs = json.dumps([{
                                            'step_number': 0,
                                            'action_type': '浏览器检查',
                                            'description': '执行前浏览器与驱动环境检查',
                                            'success': False,
                                            'error': error_msg
                                        }], ensure_ascii=False)
                                        execution.finished_at = timezone.now()
                                        execution.save()
                                        failed_count += 1
                                        continue

                                    # 创建Selenium引擎实例并执行
                                    engine = SeleniumTestEngine(browser_type=task.browser, headless=task.headless)

                                    try:
                                        # 启动浏览器
                                        engine.start()
                                        execution_logs.append("✓ 浏览器启动成功")

                                        # 导航到项目基础URL
                                        if test_case.project.base_url:
                                            success, nav_log = engine.navigate(test_case.project.base_url)
                                            execution_logs.append(nav_log)
                                            if not success:
                                                execution_result['status'] = 'failed'
                                                execution_result['error_message'] = "导航到测试页面失败"
                                                raise Exception("导航到测试页面失败")

                                        # 执行测试步骤
                                        for i, step_info in enumerate(steps_data, 1):
                                            step = step_info['step']
                                            action_type = step_info['action_type']
                                            element_data = step_info['element_data']

                                            success, step_log, screenshot_base64 = engine.execute_step(step,
                                                                                                       element_data or {})

                                            step_results.append({
                                                'step_number': i,
                                                'action_type': action_type,
                                                'description': step_info['description'] or '',
                                                'success': success,
                                                'error': None if success else step_log
                                            })

                                            if not success:
                                                execution_result['status'] = 'failed'
                                                execution_result['error_message'] = step_log

                                                if not screenshot_base64:
                                                    screenshot_base64 = engine.capture_screenshot()

                                                if screenshot_base64:
                                                    screenshots.append({
                                                        'url': screenshot_base64,
                                                        'description': f'步骤 {i} 失败截图',
                                                        'step_number': i,
                                                        'timestamp': timezone.now().isoformat()
                                                    })

                                                break

                                            if action_type == 'screenshot' and screenshot_base64:
                                                screenshots.append({
                                                    'url': screenshot_base64,
                                                    'description': f'步骤 {i}: {step_info["description"] or "手动截图"}',
                                                    'step_number': i,
                                                    'timestamp': timezone.now().isoformat()
                                                })

                                    finally:
                                        engine.stop()

                                else:  # Playwright
                                    import asyncio
                                    from asgiref.sync import sync_to_async
                                    from .playwright_engine import PlaywrightTestEngine

                                    async def run_playwright_test():
                                        browser_map = {
                                            'chrome': 'chromium',
                                            'firefox': 'firefox',
                                            'safari': 'webkit',
                                            'edge': 'chromium'
                                        }
                                        browser_type = browser_map.get(task.browser, 'chromium')

                                        engine = PlaywrightTestEngine(browser_type=browser_type, headless=task.headless, base_url=test_case.project.base_url)

                                        try:
                                            # 启动浏览器
                                            await engine.start()
                                            execution_logs.append("✓ 浏览器启动成功")

                                            # 获取项目基础URL（同步操作）
                                            base_url = await sync_to_async(lambda: test_case.project.base_url)()

                                            # 导航到项目基础URL
                                            if base_url:
                                                success, nav_log = await engine.navigate(base_url)
                                                execution_logs.append(nav_log)
                                                if not success:
                                                    execution_result['status'] = 'failed'
                                                    execution_result['error_message'] = "导航到测试页面失败"
                                                    return False

                                            # 执行测试步骤
                                            for i, step_info in enumerate(steps_data, 1):
                                                step = step_info['step']
                                                action_type = step_info['action_type']
                                                element_data = step_info['element_data']

                                                success, step_log, screenshot_base64 = await engine.execute_step(step,
                                                                                                                 element_data or {})

                                                step_results.append({
                                                    'step_number': i,
                                                    'action_type': action_type,
                                                    'description': step_info['description'] or '',
                                                    'success': success,
                                                    'error': None if success else step_log
                                                })

                                                if not success:
                                                    execution_result['status'] = 'failed'
                                                    execution_result['error_message'] = step_log

                                                    if not screenshot_base64:
                                                        screenshot_base64 = await engine.capture_screenshot()

                                                    if screenshot_base64:
                                                        screenshots.append({
                                                            'url': screenshot_base64,
                                                            'description': f'步骤 {i} 失败截图',
                                                            'step_number': i,
                                                            'timestamp': timezone.now().isoformat()
                                                        })

                                                    return False

                                                if action_type == 'screenshot' and screenshot_base64:
                                                    screenshots.append({
                                                        'url': screenshot_base64,
                                                        'description': f'步骤 {i}: {step_info["description"] or "手动截图"}',
                                                        'step_number': i,
                                                        'timestamp': timezone.now().isoformat()
                                                    })

                                            return True

                                        finally:
                                            await engine.stop()

                                    # 在新的事件循环中运行Playwright测试
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    try:
                                        loop.run_until_complete(run_playwright_test())
                                    finally:
                                        loop.close()

                                # 计算执行时间
                                total_time = round(time.time() - start_time, 2)

                                # 保存执行结果
                                execution.status = execution_result['status']
                                execution.error_message = execution_result['error_message'] or ''
                                execution.execution_logs = json.dumps(step_results, ensure_ascii=False)
                                execution.execution_time = total_time
                                execution.screenshots = screenshots
                                execution.finished_at = timezone.now()
                                execution.save()

                                if execution.status == 'passed':
                                    success_count += 1
                                    logger.info(f"测试用例 {test_case.name} 执行成功")
                                else:
                                    failed_count += 1
                                    logger.warning(f"测试用例 {test_case.name} 执行失败: {execution.error_message}")

                            except Exception as e:
                                logger.error(f"执行测试用例 {test_case.name} 时发生异常: {str(e)}")
                                execution.status = 'failed'
                                execution.error_message = str(e)
                                execution.finished_at = timezone.now()
                                execution.save()
                                failed_count += 1

                        # 更新任务执行结果
                        if failed_count == 0:
                            task.successful_runs += 1
                            task.last_result = {
                                'status': 'success',
                                'message': f'执行完成: {success_count}个成功',
                                'success_count': success_count,
                                'failed_count': failed_count
                            }
                            task.error_message = ''
                            task.save()

                            # 发送成功通知
                            self._send_task_notification(task, success=True)
                        else:
                            task.failed_runs += 1
                            task.last_result = {
                                'status': 'partial',
                                'message': f'执行完成: {success_count}个成功, {failed_count}个失败',
                                'success_count': success_count,
                                'failed_count': failed_count
                            }
                            task.error_message = f'{failed_count}个测试用例执行失败'
                            task.save()

                            # 发送失败通知
                            self._send_task_notification(task, success=False)

                    except Exception as e:
                        logger.error(f"执行定时任务测试用例时发生异常: {str(e)}")
                        task.failed_runs += 1
                        task.last_result = {'status': 'failed', 'message': str(e)}
                        task.error_message = str(e)
                        task.save()

                        # 发送失败通知
                        self._send_task_notification(task, success=False)

                # 启动后台线程执行测试
                thread = threading.Thread(target=run_test_cases)
                thread.daemon = True
                thread.start()

                log_operation('run', 'scheduled_task', task.id, task.name, request.user)

                return Response({
                    'message': '测试用例开始执行',
                    'task_id': task.id,
                    'task_name': task.name,
                    'test_case_count': test_case_count,
                    'engine': task.engine,
                    'browser': task.browser,
                    'headless': task.headless
                }, status=status.HTTP_200_OK)

            else:
                return Response({
                    'error': '不支持的任务类型'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f'执行定时任务失败: {str(e)}')
            return Response({
                'error': f'执行失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _send_task_notification(self, task, success):
        """发送任务执行通知"""
        try:
            logger.info(f"准备发送任务 {task.id} 的通知，执行结果: {'成功' if success else '失败'}")

            # 检查是否需要发送通知
            if success and not task.notify_on_success:
                logger.info("任务执行成功但未启用成功通知")
                return

            if not success and not task.notify_on_failure:
                logger.info("任务执行失败但未启用失败通知")
                return

            # 检查通知类型
            if not task.notification_type:
                logger.info("未设置通知类型")
                return

            logger.info(f"通知类型: {task.notification_type}")

            # 根据通知类型发送不同的通知
            if task.notification_type in ['webhook', 'both']:
                logger.info("发送Webhook通知")
                self._send_webhook_notification(task, success)

            if task.notification_type in ['email', 'both']:
                logger.info("发送邮件通知")
                self._send_email_notification(task, success)

        except Exception as e:
            logger.error(f"发送通知失败: {str(e)}", exc_info=True)

    def _send_webhook_notification(self, task, success):
        """发送Webhook通知"""
        try:
            import requests
            import json

            logger.info("=== 开始发送Webhook通知 ===")

            # 使用统一的通知配置
            try:
                from apps.core.models import UnifiedNotificationConfig
                all_webhook_configs = UnifiedNotificationConfig.objects.filter(
                    config_type__in=['webhook_wechat', 'webhook_feishu', 'webhook_dingtalk'],
                    is_active=True
                )
                logger.info("使用统一通知配置 (UnifiedNotificationConfig)")
            except ImportError as e:
                # 如果 core 模块不可用，记录错误并返回
                logger.error(f"无法导入统一通知配置: {e}")
                logger.warning("通知发送失败：无法找到通知配置模块")
                return
            except Exception as e:
                logger.error(f"获取通知配置时出错: {e}")
                return

            all_webhook_bots = []
            for config in all_webhook_configs:
                bots = config.get_webhook_bots()
                if bots:
                    for bot in bots:
                        # 只添加启用了"UI自动化测试"的机器人
                        if bot.get('enabled', True) and bot.get('enable_ui_automation', True):
                            all_webhook_bots.append(bot)
                            logger.info(f"添加机器人: {bot.get('name')} (UI自动化测试已启用)")
                        elif bot.get('enabled', True):
                            logger.info(f"配置中心机器人 {bot.get('name')} 未启用UI自动化测试，跳过")

            if not all_webhook_bots:
                logger.warning("没有找到任何启用的webhook机器人配置")
                return

            logger.info(f"找到 {len(all_webhook_bots)} 个启用的webhook机器人配置")

            # 准备通知内容
            status_text = '成功' if success else '失败'
            task_type_text = '测试套件执行' if task.task_type == 'TEST_SUITE' else '测试用例执行'

            # 获取最后执行结果的详细信息
            last_result = task.last_result or {}
            result_message = last_result.get('message', '')
            success_count = last_result.get('success_count', 0)
            failed_count = last_result.get('failed_count', 0)

            # 为不同的机器人平台准备消息格式
            for bot in all_webhook_bots:
                if not bot.get('enabled', True) or not bot.get('webhook_url'):
                    logger.info(f"跳过未启用或无URL的机器人: {bot.get('name', 'Unknown')}")
                    continue

                bot_type = bot.get('type', 'unknown')
                webhook_url = bot['webhook_url']
                logger.info(f"发送通知到 {bot_type} 机器人: {bot.get('name', 'Unknown')}")

                # 构造详细内容
                # 转换执行时间到本地时区
                local_run_time = timezone.localtime(task.last_run_time).strftime(
                    '%Y-%m-%d %H:%M:%S') if task.last_run_time else '未知'
                detail_content = f"""任务名称: {task.name}

执行状态: {status_text}

执行时间: {local_run_time}

任务类型: {task_type_text}

执行引擎: {task.engine.upper()}

浏览器: {task.browser.capitalize()}"""

                if result_message:
                    detail_content += f"\n\n执行结果: {result_message}"

                if success_count > 0 or failed_count > 0:
                    detail_content += f"\n\n成功: {success_count} 个，失败: {failed_count} 个"

                # 根据机器人类型构造消息格式
                if bot_type == 'wechat':  # 企业微信
                    message_data = {
                        "msgtype": "markdown",
                        "markdown": {
                            "content": f"""**UI自动化定时任务执行{status_text}**

{detail_content}"""
                        }
                    }
                elif bot_type == 'feishu':  # 飞书
                    message_data = {
                        "msg_type": "interactive",
                        "card": {
                            "elements": [{
                                "tag": "div",
                                "text": {
                                    "content": f"**UI自动化定时任务执行{status_text}**\n\n{detail_content}",
                                    "tag": "lark_md"
                                }
                            }],
                            "header": {
                                "title": {
                                    "content": f"UI自动化定时任务执行{status_text}",
                                    "tag": "plain_text"
                                },
                                "template": "green" if success else "red"
                            }
                        }
                    }
                elif bot_type == 'dingtalk':  # 钉钉
                    message_data = {
                        "msgtype": "markdown",
                        "markdown": {
                            "title": f"UI自动化定时任务执行{status_text}",
                            "text": f"""**UI自动化定时任务执行{status_text}**

{detail_content}"""
                        }
                    }

                    # 钉钉机器人签名验证
                    secret = bot.get('secret')
                    if secret:
                        import time
                        import hmac
                        import hashlib
                        import base64
                        import urllib.parse

                        timestamp = str(round(time.time() * 1000))
                        string_to_sign = f'{timestamp}\n{secret}'
                        string_to_sign_enc = string_to_sign.encode('utf-8')
                        secret_enc = secret.encode('utf-8')
                        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
                        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

                        # 在URL中添加签名参数
                        if '?' in webhook_url:
                            webhook_url += f'&timestamp={timestamp}&sign={sign}'
                        else:
                            webhook_url += f'?timestamp={timestamp}&sign={sign}'
                else:
                    logger.warning(f"未知的机器人类型: {bot_type}")
                    continue

                # 发送webhook请求
                try:
                    logger.info(f"发送请求到: {webhook_url}")
                    logger.info(f"消息数据: {json.dumps(message_data, ensure_ascii=False, indent=2)}")

                    response = requests.post(
                        webhook_url,
                        json=message_data,
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )

                    logger.info(f"响应状态码: {response.status_code}")
                    logger.info(f"响应内容: {response.text}")

                    if response.status_code == 200:
                        logger.info(f"成功发送通知到 {bot.get('name', 'Unknown')}")

                        # 记录通知日志
                        UiNotificationLog.objects.create(
                            task=task,
                            task_name=task.name,
                            task_type=task.task_type,
                            notification_type='task_execution',
                            sender_name='系统Webhook通知',
                            sender_email='system@notification.com',
                            recipient_info=[{'name': bot.get('name', 'Unknown'), 'webhook_url': webhook_url}],
                            webhook_bot_info=bot,
                            notification_content=json.dumps(message_data, ensure_ascii=False),
                            status='success',
                            response_info={'status_code': response.status_code, 'response': response.text},
                            sent_at=timezone.now()
                        )
                    else:
                        logger.error(f"发送通知失败，状态码: {response.status_code}, 响应: {response.text}")

                        # 记录失败日志
                        UiNotificationLog.objects.create(
                            task=task,
                            task_name=task.name,
                            task_type=task.task_type,
                            notification_type='task_execution',
                            sender_name='系统Webhook通知',
                            sender_email='system@notification.com',
                            recipient_info=[{'name': bot.get('name', 'Unknown'), 'webhook_url': webhook_url}],
                            webhook_bot_info=bot,
                            notification_content=json.dumps(message_data, ensure_ascii=False),
                            status='failed',
                            error_message=f'HTTP {response.status_code}: {response.text}',
                            response_info={'status_code': response.status_code, 'response': response.text}
                        )

                except requests.exceptions.RequestException as e:
                    logger.error(f"发送webhook请求失败: {str(e)}")

                    # 记录失败日志
                    UiNotificationLog.objects.create(
                        task=task,
                        task_name=task.name,
                        task_type=task.task_type,
                        notification_type='task_execution',
                        sender_name='系统Webhook通知',
                        sender_email='system@notification.com',
                        recipient_info=[{'name': bot.get('name', 'Unknown'), 'webhook_url': webhook_url}],
                        webhook_bot_info=bot,
                        notification_content=json.dumps(message_data, ensure_ascii=False),
                        status='failed',
                        error_message=str(e)
                    )

        except Exception as e:
            logger.error(f"发送Webhook通知失败: {str(e)}", exc_info=True)

    def _send_email_notification(self, task, success):
        """发送邮件通知"""
        try:
            from django.core.mail import send_mail
            from django.conf import settings

            logger.info("=== 开始发送邮件通知 ===")

            # 获取收件人列表
            recipients = []
            if task.notify_emails:
                if isinstance(task.notify_emails, list):
                    recipients = task.notify_emails
                else:
                    recipients = [task.notify_emails]

            if not recipients:
                logger.warning("没有找到任何邮件收件人")
                return

            # 准备邮件内容
            status_text = '成功' if success else '失败'
            task_type_text = '测试套件执行' if task.task_type == 'TEST_SUITE' else '测试用例执行'

            subject = f"UI自动化定时任务执行{status_text}: {task.name}"

            last_result = task.last_result or {}
            result_message = last_result.get('message', '')

            # 转换执行时间到本地时区
            local_run_time = timezone.localtime(task.last_run_time).strftime(
                '%Y-%m-%d %H:%M:%S') if task.last_run_time else '未知'

            message = f"""
任务名称: {task.name}
执行状态: {status_text}
执行时间: {local_run_time}
任务类型: {task_type_text}
执行引擎: {task.engine.upper()}
浏览器: {task.browser.capitalize()}

执行结果:
{result_message if result_message else '无详细信息'}

错误信息:
{task.error_message if task.error_message else '无错误信息'}
            """

            # 发送邮件
            from_email = settings.DEFAULT_FROM_EMAIL
            logger.info(f"准备发送邮件，发件人: {from_email}, 收件人: {recipients}")

            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipients,
                fail_silently=False,
            )
            logger.info("邮件发送成功")

            # 记录通知日志
            UiNotificationLog.objects.create(
                task=task,
                task_name=task.name,
                task_type=task.task_type,
                notification_type='task_execution',
                sender_name='系统邮件通知',
                sender_email=from_email,
                recipient_info=[{'email': email} for email in recipients],
                notification_content=message,
                status='success',
                sent_at=timezone.now()
            )

        except Exception as e:
            logger.error(f"发送邮件通知失败: {str(e)}", exc_info=True)

            # 记录失败日志
            try:
                UiNotificationLog.objects.create(
                    task=task,
                    task_name=task.name,
                    task_type=task.task_type,
                    notification_type='task_execution',
                    sender_name='系统邮件通知',
                    sender_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_info=[{'email': email} for email in recipients] if recipients else [],
                    notification_content=f"发送邮件通知失败: {str(e)}",
                    status='failed',
                    error_message=str(e)
                )
            except:
                pass


class UiNotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """UI通知日志视图集（只读）"""
    queryset = UiNotificationLog.objects.all()
    serializer_class = UiNotificationLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'notification_type']
    search_fields = ['task_name', 'notification_content']
    ordering_fields = ['created_at', 'sent_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """重试发送通知"""
        log = self.get_object()
        if log.status == 'failed':
            # 这里应该触发实际的重试逻辑
            log.retry_count += 1
            log.is_retried = True
            log.save()
            return Response({'message': '通知已加入重试队列'})
        return Response({'error': '只能重试失败的通知'}, status=status.HTTP_400_BAD_REQUEST)


class UiTaskNotificationSettingViewSet(viewsets.ModelViewSet):
    """UI任务通知设置视图集"""
    queryset = UiTaskNotificationSetting.objects.all()
    serializer_class = UiTaskNotificationSettingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['task', 'is_enabled', 'notification_type']


class AICaseViewSet(viewsets.ModelViewSet):
    queryset = AICase.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = AICaseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project']
    search_fields = ['name', 'description', 'task_description']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        # 返回用户有权限的项目下的AI用例，以及没有关联项目的AI用例
        return AICase.objects.filter(
            models.Q(project__in=accessible_projects) | models.Q(project__isnull=True)
        ).distinct()

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """执行 AI 用例"""
        ai_case = self.get_object()

        # 创建执行记录
        execution_record = AIExecutionRecord.objects.create(
            project=ai_case.project,
            ai_case=ai_case,
            case_name=ai_case.name,
            task_description=ai_case.task_description,
            status='running',
            executed_by=request.user,
            logs="正在分析任务...\n"
        )

        # 异步执行
        import threading
        import os
        from asgiref.sync import sync_to_async
        from django.db import connection, DatabaseError
        from .ai_agent import run_full_process_sync

        def run_task():
            # 注册停止信号
            STOP_SIGNALS[execution_record.id] = False

            # 关键修复：关闭旧连接，避免子线程共享主线程的连接
            try:
                connection.close()
            except:
                pass

            # 设置环境变量，允许在后台线程中使用同步 ORM
            os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'

            def safe_save(record, update_fields=None, max_retries=3):
                """安全的保存方法，带有重试机制"""
                for attempt in range(max_retries):
                    try:
                        record.save(update_fields=update_fields)
                        return True
                    except (DatabaseError, Exception) as e:
                        error_str = str(e)
                        # 检查是否是MySQL连接错误
                        if '2006' in error_str or 'MySQL server has gone away' in error_str or '0' == error_str:
                            if attempt < max_retries - 1:
                                logger.warning(f"数据库连接失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                                # 关闭旧连接并重试
                                try:
                                    connection.close()
                                except:
                                    pass
                                import time
                                time.sleep(0.5)  # 等待一下再重试
                                continue
                            else:
                                logger.error(f"数据库保存失败，已达最大重试次数: {e}")
                                raise
                        else:
                            # 其他错误直接抛出
                            logger.error(f"数据库保存失败: {e}")
                            raise
                return False

            try:
                def should_stop():
                    return STOP_SIGNALS.get(execution_record.id, False)

                async def on_analysis_complete(planned_tasks):
                    execution_record.planned_tasks = planned_tasks
                    execution_record.logs += "任务分析完成，开始执行...\n"
                    await sync_to_async(safe_save)(execution_record, update_fields=['planned_tasks', 'logs'])

                async def on_step_update(step_info):
                    try:
                        # 处理日志
                        if step_info.get('type') == 'log':
                            content = step_info.get('content')
                            if content:
                                execution_record.logs += content
                                await sync_to_async(safe_save)(execution_record, update_fields=['logs'])
                            return

                        # 处理任务状态
                        task_id = step_info.get('task_id')
                        status = step_info.get('status')
                        if task_id and status:
                            if str(status).strip().lower() == 'completed':
                                backfilled_ids = backfill_prior_pending_tasks(
                                    execution_record.planned_tasks,
                                    task_id
                                )
                                if backfilled_ids:
                                    execution_record.logs += (
                                        f"\n[System] 已补齐遗漏标记的前序子任务: "
                                        f"{', '.join(map(str, backfilled_ids))}"
                                    )
                            updated = update_planned_task_status(
                                execution_record.planned_tasks,
                                task_id,
                                status
                            )
                            if updated:
                                update_fields = ['planned_tasks']
                                if str(status).strip().lower() == 'completed' and 'backfilled_ids' in locals() and backfilled_ids:
                                    update_fields.append('logs')
                                await sync_to_async(safe_save)(execution_record, update_fields=update_fields)
                    except Exception as e:
                        logger.error(f"更新步骤状态失败: {e}")

                history = run_full_process_sync(
                    ai_case.task_description,
                    analysis_callback=on_analysis_complete,
                    step_callback=on_step_update,
                    should_stop=should_stop
                )

                # 检查是否是手动停止
                if should_stop():
                    execution_record.status = 'stopped'
                    execution_record.logs += "\n[System] 任务已由用户停止。"
                else:
                    # 根据执行过程判断最终状态（任务或步骤出现失败则标记失败）
                    failed = False
                    if execution_record.planned_tasks:
                        failed = any(t.get('status') in ('failed', 'error') for t in execution_record.planned_tasks)
                    # history 也可能包含状态信息
                    if not failed and history:
                        try:
                            steps = history.steps if hasattr(history, 'steps') else []
                            for step in steps:
                                if getattr(step, 'status', None) == 'failed':
                                    failed = True
                                    break
                        except Exception:
                            pass

                    if failed:
                        execution_record.status = 'failed'
                        execution_record.logs += "\n执行完成，但检测到失败步骤或任务。"
                    else:
                        execution_record.status = 'passed'
                        execution_record.logs += "\n执行完成。"

                    # 记录任务完成统计信息
                    if execution_record.planned_tasks:
                        total_tasks = len(execution_record.planned_tasks)
                        completed_tasks = len(
                            [t for t in execution_record.planned_tasks if t.get('status') == 'completed'])
                        pending_tasks = len([t for t in execution_record.planned_tasks if t.get('status') == 'pending'])
                        logger.info(
                            f"🏁 Task completion summary: {completed_tasks}/{total_tasks} tasks completed, {pending_tasks} pending")

                execution_record.end_time = timezone.now()
                execution_record.duration = (execution_record.end_time - execution_record.start_time).total_seconds()

                # 格式化 history 为日志 (如果不是停止状态)
                steps = []
                if history:
                    if hasattr(history, 'steps'):
                        steps = [extract_step_info(s, i) for i, s in enumerate(history.steps)]

                execution_record.steps_completed = steps

                # 自动标记已完成的任务
                if execution_record.planned_tasks:
                    self._auto_mark_completed_tasks(execution_record)
                    execution_record.logs = append_execution_summary(
                        execution_record.logs,
                        summarize_planned_tasks(execution_record.planned_tasks)
                    )

                # 处理GIF录制文件
                self._process_gif_recording(execution_record, history)

                safe_save(execution_record)

            except Exception as e:
                error_message = str(e)
                failed_task_id = None if is_infrastructure_failure(error_message) else mark_first_active_task(execution_record.planned_tasks, 'failed')
                execution_record.status = 'failed'
                execution_record.end_time = timezone.now()
                execution_record.duration = (execution_record.end_time - execution_record.start_time).total_seconds()
                if 'Execution LLM unavailable' in error_message:
                    execution_record.logs += f"\n执行出错: AI 执行模型连接失败。{error_message}"
                else:
                    execution_record.logs += f"\n执行出错: {error_message}"
                if failed_task_id is not None:
                    execution_record.logs += f"\n[System] 子任务 {failed_task_id} 已自动标记为失败。"
                execution_record.logs = append_execution_summary(
                    execution_record.logs,
                    summarize_planned_tasks(execution_record.planned_tasks)
                )
                try:
                    safe_save(execution_record)
                except:
                    # 如果保存失败，至少尝试保存基本信息
                    logger.error(f"保存失败状态时出错: {e}")
                    pass
            finally:
                # 清理停止信号
                if execution_record.id in STOP_SIGNALS:
                    del STOP_SIGNALS[execution_record.id]

        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()

        return Response({
            'message': 'AI 用例开始执行',
            'execution_id': execution_record.id
        })

    def _process_gif_recording(self, execution_record, history):
        """
        处理GIF录制文件
        在执行完成后查找生成的GIF文件并保存路径到数据库
        """
        try:
            import os
            from django.conf import settings
            from datetime import datetime

            # browser-use 默认生成的GIF文件名（固定为agent_history.gif）
            default_gif_path = os.path.join(os.getcwd(), 'agent_history.gif')

            # 如果找到GIF文件，移动到media/ai_recording目录并重命名
            if os.path.exists(default_gif_path):
                import shutil

                # 创建录制文件目录
                gif_dir = os.path.join(settings.MEDIA_ROOT, 'ai_recording')
                os.makedirs(gif_dir, exist_ok=True)

                # 生成新的文件名：用例名称+年月日时分秒
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                # 清理用例名称中的非法字符
                safe_case_name = "".join(
                    [c if c.isalnum() or c in (' ', '_', '-') else '_' for c in execution_record.case_name])
                new_gif_filename = f"{safe_case_name}_{timestamp}.gif"
                new_gif_path = os.path.join(gif_dir, new_gif_filename)

                # 移动并重命名文件
                shutil.move(default_gif_path, new_gif_path)

                # 保存相对路径到数据库（使用正斜杠，确保跨平台兼容）
                relative_path = f'media/ai_recording/{new_gif_filename}'
                execution_record.gif_path = relative_path

                logger.info(f"✅ GIF recording saved to: {relative_path}")
            else:
                logger.warning(f"⚠️ GIF file not found at: {default_gif_path}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to process GIF recording: {e}")

    def _auto_mark_completed_tasks(self, execution_record):
        """
        自动标记已完成的任务
        通过分析执行历史和当前任务状态，自动标记那些已经执行但未被标记完成的任务
        
        注意：已移除统一标记逻辑，任务状态完全由AI智能体通过mark_task_complete控制
        - 执行成功时标记为completed
        - 执行失败时标记为failed
        - 跳过执行时标记为skipped
        - 未执行时标记为pending
        """
        try:
            # 记录初始状态
            initial_completed = 0
            initial_pending = 0
            initial_failed = 0
            initial_skipped = 0
            
            if execution_record.planned_tasks:
                initial_completed = len([t for t in execution_record.planned_tasks if t.get('status') == 'completed'])
                initial_pending = len([t for t in execution_record.planned_tasks if t.get('status') == 'pending'])
                initial_failed = len([t for t in execution_record.planned_tasks if t.get('status') == 'failed'])
                initial_skipped = len([t for t in execution_record.planned_tasks if t.get('status') == 'skipped'])
                
                logger.info(f"📊 Task status summary: {initial_completed} completed, {initial_pending} pending, {initial_failed} failed, {initial_skipped} skipped")
            
            # 不再自动标记所有任务为完成
            # 任务状态完全由AI智能体通过mark_task_complete来控制
            logger.info("📋 Task statuses are controlled by AI agent via mark_task_complete action")

        except Exception as e:
            logger.warning(f"⚠️ Failed to summarize task statuses: {e}")


# 全局停止信号字典 {execution_id: bool}
STOP_SIGNALS = {}

TERMINAL_TASK_STATUSES = {'completed', 'failed', 'skipped'}
ACTIVE_TASK_STATUSES = {'pending', 'in_progress'}


def update_planned_task_status(planned_tasks, task_id, task_status):
    """更新子任务状态，返回是否命中任务。"""
    if not planned_tasks or task_id is None or not task_status:
        return False

    normalized_status = str(task_status).strip().lower()
    for task in planned_tasks:
        if str(task.get('id')) == str(task_id):
            task['status'] = normalized_status
            return True
    return False


def backfill_prior_pending_tasks(planned_tasks, current_task_id):
    """受限补齐：仅在强依赖场景下补齐紧邻前一步遗漏标记。"""
    if not planned_tasks or current_task_id is None:
        return []

    try:
        current_task_id_int = int(current_task_id)
    except (TypeError, ValueError):
        return []

    task_by_id = {}
    for task in planned_tasks:
        try:
            task_by_id[int(task.get('id'))] = task
        except (TypeError, ValueError):
            continue

    current_task = task_by_id.get(current_task_id_int)
    previous_task = task_by_id.get(current_task_id_int - 1)
    if not current_task or not previous_task:
        return []

    if previous_task.get('status', 'pending') not in ACTIVE_TASK_STATUSES:
        return []

    previous_desc = str(previous_task.get('description', '')).strip()
    current_desc = str(current_task.get('description', '')).strip()

    # 验证/检查类任务必须显式标记，禁止自动补齐
    verification_keywords = ['校验', '确认', '检查', '验证', '断言']
    if any(keyword in previous_desc for keyword in verification_keywords):
        return []

    dependency_pairs = [
        (['访问', '打开', '进入'], ['搜索', '输入', '点击', '查看']),
        (['搜索'], ['点击第', '点击第2条', '点击第二条', '查看详情']),
        (['点击第', '点击第2条', '点击第二条', '查看详情'], ['关闭', '关闭该标签页', '关闭标签页']),
        (['打开详情', '查看详情'], ['关闭', '返回']),
    ]

    def matches_any(text, keywords):
        return any(keyword in text for keyword in keywords)

    allowed = any(
        matches_any(previous_desc, prev_keywords) and matches_any(current_desc, curr_keywords)
        for prev_keywords, curr_keywords in dependency_pairs
    )

    if not allowed:
        return []

    previous_task['status'] = 'completed'
    return [current_task_id_int - 1]


def mark_first_active_task(planned_tasks, task_status):
    """在执行异常时为第一个未终态任务补一个状态。"""
    if not planned_tasks:
        return None

    normalized_status = str(task_status).strip().lower()
    for task in planned_tasks:
        if task.get('status', 'pending') in ACTIVE_TASK_STATUSES:
            task['status'] = normalized_status
            return task.get('id')
    return None


def summarize_planned_tasks(planned_tasks):
    """汇总子任务状态。"""
    summary = {
        'total': 0,
        'completed': 0,
        'failed': 0,
        'skipped': 0,
        'pending': 0,
        'in_progress': 0,
    }
    if not planned_tasks:
        return summary

    summary['total'] = len(planned_tasks)
    for task in planned_tasks:
        task_status = task.get('status', 'pending')
        if task_status in summary:
            summary[task_status] += 1
        else:
            summary['pending'] += 1
    return summary


def resolve_execution_status(planned_tasks):
    """根据子任务实际状态推导整单状态。"""
    summary = summarize_planned_tasks(planned_tasks)

    if summary['total'] == 0:
        return 'passed', summary
    if summary['failed'] > 0:
        return 'failed', summary
    if summary['pending'] > 0 or summary['in_progress'] > 0:
        return 'failed', summary
    return 'passed', summary


def append_execution_summary(logs, summary):
    """把任务统计附加到日志中。"""
    if summary['total'] == 0:
        return logs
    return (
        f"{logs}\n[System] 子任务统计: 总数 {summary['total']}，"
        f"已完成 {summary['completed']}，失败 {summary['failed']}，"
        f"跳过 {summary['skipped']}，待处理 {summary['pending'] + summary['in_progress']}。"
    )


def is_infrastructure_failure(error_message: str) -> bool:
    """判断是否为模型/网络/初始化类故障，这类问题不应直接把首个子任务标失败。"""
    message = (error_message or '').lower()
    infra_markers = [
        'execution llm unavailable',
        'connection error',
        'timed out',
        'timeout',
        'api key',
        'authentication',
        'unauthorized',
        'forbidden',
        'rate limit',
        'service unavailable',
    ]
    return any(marker in message for marker in infra_markers)


class AIExecutionRecordViewSet(viewsets.ModelViewSet):
    """AI执行记录视图集"""
    queryset = AIExecutionRecord.objects.all()
    serializer_class = AIExecutionRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['project', 'ai_case', 'status']
    ordering = ['-start_time']

    def get_queryset(self):
        user = self.request.user
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        # 返回用户有权限的项目下的执行记录，以及没有关联项目的执行记录
        return AIExecutionRecord.objects.filter(
            models.Q(project__in=accessible_projects) | models.Q(project__isnull=True)
        ).distinct()

    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """批量删除AI执行记录"""
        try:
            ids = request.data.get('ids', [])

            # 验证ids参数
            if not ids:
                return Response({'error': '请选择要删除的记录'}, status=status.HTTP_400_BAD_REQUEST)

            # 确保ids是列表
            if not isinstance(ids, list):
                return Response({'error': 'ids参数格式错误，应为数组'}, status=status.HTTP_400_BAD_REQUEST)

            # 只能删除自己有权限的项目下的记录
            queryset = self.get_queryset()
            records_to_delete = queryset.filter(id__in=ids)

            # 检查是否有权限删除这些记录
            if not records_to_delete.exists():
                return Response({'error': '未找到可删除的记录或没有权限删除'}, status=status.HTTP_404_NOT_FOUND)

            # 获取可删除记录的ID列表，避免对distinct()后的queryset调用delete()
            deletable_ids = list(records_to_delete.values_list('id', flat=True))

            # 使用ID列表直接删除，避免distinct()的问题
            deleted_count = AIExecutionRecord.objects.filter(id__in=deletable_ids).delete()[0]

            return Response({'message': f'成功删除 {deleted_count} 条记录', 'deleted_count': deleted_count})
        except Exception as e:
            logger.error(f"批量删除AI执行记录失败: {str(e)}", exc_info=True)
            return Response({'error': f'批量删除失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='run_adhoc')
    def run_adhoc(self, request):
        """执行临时 AI 任务"""
        project_id = request.data.get('project_id')
        task_description = request.data.get('task_description')
        execution_mode = request.data.get('execution_mode', 'text')  # 默认文本模式
        enable_gif = request.data.get('enable_gif', True)  # GIF录制开关，默认开启

        if not task_description:
            return Response({'error': '缺少任务描述参数'}, status=status.HTTP_400_BAD_REQUEST)

        # 获取项目对象（如果提供了project_id）
        project = None
        if project_id:
            try:
                project = UiProject.objects.get(id=project_id)
            except UiProject.DoesNotExist:
                return Response({'error': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 创建执行记录
        execution_record = AIExecutionRecord.objects.create(
            project=project,
            case_name="Adhoc Task",
            task_description=task_description,
            execution_mode=execution_mode,
            status='running',
            executed_by=request.user,
            logs="正在分析任务...\n"
        )

        # 异步执行
        import threading
        import os
        from asgiref.sync import sync_to_async
        from django.db import connection, DatabaseError
        from .ai_agent import run_full_process_sync

        def run_task():
            # 注册停止信号
            STOP_SIGNALS[execution_record.id] = False

            # 关键修复：关闭旧连接，避免子线程共享主线程的连接
            try:
                connection.close()
            except:
                pass

            # 设置环境变量，允许在后台线程中使用同步 ORM
            os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'

            def safe_save(record, update_fields=None, max_retries=3):
                """安全的保存方法，带有重试机制"""
                for attempt in range(max_retries):
                    try:
                        record.save(update_fields=update_fields)
                        return True
                    except (DatabaseError, Exception) as e:
                        error_str = str(e)
                        # 检查是否是MySQL连接错误
                        if '2006' in error_str or 'MySQL server has gone away' in error_str or '0' == error_str:
                            if attempt < max_retries - 1:
                                logger.warning(f"数据库连接失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                                # 关闭旧连接并重试
                                try:
                                    connection.close()
                                except:
                                    pass
                                import time
                                time.sleep(0.5)  # 等待一下再重试
                                continue
                            else:
                                logger.error(f"数据库保存失败，已达最大重试次数: {e}")
                                raise
                        else:
                            # 其他错误直接抛出
                            logger.error(f"数据库保存失败: {e}")
                            raise
                return False

            try:
                # 定义异步安全的 should_stop
                async def should_stop_async():
                    # 优先检查内存信号
                    if STOP_SIGNALS.get(execution_record.id, False):
                        return True
                    # 兜底检查数据库状态 (使用 sync_to_async 避免异步上下文错误)
                    await sync_to_async(execution_record.refresh_from_db)()
                    return execution_record.status == 'stopped'

                # 定义同步版本的 should_stop 用于最后检查
                def should_stop_sync():
                    if STOP_SIGNALS.get(execution_record.id, False):
                        return True
                    execution_record.refresh_from_db()
                    return execution_record.status == 'stopped'

                async def on_analysis_complete(planned_tasks):
                    execution_record.planned_tasks = planned_tasks
                    execution_record.logs += "任务分析完成，开始执行...\n"
                    await sync_to_async(safe_save)(execution_record, update_fields=['planned_tasks', 'logs'])

                async def on_step_update(step_info):
                    try:
                        # 处理日志
                        if step_info.get('type') == 'log':
                            content = step_info.get('content')
                            if content:
                                execution_record.logs += content
                                # 立即保存到数据库，确保前端轮询能看到最新日志
                                await sync_to_async(safe_save)(execution_record, update_fields=['logs'])
                            return

                        # 处理任务状态
                        task_id = step_info.get('task_id')
                        status = step_info.get('status')
                        logger.info(f"DEBUG: on_step_update received: task_id={task_id}, status={status}")

                        if task_id and status:
                            updated = False
                            if execution_record.planned_tasks:
                                old_status = None
                                for task in execution_record.planned_tasks:
                                    if str(task.get('id')) == str(task_id):
                                        old_status = task.get('status', 'pending')
                                        break
                                backfilled_ids = []
                                if str(status).strip().lower() == 'completed':
                                    backfilled_ids = backfill_prior_pending_tasks(
                                        execution_record.planned_tasks,
                                        task_id
                                    )
                                    if backfilled_ids:
                                        execution_record.logs += (
                                            f"\n[System] 已补齐遗漏标记的前序子任务: "
                                            f"{', '.join(map(str, backfilled_ids))}"
                                        )
                                updated = update_planned_task_status(
                                    execution_record.planned_tasks,
                                    task_id,
                                    status
                                )
                                if updated:
                                    logger.info(f"DEBUG: Updated task {task_id} from {old_status} to {status}")
                            if updated:
                                # 立即保存到数据库，确保前端轮询能看到最新状态
                                update_fields = ['planned_tasks']
                                if 'backfilled_ids' in locals() and backfilled_ids:
                                    update_fields.append('logs')
                                await sync_to_async(safe_save)(execution_record, update_fields=update_fields)
                            else:
                                logger.warning(
                                    f"DEBUG: Task ID {task_id} not found in planned_tasks: {execution_record.planned_tasks}")
                    except Exception as e:
                        logger.error(f"更新步骤状态失败: {e}", exc_info=True)

                history = run_full_process_sync(
                    task_description,
                    analysis_callback=on_analysis_complete,
                    step_callback=on_step_update,
                    should_stop=should_stop_async,  # 传递异步版本
                    execution_mode=execution_mode,
                    enable_gif=enable_gif,  # 传递GIF录制开关
                    case_name=task_description[:50] if task_description else "Adhoc Task"  # 传递用例名称用于GIF文件命名
                )

                # 检查是否是手动停止 (使用同步版本)
                if should_stop_sync():
                    execution_record.status = 'stopped'
                    execution_record.logs += "\n[System] 任务已由用户停止。"
                else:
                    # 根据执行结果判定失败
                    failed = False
                    if execution_record.planned_tasks:
                        failed = any(t.get('status') in ('failed', 'error') for t in execution_record.planned_tasks)
                    if not failed and history:
                        try:
                            steps = history.steps if hasattr(history, 'steps') else []
                            for step in steps:
                                if getattr(step, 'status', None) == 'failed':
                                    failed = True
                                    break
                        except Exception:
                            pass

                    if failed:
                        execution_record.status = 'failed'
                        execution_record.logs += "\n执行完成，但检测到失败步骤或任务。"
                    else:
                        execution_record.status = 'passed'
                        execution_record.logs += "\n执行完成。"

                    # 记录任务完成统计信息
                    if execution_record.planned_tasks:
                        total_tasks = len(execution_record.planned_tasks)
                        completed_tasks = len(
                            [t for t in execution_record.planned_tasks if t.get('status') == 'completed'])
                        pending_tasks = len([t for t in execution_record.planned_tasks if t.get('status') == 'pending'])
                        logger.info(
                            f"🏁 Task completion summary: {completed_tasks}/{total_tasks} tasks completed, {pending_tasks} pending")

                execution_record.end_time = timezone.now()
                execution_record.duration = (execution_record.end_time - execution_record.start_time).total_seconds()

                # 格式化 history 为日志 (如果不是停止状态)
                steps = []
                if history:
                    if hasattr(history, 'steps'):
                        steps = [extract_step_info(s, i) for i, s in enumerate(history.steps)]

                execution_record.steps_completed = steps

                # 自动标记已完成的任务
                if execution_record.planned_tasks:
                    self._auto_mark_completed_tasks(execution_record)
                    execution_record.logs = append_execution_summary(
                        execution_record.logs,
                        summarize_planned_tasks(execution_record.planned_tasks)
                    )

                # 处理GIF录制文件
                self._process_gif_recording(execution_record, history)

                safe_save(execution_record)

            except Exception as e:
                error_message = str(e)
                failed_task_id = None if is_infrastructure_failure(error_message) else mark_first_active_task(execution_record.planned_tasks, 'failed')
                execution_record.status = 'failed'
                execution_record.end_time = timezone.now()
                execution_record.duration = (execution_record.end_time - execution_record.start_time).total_seconds()
                if 'Execution LLM unavailable' in error_message:
                    execution_record.logs += f"\n执行出错: AI 执行模型连接失败。{error_message}"
                else:
                    execution_record.logs += f"\n执行出错: {error_message}"
                if failed_task_id is not None:
                    execution_record.logs += f"\n[System] 子任务 {failed_task_id} 已自动标记为失败。"
                execution_record.logs = append_execution_summary(
                    execution_record.logs,
                    summarize_planned_tasks(execution_record.planned_tasks)
                )
                try:
                    safe_save(execution_record)
                except:
                    # 如果保存失败，至少尝试保存基本信息
                    logger.error(f"保存失败状态时出错: {e}")
                    pass
            finally:
                # 清理停止信号
                if execution_record.id in STOP_SIGNALS:
                    del STOP_SIGNALS[execution_record.id]

        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()

        return Response({
            'message': 'AI 任务开始执行',
            'execution_id': execution_record.id
        })

    @action(detail=True, methods=['post'], url_path='stop')
    def stop_task(self, request, pk=None):
        """停止正在执行的任务"""
        try:
            execution_id = int(pk)
            if execution_id in STOP_SIGNALS:
                STOP_SIGNALS[execution_id] = True
                return Response({'message': '已发送停止信号'})
            else:
                # 如果不在内存中，可能已经结束，或者重启过服务
                # 尝试直接更新数据库状态
                record = self.get_object()
                if record.status == 'running':
                    record.status = 'stopped'
                    record.end_time = timezone.now()
                    record.logs += "\n[System] 任务被强制标记为停止（未在运行队列中找到）。"
                    record.save()
                    return Response({'message': '任务已标记为停止'})
                return Response({'message': '任务不在运行中'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _process_gif_recording(self, execution_record, history):
        """
        处理GIF录制文件
        在执行完成后查找生成的GIF文件并保存路径到数据库
        """
        try:
            import os
            from django.conf import settings
            from datetime import datetime

            # browser-use 默认生成的GIF文件名（固定为agent_history.gif）
            default_gif_path = os.path.join(os.getcwd(), 'agent_history.gif')

            # 如果找到GIF文件，移动到media/ai_recording目录并重命名
            if os.path.exists(default_gif_path):
                import shutil

                # 创建录制文件目录
                gif_dir = os.path.join(settings.MEDIA_ROOT, 'ai_recording')
                os.makedirs(gif_dir, exist_ok=True)

                # 生成新的文件名：用例名称+年月日时分秒
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                # 清理用例名称中的非法字符
                safe_case_name = "".join(
                    [c if c.isalnum() or c in (' ', '_', '-') else '_' for c in execution_record.case_name])
                new_gif_filename = f"{safe_case_name}_{timestamp}.gif"
                new_gif_path = os.path.join(gif_dir, new_gif_filename)

                # 移动并重命名文件
                shutil.move(default_gif_path, new_gif_path)

                # 保存相对路径到数据库（使用正斜杠，确保跨平台兼容）
                relative_path = f'media/ai_recording/{new_gif_filename}'
                execution_record.gif_path = relative_path

                logger.info(f"✅ GIF recording saved to: {relative_path}")
            else:
                logger.warning(f"⚠️ GIF file not found at: {default_gif_path}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to process GIF recording: {e}")

    def _auto_mark_completed_tasks(self, execution_record):
        """
        自动标记已完成的任务
        通过分析执行历史和当前任务状态，自动标记那些已经执行但未被标记完成的任务
        
        注意：已移除统一标记逻辑，任务状态完全由AI智能体通过mark_task_complete控制
        - 执行成功时标记为completed
        - 执行失败时标记为failed
        - 跳过执行时标记为skipped
        - 未执行时标记为pending
        """
        try:
            # 记录初始状态
            initial_completed = 0
            initial_pending = 0
            initial_failed = 0
            initial_skipped = 0
            
            if execution_record.planned_tasks:
                initial_completed = len([t for t in execution_record.planned_tasks if t.get('status') == 'completed'])
                initial_pending = len([t for t in execution_record.planned_tasks if t.get('status') == 'pending'])
                initial_failed = len([t for t in execution_record.planned_tasks if t.get('status') == 'failed'])
                initial_skipped = len([t for t in execution_record.planned_tasks if t.get('status') == 'skipped'])
                
                logger.info(f"📊 Task status summary: {initial_completed} completed, {initial_pending} pending, {initial_failed} failed, {initial_skipped} skipped")
            
            # 不再自动标记所有任务为完成
            # 任务状态完全由AI智能体通过mark_task_complete来控制
            logger.info("📋 Task statuses are controlled by AI agent via mark_task_complete action")

        except Exception as e:
            logger.warning(f"⚠️ Failed to summarize task statuses: {e}")

    @action(detail=True, methods=['get'], url_path='report')
    def generate_report(self, request, pk=None):
        """
        生成AI执行报告

        Query Parameters:
            report_type: 报告类型 (summary/detailed/performance)，默认为 summary

        Returns:
            执行报告数据
        """
        try:
            record = self.get_object()
            report_type = request.query_params.get('report_type', 'summary')

            # 导入报告生成器
            from .reports import AIExecutionReportGenerator

            # 生成报告
            generator = AIExecutionReportGenerator(record)

            if report_type == 'detailed':
                report = generator.generate_detailed_report()
            elif report_type == 'performance':
                report = generator.generate_performance_report()
            else:  # summary
                report = generator.generate_summary_report()

            return Response({
                'success': True,
                'data': report,
                'report_type': report_type
            })

        except Exception as e:
            logger.error(f"生成AI执行报告失败: {e}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        """
        导出AI执行报告为PDF

        Query Parameters:
            report_type: 报告类型 (summary/detailed/performance)，默认为 summary

        Returns:
            PDF文件下载
        """
        try:
            record = self.get_object()
            report_type = request.query_params.get('report_type', 'summary')

            # 导入报告生成器
            from .reports import AIExecutionReportGenerator
            from .pdf_generator import AIReportPDFGenerator

            # 生成报告数据
            generator = AIExecutionReportGenerator(record)

            if report_type == 'detailed':
                report_data = generator.generate_detailed_report()
            elif report_type == 'performance':
                report_data = generator.generate_performance_report()
            else:  # summary
                report_data = generator.generate_summary_report()

            # 生成PDF
            pdf_generator = AIReportPDFGenerator(report_data, report_type)
            pdf_buffer = pdf_generator.generate()

            # 生成文件名
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            safe_case_name = "".join([c if c.isalnum() or c in (' ', '_', '-') else '_' for c in record.case_name])
            filename = f"AI_Report_{safe_case_name}_{timestamp}.pdf"

            # 返回PDF文件
            response = HttpResponse(
                pdf_buffer.getvalue(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(pdf_buffer.getvalue())

            return response

        except ImportError as e:
            logger.error(f"PDF生成库未安装: {e}")
            return Response({
                'success': False,
                'error': 'PDF生成功能需要安装 reportlab 库，请运行: pip install reportlab'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"导出PDF失败: {e}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UiDashboardViewSet(viewsets.ViewSet):
    """UI自动化仪表盘视图集"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取仪表盘统计数据"""
        user = request.user

        # 获取用户可访问的项目ID列表
        accessible_projects = UiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        project_ids = accessible_projects.values_list('id', flat=True)

        # 统计数据
        project_count = accessible_projects.count()

        # 测试用例数量
        test_case_count = TestCase.objects.filter(project_id__in=project_ids).count()

        # 测试套件数量（包含用例总数）
        suite_count = TestSuite.objects.filter(project_id__in=project_ids).count()

        from .models import TestSuiteTestCase
        suite_test_case_count = TestSuiteTestCase.objects.filter(
            test_suite__project_id__in=project_ids
        ).count()

        # 测试执行数量（传统+新版）
        execution_count = TestExecution.objects.filter(project_id__in=project_ids).count()
        test_case_execution_count = TestCaseExecution.objects.filter(project_id__in=project_ids).count()
        total_execution_count = execution_count + test_case_execution_count

        return Response({
            'project_count': project_count,
            'test_case_count': test_case_count,
            'suite_count': suite_test_case_count,
            'execution_count': total_execution_count
        })
