/**
 * Midscene 微服务 — 对齐 Midscene 官方 Playwright 集成方式
 * 
 * 核心流程（与 midscene-example/playwright-demo 完全一致）：
 *   1. chromium.launch() 启动浏览器
 *   2. browser.newPage() 创建页面
 *   3. page.goto() 导航到目标URL
 *   4. new PlaywrightAgent(page) 创建 Midscene Agent
 *   5. 逐步调用 agent.aiAct / aiAssert / aiTap / aiWaitFor 等
 *   6. agent.destroy() 完成报告写入
 *   7. browser.close() 关闭浏览器
 * 
 * 报告自动生成到 midscene_run/report/ 目录，通过 /report/ 路由静态服务访问
 */
const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');
const { PlaywrightAgent } = require('@midscene/web/playwright');
const { randomUUID } = require('crypto');

// @midscene/android 按需加载（APP端执行时才require）
let androidModules = null;
function getAndroidModules() {
  if (!androidModules) {
    try {
      androidModules = require('@midscene/android');
    } catch (e) {
      throw new Error('@midscene/android 未安装，APP端执行不可用');
    }
  }
  return androidModules;
}

const app = express();
app.use(cors());
app.use(express.json());

const PORT = 8001;

// Midscene 运行产物目录（与 Midscene CLI 行为一致）
const MIDSCENE_RUN_DIR = path.join(__dirname, 'midscene_run');
const REPORT_DIR = path.join(MIDSCENE_RUN_DIR, 'report');

// 确保目录存在
if (!fs.existsSync(REPORT_DIR)) {
  fs.mkdirSync(REPORT_DIR, { recursive: true });
}

// 报告静态文件服务
app.use('/report', express.static(REPORT_DIR));

// 任务存储
const tasks = new Map();

// ============ API ============

app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'midscene-service',
    version: '2.0.0',
    activeTasks: tasks.size,
    reportDir: REPORT_DIR,
  });
});

/**
 * 执行用例 — 核心接口
 * 
 * 请求体：
 * {
 *   url: 'https://example.com',      // 目标URL
 *   steps: [                          // 结构化步骤（与Midscene YAML flow对应）
 *     { type: 'aiAct', instruction: '...' },
 *     { type: 'aiAssert', instruction: '...' },
 *     { type: 'aiTap', instruction: '...' },
 *     { type: 'aiWaitFor', instruction: '...' },
 *     { type: 'sleep', duration: 2000 },
 *   ],
 *   headless: false,                  // 是否无头模式
 *   viewport: { width: 1280, height: 768 },
 *   model_config: {},                // 模型配置（通过环境变量传递给Midscene）
 *   callback_url: '',                 // 执行完成后回调Django
 *   execution_id: null,               // Django侧的执行记录ID
 * }
 */
app.post('/execute', async (req, res) => {
  const {
    platform = 'web',  // web 或 app
    url,
    steps = [],
    headless = false,
    viewport = { width: 1280, height: 768 },
    model_config = {},
    callback_url,
    execution_id,
    // Web高级配置
    user_agent = null,
    device_scale_factor = null,
    cookie_file = null,
    wait_for_network_idle = null,  // { timeout, continue_on_error }
    // APP配置
    app_config = null,  // { device_id, package_name, app_activity }
  } = req.body;

  if (!steps.length) {
    return res.status(400).json({ error: 'steps 不能为空' });
  }

  // APP平台校验（放宽：只提示，不阻止执行）
  if (platform === 'app' && (!app_config || !app_config.device_id || !app_config.package_name)) {
    task.logs && task.logs.push ? null : null; // 仅日志提示，不拦截
  }

  const taskId = randomUUID();
  const task = {
    task_id: taskId,
    platform,
    url,
    steps,
    headless,
    viewport,
    model_config,
    callback_url,
    execution_id,
    // Web高级配置
    user_agent,
    device_scale_factor,
    cookie_file,
    wait_for_network_idle,
    // APP配置
    app_config,
    created_at: new Date().toISOString(),
    started_at: null,
    completed_at: null,
    result: null,
    error: null,
    logs: [],
    report_file: null,
  };

  tasks.set(taskId, task);
  executeTask(taskId);

  res.json({ task_id: taskId, status: 'pending', message: '任务已提交' });
});

