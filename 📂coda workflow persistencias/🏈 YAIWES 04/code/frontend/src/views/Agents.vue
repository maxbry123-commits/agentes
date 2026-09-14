<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-white">智能体团队</h2>
        <p class="text-slate-400 mt-1">观测智能体协作轮次、会话消息和工具调用过程</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700">
          <div class="w-2 h-2 rounded-full" :class="liveConnected ? 'bg-green-500' : 'bg-amber-500'"></div>
          <span class="text-sm text-slate-300">{{ liveConnected ? '实时订阅中' : '轮询同步中' }}</span>
        </div>
        <t-button theme="primary" size="small" @click="manualRefresh">
          刷新数据
        </t-button>
      </div>
    </div>

    <div class="grid grid-cols-5 gap-4">
      <div
        v-for="agent in agents"
        :key="agent.name"
        class="overflow-hidden rounded-xl border transition-colors duration-200"
        :class="[
          agent.enabled ? 'bg-slate-800/80 border-slate-600' : 'bg-slate-800/40 border-slate-700/50 opacity-60'
        ]"
      >
        <div class="h-1.5 w-full" :style="{ background: `linear-gradient(90deg, ${agent.color}, ${agent.color}80)` }"></div>

        <div class="p-5">
          <div class="flex items-center justify-between mb-4">
            <div
              class="w-14 h-14 rounded-xl flex items-center justify-center text-2xl"
              :style="{
                background: `linear-gradient(135deg, ${agent.color}40, ${agent.color}20)`,
              }"
            >
              <component :is="agent.icon" class="w-7 h-7" :style="{ color: agent.color }" />
            </div>
            <div class="flex flex-col items-end">
              <span
                class="w-3 h-3 rounded-full mb-1"
                :class="agent.status === 'running' ? 'bg-green-500' : 'bg-slate-500'"
              ></span>
              <span class="text-[10px] text-slate-400 uppercase tracking-wider">
                {{ agent.status === 'running' ? 'Active' : 'Idle' }}
              </span>
            </div>
          </div>

          <h4 class="text-white font-semibold text-lg mb-1">{{ agent.display_name }}</h4>
          <p class="text-xs text-slate-400 mb-3">{{ agent.role }}</p>

          <div class="flex items-center gap-2 text-xs">
            <Cpu class="w-3 h-3 text-slate-500" />
            <span class="text-slate-400">{{ agent.model_provider || 'DeepSeek' }}</span>
          </div>

          <div class="mt-4 pt-3 border-t border-slate-700/50 flex items-center justify-between">
            <span class="text-xs text-slate-500">活动次数</span>
            <span class="text-sm font-medium text-white">{{ getActivityCount(agent.name) }}</span>
          </div>
        </div>

      </div>
    </div>

    <div class="grid grid-cols-3 gap-5 items-start">
      <div class="col-span-2 space-y-5">
        <div class="obs-card">
          <div class="obs-card-body py-4">
          <div v-if="currentSession" class="flex items-center justify-between gap-4 flex-wrap">
            <div class="flex items-center gap-2 text-slate-200 min-w-0">
              <Layers3 class="w-4 h-4 text-cyan-400 flex-shrink-0" />
              <span class="text-sm text-slate-400">当前会话</span>
              <span class="text-sm text-white truncate max-w-[24rem]">{{ currentSession.target || '未知目标' }}</span>
              <span class="text-xs text-slate-500">{{ simplifyId(currentSession.session_id) }}</span>
            </div>
            <div class="flex items-center gap-3 flex-wrap text-sm">
              <div class="rounded-lg border border-slate-700/60 bg-slate-900/40 px-3 py-2 text-slate-300">
                轮次 <span class="ml-1 font-semibold text-cyan-300">{{ currentSession.round_count }}</span>
              </div>
              <div class="rounded-lg border border-slate-700/60 bg-slate-900/40 px-3 py-2 text-slate-300">
                事件 <span class="ml-1 font-semibold text-emerald-300">{{ currentSession.event_count }}</span>
              </div>
            </div>
          </div>
          <div v-else class="text-sm text-slate-500">
            暂无会话数据，请先启动扫描任务。
          </div>
          </div>
        </div>

        <div class="obs-card overflow-hidden">
          <div class="obs-card-header flex-wrap">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-slate-700/70 flex items-center justify-center flex-shrink-0">
                <Activity class="w-4 h-4 text-cyan-400" />
              </div>
              <div>
                <h3 class="obs-card-title">会话事件流</h3>
                <p class="obs-card-desc">当前会话的轮次、消息、决策与工具调用</p>
              </div>
            </div>
            <div class="flex items-center gap-3 flex-wrap">
              <t-select
                v-model="selectedSessionId"
                placeholder="选择会话"
                size="small"
                class="w-56"
                @change="handleSessionChange"
              >
                <t-option
                  v-for="session in sessions"
                  :key="session.session_id"
                  :value="session.session_id"
                  :label="`${session.target || '未知目标'} (${simplifyId(session.session_id)})`"
                />
              </t-select>
              <t-button
                variant="outline"
                size="small"
                :disabled="!selectedSessionId"
                @click="openSessionDetail"
              >
                查看详情
              </t-button>
              <t-select v-model="agentFilter" placeholder="筛选智能体" clearable size="small" class="w-36">
                <t-option v-for="agent in agents" :key="agent.name" :value="agent.name" :label="agent.display_name" />
              </t-select>
              <t-select v-model="typeFilter" placeholder="活动类型" clearable size="small" class="w-36">
                <t-option v-for="option in typeFilterOptions" :key="option.value" :value="option.value" :label="option.label" />
              </t-select>
            </div>
          </div>

          <div class="px-5 py-3 border-b border-slate-700/60 bg-slate-900/30 flex items-center gap-3 flex-wrap text-xs">
            <span class="px-2 py-1 rounded bg-slate-700/60 text-slate-200">
              当前会话: {{ selectedSessionLabel }}
            </span>
            <span class="px-2 py-1 rounded bg-indigo-500/15 text-indigo-300">
              轮次 {{ rounds.length }}
            </span>
            <span class="px-2 py-1 rounded bg-cyan-500/15 text-cyan-300">
              事件 {{ activities.length }}
            </span>
            <span class="px-2 py-1 rounded bg-emerald-500/15 text-emerald-300">
              消息 {{ totalMessages }}
            </span>
          </div>

          <div class="obs-card-body max-h-[700px] overflow-y-auto">
            <AgentActivityFeed :activities="filteredActivities" />
          </div>
        </div>
      </div>

      <div class="space-y-5">
        <div class="obs-card">
          <div class="obs-card-header-plain">
          <h3 class="obs-card-title flex items-center gap-2">
            <GitBranch class="w-4 h-4 text-cyan-400" />
            协作轮次
          </h3>
          </div>
          <div class="obs-card-body pt-0">
          <div v-if="rounds.length" class="space-y-3 max-h-[280px] overflow-y-auto">
            <button
              v-for="round in rounds"
              :key="round.round_id"
              class="w-full text-left p-3 rounded-lg border transition-colors obs-subcard"
              :class="selectedRoundId === round.round_id ? 'border-cyan-500/60 bg-cyan-500/10' : 'border-slate-700 bg-slate-900/40 hover:border-slate-600'"
              @click="selectRound(round.round_id)"
            >
              <div class="flex items-center justify-between gap-3">
                <span class="text-sm font-medium text-white">{{ round.goal }}</span>
                <span class="text-[10px] px-2 py-0.5 rounded" :class="round.status === 'completed' ? 'bg-green-500/20 text-green-400' : 'bg-amber-500/20 text-amber-400'">
                  {{ round.status }}
                </span>
              </div>
              <p class="text-xs text-slate-400 mt-1">{{ round.phase }}</p>
              <p class="text-[11px] text-slate-500 mt-2">参与者: {{ round.participants?.join('、') || '-' }}</p>
            </button>
          </div>
          <div v-else class="text-sm text-slate-500">
            当前会话尚未生成协作轮次。
          </div>
          </div>
        </div>

        <div class="obs-card">
          <div class="obs-card-header-plain">
          <h3 class="obs-card-title flex items-center gap-2">
            <MessagesSquare class="w-4 h-4 text-indigo-400" />
            当前轮消息
          </h3>
          </div>
          <div class="obs-card-body pt-0">
          <div v-if="selectedRoundMessages.length" class="space-y-3 max-h-[300px] overflow-y-auto">
            <div
              v-for="message in selectedRoundMessages"
              :key="message.message_id"
              class="p-3 rounded-lg bg-slate-900/50 border border-slate-700/60"
            >
              <div class="flex items-center gap-2 text-[11px] mb-2 flex-wrap">
                <span class="px-2 py-0.5 rounded bg-fuchsia-500/15 text-fuchsia-300">{{ message.message_type }}</span>
                <span class="text-slate-300">{{ message.sender }}</span>
                <ArrowRight class="w-3 h-3 text-slate-500" />
                <span class="text-slate-300">{{ message.receiver }}</span>
                <span class="text-slate-500 ml-auto">{{ formatTime(message.timestamp) }}</span>
              </div>
              <p class="text-sm text-slate-200 break-words">{{ message.content }}</p>
            </div>
          </div>
          <div v-else class="text-sm text-slate-500">
            选择一个协作轮次后可查看消息往返。
          </div>
          </div>
        </div>

        <div class="obs-card">
          <div class="obs-card-header-plain">
          <h3 class="obs-card-title flex items-center gap-2">
            <Wrench class="w-4 h-4 text-orange-400" />
            工具调用统计
          </h3>
          </div>
          <div class="obs-card-body pt-0">
          <div class="space-y-3">
            <div
              v-for="stat in toolCallStats"
              :key="stat.name"
              class="flex items-center gap-3"
            >
              <div class="flex-1">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-sm text-slate-300">{{ stat.name }}</span>
                  <span class="text-xs text-slate-400">{{ stat.count }} 次</span>
                </div>
                <div class="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    class="h-full rounded-full transition-all duration-500"
                    :style="{ width: stat.percentage + '%', background: 'linear-gradient(90deg, #0ea5e9, #06b6d4)' }"
                  ></div>
                </div>
              </div>
            </div>
            <div v-if="toolCallStats.length === 0" class="text-center py-4 text-slate-500 text-sm">
              暂无工具调用记录
            </div>
          </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Target, Bug, FileText, Wrench, Cpu, Activity, GitBranch, Shield, Layers3, MessagesSquare, ArrowRight } from 'lucide-vue-next'
