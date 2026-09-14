<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-white">会话观测</h2>
        <p class="text-slate-400 mt-1">查看多智能体协作会话的时间线、轮次、消息和实时事件</p>
      </div>
      <div class="flex items-center gap-3">
        <t-button variant="outline" size="small" @click="router.push('/agents')">
          返回智能体面板
        </t-button>
        <t-button theme="primary" size="small" @click="refreshAll">
          刷新会话
        </t-button>
      </div>
    </div>

    <div class="grid grid-cols-12 gap-5 items-start">
      <div class="col-span-3 space-y-5">
        <div class="obs-card">
          <div class="obs-card-header-plain">
          <div class="flex items-center justify-between w-full">
            <h3 class="obs-card-title">会话列表</h3>
            <span class="text-xs text-slate-500">{{ sessions.length }} 个</span>
          </div>
          </div>
          <div class="obs-card-body pt-0">
          <div v-if="sessions.length" class="space-y-3 max-h-[620px] overflow-y-auto pr-1">
            <button
              v-for="session in sessions"
              :key="session.session_id"
              class="w-full text-left p-3 rounded-lg border transition-colors"
              :class="selectedSessionId === session.session_id ? 'border-cyan-500/60 bg-cyan-500/10' : 'border-slate-700 bg-slate-900/40 hover:border-slate-600'"
              @click="openSession(session.session_id)"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm text-white font-medium truncate">{{ session.target || '未知目标' }}</span>
                <span class="text-[10px] px-2 py-0.5 rounded bg-slate-700/60 text-slate-300">{{ session.round_count }} 轮</span>
              </div>
              <p class="text-[11px] text-slate-400 mt-1">{{ simplifyId(session.session_id) }}</p>
              <p class="text-[11px] text-slate-500 mt-1">事件 {{ session.event_count }}</p>
            </button>
          </div>
          <div v-else class="text-sm text-slate-500">
            暂无会话，请先发起扫描任务。
          </div>
          </div>
        </div>

        <div class="obs-card">
          <div class="obs-card-header-plain">
            <h3 class="obs-card-title">会话摘要</h3>
          </div>
          <div class="obs-card-body pt-0">
          <div v-if="currentSession" class="space-y-3 text-sm">
            <div class="flex items-center justify-between gap-3">
              <span class="text-slate-400">目标</span>
              <span class="text-white text-right break-all">{{ currentSession.target || '未知目标' }}</span>
            </div>
            <div class="flex items-center justify-between gap-3">
              <span class="text-slate-400">会话ID</span>
              <span class="text-slate-300 text-xs">{{ simplifyId(currentSession.session_id) }}</span>
            </div>
            <div class="flex items-center justify-between gap-3">
              <span class="text-slate-400">事件数</span>
              <span class="text-cyan-300">{{ currentSession.event_count }}</span>
            </div>
            <div class="flex items-center justify-between gap-3">
              <span class="text-slate-400">轮次数</span>
              <span class="text-indigo-300">{{ currentSession.round_count }}</span>
            </div>
            <div class="flex items-center justify-between gap-3">
              <span class="text-slate-400">连接状态</span>
              <span :class="liveConnected ? 'text-green-400' : 'text-amber-400'">
                {{ liveConnected ? '实时订阅中' : '轮询同步中' }}
              </span>
            </div>
          </div>
          <div v-else class="text-sm text-slate-500">
            选择左侧会话以查看详情。
          </div>
          </div>
        </div>

        <div class="obs-card">
          <div class="obs-card-header-plain">
          <div class="flex items-center justify-between w-full">
            <h3 class="obs-card-title">Flag 面板</h3>
            <div class="flex items-center gap-3">
              <span class="text-xs text-slate-500">{{ sessionFlags.length }} 个</span>
              <button
                class="text-xs text-cyan-400 hover:text-cyan-300"
                @click="flagPanelExpanded = !flagPanelExpanded"
              >
                {{ flagPanelExpanded ? '收起' : '展开' }}
              </button>
            </div>
          </div>
          </div>
          <div class="obs-card-body pt-0">
          <div v-if="flagPanelExpanded && currentScanTask" class="space-y-3">
            <div class="text-xs text-slate-400">
              任务状态: <span class="text-slate-200">{{ currentScanTask.status || 'unknown' }}</span>
            </div>
            <div v-if="flagMeta.authMethod" class="text-xs text-slate-400">
              获取方式: <span class="text-emerald-300">{{ flagMeta.authMethod }}</span>
            </div>
            <div v-if="flagMeta.credential" class="text-xs text-slate-400 break-all">
              使用凭据: <span class="text-amber-300">{{ flagMeta.credential }}</span>
            </div>
            <div v-if="sessionFlags.length" class="space-y-2">
              <div
                v-for="flag in sessionFlags"
                :key="flag"
                class="rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-2"
              >
                <p class="text-sm text-emerald-200 break-all font-mono">{{ flag }}</p>
              </div>
            </div>
            <div v-else class="text-sm text-slate-500">
              当前会话已关联扫描任务，但尚未提取到 flag。
            </div>
          </div>
          <div v-else-if="flagPanelExpanded" class="text-sm text-slate-500">
            当前会话尚未关联到扫描结果。
          </div>
          <div v-else class="text-sm text-slate-500">
            Flag 面板默认折叠，点击右上角“展开”查看。
          </div>
          </div>
        </div>
      </div>

      <div class="col-span-6">
        <div class="obs-card overflow-hidden">
          <div class="obs-card-header">
            <div>
              <h3 class="obs-card-title">事件时间线</h3>
              <p class="obs-card-desc">按时间查看消息、轮次、决策、工具和任务事件</p>
            </div>
            <div class="flex items-center gap-3">
              <t-button
                size="small"
                variant="outline"
                :theme="decisionChainOnly ? 'primary' : 'default'"
                @click="decisionChainOnly = !decisionChainOnly"
              >
                {{ decisionChainOnly ? '显示全部事件' : '只看当前决策链' }}
              </t-button>
              <t-select v-model="agentFilter" clearable size="small" class="w-36" placeholder="筛选智能体">
                <t-option v-for="option in agentOptions" :key="option.value" :value="option.value" :label="option.label" />
              </t-select>
              <t-select v-model="typeFilter" clearable size="small" class="w-36" placeholder="筛选类型">
                <t-option v-for="option in typeOptions" :key="option.value" :value="option.value" :label="option.label" />
              </t-select>
            </div>
          </div>
          <div class="obs-card-body max-h-[780px] overflow-y-auto">
            <AgentActivityFeed
              :activities="filteredEvents"
              :selected-activity-id="selectedEventId"
              @activity-click="handleActivityClick"
            />
          </div>
        </div>
      </div>

      <div class="col-span-3 space-y-5">
        <div class="obs-card">
          <div class="obs-card-header-plain">
          <div class="flex items-center justify-between w-full">
            <h3 class="obs-card-title">当前决策摘要</h3>
            <span class="text-xs text-slate-500">{{ decisionSummary.sourceLabel }}</span>
          </div>
          </div>
          <div class="obs-card-body pt-0">
          <div v-if="decisionSummary.summary" class="space-y-3">
            <div class="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <p class="text-sm text-emerald-200 break-words">{{ decisionSummary.summary }}</p>
            </div>
            <div v-if="decisionSummary.roundLabel" class="text-xs text-slate-400">
              所属轮次: {{ decisionSummary.roundLabel }}
            </div>
            <div v-if="decisionSummary.agent" class="text-xs text-slate-500">
              产生者: {{ decisionSummary.agent }}
            </div>
            <div class="flex items-center gap-2 flex-wrap">
              <t-button
                v-if="decisionSummary.eventId"
                size="small"
                variant="outline"
                @click="focusEvent(decisionSummary.eventId)"
              >
                定位到事件
              </t-button>
              <t-button
                v-if="decisionSummary.roundId"
                size="small"
                variant="outline"
                @click="focusRound(decisionSummary.roundId)"
              >
                跳转到轮次
              </t-button>
            </div>
          </div>
          <div v-else class="text-sm text-slate-500">
            当前会话还没有生成明确的阶段结论。
          </div>
          </div>
        </div>

        <div class="obs-card">
          <div class="obs-card-header-plain">
          <div class="flex items-center justify-between w-full">
            <h3 class="obs-card-title">当前事件</h3>
            <span class="text-xs text-slate-500">{{ selectedEvent ? getEventTypeLabel(selectedEvent.type) : '未选中' }}</span>
          </div>
          </div>
          <div class="obs-card-body pt-0">
          <div v-if="selectedEvent" class="space-y-3 text-sm">
            <div class="p-3 rounded-lg bg-slate-900/50 border border-slate-700/60">
              <p class="text-slate-200 break-words">{{ selectedEvent.content }}</p>
            </div>
            <div class="text-xs text-slate-400">智能体: {{ selectedEvent.agent }}</div>
            <div class="text-xs text-slate-500">时间: {{ formatTime(selectedEvent.timestamp) }}</div>
            <div v-if="selectedEvent.round_id" class="text-xs text-indigo-300">轮次: {{ simplifyId(selectedEvent.round_id) }}</div>
            <div class="flex items-center gap-2 flex-wrap">
              <t-button
                v-if="previousRelatedEvent"
                size="small"
                variant="outline"
                @click="focusEvent(previousRelatedEvent.id)"
              >
                上一个相关事件
              </t-button>
              <t-button
                v-if="nextRelatedEvent"
                size="small"
                variant="outline"
                @click="focusEvent(nextRelatedEvent.id)"
              >
                下一个相关事件
              </t-button>
            </div>
          </div>
          <div v-else class="text-sm text-slate-500">
            点击中间时间线的事件可在这里查看当前焦点。
          </div>
          </div>
        </div>

      </div>
    </div>

    <div class="obs-card">
      <div class="obs-card-header">
        <div>
          <h3 class="obs-card-title">协作轮次与轮次消息</h3>
          <p class="obs-card-desc">左侧选择协作轮次，右侧查看该轮真实消息与 payload</p>
        </div>
        <span class="text-xs text-slate-500">{{ rounds.length }} 轮 / {{ selectedRoundMessages.length }} 条消息</span>
      </div>
      <div class="obs-card-body">
      <div class="grid grid-cols-1 xl:grid-cols-12 gap-4">
        <div class="xl:col-span-4">
          <div v-if="rounds.length" class="space-y-3 max-h-[420px] overflow-y-auto pr-1">
            <button
              v-for="round in rounds"
              :key="round.round_id"
              class="w-full text-left p-3 rounded-lg border transition-colors"
              :class="selectedRoundId === round.round_id ? 'border-indigo-500/60 bg-indigo-500/10' : 'border-slate-700 bg-slate-900/40 hover:border-slate-600'"
              @click="selectRound(round.round_id)"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm text-white font-medium">{{ round.phase }}</span>
                <span class="text-[10px] px-2 py-0.5 rounded" :class="round.status === 'completed' ? 'bg-green-500/20 text-green-400' : 'bg-amber-500/20 text-amber-400'">
                  {{ round.status }}
                </span>
              </div>
              <p class="text-xs text-slate-300 mt-1 break-words">{{ round.goal }}</p>
              <p class="text-[11px] text-slate-500 mt-2">{{ round.participants?.join('、') || '-' }}</p>
            </button>
          </div>
          <div v-else class="text-sm text-slate-500">
            该会话暂无轮次记录。
          </div>
        </div>

        <div class="xl:col-span-8">
          <div v-if="selectedRoundItem" class="mb-4 p-3 rounded-lg bg-slate-900/50 border border-slate-700/60">
            <div class="flex items-center justify-between gap-3 flex-wrap">
              <div>
                <p class="text-xs text-slate-500">当前轮次</p>
                <p class="text-sm text-white font-medium">{{ selectedRoundItem.phase }}</p>
              </div>
              <div class="text-right">
                <p class="text-xs text-slate-500">目标</p>
                <p class="text-sm text-slate-200 break-words">{{ selectedRoundItem.goal }}</p>
              </div>
            </div>
          </div>

          <div v-if="roundFlagPayloads.length" class="mb-4 p-3 rounded-lg bg-slate-950/60 border border-emerald-500/20">
            <div class="flex items-center justify-between gap-3 flex-wrap">
              <div>
                <p class="text-xs text-slate-500">真实利用 Payload 与 Flag</p>
                <p class="text-sm text-emerald-200">当前会话已验证 {{ roundFlagPayloads.length }} 条利用记录</p>
              </div>
              <span class="text-xs text-slate-500">来自 exploit 阶段真实结果</span>
            </div>
            <div class="mt-3 space-y-3">
              <div
                v-for="(item, index) in roundFlagPayloads"
                :key="`${item.flag}-${index}`"
                class="rounded-lg border border-emerald-500/15 bg-slate-900/60 p-3"
              >
                <div class="flex items-center justify-between gap-3 flex-wrap">
                  <div>
                    <p class="text-sm text-emerald-200 font-medium">{{ item.title || '真实利用记录' }}</p>
                    <p class="text-xs text-slate-500 mt-1">{{ item.method }} {{ item.endpoint }}</p>
                  </div>
                  <span class="text-xs font-mono text-emerald-300 break-all">{{ item.flag }}</span>
                </div>
                <p v-if="item.note" class="text-xs text-slate-400 mt-2 break-words">{{ item.note }}</p>
                <div class="mt-3">
                  <p class="text-xs text-slate-500 mb-2">Payload</p>
                  <JsonTreeView
                    :data="item.payload"
                    :path="`flagPayload.${index}.payload`"
                    :expanded-paths="expandedJsonPaths"
                    @toggle="toggleJsonPath"
                  />
                </div>
                <div v-if="item.related_artifacts && Object.keys(item.related_artifacts).length" class="mt-3">
                  <p class="text-xs text-slate-500 mb-2">关联上下文</p>
                  <JsonTreeView
                    :data="item.related_artifacts"
                    :path="`flagPayload.${index}.artifacts`"
                    :expanded-paths="expandedJsonPaths"
                    @toggle="toggleJsonPath"
                  />
                </div>
              </div>
            </div>
          </div>

          <div v-if="selectedRoundMessages.length" class="space-y-3 max-h-[520px] overflow-y-auto pr-1">
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
              <div v-if="hasMessagePayload(message)" class="mt-3">
                <button
                  class="text-xs text-cyan-400 hover:text-cyan-300"
                  @click="toggleMessagePayload(message.message_id)"
                >
                  {{ expandedPayloads[message.message_id] ? '收起 payload' : '展开 payload' }}
                </button>
                <div
                  v-if="expandedPayloads[message.message_id]"
                  class="mt-2"
                >
                  <JsonTreeView
                    :data="getMessagePayload(message)"
                    :path="getMessagePayloadPath(message)"
                    :expanded-paths="expandedJsonPaths"
                    @toggle="toggleJsonPath"
                  />
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-sm text-slate-500">
            选择轮次后可查看当前轮的智能体消息。
          </div>
        </div>
      </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight } from 'lucide-vue-next'
