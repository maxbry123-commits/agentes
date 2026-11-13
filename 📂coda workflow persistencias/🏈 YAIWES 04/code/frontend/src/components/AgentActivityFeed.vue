<template>
  <div class="space-y-4">
    <div v-if="activities.length === 0" class="text-center py-12">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-700/50 flex items-center justify-center">
        <Bot class="w-8 h-8 text-slate-500" />
      </div>
      <p class="text-slate-400">暂无智能体活动记录</p>
      <p class="text-xs text-slate-500 mt-1">开始扫描后，活动将实时显示在这里</p>
    </div>
    
    <div 
      v-for="(activity, index) in activities" 
      :key="activity.id"
      class="group relative"
    >
      <!-- 连接线 -->
      <div v-if="index < activities.length - 1" 
        class="absolute left-[22px] top-12 w-0.5 h-full bg-slate-700/70">
      </div>
      
      <div 
        :id="`activity-${activity.id}`"
        class="relative flex gap-4 p-4 rounded-xl border transition-all duration-300 hover:border-slate-600"
        :class="[
          getActivityBackground(activity),
          selectedActivityId === activity.id ? 'ring-1 ring-cyan-400/60 border-cyan-400/70' : 'cursor-pointer'
        ]"
        @click="emit('activity-click', activity)"
      >
        <!-- 活动类型图标 -->
        <div class="flex-shrink-0">
          <div 
            class="w-11 h-11 rounded-xl flex items-center justify-center"
            :style="{ 
              background: `linear-gradient(135deg, ${getAgentColor(activity.agent)}26, ${getAgentColor(activity.agent)}12)`
            }"
          >
            <component :is="getTypeIcon(activity.type)" class="w-5 h-5" :style="{ color: getAgentColor(activity.agent) }" />
          </div>
        </div>
        
        <!-- 活动内容 -->
        <div class="flex-1 min-w-0">
          <!-- 头部：智能体名称 + 活动类型标签 + 时间 -->
          <div class="flex items-center gap-2 mb-2 flex-wrap">
            <span class="text-white font-medium text-sm">{{ getAgentDisplayName(activity.agent) }}</span>
            <span 
              class="px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wide"
              :class="getTypeBadgeClass(activity.type)"
            >
              {{ getTypeText(activity.type) }}
            </span>
            <span class="text-[10px] text-slate-500 ml-auto">
              {{ formatTime(activity.timestamp) }}
            </span>
          </div>

          <div class="flex items-center gap-2 mb-2 flex-wrap text-[10px]">
            <span
              v-if="activity.session_id"
              class="px-2 py-0.5 rounded bg-slate-700/60 text-slate-300"
            >
              会话 {{ simplifyId(activity.session_id) }}
            </span>
            <span
              v-if="activity.round_id"
              class="px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-300"
            >
              轮次 {{ simplifyId(activity.round_id) }}
            </span>
          </div>
          
          <!-- 活动内容文字 -->
          <p class="text-sm text-slate-300 leading-relaxed">{{ activity.content }}</p>
          
          <!-- 思考过程展示 -->
          <div 
            v-if="isThinkingEvent(activity.type) && (activity.details?.thoughts || activity.details?.prompt_preview || activity.details?.result_preview)" 
            class="mt-3 p-3 rounded-lg bg-slate-900/50 border border-slate-700/50"
          >
            <div class="flex items-center gap-2 mb-2">
              <Brain class="w-3.5 h-3.5 text-blue-400" />
              <span class="text-xs text-blue-400 font-medium">思考过程</span>
            </div>
            <p v-if="activity.details?.thoughts" class="text-xs text-slate-400 leading-relaxed">{{ activity.details.thoughts }}</p>
            <p v-if="activity.details?.prompt_preview" class="text-xs text-slate-500 leading-relaxed mt-2 break-all">
              Prompt: {{ activity.details.prompt_preview }}
            </p>
            <p v-if="activity.details?.result_preview" class="text-xs text-slate-400 leading-relaxed mt-2 break-all">
              输出摘要: {{ activity.details.result_preview }}
            </p>
          </div>
          
          <!-- 工具调用详情 -->
          <div 
            v-if="isToolEvent(activity.type) && activity.details" 
            class="mt-3 p-3 rounded-lg bg-slate-900/50 border border-slate-700/50"
          >
            <div class="flex items-center gap-2 mb-2">
              <Terminal class="w-3.5 h-3.5 text-cyan-400" />
              <span class="text-xs text-cyan-400 font-medium">工具调用</span>
            </div>
            <div class="space-y-1.5 font-mono text-xs">
              <div v-if="activity.details.tool" class="flex items-center gap-2">
                <span class="text-slate-500">Tool:</span>
                <span class="text-cyan-300">{{ activity.details.tool }}</span>
              </div>
              <div v-if="activity.details.tools?.length" class="flex items-start gap-2">
                <span class="text-slate-500">Tools:</span>
                <span class="text-cyan-300 break-all">{{ activity.details.tools.join(', ') }}</span>
              </div>
              <div v-if="activity.details.command" class="flex items-start gap-2">
                <span class="text-slate-500">Cmd:</span>
                <code class="text-emerald-300 break-all">{{ activity.details.command }}</code>
              </div>
              <div v-if="activity.details.target" class="flex items-center gap-2">
                <span class="text-slate-500">Target:</span>
                <span class="text-amber-300">{{ activity.details.target }}</span>
              </div>
              <div v-if="activity.details.depth" class="flex items-center gap-2">
                <span class="text-slate-500">Depth:</span>
                <span class="text-amber-300">{{ activity.details.depth }}</span>
              </div>
              <div v-if="activity.details.os_family" class="flex items-center gap-2">
                <span class="text-slate-500">OS:</span>
                <span class="text-purple-300">{{ activity.details.os_family }}</span>
              </div>
            </div>
          </div>
          
          <!-- 结果详情 -->
          <div 
            v-if="isResultEvent(activity.type) && activity.details" 
            class="mt-3 p-3 rounded-lg bg-slate-900/50 border border-slate-700/50"
          >
            <div class="flex items-center gap-2 mb-2">
              <CheckCircle class="w-3.5 h-3.5 text-green-400" />
              <span class="text-xs text-green-400 font-medium">执行结果</span>
            </div>
            <div class="space-y-1.5 text-xs">
              <div v-if="activity.details.ports" class="flex items-center gap-2 flex-wrap">
                <span class="text-slate-500">开放端口:</span>
                <div class="flex flex-wrap gap-1">
                  <span v-for="port in activity.details.ports" :key="port" 
                    class="px-1.5 py-0.5 rounded bg-green-500/20 text-green-400">
                    {{ port }}
                  </span>
                </div>
              </div>
              <div v-if="activity.details.vulns" class="flex items-center gap-2 flex-wrap">
                <span class="text-slate-500">发现漏洞:</span>
                <div class="flex flex-wrap gap-1">
                  <span v-for="vuln in activity.details.vulns" :key="vuln" 
                    class="px-1.5 py-0.5 rounded bg-red-500/20 text-red-400">
                    {{ vuln }}
                  </span>
                </div>
              </div>
              <div v-if="activity.details.services" class="flex items-center gap-2">
                <span class="text-slate-500">服务:</span>
                <span class="text-purple-300">{{ activity.details.services }}</span>
              </div>
              <div v-if="activity.details.report_id" class="flex items-center gap-2">
                <span class="text-slate-500">报告ID:</span>
                <span class="text-blue-300">{{ activity.details.report_id }}</span>
              </div>
              <div v-if="activity.details.data_preview" class="flex items-start gap-2">
                <span class="text-slate-500">摘要:</span>
                <span class="text-slate-300 break-all">{{ activity.details.data_preview }}</span>
              </div>
              <div v-if="activity.details.status" class="flex items-center gap-2">
                <span class="text-slate-500">状态:</span>
                <span class="text-blue-300">{{ activity.details.status }}</span>
              </div>
            </div>
          </div>

          <!-- 消息详情 -->
          <div
            v-if="isMessageEvent(activity.type) && activity.details"
            class="mt-3 p-3 rounded-lg bg-slate-900/50 border border-slate-700/50"
          >
            <div class="flex items-center gap-2 mb-2">
              <MessageSquare class="w-3.5 h-3.5 text-indigo-400" />
              <span class="text-xs text-indigo-400 font-medium">智能体消息</span>
            </div>
            <div class="space-y-1.5 text-xs">
              <div v-if="activity.details.sender" class="flex items-center gap-2">
                <span class="text-slate-500">发送方:</span>
                <span class="text-slate-300">{{ getAgentDisplayName(activity.details.sender) }}</span>
              </div>
              <div v-if="activity.details.receiver" class="flex items-center gap-2">
                <span class="text-slate-500">接收方:</span>
                <span class="text-slate-300">{{ getAgentDisplayName(activity.details.receiver) }}</span>
              </div>
              <div v-if="activity.details.message_type" class="flex items-center gap-2">
                <span class="text-slate-500">消息类型:</span>
                <span class="text-indigo-300">{{ activity.details.message_type }}</span>
              </div>
              <div v-if="activity.details.message_id" class="flex items-center gap-2">
                <span class="text-slate-500">消息ID:</span>
                <span class="text-slate-400">{{ simplifyId(activity.details.message_id) }}</span>
              </div>
            </div>
          </div>
          
          <!-- 错误详情 -->
          <div 
            v-if="isErrorEvent(activity.type) && activity.details?.error" 
            class="mt-3 p-3 rounded-lg bg-red-900/20 border border-red-800/30"
          >
            <div class="flex items-center gap-2 mb-2">
              <AlertCircle class="w-3.5 h-3.5 text-red-400" />
              <span class="text-xs text-red-400 font-medium">错误信息</span>
            </div>
            <p class="text-xs text-red-300">{{ activity.details.error }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, watch } from 'vue'
