<template>
  <div class="space-y-5">
    <!-- 任务选择 -->
    <div class="obs-card">
      <div class="obs-card-body">
      <h3 class="obs-card-title mb-4 flex items-center gap-3">
        <GitBranch class="w-5 h-5 text-cyber-blue" />
        攻击链路
      </h3>
      <div class="grid grid-cols-3 gap-4">
        <t-select v-model="selectedTaskId" placeholder="选择已完成的任务" @change="loadAttackGraph">
          <t-option
            v-for="task in completedTasks"
            :key="task.id"
            :value="task.id"
            :label="`${task.target || task.id} - ${task.status}`"
          />
        </t-select>
        <t-button theme="primary" @click="generateFromTask" :loading="loading">
          <RefreshCw class="w-4 h-4 mr-2" />
          生成攻击图
        </t-button>
        <t-button variant="outline" @click="exportGraph">
          <Download class="w-4 h-4 mr-2" />
          导出报告
        </t-button>
      </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div v-if="attackGraph" class="grid grid-cols-5 gap-4">
      <div class="obs-card">
        <div class="p-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
            <CheckCircle class="w-5 h-5 text-green-400" />
          </div>
          <div>
            <div class="text-2xl font-bold text-white">{{ (summary.attack_success_rate * 100).toFixed(0) }}%</div>
            <div class="text-xs text-gray-400">攻击成功率</div>
          </div>
        </div>
        </div>
      </div>
      <div class="obs-card">
        <div class="p-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center">
            <Bug class="w-5 h-5 text-red-400" />
          </div>
          <div>
            <div class="text-2xl font-bold text-white">{{ exploitStats.total }}</div>
            <div class="text-xs text-gray-400">漏洞利用</div>
          </div>
        </div>
        </div>
      </div>
      <div class="obs-card">
        <div class="p-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
            <Target class="w-5 h-5 text-orange-400" />
          </div>
          <div>
            <div class="text-2xl font-bold text-white">{{ summary.compromised_assets || 0 }}</div>
            <div class="text-xs text-gray-400">沦陷资产</div>
          </div>
        </div>
        </div>
      </div>
      <div class="obs-card">
        <div class="p-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
            <GitBranch class="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <div class="text-2xl font-bold text-white">{{ attackChain.steps?.length || 0 }}</div>
            <div class="text-xs text-gray-400">攻击步骤</div>
          </div>
        </div>
        </div>
      </div>
      <div class="obs-card">
        <div class="p-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
            <Clock class="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <div class="text-2xl font-bold text-white">{{ formatDuration(summary.total_duration) }}</div>
            <div class="text-xs text-gray-400">持续时间</div>
          </div>
        </div>
        </div>
      </div>
    </div>

    <div v-if="attackGraph" class="obs-card">
      <div class="obs-card-header-plain">
      <h3 class="obs-card-title flex items-center gap-2">
        <GitBranch class="w-5 h-5 text-purple-400" />
        事件类型分布
      </h3>
      </div>
      <div class="obs-card-body pt-0">
      <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        <div
          v-for="item in eventTypeStats"
          :key="item.name"
          class="p-4 rounded-lg border border-slate-700/60 bg-slate-900/45 text-center"
        >
          <div class="text-2xl font-bold" :style="{ color: item.color }">{{ item.count }}</div>
          <div class="text-xs text-gray-400 mt-1">{{ item.label }}</div>
        </div>
      </div>
      </div>
    </div>

    <!-- 攻击链时间线 -->
    <div v-if="attackGraph && attackChain.steps?.length" class="obs-card">
      <div class="obs-card-header-plain">
      <h3 class="obs-card-title flex items-center gap-2">
        <Route class="w-5 h-5" />
        攻击链路
      </h3>
      </div>
      <div class="obs-card-body pt-0">
      <div class="relative">
        <!-- 时间线 -->
        <div class="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-700"></div>
        <div class="space-y-6">
          <div
            v-for="step in attackChain.steps"
            :key="step.id"
            class="relative pl-16"
          >
            <!-- 步骤标记 -->
            <div
              class="absolute left-3 w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold"
              :class="step.success ? 'bg-green-500' : 'bg-red-500'"
            >
              {{ step.order }}
            </div>
            <!-- 步骤卡片 -->
            <div class="p-4 bg-slate-900/45 rounded-lg border border-slate-700/60">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-3">
                  <t-tag :theme="getPhaseTheme(step.phase)" size="small">
                    {{ getPhaseName(step.phase) }}
                  </t-tag>
                  <span class="font-medium text-white">{{ step.action }}</span>
                </div>
                <t-tag :theme="step.success ? 'success' : 'danger'" size="small">
                  {{ step.success ? '成功' : '失败' }}
                </t-tag>
              </div>
              <div class="text-sm text-gray-400 mb-2">
                目标: {{ step.target }} | 技术: {{ step.technique }}
              </div>
              <div v-if="step.details" class="text-sm text-gray-300">
                {{ step.details }}
              </div>
              <div v-if="step.flag || step.endpoint" class="mt-3 flex flex-wrap gap-2">
                <t-tag v-if="step.flag" theme="success" size="small">
                  {{ step.flag }}
                </t-tag>
                <t-tag v-if="step.method || step.endpoint" theme="primary" size="small">
                  {{ step.method || 'GET' }} {{ step.endpoint || '' }}
                </t-tag>
              </div>
              <div v-if="hasPayload(step.payload)" class="mt-3 rounded-lg border border-slate-700/60 bg-slate-950/80 overflow-hidden">
                <div class="px-3 py-2 text-xs font-medium text-slate-300 border-b border-slate-700/60">
                  真实 Payload
                </div>
                <pre class="p-3 text-xs leading-6 text-cyan-200 overflow-x-auto whitespace-pre-wrap break-all">{{ formatPayload(step.payload) }}</pre>
              </div>
              <div v-if="step.evidence?.length" class="mt-2 flex flex-wrap gap-2">
                <t-tag v-for="(ev, i) in step.evidence" :key="i" size="small" theme="default">
                  {{ ev }}
                </t-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- 漏洞利用情况 -->
    <div v-if="attackGraph && vulnerabilityExploits.length" class="obs-card">
      <div class="obs-card-header">
        <h3 class="obs-card-title flex items-center gap-2">
          <Shield class="w-5 h-5" />
          漏洞利用情况
        </h3>
        <div class="flex gap-2">
          <t-tag theme="danger">Critical: {{ severityCounts.critical }}</t-tag>
          <t-tag theme="warning">High: {{ severityCounts.high }}</t-tag>
          <t-tag theme="primary">Medium: {{ severityCounts.medium }}</t-tag>
        </div>
      </div>
      <div class="obs-card-body pt-0">
      <t-table :data="vulnerabilityExploits" :columns="exploitColumns" row-key="id" hover>
        <template #severity="{ row }">
          <t-tag :theme="getSeverityTheme(row.severity)" size="small">
            {{ row.severity }}
          </t-tag>
        </template>
        <template #poc="{ row }">
          <div v-if="hasPayload(row.poc)" class="max-w-[320px] rounded border border-slate-700/60 bg-slate-950/80">
            <pre class="p-2 text-xs leading-5 text-cyan-200 overflow-x-auto whitespace-pre-wrap break-all">{{ formatPayload(row.poc) }}</pre>
          </div>
          <span v-else class="text-xs text-slate-500">无</span>
        </template>
        <template #success="{ row }">
          <t-tag :theme="row.success ? 'success' : 'danger'" size="small">
            {{ row.success ? '成功' : '失败' }}
          </t-tag>
        </template>
      </t-table>
      </div>
    </div>

    <!-- 修复建议 -->
    <div v-if="attackGraph && summary.recommendations?.length" class="obs-card">
      <div class="obs-card-header-plain">
      <h3 class="obs-card-title flex items-center gap-2">
        <Lightbulb class="w-5 h-5 text-yellow-400" />
        修复建议
      </h3>
      </div>
      <div class="obs-card-body pt-0">
      <div class="space-y-2">
        <div
          v-for="(rec, i) in summary.recommendations"
          :key="i"
          class="p-3 bg-slate-900/45 rounded-lg border border-slate-700/60 flex items-center gap-3"
        >
          <CheckCircle class="w-5 h-5 text-green-400" />
          <span class="text-gray-300">{{ rec }}</span>
        </div>
      </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  GitBranch, Target, Bug, Clock, Route, Shield,
  CheckCircle, Download, RefreshCw, Lightbulb
} from 'lucide-vue-next'
import { scanApi, sessionApi } from '../api'

