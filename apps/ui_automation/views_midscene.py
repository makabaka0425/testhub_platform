"""
Midscene AI视觉自动化 — ViewSet
包含：分组管理、用例管理（CRUD+AI导入+执行）、执行记录
"""
import os
import json
import time
import logging
import httpx
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import (
    MidsceneGroup, MidsceneCase, MidsceneExecution, AiProject,
    AiScheduledTask, AiNotificationLog,
    AiTestPlan, AiTestPlanItem,
)
from .serializers import (
    AiProjectSerializer, AiProjectCreateSerializer, AiProjectUpdateSerializer,
    AiScheduledTaskSerializer, AiNotificationLogSerializer,
    AiTestPlanSerializer, AiTestPlanCreateSerializer, AiTestPlanUpdateSerializer,
    AiTestPlanItemSerializer,
)
from django.db import models
from django.db.models import Max
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

logger = logging.getLogger(__name__)

MIDSCENE_SERVICE_URL = os.environ.get('MIDSCENE_SERVICE_URL', 'http://localhost:8001')


# ============================================================================
# AI自动化项目管理
# ============================================================================

class AiProjectViewSet(viewsets.ModelViewSet):
    """AI自动化测试项目管理"""
    queryset = AiProject.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'owner', 'default_platform']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return AiProjectCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AiProjectUpdateSerializer
        return AiProjectSerializer

    def get_queryset(self):
        user = self.request.user
        return AiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()

    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.delete()


# ============================================================================
# 分组管理
# ============================================================================

