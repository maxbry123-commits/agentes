<template>
  <div class="space-y-6">
    <!-- 顶部统计卡片 -->
    <div class="grid grid-cols-4 gap-6">
      <StatCard
        title="活跃目标"
        :value="stats.activeTargets"
        :change="stats.activeTargetsChange"
        :trend-points="stats.activeTargetsTrend"
        icon="Target"
        color="blue"
      />
      <StatCard
        title="扫描任务"
        :value="stats.scanTasks"
        :change="stats.scanTasksChange"
        :trend-points="stats.scanTasksTrend"
        icon="Radar"
        color="purple"
      />
      <StatCard
        title="发现漏洞"
        :value="stats.vulnerabilities"
        :change="stats.vulnerabilitiesChange"
        :trend-points="stats.vulnerabilitiesTrend"
        icon="Bug"
        color="red"
      />
      <StatCard
        title="生成报告"
        :value="stats.reports"
        :change="stats.reportsChange"
        :trend-points="stats.reportsTrend"
        icon="FileText"
        color="green"
      />
    </div>

    <!-- 主内容区域 -->
    <div class="grid grid-cols-3 gap-6">
      <!-- 左侧：测试活动图表 -->
      <div class="col-span-2 space-y-6">
        <!-- 活动趋势图 -->
        <div class="bg-dark-800 rounded-xl p-6 border border-dark-500 card-hover">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-semibold text-white">测试活动趋势</h3>
            <div class="flex gap-2">
              <t-button
                v-for="option in trendRangeOptions"
                :key="option.value"
                size="small"
                :variant="selectedTrendRange === option.value ? 'base' : 'outline'"
                @click="selectedTrendRange = option.value"
              >
                {{ option.label }}
              </t-button>
            </div>
          </div>
          <ActivityChart :data="activityData" />
        </div>

        <!-- 最近扫描任务 -->
        <div class="bg-dark-800 rounded-xl p-6 border border-dark-500 card-hover">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-semibold text-white">最近扫描任务</h3>
            <t-button variant="text" size="small" @click="router.push('/scan')">
              查看全部 <ChevronRight class="w-4 h-4" />
            </t-button>
          </div>
          <RecentScansTable :scans="recentScans" />
        </div>
      </div>

      <!-- 右侧：漏洞分布与风险摘要 -->
      <div>
        <div class="bg-dark-800 rounded-xl p-6 border border-dark-500 card-hover h-full min-h-[34rem] flex flex-col">
          <div class="flex items-start justify-between gap-4 mb-6">
            <div>
              <h3 class="text-lg font-semibold text-white">漏洞分布</h3>
              <p class="text-sm text-gray-400 mt-1">显示真实历史漏洞等级与高价值汇总信息</p>
            </div>
            <div class="text-right">
              <div class="text-3xl font-bold text-white">{{ stats.vulnerabilities }}</div>
              <div class="text-xs text-gray-400">累计漏洞</div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 mb-6">
            <button
              class="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-left transition-colors hover:border-red-400/60 hover:bg-red-500/15"
              @click="jumpToVulnerabilities(['critical', 'high'])"
            >
              <div class="text-xs text-red-200/80">高风险</div>
              <div class="mt-1 text-xl font-semibold text-white">{{ highRiskCount }}</div>
              <div class="text-xs text-gray-400">严重 + 高危</div>
            </button>
            <button
              class="rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-4 py-3 text-left transition-colors hover:border-cyan-400/60 hover:bg-cyan-500/15"
              @click="router.push('/reports')"
            >
              <div class="text-xs text-cyan-200/80">成功报告</div>
              <div class="mt-1 text-xl font-semibold text-white">{{ stats.reports }}</div>
              <div class="text-xs text-gray-400">已生成渗透报告</div>
            </button>
          </div>

          <div class="flex-1 flex flex-col">
            <VulnDistributionChart :data="vulnDistribution" />
            <div class="mt-4 grid grid-cols-2 gap-3">
              <button
                v-for="item in severityQuickFilters"
                :key="item.value"
                class="rounded-lg border px-4 py-3 text-left transition-colors"
                :class="item.className"
                @click="jumpToVulnerabilities(item.values)"
              >
                <div class="text-xs text-slate-300">{{ item.label }}</div>
                <div class="mt-1 text-lg font-semibold text-white">{{ item.count }}</div>
              </button>
            </div>
            <div class="mt-6 space-y-3">
              <div class="flex items-center justify-between rounded-lg border border-dark-500 bg-dark-700/50 px-4 py-3">
                <span class="text-sm text-gray-300">最近 7 天扫描任务</span>
                <span class="text-sm font-semibold text-white">{{ recentTaskCount }}</span>
              </div>
              <div class="flex items-center justify-between rounded-lg border border-dark-500 bg-dark-700/50 px-4 py-3">
                <span class="text-sm text-gray-300">最近 7 天新增漏洞</span>
                <span class="text-sm font-semibold text-white">{{ recentVulnerabilityCount }}</span>
              </div>
              <div class="flex items-center justify-between rounded-lg border border-dark-500 bg-dark-700/50 px-4 py-3">
                <span class="text-sm text-gray-300">覆盖目标数</span>
                <span class="text-sm font-semibold text-white">{{ stats.activeTargets }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部：时间线 -->
    <div class="bg-dark-800 rounded-xl p-6 border border-dark-500 card-hover">
      <h3 class="text-lg font-semibold text-white mb-6">实时活动日志</h3>
      <ActivityTimeline :activities="recentActivities" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronRight } from 'lucide-vue-next'
