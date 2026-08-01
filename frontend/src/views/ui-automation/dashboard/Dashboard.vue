<template>
  <div class="dashboard">
    <!-- 顶部数据概览卡片 -->
    <div class="overview-cards">
      <div class="overview-card" v-for="item in overviewItems" :key="item.key">
        <div class="card-indicator" :style="{ background: item.color }"></div>
        <div class="card-body">
          <div class="card-value">{{ item.value }}</div>
          <div class="card-label">{{ item.label }}</div>
        </div>
        <div class="card-icon" :style="{ color: item.color }">
          <el-icon :size="24"><component :is="item.icon" /></el-icon>
        </div>
      </div>
    </div>

    <!-- 主体两栏 -->
    <div class="main-grid">
      <!-- 左侧：测试计划看板 -->
      <div class="plan-board">
        <div class="section-header">
          <span class="section-title">测试计划看板</span>
          <span class="section-badge">{{ planCount }} 个计划</span>
        </div>

        <!-- 计划状态分布 -->
        <div class="plan-status-row">
          <div class="plan-status-chip passed">
            <span class="dot"></span>通过 {{ planPassed }}
          </div>
          <div class="plan-status-chip failed">
            <span class="dot"></span>失败 {{ planFailed }}
          </div>
          <div class="plan-status-chip running">
            <span class="dot"></span>执行中 {{ planRunning }}
          </div>
          <div class="plan-status-chip pending">
            <span class="dot"></span>待执行 {{ planPending }}
          </div>
        </div>

        <!-- 最近执行的计划列表 -->
        <div class="plan-list" v-if="recentPlans.length > 0">
          <div class="plan-item" v-for="plan in recentPlans" :key="plan.id" @click="goToPlanDetail(plan.id)">
            <div class="plan-item-left">
              <div class="plan-item-name">{{ plan.name }}</div>
              <div class="plan-item-project">{{ plan.project_name }}</div>
            </div>
            <div class="plan-item-right">
              <div class="plan-item-stats">
                <span class="stat-pass" v-if="plan.passed_count">{{ plan.passed_count }} 通过</span>
                <span class="stat-fail" v-if="plan.failed_count">{{ plan.failed_count }} 失败</span>
              </div>
              <div class="plan-item-status" :class="plan.execution_status">
                {{ planStatusText(plan.execution_status) }}
              </div>
            </div>
          </div>
        </div>
        <div class="plan-list-empty" v-else>
          <el-icon :size="32" color="#c0c4cc"><Tickets /></el-icon>
          <span>暂无执行记录</span>
        </div>

        <!-- 查看全部 -->
        <div class="plan-footer" v-if="planCount > 0" @click="goToTestPlans">
          查看全部计划 <el-icon><ArrowRight /></el-icon>
        </div>
      </div>

      <!-- 右侧 -->
      <div class="right-col">
        <!-- 快速操作 -->
        <div class="quick-panel">
          <div class="section-header">
            <span class="section-title">快速操作</span>
          </div>
          <div class="quick-grid">
            <div class="quick-item" v-for="item in quickActions" :key="item.label" @click="item.action">
              <div class="quick-icon" :style="{ background: item.bg, color: item.fg }">
                <el-icon :size="18"><component :is="item.icon" /></el-icon>
              </div>
              <div class="quick-text">
                <span class="quick-label">{{ item.label }}</span>
                <span class="quick-desc">{{ item.desc }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 最近活动 -->
        <div class="activity-panel">
          <div class="section-header">
            <span class="section-title">最近活动</span>
          </div>
          <div v-if="loading" class="panel-empty">
            <span>加载中...</span>
          </div>
          <div v-else-if="operationRecords.length === 0" class="panel-empty">
            <span>暂无记录</span>
          </div>
          <div v-else class="activity-list">
            <div v-for="record in operationRecords" :key="record.id" class="activity-row">
              <div class="activity-dot" :class="getDotClass(record.operation_type)"></div>
              <div class="activity-body">
                <div class="activity-text">
                  <span class="op-user">{{ record.user_name }}</span>
                  <span class="op-action">{{ record.operation_type_display }}</span>
                  <span class="op-resource">{{ record.resource_type_display }}</span>
                  <span class="op-name">{{ record.resource_name }}</span>
                </div>
                <div class="activity-time">{{ formatRelativeTime(record.created_at) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  Folder, Document, Collection, RefreshRight,
  Bell, Cpu, Monitor, Platform, VideoPlay, DataAnalysis,
  Plus, Delete, CaretRight, Refresh, Tickets, ArrowRight,
  Calendar, Setting, Aim, Connection, Timer
} from '@element-plus/icons-vue'
import router from '@/router'
import {
  getDashboardStats,
  getOperationRecords
} from '@/api/ui_automation'

const { t } = useI18n()

// 统计数据
const projectCount = ref(0)
const testCaseCount = ref(0)
const suiteCount = ref(0)
const executionCount = ref(0)
const planCount = ref(0)
const planPassed = ref(0)
const planFailed = ref(0)
const planRunning = ref(0)
const planPending = ref(0)
const recentPlans = ref([])

// 操作记录
const operationRecords = ref([])
const loading = ref(false)

// 概览卡片
const overviewItems = computed(() => [
  { key: 'project', label: '测试项目', value: projectCount.value, icon: Folder, color: '#6366f1' },
  { key: 'case', label: '测试用例', value: testCaseCount.value, icon: Document, color: '#0ea5e9' },
  { key: 'suite', label: '测试套件', value: suiteCount.value, icon: Collection, color: '#8b5cf6' },
  { key: 'exec', label: '执行记录', value: executionCount.value, icon: RefreshRight, color: '#f59e0b' },
])

// 快速操作（含功能描述）
const quickActions = [
  { label: '项目管理', desc: '管理测试项目与成员', icon: Folder, bg: '#eef2ff', fg: '#6366f1', action: () => router.push('/ui-automation/projects') },
  { label: '元素管理', desc: 'AI提取+交互式定位', icon: Monitor, bg: '#ecfdf5', fg: '#10b981', action: () => router.push('/ui-automation/elements-enhanced') },
  { label: '用例管理', desc: '可视化编排测试步骤', icon: Document, bg: '#f0f9ff', fg: '#0ea5e9', action: () => router.push('/ui-automation/test-cases') },
  { label: '套件管理', desc: '组合用例批量执行', icon: Collection, bg: '#faf5ff', fg: '#8b5cf6', action: () => router.push('/ui-automation/suites') },
  { label: '测试计划', desc: '计划编排+共享会话', icon: Tickets, bg: '#fff7ed', fg: '#f59e0b', action: () => router.push('/ui-automation/test-plans') },
  { label: '执行记录', desc: '实时日志+截图回溯', icon: VideoPlay, bg: '#fef2f2', fg: '#ef4444', action: () => router.push('/ui-automation/executions') },
  { label: '测试报告', desc: 'Allure报告+失败归因', icon: DataAnalysis, bg: '#f0fdf4', fg: '#22c55e', action: () => router.push('/ui-automation/reports') },
  { label: '定时任务', desc: 'Cron调度+邮件通知', icon: Timer, bg: '#eff6ff', fg: '#3b82f6', action: () => router.push('/ui-automation/scheduled-tasks') },
]

// 计划状态文本
const planStatusText = (status) => {
  const map = { 'passed': '通过', 'failed': '失败', 'running': '执行中', 'pending': '待执行', 'not_executed': '未执行' }
  return map[status] || status
}

// 活动圆点样式
const getDotClass = (type) => {
  const map = { 'create': 'dot-create', 'edit': 'dot-edit', 'delete': 'dot-delete', 'run': 'dot-run', 'rerun': 'dot-rerun', 'save': 'dot-save' }
  return map[type] || ''
}

// 格式化相对时间
const formatRelativeTime = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  return `${diffDays} 天前`
}

// 导航
const goToTestPlans = () => router.push('/ui-automation/test-plans')
const goToPlanDetail = (id) => router.push(`/ui-automation/test-plans/${id}`)

// 加载数据
const loadDashboardData = async () => {
  loading.value = true
  try {
    const [statsRes, recordsRes] = await Promise.all([
      getDashboardStats(),
      getOperationRecords({ limit: 8 })
    ])
    const stats = statsRes.data
    projectCount.value = stats.project_count || 0
    testCaseCount.value = stats.test_case_count || 0
    suiteCount.value = stats.suite_count || 0
    executionCount.value = stats.execution_count || 0
    planCount.value = stats.plan_count || 0
    planPassed.value = stats.plan_passed || 0
    planFailed.value = stats.plan_failed || 0
    planRunning.value = stats.plan_running || 0
    planPending.value = stats.plan_pending || 0
    recentPlans.value = stats.recent_plans || []
    operationRecords.value = recordsRes.data.results || recordsRes.data || []
  } catch (error) {
    ElMessage.error('加载仪表盘数据失败')
    console.error('Failed to load dashboard data:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
/* ===== 全局布局 ===== */
.dashboard {
  padding: 32px 36px;
  background: #f7f8fa;
  min-height: calc(100vh - 100px);
}

/* ===== 概览卡片 ===== */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 28px;
}

.overview-card {
  position: relative;
  background: #fff;
  border-radius: 12px;
  padding: 24px 24px 24px 0;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  transition: box-shadow 0.2s, transform 0.2s;
  overflow: hidden;
}
.overview-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
  transform: translateY(-2px);
}

.card-indicator {
  width: 4px;
  height: 100%;
  position: absolute;
  left: 0;
  top: 0;
  border-radius: 12px 0 0 12px;
}

.card-body {
  flex: 1;
  padding-left: 24px;
}

.card-value {
  font-size: 28px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.2;
  letter-spacing: -0.5px;
}

.card-label {
  font-size: 13px;
  color: #94a3b8;
  margin-top: 4px;
  font-weight: 400;
}

.card-icon {
  padding-right: 20px;
  opacity: 0.85;
}

/* ===== 主网格 ===== */
.main-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 20px;
  margin-bottom: 28px;
}

/* ===== 测试计划看板 ===== */
.plan-board {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.section-badge {
  font-size: 12px;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 400;
}

/* 计划状态分布 */
.plan-status-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.plan-status-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #64748b;
  background: #f8fafc;
  padding: 6px 14px;
  border-radius: 8px;
  font-weight: 400;
}

.plan-status-chip .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.plan-status-chip.passed .dot { background: #10b981; }
.plan-status-chip.failed .dot { background: #ef4444; }
.plan-status-chip.running .dot { background: #3b82f6; animation: pulse-dot 1.5s infinite; }
.plan-status-chip.pending .dot { background: #94a3b8; }

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* 计划列表 */
.plan-list {
  flex: 1;
  overflow-y: auto;
}

.plan-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
  border: 1px solid transparent;
}
.plan-item:hover {
  background: #f8fafc;
  border-color: #e2e8f0;
}

.plan-item-name {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 3px;
}

.plan-item-project {
  font-size: 12px;
  color: #94a3b8;
}

.plan-item-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.plan-item-stats {
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  gap: 8px;
}

.stat-pass { color: #10b981; }
.stat-fail { color: #ef4444; }

.plan-item-status {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: 500;
  min-width: 60px;
  text-align: center;
}
.plan-item-status.passed { background: #ecfdf5; color: #10b981; }
.plan-item-status.failed { background: #fef2f2; color: #ef4444; }
.plan-item-status.running { background: #eff6ff; color: #3b82f6; }
.plan-item-status.pending, .plan-item-status.not_executed { background: #f1f5f9; color: #94a3b8; }

.plan-list-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #c0c4cc;
  padding: 40px 0;
  font-size: 14px;
}

.plan-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding-top: 16px;
  margin-top: 8px;
  border-top: 1px solid #f1f5f9;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: color 0.15s;
}
.plan-footer:hover { color: #6366f1; }

/* ===== 右侧栏 ===== */
.right-col {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.quick-panel,
.activity-panel {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* 快速操作 */
.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.quick-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s, transform 0.15s;
}
.quick-item:hover {
  background: #f8fafc;
  transform: translateY(-1px);
}

.quick-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.quick-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.quick-label {
  font-size: 13px;
  color: #1e293b;
  font-weight: 500;
  line-height: 1.3;
}

.quick-desc {
  font-size: 11px;
  color: #94a3b8;
  line-height: 1.4;
  margin-top: 2px;
}

/* 活动面板 */
.panel-empty {
  text-align: center;
  color: #c0c4cc;
  padding: 32px 0;
  font-size: 14px;
}

.activity-list {
  max-height: 320px;
  overflow-y: auto;
}

.activity-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}
.activity-row:last-child { border-bottom: none; }

.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
  background: #cbd5e1;
}
.activity-dot.dot-create { background: #6366f1; }
.activity-dot.dot-edit, .activity-dot.dot-save { background: #f59e0b; }
.activity-dot.dot-delete { background: #ef4444; }
.activity-dot.dot-run, .activity-dot.dot-rerun { background: #10b981; }

.activity-body { flex: 1; min-width: 0; }

.activity-text {
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
  word-break: break-all;
}

.op-user { color: #6366f1; font-weight: 500; }
.op-action { margin: 0 2px; }
.op-resource { margin: 0 2px; color: #94a3b8; }
.op-name { font-weight: 500; color: #1e293b; }

.activity-time {
  font-size: 12px;
  color: #cbd5e1;
  margin-top: 4px;
}



/* ===== 响应式 ===== */
@media (max-width: 1600px) {
  .main-grid { grid-template-columns: 1fr 340px; }
  .overview-cards { gap: 16px; }
  .card-value { font-size: 24px; }
}

@media (max-width: 1280px) {
  .dashboard { padding: 24px; }
  .main-grid { grid-template-columns: 1fr; }
}

@media (max-width: 1024px) {
  .overview-cards { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .dashboard { padding: 16px; }
  .overview-cards { grid-template-columns: 1fr; }
  .quick-grid { grid-template-columns: 1fr; }
}
</style>