import { MessagePlugin } from 'tdesign-vue-next'
import AgentActivityFeed from '../components/AgentActivityFeed.vue'
import JsonTreeView from '../components/JsonTreeView.vue'
import { createSessionEventsWebSocket, scanApi, sessionApi } from '../api'

interface SessionItem {
  session_id: string
  target: string
  created_at: string
  round_count: number
  event_count: number
  metadata?: Record<string, any>
}

interface TimelineEvent {
  id: string
  agent: string
  type: string
  content: string
  details: Record<string, any>
  timestamp: string
  session_id?: string
  round_id?: string
}

interface RoundItem {
  round_id: string
  session_id: string
  phase: string
  goal: string
  participants: string[]
  status: string
  started_at: string
}

interface RoundMessage {
  message_id: string
  session_id: string
  round_id: string
  sender: string
  receiver: string
  message_type: string
  content: string
  payload?: unknown
  timestamp: string
}

interface ScanTask {
  id: string
  target: string
  status: string
  session_id?: string
  result?: Record<string, any>
  normalized_result?: Record<string, any>
}

interface FlagPayloadRecord {
  flag: string
  title: string
  endpoint: string
  method: string
  payload: unknown
  note?: string
  related_artifacts?: Record<string, unknown>
}

const route = useRoute()
const router = useRouter()

