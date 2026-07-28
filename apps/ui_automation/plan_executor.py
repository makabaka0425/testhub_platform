"""测试计划执行器 — 串行执行计划内各项目（用例或套件），复用现有执行引擎"""

import os
import time
import json
import traceback
from datetime import datetime

from django.utils import timezone
from django.db import connection

from .models import (
    UiTestPlan, UiTestPlanItem, TestExecution, TestCaseExecution
)


class PlanExecutor:
    """测试计划执行器"""

    def __init__(self, test_plan, engine='playwright', browser='chrome', headless=False, executed_by=None):
        self.test_plan = test_plan
        self.engine = engine
        self.browser = browser
        self.headless = headless
        self.executed_by = executed_by
        self.plan_items = []
        self.item_results = []  # 每个计划项的执行结果摘要
        self.plan_execution = None  # 计划级 TestExecution 记录

        # 计划级共享变量池（共享会话模式）
        self.plan_context_variables = {}
        self.plan_protected_vars = set()

    def run(self):
        """执行测试计划"""
        print(f"[PlanExecutor] 初始化计划执行器...")
        try:
            os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
            connection.close()

            # 重新加载计划对象，避免过期引用
            self.test_plan = UiTestPlan.objects.get(id=self.test_plan.id)

            # 获取计划项
            self.plan_items = list(
                self.test_plan.plan_items.select_related(
                    'test_case', 'test_suite', 'test_suite__project'
                ).order_by('order')
            )

            if not self.plan_items:
                print(f"[PlanExecutor] 计划无项目，跳过执行")
                return

            # 创建计划级执行记录
            self.plan_execution = TestExecution.objects.create(
                project=self.test_plan.project,
                test_plan=self.test_plan,
                status='RUNNING',
                engine=self.engine,
                browser=self.browser,
                headless=self.headless,
                executed_by=self.executed_by,
                started_at=timezone.now()
            )

            # 根据执行模式分发
            if self.test_plan.execution_mode == 'shared_session':
                self._run_shared_session()
            else:
                self._run_per_case()

            # 汇总结果
            self._update_plan_result()

            # 执行计划级清理SQL
            self._execute_cleanup_sql()

        except Exception as e:
            print(f"[PlanExecutor] 计划执行异常: {str(e)}")
            traceback.print_exc()
            if self.plan_execution:
                self.plan_execution.status = 'FAILED'
                self.plan_execution.error_message = str(e)
                self.plan_execution.finished_at = timezone.now()
                self.plan_execution.save()

            # 更新计划状态
            try:
                self.test_plan.execution_status = 'failed'
                self.test_plan.save()
            except Exception:
                pass

    def _run_shared_session(self):
        """共享会话模式：整个计划共享一个浏览器和变量池"""
        print(f"[PlanExecutor] 共享会话模式执行计划: {self.test_plan.name}")

        if self.engine == 'playwright':
            self._run_shared_session_playwright()
        else:
            self._run_shared_session_selenium()

    def _run_shared_session_playwright(self):
        """Playwright 共享会话模式"""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            launch_args = ['--start-maximized'] if not self.headless else ['--headless=new']
            browser = p.chromium.launch(
                headless=self.headless,
                args=launch_args
            )
            context = browser.new_context(no_viewport=not self.headless)
            page = context.new_page()

            try:
                # 导航到项目基础URL
                base_url = self.test_plan.project.base_url
                if base_url:
                    page.goto(base_url, timeout=30000)

                # 计划级登录（如果配置了）
                if self.test_plan.login_config:
                    print(f"[PlanExecutor] 执行计划级登录: {self.test_plan.login_config.name}")
                    self._perform_plan_login_playwright(page, self.test_plan.login_config)

                # 串行执行每个计划项
                for item in self.plan_items:
                    result = self._execute_plan_item_playwright(
                        page, item, skip_login=True
                    )
                    self.item_results.append(result)

            finally:
                context.close()
                browser.close()

    def _run_shared_session_selenium(self):
        """Selenium 共享会话模式"""
        from .test_executor import TestExecutor
        executor = TestExecutor(
            test_suite=self.test_plan.project.test_suites.first(),
            engine='selenium', browser=self.browser,
            headless=self.headless, executed_by=self.executed_by
        )
        driver = executor.create_selenium_driver()

        try:
            base_url = self.test_plan.project.base_url
            if base_url:
                driver.get(base_url)

            if self.test_plan.login_config:
                print(f"[PlanExecutor] 执行计划级登录(Selenium): {self.test_plan.login_config.name}")
                self._perform_plan_login_selenium(driver, self.test_plan.login_config)

            for item in self.plan_items:
                result = self._execute_plan_item_selenium(
                    driver, item, skip_login=True
                )
                self.item_results.append(result)

        finally:
            driver.quit()

    def _run_per_case(self):
        """独立模式：每个计划项独立启动浏览器"""
        print(f"[PlanExecutor] 独立模式执行计划: {self.test_plan.name}")

        for i, item in enumerate(self.plan_items):
            try:
                if item.item_type == 'test_suite' and item.test_suite:
                    result = self._execute_suite_standalone(item.test_suite)
                elif item.item_type == 'test_case' and item.test_case:
                    result = self._execute_case_standalone(item.test_case)
                else:
                    result = {'item_type': item.item_type, 'status': 'error', 'error': '无效的计划项'}
                self.item_results.append(result)
            except Exception as e:
                print(f"[PlanExecutor] 计划项执行异常: {e}")
                self.item_results.append({
                    'item_type': item.item_type,
                    'status': 'error',
                    'error': str(e)
                })

            # 用例之间间隔3秒，让浏览器完全释放资源
            if i < len(self.plan_items) - 1:
                print(f"[PlanExecutor] 用例间隔等待3秒...")
                time.sleep(3)

    def _execute_suite_standalone(self, test_suite):
        """独立模式执行套件 — 复用 TestExecutor"""
        from .test_executor import TestExecutor

        print(f"[PlanExecutor] 独立执行套件: {test_suite.name}")
        executor = TestExecutor(
            test_suite=test_suite,
            engine=self.engine,
            browser=self.browser,
            headless=self.headless,
            executed_by=self.executed_by
        )
        executor.run()

        # 找到该套件最新的执行记录
        latest_execution = TestExecution.objects.filter(
            test_suite=test_suite
        ).order_by('-created_at').first()

        # 将套件内用例的执行记录关联到计划级 TestExecution
        # 这样 execution_history 接口才能通过 test_execution 外键查到套件内用例
        if latest_execution and self.plan_execution:
            suite_case_executions = TestCaseExecution.objects.filter(
                test_execution=latest_execution
            )
            updated_count = suite_case_executions.update(
                test_plan=self.test_plan,
                execution_source='plan',
            )
            # 同时将这些记录也关联到计划级 TestExecution
            # 通过在同一时间窗口内匹配来建立关联
            if updated_count == 0:
                # 旧记录可能没有 test_execution 外键，通过套件+时间窗口匹配
                time_window_cases = TestCaseExecution.objects.filter(
                    test_suite=test_suite,
                    started_at__gte=self.plan_execution.started_at,
                )
                if self.plan_execution.finished_at:
                    time_window_cases = time_window_cases.filter(
                        started_at__lte=self.plan_execution.finished_at
                    )
                time_window_cases.update(
                    test_plan=self.test_plan,
                    execution_source='plan',
                )
                updated_count = time_window_cases.count()

            # 将套件内用例执行记录也关联到计划级 test_execution
            # 创建一个映射关系：在 test_execution 外键上设置计划级ID
            if updated_count > 0:
                # 重新查询已更新的记录，设置计划级test_execution
                TestCaseExecution.objects.filter(
                    test_suite=test_suite,
                    test_plan=self.test_plan,
                    execution_source='plan',
                    started_at__gte=self.plan_execution.started_at,
                ).update(test_execution=self.plan_execution)
                print(f"[PlanExecutor] 已关联 {updated_count} 条套件用例到计划执行记录")

        return {
            'item_type': 'test_suite',
            'item_id': test_suite.id,
            'item_name': test_suite.name,
            'status': 'passed' if latest_execution and latest_execution.status == 'SUCCESS' else 'failed',
            'execution_id': latest_execution.id if latest_execution else None,
        }

    def _execute_case_standalone(self, test_case):
        """独立模式执行单用例"""
        print(f"[PlanExecutor] 独立执行用例: {test_case.name}")

        from .models import TestCase as TC

        # 创建用例执行记录
        case_execution = TestCaseExecution.objects.create(
            test_case=test_case,
            project=self.test_plan.project,
            test_plan=self.test_plan,
            execution_source='plan',
            status='running',
            engine=self.engine,
            browser=self.browser,
            headless=self.headless,
            created_by=self.executed_by,
            started_at=timezone.now()
        )

        start_time = time.time()
        try:
            result = self._run_single_case(test_case)
            # 兼容 Playwright(success) 和 Selenium(status) 两种返回格式
            if 'success' in result:
                case_execution.status = 'passed' if result.get('success') else 'failed'
            else:
                case_execution.status = result.get('status', 'failed')
            case_execution.execution_logs = json.dumps({
                'steps': result.get('steps', []),
                'variable_snapshot': result.get('variable_snapshot', {})
            }, ensure_ascii=False)
            if result.get('error'):
                case_execution.error_message = result['error']
            if result.get('screenshots'):
                case_execution.screenshots = result['screenshots']
        except Exception as e:
            case_execution.status = 'error'
            case_execution.error_message = str(e)

        case_execution.execution_time = time.time() - start_time
        case_execution.finished_at = timezone.now()
        case_execution.save()

        # 回写用例状态
        status_map = {'passed': 'passed', 'failed': 'failed', 'skipped': 'skipped'}
        new_status = status_map.get(case_execution.status)
        if new_status and test_case.status != new_status:
            test_case.status = new_status
            test_case.save(update_fields=['status', 'updated_at'])

        return {
            'item_type': 'test_case',
            'item_id': test_case.id,
            'item_name': test_case.name,
            'status': case_execution.status,
            'execution_id': case_execution.id,
        }

    def _execute_plan_item_playwright(self, page, item, skip_login=False):
        """共享会话模式执行单个计划项（Playwright）"""
        if item.item_type == 'test_suite' and item.test_suite:
            return self._execute_suite_in_session_playwright(page, item.test_suite, skip_login)
        elif item.item_type == 'test_case' and item.test_case:
            return self._execute_case_in_session_playwright(page, item.test_case, skip_login)
        return {'item_type': item.item_type, 'status': 'error', 'error': '无效的计划项'}

    def _execute_suite_in_session_playwright(self, page, test_suite, skip_login):
        """共享会话中执行套件 — 跳过套件自身的登录"""
        from .models import TestSuiteTestCase as SuiteTC, TestCaseExecution as TCE

        print(f"[PlanExecutor] 共享会话中执行套件: {test_suite.name} (跳过登录={skip_login})")

        suite_relations = list(SuiteTC.objects.filter(
            test_suite=test_suite
        ).select_related('test_case').order_by('order'))

        passed = 0
        failed = 0
        for idx, rel in enumerate(suite_relations):
            case = rel.test_case
            case_execution = TCE.objects.create(
                test_case=case,
                project=self.test_plan.project,
                test_suite=test_suite,
                test_plan=self.test_plan,
                execution_source='plan',
                status='running',
                engine=self.engine,
                browser=self.browser,
                headless=self.headless,
                created_by=self.executed_by,
                started_at=timezone.now()
            )

            start_time = time.time()
            try:
                result = self._run_case_with_page(page, case)
                case_execution.status = 'passed' if result.get('success') else 'failed'
                case_execution.execution_logs = json.dumps({
                    'steps': result.get('steps', []),
                    'variable_snapshot': result.get('variable_snapshot', {})
                }, ensure_ascii=False)
                if result.get('error'):
                    case_execution.error_message = result['error']
                if result.get('screenshots'):
                    case_execution.screenshots = result['screenshots']
            except Exception as e:
                case_execution.status = 'error'
                case_execution.error_message = str(e)

            case_execution.execution_time = time.time() - start_time
            case_execution.finished_at = timezone.now()
            case_execution.save()

            # 回写用例状态
            status_map = {'passed': 'passed', 'failed': 'failed', 'skipped': 'skipped'}
            new_status = status_map.get(case_execution.status)
            if new_status and case.status != new_status:
                case.status = new_status
                case.save(update_fields=['status', 'updated_at'])

            # 执行后动作（最后一条用例不需要）
            if idx < len(suite_relations) - 1:
                self._execute_post_action_plan(page, test_suite, rel, case, idx, len(suite_relations))

            if case_execution.status in ('passed',):
                passed += 1
            else:
                failed += 1

        return {
            'item_type': 'test_suite',
            'item_id': test_suite.id,
            'item_name': test_suite.name,
            'status': 'passed' if failed == 0 else 'failed',
            'passed': passed,
            'failed': failed,
        }

    def _execute_case_in_session_playwright(self, page, test_case, skip_login):
        """共享会话中执行单用例"""
        from .models import TestCaseExecution as TCE

        print(f"[PlanExecutor] 共享会话中执行用例: {test_case.name} (跳过登录={skip_login})")

        case_execution = TCE.objects.create(
            test_case=test_case,
            project=self.test_plan.project,
            test_plan=self.test_plan,
            execution_source='plan',
            status='running',
            engine=self.engine,
            browser=self.browser,
            headless=self.headless,
            created_by=self.executed_by,
            started_at=timezone.now()
        )

        start_time = time.time()
        try:
            result = self._run_case_with_page(page, test_case)
            case_execution.status = 'passed' if result.get('success') else 'failed'
            case_execution.execution_logs = json.dumps({
                'steps': result.get('steps', []),
                'variable_snapshot': result.get('variable_snapshot', {})
            }, ensure_ascii=False)
            if result.get('error'):
                case_execution.error_message = result['error']
            if result.get('screenshots'):
                case_execution.screenshots = result['screenshots']
        except Exception as e:
            case_execution.status = 'error'
            case_execution.error_message = str(e)

        case_execution.execution_time = time.time() - start_time
        case_execution.finished_at = timezone.now()
        case_execution.save()

        # 回写用例状态
        status_map = {'passed': 'passed', 'failed': 'failed', 'skipped': 'skipped'}
        new_status = status_map.get(case_execution.status)
        if new_status and test_case.status != new_status:
            test_case.status = new_status
            test_case.save(update_fields=['status', 'updated_at'])

        return {
            'item_type': 'test_case',
            'item_id': test_case.id,
            'item_name': test_case.name,
            'status': case_execution.status,
        }

    def _execute_plan_item_selenium(self, driver, item, skip_login=False):
        """共享会话模式执行单个计划项（Selenium）"""
        if item.item_type == 'test_suite' and item.test_suite:
            return self._execute_suite_in_session_selenium(driver, item.test_suite, skip_login)
        elif item.item_type == 'test_case' and item.test_case:
            return self._execute_case_in_session_selenium(driver, item.test_case, skip_login)
        return {'item_type': item.item_type, 'status': 'error', 'error': '无效的计划项'}

    def _execute_suite_in_session_selenium(self, driver, test_suite, skip_login):
        """Selenium共享会话中执行套件"""
        from .models import TestSuiteTestCase as SuiteTC, TestCaseExecution as TCE

        print(f"[PlanExecutor] Selenium共享会话中执行套件: {test_suite.name}")
        suite_relations = SuiteTC.objects.filter(
            test_suite=test_suite
        ).select_related('test_case').order_by('order')

        passed = 0
        failed = 0
        for rel in suite_relations:
            case = rel.test_case
            case_execution = TCE.objects.create(
                test_case=case,
                project=self.test_plan.project,
                test_suite=test_suite,
                test_plan=self.test_plan,
                execution_source='plan',
                status='running',
                engine='selenium',
                browser=self.browser,
                headless=self.headless,
                created_by=self.executed_by,
                started_at=timezone.now()
            )

            start_time = time.time()
            try:
                from .test_executor import TestExecutor
                executor = TestExecutor(test_suite, engine='selenium')
                executor.context_variables = self.plan_context_variables
                executor._protected_vars = self.plan_protected_vars

                case_data = executor._build_case_data(case)
                result = executor.execute_test_case_selenium_no_db(driver, case_data)

                case_execution.status = result.get('status', 'failed')
                case_execution.execution_logs = json.dumps({
                    'steps': result.get('steps', []),
                    'variable_snapshot': result.get('variable_snapshot', {})
                }, ensure_ascii=False)
                if result.get('error'):
                    case_execution.error_message = result['error']
                if result.get('screenshots'):
                    case_execution.screenshots = result['screenshots']
            except Exception as e:
                case_execution.status = 'error'
                case_execution.error_message = str(e)

            case_execution.execution_time = time.time() - start_time
            case_execution.finished_at = timezone.now()
            case_execution.save()

            # 回写用例状态
            status_map = {'passed': 'passed', 'failed': 'failed', 'skipped': 'skipped'}
            new_status = status_map.get(case_execution.status)
            if new_status and case.status != new_status:
                case.status = new_status
                case.save(update_fields=['status', 'updated_at'])

            if case_execution.status == 'passed':
                passed += 1
            else:
                failed += 1

        return {
            'item_type': 'test_suite',
            'item_id': test_suite.id,
            'item_name': test_suite.name,
            'status': 'passed' if failed == 0 else 'failed',
            'passed': passed,
            'failed': failed,
        }

    def _execute_case_in_session_selenium(self, driver, test_case, skip_login):
        """Selenium共享会话中执行单用例"""
        from .models import TestCaseExecution as TCE

        case_execution = TCE.objects.create(
            test_case=test_case,
            project=self.test_plan.project,
            test_plan=self.test_plan,
            execution_source='plan',
            status='running',
            engine='selenium',
            browser=self.browser,
            headless=self.headless,
            created_by=self.executed_by,
            started_at=timezone.now()
        )

        start_time = time.time()
        try:
            from .test_executor import TestExecutor
            executor = TestExecutor(self.test_plan.project.test_suites.first(), engine='selenium')
            executor.context_variables = self.plan_context_variables
            executor._protected_vars = self.plan_protected_vars

            case_data = executor._build_case_data(test_case)
            result = executor.execute_test_case_selenium_no_db(driver, case_data)

            case_execution.status = result.get('status', 'failed')
            case_execution.execution_logs = json.dumps({
                'steps': result.get('steps', []),
                'variable_snapshot': result.get('variable_snapshot', {})
            }, ensure_ascii=False)
            if result.get('error'):
                case_execution.error_message = result['error']
            if result.get('screenshots'):
                case_execution.screenshots = result['screenshots']
        except Exception as e:
            case_execution.status = 'error'
            case_execution.error_message = str(e)

        case_execution.execution_time = time.time() - start_time
        case_execution.finished_at = timezone.now()
        case_execution.save()

        # 回写用例状态
        status_map = {'passed': 'passed', 'failed': 'failed', 'skipped': 'skipped'}
        new_status = status_map.get(case_execution.status)
        if new_status and test_case.status != new_status:
            test_case.status = new_status
            test_case.save(update_fields=['status', 'updated_at'])

        return {
            'item_type': 'test_case',
            'item_id': test_case.id,
            'item_name': test_case.name,
            'status': case_execution.status,
        }

    def _perform_plan_login_playwright(self, page, login_config):
        """执行计划级登录（Playwright）"""
        from .test_executor import TestExecutor

        login_case = login_config.login_test_case
        if not login_case:
            print(f"[PlanExecutor] 登录配置无关联用例，跳过")
            return

        # 导航到登录页
        if login_config.login_url:
            page.goto(login_config.login_url, timeout=30000)

        # 执行登录用例步骤
        result = self._run_case_with_page(page, login_case)
        print(f"[PlanExecutor] 登录结果: {'成功' if result.get('success') else '失败'}")

    def _perform_plan_login_selenium(self, driver, login_config):
        """执行计划级登录（Selenium）"""
        login_case = login_config.login_test_case
        if not login_case:
            return

        if login_config.login_url:
            driver.get(login_config.login_url)

        from .test_executor import TestExecutor
        executor = TestExecutor(self.test_plan.project.test_suites.first(), engine='selenium')
        executor.context_variables = self.plan_context_variables
        executor._protected_vars = self.plan_protected_vars

        case_data = executor._build_case_data(login_case)
        executor.execute_test_case_selenium_no_db(driver, case_data)

    def _run_case_with_page(self, page, test_case):
        """用给定 page 对象执行单用例步骤（PlanExecutor 专用）

        返回结构化数据，与套件执行器格式一致：
        {'success': bool, 'steps': [...], 'error': str, 'screenshots': [...], 'variable_snapshot': {...}}
        """
        from .test_executor import TestExecutor
        from .models import TestCaseStep

        executor = TestExecutor.__new__(TestExecutor)
        executor.context_variables = self.plan_context_variables
        executor._protected_vars = self.plan_protected_vars
        executor.current_page = page

        # 构建步骤数据
        steps = test_case.steps.select_related(
            'element', 'element__locator_strategy'
        ).filter(is_cleanup=False).order_by('step_number')

        step_data_list = []
        for step in steps:
            sd = {
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
                sd['element'] = {
                    'id': step.element.id,
                    'name': step.element.name,
                    'locator_strategy': step.element.locator_strategy.name if step.element.locator_strategy else '',
                    'locator_value': step.element.locator_value,
                }
            step_data_list.append(sd)

        steps_list = []
        all_success = True
        error = None
        screenshots = []

        for sd in step_data_list:
            try:
                step_result = executor.execute_step_playwright(sd)
                steps_list.append(step_result)
                if not step_result.get('success', False):
                    all_success = False
                    error = step_result.get('error', f"步骤{sd['step_number']} 执行失败")
                    # 捕获失败截图
                    try:
                        import base64
                        page.evaluate("window.scrollTo(0, 0)")
                        page.wait_for_timeout(300)
                        screenshot_bytes = page.screenshot(timeout=5000)
                        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                        screenshots.append({
                            'url': f'data:image/png;base64,{screenshot_base64}',
                            'description': f"步骤 {sd['step_number']} 失败截图",
                            'step_number': sd['step_number'],
                            'timestamp': datetime.now().isoformat()
                        })
                    except Exception as screenshot_err:
                        print(f"[PlanExecutor] 捕获失败截图失败: {str(screenshot_err)}")
                    break  # 步骤失败后停止
            except Exception as e:
                all_success = False
                error = str(e)
                steps_list.append({
                    'step_number': sd['step_number'],
                    'action_type': sd['action_type'],
                    'description': sd['description'],
                    'input_value': sd.get('input_value', ''),
                    'success': False,
                    'error': str(e)
                })
                break  # 异常后停止

        # 同步变量池回计划级
        self.plan_context_variables = executor.context_variables
        self.plan_protected_vars = executor._protected_vars

        return {
            'success': all_success,
            'steps': steps_list,
            'error': error,
            'screenshots': screenshots,
            'variable_snapshot': dict(self.plan_context_variables)
        }

    def _run_single_case(self, test_case):
        """独立模式执行单用例（新建浏览器）"""
        if self.engine == 'playwright':
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                launch_args = ['--start-maximized'] if not self.headless else ['--headless=new']
                browser = p.chromium.launch(headless=self.headless, args=launch_args)
                context = browser.new_context(no_viewport=not self.headless)
                page = context.new_page()

                try:
                    base_url = self.test_plan.project.base_url
                    if base_url:
                        page.goto(base_url, timeout=30000)

                    # 独立模式下，如果用例有前置条件且是登录类，正常执行
                    result = self._run_case_with_page(page, test_case)
                finally:
                    # 等待网络请求完成，防止服务端操作未完成
                    try:
                        page.wait_for_load_state('networkidle', timeout=5000)
                    except Exception:
                        pass
                    time.sleep(2)  # 兜底等待2秒，确保服务端请求处理完毕
                    context.close()
                    browser.close()

            return result
        else:
            # Selenium 独立模式
            from .test_executor import TestExecutor
            dummy_suite = self.test_plan.project.test_suites.first()
            if not dummy_suite:
                return {'success': False, 'steps': [], 'error': '无可用的套件对象创建Selenium驱动'}

            executor = TestExecutor(dummy_suite, engine='selenium', browser=self.browser, headless=self.headless)
            driver = executor.create_selenium_driver()
            try:
                base_url = self.test_plan.project.base_url
                if base_url:
                    driver.get(base_url)

                case_data = executor._build_case_data(test_case)
                executor.context_variables = {}
                result = executor.execute_test_case_selenium_no_db(driver, case_data)
            finally:
                driver.quit()

            return result

    def _update_plan_result(self):
        """汇总更新计划执行结果"""
        if not self.plan_execution:
            return

        total_passed = sum(1 for r in self.item_results if r.get('status') == 'passed')
        total_failed = sum(1 for r in self.item_results if r.get('status') == 'failed')
        total_skipped = sum(1 for r in self.item_results if r.get('status') == 'skipped')
        overall_status = 'SUCCESS' if total_failed == 0 else 'FAILED'

        self.plan_execution.status = overall_status
        self.plan_execution.passed_cases = total_passed
        self.plan_execution.failed_cases = total_failed
        self.plan_execution.total_cases = total_passed + total_failed + total_skipped
        self.plan_execution.finished_at = timezone.now()
        self.plan_execution.result_data = {
            'plan_items': self.item_results,
            'summary': {
                'total': total_passed + total_failed + total_skipped,
                'passed': total_passed,
                'failed': total_failed,
                'skipped': total_skipped,
            }
        }
        self.plan_execution.save()

        # 更新计划状态
        self.test_plan.execution_status = 'passed' if total_failed == 0 else 'failed'
        self.test_plan.passed_count = total_passed
        self.test_plan.failed_count = total_failed
        self.test_plan.skipped_count = total_skipped
        self.test_plan.save()

    def _execute_cleanup_sql(self):
        """执行计划级清理SQL"""
        if not self.test_plan.cleanup_sql:
            return

        sql_text = self.test_plan.cleanup_sql.strip()
        if not sql_text:
            return

        print(f"[PlanExecutor] 执行计划级清理SQL")
        try:
            from .models import UiProject
            project = UiProject.objects.get(id=self.test_plan.project_id)

            if not all([project.db_host, project.db_name, project.db_user, project.db_password]):
                print(f"[PlanExecutor] 项目未配置数据库连接，跳过清理SQL")
                return

            from .db_cleanup_executor import execute_cleanup_sql
            for sql in sql_text.split(';'):
                sql = sql.strip()
                if sql:
                    execute_cleanup_sql(project, sql, self.plan_context_variables)
                    print(f"[PlanExecutor] 清理SQL执行成功: {sql[:50]}...")
        except Exception as e:
            print(f"[PlanExecutor] 清理SQL执行异常: {str(e)}")

    def _execute_post_action_plan(self, page, test_suite, suite_tc_relation, test_case, case_index, total_cases):
        """计划级共享会话中的执行后动作

        Args:
            page: Playwright page 对象
            test_suite: 当前套件（用于获取 default_post_action）
            suite_tc_relation: TestSuiteTestCase关联对象
            test_case: 当前用例
            case_index: 当前用例序号（0-based）
            total_cases: 套件内总用例数
        """
        # 用例级 > 套件级
        action = ''
        if suite_tc_relation and suite_tc_relation.post_action:
            action = suite_tc_relation.post_action
        else:
            action = getattr(test_suite, 'default_post_action', '') or 'refresh_page'

        print(f"[PlanExecutor-执行后动作] 用例「{test_case.name}」执行后动作: {action}")

        try:
            if action == 'close_page':
                current_url_before = page.url
                page.close()
                print(f"[PlanExecutor-执行后动作] 已关闭页面: {current_url_before}")

                # 新开tab
                new_page = page.context.new_page()
                base_url = self.test_plan.project.base_url
                if base_url:
                    try:
                        new_page.goto(base_url, wait_until='networkidle', timeout=30000)
                        time.sleep(1)
                        print(f"[PlanExecutor-执行后动作] 新页面已导航到: {base_url}")
                    except Exception as e:
                        print(f"[PlanExecutor-执行后动作] 导航失败: {str(e)}")
                # 注意：调用方需要拿到新的 page，这里通过返回值传递不方便
                # 用简单方式：直接修改传入的 page 对象引用不太可能，但我们可以用 self 共享
                self._current_page_ref = new_page

            elif action == 'refresh_page':
                page.reload(wait_until='networkidle', timeout=30000)
                time.sleep(1)
                print(f"[PlanExecutor-执行后动作] 页面已刷新: {page.url}")

            elif action == 'keep_state':
                print(f"[PlanExecutor-执行后动作] 维持当前页面状态: {page.url}")

        except Exception as e:
            print(f"[PlanExecutor-执行后动作] 执行异常: {str(e)}")
