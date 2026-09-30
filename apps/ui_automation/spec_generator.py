#!/usr/bin/env python3
"""
灵测 L-Test Platform - Spec 生成器

将 Django 用例数据动态生成 .spec.ts 测试脚本，供 Playwright Test 执行。

变量处理分层：
1. Python 端（run_case / _build_midscene_payload）：
   - 数据工厂函数（${random_phone()}、${timestamp()} 等）→ Python resolve_variables() 解析为实际值
   - 已有的 context_variables 中的变量 → Python 端直接替换
2. JS 运行时（.spec.ts 中）：
   - 步骤输出变量（output_var）产生的值 → 运行时写入 sharedVariables 对象
   - 后续步骤引用 ${varName} → JS 端从 sharedVariables 替换
   - 注意：Python 端已替换数据工厂函数，JS 端只需替换 output_var 产生的变量
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List


# ---- JS 辅助函数模板 ----
# 这段 JS 代码会被嵌入到每个生成的 .spec.ts 文件中
# 用于在运行时将 ${varName} 替换为 sharedVariables 中的实际值
JS_HELPER_FUNCTIONS = r"""
// ---- 运行时变量替换辅助函数 ----
// 替换文本中 ${varName} 占位符为 sharedVariables 中的实际值
function resolveRuntimeVariables(text: string, vars: Record<string, any>): string {
  if (!text || typeof text !== 'string') return text || '';
  return text.replace(/\$\{([^}]+)\}/g, (match, varName) => {
    if (varName in vars) {
      return String(vars[varName]);
    }
    return match; // 未找到变量，保留原样
  });
}

// 提取步骤输出变量值
// 优先级: aiQuery的data > input_value > message
function extractVariableValue(stepResult: any, inputVal: string): any {
  if (stepResult.data !== undefined && stepResult.data !== null) return stepResult.data;
  if (inputVal) return inputVal;
  if (stepResult.message) return stepResult.message;
  return '';
}

// 安全等待：浏览器已关闭时不抛异常（常见于页面导航/超时后浏览器被 Playwright 回收）
async function safeWait(page: any, ms: number): Promise<void> {
  try {
    await page.waitForTimeout(ms);
  } catch (_) {
    // 浏览器/页面已关闭，忽略等待错误
  }
}

// 失败截图
async function captureFailureScreenshot(page: any): Promise<string | null> {
  try {
    const buf = await page.screenshot({ type: 'png', timeout: 5000 });
    return 'data:image/png;base64,' + buf.toString('base64');
  } catch (_) {
    return null;
  }
}

