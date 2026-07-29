"""
Allure 测试报告生成器

负责将 UI 自动化执行结果转换为 Allure Results JSON 格式，
并调用 allure generate 生成静态报告。
"""

import json
import os
import uuid
import shutil
import subprocess
import re
import base64
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.utils import timezone


# Allure 命令行路径
ALLURE_BIN = r'D:\install\allure-2.34.1\allure-2.34.1\bin\allure.bat'

# 报告输出根目录
REPORTS_ROOT = os.path.join(settings.BASE_DIR, 'allure_reports')

# 敏感字段关键词（输入值脱敏）
SENSITIVE_KEYWORDS = ['password', 'passwd', 'pwd', 'secret', 'token', 'apikey', 'api_key']

# UI 异常分类映射
UI_EXCEPTION_PATTERNS = {
    '元素定位失败': [
        r'NoSuchElement',
        r'元素未找到',
        r'no such element',
        r'Unable to locate element',
        r'Waiting for selector.*timed out',
    ],
    '等待超时': [
        'TimeoutException',
        r'超时',
        r'timed? ?out',
        r'waiting.*timeout',
    ],
    '断言失败': [
        'AssertionError',
        'AssertionError',
        r'断言失败',
        r'assertion failed',
        r'expected.*but was',
    ],
    'DOM元素失效': [
        'StaleElementReferenceException',
        r'stale element',
        r'元素已失效',
        r'detached DOM',
    ],
    '浏览器崩溃': [
        'WebDriverException',
        r'browser.*crash',
        r'连接被拒绝',
        r'session.*deleted',
    ],
}


def classify_ui_error(error_message):
    """根据错误信息分类 UI 异常类型"""
    if not error_message:
        return '未知异常'
    for category, patterns in UI_EXCEPTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, error_message, re.IGNORECASE):
                return category
    return '其他异常'


def mask_sensitive_value(input_value, action_type=''):
    """对敏感输入值脱敏"""
    if not input_value:
        return input_value or ''
    # 密码类型操作直接脱敏
    input_lower = (action_type + input_value).lower()
    for keyword in SENSITIVE_KEYWORDS:
        if keyword in input_lower:
            return '***'
    return input_value


def save_base64_image(base64_str, output_dir, filename):
    """将 base64 截图保存为文件"""
    try:
        if base64_str.startswith('data:image'):
            # 去掉 data:image/png;base64, 前缀
            base64_str = base64_str.split(',', 1)[1]
        image_data = base64.b64decode(base64_str)
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(image_data)
        return filename
    except Exception:
        return None


def generate_allure_uuid():
    """生成 Allure 格式的 UUID"""
    return str(uuid.uuid4())


