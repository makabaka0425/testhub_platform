<template>
  <div class="ai-dashboard">
    <!-- 顶部：项目选择 + 平台切换 -->
    <div class="dashboard-header">
      <div class="header-left">
        <span class="page-title">{{ $t('menu.dashboard') }}</span>
      </div>
      <div class="header-right">
        <el-select v-model="projectId" :placeholder="$t('menu.projectManagement')" clearable style="width: 200px" @change="loadAllStats">
          <el-option v-for="p in projectList" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-radio-group v-model="platform" @change="loadAllStats">
          <el-radio-button value="all">{{ $t('aiAutomation.dashboard.all') }}</el-radio-button>
          <el-radio-button value="web">{{ $t('aiAutomation.dashboard.web') }}</el-radio-button>
          <el-radio-button value="app">{{ $t('aiAutomation.dashboard.app') }}</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 总体统计卡片 -->
    <div class="stats-row" v-if="statsData">
      <div class="stat-card">
        <div class="stat-card__icon" style="background:#ecf5ff;color:#409eff"><el-icon :size="22"><VideoPlay /></el-icon></div>
        <div class="stat-card__body">
          <div class="stat-card__value">{{ statsData.total }}</div>
          <div class="stat-card__label">{{ $t('aiAutomation.dashboard.totalExec') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-card__icon" style="background:#f0f9eb;color:#67c23a"><el-icon :size="22"><CircleCheck /></el-icon></div>
        <div class="stat-card__body">
          <div class="stat-card__value" style="color:#67c23a">{{ statsData.passed }}</div>
          <div class="stat-card__label">{{ $t('aiAutomation.dashboard.passed') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-card__icon" style="background:#fef0f0;color:#f56c6c"><el-icon :size="22"><CircleClose /></el-icon></div>
        <div class="stat-card__body">
          <div class="stat-card__value" style="color:#f56c6c">{{ statsData.failed }}</div>
          <div class="stat-card__label">{{ $t('aiAutomation.dashboard.failed') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-card__icon" style="background:#ecf5ff;color:#409eff"><el-icon :size="22"><DataAnalysis /></el-icon></div>
        <div class="stat-card__body">
          <div class="stat-card__value" style="color:#409eff">{{ statsData.pass_rate }}%</div>
          <div class="stat-card__label">{{ $t('aiAutomation.dashboard.passRate') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-card__icon" style="background:#f5f7fa;color:#909399"><el-icon :size="22"><Timer /></el-icon></div>
        <div class="stat-card__body">
          <div class="stat-card__value">{{ statsData.avg_duration }}s</div>
          <div class="stat-card__label">{{ $t('aiAutomation.dashboard.avgDuration') }}</div>
        </div>
      </div>
      <div class="stat-card" v-if="statsData.running > 0">
        <div class="stat-card__icon" style="background:#fdf6ec;color:#e6a23c"><el-icon :size="22"><Loading /></el-icon></div>
        <div class="stat-card__body">
          <div class="stat-card__value" style="color:#e6a23c">{{ statsData.running }}</div>
          <div class="stat-card__label">{{ $t('aiAutomation.dashboard.running') }}</div>
        </div>
      </div>
    </div>

    <!-- 中部两栏：趋势图 + 平台分布 -->
    <div class="charts-row">
      <div class="chart-card trend-card">
        <div class="chart-card__header">
          <span class="chart-card__title">{{ $t('aiAutomation.dashboard.execTrend') }}</span>
        </div>
        <div class="chart-card__body">
          <div ref="trendChartRef" class="chart-container"></div>
          <div v-if="!statsData?.trend?.length" class="chart-empty">
            <el-icon :size="40" color="#dcdfe6"><DataLine /></el-icon>
            <span>{{ $t('aiAutomation.dashboard.noData') }}</span>
          </div>
        </div>
      </div>
      <div class="chart-card platform-card">
        <div class="chart-card__header">
          <span class="chart-card__title">{{ $t('aiAutomation.dashboard.platformDist') }}</span>
        </div>
        <div class="chart-card__body">
          <div ref="platformChartRef" class="chart-container"></div>
          <div v-if="!platformStats" class="chart-empty">
            <el-icon :size="40" color="#dcdfe6"><DataAnalysis /></el-icon>
            <span>{{ $t('aiAutomation.dashboard.noData') }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 下方：失败Top10表格 -->
    <div class="chart-card top-failed-card" v-if="statsData?.top_failed?.length">
      <div class="chart-card__header">
        <span class="chart-card__title">{{ $t('aiAutomation.dashboard.topFailed') }}</span>
      </div>
      <div class="chart-card__body">
        <el-table :data="statsData.top_failed" size="small" stripe>
          <el-table-column prop="case_name" :label="$t('aiAutomation.dashboard.caseName')" min-width="200" show-overflow-tooltip />
          <el-table-column prop="total" :label="$t('aiAutomation.dashboard.totalExec')" width="80" align="center" />
          <el-table-column prop="passed" :label="$t('aiAutomation.dashboard.passed')" width="70" align="center">
            <template #default="{ row }">
              <span style="color:#67c23a">{{ row.passed }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="failed" :label="$t('aiAutomation.dashboard.failed')" width="70" align="center">
            <template #default="{ row }">
              <span style="color:#f56c6c">{{ row.failed }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="pass_rate" :label="$t('aiAutomation.dashboard.passRate')" width="120" align="center">
            <template #default="{ row }">
              <el-progress :percentage="row.pass_rate" :stroke-width="6"
                :color="row.pass_rate >= 80 ? '#67c23a' : row.pass_rate >= 50 ? '#e6a23c' : '#f56c6c'"
                style="width:90px" />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { getMidsceneStatistics, getAiProjects } from '@/api/ui_automation'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { VideoPlay, CircleCheck, CircleClose, Timer, Loading, DataLine, DataAnalysis } from '@element-plus/icons-vue'

const { t } = useI18n()

const projectId = ref(null)
const platform = ref('all')
const projectList = ref([])
const statsData = ref(null)
const platformStats = ref(null)

const trendChartRef = ref(null)
const platformChartRef = ref(null)
let trendChartInstance = null
let platformChartInstance = null

// 加载项目列表
async function loadProjects() {
  try {
    const res = await getAiProjects()
    projectList.value = res.data?.results || res.data || []
  } catch { projectList.value = [] }
}

// 加载统计
async function loadAllStats() {
  await Promise.all([loadStatistics(), loadPlatformStats()])
}

async function loadStatistics() {
  try {
    const params = {}
    if (projectId.value) params.project_id = projectId.value
    if (platform.value !== 'all') params.platform = platform.value
    const res = await getMidsceneStatistics(params)
    statsData.value = res.data || null
    await nextTick()
    renderTrendChart()
  } catch {
    statsData.value = null
  }
}

async function loadPlatformStats() {
  try {
    const params = {}
    if (projectId.value) params.project_id = projectId.value
    const [webRes, appRes] = await Promise.all([
      getMidsceneStatistics({ ...params, platform: 'web' }),
      getMidsceneStatistics({ ...params, platform: 'app' })
    ])
    const webData = webRes.data
    const appData = appRes.data
    platformStats.value = { web: webData, app: appData }
    await nextTick()
    renderPlatformChart()
  } catch {
    platformStats.value = null
  }
}

// 渲染趋势图
function renderTrendChart() {
  if (!trendChartRef.value || !statsData.value?.trend?.length) return
  if (trendChartInstance) { trendChartInstance.dispose(); trendChartInstance = null }
  trendChartInstance = echarts.init(trendChartRef.value)
  const trend = statsData.value.trend
  const dates = trend.map(d => d.date.slice(5))
  trendChartInstance.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: [t('aiAutomation.dashboard.passed'), t('aiAutomation.dashboard.failed')], top: 4, right: 10, textStyle: { fontSize: 12 } },
    grid: { top: 36, right: 16, bottom: 28, left: 44 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 11, color: '#909399' }, axisTick: { show: false }, axisLine: { lineStyle: { color: '#ebeef5' } } },
    yAxis: { type: 'value', minInterval: 1, axisLabel: { fontSize: 11, color: '#909399' }, splitLine: { lineStyle: { color: '#f0f2f5' } } },
    series: [
      { name: t('aiAutomation.dashboard.passed'), type: 'bar', stack: 'total', data: trend.map(d => d.passed), itemStyle: { color: '#67c23a' }, barMaxWidth: 16 },
      { name: t('aiAutomation.dashboard.failed'), type: 'bar', stack: 'total', data: trend.map(d => d.failed), itemStyle: { color: '#f56c6c', borderRadius: [2, 2, 0, 0] }, barMaxWidth: 16 },
    ]
  })
}

// 渲染平台分布饼图
function renderPlatformChart() {
  if (!platformChartRef.value || !platformStats.value) return
  if (platformChartInstance) { platformChartInstance.dispose(); platformChartInstance = null }
  platformChartInstance = echarts.init(platformChartRef.value)
  const web = platformStats.value.web
  const app = platformStats.value.app
  platformChartInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 4, textStyle: { fontSize: 12 } },
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      center: ['50%', '45%'],
      label: { show: true, formatter: '{b}\n{d}%', fontSize: 12 },
      data: [
        { value: web?.total || 0, name: t('aiAutomation.dashboard.web'), itemStyle: { color: '#409eff' } },
        { value: app?.total || 0, name: t('aiAutomation.dashboard.app'), itemStyle: { color: '#67c23a' } },
      ]
    }]
  })
}

function handleResize() {
  trendChartInstance?.resize()
  platformChartInstance?.resize()
}

onMounted(() => {
  loadProjects()
  loadAllStats()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChartInstance?.dispose()
  platformChartInstance?.dispose()
})
</script>

<style lang="scss" scoped>
.ai-dashboard {
  height: calc(100vh - 100px);
  overflow-y: auto;
  padding: 20px;
  &::-webkit-scrollbar { width: 0; }
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .page-title {
    font-size: 18px;
    font-weight: 600;
    color: #303133;
  }

  .header-right {
    display: flex;
    gap: 12px;
    align-items: center;
  }
}

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 14px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px 20px;
  transition: box-shadow 0.2s;

  &:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }

  .stat-card__icon {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .stat-card__value {
    font-size: 22px;
    font-weight: 700;
    color: #303133;
    line-height: 1.2;
  }

  .stat-card__label {
    font-size: 12px;
    color: #909399;
    margin-top: 2px;
  }
}

/* 图表卡片 */
.charts-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.chart-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;

  .chart-card__header {
    padding: 14px 20px 0;
    .chart-card__title {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
    }
  }

  .chart-card__body {
    padding: 12px 16px 16px;
    position: relative;
  }
}

.trend-card { flex: 3; }
.platform-card { flex: 2; }

.chart-container {
  width: 100%;
  height: 280px;
}

.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 280px;
  color: #c0c4cc;
  gap: 8px;
  font-size: 13px;
}

/* Top10表格 */
.top-failed-card {
  .chart-card__body { padding: 0 16px 16px; }
}
</style>
