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
const { v4: uuidv4 } = require('uuid');

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

  const taskId = uuidv4();
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

  const taskId = uuidv4();
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

    // ---- 6. 销毁 Agent（必须！报告在这步写入磁盘）----
    task.logs.push({ time: new Date().toISOString(), level: 'info', message: '正在生成报告...' });
    try {
      await Promise.race([
        agent.destroy(),
        new Promise((_, reject) => setTimeout(() => reject(new Error('agent.destroy() 超时30秒')), 30000))
      ]);
    } catch (destroyErr) {
      task.logs.push({ time: new Date().toISOString(), level: 'warn', message: `Agent销毁超时或失败: ${destroyErr.message}` });
    }

    // ---- 7. 获取报告路径 ----
    if (agent.reportFile) {
      task.report_file = agent.reportFile;
      task.logs.push({ time: new Date().toISOString(), level: 'info', message: `报告已生成: ${agent.reportFile}` });
    } else {
      task.logs.push({ time: new Date().toISOString(), level: 'warn', message: '未获取到报告路径，尝试扫描报告目录' });
      // fallback: 扫描报告目录找最新生成的文件
      try {
        const reportFiles = fs.readdirSync(REPORT_DIR).filter(f => f.endsWith('.html'));
        if (reportFiles.length > 0) {
          const latest = reportFiles.map(f => ({
            name: f,
            mtime: fs.statSync(path.join(REPORT_DIR, f)).mtime,
          })).sort((a, b) => b.mtime - a.mtime)[0];
          task.report_file = path.join(REPORT_DIR, latest.name);
          task.logs.push({ time: new Date().toISOString(), level: 'info', message: `Fallback找到报告: ${task.report_file}` });
        }
      } catch (_) {}
    }

    // ---- 8. 判断整体结果 ----
    const hasFailed = stepResults.some(s => s.status === 'failed');
    task.result = {
      status: hasFailed ? 'failed' : 'passed',
      step_results: stepResults,
    };
    task.status = hasFailed ? 'failed' : 'completed';

    // ---- 恢复环境变量 ----
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

    // 失败时也要尝试 destroy agent（让报告记录失败状态）
    try {
      if (agent) {
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: '尝试销毁Agent生成报告...' });
        await Promise.race([
          agent.destroy(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('agent.destroy() 超时30秒')), 30000))
        ]);
        if (agent.reportFile) {
          task.report_file = agent.reportFile;
          task.logs.push({ time: new Date().toISOString(), level: 'info', message: `失败报告已生成: ${agent.reportFile}` });
        }
      }
    } catch (destroyErr) {
      task.logs.push({ time: new Date().toISOString(), level: 'warn', message: `Agent销毁超时或失败: ${destroyErr.message}` });
    }

  } finally {
    task.completed_at = new Date().toISOString();

    // 关闭浏览器（加超时保护，避免卡住整个执行流程）
    try {
      if (browser) {
        await Promise.race([
          browser.close(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('browser.close() 超时10秒')), 10000))
        ]);
      }
    } catch (closeErr) {
      task.logs.push({ time: new Date().toISOString(), level: 'warn', message: `浏览器关闭超时，强制终止: ${closeErr.message}` });
      // 强制杀掉chromium进程
      try {
        const { execSync } = require('child_process');
        execSync('taskkill /f /im chromium.exe 2>nul', { timeout: 3000 });
        execSync('taskkill /f /im chrome.exe 2>nul', { timeout: 3000 });
      } catch (_) {}
    }

    // 回调 Django
    if (task.callback_url) {
      try {
        let reportUrl = null;
        if (task.report_file) {
          reportUrl = `http://localhost:${PORT}/report/${path.basename(task.report_file)}`;
        }

        const callbackBody = JSON.stringify({
          task_id: task.task_id,
          execution_id: task.execution_id,
          status: task.status,
          result: task.result,
          error: task.error,
          completed_at: task.completed_at,
          report_url: reportUrl,
          report_file: task.report_file,
        });

        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `正在回调Django: ${task.callback_url}` });
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `回调payload: execution_id=${task.execution_id}, status=${task.status}` });

        const fetch = require('node-fetch');
        const cbRes = await fetch(task.callback_url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: callbackBody,
        });

        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `回调响应: HTTP ${cbRes.status} ${cbRes.statusText}` });
      } catch (e) {
        task.logs.push({ time: new Date().toISOString(), level: 'warn', message: `回调失败: ${e.message}` });
      }
    } else {
      task.logs.push({ time: new Date().toISOString(), level: 'warn', message: '未配置callback_url，跳过回调' });
    }
  }
}

// ============ 启动 ============

app.listen(PORT, () => {
  console.log(`[Midscene Service v2] 已启动，端口: ${PORT}`);
  console.log(`[Midscene Service] 健康检查: http://localhost:${PORT}/health`);
  console.log(`[Midscene Service] 执行接口: POST http://localhost:${PORT}/execute`);
  console.log(`[Midscene Service] 报告目录: ${REPORT_DIR}`);
  console.log(`[Midscene Service] 报告访问: http://localhost:${PORT}/report/<filename>`);
});