const sessions = ref<SessionItem[]>([])
const events = ref<TimelineEvent[]>([])
const rounds = ref<RoundItem[]>([])
const selectedSessionId = ref('')
const selectedRoundId = ref('')
const roundMessages = ref<Record<string, RoundMessage[]>>({})
const scanTasks = ref<ScanTask[]>([])
const liveConnected = ref(false)
const flagPanelExpanded = ref(false)
const agentFilter = ref('')
const typeFilter = ref('')
const decisionChainOnly = ref(false)
const sessionDetail = ref<SessionItem | null>(null)
const expandedPayloads = ref<Record<string, boolean>>({})
const expandedJsonPaths = ref<Record<string, boolean>>({})
const selectedEventId = ref('')

let socket: WebSocket | null = null
let refreshTimer: number | null = null

const currentSession = computed(() =>
  sessionDetail.value || sessions.value.find(item => item.session_id === selectedSessionId.value) || null
)
const currentScanTask = computed(() =>
  scanTasks.value.find(item => item.session_id === selectedSessionId.value) || null
)
const normalizedTaskResult = computed<Record<string, any>>(() =>
  currentScanTask.value?.normalized_result && typeof currentScanTask.value.normalized_result === 'object'
    ? currentScanTask.value.normalized_result as Record<string, any>
    : {}
)