import { Bot, Brain, Terminal, CheckCircle, AlertCircle, Search, Wrench, FileCheck, AlertTriangle, Sparkles, MessageSquare, PlayCircle, PauseCircle, CheckCheck } from 'lucide-vue-next'

interface Activity {
  id: string
  agent: string
  type: string
  content: string
  details: Record<string, any>
  timestamp: string
  session_id?: string
  round_id?: string
}

const props = defineProps<{
  activities: Activity[]
  selectedActivityId?: string
}>()

const emit = defineEmits<{
  (e: 'activity-click', activity: Activity): void
}>()

const agentColors: Record<string, string> = {
  CoordinatorAgent: '#ef4444',
  ReconAgent: '#00d4ff',
  VulnAgent: '#8b5cf6',
  ExploitAgent: '#f59e0b',
  ReportAgent: '#10b981',
}

const agentDisplayNames: Record<string, string> = {
  CoordinatorAgent: '协调者',
  ReconAgent: '侦察专家',
  VulnAgent: '漏洞分析师',
  ExploitAgent: '攻击专家',
  ReportAgent: '报告专家',
}

const getAgentColor = (agent: string): string => agentColors[agent] || '#6b7280'
const getAgentDisplayName = (agent: string): string => agentDisplayNames[agent] || agent