def build_allure_result(case_data, case_execution, suite_name='', plan_name=''):
    """
    构建单条用例的 Allure result JSON

    Args:
        case_data: 用例执行数据字典（从 TestCaseExecution 提取）
        case_execution: TestCaseExecution 实例
        suite_name: 所属套件名
        plan_name: 所属计划名

    Returns:
        dict: Allure result JSON 对象
    """
    allure_uuid = generate_allure_uuid()

    # 解析执行日志获取步骤详情
    steps_data = []
    execution_logs = {}
    if case_execution.execution_logs:
        try:
            execution_logs = json.loads(case_execution.execution_logs) if isinstance(case_execution.execution_logs, str) else case_execution.execution_logs
            steps_data = execution_logs.get('steps', [])
        except (json.JSONDecodeError, TypeError):
            pass

    # 构建 Allure 步骤
    allure_steps = []
    for idx, step_data in enumerate(steps_data, 1):
        step_uuid = generate_allure_uuid()
        action_type = step_data.get('action_type', '')
        description = step_data.get('description', '')
        step_status = 'passed' if step_data.get('success', True) else 'failed'

        # 输入值脱敏
        input_value = mask_sensitive_value(
            step_data.get('input_value', ''),
            action_type
        )

        # 步骤名称
        step_name = description or f'{action_type} 步骤{idx}'
        if input_value and action_type in ('fill', 'select', 'type'):
            step_name += f' - {input_value}'

        step_result = {
            'name': step_name,
            'status': step_status,
            'stage': 'finished',
            'start': _to_epoch_ms(step_data.get('start_time')),
            'stop': _to_epoch_ms(step_data.get('end_time')),
            'parameters': [],
        }

        # 元素定位信息作为参数展示
        element_info = step_data.get('element', step_data.get('element_data', {}))
        if element_info:
            locator_strategy = element_info.get('locator_strategy', element_info.get('strategy', ''))
            locator_value = element_info.get('locator_value', element_info.get('value', ''))
            element_name = element_info.get('name', '')
            if locator_strategy:
                step_result['parameters'].append({
                    'name': '定位策略',
                    'value': locator_strategy,
                })
            if locator_value:
                step_result['parameters'].append({
                    'name': '定位表达式',
                    'value': locator_value,
                })
            if element_name:
                step_result['parameters'].append({
                    'name': '元素名称',
                    'value': element_name,
                })

        # 断言信息
        assert_type = step_data.get('assert_type', '')
        assert_value = step_data.get('assert_value', '')
        if assert_type:
            step_result['parameters'].append({
                'name': f'断言({assert_type})',
                'value': assert_value,
            })

        allure_steps.append(step_result)

    # 状态映射
    case_status = case_execution.status or 'pending'
    status_map = {
        'pending': 'skipped',
        'running': 'running',
        'passed': 'passed',
        'failed': 'failed',
        'error': 'broken',
        'skipped': 'skipped',
    }
    allure_status = status_map.get(case_status, 'skipped')

    # 时间
    start_ms = _to_epoch_ms(str(case_execution.started_at)) if case_execution.started_at else None
    stop_ms = _to_epoch_ms(str(case_execution.finished_at)) if case_execution.finished_at else None

    # 标签
    labels = [
        {'name': 'suite', 'value': suite_name or '默认套件'},
        {'name': 'parentSuite', 'value': plan_name or '默认计划'},
        {'name': 'feature', 'value': 'UI自动化测试'},
        {'name': 'framework', 'value': case_execution.engine or 'playwright'},
    ]

    # 浏览器标签
    if case_execution.browser:
        labels.append({'name': 'Browser', 'value': case_execution.browser})

    # 失败原因分类标签
    if case_status in ('failed', 'error'):
        error_category = classify_ui_error(case_execution.error_message)
        labels.append({'name': 'severity', 'value': 'blocker' if error_category in ('元素定位失败', '浏览器崩溃') else 'critical'})
        labels.append({'name': 'failureCategory', 'value': error_category})

    result = {
        'name': case_execution.test_case.name if case_execution.test_case else f'用例#{case_execution.id}',
        'status': allure_status,
        'statusDetails': {},
        'stage': 'finished',
        'description': f'执行人: {case_execution.created_by.username if case_execution.created_by else "系统"}',
        'steps': allure_steps,
        'attachments': [],
        'parameters': [],
        'labels': labels,
        'links': [],
        'start': start_ms,
        'stop': stop_ms,
        'uuid': allure_uuid,
        'historyId': f'{case_execution.test_case_id}-{suite_name}',
        'testCaseId': str(case_execution.test_case_id),
        'fullName': f'{plan_name}.{suite_name}.{case_execution.test_case.name if case_execution.test_case else case_execution.id}',
    }

    # 错误信息
    if case_execution.error_message:
        result['statusDetails'] = {
            'message': case_execution.error_message[:500],
            'trace': case_execution.error_message[:2000],
        }

    return result


def build_attachments(case_execution, results_dir):
    """
    构建用例的附件列表（截图等），保存文件到 results_dir

    Returns:
        list: Allure attachment 对象列表
    """
    attachments = []

    # 从 screenshots 字段提取
    screenshots = case_execution.screenshots or []
    for idx, screenshot in enumerate(screenshots):
        screenshot_url = screenshot.get('url', '') if isinstance(screenshot, dict) else ''
        step_number = screenshot.get('step_number', idx) if isinstance(screenshot, dict) else idx
        description = screenshot.get('description', f'步骤{step_number}截图') if isinstance(screenshot, dict) else f'截图{idx+1}'

        if isinstance(screenshot, str):
            screenshot_url = screenshot
            description = f'截图{idx+1}'

        if not screenshot_url:
            continue

        # 保存截图文件
        att_uuid = generate_allure_uuid()
        filename = f'{att_uuid}-screenshot-{idx+1}.png'

        if screenshot_url.startswith('data:image'):
            saved = save_base64_image(screenshot_url, results_dir, filename)
            if saved:
                attachments.append({
                    'name': description,
                    'source': filename,
                    'type': 'image/png',
                })
        elif screenshot_url.startswith('http'):
            # URL 类型截图暂时跳过，后续可下载
            pass

    # 失败步骤额外标记
    if case_execution.status in ('failed', 'error') and case_execution.error_message:
        att_uuid = generate_allure_uuid()
        error_filename = f'{att_uuid}-error.txt'
        error_path = os.path.join(results_dir, error_filename)
        with open(error_path, 'w', encoding='utf-8') as f:
            f.write(case_execution.error_message)
        attachments.append({
            'name': '失败错误信息',
            'source': error_filename,
            'type': 'text/plain',
        })

    return attachments


