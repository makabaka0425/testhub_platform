import { test as base } from '@playwright/test';
import type { PlayWrightAiFixtureType } from '@midscene/web/playwright';
import { PlaywrightAiFixture } from '@midscene/web/playwright';

/**
 * 灵测 L-Test Platform - Midscene AI Fixture
 *
 * 扩展 Playwright test 对象，注入 Midscene AI 能力：
 * - ai: AI 操作（点击、输入、导航等自然语言指令）
 * - aiQuery: AI 查询（从页面提取结构化数据）
 * - aiAssert: AI 断言（用自然语言验证页面状态）
 * - aiWaitFor: AI 等待（等待页面达到指定状态）
 * - aiTap: AI 点击（精准点击指定元素）
 * - aiLocate: AI 定位（定位元素位置）
 * - aiNumber/aiBoolean/aiString: AI 提取特定类型数据
 *
 * 同时注入有头模式防闪烁机制：
 * - CDP 层：通过 Chrome DevTools Protocol 禁用浏览器级别动画
 * - CSS 层：注入样式禁用 CSS animation/transition/scroll-behavior
 * - 截图层：替换 page.screenshot 为 CDP 截图（避免闪烁）
 * - 导航后自动重新注入 CSS
 */

// 是否有头模式（由 Django 启动 subprocess 时设置 LINGCE_LTEST_HEADLESS 环境变量）
const headless = process.env.LINGCE_LTEST_HEADLESS !== 'false';

// 防闪烁 CSS 内容
const ANTI_FLICKER_CSS = `*, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; scroll-behavior: auto !important; }`;

// 先扩展 Midscene AI fixture
const testWithAi = base.extend<PlayWrightAiFixtureType>(PlaywrightAiFixture());

// 再扩展 page fixture，添加 CDP 防闪烁
export const test = testWithAi.extend({
  page: async ({ page }, use) => {
    if (!headless) {
      try {
        // ---- CDP 层防闪烁 ----
        const cdp = await page.context().newCDPSession(page);

        // 1. 禁用 CDP Animation 域（阻止浏览器执行动画）
        await cdp.send('Animation.disable');

        // 2. 通过 Page.addScriptToEvaluateOnNewDocument 注入 JS
        //    在每个新文档加载时自动执行，确保导航后也生效
        await cdp.send('Page.addScriptToEvaluateOnNewDocument', {
          source: `
            (function() {
              const style = document.createElement('style');
              style.textContent = ${JSON.stringify(ANTI_FLICKER_CSS)};
              (document.head || document.documentElement).appendChild(style);
            })();
          `,
        });

        // 3. CSS 层防闪烁（对当前页面立即生效）
        await page.addStyleTag({ content: ANTI_FLICKER_CSS });

        // 4. 截图层防闪烁：用 CDP 截图替代 Playwright 原生截图
        //    CDP 截图直接调用浏览器内部接口，不会触发页面重绘/闪烁
        const originalScreenshot = page.screenshot.bind(page);
        page.screenshot = async function (opts: any = {}) {
          try {
            const { data } = await cdp.send('Page.captureScreenshot', {
              format: opts.type === 'png' ? 'png' : 'jpeg',
              quality: opts.type === 'png' ? undefined : (opts.quality || 90),
            });
            return Buffer.from(data, 'base64');
          } catch (_) {
            // CDP 截图失败时回退到 Playwright 原生截图
            return originalScreenshot(opts);
          }
        };

        // 5. 监听页面导航，重新注入 CSS（导航后 addStyleTag 可能丢失）
        page.on('framenavigated', async () => {
          try {
            await page.addStyleTag({ content: ANTI_FLICKER_CSS });
          } catch (_) {
            // 页面可能已关闭，忽略
          }
        });
      } catch (e) {
        // CDP 注入失败时静默降级为纯 CSS 模式（不影响测试执行）
        console.warn('[anti-flicker] CDP 防闪烁注入失败，降级为纯 CSS 模式:', (e as Error).message);
        try {
          await page.addStyleTag({ content: ANTI_FLICKER_CSS });
        } catch (_) {}
      }
    }

    await use(page);
  },
});

export { expect } from '@playwright/test';