import AgentActivityFeed from '../components/AgentActivityFeed.vue'
import { agentApi, sessionApi, createSessionEventsWebSocket } from '../api'
import { MessagePlugin } from 'tdesign-vue-next'

interface Agent {
  name: string
  display_name: string
  role: string
  status: string
  color: string
  icon: any
  model_provider?: string
  model_name?: string
  enabled?: boolean
}

interface ActivityItem {
  id: string
  agent: string
  type: string
  content: string
  details: Record<string, any>
  timestamp: string
  session_id?: string
  round_id?: string
}

interface SessionItem {
  session_id: string
  target: string
  created_at: string
  round_count: number
  event_count: number
}

interface RoundItem {
  round_id: string
  session_id: string
  phase: string
  goal: string
  participants: string[]
  status: string
  started_at: string
  ended_at?: string | null
  summary?: string
}

interface RoundMessage {
  message_id: string
  session_id: string
  round_id: string
  sender: string
  receiver: string
  message_type: string
  content: string
  payload?: Record<string, any>
  timestamp: string
}

const agents = ref<Agent[]>([
  { name: 'CoordinatorAgent', display_name: '协调者', role: '团队领导，任务分配与轮次收敛', status: 'idle', color: '#ef4444', icon: Shield },
  { name: 'ReconAgent', display_name: '侦察专家', role: '信息收集和目标侦察', status: 'idle', color: '#00d4ff', icon: Search },
  { name: 'VulnAgent', display_name: '漏洞分析师', role: '漏洞扫描和风险评估', status: 'idle', color: '#8b5cf6', icon: Bug },
  { name: 'ExploitAgent', display_name: '攻击专家', role: '漏洞利用和权限获取', status: 'idle', color: '#f59e0b', icon: Target },
  { name: 'ReportAgent', display_name: '报告专家', role: '生成渗透测试报告', status: 'idle', color: '#10b981', icon: FileText },
])
const router = useRouter()