const getActivityBackground = (activity: Activity): string => {
  const baseClasses = 'bg-slate-800/40 border-slate-700/50'
  const typeClasses: Record<string, string> = {
    thinking: 'bg-blue-950/30 border-blue-900/30',
    tool_call: 'bg-cyan-950/30 border-cyan-900/30',
    result: 'bg-green-950/30 border-green-900/30',
    error: 'bg-red-950/30 border-red-900/30',
    task_started: 'bg-sky-950/30 border-sky-900/30',
    task_completed: 'bg-emerald-950/30 border-emerald-900/30',
    task_failed: 'bg-red-950/30 border-red-900/30',
    round_started: 'bg-indigo-950/30 border-indigo-900/30',
    round_completed: 'bg-violet-950/30 border-violet-900/30',
    message_sent: 'bg-fuchsia-950/30 border-fuchsia-900/30',
    message_received: 'bg-purple-950/30 border-purple-900/30',
    session_started: 'bg-cyan-950/30 border-cyan-900/30',
    session_completed: 'bg-green-950/30 border-green-900/30',
    session_failed: 'bg-red-950/30 border-red-900/30',
    decision_finalized: 'bg-emerald-950/30 border-emerald-900/30',
    tool_call_started: 'bg-cyan-950/30 border-cyan-900/30',
    tool_call_completed: 'bg-teal-950/30 border-teal-900/30',
    thinking_started: 'bg-blue-950/30 border-blue-900/30',
    thinking_completed: 'bg-indigo-950/30 border-indigo-900/30',
    thinking_failed: 'bg-red-950/30 border-red-900/30',
  }
  return typeClasses[activity.type] || baseClasses
}

