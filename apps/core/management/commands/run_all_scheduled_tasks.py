from django.core.management.base import BaseCommand
from django.utils import timezone
import time
import logging
import sys

# 避免长循环中的数据库连接超时
from django.db import close_old_connections

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '运行所有模块的定时任务调度器（API测试 + UI自动化 + APP自动化）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='检查间隔（秒），默认60秒'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='只执行一次检查，不循环'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']

        self.stdout.write(self.style.SUCCESS(f"{'='*60}"))
        self.stdout.write(self.style.SUCCESS("启动统一定时任务调度器"))
        self.stdout.write(self.style.SUCCESS(f"检查间隔: {interval}秒"))
        self.stdout.write(self.style.SUCCESS(f"调度模块: API测试 + UI自动化 + APP自动化 + AI自动化"))
        self.stdout.write(self.style.SUCCESS(f"{'='*60}"))

        while True:
            # 每次循环前关闭旧连接，防止 MySQL 超时断开
            close_old_connections()
            try:
                # 统一使用本地时区，避免UTC导致调度延后8小时问题
                now = timezone.localtime(timezone.now())
                self.stdout.write(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] 开始检查任务...")

                # 调度 API 测试模块的定时任务
                api_count = self.schedule_api_tasks()

                # 调度 UI 自动化模块的定时任务
                ui_count = self.schedule_ui_tasks()

                # 调度 APP 自动化模块的定时任务
                app_count = self.schedule_app_tasks()

                # 调度 AI 自动化模块的定时任务
                ai_count = self.schedule_ai_tasks()

                total_count = api_count + ui_count + app_count + ai_count
                if total_count > 0:
                    self.stdout.write(self.style.SUCCESS(f"✓ 本次调度执行了 {total_count} 个任务 (API: {api_count}, UI: {ui_count}, APP: {app_count}, AI: {ai_count})"))
                else:
                    self.stdout.write("  没有需要执行的任务")

                if run_once:
                    self.stdout.write(self.style.WARNING("单次执行模式，调度器退出"))
                    break

                self.stdout.write(f"等待 {interval} 秒后进行下一次检查...")
                time.sleep(interval)

            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("\n\n调度器已停止"))
                break
            except Exception as e:
                logger.error(f"调度器运行出错: {e}", exc_info=True)
                self.stdout.write(self.style.ERROR(f"调度器运行出错: {e}"))
                if run_once:
                    break
                self.stdout.write(f"等待 {interval} 秒后重试...")
                time.sleep(interval)

    def schedule_api_tasks(self):
        """调度 API 测试模块的定时任务"""
        try:
            # 确保连接有效，简单地关闭旧连接让 Django 重连
            close_old_connections()
            from apps.api_testing.models import ScheduledTask
            from apps.api_testing.views import ScheduledTaskViewSet

            # 获取所有活跃的定时任务
            active_tasks = ScheduledTask.objects.filter(status='ACTIVE')
            executed_count = 0

            # 显示所有活跃任务的调试信息
            if active_tasks.exists():
                now = timezone.now()
                self.stdout.write(f"  [API] 活跃任务数: {active_tasks.count()}")
                for task in active_tasks:
                    if task.next_run_time:
                        time_diff = (task.next_run_time - now).total_seconds()
                        if time_diff > 0:
                            self.stdout.write(f"        - {task.name}: 距下次执行还有 {int(time_diff)} 秒")
                        else:
                            self.stdout.write(f"        - {task.name}: 应该立即执行！")
                    else:
                        self.stdout.write(f"        - {task.name}: 未设置下次执行时间")

            for task in active_tasks:
                if task.should_run_now():
                    self.stdout.write(f"  [API] 执行任务: {task.name}")
                    self.stdout.write(f"       类型: {task.get_task_type_display() if hasattr(task, 'get_task_type_display') else task.task_type}, 触发方式: {task.get_trigger_type_display() if hasattr(task, 'get_trigger_type_display') else task.trigger_type}")
                    try:
                        # 创建执行日志
                        from apps.api_testing.models import TaskExecutionLog
                        execution_log = TaskExecutionLog.objects.create(
                            task=task,
                            status='PENDING'
                        )

                        # 调用任务执行方法
                        view = ScheduledTaskViewSet()
                        view._execute_task_async(task, execution_log)

                        executed_count += 1
                        self.stdout.write(self.style.SUCCESS(f"    ✓ 任务 {task.name} 已启动"))

                    except Exception as e:
                        logger.error(f"执行API任务 {task.name} 时出错: {e}", exc_info=True)
                        self.stdout.write(self.style.ERROR(f"    ✗ 任务 {task.name} 执行失败: {e}"))

            return executed_count

        except Exception as e:
            logger.error(f"调度API任务时出错: {e}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"[API] 调度失败: {e}"))
            return 0

    def schedule_ui_tasks(self):
        """调度 UI 自动化模块的定时任务"""
        try:
            from apps.ui_automation.models import UiScheduledTask

            # 获取所有活跃的定时任务
            active_tasks = UiScheduledTask.objects.filter(status='ACTIVE')
            executed_count = 0

            # 显示所有活跃任务的调试信息
            if active_tasks.exists():
                now = timezone.now()
                self.stdout.write(f"  [UI]  活跃任务数: {active_tasks.count()}")
                for task in active_tasks:
                    if task.next_run_time:
                        time_diff = (task.next_run_time - now).total_seconds()
                        if time_diff > 0:
                            self.stdout.write(f"        - {task.name}: 距下次执行还有 {int(time_diff)} 秒")
                        else:
                            self.stdout.write(f"        - {task.name}: 应该立即执行！")
                    else:
                        self.stdout.write(f"        - {task.name}: 未设置下次执行时间")

            for task in active_tasks:
                if task.should_run_now():
                    self.stdout.write(f"  [UI]  执行任务: {task.name}")
                    self.stdout.write(f"       类型: {task.get_task_type_display()}, 触发方式: {task.get_trigger_type_display()}")
                    try:
                        # 更新任务执行时间和次数，并立即计算下次运行时间
                        # 必须在启动线程前更新next_run_time，否则下一轮轮询会重复触发
                        task.last_run_time = timezone.now()
                        task.total_runs += 1
                        task.next_run_time = task.calculate_next_run()
                        task.save()

                        # 根据任务类型执行不同的逻辑
                        if task.task_type == 'TEST_PLAN':
                            # 执行测试计划
                            if not task.test_plan:
                                self.stdout.write(self.style.ERROR(f"    ✗ 任务 {task.name} 未配置测试计划"))
                                task.refresh_from_db()
                                task.next_run_time = task.calculate_next_run()
                                task.save()
                                continue

                            test_plan = task.test_plan
                            plan_items = test_plan.plan_items.all()
                            if plan_items.count() == 0:
                                self.stdout.write(self.style.ERROR(f"    ✗ 任务 {task.name} 的测试计划没有用例或套件"))
                                task.refresh_from_db()
                                task.next_run_time = task.calculate_next_run()
                                task.save()
                                continue

                            # 更新计划执行状态
                            test_plan.execution_status = 'running'
                            test_plan.save()

                            # 在后台线程中执行测试计划
                            import threading
                            from apps.ui_automation.plan_executor import PlanExecutor

                            def run_test_plan():
                                try:
                                    executor = PlanExecutor(
                                        test_plan=test_plan,
                                        engine=task.engine,
                                        browser=task.browser,
                                        headless=task.headless,
                                        executed_by=task.created_by
                                    )
                                    executor.run()

                                    # 刷新计划对象状态
                                    test_plan.refresh_from_db()

                                    # 重新加载任务并更新执行结果（next_run_time已在主线程中更新）
                                    task.refresh_from_db()
                                    if test_plan.execution_status == 'passed':
                                        task.successful_runs += 1
                                        task.last_result = {
                                            'status': 'success',
                                            'message': f'测试计划执行完成: {test_plan.passed_count}通过, {test_plan.failed_count}失败'
                                        }
                                        task.error_message = ''
                                    else:
                                        task.failed_runs += 1
                                        task.last_result = {
                                            'status': 'failed',
                                            'message': f'测试计划执行完成: {test_plan.passed_count}通过, {test_plan.failed_count}失败'
                                        }
                                        task.error_message = f'{test_plan.failed_count}个用例执行失败'
                                    task.save()

                                    logger.info(f"UI定时任务 {task.name} 执行完成")

                                    # 发送通知
                                    success = (test_plan.execution_status == 'passed')
                                    notification_setting = None
                                    if hasattr(task, 'notification_settings'):
                                        try:
                                            notification_setting = task.notification_settings.first()
                                        except Exception:
                                            pass

                                    if notification_setting and notification_setting.is_enabled:
                                        should_notify = (success and notification_setting.notify_on_success) or \
                                                       (not success and notification_setting.notify_on_failure)
                                        if should_notify:
                                            try:
                                                from apps.ui_automation.views import UiScheduledTaskViewSet
                                                viewset = UiScheduledTaskViewSet()
                                                viewset._send_task_notification(task, success=success)
                                            except Exception as notify_error:
                                                logger.error(f"发送UI定时任务 {task.name} 通知失败: {notify_error}")

                                except Exception as e:
                                    logger.error(f"UI定时任务 {task.name} 执行失败: {e}", exc_info=True)
                                    task.refresh_from_db()
                                    task.failed_runs += 1
                                    task.error_message = str(e)
                                    task.last_result = {
                                        'status': 'failed',
                                        'error': str(e)
                                    }
                                    task.save()

                                    # 发送失败通知
                                    notification_setting = None
                                    if hasattr(task, 'notification_settings'):
                                        try:
                                            notification_setting = task.notification_settings.first()
                                        except Exception:
                                            pass

                                    if notification_setting and notification_setting.is_enabled and notification_setting.notify_on_failure:
                                        try:
                                            from apps.ui_automation.views import UiScheduledTaskViewSet
                                            viewset = UiScheduledTaskViewSet()
                                            viewset._send_task_notification(task, success=False)
                                        except Exception as notify_error:
                                            logger.error(f"发送UI定时任务 {task.name} 失败通知失败: {notify_error}")

                            thread = threading.Thread(target=run_test_plan, daemon=True)
                            thread.start()

                        executed_count += 1
                        self.stdout.write(self.style.SUCCESS(f"    ✓ 任务 {task.name} 已启动"))

                    except Exception as e:
                        logger.error(f"执行UI任务 {task.name} 时出错: {e}", exc_info=True)
                        self.stdout.write(self.style.ERROR(f"    ✗ 任务 {task.name} 执行失败: {e}"))

            return executed_count

        except Exception as e:
            logger.error(f"调度UI任务时出错: {e}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"[UI] 调度失败: {e}"))
            return 0

    def schedule_app_tasks(self):
        """调度 APP 自动化模块的定时任务"""
        try:
            from apps.app_automation.models import AppScheduledTask, AppTestExecution

            active_tasks = AppScheduledTask.objects.filter(status='ACTIVE')
            executed_count = 0

            if active_tasks.exists():
                now = timezone.now()
                self.stdout.write(f"  [APP] 活跃任务数: {active_tasks.count()}")
                for task in active_tasks:
                    if task.next_run_time:
                        time_diff = (task.next_run_time - now).total_seconds()
                        if time_diff > 0:
                            self.stdout.write(f"        - {task.name}: 距下次执行还有 {int(time_diff)} 秒")
                        else:
                            self.stdout.write(f"        - {task.name}: 应该立即执行！")
                    else:
                        self.stdout.write(f"        - {task.name}: 未设置下次执行时间")

            for task in active_tasks:
                if task.should_run_now():
                    self.stdout.write(f"  [APP] 执行任务: {task.name}")
                    self.stdout.write(f"       类型: {task.get_task_type_display()}, 触发方式: {task.get_trigger_type_display()}")
                    try:
                        # 更新统计
                        task.last_run_time = timezone.now()
                        task.total_runs += 1
                        task.next_run_time = task.calculate_next_run()
                        task.save()

                        device = task.device
                        if not device:
                            self.stdout.write(self.style.ERROR(f"    ✗ 任务 {task.name} 未配置设备"))
                            continue

                        package_name = task.app_package.package_name if task.app_package else ''

                        if task.task_type == 'TEST_SUITE' and task.test_suite:
                            suite_cases = task.test_suite.suite_cases.select_related('test_case').all()
                            if not suite_cases.exists():
                                self.stdout.write(self.style.ERROR(f"    ✗ 套件 {task.test_suite.name} 无用例"))
                                continue

                            executions = []
                            for sc in suite_cases:
                                execution = AppTestExecution.objects.create(
                                    test_case=sc.test_case,
                                    test_suite=task.test_suite,
                                    device=device,
                                    user=task.created_by,
                                    status='pending'
                                )
                                executions.append(execution)

                            task.test_suite.execution_status = 'running'
                            task.test_suite.save(update_fields=['execution_status'])

                            from apps.app_automation.tasks import execute_app_suite_task
                            execute_app_suite_task.delay(
                                suite_id=task.test_suite.id,
                                execution_ids=[e.id for e in executions],
                                package_name=package_name,
                                scheduled_task_id=task.id,
                            )

                        elif task.task_type == 'TEST_CASE' and task.test_case:
                            execution = AppTestExecution.objects.create(
                                test_case=task.test_case,
                                device=device,
                                user=task.created_by,
                                status='pending'
                            )
                            from apps.app_automation.tasks import execute_app_test_task
                            celery_task = execute_app_test_task.delay(
                                execution.id,
                                package_name=package_name,
                                scheduled_task_id=task.id,
                            )
                            execution.task_id = celery_task.id
                            execution.save(update_fields=['task_id'])

                        else:
                            self.stdout.write(self.style.ERROR(f"    ✗ 任务 {task.name} 配置不完整"))
                            continue

                        executed_count += 1
                        self.stdout.write(self.style.SUCCESS(f"    ✓ 任务 {task.name} 已启动"))

                    except Exception as e:
                        logger.error(f"执行APP任务 {task.name} 时出错: {e}", exc_info=True)
                        self.stdout.write(self.style.ERROR(f"    ✗ 任务 {task.name} 执行失败: {e}"))

            return executed_count

        except Exception as e:
            logger.error(f"调度APP任务时出错: {e}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"[APP] 调度失败: {e}"))
            return 0

    def schedule_ai_tasks(self):
        """调度 AI 自动化模块的定时任务（Midscene异步执行）"""
        try:
            import httpx
            from apps.ui_automation.models import AiScheduledTask, MidsceneExecution, MidsceneCase
            from apps.ui_automation.views_midscene import _build_midscene_payload, MIDSCENE_SERVICE_URL

            active_tasks = AiScheduledTask.objects.filter(status='ACTIVE')
            executed_count = 0

            if active_tasks.exists():
                now = timezone.now()
                self.stdout.write(f"  [AI]  活跃任务数: {active_tasks.count()}")
                for task in active_tasks:
                    if task.next_run_time:
                        time_diff = (task.next_run_time - now).total_seconds()
                        if time_diff > 0:
                            self.stdout.write(f"        - {task.name}: 距下次执行还有 {int(time_diff)} 秒")
                        else:
                            self.stdout.write(f"        - {task.name}: 应该立即执行！")
                    else:
                        self.stdout.write(f"        - {task.name}: 未设置下次执行时间")

            for task in active_tasks:
                if task.should_run_now():
                    self.stdout.write(f"  [AI]  执行任务: {task.name}")
                    self.stdout.write(f"       类型: {task.get_task_type_display()}, 触发方式: {task.get_trigger_type_display()}")
                    try:
                        # 更新任务统计（必须在发请求前更新，防止下一轮重复触发）
                        task.last_run_time = timezone.now()
                        task.total_runs += 1
                        task.next_run_time = task.calculate_next_run()

                        if not task.midscene_case:
                            self.stdout.write(self.style.ERROR(f"    ✗ 任务 {task.name} 未配置Midscene用例"))
                            task.save()
                            continue

                        case = task.midscene_case

                        # 创建执行记录
                        execution = MidsceneExecution.objects.create(
                            case=case,
                            status='running',
                            executed_by=task.created_by,
                        )
                        case.last_status = 'running'
                        case.save(update_fields=['last_status'])

                        task.save()

                        # 构建并发送 Midscene 执行请求
                        payload = _build_midscene_payload(case, execution.id)

                        try:
                            with httpx.Client(timeout=10) as client:
                                resp = client.post(f'{MIDSCENE_SERVICE_URL}/execute', json=payload)
                                resp.raise_for_status()

                            self.stdout.write(self.style.SUCCESS(f"    ✓ 任务 {task.name} 已提交到Midscene微服务"))
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

                            self.stdout.write(self.style.ERROR(f"    ✗ 任务 {task.name}: Midscene微服务未启动"))

                            # 发送失败通知
                            try:
                                from apps.ui_automation.views_midscene import _send_ai_task_notification
                                _send_ai_task_notification(task, success=False)
                            except Exception as notify_err:
                                logger.error(f"发送AI任务 {task.name} 失败通知失败: {notify_err}")

                        except Exception as e:
                            execution.status = 'failed'
                            execution.error_message = str(e)
                            execution.finished_at = timezone.now()
                            execution.save()
                            case.last_status = 'failed'
                            case.last_result = str(e)[:500]
                            case.save(update_fields=['last_status', 'last_result'])

                            task.failed_runs += 1
                            task.last_result = {'status': 'failed', 'message': str(e)}
                            task.error_message = str(e)[:500]
                            task.save()

                            self.stdout.write(self.style.ERROR(f"    ✗ 任务 {task.name} 提交失败: {e}"))

                            # 发送失败通知
                            try:
                                from apps.ui_automation.views_midscene import _send_ai_task_notification
                                _send_ai_task_notification(task, success=False)
                            except Exception as notify_err:
                                logger.error(f"发送AI任务 {task.name} 失败通知失败: {notify_err}")

                        executed_count += 1

                    except Exception as e:
                        logger.error(f"执行AI任务 {task.name} 时出错: {e}", exc_info=True)
                        self.stdout.write(self.style.ERROR(f"    ✗ 任务 {task.name} 执行失败: {e}"))

            return executed_count

        except Exception as e:
            logger.error(f"调度AI任务时出错: {e}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"[AI] 调度失败: {e}"))
            return 0