// 兼容旧的单步执行接口
app.post('/execute-step', async (req, res) => {
  const {
    task_type = 'aiAct',
    instruction,
    url,
    model_config = {},
    headless = false,
    viewport = { width: 1280, height: 768 },
    timeout = 60000,
    callback_url,
  } = req.body;

  if (!instruction) {
    return res.status(400).json({ error: 'instruction 是必填参数' });
  }

  // 将单步包装成 steps 格式
  const steps = [{ type: task_type, instruction }];

  const taskId = randomUUID();
  const task = {
    task_id: taskId,
    status: 'pending',
    url,
    steps,
    headless,
    viewport,
    model_config,
    callback_url,
    execution_id: null,
    created_at: new Date().toISOString(),
    started_at: null,
    completed_at: null,
    result: null,
    error: null,
    logs: [],
    report_file: null,
  };

  tasks.set(taskId, task);
  executeTask(taskId);

  res.json({ task_id: taskId, status: 'pending', message: '任务已提交' });
});

// 查询任务
app.get('/task/:taskId', (req, res) => {
  const task = tasks.get(req.params.taskId);
  if (!task) {
    return res.status(404).json({ error: '任务不存在' });
  }
  res.json({
    task_id: task.task_id,
    status: task.status,
    browser_closed: task.browser_closed !== false,  // 兼容旧任务
    url: task.url,
    started_at: task.started_at,
    completed_at: task.completed_at,
    result: task.result,
    error: task.error,
    report_url: task.report_file ? `http://localhost:${PORT}/report/${path.basename(task.report_file)}` : null,
    logs: task.logs,
  });
});

// 任务列表
app.get('/tasks', (req, res) => {
  const list = Array.from(tasks.values()).map(t => ({
    task_id: t.task_id,
    status: t.status,
    url: t.url,
    created_at: t.created_at,
    completed_at: t.completed_at,
    error: t.error,
    report_url: t.report_file ? `http://localhost:${PORT}/report/${path.basename(t.report_file)}` : null,
  }));
  res.json(list);
});

// 获取报告信息
app.get('/task/:taskId/report', (req, res) => {
  const task = tasks.get(req.params.taskId);
  if (!task) {
    return res.status(404).json({ error: '任务不存在' });
  }
  if (!task.report_file) {
    return res.status(404).json({ error: '报告尚未生成' });
  }
  const reportFileName = path.basename(task.report_file);
  res.json({
    task_id: task.task_id,
    report_url: `http://localhost:${PORT}/report/${reportFileName}`,
    report_file: task.report_file,
    status: task.status,
  });
});

// 列出已有报告
app.get('/reports', (req, res) => {
  try {
    const files = fs.readdirSync(REPORT_DIR)
      .filter(f => f.endsWith('.html'))
      .map(f => ({
        filename: f,
        url: `http://localhost:${PORT}/report/${f}`,
        size: fs.statSync(path.join(REPORT_DIR, f)).size,
        mtime: fs.statSync(path.join(REPORT_DIR, f)).mtime,
      }))
      .sort((a, b) => b.mtime - a.mtime)
      .slice(0, 50);
    res.json(files);
  } catch (e) {
    res.json([]);
  }
});

// 关闭浏览器（预留，当前每次任务独立浏览器）
app.post('/browser/close', (req, res) => {
  res.json({ message: '当前版本每次任务独立浏览器，无需手动关闭' });
});

// ============ 执行引擎 ============