interface TaskItem {
  id: string
  target?: string
  status: string
  session_id?: string
  normalized_result?: Record<string, any>
  result?: Record<string, any>
}

interface SessionEvent {
  event_type?: string
  type?: string
}

const selectedTaskId = ref('')
const loading = ref(false)
const attackGraph = ref<any>(null)
const completedTasks = ref<TaskItem[]>([])
const eventTypeCounts = ref<Record<string, number>>({})

const eventTypeMeta = [
  { name: 'round_started', label: '轮次', color: '#6366f1' },
  { name: 'message_sent', label: '消息', color: '#d946ef' },
  { name: 'tool_call_started', label: '工具', color: '#06b6d4' },
  { name: 'task_completed', label: '完成', color: '#22c55e' },
  { name: 'decision_finalized', label: '决策', color: '#10b981' },
  { name: 'session_failed', label: '异常', color: '#ef4444' },
]

const exploitColumns = [
  { colKey: 'vuln_name', title: '漏洞名称', width: '25%' },
  { colKey: 'target', title: '目标', width: '15%' },
  { colKey: 'severity', title: '严重程度', width: '12%' },
  { colKey: 'exploit_method', title: '利用方式', width: '16%' },
  { colKey: 'poc', title: 'Payload', width: '22%' },
  { colKey: 'success', title: '状态', width: '10%' },
  { colKey: 'impact', title: '影响', width: '20%' }
]