import StatCard from '../components/StatCard.vue'
import ActivityChart from '../components/ActivityChart.vue'
import RecentScansTable from '../components/RecentScansTable.vue'
import VulnDistributionChart from '../components/VulnDistributionChart.vue'
import ActivityTimeline from '../components/ActivityTimeline.vue'
import { scanApi, vulnerabilityApi, reportApi, activityApi } from '../api'

const router = useRouter()

// 统计数据
const stats = ref({
  activeTargets: 0,
  activeTargetsChange: 0,
  activeTargetsTrend: [] as number[],
  scanTasks: 0,
  scanTasksChange: 0,
  scanTasksTrend: [] as number[],
  vulnerabilities: 0,
  vulnerabilitiesChange: 0,
  vulnerabilitiesTrend: [] as number[],
  reports: 0,
  reportsChange: 0,
  reportsTrend: [] as number[],
})

// 最近扫描任务
const recentScans = ref<any[]>([])

// 漏洞分布
const vulnDistribution = ref([
  { name: '严重', value: 0, color: '#ef4444' },
  { name: '高危', value: 0, color: '#f59e0b' },
  { name: '中危', value: 0, color: '#eab308' },
  { name: '低危', value: 0, color: '#22c55e' },
])

// 最近活动
const recentActivities = ref<any[]>([])
const allTasks = ref<any[]>([])
const allReports = ref<any[]>([])
const selectedTrendRange = ref<'day' | 'week' | 'month'>('day')

// 刷新定时器
let refreshTimer: number | null = null
const trendRangeOptions = [
  { label: '日', value: 'day' as const },
  { label: '周', value: 'week' as const },
  { label: '月', value: 'month' as const },
]

const startOfWeek = (date: Date) => {
  const next = new Date(date)
  next.setHours(0, 0, 0, 0)
  const day = next.getDay()
  const diff = day === 0 ? 6 : day - 1
  next.setDate(next.getDate() - diff)
  return next
}

const startOfMonth = (date: Date) => {
  const next = new Date(date)
  next.setHours(0, 0, 0, 0)
  next.setDate(1)
  return next
}

const getTaskNormalizedResult = (task: any) => {
  if (task?.normalized_result && typeof task.normalized_result === 'object') {
    return task.normalized_result
  }

  const vulnList = task?.result?.results?.vuln?.data?.vulnerabilities
  return {
    vuln: {
      items: Array.isArray(vulnList) ? vulnList : [],
    },
  }
}

const getTaskVulnerabilities = (task: any) => {
  const normalized = getTaskNormalizedResult(task)
  return Array.isArray(normalized?.vuln?.items) ? normalized.vuln.items : []
}