async function executeTask(taskId) {
  const task = tasks.get(taskId);
  if (!task) return;

  task.status = 'running';
  task.started_at = new Date().toISOString();
  task.logs.push({ time: new Date().toISOString(), level: 'info', message: '开始执行任务' });
  task.logs.push({ time: new Date().toISOString(), level: 'info', message: `callback_url=${task.callback_url || '空'}, execution_id=${task.execution_id || '空'}` });

  let browser = null;

  try {
    // ---- 1. 设置模型环境变量（Midscene 通过环境变量读取模型配置）----
    const mc = task.model_config || {};
    const prevEnv = {};
    const envMappings = {
      api_key: 'MIDSCENE_MODEL_API_KEY',
      base_url: 'MIDSCENE_MODEL_BASE_URL',
      model_name: 'MIDSCENE_MODEL_NAME',
      model_family: 'MIDSCENE_MODEL_FAMILY',
    };

    for (const [key, envName] of Object.entries(envMappings)) {
      if (mc[key]) {
        prevEnv[envName] = process.env[envName];
        process.env[envName] = mc[key];
      }
    }

    // 设置 MIDSCENE_RUN_DIR，让报告存到我们的目录
    const prevRunDir = process.env.MIDSCENE_RUN_DIR;
    process.env.MIDSCENE_RUN_DIR = MIDSCENE_RUN_DIR;

    // ---- 2. 根据平台启动浏览器或连接APP设备 ----
    let page = null;
    let agent = null;  // Midscene Agent（Web: PlaywrightAgent, APP: AndroidAgent）

    if (task.platform === 'app') {
      // ===== APP端：使用 @midscene/android 原生支持 =====
      // 与 Midscene YAML 工作流一致：AndroidDevice + AndroidAgent
      const appCfg = task.app_config || {};
      task.logs.push({ time: new Date().toISOString(), level: 'info', message: `APP模式: device=${appCfg.device_id || '自动检测'}, pkg=${appCfg.package_name || '未指定'}` });

      const { AndroidAgent, AndroidDevice, getConnectedDevices } = getAndroidModules();

      // 获取设备ID
      let deviceId = appCfg.device_id;
      if (!deviceId) {
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: '未指定device_id，自动检测已连接设备...' });
        const devices = await getConnectedDevices();
        if (!devices.length) {
          throw new Error('未检测到已连接的Android设备，请通过 adb devices 确认设备已连接');
        }
        deviceId = devices[0].udid;
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `自动选择设备: ${deviceId}` });
      }

      // 创建 AndroidDevice 并连接
      const androidPage = new AndroidDevice(deviceId);
      await androidPage.connect();
      task.logs.push({ time: new Date().toISOString(), level: 'info', message: `Android设备已连接: ${deviceId}` });

      // 如果配置了启动URL，则打开
      if (task.url) {
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `APP导航到: ${task.url}` });
        await androidPage.launch(task.url);
        await new Promise(r => setTimeout(r, 3000)); // 等待页面加载
      }

      // 创建 AndroidAgent（与 Midscene 示例一致）
      agent = new AndroidAgent(androidPage, {
        aiActContext: 'If any location, permission, user agreement, etc. popup, click agree. If login page pops up, close it.',
      });
      task.logs.push({ time: new Date().toISOString(), level: 'info', message: 'AndroidAgent 已初始化' });

    } else {
      // ===== Web端：启动浏览器（与 playwright-demo/demo.ts 一致）=====
      task.logs.push({ time: new Date().toISOString(), level: 'info', message: `Web模式: 启动浏览器 headless=${task.headless}` });
      
      const launchArgs = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-blink-features=AutomationControlled',
        '--disable-infobars',
        '--disable-background-timer-throttling',
        '--disable-renderer-backgrounding',
        '--no-first-run',
      ];
      // 有头模式：直接以目标尺寸启动，加防闪烁参数
      if (!task.headless) {
        const winWidth = task.viewport.width || 1280;
        const winHeight = task.viewport.height || 768;
        launchArgs.push(`--window-size=${winWidth},${winHeight}`);
        launchArgs.push('--window-position=0,0');
        // 禁用GPU合成、DWM等，减少Windows有头模式下渲染管线切换导致的窗口闪烁
        launchArgs.push('--disable-gpu');
        launchArgs.push('--disable-software-rasterizer');
        launchArgs.push('--disable-dev-shm-usage');
        launchArgs.push('--disable-features=TranslateUI,WindowsDwmComposition');
        // 减少渲染管线抖动：跳帧和绘制节奏控制
        launchArgs.push('--disable-frame-rate-limit');
        launchArgs.push('--run-all-compositor-stages-before-draw');
        // 禁用平滑滚动（避免滚动时触发多余的重绘帧）
        launchArgs.push('--disable-smooth-scrolling');
      }

      browser = await chromium.launch({
        headless: task.headless,
        args: launchArgs,
      });

      const contextOptions = {};
      if (task.user_agent) {
        contextOptions.userAgent = task.user_agent;
      }
      if (task.device_scale_factor) {
        contextOptions.deviceScaleFactor = task.device_scale_factor;
      }
      if (task.cookie_file) {
        contextOptions.storageState = task.cookie_file;
      }
      // 有头模式：不固定viewport，窗口大小由--window-size控制
      if (!task.headless) {
        contextOptions.noViewport = true;
      }

      const context = await browser.newContext(contextOptions);
      page = await context.newPage();
      // 仅无头模式下设置固定viewport
      if (task.headless) {
        await page.setViewportSize(task.viewport);
      }

      // 有头模式：防闪烁优化（CSS禁用动画 + Chromium启动参数 + CDP截图）
      // 核心：步骤执行期间用CDP截图替代Playwright截图防闪烁，步骤结束后立即释放CDP session
      if (!task.headless) {
        await page.addStyleTag({
          content: `
            *, *::before, *::after {
              animation-duration: 0.01ms !important;
              animation-iteration-count: 1 !important;
              transition-duration: 0.01ms !important;
              scroll-behavior: auto !important;
            }
          `
        });

        // 创建CDP session用于步骤执行期间的截图
        const cdpClient = await context.newCDPSession(page);
        const originalScreenshot = page.screenshot.bind(page);
        page.screenshot = async function (opts = {}) {
          try {
            const { data } = await cdpClient.send('Page.captureScreenshot', {
              format: opts.type || 'jpeg',
              quality: opts.type === 'png' ? undefined : (opts.quality || 90),
            });
            return Buffer.from(data, 'base64');
          } catch (e) {
            return originalScreenshot(opts);
          }
        };

        // 步骤结束后恢复原始截图方法（不等待cdpClient.detach，由browser.close自动清理）
        page._releaseCdpScreenshot = () => {
          page.screenshot = originalScreenshot;
        };
      }

      // ---- 导航到目标URL ----
      if (task.url) {
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `导航到: ${task.url}` });
        const gotoOptions = { waitUntil: 'domcontentloaded', timeout: 30000 };
        if (task.wait_for_network_idle && task.wait_for_network_idle.timeout) {
          gotoOptions.waitUntil = 'networkidle';
          gotoOptions.timeout = task.wait_for_network_idle.timeout;
        }
        await page.goto(task.url, gotoOptions);
        await page.waitForTimeout(2000); // 等待页面渲染
      }

      // Web端创建 PlaywrightAgent
      // forceChromeSelectRendering: false 避免注入额外的style元素导致页面重绘
      agent = new PlaywrightAgent(page, { forceChromeSelectRendering: false });
      task.logs.push({ time: new Date().toISOString(), level: 'info', message: 'PlaywrightAgent 已初始化 (Web模式, forceChromeSelectRendering=false)' });
    }

    // ---- 4. 逐步执行（Web和APP共用agent接口） ----
    const stepResults = [];
    const STEP_TIMEOUT = 60000; // 单步超时60秒
    
    function withTimeout(promise, ms, label) {
      return Promise.race([
        promise,
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error(`${label} 超时（${ms/1000}秒）`)), ms)
        )
      ]);
    }
    
    for (let i = 0; i < task.steps.length; i++) {
      const step = task.steps[i];
      // 如果有 input_value，将其追加到 instruction 中（Midscene是AI驱动，参数通过自然语言传递）
      let instruction = step.instruction || '';
      const input_value = step.input_value || '';
      if (input_value) {
        instruction = instruction
          ? `${instruction}，输入值为: ${input_value}`
          : `输入: ${input_value}`;
      }
      const stepLog = `步骤${i + 1} [${step.type}]: ${instruction}`;
      task.logs.push({ time: new Date().toISOString(), level: 'info', message: stepLog });

      try {
        let stepResult;
        switch (step.type) {
          case 'aiAct':
            await withTimeout(agent.aiAct(instruction), STEP_TIMEOUT, `步骤${i+1} aiAct`);
            stepResult = { status: 'passed', message: '操作完成' };
            if (input_value) stepResult.input_value = input_value;
            break;

          case 'aiTap':
            await withTimeout(agent.aiTap(instruction), STEP_TIMEOUT, `步骤${i+1} aiTap`);
            stepResult = { status: 'passed', message: '点击完成' };
            if (input_value) stepResult.input_value = input_value;
            break;

          case 'aiAssert':
            await withTimeout(agent.aiAssert(instruction), STEP_TIMEOUT, `步骤${i+1} aiAssert`);
            stepResult = { status: 'passed', message: '断言通过' };
            if (input_value) stepResult.input_value = input_value;
            break;

          case 'aiQuery':
            const queryResult = await withTimeout(agent.aiQuery(instruction), STEP_TIMEOUT, `步骤${i+1} aiQuery`);
            stepResult = { status: 'passed', message: '查询完成', data: queryResult };
            if (input_value) stepResult.input_value = input_value;
            break;

          case 'aiWaitFor':
            await withTimeout(agent.aiWaitFor(instruction), STEP_TIMEOUT, `步骤${i+1} aiWaitFor`);
            stepResult = { status: 'passed', message: '等待条件满足' };
            break;

          case 'sleep':
            await new Promise(r => setTimeout(r, step.duration || 2000));
            stepResult = { status: 'passed', message: `等待${(step.duration || 2000) / 1000}秒` };
            break;

          default:
            // 默认当作 aiAct
            await withTimeout(agent.aiAct(step.instruction), STEP_TIMEOUT, `步骤${i+1} aiAct`);
            stepResult = { status: 'passed', message: '操作完成（默认aiAct）' };
        }

        stepResults.push({
          order: i + 1,
          type: step.type,
          instruction: step.instruction,
          output_var: step.output_var || null,
          ...stepResult,
        });
      } catch (stepErr) {
        // 步骤失败
        stepResults.push({
          order: i + 1,
          type: step.type,
          instruction: step.instruction,
          output_var: step.output_var || null,
          status: 'failed',
          message: stepErr.message,
        });
        task.logs.push({ time: new Date().toISOString(), level: 'error', message: `步骤${i + 1} 失败: ${stepErr.message}` });
        
        // 步骤失败即终止（与 Midscene YAML continueOnError=false 行为一致）
        break;
      }
    }

    // ---- 5.5 恢复原始截图方法（步骤执行完毕，后续agent.destroy和browser.close走原生路径）----
    if (page && typeof page._releaseCdpScreenshot === 'function') {
      page._releaseCdpScreenshot();
    }

    // ---- 6. 判断整体结果（步骤已执行完，立刻出结果，不等agent.destroy）----
    const hasFailed = stepResults.some(s => s.status === 'failed');
    task.result = {
      status: hasFailed ? 'failed' : 'passed',
      step_results: stepResults,
    };
    task.status = hasFailed ? 'failed' : 'completed';
    if (hasFailed && !task.error) {
      const failedStep = stepResults.find(s => s.status === 'failed');
      task.error = failedStep?.message || '步骤执行失败';
    }

    // ---- 7. 恢复环境变量 ----
    for (const [key, envName] of Object.entries(envMappings)) {
      if (mc[key]) {
        if (prevEnv[envName] === undefined) {
          delete process.env[envName];
        } else {
          process.env[envName] = prevEnv[envName];
        }
      }
    }
    if (prevRunDir === undefined) {
      delete process.env.MIDSCENE_RUN_DIR;
    } else {
      process.env.MIDSCENE_RUN_DIR = prevRunDir;
    }

  } catch (err) {
    task.status = 'failed';
    task.error = err.message;
    task.result = { status: 'failed', error: err.message };
    task.logs.push({ time: new Date().toISOString(), level: 'error', message: `执行失败: ${err.message}` });

  } finally {
    task.completed_at = new Date().toISOString();

    // ---- 全同步流程：回调Django → agent.destroy → 关浏览器 ----
    // await executeTask() 只有这个 finally 块走完才会返回
    // executeBatch for 循环里 await executeTask() 自然就是一条完再下一条

    // 1. 回调Django
    if (task.callback_url) {
      try {
        const callbackBody = JSON.stringify({
          task_id: task.task_id,
          execution_id: task.execution_id,
          status: task.status,
          result: task.result,
          error: task.error,
          completed_at: task.completed_at,
          report_url: null,
          report_file: null,
        });

        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `回调Django: ${task.callback_url}` });

        const fetch = require('node-fetch');
        const cbRes = await fetch(task.callback_url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: callbackBody,
        });

        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `回调响应: HTTP ${cbRes.status}` });
      } catch (e) {
        task.logs.push({ time: new Date().toISOString(), level: 'warn', message: `回调失败: ${e.message}` });
      }
    }

    // 2. agent.destroy（生成报告，3秒超时）
    try {
      if (agent) {
        await Promise.race([
          agent.destroy(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 3000))
        ]);
        if (agent.reportFile) task.report_file = agent.reportFile;
      }
    } catch (_) {}

    // 3. 关闭浏览器（2秒超时）
    try {
      if (browser) await Promise.race([
        browser.close(),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 2000))
      ]);
    } catch (_) {}

    // 4. 按PID精准杀残留进程
    try {
      if (browser && browser.process) {
        const proc = browser.process();
        if (proc) {
          const { execSync } = require('child_process');
          execSync(`taskkill /f /pid ${proc.pid} /t 2>nul`, { timeout: 2000 });
        }
      }
    } catch (_) {}

    task.browser_closed = true;
    task.logs.push({ time: new Date().toISOString(), level: 'info', message: '用例执行完毕，浏览器已关闭' });
  }
}