const attackChain = computed(() => attackGraph.value?.attack_chain || {})
const vulnerabilityExploits = computed(() => attackGraph.value?.vulnerability_exploits || [])
const summary = computed(() => attackGraph.value?.summary || {})

const exploitStats = computed(() => {
  const exploits = vulnerabilityExploits.value
  return {
    total: exploits.length,
    successful: exploits.filter((e: any) => e.success).length,
    failed: exploits.filter((e: any) => !e.success).length
  }
})

const severityCounts = computed(() => {
  const exploits = vulnerabilityExploits.value
  return {
    critical: exploits.filter((e: any) => e.severity === 'critical').length,
    high: exploits.filter((e: any) => e.severity === 'high').length,
    medium: exploits.filter((e: any) => e.severity === 'medium').length,
    low: exploits.filter((e: any) => e.severity === 'low').length
  }
})

const eventTypeStats = computed(() => {
  return eventTypeMeta.map(item => ({
    ...item,
    count: eventTypeCounts.value[item.name] || 0,
  }))
})

const loadCompletedTasks = async () => {
  try {
    const data = await scanApi.listTasks() as any
    completedTasks.value = (data.tasks || []).filter((t: TaskItem) =>
      t.status === 'completed' || t.status === 'failed'
    )
  } catch (error) {
    console.error('加载任务失败:', error)
  }
}

const loadEventTypeDistribution = async (taskId: string, taskData?: TaskItem | Record<string, any> | null) => {
  if (!taskId) {
    eventTypeCounts.value = {}
    return
  }

  try {
    const resolvedTask = taskData || await scanApi.getTask(taskId) as any
    const sessionId = resolvedTask?.session_id || resolvedTask?.result?.session_id
    const fallbackCounts = deriveEventTypeCountsFromTask(resolvedTask)

    if (!sessionId) {
      eventTypeCounts.value = fallbackCounts
      return
    }

    const res = await sessionApi.getEvents(sessionId, 300) as any
    const counts = Object.fromEntries(eventTypeMeta.map(item => [item.name, 0])) as Record<string, number>
    ;(res.events || []).forEach((event: SessionEvent) => {
      const type = event.event_type || event.type || ''
      if (type in counts) {
        counts[type] += 1
      }
    })

    const hasAnyRealEvent = Object.values(counts).some(count => count > 0)
    eventTypeCounts.value = hasAnyRealEvent ? counts : fallbackCounts
  } catch (error) {
    console.error('加载事件类型分布失败:', error)
    const resolvedTask = taskData || await scanApi.getTask(taskId) as any
    eventTypeCounts.value = deriveEventTypeCountsFromTask(resolvedTask)
  }
}

const loadAttackGraph = async () => {
  if (!selectedTaskId.value) {
    attackGraph.value = null
    eventTypeCounts.value = {}
    return
  }

  loading.value = true
  try {
    await loadEventTypeDistribution(selectedTaskId.value)
    const res = await fetch(`/api/attack-graph/${selectedTaskId.value}`)
    if (res.ok) {
      attackGraph.value = await res.json()
    }
  } catch (error) {
    console.error('加载攻击图失败:', error)
  } finally {
    loading.value = false
  }
}