const sessionFlags = computed<string[]>(() => {
  const flags = normalizedTaskResult.value?.exploit?.flags
  return Array.isArray(flags) ? flags : []
})

const flagMeta = computed(() => {
  const credential = normalizedTaskResult.value?.exploit?.credential
  return {
    authMethod: normalizedTaskResult.value?.exploit?.auth_method || '',
    credential: credential?.username ? `${credential.username} / ${credential.password || ''}` : '',
  }
})

const selectedRoundMessages = computed(() => roundMessages.value[selectedRoundId.value] || [])
const selectedRoundItem = computed(() =>
  rounds.value.find(item => item.round_id === selectedRoundId.value) || null
)
const roundFlagPayloads = computed<FlagPayloadRecord[]>(() => {
  const records = normalizedTaskResult.value?.exploit?.flag_payloads
  if (!Array.isArray(records)) return []
  return records
    .filter((item): item is FlagPayloadRecord => Boolean(item && typeof item === 'object' && typeof item.flag === 'string'))
    .map(item => ({
      flag: item.flag,
      title: typeof item.title === 'string' ? item.title : '真实利用记录',
      endpoint: typeof item.endpoint === 'string' ? item.endpoint : '',
      method: typeof item.method === 'string' ? item.method : 'GET',
      payload: typeof item.payload === 'undefined' ? '' : item.payload,
      note: typeof item.note === 'string' ? item.note : '',
      related_artifacts: item.related_artifacts && typeof item.related_artifacts === 'object'
        ? item.related_artifacts as Record<string, unknown>
        : {},
    }))
})
const selectedEvent = computed(() =>
  events.value.find(item => item.id === selectedEventId.value) || null
)