// ============ 批量执行接口（计划执行用） ============

/**
 * POST /execute-batch
 * 
 * 一次接收计划所有用例，微服务内部顺序执行，每条完就回调Django。
 * Django 不需要当调度器，不再轮询，彻底解决浏览器竞态问题。
 * 
 * 请求体：
 * {
 *   cases: [
 *     { payload: { <与/execute相同的body> }, execution_id: 123, case_id: 456 },
 *     ...
 *   ],
 *   plan_id: 2,           // 计划ID（回调用）
 *   callback_base: 'http://localhost:8000/api/ui-automation/...',  // Django回调基础URL
 * }
 */
app.post('/execute-batch', async (req, res) => {
  const { cases = [], plan_id, callback_base } = req.body;

  if (!cases.length) {
    return res.status(400).json({ error: 'cases 不能为空' });
  }

  const batchId = randomUUID();
  const batchTask = {
    batch_id: batchId,
    plan_id,
    status: 'running',
    total: cases.length,
    completed: 0,
    results: [],
    created_at: new Date().toISOString(),
  };

  batches.set(batchId, batchTask);

  // 后台顺序执行
  executeBatch(batchId, cases);

  res.json({ batch_id: batchId, status: 'pending', total: cases.length, message: '批量任务已提交' });
});

