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
const { PNG } = require('pngjs');

// pixelmatch 是 ESM 模块，需要动态导入
let pixelmatch = null;
async function loadPixelmatch() {
  if (!pixelmatch) {
    const mod = await import('pixelmatch');
    pixelmatch = mod.default || mod;
  }
  return pixelmatch;
}

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
app.use(express.json({ limit: '50mb' }));

const PORT = 8001;

// ============ 并发控制 ============
const MAX_CONCURRENCY = 3;  // 最大并行执行数
let activeCount = 0;        // 当前活跃任务数
const taskQueue = [];       // 等待队列: [{ taskId, resolve }]

/** 获取执行槽位（信号量模式） */
function acquireSlot() {
  return new Promise((resolve) => {
    if (activeCount < MAX_CONCURRENCY) {
      activeCount++;
      resolve();
    } else {
      taskQueue.push({ resolve });
    }
  });
}

/** 释放执行槽位 */
function releaseSlot() {
  if (taskQueue.length > 0) {
    const { resolve } = taskQueue.shift();
    resolve();  // 直接转让槽位，不增减 activeCount
  } else {
    activeCount = Math.max(0, activeCount - 1);
  }
}

// ============ 任务取消控制 ============
// 存储已被请求取消的 taskId，executeTask 检查后提前退出
const cancelledTasks = new Set();

// Midscene 运行产物目录（与 Midscene CLI 行为一致）
const MIDSCENE_RUN_DIR = path.join(__dirname, 'midscene_run');
const REPORT_DIR = path.join(MIDSCENE_RUN_DIR, 'report');
const SCREENSHOT_DIR = path.join(MIDSCENE_RUN_DIR, 'screenshots');
// 旧 runner 截图目录（midscene-runner.js 保存到 midscene-service/screenshots）
const LEGACY_SCREENSHOT_DIR = path.join(__dirname, 'screenshots');

// 确保目录存在
for (const dir of [REPORT_DIR, SCREENSHOT_DIR, LEGACY_SCREENSHOT_DIR]) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

// 报告静态文件服务（全局报告目录 + 任务独立子目录）
app.use('/report', express.static(REPORT_DIR));
// 任务独立报告目录：通过 /report/<taskId>/report/<filename> 访问
app.use('/report', express.static(MIDSCENE_RUN_DIR));
// 截图静态服务：优先从 midscene_run/screenshots 查找，再从旧 screenshots 目录查找
app.use('/screenshots', express.static(SCREENSHOT_DIR));
app.use('/screenshots', express.static(LEGACY_SCREENSHOT_DIR));

// 任务存储
const tasks = new Map();

// ============ API ============