const activities = ref<ActivityItem[]>([])
const sessions = ref<SessionItem[]>([])
const rounds = ref<RoundItem[]>([])
const roundMessages = ref<Record<string, RoundMessage[]>>({})
const selectedSessionId = ref('')
const selectedRoundId = ref('')
const agentFilter = ref('')
const typeFilter = ref('')
const liveConnected = ref(false)

let refreshTimer: number | null = null
let socket: WebSocket | null = null

const currentSession = computed(() =>
  sessions.value.find(session => session.session_id === selectedSessionId.value) || null
)

const selectedSessionLabel = computed(() => {
  if (!currentSession.value) return '未选择'
  return `${currentSession.value.target || '未知目标'} / ${simplifyId(currentSession.value.session_id)}`
})

const filteredActivities = computed(() => {
  let result = [...activities.value].sort((a, b) => {
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  })
  if (agentFilter.value) {
    result = result.filter(a => a.agent === agentFilter.value)
  }
  if (typeFilter.value) {
    result = result.filter(a => a.type === typeFilter.value)
  }
  return result
})

const typeFilterOptions = computed(() => {
  const uniqueTypes = Array.from(new Set(activities.value.map(item => item.type)))
  return uniqueTypes.map(type => ({
    value: type,
    label: getEventTypeLabel(type),
  }))
})