// 批量任务存储
const batches = new Map();

// 查询批量任务状态
app.get('/batch/:batchId', (req, res) => {
  const batch = batches.get(req.params.batchId);
  if (!batch) {
    return res.status(404).json({ error: '批量任务不存在' });
  }
  res.json({
    batch_id: batch.batch_id,
    plan_id: batch.plan_id,
    status: batch.status,
    total: batch.total,
    completed: batch.completed,
    results: batch.results.map(r => ({
      execution_id: r.execution_id,
      case_id: r.case_id,
      status: r.status,
      error: r.error,
    })),
  });
});

/**
 * 顺序执行批量用例
 * 简单 for 循环 await executeTask()，一条完全结束再下一条
 */
async function executeBatch(batchId, cases) {
  const batch = batches.get(batchId);
  if (!batch) return;

  for (let i = 0; i < cases.length; i++) {
    const caseItem = cases[i];
    const payload = caseItem.payload;
    const executionId = caseItem.execution_id;
    const caseId = caseItem.case_id;

    batch.results.push({ execution_id: executionId, case_id: caseId, status: 'running', error: null });
    const resultIdx = batch.results.length - 1;

    try {
      // 构造标准task，复用 executeTask
      const taskId = randomUUID();
      const task = {
        task_id: taskId,
        platform: payload.platform || 'web',
        url: payload.url,
        steps: payload.steps || [],
        headless: payload.headless || false,
        viewport: payload.viewport || { width: 1280, height: 768 },
        model_config: payload.model_config || {},
        callback_url: payload.callback_url,
        execution_id: executionId,
        user_agent: payload.user_agent || null,
        device_scale_factor: payload.device_scale_factor || null,
        cookie_file: payload.cookie_file || null,
        wait_for_network_idle: payload.wait_for_network_idle || null,
        app_config: payload.app_config || null,
        created_at: new Date().toISOString(),
        started_at: null,
        completed_at: null,
        result: null,
        error: null,
        logs: [],
        report_file: null,
      };

      tasks.set(taskId, task);
      await executeTask(taskId);

      batch.results[resultIdx].status = task.status === 'completed' ? 'passed' : 'failed';
      batch.results[resultIdx].error = task.error;

    } catch (err) {
      batch.results[resultIdx].status = 'failed';
      batch.results[resultIdx].error = err.message;
    }

    batch.completed = i + 1;
  }

  batch.status = 'completed';
}

// ============ 启动 ============

app.listen(PORT, () => {
  console.log(`[Midscene Service v2] 已启动，端口: ${PORT}`);
  console.log(`[Midscene Service] 健康检查: http://localhost:${PORT}/health`);
  console.log(`[Midscene Service] 执行接口: POST http://localhost:${PORT}/execute`);
  console.log(`[Midscene Service] 报告目录: ${REPORT_DIR}`);
  console.log(`[Midscene Service] 报告访问: http://localhost:${PORT}/report/<filename>`);
});