const buildActivityData = (tasks: any[], range: 'day' | 'week' | 'month') => {
  const buckets = new Map<string, { scans: number; vulns: number; sortValue: number }>()
  const now = new Date()
  const bucketCount = range === 'day' ? 7 : range === 'week' ? 8 : 6

  const buildLabel = (date: Date) => {
    if (range === 'day') {
      return `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    }
    if (range === 'week') {
      const start = startOfWeek(date)
      const end = new Date(start)
      end.setDate(end.getDate() + 6)
      return `${String(start.getMonth() + 1).padStart(2, '0')}/${String(start.getDate()).padStart(2, '0')}-${String(end.getMonth() + 1).padStart(2, '0')}/${String(end.getDate()).padStart(2, '0')}`
    }
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
  }

  for (let offset = bucketCount - 1; offset >= 0; offset -= 1) {
    const bucketDate = new Date(now)
    if (range === 'day') {
      bucketDate.setHours(0, 0, 0, 0)
      bucketDate.setDate(bucketDate.getDate() - offset)
    } else if (range === 'week') {
      const weekStart = startOfWeek(bucketDate)
      weekStart.setDate(weekStart.getDate() - offset * 7)
      bucketDate.setTime(weekStart.getTime())
    } else {
      const monthStart = startOfMonth(bucketDate)
      monthStart.setMonth(monthStart.getMonth() - offset)
      bucketDate.setTime(monthStart.getTime())
    }
    const label = buildLabel(bucketDate)
    buckets.set(label, { scans: 0, vulns: 0, sortValue: bucketDate.getTime() })
  }

  tasks.forEach((task: any) => {
    const rawDate = task.created_at || task.started_at || task.completed_at
    if (!rawDate) return

    const date = new Date(rawDate)
    if (Number.isNaN(date.getTime())) return

    const label = buildLabel(date)
    const bucket = buckets.get(label)
    if (!bucket) return
    bucket.scans += 1

    bucket.vulns += getTaskVulnerabilities(task).length
  })

  const labels = Array.from(buckets.entries())
    .sort((a, b) => a[1].sortValue - b[1].sortValue)
    .map(([label]) => label)
  return {
    labels,
    scans: labels.map(label => buckets.get(label)?.scans || 0),
    vulns: labels.map(label => buckets.get(label)?.vulns || 0),
  }
}

const activityData = computed(() => buildActivityData(allTasks.value, selectedTrendRange.value))

const buildDailyStatSeries = (tasks: any[], reports: any[]) => {
  const buckets = new Map<string, {
    scans: number
    vulns: number
    reports: number
    targets: Set<string>
  }>()

  const ensureBucket = (label: string) => {
    const existing = buckets.get(label)
    if (existing) return existing
    const created = {
      scans: 0,
      vulns: 0,
      reports: 0,
      targets: new Set<string>(),
    }
    buckets.set(label, created)
    return created
  }

  const normalizeLabel = (value: string | undefined) => {
    if (!value) return null
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return null
    return `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  }

  tasks.forEach((task: any) => {
    const label = normalizeLabel(task.completed_at || task.created_at || task.started_at)
    if (!label) return

    const bucket = ensureBucket(label)
    bucket.scans += 1
    if (task.target) {
      bucket.targets.add(task.target)
    }

    bucket.vulns += getTaskVulnerabilities(task).length
  })

  reports.forEach((report: any) => {
    const label = normalizeLabel(report.created_at)
    if (!label) return
    ensureBucket(label).reports += 1
  })

  const labels = Array.from(buckets.keys()).sort().slice(-7)
  return {
    labels,
    activeTargetsTrend: labels.map(label => buckets.get(label)?.targets.size || 0),
    scanTasksTrend: labels.map(label => buckets.get(label)?.scans || 0),
    vulnerabilitiesTrend: labels.map(label => buckets.get(label)?.vulns || 0),
    reportsTrend: labels.map(label => buckets.get(label)?.reports || 0),
  }
}

const getWindowStart = (date: Date, days: number) => {
  const next = new Date(date)
  next.setHours(0, 0, 0, 0)
  next.setDate(next.getDate() - days)
  return next
}

const calculateChangePercent = (current: number, previous: number) => {
  if (previous <= 0) {
    return current > 0 ? 100 : 0
  }
  return Math.round(((current - previous) / previous) * 100)
}

const recentTaskCount = computed(() => {
  const now = new Date()
  const recentStart = getWindowStart(now, 7)
  return allTasks.value.filter((task: any) => {
    const value = task.completed_at || task.created_at || task.started_at
    if (!value) return false
    const date = new Date(value)
    return !Number.isNaN(date.getTime()) && date >= recentStart && date <= now
  }).length
})

const recentVulnerabilityCount = computed(() => {
  const now = new Date()
  const recentStart = getWindowStart(now, 7)
  return allTasks.value.reduce((sum: number, task: any) => {
    const value = task.completed_at || task.created_at || task.started_at
    if (!value) return sum
    const date = new Date(value)
    if (Number.isNaN(date.getTime()) || date < recentStart || date > now) {
      return sum
    }
    return sum + getTaskVulnerabilities(task).length
  }, 0)
})

const highRiskCount = computed(() =>
  vulnDistribution.value
    .filter(item => item.name === '严重' || item.name === '高危')
    .reduce((sum, item) => sum + item.value, 0)
)

const severityQuickFilters = computed(() => [
  {
    label: '严重漏洞',
    value: 'critical',
    values: ['critical'],
    count: vulnDistribution.value.find(item => item.name === '严重')?.value || 0,
    className: 'border-red-500/30 bg-red-500/10 hover:border-red-400/60 hover:bg-red-500/15',
  },
  {
    label: '高危漏洞',
    value: 'high',
    values: ['high'],
    count: vulnDistribution.value.find(item => item.name === '高危')?.value || 0,
    className: 'border-orange-500/30 bg-orange-500/10 hover:border-orange-400/60 hover:bg-orange-500/15',
  },
  {
    label: '中危漏洞',
    value: 'medium',
    values: ['medium'],
    count: vulnDistribution.value.find(item => item.name === '中危')?.value || 0,
    className: 'border-yellow-500/30 bg-yellow-500/10 hover:border-yellow-400/60 hover:bg-yellow-500/15',
  },
  {
    label: '低危漏洞',
    value: 'low',
    values: ['low'],
    count: vulnDistribution.value.find(item => item.name === '低危')?.value || 0,
    className: 'border-green-500/30 bg-green-500/10 hover:border-green-400/60 hover:bg-green-500/15',
  },
])

const jumpToVulnerabilities = (severities: string[]) => {
  if (!severities.length) {
    router.push('/vulnerabilities')
    return
  }
  router.push({ path: '/vulnerabilities', query: { severity: severities.join(',') } })
}

const buildStatsSummary = (tasks: any[], reports: any[], totalVulns: number) => {
  const now = new Date()
  const recentStart = getWindowStart(now, 7)
  const previousStart = getWindowStart(now, 14)
  const dailySeries = buildDailyStatSeries(tasks, reports)

  const parseDate = (value: string | undefined) => {
    if (!value) return null
    const parsed = new Date(value)
    return Number.isNaN(parsed.getTime()) ? null : parsed
  }

  const inRange = (date: Date | null, start: Date, end: Date) =>
    Boolean(date && date >= start && date < end)

  const currentTasks = tasks.filter((task: any) =>
    inRange(parseDate(task.completed_at || task.created_at || task.started_at), recentStart, now)
  )
  const previousTasks = tasks.filter((task: any) =>
    inRange(parseDate(task.completed_at || task.created_at || task.started_at), previousStart, recentStart)
  )

  const currentReports = reports.filter((report: any) =>
    inRange(parseDate(report.created_at), recentStart, now)
  )
  const previousReports = reports.filter((report: any) =>
    inRange(parseDate(report.created_at), previousStart, recentStart)
  )

  const currentTargets = new Set(
    currentTasks.map((task: any) => task.target).filter((target: string | undefined) => Boolean(target))
  )
  const previousTargets = new Set(
    previousTasks.map((task: any) => task.target).filter((target: string | undefined) => Boolean(target))
  )

  const countVulns = (taskList: any[]) =>
    taskList.reduce((sum: number, task: any) => {
      return sum + getTaskVulnerabilities(task).length
    }, 0)

  const currentVulns = countVulns(currentTasks)
  const previousVulns = countVulns(previousTasks)

  const allTargets = new Set(
    tasks.map((task: any) => task.target).filter((target: string | undefined) => Boolean(target))
  )

  return {
    activeTargets: allTargets.size,
    activeTargetsChange: calculateChangePercent(currentTargets.size, previousTargets.size),
    activeTargetsTrend: dailySeries.activeTargetsTrend,
    scanTasks: tasks.length,
    scanTasksChange: calculateChangePercent(currentTasks.length, previousTasks.length),
    scanTasksTrend: dailySeries.scanTasksTrend,
    vulnerabilities: totalVulns,
    vulnerabilitiesChange: calculateChangePercent(currentVulns, previousVulns),
    vulnerabilitiesTrend: dailySeries.vulnerabilitiesTrend,
    reports: reports.length,
    reportsChange: calculateChangePercent(currentReports.length, previousReports.length),
    reportsTrend: dailySeries.reportsTrend,
  }
}

// 加载数据
const loadData = async () => {
  try {
    // 加载扫描任务
    const tasksData = await scanApi.listTasks() as any
    allTasks.value = tasksData.tasks || []
    recentScans.value = (tasksData.tasks || []).slice(0, 5).map((task: any) => ({
      id: task.id,
      target: task.target,
      type: task.scan_type || '快速扫描',
      status: task.status,
      time: task.created_at || '-',
      progress: typeof task.progress === 'number'
        ? task.progress
        : task.status === 'completed'
          ? 100
          : task.status === 'running'
            ? 50
            : 0,
    }))

    // 加载漏洞统计
    const vulnStats = await vulnerabilityApi.getStats() as any
    const totalVulns = vulnStats.total || 0

    vulnDistribution.value = [
      { name: '严重', value: vulnStats.critical || 0, color: '#ef4444' },
      { name: '高危', value: vulnStats.high || 0, color: '#f59e0b' },
      { name: '中危', value: vulnStats.medium || 0, color: '#eab308' },
      { name: '低危', value: vulnStats.low || 0, color: '#22c55e' },
    ]

    // 加载报告列表
    const reportsData = await reportApi.list() as any
    allReports.value = reportsData.reports || []
    stats.value = buildStatsSummary(allTasks.value, allReports.value, totalVulns)

    // 加载活动日志
    const activityDataResult = await activityApi.list(10) as any
    recentActivities.value = activityDataResult.activities || []

  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

onMounted(() => {
  loadData()
  refreshTimer = window.setInterval(loadData, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>
