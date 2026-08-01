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
    AiScheduledTask,
)
from .serializers import (
    AiProjectSerializer, AiProjectCreateSerializer, AiProjectUpdateSerializer,
    AiScheduledTaskSerializer,
)
from django.db import models
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
        result_data = request.data.get('result', {})
        error_msg = request.data.get('error', '')
        report_url = request.data.get('report_url', '')
        report_file = request.data.get('report_file', '')

        execution = MidsceneExecution.objects.filter(id=execution_id).first()
        if execution:
            execution.status = 'passed' if task_status == 'completed' else 'failed'
            # 保存步骤结果
            if isinstance(result_data, dict) and 'step_results' in result_data:
                execution.step_results = result_data['step_results']
            execution.logs = json.dumps(result_data, ensure_ascii=False) if isinstance(result_data, dict) else str(result_data)
            execution.error_message = error_msg
            execution.finished_at = timezone.now()
            if execution.started_at and execution.finished_at:
                execution.duration = (execution.finished_at - execution.started_at).total_seconds()
            # 保存回放报告信息
            if report_url:
                execution.report_url = report_url
            if report_file:
                execution.report_file = report_file
            execution.save()

        # 回写用例状态
        case.last_status = 'passed' if task_status == 'completed' else 'failed'
        case.last_result = error_msg or (json.dumps(result_data, ensure_ascii=False)[:500] if result_data else '')
        case.save(update_fields=['last_status', 'last_result', 'updated_at'])

        return Response({'message': '回调已处理'})

    # ---- 查询执行状态 ----
    @action(detail=False, methods=['get'], url_path='execution-status')
    def execution_status(self, request):
        """查询Midscene执行状态（从微服务获取）"""
        task_id = request.query_params.get('task_id')
        execution_id = request.query_params.get('execution_id')

        # 优先从本地数据库查
        if execution_id:
            execution = MidsceneExecution.objects.filter(id=execution_id).first()
            if execution:
                return Response({
                    'execution_id': execution.id,
                    'case_id': execution.case_id,
                    'case_name': execution.case.name,
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


# ============================================================================
# 执行记录
# ============================================================================

class MidsceneExecutionViewSet(viewsets.ModelViewSet):
    """Midscene执行记录"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MidsceneExecution.objects.select_related('case', 'executed_by')

    def list(self, request):
        case_id = request.query_params.get('case_id')
        qs = self.get_queryset()
        if case_id:
            qs = qs.filter(case_id=case_id)

        data = []
        for e in qs.order_by('-started_at')[:50]:
            data.append({
                'id': e.id,
                'case_id': e.case_id,
                'case_name': e.case.name if e.case else '',
                'status': e.status,
                'duration': e.duration,
                'error_message': e.error_message,
                'report_url': e.report_url,
                'started_at': e.started_at,
                'finished_at': e.finished_at,
                'step_results': e.step_results,
                'executed_by': e.executed_by.username if e.executed_by else None,
            })
        return Response(data)

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