app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'midscene-service',
    version: '2.1.0',
    activeTasks: tasks.size,
    activeRunning: activeCount,
    maxConcurrency: MAX_CONCURRENCY,
    queuedTasks: taskQueue.length,
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
    device_type = '',  // web/android/ios/harmony（优先于platform）
    url,
    steps = [],
    headless = false,
    viewport = { width: 1280, height: 768 },
    model_config = {},   // AI模型配置（注入Agent构造函数）
    callback_url,
    execution_id,
    // Web高级配置
    user_agent = null,
    device_scale_factor = null,
    cookie_file = null,
    wait_for_network_idle = null,  // { timeout, continue_on_error }
    // APP配置
    app_config = null,  // { device_id, package_name, app_activity }
    // 全局配置合并后的执行参数
    execution_config = {},   // { waitAfterAction, screenshotShrinkFactor, ... }
    report_config = {},     // { generateReport, ... }
    web_config = {},        // { browserPath, ... }
    android_config = {},    // { androidAdbPath, ... }
    ios_config = {},        // { wdaPort, ... }
    harmony_config = {},    // { hdcPath, ... }
    app_name_mapping = {},   // { "微信": "com.tencent.mm" }
  } = req.body;

  if (!steps.length) {
    return res.status(400).json({ error: 'steps 不能为空' });
  }

  // APP平台校验（放宽：只提示，不阻止执行）
  if (platform === 'app' && (!app_config || !app_config.device_id || !app_config.package_name)) {
    task.logs && task.logs.push ? null : null; // 仅日志提示，不拦截
  }

  const taskId = randomUUID();
  const resolvedDeviceType = device_type || (platform === 'app' ? 'android' : 'web');
  const task = {
    task_id: taskId,
    platform,
    device_type: resolvedDeviceType,
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
    // 全局配置（三级配置合并后）
    execution_config,
    report_config,
    web_config,
    android_config,
    ios_config,
    harmony_config,
    app_name_mapping,
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

// ============ 任务取消接口 ============
app.post('/cancel/:taskId', (req, res) => {
  const taskId = req.params.taskId;
  const task = tasks.get(taskId);
  if (!task) {
    return res.status(404).json({ error: '任务不存在' });
  }
  if (task.status === 'completed' || task.status === 'failed') {
    return res.status(400).json({ error: '任务已结束，无法取消' });
  }
  cancelledTasks.add(taskId);
  task.logs.push({ time: new Date().toISOString(), level: 'warn', message: '收到取消请求' });
  res.json({ task_id: taskId, status: 'cancelling', message: '取消请求已发送' });
});

// ============ 视觉回归：截图对比 + 基线管理 ============

const BASELINE_DIR = path.join(MIDSCENE_RUN_DIR, 'baselines');
if (!fs.existsSync(BASELINE_DIR)) {
  fs.mkdirSync(BASELINE_DIR, { recursive: true });
}
app.use('/baselines', express.static(BASELINE_DIR));

/**
 * POST /visual-compare
 * 对比两张截图，返回差异百分比和差异图URL
 * body: { baseline: "http://localhost:8001/screenshots/xxx.png", current: "http://localhost:8001/screenshots/yyy.png", threshold?: 0.1 }
 */
app.post('/visual-compare', async (req, res) => {
  const { baseline, current, threshold = 0.1 } = req.body;
  if (!baseline || !current) {
    return res.status(400).json({ error: '需要提供 baseline 和 current 截图URL' });
  }

  try {
    // 下载两张图片
    const fetch = require('node-fetch');
    const [baselineRes, currentRes] = await Promise.all([
      fetch(baseline),
      fetch(current),
    ]);
    if (!baselineRes.ok || !currentRes.ok) {
      return res.status(400).json({ error: '无法获取截图文件' });
    }

    const baselineBuf = await baselineRes.buffer();
    const currentBuf = await currentRes.buffer();

    // 解析 PNG
    const imgA = PNG.sync.read(baselineBuf);
    const imgB = PNG.sync.read(currentBuf);

    // 统一尺寸（取最大宽高，不足的用白色填充）
    const width = Math.max(imgA.width, imgB.width);
    const height = Math.max(imgA.height, imgB.height);

    const diff = new PNG({ width, height });
    const numDiffPixels = (await loadPixelmatch())(imgA.data, imgB.data, diff.data, width, height, { threshold });
    const totalPixels = width * height;
    const diffPercent = parseFloat((numDiffPixels / totalPixels * 100).toFixed(2));

    // 保存差异图
    const diffFileName = `diff_${Date.now()}.png`;
    const diffPath = path.join(SCREENSHOT_DIR, diffFileName);
    fs.writeFileSync(diffPath, PNG.sync.write(diff));
    const diffUrl = `http://localhost:${PORT}/screenshots/${diffFileName}`;

    res.json({
      match: diffPercent === 0,
      diff_percent: diffPercent,
      diff_pixels: numDiffPixels,
      total_pixels: totalPixels,
      diff_url: diffUrl,
      baseline_url: baseline,
      current_url: current,
    });
  } catch (e) {
    res.status(500).json({ error: `截图对比失败: ${e.message}` });
  }
});

/**
 * POST /baseline/save
 * 将指定截图保存为基线（按用例ID归档）
 * body: { case_id: 123, screenshot_url: "http://localhost:8001/screenshots/xxx.png" }
 */
app.post('/baseline/save', async (req, res) => {
  const { case_id, screenshot_url, screenshot_base64 } = req.body;
  if (!case_id || (!screenshot_url && !screenshot_base64)) {
    return res.status(400).json({ error: '需要提供 case_id 和 screenshot_url 或 screenshot_base64' });
  }

  try {
    const caseDir = path.join(BASELINE_DIR, String(case_id));
    if (!fs.existsSync(caseDir)) {
      fs.mkdirSync(caseDir, { recursive: true });
    }
    const fileName = `baseline_${Date.now()}.png`;
    const filePath = path.join(caseDir, fileName);

    if (screenshot_base64) {
      // 直接接收 base64 数据（格式: data:image/png;base64,xxxx 或纯 base64）
      const base64Data = screenshot_base64.includes(',')
        ? screenshot_base64.split(',')[1]
        : screenshot_base64;
      const buf = Buffer.from(base64Data, 'base64');
      fs.writeFileSync(filePath, buf);
    } else if (screenshot_url.startsWith('data:')) {
      // screenshot_url 是 data URL
      const base64Data = screenshot_url.split(',')[1];
      const buf = Buffer.from(base64Data, 'base64');
      fs.writeFileSync(filePath, buf);
    } else {
      // HTTP URL：fetch 下载
      const fetch = require('node-fetch');
      const imgRes = await fetch(screenshot_url);
      if (!imgRes.ok) {
        return res.status(400).json({ error: '无法获取截图文件' });
      }
      const buf = await imgRes.buffer();
      fs.writeFileSync(filePath, buf);
    }

    res.json({
      message: '基线已保存',
      case_id,
      baseline_url: `http://localhost:${PORT}/baselines/${case_id}/${fileName}`,
      saved_at: new Date().toISOString(),
    });
  } catch (e) {
    res.status(500).json({ error: `基线保存失败: ${e.message}` });
  }
});

/**
 * GET /baseline/list?case_id=123
 * 查询某用例的基线列表
 */
app.get('/baseline/list', (req, res) => {
  const caseId = req.query.case_id;
  if (!caseId) {
    return res.status(400).json({ error: '需要提供 case_id' });
  }
  const caseDir = path.join(BASELINE_DIR, String(caseId));
  if (!fs.existsSync(caseDir)) {
    return res.json({ case_id: caseId, baselines: [] });
  }
  const files = fs.readdirSync(caseDir)
    .filter(f => f.endsWith('.png'))
    .map(f => ({
      filename: f,
      url: `http://localhost:${PORT}/baselines/${caseId}/${f}`,
      size: fs.statSync(path.join(caseDir, f)).size,
      saved_at: fs.statSync(path.join(caseDir, f)).mtime,
    }))
    .sort((a, b) => new Date(b.saved_at) - new Date(a.saved_at));

  res.json({ case_id: caseId, baselines: files });
});

// ============ 执行引擎 ============

async function executeTask(taskId) {
  const task = tasks.get(taskId);
  if (!task) return;

  // 取消检查
  if (cancelledTasks.has(taskId)) {
    task.status = 'failed';
    task.error = '任务已被取消';
    task.completed_at = new Date().toISOString();
    cancelledTasks.delete(taskId);
    releaseSlot();
    return;
  }

  task.status = 'running';
  task.started_at = new Date().toISOString();
  task.logs.push({ time: new Date().toISOString(), level: 'info', message: '开始执行任务' });
  task.logs.push({ time: new Date().toISOString(), level: 'info', message: `callback_url=${task.callback_url || '空'}, execution_id=${task.execution_id || '空'}` });

  let browser = null;
  let browserPid = null;

  try {
    // ---- 1. 构造 modelConfig（注入 Agent 构造函数，不再依赖环境变量）----
    const mc = task.model_config || {};
    const modelConfig = {};
    // 支持三级意图模型
    if (mc.default) modelConfig.default = mc.default;
    else if (mc.api_key || mc.model_name) {
      // 向后兼容：旧格式 { api_key, model_name, base_url } → default
      modelConfig.default = {};
      if (mc.api_key) modelConfig.default.apiKey = mc.api_key;
      if (mc.model_name) modelConfig.default.modelName = mc.model_name;
      if (mc.base_url) modelConfig.default.baseURL = mc.base_url;
    }
    if (mc.insight) modelConfig.insight = mc.insight;
    if (mc.planning) modelConfig.planning = mc.planning;

    // 设置每个任务独立的 MIDSCENE_RUN_DIR，避免并发竞态
    const taskRunDir = path.join(MIDSCENE_RUN_DIR, taskId);
    const taskReportDir = path.join(taskRunDir, 'report');
    if (!fs.existsSync(taskReportDir)) {
      fs.mkdirSync(taskReportDir, { recursive: true });
    }
    const prevRunDir = process.env.MIDSCENE_RUN_DIR;
    process.env.MIDSCENE_RUN_DIR = taskRunDir;

    // ---- 2. 根据device_type选择Agent工厂 ----
    let page = null;
    let agent = null;
    const resolvedDeviceType = task.device_type || 'web';

    if (resolvedDeviceType === 'android') {
      // ===== Android端 =====
      const appCfg = task.app_config || {};
      const androidCfg = task.android_config || {};
      const appNameMapping = task.app_name_mapping || {};
      task.logs.push({ time: new Date().toISOString(), level: 'info', message: `Android模式: device=${appCfg.device_id || '自动检测'}, pkg=${appCfg.package_name || '未指定'}, activity=${appCfg.app_activity || '未指定'}` });

      const { AndroidAgent, AndroidDevice, getConnectedDevices } = getAndroidModules();

      let deviceId = appCfg.device_id;
      if (!deviceId) {
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: '未指定device_id，自动检测已连接设备...' });
        const devices = await getConnectedDevices();
        if (!devices.length) throw new Error('未检测到已连接的Android设备');
        deviceId = devices[0].udid;
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `自动选择设备: ${deviceId}` });
      }

      // 传递 android_config 给 AndroidDevice（如 adbPath 等）
      const androidDeviceOpts = {};
      if (androidCfg.androidAdbPath) androidDeviceOpts.adbPath = androidCfg.androidAdbPath;
      const androidPage = new AndroidDevice(deviceId, Object.keys(androidDeviceOpts).length ? androidDeviceOpts : undefined);
      await androidPage.connect();
      task.androidDevice = androidPage; // 保存引用，用于 finally disconnect

      // APP启动方式：使用包名启动（AndroidDevice.launch 接受包名字符串）
      const packageName = appCfg.package_name;
      if (packageName) {
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `APP包名启动: ${packageName}` });
        await androidPage.launch(packageName);
        await new Promise(r => setTimeout(r, 3000));
      } else if (task.url) {
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `APP导航到: ${task.url}（未配置包名，使用URL方式）` });
        await androidPage.launch(task.url);
        await new Promise(r => setTimeout(r, 3000));
      }

      // 构造 AndroidAgent 的 modelConfig + app_name_mapping
      const agentOpts = {
        modelConfig: Object.keys(modelConfig).length ? modelConfig : undefined,
        aiActContext: 'If any location, permission, user agreement, etc. popup, click agree. If login page pops up, close it.',
      };
      // 传递 app_name_mapping（应用名称→包名映射）
      if (Object.keys(appNameMapping).length) {
        agentOpts.appNameMapping = appNameMapping;
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `app_name_mapping: ${JSON.stringify(appNameMapping)}` });
      }
      agent = new AndroidAgent(androidPage, agentOpts);
      task.logs.push({ time: new Date().toISOString(), level: 'info', message: 'AndroidAgent 已初始化 (modelConfig注入' + (Object.keys(appNameMapping).length ? ', appNameMapping注入' : '') + ')' });

    } else if (resolvedDeviceType === 'ios') {
      // ===== iOS端（预留占位，友好提示） =====
      // @midscene/ios 尚未安装，给出明确指引
      throw new Error('iOS端暂未实现。请安装 @midscene/ios 后重试，或使用 Web / Android 模式执行。参考: npm install @midscene/ios');

    } else if (resolvedDeviceType === 'harmony') {
      // ===== HarmonyOS端（预留占位，友好提示） =====
      // @midscene/harmony 尚未安装，给出明确指引
      throw new Error('HarmonyOS端暂未实现。请安装 @midscene/harmony 后重试，或使用 Web / Android 模式执行。参考: npm install @midscene/harmony');

    } else {
      // ===== Web端：启动浏览器 =====
      const webCfg = task.web_config || {};
      const execCfg = task.execution_config || {};
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
      if (!task.headless) {
        const winWidth = task.viewport.width || 1280;
        const winHeight = task.viewport.height || 768;
        launchArgs.push(`--window-size=${winWidth},${winHeight}`);
        launchArgs.push('--window-position=0,0');
        launchArgs.push('--disable-gpu');
        launchArgs.push('--disable-software-rasterizer');
        launchArgs.push('--disable-dev-shm-usage');
        launchArgs.push('--disable-features=TranslateUI,WindowsDwmComposition');
        launchArgs.push('--disable-frame-rate-limit');
        launchArgs.push('--run-all-compositor-stages-before-draw');
        launchArgs.push('--disable-smooth-scrolling');
      }

      const launchOpts = {
        headless: task.headless,
        args: launchArgs,
      };
      // 如果配置了浏览器路径
      if (webCfg.browserPath) launchOpts.executablePath = webCfg.browserPath;

      browser = await chromium.launch(launchOpts);
      // 启动后立刻记录浏览器主进程PID，有头模式下 browser.process() 后续可能返回null
      browserPid = browser.process()?.pid || null;
      if (browserPid) {
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `浏览器已启动，PID=${browserPid}` });
      }

      const contextOptions = {};
      if (task.user_agent) contextOptions.userAgent = task.user_agent;
      if (task.device_scale_factor) contextOptions.deviceScaleFactor = task.device_scale_factor;
      if (task.cookie_file) contextOptions.storageState = task.cookie_file;
      if (!task.headless) contextOptions.noViewport = true;

      const context = await browser.newContext(contextOptions);
      page = await context.newPage();
      if (task.headless) await page.setViewportSize(task.viewport);

      // 有头模式防闪烁
      if (!task.headless) {
        await page.addStyleTag({
          content: `*, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; scroll-behavior: auto !important; }`
        });
        const cdpClient = await context.newCDPSession(page);
        const originalScreenshot = page.screenshot.bind(page);
        page.screenshot = async function (opts = {}) {
          try {
            const { data } = await cdpClient.send('Page.captureScreenshot', { format: opts.type || 'jpeg', quality: opts.type === 'png' ? undefined : (opts.quality || 90) });
            return Buffer.from(data, 'base64');
          } catch (e) { return originalScreenshot(opts); }
        };
        page._releaseCdpScreenshot = () => { page.screenshot = originalScreenshot; };
      }

      if (task.url) {
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `导航到: ${task.url}` });
        const gotoOptions = { waitUntil: 'domcontentloaded', timeout: 30000 };
        if (task.wait_for_network_idle && task.wait_for_network_idle.timeout) {
          gotoOptions.waitUntil = 'networkidle';
          gotoOptions.timeout = task.wait_for_network_idle.timeout;
        }
        await page.goto(task.url, gotoOptions);
        await page.waitForTimeout(2000);
      }

      // Web端创建 PlaywrightAgent，注入 modelConfig
      const agentOpts = { forceChromeSelectRendering: false };
      if (Object.keys(modelConfig).length) agentOpts.modelConfig = modelConfig;
      agent = new PlaywrightAgent(page, agentOpts);
      task.logs.push({ time: new Date().toISOString(), level: 'info', message: `PlaywrightAgent 已初始化 (modelConfig${Object.keys(modelConfig).length ? '已注入' : '使用环境变量'})` });
    }

    // ---- 4. 逐步执行（AI/传统分派） ----
    const stepResults = [];
    const STEP_TIMEOUT = 60000;
    const waitAfterAction = (task.execution_config && task.execution_config.waitAfterAction) || 1000;
    
    function withTimeout(promise, ms, label) {
      return Promise.race([
        promise,
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error(`${label} 超时（${ms/1000}秒）`)), ms)
        )
      ]);
    }

    // 步骤级重试辅助：执行异步操作，失败时按 retry_count 自动重试
    async function withRetry(fn, retryCount, label) {
      let lastError = null;
      const maxAttempts = (retryCount || 0) + 1;
      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
          const result = await fn();
          if (attempt > 1) {
            task.logs.push({ time: new Date().toISOString(), level: 'info', message: `${label} 第${attempt}次尝试成功` });
          }
          return result;
        } catch (err) {
          lastError = err;
          if (attempt < maxAttempts) {
            task.logs.push({ time: new Date().toISOString(), level: 'warn', message: `${label} 第${attempt}次失败(${err.message})，${2}秒后重试(${attempt}/${retryCount})` });
            await new Promise(r => setTimeout(r, 2000));
          }
        }
      }
      throw lastError;
    }
    
    // 失败截图捕获辅助：截图保存到 SCREENSHOT_DIR，返回可访问的 URL
    async function captureFailureScreenshot(stepIndex, pageOrDevice) {
      try {
        const screenshotFileName = `${taskId}_step${stepIndex + 1}_fail_${Date.now()}.png`;
        const screenshotPath = path.join(SCREENSHOT_DIR, screenshotFileName);
        if (pageOrDevice && typeof pageOrDevice.screenshot === 'function') {
          const buf = await pageOrDevice.screenshot({ type: 'png', timeout: 5000 });
          fs.writeFileSync(screenshotPath, buf);
          task.logs.push({ time: new Date().toISOString(), level: 'info', message: `失败截图已保存: ${screenshotFileName}` });
          return `http://localhost:${PORT}/screenshots/${screenshotFileName}`;
        }
      } catch (e) {
        task.logs.push({ time: new Date().toISOString(), level: 'warn', message: `失败截图捕获异常: ${e.message}` });
      }
      return null;
    }

    for (let i = 0; i < task.steps.length; i++) {
      // 取消检查
      if (cancelledTasks.has(taskId)) {
        task.logs.push({ time: new Date().toISOString(), level: 'warn', message: `任务已取消，中止执行（步骤${i + 1}前）` });
        break;
      }

      const step = task.steps[i];
      const stepMode = step.mode || 'ai';  // 默认AI模式（向后兼容）
      let instruction = step.instruction || '';
      const input_value = step.input_value || '';
      const retryCount = step.retry_count || 0;
      
      if (stepMode === 'traditional') {
        // ===== 传统模式：使用 Playwright 原生 API =====
        const stepLog = `步骤${i + 1} [传统/${step.action_type || 'click'}]: ${step.locator_value || instruction}`;
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: stepLog });

        try {
          const stepResult = await withRetry(async () => {
            const locator = step.locator_value;
            const actionType = step.action_type || 'click';

            if (!page) {
              throw new Error('传统模式仅支持 Web 端（需要 Playwright page 对象）');
            }

            let result;
            switch (actionType) {
              case 'click':
                await withTimeout(page.locator(locator).click(), STEP_TIMEOUT, `步骤${i+1} click`);
                result = { status: 'passed', message: '点击完成' };
                break;
              case 'input':
                await withTimeout(page.locator(locator).fill(input_value), STEP_TIMEOUT, `步骤${i+1} input`);
                result = { status: 'passed', message: '输入完成', input_value };
                break;
              case 'select':
                await withTimeout(page.locator(locator).selectOption(input_value), STEP_TIMEOUT, `步骤${i+1} select`);
                result = { status: 'passed', message: '选择完成', input_value };
                break;
              case 'hover':
                await withTimeout(page.locator(locator).hover(), STEP_TIMEOUT, `步骤${i+1} hover`);
                result = { status: 'passed', message: '悬停完成' };
                break;
              case 'wait':
                await page.waitForSelector(locator, { timeout: STEP_TIMEOUT });
                result = { status: 'passed', message: '元素出现' };
                break;
              case 'scroll':
                await page.locator(locator).scrollIntoViewIfNeeded();
                result = { status: 'passed', message: '滚动到元素' };
                break;
              default:
                await withTimeout(page.locator(locator).click(), STEP_TIMEOUT, `步骤${i+1} click(default)`);
                result = { status: 'passed', message: `操作完成(${actionType})` };
            }

            // 传统断言
            if (step.type === 'assert' && step.assert_type) {
              const assertType = step.assert_type;
              const assertValue = step.assert_value || '';
              if (assertType === 'exists') {
                const visible = await page.locator(locator).isVisible().catch(() => false);
                if (!visible) throw new Error(`断言失败: 元素不存在或不可见`);
              } else {
                const text = await page.locator(locator).textContent().catch(() => '');
                if (assertType === 'equals' && text !== assertValue) throw new Error(`断言失败: 期望"${assertValue}", 实际"${text}"`);
                if (assertType === 'contains' && !text.includes(assertValue)) throw new Error(`断言失败: 期望包含"${assertValue}", 实际"${text}"`);
                if (assertType === 'not_equals' && text === assertValue) throw new Error(`断言失败: 值不应等于"${assertValue}"`);
              }
              result = { status: 'passed', message: '断言通过' };
            }

            await page.waitForTimeout(waitAfterAction);
            return result;
          }, retryCount, `步骤${i+1}`);

          stepResults.push({
            order: i + 1, type: step.type, mode: 'traditional',
            instruction, locator_value: step.locator_value, action_type: step.action_type || 'click',
            output_var: step.output_var || null,
            retry_count: retryCount,
            ...stepResult,
          });

        } catch (stepErr) {
          // 失败截图（Web端 page 对象可用时）
          const failureScreenshot = await captureFailureScreenshot(i, page);
          stepResults.push({
            order: i + 1, type: step.type, mode: 'traditional',
            instruction, locator_value: step.locator_value,
            output_var: step.output_var || null,
            retry_count: retryCount,
            status: 'failed', message: stepErr.message,
            screenshot: failureScreenshot,
          });
          task.logs.push({ time: new Date().toISOString(), level: 'error', message: `步骤${i + 1} 失败(重试${retryCount}次后): ${stepErr.message}` });
          break;
        }

      } else {
        // ===== AI模式：使用 Midscene Agent =====
        if (input_value) {
          instruction = instruction
            ? `${instruction}，输入值为: ${input_value}`
            : `输入: ${input_value}`;
        }
        const stepLog = `步骤${i + 1} [AI/${step.type}]: ${instruction}`;
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: stepLog });

        try {
          const stepResult = await withRetry(async () => {
            let result;
            switch (step.type) {
              case 'aiAct':
                await withTimeout(agent.aiAct(instruction), STEP_TIMEOUT, `步骤${i+1} aiAct`);
                result = { status: 'passed', message: '操作完成' };
                if (input_value) result.input_value = input_value;
                break;
              case 'aiTap':
                await withTimeout(agent.aiTap(instruction), STEP_TIMEOUT, `步骤${i+1} aiTap`);
                result = { status: 'passed', message: '点击完成' };
                if (input_value) result.input_value = input_value;
                break;
              case 'aiAssert':
                await withTimeout(agent.aiAssert(instruction), STEP_TIMEOUT, `步骤${i+1} aiAssert`);
                result = { status: 'passed', message: '断言通过' };
                if (input_value) result.input_value = input_value;
                break;
              case 'aiQuery':
                const queryResult = await withTimeout(agent.aiQuery(instruction), STEP_TIMEOUT, `步骤${i+1} aiQuery`);
                result = { status: 'passed', message: '查询完成', data: queryResult };
                if (input_value) result.input_value = input_value;
                break;
              case 'aiWaitFor':
                await withTimeout(agent.aiWaitFor(instruction), STEP_TIMEOUT, `步骤${i+1} aiWaitFor`);
                result = { status: 'passed', message: '等待条件满足' };
                break;
              case 'sleep':
                await new Promise(r => setTimeout(r, step.duration || 2000));
                result = { status: 'passed', message: `等待${(step.duration || 2000) / 1000}秒` };
                break;
              default:
                await withTimeout(agent.aiAct(instruction || step.instruction), STEP_TIMEOUT, `步骤${i+1} aiAct`);
                result = { status: 'passed', message: '操作完成（默认aiAct）' };
            }

            // 操作后等待
            if (step.type !== 'sleep') {
              await new Promise(r => setTimeout(r, Math.min(waitAfterAction, 3000)));
            }
            return result;
          }, retryCount, `步骤${i+1}`);

          stepResults.push({
            order: i + 1, type: step.type, mode: 'ai',
            instruction: step.instruction,
            output_var: step.output_var || null,
            retry_count: retryCount,
            ...stepResult,
          });
        } catch (stepErr) {
          // 失败截图（Web端 page 对象可用时）
          const failureScreenshot = await captureFailureScreenshot(i, page);
          stepResults.push({
            order: i + 1, type: step.type, mode: 'ai',
            instruction: step.instruction,
            output_var: step.output_var || null,
            retry_count: retryCount,
            status: 'failed', message: stepErr.message,
            screenshot: failureScreenshot,
          });
          task.logs.push({ time: new Date().toISOString(), level: 'error', message: `步骤${i + 1} 失败(重试${retryCount}次后): ${stepErr.message}` });
          break;
        }
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
    const finallyStart = Date.now();

    // ---- 彻底解耦流程：立即关浏览器 → 回调Django → 异步生成报告 ----

    // 1. 恢复原始截图方法（确保后续不走CDP）
    if (page && typeof page._releaseCdpScreenshot === 'function') {
      page._releaseCdpScreenshot();
    }

    // 2. 立即关闭浏览器（步骤执行完第一时间关，不等任何报告生成）
    //    策略：先尝试优雅关闭（3秒），超时则直接taskkill强杀
    const killBrowser = async () => {
      const { execSync } = require('child_process');
      // 优先用启动时记录的PID（最可靠），其次用 browser.process()
      const pid = browserPid || browser?.process?.()?.pid;
      if (pid) {
        try {
          execSync(`taskkill /f /pid ${pid} /t 2>nul`, { timeout: 3000 });
          task.logs.push({ time: new Date().toISOString(), level: 'info', message: `taskkill /f /pid ${pid} /t 强杀浏览器进程` });
          return;
        } catch (e) {
          task.logs.push({ time: new Date().toISOString(), level: 'warn', message: `taskkill pid=${pid} 失败: ${e.message}` });
        }
      }
      // 最后兜底：按名称杀chrome/chromium进程（仅限测试场景，不影响用户日常浏览器）
      try {
        execSync(`wmic process where "CommandLine like '%--test-type%' and Name='chrome.exe'" call terminate 2>nul`, { timeout: 3000 });
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: 'wmic 兜底终止测试chrome进程' });
      } catch (_) {}
    };

    if (browser) {
      console.time('browser-close');
      task.logs.push({ time: new Date().toISOString(), level: 'info', message: '步骤执行完毕，立即关闭浏览器...' });
      try {
        await Promise.race([
          browser.close(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 3000))
        ]);
        console.timeEnd('browser-close');
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `browser.close() 正常完成（耗时 ${Date.now() - finallyStart}ms）` });
      } catch (e) {
        console.timeEnd('browser-close');
        task.logs.push({ time: new Date().toISOString(), level: 'warn', message: `browser.close() 超时(${e.message})，强杀进程` });
        await killBrowser();
      }
    }
    task.browser_closed = true;
    task.logs.push({ time: new Date().toISOString(), level: 'info', message: `浏览器已关闭（finally耗时 ${Date.now() - finallyStart}ms）` });

    // 3. Android设备断开（3秒超时）
    try {
      if (task.androidDevice && typeof task.androidDevice.destroy === 'function') {
        await Promise.race([
          task.androidDevice.destroy(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 3000))
        ]);
        task.logs.push({ time: new Date().toISOString(), level: 'info', message: 'Android设备已释放' });
      }
    } catch (_) {
      task.logs.push({ time: new Date().toISOString(), level: 'warn', message: 'Android设备释放超时' });
    }

    // 4. 立即回调Django（不等报告生成，步骤结果已确定）
    //    报告路径先置null，后续异步生成完成后可通过单独接口获取
    if (task.callback_url) {
      try {
        const callbackBody = JSON.stringify({
          task_id: task.task_id,
          execution_id: task.execution_id,
          status: task.status,
          result: task.result,
          error: task.error,
          completed_at: task.completed_at,
          report_url: null,      // 报告异步生成，先回null
          report_file: null,
        });

        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `回调Django（报告异步生成中）: ${task.callback_url}` });

        const fetch = require('node-fetch');
        const cbRes = await fetch(task.callback_url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: callbackBody,
        });

        task.logs.push({ time: new Date().toISOString(), level: 'info', message: `回调响应: HTTP ${cbRes.status}（finally耗时 ${Date.now() - finallyStart}ms）` });
      } catch (e) {
        task.logs.push({ time: new Date().toISOString(), level: 'warn', message: `回调失败: ${e.message}` });
      }
    }

    // 5. 异步生成报告（不阻塞主流程，浏览器已关闭，用户无需等待）
    setImmediate(async () => {
      const reportStart = Date.now();
      try {
        if (agent) {
          await Promise.race([
            agent.destroy(),
            new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 15000))
          ]);
          if (agent.reportFile) task.report_file = agent.reportFile;
        }
      } catch (_) {
        task.logs.push({ time: new Date().toISOString(), level: 'warn', message: 'agent.destroy() 异步超时，扫描报告目录' });
      }

      // 扫描报告文件
      if (!task.report_file) {
        try {
          const taskReportDir = path.join(taskRunDir, 'report');
          if (fs.existsSync(taskReportDir)) {
            const reportFiles = fs.readdirSync(taskReportDir).filter(f => f.endsWith('.html')).sort().reverse();
            if (reportFiles.length > 0) {
              const startedAt = task.started_at ? new Date(task.started_at) : new Date(Date.now() - 300000);
              for (const fname of reportFiles) {
                const fpath = path.join(taskReportDir, fname);
                const stat = fs.statSync(fpath);
                if (stat.mtime >= startedAt) {
                  task.report_file = fpath;
                  break;
                }
              }
            }
          }
          if (!task.report_file) {
            const globalReportFiles = fs.readdirSync(REPORT_DIR).filter(f => f.endsWith('.html')).sort().reverse();
            const startedAt = task.started_at ? new Date(task.started_at) : new Date(Date.now() - 300000);
            for (const fname of globalReportFiles) {
              const fpath = path.join(REPORT_DIR, fname);
              const stat = fs.statSync(fpath);
              if (stat.mtime >= startedAt) {
                task.report_file = fpath;
                break;
              }
            }
          }
        } catch (_) {}
      }

      if (task.report_file) {
        console.log(`[异步] 报告生成完成: ${task.report_file}（耗时 ${Date.now() - reportStart}ms）`);
      } else {
        console.log(`[异步] 未找到报告文件（耗时 ${Date.now() - reportStart}ms）`);
      }
    });

    // 清理取消标记
    cancelledTasks.delete(taskId);
    // 释放并发槽位
    releaseSlot();
    task.logs.push({ time: new Date().toISOString(), level: 'info', message: `executeTask finally 完成（总耗时 ${Date.now() - finallyStart}ms）` });
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
  const { cases = [], plan_id, callback_base, execution_mode = 'per_case', login_config = null } = req.body;

  if (!cases.length) {
    return res.status(400).json({ error: 'cases 不能为空' });
  }

  const batchId = randomUUID();
  const batchTask = {
    batch_id: batchId,
    plan_id,
    execution_mode,
    login_config,
    status: 'running',
    total: cases.length,
    completed: 0,
    results: [],
    created_at: new Date().toISOString(),
  };

  batches.set(batchId, batchTask);

  // 后台顺序执行
  executeBatch(batchId, cases, execution_mode, login_config);

  res.json({ batch_id: batchId, status: 'pending', total: cases.length, execution_mode, message: '批量任务已提交' });
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
 * 
 * 独立模式（per_case）: 每条用例独立浏览器，互不影响
 * 共享会话模式（shared_session）: 共用一个浏览器+Agent，变量池共享，login_config优先
 */