const getTypeIcon = (type: string) => {
  const icons: Record<string, any> = {
    thinking: Brain,
    tool_call: Terminal,
    result: CheckCircle,
    error: AlertTriangle,
    task_started: PlayCircle,
    task_completed: CheckCheck,
    task_failed: AlertTriangle,
    round_started: PlayCircle,
    round_completed: CheckCheck,
    message_sent: MessageSquare,
    message_received: MessageSquare,
    session_started: PlayCircle,
    session_completed: CheckCheck,
    session_failed: AlertTriangle,
    decision_finalized: FileCheck,
    tool_call_started: Terminal,
    tool_call_completed: Wrench,
    thinking_started: Brain,
    thinking_completed: Sparkles,
    thinking_failed: AlertTriangle,
  }
  return icons[type] || Sparkles
}

const getTypeBadgeClass = (type: string): string => {
  const classes: Record<string, string> = {
    thinking: 'bg-blue-500/20 text-blue-400',
    tool_call: 'bg-cyan-500/20 text-cyan-400',
    result: 'bg-green-500/20 text-green-400',
    error: 'bg-red-500/20 text-red-400',
    task_started: 'bg-sky-500/20 text-sky-400',
    task_completed: 'bg-emerald-500/20 text-emerald-400',
    task_failed: 'bg-red-500/20 text-red-400',
    round_started: 'bg-indigo-500/20 text-indigo-400',
    round_completed: 'bg-violet-500/20 text-violet-400',
    message_sent: 'bg-fuchsia-500/20 text-fuchsia-400',
    message_received: 'bg-purple-500/20 text-purple-400',
    session_started: 'bg-cyan-500/20 text-cyan-400',
    session_completed: 'bg-green-500/20 text-green-400',
    session_failed: 'bg-red-500/20 text-red-400',
    decision_finalized: 'bg-emerald-500/20 text-emerald-400',
    tool_call_started: 'bg-cyan-500/20 text-cyan-400',
    tool_call_completed: 'bg-teal-500/20 text-teal-400',
    thinking_started: 'bg-blue-500/20 text-blue-400',
    thinking_completed: 'bg-indigo-500/20 text-indigo-400',
    thinking_failed: 'bg-red-500/20 text-red-400',
  }
  return classes[type] || 'bg-slate-500/20 text-slate-400'
}

const getTypeText = (type: string): string => {
  const texts: Record<string, string> = {
    thinking: '思考中',
    tool_call: '工具调用',
    result: '结果输出',
    error: '错误',
    task_started: '任务开始',
    task_completed: '任务完成',
    task_failed: '任务失败',
    round_started: '轮次开始',
    round_completed: '轮次完成',
    message_sent: '消息发送',
    message_received: '消息接收',
    session_started: '会话开始',
    session_completed: '会话完成',
    session_failed: '会话失败',
    decision_finalized: '最终决策',
    tool_call_started: '工具开始',
    tool_call_completed: '工具完成',
    thinking_started: '开始分析',
    thinking_completed: '分析完成',
    thinking_failed: '分析失败',
  }
  return texts[type] || type
}

const isThinkingEvent = (type: string): boolean =>
  ['thinking', 'thinking_started', 'thinking_completed', 'thinking_failed'].includes(type)

const isToolEvent = (type: string): boolean =>
  ['tool_call', 'tool_call_started', 'tool_call_completed'].includes(type)

const isResultEvent = (type: string): boolean =>
  ['result', 'task_completed', 'round_completed', 'session_completed', 'decision_finalized'].includes(type)

const isMessageEvent = (type: string): boolean =>
  ['message_sent', 'message_received'].includes(type)

const isErrorEvent = (type: string): boolean =>
  ['error', 'task_failed', 'session_failed', 'thinking_failed'].includes(type)

const simplifyId = (value: string): string => {
  if (!value) return '-'
  return value.length > 18 ? `${value.slice(0, 8)}...${value.slice(-4)}` : value
}

const formatTime = (timestamp: string): string => {
  if (!timestamp) return '-'
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return timestamp
  }
}

watch(
  () => props.selectedActivityId,
  async (activityId) => {
    if (!activityId) return
    await nextTick()
    const element = document.getElementById(`activity-${activityId}`)
    element?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
)
</script>