// ---- 每个用例执行后回调 Django ----
// 从 stepResults 中提取该用例的步骤结果（caseStartIdx ~ 末尾），发送回调
async function callbackForExecution(
  executionId: number,
  caseId: number,
  stepResults: any[],
  caseStartIdx: number,
  status: string,
  errorMsg: string,
  sharedVariables: Record<string, any>,
  variableSnapshot: Record<string, any>
): Promise<void> {
  const caseStepResults = stepResults.slice(caseStartIdx);
  const isPassed = status === 'passed';
  const callbackUrl = `http://localhost:8000/api/ui-automation/midscene-cases/${caseId}/callback/`;
  const failedScreenshots = caseStepResults
    .filter((s: any) => s.status === 'failed' && s.screenshot)
    .map((s: any) => ({ order: s.order, screenshot: s.screenshot }));

  const callbackData = {
    task_id: process.env.LINGCE_LTEST_TASK_ID || '',
    execution_id: executionId,
    status: isPassed ? 'completed' : 'failed',
    result: {
      status: isPassed ? 'passed' : 'failed',
      step_results: caseStepResults,
    },
    error: errorMsg,
    completed_at: new Date().toISOString(),
    failed_screenshots: failedScreenshots,
    variable_snapshot: variableSnapshot,
  };

  // 导入 fs/path（提前导入，供后续报告扫描和结果文件写入使用）
  const fs = await import('fs');
  const path = await import('path');

  // ---- 查找 Midscene Reporter 生成的回放报告 ----
  // 扫描 MIDSCENE_RUN_DIR/report/ 目录，找到最近5分钟内生成的 .html 报告文件
  try {
    const midsceneRunDir = process.env.MIDSCENE_RUN_DIR || path.join(__dirname, '..', 'midscene_run');
    const reportDir = path.join(midsceneRunDir, 'report');
    if (fs.existsSync(reportDir)) {
      const files = fs.readdirSync(reportDir)
        .filter((f: string) => f.endsWith('.html'))
        .map((f: string) => {
          const fp = path.join(reportDir, f);
          return { name: f, path: fp, mtime: fs.statSync(fp).mtimeMs };
        })
        .sort((a: any, b: any) => b.mtime - a.mtime);
      const fiveMinutesAgo = Date.now() - 300000;
      for (const f of files) {
        if (f.mtime >= fiveMinutesAgo) {
          (callbackData as any).report_file = f.path;
          (callbackData as any).report_url = `http://localhost:8001/report/${f.name}`;
          break;
        }
      }
    }
  } catch (_: any) {}

  // 写入结果文件
  const resultsDir = process.env.LINGCE_LTEST_RESULTS_DIR || './midscene_run/results';
  const resultFilePath = path.join(resultsDir, `result_${executionId}.json`);
  try {
    fs.writeFileSync(resultFilePath, JSON.stringify(callbackData, null, 2));
  } catch (_) {}

  // 发送 HTTP 回调
  try {
    const http = await import('http');
    const body = JSON.stringify(callbackData);
    const urlObj = new URL(callbackUrl);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || '80',
      path: urlObj.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
      timeout: 10000,
    };
    const req = http.request(options, (res: any) => { res.resume(); });
    req.on('error', () => {});
    req.on('timeout', () => { req.destroy(); });
    req.write(body);
    req.end();
  } catch (_) {}
}
"""


def generate_single_case_spec(payload: Dict[str, Any], spec_path: str, env_path: str, result_dir: str) -> str:
    """
    生成单用例 .spec.ts 文件

    Args:
        payload: 用例执行参数（steps 已经过 Python resolve_variables 解析）
        spec_path: .spec.ts 文件输出路径
        env_path: .env 文件输出路径
        result_dir: 结果文件目录

    Returns:
        spec_path: 生成的 .spec.ts 文件路径
    """
    steps = payload.get('steps', [])
    url = payload.get('url', '')
    headless = payload.get('headless', True)
    viewport = payload.get('viewport', {'width': 1280, 'height': 768})
    execution_id = payload.get('execution_id', 0)
    case_name = payload.get('case_name', 'unnamed')
    case_id = payload.get('case_id', 0)
    user_agent = payload.get('user_agent')
    wait_after_action = payload.get('execution_config', {}).get('waitAfterAction', 1000)

    # 生成 .env 文件
    model_config = payload.get('model_config', {})
    _write_env_file(model_config, env_path)

    # 生成步骤代码
    steps_code = _generate_steps_code(steps, 'sharedVariables', wait_after_action)

    # 导航代码
    navigation_code = ''
    if url:
        navigation_code = f"    await page.goto('{url}', {{ waitUntil: 'domcontentloaded', timeout: 30000 }});\n    await safeWait(page, 2000);"

    # viewport
    viewport_code = ''
    if headless:
        viewport_code = f"    await page.setViewportSize({{ width: {viewport['width']}, height: {viewport['height']} }});"
    else:
        viewport_code = "    // 有头模式：窗口最大化，viewport 由 Playwright 的 noViewport 配置处理"

    # 防闪烁已移至 e2e/fixture.ts 的 CDP + CSS 双层机制
    # 不再在 spec 中重复注入，避免双重 addStyleTag
    anti_flicker_code = ''

    # 用户代理
    user_agent_code = ''
    if user_agent:
        user_agent_code = f"    await page.setExtraHTTPHeaders({{ 'User-Agent': '{user_agent}' }});"

    safe_case_name = case_name.replace("'", "\\'").replace('"', '\\"')

    # 使用拼接方式构建 spec 内容，避免 f-string 花括号冲突
    L = []
    L.append(f"/**")
    L.append(f" * 灵测 L-Test 自动生成 - 单用例执行")
    L.append(f" * 用例: {safe_case_name} (ID={case_id})")
    L.append(f" * 执行记录: {execution_id}")
    L.append(f" * 生成时间: {datetime.now().isoformat()}")
    L.append(f" */")
    L.append(f"import {{ test, expect }} from './fixture';")
    L.append(f"")
    L.append(JS_HELPER_FUNCTIONS)
    L.append(f"")
    L.append(f"// ---- 全局变量 ----")
    L.append(f"const sharedVariables: Record<string, any> = {{}};")
    L.append(f"const stepResults: any[] = [];")
    L.append(f"")
    L.append(f"test.describe('{safe_case_name}', () => {{")
    L.append(f"")
    L.append(f"  test('{safe_case_name}', async ({{ page, ai, aiQuery, aiAssert, aiWaitFor, aiTap, aiLocate, aiNumber, aiBoolean, aiString }}) => {{")
    L.append(f"    try {{")
    if navigation_code:
        L.append(navigation_code)
    if viewport_code:
        L.append(viewport_code)
    if anti_flicker_code:
        L.append(anti_flicker_code)
    if user_agent_code:
        L.append(user_agent_code)
    L.append(f"")
    # 步骤代码不需要额外缩进（JS语法不要求花括号内必须多缩进）
    L.append(f"      // ---- 逐步执行 ----")
    L.append(steps_code)
    L.append(f"    }} finally {{")
    L.append(f"      // ---- 附加步骤结果和变量快照（finally 确保失败时也能写入） ----")
    L.append(f"      await test.info().attach('step-results', {{ body: JSON.stringify(stepResults) }});")
    L.append(f"      await test.info().attach('variable-snapshot', {{ body: JSON.stringify(sharedVariables) }});")
    L.append(f"    }}")
    L.append(f"  }});")
    L.append(f"}});")

    spec_content = '\n'.join(L)

    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)

    return spec_path


def generate_shared_session_spec(cases: List[Dict[str, Any]], batch_config: Dict[str, Any],
                                  spec_path: str, env_path: str, result_dir: str) -> str:
    """
    生成共享会话 .spec.ts 文件

    方案A：单 test() + 多 test.step()，浏览器天然共享，变量天然传递
    """
    login_config = batch_config.get('login_config', {})
    batch_id = batch_config.get('batch_id', f'batch-{datetime.now().strftime("%Y%m%d%H%M%S")}')

    first_payload = cases[0]['payload'] if cases else {}
    headless = first_payload.get('headless', True)
    viewport = first_payload.get('viewport', {'width': 1280, 'height': 768})
    wait_after_action = first_payload.get('execution_config', {}).get('waitAfterAction', 1000)

    # 生成 .env 文件
    model_config = first_payload.get('model_config', {})
    _write_env_file(model_config, env_path)

    # 登录步骤
    login_code = ''
    login_steps = login_config.get('steps', [])
    if login_steps:
        login_step_lines = []
        for step in login_steps:
            instruction = step.get('instruction', '').replace("'", "\\'")
            if instruction:
                login_step_lines.append(f"        await ai('{instruction}');")
                login_step_lines.append(f"        await safeWait(page, {min(wait_after_action, 3000)});")
        if login_step_lines:
            login_code = "    await test.step('统一登录', async () => {\n"
            login_code += '\n'.join(login_step_lines) + '\n'
            login_code += "    });\n"

    # 每个用例的 test.step
    case_steps_code = ''
    for idx, case_item in enumerate(cases):
        execution_id = case_item['execution_id']
        case_id = case_item['case_id']
        case_payload = case_item['payload']
        case_name = case_payload.get('case_name', f'case_{case_id}')
        safe_case_name = case_name.replace("'", "\\'")
        steps = case_payload.get('steps', [])

        # 过滤登录步骤
        filtered_steps = [s for s in steps if not s.get('is_login_step')]

        steps_code = _generate_steps_code(filtered_steps, 'sharedVariables', wait_after_action)

        case_steps_code += f"\n    // ---- 用例 {idx + 1}/{len(cases)}: {safe_case_name} (execution_id={execution_id}, case_id={case_id}) ----\n"
        case_steps_code += f"    const case_{execution_id}_startIdx = stepResults.length;\n"
        case_steps_code += f"    let case_{execution_id}_status = 'passed';\n"
        case_steps_code += f"    let case_{execution_id}_error = '';\n"
        case_steps_code += f"    await test.step('[用例{idx + 1}] {safe_case_name}', async () => {{\n"
        case_steps_code += steps_code + '\n'
        case_steps_code += f"    }}).catch((err: any) => {{ case_{execution_id}_status = 'failed'; case_{execution_id}_error = err?.message || String(err); }});\n"
        # 每个用例执行完后立即回调Django
        case_steps_code += f"    await callbackForExecution({execution_id}, {case_id}, stepResults, case_{execution_id}_startIdx, case_{execution_id}_status, case_{execution_id}_error, sharedVariables, JSON.parse(JSON.stringify(sharedVariables)));\n"

    # 导航
    url = first_payload.get('url', '')
    navigation_code = ''
    if url:
        navigation_code = f"    await page.goto('{url}', {{ waitUntil: 'domcontentloaded', timeout: 30000 }});\n    await safeWait(page, 2000);"

    # viewport
    viewport_code = ''
    if headless:
        viewport_code = f"    await page.setViewportSize({{ width: {viewport['width']}, height: {viewport['height']} }});"

    # 防闪烁已移至 e2e/fixture.ts 的 CDP + CSS 双层机制
    # 不再在 spec 中重复注入，避免双重 addStyleTag
    anti_flicker_code = ''

    # 使用拼接方式构建 spec 内容，避免 f-string 花括号冲突
    L = []
    L.append(f"/**")
    L.append(f" * 灵测 L-Test 自动生成 - 共享会话执行")
    L.append(f" * 批次ID: {batch_id}")
    L.append(f" * 用例数: {len(cases)}")
    L.append(f" * 生成时间: {datetime.now().isoformat()}")
    L.append(f" */")
    L.append(f"import {{ test, expect }} from './fixture';")
    L.append(f"")
    L.append(JS_HELPER_FUNCTIONS)
    L.append(f"")
    L.append(f"// ---- 全局变量池（用例间共享）----")
    L.append(f"const sharedVariables: Record<string, any> = {{}};")
    L.append(f"const stepResults: any[] = [];")
    L.append(f"")
    L.append(f"test.describe('共享会话 - 批次 {batch_id}', () => {{")
    L.append(f"")
    L.append(f"  test('共享会话执行', async ({{ page, ai, aiQuery, aiAssert, aiWaitFor, aiTap, aiLocate, aiNumber, aiBoolean, aiString }}) => {{")
    L.append(f"    try {{")
    if navigation_code:
        L.append(navigation_code)
    if viewport_code:
        L.append(viewport_code)
    if anti_flicker_code:
        L.append(anti_flicker_code)
    if login_code:
        L.append(login_code.rstrip())
    L.append(case_steps_code.rstrip())
    L.append(f"    }} finally {{")
    L.append(f"      // 附加步骤结果和变量快照（finally 确保失败时也能写入）")
    L.append(f"      await test.info().attach('step-results', {{ body: JSON.stringify(stepResults) }});")
    L.append(f"      await test.info().attach('variable-snapshot', {{ body: JSON.stringify(sharedVariables) }});")
    L.append(f"    }}")
    L.append(f"  }});")
    L.append(f"}});")

    spec_content = '\n'.join(L)

    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)

    return spec_path


def _write_env_file(model_config: Dict[str, Any], env_path: str) -> None:
    """生成 .env 文件"""
    lines = []

    KEY_MAP = {
        'model_name': 'MIDSCENE_MODEL_NAME',
        'api_key': 'MIDSCENE_MODEL_API_KEY',
        'base_url': 'MIDSCENE_MODEL_BASE_URL',
        'model_family': 'MIDSCENE_MODEL_FAMILY',
        'model_timeout': 'MIDSCENE_MODEL_TIMEOUT',
        'temperature': 'MIDSCENE_MODEL_TEMPERATURE',
        'insight_model_name': 'MIDSCENE_INSIGHT_MODEL_NAME',
        'insight_api_key': 'MIDSCENE_INSIGHT_MODEL_API_KEY',
        'insight_base_url': 'MIDSCENE_INSIGHT_MODEL_BASE_URL',
        'insight_model_family': 'MIDSCENE_INSIGHT_MODEL_FAMILY',
        'planning_model_name': 'MIDSCENE_PLANNING_MODEL_NAME',
        'planning_api_key': 'MIDSCENE_PLANNING_MODEL_API_KEY',
        'planning_base_url': 'MIDSCENE_PLANNING_MODEL_BASE_URL',
        'planning_model_family': 'MIDSCENE_PLANNING_MODEL_FAMILY',
    }

    configs_to_process = []
    if model_config.get('default') and isinstance(model_config['default'], dict):
        configs_to_process.append(model_config['default'])
    if model_config.get('insight') and isinstance(model_config['insight'], dict):
        configs_to_process.append(model_config['insight'])
    if model_config.get('planning') and isinstance(model_config['planning'], dict):
        configs_to_process.append(model_config['planning'])
    if not configs_to_process:
        configs_to_process.append(model_config)

    for config in configs_to_process:
        for key, value in config.items():
            if value is None:
                continue
            env_key = KEY_MAP.get(key)
            if env_key:
                lines.append(f'{env_key}="{value}"')
            elif key.startswith('MIDSCENE_') or key.startswith('OPENAI_'):
                lines.append(f'{key}="{value}"')

    with open(env_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def _escape_js_string(text: str) -> str:
    """转义 JS 字符串中的特殊字符"""
    return text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')


def _generate_steps_code(steps: List[Dict[str, Any]], variables_name: str, wait_after_action: int) -> str:
    """
    生成步骤执行代码

    变量分层处理：
    - Python 端已将数据工厂函数（${random_phone()}等）解析为实际值
    - JS 运行时只需处理步骤输出变量（output_var）产生的 ${varName} 引用
    - 每个步骤执行前调用 resolveRuntimeVariables() 做运行时变量替换
    - 每个步骤完成后将 output_var 写入 sharedVariables
    """
    if not steps:
        return '    // 无步骤'

    lines = []
    for i, step in enumerate(steps):
        step_type = step.get('type', 'aiAct')
        instruction = step.get('instruction', '')
        input_value = step.get('input_value', '')
        output_var = step.get('output_var', '')
        mode = step.get('mode', 'ai')
        action_wait = step.get('action_wait', 0) or 0

        # 转义
        safe_instruction = _escape_js_string(instruction)
        safe_input_value = _escape_js_string(input_value)
        step_label = f'步骤{i + 1}: {safe_instruction[:50]}'
        total_wait = wait_after_action + action_wait

        # 判断是否需要运行时变量替换
        needs_var_resolve = '${' in instruction or '${' in input_value

        if mode == 'traditional':
            locator_value = step.get('locator_value', '')
            action_type = step.get('action_type', 'click')
            assert_type = step.get('assert_type', '')
            assert_value = step.get('assert_value', '')
            safe_locator = _escape_js_string(locator_value)
            safe_assert_value = _escape_js_string(assert_value)

            needs_var_resolve = needs_var_resolve or '${' in locator_value or '${' in assert_value

            # 断言代码
            assert_code = ''
            if assert_type == 'exists':
                assert_code = "\n        const visible = await locator.isVisible().catch(() => false);\n        if (!visible) throw new Error('断言失败: 元素不存在或不可见');"
            elif assert_type == 'equals':
                assert_code = f"\n        const text = await locator.textContent().catch(() => '');\n        if (text !== '{safe_assert_value}') throw new Error(`断言失败: 期望\"{safe_assert_value}\", 实际\"${{text}}\"`);"
            elif assert_type == 'contains':
                assert_code = f"\n        const text = await locator.textContent().catch(() => '');\n        if (!text.includes('{safe_assert_value}')) throw new Error(`断言失败: 期望包含\"{safe_assert_value}\", 实际\"${{text}}\"`);"
            elif assert_type == 'not_equals':
                assert_code = f"\n        const text = await locator.textContent().catch(() => '');\n        if (text === '{safe_assert_value}') throw new Error(`断言失败: 值不应等于\"{safe_assert_value}\"`);"

            # 变量提取
            var_extract = ''
            if output_var:
                var_extract = f"\n        const elText = await locator.textContent().catch(() => '');\n        {variables_name}['{output_var}'] = elText;\n        stepResult.output_var = '{output_var}';"

            # 运行时变量替换
            if needs_var_resolve:
                var_resolve_code = f"\n      const resolvedLocator = resolveRuntimeVariables('{safe_locator}', {variables_name});\n      const resolvedInput = resolveRuntimeVariables('{safe_input_value}', {variables_name});"
            else:
                var_resolve_code = f"\n      const resolvedLocator = '{safe_locator}';\n      const resolvedInput = '{safe_input_value}';"

            # 使用拼接方式构建步骤代码
            step_lines = []
            step_lines.append(f"    await test.step('{step_label}', async () => {{{var_resolve_code}")
            step_lines.append(f"      const locator = page.locator(resolvedLocator);")
            step_lines.append(f"      let stepResult: any = {{ order: {i + 1}, type: '{step_type}', mode: 'traditional', instruction: '{safe_instruction}', locator_value: resolvedLocator }};")
            step_lines.append(f"      try {{")
            step_lines.append(f"        switch ('{action_type}') {{")
            step_lines.append(f"          case 'click':")
            step_lines.append(f"            await locator.click({{ timeout: 60000 }}); stepResult.status = 'passed'; stepResult.message = '点击完成'; break;")
            step_lines.append(f"          case 'input':")
            step_lines.append(f"            await locator.fill(resolvedInput); stepResult.status = 'passed'; stepResult.message = '输入完成'; stepResult.input_value = resolvedInput; break;")
            step_lines.append(f"          case 'select':")
            step_lines.append(f"            await locator.selectOption(resolvedInput); stepResult.status = 'passed'; stepResult.message = '选择完成'; break;")
            step_lines.append(f"          case 'hover':")
            step_lines.append(f"            await locator.hover({{ timeout: 60000 }}); stepResult.status = 'passed'; stepResult.message = '悬停完成'; break;")
            step_lines.append(f"          case 'wait':")
            step_lines.append(f"            await page.waitForSelector(resolvedLocator, {{ timeout: 60000 }}); stepResult.status = 'passed'; stepResult.message = '元素出现'; break;")
            step_lines.append(f"          case 'scroll':")
            step_lines.append(f"            await locator.scrollIntoViewIfNeeded(); stepResult.status = 'passed'; stepResult.message = '滚动到元素'; break;")
            step_lines.append(f"          default:")
            step_lines.append(f"            await locator.click({{ timeout: 60000 }}); stepResult.status = 'passed'; stepResult.message = '操作完成({action_type})';")
            step_lines.append(f"        }}{assert_code}")
            step_lines.append(f"        await safeWait(page, {total_wait});{var_extract}")
            step_lines.append(f"      }} catch (err: any) {{")
            step_lines.append(f"        stepResult.status = 'failed'; stepResult.message = err.message;")
            step_lines.append(f"        const screenshot = await captureFailureScreenshot(page);")
            step_lines.append(f"        if (screenshot) stepResult.screenshot = screenshot;")
            step_lines.append(f"        stepResults.push(stepResult);")
            step_lines.append(f"        throw err;")
            step_lines.append(f"      }}")
            step_lines.append(f"      stepResults.push(stepResult);")
            step_lines.append(f"    }});")
            step_code = '\n'.join(step_lines)
        else:
            # AI 模式
            if needs_var_resolve:
                var_resolve_code = f"\n      let aiInstruction = resolveRuntimeVariables('{safe_instruction}', {variables_name});"
            else:
                var_resolve_code = f"\n      let aiInstruction = '{safe_instruction}';"

            input_append = ''
            if input_value:
                if needs_var_resolve:
                    input_append = f"\n      let resolvedInput = resolveRuntimeVariables('{safe_input_value}', {variables_name});\n      if (resolvedInput) aiInstruction += '，输入值为: ' + resolvedInput;"
                else:
                    input_append = f"\n      if ('{safe_input_value}') aiInstruction += '，输入值为: {safe_input_value}';"

            # AI 调用
            ai_call = _generate_ai_call_code(step_type)

            # 变量提取
            var_extract = ''
            if output_var:
                var_extract = f"\n        {variables_name}['{output_var}'] = result;\n        stepResult.output_var = '{output_var}';\n        stepResult.data = result;"

            # 使用拼接方式构建步骤代码
            step_lines = []
            step_lines.append(f"    await test.step('{step_label}', async () => {{{var_resolve_code}{input_append}")
            step_lines.append(f"      let stepResult: any = {{ order: {i + 1}, type: '{step_type}', mode: 'ai', instruction: '{safe_instruction}' }};")
            step_lines.append(f"      try {{")
            step_lines.append(f"        {ai_call}")
            step_lines.append(f"        await safeWait(page, {total_wait});{var_extract}")
            step_lines.append(f"        stepResult.status = 'passed'; stepResult.message = '操作完成';")
            step_lines.append(f"      }} catch (err: any) {{")
            step_lines.append(f"        stepResult.status = 'failed'; stepResult.message = err.message;")
            step_lines.append(f"        const screenshot = await captureFailureScreenshot(page);")
            step_lines.append(f"        if (screenshot) stepResult.screenshot = screenshot;")
            step_lines.append(f"        stepResults.push(stepResult);")
            step_lines.append(f"        throw err;")
            step_lines.append(f"      }}")
            step_lines.append(f"      stepResults.push(stepResult);")
            step_lines.append(f"    }});")
            step_code = '\n'.join(step_lines)

        lines.append(step_code)

    return '\n'.join(lines)


def _generate_ai_call_code(step_type: str) -> str:
    """生成 AI 调用代码"""
    if step_type == 'aiAct':
        return "const result = await ai(aiInstruction);"
    elif step_type == 'aiTap':
        return "const result = await aiTap(aiInstruction);"
    elif step_type == 'aiAssert':
        return "const result = await aiAssert(aiInstruction);"
    elif step_type == 'aiQuery':
        return "const result = await aiQuery(aiInstruction);"
    elif step_type == 'aiWaitFor':
        return "const result = await aiWaitFor(aiInstruction);"
    elif step_type == 'sleep':
        return "await safeWait(page, 2000); const result = 'sleep 2000ms';"
    else:
        return "const result = await ai(aiInstruction);"