async function executeBatch(batchId, cases, executionMode = 'per_case', loginConfig = null) {
  const batch = batches.get(batchId);
  if (!batch) return;

  if (executionMode === 'shared_session') {
    // ===== 共享会话模式 =====
    await executeBatchSharedSession(batchId, cases, loginConfig);
  } else {
    // ===== 独立模式：并发执行（受并发控制信号量约束）=====
    // 初始化所有 result 条目
    for (let i = 0; i < cases.length; i++) {
      const caseItem = cases[i];
      batch.results.push({ execution_id: caseItem.execution_id, case_id: caseItem.case_id, status: 'pending', error: null });
    }

    // 并发启动所有用例，每个通过 acquireSlot 获取执行槽位
    const promises = cases.map((caseItem, i) => (async () => {
      const payload = caseItem.payload;
      const resultIdx = i;
      batch.results[resultIdx].status = 'running';

      await acquireSlot();
      try {
        const taskId = randomUUID();
        const task = {
          task_id: taskId,
          platform: payload.platform || 'web',
          device_type: payload.device_type || (payload.platform === 'app' ? 'android' : 'web'),
          url: payload.url,
          steps: payload.steps || [],
          headless: payload.headless || false,
          viewport: payload.viewport || { width: 1280, height: 768 },
          model_config: payload.model_config || {},
          callback_url: payload.callback_url,
          execution_id: caseItem.execution_id,
          user_agent: payload.user_agent || null,
          device_scale_factor: payload.device_scale_factor || null,
          cookie_file: payload.cookie_file || null,
          wait_for_network_idle: payload.wait_for_network_idle || null,
          app_config: payload.app_config || null,
          execution_config: payload.execution_config || {},
          report_config: payload.report_config || {},
          web_config: payload.web_config || {},
          android_config: payload.android_config || {},
          ios_config: payload.ios_config || {},
          harmony_config: payload.harmony_config || {},
          app_name_mapping: payload.app_name_mapping || {},
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
      batch.completed = batch.results.filter(r => r.status !== 'pending' && r.status !== 'running').length;
    })());

    await Promise.allSettled(promises);
  }

  batch.status = 'completed';
}

/**
 * 共享会话模式执行
 * 
 * 流程：
 *   1. 启动一个浏览器 + 创建一个 PlaywrightAgent
 *   2. 如果有 login_config，先执行登录步骤
 *   3. 逐条执行用例，跳过用例中的登录步骤，共享变量池
 *   4. 每条用例执行完后立即回调Django
 *   5. 全部完成后关闭浏览器
 */
async function executeBatchSharedSession(batchId, cases, loginConfig) {
  const batch = batches.get(batchId);
  if (!batch) return;

  // 从第一条用例提取公共配置
  const firstPayload = cases[0]?.payload || {};
  const execCfg = firstPayload.execution_config || {};
  const mc = firstPayload.model_config || {};
  const waitAfterAction = execCfg.waitAfterAction || 1000;
  const STEP_TIMEOUT = 60000;

  // 判断设备类型（共享会话模式下所有用例必须同设备类型）
  const sharedDeviceType = firstPayload.device_type || (firstPayload.platform === 'app' ? 'android' : 'web');

  function withTimeout(promise, ms, label) {
    return Promise.race([
      promise,
      new Promise((_, reject) => setTimeout(() => reject(new Error(`${label} 超时（${ms/1000}秒）`)), ms))
    ]);
  }

  // 步骤级重试辅助（共享会话模式）
  async function withRetry(fn, retryCount, label) {
    let lastError = null;
    const maxAttempts = (retryCount || 0) + 1;
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const result = await fn();
        if (attempt > 1) {
          console.log(`[SharedSession] ${label} 第${attempt}次尝试成功`);
        }
        return result;
      } catch (err) {
        lastError = err;
        if (attempt < maxAttempts) {
          console.log(`[SharedSession] ${label} 第${attempt}次失败(${err.message})，2秒后重试(${attempt}/${retryCount})`);
          await new Promise(r => setTimeout(r, 2000));
        }
      }
    }
    throw lastError;
  }

  // 失败截图捕获辅助（共享会话模式）
  async function captureFailureScreenshot(batchTaskId, stepIndex, pageOrDevice) {
    try {
      const screenshotFileName = `batch-${batchTaskId}_step${stepIndex + 1}_fail_${Date.now()}.png`;
      const screenshotPath = path.join(SCREENSHOT_DIR, screenshotFileName);
      if (pageOrDevice && typeof pageOrDevice.screenshot === 'function') {
        const buf = await pageOrDevice.screenshot({ type: 'png', timeout: 5000 });
        fs.writeFileSync(screenshotPath, buf);
        return `http://localhost:${PORT}/screenshots/${screenshotFileName}`;
      }
    } catch (_) {}
    return null;
  }

  let browser = null;
  let page = null;
  let agent = null;
  let androidDevice = null;
  let browserPid = null;
  const sharedVariables = {}; // 共享变量池

  try {
    // ---- 1. 构造 modelConfig ----
    const modelConfig = {};
    if (mc.default) modelConfig.default = mc.default;
    else if (mc.api_key || mc.model_name) {
      modelConfig.default = {};
      if (mc.api_key) modelConfig.default.apiKey = mc.api_key;
      if (mc.model_name) modelConfig.default.modelName = mc.model_name;
      if (mc.base_url) modelConfig.default.baseURL = mc.base_url;
    }
    if (mc.insight) modelConfig.insight = mc.insight;
    if (mc.planning) modelConfig.planning = mc.planning;

    const prevRunDir = process.env.MIDSCENE_RUN_DIR;
    process.env.MIDSCENE_RUN_DIR = MIDSCENE_RUN_DIR;

    if (sharedDeviceType === 'android') {
      // ===== Android端共享会话 =====
      const appCfg = firstPayload.app_config || {};
      const androidCfg = firstPayload.android_config || {};
      const appNameMapping = firstPayload.app_name_mapping || {};
      batch.logs && console.log(`[SharedSession-Android] 启动共享Android会话`);

      const { AndroidAgent, AndroidDevice, getConnectedDevices } = getAndroidModules();
      let deviceId = appCfg.device_id;
      if (!deviceId) {
        const devices = await getConnectedDevices();
        if (!devices.length) throw new Error('未检测到已连接的Android设备');
        deviceId = devices[0].udid;
      }

      const androidDeviceOpts = {};
      if (androidCfg.androidAdbPath) androidDeviceOpts.adbPath = androidCfg.androidAdbPath;
      androidDevice = new AndroidDevice(deviceId, Object.keys(androidDeviceOpts).length ? androidDeviceOpts : undefined);
      await androidDevice.connect();

      // 包名启动
      const packageName = appCfg.package_name;
      const appActivity = appCfg.app_activity;
      if (packageName) {
        await androidDevice.launch(packageName);
        await new Promise(r => setTimeout(r, 3000));
      } else if (firstPayload.url) {
        await androidDevice.launch(firstPayload.url);
        await new Promise(r => setTimeout(r, 3000));
      }

      // 创建 AndroidAgent
      const agentOpts = {
        modelConfig: Object.keys(modelConfig).length ? modelConfig : undefined,
        aiActContext: 'If any location, permission, user agreement, etc. popup, click agree. If login page pops up, close it.',
      };
      if (Object.keys(appNameMapping).length) agentOpts.appNameMapping = appNameMapping;
      agent = new AndroidAgent(androidDevice, agentOpts);

    } else if (sharedDeviceType === 'ios') {
      throw new Error('iOS端共享会话模式暂未实现，请使用独立模式或 Web/Android 模式');
    } else if (sharedDeviceType === 'harmony') {
      throw new Error('HarmonyOS端共享会话模式暂未实现，请使用独立模式或 Web/Android 模式');
    } else {
      // ===== Web端共享会话（原有逻辑） =====
      const webCfg = firstPayload.web_config || {};
      const headless = firstPayload.headless || false;
      const viewport = firstPayload.viewport || { width: 1280, height: 768 };

      batch.logs && console.log(`[SharedSession-Web] 启动共享浏览器 headless=${headless}`);

      const launchArgs = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-blink-features=AutomationControlled',
        '--disable-infobars',
        '--disable-background-timer-throttling',
        '--disable-renderer-backgrounding',
        '--no-first-run',
      ];
      if (!headless) {
        launchArgs.push(`--window-size=${viewport.width},${viewport.height}`);
        launchArgs.push('--window-position=0,0');
        launchArgs.push('--disable-gpu', '--disable-software-rasterizer', '--disable-dev-shm-usage');
        launchArgs.push('--disable-features=TranslateUI,WindowsDwmComposition');
        launchArgs.push('--disable-frame-rate-limit', '--run-all-compositor-stages-before-draw', '--disable-smooth-scrolling');
      }

      const launchOpts = { headless, args: launchArgs };
      if (webCfg.browserPath) launchOpts.executablePath = webCfg.browserPath;

      browser = await chromium.launch(launchOpts);
      browserPid = browser.process()?.pid || null;

      const contextOpts = {};
      if (firstPayload.user_agent) contextOpts.userAgent = firstPayload.user_agent;
      if (firstPayload.device_scale_factor) contextOpts.deviceScaleFactor = firstPayload.device_scale_factor;
      if (firstPayload.cookie_file) contextOpts.storageState = firstPayload.cookie_file;
      if (!headless) contextOpts.noViewport = true;

      const context = await browser.newContext(contextOpts);
      page = await context.newPage();
      if (headless) await page.setViewportSize(viewport);

      // 有头模式防闪烁
      if (!headless) {
        await page.addStyleTag({
          content: `*, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; scroll-behavior: auto !important; }`
        });
        const cdpClient = await context.newCDPSession(page);
        const originalScreenshot = page.screenshot.bind(page);
        page.screenshot = async function (opts = {}) {
          try {
            const { data } = await cdpClient.send('Page.captureScreenshot', { format: opts.type || 'jpeg', quality: opts.type === 'png' ? undefined : (opts.quality || 90) });
            return Buffer.from(data, 'base64');
          } catch (e) { return originalScreenshot(opts); }
        };
        page._releaseCdpScreenshot = () => { page.screenshot = originalScreenshot; };
      }

      // 导航到第一个URL
      const firstUrl = firstPayload.url;
      if (firstUrl) {
        const gotoOptions = { waitUntil: 'domcontentloaded', timeout: 30000 };
        if (firstPayload.wait_for_network_idle && firstPayload.wait_for_network_idle.timeout) {
          gotoOptions.waitUntil = 'networkidle';
          gotoOptions.timeout = firstPayload.wait_for_network_idle.timeout;
        }
        await page.goto(firstUrl, gotoOptions);
        await page.waitForTimeout(2000);
      }

      // 创建 PlaywrightAgent
      const agentOpts = { forceChromeSelectRendering: false };
      if (Object.keys(modelConfig).length) agentOpts.modelConfig = modelConfig;
      agent = new PlaywrightAgent(page, agentOpts);
    }

    // ---- 执行 login_config（共享会话模式下仅登录一次）----
    if (loginConfig && loginConfig.steps && loginConfig.steps.length) {
      // Web端导航到登录URL
      if (sharedDeviceType === 'web' && page && loginConfig.url) {
        await page.goto(loginConfig.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
      }
      for (const step of loginConfig.steps) {
        const loginInstruction = step.instruction || '';
        if (!loginInstruction) continue;
        try {
          await withTimeout(agent.aiAct(loginInstruction), STEP_TIMEOUT, 'login_step');
          await new Promise(r => setTimeout(r, Math.min(waitAfterAction, 3000)));
        } catch (loginErr) {
          console.error(`[SharedSession] 登录步骤失败: ${loginErr.message}`);
          throw new Error(`登录步骤失败: ${loginErr.message}`);
        }
      }
      console.log(`[SharedSession] 登录完成，开始执行用例`);
    }

    // ---- 逐条执行用例（共享Agent+变量池）----
    for (let i = 0; i < cases.length; i++) {
      const caseItem = cases[i];
      const payload = caseItem.payload;
      const executionId = caseItem.execution_id;
      const caseId = caseItem.case_id;

      batch.results.push({ execution_id: executionId, case_id: caseId, status: 'running', error: null });
      const resultIdx = batch.results.length - 1;

      try {
        // Web端：如果用例URL不同于当前页面，导航到用例URL
        if (sharedDeviceType === 'web' && page && payload.url && payload.url !== page.url()) {
          await page.goto(payload.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
          await page.waitForTimeout(1000);
        }

        // 过滤步骤：跳过登录步骤（共享会话模式下已统一登录）
        const steps = (payload.steps || []).filter(step => {
          if (step.is_login_step) return false;
          if (loginConfig && loginConfig.steps && loginConfig.steps.length) {
            const loginInstructions = loginConfig.steps.map(s => (s.instruction || '').trim()).filter(Boolean);
            if (loginInstructions.includes((step.instruction || '').trim())) return false;
          }
          return true;
        });

        // 执行步骤
        const stepResults = [];
        for (let j = 0; j < steps.length; j++) {
          const step = steps[j];
          const stepMode = step.mode || 'ai';
          let instruction = step.instruction || '';
          const input_value = step.input_value || '';
          const retryCount = step.retry_count || 0;

          if (stepMode === 'traditional') {
            // ===== 传统模式 =====
            // APP端不支持传统模式，跳过并标记警告
            if (sharedDeviceType !== 'web' || !page) {
              stepResults.push({
                order: j + 1, type: step.type, mode: 'traditional',
                instruction, locator_value: step.locator_value,
                output_var: step.output_var || null,
                retry_count: retryCount,
                status: 'skipped', message: 'APP端不支持传统模式步骤，已跳过',
              });
              continue;
            }
            // Web端传统步骤（withRetry包装）
            try {
              const stepResult = await withRetry(async () => {
                const locator = step.locator_value;
                const actionType = step.action_type || 'click';
                switch (actionType) {
                  case 'click': await withTimeout(page.locator(locator).click(), STEP_TIMEOUT, `步骤${j+1}`); break;
                  case 'input': await withTimeout(page.locator(locator).fill(input_value), STEP_TIMEOUT, `步骤${j+1}`); break;
                  case 'select': await withTimeout(page.locator(locator).selectOption(input_value), STEP_TIMEOUT, `步骤${j+1}`); break;
                  case 'hover': await withTimeout(page.locator(locator).hover(), STEP_TIMEOUT, `步骤${j+1}`); break;
                  case 'wait': await page.waitForSelector(locator, { timeout: STEP_TIMEOUT }); break;
                  case 'scroll': await page.locator(locator).scrollIntoViewIfNeeded(); break;
                  default: await withTimeout(page.locator(locator).click(), STEP_TIMEOUT, `步骤${j+1}`);
                }
                // 传统断言
                if (step.type === 'assert' && step.assert_type) {
                  const assertType = step.assert_type;
                  const assertValue = step.assert_value || '';
                  if (assertType === 'exists') {
                    const visible = await page.locator(locator).isVisible().catch(() => false);
                    if (!visible) throw new Error(`断言失败: 元素不存在或不可见`);
                  } else {
                    const text = await page.locator(locator).textContent().catch(() => '');
                    if (assertType === 'equals' && text !== assertValue) throw new Error(`断言失败: 期望"${assertValue}", 实际"${text}"`);
                    if (assertType === 'contains' && !text.includes(assertValue)) throw new Error(`断言失败: 期望包含"${assertValue}"`);
                  }
                }
                await page.waitForTimeout(waitAfterAction);
                // 变量提取
                if (step.output_var) {
                  const elText = await page.locator(step.locator_value).textContent().catch(() => '');
                  sharedVariables[step.output_var] = elText;
                }
                return { status: 'passed', message: '操作完成' };
              }, retryCount, `用例${i+1}步骤${j+1}`);

              stepResults.push({ order: j + 1, type: step.type, mode: 'traditional', instruction, locator_value: step.locator_value, action_type: step.action_type || 'click', output_var: step.output_var || null, retry_count: retryCount, ...stepResult });
            } catch (stepErr) {
              const failureScreenshot = await captureFailureScreenshot(batchId, j, page);
              stepResults.push({ order: j + 1, type: step.type, mode: 'traditional', instruction, locator_value: step.locator_value, output_var: step.output_var || null, retry_count: retryCount, status: 'failed', message: stepErr.message, screenshot: failureScreenshot });
              break;
            }
          } else {
            // ===== AI模式 =====
            let aiInstruction = instruction;
            if (input_value) aiInstruction = aiInstruction ? `${aiInstruction}，输入值为: ${input_value}` : `输入: ${input_value}`;
            // 替换共享变量
            for (const [varName, varValue] of Object.entries(sharedVariables)) {
              const placeholder = '${' + varName + '}';
              if (aiInstruction.includes(placeholder)) {
                aiInstruction = aiInstruction.replaceAll(placeholder, String(varValue));
              }
            }
            try {
              const stepResult = await withRetry(async () => {
                let result;
                switch (step.type) {
                  case 'aiAct':
                    await withTimeout(agent.aiAct(aiInstruction), STEP_TIMEOUT, `步骤${j+1}`);
                    result = { status: 'passed', message: '操作完成' };
                    break;
                  case 'aiTap':
                    await withTimeout(agent.aiTap(aiInstruction), STEP_TIMEOUT, `步骤${j+1}`);
                    result = { status: 'passed', message: '点击完成' };
                    break;
                  case 'aiAssert':
                    await withTimeout(agent.aiAssert(aiInstruction), STEP_TIMEOUT, `步骤${j+1}`);
                    result = { status: 'passed', message: '断言通过' };
                    break;
                  case 'aiQuery':
                    const queryResult = await withTimeout(agent.aiQuery(aiInstruction), STEP_TIMEOUT, `步骤${j+1}`);
                    result = { status: 'passed', message: '查询完成', data: queryResult };
                    break;
                  case 'aiWaitFor':
                    await withTimeout(agent.aiWaitFor(aiInstruction), STEP_TIMEOUT, `步骤${j+1}`);
                    result = { status: 'passed', message: '等待条件满足' };
                    break;
                  case 'sleep':
                    await new Promise(r => setTimeout(r, step.duration || 2000));
                    result = { status: 'passed', message: `等待${(step.duration || 2000) / 1000}秒` };
                    break;
                  default:
                    await withTimeout(agent.aiAct(aiInstruction), STEP_TIMEOUT, `步骤${j+1}`);
                    result = { status: 'passed', message: '操作完成（默认aiAct）' };
                }
                if (step.type !== 'sleep') await new Promise(r => setTimeout(r, Math.min(waitAfterAction, 3000)));
                // 变量提取
                if (step.output_var) {
                  let varValue = result.data || input_value || result.message || '';
                  sharedVariables[step.output_var] = varValue;
                }
                return result;
              }, retryCount, `用例${i+1}步骤${j+1}`);

              stepResults.push({ order: j + 1, type: step.type, mode: 'ai', instruction: step.instruction, output_var: step.output_var || null, retry_count: retryCount, ...stepResult });
            } catch (stepErr) {
              const failureScreenshot = await captureFailureScreenshot(batchId, j, page);
              stepResults.push({ order: j + 1, type: step.type, mode: 'ai', instruction: step.instruction, output_var: step.output_var || null, retry_count: retryCount, status: 'failed', message: stepErr.message, screenshot: failureScreenshot });
              break;
            }
          }
        }

        // 用例执行完毕，回调Django
        const hasFailed = stepResults.some(s => s.status === 'failed');
        const caseResult = { status: hasFailed ? 'failed' : 'passed', step_results: stepResults };
        const caseError = hasFailed ? (stepResults.find(s => s.status === 'failed')?.message || '步骤失败') : '';

        batch.results[resultIdx].status = hasFailed ? 'failed' : 'passed';
        batch.results[resultIdx].error = caseError || null;

        // 提取失败步骤截图
        const failedScreenshots = stepResults
          .filter(s => s.status === 'failed' && s.screenshot)
          .map(s => ({ order: s.order, screenshot: s.screenshot }));

        // 回调
        if (payload.callback_url) {
          try {
            const fetch = require('node-fetch');
            await fetch(payload.callback_url, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                task_id: `shared-${batchId}-${i}`,
                execution_id: executionId,
                status: hasFailed ? 'failed' : 'completed',
                result: caseResult,
                error: caseError || '',
                completed_at: new Date().toISOString(),
                report_url: null,
                report_file: null,
                failed_screenshots: failedScreenshots,
              })
            });
          } catch (_) {}
        }

      } catch (err) {
        batch.results[resultIdx].status = 'failed';
        batch.results[resultIdx].error = err.message;

        // 回调失败
        if (payload.callback_url) {
          try {
            const fetch = require('node-fetch');
            await fetch(payload.callback_url, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                task_id: `shared-${batchId}-${i}`,
                execution_id: executionId,
                status: 'failed',
                result: { status: 'failed', step_results: [] },
                error: err.message,
                completed_at: new Date().toISOString(),
                report_url: null,
                report_file: null,
                failed_screenshots: [],
              })
            });
          } catch (_) {}
        }
      }

      batch.completed = i + 1;
    }

  } catch (err) {
    console.error(`[SharedSession] 共享会话执行失败: ${err.message}`);
    // 所有未完成的用例标记失败
    for (let i = 0; i < batch.results.length; i++) {
      if (batch.results[i].status === 'running') {
        batch.results[i].status = 'failed';
        batch.results[i].error = err.message;
      }
    }
  } finally {
    // 恢复截图方法（Web端）
    if (page && typeof page._releaseCdpScreenshot === 'function') {
      page._releaseCdpScreenshot();
    }

    // 立即关闭浏览器：3秒优雅关闭 → 超时则taskkill强杀
    console.log(`[SharedSession] 所有用例执行完毕，立即关闭浏览器...`);
    if (browser) {
      console.time('[SharedSession] browser-close');
      try {
        await Promise.race([browser.close(), new Promise((_, r) => setTimeout(() => r(new Error('timeout')), 3000))]);
        console.timeEnd('[SharedSession] browser-close');
      } catch (e) {
        console.timeEnd('[SharedSession] browser-close');
        console.warn(`[SharedSession] browser.close() 超时，强杀进程`);
        // 用启动时记录的PID强杀
        const pid = browserPid || browser?.process?.()?.pid;
        if (pid) {
          try {
            const { execSync } = require('child_process');
            execSync(`taskkill /f /pid ${pid} /t 2>nul`, { timeout: 3000 });
            console.log(`[SharedSession] taskkill /f /pid ${pid} /t`);
          } catch (_) {}
        }
      }
    }
    console.log(`[SharedSession] 浏览器已关闭`);

    // agent.destroy 异步执行（报告生成不阻塞）
    if (agent) {
      setImmediate(async () => {
        try {
          await Promise.race([agent.destroy(), new Promise((_, r) => setTimeout(() => r(), 15000))]);
          console.log(`[SharedSession] agent.destroy() 异步完成`);
        } catch (_) {}
      });
    }

    // Android设备释放
    try {
      if (androidDevice && typeof androidDevice.destroy === 'function') {
        await Promise.race([androidDevice.destroy(), new Promise((_, r) => setTimeout(() => r(new Error('timeout')), 3000))]);
      }
    } catch (_) {}
  }
}

// ============ 启动 ============

app.listen(PORT, () => {
  console.log(`[Midscene Service v2.1] 已启动，端口: ${PORT}`);
  console.log(`[Midscene Service] 健康检查: http://localhost:${PORT}/health`);
  console.log(`[Midscene Service] 执行接口: POST http://localhost:${PORT}/execute`);
  console.log(`[Midscene Service] 批量执行: POST http://localhost:${PORT}/execute-batch`);
  console.log(`[Midscene Service] 取消任务: POST http://localhost:${PORT}/cancel/:taskId`);
  console.log(`[Midscene Service] 最大并发数: ${MAX_CONCURRENCY}`);
  console.log(`[Midscene Service] 报告目录: ${REPORT_DIR}`);
  console.log(`[Midscene Service] 截图目录: ${SCREENSHOT_DIR}`);
  console.log(`[Midscene Service] 报告访问: http://localhost:${PORT}/report/<filename>`);
});