const decisionSummary = computed(() => {
  const source = events.value.find(item =>
    ['decision_finalized', 'session_completed', 'round_completed'].includes(item.type)
  )
  if (!source) {
    return { summary: '', sourceLabel: '暂无', roundLabel: '', roundId: '', eventId: '', agent: '' }
  }
  return {
    summary: source.content || source.details?.status || '',
    sourceLabel: getEventTypeLabel(source.type),
    roundLabel: source.round_id ? simplifyId(source.round_id) : '',
    roundId: source.round_id || '',
    eventId: source.id,
    agent: source.agent || '',
  }
})

const currentRoundEvents = computed(() => {
  if (selectedEvent.value?.round_id) {
    return [...events.value]
      .filter(item => item.round_id === selectedEvent.value?.round_id)
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
  }

  if (selectedEvent.value) {
    return [...events.value]
      .filter(item => item.agent === selectedEvent.value?.agent)
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
  }

  return []
})

const previousRelatedEvent = computed(() => {
  if (!selectedEvent.value) return null
  const index = currentRoundEvents.value.findIndex(item => item.id === selectedEvent.value?.id)
  return index > 0 ? currentRoundEvents.value[index - 1] : null
})

const nextRelatedEvent = computed(() => {
  if (!selectedEvent.value) return null
  const index = currentRoundEvents.value.findIndex(item => item.id === selectedEvent.value?.id)
  return index >= 0 && index < currentRoundEvents.value.length - 1
    ? currentRoundEvents.value[index + 1]
    : null
})

const decisionChainRoundId = computed(() => {
  if (decisionSummary.value.roundId) return decisionSummary.value.roundId
  if (selectedEvent.value?.round_id) return selectedEvent.value.round_id
  if (selectedRoundId.value) return selectedRoundId.value
  return ''
})

const decisionChainEventTypes = new Set([
  'message_sent',
  'message_received',
  'tool_call',
  'tool_call_started',
  'tool_call_completed',
  'task_started',
  'task_completed',
  'task_failed',
  'decision_finalized',
  'round_completed',
])

const decisionChainEvents = computed(() => {
  if (!decisionChainRoundId.value) return []
  return [...events.value]
    .filter(item => item.round_id === decisionChainRoundId.value)
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
})

