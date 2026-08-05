import type { Reporter, FullConfig, Suite, TestCase, TestResult } from '@playwright/test/reporter';
import http from 'http';
import fs from 'fs';
import path from 'path';

/**
 * TestHub Platform - Django 回调 Reporter
 *
 * 在每个 test case 结束后，通过 HTTP POST 回调 Django 后端，更新执行记录状态。
 *
 * 步骤结果来源优先级：
 * 1. test.info().attachments 中名为 'step-results' 的 attachment
 * 2. 环境变量 TESTHUB_STEP_RESULTS（仅单用例模式）
 * 3. 空 fallback
 */
class DjangoCallbackReporter implements Reporter {
  private callbackUrl: string = '';
  private executionId: number = 0;
  private taskId: string = '';
  private resultsDir: string = '';

  onBegin(config: FullConfig, suite: Suite) {
    this.callbackUrl = process.env.TESTHUB_CALLBACK_URL || '';
    this.executionId = parseInt(process.env.TESTHUB_EXECUTION_ID || '0', 10);
    this.taskId = process.env.TESTHUB_TASK_ID || '';
    this.resultsDir = process.env.TESTHUB_RESULTS_DIR || './midscene_run/results';

    // 确保结果目录存在
    if (!fs.existsSync(this.resultsDir)) {
      fs.mkdirSync(this.resultsDir, { recursive: true });
    }
  }

  onTestEnd(testCase: TestCase, result: TestResult) {
    // 提取步骤结果（从 attachments）
    let stepResults: any[] = [];
    for (const attachment of result.attachments) {
      if (attachment.name === 'step-results') {
        try {
          let bodyStr: string;
          if (attachment.body) {
            bodyStr = attachment.body.toString('utf-8');
          } else if (attachment.path) {
            bodyStr = fs.readFileSync(attachment.path, 'utf-8');
          } else {
            continue;
          }
          const parsed = JSON.parse(bodyStr);
          if (Array.isArray(parsed)) {
            stepResults = parsed;
          }
        } catch (_) {}
      }
    }

    // 状态判断：Playwright result.status + step_results 双重校验
    // 共享会话模式下 test.step().catch() 会吞掉错误，导致 Playwright 认为 test passed
    // 但 step_results 中有 failed 步骤，此时应标记为 failed
    const hasFailedStep = stepResults.some((s: any) => s.status === 'failed');
    const isPassed = result.status === 'passed' && !hasFailedStep;
    const status = isPassed ? 'completed' : 'failed';
    const error = result.error?.message || (hasFailedStep ? '存在失败的步骤' : '');

    // 提取变量快照（从 attachments）
    let variableSnapshot: Record<string, any> = {};
    for (const attachment of result.attachments) {
      if (attachment.name === 'variable-snapshot') {
        try {
          let bodyStr: string;
          if (attachment.body) {
            bodyStr = attachment.body.toString('utf-8');
          } else if (attachment.path) {
            bodyStr = fs.readFileSync(attachment.path, 'utf-8');
          } else {
            continue;
          }
          variableSnapshot = JSON.parse(bodyStr);
        } catch (_) {}
      }
    }

    // 失败截图
    const failedScreenshots = stepResults
      .filter(s => s.status === 'failed' && s.screenshot)
      .map(s => ({ order: s.order, screenshot: s.screenshot }));

    // ---- 查找 Midscene Reporter 生成的回放报告 ----
    // Playwright Test 模式下，@midscene/web/playwright-reporter 将报告输出到 MIDSCENE_RUN_DIR/report/
    // 扫描该目录，找到最近5分钟内生成的 .html 报告文件，构造 URL 回传
    let reportUrl: string | null = null;
    let reportFile: string | null = null;
    try {
      const midsceneRunDir = process.env.MIDSCENE_RUN_DIR || path.join(__dirname, '..', 'midscene_run');
      const reportDir = path.join(midsceneRunDir, 'report');
      if (fs.existsSync(reportDir)) {
        const files = fs.readdirSync(reportDir)
          .filter(f => f.endsWith('.html'))
          .map(f => {
            const fp = path.join(reportDir, f);
            return { name: f, path: fp, mtime: fs.statSync(fp).mtimeMs };
          })
          .sort((a, b) => b.mtime - a.mtime); // 按修改时间降序

        const fiveMinutesAgo = Date.now() - 300000;
        for (const f of files) {
          if (f.mtime >= fiveMinutesAgo) {
            reportFile = f.path;
            // 通过 server.js (端口8001) 的 /report 路由访问
            reportUrl = `http://localhost:8001/report/${f.name}`;
            break;
          }
        }
      }
    } catch (e: any) {
      console.warn(`[DjangoCallback] 查找回放报告失败: ${e.message}`);
    }

    // ---- 查找 Midscene 注解中的报告路径（PlaywrightAiFixture 会设置）----
    // 优先使用注解中的路径，比扫描文件系统更准确
    for (const annotation of testCase.annotations) {
      if (annotation.type === 'MIDSCENE_DUMP_ANNOTATION' && annotation.description) {
        reportFile = annotation.description;
        // 从文件路径提取文件名构造 URL
        const reportName = path.basename(annotation.description);
        reportUrl = `http://localhost:8001/report/${reportName}`;
        break;
      }
    }

    const callbackData = {
      task_id: this.taskId,
      execution_id: this.executionId,
      status,
      result: {
        status: isPassed ? 'passed' : 'failed',
        step_results: stepResults,
      },
      error,
      completed_at: new Date().toISOString(),
      report_url: reportUrl,
      report_file: reportFile,
      failed_screenshots: failedScreenshots,
      variable_snapshot: variableSnapshot,
    };

    // 写入结果文件（供 Django _sync_from_result_file 读取）
    const resultFilePath = path.join(this.resultsDir, `result_${this.executionId}.json`);
    try {
      fs.writeFileSync(resultFilePath, JSON.stringify(callbackData, null, 2));
    } catch (_) {}

    // 发送回调
    if (this.callbackUrl) {
      this._sendCallback(this.callbackUrl, callbackData);
    }

    // 如果有多个 execution（共享会话模式），需要处理批量回调
    // 共享会话的结果由 .spec.ts 中每个 test.step 的步骤结果整合
  }

  onEnd() {
    // 汇总结束
  }

  private _sendCallback(url: string, data: any): void {
    try {
      const body = JSON.stringify(data);
      const urlObj = new URL(url);
      const options = {
        hostname: urlObj.hostname,
        port: urlObj.port || 80,
        path: urlObj.pathname + urlObj.search,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body),
        },
        timeout: 10000,
      };

      const req = http.request(options, (res) => {
        res.resume();
        if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
          console.log(`[DjangoCallback] 回调成功: ${url}`);
        } else {
          console.warn(`[DjangoCallback] 回调返回非2xx: ${res.statusCode}`);
        }
      });
      req.on('error', (err) => {
        console.error(`[DjangoCallback] 回调失败: ${err.message}`);
      });
      req.on('timeout', () => {
        req.destroy();
        console.error('[DjangoCallback] 回调超时');
      });
      req.write(body);
      req.end();
    } catch (err: any) {
      console.error(`[DjangoCallback] 回调异常: ${err.message}`);
    }
  }
}

export default DjangoCallbackReporter;