const generateFromTask = async () => {
  if (!selectedTaskId.value) return

  loading.value = true
  try {
    const taskData = await scanApi.getTask(selectedTaskId.value) as any

    const res = await fetch('/api/attack-graph/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...taskData, task_id: selectedTaskId.value })
    })
    attackGraph.value = await res.json()
    await loadEventTypeDistribution(selectedTaskId.value, taskData)
  } catch (error) {
    console.error('生成攻击图失败:', error)
  } finally {
    loading.value = false
  }
}

const exportGraph = () => {
  if (!attackGraph.value) return
  const data = JSON.stringify(attackGraph.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `attack-graph-${selectedTaskId.value}.json`
  a.click()
}

const getPhaseTheme = (phase: string) => {
  const map: Record<string, string> = {
    recon: 'primary', vuln: 'warning', exploit: 'danger',
    post_exploit: 'warning', pivot: 'warning', report: 'success'
  }
  return map[phase] || 'default'
}

const getPhaseName = (phase: string) => {
  const map: Record<string, string> = {
    recon: '信息收集', vuln: '漏洞发现', exploit: '漏洞利用',
    post_exploit: '后渗透', pivot: '横向移动', report: '报告生成'
  }
  return map[phase] || phase
}

const getSeverityTheme = (severity: string) => {
  const map: Record<string, string> = {
    critical: 'danger', high: 'warning', medium: 'warning', low: 'primary'
  }
  return map[severity] || 'default'
}

const formatDuration = (seconds: number) => {
  if (!seconds) return '0s'
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
}

const deriveEventTypeCountsFromTask = (task: any) => {
  const counts = Object.fromEntries(eventTypeMeta.map(item => [item.name, 0])) as Record<string, number>
  const normalized = task?.normalized_result || {}
  const result = task?.result || task || {}
  const results = result?.results || {}
  const timeline = Array.isArray(result?.timeline) ? result.timeline : []
  const errors = Array.isArray(result?.errors) ? result.errors : []

  const completedPhases = ['recon', 'vuln', 'exploit', 'report'].filter((phase) => Boolean(results?.[phase]?.success))
  const attempts = Array.isArray(normalized?.exploit?.attempts)
    ? normalized.exploit.attempts
    : (Array.isArray(results?.exploit?.data?.results?.attempts) ? results.exploit.data.results.attempts : [])
  const successful = Array.isArray(normalized?.exploit?.successful_attempts)
    ? normalized.exploit.successful_attempts
    : (Array.isArray(results?.exploit?.data?.results?.successful) ? results.exploit.data.results.successful : [])
  const exploitPlanSteps = Array.isArray(results?.exploit?.data?.exploit_plan?.steps)
    ? results.exploit.data.exploit_plan.steps.length
    : 0
  const vulnPriorities = Array.isArray(results?.vuln?.data?.scan_plan?.priority_vulns)
    ? results.vuln.data.scan_plan.priority_vulns.length
    : 0

  const visitedUrls = Array.isArray(normalized?.exploit?.visited_urls)
    ? normalized.exploit.visited_urls
    : attempts.flatMap((attempt: any) =>
        Array.isArray(attempt?.details?.visited_urls) ? attempt.details.visited_urls : []
      )

  counts.round_started = completedPhases.length || timeline.filter((item: any) => ['recon', 'vuln', 'exploit', 'report'].includes(item?.phase)).length
  counts.message_sent = exploitPlanSteps + vulnPriorities + counts.round_started
  counts.tool_call_started = visitedUrls.length || attempts.length
  counts.task_completed = completedPhases.length
  counts.decision_finalized = completedPhases.length + (successful.length > 0 ? 1 : 0)
  counts.session_failed = errors.length

  return counts
}

const hasPayload = (payload: unknown) => {
  if (payload === null || payload === undefined) return false
  if (typeof payload === 'string') return payload.trim().length > 0
  if (Array.isArray(payload)) return payload.length > 0
  if (typeof payload === 'object') return Object.keys(payload as Record<string, unknown>).length > 0
  return true
}

const formatPayload = (payload: unknown) => {
  if (payload === null || payload === undefined) return ''
  if (typeof payload === 'string') {
    const trimmed = payload.trim()
    if (!trimmed) return ''
    try {
      return JSON.stringify(JSON.parse(trimmed), null, 2)
    } catch (_error) {
      return trimmed
    }
  }
  try {
    return JSON.stringify(payload, null, 2)
  } catch (_error) {
    return String(payload)
  }
}

onMounted(() => {
  loadCompletedTasks()
})
</script>