const decisionChainEventIds = computed(() => {
  return new Set(
    decisionChainEvents.value
      .filter(item =>
        decisionChainEventTypes.has(item.type) ||
        ['thinking_started', 'thinking_completed', 'thinking_failed'].includes(item.type)
      )
      .map(item => item.id)
  )
})

const filteredEvents = computed(() => {
  let result = [...events.value]
  if (decisionChainOnly.value && decisionChainEventIds.value.size) {
    result = result.filter(item => decisionChainEventIds.value.has(item.id))
  }
  if (agentFilter.value) result = result.filter(item => item.agent === agentFilter.value)
  if (typeFilter.value) result = result.filter(item => item.type === typeFilter.value)
  return result.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
})

const agentOptions = computed(() => {
  const values = Array.from(new Set(events.value.map(item => item.agent))).filter(Boolean)
  return values.map(value => ({ value, label: value }))
})

const typeOptions = computed(() => {
  const values = Array.from(new Set(events.value.map(item => item.type))).filter(Boolean)
  return values.map(value => ({ value, label: getEventTypeLabel(value) }))
})

const simplifyId = (value: string): string => {
  if (!value) return '-'
  return value.length > 18 ? `${value.slice(0, 8)}...${value.slice(-4)}` : value
}

const formatTime = (timestamp: string): string => {
  if (!timestamp) return '-'
  try {
    return new Date(timestamp).toLocaleString('zh-CN', {
      hour12: false,
      month: '2-digit',
      day: '2-digit',
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

const normalizeEvent = (event: any): TimelineEvent => ({
  id: event.event_id || event.id,
  agent: event.agent,
  type: event.event_type || event.type,
  content: event.summary || event.content || '',
  details: event.details || {},
  timestamp: event.timestamp,
  session_id: event.session_id,
  round_id: event.round_id,
})

const hasMessagePayload = (message: RoundMessage): boolean => {
  const payload = getMessagePayload(message)
  if (payload === null || typeof payload === 'undefined') return false
  if (typeof payload !== 'object') return true
  return Object.keys(payload as Record<string, unknown>).length > 0
}

const parseJsonLikeString = (value: string): unknown => {
  const normalized = value.trim()
  if (!normalized) return value
  if (
    (normalized.startsWith('{') && normalized.endsWith('}')) ||
    (normalized.startsWith('[') && normalized.endsWith(']'))
  ) {
    try {
      return JSON.parse(normalized)
    } catch {
      return value
    }
  }
  return value
}

const normalizePayload = (payload: unknown): unknown => {
  if (typeof payload === 'string') return parseJsonLikeString(payload)
  return payload
}

const getMessagePayload = (message: RoundMessage): unknown => {
  return normalizePayload(message.payload)
}

const getMessagePayloadPath = (message: RoundMessage): string => {
  return `message.${message.message_id}.payload`
}

const toggleMessagePayload = (messageId: string) => {
  expandedPayloads.value = {
    ...expandedPayloads.value,
    [messageId]: !expandedPayloads.value[messageId],
  }
}

const toggleJsonPath = (path: string) => {
  expandedJsonPaths.value = {
    ...expandedJsonPaths.value,
    [path]: !expandedJsonPaths.value[path],
  }
}

const upsertEvent = (event: TimelineEvent) => {
  const index = events.value.findIndex(item => item.id === event.id)
  if (index >= 0) {
    events.value[index] = event
  } else {
    events.value.unshift(event)
  }
  events.value = [...events.value]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 400)
}

const loadSessions = async () => {
  const res = await sessionApi.list() as any
  sessions.value = (res.sessions || []).sort((a: SessionItem, b: SessionItem) => (
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  ))
}

const loadSessionDetail = async () => {
  if (!selectedSessionId.value) {
    sessionDetail.value = null
    return
  }
  const res = await sessionApi.get(selectedSessionId.value) as any
  sessionDetail.value = res as SessionItem
}

const loadScanTasks = async () => {
  const res = await scanApi.listTasks() as any
  scanTasks.value = res.tasks || []
}

const loadEvents = async () => {
  if (!selectedSessionId.value) {
    events.value = []
    selectedEventId.value = ''
    return
  }
  const res = await sessionApi.getEvents(selectedSessionId.value, 300) as any
  events.value = (res.events || []).map(normalizeEvent)
    .sort((a: TimelineEvent, b: TimelineEvent) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  if (!selectedEventId.value && events.value.length) {
    selectedEventId.value = events.value[0].id
  }
}

const loadRounds = async () => {
  if (!selectedSessionId.value) {
    rounds.value = []
    selectedRoundId.value = ''
    return
  }
  const res = await sessionApi.getRounds(selectedSessionId.value) as any
  rounds.value = (res.rounds || []).sort((a: RoundItem, b: RoundItem) => (
    new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
  ))
  if (!selectedRoundId.value && rounds.value.length) {
    selectedRoundId.value = rounds.value[0].round_id
    await loadRoundMessages(selectedRoundId.value)
  }
}

const loadRoundMessages = async (roundId: string) => {
  if (!selectedSessionId.value || !roundId) return
  const res = await sessionApi.getRoundMessages(selectedSessionId.value, roundId) as any
  roundMessages.value = {
    ...roundMessages.value,
    [roundId]: (res.messages || []).map((message: RoundMessage) => ({
      ...message,
      payload: normalizePayload(message.payload),
    })),
  }
}

const selectRound = async (roundId: string) => {
  selectedRoundId.value = roundId
  expandedPayloads.value = {}
  expandedJsonPaths.value = {}
  await loadRoundMessages(roundId)
}

const focusEvent = (eventId: string) => {
  selectedEventId.value = eventId
  const event = events.value.find(item => item.id === eventId)
  if (event?.round_id) {
    selectedRoundId.value = event.round_id
    loadRoundMessages(event.round_id)
  }
}

const focusRound = async (roundId: string) => {
  selectedRoundId.value = roundId
  decisionChainOnly.value = false
  await loadRoundMessages(roundId)
}

const handleActivityClick = async (activity: TimelineEvent) => {
  selectedEventId.value = activity.id
  if (activity.round_id) {
    selectedRoundId.value = activity.round_id
    await loadRoundMessages(activity.round_id)
  }
}

const connectSocket = () => {
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
  socket.onmessage = async (message) => {
    try {
      const payload = JSON.parse(message.data)
      if (!payload?.data) return
      upsertEvent(normalizeEvent(payload.data))
      await loadSessionDetail()
      await loadRounds()
      await loadScanTasks()
      if (selectedRoundId.value) {
        await loadRoundMessages(selectedRoundId.value)
      }
    } catch (error) {
      console.error('WebSocket message parse failed:', error)
    }
  }
  socket.onerror = () => {
    liveConnected.value = false
  }
  socket.onclose = () => {
    liveConnected.value = false
  }
}

const openSession = async (sessionId: string) => {
  if (!sessionId || selectedSessionId.value === sessionId) return
  await router.push(`/sessions/${sessionId}`)
}

const syncFromRoute = async () => {
  const routeSessionId = typeof route.params.sessionId === 'string' ? route.params.sessionId : ''
  selectedSessionId.value = routeSessionId || sessions.value[0]?.session_id || ''
  roundMessages.value = {}
  selectedRoundId.value = ''
  decisionChainOnly.value = false
  expandedPayloads.value = {}
  expandedJsonPaths.value = {}
  selectedEventId.value = ''

  if (!selectedSessionId.value) return

  await Promise.all([loadSessionDetail(), loadEvents(), loadRounds(), loadScanTasks()])
  connectSocket()
}

const refreshAll = async () => {
  try {
    await Promise.all([loadSessions(), loadScanTasks()])
    await syncFromRoute()
  } catch (error) {
    console.error('Failed to refresh session detail:', error)
    MessagePlugin.error('会话详情刷新失败')
  }
}

watch(
  () => route.params.sessionId,
  async () => {
    await syncFromRoute()
  }
)

onMounted(async () => {
  try {
    await Promise.all([loadSessions(), loadScanTasks()])
    if (!route.params.sessionId && sessions.value[0]?.session_id) {
      await router.replace(`/sessions/${sessions.value[0].session_id}`)
    } else {
      await syncFromRoute()
    }

    refreshTimer = window.setInterval(async () => {
      await Promise.all([loadSessions(), loadScanTasks()])
      if (selectedSessionId.value) {
        await loadSessionDetail()
        await loadEvents()
        await loadRounds()
        if (selectedRoundId.value) {
          await loadRoundMessages(selectedRoundId.value)
        }
      }
    }, 5000)
  } catch (error) {
    console.error('Session detail init failed:', error)
    MessagePlugin.warning('会话详情初始化失败')
  }
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (socket) socket.close()
})
</script>