const selectedRoundMessages = computed(() => {
  return roundMessages.value[selectedRoundId.value] || []
})

const totalMessages = computed(() => {
  return Object.values(roundMessages.value).reduce((sum, items) => sum + items.length, 0)
})

const toolCallStats = computed(() => {
  const stats: Record<string, number> = {}
  activities.value
    .filter(a => ['tool_call', 'tool_call_started', 'tool_call_completed'].includes(a.type))
    .forEach(a => {
      const toolNames = []
      if (a.details?.tool) toolNames.push(a.details.tool)
      if (Array.isArray(a.details?.tools)) toolNames.push(...a.details.tools)
      toolNames.forEach((tool: string) => {
        stats[tool] = (stats[tool] || 0) + 1
      })
    })
  const maxCount = Math.max(...Object.values(stats), 1)
  return Object.entries(stats)
    .map(([name, count]) => ({ name, count, percentage: (count / maxCount) * 100 }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5)
})

const getActivityCount = (agentName: string): number => {
  return activities.value.filter(a => a.agent === agentName).length
}

const simplifyId = (value: string): string => {
  if (!value) return '-'
  return value.length > 18 ? `${value.slice(0, 8)}...${value.slice(-4)}` : value
}

const formatTime = (timestamp: string): string => {
  if (!timestamp) return '-'
  try {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return timestamp
  }
}

const getEventTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    round_started: '轮次开始',
    round_completed: '轮次完成',
    message_sent: '消息发送',
    message_received: '消息接收',
    task_started: '任务开始',
    task_completed: '任务完成',
    task_failed: '任务失败',
    tool_call_started: '工具开始',
    tool_call_completed: '工具完成',
    thinking_started: '开始分析',
    thinking_completed: '分析完成',
    thinking_failed: '分析失败',
    session_started: '会话开始',
    session_completed: '会话完成',
    session_failed: '会话失败',
    decision_finalized: '最终决策',
  }
  return labels[type] || type
}

const upsertActivity = (activity: ActivityItem) => {
  const normalized: ActivityItem = {
    ...activity,
    id: activity.id || (activity as any).event_id,
    content: activity.content || (activity as any).summary || '',
    type: activity.type || (activity as any).event_type || 'info',
    details: activity.details || {},
    session_id: activity.session_id || (activity as any).session_id,
    round_id: activity.round_id || (activity as any).round_id,
  }
  const existingIndex = activities.value.findIndex(item => item.id === normalized.id)
  if (existingIndex >= 0) {
    activities.value[existingIndex] = normalized
  } else {
    activities.value.unshift(normalized)
  }
  activities.value = [...activities.value]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 300)
}

const connectSessionSocket = () => {
  if (!selectedSessionId.value) return
  if (socket) {
    socket.close()
    socket = null
  }
  liveConnected.value = false
  socket = createSessionEventsWebSocket(selectedSessionId.value)
  socket.onopen = () => {
    liveConnected.value = true
  }
  socket.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data)
      const rawEvent = payload?.data
      if (!rawEvent) return
      upsertActivity({
        id: rawEvent.event_id,
        agent: rawEvent.agent,
        type: rawEvent.event_type,
        content: rawEvent.summary,
        details: rawEvent.details || {},
        timestamp: rawEvent.timestamp,
        session_id: rawEvent.session_id,
        round_id: rawEvent.round_id,
      })
      loadRounds(false)
      if (selectedRoundId.value) loadRoundMessages(selectedRoundId.value, false)
    } catch (error) {
      console.error('Failed to parse websocket event:', error)
    }
  }
  socket.onerror = () => {
    liveConnected.value = false
  }
  socket.onclose = () => {
    liveConnected.value = false
  }
}