def generate_allure_results(report, case_executions_with_context):
    """
    生成 Allure Results JSON 文件

    Args:
        report: AllureReport 实例
        case_executions_with_context: list of (TestCaseExecution, suite_name, plan_name) 元组

    Returns:
        str: results 目录路径
    """
    # 创建独立的临时目录
    results_dir = os.path.join(REPORTS_ROOT, f'results_{report.id}_{generate_allure_uuid()[:8]}')
    os.makedirs(results_dir, exist_ok=True)

    # 生成环境信息文件
    _write_environment_file(results_dir, report)

    # 生成 executorinfo
    _write_executor_info(results_dir, report)

    for case_execution, suite_name, plan_name in case_executions_with_context:
        try:
            # 构建 result JSON
            result_json = build_allure_result(None, case_execution, suite_name, plan_name)

            # 构建附件
            attachments = build_attachments(case_execution, results_dir)
            result_json['attachments'] = attachments

            # 写入 result JSON
            result_filename = f'{result_json["uuid"]}-result.json'
            result_path = os.path.join(results_dir, result_filename)
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result_json, f, ensure_ascii=False, indent=2, default=str)

            # 写入 attachment 的 container JSON
            container_filename = f'{generate_allure_uuid()}-container.json'
            container_path = os.path.join(results_dir, container_filename)
            container = {
                'uuid': result_json['uuid'],
                'children': [result_json['uuid']],
                'befores': [],
                'afters': [],
            }
            with open(container_path, 'w', encoding='utf-8') as f:
                json.dump(container, f, ensure_ascii=False, indent=2, default=str)

        except Exception as e:
            print(f'[Allure] 生成用例结果失败: {e}')
            continue

    return results_dir


def run_allure_generate(results_dir, report_id):
    """
    调用 allure generate 生成静态报告

    Args:
        results_dir: Allure results 目录路径
        report_id: AllureReport ID

    Returns:
        str: 报告输出目录路径
    """
    output_dir = os.path.join(REPORTS_ROOT, f'report_{report_id}')

    # 清理旧报告
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    cmd = [ALLURE_BIN, 'generate', results_dir, '-o', output_dir, '--clean']

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            encoding='utf-8',
            errors='replace',
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or 'allure generate 执行失败'
            raise RuntimeError(error_msg)

        return output_dir

    except FileNotFoundError:
        raise RuntimeError(f'Allure 命令未找到: {ALLURE_BIN}')
    except subprocess.TimeoutExpired:
        raise RuntimeError('Allure 报告生成超时（5分钟）')


def _write_environment_file(results_dir, report):
    """写入 environment.properties 文件"""
    env_path = os.path.join(results_dir, 'environment.properties')
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(f'Browser={report.browser or "chrome"}\n')
        f.write(f'Engine=playwright\n')
        f.write(f'Project={report.project.name if report.project else ""}\n')
        if report.test_plan:
            f.write(f'TestPlan={report.test_plan.name}\n')
        f.write(f'Environment={report.environment or "default"}\n')
        f.write(f'Report.ID={report.id}\n')
        f.write(f'Report.Name={report.name}\n')


def _write_executor_info(results_dir, report):
    """写入 executorinfo.json 文件"""
    executor_path = os.path.join(results_dir, 'executorinfo.json')
    executor = {
        'name': 'UI自动化测试平台',
        'type': 'ui_automation',
        'buildName': report.name,
        'buildUrl': '',
        'reportUrl': f'/ui-automation/allure-reports/{report.id}/view/',
    }
    if report.created_by:
        executor['author'] = report.created_by.username
    with open(executor_path, 'w', encoding='utf-8') as f:
        json.dump(executor, f, ensure_ascii=False, indent=2)


def _to_epoch_ms(dt_str):
    """将日期时间字符串转换为 epoch 毫秒"""
    if not dt_str:
        return None
    try:
        # 尝试多种格式
        for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S'):
            try:
                dt = datetime.strptime(str(dt_str).split('+')[0].split('Z')[0].strip(), fmt)
                return int(dt.timestamp() * 1000)
            except ValueError:
                continue
        # 最后尝试直接解析
        dt = datetime.fromisoformat(str(dt_str).split('+')[0].split('Z')[0].strip())
        return int(dt.timestamp() * 1000)
    except Exception:
        return None


def calculate_report_stats(case_executions):
    """
    计算报告统计数据

    Args:
        case_executions: TestCaseExecution queryset 或列表

    Returns:
        dict: 统计数据
    """
    total = len(case_executions)
    passed = sum(1 for c in case_executions if c.status == 'passed')
    failed = sum(1 for c in case_executions if c.status == 'failed')
    error = sum(1 for c in case_executions if c.status == 'error')
    skipped = sum(1 for c in case_executions if c.status in ('skipped', 'pending'))

    pass_rate = round((passed / total * 100), 1) if total > 0 else 0

    durations = [c.execution_time for c in case_executions if c.execution_time and c.execution_time > 0]
    avg_duration = round(sum(durations) / len(durations), 2) if durations else 0

    # 失败原因分类统计
    failure_categories = {}
    for c in case_executions:
        if c.status in ('failed', 'error'):
            category = classify_ui_error(c.error_message)
            failure_categories[category] = failure_categories.get(category, 0) + 1

    return {
        'total': total,
        'passed': passed,
        'failed': failed + error,
        'skipped': skipped,
        'pass_rate': pass_rate,
        'avg_duration': avg_duration,
        'failure_categories': failure_categories,
    }