class MidsceneGroupViewSet(viewsets.ModelViewSet):
    """Midscene用例分组"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MidsceneGroup.objects.all()

    def list(self, request):
        project_id = request.query_params.get('project_id')
        qs = self.get_queryset()
        if project_id:
            qs = qs.filter(project_id=project_id)

        data = []
        for g in qs.order_by('order', '-created_at'):
            data.append({
                'id': g.id,
                'name': g.name,
                'project_id': g.project_id,
                'parent_id': g.parent_id,
                'order': g.order,
                'case_count': g.cases.count(),
                'created_at': g.created_at,
            })
        return Response(data)

    def create(self, request):
        name = request.data.get('name')
        if not name:
            return Response({'error': '分组名称不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        group = MidsceneGroup.objects.create(
            name=name,
            project_id=request.data.get('project_id') or None,
            parent_id=request.data.get('parent_id') or None,
            order=request.data.get('order', 0),
        )
        return Response({'id': group.id, 'name': group.name}, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None, **kwargs):
        group = self.get_queryset().filter(pk=pk).first()
        if not group:
            return Response({'error': '分组不存在'}, status=status.HTTP_404_NOT_FOUND)

        if 'name' in request.data:
            group.name = request.data['name']
        if 'parent_id' in request.data:
            group.parent_id = request.data['parent_id'] or None
        if 'order' in request.data:
            group.order = request.data['order']
        group.save()
        return Response({'id': group.id, 'name': group.name})

    def destroy(self, request, pk=None):
        group = self.get_queryset().filter(pk=pk).first()
        if not group:
            return Response({'error': '分组不存在'}, status=status.HTTP_404_NOT_FOUND)
        group.delete()
        return Response({'message': '已删除'})


# ============================================================================
# 用例管理
# ============================================================================

class MidsceneCaseViewSet(viewsets.ModelViewSet):
    """Midscene AI视觉自动化用例"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MidsceneCase.objects.select_related('group', 'project', 'created_by')

    def _serialize_case(self, case):
        """序列化单条用例"""
        return {
            'id': case.id,
            'name': case.name,
            'description': case.description,
            'group_id': case.group_id,
            'group_name': case.group.name if case.group else None,
            'project_id': case.project_id,
            'source': case.source,
            'source_case_id': case.source_case_id,
            'platform': case.platform,
            'steps': case.steps or [],
            # Web配置
            'url': case.url,
            'headless': case.headless,
            'cache_strategy': case.cache_strategy,
            'new_tab': case.new_tab,
            # Web高级配置
            'user_agent': case.user_agent,
            'viewport_width': case.viewport_width,
            'viewport_height': case.viewport_height,
            'device_scale_factor': case.device_scale_factor,
            'cookie_file': case.cookie_file,
            'wait_for_network_idle_timeout': case.wait_for_network_idle_timeout,
            'continue_on_network_idle_error': case.continue_on_network_idle_error,
            # APP配置
            'device_id': case.device_id,
            'package_name': case.package_name,
            'app_activity': case.app_activity,
            # 状态
            'last_status': case.last_status,
            'last_result': case.last_result,
            'created_by': case.created_by_id,
            'created_by_name': case.created_by.username if case.created_by else None,
            'created_at': case.created_at,
            'updated_at': case.updated_at,
            'step_count': len(case.steps) if case.steps else 0,
        }

    def list(self, request):
        qs = self.get_queryset()
        project_id = request.query_params.get('project_id')
        group_id = request.query_params.get('group_id')
        platform = request.query_params.get('platform')
        search = request.query_params.get('search')

        if project_id:
            qs = qs.filter(project_id=project_id)
        if group_id:
            if group_id in ('0', 'ungrouped'):
                qs = qs.filter(group_id__isnull=True)
            else:
                qs = qs.filter(group_id=group_id)
        if platform:
            qs = qs.filter(platform=platform)
        if search:
            qs = qs.filter(name__icontains=search)

        cases = qs.order_by('-created_at')
        data = [self._serialize_case(c) for c in cases]
        return Response({
            'count': len(data),
            'results': data,
        })

    def retrieve(self, request, pk=None):
        case = self.get_queryset().filter(pk=pk).first()
        if not case:
            return Response({'error': '用例不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self._serialize_case(case))

    def create(self, request):
        try:
            steps = request.data.get('steps', [])
            case = MidsceneCase.objects.create(
                name=request.data.get('name', ''),
                description=request.data.get('description', ''),
                group_id=request.data.get('group_id') or None,
                project_id=request.data.get('project_id') or None,
                source='manual',
                platform=request.data.get('platform', 'web'),
                steps=steps,
                # Web配置
                url=request.data.get('url', ''),
                headless=request.data.get('headless', False),
                cache_strategy=request.data.get('cache_strategy', 'normal'),
                new_tab=request.data.get('new_tab', False),
                # Web高级配置
                user_agent=request.data.get('user_agent', ''),
                viewport_width=request.data.get('viewport_width') or None,
                viewport_height=request.data.get('viewport_height') or None,
                device_scale_factor=request.data.get('device_scale_factor') or None,
                cookie_file=request.data.get('cookie_file', ''),
                wait_for_network_idle_timeout=request.data.get('wait_for_network_idle_timeout') or None,
                continue_on_network_idle_error=request.data.get('continue_on_network_idle_error', True),
                # APP配置
                device_id=request.data.get('device_id', ''),
                package_name=request.data.get('package_name', ''),
                app_activity=request.data.get('app_activity', ''),
                created_by=request.user,
            )
            return Response(self._serialize_case(case), status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f'创建Midscene用例失败')
            return Response({'error': f'创建失败: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None, **kwargs):
        case = self.get_queryset().filter(pk=pk).first()
        if not case:
            return Response({'error': '用例不存在'}, status=status.HTTP_404_NOT_FOUND)

        try:
            fields = ['name', 'description', 'platform', 'steps',
                      'url', 'headless', 'cache_strategy', 'new_tab',
                      'user_agent', 'viewport_width', 'viewport_height',
                      'device_scale_factor', 'cookie_file',
                      'wait_for_network_idle_timeout', 'continue_on_network_idle_error',
                      'device_id', 'package_name', 'app_activity']
            for f in fields:
                if f in request.data:
                    setattr(case, f, request.data[f])

            if 'group_id' in request.data:
                case.group_id = request.data['group_id'] or None

            case.save()
            return Response(self._serialize_case(case))
        except Exception as e:
            logger.exception(f'更新Midscene用例失败 case_id={pk}')
            return Response({'error': f'更新失败: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        case = self.get_queryset().filter(pk=pk).first()
        if not case:
            return Response({'error': '用例不存在'}, status=status.HTTP_404_NOT_FOUND)
        case.delete()
        return Response({'message': '已删除'})

    @action(detail=False, methods=['post'], url_path='batch-delete')
    def batch_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': '请选择要删除的用例'}, status=status.HTTP_400_BAD_REQUEST)
        self.get_queryset().filter(id__in=ids).delete()
        return Response({'message': f'已删除{len(ids)}条用例'})

    # ---- 从AI生成用例导入 ----
    @action(detail=False, methods=['post'], url_path='import-ai')
    def import_ai(self, request):
        """从AI生成用例导入到Midscene"""
        case_ids = request.data.get('case_ids', [])
        group_id = request.data.get('group_id')
        platform = request.data.get('platform', 'web')
        project_id = request.data.get('project_id')

        if not case_ids:
            return Response({'error': '请选择要导入的用例'}, status=status.HTTP_400_BAD_REQUEST)

        from apps.requirement_analysis.models import GeneratedTestCase
        ai_cases = GeneratedTestCase.objects.filter(id__in=case_ids)
        imported = []

        for ai_case in ai_cases:
            # 将AI用例的test_steps和expected_result映射为结构化步骤
            steps = []

            # 前置条件作为第一步
            if ai_case.precondition and ai_case.precondition.strip():
                steps.append({
                    'order': len(steps) + 1,
                    'type': 'action',
                    'instruction': ai_case.precondition.strip(),
                })

            # 测试步骤拆分（AI生成的步骤通常以换行或数字编号分隔）
            raw_steps = ai_case.test_steps or ''
            step_lines = [s.strip() for s in raw_steps.split('\n') if s.strip()]
            for line in step_lines:
                # 去掉数字前缀如 "1." "1)" "步骤1:"
                cleaned = line
                for prefix in ['步骤', 'Step', 'step']:
                    if cleaned.lower().startswith(prefix.lower()):
                        cleaned = cleaned[len(prefix):].lstrip(':：.、)）')
                        break
                import re
                cleaned = re.sub(r'^\d+[.、:：)）]\s*', '', cleaned)
                if cleaned:
                    steps.append({
                        'order': len(steps) + 1,
                        'type': 'action',
                        'instruction': cleaned,
                    })

            # 预期结果作为断言步骤
            if ai_case.expected_result and ai_case.expected_result.strip():
                expected_lines = [s.strip() for s in ai_case.expected_result.split('\n') if s.strip()]
                for line in expected_lines:
                    cleaned = re.sub(r'^\d+[.、:：)）]\s*', '', line)
                    if cleaned:
                        steps.append({
                            'order': len(steps) + 1,
                            'type': 'assert',
                            'instruction': cleaned,
                        })

            mc = MidsceneCase.objects.create(
                name=ai_case.title or f'AI导入-{ai_case.case_id}',
                description=f'从AI用例 {ai_case.case_id} 导入',
                group_id=group_id or None,
                project_id=project_id or None,
                source='ai_import',
                source_case_id=ai_case.id,
                platform=platform,
                steps=steps,
                created_by=request.user,
            )
            imported.append(mc.id)

        return Response({
            'message': f'成功导入{len(imported)}条用例',
            'imported_ids': imported,
        })

    # ---- 执行用例 ----
    @action(detail=True, methods=['post'], url_path='run')
    def run_case(self, request, pk=None):
        """执行单条Midscene用例"""
        case = self.get_queryset().filter(pk=pk).first()
        if not case:
            return Response({'error': '用例不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 创建执行记录
        execution = MidsceneExecution.objects.create(
            case=case,
            status='running',
            executed_by=request.user,
        )

        # 更新用例状态为执行中
        case.last_status = 'running'
        case.save(update_fields=['last_status'])

        # 获取模型配置
        from apps.requirement_analysis.models import AIModelConfig
        config_obj = AIModelConfig.objects.filter(role='midscene_web', is_active=True).first()
        if not config_obj:
            config_obj = AIModelConfig.objects.filter(role='browser_use_text', is_active=True).first()

        model_config = {}
        if config_obj:
            # 根据 model_name 推断 Midscene 认可的 model_family
            # Midscene v1.10.8 支持的 family: qwen3-vl, qwen2.5-vl, qwen3, qwen3.5, qwen3.6,
            # doubao-vision, doubao-seed, gemini, glm-v, auto-glm, gpt-5, kimi, kimi3, xiaomi-mimo 等
            model_name = (config_obj.model_name or '').lower()
            if 'qwen3.6' in model_name:
                model_family = 'qwen3.6'
            elif 'qwen3.5' in model_name:
                model_family = 'qwen3.5'
            elif 'qwen3' in model_name and 'vl' in model_name:
                model_family = 'qwen3-vl'
            elif 'qwen3' in model_name:
                model_family = 'qwen3'
            elif 'qwen2.5' in model_name and 'vl' in model_name:
                model_family = 'qwen2.5-vl'
            elif 'qwen' in model_name and 'vl' in model_name:
                model_family = 'qwen2.5-vl'  # fallback
            elif 'qwen' in model_name:
                model_family = 'qwen3'
            elif 'doubao-seed' in model_name or 'seed' in model_name:
                model_family = 'doubao-seed'
            elif 'doubao' in model_name and 'vision' in model_name:
                model_family = 'doubao-vision'
            elif 'doubao' in model_name:
                model_family = 'doubao-vision'
            elif 'gemini' in model_name:
                model_family = 'gemini'
            elif 'glm' in model_name and 'auto-glm' in model_name:
                model_family = 'auto-glm'
            elif 'glm' in model_name:
                model_family = 'glm-v'
            elif 'gpt' in model_name:
                model_family = 'gpt-5'
            elif 'kimi3' in model_name:
                model_family = 'kimi3'
            elif 'kimi' in model_name:
                model_family = 'kimi'
            elif 'mimo' in model_name or 'xiaomi' in model_name:
                model_family = 'xiaomi-mimo'
            else:
                model_family = 'qwen3-vl'  # 默认fallback

            model_config = {
                'api_key': config_obj.api_key,
                'base_url': config_obj.base_url,
                'model_name': config_obj.model_name,
                'model_family': model_family,
            }

        # 构建微服务请求：对齐 v2 /execute 接口（steps 数组格式）
        steps = []
        for step in (case.steps or []):
            step_type = step.get('type', 'action')
            instruction = step.get('instruction', '')
            # 将前端 action/assert 映射为 Midscene API 类型
            if step_type == 'assert':
                midscene_type = 'aiAssert'
            elif step_type == 'action':
                midscene_type = 'aiAct'
            else:
                midscene_type = step_type  # 支持 aiTap/aiWaitFor/aiQuery/sleep 等
            steps.append({
                'type': midscene_type,
                'instruction': instruction,
            })

        if not steps:
            execution.status = 'failed'
            execution.error_message = '用例没有测试步骤'
            execution.finished_at = timezone.now()
            execution.save()
            case.last_status = 'failed'
            case.last_result = '用例没有测试步骤'
            case.save(update_fields=['last_status', 'last_result'])
            return Response({'error': '用例没有测试步骤'}, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            'platform': case.platform or 'web',  # 传递平台类型
            'url': case.url or None,
            'steps': steps,
            'headless': case.headless,
            'viewport': {
                'width': case.viewport_width or 1280,
                'height': case.viewport_height or 768,
            },
            'model_config': model_config,
            'callback_url': f'http://localhost:8000/api/ui-automation/midscene-cases/{case.id}/callback/',
            'execution_id': execution.id,
            # Web高级配置
            'user_agent': case.user_agent or None,
            'device_scale_factor': case.device_scale_factor or None,
            'cookie_file': case.cookie_file or None,
            'wait_for_network_idle': {
                'timeout': case.wait_for_network_idle_timeout,
                'continue_on_error': case.continue_on_network_idle_error,
            } if case.wait_for_network_idle_timeout else None,
            # APP配置
            'app_config': {
                'device_id': case.device_id or '',
                'package_name': case.package_name or '',
                'app_activity': case.app_activity or '',
            } if case.platform == 'app' else None,
        }

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(f'{MIDSCENE_SERVICE_URL}/execute', json=payload)
                resp.raise_for_status()
                data = resp.json()

            return Response({
                'execution_id': execution.id,
                'task_id': data.get('task_id'),
                'status': 'submitted',
                'message': '任务已提交到Midscene微服务',
            })
        except httpx.ConnectError:
            execution.status = 'failed'
            execution.error_message = 'Midscene微服务未启动'
            execution.finished_at = timezone.now()
            execution.save()
            case.last_status = 'failed'
            case.last_result = 'Midscene微服务未启动'
            case.save(update_fields=['last_status', 'last_result'])
            return Response({
                'error': 'Midscene微服务未启动，请检查 midscene-service 是否运行',
                'execution_id': execution.id,
                'status': 'failed',
            })
        except Exception as e:
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.finished_at = timezone.now()
            execution.save()
            case.last_status = 'failed'
            case.last_result = str(e)[:500]
            case.save(update_fields=['last_status', 'last_result'])
            return Response({
                'error': f'提交失败: {str(e)}',
                'execution_id': execution.id,
                'status': 'failed',
            })

    # ---- 执行结果回调（微服务调用，免认证） ----
    @action(detail=True, methods=['post'], url_path='callback', permission_classes=[AllowAny])
    def callback(self, request, pk=None):
        """微服务执行完成后的回调"""
        case = self.get_queryset().filter(pk=pk).first()
        if not case:
            return Response({'error': '用例不存在'}, status=status.HTTP_404_NOT_FOUND)

        execution_id = request.data.get('execution_id')
        task_status = request.data.get('status')
        result_data = request.data.get('result') or {}
        error_msg = request.data.get('error') or ''
        report_url = request.data.get('report_url') or ''
        report_file = request.data.get('report_file') or ''

        execution = MidsceneExecution.objects.filter(id=execution_id).first()
        if execution:
            execution.status = 'passed' if task_status == 'completed' else 'failed'
            # 保存步骤结果
            if isinstance(result_data, dict) and 'step_results' in result_data:
                execution.step_results = result_data['step_results']
            execution.logs = json.dumps(result_data, ensure_ascii=False) if isinstance(result_data, dict) else str(result_data)[:2000]
            execution.error_message = error_msg
            execution.finished_at = timezone.now()
            if execution.started_at and execution.finished_at:
                execution.duration = (execution.finished_at - execution.started_at).total_seconds()
            # 保存回放报告信息
            execution.report_url = report_url
            execution.report_file = report_file
            execution.save()

        # 回写用例状态
        case.last_status = 'passed' if task_status == 'completed' else 'failed'
        case.last_result = error_msg or (json.dumps(result_data, ensure_ascii=False)[:500] if result_data else '')
        case.save(update_fields=['last_status', 'last_result', 'updated_at'])

        # 触发通知：查找关联此用例的活跃定时任务
        try:
            from apps.ui_automation.models import AiScheduledTask
            success = (task_status == 'completed')
            related_tasks = AiScheduledTask.objects.filter(
                midscene_case=case, status='ACTIVE'
            ).select_related('midscene_case')
            for task in related_tasks:
                # 更新任务统计
                if success:
                    task.last_result = {'status': 'success', 'message': '执行成功'}
                    task.error_message = ''
                else:
                    task.failed_runs += 1
                    task.last_result = {'status': 'failed', 'message': error_msg or '执行失败'}
                    task.error_message = (error_msg or '')[:500]
                task.save()
                _send_ai_task_notification(task, success=success)
        except Exception as notify_err:
            logger.error(f"发送AI任务通知失败: {notify_err}")

        return Response({'message': '回调已处理'})

    # ---- 查询执行状态 ----
    @action(detail=False, methods=['get'], url_path='execution-status')
    def execution_status(self, request):
        """查询Midscene执行状态（主动从微服务同步）"""
        task_id = request.query_params.get('task_id')
        execution_id = request.query_params.get('execution_id')

        execution = None
        if execution_id:
            execution = MidsceneExecution.objects.filter(id=execution_id).first()

        if execution:
            # 如果Django侧还是running，主动去微服务查真实状态并同步
            if execution.status == 'running':
                synced = self._sync_from_microservice(execution)
                if synced:
                    execution.refresh_from_db()

            return Response({
                'execution_id': execution.id,
                'case_id': execution.case_id,
                'case_name': execution.case.name if execution.case else '',
                'status': execution.status,
                'duration': execution.duration,
                'error_message': execution.error_message,
                'started_at': execution.started_at,
                'finished_at': execution.finished_at,
                'step_results': execution.step_results,
                'report_url': execution.report_url,
                'logs': execution.logs[:2000] if execution.logs else '',
            })

        # 从微服务查
        if task_id:
            try:
                with httpx.Client(timeout=10) as client:
                    resp = client.get(f'{MIDSCENE_SERVICE_URL}/task/{task_id}')
                    resp.raise_for_status()
                    return Response(resp.json())
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'error': '请提供execution_id或task_id'}, status=status.HTTP_400_BAD_REQUEST)

    def _sync_from_microservice(self, execution):
        """主动从微服务同步执行状态到Django"""
        try:
            # 用case_id构造微服务回调结果来查找最新task
            with httpx.Client(timeout=5) as client:
                resp = client.get(f'{MIDSCENE_SERVICE_URL}/tasks')
                resp.raise_for_status()
                tasks = resp.json()

            # 找最近完成的、与该execution时间匹配的task
            from datetime import datetime, timedelta
            exec_time = execution.started_at
            matching_task = None
            for t in tasks:
                if t.get('status') not in ('completed', 'failed'):
                    continue
                try:
                    task_time = datetime.fromisoformat(t['created_at'].replace('Z', '+00:00'))
                    if task_time >= exec_time - timedelta(seconds=5):
                        matching_task = t
                        break  # tasks按时间倒序，第一个匹配的就是最新的
                except (ValueError, KeyError):
                    continue

            if not matching_task:
                return False

            # 获取完整task详情
            task_id = matching_task['task_id']
            with httpx.Client(timeout=5) as client:
                resp = client.get(f'{MIDSCENE_SERVICE_URL}/task/{task_id}')
                resp.raise_for_status()
                task_data = resp.json()

            if task_data.get('status') in ('completed', 'failed'):
                # 同步状态到Django
                execution.status = 'passed' if task_data['status'] == 'completed' else 'failed'
                execution.error_message = task_data.get('error') or ''
                execution.finished_at = timezone.now()

                result = task_data.get('result') or {}
                if isinstance(result, dict) and 'step_results' in result:
                    execution.step_results = result['step_results']
                execution.logs = json.dumps(task_data.get('logs') or [], ensure_ascii=False)

                if execution.started_at and execution.finished_at:
                    execution.duration = (execution.finished_at - execution.started_at).total_seconds()

                report_url = task_data.get('report_url') or ''
                execution.report_url = report_url
                execution.report_file = ''
                if report_url and '/report/' in report_url:
                    report_filename = report_url.split('/report/')[-1]
                    execution.report_file = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        '..', '..', 'midscene-service', 'midscene_run', 'report', report_filename
                    )

                execution.save()

                # 更新用例状态
                case = execution.case
                if case:
                    case.last_status = execution.status
                    case.last_result = execution.error_message or json.dumps(result, ensure_ascii=False)[:500] if result else ''
                    case.save(update_fields=['last_status', 'last_result', 'updated_at'])

                return True
        except Exception as e:
            logger.error(f'同步微服务状态失败: {e}')

        return False


# ============================================================================
# 执行记录
# ============================================================================

class MidsceneExecutionViewSet(viewsets.ModelViewSet):
    """Midscene执行记录"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MidsceneExecution.objects.select_related('case', 'case__project', 'executed_by')

    def list(self, request):
        case_id = request.query_params.get('case_id')
        project_id = request.query_params.get('project_id')
        platform = request.query_params.get('platform')
        status_filter = request.query_params.get('status')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        # 报告汇总模式
        report_only = request.query_params.get('report_only') == 'true'

        qs = self.get_queryset()
        if case_id:
            qs = qs.filter(case_id=case_id)
        if project_id:
            qs = qs.filter(case__project_id=project_id)
        if platform:
            qs = qs.filter(case__platform=platform)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if report_only:
            qs = qs.exclude(report_url='')

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        data = []
        for e in qs.order_by('-started_at')[start:end]:
            data.append({
                'id': e.id,
                'case_id': e.case_id,
                'case_name': e.case.name if e.case else '',
                'platform': e.case.platform if e.case else '',
                'project_id': e.case.project_id if e.case else None,
                'project_name': e.case.project.name if e.case and e.case.project else '',
                'status': e.status,
                'duration': e.duration,
                'error_message': e.error_message,
                'report_url': e.report_url,
                'report_file': e.report_file,
                'started_at': e.started_at,
                'finished_at': e.finished_at,
                'step_results': e.step_results,
                'executed_by': e.executed_by.username if e.executed_by else None,
            })
        return Response({'results': data, 'count': total, 'page': page, 'page_size': page_size})

    def retrieve(self, request, pk=None):
        execution = self.get_queryset().filter(pk=pk).first()
        if not execution:
            return Response({'error': '记录不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'id': execution.id,
            'case_id': execution.case_id,
            'case_name': execution.case.name if execution.case else '',
            'status': execution.status,
            'step_results': execution.step_results,
            'logs': execution.logs,
            'error_message': execution.error_message,
            'screenshot_urls': execution.screenshot_urls,
            'report_url': execution.report_url,
            'report_file': execution.report_file,
            'duration': execution.duration,
            'started_at': execution.started_at,
            'finished_at': execution.finished_at,
            'executed_by': execution.executed_by.username if execution.executed_by else None,
        })


# ──────────────────────────────────────────────
# AI 自动化定时任务
# ──────────────────────────────────────────────

def _build_midscene_payload(case, execution_id):
    """
    构建 Midscene 微服务执行 payload（复用 run_case 的逻辑）
    """
    # 获取模型配置
    from apps.requirement_analysis.models import AIModelConfig
    config_obj = AIModelConfig.objects.filter(role='midscene_web', is_active=True).first()
    if not config_obj:
        config_obj = AIModelConfig.objects.filter(role='browser_use_text', is_active=True).first()

    model_config = {}
    if config_obj:
        model_name = (config_obj.model_name or '').lower()
        if 'qwen3.6' in model_name:
            model_family = 'qwen3.6'
        elif 'qwen3.5' in model_name:
            model_family = 'qwen3.5'
        elif 'qwen3' in model_name and 'vl' in model_name:
            model_family = 'qwen3-vl'
        elif 'qwen3' in model_name:
            model_family = 'qwen3'
        elif 'qwen2.5' in model_name and 'vl' in model_name:
            model_family = 'qwen2.5-vl'
        elif 'qwen' in model_name and 'vl' in model_name:
            model_family = 'qwen2.5-vl'
        elif 'qwen' in model_name:
            model_family = 'qwen3'
        elif 'doubao-seed' in model_name or 'seed' in model_name:
            model_family = 'doubao-seed'
        elif 'doubao' in model_name and 'vision' in model_name:
            model_family = 'doubao-vision'
        elif 'doubao' in model_name:
            model_family = 'doubao-vision'
        elif 'gemini' in model_name:
            model_family = 'gemini'
        elif 'glm' in model_name and 'auto-glm' in model_name:
            model_family = 'auto-glm'
        elif 'glm' in model_name:
            model_family = 'glm-v'
        elif 'gpt' in model_name:
            model_family = 'gpt-5'
        elif 'kimi3' in model_name:
            model_family = 'kimi3'
        elif 'kimi' in model_name:
            model_family = 'kimi'
        elif 'mimo' in model_name or 'xiaomi' in model_name:
            model_family = 'xiaomi-mimo'
        else:
            model_family = 'qwen3-vl'

        model_config = {
            'api_key': config_obj.api_key,
            'base_url': config_obj.base_url,
            'model_name': config_obj.model_name,
            'model_family': model_family,
        }

    steps = []
    for step in (case.steps or []):
        step_type = step.get('type', 'action')
        instruction = step.get('instruction', '')
        if step_type == 'assert':
            midscene_type = 'aiAssert'
        elif step_type == 'action':
            midscene_type = 'aiAct'
        else:
            midscene_type = step_type
        steps.append({
            'type': midscene_type,
            'instruction': instruction,
        })

    payload = {
        'platform': case.platform or 'web',
        'url': case.url or None,
        'steps': steps,
        'headless': case.headless,
        'viewport': {
            'width': case.viewport_width or 1280,
            'height': case.viewport_height or 768,
        },
        'model_config': model_config,
        'callback_url': f'http://localhost:8000/api/ui-automation/midscene-cases/{case.id}/callback/',
        'execution_id': execution_id,
        'user_agent': case.user_agent or None,
        'device_scale_factor': case.device_scale_factor or None,
        'cookie_file': case.cookie_file or None,
        'wait_for_network_idle': {
            'timeout': case.wait_for_network_idle_timeout,
            'continue_on_error': case.continue_on_network_idle_error,
        } if case.wait_for_network_idle_timeout else None,
        'app_config': {
            'device_id': case.device_id or '',
            'package_name': case.package_name or '',
            'app_activity': case.app_activity or '',
        } if case.platform == 'app' else None,
    }
    return payload


class AiScheduledTaskViewSet(viewsets.ModelViewSet):
    """AI自动化定时任务视图集"""
    queryset = AiScheduledTask.objects.all()
    serializer_class = AiScheduledTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['task_type', 'status', 'trigger_type', 'project']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'next_run_time', 'last_run_time']
    ordering = ['-created_at']

    def get_queryset(self):
        """只显示用户有权限访问的项目的定时任务"""
        user = self.request.user
        accessible_projects = AiProject.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        return AiScheduledTask.objects.filter(project__in=accessible_projects)

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        logger.info(f"AI定时任务已创建: {instance.name} (id={instance.id})")

    def perform_update(self, serializer):
        instance = serializer.save()
        logger.info(f"AI定时任务已更新: {instance.name} (id={instance.id})")

    def perform_destroy(self, instance):
        logger.info(f"AI定时任务已删除: {instance.name} (id={instance.id})")
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

    @action(detail=True, methods=['post'], url_path='run-now')
    def run_now(self, request, pk=None):
        """立即运行任务 — POST 到 Midscene 微服务，异步回调更新结果"""
        task = self.get_object()

        try:
            if not task.midscene_case:
                return Response({'error': '该任务未配置Midscene用例'}, status=status.HTTP_400_BAD_REQUEST)

            case = task.midscene_case

            # 创建执行记录
            execution = MidsceneExecution.objects.create(
                case=case,
                status='running',
                executed_by=task.created_by,
            )
            case.last_status = 'running'
            case.save(update_fields=['last_status'])

            # 更新任务统计
            task.last_run_time = timezone.now()
            task.total_runs += 1
            task.next_run_time = task.calculate_next_run()
            task.save()

            # 构建并发送 Midscene 执行请求
            payload = _build_midscene_payload(case, execution.id)

            try:
                with httpx.Client(timeout=10) as client:
                    resp = client.post(f'{MIDSCENE_SERVICE_URL}/execute', json=payload)
                    resp.raise_for_status()
                    data = resp.json()

                return Response({
                    'message': '任务已提交到Midscene微服务',
                    'task_id': task.id,
                    'task_name': task.name,
                    'execution_id': execution.id,
                    'midscene_task_id': data.get('task_id'),
                    'status': 'submitted',
                }, status=status.HTTP_200_OK)

            except httpx.ConnectError:
                execution.status = 'failed'
                execution.error_message = 'Midscene微服务未启动'
                execution.finished_at = timezone.now()
                execution.save()
                case.last_status = 'failed'
                case.last_result = 'Midscene微服务未启动'
                case.save(update_fields=['last_status', 'last_result'])

                task.failed_runs += 1
                task.last_result = {'status': 'failed', 'message': 'Midscene微服务未启动'}
                task.error_message = 'Midscene微服务未启动'
                task.save()

                return Response({
                    'error': 'Midscene微服务未启动，请检查 midscene-service 是否运行',
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f'AI定时任务执行失败: {str(e)}', exc_info=True)
            return Response({'error': f'执行失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ──────────────────────────────────────────────
# AI 通知日志 + 通知发送逻辑
# ──────────────────────────────────────────────

def _send_ai_task_notification(task, success):
    """发送AI定时任务执行通知（复用 UnifiedNotificationConfig）"""
    try:
        logger.info(f"准备发送AI任务 {task.id} 的通知，执行结果: {'成功' if success else '失败'}")

        if success and not task.notify_on_success:
            return
        if not success and not task.notify_on_failure:
            return
        if not task.notification_type:
            return

        if task.notification_type in ['webhook', 'both']:
            _send_ai_webhook_notification(task, success)

        if task.notification_type in ['email', 'both']:
            _send_ai_email_notification(task, success)

    except Exception as e:
        logger.error(f"发送AI任务通知失败: {str(e)}", exc_info=True)


def _send_ai_webhook_notification(task, success):
    """发送AI任务Webhook通知"""
    try:
        import requests as req_lib
        import json

        from apps.core.models import UnifiedNotificationConfig
        all_webhook_configs = UnifiedNotificationConfig.objects.filter(
            config_type__in=['webhook_wechat', 'webhook_feishu', 'webhook_dingtalk'],
            is_active=True
        )

        all_webhook_bots = []
        for config in all_webhook_configs:
            bots = config.get_webhook_bots()
            if bots:
                for bot in bots:
                    if bot.get('enabled', True):
                        all_webhook_bots.append(bot)

        if not all_webhook_bots:
            logger.warning("没有找到任何启用的webhook机器人配置")
            return

        status_text = '成功' if success else '失败'
        local_run_time = timezone.localtime(task.last_run_time).strftime(
            '%Y-%m-%d %H:%M:%S') if task.last_run_time else '未知'
        case_name = task.midscene_case.name if task.midscene_case else '未知'

        for bot in all_webhook_bots:
            if not bot.get('enabled', True) or not bot.get('webhook_url'):
                continue

            bot_type = bot.get('type', 'unknown')
            webhook_url = bot['webhook_url']

            detail_content = f"""任务名称: {task.name}

执行状态: {status_text}

执行时间: {local_run_time}

关联用例: {case_name}"""

            last_result = task.last_result or {}
            result_message = last_result.get('message', '')
            if result_message:
                detail_content += f"\n\n执行结果: {result_message}"

            if bot_type == 'wechat':
                message_data = {
                    "msgtype": "markdown",
                    "markdown": {
                        "content": f"""**AI自动化定时任务执行{status_text}**\n\n{detail_content}"""
                    }
                }
            elif bot_type == 'feishu':
                message_data = {
                    "msg_type": "interactive",
                    "card": {
                        "elements": [{
                            "tag": "div",
                            "text": {
                                "content": f"**AI自动化定时任务执行{status_text}**\n\n{detail_content}",
                                "tag": "lark_md"
                            }
                        }],
                        "header": {
                            "title": {
                                "content": f"AI自动化定时任务执行{status_text}",
                                "tag": "plain_text"
                            },
                            "template": "green" if success else "red"
                        }
                    }
                }
            elif bot_type == 'dingtalk':
                message_data = {
                    "msgtype": "markdown",
                    "markdown": {
                        "title": f"AI自动化定时任务执行{status_text}",
                        "text": f"""**AI自动化定时任务执行{status_text}**\n\n{detail_content}"""
                    }
                }
                secret = bot.get('secret')
                if secret:
                    import time, hmac, hashlib, base64, urllib.parse
                    timestamp = str(round(time.time() * 1000))
                    string_to_sign = f'{timestamp}\n{secret}'
                    hmac_code = hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
                    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
                    if '?' in webhook_url:
                        webhook_url += f'&timestamp={timestamp}&sign={sign}'
                    else:
                        webhook_url += f'?timestamp={timestamp}&sign={sign}'
            else:
                continue

            try:
                response = req_lib.post(webhook_url, json=message_data, headers={'Content-Type': 'application/json'}, timeout=10)
                if response.status_code == 200:
                    AiNotificationLog.objects.create(
                        task=task, task_name=task.name, task_type=task.task_type,
                        notification_type='task_execution',
                        sender_name='系统Webhook通知', sender_email='system@notification.com',
                        recipient_info=[{'name': bot.get('name', 'Unknown'), 'webhook_url': webhook_url}],
                        webhook_bot_info=bot,
                        notification_content=json.dumps(message_data, ensure_ascii=False),
                        status='success', response_info={'status_code': response.status_code, 'response': response.text},
                        sent_at=timezone.now()
                    )
                else:
                    AiNotificationLog.objects.create(
                        task=task, task_name=task.name, task_type=task.task_type,
                        notification_type='task_execution',
                        sender_name='系统Webhook通知', sender_email='system@notification.com',
                        recipient_info=[{'name': bot.get('name', 'Unknown'), 'webhook_url': webhook_url}],
                        webhook_bot_info=bot,
                        notification_content=json.dumps(message_data, ensure_ascii=False),
                        status='failed', error_message=f'HTTP {response.status_code}: {response.text}',
                        response_info={'status_code': response.status_code, 'response': response.text}
                    )
            except Exception as e:
                AiNotificationLog.objects.create(
                    task=task, task_name=task.name, task_type=task.task_type,
                    notification_type='task_execution',
                    sender_name='系统Webhook通知', sender_email='system@notification.com',
                    recipient_info=[{'name': bot.get('name', 'Unknown'), 'webhook_url': webhook_url}],
                    webhook_bot_info=bot,
                    notification_content=json.dumps(message_data, ensure_ascii=False),
                    status='failed', error_message=str(e)
                )

    except Exception as e:
        logger.error(f"发送AI Webhook通知失败: {str(e)}", exc_info=True)


def _send_ai_email_notification(task, success):
    """发送AI任务邮件通知"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from django.conf import settings

        recipients = []
        if task.notify_emails:
            recipients = task.notify_emails if isinstance(task.notify_emails, list) else [task.notify_emails]
        if not recipients:
            return

        email_config = None
        try:
            from apps.core.models import UnifiedNotificationConfig
            email_config = UnifiedNotificationConfig.objects.filter(config_type='email', is_active=True).first()
        except Exception:
            pass

        if email_config and email_config.email_smtp_host:
            smtp_host = email_config.email_smtp_host
            smtp_port = email_config.email_smtp_port or 465
            use_ssl = email_config.email_use_ssl
            use_tls = email_config.email_use_tls
            smtp_user = email_config.email_host_user
            smtp_password = email_config.email_host_password
            from_email = email_config.email_from or email_config.email_host_user
        else:
            smtp_host = settings.EMAIL_HOST
            smtp_port = settings.EMAIL_PORT
            use_ssl = settings.EMAIL_USE_SSL
            use_tls = settings.EMAIL_USE_TLS
            smtp_user = settings.EMAIL_HOST_USER
            smtp_password = settings.EMAIL_HOST_PASSWORD
            from_email = settings.DEFAULT_FROM_EMAIL

        status_text = '成功' if success else '失败'
        case_name = task.midscene_case.name if task.midscene_case else '未知'
        local_run_time = timezone.localtime(task.last_run_time).strftime('%Y-%m-%d %H:%M:%S') if task.last_run_time else '未知'

        subject = f"AI自动化定时任务执行{status_text}: {task.name}"
        message = f"""
任务名称: {task.name}
执行状态: {status_text}
执行时间: {local_run_time}
关联用例: {case_name}

执行结果:
{(task.last_result or {}).get('message', '无详细信息')}

错误信息:
{task.error_message or '无错误信息'}
        """

        try:
            msg = MIMEText(message, 'plain', 'utf-8')
            msg['From'] = from_email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject

            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
                if use_tls:
                    server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.sendmail(from_email, recipients, msg.as_string())
            server.quit()

            AiNotificationLog.objects.create(
                task=task, task_name=task.name, task_type=task.task_type,
                notification_type='task_execution',
                sender_name='系统邮件通知', sender_email=from_email,
                recipient_info=[{'email': email} for email in recipients],
                notification_content=message,
                status='success', sent_at=timezone.now()
            )
        except Exception as e:
            AiNotificationLog.objects.create(
                task=task, task_name=task.name, task_type=task.task_type,
                notification_type='task_execution',
                sender_name='系统邮件通知', sender_email=from_email,
                recipient_info=[{'email': email} for email in recipients],
                notification_content=f"发送邮件通知失败: {str(e)}",
                status='failed', error_message=str(e)
            )

    except Exception as e:
        logger.error(f"发送AI邮件通知失败: {str(e)}", exc_info=True)


class AiNotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """AI自动化通知日志视图集（只读）"""
    queryset = AiNotificationLog.objects.all()
    serializer_class = AiNotificationLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'notification_type', 'task']
    search_fields = ['task_name', 'notification_content']
    ordering_fields = ['created_at', 'sent_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """重试发送通知"""
        log = self.get_object()
        if log.status == 'failed':
            log.retry_count += 1
            log.is_retried = True
            log.save()
            return Response({'message': '通知已加入重试队列'})
        return Response({'error': '只能重试失败的通知'}, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# AI 测试计划 ViewSet
# ──────────────────────────────────────────────

class AiTestPlanViewSet(viewsets.ModelViewSet):
    """AI自动化测试计划视图集"""
    queryset = AiTestPlan.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'execution_status', 'platform']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return AiTestPlanCreateSerializer
        if self.action in ('update', 'partial_update'):
            return AiTestPlanUpdateSerializer
        return AiTestPlanSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def plan_items(self, request, pk=None):
        """获取计划项列表"""
        plan = self.get_object()
        items = plan.plan_items.all().select_related('midscene_case')
        serializer = AiTestPlanItemSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """添加单个计划项"""
        plan = self.get_object()
        midscene_case_id = request.data.get('midscene_case')

        if not midscene_case_id:
            return Response({'error': '请指定Midscene用例'}, status=status.HTTP_400_BAD_REQUEST)

        # 去重检查
        if AiTestPlanItem.objects.filter(test_plan=plan, midscene_case_id=midscene_case_id).exists():
            return Response({'error': '该用例已在计划中'}, status=status.HTTP_400_BAD_REQUEST)

        max_order = plan.plan_items.aggregate(max_order=Max('order'))['max_order'] or 0
        item = AiTestPlanItem.objects.create(
            test_plan=plan,
            midscene_case_id=midscene_case_id,
            order=max_order + 1
        )
        self._update_plan_counts(plan)
        return Response(AiTestPlanItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def add_items_batch(self, request, pk=None):
        """批量添加计划项"""
        plan = self.get_object()
        case_ids = request.data.get('midscene_case_ids', [])

        if not case_ids:
            return Response({'error': '请提供用例ID列表'}, status=status.HTTP_400_BAD_REQUEST)

        max_order = plan.plan_items.aggregate(max_order=Max('order'))['max_order'] or 0
        existing = set(AiTestPlanItem.objects.filter(
            test_plan=plan, midscene_case_id__in=case_ids
        ).values_list('midscene_case_id', flat=True))

        created = []
        for i, case_id in enumerate(case_ids):
            if case_id in existing:
                continue
            item = AiTestPlanItem.objects.create(
                test_plan=plan,
                midscene_case_id=case_id,
                order=max_order + i + 1
            )
            created.append(item)

        self._update_plan_counts(plan)
        return Response(AiTestPlanItemSerializer(created, many=True).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='remove_item/(?P<item_id>[^/.]+)')
    def remove_item(self, request, pk=None, item_id=None):
        """移除计划项"""
        plan = self.get_object()
        item = plan.plan_items.filter(pk=item_id).first()
        if not item:
            return Response({'error': '计划项不存在'}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        self._update_plan_counts(plan)
        return Response({'message': '已移除'})

    @action(detail=True, methods=['post'])
    def update_item_order(self, request, pk=None):
        """更新计划项顺序"""
        plan = self.get_object()
        item_orders = request.data.get('item_orders', [])
        for item_data in item_orders:
            AiTestPlanItem.objects.filter(
                pk=item_data.get('id'), test_plan=plan
            ).update(order=item_data.get('order', 0))
        return Response({'message': '顺序已更新'})

    @action(detail=True, methods=['post'])
    def run_plan(self, request, pk=None):
        """执行AI测试计划"""
        plan = self.get_object()
        items = plan.plan_items.all().select_related('midscene_case')

        if not items.exists():
            return Response({'error': '计划中没有用例'}, status=status.HTTP_400_BAD_REQUEST)

        plan.execution_status = 'running'
        plan.save(update_fields=['execution_status'])

        # 逐个提交用例到Midscene微服务执行
        results = []
        for item in items:
            case = item.midscene_case
            if not case:
                continue

            try:
                execution = MidsceneExecution.objects.create(
                    case=case,
                    status='running',
                    executed_by=request.user,
                )
                case.last_status = 'running'
                case.save(update_fields=['last_status'])

                payload = _build_midscene_payload(case, execution.id)

                try:
                    import httpx
                    with httpx.Client(timeout=10) as client:
                        resp = client.post(f'{MIDSCENE_SERVICE_URL}/execute', json=payload)
                        resp.raise_for_status()
                    results.append({'case_id': case.id, 'case_name': case.name, 'status': 'submitted'})
                except Exception as e:
                    execution.status = 'failed'
                    execution.error_message = str(e)
                    execution.finished_at = timezone.now()
                    execution.save()
                    case.last_status = 'failed'
                    case.last_result = str(e)[:500]
                    case.save(update_fields=['last_status', 'last_result'])
                    results.append({'case_id': case.id, 'case_name': case.name, 'status': 'failed', 'error': str(e)})

            except Exception as e:
                results.append({'case_id': case.id if case else None, 'status': 'error', 'error': str(e)})

        return Response({
            'message': '计划已提交执行',
            'execution_status': 'running',
            'results': results
        })

    def _update_plan_counts(self, plan):
        """更新计划的用例计数"""
        plan.total_cases = plan.plan_items.count()
        plan.save(update_fields=['total_cases'])