const loadAgents = async () => {
  try {
    const res = await agentApi.getStatus() as any
    if (res.agents) {
      agents.value = agents.value.map(agent => {
        const found = res.agents.find((item: any) => item.name === agent.name)
        return found ? { ...agent, ...found, icon: agent.icon } : agent
      })
    }
  } catch (error) {
    console.error('Failed to load agents:', error)
  }
}

const loadSessions = async (showError = true) => {
  try {
    const res = await sessionApi.list() as any
    const nextSessions = (res.sessions || []).sort((a: SessionItem, b: SessionItem) => {
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })
    sessions.value = nextSessions
    if (!selectedSessionId.value && nextSessions.length > 0) {
      selectedSessionId.value = nextSessions[0].session_id
      await handleSessionChange()
    } else if (selectedSessionId.value && !nextSessions.find((item: SessionItem) => item.session_id === selectedSessionId.value) && nextSessions.length > 0) {
      selectedSessionId.value = nextSessions[0].session_id
      await handleSessionChange()
    }
  } catch (error) {
    console.error('Failed to load sessions:', error)
    if (showError) {
      MessagePlugin.warning('暂时无法获取交互会话列表')
    }
  }
}

const loadEvents = async (showError = false) => {
  if (!selectedSessionId.value) {
    activities.value = []
    return
  }
  try {
    const res = await sessionApi.getEvents(selectedSessionId.value, 200) as any
    activities.value = (res.events || []).map((event: any) => ({
      id: event.event_id,
      agent: event.agent,
      type: event.event_type,
      content: event.summary,
      details: event.details || {},
      timestamp: event.timestamp,
      session_id: event.session_id,
      round_id: event.round_id,
    }))
      .sort((a: ActivityItem, b: ActivityItem) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  } catch (error) {
    console.error('Failed to load events:', error)
    if (showError) MessagePlugin.error('会话事件加载失败')
  }
}

const loadRounds = async (autoSelect = true) => {
  if (!selectedSessionId.value) {
    rounds.value = []
    selectedRoundId.value = ''
    return
  }
  try {
    const res = await sessionApi.getRounds(selectedSessionId.value) as any
    rounds.value = (res.rounds || []).sort((a: RoundItem, b: RoundItem) => {
      return new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
    })
    if (autoSelect && rounds.value.length > 0) {
      const exists = rounds.value.find(item => item.round_id === selectedRoundId.value)
      if (!exists) {
        await selectRound(rounds.value[0].round_id)
      }
    }
  } catch (error) {
    console.error('Failed to load rounds:', error)
  }
}

const loadRoundMessages = async (roundId: string, showError = false) => {
  if (!selectedSessionId.value || !roundId) return
  try {
    const res = await sessionApi.getRoundMessages(selectedSessionId.value, roundId) as any
    roundMessages.value = {
      ...roundMessages.value,
      [roundId]: res.messages || [],
    }
  } catch (error) {
    console.error('Failed to load round messages:', error)
    if (showError) MessagePlugin.error('轮次消息加载失败')
  }
}

const selectRound = async (roundId: string) => {
  selectedRoundId.value = roundId
  await loadRoundMessages(roundId)
}

const handleSessionChange = async () => {
  roundMessages.value = {}
  selectedRoundId.value = ''
  await Promise.all([
    loadEvents(false),
    loadRounds(true),
  ])
  connectSessionSocket()
}

const manualRefresh = async () => {
  await Promise.all([
    loadAgents(),
    loadSessions(false),
  ])
  if (selectedSessionId.value) {
    await Promise.all([
      loadEvents(true),
      loadRounds(true),
    ])
    if (selectedRoundId.value) {
      await loadRoundMessages(selectedRoundId.value, true)
    }
  }
}

const openSessionDetail = () => {
  if (!selectedSessionId.value) return
  router.push(`/sessions/${selectedSessionId.value}`)
}

onMounted(async () => {
  await Promise.all([loadAgents(), loadSessions(false)])
  refreshTimer = window.setInterval(() => {
    loadAgents()
    loadSessions(false)
    if (selectedSessionId.value) {
      loadEvents(false)
      loadRounds(false)
      if (selectedRoundId.value) loadRoundMessages(selectedRoundId.value, false)
    }
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (socket) socket.close()
})
</script>
