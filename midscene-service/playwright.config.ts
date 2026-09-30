import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';
import path from 'path';

/**
 * 灵测 L-Test Platform - Playwright Test 配置
 *
 * 架构说明：
 * - 浏览器生命周期由 Playwright Test 自动托管（不再手动 browser.close()）
 * - Midscene AI 能力通过 PlaywrightAiFixture 注入
 * - Midscene 官方报告通过 @midscene/web/playwright-reporter 生成
 * - Django 回调通过自定义 django-callback-reporter 实现
 * - 模型配置通过 .env 环境变量注入（MIDSCENE_MODEL_NAME 等）
 */

// 加载 .env 环境变量
dotenv.config();

// 如果指定了额外的 .env 文件路径（通过环境变量），加载它
const envFile = process.env.LINGCE_LTEST_ENV_FILE;
if (envFile) {
  dotenv.config({ path: envFile });
}

// 结果目录（由 Django 启动 subprocess 时设置）
const resultsDir = process.env.LINGCE_LTEST_RESULTS_DIR || path.join(__dirname, 'midscene_run', 'results');

// 是否有头模式（由 Django 启动 subprocess 时设置）
const headless = process.env.LINGCE_LTEST_HEADLESS !== 'false';

// 设置 MIDSCENE_RUN_DIR（Midscene SDK 报告输出目录）
// 必须在 defineConfig 之前设置，因为 Midscene Reporter 在进程启动时读取此变量
if (!process.env.MIDSCENE_RUN_DIR) {
  process.env.MIDSCENE_RUN_DIR = path.join(__dirname, 'midscene_run');
}

// 确保结果目录存在
import fs from 'fs';
if (!fs.existsSync(resultsDir)) {
  fs.mkdirSync(resultsDir, { recursive: true });
}

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.spec.ts',

  // 超时：单用例最长10分钟
  timeout: 10 * 60 * 1000,

  // 不并行（保持执行顺序，共享会话模式依赖此特性）
  fullyParallel: false,

  // 单worker（共享会话模式需要串行执行）
  workers: 1,

  // 不重试（失败即停，与旧逻辑一致）
  retries: 0,

  // Reporter 配置
  reporter: [
    // 控制台输出
    ['list'],
    // Midscene 官方报告（生成可视化回放报告）
    ['@midscene/web/playwright-reporter'],
    // Django 回调 Reporter
    ['./e2e/django-callback-reporter.ts'],
    // JSON 报告（用于 Django 读取步骤结果，兜底）
    ['json', path.join(resultsDir, 'report.json')],
  ],

  // 浏览器配置
  use: {
    headless,

    // 有头模式：不使用 Playwright 管理的 viewport（让窗口最大化）
    viewport: headless ? { width: 1280, height: 768 } : undefined,
    noViewport: !headless,

    // 截图策略：失败时截图
    screenshot: 'only-on-failure',

    // Trace：关闭
    trace: 'off',

    // 浏览器启动参数
    launchOptions: {
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-blink-features=AutomationControlled',
        '--disable-infobars',
        '--disable-background-timer-throttling',
        '--disable-renderer-backgrounding',
        '--no-first-run',
      ],
    },
  },

  // 只使用 Chromium
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
